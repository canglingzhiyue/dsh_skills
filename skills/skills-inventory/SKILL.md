---
name: skills-inventory
description: >
  Append-only ledger of the skills, DSH plugins and MCP mounts installed in this environment, plus the
  install guide and a one-shot restore script for a new machine. Records source, P0/P1/P2 priority and
  adaptation notes; mirrors all skill content into a private git repo. Use after
  installing/updating/modifying/removing a recorded item, or when the user says "备份 skill 清单",
  "记录装了哪些 skill", "迁移 skill 到新环境", "skill inventory", /skills-inventory. Never records
  items the user did not ask for.
---

# Skills Inventory

**账本目录：`D:\AI_python\skills_backup`** ← 本机路径。**它同时是一个私有 git 仓库**，
remote = `https://github.com/canglingzhiyue/dsh_skills.git`。换机器时改这一行（见「账本目录怎么定」）。

**范围：这套环境里凡是"不是 DSH 自带"的都算** —— 第三方来源装的、用户手动装的、你（AI）帮他装的，
都要记、都要备份。**四类东西**分别处理：

- **skill** —— `$DSH_HOME/skills` 下的一个目录；
- **DSH 插件** —— 某个 profile 的 `dependencies` / `dsh.profile.bundles` 里**非 `@deepseek-ai/*`** 的条目；
- **MCP server 挂载** —— `@deepseek-ai/dsh-mcp-client` 的一条挂载行，**可以挂两层**：
  profile 的 `cordis.patch.yml` 里的 `insert` 条目（**profile 层** = 常驻，harness 启动即拉起），
  或 agent preset 的 `agent.cordis.yml` 里的普通行（**preset 层** = 按需，只有新会话选中该 preset
  才 compose —— preset 是 DSH 里唯一的惰性挂载点）。**层决定进程何时启动，不决定算不算资产。**
  （它既不是 skill 也不是 npm 插件，但同样是"这台机器的资产"，不记就迁移不走。）
- **agent preset** —— `$DSH_HOME\.agent-presets\<id>\` 下的一个目录（**用户自己写的**那些）。
  它**不在任何 profile 的 `package.json` / `bundles` 里**，所以换机器会**凭空消失** —— 备份形态是
  `presets\<id>\` 下的整份 composition 副本（见「agent preset 怎么备份」一节）。
  **部署自带的 preset**（`standard` / `ptc` / `minimal` / `cordis`）与**第三方包内的 preset**
  （如 `@howmp/dsh-pentest` 的 `pentest`）都不算、不记、不备份。

**不记、不备份**：DSH 自带的那批 bundle、环境预装的工具（npm / pnpm / node / corepack / uv …）、
以及根本不是 DSH skill / 插件 / MCP / preset 的普通 npm 包。**拿不准某样东西算不算"自带" → 问用户，不要擅自记或擅自排除。**

## 仓库结构

| 路径 | 内容 |
|---|---|
| `skills\<name>\` | **全部 skill 的完整内容** —— `$DSH_HOME/skills` 的**全量镜像**（逐文件 SHA256 一致） |
| `SKILLS.md` | **账本**：装过什么、优先级、来源、适配。**只追加，绝不重写**（表格结构变更例外，须在日志说明） |
| `INSTALL.md` | **安装说明**：新环境照着它**按优先级顺序**一节一节装。它是"当前说明"，有错就当场改对（不保旧版） |
| `plugins\<name>\RECIPE.md` | 已记账插件的**配方**；插件若是自己写的，连源码一起放这里 |
| `presets\<id>\` | 已记账 **agent preset** 的**整份副本**：`agent.cordis.yml` + `preset.yml` + `README.md`（见「agent preset 怎么备份」一节） |
| `config\` | **环境配置**：`AGENTS.md`（常驻规则）、`settings.yaml`、`cordis.patch.yml`（profile 补丁层；**只有 profile 层 / 常驻的 MCP 挂载在这里** —— preset 层的 MCP 随 `presets\<id>\` 走）、`profile\`（`package.json` / `pnpm-workspace.yaml` / `cordis.yml`） |
| `install.ps1` | **一键恢复脚本**：skill + agent preset + 常驻规则 + DSH 设置 + MCP 挂载 + profile 配置 + 插件安装 |
| `README.md` / `CHANGELOG.md` | 仓库说明 / **变更说明**（每次改了什么、为什么、影响哪些文件） |
| `archive\` | 历史归档（如 `AGENTS.md` 的旧版本） |

## 九条规矩

1. **范围：非 DSH 自带就纳入**（见开头那段，**四类**）。第三方装的、用户手动装的、你帮装的，都记；
   DSH 自带 bundle、环境预装工具、普通 npm 包、部署自带的 preset 不记。分不清就问用户。
2. **一次安装记一条，不是每个目录一条。** 仓库里打包了多个 skill（例如 ponytail 带 6 个）
   也只记一条，拆包的事由新环境的 DSH 读仓库后自行处理。
3. **账本只追加，不覆盖。** 新行加到表格末尾、新日志加到文件末尾；已有行不改不删，要更正就再追加一行说明。
4. **照着账本/安装说明重装，什么都不写。** 那属于幂等重装，不是新要求；追加只会产生重复记录。
5. **任何已记账的条目被修改，都要重新同步 + 提交一趟**（含本 skill `skills-inventory` 自己）。
6. **skill 一律全量镜像到 `skills\<name>\`**，不管有没有来源（见「skill 怎么备份」一节）。
   它背后若有**一整套本机环境**（自制脚本 + 客户端配置 + 几百 MB 到几 GB 的运行时），
   按「配套环境型 skill」一节处理 —— **自制件收进 skill 目录，大件只记重建配方，敏感的永不备份**。
7. **插件只存配方，且只记来源与安装命令**（见「插件怎么备份」一节）：`plugins\<name>\RECIPE.md`
   写清**来源 spec（不锁版本）**、安装命令、前置条件、profile 配置片段、验证与重启要求；
   `node_modules` 可重装，永不复制，**插件源码也从不备份**。
8. **每次记账同时补/更新安装说明**（见下节）。
9. **每次改完，提交并推送到仓库**（见「变更即提交」）：**git 历史就是回退手段**，
   原先的按日 zip 快照已退休。

## 优先级与安装顺序

每个记账的条目都要标一个优先级，写进账本表格的「优先级」列；**新装时先判定优先级**：

| 优先级 | 含义 | 当前 |
|---|---|---|
| **P0 治理类** | 它决定"其他 skill 怎么被安装/记账/生效"；**必须最先装，最后卸** | `skills-inventory` |
| **P1 依赖类** | 别的 skill 或其脚本会引用它、调用它提供的命令/文件；**先装被依赖的，卸载反序** | `dev-hygiene` |
| **P2 独立类** | 跟其他互不影响，**任意顺序** | 其余全部 |

判定方法（不确定就往低依赖方向判，别乱升）：

- 改了它会影响"别的 skill 能不能被正确安装/记账"？→ **P0**。
- 别的 skill 的 `SKILL.md` 或脚本会引用、调用它提供的命令/文件？→ **P1**。
- 都不 → **P2**。

安装顺序：**P0 全部先装** → P1（按依赖先后）→ P2（任意）。卸载顺序相反：先 P2/P1，最后 P0。
**插件与 MCP 的额外要求**：插件都在 profile 的 bundle 层，装完**必须重启 DSH** 才生效；
MCP 看层 —— **profile 层**的同样必须重启，**preset 层**的随 preset 由新会话按需 compose、不必重启
（但 preset 依赖的 skill 必须先装好）。所以同优先级下，把它们排在最后装，重启一次即可。

新装的条目如果改变了总体顺序规则（例如新增了一个 P0），除了账本与安装说明，还要同步更新
`$DSH_HOME/AGENTS.md` 常驻规则，必要时更新本 skill 正文。

## 账本目录怎么定

- 以本文件顶部那一行为准。
- 那一行在当前机器上**不存在**（换了机器、换了盘）→ **问用户账本放哪**，拿到路径后改两处：
  本文件顶部这一行 + `$DSH_HOME/AGENTS.md` 常驻规则里的路径，然后继续干活。
- 不要默认假设 `D:\AI_python\skills_backup` 一定存在，也不要静默地在别处新建一份。
- **换机器时**：不必新建账本目录，直接照「迁移到新环境」一节 `git clone` 本仓库即可。

## skill 怎么备份：全量镜像

**所有 skill（不论有没有来源）都整份镜像到 `skills\<name>\`**：

```powershell
robocopy "$env:USERPROFILE\.dsh\skills" "D:\AI_python\skills_backup\skills" `
  /E /XD __pycache__ .git node_modules .venv /XF *.pyc /NFL /NDL /NJH /NJS /NP
```

- 跳过 `node_modules` / `.venv` / `__pycache__`（可重装），其余**全部**保留 ——
  含上游代码、`references\`、`scripts\`、大文档（如 firerpa 的 `llms-full.txt` 496 KB）。
- **为什么要全量**：新环境 `git clone` 后直接把 `skills\*` 复制到 `$DSH_HOME/skills` 即可，
  **不必再去各自的上游仓库逐个拉取**；恢复流程从"拉上游 + 打适配层 + 建环境"缩短为"clone + 复制"。
- 同步完**必须核对**：逐文件 SHA256 与 `$DSH_HOME/skills` 一致，文件数相同。
- **没有来源的 skill**（自己写的 / 导入的 / 被改到与上游无关的）也在同一个 `skills\` 下 ——
  它们的特殊之处只在**账本里要标注「唯一副本在这里」**（见「表格每列写什么」的「来源」列）。

> 旧规则里的 `local\skill\<name>\` 已取消：`skills\` 全量镜像把它取代了（不再"只备份没来源的"）。

## 插件怎么备份：配方 + profile 片段，不是文件副本

插件与 skill 的**安装方式完全不同**：skill 是"把目录复制到 `$DSH_HOME/skills`"，
而插件要装进**某个 profile 的依赖**并被它的 `bundles` 列表加载，装完还得**重启 DSH**。
所以插件的备份 = **一份能照着重装的配方**，放在 `plugins\<name>\RECIPE.md`：

1. **身份**：插件名、类型（DSH 插件）、优先级、用途、来源 URL、记录日期。
2. **来源与安装命令**：`dsh plugin --profile <profile> add <spec>`。
   **spec 写来源本身、不锁版本**（`github:owner/repo`、`@scope/pkg`、release 的
   `…/releases/latest/download/<asset>` 等）—— 重装即升级到最新版。**不要记 commit / tag / 校验和 /
   包内文件清单**：它们随升级立刻过期，而且属于源码级内容，插件从来只记配方、不备份源码。
3. **前置条件**：`dsh plugin` 只是 pnpm 的转发器（机器上要有 pnpm）；git 依赖的 prepare 构建会被 pnpm
   默认拦截，要把**确切的那个 `allowBuilds` 键**（形如
   `"<name>@https://codeload.github.com/<owner>/<repo>/tar.gz/<commit>": true`，键里带 `@` `:` `/`，
   **必须加引号**）写进 `<profile>\pnpm-workspace.yaml` 再重跑。这个键非常容易丢，**必须记进配方**。
   （该文件的完整内容已备份在 `config\profile\pnpm-workspace.yaml`。）
4. **装完应该长成什么样**：profile 的 `package.json` 里
   `dependencies` 多出哪一条、`dsh.profile.bundles` 末尾多出哪一个。
   `bundles` 由 dsh 自动 reconcile，但**少了它插件不会加载**，所以它是核对基准。
   （该文件的完整内容已备份在 `config\profile\package.json`。）
5. **验证**：`dsh --profile <profile> --dump-config` 输出里应出现该插件段落；以及
   **必须重启 DSH**（bundle 层在 profile 启动时组合，运行中不会热加载）。
6. **卸载**：`dsh plugin --profile <profile> remove <name>` + 重启。
7. **不复制 `node_modules`**：构建产物可重装，只保留配方。
   **例外**：插件是**自己写的**（没有任何来源）→ 连源码一起放进 `plugins\<name>\`，
   并在配方里写清它该放哪、怎么被 profile 引用。

> 判断"有来源 / 无来源"和 skill 一样：能用一条 `dsh plugin add` 重新拿到的，只记配方。

## MCP 怎么备份：挂载条目 + 运行时重建配方

MCP server 既不是 skill 也不是 npm 插件 —— 它是**一条 DSH 配置**：`name: '@deepseek-ai/dsh-mcp-client'`
的挂载行。它必须被记账，因为**不记就迁移不走**，新环境会少掉这些工具。

**先分清挂在哪一层，因为备份去向与验证方式都不同：**

| 层 | 写在哪 | 何时启动 | 备份去向 |
|---|---|---|---|
| **profile 层（常驻）** | profile 的 `cordis.patch.yml`，包在 `- insert:` 列表里 | harness 启动即拉起 | `config\cordis.patch.yml` |
| **preset 层（按需）** | agent preset 的 `agent.cordis.yml`，普通行 | 只有新会话选中该 preset 才 startup | 随 `presets\<id>\` 一起（**不需要另存**） |

**preset 层是本机 2026-10-02 起的形态**：4 个逆向 MCP 全部从 profile 层搬进了 `presets\reverse\`。
动机是 profile 层会让 `dsh web` 一启动就 spawn 全部服务器（实测 10 进程 / 约 300 MB），且
`dsh-mcp-client` 的 `apply()` 会**同步等待「连接 + `tools/list`」完成**、其 Config schema
**没有任何懒加载字段**（启动与发现超时直接继承 MCP SDK）—— 所以"按需"只能靠换挂载层，
而 **preset 是 DSH 里唯一的惰性挂载点**（`dsh-agent-presets` 的 "reading never mounts"）。

⚠️ **换成 preset 层的代价必须一起记**：该 MCP 的工具**只对该 preset 的会话可见**，
普通会话里根本不存在 —— 不写这一条，新环境会以为工具坏了。

账本里给每个 MCP 记一条，并在**「来源」列写它依赖的运行时**。

一个 MCP 条目的配方要写清：

1. **身份与用途**：`serverName`（工具在会话里以 `mcp__<serverName>__<tool>` 暴露）、干什么用的。
2. **挂载层 + 配置来源**：profile 层还是 preset 层；原文条目在哪份配置里（`config\cordis.patch.yml`
   或 `presets\<id>\agent.cordis.yml`），原样保留。
3. **依赖的运行时**：`command` / `args` 指向什么 —— 例如 camoufox MCP 指向
   `D:\AI_python\camoufox\.venv\Scripts\python.exe`，jadx MCP 由 `uv` 在
   `D:\AI_python\MCP\MCP合集\jadx-mcp-server` 下启动。
   **运行时体积大、有来源 → 只记重建配方，不备份**（见「配套环境型 skill」）。
4. **外部前置**：例如 jadx MCP 需要 **JADX-GUI 里装好 `jadx-ai-mcp` 插件并保持开启**
   （默认 `127.0.0.1:8650`）—— 这类"不在本机、也不在仓库"的前置必须写明，否则新环境会一头雾水。
5. **凭据**：MCP 若需要 token，**绝不写进配置**（配置文件会进本仓库）—— 用
   `!!js process.env.<NAME>` 引用，真值放 `$DSH_HOME\.env`（Harness-home 专属层，明确不随仓库传播，
   **不入账本**），并在配方里写明变量名与"改完要重启 DSH"。注意 `!!js` 的求值环境
   （`new Function` + `with(ctx)`）**有 `process` 全局、没有 `require`**，所以只能读环境变量。
6. **验证**：分层的验证方式不同 ——
   - profile 层：重启 DSH 后会话里出现 `mcp__<serverName>__*`；`dsh --profile <p> --dump-config` 里能看到该条目。
   - preset 层：**`--dump-config` 看不到**（它只打印 host 组装的树）。改用
     `reverse-skill-router` 的能力扫描器（它同时扫 profile 与 preset 两层，清单「层」列会标出
     `preset:<id>`），或新开一个该 preset 的会话看工具列表。
   `failOnStartupError: false` 的条目（如 jadx / analyzer）**启动失败不会报错**，所以要主动验证。
7. **何时需要重启 DSH**：profile 层在启动时组合，**必须重启**；preset 层由新会话按需 compose，
   **不需要重启**（但 `.env` 里的变量只在启动时读取，改了它仍要重启）。

## agent preset 怎么备份：整份 composition 副本，不是配方

**第四类资产**。它住在 `$DSH_HOME\.agent-presets\<id>\`，**不在任何 profile 的 `package.json` / `bundles` 里**
—— skill 镜像、插件配方、MCP 挂载三种办法都覆盖不到它，新环境克隆本仓库再跑 `install.ps1`
也拿不回它，**模式会凭空消失**。

备份形态 = `presets\<id>\` 下的**整份副本**：

| 文件 | 说明 |
|---|---|
| `agent.cordis.yml` | composition 本体（整份复制，不裁剪、不改写） |
| `preset.yml` | 显示名与描述（会话选择器里显示的就是它；没有它 picker 里只显示目录名） |
| `README.md` | **必写**：这是什么、依赖哪些 skill（按什么顺序）、有没有必须先跑的生成物、怎么验证挂载、不要做什么 |

恢复 = 把目录复制回 `$DSH_HOME\.agent-presets\<id>\`，然后：

1. **打开一个该 preset 的新会话** → 挂载成功即工具与 persona 正常。
   **`preset_probe` 在现行 DSH 里不存在**（它是某个会话里动态定义的 cordis 包，重启即消失、从未落盘）
   —— 旧版本节写的 `preset_probe validate <id>` 已失效，不要照做。
   **roster 里的 `broken: false` 也不算验证** —— 它只做形状检查（YAML 能解析、有具名行），
   行引用的包不存在、配置非法、行没激活、服务发布到根 realm 这四种失败它都照过；
   而**真实挂载失败会让会话创建直接失败并回滚、且指名是哪一行** —— 所以新开会话是最强也最省事的验证。
   静态复核（可选，能提前抓错）：用 `cordis-plugin-include` 导出的 `entryListSchema` 解析 composition
   （它就是 Loader 的 YAML 方言），再把每行 `config` 喂给对应插件自己的 Schemastery schema；
2. 若该 preset 依赖**生成物**（例如逆向模式的能力清单 `$DSH_HOME\reverse\capabilities.md`），
   先跑它的生成脚本，否则 persona 指向的文件不存在；
3. 确认 persona 生效、工具列表符合预期（只有真实会话能看出 composition 产出的 agent）。

**规则**：

- preset **引用** skill、但自己不提供能力 —— 它的行必须写清依赖顺序（先装引用的 skill），
  `README.md` 里再重复一遍；
- **绝不备份 DSH 部署自带的 preset**（`standard` / `ptc` / `minimal` / `cordis`）与第三方包内的 preset
  （如 `@howmp/dsh-pentest` 的 `pentest`）：前者归部署所有、升级会覆盖，改坏 `cordis` 还会让 preset
  创作能力失效；后者随插件重装即回来；
- 只记**用户自己写在 `.agent-presets\` 下的** preset；
- 改了 composition 必须重新整份复制回 `presets\<id>\`（并核 SHA256）—— 这是"已记账条目修改后
  重新同步一趟"的一个实例。

## 配套环境型 skill：自制件进目录，有来源的只记配方

有些 skill 描述的**不是一段提示词，而是一整套本机环境的用法**：正文引用工作区里的自制脚本、
某个客户端的配置，背后还有几百 MB 到几 GB 的第三方运行时（浏览器引擎、模型、服务二进制）。

这类 skill **只备份 `SKILL.md` 是残缺的** —— 换台机器拿到的是一份"说明书"，里面提到的脚本、配置和
重建步骤全都不在。反过来把几 GB 运行时塞进仓库也不合理：它们本来就能从网上重下，
而且体积会毁掉仓库的克隆体验。办法是**让 skill 目录自包含，大件只留重建配方**。

### 什么时候适用

skill 正文出现下列任一情况，就按本节处理：

- 引用了 skill 目录**之外**的自制文件（工作区脚本、配置文件、说明书）；
- 依赖一个要另外安装的运行时 / 服务（浏览器、引擎、数据库、CLI）；
- 含有"安装 / 重建 / 迁移"这类带固定步骤与版本号的内容。

### 怎么做

1. **把目录外的自制产物收进 skill 目录**：脚本 → `scripts\`，说明书 / 配置片段 / 示例 → `references\`。
   自制的东西**必须进目录**：它们在别处没有任何来源。
2. **在 `references\` 写一份「重建配方」**，让新环境不靠记忆也能装回来：
   - 每个大件的**来源**（release 页 / PyPI / 包名）、**固定版本**、**校验和**（sha256 之类）；
   - 按顺序的可执行命令，含"必须先做"的前置（例如先建目录联接再装引擎）；
   - 要写进**其它**配置文件的片段原文（如 DSH 的 `cordis.patch.yml` 条目）；
   - **明确列出永不备份的敏感数据**（凭据、登录态、profile）以及它们怎么重建。
3. **能给就给一个 `scripts\restore` 一键重建脚本**：建环境 → 装依赖 → 下大件并校验 → 冒烟测试 →
   打印还需手工贴的配置片段。没有它，"轻量备份"只是"记了一堆要手工执行的步骤"。
4. **`skills\<name>\` 里备份整个自包含目录**（一般几十 KB 到几百 KB）；大件**不进仓库**，
   只在账本「适配」列与重建配方里写清来源和版本。
5. 账本两列照写，但「适配」列要补一句环境依赖：
   - 来源：有来源就写来源 URL；没来源写 `本地自制（唯一副本在 skills/<name>/）`
   - 适配：`该 skill 目录自包含，背后的 <大件>（约 <体积>）按 references\<配方> 重建，不随仓库迁移`
6. **在 `INSTALL.md` 小节里写明维护提醒**：目录外的自制产物一旦改动，要重新同步进 skill 目录、
   重新同步到 `skills\` 并提交 —— 否则备份会静默过期。

### 一句话判据

**自制的进目录，有来源的记配方，敏感的永不备份。**
（体型线索：自制件通常 < 1 MB，有来源的大件往往 100 MB ~ 数 GB；这个体积差就是本节存在的理由。）

## 修改已记账的条目

只针对**账本里已有记录**的条目。它们只要内容被改动（你改的、用户改的、工具改的），都要走一遍重备份：

- **skill**（含 `skills-inventory` 自己）→ 重新同步到 `skills\<name>\`（见「skill 怎么备份」），
  再在日志追加一行说明改了什么。**历史由 git 提交历史承担**。
- **网络来源的 skill** → 同样全量镜像；另外在日志说明本地改了什么；
  如果这个改动会影响新环境重建（例如适配步骤变了），**同时更新 `INSTALL.md` 里该条目的小节**。
- **插件** → 更新 `plugins\<name>\RECIPE.md`（来源 / 安装命令 / `allowBuilds` 键 / profile 片段变了
  就要改），再追加日志；插件是自写的还要重新复制源码。
- **MCP** → 看层：**profile 层**更新 `config\cordis.patch.yml` 的副本；**preset 层**的挂载行在
  `presets\<id>\agent.cordis.yml` 里，随 preset 一起同步（**不需要**另存到 `config\`）。
  两种都要更新账本里该行的说明，再追加日志。凭据变动只改 `$DSH_HOME\.env`（**不入账本**）。
- **`config\` 里的任何文件被改**（`AGENTS.md` / `settings.yaml` / profile 配置）→
  重新复制到 `config\`，再追加日志。
- **不在账本里的东西被改 → 什么都不做**：不补记、不进 `skills\`、不加安装说明小节。
- 改完再核对一次：镜像文件数与源目录一致（SHA256 一致）；`INSTALL.md` 的小节仍然能照着装出同样的结果。
- **动手之前**不必再打 zip；正常改、改完提交即可（真要留退路就先 `git commit` 一个基线）。

## 变更即提交：git 取代了按日 zip 快照

**回退手段就是 git 历史**，不再有 `snapshots\ledger-YYYY-MM-DD.zip`（旧文件已退休，见 `.gitignore`）。
原先"动手前先打快照"的理由（活账本每个条目只保留最新一份，改坏了没得退）现在由
**上一次 commit** 承担，而且更强：能 diff、能定位是哪次改动引入的问题、能只回退单个文件。

**每次改完账本（新增 / 修改 / 删除任何已记账条目）之后：**

```powershell
$L = 'D:\AI_python\skills_backup'
cd $L

# ① 同步 skill 内容（skills\ ← $DSH_HOME\skills）
robocopy "$env:USERPROFILE\.dsh\skills" "$L\skills" `
  /E /XD __pycache__ .git node_modules .venv /XF *.pyc /NFL /NDL /NJH /NJS /NP

# ② 同步环境配置（config\ ← $DSH_HOME）
Copy-Item "$env:USERPROFILE\.dsh\AGENTS.md"                       "$L\config\AGENTS.md" -Force
Copy-Item "$env:USERPROFILE\.dsh\settings.yaml"                   "$L\config\settings.yaml" -Force
Copy-Item "$env:USERPROFILE\.dsh\profiles\web\cordis.patch.yml"   "$L\config\cordis.patch.yml" -Force
Copy-Item "$env:USERPROFILE\.dsh\profiles\web\package.json"       "$L\config\profile\package.json" -Force
Copy-Item "$env:USERPROFILE\.dsh\profiles\web\pnpm-workspace.yaml" "$L\config\profile\pnpm-workspace.yaml" -Force
Copy-Item "$env:USERPROFILE\.dsh\profiles\web\cordis.yml"         "$L\config\profile\cordis.yml" -Force
# ②b 同步用户自建 agent preset（presets\ ← $DSH_HOME\.agent-presets）—— preset 层的 MCP 挂载在这里
Get-ChildItem "$env:USERPROFILE\.dsh\.agent-presets" -Directory | ForEach-Object {
  Copy-Item $_.FullName "$L\presets\" -Recurse -Force
}
# ⚠️ 永不复制 .env / .credentials.yaml / 登录态 —— 凭据不进仓库

# ③ 更新 SKILLS.md（追加日志）+ CHANGELOG.md（追加变更说明）

# ④ 提交推送 —— **只 add 你这次真的改过的路径**，禁 git add -A / commit -a
git status --porcelain                      # 逐项确认归属：不认识的改动一律不提交
git add skills\dev-hygiene\SKILL.md SKILLS.md CHANGELOG.md   # ← 显式列（路径按本次实际改的填）
git commit -m "<类型>: <一句话说明>"
git push
git status -sb                              # 期望 ## main...origin/main，无 ahead/behind
```

**提交信息约定**：`install:` / `update:` / `remove:` / `rule:` / `config:` + 一句话。

### ★ 为什么这里必须显式列路径（2026-10-27 实测事故）

账本仓库是**多会话共享**的：同一个 `D:\AI_python\skills_backup` 可能同时有别的会话在写新条目。
`git add -A` 会把**你从没打开过的、别人未提交的改动**一起吞进你的提交 —— 提交信息还写着你的活儿：

- 实测：我在做 reverse-skill 上游升级，第二次提交用了 `git add -A`，把另一会话未提交的
  `plugins\dsh-skillhub\RECIPE.md` + `INSTALL.md` / `SKILLS.md` 追加（共 302 行）带进了 `5817940`；
  对方随后只能把剩余文件另提一条 `40a396d`。
- 处理原则（当时就这么做的）：**不重写已推送历史**（不 `reset --hard`、不 `amend`、不 `force push`）——
  那会打断对方基于同一 HEAD 的工作。误带了就补一条说明，或让属主自己记一笔。
- 通用规则与更多坑（行尾符、`numstat` 异常、ff 升级、push 后验证）见 `dev-hygiene` 规则 6。

### 并发会话下的账本操作

- 动手前先 `git status --porcelain`；**看到不是自己产生的改动 → 不要覆盖、不要回滚、不要提交**。
- 对方推了新提交、而本地工作树还脏着：用 `git merge`（或 `git pull --no-rebase`）——
  `git pull --rebase` 在脏工作树会直接拒绝（"cannot pull with rebase: You have unstaged changes"）。


### 怎么回退

| 想要什么 | 怎么做 |
|---|---|
| **改坏了，退回上一版** | `git log --oneline` 找到目标提交 → `git revert <commit>`（保留历史）或 `git checkout <commit> -- <路径>`（只回退某文件） |
| 只想看看某次改了什么 | `git show <commit>` / `git diff <commit>~1 <commit>` |
| 整个仓库回到某天 | `git checkout <commit>`（游离头）或 `git reset --hard <commit>`（**会丢未提交改动，慎用**） |
| 回退后 | 按「修改已记账的条目」走一遍，并在 `SKILLS.md` **追加日志说明这是一次回退** |

**和「只追加」的关系**：正常情况下账本不需要"撤销"，行和日志写了就留着。git 是给
**装坏、写坏、误删**这三件事兜底的，不是日常撤销手段。

## 每次记账都要补一节安装说明

在 `INSTALL.md` 里写清新的环境要照着做什么；新条目就在末尾**追加一节**
（`## <name>（P? 类型 · skill/插件/MCP · 网络来源/本地来源）`）：

- **网络来源的 skill**：仓库 URL、**只取哪一部分**（上游往往还带 README、hooks、benchmark，不要照搬整个仓库）、
  需要哪些 DSH 化改造（frontmatter 只留 `name`/`description`、命令改用 `/name` 调用、
  子代理规则要写进 subagent 的 prompt），以及装完怎么验证。
- **本地来源的 skill**：`skills\<name>\` 直接整份复制到 skill 根、不需要改造；它是**唯一副本**，
  仓库里那份不在时先找用户要，**不要去网上找同名 skill 顶替**。
- **插件**：照 `plugins\<name>\RECIPE.md` 的内容写（安装命令、`allowBuilds` 键、profile 片段、
  验证、**必须重启 DSH**），并指回那份配方。
- **MCP**：写清 `serverName`、**它挂在哪一层**（profile 的 `cordis.patch.yml`，还是 preset 的
  `agent.cordis.yml`）、**依赖的运行时怎么重建**、**外部前置**（如需要某个 GUI 工具在跑）、
  凭据走哪个环境变量，以及分层的验证方法（preset 层 `--dump-config` 看不到；
  `failOnStartupError: false` 的"启动失败不会报错"）。

安装说明是给"完全没有上下文的新 DSH"看的：写成能照着执行的动作，不要写"参考某处"这类空话。
**最省事的做法**是让新环境直接跑 `install.ps1`，安装说明只需写它覆盖不到的部分。

## 什么时候动它

用户要求安装、更新、修改或删除之后：

1. `read` 打开 `<账本目录>\SKILLS.md` 和 `INSTALL.md`。
2. **顺手清点一次**（避免漏掉用户自己装的）—— 现在要扫**四类**：
   - skill = `$DSH_HOME/skills` 下的目录；
   - 插件 = `<profile>\package.json` 的 `dependencies` 里**非 `@deepseek-ai/*`** 的条目，
     以及 `dsh.profile.bundles` 里非自带的那些；
   - **MCP = `name: '@deepseek-ai/dsh-mcp-client'` 的挂载行 —— 两层都算**：
     **profile 层**在 `<profile>\cordis.patch.yml` 里包成 `insert` 条目（常驻）；
     **preset 层**在 `$DSH_HOME\.agent-presets\<id>\agent.cordis.yml` 里是普通行（按需）。
     账本与配置里都要写明层，因为备份去向与验证方式不同（见「MCP 怎么备份」一节）；
   - **agent preset = `$DSH_HOME\.agent-presets\` 下的目录**（凡是用户自己写在那里的，
     都不在任何 profile 配置里 —— 漏记就等于新环境没有这个模式）。
   发现没记账的（用户手动装的、第三方装的）→ 一并补记；分不清是否自带的 → 问用户。
3. 判定优先级（P0/P1/P2），确认它是否改变安装顺序。**preset 引用 skill 而不提供能力**：
   它的优先级按"消费者"记，并在行里写清必须先装哪些 skill。
4. 记账：账本追加一行表格（含优先级）+ 一行日志，`INSTALL.md` 追加一节（或更新 `install.ps1`）；
   插件无论有无来源都要写 `RECIPE.md`；preset 备份整份目录到 `presets\<id>\` 并写 `README.md`。
5. **同步 + 提交推送**（见「变更即提交」），并在 `CHANGELOG.md` 追加一条变更说明。
6. 文件在工作区之外时可能被沙箱拒绝：**同一次操作重试一次**并申请 `danger-full-access`，
   理由写"更新工作区外的 skill 清单"。

## 表格每列写什么

| 列 | 内容 |
|---|---|
| 名称 | 用户口中或来源里的名字（仓库名即可）；**是插件就标注「DSH 插件」**，是 MCP 就标注「MCP」，是 **agent preset 就标注「agent preset」**（并写上会话选择器里的显示名），是 skill 可不标 |
| 优先级 | `P0 治理类` / `P1 依赖类` / `P2 独立类`（判定见上） |
| 来源 | GitHub 仓库 URL、ClawHub 名称；**没来源写 `本地自制（唯一副本在 skills/<name>/）`**；推不出来写 `未知（本地）`，**绝不编造**。**MCP 这一列写它依赖的运行时**（如 `camoufox MCP ← D:\AI_python\camoufox`） |
| 适配 | 来源不是 DSH 原生格式时必写：`需按 DSH 模式定制修改 —— SKILL.md frontmatter 只留 name/description（≤500 字符）、命令说明改用 /name 调用、子代理规则写进 subagent prompt`；本身就是 DSH skill 则写 `DSH 原生，复制 skills/<name>/ 即可`；**插件写安装命令与前置，并指向 `plugins\<name>\RECIPE.md`**；**MCP 写它的 `serverName`、挂在哪一层（profile 层 `config\cordis.patch.yml` / preset 层 `presets\<id>\agent.cordis.yml`）、外部前置、凭据环境变量、分层验证方式**；**preset 写它依赖哪些 skill（按顺序）、有没有必须先跑的生成物脚本、验证方式（新开会话实测；`preset_probe` 已不存在），并指向 `presets\<id>\README.md`** |
| 记录日期 | `YYYY-MM-DD` |

日志一行说清这次做了什么：装/改了哪个来源、带了几个 skill / 插件 / MCP、同步了哪些目录、优先级变化、删掉了什么。

## 迁移到新环境

新环境只需要**仓库地址**：

```powershell
git clone https://github.com/canglingzhiyue/dsh_skills.git
cd dsh_skills
pwsh -File install.ps1 -DryRun     # 先看它会做什么
pwsh -File install.ps1             # 执行
```

`install.ps1` 会做完**自动部分**：备份现有配置 → 恢复全部 skill → 恢复常驻规则与 DSH 设置 →
恢复 MCP 挂载与 profile 配置 → 装第三方插件 → 打印**必须人工完成**的待办
（重建 GB 级运行时、填凭据、登录、改硬编码路径、**重启 DSH**）。

**它做不到的事**（脚本末尾会列出来，必须人工）：

- 各 skill 背后的**运行时**（约 2.7 GB）—— 按各 skill 的 `references\重建配方` 或 `scripts\restore.ps1` 联网重建；
- **凭据**（`.credentials.yaml` 里的 API key）—— 永不进仓库，必须手填；
- **登录态** —— 永不进仓库（如 camoufox 的 `states\` / `profiles\`）；
- **外部前置** —— 如 jadx MCP 需要 JADX-GUI 里装好插件并保持开启。

**不要**往 `SKILLS.md` / `CHANGELOG.md` 追加任何内容：那是重装，不是新变更。
新环境里系统自带、环境预装的 skill / 插件 / MCP 不在清单里，也**不要装、不要记**。

## 边界

有来源的只记来源，没来源的照样全量镜像（只是账本里标注"唯一副本在这里"）。
插件永远只存配方不存 `node_modules`；MCP 永远只存挂载条目不存运行时。
**DSH 自带的东西永远不记、不备份**（包括只是被改过的那些）；
**凭据与登录态永远不进仓库**（`.credentials.yaml`、`states\`、`profiles\`）。
重装永远不重复记账；改动永远不丢 —— **最坏也能从上一个 commit 取回**。
