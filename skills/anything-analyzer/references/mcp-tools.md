# MCP 工具清单与实测用法

工具名在会话里以 `mcp__analyzer__<tool>` 暴露（`serverName: analyzer`）。
全部 30 个工具实测于 v3.6.62；返回统一为 `{ content: [{ type: "text", text: "<JSON 字符串>" }] }`，内层 `text` 需再解析一次。

## 会话与抓包（7）

| 工具 | 参数 | 备注 |
|---|---|---|
| `list_sessions` | — | 返回 `[{id, name, target_url, status, created_at, stopped_at}]` |
| `create_session` | `name`, `targetUrl` | `targetUrl` 必填但**可以是占位符**；手机抓包场景填任意 URL 即可 |
| `start_capture` | `sessionId` | **内嵌浏览器必须已打开**；之后第一次导航可能漏抓（见坑 1） |
| `pause_capture` / `resume_capture` | `sessionId` | 暂停/恢复，不清空已抓数据 |
| `stop_capture` | `sessionId` | 结束会话 |
| `delete_session` | `sessionId` | 删会话及其全部数据 |

## 浏览器控制（11）

| 工具 | 参数 | 备注 |
|---|---|---|
| `navigate` | `url` | 作用于**当前活动标签页** |
| `browser_back` / `browser_forward` / `browser_reload` | — | |
| `create_tab` | `url?` | 弹窗会被自动捕获为内部标签（OAuth 友好） |
| `close_tab` | `tabId` | |
| `list_tabs` | — | 返回 `[{id, url, title}]` |
| `clear_browser_env` | — | 清 cookie/localStorage/sessionStorage/缓存，**登录态会丢** |
| `browser_screenshot` | — | 当前标签页 PNG |
| `cdp_send_command` | `method`, `params` | **任意 CDP 命令**——最强的一个，见下 |
| `execute_browser_action` | `action`, `selector?`, `text?`, `url?`, `x?`, `y?` | 单击/输入/滚动/导航 |
| `get_page_elements` | `filter` (`clickable`/`inputs`/`links`/`buttons`/`all`) | 拿 CSS 选择器，配合上一个用 |

### `cdp_send_command` 实测有效的命令

```
Network.setUserAgentOverride   # 洗掉 anything-analyzer UA —— 实测生效
  { userAgent, acceptLanguage, platform }
Runtime.evaluate               # 任意 JS（返回需 returnByValue 才带值）
  { expression: "...", returnByValue: true, awaitPromise: true }
Page.captureScreenshot         # 截图（base64）
Network.getResponseBody        # 取某请求响应体
Emulation.setDeviceMetricsOverride  # 移动端视口
```

> 需要 `start_capture` 已 attach CDP 才能用。

## 数据读取（5）—— 逆向主战场

| 工具 | 参数 | 返回 |
|---|---|---|
| `get_requests` | `sessionId` | 全量请求；body 超 2000 字符截断 |
| `filter_requests` | `sessionId`, `method?`, `domain?`, `statusCode?`, `statusRange?`(`2xx`…), `contentType?`, `urlPattern?`, `limit?`(默认 50) | **实际首选**：抓手机 App 一次几百条，先按 domain 收窄 |
| `get_request_detail` | `requestId` | 单条完整 headers + request/response body |
| `get_hooks` | `sessionId` | JS Hook 记录：fetch / XHR / crypto.subtle / CryptoJS / sm-crypto(SM2-3-4) / JSEncrypt 的**入参+调用栈+结果** |
| `get_storage` | `sessionId` | cookie / localStorage / sessionStorage 快照 |

`get_hooks` 是找前端加密最快的入口：先看有没有 `CryptoJS.AES.encrypt` 之类调用，再看入参与结果，就能定位签名/加密参数是怎么算出来的。

## 交互录制与回放（4）

| 工具 | 参数 |
|---|---|
| `get_interactions` | `sessionId`, `type?`(click/dblclick/input/scroll/navigate/hover), `limit?` |
| `get_interaction_summary` | `sessionId` —— 动作序列 + 关键元素 + 导航流 |
| `replay_interactions` | `sessionId`, `speed?`(默认 2), `fromSequence?`, `toSequence?`, `skipMoves?` |
| — | 回放走 CDP Input 模拟；用于「重跑一遍用户刚做的操作」 |

## AI 分析（3，本机未配 LLM，逆向模式下非必需）

| 工具 | 参数 |
|---|---|
| `run_analysis` | `sessionId`, `purpose?`(`reverse-api`/`security-audit`/`performance`/`crypto-reverse`/自定义), `selectedSeqs?` |
| `get_reports` | `sessionId` |
| `chat_followup` | `sessionId`, `message` |

> 需要应用 Settings → LLM 里配好 API Key。**逆向模式下建议跳过**：抓到的原始数据由 Agent 自己分析，结论更可控、也更贴合案件上下文。

## 资源（1）

`session://…` 形式的 resource，列出会话。用 `list_sessions` 更直接。

## 手动调用（GUI 不配合时）

两个脚本都**从 `mcp-server-config.json` 自动读 token**，不需要手动传凭据。

```powershell
# 探活 + 列工具（curl 实现，退出码 0 = 可用）
pwsh -File "$env:USERPROFILE\.dsh\skills\anything-analyzer\scripts\probe-mcp.ps1"

# 列全部工具 / 任意工具调用（Node + MCP SDK 实现）
$MCP = "$env:USERPROFILE\.dsh\skills\anything-analyzer\scripts\mcp-call.mjs"
node $MCP __list__
node $MCP list_sessions
node $MCP filter_requests '{"sessionId":"<sid>","domain":"api.example.com"}'
node $MCP get_request_detail '{"requestId":"<rid>"}'
```

> **不要用 `Invoke-WebRequest`** —— 它对 `mcp-session-id` header 处理有问题，第二个请求必 404。用 `curl.exe`（探活脚本）或 MCP SDK（调用脚本）。
