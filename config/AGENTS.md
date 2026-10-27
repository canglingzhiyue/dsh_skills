# Global DSH rules (user-global instructions, loaded in every session)

## Skill inventory — for skills, DSH plugins, MCP mounts and agent presets that are not DSH-bundled

账本目录：`D:\AI_python\skills_backup` —— **它同时是一个私有 git 仓库**，
remote = `https://github.com/canglingzhiyue/dsh_skills.git`。
换机器时连同 `skills-inventory` skill 顶部那一行一起改；**新环境直接 `git clone` 本仓库即可**。

- `skills\<name>\` — **every skill mirrored in full** (= `$DSH_HOME/skills`, byte-for-byte).
  Clone → copy into the skill root; no upstream fetch, no adaptation step.
- `SKILLS.md` — the ledger: append one table row (with its P0/P1/P2 priority) and one log line.
  Never rewrite, reorder, or delete; a table-schema change must be explained in a log line.
- `INSTALL.md` — the install guide, ordered by priority: append one section per entry; fix its wording
  in place when a step is wrong.
- `plugins\<name>\RECIPE.md` — a recorded plugin's recipe (spec + install command + prerequisites +
  profile snippets + verification); a self-written plugin also gets its source copied here.
- `presets\<id>\` — a recorded **agent preset**, copied verbatim: `agent.cordis.yml` + `preset.yml`
  + a `README.md` naming the skills it references. Restore = copy the directory back into
  `$DSH_HOME\.agent-presets\<id>\`, then verify by opening a new session on that preset
  (**`preset_probe` does not exist in current DSH** — it was a session-authored dynamic package).
- `config\` — environment config: `AGENTS.md` (these global rules), `settings.yaml`,
  `cordis.patch.yml` (profile patch layer — **MCP mounts live here only when they are profile-layer /
  always-on**; since 2026-10-02 this deployment's 4 MCPs are rows in `presets\reverse\` instead),
  and `profile\` (`package.json` / `pnpm-workspace.yaml` / `cordis.yml`).
- `install.ps1` — the one-shot restore script (skills + presets + rules + settings + MCP + plugins).
- `README.md` / `CHANGELOG.md` — repo guide / **change log** (what changed, why, which files).

Rules:

- **Scope: anything in this environment that is not DSH-bundled is recorded and backed up** — third-party
  installs, things the user installed by hand, and things you installed for them. **Four kinds** qualify: a
  **skill** (a directory under `$DSH_HOME/skills`), a **DSH plugin** (a non-`@deepseek-ai/*` entry in a
  profile's `dependencies` or `dsh.profile.bundles`), an **MCP mount** (a `@deepseek-ai/dsh-mcp-client`
  `insert` entry in a profile's `cordis.patch.yml`, **or a `dsh-mcp-client` row in an agent preset's
  `agent.cordis.yml`** — the layer decides *when* the server starts, not whether it counts), and an
  **agent preset** (a directory under
  `$DSH_HOME\.agent-presets\<id>\` — it is in **no** profile's `package.json`, so it does not migrate by
  itself and would otherwise vanish on a new machine). Never recorded or backed up: DSH's own bundles,
  environment-provided tooling (npm/pnpm/node/corepack/uv/…), and ordinary npm packages that are not DSH
  skills, plugins, MCP mounts or presets. When unsure whether something counts as bundled, ask the user.
- One entry per requested install, **not** per directory: a repository shipping six skills is one entry,
  and the new environment reads the repository and handles the rest.
- Record the source (repository URL / ClawHub name) plus the adaptation note when the source is not
  DSH-native. If the source cannot be determined, write `未知（本地）` — never guess. For an **MCP mount**
  the source column records **the runtime it depends on** (e.g. `camoufox MCP ← D:\AI_python\camoufox`).
- **Assign a priority whenever you record an entry**: `P0 治理类` (affects how other skills are installed
  or recorded — install first, remove last), `P1 依赖类` (other skills reference it — install before its
  dependents), `P2 独立类` (order-free). A new entry that changes the overall order must also be reflected
  in the ledger, `INSTALL.md`, this file, and the `skills-inventory` skill when its rules change.
- **Every skill is mirrored in full into `skills\<name>\`**, whether or not it has a fetchable source
  (copy the whole directory — `SKILL.md` plus `references/`, `scripts/`, `assets/` — skipping
  `node_modules`/`.venv`/`__pycache__`). A skill with **no** source needs no special treatment beyond
  being marked in the ledger as `本地自制（唯一副本在 skills/<name>/）`: the mirror *is* the backup.
- **A recorded plugin is backed up as a recipe — source and install command only, never its source
  code or build output**: give it `plugins\<name>\RECIPE.md` holding the source spec itself
  (**never a pinned version** — re-installing takes the newest release), the
  `dsh plugin --profile <p> add` command, its prerequisites (pnpm, the exact `allowBuilds` key), the
  profile config it must end up in (`dependencies` entry plus `dsh.profile.bundles` entry), the
  verification command, and the fact that DSH must be restarted. `node_modules` is reproducible and is
  never copied; a self-written plugin also gets its source copied into the same directory.
- **An MCP mount is recorded too, because it does not migrate by itself**: it lives as a
  `@deepseek-ai/dsh-mcp-client` row — either an `insert` entry in a profile's `cordis.patch.yml`
  (starts with the harness: always-on) **or a row in an agent preset's `agent.cordis.yml` (starts only
  when a new session selects that preset — a preset is the only lazy mount point DSH has)**. Record its
  `serverName`, **which layer it is on**, the runtime it depends on, any **external prerequisite**
  (e.g. JADX-GUI with the `jadx-ai-mcp` plugin running), and how to verify it — remember
  `failOnStartupError: false` mounts fail **silently**, and that a profile-layer mount is invisible to
  `dsh --dump-config` once it moves into a preset. The runtime itself is rebuilt, never backed up.
  Details in the `skills-inventory` skill.
- **An agent preset is recorded too — it lives outside every profile and would otherwise vanish**: it sits
  only in `$DSH_HOME\.agent-presets\<id>\`, so a new machine that clones this repo and runs `install.ps1`
  gets nothing unless the preset is backed up here. Back up the **whole preset directory** under
  `presets\<id>\` (composition + metadata + a `README.md` naming the skills it references and the
  generator scripts it depends on), restore by copying it back, and verify it by **opening a new session
  on that preset** — a mount failure fails session creation loudly and names the row, and the roster's
  `broken: false` is only a shape check. (**`preset_probe` does not exist in current DSH**: it was a
  session-authored dynamic Cordis package, never on disk — do not put it in a restore step.) A preset
  **references** skills but provides none, so record the dependency
  order in its row and install the referenced skills first. Never edit a preset that ships with the
  deployment — a locally authored one under the user root is the only kind this covers. Details in the
  `skills-inventory` skill.
- **A skill that fronts a whole local environment is backed up self-contained**: when a recorded skill
  describes how to use an environment built on this machine (self-made helper scripts, client config, a
  heavyweight runtime of hundreds of MB to GBs), move the self-made pieces *into* the skill directory
  (`scripts/`, `references/`), write a rebuild recipe under `references/` for the sourced heavy parts
  (URL + pinned version + checksum + commands + any config snippet to paste), and keep those heavy parts
  out of the repository — only the self-contained directory is mirrored. Credentials, login state and
  profiles are never backed up. Self-made in the directory, sourced as a recipe, sensitive never. Details
  in the `skills-inventory` skill.
- **Any change to a *recorded* entry — including `skills-inventory` itself — goes through the backup pass
  again**: re-sync the skill into `skills\`, refresh `config\` if a config file changed, update a plugin's
  `RECIPE.md`, and update its `INSTALL.md` section when the change affects how a new environment rebuilds
  it. Anything not recorded stays unrecorded: change it and move on — no ledger row, no mirror, no guide
  section.
- **Commit and push after every change — the git history *is* the rollback mechanism** (the old dated
  `snapshots\ledger-YYYY-MM-DD.zip` scheme is retired). After editing the ledger, re-sync `skills\` and
  `config\`, append a line to `CHANGELOG.md`, then **`git add <explicit paths> && git commit -m "<type>: <what>" && git push`**
  (**never `git add -A`** — see the dev-hygiene red line, it swallows other sessions' uncommitted work).
  Roll back with `git revert <commit>` or `git checkout <commit> -- <path>` — strictly better than a zip:
  it diffs, it tells you which change broke things, and it restores a single file. Details in the
  `skills-inventory` skill.
- **Re-installing from this ledger or the install guide is idempotent: append nothing.** Those installs
  are not new requests; a second row would be a duplicate. Only a new request from the user is recorded.
  (The fastest path for a new machine is `git clone` + `pwsh -File install.ps1`.)
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
  uv 本体 = `C:\Users\y\.local\bin\uv.exe`（**独立安装**，2026-09-30 起 anaconda 已整机移除）；
  本机 PATH 上**没有可用的 `python`**（只剩 WindowsApps 的 0 字节 Store 存根）——一律 `uv run` 或环境的绝对路径。
- **每个开发阶段收尾清理无用文件**（限本项目目录内、走回收站），交付前再清一次；删完报告清单与释放空间。
- **Git 提交一律显式列路径**：禁 `git add -A` / `git add .` / `git commit -a`（账本仓库与工作区可能同时有别的会话在改，
  `-A` 会吞掉别人的未提交改动 —— 2026-10-27 实测踩过）；**不重写已推送历史**（`reset --hard` / `amend` / `force push`）；
  提交前看 `git diff --numstat`，整文件级变更多半是行尾符/编码变了（`--ignore-cr-at-eol` 可辨）；push 后
  `git status -sb` 必须无 ahead/behind。细则见 `dev-hygiene` 规则 6。
- **每个项目产出 `HANDOVER.md`**（项目根、中文）：环境 / 从零重建命令 / 运行与验证 / 目录结构 / 数据与凭据来源
  （只写从哪取）/ 已知坑 / 变更记录 / 回退方式 / 待办；**更新前先把旧版复制到
  `docs\handover-history\HANDOVER-YYYY-MM-DD.md`**；项目完事且重建命令已验证时可删 `.venv`（先问一次）。





## 代码风格 — 所有 worker 通用（用户指定，2026-10-21）

> 来源：用户明确要求「以后所有 worker 都按这个风格写代码」。
> 样板在 `D:\AI_python\reverse-cases\2026-10-20_xc-pyinstaller\output\xc_*.py`（六个文件）。

### 1. 文件组织

- **按职责拆文件，一个文件一件事**。整套脚本的拆分粒度：核心层 / 外部依赖层 / 每个业务分支一个文件 / 总控一个文件。
- 每个文件顶部必须有一段 docstring，写清三件事：**这个文件干什么、怎么用（可复制运行的示例）、关键结论或限制**。
- 文件名小写 + 下划线。总控文件叫 `xxx_main.py`，核心叫 `xxx_core.py`。

### 2. 函数设计

- **短小、单一职责**，一个函数控制在 50 行内。
- **每个函数都有 docstring**，至少写清：参数含义、返回什么、抛什么异常。
- **依赖靠参数注入，不硬编码**。需要外部能力时留 `xxx_fn=None` 参数，默认指向实现，调用方可替换：
  ```python
  def process_one(item, user_id, detail_fn=None, submit_fn=None):
      detail_fn = detail_fn or xc_detail.fetch_room_list
      submit_fn = submit_fn or core.submit_task
  ```
- **提供两种粒度，都可独立调用**：`run()` 处理一整批，`process_one()` 处理一条。不要只有批处理入口。
- **返回值用简单 dict**，不套 dataclass / namedtuple。字段名用英文小写下划线。
- 可选参数默认 `None`，函数内 `x = x or 默认值` 收敛。**不要用 argparse / sys.argv**，配置全放在文件顶部常量区。

### 3. 注释与标注

- **一律简体中文**。代码、标识符、路径、命令保持原文。
- 关键决策写**「为什么」**，不是写「做什么」。例如不要写「循环遍历 hotel_ids」，要写「服务端从候选池里挑，所以要全量上报」。
- **区分【实测】【推断】【未验证】**，并在注释里标明依据（源码行号、实测时间、文件路径）。
- 踩坑点用 `★` 或 `⚠` 开头标出，一眼能看到。
- 复杂函数内部用分段注释组织：
  ```python
  # ---- 1. 字段检查 ----
  # ---- 2. 取详情数据 ----
  # ---- 3. 提交 ----
  ```
- 文件内的分区用 `# ====` 横线包起来。

### 4. 日志输出

- `print` 带**方括号模块前缀**：`[注册]`、`[拉任务]`、`[brand]`、`[camoufox]`。
- 打印关键参数和数据规模：`f'[{hotel_id}] 数据 {size:,} B'`。
- 错误信息必须带**上下文**：哪个酒店、哪个字段、服务端回了什么。不要只打 `e`。
- 进度用 `第 i/N 次` 形式，方便判断卡在哪。

### 5. 错误处理

- 明确捕获，给**可操作**的错误信息（告诉人下一步该干什么）。
- 批处理场景提供 `*_safe()` 变体，返回 `(结果, 错误)` 而不抛异常，避免一家失败中断整批。
- **不吞异常**：要么处理掉，要么带上下文重新抛出，要么 `traceback.print_exc()` 记录下来。禁止裸 `except: pass`。

### 6. 验证要求

- **每个交付都附带自检脚本**，且验证手段必须是硬的：
  - 与真实采集数据对比（如用录制的真实密文验证加密函数）
  - 与已知正确的基线逐项比对（如与字节码级验证过的重建源码比）
  - 边界用例（空值、超长、非法输入、补位对齐）
- **「没有报错」不是证据，「流程跑完」不是完成**。自检脚本要打印 `OK/FAIL` 和最终结论行。
- 端到端要有 mock 版自检（mock 掉网络和外部依赖），证明模块之间确实串通。

### 7. 不要做的事

- 不过度抽象：不写基类、不用装饰器魔法、不搞插件注册机制。
- 不把简单逻辑拆成一堆小函数（三行的东西就写在原地）。
- 不引入重量级第三方库来解决几行代码能解决的问题。
- 不在业务函数里硬编码配置（URL、密钥、账号）——统一放顶部常量区或独立配置文件。

