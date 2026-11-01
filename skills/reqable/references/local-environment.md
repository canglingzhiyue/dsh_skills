# 本机 Reqable 环境事实与重建配方

> 实测时间 2026-11-01，Reqable 3.3.9 / mcp-server `reqable-mcp` 1.0.1。改动环境后请重跑 `scripts\probe-mcp.ps1` 复核。

## 1. 路径

| 项 | 路径 |
|---|---|
| 主程序 | `D:\ProgramsDev\reqable\Reqable.exe` |
| MCP 服务器 | `D:\ProgramsDev\reqable\mcp-server.exe`（Dart 编译的单文件，约 6.6 MB） |
| 配置 | `%APPDATA%\Reqable\config\capture_config.json` |
| 根证书（文件） | `%APPDATA%\Reqable\certificate\reqable-root.crt` |
| 私钥/CA 容器 | `%APPDATA%\Reqable\certificate\capture.bin` |
| 抓包脚本目录 | `%APPDATA%\Reqable\scripts`（本机为空） |
| 用户数据（集合/环境） | `%APPDATA%\Reqable\user\0\{config,environment,rest}` |
| 日志 | `%APPDATA%\Reqable\log\*.log` |
| 官方源码 | `https://github.com/reqable/reqable-mcp-server`（MCP 服务器开源；`reqable-app` 只是 issue 仓库，没源码） |

## 2. 令牌：`REQABLE_TOKEN`

- **形态**：用户级环境变量，值是一串长随机字符串（本机 66 字符）。**不要**把值写进任何文件、skill、账本、报告。
- **强制程度**：实测无令牌 / 错令牌 → `HTTP 401 {"message":"Missing or invalid access token."}`；正确令牌 → 200。
- **谁读它**：`mcp-server.exe` 启动时从环境继承，用它给每个 API 请求加 `Authorization: Bearer <token>`。
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

`capture_config.json` 关键字段：

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
            command: 'D:\ProgramsDev\reqable\mcp-server.exe'
            args:
              - '--scope'
              - 'all'
            env:
              REQABLE_TOKEN: !!js "process.env.REQABLE_TOKEN || ''"
            toolCallTimeoutMs: 60000
            failOnStartupError: false
```

要点：

- **`!!js` 引用环境变量**，配置里不出现令牌本体 —— 这样 `cordis.patch.yml` 被镜像进账本仓库时不泄密。
- `failOnStartupError: false`：Reqable 没开时静默少工具、不拦会话创建 → **用前必须探活**。
- 生效条件：**新建逆向模式会话**（activator 在会话创建时挂载）；当前会话不会凭空出现 `mcp__reqable__*`。
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

## 7. 从零重建（换机配方）

1. 官网下载安装 Reqable ≥ 3.2.0（MCP 服务器从 3.2.0 起内置；本机 3.3.9）。
2. 首次启动跟引导**安装并信任根证书**（否则 HTTPS 全是乱码）。
3. GUI 里生成访问令牌 → 按 §2 写进用户环境变量 `REQABLE_TOKEN`。
4. 按 §5 在 `cordis.patch.yml` 的 activator `servers` 里加 reqable 行（`!!js` 引用环境变量，别硬编码）。
5. `pwsh -NoProfile -File scripts\probe-mcp.ps1` → 期望 `INIT_OK` + `TOOLS_COUNT=146`。
6. 新建逆向模式会话，确认出现 `mcp__reqable__*` 工具。

版本对应关系：Reqable < 3.2.0 **没有** MCP 服务器；`mcp-server.exe` 与主程序必须同版本目录（升级 Reqable 会一起更新）。
