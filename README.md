# dsh_skills

DSH 环境的**完整可迁移备份**（私有仓库）：skill、MCP、第三方插件、常驻规则与 DSH 配置。
每次本地有变更就提交推送一次 —— **git 历史取代了原先的按日 zip 快照**。

**新环境只需要这个仓库地址：**

```powershell
git clone https://github.com/canglingzhiyue/dsh_skills.git
cd dsh_skills
pwsh -File install.ps1 -DryRun     # 先看它会做什么（不落盘）
pwsh -File install.ps1             # 执行（会先备份现有配置）
```

- **本机对应目录**：`D:\AI_python\skills_backup`（就是本仓库的工作副本）
- **skill 权威位置**：`C:\Users\y\.dsh\skills`（本仓库 `skills/` 是它的逐字节镜像）
- **账本规则**：加载 `skills-inventory` skill 查看完整规则

---

## 结构

| 路径 | 内容 |
|---|---|
| `skills/` | **全部 skill 的完整内容** —— `$DSH_HOME/skills` 的镜像（逐文件 SHA256 一致） |
| `SKILLS.md` | **账本**：装过什么、优先级（P0/P1/P2）、来源、适配、记录日期。**只追加，绝不重写** |
| `INSTALL.md` | **安装说明**：手工版的完整步骤，按优先级排列，含 MCP 一节 |
| `plugins/` | DSH 插件**配方**（`RECIPE.md`：来源 + 安装命令 + 前置 + profile 片段 + 验证） |
| `config/` | **环境配置**：`AGENTS.md`（常驻规则）、`settings.yaml`、`cordis.patch.yml`（**MCP 挂载**）、`profile/`（插件依赖与 pnpm 配置） |
| `install.ps1` | **一键恢复脚本**：自动部分全做完，并打印必须人工完成的待办 |
| `CHANGELOG.md` | **变更说明**：每次改了什么、为什么、影响哪些文件 |
| `archive/` | 历史归档（如 `AGENTS.md` 的旧版本） |
| `snapshots/` | 旧按日 zip 快照 —— **已退休**，被 git 历史取代（`.gitignore` 中，不再新增） |

## `install.ps1` 做什么

```
前置检查（pwsh/git/node/pnpm/uv/dsh）
  → 备份现有配置到 $DSH_HOME\_restore_backup_<时间戳>
  → 恢复 skills/          → $DSH_HOME/skills/
  → 恢复 config/AGENTS.md → $DSH_HOME/AGENTS.md（常驻规则）
  → 恢复 settings.yaml    → $DSH_HOME/
  → 恢复 MCP + profile    → $DSH_HOME/profiles/<profile>/
  → 装 4 个第三方插件（dsh plugin add）
  → 打印待办清单
```

## 它做不到什么（**必须人工**，脚本末尾会列出来）

| 做不到 | 原因 | 怎么办 |
|---|---|---|
| 重建运行时（约 **2.7 GB**） | camoufox 引擎 2.3 GB、firerpa venv 160 MB、vmpfdebugger 165 MB、MCP 41 MB —— 无法进仓库 | 跑各 skill 的 `scripts\restore.ps1` 或照 `references\重建配方`，**部分需代理** |
| 填凭据 | `.credentials.yaml` 里 3 个 API key，**永不进仓库** | 手工填 |
| 登录态 | camoufox 的 `states/` `profiles/`，**永不进仓库** | 手工登录 |
| JADX-GUI 及其插件 | 外部工具，不属本仓库范围 | 自行安装并保持开启 |
| 改硬编码路径 | `cordis.patch.yml` 里的 `D:\AI_python\...`、`AGENTS.md` 里的账本路径、`settings.yaml` 里的 provider | 按新环境改 |
| **重启 DSH** | 插件与 MCP 在启动时组合，不重启不生效 | 重启 |

## 本仓库不包含什么

凭据（token / API key / 登录态）、`node_modules`、`.venv`、浏览器引擎等大体积运行时、
插件源码与构建产物 —— 全部有来源可重装，或属于永不可备份的敏感数据。

## 怎么维护

**每次本地有变更后**，在 `D:\AI_python\skills_backup` 里：

```powershell
$L = 'D:\AI_python\skills_backup'; $D = "$env:USERPROFILE\.dsh"

# ① 同步 skill 内容
robocopy "$D\skills" "$L\skills" /E /XD __pycache__ .git node_modules .venv /XF *.pyc /NFL /NDL /NJH /NJS /NP

# ② 同步环境配置
Copy-Item "$D\AGENTS.md"                        "$L\config\AGENTS.md" -Force
Copy-Item "$D\settings.yaml"                    "$L\config\settings.yaml" -Force
Copy-Item "$D\profiles\web\cordis.patch.yml"    "$L\config\cordis.patch.yml" -Force
Copy-Item "$D\profiles\web\package.json"        "$L\config\profile\package.json" -Force
Copy-Item "$D\profiles\web\pnpm-workspace.yaml" "$L\config\profile\pnpm-workspace.yaml" -Force
Copy-Item "$D\profiles\web\cordis.yml"          "$L\config\profile\cordis.yml" -Force

# ③ 更新 SKILLS.md（追加日志）与 CHANGELOG.md（追加变更说明）

# ④ 提交推送
git add -A; git commit -m "<类型>: <一句话说明>"; git push
```

**提交信息约定**：`install:` / `update:` / `remove:` / `rule:` / `config:` + 一句话。

**回退**：`git log --oneline` 找到目标提交 → `git revert <commit>`（保留历史）
或 `git checkout <commit> -- <路径>`（只回退某文件）。
这比原来的 zip 快照强：能 diff、能定位是哪次改动引入的问题、能单文件回退。
