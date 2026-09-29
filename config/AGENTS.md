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
  `$DSH_HOME\.agent-presets\<id>\`, then `preset_probe validate <id>`.
- `config\` — environment config: `AGENTS.md` (these global rules), `settings.yaml`,
  `cordis.patch.yml` (**MCP mounts**), and `profile\` (`package.json` / `pnpm-workspace.yaml` / `cordis.yml`).
- `install.ps1` — the one-shot restore script (skills + presets + rules + settings + MCP + plugins).
- `README.md` / `CHANGELOG.md` — repo guide / **change log** (what changed, why, which files).

Rules:

- **Scope: anything in this environment that is not DSH-bundled is recorded and backed up** — third-party
  installs, things the user installed by hand, and things you installed for them. **Four kinds** qualify: a
  **skill** (a directory under `$DSH_HOME/skills`), a **DSH plugin** (a non-`@deepseek-ai/*` entry in a
  profile's `dependencies` or `dsh.profile.bundles`), an **MCP mount** (a `@deepseek-ai/dsh-mcp-client`
  `insert` entry in the profile's `cordis.patch.yml`), and an **agent preset** (a directory under
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
- **An MCP mount is recorded too, because it does not migrate by itself**: it lives only as a line in
  `config\cordis.patch.yml`. Record its `serverName`, the runtime it depends on, any **external
  prerequisite** (e.g. JADX-GUI with the `jadx-ai-mcp` plugin running), and how to verify it — remember
  `failOnStartupError: false` mounts fail **silently**. The runtime itself is rebuilt, never backed up.
  Details in the `skills-inventory` skill.
- **An agent preset is recorded too — it lives outside every profile and would otherwise vanish**: it sits
  only in `$DSH_HOME\.agent-presets\<id>\`, so a new machine that clones this repo and runs `install.ps1`
  gets nothing unless the preset is backed up here. Back up the **whole preset directory** under
  `presets\<id>\` (composition + metadata + a `README.md` naming the skills it references and the
  generator scripts it depends on), restore by copying it back, and prove it with
  `preset_probe validate <id>`. A preset **references** skills but provides none, so record the dependency
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
  `config\`, append a line to `CHANGELOG.md`, then `git add -A && git commit -m "<type>: <what>" && git push`.
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
- **每个项目产出 `HANDOVER.md`**（项目根、中文）：环境 / 从零重建命令 / 运行与验证 / 目录结构 / 数据与凭据来源
  （只写从哪取）/ 已知坑 / 变更记录 / 回退方式 / 待办；**更新前先把旧版复制到
  `docs\handover-history\HANDOVER-YYYY-MM-DD.md`**；项目完事且重建命令已验证时可删 `.venv`（先问一次）。




