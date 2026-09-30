---
name: anything-analyzer
description: 本机已装好的 Anything Analyzer（抓包 + MITM 代理 + 协议分析 GUI，内置 MCP Server，30 个工具）。当需要抓非浏览器流量（手机 App / 桌面应用 / curl / Python 脚本 / IoT）、要求 Agent 直接读取抓包会话、做协议还原与接口签名分析、或提到 anything-analyzer / analyzer MCP / 8888 代理 / 抓包会话 / mcp__analyzer__ 时使用。浏览器侧对抗性抓取仍归 camoufox-reverse。
---

# anything-analyzer —— 抓包与协议分析（Agent 可直驱）

Electron GUI 应用：内嵌浏览器（CDP 抓包）+ MITM 代理（8888）+ 统一会话 + 内置 MCP Server。
**它的定位不是"又一个浏览器"，而是「非浏览器流量的、Agent 可直接读的抓包台」。**

## 0. 与本机其他能力的分工（先看这张表，别用错工具）

| 需求 | 用什么 | 为什么 |
|---|---|---|
| 手机 App / 桌面应用 / curl / Python 脚本 / IoT 的流量 | **本 skill**（MITM 8888 → MCP 读） | camoufox 只能抓浏览器；Reqable/Fiddler 抓得到但 Agent 读不到 |
| 站点有反爬 / 需要指纹对抗 | `camoufox-reverse` | 本工具的指纹伪造只在 JS 层，远弱于 camoufox 的引擎级补丁 |
| 浏览器内 JS 加密逆向、JSVMP、Hook 函数 | `camoufox-reverse` 为主 | camoufox 可任意 Hook；本工具的 Hook 是固定预设 |
| 快速看「哪个接口带了签名参数」、要完整请求/响应留档 | **本 skill** | JS Hook 自动记录 fetch/XHR/crypto/CryptoJS/SM2-4，零配置 |
| 需要**改包**（改请求/响应重放） | `mitmdump` | 本工具的 MITM 是**只读**捕获，不改内容 |
| 微信小程序 | `wmpf-miniapp-reverse` | 走 WMPFDebugger，与本工具无关 |

**一句话**：伪装与 JS 深挖找 camoufox；**非浏览器流量的抓包和留档找本工具**。

## 1. 本机环境（实测，2026-09-30）

| 项 | 值 |
|---|---|
| 版本 | v3.6.62（Electron 35 + React 19） |
| 安装路径 | `D:\ProgramsDev\AnythingAnalyzer\Anything Analyzer.exe` |
| 用户数据 | `C:\Users\y\AppData\Roaming\anything-analyzer\` |
| MCP Server | `http://127.0.0.1:23816/mcp`（StreamableHTTP + Bearer 认证） |
| MITM 代理 | `0.0.0.0:8888`（HTTP/HTTPS，已启用；`systemProxy=false`） |
| CA 证书 | `%APPDATA%\anything-analyzer\certs\ca-cert.pem`（**尚未装入系统信任库，见 §5**） |
| 数据库 | `%APPDATA%\anything-analyzer\data\anything-register.db`（SQLite，存会话与请求） |
| DSH 挂载 | profile `web`，`serverName: analyzer` → 工具名 `mcp__analyzer__<tool>` |

源码副本（审查用，pin 在 `1da6b5c9acc024e987d41e4b9c88676ffea0da0c`）：
`D:\AI_python\reverse-cases\2026-09-30_anything-analyzer\data\src\`

## 2. 启动（顺序敏感）

**MCP Server 跑在 Electron 主进程里 —— GUI 不开，MCP 就不存在。** `failOnStartupError: false` 时它静默失效，所以每次用之前先探活。

```powershell
# 一键：启动 GUI 并等待 MCP 就绪（幂等）
pwsh -File "$env:USERPROFILE\.dsh\skills\anything-analyzer\scripts\start-analyzer.ps1"

# 只探活（exit 0 = 可用，会打印工具数）
pwsh -File "$env:USERPROFILE\.dsh\skills\anything-analyzer\scripts\probe-mcp.ps1"
```

配置是**纯 JSON 文件**，改完重启应用生效（不必点 GUI）：

- `%APPDATA%\anything-analyzer\mcp-server-config.json`
  `{ "enabled": true, "host": "127.0.0.1", "port": 23816, "authEnabled": true, "authToken": "<uuid>" }`
- `%APPDATA%\anything-analyzer\mitm-proxy-config.json`
  `{ "enabled": true, "port": 8888, "caInstalled": false, "systemProxy": false }`

> `authToken` 是凭据：脚本一律**从配置文件读**，不写进任何 skill 文本。换机器重新生成（首次启动自动生成）。

## 3. 典型工作流

### A. 抓手机 App 流量 → Agent 读
1. `start-analyzer.ps1` 启动（MITM 已在 8888）
2. 手机 Wi-Fi → 手动代理 → `<电脑局域网IP>:8888`
3. 手机浏览器打开 `http://<电脑局域网IP>/cert.cer` 装 CA
4. MCP：`create_session`（targetUrl 可留空占位）→ `start_capture`
5. 手机操作 App，然后 `filter_requests` / `get_request_detail` 读

详细步骤与 Android 7+ 的证书信任问题见 `references\setup.md`。

### B. 浏览器侧接口留档 + 加密定位
1. MCP：`create_session` → `start_capture` → `navigate`
2. 读：`get_requests`（全量）、`filter_requests`（按域名/方法/状态码筛）、`get_request_detail`（完整 headers+body）
3. 加密调用：`get_hooks` 拿 fetch/XHR/crypto.subtle/CryptoJS/SM2-4 的入参与结果
4. 需要登录态：`get_storage` 拿 cookie/localStorage/sessionStorage

### C. 对抗性访问（补 camoufox 的缺口）
默认 UA 带 `anything-analyzer/3.6.62`，**站点一眼识别**。用 CDP 洗掉（已实测有效）：

```
mcp__analyzer__cdp_send_command
  method: "Network.setUserAgentOverride"
  params: { userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36", acceptLanguage: "zh-CN,zh;q=0.9", platform: "Win32" }
```

`cdp_send_command` 可发**任意 CDP 命令**（`Emulation.*` / `Runtime.evaluate` / `Page.captureScreenshot` / `Network.*`），等于一个受限的浏览器控制面。

完整 30 个工具与实测参数见 `references\mcp-tools.md`。

## 4. 已知坑（都是实测的）

1. **`start_capture` 之后第一次导航可能漏抓** —— CDP attach 需要时间。实测：start_capture → navigate(example.com) 抓到 0 条；紧接着再 navigate(httpbin.org/get) 抓到 1 条。**对策：start_capture 后先 navigate 一次"预热"，或等待 2-3 秒再导航。**
2. **UA 暴露工具名**（见 §3-C）。UA 里的 `Sec-Ch-Ua-Platform: "Linux"` 也很怪（Windows 上跑 Electron），需要指纹一致性时一并覆盖。
3. **MITM 只读** —— 不改请求/响应内容，body 上限 1MB，二进制跳过，WebSocket 只隧道不解密。要改包用 `mitmdump`。
4. **必须开着 GUI** —— 不能当 headless 服务用。
5. **CA 未装系统信任库** —— 所以现在**只能抓 HTTP，HTTPS MITM 会因证书不受信而失败**。装 CA 需要管理员权限并改动系统根存储，属于要用户拍板的一步，见 `references\setup.md`。
6. **`Invoke-WebRequest` 发 MCP 请求会 404** —— PowerShell 对 `mcp-session-id` header 的处理有问题。**用 `curl.exe` 或 MCP SDK**（探活脚本已按此实现）。
7. **`run_analysis` / `chat_followup` 需要应用内配好 LLM API Key** —— 本机未配，且逆向模式下**不需要**：抓到的数据由 Agent（我自己）分析，比它的内置分析更贴合案件。这两个工具留作可选。
8. **自动更新** —— 启动 3 秒后检查 GitHub 更新。升级会换版本号，UA 里的版本串随之变化；升级后重跑探活。

## 5. 边界与红线

- 抓包数据可能含凭据/token：**不外传、不进镜像、不上账本**（按案件规范落 `data\`，收尾按需清理）。
- 只读捕获，不修改第三方流量内容。
- 装 CA 根证书 = 系统级信任改动：**先问用户**，别自动做。

## 6. 相关文件

- `references\mcp-tools.md` —— 30 个 MCP 工具清单、实测参数与返回值形状
- `references\setup.md` —— 安装/重装、配置文件、CA 证书与手机抓包、升级
- `scripts\start-analyzer.ps1` / `scripts\probe-mcp.ps1` —— 启动与探活
- 上游：https://github.com/Mouseww/anything-analyzer （MIT）
- 案件库：`D:\AI_python\reverse-cases\2026-09-30_anything-analyzer\`
