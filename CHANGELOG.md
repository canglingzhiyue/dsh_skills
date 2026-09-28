# 变更记录（CHANGELOG）

本文件记录**仓库层面的每一次变更**：skill 的增删改、目录结构变化、规则变化，以及为什么这么改。

**与 `SKILLS.md` 的分工**：

| 文件 | 记什么 | 更新方式 |
|---|---|---|
| `SKILLS.md` | **账本** —— 有哪些条目、优先级、来源、适配、记录日期 | 只追加，绝不重写 |
| `CHANGELOG.md` | **变更说明** —— 每次改了什么、为什么、影响哪些文件 | 每次提交前在顶部追加一条 |

**写法**：最新在最上面。每条包含「变更类型 / 内容 / 原因 / 影响文件」。
回退时配合 `git log` / `git revert` 使用。

---

## 2026-09-28 — donsetch 首次安装被代理挡住：手动补二进制 + 记录绕法

### 变更类型

运行期修复（无条目增删）：补上 donsetch 插件缺失的二进制，并把绕法记进配方。

### 内容

用户重启 DSH 后测试，`donsetch_status` 报首次安装失败：

```
state: could not reach https://github.com/dondai44423/donsetch/releases/download (network down?) while installing donsetch v4.3.6
registered tools (0): (none)
```

- **根因**：插件二进制下载器用 `node:https.request`（`dist/binary.js`），**不读** `HTTP_PROXY` / `HTTPS_PROXY` /
  `NODE_USE_ENV_PROXY`（Node 24 的该变量只作用于 `fetch`）；本机出网靠代理 `127.0.0.1:7890` → 直连 GitHub 失败。
- **修复**：用能走代理的 `fetch` 下载 `donsetch-win32-x64.tar.gz` + 官方 `.sha256`（SHA256 校验通过），
  解包后**整目录**（`donsetch.exe` + `onnxruntime.dll` + `pdfium.dll`）落位到
  `C:\Users\y\.cache\donsetch\dsh\bin\4.3.7\` —— 命中 `resolveBinary` 第 2 优先级（缓存里的最新版本），插件无需再下载。
  中途踩坑：**只放 exe 会启动即退出、无输出、exit 1**（缺 DLL），已改正。
- **预检**：对该二进制跑 stdio MCP → `initialize` = `donsetch 4.3.7`，`tools/list` = 4 个工具
  （`web_fetch` / `web_search` / `web_crawl` / `web_screenshot`），daemon 正常。
- **仍需重启一次 `dsh web`**：插件把首次 boot 的失败缓存在进程内，不热重试。

### 原因

本机是"必须走代理才能出网"的环境，而插件下载器不认代理 —— 属于**新环境迁移必踩**的坑，必须写进配方。

### 影响

- `plugins\donsetch\RECIPE.md`（新增「代理 / 受限网络下的首次安装」一节：根因、绕法、整目录要求、预检命令）
- `INSTALL.md`（donsetch 节要点补一条同款警告）
- `SKILLS.md`（追加日志一条）
- 本机：`C:\Users\y\.cache\donsetch\dsh\bin\4.3.7\`（3 个文件，19 MB + 2 个 DLL）

---

## 2026-09-28 — donsetch 用户调整：卸载全局 CLI + 新增 web-search-router 自动路由 skill

### 变更类型

插件调整（移除全局 CLI）+ 新增 1 个本地自制 skill（`web-search-router`）；无 MCP 增减。

### 内容

用户反馈后做的三点调整：

1. **卸载全局 CLI `donsetch`**（`npm uninstall -g donsetch`）：用户不需要 CLI。CLI 型操作
   （`doctor` / `login` / `keys`）改走**插件内置二进制**（`~\.cache\donsetch\dsh\bin\...\donsetch.exe`）。
   插件本体不受影响（二进制由插件自行下载管理）。
2. **新增 `web-search-router` skill**（本地自制，`$DSH_HOME\skills\web-search-router\`，即时生效）：
   多搜索工具的**自动路由表** —— 普通搜索→`web_search`（modsearch 引擎）、X→`x_search`、单页→`read_page`、
   反爬/JS 壳/PDF→`donsetch_web_fetch`、多引擎/技术向→`donsetch_web_search`、整站→`donsetch_web_crawl`。
3. **登录墙 SOP（硬性要求）**：401/403/跳转登录/付费墙 → 内置二进制 `donsetch login <域名>` 弹**真实浏览器**
   → agent **停下告知用户登录、等用户回复再继续** → cookie 入 vault → `donsetch_web_fetch` 自动带登录态重试。
   凭据只由用户在浏览器输入，agent 不碰密码/不截图/不抓键盘。
4. **常驻规则**：`$DSH_HOME/AGENTS.md` 新增「搜索与联网检索 —— 自动路由」段（每个会话默认生效）。

### 原因

用户要求：① "我就不需要那个cli了"；② "直接说用 donsetch_web_search 查…太麻烦了"，
要有几个搜索自动决定用哪个；③ "遇到需要登录的网站，donsetch 需要弹出来网页等待我登录后再继续"。

### 影响

- `plugins\donsetch\RECIPE.md`（整篇重写：CLI 卸载、内置二进制用法、登录墙流程）
- `SKILLS.md`（donsetch 行同批更正 + web-search-router 新行 + 两条补记 + 日志）
- `INSTALL.md`（donsetch 节重写 + 新增 web-search-router 节）
- `config\AGENTS.md`（同步新增常驻段）
- `skills\web-search-router\SKILL.md`（新增镜像，唯一副本）
- 本机：`D:\ProgramsDev\nodejs`（npm 全局包卸载，经包管理器）

---

## 2026-09-28 — context-mode 补上自动路由（自制 hook 适配层）+ 清理 OpenClaw 残留

### 变更类型

新增**自制适配层**（`plugins\context-mode-dsh-hook\`）+ 新增一个 **DSH hook 桥接挂载**
+ 修改**常驻规则**（`AGENTS.md` 新增一节）+ 环境清理（删除 `~/.openclaw`）。

### 内容

用户追问"这个不能自动在会话中激活使用吗？每次会话那么多文件要读，没办法一个一个去指定"，
并要求"**如果没办法自动使用的话就不要安装了，卸载掉**"，同时要求"顺便把 openclaw 也清理掉"。

**结论：自动路由能做出来，已实现。**

- **根因**：context-mode 的官方 hook 用 `hooks/core/routing.mjs` 里**写死的** `TOOL_ALIASES`
  表识别工具（只有 Claude Code 的 `Bash`/`Read`/`Grep`/`WebFetch`/`Glob`），
  DSH 的 `pwsh`/`read`/`grep` 不在表里、**没有配置扩展点** → 官方 hook 收到 DSH 工具名直接放行。
  且 DSH 的 hook 拦截缝默认是空的：`@deepseek-ai/dsh-hooks-claude-code`
  **不在 `--dump-default-config` 的默认 bundle 里**（实测默认层 586 行、零 hook 条目），
  属可选桥接插件，必须自己挂。
- **解法**：新增自制适配层 `plugins\context-mode-dsh-hook\`（**唯一副本**）——
  `dsh-pretooluse-hook.mjs` + `dsh-hooks.json`（matcher 用 DSH 真实工具名）+ `RECIPE.md`；
  在 `cordis.patch.yml` 挂 `@deepseek-ai/dsh-hooks-claude-code` 指向该配置。
- **拦截范围（保守）**：`pwsh` 命中 `curl`/`wget`/`Invoke-WebRequest`/`Invoke-RestMethod`/
  `Get-Content -Raw`/`cat`/`type`/`Select-String`/`rg`/`findstr`/`docker logs`/`kubectl logs`/
  `journalctl`/无上限 `git log`、`git diff`/`find`/`Get-ChildItem -Recurse`；
  `read` 未带 `limit`/`offset` 且 > 256 KB。**不拦** `grep`/`web_fetch`/`glob`/`edit`/`write`
  与改状态操作（构建、测试、写文件、建目录）。
  **逃生舱**：命令含 `ctx-allow`、或 `read` 带 `limit`/`offset` → 放行；hook 异常 **fail-open**。
- **常驻规则**：`$DSH_HOME\AGENTS.md` 新增「上下文保护 — 大输出走沙箱（context-mode）」一节，
  写明各场景该用哪个 `ctx_*` 工具与"仍然直接用原生工具"的边界。
  这条**不依赖重启**，装完即对所有会话生效，是 hook 之外的第二道保险。
- **OpenClaw 清理**：`C:\Users\y\.openclaw` 经清点为**纯残留壳**（仅一个 232 B 的
  `autorun_state.json`，`enabled:false` 且自 2026-03-26 创建后从未运行；无进程、无全局包、
  无计划任务、无快捷方式，共 0.2 KB）。**已走回收站删除**（可还原）。
  它正是此前把 context-mode 平台探测误导为 OpenClaw 的元凶。

### 验证

- **离线单测 7 例全部符合预期**：`Get-ChildItem -Recurse` → deny；`git status --short` → 放行；
  `curl` → deny；`curl ... # ctx-allow` → 放行；`read` 大文件无 limit → deny；
  `read` 带 `limit:100` → 放行；`grep` → 放行。
- `dsh --profile web --dump-config` 出现 `id: hooks-claude-code` + `configPath` + `defaultTimeoutMs`。
- **端到端待重启**：适配层挂上后实测一条 `Get-ChildItem -Recurse` 未被拦截，
  且当前会话 `session.v3.jsonl.zstd` 的 **hook 事件数为 0** —— 证实桥接
  "**配置在进程启动时只读一次**"，**必须重启 `dsh web`**。故 `SKILLS.md` 同条目 ④ 中
  "DSH 里没有强制路由"一句应读作"**重启前**没有"。
- 自制件 SHA256 与 `$DSH_HOME` 实件核对一致。

### 原因

用户的核心诉求是"不想每次手动指定用哪个工具"。若做不到自动，用户选择卸载；
经查 DSH 自带 hook 拦截缝 + Claude Code 桥接插件，自动路由可实现，故保留并补齐。

### 影响文件

- 新增 `plugins\context-mode-dsh-hook\`（`RECIPE.md` + `dsh-pretooluse-hook.mjs` + `dsh-hooks.json`）
- `config\cordis.patch.yml`（新增 `hooks-claude-code` 挂载；因覆盖在 bundle 层，需重启才注册）
- `config\AGENTS.md`（新增「上下文保护」一节；**该文件已同步到仓库**）
- `SKILLS.md`（追加更正与说明日志一条）
- `INSTALL.md`（context-mode 小节新增「自动路由」段与重建步骤）
- `install.ps1`（待办补自制件落位步骤）
- `CHANGELOG.md`（本条）

### 未做 / 不做

- **未接** `SessionStart` 上下文注入与 `PostToolUse` 会话捕获：依赖 context-mode 自己的
  会话/转写格式（DSH 的 `transcript_path` 恒为空、会话日志是 zstd 压缩的 `session.v3.jsonl.zstd`），
  且官方注入块是 Claude Code 专属工具名 —— 改由常驻 `AGENTS.md` 规则覆盖。
- 未跑 `npm approve-scripts`（先前已确认原生产物在位、无实际影响）。
- 未卸载 context-mode（用户的条件是"做不到自动就卸载"，而自动已实现）。

### 顺带记录

- 本次记账期间**另一个会话同时提交了 donsetch 条目**（commit `b095b3d`，已 push）。
  本条目所有改动按**追加**方式落在其后，未覆盖对方内容。

## 2026-09-28 — 安装 donsetch（DSH 插件 + 可选全局 CLI）

### 变更类型

新增 **DSH 插件**（第 5 个：`@dsh-external/donsetch` ← `github:dondai44423/donsetch-dsh`）；
另有同源全局 CLI 工具 `donsetch`（npm 包，非 DSH 挂载）。

### 内容

用户要求安装 <https://github.com/dondai44423/donsetch>，并说明"这是什么、怎么用"、
"装完不要在当前文件夹留文件"。

- **它是什么**：DonSeTch —— Rust 单二进制的 Web 研究工具（fetch / search / crawl / screenshot / PDF OCR），
  给 AI agent 用；零 API key、零账号、全本地自研（Chrome 真实 TLS 指纹 + 自研 HTTP/2 + 无头浏览器绕反爬 +
  本地 ONNX 语义重排）。donsetch-dsh 插件壳把它注册为 DSH 进程内原生工具
  `donsetch_web_fetch` / `donsetch_web_search` / `donsetch_web_crawl` / `donsetch_status`。
- **为什么装两式（用户拍板「两个都装」）**：全局 CLI 立即可用 + doctor 诊断；DSH 插件给 agent 用
  （需重启生效）。
- **与 modsearch 的区别**（用户已装 `@liustack/modsearch`）：modsearch 是云端 Firecrawl keyless 驱动的
  轻量搜索（npm 包小、1000 免费额度/月、MIT）；donsetch 是本地的重工具（自有传输/提取/PDF/搜索聚合/爬虫
  引擎，能绕反爬、OCR、省 token、续传爬虫、登录会话、BYOK，AGPL-3.0）。两者工具名前缀不同、可共存。
- **安装**：`npm install -g donsetch`（v4.3.6，orc+rerank features，二进制已落位）+ 
  `dsh plugin --profile web add github:dondai44423/donsetch-dsh`（5.2 秒，未触发 allowBuilds）。
  全部落在工作区之外（全局 npm 目录 + `$DSH_HOME`），`D:\AI_python\无实际文件区` 复核无新增。
- **验证**：`donsetch doctor` 全绿（经内网代理 127.0.0.1:7890，JA4 = Chrome 指纹）；`donsetch --version` 正常。
- **影响文件**：`plugins\donsetch\RECIPE.md`（新增）、`SKILLS.md`（表格行 + 「当前插件共 5 个」补记 + 日志）、
  `INSTALL.md`（新增 donsetch 小节）、`install.ps1`（待办清单补一条）、`config\profile\package.json`（同步）。

### 原因

用户要求安装并记录；该插件属「非 DSH 自带」，按账本规则纳入三类备份范围。

### 影响

- 插件在 bundle 层：**重启 `dsh web` 后**会话出现 `donsetch_*` 工具。
- `config\profile\package.json` 需保持与 profile 实际一致（dependencies + bundles 各多一条）。

---

## 2026-09-28 — 新增第四个 MCP 挂载：context-mode（上下文窗口优化）

### 变更类型

新增 **MCP 挂载**（既不是 skill 也不是插件）；无 skill / 插件增减。

### 内容

用户要求安装 <https://github.com/mksglu/context-mode>，并要求说明"这是什么、怎么用"，
且**装完不要在会话工作区留文件**。

- **它是什么**：MCP server，把大块工具输出（curl / 日志 / 网页 / Playwright 快照 / 几 MB JSON）
  留在沙箱子进程里处理，只回传结论（官方基准 315 KB → 5.4 KB）；另带 SQLite 会话记忆
  （对话压缩后可续）与 FTS5 知识库检索。共 **11 个工具**：`ctx_execute` / `ctx_execute_file` /
  `ctx_index` / `ctx_search` / `ctx_fetch_and_index` / `ctx_batch_execute` +
  `ctx_stats` / `ctx_doctor` / `ctx_upgrade` / `ctx_purge` / `ctx_insight`。
- **安装**：`npm install -g context-mode` → **1.0.169**（Elastic-2.0，前置 Node ≥ 22.5），
  落在 `D:\ProgramsDev\nodejs\node_modules\context-mode` —— **在工作区之外**，满足用户要求。
  npm 的 `allow-scripts` 警告未造成影响：`better_sqlite3.node` 已在位，`doctor` 的 FTS5 自检 PASS。
- **挂载**：`config\cordis.patch.yml` 新增 `id: mcp-context-mode` / `serverName: context-mode`，
  命令 `node D:\ProgramsDev\nodejs\node_modules\context-mode\cli.bundle.mjs`（不用 `.cmd` shim ——
  Windows 下 spawn `.cmd` 需要 shell），`toolCallTimeoutMs: 300000`，并显式设
  `CONTEXT_MODE_DIR=C:\Users\y\.dsh\context-mode`。
- **为什么必须设 `CONTEXT_MODE_DIR`**：它自己做平台探测，**看到 `~/.openclaw\` 就判成 OpenClaw**
  （用户 2026-03 装过 OpenClaw，属预先存在的目录），否则存储会落到 `~/.openclaw/context-mode/`。
- **平台限制**：DSH 不在其官方 17 平台清单内 → 11 个 MCP 工具可用、但**没有 hook 层强制路由**
  （官方对比：有 hook ≈ 省 98%，无 hook ≈ 省 60%）。
- **验证**：stdio 探针 `initialize` + `tools/list` → 11 个工具；`context-mode doctor` → Server test PASS、
  FTS5 / SQLite PASS；`dsh --profile web --dump-config` 出现该条目。

### 原因

上下文窗口是长会话的主要瓶颈；该工具纯本地（无遥测、无账号），与本机既有的"在大输出上进沙箱"用法一致。

### 影响文件

- `config\cordis.patch.yml`（新增挂载条目，已与 profile 同步）
- `SKILLS.md`（表格加 1 行 + 「当前 MCP 共 4 个」补记 + 日志）
- `INSTALL.md`（MCP 节 3 → 4 个 + 表格加 1 行 + 新增「context-mode MCP」小节）
- `install.ps1`（待办清单补一条：新环境需 `npm install -g context-mode`）
- `CHANGELOG.md`（本条）

### 未做 / 不做

- 不跑 `npm approve-scripts`（实测无影响，原生产物已在位）。
- 不备份 npm 全局包本身与 `CONTEXT_MODE_DIR` 下的 SQLite 数据（后者是运行期会话数据）。

### 顺带记录

- 本次同步时发现 `config\settings.yaml` 已被**用户自己**修改（默认模型由 `ds-1zhe/deepseek-flash`
  改为 `claudex/deepseek-v4.1-flash`，并移除 `ds-1zhe` provider 与其两个模型定义）——
  按「`config\` 任何文件被改都要重新同步」的规则一并备份，非本次安装所致。
- 本次第二次踩到 `dev-hygiene` 的 `Remove-ToRecycleBin.ps1` **空目录缺陷**
  （`Set-StrictMode -Latest` 下对空集合取 `Measure-Object -Sum` 的 `.Sum` 抛"找不到属性 Sum"）——
  仍按上次做法用同款 `Microsoft.VisualBasic.FileIO.FileSystem` 回收站 API 完成删除，**脚本未改动**。

## 2026-09-26 — 新增第三个 MCP 挂载：Hex-Rays 官方 IDA MCP（`ida-mcp`）

### 变更类型

新增 **MCP 挂载**（既不是 skill 也不是插件）+ 一处环境改动（IDA 的 Python 环境）。

### 内容

用户要求安装 <https://github.com/HexRaysSA/ida-mcp>（官方 Hex-Rays IDA MCP Server），
并给出 IDA 安装路径 `D:\ProgramsDev\IDA Professional 9.4`。

- **挂载**：`config\cordis.patch.yml` 新增 `id: mcp-ida` / `serverName: ida` 条目，
  命令 `uvx --exclude-newer=1s ida-mcp stdio --agent=dsh`，`toolCallTimeoutMs: 600000`。
  本 profile 是 `patchReload: live` —— **实测无需重启 DSH**：改完进程列表随即出现该 uvx 进程，
  会话工具列表里也随即出现 `mcp__ida__*`（6 个工具：open_database / execute_python / reference /
  list_databases / save_database / close_database）。
- **运行时**：`uvx` 直接跑 PyPI 上的 `ida-mcp`（缓存环境 7 个包，含 `idapro`），
  **没有需要重建的独立目录**；它依赖本机 IDA 9.4 的 idalib，路径早已写在
  `%APPDATA%\HexRays\IDA Pro\ida-config.json`（`hcli` 自检报 `idalib: active`），**不需要设 `IDADIR`**
  （官方明确警告不要设全局 `IDADIR`，会干扰 IDA GUI）。
- **外部前置（可选）**：IDA GUI 插件 —— `uvx ida-hcli plugin install 'ida-mcp@https://github.com/hexrayssa/ida-mcp'`
  → `Installed plugin: ida-mcp==20260924.0.3`，落在 `%APPDATA%\HexRays\IDA Pro\plugins\ida-mcp\`，
  **装完需重启 IDA** 才生效。
- **环境改动**：原先 IDA 用的是 uv 托管的全局 CPython 3.13（PEP 668 外部管理、非 venv），
  hcli 拒绝往里装 `ida-nexus`；按官方解法跑 `ida-hcli ida python create-environment` →
  建 `%APPDATA%\HexRays\IDA Pro\venv`（3.13 + pip，已装 `ida-nexus 0.13.0` / `ida-domain 0.5.1` /
  `idapro 0.0.10`）并设置**用户级**环境变量 `IDAPYTHON_VENV_EXECUTABLE` 指向它。

### 原因

用户正在做 IDA 逆向（工作区 `tb_10.41.0.1` 里有 `libsgmainso-6.6.241002.so` 的 ida_recon 流程），
需要一条让 DSH 会话直接驱动 IDA 做反编译 / 交叉引用 / 类型恢复的通路。

### 验证（两层，都实测）

1. 独立 MCP 探针：`initialize` 604 ms → `open_database` 4.4 s 返回 `backend: idalib` →
   `execute_python` 得 `0x140001000`–`0x140010000` / **172 个函数**；
2. **经 DSH 自己的 MCP 客户端**重复一遍，结果一致（`dsh→mcp→idalib ok`）——
   即"会话 → DSH → MCP → idalib → IDA"全链路通。

样本是临时复制的 45 KB PE，验证后已 `close_database` 并清理 `%TEMP%`。

### 踩到的三个坑（已写进 `INSTALL.md` 的「ida MCP」小节）

1. **`ida-hcli` 插件名歧义**：社区插件仓库里有个同名第三方 `IDA-MCP@github.com/captain-ai-hub/ida-mcp`，
   直接给 URL 会报 `ambiguous plugin reference: 'ida-mcp' matches 2 plugins`
   → 必须写全限定 `ida-mcp@https://github.com/hexrayssa/ida-mcp`。
2. **hcli 不读 git 的代理配置**：直连 GitHub 报 `[WinError 10054] 远程主机强迫关闭了一个现有的连接`
   → 显式给 `HTTP_PROXY` / `HTTPS_PROXY`（本机 `http://127.0.0.1:7890`），pip 侧另加清华源。
3. **IDA 的 Python 是 PEP 668 外部管理**（uv 托管 CPython 3.13，非 venv）→ 必须先
   `ida-hcli ida python create-environment`，否则插件依赖装不进去。

### 影响文件

- `config\cordis.patch.yml`（第三个 MCP 条目；SHA256 与 profile 一致 `E9C1C0B1…`）
- `SKILLS.md`（+1 行表格 + 1 行日志）
- `INSTALL.md`（MCP 节：表格 2 → 3 行；新增「ida MCP」小节）
- `install.ps1`（待办清单补 ida MCP 一条）
- `CHANGELOG.md`（本条目）
- 仓库之外：`~/.dsh/profiles/web/cordis.patch.yml`、`%APPDATA%\HexRays\IDA Pro\plugins\ida-mcp\`、
  `%APPDATA%\HexRays\IDA Pro\venv\`、用户级环境变量 `IDAPYTHON_VENV_EXECUTABLE`

---

## 2026-09-26 — 备份范围扩展到 skill + MCP + 插件 + 环境配置；新增一键恢复

### ① 环境配置纳入 `config/`（此前完全没备份）

用户的目标是"新环境把仓库地址给我就能全部配好"，而此前仓库**只有 skill 内容和插件配方**，
缺了让配置真正生效的那几样。新增 `config\`，与 `$DSH_HOME` **逐文件哈希核对一致**：

| 文件 | 大小 | 作用 | 为什么必须有 |
|---|---|---|---|
| `AGENTS.md` | 7,755 B | 常驻规则（skill 记账 + dev-hygiene 红线） | 没有它，新环境不知道"删除走回收站 / shell 一律 pwsh 7 / Python 一律 uv / 必须 HANDOVER"这些红线，`dev-hygiene` 形同虚设 |
| `settings.yaml` | 967 B | DSH 设置（模型 provider、UI） | **无明文密钥**（用 `apiKeyEnv` 引用），可安全备份 |
| `cordis.patch.yml` | 2,132 B | **MCP 挂载** | 两个 MCP（camoufox / jadx）只活在这里 |
| `profile/package.json` | 583 B | 插件依赖 + `dsh.profile.bundles` | 少了 bundles 条目插件不会被加载 |
| `profile/pnpm-workspace.yaml` | 419 B | `allowBuilds` 键 + `minimumReleaseAgeExclude` | 丢了它，git 依赖的插件装不上 |
| `profile/cordis.yml` | 223 B | profile 根 | 配套 |

### ② 补记 MCP —— 发现并填上账本缺口

清点时发现 **camoufox MCP 与 jadx MCP 从未被记账**：旧规则的"范围"只管 skill 和 npm 插件两类，
而 MCP 是 `cordis.patch.yml` 里的一条 `@deepseek-ai/dsh-mcp-client` 配置，**哪一类都不算** ——
后果就是它根本不会迁移。

- 账本新增 **2 行**（`camoufox` / `jadx`，均 P2 独立类）
- `skills-inventory` **范围从两类扩为三类**，并新增「MCP 怎么备份」一节
- `AGENTS.md` 常驻规则同步

两个必须记下来的点：jadx MCP 是 **`failOnStartupError: false`** —— **启动失败静默无错**；
且它需要 **JADX-GUI 装好 `jadx-ai-mcp` 插件并保持开启**这个外部前置。
这两点不写下来，新环境必然踩坑。

### ③ 新增 `install.ps1` 一键恢复脚本

自动部分：前置检查（pwsh/git/node/pnpm/uv/dsh）→ 备份现有配置 → 恢复 skill（幂等，哈希一致则跳过）→
恢复常驻规则与 DSH 设置 → 恢复 MCP 挂载与 profile 配置 → 装 4 个第三方插件 → 打印**必须人工完成**的待办。
含中文，故保存为 **UTF-8 with BOM**；Parser 语法检查 0 错误；`-DryRun` 实测通过。

### ④ 结构变更

- 新增 `config\`、`install.ps1`
- `local\` **退役**：`local\skill\` 被 `skills\` 全量镜像取代（0.23 MB 入回收站）
- `local\AGENTS.md.bak-20260915` → `archive\`
- `snapshots\` **退休**：不再新增 zip，已进 `.gitignore`（本地历史留作过渡）

### 影响文件

新增 `config/**`（6 个）、`install.ps1`；重写 `README.md`；
更新 `CHANGELOG.md`、`.gitignore`、`SKILLS.md`（+2 行 MCP + 日志）、
`INSTALL.md`（头部一键路径 / 装法 / 记账规则 / 新增 MCP 一节）、
`skills/skills-inventory/SKILL.md`（规则重写）、`$DSH_HOME/AGENTS.md`（常驻规则重写）；
删除 `local/**`。

---

## 2026-09-26 — 建立仓库；firerpa 安装、实测与融合

### ① 仓库建立（结构变更）

**做了什么**

- 把 `D:\AI_python\skills_backup` 初始化为 git 仓库，`main` 分支，remote 指向
  `https://github.com/canglingzhiyue/dsh_skills.git`（**私有**）。
- 新增 **`skills/`** —— `$DSH_HOME/skills`（`C:\Users\y\.dsh\skills`）下**全部 7 个 skill 的完整内容**，
  65 文件 / 1,020 KB，与源目录**逐文件 SHA256 一致**。
- `local\plugin\` → **`plugins\`**（4 个插件配方：`dsh-think-zh`、`modsearch`、`dsh-ding`、`dsh-pentest`）。
- `local\skill\` → **由 `skills\` 取代**；`local\` 整体退役（经 `dev-hygiene` 回收站脚本，0.23 MB）。
- `local\AGENTS.md.bak-20260915` → **`archive\`**（追溯常驻规则的历史版本）。
- 新增 `README.md`（仓库说明 + 恢复到新环境的完整流程）、`CHANGELOG.md`（本文件）、`.gitignore`。
- **`snapshots\` 退休**：不再新增按日 zip，已加入 `.gitignore`（本地历史文件留作过渡，可随时删）。

**为什么**

用户要求用 GitHub 仓库取代按日 zip 快照。**git 历史严格强于 zip**：能 diff、能定位是哪次改动引入的问题、
能按文件回退，而且不占本地磁盘。原先 zip 的"改动前状态"作用，由「上一次 commit」天然承担。

**另一个收益**：`skills/` 存**完整内容**（含 firerpa 的上游 `client/`、`llms-full.txt` 等），
所以恢复流程从原来的「拉上游 → 盖适配层 → 建环境」简化为「clone → 复制 skills → 建环境」。

**影响文件**：`.gitignore`、`README.md`、`CHANGELOG.md`、`skills/**`（新增 65 文件）、
`plugins/**`（迁移 4 文件）、`archive/**`；删除 `local/**`。

---

### ② 新增 skill：`firerpa`（Android 自动化）

**做了什么**

- 来源 `https://github.com/firerpa/skills`（该仓库**只有 `firerpa/` 一个 skill**）。
  上游 frontmatter 已是 DSH 原生，**整份复制**即可，无需改造。
- 建配套 uv 环境 `D:\AI_python\firerpa\.venv`（uv 托管 CPython 3.12.13 + `lamda==10.8`，
  共 15 包 / 160 MB / 983 文件，清华源）。**该环境不入仓库**（PyPI 可重装）。
- 记账：`SKILLS.md` 追加一行（**P2 独立类**）；`INSTALL.md` 追加一节。

**设备端实测（用户授权装 firerpa.apk）**

在用户的**雷电模拟器 9** 上装服务端并端到端跑通：

| 项 | 实测值 |
|---|---|
| 设备 | `emulator-5562`（**非默认 5555**） |
| 架构 / 系统 | `x86_64` / Android 9（SDK 28）/ 型号伪装 `GM1910` |
| root | Magisk 可用（`uid=0 context=u:r:magisk:s0`） |
| 服务端 | 包名 `com.firerpa`，版本 10.8，进程 `lamda`，监听 `65000` |
| **服务目录** | **`/data/89frma`（随机化，不是文档里的 `/data/server`）** |

**三条关键实测结论**（都写进了 `skills/firerpa/SKILL.md`）：

1. **PC 直连模拟器 65000 不通** —— `172.16.1.4` 是 NAT 网段（`TcpTestSucceeded=False`）→
   必须 `adb forward tcp:65000 tcp:65000` + `--host localhost`。
2. **两个 adb 互杀** —— 系统 `D:\ProgramsDev\adb\adb.exe` 与雷电自带 `D:\leidian\LDPlayer9\adb.exe`
   进程同时在跑、抢 5037 端口。
3. `d.current_application()` 返回 `Application:pkg:uid@pid`，而 CLI `app-current` 只打印纯包名。

**验证**：`server-info` / `device-info` / `dump`（73 节点含 resourceId）/ `screenshot` /
端到端脚本（启停 `com.android.settings`）全部通过。

---

### ③ `firerpa` 的 `SKILL.md` 融合（结构变更）

**做了什么**

最初把本机内容写成独立的 `references\知识库.md`，靠 `SKILL.md` 里的「Step 0」二次引导读取。
随后**用户拍板取消独立文件，全部融合进 `SKILL.md`**：

- 融合版 `SKILL.md` = **992 行 / 54,460 字节**，**上游原文一字未删**
  （Purpose and boundaries / Target-app discipline / Source of truth / Verification standard /
  Interaction rules / Connection and app prechecks / Hard rules / Forbidden API guesses /
  Allowed common APIs / Proto field access rules / Watcher rules / User-control boundaries /
  Authoring display and OCR policy / Pre-output checklist 全部原样保留），
  本机内容按主题插入。结构：`§0 铁律 → §1 架构 → §2 本机环境实测 → §3 首次接入 SOP →
  §4 每次干活 SOP（含上游规范 4.1–4.11）→ §5 CLI 26 命令 → §6 Python API → §7 任务配方 →
  §8 排障 → §9 安全与反检测 → §10 卸载还原 → §11 资料优先级 → §12 交付前检查清单 → §13 维护提醒`。
- 独立 `references\知识库.md` **退役**（入回收站）；`references\` 只留上游的
  `reference.md` + `llms-full.txt`。
- 「Step 0 强制读知识库」两段补丁**因融合而失去意义，一并移除**（它们的前提就是"内容在别处"）。
- skill 目录回到 **36 文件**（与上游文件数一致 —— 本机内容全在 `SKILL.md` 内，不新增文件）。

**为什么**

独立文件必须靠二次引导才会被读，是**两次动作**；并进 `SKILL.md` 后**加载 skill 一次即全部到位**，
不再依赖 agent 是否老实去读第二个文件。

**代价（已知并接受）**：`SKILL.md` 变长，加载一次约 1.5 万 token 常驻 context。

---

### ④ 规则变更：zip 快照 → git 提交

**做了什么**

- `skills-inventory` skill（P0 治理类）的「按日快照」一节与实际不符了 ——
  由「每次动账本前打 `snapshots\ledger-YYYY-MM-DD.zip`」改为
  **「每次改完提交并推送到本仓库」**，回退手段由「解压当日 zip」改为
  「`git log` + `git revert` / `git checkout <commit> -- <path>`」。
- 同步更新 `$DSH_HOME/AGENTS.md` 的常驻规则（原「Snapshot the ledger by date before every change」一条）。
- `skills-inventory` 里 `local\skill\` / `local\plugin\` 的路径改为 `skills\` / `plugins\`。

**为什么**

仓库建立后，zip 快照成为冗余机制：同一件事有两个回退来源（zip 与 git），容易不一致。

---

### ⑤ 环境注记（非仓库内容，但影响可复现性）

- 本机 **shell 的 TLS 是坏的**：`Invoke-WebRequest` 报 `Authentication failed`、
  `curl.exe` 报 `schannel: SEC_E_NO_CREDENTIALS`、`git clone` 曾报
  `cannot create standard input pipe for remote-https: Permission denied`（沙箱管道边界）。
  **可行通道**：python 的 `urllib.request`（用于下载）。
- git 全局配置了代理 `127.0.0.1:7890`，以及 **`http.sslVerify=false`**
  （推送时 git 会打 TLS 校验禁用警告）。**这是安全弱点，待用户决定是否收紧**。
- 本机路径含中文的会话工作区（`D:\AI_python\无实际文件区`）**不能放 firerpa 脚本** ——
  `import lamda` 会因 `grpc_tools.protoc` 的 `path.encode("ascii")` 崩 `UnicodeEncodeError`。
  已知并记录在 `skills/firerpa/SKILL.md` §8.1。
