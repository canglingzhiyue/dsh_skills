#!/usr/bin/env node
/**
 * DSH ← context-mode 的 PreToolUse 适配层（自制，唯一副本在此目录）
 *
 * 为什么需要它：
 *   context-mode 官方的 PreToolUse hook 用一张**写死的**平台工具名别名表
 *   （只认 Claude Code 的 Bash / Read / Grep …）来识别工具，而 DSH 的工具叫
 *   `pwsh` / `read` / `grep` —— 表里没有，也没有配置扩展点，所以官方 hook 收到
 *   DSH 的工具名会直接放行，等于没装。
 *   本脚本挂在 DSH 自己的 hook 拦截缝（@deepseek-ai/dsh-hooks-claude-code）上，
 *   自己判断"这次调用会不会把大块原始数据灌进上下文"，是则 deny 并给出沙箱替代。
 *
 * 拦截范围（保守，只拦最明确的"数据抓取"）：
 *   - pwsh：curl / wget / Invoke-WebRequest / Get-Content -Raw / cat / type /
 *           Select-String / rg / findstr / docker logs / kubectl logs / journalctl /
 *           无上限的 git log、git diff / find / Get-ChildItem -Recurse
 *   - read：无 limit/offset 且文件 > 256 KB
 *   不拦：grep、web_fetch、glob、edit、write（DSH 侧输出本就有溢写与裁剪），
 *         也不拦改状态的操作（构建、测试、写文件、建目录）。
 *
 * 逃生舱（避免死锁）：
 *   - 命令里含 `ctx-allow`（例如 `# ctx-allow`）→ 放行
 *   - read 显式带 limit 或 offset（即主动分块读）→ 放行
 *
 * 协议：读 stdin 的 Claude Code PreToolUse payload，输出
 *   {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny",
 *    "permissionDecisionReason":"..."}}
 *   DSH 桥接的 PreToolUse 只支持 deny / ask（不支持 updatedInput）。
 * 任何异常都 fail-open（不输出、exit 0），绝不阻断会话。
 */

import { statSync } from 'node:fs';

const MAX_READ_BYTES = 256 * 1024;

// ── 会直接把大块原始数据吐进上下文的命令特征 ────────────────────────────
const FETCH_PATTERNS = [
  [/\b(curl|wget|iwr|irm)\b/i, '下载 / 请求原始响应'],
  [/Invoke-WebRequest|Invoke-RestMethod/i, '下载 / 请求原始响应'],
  [/Get-Content\b[^\n]*-Raw/i, '一次性读入整个文件'],
  [/(^|[|;&]\s*)(cat|type)\s+\S/i, '整文件输出'],
  [/\bSelect-String\b|\brg\b|\bfindstr\b/i, '全文搜索'],
  [/docker\s+logs|kubectl\s+logs|journalctl/i, '服务日志'],
  [/\bgit\s+log\b(?![^\n]*(-n\s|--max-count|-\d))/i, '完整提交历史'],
  [/\bgit\s+diff\b(?![^\n]*--stat)/i, '完整 diff'],
  [/(^|[|;&]\s*)find\s+\S|Get-ChildItem[^\n]*-Recurse/i, '目录树枚举'],
];

const WHY = [
  '这次调用的原始输出会直接进入上下文窗口，并占满本次会话余下的推理容量。',
  '',
  '改用沙箱（原始字节留在子进程里，只把结论拿回来）：',
  '  • 跑命令 / 多路调研 → mcp__context-mode__ctx_batch_execute(',
  '      commands: [{ label: "小节标题", command: "你的命令" }], queries: ["要问的问题"])',
  '  • 写代码算结论     → mcp__context-mode__ctx_execute(language: "javascript", code: "...")',
  '  • 分析单个文件     → mcp__context-mode__ctx_execute_file(path, language, code)',
  '',
  '确实需要看原文时：把范围缩小（例如只取头几行），或在命令里写 `ctx-allow` 显式放行。',
].join('\n');

function allow() {
  process.exit(0);
}

function deny(headline) {
  const reason = `${headline}\n\n${WHY}`;
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reason,
      },
    }) + '\n',
  );
  process.exit(0);
}

function readStdin() {
  return new Promise((resolve) => {
    if (process.stdin.isTTY) return resolve('');
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', () => resolve(data));
    // 兜底：3 秒还没结束就按已有内容处理（fail-open）
    const timer = setTimeout(() => resolve(data), 3000);
    timer.unref?.();
  });
}

try {
  const raw = await readStdin();
  if (!raw.trim()) allow();

  const payload = JSON.parse(raw);
  const tool = String(payload.tool_name ?? '');
  const input = payload.tool_input ?? {};

  // ── read：只在"没主动分块 + 文件很大"时拦 ────────────────────────────
  if (tool === 'read') {
    if (input.limit || input.offset) allow(); // 主动分块读 → 放行，不会死锁
    const file = input.file_path;
    if (typeof file === 'string' && file) {
      let size = 0;
      try {
        size = statSync(file).size;
      } catch {
        allow(); // 文件不存在 / 无权限 → 交给 read 自己报错
      }
      if (size > MAX_READ_BYTES) {
        deny(
          `read 被 context-mode 路由拦下：${file} 有 ${(size / 1024 / 1024).toFixed(2)} MB，` +
            `整份读进来会挤掉大量上下文。`,
        );
      }
    }
    allow();
  }

  // ── pwsh：命中"数据抓取"特征就拦 ────────────────────────────────────
  if (tool === 'pwsh') {
    const cmd = String(input.command ?? '');
    if (!cmd) allow();
    if (/ctx-allow/i.test(cmd)) allow(); // 逃生舱
    for (const [re, label] of FETCH_PATTERNS) {
      const m = cmd.match(re);
      if (m) {
        deny(`pwsh 被 context-mode 路由拦下（命中特征：${label}）。`);
      }
    }
    allow();
  }

  allow();
} catch {
  allow(); // fail-open
}
