# reverse —— 「逆向模式」agent preset（第四类资产）

本目录是 preset `reverse` 的整份副本，恢复方式见 `INSTALL.md` 的「reverse（逆向模式）」一节。

## 这是什么

一个 **DSH agent preset**，在会话选择器里显示为「逆向模式」。它不是 skill、不是 DSH 插件
—— 这两类都不覆盖它：

| 资产类型 | 住哪 | 换机器会自己回来吗 |
|---|---|---|
| skill | `$DSH_HOME\skills\<name>\` | 会（本仓库 `skills\` 镜像） |
| DSH 插件 | profile 的 `package.json` / `bundles` | 会（`install.ps1` 装） |
| MCP 挂载 | **profile patch 的 `preset-reverse` 声明块（内联 composition）**（2026-10-02 起在 preset；2026-10-09 起随 0.2.0 适配改为内联） | 会 —— 装 preset 即带上（DSH 0.2.0 起必须同时带 `preset-reverse` 声明块，否则选择器里看不到） |
| **agent preset** | `$DSH_HOME\.agent-presets\<id>\` | **不会** —— 只有本目录这份副本能带回去 |

## 内容

| 文件 | 说明 |
|---|---|
| `agent.cordis.yml` | composition：DSH 自带 `standard` 骨架 + 逆向 persona（身份、默认已授权、开工五步、验收骨架、脚本分级、增删自检、事实纪律）+ **末尾 5 段 MCP 挂载**（见下；2026-10-08 起是 5 段，新增自研 `wireshark-mcp-lite`） |
| `preset.yml` | 显示名与描述（会话选择器里显示「逆向模式」） |

## 这 5 个 MCP 为什么在这里（2026-10-02 起 4 个，2026-10-08 起 5 个）

`mcp-camoufox-reverse` / `mcp-jadx` / `mcp-ida` / `mcp-anything-analyzer` 原本挂在 profile 的
host 层，后果是 `dsh web` **一启动就 spawn 全部 MCP 服务器**：实测 10 个常驻进程、约 300 MB，
且 `dsh-mcp-client` 的 `apply()` 会**同步等待「连接 + `tools/list`」完成**才让条目激活
（它的 Config schema 里没有懒加载字段，启动与发现超时又直接继承 MCP SDK 的 60 s）
—— 启动卡顿由此而来。

**preset 曾是 DSH 里唯一的惰性挂载点**（`dsh-agent-presets` 的 "reading never mounts"：
读文件不会挂载，只有新会话真的选中才 compose），所以搬到这里就实现了按需：
`dsh web` 启动与普通会话零 MCP 进程，只有新开「逆向模式」会话才拉起它们。

> ⚠️ **DSH 0.2.0-rc.2 起按需语义已失效（2026-10-09 实测）**：registry 改为**启动期急切挂载**
> 所有已声明 preset（roster 上先挂好，会话选择时直接复用）—— `dsh web` 启动即拉起末尾
> 5 个 MCP 服务器（全部 `failOnStartupError: false`，连不上只是静默少工具，不影响启动）。
> 若连回旧语义（选中才挂载）值得争取，属上游 issue；当前形态与官方四个 preset 完全一致。

代价（明确的取舍）：普通会话不再有 `mcp__camoufox__*` / `mcp__jadx__*` / `mcp__ida__*` /
`mcp__analyzer__*` / `mcp__wireshark__*`；开逆向会话时要等服务器连上（camoufox 冷启动最慢）。

**生命周期**：preset 子树归它的 agent 所有（`dsh-agent-presets/mount` 的 `PresetTree`），
agent 被拆掉时整棵子树一起 dispose —— 这些 MCP 服务器**随会话结束而退出**，
不会变成新的常驻空闲进程。代价是每个逆向会话有自己的一份服务器进程
（并发的逆向会话 = 多份），工具也随会话存亡。

**挂载失败不会拦住会话**：5 行的 `failOnStartupError` 都是 `false`
（camoufox / ida 用 schema 默认值，jadx / analyzer / wireshark-lite 显式写），所以服务器连不上时
只会**静默少掉工具**，不会让逆向会话创建失败 —— 用工具前先按能力清单探活。
（能让会话创建失败的只有 composition 语法/结构错误、行引用的包不存在这类硬错误。）

**它们仍然不需要 `isolate` realm** —— 只往 `ctx.tools` 注册工具、不 `provide` 服务，
和上面的 `tool-fs` / `tool-pwsh` 同类。**不要**给它们套 group。

**analyzer 的 token 不在这个文件里**：composition 只写 `!!js process.env.ANALYZER_MCP_TOKEN`，
真值在 `$DSH_HOME\.env`（Harness-home 专属层，明确不随任何仓库传播）。这是刻意的 ——
本目录要进私有备份仓库，而凭据永不备份。该变量只在 DSH 启动时读取，改完要重启。

## 依赖（必须先装）

`reverse-skill-router`、`apk-reverse`、`camoufox-reverse`、`wmpf-miniapp-reverse`、`firerpa`。
iOS 与 Windows 域当前为 `shallow` 降级（见 `reverse-skill-router\references\domain-registry.json`）。

## 恢复步骤

> ⚠️ **DSH 0.2.0 起多了一步**：`.agent-presets\` 目录扫描被移除，光复制文件**不够**了 ——
> 还必须在 profile 的 `cordis.patch.yml` 里加一行 `@deepseek-ai/dsh-agent-preset` 声明，
> 否则选择器里看不到「逆向模式」。声明行的内容在仓库 `config\cordis.patch.yml`（本机实际
> 生效版见 `profiles\web\cordis.patch.yml` 末尾的 `preset-reverse` 段）。

```powershell
# 1) 复制回 preset 根（MCP 挂载随本目录一起到位）
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.dsh\.agent-presets\reverse" | Out-Null
Copy-Item (Join-Path $PSScriptRoot '*') "$env:USERPROFILE\.dsh\.agent-presets\reverse\" -Force

# 2) 【DSH 0.2.0 起必需】把仓库 config\cordis.patch.yml 里的 preset-reverse
#    声明块（内含**全量内联**的 composition）追加进 profile 的 cordis.patch.yml。
#    ⚠️ 是"追加"不是"覆盖"—— profile 里可能已有 LLM provider 等别的内容。
#    用 install.ps1 恢复时这一步自动完成（它整体复制 config\cordis.patch.yml）。
#    ⚠️ 2026-10-09 起是内联形态（与官方 standard.patch.yml 同构）：不再引用
#    file:/// 路径，因此无需改路径；上面第 1 步复制的 agent.cordis.yml 只作
#    历史参考，DSH 不会读它（文件头有停用说明）。

# 3) 可选：analyzer 的凭据（只在启用鉴权时需要；.env 只在启动时读取）
Add-Content "$env:USERPROFILE\.dsh\.env" "`nANALYZER_MCP_TOKEN=<token>"

# 4) 生成能力清单（persona 第一步就要读它）
pwsh -NoProfile -File "$env:USERPROFILE\.dsh\skills\reverse-skill-router\scripts\scan-capabilities.ps1"

# 5) 重启 DSH（preset 声明只在启动期装载），再新开一个会话，预设选「逆向模式」，
#    确认 persona 与工具列表（含 mcp__* 工具）
```

### 关于验证：`preset_probe` 已失效

旧版本这里写的是 `preset_probe validate reverse` → `mounted OK`。**该工具在本机已不存在**——
它是某个会话里动态定义的 cordis 包，重启即消失、从未落盘。现在按上表第 3、4 步验证：
扫描器给出静态+半动态证据（清单第 1 节的「层」列应显示 `preset:reverse`），
**真正的权威验证是新开会话** —— 挂载失败会让会话创建直接失败并回滚，并指名是哪一行。
roster 里的 `broken: false` **不算验证**（只做形状检查）。

## 不要做

- 不要编辑 DSH 部署自带的 preset（`standard` / `ptc` / `minimal` / `cordis`）：升级会覆盖，
  改坏 `cordis` 还会让 preset 创作能力失效。
- 不要把本机工具路径写进 composition：本机状态由 `$DSH_HOME\reverse\capabilities.md` 提供，
  那正是"装了新工具不用改 preset"的原因。**唯一例外**是末尾那 5 段 MCP 挂载 ——
  挂载行本身就是路径；它们决定"怎么连上服务器"，不决定"本机有什么"。
- 不要把 analyzer 的 token 明文写回 `agent.cordis.yml`。

## 第 5 个 MCP：wireshark-mcp-lite（2026-10-08）

自研轻量单文件 MCP（`server.py`，FastMCP stdio，10 工具：`open_capture` / `analyze_packets` /
`packet_statistics` / `io_stat` / `conversation_stats` / `extract_fields` /
`analyze_protocol` / `capture_live` / `list_interfaces` / `list_protocols`），
挂载行为 `mcp-wireshark-lite`（`serverName: wireshark` → `mcp__wireshark__*`）。
项目在 `D:\AI_python\无实际文件区\wireshark-mcp-lite\`（**不进本仓库**，重建见该目录 `HANDOVER.md`）；
前置是本机 Wireshark 的 tshark。探活先调 `list_protocols`（tshark 缺失只回 `tshark_missing`）。

## 维护

改完 composition：① 重跑能力扫描器（见上）；② 整份复制回本目录并核对 SHA256；
③ 在账本 `SKILLS.md` 追加一行日志。**不要**用 `preset_probe`（已不存在）。
改完 profile patch 的 `preset-reverse` 声明行：同步回仓库 `config\cordis.patch.yml` 对应段。
