---
name: dev-hygiene
description: 开发规则与卫生规范（本机常驻红线）。删除一律走 Windows 回收站，禁止 del/rmdir/rd/Remove-Item/rm -rf/os.remove/shutil.rmtree 硬删；所有 shell 一律 pwsh 7，脚本含中文必须 UTF-8 with BOM；Python 一律用 uv 建项目内环境、默认清华源、永不使用 anaconda 装包；每个开发阶段收尾清理无用文件；每个项目产出 HANDOVER.md 交接文档，更新前先备份可回退。触发：删除、回收站、硬删、清理无用文件、pwsh、powershell、shell、uv、清华源、虚拟环境、.venv、交接文档、handover、重现、重建。
---

# dev-hygiene —— 开发规则与卫生规范

本机（Windows + pwsh 7）做任何开发时的五条硬规则。细则是唯一权威，`AGENTS.md` 里那 5 行只是常驻指针。

## 什么时候必须遵守

- 要删任何文件 / 目录（包括"顺手清理"）；
- 要执行命令、写 shell 脚本；
- 要建 Python 环境、装依赖、跑脚本；
- 每个开发阶段收尾、项目交付前；
- 要写或更新交接文档。

## 规则 1 —— 删除一律走回收站

### 唯一实现

`<本 skill>\scripts\Remove-ToRecycleBin.ps1`（多路径、通配、目录、`-WhatIf` 预演、失败**抛异常绝不降级**）。

```powershell
$del = "$env:USERPROFILE\.dsh\skills\dev-hygiene\scripts\Remove-ToRecycleBin.ps1"

# 外部调用：多路径用位置参数（PowerShell 不允许重复 -Path，逗号数组也传不进去）
pwsh -File $del '.\tmp' '.\a.txt' -WhatIf
# 真删（进回收站）
pwsh -File $del '.\__pycache__'
# 会话内直接调用：可以用 -Path 数组
& $del -Path '.\tmp', '.\a.txt' -WhatIf
```

没有脚本时的内联等价写法（第三个参数写错 = 永久删除，务必照抄）：

```powershell
Add-Type -AssemblyName Microsoft.VisualBasic
[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($p,      'OnlyErrorDialogs', 'SendToRecycleBin')
[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($p, 'OnlyErrorDialogs', 'SendToRecycleBin')
```

### 禁止清单（一律不用）

`del`、`rd`、`rmdir`、`Remove-Item`（/`ri`/`rm` 别名）、`rm -rf`、`shutil.rmtree`、`os.remove`、`os.unlink`、`pathlib.Path.unlink`、`[System.IO.File]::Delete`、`git clean -fdx`。

### 项目里怎么删：自包含，不引用本 skill 的绝对路径

需要删除逻辑的项目，把这两个模板复制进项目 `tools\`：

| 模板 | 用途 |
|---|---|
| `scripts\Remove-ToRecycleBin.ps1` | 唯一实现，pwsh 侧直接调 |
| `scripts\recycle.py` | Python 侧封装，转调同目录的 ps1（`from tools.recycle import recycle`） |

项目换机器后必须还能用，所以**任何迁移物都不得引用 `C:\Users\...\.dsh\skills\...` 这类本机绝对路径**；在 `HANDOVER.md` 里注明"删除逻辑来自 dev-hygiene，模板路径 X"。

### 硬删豁免白名单（只有两类，其余一律回收站）

1. **可重建的大体积产物**：`<项目>\.venv`、uv 缓存、`node_modules`、构建中间物。
   **前置条件（全部满足才可硬删）**：`pyproject.toml` + `uv.lock` + `.python-version` 齐全，且 `HANDOVER.md` 里的重建命令**已实测跑通过一次**（不是"理论上能"）。**删前先问用户一次**。
   理由：回收站不释放磁盘（只是移到同分区 `$Recycle.Bin`），几 GB 的 `.venv` 放回收站等于没省空间。
2. **`%TEMP%` 下本次会话自己刚创建的临时文件。**

以下情况**先列清单问用户**，不要自作主张：`git clean`、构建/包管理器自带的清理（`uv cache clean` 等）、项目目录之外的任何东西、以及任何你不确定的东西。

### 永久保留（清理时绝不碰）

`pyproject.toml`、`uv.lock`、`.python-version`、`HANDOVER.md`、`tools\`、源码、数据成果、分析报告、有证据价值的 `debug\` 脚本。
凭据与登录态（`state*.json`、`profiles\`）归用户：不删、不备份、不外传。

## 规则 2 —— 所有 shell 一律 pwsh

- 只用 **pwsh 7**（`pwsh`）；禁止 `powershell.exe`（5.1）、`cmd /c`、Git Bash、WSL 执行任何命令。
- 生成的脚本一律 `.ps1`；**含中文必须存成 UTF-8 with BOM**（无 BOM 时 Windows PowerShell 会按 ANSI 解析，中文脚本报 `Missing closing '}'` —— 本机踩过）。
- 给新环境的脚本加 `#Requires -Version 7.0`，让 5.1 直接拒绝运行而不是跑出奇怪结果。
- Linux 部署脚本 `.sh` **可以正常开发**，但**本机不得以任何方式执行**（包括 `wsl bash`、Git Bash）；文件头标注"仅 Linux 用，本机不执行"。

## 规则 3 —— Python 一律 uv，默认清华源

- 全局配置：`C:\Users\y\AppData\Roaming\uv\uv.toml`（本机已建，内容见 `references\uv-清华源.md`）：
  清华 index + `python-preference = "only-managed"`。**顶层键必须写在 `[[index]]` 之前**，写后面会静默失效。
- **只用 uv 托管的 CPython**（本机 `cpython-3.12.13`，装在 `%APPDATA%\uv\python`；本机已有 3.10.21 / 3.11.16 / 3.12.13 / 3.13.14）。新环境先
  `uv python install 3.12` 再 `uv sync`；uv 的 stderr 应显示 `Using CPython <版本>`（2026-09-30 起 anaconda 已整机移除，不会再出现下面那行路径）
  ~~`D:\ProgramsDev\anaconda3\python.exe`~~（该路径已不存在）。下载不通（GitHub 受限）时临时把那行改回 `managed`，
  并在该项目 `HANDOVER.md` 里写明原因。
- **每个项目内也写一份**同样的 index 配置（`pyproject.toml` 或项目根 `uv.toml`），保证换机器 clone 下来零配置就快。
- 新项目标准流程：
  ```powershell
  uv init <项目名>; cd <项目名>
  uv python pin 3.12          # 版本按项目需要定
  # 删掉 uv init 生成的示例代码（hello.py / main.py 与示例 main 函数），只留 pyproject.toml
  uv add <依赖>               # 走清华源
  uv run <脚本>               # 一律用 uv run 跑，不要手动 activate
  ```
- **禁止**：`pip install` 装到全局；`uv pip install --system`；依赖 PATH 上的裸 `python`（本机只剩 WindowsApps 的 0 字节 Store 存根，不可用）。uv 本体 = `C:\Users\y\.local\bin\uv.exe`（独立安装，不依赖任何 python 发行版）。**anaconda 已于 2026-09-30 整机卸载**（base + pkgs 缓存 + 注册表 + shell hook + 开始菜单全清），旧的「不得用 anaconda 装包」红线已无对象，留此条以记历史。
- `uv.lock` **必须留在项目里**（可重现的前提）。`uv sync` 是重建环境的唯一标准命令。
- 细节、配置片段与实测记录：`references\uv-清华源.md`；Python 打印中文乱码的坑见文末「本机已知坑」。

## 规则 4 —— 每阶段收尾清理

**时机**：每个开发阶段结束 + 项目交付前各一次。**范围**：只在本项目目录内。

- **自动删（走回收站）**：`__pycache__`、`*.pyc`、`.pytest_cache`、`.mypy_cache`、`.ruff_cache`、临时下载文件、一次性探测脚本、失败实验的中间产物、重复的数据副本。
- **先问再删**：看起来像成果但可能没用的（半成品脚本、中间数据）、项目目录外的、体积大的。
- **绝不删**：见规则 1「永久保留」。
- 删完**报告清单 + 释放的空间**；回收站删除请注明"可还原"。

## 规则 5 —— 每个项目都要 `HANDOVER.md`

**位置**：项目根 `HANDOVER.md`，中文内容（命令、标识符、路径保持原文）。模板：`templates\HANDOVER.md`。

**必备字段**：用途一句话 / 环境（OS、pwsh、uv、Python 版本、清华源配置）/ **从零重建**（逐条可复制命令，含 `uv sync`）/ 运行与验证（命令 + 期望输出）/ 目录结构 / 数据与凭据来源（只写"从哪取"，**绝不写值**）/ 已知坑与限制 / 变更记录（日期 + 改了什么 + 为什么）/ 回退方式 / 不确定与待办。

**更新流程（先备份再更新）**：

```powershell
# 1) 先把旧版备份成带日期的历史副本
$h = 'HANDOVER.md'; $d = "docs\handover-history"
New-Item -ItemType Directory -Force -Path $d | Out-Null
Copy-Item $h (Join-Path $d ("HANDOVER-{0:yyyy-MM-dd}.md" -f (Get-Date)))
# 2) 再改 \(h，并在「变更记录」追加一行
```

有 git 的项目，更新完建议提交一次（回退就用 `git log` / `git checkout`）；没有 git 时，`docs\handover-history\` 就是回退手段。

**阈值**：凡产出可复用产物（脚本、数据、项目）都写；纯一次性查询、<30 行的试验脚本可在 `README.md` 里放三行版（做什么 / 怎么跑 / 依赖什么），不单开文件。

## 规则 6 —— Git 提交红线（2026-10-27 实测踩过，多会话环境尤其致命）

- **提交一律显式列路径**：`git add <路径1> <路径2> ...`。**禁用 `git add -A` / `git add .` / `git commit -a`**。
  ★ 本机的账本仓库（`D:\AI_python\skills_backup`）和默认工作区可能**同时有别的会话在改**；`-A` 会把
  你从没打开过的、别人未提交的改动一起吞进你的提交，提交信息还写着你的活儿。
  **实测**：2026-10-27 我 `git add -A` 把另一会话未提交的 `plugins\dsh-skillhub\RECIPE.md` 与
  `INSTALL.md` / `SKILLS.md` 追加（共 302 行）带进了 `5817940`，对方随后只能把剩余文件另提一条。
- **提交前逐文件确认归属**：`git status --porcelain` 过一遍，问自己"这个文件我这次动过吗"。
  不认识/没动过的改动 → **不 add、不覆盖、不回滚**，大概率是并发会话的 WIP。
- **不重写已推送的历史**：`git reset --hard`、`git commit --amend`、`git push --force` 在共享仓库里会
  打断正基于同一 HEAD 工作的会话/人。**误带了别人的文件 → 补一条说明性提交或让属主自己记一笔，不回滚**
  （2026-10-27 就按这条处理：保留 `5817940`，对方 `40a396d` 在其上正常提交，双方内容都在）。
- **提交前看 `git diff --numstat`**：某文件行数异常巨大（几乎整文件重写）**先怀疑行尾符或编码变了**，
  不是内容变了。`.gitattributes` 写成 `* -text` 的仓库（本机账本就是）**逐字节存储**，CRLF↔LF 会让每一行
  都算改动；`git diff --ignore-cr-at-eol` 一眼识别。
  ★ **实测**：用 `[IO.File]::WriteAllLines` 重写 CHANGELOG 后 `--numstat` 显示 `2376 行`变更，实际只新增 46 行
  —— 原因是 WriteAllLines 固定写 CRLF 而仓库里是 LF。**改写文件要保留原行尾**（用 `edit` 工具，
  或读成 byte/string 后按原样写回）。
- **升级上游代码不碰脏工作树**：先 `git status` 记下本地已改/未跟踪文件 → 能用 `git merge --ff-only`
  就**不要** `git stash` / `git checkout -f` → 升级后立刻复查那几个文件仍在。
  ★ **判断"上游有没有新版"要看 commit，不能看 `VERSION` 文件**：上游可能进了几十个 commit 都没发版
  （2026-10-27 实测 39 个 commit、`VERSION` 仍是 1.0.1）。用
  `git rev-list --left-right --count HEAD...origin/main`，或 `git log --oneline HEAD..origin/main`。
- **push 前后都验证**：`git remote -v` 确认推的是哪个仓库；push 后 `git status -sb` 必须显示
  `## main...origin/main`（**没有** ahead/behind），`git log --oneline -1` 与远端一致。
  本机直连 GitHub 常 `Recv failure: Connection was reset`，走全局代理（已配 `http(s).proxy = 127.0.0.1:7890`）。
- **并发下同步远端用 `merge` 不用 `pull --rebase`**：工作树有别人的未提交改动时 `pull --rebase` 会直接拒绝
  （"cannot pull with rebase: You have unstaged changes"），`git merge` 允许脏工作树，只要不冲突就合并。

## 收尾清单（每次开发结束照做）

- [ ] 垃圾文件已清（走回收站）并报告清单与空间
- [ ] `HANDOVER.md` 已更新，且**曾先备份旧版**到 `docs\handover-history\`
- [ ] 提交**显式列路径**（未用 `add -A`），`numstat` 无异常整文件级变更，push 后 `git status -sb` 无 ahead/behind
- [ ] `.venv` 若已无用：确认 `uv.lock` + 重建命令已实测 → 问用户 → 硬删（豁免条款）
- [ ] 本次没有任何非豁免文件被硬删
- [ ] 项目内没有引用本机 skill 绝对路径
- [ ] Linux 脚本只写没跑

## 本机已知坑（都实测踩过，2026-09-15）

| 现象 | 真因 | 处理 |
|---|---|---|
| Python 脚本 print 的中文在终端里乱码 | Windows 下 Python 的 stdout 默认 cp936，而日志按 UTF-8 读。**与 pwsh、与删除逻辑无关**：pwsh 输出本来就是 UTF-8 字节（已验证 `中文` → `e4 b8 ad e6 96 87`） | 入口脚本开头 `sys.stdout.reconfigure(encoding="utf-8")`，或运行前设 `$env:PYTHONUTF8='1'` |
| `pwsh -File x.ps1 -Path a, b` 报"找不到接受自变量的位置参数" | 经 `-File` 外部调用时逗号数组会整体变成字符串 `"a,b"` | 多路径用位置参数 `pwsh -File x.ps1 a b` |
| `pwsh -File x.ps1 -Path a -Path b` 报"多次指定了参数 'Path'" | PowerShell 不允许重复指定同一个命名参数 | 同上；只有会话内 `& x.ps1 -Path a, b` 能用数组 |
| 命令明明有输出，副作用（生成的文件、退出码）却像没发生 | 管道里用了 `Select-Object -First N`：取够对象后**提前掐断管道并终止上游进程**（`uv add`、`pwsh` 都会被中途杀掉，`$LASTEXITCODE` 也随之不可信） | 测副作用时先 `$out = cmd 2>&1; $code = $LASTEXITCODE`，再对 `$out` 做截取 |
| 含中文的 `.ps1` 被 Windows PowerShell 5.1 跑时报 `Missing closing '}'` | 无 BOM 时按 ANSI(GBK) 解析中文 | 存成 **UTF-8 with BOM**；脚本加 `#Requires -Version 7.0` 让 5.1 直接拒跑 |

## 与其它 skill 的关系

- **项目命名 / 位置 / 工作区结构**以 `camoufox-reverse` 为准（目标网站域名规范化、建目录前问用户）；**删除、清理、uv、交接文档**按本 skill。
- 本 skill 自身被修改时，按 `skills-inventory` 的流程重新整份复制到账本的 `skills\dev-hygiene\` 并追加账本日志。

## 边界

无网络、无第三方依赖、不改系统设置（唯一的用户级改动是 `%APPDATA%\uv\uv.toml` 与 `AGENTS.md` 红线）。
拿不准的一律先问用户：删什么、放哪、留不留。
