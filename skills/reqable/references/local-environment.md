# 本机 Reqable 环境事实与重建配方

> 实测时间 2026-11-01，Reqable 3.3.9 / mcp-server `reqable-mcp` 1.0.1。改动环境后请重跑 `scripts\probe-mcp.ps1` 复核。

## 1. 路径

| 项 | 路径 |
|---|---|
| 主程序 | `D:\ProgramsDev\reqable\Reqable.exe` |
| MCP 服务器 | `D:\ProgramsDev\reqable\mcp-server.exe`（Dart 编译的单文件，约 6.6 MB） |
| 配置 | `%APPDATA%\Reqable\config\capture_config`（**无扩展名**；同目录另有 `capture_config.json_bak` 备份） |
| 根证书（文件） | `%APPDATA%\Reqable\certificate\reqable-root.crt` |
| 私钥/CA 容器 | `%APPDATA%\Reqable\certificate\capture.bin` |
| 抓包脚本目录 | `%APPDATA%\Reqable\scripts`（本机为空） |
| 用户数据（集合/环境） | `%APPDATA%\Reqable\user\0\{config,environment,rest}` |
| 日志 | `%APPDATA%\Reqable\log\*.log` |
| 官方源码 | `https://github.com/reqable/reqable-mcp-server`（MCP 服务器开源；`reqable-app` 只是 issue 仓库，没源码） |

## 2. 令牌：`REQABLE_TOKEN`

- **形态**：用户级环境变量，值是一串长随机字符串（本机 66 字符）。**不要**把值写进任何文件、skill、账本、报告。
- **强制程度**：实测无令牌 / 错令牌 → `HTTP 401 {"message":"Missing or invalid access token."}`；正确令牌 → 200。
- **谁读它**：`mcp-server.exe` 用它给每个 API 请求加 `Authorization: Bearer <token>`。读取时机是启动瞬间。

### ★ 环境继承陷阱（2026-11-01 实测，踩过一次）

写进用户级环境变量后**重启 `dsh web` 并不保证生效**：

- 现象：MCP 工具全部出现（146 个），但每次调用都返回 `Error: Missing or invalid access token.`
- 取证：`[Environment]::GetEnvironmentVariable('REQABLE_TOKEN','User')` = 66 字符 ✓；DSH 服务进程（3080 端口那个 node）启动于 16:49:59，变量 16:44 就写进注册表了 ✓；但在 DSH 派生的任何子进程里读 `$env:REQABLE_TOKEN` → **MISSING**。
- 根因：Windows 只在**之后新启动**的进程里注入新变量。`dsh web` 是从一个**早于改动**的终端窗口里重启的，那个 shell 的环境块还是旧的，`dsh web` 继承它再传给子进程。
- 修法：`scripts\reqable-mcp-launch.cmd` 在启动瞬间兜底 —— 先用继承值，没有就 `reg query HKCU\Environment /v REQABLE_TOKEN`。实测在**完全空环境**下启动，握手 `INIT OK` + `tools/call` 成功。
- 备选（只在你想彻底干净时才用）：在**新开的**终端里重启 `dsh web`，让环境块刷新。

- **怎么设**（本机已设好，换机/重置时执行）：

  ```powershell
  [Environment]::SetEnvironmentVariable('REQABLE_TOKEN','<在你的 Reqable GUI 里生成的令牌>','User')
  ```

- **令牌从哪来**：Reqable GUI 内生成（MCP 服务器配置页 / 访问令牌入口；具体菜单位置随版本变化，**未逐版本验证**）。生成后本机 `remoteControl: true` 与 `proxyPort` 必须处于可用状态。

## 3. 端口

| 端口 | 实测行为 |
|---|---|
| **9000**（= 配置里的 `proxyPort`） | 主通道。既是 MITM 代理，也直接路由 API（`GET http://127.0.0.1:9000/` → `Hello Reqable!`） |
| 9016 | 内部 API 端口，同样返回 `Hello Reqable!` 且 API 路由可用（实测）。**不保证跨版本存在**，脚本里以 `proxyPort` 为准 |

`capture_config` 关键字段（文件名本身没有 `.json`，别按 `.json` 拼路径）：

| 字段 | 本机值 | 含义 |
|---|---|---|
| `proxyPort` | `9000` | 代理 + API 端口 |
| `autoProxy` | `false` | **默认不接管系统代理** → 抓浏览器必须显式 `proxy_set(overrideSystem=true)` |
| `remoteControl` | `true` | 允许本地 API / MCP 遥控 |
| `proxyLoopback` | `true` | 允许 loopback 流量（但见 §6 坑 6） |
| `sslProxyingConfig` | 内置 include-all + exclude-all | 解密全部 HTTPS；要按域名绕过就改这里 |
| `secondaryProxyConfig` | `isEnabled: true`、`proxies: []` | 二级代理开关开着但没配规则 |

## 4. 探活与直连

```powershell
# ① MCP 握手 + 一次真实 tools/call（推荐；这是唯一能证明「GUI 活着」的检查）
pwsh -NoProfile -File $env:USERPROFILE\.dsh\skills\reqable\scripts\probe-mcp.ps1
# 期望：INIT_OK server=reqable-mcp v1.0.1 / TOOLS_COUNT=146 / CALL_OK {"status":"active"|"inactive"}

# ② 不走 MCP 直连本地 API（MCP 没挂上、或要在别处脚本里用）
pwsh -NoProfile -File $env:USERPROFILE\.dsh\skills\reqable\scripts\reqable-api.ps1 -Path /capture/live/status
pwsh -NoProfile -File $env:USERPROFILE\.dsh\skills\reqable\scripts\reqable-api.ps1 -Path /capture/live/on -Method Post -Body '{}'
pwsh -NoProfile -File $env:USERPROFILE\.dsh\skills\reqable\scripts\reqable-api.ps1 -Path /capture/live/filter -Method Post -Body '{"filters":[{"type":"host","hosts":["www.baidu.com"]}]}'
```

## 5. DSH 挂载（本机已配）

MCP 行写在 `C:\Users\y\.dsh\profiles\web\cordis.patch.yml` 的 **`reverse-mcp-activator.config.servers`**（不是 preset，也不是 profile 顶层）：

```yaml
          - serverName: reqable
            transport: stdio
            command: 'C:\Windows\System32\cmd.exe'
            args:
              - '/c'
              - 'C:\Users\y\.dsh\skills\reqable\scripts\reqable-mcp-launch.cmd'
              - '--scope'
              - 'all'
            toolCallTimeoutMs: 60000
            failOnStartupError: false
```

要点：

- **为什么经 `cmd.exe /c` + `reqable-mcp-launch.cmd` 中转，而不是直接 exec `mcp-server.exe`**：见 §2 的「环境继承陷阱」—— 直接从 DSH 继承环境会拿到空的 `REQABLE_TOKEN`，表现为工具全在但每次调用 401。launcher 在启动瞬间补上令牌，配置里不需要出现令牌，也不依赖 DSH 的启动环境。
- launcher 的取令牌顺序：**已继承的进程环境 → 否则读 `HKCU\Environment`**。令牌只存在于内存与注册表，**不落任何文件**（本文件与账本都不含令牌值）。
- `failOnStartupError: false`：Reqable 没开时静默少工具、不拦会话创建 → **用前必须探活**。
- 生效条件：**新建逆向模式会话**（activator 在会话创建时挂载）；当前会话不会凭空出现 `mcp__reqable__*`。改完 `cordis.patch.yml` 必须重启 `dsh web`。
- 只想在个别操作里用、不想开会话 → 直接走 §4 的 `reqable-api.ps1`，能力等价（MCP 只是 API 的封装）。

## 6. 坑（实测，按遇到概率排序）

1. **`mcp-server.exe --help` 直接崩**：`Unhandled exception: FormatException: Could not find an option named "--help"`。它是 Dart `ArgParser` 且没注册 help。只认三个参数：

   | 参数 | 缩写 | 默认 | 说明 |
   |---|---|---|---|
   | `--host` | `-h` | `127.0.0.1` | Reqable API 地址（遥控远程/手机端 Reqable 时用） |
   | `--port` | `-p` | 读配置 `proxyPort`，失败回退 `9000` | API 端口 |
   | `--scope` | `-s` | `minimal` | `minimal`=48 工具 / `all`=146 工具 |

2. **GUI 不在 = 全挂**：MCP 握手成功、146 个工具照列，但每次 `tools/call` 都失败。所以「协议层通了」不等于「能用」。
3. **系统代理不接管就没浏览器流量**：`autoProxy=false` 是本机配置，必须 `proxy_set(overrideSystem=true)`。
4. **别和 Clash / v2ray 抢系统代理**：抓包期间关掉别的代理软件，否则表现为「Reqable 里一条记录都没有」。
5. **`--scope minimal` 静默降级**：断点 / 重写 / 脚本族整族都缺，工具调用会报「unknown tool」而不是「能力不足」。
6. **loopback 目标不进记录**：`proxyLoopback=true` 时经代理访问 `127.0.0.1:xxxx` 能拿到 200，但 `capture_live/filter` 查不到该条（实测 2 次）。抓本机服务改用「客户端直连 127.0.0.1:9000」或换 anything-analyzer。
7. **HTTPS 乱码 = 根证书没被信任**：检查 `Get-ChildItem Cert:\CurrentUser\Root | ? Subject -match Reqable`。本机已有 `CN="Reqable CA (Aug 3, 2025, DEA51A81)"`，所以 `https://www.baidu.com` 可直接明文入库。
8. **手机端缺三件套**：断点 / 重写 / 脚本在 Android/iOS 上不可用（系统安全策略），必须回桌面端做。
9. **「重启 DSH 就继承环境变量」是错的**（详见 §2）：必须用 launcher 兜底，或换新终端重启 `dsh web`。判断方法：在会话里跑 `pwsh -Command '$env:REQABLE_TOKEN'`，空字符串就说明 DSH 进程没继承。
10. **未登录账号时不能写**（2026-11-01 实测）：`capture_rewrite_create` / `capture_breakpoint_create` / `capture_network_throttling_create` / `capture_ssl_proxying_create` / `collection_create` / `environment_create` / `capture_live_compose` 全部返回 `… requires an account, please login to your Reqable account.`；而抓包开关、`proxy_set`、`generate_curl`、各类读取与**总开关**都正常。判断当前能否写：直接试一次 `*_create`，看是不是这条报错。要写规则得让人在 GUI 里登录（Agent 不代劳），或改用 `mitmdump`。

## 7. 从零重建（换机配方）

1. 官网下载安装 Reqable ≥ 3.2.0（MCP 服务器从 3.2.0 起内置；本机 3.3.9）。
2. 首次启动跟引导**安装并信任根证书**（否则 HTTPS 全是乱码）。
3. GUI 里生成访问令牌 → 按 §2 写进用户环境变量 `REQABLE_TOKEN`。
4. 把 `scripts\reqable-mcp-launch.cmd` 里的 `mcp-server.exe` 路径改成新机安装路径（换机唯一要改的地方）。
5. 按 §5 在 `cordis.patch.yml` 的 activator `servers` 里加 reqable 行 —— **命令走 `cmd.exe /c …reqable-mcp-launch.cmd`，不要直接 exec `mcp-server.exe`**（否则环境继承陷阱会以 401 的形式出现）。
6. `pwsh -NoProfile -File scripts\probe-mcp.ps1` → 期望 `INIT_OK` + `TOOLS_COUNT=146` + `CALL_OK`。
7. 重启 `dsh web`，新建逆向模式会话，确认出现 `mcp__reqable__*` 且一次 `capture_live_status` 返回而不报 401。
8. **账号登录状态决定能不能写规则**（见 §6 坑 10）：不登录也能抓包/筛选/读/出 cURL；要建断点/重写/脚本/限速/集合，必须在 GUI 里登录 Reqable 账号。

版本对应关系：Reqable < 3.2.0 **没有** MCP 服务器；`mcp-server.exe` 与主程序必须同版本目录（升级 Reqable 会一起更新）。
