---
name: reqable
description: 本机已装好的 Reqable（Fiddler + Charles + Postman 三合一，v3.3.9）及其内置 MCP 服务器 reqable-mcp（v1.0.1，--scope all 提供 146 个工具）。当需要抓本机 / 手机 App / 桌面程序 / CLI / Python 脚本的 HTTP(S) 流量、筛会话、读单条报文、转可重放 cURL、开关抓包与系统代理，或提到 reqable / Reqable MCP / 9000 代理 / 抓包 / HAR / 协同模式时使用。注意：断点 / 重写 / 脚本 / 限速等**创建类操作需要登录 Reqable 账号**，未登录时本技能只能读与开关。
---

# reqable — Reqable 抓包与内置 MCP 服务器

Reqable = 抓包调试 + 接口测试。对本模式真正的价值是：**它自带 stdio MCP 服务器，Agent 能直接遥控抓包、筛流量、建规则**，不需要人肉点 GUI。
与 `anything-analyzer`（只读 MITM + MCP）的差别：Reqable **能改**（重写 / 断点 / 脚本 / 镜像 / 限速），代价是要 GUI 常驻且令牌鉴权。

## 0. 本机事实（2026-11-01 实测，非推断）

| 项 | 值 |
|---|---|
| 程序 | `D:\ProgramsDev\reqable\Reqable.exe`（v3.3.9） |
| MCP 服务器 | 同目录 `mcp-server.exe`（serverInfo `reqable-mcp` v1.0.1，协议 `2024-11-05`） |
| 传输 | **stdio**（不是 HTTP，别按 URL 挂） |
| 鉴权 | 用户环境变量 **`REQABLE_TOKEN`**：缺失或错误 → API 返回 `401 Missing or invalid access token.` |
| API 端口 | `proxyPort`（本机配置 = **9000**；实测内部端口 9016 同样响应，但以 9000 为准） |
| 工具数 | `--scope all` = **146**；`--scope minimal` = **48** |
| 配置 | `%APPDATA%\Reqable\config\capture_config`（**无扩展名**，旁边是 `capture_config.json_bak`）：`proxyPort` / `autoProxy` / `remoteControl` / `sslProxyingConfig` |
| 根证书 | `%APPDATA%\Reqable\certificate\reqable-root.crt`（本机已装进 `Cert:\CurrentUser\Root`） |
| DSH 挂载 | `cordis.patch.yml` 的 `reverse-mcp-activator.config.servers`，工具前缀 **`mcp__reqable__*`**；经 `scripts\reqable-mcp-launch.cmd` 启动（见坑 3） |
| 等价通道 | 不带 MCP 也能用：`scripts\reqable-api.ps1` 直连本地 API（见 references\local-environment.md） |

细节与坑：`references\local-environment.md`；工具全表与参数结构：`references\mcp-tools.md`；抓包流程：`references\capture-workflows.md`。

## 1. 开工三步（顺序敏感）

1. **确认 GUI 在跑。** MCP 服务器只是遥控器，抓包本体在 GUI 进程里 —— GUI 不在，所有工具调用失败。探：
   ```powershell
   Get-Process Reqable -ErrorAction SilentlyContinue | Select-Object Id,StartTime
   ```
   不在就 `Start-Process 'D:\ProgramsDev\reqable\Reqable.exe'`，等 9000 监听（约 3–5 秒）。
2. **探活 MCP。** `pwsh -NoProfile -File scripts\probe-mcp.ps1` —— 期望输出 `INIT_OK server=reqable-mcp` 且 `TOOLS_COUNT=146`（minimal 是 48）。
   逆向模式会话里更简单：直接看有没有 `mcp__reqable__*` 工具；没有就是 activator 没挂或 GUI 没起。
3. **开抓 + 接管系统代理**（两件事，别只做一件）：
   - `capture_live_set_enabled(enabled=true)`
   - `proxy_set(overrideSystem=true)` —— 不接管系统代理，浏览器流量根本不会进 9000。

## 2. 干活主线（本模式最常用）

```
开抓 → 让目标自己跑（业务操作 / 浏览器 / 脚本） → capture_live_filter(filters) → capture_live_get_by_id(id)
     → capture_live_generate_curl(id)                     # 这条不需要账号
     → capture_live_compose(id) / capture_live_collection_add(...)   # ★ 需要登录账号
     → 改行为：capture_rewrite_create / capture_breakpoint_create / capture_script_create   # ★ 需要登录账号
```

- **筛选**：`capture_live_filter` 只返回 **ID 数组**，要详情必须再 `capture_live_get_by_id`。`filters` 是数组、多项之间 **AND**，每项是 `oneOf` 的七种形状之一（`keyword` / `url` / `host` / `ip` / `method` / `code` / `application`）。形状写错 → `400 filters is required` 或 `400`。完整 schema 见 `references\mcp-tools.md#filter`。
- **单条详情**里 `application.name` / `application.path` / `application.pid` 是**发起进程**（实测能识别出 `pwsh` 及其 pid）——定位「这个请求是哪个客户端发的」比看 UA 可靠。
- **★ 能力边界（2026-11-01 实测，未登录状态）**：能读、能开关、**不能写**。
  - ✅ 可用：`capture_live_status/filter/get/generate_curl/set_enabled/clear`、`proxy_set`、各族 `*_get_config`/`*_list`/`*_lookup`/`*_get_active`、各族 `*_set_enabled`（总开关）、`script_framework`/`script_template`。
  - ❌ 需登录账号：**所有 `*_create`**（rewrite / breakpoint / network_throttling / ssl_proxying / collection / environment 实测全部返回 `… requires an account, please login to your Reqable account.`）、`capture_live_compose`、`capture_live_collection_add`。
  - 想在未登录状态下**改流量** → 换 `mitmdump`（可写脚本）或让用户在 GUI 里登录 Reqable 账号后重试（登录是人在 GUI 里做的，Agent 不该代劳）。

## 3. 验收（本域附加判据）

「工具调用没报错」不算完成。至少给到：

1. `capture_live_filter` 返回**非空 ID 数组**，且 `capture_live_get_by_id` 拿到的记录含完整 url / 请求头 / 响应体；
2. 该记录能用 `capture_live_generate_curl` 生成命令并**重放成功**（同状态码、关键字段一致）；
3. **只有用户已登录账号时**才要求这一条：建的规则在 `capture_breakpoint_list` / `capture_rewrite_list` / `capture_script_list` 里可见且 `isEnabled=true`，并**直接观察到目标流量被改变**（不是「规则建好了」）。未登录时把「创建被拒」当作**已知边界**记录，不要伪报成功；
4. 收尾把规则关掉或删掉，不留残留（`*_set_enabled(false)` / `*_delete`）。

## 4. 已知坑（都踩过或实测过）

1. **`mcp-server.exe --help` 会崩**：`FormatException: Could not find an option named "--help"`（Dart `ArgParser`，没有 help 分支）。想查参数就读 `--host/-h`、`--port/-p`、`--scope/-s` 三项，或者从源码 `github.com/reqable/reqable-mcp-server` 看。
2. **GUI 不在 = 全挂**。MCP 握手仍会成功（146 工具照列），但**每次 tools/call 都失败**。所以探活要探到「一次真实调用」，`probe-mcp.ps1` 就是这么设计的。
3. **令牌是硬门槛，且「重启 DSH 就继承环境变量」是错的**：无令牌 / 错令牌一律 `401 Missing or invalid access token.`。
   ★ 2026-11-01 实测踩过的坑：令牌写进用户环境变量后重启 `dsh web`，**仍然 401** —— Windows 只把新变量传给之后启动的进程，而 `dsh web` 是从**旧终端**里重启的，继承的是旧环境块（实测 DSH 进程启动于 16:49:59、变量 16:44 已入注册表，但 DSH 进程的 `process.env` 里就没有）。
   **修法**：MCP 经 `scripts\reqable-mcp-launch.cmd` 启动 —— 优先用已继承的值，没有就当场读 `HKCU\Environment`（**令牌不落任何文件**）。这样无论 DSH 从新终端还是旧终端重启都能拿到令牌（实测空环境下手动握手 `INIT OK` + `CALL OK`）。
   **换机/重置令牌**：在 GUI 里重新生成 → 覆盖用户环境变量 → launcher 下次启动自动生效，无需重启 DSH 也能被新会话读到。
4. **★ 创建类操作全部需要登录 Reqable 账号（未登录时最容易被误判成「技能不行」）**：2026-11-01 实测，未登录状态下 `capture_rewrite_create` / `capture_breakpoint_create` / `capture_network_throttling_create` / `capture_ssl_proxying_create` / `collection_create` / `environment_create` / `capture_live_compose` 一律返回 `… requires an account, please login to your Reqable account.`。而抓包开关、`proxy_set`、`generate_curl`、各类读取与**总开关**都正常。
   → 未登录时的正确姿势是「**抓包 + 筛 + 读 + 出 cURL**」；要写规则只有两条路：① 让用户**在 GUI 里自己登录**（然后重试，Agent 不代劳登录）；② 改用 `mitmdump` 等能写脚本的通道。不要把「创建被拒」包装成「已配置」。
5. **9000 是「代理 + API」同端口**。别把它当纯 REST 端口去远程直连：远程要用 `--host <ip> --port <port>` 由 mcp-server 自己连，且对端 Reqable 也得开着。
6. **`--scope minimal` 缺一整批能力**：断点 / 重写 / 脚本 / 网关 / 镜像 / 网络限速 / 反向代理 / 二级代理 / 访问控制 / 集合删除类基本都不在 minimal 里（minimal 48 个，all 146 个）。做逆向要 `all`。
7. **只经代理访问 loopback 的目标实测不进记录**：`proxyLoopback=true` 时请求能通（返回 200），但 `capture_live/filter` 查不到该记录；真实站点（baidu）正常出入库。要抓本机服务，用「应用直连 127.0.0.1:9000」或改用 anything-analyzer。
8. **和 Clash / v2ray 抢代理**：Reqable 接管系统代理时其它代理软件会打架，抓包期间先关掉（官方文档明说）。本机 `autoProxy=false`，即**默认不接管**，要抓浏览器必须显式 `proxy_set(overrideSystem=true)`。
9. **手机端三件套用不了**：断点 / 重写 / 脚本在 Android/iOS 端因系统限制不可用，只能回桌面端做。

## 5. 与其他技能的边界

| 场景 | 用哪个 |
|---|---|
| 要**改**流量（重写 / 断点 / 脚本 / 限速 / 镜像）、要 cURL/集合资产、要 GUI 里看得见 | **本技能（Reqable）** |
| 只读抓包、要 JS Hook 与「Agent 直读会话」的轻量链路、不想起第二个 GUI | `anything-analyzer`（protocol 域主技能，8888 端口） |
| 浏览器反指纹、反爬对抗、JSVMP、签名参数定位 | `camoufox-reverse`（web 域主技能） |
| 手机 App 走流程做回归 | `firerpa` 驱动 UI + 本技能或 anything-analyzer 读流量 |
| 抓到包之后要脱壳 / 补丁 / 反编译 | `apk-reverse`、`aidbg`、`nixiang-shu` |
| 卡住没思路 | `nixiang-shu` 症状索引 |

⚠ 两个抓包 GUI 不要同时接管系统代理 —— 谁后开谁抢走，表现是「另一个工具一条记录都没有」。
