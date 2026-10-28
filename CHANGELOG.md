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

## 2026-10-27 —— rule: 新增「第三方模型数据边界」核心规则（AGENTS.md 第一节）

- **变更类型**：rule（用户要求「agent.md 追加一条核心规则」）
- **内容**：`$DSH_HOME/AGENTS.md` 顶部新增第一节「核心规则 — 数据边界：第三方模型不得读取 / 上传工作区外的数据」：
  1. 默认边界 = 当前会话工作区；使用**任何第三方模型 / 外部服务**（subagent 指定外部 `provider`/`model`、
     OpenRouter 等网关、MCP server、AutoGLM / web search / web fetch、抓包工具）时只允许输入工作区内数据。
  2. 工作区外目录（`D:\AI_python\` 其他项目、`C:\Users\y\`、网络与共享盘、系统目录）未经用户**逐次、逐目录、
     显式**授权，禁止扫描 / 读取 / 上传；禁止用 `..` 上跳、绝对路径、符号链接、`glob **` 绕过。
  3. 越界即停并先问，不把路径名 / 文件名 / 摘要当碎片发出去。
  4. 本机维护类纯本地操作（`$DSH_HOME` skill 读写、账本同步、回收站脚本、uv 缓存）不受阻断，
     但其原文同样不得作为上下文发给第三方模型。
- **原因**：用户明确要求把「第三方模型使用中不得上传工作区外其他目录数据」定为常驻核心红线 ——
  此前只在个别会话里口头约束，跨会话/跨 subagent 不保证被遵守。
- **影响文件**：`config\AGENTS.md`（实况同步）、`CHANGELOG.md`。

## 2026-10-27 —— rule: 新增「Git 提交红线」（dev-hygiene 规则 6）+ 修正账本的提交命令

- **变更类型**：rule（用户要求「记住这次 github 操作的经验教训」）
- **起因（实测事故）**：reverse-skill 上游升级的第二次提交用了 `git add -A`，把**另一并发会话未提交**的
  `plugins\dsh-skillhub\RECIPE.md` + `INSTALL.md` / `SKILLS.md` 追加（共 302 行）吞进 `5817940`；
  对方随后只能把剩余文件另提一条 `40a396d`。处理原则：**不重写已推送历史**（不 `reset --hard`、
  不 `amend`、不 `force push`），两边的改动都在，无损。
- **内容**：
  1. **`dev-hygiene` 新增规则 6「Git 提交红线」**：显式路径 `git add`（禁 `-A` / `add .` / `commit -a`）、
     提交前用 `status --porcelain` 逐文件确认归属、不重写已推历史、`git diff --numstat` 里整文件级变更
     先怀疑行尾符/编码（`* -text` 仓库逐字节存储，`--ignore-cr-at-eol` 可辨；`WriteAllLines` 固定 CRLF 是坑）、
     升级上游用 `--ff-only` 且不碰脏工作树、**"上游有没有新版"看 commit 不看 `VERSION`**、
     push 后 `git status -sb` 必须无 ahead/behind、并发下同步远端用 `merge` 而非 `pull --rebase`。
     收尾清单同步加一条勾选项。
  2. **`skills-inventory` 的「④ 提交推送」由 `git add -A` 改为显式列路径**，并新增「为什么这里必须显式列路径」
     与「并发会话下的账本操作」两小节（账本是多会话共享仓库，正是事故现场）。
  3. **`$DSH_HOME/AGENTS.md`**：dev-hygiene 常驻段加 1 行 Git 红线（5 行 → 6 行）；并把它自己那句
     `git add -A && git commit -m … && git push` 改成显式路径 —— **原句与新红线直接冲突，必须就地修**。
  4. **`INSTALL.md`**：dev-hygiene 节「五条硬规则」→「六条」、红线行数 5 → 6、顺手修掉 legacy 的
     `local\skill\dev-hygiene\` 路径（实际是账本 `skills\dev-hygiene\`）。
- **影响文件**：`skills\dev-hygiene\SKILL.md`、`skills\skills-inventory\SKILL.md`、`config\AGENTS.md`、
  `INSTALL.md`、`SKILLS.md`、`CHANGELOG.md`。
- **本次提交本身即示范**：`git add` 显式列上述 6 个路径（**不用 `-A`**），提交前 `status --porcelain`
  逐项确认都是本会话产生的改动。

---

## 2026-10-27 —— install: `dsh-skillhub`（技能与 MCP 统一开关面板）+ 本机 schemastery 适配

- **变更类型**：install（用户要求「根据当前环境适配这个仓库 https://github.com/aa2246740/dsh-skillhub」）
- **装了什么**：DSH 插件 `@aa2246740/dsh-skillhub@1.0.7`（本机 DSH `0.2.0-rc.2`）。
  设置页新增 `skill&mcp`（全局层），对话输入框上方新增「技能」胶囊（本项目 / 本对话层）；
  可开关 `~/.agents/skills`（54）+ `$DSH_HOME/skills`（11）与本机 MCP 服务，**纯可见性、不动磁盘文件**。
- **装法**：`dsh plugin --profile web add @aa2246740/dsh-skillhub`，`bundles` 末尾自动 reconcile；
  npm 包自带 `lib/`，**无需** `allowBuilds` / pnpm 构建 / DSHX。
- **踩到并修掉一个真问题（本机适配的核心）**：装完 `--dump-config` 通过，但**另起临时实例实跑**
  报 `dsh: warning: 1 entry did not activate` + `dsh-skillhub …: failed to import`。根因是
  `@howmp/dsh-pentest` 的依赖把 `@deepseek-ai/schemastery@3.18.1` 落在 profile 顶层（hoisted），
  而插件用到 **3.18.4+ 的 `Schema.volatile()`** → import 期抛
  `z.boolean(...).default(...).volatile is not a function`。修法：`profiles\web\package.json` 的
  `dependencies` 显式加 `"@deepseek-ai/schemastery": "3.18.5"`（与 host 同版本）+ `dsh plugin --profile web install`；
  实测 `dsh-pentest` 被一并抬到 3.18.5 后仍正常加载。
- **实测结论**：`/skillhub/catalog` 200（两个技能根、`collisions: 0`、`broken: 10` 属上游既有
  frontmatter 问题）；`/skillhub/mcp/catalog` 200 且 `servers: []`（**本机正常**：6 个 MCP 由
  `reverse-mcp-activator` 在逆向模式会话创建时才挂载）；首页 client 组合 bundle 取回 200 / 977 KB。
- **影响文件**：新增 `plugins\dsh-skillhub\RECIPE.md`；`SKILLS.md`（表格 + 安装顺序补记 + 日志）；
  `INSTALL.md`（新增一节）；`config\profile\package.json`（重新同步，含 schemastery 那行）；
  `CHANGELOG.md`（本条）。`skills\` 无变化（本插件不提供 skill）。
- **生效**：**必须重启 DSH**（bundle 层在 profile 启动时组合）。本次交付时未重启 3080 那个 host，
  设置页要重启后才有入口；会话记录不丢。

---

## 2026-10-27 —— upgrade: reverse-skill 上游 pin 升级（`7e2097f` → `cab634b`，39 个 commit）+ 兼容性适配

- **变更类型**：upgrade（用户要求「检查逆向模式上游仓库是否更新了新版本，如果有新版本直接根据当前环境做
  兼容性适配升级」）
- **检查结果**：`git fetch` 后落后上游 39 个 commit；`VERSION` 仍是 `1.0.1`（**上游没发版**），所以判断
  "有没有新版"看 commit 而不是 VERSION。
- **内容**：
  1. **仓库**：`C:\Users\y\.dsh\reverse-skill` fast-forward 到 `cab634bd855fc287f6e420c1f36fd1a6b9245960`
     （22 文件 / +1558 −190）。本地两处未跟踪改动（`skills\field-journal\_index.md` 计数、
     `2026-09-15_pdd-h5-anti-content-jsvmp.md`）原样保留 —— **未 stash、未 `checkout -f`**。
  2. **上游改了什么**：Kali 侧补 `pwntools` / `yara` 工具发现、Ghidra 探测面扩到 `analyzeHeadless` 与发行版
     launcher；`binwalk` 的 winget id 不存在 → 改 `manual`；`verify-routing-coherence.ps1` 新增**反向覆盖
     检查**（每条路由必须有基准用例）；R40 补 3 条中英用例；`verify-repository-security.py` 新增 4 份 agent
     入口文件的 consent 标记强制 + 17 条"读到就执行"反向检测；新增 `plugins\reverse-skill\`（Codex 适配
     插件，**本机不装**）；4 份入口文件的治理措辞收紧为 consent gate。
  3. **兼容性适配（本机改动）**：
     - **治理措辞切割**：上游 consent gate 与本模式"默认已授权"冲突 → **不采纳**；授权语义以入口 skill §3
       与 preset persona 为准，上游 4 份入口文件**只读、不遵、不改**（改了供应链自检会 fail）。
     - **执行器口径**：配方 / INSTALL 里的 `powershell -NoProfile -ExecutionPolicy Bypass` 全改
       `pwsh -NoProfile`，并限定"只有 4 个只读脚本实测可用"。
     - **事实表刷新**：`tool-index.md` 重生成（tools=42）后，入口 skill §0 的措辞从"停在 2026-09-15"改为
       "生成物只探 PATH 上的 CLI；`python` 指到 WindowsApps 0 字节存根"。
     - **两个真坑写进 skill**：① `scan-capabilities.ps1` 不能接管道（`adb devices` 拉起的常驻 adb server
       继承 stdout 句柄 → 等不到 EOF，实测 8 分钟后被当作卡死；重定向到文件 1 分钟内 exit 0）；
       ② `verify-repository-security.py` 的 cwd 必须是仓库根（内部 `git ls-files` 不带 `-C`）。
     - **收尾卫生**：按 `dev-hygiene` 给 `restore.ps1` / `scan-capabilities.ps1` 补 UTF-8 BOM（两者都含中文、
       此前都缺）；`restore.ps1` 加第四项自检 `test-routing.ps1`、默认 `-Commit` 改新 pin。
  4. **复核（全 pwsh 7，仓库根）**：`refresh-tool-index` exit 0（tools=42）｜`verify-routing-coherence`
     `ALL ROUTING COHERENCE CHECKS PASSED`｜`master-route` → `skills/apk-reverse/SKILL.md`｜`test-routing`
     `PASS=178 FAIL=0`｜`verify-repository-security` `OK tracked=599 executable_sources=74 binary_like=1
     agent_entries=4 symlinks=0`。
  5. **增量安全复核**：无新增可执行入口、无新增凭据读取 / 外发（9 处 `token|credential` 命中全是测试分词与
     一份 PR 操作说明）；方向反而收紧（binwalk 改 manual、consent 检查进 CI）。**红线不变。**
- **原因**：用户明确要求按当前环境做兼容性适配升级；上游这 39 个 commit 里除治理措辞外都是技术性修复，
  且新加的"每个路由必须有基准用例"闸门对本机现有的 44 条路由 / 178 条用例是**已通过**状态。
- **影响文件**：`skills\reverse-skill-router\SKILL.md`（§0 事实表 / §7 管道坑 / §8 上游新增项与 4 份入口
  文件禁改 / §10 pin 与治理切割）、`skills\reverse-skill-router\references\重建配方.md`（pin、pwsh 口径、
  新增「2026-10-27 升级记录」与增量复核）、`skills\reverse-skill-router\scripts\restore.ps1`（pin、第四项
  自检、BOM）、`skills\reverse-skill-router\scripts\scan-capabilities.ps1`（BOM）、`INSTALL.md`（该节 pin /
  文件数 / pwsh / 验证段 / 新增升级小节 / 授权口径修正）、`SKILLS.md`（追加日志）、`CHANGELOG.md`（本条）。
  生成物 `$DSH_HOME\reverse\capabilities.{md,json}` 已重生成，**不进仓库**。
- **回退**：`git revert <本 commit>`；仓库侧 `git -C $env:USERPROFILE\.dsh\reverse-skill reset --hard 7e2097f`
  再跑 `refresh-tool-index.ps1` 即可回到旧 pin（本地两处未跟踪改动不受影响）。

---

## 2026-10-26 —— install: aidbg（Windows 调试器）+ 修能力扫描器的 MCP 分层与去重

- **变更类型**：install（用户要求「安装 https://github.com/A-new/aidbg ，然后生成对应的 aidbg skill，
  配置到 reverse-router 中或者逆向环境中」）
- **内容**：
  1. **可执行文件**：`D:\AI_python\reverse\aidbg\aidbg.exe`（v0.4.0，1,715,200 B，SHA256
     `FCD5A086251CFA5B910851E136142C2F80AE66A043E6477003D7F7A7DBD28A6E`）。**不构建** ——
     本机没有 MSVC / CMake，上游 `build.bat` 跑不通，直接用 release 单文件（零 VC 运行时依赖）。
  2. **新 skill `aidbg`**（`skills\aidbg\`，3 文件约 21 KB）：`SKILL.md`（DSH 化，frontmatter 只留
     name/description，490 字符）+ `references\commands.md`（上游命令表原文 + 本机补充行）+
     `references\local-environment.md`（重建配方、MCP 挂载位置、5 条验证、6 条实测坑）。
  3. **接入 reverse-skill-router**：windows 域 `shallow` → `deep`、`primarySkills: ["aidbg"]`
     （`references\domain-registry.json`）；`SKILL.md` §2 域表与 §9 边界表各加一行；§7 补
     「MCP 该加在哪（别加错层）」；能力扫描器工具表加 `aidbg`（`k=binary`，`--version` 探活）。
  4. **MCP 挂载**：`config\cordis.patch.yml` 的 `reverse-mcp-activator.config.servers` 末尾加
     `serverName: aidbg`（stdio，`--mcp`，13 工具，`toolCallTimeoutMs: 120000`，
     `failOnStartupError: false`）—— 逆向模式会话创建时按需挂载。
- **顺带修的既有缺陷（扫描器）**：`scan-capabilities.ps1` 此前把 `reverse-mcp-activator` 段里的
  `serverName` 一律标成 `layer: profile`（= 常驻），而它实际是**会话创建时按需**；同时 preset 里
  2026-10-09 迁移遗留的 5 条 MCP 历史副本被**重复计入** → 清单显示 10 条 MCP 而本机实际只有 5 台。
  现改为：① 按 `- id: reverse-mcp-activator` 段落边界识别，条目标 `layer: activator`；
  ② 跳过与 activator 同名的 preset 副本并单独告警。清单变为 6 条（含 aidbg）。
- **原因**：用户要求安装该仓库并「配置到 reverse-router 或逆向环境中」。选择 CLI + MCP 双路径：
  CLI 是上游主设计（JSONL，不挑会话类型、不依赖挂载），MCP 让逆向模式会话能直接调结构化工具。
- **影响文件**：`skills\aidbg\`（新增 3 文件）、`skills\reverse-skill-router\SKILL.md`、
  `skills\reverse-skill-router\references\domain-registry.json`、
  `skills\reverse-skill-router\scripts\scan-capabilities.ps1`、`config\cordis.patch.yml`、
  `SKILLS.md`、`INSTALL.md`（MCP 节 5→6 台、新增 aidbg 小节、wireshark 小节挂载位置勘误）、本文件。
- **实测证据**：`aidbg.exe --version` → `aidbg 0.4.0`；调试 `C:\Windows\System32\whoami.exe` 停在
  `entry`，`disasm` / `stack` / `read` / `eval` / `bl` / `snapshot list` / `hide status` / `modules`
  全部 `ok:true`、退出码 0；MCP 手工 JSON-RPC 握手 `tools/list` 返回 **13** 个工具；
  `dsh --profile web --dump-config` 退出码 0 且组合树里出现 `serverName: aidbg`；能力扫描器重跑：
  `aidbg` present / `aidbg 0.4.0`、6 条 MCP 全在 `activator` 层、windows=deep、悬空引用 0。
- **未验证 / 待用户实测**：重启 DSH 后新开「逆向模式」会话确认 `mcp__aidbg__*`；中文路径目标；
  `detect` 在真实加固样本上的表现。
- **顺带同步（不是我改的，是仓库落后于环境）**：`config\AGENTS.md` —— 用户在 2026-10-21 加的
  「代码风格 — 所有 worker 通用」整节此前没进仓库；`config\profile\package.json` ——
  DSH 自动 reconcile 后 `dsh.profile.bundles` 的顺序变了（无实质变化）；`skills\iv8-js-sandbox\` ——
  2026-10-09 已记账、但镜像一直缺失，本次补上（20 文件）。`$DSH_HOME\settings.yaml` 当前不存在
  （DSH 自己迁移过），仓库里那份 `config\settings.yaml` 保留不动。
- **回退**：`git revert <commit>`（skill 与扫描器改动都在本提交内）；只回退 MCP 挂载就删掉
  `cordis.patch.yml` 里 `- serverName: aidbg` 那一段；exe 与 skill 目录无系统级副作用。

## 2026-10-24 —— config: 第三方模型接入的上下文长度统一调成 1M

- **变更类型**：config（用户要求）
- **内容**：给 `llm-pi-ai` 下**每一个第三方 provider 的每一个模型条目**加 `contextWindow: 1000000`
  （不改 `maxTokens`，输出上限仍走路由默认 32768）：
  - `$DSH_HOME\profiles\web\cordis.patch.yml` —— claudex、a-lang、lesec（`cn:deepseek-v4.1-flash`
    与 `deepseek-v4.1-flash` 两条）、ok88，共 **5** 条；
  - `$DSH_HOME\profiles\desktop\cordis.patch.yml` —— claudex、a-lang、lesec（2 条），共 **4** 条。
  - 官方的 `deepseek-account` 不动：它不是第三方接入。
- **原因**：用户要求「把所有第三方模型接入的上下文长度调成 1M」。
- **为什么必须写在条目上、而不是 provider 级的 `defaultContextWindow`**：
  `deepseek-v4.1-flash` 不在 pi-ai 安装目录的 catalog 里
  （`@earendil-works/pi-ai\dist\providers\data\deepseek.json` 只有 `deepseek-flash` 与
  `deepseek-v4-pro`，两者都是 `contextWindow: 1000000`），所以这些条目此前命中的是
  **路由级 fallback `defaultContextWindow = 262144`（256K）**。按 `catalog.d.ts` 的规则，
  fallback 只对"条目和目录都没定义"的模型生效，**显式条目字段才是覆盖**。
- **风险（已告知用户）**：`contextWindow` 是**本地声明**，DSH 不会去探测上游真实窗口。
  声明 1M 之后压缩阈值、token 压力、溢出判定都按 1M 算，而 claudex / a-lang / lesec / ok88
  四家站点真实上限**未验证** —— 超过服务端真实窗口的请求会被上游报错，或静默截断后返回
  `stopReason: length` 且 output=0（pi-ai 的 overflow 检测正是靠这个信号）。
- **验证**：
  1. `dsh --profile web --dump-config` → **exit 0**（62,552 B），5 条 `contextWindow: 1000000` 就位；
  2. 用 `@deepseek-ai/dsh-llm-pi-ai` 导出的 `Config`（schemastery）跑两个 profile 的用户层 →
     **9 条第三方模型条目全部 `contextWindow=1000000` 且通过 schema**（证明该字段被 schema 接受、
     没有被静默剥离）；`!!js` 标签用 js-yaml 自定义 `tag:yaml.org,2002:js` 类型解析；
  3. `desktop` profile 由 Electron 独占，`--dump-config` 直接拒绝（`error: profile "desktop" is
     managed exclusively by the Electron application`），只能做文件级 schema 校验。
- **生效方式**：模型目录在 host 启动期装载 —— **重启 DSH** 后模型选择器与上下文计量才按 1M 走。
- **回退**：`profiles\web\cordis.patch.yml.bak-20261024-ctx1m`、
  `profiles\desktop\cordis.patch.yml.bak-20261024-ctx1m`；或 `git revert` 本提交。
- **影响文件**：`config\cordis.patch.yml`（同步为实况 —— 顺带吸收了此前未同步的差异：
  `agent-default-model` 已是 `deepseek-account/deepseek-flash`、模型清单已收缩、activator 段注释措辞）、
  新增 `config\desktop\cordis.patch.yml`、`INSTALL.md` 的 `config\` 小节。

---

## 2026-10-13 —— fix: `Remove-ToRecycleBin.ps1` 回收空目录时崩溃

- **变更类型**：fix（skill 内脚本缺陷）
- **症状**：把**空目录**交给回收站脚本时报
  `在此对象上找不到属性"Sum"。请验证该属性是否存在。`，删除中止（未误删任何东西）。
- **原因**：脚本在 `Set-StrictMode -Version Latest` 下直接取
  `(Get-ChildItem ... | Measure-Object -Property Length -Sum).Sum`。
  `Measure-Object` 在**零输入**时不产生 `Sum` 属性，取属性即抛错；
  只有非空目录才会走到正常分支。
- **修复**：先取回测量对象数组，再判断 `Sum` 属性是否存在，缺失按 0 计。
- **影响文件**：`skills\dev-hygiene\scripts\Remove-ToRecycleBin.ps1`
  （已同步回 live `$DSH_HOME\skills\dev-hygiene\`，两侧 SHA256 一致）。
- **验证**：空目录 + 普通文件两种输入各回收一次，均成功；非空目录行为不变。
- **发现场景**：清理携程逆向项目的 `.tmp` / `.tmp_pip`（Python `tempfile` 残留）时触发。

---

## 2026-10-10 —— fix: 恢复被「账本回灌」抹掉的第三方 API provider 配置

- **变更类型**：fix（数据恢复 + 账本缺陷修复）
- **事故**：2026-10-09 处理 probe 污染时，用 `Copy-Item 账本 → live` 覆盖了 profile patch。
  当时的账本 `config\cordis.patch.yml` 是**精简版**（只有 preset-reverse 声明），
  于是 live 独有的 4 行 host 配置被整段截掉：
  `llm-pi-ai`（4 个第三方 provider：claudex / a-lang / lesec / ok88）、
  `agent-default-model`（被重置为内置 `deepseek-account`/`deepseek-flash`）、
  `ui-settings-general`、`ui-conversation`。
  症状：默认模型不再是 `claudex/kimi-k3`，第三方 API 在设置里消失。
- **恢复**：从 `cordis.patch.yml.before-inline`（2026-10-09 12:09，唯一仍含 llm-pi-ai 的
  备份，在本机 `D:\AI_python\无实际文件区\reverse-preset-migration-backup\`）提取那 4 行并合回
  live。**API key 本体一直在 `.credentials.yaml`，全程未受影响**。
  验证：`--dump-config` exit 0、4 个 provider 齐、默认 `claudex/kimi-k3`、无重复 id。
- **账本缺陷修复（根因）**：账本 `config\cordis.patch.yml` 此前**12 个历史版本全都没有
  llm-pi-ai** —— 它不是 live 的镜像而是子集，所以从它回灌必然丢东西。
  现在账本是 live 的**完整镜像**（含 llm-pi-ai / agent-default-model / 两条 ui-*）。
- **教训**：`config\` 是 profile patch 层的备份基准，**不能只放子集**；
  从账本回灌 profile patch 之前必须确认「账本 ⊇ live」，并先备份 live。

## 2026-10-09 —— fix: MCP 启动时机回退（新增自研插件 reverse-mcp-activator）

- **变更类型**：fix（架构适配 + 新增自研件）
- **内容**：上一轮把 reverse composition 全量内联进 profile patch 后，preset 由 broken 转健康，
  但暴露出 0.2.0 的另一个行为变化：registry **启动期急切挂载所有已声明 preset**，于是 5 个 MCP
  随 `dsh web` 一起拉起（IDA 的 uvx 在无代理时反复重试 PyPI，6×~17s，日志刷屏）。
  本轮把 MCP 挂载从 composition 移出，改由自研插件 `reverse-mcp-activator` 在
  **逆向模式会话创建时**挂到该会话自己的作用域上：新增 `plugins\reverse-mcp-activator\`
  （源码 + RECIPE），`config\cordis.patch.yml` 新增该插件行（5 个 server 的配置原样迁入其
  `config.servers`），preset 声明块回归纯 composition。
- **实测（隔离 HOME，用生产配置原样跑）**：启动后 0 个 MCP；普通会话 0 个；逆向会话按需拉起
  （wireshark + jadx 已连上）；工具落在会话作用域（全局视图 0 个 `mcp__*`）。
- **原因**：用户反馈"修复把系统修坏了，MCP 又随系统启动了"。
- **影响文件**：`plugins\reverse-mcp-activator\`（新增）、`config\cordis.patch.yml`、
  `presets\reverse\README.md`、`INSTALL.md`、`install.ps1`、`SKILLS.md`。

## 2026-10-09 —— fix: reverse preset 0.2.0 适配（声明内联化，选择器可见性修复）

- **变更类型**：fix（兼容性适配）
- **内容**：DSH 0.2.0 起 `cordis:include` 会把子条目包名的解析基址改到被包含文件自己的目录，`.agent-presets\reverse\` 向上没有 node_modules → 35 行全部解析失败，注册表审计报 "never started" → preset 标 `broken` → 会话选择器过滤掉（渗透插件的 include 之所以可行，是因为它的文件恰好在 profile 的 node_modules 里）。修复：按官方 `standard.patch.yml` 同构，把 composition **全量内联**进 `config\cordis.patch.yml` 的 `preset-reverse` 声明块（plugins 列表）。实测：测试实例 roster 里 `reverse` 与 `pentest` 均健康、无 broken；5 个 MCP 随启动拉起（0.2.0 起 registry 急切挂载所有已声明 preset，按需语义已失效，属架构现实）。
- **原因**：用户报告升级 0.2.0 后「逆向模式」从选择器消失，要求"不兼容就修改适配"。
- **影响文件**：`config\cordis.patch.yml`（声明块改为全量内联）、`presets\reverse\agent.cordis.yml`（顶部加【已停用】头注释，保留为历史参考）、`presets\reverse\README.md`（挂载位置与恢复步骤更新）、`SKILLS.md`（顺带去掉另一会话误贴的重复 iv8 日志行，内容不动）。
- **注意**：`config\cordis.patch.yml` 现在是 reverse preset 的唯一权威源；换机恢复只需整文件复制，无需再处理 file:/// 路径。

## 2026-10-08 — 新增自研 wireshark-mcp-lite（第 5 个 preset 层按需 MCP）

### 变更类型

install（新 MCP + 已记账 preset 的修改重同步）

### 内容 / 原因

- 用户要求对比 3 家 Wireshark MCP（bx33661 / sarthaksiddha / jayimu）后融合进自己的 MCP，
  且"安装后不随 dsh 启动、需要时自动触发"。中途用户明确"尽量不要太重" → 放弃 bx 52 工具基座。
- 新项目 `D:\AI_python\无实际文件区\wireshark-mcp-lite\`（**不进本仓库**）：
  单文件 `server.py`（FastMCP stdio，10 工具），jayimu 骨架 + bx 的 allowed_dirs 思想 +
  sarthak 的 anonymize 参数；stdio 冒烟通过（tools/list=10，randpkt 夹具实测；修过
  `dns.resp.addr` 非法字段真 bug）。
- `reverse` composition 末尾加 `mcp-wireshark-lite` 行（stdio，`failOnStartupError: false`）：
  不改 profile、不需重启，新开「逆向模式」会话即生效。前置 = 本机 Wireshark tshark 4.6.4。

### 影响文件

- `SKILLS.md`：表格追加 `wireshark-mcp-lite MCP` 行 + 末尾追加本日日志
- `presets\reverse\agent.cordis.yml`：重同步（含新增段，SHA256 已核对一致）
- `presets\reverse\README.md`：4→5 改写 + 新增第 5 个 MCP 小节
- `INSTALL.md`：reverse 节 / MCP 节（4→5 + 表格行 + 新增 `wireshark MCP` 小节 + 不迁移节）

### 待用户实测

新开「逆向模式」会话，确认 `mcp__wireshark__*`（10 工具）并跑一次真实 pcap。

---

## 2026-10-08 — DSH 0.2.0-rc.2 升级后双模式恢复：渗透插件 rc.30→rc.36；逆向 preset 改声明式

### 变更类型

插件升级（`dsh-pentest` 到当天最新 rc.36）+ 已记账条目修改（`reverse` preset composition 重排 + profile patch 加声明行）+ 文档（README / INSTALL.md / `config\cordis.patch.yml`）

### 内容

**起因**：用户把 DSH 升到 0.2.0-rc.2 后，会话选择器里「渗透模式」「逆向模式」都不见了。查明是**两个独立原因**：

- **渗透**：插件 `0.1.0-rc.30` 的 peerDependencies pin 死 `0.1.0-rc.6`，新版 DSH 在启动期直接拒载
  （"it stays installed but profile startup denies it"）。`dsh plugin add <latest-url>` 与 `update`
  因 lockfile 未变都是 no-op；`remove` 后重 `add` 才真正拉到当天刚发布的 `rc.36`
  （peer 已放宽到 `^0.1.0-rc.6 || ^0.2.0-rc.1`，上游 rc.34 的修复），重装后不兼容警告消失。
  历史库 `storages/pentest-sessions.db`（4.2 MB）全程未动，数据不丢。
- **逆向**：0.2.0 移除了 `.agent-presets\` 的**目录扫描**
  （`dsh-agent-preset-registry` README 明示 "neither scans directories nor accepts preset paths"），
  preset 必须是 composition 里的一行 `@deepseek-ai/dsh-agent-preset` 声明。
  目录里的文件完好（hash 与备份一致）—— 只是没人再来读它了。
  迁移：composition 按新版 `standard`（`dsh-web-app/presets/standard.patch.yml`）重排
  （`dsh-workflow-worker-thread` 包在新版已删 → 换 `workflow-ptc`；补新版新增的
  `tool-plugin-manager`；`tool-ralph` 维持本 preset 原有启用），逆向 persona 与 4 个 MCP 行原样保留；
  profile patch 末尾加 `preset-reverse` 声明行，用 `cordis:include` 指向原文件
  （`!!js` 由 include 的 entry-list schema 保留，与 pentest rc.36 的 `preset-root` 同构）。
- **验证（重启前能做的都做了）**：YAML 语法（23 个顶层 entry、3 个 `!!js` 保留）；
  36 行 27 个包逐行存在性校验**零缺失**；`dsh --profile web --dump-config` exit 0，
  `preset-reverse` 与官方 `standard/ptc/minimal/cordis` 并列、其下有 include 路径；
  include 的 `file:///` 路径可解析到真实文件（24,671 B）。
- **待用户重启实测**：preset 声明只在启动期装载。重启后新开会话，确认「渗透模式」「逆向模式」
  都在选择器里，且逆向会话能拉起 MCP（挂载失败会让会话创建直接报错，不会静默半组装）。

### 影响文件

- `presets\reverse\agent.cordis.yml`（22,528 B → 24,671 B；与 `$DSH_HOME\.agent-presets\reverse\` SHA256 一致）
- `presets\reverse\README.md`（恢复步骤加"写声明行"；表格与维护段同步）
- `config\cordis.patch.yml`（`[]` → 含 `preset-reverse` 声明行 + 换机器改路径提示）
- `INSTALL.md`（reverse 节头部/第 2.5 步/验证/实测/维护；头部配套说明与 MCP 安装注）
- `SKILLS.md`（追加本轮日志）
- DSH 本机：`profiles\web\node_modules\@howmp\dsh-pentest`（rc.30 → rc.36）、
  `profiles\web\cordis.patch.yml`（加声明行）、`.agent-presets\reverse\agent.cordis.yml`（重排）

---
## 2026-10-02 — 4 个 MCP 从 profile 层移入 agent preset `reverse`：由「启动即拉起」改为「按需启动」

### 变更类型

配置迁移（MCP 挂载层变化）+ 凭据硬化 + 扫描器修复 + 已记账条目修改（`reverse` preset、`reverse-skill-router`）+ 文档勘误

### 内容

**起因**：用户反馈「看到 dsh web 启动的时候还启动了其他 mcp 服务，这会导致服务卡死和空闲，
mcp 应该在需要用到的时候启动才对」。先调查后动手，用户在三个方案里选定「移入『逆向模式』preset」。

- **先查清成因（实测，不含推断）**：`dsh web`（pid 25184）直接 spawn 3 条常驻 stdio 链
  （camoufox / jadx / ida），**10 个进程、约 300 MB**，启动后 9~13 秒内全部拉起；
  空闲 CPU 8 秒采样增量为 **0** —— 所以「空闲」是常驻内存，「卡」在启动期，根源是
  `dsh-mcp-client` 的 `apply()` **同步等待「连接 + `tools/list`」完成**才激活，
  且其 Config schema **没有任何懒加载字段**、超时继承 MCP SDK（各 60 s）。
  → **结论：没有配置级的按需开关，只能换挂载层。**
- **迁移**：4 段 `insert` 原样搬到 `presets\reverse\agent.cordis.yml`。依据是
  `dsh-agent-presets` 的 **"reading never mounts"** —— preset 是 DSH 里唯一的惰性挂载点
  （读文件只解析不 compose，只有新会话选中才挂载）。4 行只注册工具、不 `provide` 服务，
  因此**无需 `isolate` realm**。
- **实测结果**：改完 profile patch 后借 `patchReload: live` 热加载，**MCP 进程 10 → 0**；
  `dsh web` 存活（HTTP 401 = 浏览器信任围栏，正常）；`--dump-config` exit 0、无 mcp-client 行、无报错。
  能力清单复测：4 条 MCP 全部标为 `preset:reverse`。
- **语义变化（代价，已在文档中明示）**：**普通会话不再有 `mcp__*` 工具**，
  要调用必须先新开「逆向模式」会话；开该会话时要等服务器连上。
  `config\cordis.patch.yml` 因此变为空 `[]` + 说明注释（留作改回常驻的对照）。
- **凭据硬化（顺带修掉一处旧隐患）**：analyzer 的 `Authorization: Bearer <token>` 原先
  **明文写在 `config\cordis.patch.yml` 里并随备份进私有仓库**（旧账本以「泄漏面仅限本机
  23816 端口」为由接受）。现改为 `!!js process.env.ANALYZER_MCP_TOKEN` 引用
  （`!!js` 求值是 `new Function` + `with(ctx)`，**有 `process` 无 `require`**，
  只能读环境变量），真值移入 `$DSH_HOME\.env` —— **该文件不入仓库**。
- **扫描器修复（关键连带影响）**：`scan-capabilities.ps1` 原先**只扫 profile 的
  `cordis.patch.yml`**，MCP 搬家后会**静默漏报全部 MCP** —— 而它是逆向模式「唯一事实源」。
  已扩为 **profile 层 + preset 层双扫描**，清单新增「层」列，并修正按需语义下的告警文案
  （preset 层 MCP 未监听**属正常态**，不再误报「前置未就绪」）。
- **文档勘误**：账本与 INSTALL.md 多处引用的 **`preset_probe` 工具在本机已不存在**
  （旧会话动态定义的 cordis 包，重启即消失、从未落盘）。相关验证步骤改为
  「能力扫描器 + 新开会话实测」；旧行按只追加原则保留原文并就地标注失效。
- **验证方式变化**：`dsh --profile web --dump-config` **看不到 preset 里的行**了。

### 影响文件

| 文件 | 改动 |
|---|---|
| `config\cordis.patch.yml` | 4 段 MCP `insert` 移除（现为空 `[]` + 说明注释）；analyzer 明文 token 一并移除 |
| `config\settings.yaml` | **顺带修复一处旧缺陷**：备份里一直是 2 行残桩（只有 `ui-onboarding`），live 实为 90 行；本次按实同步（已确认只含 `apiKeyEnv` 环境变量名，无明文密钥） |
| `presets\reverse\agent.cordis.yml` | 新增 4 段 MCP 挂载（含 `!!js` token 引用）；顶部设计声明与 `python` 例外说明更新 |
| `presets\reverse\README.md` | 重写：MCP 段落、"不需要 realm"表述、`preset_probe` 失效说明、恢复步骤 |
| `skills\reverse-skill-router\scripts\scan-capabilities.ps1` | profile + preset 双层扫描、`Read-McpFromFile` 抽取、清单「层」列、告警文案修正 |
| `SKILLS.md` | 4 条 MCP 行 + `reverse` preset 行就地追加迁移注记；「安装顺序」新增 2026-10-02 补记；追加日志 |
| `INSTALL.md` | MCP 节重写（两层对比表 + 改回常驻指引 + 验证方式变化）、preset 节验证步骤与凭据步、安装顺序、analyzer 凭据段与交叉引用 |
| `CHANGELOG.md` | 本条 |
| `$DSH_HOME\.env`（**不入仓库**） | 新增 `ANALYZER_MCP_TOKEN`；`.env` 只在启动时读取，需重启 DSH |

### 回退

`git revert` 本条即可恢复 profile 层挂载；或手工把 `presets\reverse\agent.cordis.yml`
末尾 4 段搬回 `config\cordis.patch.yml` 并包进 `- insert:`（analyzer 的 headers 需改回明文形式）。

### 未完成

- **「逆向模式」会话能拉起这 4 个 MCP 尚未实测** —— preset 只有被新会话选中才 compose，
  需用户新开一个逆向模式会话确认 `mcp__*` 工具出现（挂载失败会让会话创建直接报错，不会静默半组装）。
- `ANALYZER_MCP_TOKEN` 需**重启 DSH** 才对 analyzer 生效（当前 `authEnabled: false`，不影响连通）。

### 已做的静态验证（不能替代上面的实测）

- **composition 解析 + 插件 schema：4/4 通过**（两种环境状态各一次）。用 Loader 自己的
  YAML 方言（`cordis-plugin-include` 导出的 `entryListSchema`，它自带 `!!js` 类型）解析，
  再把每行 `config` 喂给 `dsh-mcp-client` 自己的 Schemastery schema。无 token →
  `headers = {}`；有 token → `headers = {"Authorization":"Bearer tok123"}`。
- **包名解析有实现保证**：`dsh-agent-presets/mount` 的 `PresetTree.import()` 把裸包名
  **从"已安装 harness"的 base** 解析（源码注释原文：*"a locally authored preset lives under the
  user's home, where Node's upward `node_modules` walk never reaches the harness's own dependencies,
  so every `@deepseek-ai/dsh-*` row would fail to import. The mount records the host composition's
  base instead … and bare names resolve from there."*）。本机该包确实在 harness 下
  （239 个 `@deepseek-ai/*` 包），profile 的 `node_modules` 里反而没有。
- **`failOnStartupError` 默认就是 `false`**（schema `z.boolean().default(false)`）——
  所以 MCP 连不上**不会**阻断逆向会话创建，只会静默少掉工具；与预设里"用前先探活"的纪律一致。
- **生命周期**：preset 子树归其 agent 所有，agent 拆掉即 dispose 子树 → MCP 服务器随会话结束退出
  （不会留下新的常驻空闲进程）；代价是每个逆向会话有自己的一份服务器进程。

---

## 2026-09-30 — 接入 Anything Analyzer：新增 `protocol` 域 + 抓包/协议分析能力（skill + MCP 各一条）

### 变更类型

安装（新 skill + 新 MCP 挂载）+ 已记账条目修改（`reverse-skill-router`）+ 扫描器修复 + 配置同步

### 内容

**起因**：用户给了 `https://github.com/Mouseww/anything-analyzer`，要求「看看是否对逆向有用，有用的话就配置进来」。

- **评估结论：有用，但增量只落在一个具体缺口** —— 非浏览器流量（手机 App / 桌面应用 / CLI /
  Python 脚本 / IoT）的抓包会话能被 Agent 经 MCP 直读。此前 camoufox 只能抓浏览器，
  Reqable / Fiddler / mitmdump 抓得到但 Agent 读不到。**刻意划清的不重叠部分**：
  指纹伪造只在 JS 层（弱于 camoufox 的引擎级补丁）；MITM 是只读捕获（要改包用 mitmdump）；
  `run_analysis` / `chat_followup` 需要配 LLM Key，逆向模式下不配（由 Agent 自己分析）。
  评估过程（读源码而非 README）与实测数据全部留在案件库
  `D:\AI_python\reverse-cases\2026-09-30_anything-analyzer\`。
- **新增 skill**：`skills\anything-analyzer\`（5 文件约 24 KB，本地自制、自包含：
  `SKILL.md` + 两份 `references\` + 两个 `scripts\`）。它背后的 Electron GUI（98.6 MB）**只记配方不备份**。
- **新增 MCP 挂载**：`serverName: analyzer`，写在 `config\cordis.patch.yml`。
  **本机第一个 `transport: streamable-http` 挂载**（其余 3 个都是 stdio）—— MCP Server 跑在 Electron
  主进程里，不可能脱离 GUI 独立跑，所以上游没有 stdio 模式。host 由出厂 `0.0.0.0` 收紧为 `127.0.0.1`，
  `authEnabled` 保持 true，`systemProxy` 保持 false。
- **`reverse-skill-router` 改动（3 个文件）**：
  - `references\domain-registry.json`：**新增 `protocol`（协议逆向 / 非浏览器流量）域**，
    主技能 = `anything-analyzer`；并把 anything-analyzer 登记为 **web / android 两域的支撑技能**
    （各配 `supportRoles` 文案）。域就绪度 5 域 → 6 域。
  - `SKILL.md`：域表加 `protocol` 行、web/android 行补支撑技能说明、§9 边界表加「抓包 / 协议还原」行。
  - `scripts\scan-capabilities.ps1`：**修一个真实缺口** —— 原扫描器只解析 stdio 的 `command`，
    `transport: streamable-http` 的条目在 capabilities.md 里 command 与外部前置两列**全为空**。
    已改为解析 `transport` / `url`、command 列回落到 url，并补 `analyzer` 的端口探活与外部前置文案。
- **实测（端到端，非"装上就算"）**：`create_session → start_capture → navigate → get_requests`
  闭环成功，Agent 读到完整 method/url/status/headers/response body；`cdp_send_command` +
  `Network.setUserAgentOverride` 可洗掉默认 UA 里的 `anything-analyzer/<版本>` 工具指纹。
  三个踩到的坑（start_capture 后首次导航漏抓 / UA 暴露工具名 / `Invoke-WebRequest` 发 MCP 第二个必 404）
  都写进了 skill 与 INSTALL.md。

### 顺带发现：DSH 自己迁移了 `settings.yaml`（**不是本次操作造成的**）

同步 `config\settings.yaml` 时发现本地该文件已被 DSH 从 21 行裁到 2 行（mtime `2026/9/30 10:05:39`），
DSH 自己留了原版 `~\.dsh\settings.yaml.imported`（1001 B，mtime `9:40:43`）。
**迁移掉的是 LLM provider 定义**（claudex / a-lang / lesec 三个 provider 的 baseURL 与 model 列表）
与 `agent-presets.default: standard`；**API key 本身在 `.credentials.yaml` 里，从未进过本仓库**。
为不让新环境缺这些 provider 定义，**把 `settings.yaml.imported` 原样备份为
`config\settings.yaml.imported`**（含 provider 定义与 `apiKeyEnv` 环境变量名，**不含任何密钥值**），
并在 `INSTALL.md` 里标注它是什么。**此事未经用户要求，属账本"迁移不丢失"职责范围的主动补记。**

### 影响文件

- 新增：`skills\anything-analyzer\`（6 文件，含 `scripts\mcp-call.mjs` —— 通用 MCP 调用探针，
  **自动从 `mcp-server-config.json` 读 token**，不必每次手传凭据；有了它 skill 才真正自包含，
  `references\mcp-tools.md` 里的"手动调用"示例不再指向案件库路径）
- 新增：`config\settings.yaml.imported`（DSH 迁移前的原版，含 LLM provider 定义，无密钥）
- 修改：`config\cordis.patch.yml`（+ `mcp-anything-analyzer` 条目）、`config\settings.yaml`（同步 DSH 现状）
- 修改：`skills\reverse-skill-router\{SKILL.md, references\domain-registry.json, scripts\scan-capabilities.ps1}`
- 修改：`SKILLS.md`（+2 条表格行 +1 条日志）、`INSTALL.md`（MCP 节 3→4 个 + 新增 `### analyzer MCP` 与
  `## anything-analyzer` 两节）、本文件

### 未做 / 待用户拍板

- **CA 根证书未装入系统信任库** → 目前只能抓 HTTP，HTTPS MITM 会因证书不受信失败
  （浏览器侧 CDP 抓包不受此限）。装它是系统级安全变更（`certutil -addstore Root` + 管理员权限）。
- `mcp__analyzer__*` 工具需**重启 DSH** 才出现在会话里（本次只做到 MCP 协议层实证：
  SDK 客户端 `listTools` 返回 30 个工具、探活脚本 exit 0）。

---

## 2026-09-30 — 本机彻底移除 Anaconda；MCP 幽灵依赖解除；5 个 conda 环境迁移为 uv 环境

### 变更类型

环境变更 + 文档修正（无 skill / plugin / preset 增删）

### 内容

- **Anaconda 整机移除**（用户要求）：base 5.18 GB + pkgs 缓存经官方 `Uninstall-Anaconda3.exe /S` 清除；
  conda 外壳（`profile.ps1` hook、cmd `AutoRun`、`~\.condarc`、`~\.conda\`、`%LOCALAPPDATA%\conda\`、
  开始菜单）、注册表 PythonCore、`kuai` 与 `juhe6 - 副本` 两个废弃环境一并清掉。
- **uv 改为独立安装**：`C:\Users\y\.local\bin\uv.exe`（0.12.20），不再依赖 anaconda。已置于用户 PATH 最前。
- **`D:\dev\py\env` 下 5 个 conda 环境原地重建为 uv 环境**（163 / dashixiong / juhe5 / juhe6 / L），
  包清单与原环境逐包一致；juhe5 的 `torch==2.2.1+cu118` 实测 CUDA 可用。
- **`config\cordis.patch.yml`：jadx / ida 两个 MCP 的 `command` 由 `uv` / `uvx` 改为绝对路径**
  `C:\Users\y\.local\bin\uv.exe` / `uvx.exe` —— 这是**解除幽灵依赖的实质修复**：此前这两个 MCP 依赖
  anaconda 目录里的 uv，anaconda 一动 MCP 就断。

### 原因

用户要求"卸载 anaconda、全局只用 uv，但不破坏正在使用的既有环境"。
账本此前已如实记下这个幽灵依赖（见 `SKILLS.md` 2026-09-26 补记与
`skills\apk-reverse\references\local-environment.md`），本次把它连同宿主一起解决。

### 影响文件

- `config\AGENTS.md` —— 红线"Python 一律 uv"改为记录 uv 绝对路径，并说明本机已无可用 `python`（只剩 Store 存根）。
- `config\cordis.patch.yml` —— MCP `command` 改绝对路径（**必须重启 DSH 才生效**）。
- `skills\apk-reverse\references\local-environment.md` —— 幽灵依赖一节改为"已修"。
- `skills\dev-hygiene\SKILL.md`、`skills\dev-hygiene\references\uv-清华源.md` —— anaconda 相关禁令标注为历史（对象已不存在）。
- `skills\firerpa\SKILL.md` —— 两处"PATH 上的 python 是 Anaconda base"改为"PATH 上已无可用 python"。
- `skills\reverse-skill-router\scripts\scan-capabilities.ps1` —— 注释更新（探测逻辑保留，用于识别新引入的同类污染）。
- `INSTALL.md` —— 新增一节「本机彻底移除 Anaconda，全局改用独立 uv」（含复现步骤与踩坑）。

### 回退

`git revert <this commit>` 可还原文档与配置；**anaconda 本体不可回退**（已走回收站）。
若需回退到 conda 时代的某个环境：`D:\dev\py\_conda_migration_2026-09-29\envs\pip-freeze-*.txt` 有完整包清单，
按 `INSTALL.md` 新增节的命令用 uv 重建即可。

---
## 2026-09-30 — 新建「逆向模式」agent preset；账本新增第四类「agent preset」；apk-reverse 首次入库

### 变更类型

新增（新 agent preset / 新 skill 首次记账 / **规则范围扩展**）+ 一处勘误（INSTALL.md 的 MCP 计数）

### 内容

**1. 新 agent preset `reverse`（会话里叫「逆向模式」）**

旧的那个是**空壳**：`$DSH_HOME\.agent-presets\reverse\agent.cordis.yml` 逐行等于 DSH 自带的 `standard`，
persona 仍是 "You are a coding agent"。已按用户要求**卸载（回收站，可还原）后重建**：
`preset_probe copy standard → reverse` 拷骨架，只写**身份与硬规则**（默认已授权 / 开工五步 / 统一验收骨架 /
脚本执行分级 / 增删自检 / 事实纪律）。`preset_probe validate reverse` → `mounted OK`。
**能力不进 composition**：本机工具状态由生成物 `$DSH_HOME\reverse\capabilities.md` 提供，
所以装了新工具**不需要改 preset**。

**2. 账本新增第四类「agent preset」**

preset 住在 `$DSH_HOME\.agent-presets\<id>\`，**不在任何 profile 的 `package.json` / `bundles` 里**
—— 旧的三类（skill / DSH 插件 / MCP 挂载）既覆盖不到、换机器也不会自动回来，逆向模式会凭空消失。
落地：新增 `presets\<id>\` 备份形态（composition + `preset.yml` + `README.md`）；
`config\AGENTS.md` 的范围 bullet 改 "Four kinds" 并新增一条 preset 规则；`install.ps1` 增加 preset 恢复段；
`INSTALL.md` 增加对应小节。仅记录用户本地自建的 preset；部署自带的与第三方包内的 preset 不记账。

**3. `apk-reverse` 首次入库（此前完全在账本之外）**

116 文件 / 1,897,362 B → `skills\apk-reverse\`。来源 `https://github.com/newliver666/apk-reverse`。
**融合层两件自制件** `references\local-environment.md`、`references\known-local-defects.md`
（后者记上游自认未修的两个活缺陷：`so_constpatch.py` 丢 zip `extra` 破坏 4 KB 对齐、
`repack.py` 的 `^lib/[^/]+\.so$` 永远匹配不到 `lib/arm64-v8a/*.so`），`SKILL.md` 顶部加 local overlay
并就地修正"jadx 是最后手段"这条与实况冲突的口径。

**4. `reverse-skill-router` 重写为「路由与治理层」**

旧版是"上游包说明书"，且有两处硬伤：description 自称"按**包内** RULES.md"（该文件不在技能目录里）、
正文把 `powershell` 5.1 当标准调用（撞 `dev-hygiene` 红线）。新版 = 三个事实源（能力清单 / 域注册表 /
上游素材库）+ 域路由表 + 授权登记模板（默认 `granted`）+ 案件目录规范 + 统一验收清单 + 脚本分级 +
增删自检 + 上游素材库用法；新增机器可读的 `references\domain-registry.json`；
`scripts\restore.ps1` 改 `pwsh` + `#Requires -Version 7.0`；新增 `scripts\scan-capabilities.ps1`
（能力清单生成器 + 悬空引用检查）。

**5. `firerpa` 归位为 Android 域的动态执行臂**（用户指出）

它不是"外围自动化"：负责实机 UI 驱动、补丁后功能回归、必须让 App 自己跑起来才能观察的行为。
`domain-registry.json` 新增 `supportRoles` 字段，扫描器输出该字段；路由技能里的错误定位已改正。

**6. 勘误与留痕**

- `INSTALL.md` MCP 节正文"挂了 **4 个** MCP server" → **3 个**（context-mode 已于 2026-09-29 卸载，
  正文与实物不符已存在一段时间）。
- `SKILLS.md` 表格多行仍写 `local/skill/<name>/`，而镜像实际在 `skills\<name>\`。按"只追加、不覆盖"
  未改旧行，只在安装顺序区加一条勘误留痕；2026-09-30 起新增的行统一写 `skills\<name>\`。

### 影响文件

- 新增 `presets\reverse\{agent.cordis.yml,preset.yml,README.md}`
- 新增 `skills\apk-reverse\`（116 文件，整份镜像）
- 更新 `skills\reverse-skill-router\`（5 文件）、`skills\wmpf-miniapp-reverse\`（重新同步）
- 更新 `SKILLS.md`（表格 2 行 + 安装顺序 2 条 + 日志 1 条）、`INSTALL.md`（新 2 节 + 1 处勘误）、
  `config\AGENTS.md`（4 处）、`install.ps1`（preset 段 + `-SkipPresets`）、本文件
- 更新 `skills\skills-inventory\SKILL.md`（**规则扩展同步到这一定义处**：范围三类→四类、仓库结构加
  `presets\<id>\`、九条规矩与「什么时候动它」的清点项、表格列说明，并新增
  「agent preset 怎么备份：整份 composition 副本」一节）

### 验证

- `preset_probe validate reverse` → `mounted OK: reverse`
- 能力扫描器实跑 → `tools: 27 present / 7 missing | skills: 8 | mcp: 3 | devices: 1 | warnings: 7`，
  悬空引用 0；并如实报出 **anaconda 幽灵依赖**（`python`/`uv`/`uvx` 实体都在 `anaconda3`，
  而 jadx / ida 两个 MCP 依赖的正是它们）
- 镜像核对：`skills\apk-reverse` 116f/1,897,362B、`skills\reverse-skill-router` 5f/52,802B、
  `skills\wmpf-miniapp-reverse` 7f/39,275B（源与镜像字节一致）
- `presets\reverse\` 两个文件 SHA256 与源一致

---

## 2026-09-28 — 用户弃用 donsetch：整体卸载并还原全部改动

### 变更类型

卸载 + 还原（用户评估该工具"没什么大用"后要求移除并还原改过的 DSH 原生配置）。

### 内容

- **插件**：`dsh plugin --profile web remove @dsh-external/donsetch`（pnpm 470ms）→ `package.json` 的
  `dependencies`/`bundles` 恢复 6+4 结构；`dsh --profile web --dump-config` exit 0 复核：
  `dsh-think-zh` / `modsearch` / `dsh-pentest` / `dsh-ding` 四个插件与 `camoufox` / `jadx` / `ida` /
  `context-mode` 四个 MCP 及 `ctx-router` 全部完好，`searchProvider: modsearch` 不变。
- **还原原生配置**：`$DSH_HOME/AGENTS.md` 删除「搜索与联网检索 —— 自动路由」常驻段（web-search-router 规则一并撤出）；
  `$DSH_HOME/skills/web-search-router/` 回收站（0.01MB）。
- **清理足迹**：`~/.cache/donsetch`（38.86MB）、`%LOCALAPPDATA%\donsetch`（48.25MB）回收站；
  daemon 进程（PID 34576，因守护占用缓存 exe 导致删除失败 → 先终止再删）；`%TEMP%` 的 package.json 备份已删。
- **账本**：`plugins\donsetch\RECIPE.md` 顶部标注已卸载（保留作恢复参考）；`SKILLS.md` 表格行标注 + 三次补记；
  `INSTALL.md` 的 donsetch 与 web-search-router 两节标注；`install.ps1` 待办标注"恢复机器时不要安装"；
  `config\AGENTS.md` / `config\profile\package.json` 重新同步；账本 `skills\web-search-router\` 镜像删除（回收站）。

### 原因

用户实测后评估该工具（Cloudflare 交互式挑战解不了、搜索后端部分不可用）不值得保留；卸载同时要求还原
DSH 原生配置且不得破坏 dsh —— 全程走官方卸载命令 + dump-config 复核 + 回收站删除，未动任何其它配置。

### 影响

- `plugins\donsetch\RECIPE.md` / `SKILLS.md` / `INSTALL.md` / `install.ps1` / `CHANGELOG.md`（本条目）
- `config\AGENTS.md` / `config\profile\package.json`（还原后的当前实况）
- 删除（回收站，可还原）：本机 donsetch 全部足迹 + 账本 `skills\web-search-router\` 镜像

---

## 2026-09-28 — donsetch 验收通过：补齐 daemon 代理池 + 记录能力边界

### 变更类型

配置补齐 + 文档记录（无条目增删）。

### 内容

用户重启后验收：`donsetch_status` = **ready**，注册 4 个工具（`donsetch_web_fetch` / `donsetch_web_search` /
`donsetch_web_crawl` / `donsetch_web_screenshot`），doctor **22/26 passed、0 failed**。实测：

- **搜索**：keyless 多引擎返回带来源条目（`3/4 backends available`，非全部后端可用）；
- **抓取**：`example.com`、`baidu.com`、`news.ycombinator.com` 均正常；
- **爬虫**：`docs.python.org` 的 `mode="full"` 抓到正文；`mode="map"` 在无 sitemap 站返回空列表（工具行为，非故障）；
- **反爬边界（诚实记录）**：`nowsecure.nl` 的 Cloudflare **交互式挑战**报
  `interactive captcha or challenge could not be solved automatically … Use an Agent browser` ——
  自动绕过到此为止，应改走本机 `camoufox-reverse`，不要死循环重试。

**本次新发现并补齐的必做配置**：daemon 由 dsh 进程 spawn，**不继承 shell 的 `HTTPS_PROXY`** → 国外站直连失败。
解法：`<内置二进制> proxy add http://127.0.0.1:7890`（落在 `%LOCALAPPDATA%\donsetch\proxies.txt`，
**热生效、不用重启**）。注意探测输出 `dead no exit IP returned` 有误导性（探测端点被规则直连），实测代理可用。

### 原因

用户提示"国外网站要使用本地代理"；且 donsetch 的自动绕过能力需要写清边界，避免后续会话在挑战页上反复失败。

### 影响

- `plugins\donsetch\RECIPE.md`（新增「本机必做：给 daemon 配代理池」+ 能力边界 + crawl map 说明）
- `INSTALL.md`（donsetch 节补代理池要点）
- `skills\web-search-router\SKILL.md`（失败降级段补 3 条：代理池、Cloudflare 挑战转向 camoufox、crawl map 语义）+ 账本镜像
- `SKILLS.md`（追加日志）

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

---

## 2026-09-28 — 更正：context-mode 自动路由改为自写原生 DSH 插件 `ctx-router`

**背景**：同日早些时候的条目声称"自动路由已实现、重启后生效"。用户重启 `dsh web` 后实测，
按特征挂上去的命令**不被拦截** —— 该结论作废。本条记录真实根因与新解法。

### 根因：hook 桥接插件被 cordis 的 `inject` 永久挂起

`@deepseek-ai/dsh-hooks-claude-code` 的 `inject = ["shell", "sessionProjections"]`。
cordis 的语义是**声明的服务不满足就永远等待、`apply` 根本不执行**（既不报错也不警告）。
因此插件包能正常 `import`（loader 不报错），但**一个 hook 都不注册**，配置根本不读。

证据：

- 会话 `session.v3.jsonl.zstd` 里 **hook 事件 = 0**，连不需要 matcher 的 `SessionStart` 也不触发；
- 把 `configPath` 故意指向不存在的文件，**没有任何警告** —— 因为 `apply` 没跑。

顺带确认（避免误判）：loader 对**解析不到的包**是 **fail-loud**（实测 `ERR_MODULE_NOT_FOUND`
终止启动），所以"没报错"恰恰证明包解析无辜，卡点是 `inject`。

### 已排除（全部实测）

YAML 缩进/格式；`insert` 语义（`applyEntryPatches`：无 `id` 的 insert 就是
`data.push(...insert)` 插到顶层）；行 `id` 与插件内部 `name` 同名；`configPath` 相对/绝对；
hooks.json 语法；matcher 写法；profile 差异（新建隔离 profile `hooktest` 复现，
且同一个 insert 里挂的 MCP 条目**工作正常** → insert 机制无辜）。

### 新解法：原生插件挂 `tools/pre-execute`

`plugins\dsh-ctx-router\`（自写，源码唯一副本在账本）：

- 拦截缝契约来自 `@deepseek-ai/dsh-tools`：
  `waterfall(carrier, 'tools/pre-execute', exec, () => ({ kind: 'allow' }))`，
  返回 `{ kind: 'deny', reason }` → 拦下，`reason` 以 `Error:` 回给模型；handler 形如 `(exec, next)`；
- `exec` 实测字段：`token, callId, rootCallId, name, signal, agent, deferContext, concludeTurn, arguments`；
- **不依赖任何服务**，也**不需要 `dsh plugin add`** —— `insert.name` 直接写 `file:///` URL，
  cordis loader 用 `import()` 加载（实测有效）；
- 拦截范围 / 逃生舱与旧适配层一致；内部 **fail-open**，绝不阻断会话。

### 实测

- `Get-ChildItem <dir> -Recurse -File` → 被拦，`ctx-router.log` 记 `DENY tool=pwsh`；
- `pwd` → 正常放行；
- `dsh --profile web --dump-config` → 出现 `id: ctx-router`（配置树第 644-645 行）；
- **不需要重启**：本机 profile 是 `patchReload: live`，改完 `cordis.patch.yml` 后
  **同一会话的下一条命令立刻被拦** —— 同时更正上一条"必须重启"的结论。

### 文件

- 新增 `plugins\dsh-ctx-router\`（`RECIPE.md` + `lib\index.js` + `package.json`）
- `plugins\context-mode-dsh-hook\RECIPE.md` 顶部加**废弃**警示（存档保留，新环境不再安装）
- `config\cordis.patch.yml`：`hooks-claude-code` → `ctx-router`
- `config\AGENTS.md`：常驻规则中"PreToolUse hook 兜底"改为"自写插件 `ctx-router` 兜底"
- `INSTALL.md` 的 context-mode 节改写；`install.ps1` 落位步骤改写

### 清理

隔离 profile `hooktest`、`test-hook.mjs`、`test-hooks.json`、旧适配层两个文件、
`hook-trace.log` **全部走回收站**（可还原）；会话自建的 `%TEMP%` 诊断文件硬删。
`$DSH_HOME\context-mode\` 现只剩 `content/`、`sessions/`、`ctx-router.log`。

### 验证（用户"检查是否生效"）

- `Get-ChildItem <目录> -Recurse -File` → **被拦**，提示 `（命中：递归目录扫描）`；
- `pwd` → **正常放行**；
- `ctx-router.log` 已积累 23 条拦截，其中包含**另一个并行会话**（taobao 逆向）的命令 ——
  证明对所有会话**全局生效**。

### 补记（同日，验证阶段）：源码改动需重启；拦截日志已加强

- **`patchReload: live` 只重放配置补丁，不会重新 `import` 已加载过的模块**（ESM 缓存）：
  改 `cordis.patch.yml` 热重载即时生效；**改 `lib\index.js` 必须重启** `dsh web`
  （实测：改完源码后拦截日志仍输出旧格式，重启后才变）。
- 首版拦截日志只存命令前 200 字符、且不记命中原因 → 22 条拦截里 **10 条无法反推命中规则**，
  其中几条表面无害（`New-Item` 建目录、`git config user.name`、`adb shell settings put`、
  跑 `python.exe`、`Get-Process` 查进程），但当时**无法证明是否误拦**。
- 日志已改为记录 `why=`（命中规则）、`arglen=`（命令总长）、`arg=`（前 400 字符）；
  `routeReason` 返回 `{reason, why}`。**该加强需重启后生效**（首版拦截功能本身正常）。

---

## 2026-09-29 — 用户弃用 context-mode：整体卸载并还原 DSH 原生配置

**背景**：用户实测后判断该工具"用处也不大"，要求**整体卸载**（MCP + 插件 + 本地数据）
并还原我改过的 DSH 原生配置，明确强调**不要破坏 dsh**。

### 卸载（顺序是关键：先改配置、后删文件）

若先删 `plugins\dsh-ctx-router\` 而配置仍挂着它，热重载会 `ERR_MODULE_NOT_FOUND`。实际顺序：

1. 备份 profile 的 `cordis.patch.yml` → `%TEMP%\cordis.patch.yml.bak-20260929-083027`
   （7239 B，SHA256 `8DE98535…`）；
2. 删 `mcp-context-mode` 与 `ctx-router` 两个 `insert` 条目；
3. `dsh --profile web --dump-config` → **exit 0、627 行、零错误**，只剩 camoufox / jadx / ida；
4. 删 `$DSH_HOME\AGENTS.md` 的「上下文保护 — 大输出走沙箱（context-mode）」整节；
5. `npm uninstall -g context-mode` → **removed 140 packages**（包目录与两个 shim 均消失）；
6. `$DSH_HOME\plugins\dsh-ctx-router\`（0.01 MB）与 `$DSH_HOME\context-mode\`（2.13 MB）走回收站。

### 账本

- `config\cordis.patch.yml`、`config\AGENTS.md` 重新同步为还原后实况
- `plugins\dsh-ctx-router\` 与 `plugins\context-mode-dsh-hook\` 两个自制件目录移入回收站
  （git 历史可恢复：`git checkout c3eab63 -- plugins/`）
- `INSTALL.md`：删 MCP 表格行；该节改写为"已卸载，新环境不要安装"
- `install.ps1`：该条待办改写为"不要安装"
- `SKILLS.md`：表格行按 append-only 规则**保留**，另追加卸载日志

### 顺带验证

卸载过程中我自己的一条 `Select-String` 命令**被 ctx-router 拦下**（`（命中：全文检索）`），
用 `ctx-allow` 逃生舱绕过 —— 证明插件在被卸载前仍在正常工作。全程两次 `dump-config`
（卸载前含两条目、卸载后 627 行）**均 exit 0**，DSH 未受影响。
