# Skill 安装说明 —— 交给新环境的 DSH 照着执行

> **最快路径：不要照本文件手工装，直接跑 `install.ps1`。**
>
> ```powershell
> git clone https://github.com/canglingzhiyue/dsh_skills.git
> cd dsh_skills
> pwsh -File install.ps1 -DryRun   # 先看它会做什么
> pwsh -File install.ps1           # 执行（会先备份现有配置）
> ```
>
> 它做不完全部（GB 级运行时、凭据、登录态要人工）—— 脚本末尾会打印待办清单。
> **本文件是手工版的完整说明**，也是脚本覆盖不到的那部分的依据。

配套文件：

- `SKILLS.md` —— 账本（装过什么、优先级、来源、为什么这样装）
- `skills\<name>\` —— **全部 skill 的完整内容**（= `$DSH_HOME/skills` 的镜像），直接复制到 skill 根即可
- `plugins\<name>\RECIPE.md` —— 插件配方（不复制 `node_modules`）
- `config\` —— 常驻规则 `AGENTS.md`、DSH 设置 `settings.yaml`、**MCP 挂载** `cordis.patch.yml`、profile 配置
- `README.md` / `CHANGELOG.md` —— 仓库说明 / 变更说明
- `install.ps1` —— 一键恢复脚本

**只处理本清单里列出的 skill / 插件 / MCP。** 新环境里系统自带、环境预装的既不要装，也不要记录、
不要备份 —— 这份仓库只负责用户明确要求安装过的东西。

## 通用步骤

1. **先读同目录的 `SKILLS.md`**：了解每个 skill 的优先级、来源与适配要求。
2. **确定本机 skill 根**：优先 `$DSH_HOME/skills`（Windows 通常是 `C:\Users\<你>\.dsh\skills`）；
   没有 `$DSH_HOME` 就用 `~/.agents/skills`。不存在就创建。
3. **确定本机账本目录**：能沿用 `D:\AI_python\skills_backup` 就沿用（**它同时是 git 仓库**，
   remote = `https://github.com/canglingzhiyue/dsh_skills.git`）；这台机器没有这个盘或不想用，
   就自己挑一个（例如 `<某个盘>\skills_backup`）把仓库内容放进去，并且**问一下用户确认**。
   之后把 `skills-inventory\SKILL.md` 顶部那一行与 `$DSH_HOME/AGENTS.md` 里的路径改成同一个（两处必须一致）。
4. **按优先级顺序装，不要一把抓**：
   - **P0 治理类先装**（`skills-inventory`）：它决定后面装的 skill 会不会被记账，必须排第一；
   - **P1 依赖类**：先装被依赖的，再装依赖它的（当前 `dev-hygiene` —— `camoufox-reverse` 等引用它）；
   - **P2 独立类**：任意顺序。（2026-09-17 起本机不再包含 `ponytail` —— 用户要求卸载，见文末该节的标注。）
5. **按下面的小节逐个安装** —— 三类东西装法完全不同，别混：
   - **skill**：把 `skills\<name>\` **整个目录**复制到 `<skill 根>\<name>\`，内容不要改动
     —— 仓库里就是**完整内容**，不必再去上游仓库拉取、也不存在"改造"这一步。
   - **DSH 插件**：**不要**复制到 skill 根。照 `plugins\<name>\RECIPE.md` 执行
     （`dsh plugin --profile <profile> add <spec>`、把那个 `allowBuilds` 键补进 `pnpm-workspace.yaml`、
     核对 profile 的 `dependencies` 与 `dsh.profile.bundles`），**装完必须重启 DSH**。
   - **MCP**：把 `config\cordis.patch.yml` 放到 `<profile>\cordis.patch.yml`（它与 profile 三件配置配套），
     再按「MCP」小节重建它依赖的运行时与外部前置。**同样必须重启 DSH**。
   插件与 MCP 都放在最后装，这样只需重启一次。
6. **硬性要求**：`<skill 根>\<name>\SKILL.md` 必须存在；frontmatter 只放 `name` 和 `description`
   （`name` 用 kebab-case 且与目录名一致；`description` ≤500 字符，超了 DSH catalog 会截断），
   可选 `metadata`。DSH 不认 `argument-hint`、`license` 这类宿主专属字段。
7. **验证**：装完用 `skill` 工具确认这些名字出现在会话 catalog 里；装不上就报错给用户。
8. **装上常驻规则**（不装这一步，"安装完/改动完自动记账"永远不会触发）：把下面的「常驻规则模板」写进
   `$DSH_HOME/AGENTS.md`，并把 `<<账本目录>>` 替换成第 3 步确定的路径。该文件已有别的内容就**追加**，不要覆盖。
   **现成的一份就在 `config\AGENTS.md`**（本机实际生效的版本），直接复制过去再改路径即可，比照模板拼更省事。
9. **把路径改成本机的**：如果账本目录不是 `D:\AI_python\skills_backup`，把
   `<skill 根>\skills-inventory\SKILL.md` 顶部「账本目录」那一行也改成同一个路径（两处必须一致）。
10. **本次安装不要往账本里追加任何东西**：你是照着账本装的，属于**重装**；追加只会产生重复记录。
    只有用户**新提出**的安装/修改要求才记账。
11. **以后只维护本清单里的 skill / 插件 / MCP**：清单里任何一条被改动（包括 `skills-inventory` 自己）→
    重新同步到 `skills\` / `plugins\` / `config\`，追加日志，并更新本文件对应小节。
    **不在清单里的（系统自带、环境预装、别人装的）改了就改了：不记录、不备份、不加小节。**
12. **每次改完，提交并推送到仓库**（**按日 zip 快照已退休**）：同步 `skills\` 与 `config\` →
    更新 `SKILLS.md`（追加日志）与 `CHANGELOG.md`（追加变更说明）→ `git add -A && git commit && git push`。
    **回退靠 git 历史**：`git revert <commit>` 或 `git checkout <commit> -- <路径>`，比 zip 强
    （能 diff、能定位是哪次改动引入的问题、能只回退单个文件）。
    命令与办法见 `skills-inventory` 的「变更即提交」一节。
13. **先问用户**：来源不明、装不上、或与用户描述不符时，不要拿网上同名 skill 顶替，也不要猜。

## 常驻规则模板（写进 `$DSH_HOME/AGENTS.md`，替换 `<<账本目录>>`）

````markdown
# Global DSH rules (user-global instructions, loaded in every session)

## Skill inventory — for skills and DSH plugins that are not DSH-bundled (skills, and DSH plugins)

账本目录：`<<账本目录>>`（换机器时连同 `skills-inventory` skill 顶部那一行一起改）

- `SKILLS.md` — the ledger: append one table row (with its P0/P1/P2 priority) and one log line.
  Never rewrite, reorder, or delete; a table-schema change must be explained in a log line.
- `INSTALL.md` — the install guide, ordered by priority: append one section per entry; fix its wording
  in place when a step is wrong.
- `local\skill\<name>\` — full copy of a recorded skill that has no fetchable source.
- `local\plugin\<name>\` — a recorded plugin's recipe (`RECIPE.md`: spec + install command +
  prerequisites + profile snippets + verification); a self-written plugin also gets its source copied here.
- `snapshots\ledger-YYYY-MM-DD.zip` — dated pre-change archive, taken *before* each edit.

Rules:

- **Scope: anything in this environment that is not DSH-bundled is recorded and backed up** — third-party
  installs, things the user installed by hand, and things you installed for them. Two kinds qualify: a
  **skill** (a directory under `$DSH_HOME/skills`) and a **DSH plugin** (a non-`@deepseek-ai/*` entry in a
  profile's `dependencies` or `dsh.profile.bundles`). Never recorded or backed up: DSH's own bundles,
  environment-provided tooling (npm/pnpm/node/corepack/…), and ordinary npm packages that are not DSH
  skills or plugins. When unsure whether something counts as bundled, ask the user.
- One entry per requested install, **not** per directory: a repository shipping six skills is one entry,
  and the new environment reads the repository and handles the rest.
- Record the source (repository URL / ClawHub name) plus the adaptation note when the source is not
  DSH-native. If the source cannot be determined, write `未知（本地）` — never guess.
- **Assign a priority whenever you record a skill**: `P0 治理类` (affects how other skills are installed
  or recorded — install first, remove last), `P1 依赖类` (other skills reference it — install before its
  dependents), `P2 独立类` (order-free). A new skill that changes the overall order must also be reflected
  in the ledger, `INSTALL.md`, this file, and the `skills-inventory` skill when its rules change.
- **A recorded skill with no fetchable source must be copied out in full**: copy the whole skill directory
  (`SKILL.md` plus `references/`, `scripts/`, `assets/`, skipping `node_modules`/`.git`) to
  `local\skill\<name>\`, write the source as `本地自制（完整备份见 local/skill/<name>/）` with adaptation
  `DSH 原生，直接复制`, and on a later change re-copy the directory and append a log line.
- **A recorded plugin is backed up as a recipe — source and install command only, never its source
  code or build output**: give it `local\plugin\<name>\RECIPE.md` holding the source spec itself
  (**never a pinned version** — re-installing takes the newest release), the
  `dsh plugin --profile <p> add` command, its prerequisites (pnpm, the exact `allowBuilds` key), the
  profile config it must end up in (`dependencies` entry plus `dsh.profile.bundles` entry), the
  verification command, and the fact that DSH must be restarted. `node_modules` is reproducible and is
  never copied; a self-written plugin also gets its source copied into the same directory.
- **A skill that fronts a whole local environment is backed up self-contained**: when a recorded skill
  describes how to use an environment built on this machine (self-made helper scripts, client config, a
  heavyweight runtime of hundreds of MB to GBs), move the self-made pieces *into* the skill directory
  (`scripts/`, `references/`), write a rebuild recipe under `references/` for the sourced heavy parts
  (URL + pinned version + checksum + commands + any config snippet to paste), and keep those heavy parts
  out of `local\skill\` — only the self-contained directory is copied. Credentials, login state and profiles
  are never backed up. Self-made in the directory, sourced as a recipe, sensitive never. Details in the
  `skills-inventory` skill.
- **Any change to a *recorded* entry — including `skills-inventory` itself — goes through the backup pass
  again**: a local/self-written skill is re-copied in full; a plugin gets its `RECIPE.md` updated; a
  network-sourced skill gets a log line describing the local change plus an update to its `INSTALL.md`
  section when the change affects how a new environment rebuilds it. Anything not recorded stays
  unrecorded: change it and move on — no ledger row, no `local/` copy, no guide section.
- **Snapshot the ledger by date *before* every change**: zip `SKILLS.md`, `INSTALL.md` and `local\` —
  skipping `snapshots\` itself — into `<账本目录>\snapshots\ledger-YYYY-MM-DD.zip`, overwriting the same
  day's file. Taken *before* the edit, the archive always holds the last known-good version, so a bad
  skill install, a broken plugin config or a mangled ledger rolls back by extracting that day's zip;
  same-day repeats keep working because each one re-archives the pre-edit state. Details in the
  `skills-inventory` skill.
- **Re-installing from this ledger or the install guide is idempotent: append nothing.** Those installs
  are not new requests; a second row would be a duplicate. Only a new request from the user is recorded.
- If the 账本目录 above does not exist on this machine, ask the user where the ledger should live, then
  update both this file and the top of the `skills-inventory` skill to the same path.
- The files are outside the session workspace, so the writes are denied first: retry that exact operation
  once with `sandbox_permissions: "danger-full-access"` and the justification "updating the skill
  inventory outside the sandboxed workspace".

Format and migration instructions: load the `skills-inventory` skill.

## 开发规则 — dev-hygiene（常驻红线，细则加载 `dev-hygiene` skill）

- **删除一律走回收站**：用 `dev-hygiene` 的 `scripts\Remove-ToRecycleBin.ps1`（失败即抛异常，绝不降级硬删）；
  禁用 `del` / `rd` / `rmdir` / `Remove-Item` / `rm -rf` / `os.remove` / `shutil.rmtree`。
  只有两类可硬删：① 可重建的大体积产物（项目 `.venv`、uv 缓存、`node_modules`、构建中间物）——需 `uv.lock`
  等锁文件齐全且 `HANDOVER.md` 的重建命令**已实测**，删前先问用户；② `%TEMP%` 下本次会话自建的临时文件。
  `git clean`、构建工具清理、本项目目录之外的删除：先列清单问用户。
- **所有 shell 一律 pwsh 7**：禁 `powershell.exe`(5.1) / `cmd` / Git Bash / WSL；`.ps1` 含中文必须 UTF-8 with BOM；
  Linux 脚本可以写，但本机不得以任何方式执行。
- **Python 一律 uv**：项目内 `.venv` + `uv.lock`，默认清华源 `https://pypi.tuna.tsinghua.edu.cn/simple`，
  全局 `python-preference = "only-managed"`（用 uv 托管的 CPython，新环境先 `uv python install 3.12`）；
  **永不**用 anaconda 的 python / pip 装任何东西。
- **每个开发阶段收尾清理无用文件**（限本项目目录内、走回收站），交付前再清一次；删完报告清单与释放空间。
- **每个项目产出 `HANDOVER.md`**（项目根、中文）：环境 / 从零重建命令 / 运行与验证 / 目录结构 / 数据与凭据来源
  （只写从哪取）/ 已知坑 / 变更记录 / 回退方式 / 待办；**更新前先把旧版复制到
  `docs\handover-history\HANDOVER-YYYY-MM-DD.md`**；项目完事且重建命令已验证时可删 `.venv`（先问一次）。
````

## skills-inventory（P0 治理类 · 本地来源 · 必装 · 最先装）

- 完整备份：`local\skill\skills-inventory\`（当前只有 `SKILL.md`，无脚本）
- 安装：把 `local\skill\skills-inventory\` 整个复制到 `<skill 根>\skills-inventory\`
- 改造：不需要，已是 DSH 原生
- **优先级 P0**：它决定"其他 skill / 插件怎么被记账"，所以必须第一个装；卸的时候最后一个卸
- **必装，不能跳过**：新环境不装它，之后新装的东西不会被记进清单，这份备份会慢慢过期。
  装完确认 `<skill 根>\skills-inventory\SKILL.md` 存在，且 catalog 里出现 `skills-inventory`
- **它内含这几类规则**（细节都在该 skill 正文里）：
  ① **范围**：非 DSH 自带的 skill 与插件都记、都备份（DSH 自带 bundle、npm/pnpm/node 等预装工具不记）；
  ② **没来源的 skill 整份备份** → `local\skill\<name>\`；
  ③ **插件只存配方** → `local\plugin\<name>\RECIPE.md`（spec + 安装命令 + `allowBuilds` 键 +
     profile 片段 + 验证 + 必须重启 DSH），`node_modules` 永不复制；
  ④ **配套环境型 skill**（skill 其实只是一整套本机环境的说明书时）：自制件收进 skill 目录、
     大件只写重建配方、敏感数据永不备份，判据 **自制的进目录，有来源的记配方，敏感的永不备份**；
  ⑤ **按日快照**：每次动账本**之前**把 `SKILLS.md` + `INSTALL.md` + `local\`（跳过 `snapshots\` 自身）
     压成 `snapshots\ledger-YYYY-MM-DD.zip`，包里永远是"上一个已知良好的版本"，这是唯一的回退手段
- 装完顺手做第 8、9 步：写常驻规则、对齐账本目录路径

## dev-hygiene（P1 依赖类 · 本地来源）

**它是什么**：本机五条开发硬规则的唯一权威 —— ① 删除一律走 Windows 回收站；② 所有 shell 一律 pwsh 7；
③ Python 一律 uv（项目内 `.venv` + `uv.lock` + 清华源 + 只用 uv 托管解释器）；④ 每阶段收尾清理无用文件；
⑤ 每项目产出 `HANDOVER.md`（更新前先备份）。规则细节在 skill 正文，`AGENTS.md` 里只留 5 行常驻红线。

**skill 目录自包含**（6 文件约 34 KB）：

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 五条规则的完整语义、硬删豁免清单、收尾清单、本机已知坑 |
| `scripts\Remove-ToRecycleBin.ps1` | **唯一删除实现**：默认回收站、`-WhatIf` 预演、失败抛异常绝不降级、`-HardDelete -Reason` 为豁免通道 |
| `scripts\recycle.py` | Python 侧封装（转调上面的 ps1、`-Quiet` 取结果），复制到项目 `tools\` 使用 |
| `templates\HANDOVER.md` | 交接文档模板（含 `docs\handover-history\` 备份 / 回退流程） |
| `references\uv-清华源.md` | 清华源与 `python-preference` 配置、实测记录、TOML 顺序坑 |
| `references\验证记录.md` | 5 项冒烟实测输出、修掉的 3 个缺陷、测试方法本身的坑 |

### 第 1 步：放入 skill 根

把 `local\skill\dev-hygiene\` **整个目录**复制到 `<skill 根>\dev-hygiene\`；frontmatter 已是 DSH 原生，不需要改造。

### 第 2 步：写常驻红线（必做，否则未加载 skill 的会话里规则不生效）

把本文件「常驻规则模板」末尾那一节「开发规则 — dev-hygiene」写进 `$DSH_HOME/AGENTS.md`（已有内容就追加）。
本机当年的 `AGENTS.md` 改前备份在 `local\AGENTS.md.bak-20260915`。

### 第 3 步：准备 uv 环境（规则 3 的落地）

1. 全局 `uv.toml`（Windows 为 `%APPDATA%\uv\uv.toml`，其它平台用 uv 文档里的等价位置）：

   ```toml
   python-preference = "only-managed"

   [[index]]
   name = "tsinghua"
   url = "https://pypi.tuna.tsinghua.edu.cn/simple"
   default = true
   ```

   **`python-preference` 是顶层键，必须写在 `[[index]]` 之前**，写在后面会被归进表数组、静默失效。
2. `uv python install 3.12`（本机装到 `cpython-3.12.13`，20.9 MiB，直连 GitHub release 5.3 秒、**不需要代理**）。
   下不动时把 `python-preference` 改成 `managed` 或删掉，并在项目 `HANDOVER.md` 里记原因。
3. 验证：临时项目里 `uv run python -c "import sys;print(sys.executable)"` 应指向项目 `.venv`，
   且 uv 的 stderr 是 `Using CPython 3.12.13` 而**不是** anaconda 的 `D:\ProgramsDev\anaconda3\python.exe`。

### 第 4 步：验证（照 `references\验证记录.md` 复现）

```powershell
$del = "$env:USERPROFILE\.dsh\skills\dev-hygiene\scripts\Remove-ToRecycleBin.ps1"
"x" | Set-Content a.txt
pwsh -File $del 'a.txt' -WhatIf      # 预演：文件必须还在
pwsh -File $del 'a.txt'              # 真删：进回收站，回收站里能看到、能还原
pwsh -File $del '不存在.txt'          # 必须 exit=1，且不删任何东西
```

### 维护提醒

本 skill 是"活规范"：改动它就要重新整份复制到 `local\skill\dev-hygiene\` 并追加 `SKILLS.md` 日志；
它的规则若有变动，`$DSH_HOME/AGENTS.md` 里那 5 行红线与本节要同步改。

## ponytail（P2 独立类 · 网络来源）—— **已于 2026-09-17 卸载，本机不再安装**

> **状态：已卸载。** 2026-09-17 按用户要求把 6 个 `ponytail*` 目录从 `$DSH_HOME\skills\` 移入回收站；本机 profile 里没有它的条目、`AGENTS.md` 没有它的常驻规则、也没有 `.dsh\ponytail\mode` 档位文件。下面保留完整安装步骤，**只作为恢复路径**（照它可从上游重装最新版）；新环境**不要**默认装它。

- 来源：https://github.com/DietrichGebert/ponytail
- 只取：仓库 `skills\` 下的 6 个目录 —— `ponytail`、`ponytail-review`、`ponytail-audit`、
  `ponytail-debt`、`ponytail-gain`、`ponytail-help`。上游面向 Claude Code / Codex 等宿主，
  仓库里的 README、benchmark、hooks、其余适配器文件都不要。
- **优先级 P2**：跟别的 skill 互不影响，任意顺序装都行
- DSH 化改造：
  1. 每个 `SKILL.md` 的 frontmatter 只留 `name` + `description`，删掉 `argument-hint`、`license` 等字段，
     `description` 压到 500 字符以内（可加中文触发词，路由只看 name + description）；
  2. 把宿主专属说法改写成 DSH 说法：斜杠命令用 DSH 的 `/name` 显式调用；"每轮自动注入"改为
     写进 `$DSH_HOME/AGENTS.md` 的常驻规则；"给子代理注入规则"改为把契约写进 `subagent` / `workflow`
     的 prompt（DSH 子代理不继承对话）；
  3. 只保留 skill 本体，不要带入上游的安装脚本与 hooks。
- 安装：6 个目录分别复制到 `<skill 根>\<name>\`
- 验证：会话 catalog 里应出现这 6 个名字，且 `/ponytail`、`/ponytail-review` 等可以直接调用
- 不进 `local\`：它有上游来源，永远按本节拉最新版 + 重做 DSH 化改造；
  但如果本地改过它，改了什么要写进账本日志，必要时补进本节（否则新环境重建不出同样的结果）

## grilling（P2 独立类 · 网络来源）

- 来源：https://github.com/mattpocock/skills —— 单个 skill，路径 `skills/productivity/grilling/`
- 只取：`skills/productivity/grilling/SKILL.md`（原始文件：`https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grilling/SKILL.md`）。
  同目录的 `agents/openai.yaml` 只是 OpenAI 宿主的界面元数据（`display_name` / `short_description`），
  DSH 不认，**不要**；仓库其余部分（README、别的 skill、别的目录）也都不要。
- **优先级 P2**：跟别的 skill 互不影响，任意顺序装都行
- DSH 化改造：
  1. frontmatter 上游本来就是 DSH 兼容的 `name` + `description`，保持原样即可（`description` 远小于 500 字符）；
  2. 正文倒数第二段里 "dispatch a sub-agent to find it" 改写成 DSH 说法：用 `subagent` 工具、后台派发，
     并补一句"DSH 子代理不继承当前对话，必须给完整独立的 prompt"；
  3. 正文其余内容与上游逐字一致；该 skill 没有脚本、没有 hooks、不联网、不需要任何外部命令。
- 安装：把改好的 `SKILL.md` 放到 `<skill 根>\grilling\SKILL.md`
- 验证：会话 catalog 里出现 `grilling`；说"grill me on …"或直接 `/grilling` 能进入"逐轮提问 + 每问给推荐答案"的模式
- 不进 `local\`：有上游来源，永远按本节拉最新版 + 重做上面第 2 条改写；
  本地若再改它，改了什么要写进账本日志，必要时补进本节

## dsh-think-zh（P2 独立类 · DSH 插件 · 网络来源）

> **配方已固化**：`local\plugin\dsh-think-zh\RECIPE.md`（含本机解析到的 commit `06a27f64…`）。
> 下面是同一份内容的摘要，新环境照着配方装即可。

- 来源：https://github.com/Len7183/DSH-Think-zh —— 强制模型思考（reasoning）用简体中文，回复跟随提问语言
- **这是 DSH 插件，不是 skill**：**不要**复制到 skill 根目录。它装在 DSH 的 profile 里，
  由 profile 的 bundle 层组合进配置；它的备份形态是 `local\plugin\dsh-think-zh\RECIPE.md`（配方，
  不是 `node_modules` 副本）
- **优先级 P2**：跟其他 skill / 插件互不影响，任意顺序；但要在启动 DSH 之前装完
- 前置：`dsh plugin` 只是 pnpm 的转发器，机器上必须有 pnpm（`pnpm -v` 能跑；没有就 `npm install -g pnpm`）。
  本机原来没有 pnpm，是这次为装这个插件补装的（pnpm 12.4.1）
- 安装（profile 名按实际用，本机 Web GUI 用的是 `web`；等价写法 `npx @deepseek-ai/dsh ...`）：
  1. `dsh plugin --profile web add github:Len7183/DSH-Think-zh`
  2. 第一次会以 `ERR_PNPM_GIT_DEP_PREPARE_NOT_ALLOWED` 失败：pnpm 默认拦截 git 依赖的 prepare 脚本，
     而这个插件的 prepare 要跑 `tsc` 构建。把 pnpm 报错里给出的**确切键**（含它解析到的 commit，形如
     `"dsh-think-zh@https://codeload.github.com/Len7183/DSH-Think-zh/tar.gz/<commit-sha>": true`）
     加到 `~/.dsh/profiles/web/pnpm-workspace.yaml` 的 `allowBuilds:` 下（键里带 `@` `:` `/`，必须加引号），
     然后重跑第 1 步
  3. 想复现同一个版本，就把 spec 写成 `github:Len7183/DSH-Think-zh#<commit-sha>`
- 验证：
  - `~/.dsh/profiles/web/package.json` 的 `dependencies` 里出现 `dsh-think-zh`，且 `dsh.profile.bundles`
    末尾自动多出 `dsh-think-zh`（dsh 装完会自己 reconcile，不用手改）
  - `dsh --profile web --dump-config` 的输出末尾出现 `# == dsh-think-zh` 那段（含 `inject: [systemPrompt]`）
  - **必须重启 DSH**（重开 `dsh web`）：bundle 层在 profile 启动时组合，运行中的进程不会热加载
- 可调配置：在 `~/.dsh/profiles/web/cordis.patch.yml` 里给该行加 `config:`，
  `injectPrompt: false` 关掉注入，`injectionText: ...` 换成自定义指令文本
- 卸载：`dsh plugin --profile web remove dsh-think-zh`，然后重启 DSH（bundle 列表会自动更新）
- 小坑：`dsh --dump-config` 会重写 profile 里的 `cordis.yml`；在沙箱里跑会因写 profile 目录被拒，
  需要放宽到 danger-full-access 再跑

## camoufox-reverse（P2 独立类 · 本地来源）

**它是什么**：本机 Camoufox 反指纹浏览器 + `camoufox-reverse-mcp`（39 个工具，Web/JS 逆向）的配套 skill。
**skill 目录本身是自包含的轻量备份**（约 50 KB）：`scripts/` 收全部自制脚本，`references/` 收说明书与重建配方。
背后约 2.2 GB 的 Python 环境、浏览器引擎、MCP 源码都有 release / PyPI 来源，本备份**只记配方、不存内容**。

### 第 1 步：把 skill 放到位

1. 把 `local\skill\camoufox-reverse\` **整个目录**复制到 `$DSH_HOME\skills\camoufox-reverse\`
   （本机即 `C:\Users\y\.dsh\skills\camoufox-reverse\`）。
2. frontmatter 已是 DSH 原生（只有 `name` / `description`），**不需要任何改造**。
3. 验证：重启 DSH 后 skill 清单里出现 `camoufox-reverse`（或用 `skill` 工具读它）。
   备份目录不在时**先找用户要**，不要拿网上同名 skill 顶替。

### 第 2 步：重建它背后的那套环境（skill 只是说明书 + 脚本，不是环境本身）

一键（推荐）：

```powershell
pwsh -File $DSH_HOME\skills\camoufox-reverse\scripts\restore.ps1 -Root D:\AI_python\camoufox
# 只想先跑通 MCP、暂不下 1 GB 引擎：追加 -SkipEngines
```

脚本依次做：复制自制脚本到 `$Root\bin\`（`camoufox.cmd` 落到根）→ 建
`%LOCALAPPDATA%\camoufox` **目录联接**指向 `$Root\.engine\camoufox`（camoufox 用 platformdirs 硬取该路径，
环境变量改不动，且**必须在装引擎之前**建）→ `uv venv --python 3.12 --python-preference only-managed` 建独立
venv → `pip install -U "camoufox[geoip]"` → clone
`https://github.com/WhiteNightShadow/camoufox-reverse-mcp` 并 `pip install -e` → 用自带
`install-camoufox-browser.py` 装官方引擎 `152.0.4-beta.30`（sha256 `ea52a02fb1cf…`，**直连 release CDN、
不查 GitHub API**，绕开未认证 60/h 限流）→ 下载并校验定制版 `152.0.4-beta.30-reverse.5`
（sha256 `d73704543a75…`，77 点引擎追踪）→ 预热 → 冒烟测试。

手动步骤、全部固定 sha256、桌面快捷方式命令见 `references\重建配方.md`。

### 第 3 步：**必做**的预热

```powershell
D:\AI_python\camoufox\.venv\Scripts\python.exe D:\AI_python\camoufox\bin\warmup.py
```

不做这一步，第一次 MCP `launch_browser` 会失败：Camoufox 首次启动下载 uBlock Origin 时把进度打到
stdout，而 MCP 的 stdio 通道上 stdout 就是 JSON-RPC 流，客户端会报
`Failed to parse JSONRPC message ... Invalid JSON`。预热（缓存插件）后消失；再报就重跑预热。
这是本机实测踩过的坑，写在 `使用说明.md` §6.1。

### 第 4 步：接进 DSH

把 `references\重建配方.md` §4 的 `insert` 片段贴进 `$DSH_HOME\profiles\web\cordis.patch.yml`：
`dsh-mcp-client`、serverName `camoufox`、transport `stdio`、`command` 指向 venv 的 `python.exe`、
`args: ['-m','camoufox_reverse_mcp','--locale','zh-CN']`、`toolCallTimeoutMs: 120000`。
profile 是 `patchReload: live`，改完几秒生效。验证：

```powershell
dsh --profile web --dump-config | Select-String 'mcp-camoufox-reverse' -Context 0,6
```

生效后工具以 `mcp__camoufox__*` 暴露（39 个），并有一个 venv 的 `python.exe` 进程常驻。

### 前置依赖

`uv`（建 venv + 托管 CPython）、`git`（clone MCP）、`node`（`verify_signer_offline(runtime="node")` 与
`vendor/acorn.cjs` 的现代语法解析；缺失时回退 esprima）。Windows 还需 VC++ 运行库
（`VCRUNTIME140.dll` / `MSVCP140.dll`，本机自带）。

### 不迁移

`states\*.json` 与 `profiles\` 里是**可直接登录的凭据**，不进任何备份；新机器用 `camoufox.cmd`
控制台菜单 `[2]/[3]` 重新扫码登录一次即可。

### 维护提醒

`$Root\bin\` 下的脚本是"活"的，`local\skill\camoufox-reverse\scripts\` 是备份副本。改了工作区脚本、
说明书或重建配方后，要**重新整份复制**到 `local\skill\camoufox-reverse\` 并在 `SKILLS.md` 追加一行日志
（属于「已记账 skill 被修改」）。升级引擎时，tag / 资产名 / sha256 要同步改三处：
`references\重建配方.md`、`scripts\restore.ps1` 参数、`使用说明.md` §8。

**与 `dev-hygiene` 的关系**：本 skill 的「收尾清理」段已收敛为指向 `dev-hygiene`（P1 依赖类，必须先装）——
删除 / 清理的规则细节都在那份 skill 里，这里只留逆向场景的落点；改本节时不要把那些规则再抄回来。

## modsearch（P2 独立类 · DSH 插件 · 网络来源）

> **配方已固化**：`local\plugin\modsearch\RECIPE.md`（含锁定版本、全部验证命令、兼容性备注）。下面是摘要。

- 来源：https://github.com/liustack/modsearch · npm `@liustack/modsearch` —— 给不能联网的模型补上
  web 搜索 / X 搜索 / 单页抓取；默认走 Firecrawl keyless（每月 1000 免费额度、免注册免 key）
- **这是 DSH 插件（原生 bundle），不是 skill**：**不要**复制到 skill 根
- **优先级 P2**：与其它条目互不影响；但它会**替换 dsh 内置 `web_search` 的 provider**，
  装完后所有会话的搜索都走它
- 前置：Node ≥ 22.13（`doctor` 会检查）、pnpm（`dsh plugin` 的转发目标）
- 安装（**版本必须写死** —— pnpm 的 `minimumReleaseAge` 会把 `@latest` 拦回旧版）：
  ```powershell
  dsh plugin --profile web add '@liustack/modsearch@5.10.3'
  ```
  本机实测 4.2 秒完成，**没有**触发 `allowBuilds` 拦截（npm 包，不需要改 `pnpm-workspace.yaml`）。
  升级（2026-09-16，5.10.2 → 5.10.3）时 pnpm 会自动往 `pnpm-workspace.yaml` 追加一条
  `minimumReleaseAgeExclude: ['@liustack/modsearch@5.10.3']` —— 正常的放行记录，不是构建拦截
- 验证（不用重启就能做）：
  ```powershell
  dsh plugin --profile web list --depth 0
  dsh --profile web --dump-config | Select-String 'modsearch|searchProvider'
  ```
  dump 里应同时有 `searchProvider: modsearch` 与 `# == @liustack/modsearch` 插件行；
  再加 `npx -y @liustack/modsearch@5.10.3 doctor`（离线）和一次真实搜索做端到端
- **必须重启 DSH**：bundle 列表在 profile 启动时组合，运行中不会热加载
- 配置：`~/.modsearch/config.json`（0600）或环境变量 `TAVILY_API_KEY` / `EXA_API_KEY` /
  `FIRECRAWL_API_KEY`；dsh web 的 Settings → Plugins 里有 ModSearch 卡片
- 卸载：`dsh plugin --profile web remove @liustack/modsearch` + 重启（bundle 自带的 `searchProvider`
  patch 会一起消失；只有你自己覆盖过才需手动改回）
- **兼容性**：上游针对 `@deepseek-ai/dsh 0.1.0-rc.7` 验证，本机是 `0.1.5-rc.1`；
  组合检查本机已通过，运行期行为重启后确认。2026-09-16 另用 `0.1.6-alpha.1` 隔离副本对同一
  profile 跑过 `--dump-config`：`searchProvider: modsearch` 与插件行仍在，两版差异只在 dsh
  自带行，故 modsearch 不阻碍升级到 0.1.6（本机当时决定暂不升级）

## reverse-skill（P2 独立类 · skill · 网络来源）

**它是什么**：一个**安全技能路由包**（逆向工程 / 渗透测试 / CTF / 恶意样本 / 移动与固件 / 前端 JS 逆向 /
安全报告），上游 v1.0.1（MIT），共 **89 个 `SKILL.md`**（`skills\` 48 个模块 + `CTF-Sandbox-Orchestrator\`
42 个子技能）。

**关键判断：不要平铺。** 这些模块互相用相对路径引用（`../ops/`、`../config/routing.json`、
`../CTF-Sandbox-Orchestrator/...`），逐个复制进 skill 根会打断引用。本机采用的形态：

- 仓库**整包**放在 `$DSH_HOME\reverse-skill`（本机 `C:\Users\y\.dsh\reverse-skill`）；
- `$DSH_HOME\skills\` 下只放**一个自制入口 skill** `reverse-skill-router`，它的正文写明包路径与执行链。

- **优先级 P2**：跟其它 skill / 插件互不影响，任意顺序装
- 前置：`git`、Windows PowerShell 5.1+（上游脚本自带 `#Requires -Version 5.1`）；本机克隆 / 更新仓库要走代理
  **`http://192.168.21.115:7890`**（这个值**只记在本账本里**；入口 skill 的脚本一律用 `-Proxy` 或
  `$env:REVERSE_SKILL_PROXY` 传入，**不要**写死进会迁移的 skill 文件）；git 直连 GitHub 会
  `Recv failure: Connection was reset`

### 第 1 步：克隆仓库（整包）

```powershell
$Proxy = $env:REVERSE_SKILL_PROXY      # 本机 = http://192.168.21.115:7890
$Repo  = 'C:\Users\y\.dsh\reverse-skill'
$Pin   = '7e2097fd90d25c2f976f6eba26d6c00aa88051df'   # 安全审查过的 commit，别用 main 浮动版本

New-Item -ItemType Directory -Force -Path $Repo | Out-Null
git -C $Repo init -q
git -C $Repo remote add origin https://github.com/zhaoxuya520/reverse-skill.git
git -C $Repo -c http.proxy=$Proxy -c https.proxy=$Proxy fetch --depth 1 origin $Pin
git -C $Repo checkout -q FETCH_HEAD
```

本机验证过的 commit：`7e2097fd90d25c2f976f6eba26d6c00aa88051df`（`main`、depth=1、约 8 MB / 596 文件）。
**按 commit pin**（`git clone` 默认追 main，等于每次装到的都是没审查过的新代码）。
**整包搬动时 `CTF-Sandbox-Orchestrator\` 必须与 `skills\` 同级**，否则 `routing.md` 里的相对路径失效。

### 第 2 步：生成工具清单（不做这步路由就缺工具信息）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$Repo\skills\scripts\refresh-tool-index.ps1"
```

产出 `skills\tool-index.md` + `tool-index.json`（本机 tools=42）。这两个是 gitignored 的**本机生成物**，
**不进任何备份**，新机器重跑即可。

### 第 3 步：放入口 skill

把 `local\skill\reverse-skill-router\` **整个目录**复制到 `<skill 根>\reverse-skill-router\`
（3 个文件：`SKILL.md`、`references\重建配方.md`、`scripts\restore.ps1`）。它是自制的适配层，
内容不要改；要改就先改活的那份，再重新整份复制回 `local\`。

### 第 4 步：验证

```powershell
# 路由冒烟：应输出 PRIMARY -> skills/<模块>/SKILL.md
powershell -NoProfile -ExecutionPolicy Bypass -File "$Repo\skills\scripts\master-route.ps1" `
  -Hint "offline apk reverse jadx" -OutDir "$env:TEMP\rs-smoke"

# 路由自洽：应输出 ALL ROUTING COHERENCE CHECKS PASSED
powershell -NoProfile -ExecutionPolicy Bypass -File "$Repo\skills\scripts\verify-routing-coherence.ps1"
```

再确认会话 catalog 里出现 `reverse-skill-router`（skill 层即时扫描，**不需要重启 DSH**）。

### 入口 skill 与原版的差异（刻意的，别改回去）

上游 `RULES.md` 的策略是"读到就立刻执行、缺工具就自动 bootstrap 安装"。本机入口 skill 收窄为五条
（**这几条是按 skill-vetter 审查结论加的，别改回去**）：

1. **先授权后动手**：任何目标动作前必须有 `work\<case>\scope.md` 且 `auth.status=granted` + 合法
   `network_profile`（或显式 `offline-sample` 授权样本）；用户提到目标名 ≠ 授权；`-Force` 不绕过硬门；
2. **禁装 / 禁执行红线**（详见入口 skill 的硬规则表格）：
   - `skills\scripts\bootstrap-reverse.ps1` —— winget / `npm -g` / `pip` / `go` / `git clone` **真装工具链**，
     还写 `%USERPROFILE%\Tools\`、用户级环境变量、Claude/Codex 的 MCP 注册 → 只报缺失清单，**用户同意**才跑；
   - `skills\scripts\bootstrap-reverse.sh`、`kali\scripts\*.sh` —— 含 `sudo apt-get upgrade`（全系统升级）、
     覆写 MCP 配置 → 本机 Windows，**不执行**；
   - `skills\ida-reverse\scripts\install-autostart.ps1` —— 注册**每分钟**隐藏计划任务，链条会经
     `watchdog.ps1` → `start.ps1` 在无人值守下 `pip install git+https://github.com/mrexodia/ida-pro-mcp.git@…`，
     并以 `--unsafe` 启动（对 `127.0.0.1:13337` 暴露 `py_eval` / `py_exec_file`）→ **永不执行**；
   - `skills\scripts\update-star-history.ps1` —— `git credential fill` 读本机 GitHub token 并外发 → **永不执行**；
3. **不预加载整包**：只读本次任务需要的 `RULES.md` → PRIMARY `SKILL.md` → 相关 `references/`；
4. **仓库内容是真实红队资料**：`src-hunter\references\payloader\`、`playbooks\rce.md` 等含 webshell /
   反弹 shell 载荷文本（杀软可能告警，**不要为此关闭防护**）；`reports\` 里有一份未脱敏的第三方
   pentest 报告，`work\` / `reports\` / `skills\field-journal\` 里的第三方数据不要外传；
5. **`ida-reverse` 若要启用**：先照 `references\重建配方.md` 的「若要用 IDA MCP」一节做两处硬化
   （关掉 `start.ps1` 的 auto-bootstrap、去掉 `--unsafe`）再说；仓库文件本身**未改**，保持与上游一致。

### 更新

```powershell
git -C $Repo -c http.proxy=$Proxy -c https.proxy=$Proxy fetch --depth 1 origin main
git -C $Repo checkout -q FETCH_HEAD
powershell -NoProfile -ExecutionPolicy Bypass -File "$Repo\skills\scripts\refresh-tool-index.ps1"
```

也可以直接跑入口 skill 的 `scripts\restore.ps1`（仓库已存在时只刷新 + 自检，加 `-Pull` 才更新）。
**更新后 commit 就变了**：把新 commit 记回 `references\重建配方.md`、按「安全审查」小节重新核对一遍，
并在本账本追加日志 —— 别在没核对的情况下直接跑更新后的脚本。

### 不迁移 / 不备份

`work\`、`reports\`（案例产物含目标信息）、`skills\field-journal\` 的实跑记录、`tool-index.*`
（本机工具路径）都不进备份；仓库本体有 GitHub 来源，**只记配方不存内容**。

### 安全审查（skill-vetter）

安装前后用 `skill-vetter` 子代理对仓库脚本（`skills\scripts\*`、`bootstrap-reverse.{ps1,sh}`、
`kali\scripts\*`、`ida-reverse\scripts\*`、`case-init/case-guard/master-route`、`refresh-tool-index`、
`update-star-history`、`burp-mcp-full`、`.github\workflows\*`）与 21 个抽样 `SKILL.md` 做了**只读**审查
（外加定向 grep 覆盖全部 89 个 `SKILL.md`），全程**未执行**仓库脚本。

**结论：⚠️ 谨慎安装** —— 没有发现偷凭据 / 外发本机数据 / 混淆代码 / 绕过授权门禁 / 提示注入的行为，
反而自带供应链自检（`verify-repository-security.py`：二进制哈希白名单、CI action 全部 pin 40 位 SHA、
禁止 `Invoke-Expression` / `curl|sh`），工程质量高于同类包；**风险等级 🔴 HIGH**，因为上游是**真实红队
工具包**（webshell / 反弹 shell 载荷文本约 72 文件 / 3.5 MB、EDR 规避与完整攻击链、真装系统软件的能力），
且存在**无人值守的自动装码链**与 `--unsafe` 任意 Python 执行面（见上面红线第 2、5 条）。

**审查提出的 5 项加固，本机已全部落实**：① 薄适配层（不平铺 89 个 skill）✅；② 禁装 / 禁执行写成硬约束 ✅；
③ 代理参数化 + `SKILL.md` 不含内网 IP + 克隆 pin commit ✅；④ `update-star-history.ps1` 永不执行 ✅；
⑤ `install-autostart.ps1` 永不执行 + 给出启用 `ida-reverse` 前的 `start.ps1` 两处硬化方案 ✅
（仓库文件未改，保持与上游可 `git pull`）。

**已核实无问题的几处**（下次核对可复用）：`master-route.ps1` / `refresh-tool-index.ps1` 只读本机、不联网；
`case-guard.ps1` 明确 `-Force does not bypass scope hard gates`；Burp MCP 桥与服务端只绑 `127.0.0.1`
且强制 Bearer 鉴权、全仓无 `Runtime.exec`；Kali 安装器对 GitHub Release 资产强制 SHA-256、缺值 fail-closed；
`CTF-Sandbox-Orchestrator/` 136 个文件里 0 可执行代码；两个 PNG 以 `IEND` 正常结束（非 polyglot）。
**唯一未核实项**：`gradle-wrapper.jar` 的 SHA256 与仓库自检白名单一致，但有说法称它对应 Gradle 8.10–8.12
而 `gradle-wrapper.properties` pin 的是 8.7 —— 属"待上游确认"，不是已确认的篡改。

**审查建议本机不要保留的东西**（本机**未删**，仓库保持完整；要删再单独确认）：
`reports\2026-05-26_new-hahacc-ctf-pentest-report.md`（未脱敏真实域名 + PoC）、
`skills\pentest-tools\src-hunter\references\payloader\`（52 文件 / 2.67 MB 载荷文本）、
`playbooks\{intranet-postexp,rce,sqli}.md`、`skills\attack-chain\`、`skills\edr-bypass-re\`、
`kali\`（Windows 用不上且带 `apt upgrade`）、`burp-mcp-full\`（不构建就没用）、
`CTF-Sandbox-Orchestrator\`（不玩 CTF 可不留）、`examples\`、`docs\`、`reverse-skill.png`。

---

## dsh-ding（P2 独立类 · DSH 插件 · 网络来源）

用途：对话完成 / 长任务运行中 / Agent 提问 / 工具审批等待时提醒 —— 播放提示音 + 弹 **Windows 原生通知**，
WebUI 对话页顶栏带铃铛（单击开关音、悬停调音量、右键选/传音效 + 高级设置）。
**完整配方在 `local\plugin\dsh-ding\RECIPE.md`** —— 只记**来源与安装命令**、**不锁版本**
（升级就是重跑同一条命令装最新版）；下面是同内容的执行版。

### 第 1 步：装进 profile（**不要**复制到 skill 根）

前置：**pnpm**（`dsh plugin` 只是它的转发器）、**Windows**（通知走 PowerShell + WinRT toast）。

```powershell
dsh plugin --profile web add github:CAOGGL/dsh-ding
# 升级也是这一条：它取仓库最新 commit，不需要版本号
```

本机实测 **4.6 秒**装完、**未触发** `allowBuilds` 拦截（该包 `package.json` 没有 `scripts`，
`lib\index.js` 与 `lib\client.js` 是随包分发的预构建产物，pnpm 无 prepare 可跑）。
若新环境被 pnpm 拦构建：把 pnpm 报错里给出的**那个键原样**（键含 `@` `:` `/` 与它当时解析到的
commit，**必须带引号**）写进 `~/.dsh/profiles/web/pnpm-workspace.yaml` 再重跑 ——
键里的 commit 随版本变，照报错现填，别抄旧值。

### 第 2 步：核对 profile 配置

`~/.dsh/profiles/web/package.json` 里：`dependencies` 多出 `"dsh-ding": "github:CAOGGL/dsh-ding"`，
`dsh.profile.bundles` 末尾多出 `"dsh-ding"`（由 dsh 自动 reconcile，**少了它插件不会加载**）。
包体落在 `~/.dsh/profiles/web/node_modules/dsh-ding/`。

### 第 3 步：验证（不用重启的两步）

```powershell
dsh plugin --profile web list --depth 0                      # 应出现 dsh-ding@<当前最新版>
dsh --profile web --dump-config | Select-String 'dsh-ding'   # 应出现 # == dsh-ding 段落
```

也可以单独试通知脚本（响一次铃 + 弹一条 toast）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.dsh\profiles\web\node_modules\dsh-ding\notify.ps1" -Title "测试" -Text "dsh-ding 工作正常"
```

### 第 4 步：**必须重启 DSH**

**bundle 列表在 profile 启动时组合，运行中的进程不会热加载。** 装完必须重启 `dsh web` 才生效。
重启后验证：① 对话页顶栏出现**铃铛**；② 跑一轮对话并切到别的窗口，结束时应**响铃 + 弹通知**；
③ 点通知应拉起浏览器并**直达对应会话**。

### 运行期副作用与卸载

首次提醒时插件自动做三件事（都只动 HKCU / 用户级，不需要管理员）：注册 AppUserModelID
**`DshDing.Notifier`**（开始菜单快捷方式 `dsh-ding-notifier.lnk`，未注册 AUMID 的 toast 会被 Windows 静默丢弃）、
注册 `dsh-ding://` 协议（`HKCU:\Software\Classes\dsh-ding`，命令走 `wscript` + `toast-activate.vbs` 无黑窗）、
把设置写进 `~/.dsh/profiles/web/data/dsh-ding.json`（自传音效在 `data/sounds/`）。

卸载：

```powershell
dsh plugin --profile web remove dsh-ding     # 然后重启 dsh
```

**残留不会自动清**（下次重装会重建）：`%APPDATA%\Microsoft\Windows\Start Menu\Programs\dsh-ding-notifier.lnk`、
`HKCU:\Software\Classes\dsh-ding`、`~/.dsh/profiles/web/data/dsh-ding.json` 与 `data/sounds\`、
`%TEMP%\dsh-ding-*.log` —— 具体命令见配方。**本机删除一律走 `dev-hygiene` 的
`scripts\Remove-ToRecycleBin.ps1`，不要用 `Remove-Item`。**

### 安全说明（安装时做的只读检查）

该插件会用 `spawn('powershell.exe', …)` 调包内 `notify.ps1`（响铃 + toast）、通知点击时调 `toast-activate.ps1`
—— 这是功能必需。只读扫描结论：全包无 `Invoke-Expression` / 下载外联 / `-EncodedCommand`，
唯一一处 `FromBase64String` 在 `toast-activate.ps1`（解码协议参数里的 sessionId / baseUrl），无异常。

### 维护提醒

**升级就是重跑安装命令**（`dsh plugin --profile web add github:CAOGGL/dsh-ding`）再重启 DSH ——
配方里不记版本，无需回写任何东西。
它运行期产生的自定义音效（`data/sounds/`）与 `node_modules` 都**不进备份**。

---

## dsh-pentest（P2 独立类 · DSH 插件 · 网络来源）

用途：DSH 的**渗透测试模式** —— 按会话记录目标 / 线索 / 事实 / 漏洞 / 资产与探索链路，Web 里以
「渗透」标签页（探索链路 / 漏洞 / 资产 / 报告）展示。它是**自包含 bundle**：宿主插件 + Web 界面 +
sqlite 后端同包分发，从单个 release tarball 就能装。
**完整配方在 `local\plugin\dsh-pentest\RECIPE.md`** —— 只记**来源与安装命令**、**不锁版本**
（`latest/download` 每次取最新 release）。

### 第 1 步：装进 profile（**不要**复制到 skill 根）

前置：**pnpm**（`dsh plugin` 只是转发器）、**Node ≥ 22.5**（sqlite 后端用 `node:sqlite`）。

```powershell
dsh plugin --profile web add https://github.com/howmp/dsh-pentest/releases/latest/download/dsh-pentest.tar.gz
# 升级也是这一条（latest 永远取最新 release）；也可以先下载再本地装：
# dsh plugin --profile web add file:C:\path\to\dsh-pentest.tar.gz
```

- **不需要 `allowBuilds`**：`scripts` 只有 `test`，发布资产里 `lib/**/*.js` 已是构建产物，
  pnpm 没有 prepare 可跑（`pnpm-workspace.yaml` 里没有它的键）。
- 配方里**不记版本 / tag / 校验和**：它是 tarball 依赖，装最新版即可，记了也会随升级立刻过期。

### 第 2 步：核对 profile 配置

`~/.dsh/profiles/web/package.json` 的 `dependencies` 多出
`"@howmp/dsh-pentest": "https://github.com/howmp/dsh-pentest/releases/latest/download/dsh-pentest.tar.gz"`，
`dsh.profile.bundles` 里多出 `"@howmp/dsh-pentest"`（少了它插件不会加载）。
包体落在 `~/.dsh/profiles/web/node_modules/@howmp/dsh-pentest/`。

### 第 3 步：验证（不用重启）

```powershell
dsh plugin --profile web list --depth 0            # 应出现 @howmp/dsh-pentest@<当前最新版>
dsh --profile web --dump-config | Select-String 'pentest' -Context 0,6
```

dump 里应有四处：`# == @deepseek-ai/dsh-base, patched by @howmp/dsh-pentest` 下的
`storage-domain` 路由 `pentest: sqlite`、`# == @howmp/dsh-pentest` 下的 `ui-pentest`（`name: '@howmp/dsh-pentest'`）、
`storage-sqlite`（`name: '@howmp/dsh-pentest/storage-sqlite'`）、以及 `pentest-preset-root`
（`name: '@howmp/dsh-pentest/preset-root'`）。本机实测四处都在。

### 第 4 步：**必须重启 DSH**

bundle 列表在 profile 启动时组合，运行中不热加载。重启 `dsh web` 后：新会话的预设列表里出现
**「渗透模式」**，选中后对话页多出**渗透标签页**，模型具备 9 个 `pentest_*` 工具
（这些工具**只在 `pentest` 预设下注册**，profile 层刻意不重复注册，否则会复制作用域工具目录导致客户端命令失效循环）。

### 兼容性（重要）

`peerDependencies` **严格 pin** 在 dsh 内部包 `0.1.0-rc.6`（`dsh-invariants` / `dsh-storage` /
`dsh-storage-domain` / `dsh-tools`）+ `@deepseek-ai/cordis ^4.0.1`。
**它是这几个插件里对 DSH 升级最敏感的一个**（历史上被 DSH 升级弄坏过数次）。
升级 dsh 本体之前先核对 `dsh-storage` 的 `StorageError` / `UNIT_NAME_RE` / `storageBackendServiceKey`、
`dsh-storage-domain` 的 `defineDomain` / `domainTable`、`dsh-tools` 的 `defineTool` 是否仍导出
（2026-09-16 对 `0.1.6-alpha.1` 的隔离预检：全部齐全）。

### 运行期数据与卸载

渗透记录写入 `$DSH_HOME/storages/pentest-sessions.db`（sqlite，仅 `pentest` 域走 sqlite，其它域仍是 json）。

```powershell
dsh plugin --profile web remove @howmp/dsh-pentest    # 然后重启 dsh
```

残留只有那个 `.db`（按需保留或删；**本机删除走 `dev-hygiene` 的 `scripts\Remove-ToRecycleBin.ps1`**）。

### 维护提醒

**升级就是重跑安装命令**（那条 `latest/download` 地址）再重启 DSH —— 配方里不记版本，无需回写任何东西；
升级 dsh 本体后若渗透模式坏了，等上游新 release 再重跑同一条命令。
想改渗透的提示词/工具集：预设不支持继承，整目录复制 `preset\pentest\`（保留 `pentest-` 前缀会立即显示）。
`storages\pentest-sessions.db` 是运行期数据，不进备份。

## donsetch（P2 独立类 · DSH 插件 · 网络来源）

本体 = DonSeTch（Rust 单二进制，https://github.com/dondai44423/donsetch ，AGPL-3.0）：给 AI agent 用的
网页抓取 / 搜索 / 爬虫 / PDF OCR，零 API key、零账号、全本地自研（Chrome 真实 TLS 指纹 + 自研 HTTP/2 +
无头浏览器绕反爬 + 本地 ONNX 语义重排）。插件壳 = donsetch-dsh（https://github.com/dondai44423/donsetch-dsh），
把本体注册为 DSH **进程内原生工具**（`donsetch_web_fetch` / `donsetch_web_search` / `donsetch_web_crawl` /
`donsetch_status`，非 `mcp__*` 前缀），首次启动自动下载本平台二进制并 SHA256 校验、按 24h 节流自动升级。

**与 modsearch 的选择**：modsearch 走云端 Firecrawl keyless（每月 1000 免费额度、免注册），轻、快、够日常；
donsetch 全本地、能力上限高（绕 Cloudflare/DataDome、PDF OCR、`focus`/`toc` 省 token、续传爬虫、登录会话、
BYOK），但要下 ~19MB 二进制、配置面大、AGPL-3.0。**两者可共存**（工具名前缀不同，不冲突）；
donsetch 的登录墙处理与自动路由统一由 `web-search-router` skill 负责（见下一节）。

**本机已卸载全局 CLI（2026-09-28，用户要求）**：只装插件、不装 `npm install -g donsetch`。
CLI 型操作（doctor / login / keys）一律用插件下载的内置二进制（`~\.cache\donsetch\dsh\bin\...\donsetch.exe`，
定位与示例见下方）。截图工具插件壳未暴露、CLI 又已卸载 → 本机不可用。

配方在 `plugins\donsetch\RECIPE.md` —— 装法：

```powershell
dsh plugin --profile web add github:dondai44423/donsetch-dsh
```

要点：

- 前置：**pnpm**、Node ≥ 22.19；装完**首次启动必须联网**（下二进制）。
- ⚠️ **需要代理的机器：首次安装下载会失败**（插件用 `node:https.request`，**不读** `HTTPS_PROXY` / `NODE_USE_ENV_PROXY`），
  症状 = `could not reach .../releases/download (network down?)` + `registered tools (0)`，且**失败被缓存、只能重启 dsh web**。
  绕法：用能走代理的 `fetch` 取 release tarball + 官方 `.sha256` 校验，解包后**整目录（`donsetch.exe` +
  `onnxruntime.dll` + `pdfium.dll`，缺 DLL 会 exit 1 无输出）**落位到
  `%USERPROFILE%\.cache\donsetch\dsh\bin\<版本>\`，再重启。完整步骤与预检见 `plugins\donsetch\RECIPE.md`。
  本机（2026-09-28）即以此法补上 v4.3.7 并验证通过。
- git 依赖但 `dist/` 已提交 → **没有 prepare 构建，不触发 `allowBuilds`**（本机实测 5.2 秒装完，
  `pnpm-workspace.yaml` 零改动）。
- 装完 `package.json` 应有：`dependencies` + `"@dsh-external/donsetch": "github:dondai44423/donsetch-dsh"`、
  `dsh.profile.bundles` 末尾 + `"@dsh-external/donsetch"`。
- CLI 操作走内置二进制（本机无全局 CLI，安装时 `doctor` 实测全绿）：
  ```powershell
  $d = Get-ChildItem "$env:USERPROFILE\.cache\donsetch" -Recurse -Filter donsetch.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  & $d.FullName doctor            # 二进制/网络/TLS/浏览器/搜索健康全扫
  & $d.FullName login <域名>       # 登录墙站点（弹出真实浏览器，见 web-search-router SOP）
  ```
- **必须重启 DSH**（bundle 层不热加载，与 modsearch 同）。重启后会话应出现 `donsetch_*` 工具，
  可用 `donsetch_status` 自查。
- 卸载：`dsh plugin --profile web remove @dsh-external/donsetch`，重启 DSH；缓存 `~/.cache/donsetch/` 手动清。
- 配置（可选，不配即用）：插件选项走 bundle patch（`toolPrefix` / `channel` / `autoUpdate` / `callTimeoutMs` 等），
  本体键/代理/登录走内置二进制的 `keys` / `proxy` / `login`。

## web-search-router（P2 独立类 · 本地自制 skill）

**它是什么**：本机联网检索的**自动路由规则**。用户不说工具名（`donsetch_web_search` 之类），由模型按意图选工具：

| 意图 | 工具 |
|---|---|
| 普通关键词搜索（时效/新闻/一般查询） | `web_search`（modsearch 插件接管，Firecrawl keyless，省额度） |
| X / Twitter 内容 | `x_search` |
| 单页精读（普通站） | `read_page` |
| 反爬 / JS 壳 / PDF（含扫描件） | `donsetch_web_fetch`（本地无头浏览器 Solve-and-Bounce + OCR） |
| 多引擎交叉 / 技术向检索 / 更多权威源 | `donsetch_web_search` |
| 整站 URL 地图 / 同域爬取 | `donsetch_web_crawl` |
| 401/403 / 跳转登录 / 付费墙 | **登录墙 SOP**（见下） |

**登录墙 SOP（用户硬性要求：弹出网页、等登录、再继续）**：用 donsetch 内置二进制跑
`donsetch login <域名>` → 用户桌面**弹出真实浏览器** → agent **停下明确告知用户去登录，等用户回复** →
登录后 cookie 入 vault → `donsetch_web_fetch` 对同域名自动带登录态重试。凭据只由用户在浏览器输入。
细则（含失败降级）全在 skill 的 `SKILL.md`。

装法：把 `skills\web-search-router\` 整个目录复制到 `$DSH_HOME\skills\web-search-router\`（DSH 原生，即时生效，**无需重启**）。
同时把 `config\AGENTS.md` 里「搜索与联网检索 —— 自动路由」那段常驻规则写进 `$DSH_HOME/AGENTS.md`
（本机已生效；它让每个会话默认按本路由行事，不依赖 skill 是否被显式加载）。


## wmpf-miniapp-reverse（P2 独立类 · 本地来源）

**它是什么**：本机 WMPFDebugger（微信小程序远程调试 / 逆向工具：Frida 注入 `WeChatAppEx.exe`
+ CDP 代理 + 浏览器内置 DevTools 前端）的配套 skill。
**skill 目录本身自包含**（7 文件约 38 KB）：`scripts\` 收自制脚本（一键重建、两个启动脚本、
链路排障探针），`references\` 收详细说明书与重建配方。
背后 `node_modules` 约 148.5 MB（其中 frida 预编译二进制 115 MB）有 npm / GitHub 来源，
本备份**只记配方、不存内容**。

### 第 1 步：把 skill 放到位

1. 把 `local\skill\wmpf-miniapp-reverse\` **整个目录**复制到 `$DSH_HOME\skills\wmpf-miniapp-reverse\`
   （本机即 `C:\Users\y\.dsh\skills\wmpf-miniapp-reverse\`）。
2. frontmatter 已是 DSH 原生（只有 `name` / `description`），**不需要任何改造**。
3. 验证：会话 catalog 里出现 `wmpf-miniapp-reverse`（skill 层是即时扫描，**不需要重启 DSH**）。
   备份目录不在时**先找用户要**，不要拿网上同名 skill 顶替。

### 第 2 步：重建它背后的那套环境（skill 只是说明书 + 脚本，不是环境本身）

一键（推荐）：

```powershell
pwsh -File $DSH_HOME\skills\wmpf-miniapp-reverse\scripts\restore.ps1 `
     -Root D:\AI_python\reverse\vmpfdebugger -Proxy http://127.0.0.1:7890
```

脚本依次做：检查前置（`node` ≥ 22 / `corepack` / `git`）→
`git clone --depth 1 https://github.com/evi0s/WMPFDebugger.git`（已存在则跳过）→
`corepack yarn install --frozen-lockfile` → 把两个启动脚本落位到 `$Root` →
校验（`tsc --noEmit`、`ts-node --version`、`frida.getLocalDevice()`）。

**代理不是可选项**：frida 的 115 MB 预编译二进制从 GitHub release 下载，直连多半超时。
不想重装依赖时可用 `-SkipClone` / `-SkipInstall` 只做落位与自检（本机实测这条路径 warn 0、exit 0）。

手动步骤、依赖版本、验证表与全套踩坑见 `references\重建配方.md`。

### 第 3 步：验证（不依赖微信）

```powershell
cd D:\AI_python\reverse\vmpfdebugger
node node_modules\typescript\bin\tsc --noEmit                                   # 期望：无输出，exit 0
node -e "require('frida').getLocalDevice().then(d=>console.log(d.name))"        # 期望：Local System
```

端到端（需要微信在跑、且目标 WMPF 版本已适配；本机 16467）：

```powershell
.\start-debugger.ps1
# 期望：debug server 9421 + proxy server 62000 + [frida] script loaded, WMPF version: 16467, pid: <pid>
# 然后在微信里打开（或关掉重开）小程序 -> 期望 [miniapp] miniapp client connected
.\open-devtools.ps1        # 浏览器地址栏 Ctrl+L / Ctrl+V / 回车 -> 期望 [cdp] CDP client connected
node $DSH_HOME\skills\wmpf-miniapp-reverse\scripts\probe-cdp.js   # 期望：有对 Runtime.enable 的响应
```

**顺序绝对不能反**（先起调试器 → 再开小程序 → 最后开 DevTools），否则小程序闪退；
`devtools://` 链接**只能手工粘贴到地址栏**，当命令行参数传给浏览器会被忽略。

### 前置依赖

`node` ≥ LTS v22、**corepack** 提供的 yarn 1.22.22（上游明确要求 yarn，**不要用 npm**，且
**不要删 `yarn.lock`**）、`git`、一个 HTTP 代理（仅安装期）。被调试端是本机微信 4.x。
调试前端复用系统已有 Chromium 系浏览器（本机 Edge 143 实测可用），**不要额外装 Chromium**。

### 不迁移 / 不备份

`node_modules\`（148.5 MB，`yarn.lock` 锁版本、一条命令可重装）、`screenshots\`（上游约 12 MB 说明图）、
以及工具目录本身（有 GitHub 来源，`git clone` 即可）。本工具**不持有任何凭据**；
微信登录态始终在微信进程里，与本工具无关。

### 维护提醒

`$Root\` 下的 `start-debugger.ps1` / `open-devtools.ps1` 是"活"的，本 skill 的 `scripts\` 是权威副本 ——
改一处必须同步另一处，并**重新整份复制**到 `local\skill\wmpf-miniapp-reverse\`，
再在 `SKILLS.md` 追加一行日志（属「已记账 skill 被修改」）。
微信升级带来新 WMPF 版本时，先查 `frida\config\win32\addresses.<新版本>.json` 是否存在，
不存在就按 `references\使用说明.md` 第 7 节处理（`-AutoDetect` / 等上游 / 自行适配）。

**与 `dev-hygiene` 的关系**：删除与清理一律走那份 skill 的回收站实现，本 skill 只写逆向场景的落点。

---

## firerpa（P2 独立类 · skill · 网络来源）

**它是什么**：用 FIRERPA / lamda 写**可复用的 Android 自动化脚本**的 skill —— 设备连通性检查、App 预检、
UI 树 dump、选择器（selector）驱动的校验与交互、文本读写、等待工具、App 断言。
最终交付物必须是**一个落盘的 Python 自动化脚本**，不是一次性的设备操作。

**只取哪一部分**：整个仓库 `https://github.com/firerpa/skills` 里**只有 `firerpa/` 一个 skill**
（另有 `README.md` / `.gitignore` / 空 `requirements.txt`，都不要）。
把 `firerpa/` 这个目录**整份**放进 skill 根即可，**不要**只挑 `SKILL.md`。

### 第 1 步：把 skill 放到位

1. 取仓库（本机 shell 的 TLS 是坏的，见下面「已知坑」）：

   ```powershell
   # 用任一能走通 TLS 的通道拉 zip，例如 python 的 urllib
   python -c "import urllib.request;urllib.request.urlretrieve('https://codeload.github.com/firerpa/skills/zip/refs/heads/main', r'D:\temp\firerpa-skills.zip')"
   ```
2. 解压后把 `skills-main\firerpa\` **整个目录**复制到 `$DSH_HOME\skills\firerpa\`
   （本机即 `C:\Users\y\.dsh\skills\firerpa\`）。上游是 **36 文件 / 约 817 KB**：
   `SKILL.md`、`requirements.txt`、`scripts\firerpa.py`、
   `client\`（`client.py` + `const.py` + `exceptions.py` + `types.py` + `rpc\*.proto` + `google\protobuf\*.proto`）、
   `references\`（`reference.md` + `llms-full.txt` 496 KB）。
   盖上融合版 `SKILL.md` 后仍是 **36 文件 / 约 847 KB** —— 本机内容全部在 `SKILL.md` 内，不新增文件。
3. frontmatter 上游已是 **DSH 原生**（只有 `name` / `description`，248 字符），**不需要改造**；
   正文对 `scripts/firerpa.py`、`client/client.py` 的引用都是目录内相对路径，自洽。
4. 验证：会话 catalog 里出现 `firerpa`（skill 层即时扫描，**不需要重启 DSH**）。

### 第 2 步：盖上融合版 `SKILL.md`（**本机适配层就是一个文件**）

本机适配层 = **一个融合版 `SKILL.md`**（上游原文全保留 + 本机实测内容并入，**自包含 54,460 字节 / 992 行**），
整份备份在 `local\skill\firerpa\`（另含 `README.md` 重建说明）。

```powershell
$bk = '<账本目录>\local\skill\firerpa'
$sk = "$env:USERPROFILE\.dsh\skills\firerpa"

# 整份覆盖 —— 融合版已含上游全部规范，装完即可用
Copy-Item "$bk\SKILL.md" "$sk\SKILL.md" -Force
```

- **推荐直接覆盖**。⚠️ 代价：会丢掉上游此后对 `SKILL.md` 的更新 ——
  若上游有更新，先 `diff` 上游新版与本地融合版，把上游新增内容并进来，再覆盖。
- **没有单独的 `references\知识库.md`**：本机内容全部在 `SKILL.md` 里，
  **加载 skill 一次即全部到位，不存在"再读第二个文件"的二次动作**。
- 融合版比上游多了什么，见 `local\skill\firerpa\README.md` 的对照表（§0 铁律 / §2 环境实测 /
  §3 接入 SOP / §5 CLI 实测 / §7 配方 / §8 排障 / §9 反检测 / §10 卸载）。
- 验证：打开 `SKILL.md` 应能看到 `## 0. 铁律` 与 `## 2. 本机环境现状`；
  会话 catalog 出现 `firerpa`（skill 层即时扫描，**不需要重启 DSH**）。

### 第 3 步：建它背后的 uv 环境（skill 目录里**不含**运行时）

```powershell
uv venv --python 3.12 --python-preference only-managed D:\AI_python\firerpa\.venv
uv pip install --python D:\AI_python\firerpa\.venv\Scripts\python.exe `
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple "lamda[full]"
```

- 本机实测：uv 托管 CPython **3.12.13**，装出 **15 个包**（`lamda==10.8`、`frida==17.19.0`、
  `grpcio==1.81.1`、`grpcio-tools==1.81.1`、`cryptography==50.0.1`、`protobuf==6.33.6`、
  `msgpack==1.2.2`、`pem==23.1.0`、`pyreadline==2.1`、`setuptools`、`typing-extensions`、`cffi`、
  `pycparser`、`asn1crypto`、`grpc-interceptor`），占 **160.1 MB / 983 文件**，约 1 分钟。
- `requirements.txt` 只写 `lamda[full]>=10.0`，**不锁版本**；想固定就照 `requirements.txt` 装。
- **遵守 `dev-hygiene`**：一律 uv、**不要**用 anaconda 的 pip；本机 uv 缓存与托管 Python 在
  `D:\AI_python\_uvcache`、`D:\AI_python\_uvpython`。
- 它需要 `frida` 才能用图像匹配 / 部分能力，所以 `[full]` 别省。

### 第 4 步：设备端接入（本机是雷电模拟器，**已实测**）

完整实操见 `SKILL.md` 的 **§3 首次接入 SOP**。本机已验证的路径：

```powershell
$adb = 'D:\ProgramsDev\adb\adb.exe'
$cli = "$env:USERPROFILE\.dsh\skills\firerpa\scripts\firerpa.py"
```

| # | 做什么 | 命令 | 通过标准 |
|---|---|---|---|
| 1 | 确认设备在 | `& $adb devices -l` | `emulator-5562  device`（**非默认 5555**） |
| 2 | 确认服务端已装 | `& $adb -s emulator-5562 shell pm list packages` | 含 `package:com.firerpa` |
| 3 | 确认服务在跑 | `& $adb -s emulator-5562 shell "su -c 'netstat -tlnp \| grep 65000'"` | `lamda` 在 LISTEN |
| 4 | **建端口通道** | `& $adb -s emulator-5562 forward tcp:65000 tcp:65000` | 输出 `65000` |
| 5 | 连通性探针 | `& $Py $cli server-info --host localhost` | `version=10.8` |

⚠️ **本机最关键的一条**：模拟器内部 IP `172.16.1.4` 属 **NAT 网段**，**PC 直连 65000 不通**
（实测 `Test-NetConnection 172.16.1.4 -Port 65000` = `False`）→ **必须走 `adb forward` + `--host localhost`**。
这个转发在模拟器重启 / adb server 重启后**会失效**，连不上时第一件事就是重跑第 4 行。

服务端**没装**时（本机已装；换机器或重装模拟器才需要）：

```powershell
# ① 下 APK（本机 shell 的 TLS 是坏的，用 python urllib）
python -c "import urllib.request;urllib.request.urlretrieve('https://device-farm.com/assets/apk/firerpa.apk', r'firerpa.apk')"
# ② 装
& $adb -s emulator-5562 install -r firerpa.apk
# ③ 打开 APP（包名 com.firerpa）→ 若提示 Install required 就点 Download now
# ④ 回控制台确认 IDENTITY=root、ABI=x86_64 → 点 Start Service（状态先 CHECKING，几秒后变"运行中"）
```

其它安装方式（Magisk 模块 / 手动 tar.gz）见 `SKILL.md` §3.2 —— 注意手动装要下 **x86_64** 包
（官方文档示例写的是 arm64-v8a，本机架构不同）。

⚠️ **两个 adb 会互杀**：系统 `D:\ProgramsDev\adb\adb.exe`(1.0.41/36.0.0) 与雷电自带
`D:\leidian\LDPlayer9\adb.exe` 进程同时在跑、抢 5037 端口 → **全程固定用系统 adb 全路径**，
连接异常时先 `kill-server` 再重来。

### 第 5 步：验证

```powershell
$Py = 'D:\AI_python\firerpa\.venv\Scripts\python.exe'
& $Py -c "from lamda.client import Device, Selector, Bound, Keys, Point; import lamda; print('lamda OK', lamda.__version__)"
# 期望：lamda OK 10.8

& $Py "$env:USERPROFILE\.dsh\skills\firerpa\scripts\firerpa.py" --help
# 期望：usage 里列出 26 个子命令（dump / screenshot / app-start / app-check / click / exists / scroll-to …），exit 0
```

真机端到端（需要用户提供 FIRERPA 设备地址，或 `lamda.pem`）：

```powershell
& $Py "$env:USERPROFILE\.dsh\skills\firerpa\scripts\firerpa.py" device-info --host <设备IP>
& $Py "$env:USERPROFILE\.dsh\skills\firerpa\scripts\firerpa.py" dump -o ui.xml --host <设备IP>
```

环境变量 `DEVICE`（默认 host）/ `CERTIFICATE`（TLS 时的 `lamda.pem`）/ `PORT`（默认 65000）
可省掉每次传参；**设备地址必须问用户，不要猜**（skill 正文对此有硬性要求）。

### 已知坑

- **本机 shell 的 TLS 是坏的**，拉这个仓库会连撞三种错：`Invoke-WebRequest` 报
  `Authentication failed`；`curl.exe` 报 `schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS (0x8009030E)`；
  `git clone` 报 `error: cannot create standard input pipe for remote-https: Permission denied`（后者是沙箱
  具名管道的已知边界，不是网络问题）。**可行通道**：用 python 的 `urllib.request` 拉
  `https://codeload.github.com/firerpa/skills/zip/refs/heads/main`（本机 240825 字节）。
- **不要**用 Anaconda 的 python 跑这个 skill，只用第 3 步那个 `.venv` 的解释器。
- skill 正文要求：只用 `scripts/firerpa.py` 做设备检查，**不要**写一次性 `python -c` / 临时探测脚本；
  交付物必须是落盘的自动化脚本。

### 维护提醒

- **上游更新时**：重取 `firerpa/` 与融合版 `SKILL.md` 对比，把上游新增内容并进融合版再覆盖。
  这属「已记账 skill 被修改」，要重新同步到 `skills\firerpa\` 并在 `SKILLS.md` 追加日志。
- **改融合版 `SKILL.md` 时**：它自包含（没有第二个文件要同步）→
  改完重新同步到 `skills\firerpa\`，再追加日志；两边必须一致（用 SHA256 核对）。
- **环境变了**（换模拟器 / 服务端升级 / 端口或目录变化）→ `SKILL.md` §2、§3 的实测值会过期：
  重跑「第 4 步：设备端接入」的 5 条验收并更新 §2。
- **备份额度**：`skills\firerpa\` 里是**完整内容**（36 文件 / 842 KB，含上游 `client\` 与 `llms-full.txt`）；
  `.venv`（约 160 MB / 983 文件）有 PyPI 来源可重装，**不入仓库**。

---

## MCP（P2 独立类 · 网络来源 + 本地运行时）

本机在 `<profile>\cordis.patch.yml` 里挂了 **4 个 MCP server**。它们**不是 skill、也不是 npm 插件**，
而是一条 DSH 配置（`@deepseek-ai/dsh-mcp-client` 的 `insert` 条目）—— 但同样必须迁移，
否则新环境会少掉这些工具。配置文件整份备份在 **`config\cordis.patch.yml`**。

装法：把 `config\cordis.patch.yml` 放到 `<profile>\cordis.patch.yml`（与 profile 三件配置配套），
再重建下面各自的运行时。**装完必须重启 DSH**（MCP 在 profile 启动时组合；本机实测 `patchReload: live`
下**新增 MCP 挂载会即时热加载**，但重启一次更保险）。

| MCP | `serverName` | 工具前缀 | 依赖的运行时 |
|---|---|---|---|
| camoufox | `camoufox` | `mcp__camoufox__*` | `D:\AI_python\camoufox\.venv`（约 2.3 GB，见下） |
| jadx | `jadx` | `mcp__jadx__*` | `D:\AI_python\MCP\MCP合集\jadx-mcp-server`（约 41 MB，见下） |
| ida | `ida` | `mcp__ida__*` | 本机 IDA 9.4 的 idalib（无独立目录，`uvx` 跑 PyPI 包，见下） |
| context-mode | `context-mode` | `mcp__context-mode__*` | 全局 npm 包（`npm install -g context-mode`，无独立目录，见下） |

### camoufox MCP

- **上游**：https://github.com/WhiteNightShadow/camoufox-reverse-mcp （1.8.0，39 个工具）
- **命令**：`D:\AI_python\camoufox\.venv\Scripts\python.exe -m camoufox_reverse_mcp --locale zh-CN`
- **运行时重建**：照 `skills\camoufox-reverse\references\重建配方.md`，或直接跑
  `pwsh -File skills\camoufox-reverse\scripts\restore.ps1` ——
  它会建 venv、装 `camoufox[geoip]`、`git clone` MCP 源码并 `pip install -e`、下载浏览器引擎（**需代理**）。
- **验证**：
  ```powershell
  & 'D:\AI_python\camoufox\.venv\Scripts\python.exe' skills\camoufox-reverse\scripts\mcp_smoke_test.py --browser
  ```
  期望：能列出 39 个工具。重启 DSH 后会话里应出现 `mcp__camoufox__*`。

### jadx MCP

- **上游**：https://github.com/zinja-coder/jadx-ai-mcp
- **命令**：`uv --directory D:\AI_python\MCP\MCP合集\jadx-mcp-server run jadx_mcp_server.py`
  （`uv` 依该目录的 `pyproject.toml` + `uv.lock` 自动建缓存环境，不需要手工建 venv）
- **外部前置（不在本机、也不在仓库里）**：**JADX-GUI 里必须装好 `jadx-ai-mcp` 插件并保持开启**
  （默认监听 `127.0.0.1:8650`）。插件不开，MCP 就是个空壳。
- ⚠️ **该条目是 `failOnStartupError: false` —— 启动失败不会报错**，所以必须主动验证：
  重启 DSH 后确认会话里出现 `mcp__jadx__*` 工具（例如 `mcp__jadx__get_all_classes`）；
  没出现就去查 `--dump-config` 与该目录能否 `uv run`。
- **运行时重建**：把 `jadx-mcp-server` 目录（`pyproject.toml` + `uv.lock` + `jadx_mcp_server.py`）重新取回原位，
  `uv` 会自动装依赖（fastmcp / httpx / requests）。

### ida MCP

- **上游**：https://github.com/HexRaysSA/ida-mcp （官方 Hex-Rays IDA MCP Server，MIT，PyPI 包名同为 `ida-mcp`）
  文档：https://docs.hex-rays.com/core/mcp
- **命令**：`uvx --exclude-newer=1s ida-mcp stdio --agent=dsh`
  —— `uvx` 直接跑 PyPI 上的最新稳定版，**不需要手工建 venv、也没有要重建的目录**
  （首次会自动往 uv 缓存里装 7 个包，含 `idapro` 2.1 MiB）。
- **依赖的运行时 = 本机 IDA 的 idalib，不产生任何目录**：机器上要有 **IDA 9.4 或更高（含 idalib）**，
  并把安装路径写进 IDA 的用户配置（激活一次即可）：

  ```powershell
  # IDA 侧一次性激活 idalib（本机早已做过，路径已写在 json 里）
  python "<IDA 安装目录>\idalib\python\py-activate-idalib.py" -d "D:\ProgramsDev\IDA Professional 9.4"
  ```

  激活后 `%APPDATA%\HexRays\IDA Pro\ida-config.json` 里应有
  `"Paths": { "ida-install-dir": "D:\\ProgramsDev\\IDA Professional 9.4" }`。
  **不要设全局 `IDADIR`**（官方明确警告会干扰 IDA GUI）；只在单次会话里临时覆盖时才用。
  自检：`uvx ida-hcli` 的输出里应出现 `idalib: active (<你的 IDA 路径>)`。
  PATH 里需要 `uv` 与 `git`。
- **外部前置（可选但建议装）**：**IDA GUI 插件** —— 装了 MCP 才能读/操作「已打开的 IDA 窗口」
  （否则 `list_databases` 会一直提示装）；**没装也能用 headless**（MCP 自己用 idalib 打开二进制分析）。

  ```powershell
  # 必须写「全限定名」：社区插件仓库里有个同名第三方 IDA-MCP，只给 URL 会报 ambiguous
  uvx ida-hcli plugin install 'ida-mcp@https://github.com/hexrayssa/ida-mcp'
  # 落在 %APPDATA%\HexRays\IDA Pro\plugins\ida-mcp\ ；**装完必须重启 IDA** 才生效
  ```

  - ⚠️ **hcli 不读 git 的代理配置**：直连 GitHub 会报
    `[WinError 10054] 远程主机强迫关闭了一个现有的连接`
    → 显式给 `HTTP_PROXY` / `HTTPS_PROXY`（本机 `http://127.0.0.1:7890`），pip 侧另加清华源。
  - ⚠️ 它还要往 **IDA 的 Python** 里装 `ida-nexus`；若报
    `IDA's Python is not a virtual environment` 或 `externally managed (PEP 668)`，先建专用环境：

    ```powershell
    uvx ida-hcli ida python create-environment
    # 建 %APPDATA%\HexRays\IDA Pro\venv（Python 3.13 + pip），并设用户级
    # IDAPYTHON_VENV_EXECUTABLE 指向它的 python.exe；之后 hcli 才装得进依赖
    ```

    本机实测该 venv 里是 `ida-nexus 0.13.0` / `ida-domain 0.5.1` / `idapro 0.0.10`。
- **验证（两层都做）**：
  1. 会话里出现 `mcp__ida__*`（6 个工具：`open_database` / `execute_python` / `reference` /
     `list_databases` / `save_database` / `close_database`）；
  2. 端到端：对任意二进制调 `mcp__ida__open_database`（本机实测 45 KB 的 PE 用 **4.4 s** 返回
     `backend: idalib`），再调 `mcp__ida__execute_python` 执行
     `hex(db.minimum_ea), hex(db.maximum_ea), sum(1 for _ in db.functions)`
     —— 能返回地址范围与函数数（本机实测 172）即通路正常；用完 `mcp__ida__close_database`。
  GUI 插件自检：`uvx ida-hcli plugin status` 应显示 `ida-mcp  <版本>`。
  ⚠️ **测 stdio 别用「一次性喂完 JSON 再关 stdin」的写法** —— server 收到 EOF 会开始关停，
  `open_database` 会撞上竞态返回 `database manager is shutting down`；要保持连接逐条等响应。
- **不迁移 / 不备份**：`uvx` 缓存环境（PyPI 一条命令可重装）、
  `%APPDATA%\HexRays\IDA Pro\plugins\ida-mcp\`（hcli 可重装）、IDA 的 `venv`（可重建）、
  IDA 本体与 license（用户自行安装）。挂载条目已在 `config\cordis.patch.yml` 里。

### context-mode MCP

- **上游**：https://github.com/mksglu/context-mode （npm 包名同为 `context-mode`，Elastic-2.0 许可）
- **它做什么**：把大块工具输出挡在上下文之外 —— 在沙箱子进程里跑代码 / 抓网页 / 建索引，只把结论回传
  （官方基准 315 KB → 5.4 KB）；另带 SQLite 会话记忆与 FTS5 知识库检索。共 **11 个工具**：
  `ctx_execute` / `ctx_execute_file` / `ctx_index` / `ctx_search` / `ctx_fetch_and_index` /
  `ctx_batch_execute`（沙箱与索引）+ `ctx_stats` / `ctx_doctor` / `ctx_upgrade` / `ctx_purge` /
  `ctx_insight`（meta）。
- **重建运行时（一条命令）**：

  ```powershell
  npm install -g context-mode     # 前置 Node >= 22.5
  # 本机落在 D:\ProgramsDev\nodejs\node_modules\context-mode（全局根 = D:\ProgramsDev\nodejs）
  ```
  它依赖原生模块 `better-sqlite3`。npm 可能报 `allow-scripts` 警告（install script 未登记）——
  **先复核二进制是否已落位**，再决定要不要 `npm approve-scripts`：

  ```powershell
  Get-ChildItem "$(npm root -g)\context-mode\node_modules\better-sqlite3" -Recurse -Filter *.node
  # 出现 better_sqlite3.node（约 1.9 MB）即正常；再跑 context-mode doctor 应报 FTS5 / SQLite: PASS
  ```
- **命令**（挂载条目里写死的形态）：`node <npm 全局根>\context-mode\cli.bundle.mjs`
  —— **不带任何参数就是 stdio MCP server**。刻意不用 `context-mode.cmd` shim：
  Windows 下 spawn `.cmd` 需要 shell。若新环境的 npm 全局根不是 `D:\ProgramsDev\nodejs`，
  改 `config\cordis.patch.yml` 该条的 `command` / `args`。
- ⚠️ **必须显式设 `CONTEXT_MODE_DIR`**：它自己做平台探测，**只要 `~/.openclaw\` 目录存在就会把平台判成
  OpenClaw**（medium confidence），存储随之写到 `~/.openclaw/context-mode/`。挂载条目里已设
  `CONTEXT_MODE_DIR=C:\Users\y\.dsh\context-mode` 把它收回 `$DSH_HOME`；新环境照着改这一行路径。
- ⚠️ **DSH 不在它的官方 17 平台清单内**：11 个 MCP 工具可用（走 standalone MCP 模式），
  但它的 hook 层不认识 DSH 的工具名（见下「自动路由」）。也就是说它**不会自动抢走** `Bash` / `Read`：
  要真省上下文，得靠下面的自动路由，或提示词与常驻规则引导。
- ✅ **自动路由（自写原生插件 `ctx-router`，必须重建）**：由 DSH 自己的拦截缝 `tools/pre-execute`
  自动拦截"抓大块数据"的工具调用，改道 `ctx_*` 沙箱。

  | 组件 | 来源 | 落在哪 |
  |---|---|---|
  | `lib\index.js` + `package.json` | **自制**，源码唯一副本在 `plugins\dsh-ctx-router\` | `$DSH_HOME\plugins\dsh-ctx-router\` |
  | profile 挂载行（`insert`） | 随 `config\cordis.patch.yml` 恢复 | profile 的 `cordis.patch.yml` |

  ```powershell
  # 落位（两个文件都来自 plugins\dsh-ctx-router\）
  $dst = "$env:USERPROFILE\.dsh\plugins\dsh-ctx-router"
  New-Item -ItemType Directory -Force "$dst\lib" | Out-Null
  Copy-Item plugins\dsh-ctx-router\lib\index.js "$dst\lib\" -Force
  Copy-Item plugins\dsh-ctx-router\package.json "$dst\" -Force
  ```
  挂载条目（已随 `config\cordis.patch.yml` 恢复；注意 `file:///` 是三斜杠）：
  ```yaml
  - insert:
      - id: ctx-router
        name: 'file:///C:/Users/y/.dsh/plugins/dsh-ctx-router/lib/index.js'
  ```
  **为什么不能直接用官方的 `hooks/hooks.json`**：它里面写的是 Claude Code 的工具名（`Bash`/`Read`），
  其 `core/routing.mjs` 的工具别名表**写死且无配置扩展点**，DSH 的 `pwsh`/`read`/`grep`
  不在表里 → 官方 hook 收到 DSH 工具名会直接放行。
  **⚠️ 也不要改用 `@deepseek-ai/dsh-hooks-claude-code` 桥接**（本仓库早期试过、已废弃）：
  它 `inject` 的 `shell` / `sessionProjections` 在 profile 里不满足，cordis 会让它**永远等待、
  `apply` 永不执行** —— 插件能被 `import`、loader 也不报错，但**一个 hook 都不注册**、配置根本不读。
  完整证据见 `plugins\dsh-ctx-router\RECIPE.md`。
  **不需要 `dsh plugin add`**：`insert.name` 直接写 `file:///` URL，cordis loader 用 `import()` 加载。
  **拦截范围**：`pwsh` / `bash` 命中 `curl`/`wget`/`iwr`/`irm`/`Invoke-WebRequest`/`Invoke-RestMethod`/
  `Get-Content -Raw`/`cat`/`type`/`Select-String`/`rg`/`findstr`/`docker logs`/`kubectl logs`/
  `journalctl`/无上限 `git log`、`git diff`/`find`/`Get-ChildItem -Recurse`；`read` 未带
  `limit`/`offset` 且 > 256 KB。**不拦** `grep`/`web_fetch`/`glob`/`edit`/`write` 与改状态操作。
  **逃生舱**：命令含 `ctx-allow`、或 `read` 带 `limit`/`offset` → 放行；插件内部 fail-open（绝不阻断会话）。
  **每次拦截**往 `$DSH_HOME\context-mode\ctx-router.log` 记一行。
  **生效**：本机 profile 是 `patchReload: live`，**改完即热重载生效、不需要重启**
  （实测同一会话下一条命令立刻被拦）；若某台机器是 `startup` 则需重启。
  **验证**：发一条 `Get-ChildItem <目录> -Recurse -File` 应被 deny 并提示改用 `ctx_*`，
  且 `ctx-router.log` 出现 `DENY tool=pwsh`；`pwd` 应正常放行。
  **仍未接**：`SessionStart` 上下文注入与 `PostToolUse` 会话捕获 —— 由 `$DSH_HOME\AGENTS.md`
  的常驻规则覆盖（那条规则装完即生效、不依赖重启）。
- **验证（三层）**：
  1. `context-mode doctor` → `Server test: PASS`、`FTS5 / SQLite: PASS`；
  2. `dsh --profile web --dump-config` 里出现 `id: mcp-context-mode` 与 `id: ctx-router`；
  3. 发一条命中特征的 `pwsh` 命令会被拦（理由里给出 `ctx_batch_execute` 等替代），
     且 `ctx-router.log` 有 `DENY` 行。
- **升级**：`npm install -g context-mode@latest`（重新取最新版即可，挂载条目里的路径不变）。
  升级**不影响**自制插件（没改它的源码）；但若官方调整工具名或路由语义，插件需复核。
- **不备份**：npm 全局包本身（一条命令可重装）、`CONTEXT_MODE_DIR` 下的 SQLite 数据
  （运行期会话轨迹与索引，属本机数据）。自制插件**要备份**（已在 `plugins\dsh-ctx-router\`）。

### 不迁移 / 不备份

四个 MCP 依赖的运行时（camoufox 的 venv+引擎约 **2.3 GB**、jadx 约 **41 MB**）**只记配方、不备份**；
`ida` 与 `context-mode` 都没有独立运行时目录（`uvx` 跑 PyPI 包 / 全局 npm 包）。
MCP 的挂载条目已在 `config\cordis.patch.yml` 里。JADX-GUI 及其插件、IDA 本体与其 license、
IDA GUI 插件目录都属于**外部工具**，不在本仓库范围内 —— 需要用户自行安装。