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
