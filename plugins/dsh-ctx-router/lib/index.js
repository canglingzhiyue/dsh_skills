/**
 * dsh-ctx-router — a native DSH plugin on the `tools/pre-execute` seam.
 *
 * Purpose: keep large raw outputs out of the model's context. A tool call that
 * would flood the transcript (recursive listings, unbounded logs, raw file
 * dumps, wide greps) is denied with guidance to use the context-mode sandbox
 * (`ctx_*` MCP tools), where the raw bytes stay in the sandbox and only the
 * derived conclusion returns.
 *
 * Contract (from @deepseek-ai/dsh-tools): the seam is a waterfall invoked as
 *   waterfall(carrier, 'tools/pre-execute', exec, () => ({ kind: 'allow' }))
 * and its decision is consumed as
 *   denialReason = decision.kind === 'allow' ? guardReason(exec) : decision.reason
 * so returning `{ kind: 'deny', reason }` blocks the call and surfaces `reason`
 * to the model as an error. The handler shape is `(exec, next)`.
 *
 * Fail-open by design: any unexpected error allows the call. It never throws
 * into the tool pipeline and never blocks a call it does not recognise.
 */
import { appendFileSync, statSync } from 'node:fs';

export const name = 'ctx-router';
export const inject = [];

const LOG = 'C:\\Users\\y\\.dsh\\context-mode\\ctx-router.log';
const MAX_READ_BYTES = 256 * 1024;
/** Escape hatch: put this token anywhere in the command to bypass the router. */
const ESCAPE = 'ctx-allow';

const HINT_EXEC = [
  'ctx-router: 这次调用会把大量原始输出灌进上下文，已拦下 —— 请让原始字节留在沙箱，只把结论取回：',
  '  · 日志 / HTML / 大 JSON / CSV / 多文件统计 / 目录扫描 → mcp__context-mode__ctx_execute（写代码算，只 console.log 结论）',
  '  · 单个大文件 → mcp__context-mode__ctx_execute_file',
  '  · 多命令调研（git log、多处搜索、多个接口）→ mcp__context-mode__ctx_batch_execute，queries 里一次问全',
  '  · 抓网页 → mcp__context-mode__ctx_fetch_and_index（之后用 ctx_search 按主题回查）',
  '确实需要原始输出时：在命令里带上 ctx-allow 再重试。',
].join('\n');

const HINT_READ = [
  'ctx-router: 这个文件很大，整读会占掉大量上下文，已拦下。',
  '  · 要从文件里得出结论 → mcp__context-mode__ctx_execute_file（只把结论打印回来）',
  '  · 确实要读原文 → 给 read 加上 limit / offset 分页读取',
].join('\n');

/** Command shapes whose raw output is typically large enough to waste context. */
const BIG_OUTPUT = [
  { re: /\b(?:curl|wget|iwr|irm)\b/i, why: '网络抓取' },
  { re: /\bInvoke-(?:WebRequest|RestMethod)\b/i, why: '网络抓取' },
  { re: /Get-Content\b[^|]*-Raw/i, why: '整文件读取' },
  { re: /(?:^|[|;&]\s*)(?:cat|type)\s+\S/i, why: '整文件读取' },
  { re: /(?:Select-String|\brg\b|findstr)/i, why: '全文检索' },
  { re: /(?:docker|kubectl)\s+logs|journalctl/i, why: '日志读取' },
  { re: /\bgit\s+log\b(?![^|]*(?:-n\b|--max-count|-\d))/i, why: '未限量的 git log' },
  { re: /\bgit\s+diff\b(?![^|]*--stat)/i, why: '未限量的 git diff' },
  { re: /\b(?:find|Get-ChildItem)\b[^|]*-Recurse/i, why: '递归目录扫描' },
];

function log(line) {
  try {
    appendFileSync(LOG, `${new Date().toISOString()}  ${line}\n`);
  } catch {}
}

/**
 * Decide whether one tool call should be routed to the sandbox.
 * @returns a denial reason, or undefined to let the call proceed.
 */
function routeReason(exec) {
  const tool = exec?.name;
  const args = exec?.arguments ?? {};

  if (tool === 'read') {
    const file = args.file_path ?? args.path;
    if (typeof file !== 'string' || file.length === 0) return undefined;
    // An explicit window means the caller already bounded the read.
    if (args.limit !== undefined || args.offset !== undefined) return undefined;
    try {
      const info = statSync(file);
      if (info.isFile() && info.size > MAX_READ_BYTES) {
        return { reason: HINT_READ, why: `大文件整读 ${(info.size / 1024 / 1024).toFixed(2)} MB` };
      }
    } catch {
      /* unreadable path: not this guard's business */
    }
    return undefined;
  }

  if (tool !== 'pwsh' && tool !== 'bash') return undefined;
  const command = args.command;
  if (typeof command !== 'string' || command.length === 0) return undefined;
  if (command.includes(ESCAPE)) return undefined;
  for (const { re, why } of BIG_OUTPUT) {
    if (re.test(command)) return { reason: `${HINT_EXEC}\n\n（命中：${why}）`, why };
  }
  return undefined;
}

export function apply(ctx) {
  ctx.on('tools/pre-execute', async (exec, next) => {
    try {
      const hit = routeReason(exec);
      if (hit !== undefined) {
        const target = exec?.arguments?.command ?? exec?.arguments?.file_path ?? '';
        log(
          `DENY  tool=${exec?.name}  why=${hit.why}` +
          `  arglen=${typeof target === 'string' ? target.length : 0}` +
          `  arg=${JSON.stringify(target).slice(0, 400)}`,
        );
        return { kind: 'deny', reason: hit.reason };
      }
    } catch (error) {
      log(`ERROR ${String(error && error.message)} — allowed`);
    }
    return next();
  });
}
