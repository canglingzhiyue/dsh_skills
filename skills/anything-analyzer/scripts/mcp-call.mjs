// 通用 MCP 调用探针 —— 直连 anything-analyzer 内置 MCP Server
//
// 用法:
//   node mcp-call.mjs __list__                 # 列出全部工具
//   node mcp-call.mjs list_sessions
//   node mcp-call.mjs filter_requests '{"sessionId":"<sid>","domain":"api.example.com"}'
//
// 凭据: 默认自动读 %APPDATA%\anything-analyzer\mcp-server-config.json 里的 authToken
//       （可用环境变量 MCP_TOKEN / MCP_URL 覆盖）
//
// 注意: 用 MCP SDK 而不是 Invoke-WebRequest —— PowerShell 对 mcp-session-id
//       header 的处理有问题，第二个请求必 404。
import { readFileSync } from "node:fs";
import { join } from "node:path";

const SDK = "file:///D:/ProgramsDev/nodejs/node_modules/@deepseek-ai/dsh/node_modules/@modelcontextprotocol/sdk/dist/esm";
const { Client } = await import(`${SDK}/client/index.js`);
const { StreamableHTTPClientTransport } = await import(`${SDK}/client/streamableHttp.js`);

function loadConfig() {
  const cfgPath = join(process.env.APPDATA || "", "anything-analyzer", "mcp-server-config.json");
  try {
    return JSON.parse(readFileSync(cfgPath, "utf-8"));
  } catch {
    return null;
  }
}

const cfg = loadConfig();
const host = process.env.MCP_HOST || (cfg?.host && cfg.host !== "0.0.0.0" ? cfg.host : "127.0.0.1");
const port = process.env.MCP_PORT || cfg?.port || 23816;
const url = process.env.MCP_URL || `http://${host}:${port}/mcp`;
const token = process.env.MCP_TOKEN || cfg?.authToken || "";

if (!token) {
  console.error("[mcp-call] 拿不到 authToken —— 检查 %APPDATA%\\anything-analyzer\\mcp-server-config.json 是否存在，或用 MCP_TOKEN 传入");
  process.exit(2);
}

const toolName = process.argv[2];
const argsJson = process.argv[3];

const transport = new StreamableHTTPClientTransport(new URL(url), {
  requestInit: { headers: { Authorization: `Bearer ${token}` } },
});
const client = new Client({ name: "dsh-probe", version: "1.0" }, { capabilities: {} });

try {
  await client.connect(transport);
  if (toolName === "__list__") {
    const r = await client.listTools();
    console.log(JSON.stringify({ count: r.tools.length, names: r.tools.map((t) => t.name) }, null, 2));
  } else if (!toolName) {
    console.error("用法: node mcp-call.mjs <toolName|__list__> ['<jsonArgs>']");
    process.exit(2);
  } else {
    const r = await client.callTool({ name: toolName, arguments: argsJson ? JSON.parse(argsJson) : {} });
    const text = JSON.stringify(r, null, 2);
    console.log(text.length > 6000 ? text.slice(0, 6000) + "\n...[truncated]" : text);
  }
} catch (err) {
  console.error(`[mcp-call] 失败: ${err?.message || err}`);
  console.error(`[mcp-call] 目标: ${url} —— GUI 没开？先跑 scripts\\probe-mcp.ps1`);
  process.exit(1);
} finally {
  await client.close().catch(() => {});
}
