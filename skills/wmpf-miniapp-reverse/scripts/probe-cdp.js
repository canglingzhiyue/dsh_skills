// 链路排障探针：以第二个 CDP 客户端身份连 WMPFDebugger 的代理端口，
// 验证「DevTools 前端 ←→ 代理 ←→ 小程序」这条链是否真的通。
//
// 用法：node probe-cdp.js [port]
//   port 默认 62000（与 start-debugger.ps1 的 -CdpPort 一致）
// 依赖：复用工具目录下已装好的 ws 包（env WMPFDEBUGGER_ROOT 可覆盖工具目录）
//
// 期望输出：RECEIVED 若干条消息，其中有
//   {"id":900001,"result":{}}            <- 我们发的 Runtime.enable 的响应
// 以及持续的 Page.screencastFrame（若前端开着设备工具栏/Screencast）
// 没有响应 = 小程序没连上，或小程序没在运行。

const path = require("path");

const port = Number(process.argv[2] || 62000);
const root = process.env.WMPFDEBUGGER_ROOT || "D:\\AI_python\\reverse\\vmpfdebugger";

let WebSocket;
try {
  WebSocket = require(path.join(root, "node_modules", "ws"));
} catch (e) {
  console.error(`找不到 ws 包（${root}\\node_modules\\ws）。先跑 scripts\\restore.ps1 重建环境。`);
  process.exit(3);
}

const ws = new WebSocket(`ws://127.0.0.1:${port}`);
const got = [];
const base = 900000; // 用大 id，避免与浏览器前端自身的请求 id 冲突

ws.on("open", () => {
  console.log(`connected to proxy 127.0.0.1:${port}`);
  const cmds = [
    { id: base + 1, method: "Runtime.enable" },
    { id: base + 2, method: "Page.enable" },
    { id: base + 3, method: "Runtime.evaluate", params: { expression: "1+1", returnByValue: true } },
  ];
  cmds.forEach((c, i) =>
    setTimeout(() => {
      ws.send(JSON.stringify(c));
      console.log("SENT " + c.method);
    }, 400 + i * 500),
  );
  setTimeout(() => {
    const answers = got.filter((m) => m.includes(`"id":${base}`));
    console.log(`=== RECEIVED ${got.length} messages, ${answers.length} answers to our requests ===`);
    got.slice(0, 20).forEach((m) => console.log("  " + m.slice(0, 240)));
    if (answers.length === 0) {
      console.log("!! 没有任何响应：小程序未连接或未运行（看调试器日志有没有 [miniapp] miniapp client connected）");
      process.exit(2);
    }
    process.exit(0);
  }, 12000);
});

ws.on("message", (m) => got.push(m.toString()));
ws.on("error", (e) => {
  console.error("WS ERR " + e.message + "（确认 start-debugger.ps1 正在运行、端口一致）");
  process.exit(1);
});
