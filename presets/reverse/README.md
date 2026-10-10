# reverse —— 「逆向模式」agent preset（第四类资产）

本目录是 preset `reverse` 的整份副本，恢复方式见 `INSTALL.md` 的「reverse（逆向模式）」一节。

## 这是什么

一个 **DSH agent preset**，在会话选择器里显示为「逆向模式」。它不是 skill、不是 DSH 插件
—— 这两类都不覆盖它：

| 资产类型 | 住哪 | 换机器会自己回来吗 |
|---|---|---|
| skill | `$DSH_HOME\skills\<name>\` | 会（本仓库 `skills\` 镜像） |
| DSH 插件 | profile 的 `package.json` / `bundles`，或 profile patch 的一行 | 会（`install.ps1` 装；自研件在本仓库 `plugins\`） |
| MCP 挂载 | **`reverse-mcp-activator` 插件的 `config.servers`**（2026-10-09 起；此前在 preset composition 里，再此前在 profile host 层） | 会 —— 随 `config\cordis.patch.yml` 一起带回 |
| **agent preset** | profile patch 里的 `preset-reverse` 声明（0.2.0 起；`.agent-presets\` 目录已不再被扫描） | 会 —— 本仓库 `config\cordis.patch.yml` 里就是**全量内联**的 composition |

## 内容

| 文件 | 说明 |
|---|---|
| `agent.cordis.yml` | **历史参考副本**（文件头有【已停用】说明）。0.2.0 下 DSH 不读它；生效的 composition 全量内联在 `config\cordis.patch.yml` 的 `preset-reverse` 声明块里 |
| `preset.yml` | 显示名与描述（会话选择器里显示「逆向模式」） |

## MCP 挂载在哪（三次搬家，2026-09-30 → 10-02 → 10-09）

| 时间 | 挂载层 | 启动时机 | 为什么改 |
|---|---|---|---|
| ~09-30 | profile host 层 | `dsh web` 启动即 spawn 全部 | 最初形态 |
| 10-02 | preset composition | 当时语义：**新会话选中该 preset 才 compose** | 启动期 10 个进程、约 300 MB 常驻，要改成按需 |
| **10-09** | **`reverse-mcp-activator` 插件的 config**（host 层插件 + 会话创建时挂载） | **新开逆向模式会话时** | 0.2.0 起 registry **启动期急切挂载所有 preset**，「preset = 惰性挂载点」的语义没了：MCP 行只要写在任何 composition 里就必然随启动拉起 |

**现在的机制**（源码与配方：本仓库 `plugins\reverse-mcp-activator\`）：

- 启动只加载插件本身，**不碰任何 MCP**；
- 逆向模式会话创建时（`agent/created`，serial 且被 await），插件用
  `agentPresets.composedPreset(agent.ctx)` 认出目标 preset，再对 `agent.ctx` 调
  `ctx.plugin(McpClient, server)` —— 工具落在**该会话自己的 scope 层**；
- 所以普通会话看不到 `mcp__*`（实测全局视图 0 个），会话销毁时 MCP 进程随之退出；
- 并发挂载 + `startupTimeoutMs`（默认 5s）超时放行：快的服务器先就绪，慢的转后台继续。

**代价（明确的取舍）**：开逆向会话时工具可能晚几秒才齐（camoufox 冷启动最慢）；
每个逆向会话有自己的一份服务器进程（并发的逆向会话 = 多份）。

**挂载失败不会拦住会话**：每个 server 的 `failOnStartupError` 都是 `false`，服务器连不上时
只会**静默少掉工具**。能让会话创建失败的只有 composition 语法/结构错误、行引用的包不存在
这类硬错误 —— 用工具前先按能力清单探活。

**它们仍然不需要 `isolate` realm** —— 只往 `ctx.tools` 注册工具、不 `provide` 服务。

**analyzer 的 token 不在仓库里**：`config\cordis.patch.yml` 里只写
`!!js process.env.ANALYZER_MCP_TOKEN`，真值在 `$DSH_HOME\.env`（Harness-home 专属层，
明确不随任何仓库传播）。这是刻意的 —— 本目录要进私有备份仓库，而凭据永不备份。
该变量只在 DSH 启动时读取，改完要重启。

## 依赖（必须先装）

`reverse-skill-router`、`apk-reverse`、`camoufox-reverse`、`wmpf-miniapp-reverse`、`firerpa`。
iOS 与 Windows 域当前为 `shallow` 降级（见 `reverse-skill-router\references\domain-registry.json`）。

## 恢复步骤

> ⚠️ **DSH 0.2.0 起光复制文件不算装好 preset**：`.agent-presets\` 目录扫描被移除，
> preset 必须由 profile patch 里的一行 `@deepseek-ai/dsh-agent-preset` 声明（内含全量
> composition）来注册，否则选择器里看不到「逆向模式」。

```powershell
# 1) 复制 preset 目录（只为留一份历史参考；DSH 0.2.0 起不读它）
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.dsh\.agent-presets\reverse" | Out-Null
Copy-Item (Join-Path $PSScriptRoot '*') "$env:USERPROFILE\.dsh\.agent-presets\reverse\" -Force

# 2) 【必需】把仓库 config\cordis.patch.yml 追加/复制进 profile 的 cordis.patch.yml。
#    里面同时带着 preset-reverse 声明（全量内联 composition）与 reverse-mcp-activator 行。
#    ⚠️ 是"追加"不是"覆盖"—— profile 里可能已有 LLM provider 等别的内容。
#    用 install.ps1 恢复时这一步自动完成。

# 3) 【必需】放 activator 插件源码（否则逆向会话没有 MCP 工具）
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.dsh\plugins\reverse-mcp-activator" | Out-Null
Copy-Item "D:\AI_python\skills_backup\plugins\reverse-mcp-activator\*" `
          "$env:USERPROFILE\.dsh\plugins\reverse-mcp-activator\" -Force
#    ⚠️ 换机器要改 config\cordis.patch.yml 里 activator 的 name（file:/// 绝对路径）
#       与各 server 的 command/args 绝对路径。

# 4) 可选：analyzer 的凭据（只在启用鉴权时需要；.env 只在启动时读取）
Add-Content "$env:USERPROFILE\.dsh\.env" "`nANALYZER_MCP_TOKEN=<token>"

# 5) 生成能力清单（persona 第一步就要读它）
pwsh -NoProfile -File "$env:USERPROFILE\.dsh\skills\reverse-skill-router\scripts\scan-capabilities.ps1"

# 6) 重启 DSH，再分别验证两个方向：
#    a. 启动日志里不该有任何 MCP 字样（这是 activator 存在的意义）
#    b. 新开一个「逆向模式」会话 → 日志出现 MCP 启动特征、会话里出现 mcp__* 工具
```

### 关于验证：`preset_probe` 已失效

旧版本这里写的是 `preset_probe validate reverse` → `mounted OK`。**该工具在本机已不存在**——
它是某个会话里动态定义的 cordis 包，重启即消失、从未落盘。现在按上面第 6 步的两个方向验证：
**权威证据是启动日志与逆向会话里真实出现的 `mcp__*` 工具**。
扫描器给出的是静态证据（清单第 1 节的「层」列）。roster 里的 `broken` 字段在 0.2.0 下
是真实审计（会点名 `never started` 的行），但仍不如上面两个方向直接。

## 不要做

- 不要编辑 DSH 部署自带的 preset（`standard` / `ptc` / `minimal` / `cordis`）：升级会覆盖，
  改坏 `cordis` 还会让 preset 创作能力失效。
- 不要把本机工具路径写进 composition：本机状态由 `$DSH_HOME\reverse\capabilities.md` 提供，
  那正是"装了新工具不用改 preset"的原因。**唯一例外**是 MCP 挂载（现在在 activator 的
  `config.servers` 里）—— 挂载本身就是路径；它们决定"怎么连上服务器"，不决定"本机有什么"。
- **不要把 MCP 行写回任何 composition**（preset 或 profile host 层）：0.2.0 下那会让它们
  随 `dsh web` 启动拉起，正是 2026-10-09 这次要修掉的问题。
- 不要把 analyzer 的 token 明文写回 `config\cordis.patch.yml`。

## 第 5 个 MCP：wireshark-mcp-lite（2026-10-08）

自研轻量单文件 MCP（`server.py`，FastMCP stdio，10 工具：`open_capture` / `analyze_packets` /
`packet_statistics` / `io_stat` / `conversation_stats` / `extract_fields` /
`analyze_protocol` / `capture_live` / `list_interfaces` / `list_protocols`），
在 activator 的 `config.servers` 里是 `serverName: wireshark` → 会话里暴露为 `mcp__wireshark__*`。
项目在 `D:\AI_python\无实际文件区\wireshark-mcp-lite\`（**不进本仓库**，重建见该目录 `HANDOVER.md`）；
前置是本机 Wireshark 的 tshark。探活先调 `list_protocols`（tshark 缺失只回 `tshark_missing`）。

## 维护

- 改 composition（现在在 `config\cordis.patch.yml` 的 `preset-reverse` 声明块里）：① 同步回
  本仓库对应段；② 重跑能力扫描器；③ 在账本 `SKILLS.md` 追加一行日志。
- 改 MCP 挂载：改的就是 `config\cordis.patch.yml` 里 activator 的 `config.servers`，
  同步回本仓库后同样记一笔。**不要**用 `preset_probe`（已不存在）。
