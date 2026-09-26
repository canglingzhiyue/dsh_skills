---
name: reverse-skill-router
description: 本机已装好的 reverse-skill 安全技能路由包（逆向工程 / 渗透测试 / CTF / 恶意样本 / 移动与固件 / 前端 JS 逆向 / 安全报告）。当任务涉及 APK、二进制、反编译、IDA / radare2 / Ghidra / Binary Ninja、Frida Hook、前端签名与加密参数、抓包重放、CTF、漏洞利用、提权、内网渗透、EDR 免杀、固件、恶意软件分析、安全报告或 writeup 时使用。按包内 RULES.md 路由到 PRIMARY 子技能，并强制执行 case-init 授权门禁。
---

# reverse-skill 路由包（本机已配置）

上游：<https://github.com/zhaoxuya520/reverse-skill> · 版本 **v1.0.1** · 许可 MIT。
仓库由 89 个 `SKILL.md` 组成（`skills/` 48 个模块 + `CTF-Sandbox-Orchestrator/` 42 个子技能），
**靠相对路径互相引用，必须整包使用，不要拆散或平铺**。

## 位置

| 东西 | 路径 |
|---|---|
| 包根（`<REPO>`） | `C:\Users\y\.dsh\reverse-skill` |
| 行为链唯一真相源 | `<REPO>\RULES.md` |
| 路由主入口 | `<REPO>\skills\SKILL.md`、`<REPO>\skills\MASTER-ROUTING.md` |
| 路由配置 SSoT | `<REPO>\skills\config\routing.json` |
| 工具清单（本机生成，gitignored） | `<REPO>\skills\tool-index.md` / `tool-index.json` |
| 案例产物 | 当前项目的 `work\<case>\`（`scope.md` / timeline / workitems） |
| 重建与更新配方 | `references\重建配方.md`（本 skill 目录内） |

## 硬规则（DSH 侧收敛）

1. **先授权，后动手。** 对任何目标执行动作前，必须先用 `case-init` 落地 `work\<case>\scope.md`
   且 `auth.status=granted` + 合法 `network_profile`（或显式的 `offline-sample` 授权样本）。
   **用户提到一个目标名不等于授权**；`-Force` / `--force` 永远不能绕过硬门。
2. **禁装 / 禁执行约束（红线，MUST NOT 自行执行）。** 上游 `RULES.md` 的策略是"缺工具就自动 bootstrap"，
   而下面这些脚本在本机会**真的装软件、改系统、读凭据**，因此一律先问用户，默认不跑：

   | 脚本 | 它会做什么 | 本机策略 |
   |---|---|---|
   | `skills\scripts\bootstrap-reverse.ps1` | winget / `npm -g` / `pip` / `go` / `git clone` 真装工具链；写 `%USERPROFILE%\Tools\`、用户级环境变量、Claude/Codex 的 MCP 注册 | 只报缺失清单 → **用户明确同意**才可跑 |
   | `skills\scripts\bootstrap-reverse.sh`、`kali\scripts\*.sh` | `sudo apt-get install/upgrade`（**含全系统升级**）、覆写 MCP 配置 | 本机是 Windows，**不执行** |
   | `skills\ida-reverse\scripts\install-autostart.ps1` | 注册隐藏计划任务（**每分钟**、3650 天、`Hidden`）；它拉起 `watchdog.ps1` → `start.ps1`，后者缺 `idalib-mcp` 时会**无人值守地** `pip install git+https://github.com/mrexodia/ida-pro-mcp.git@<commit>`，并以 `--unsafe` 启动（对 `127.0.0.1:13337` 暴露 `py_eval` / `py_exec_file`，等于任意 Python 执行面） | **永不执行**；确实需要 IDA MCP 常驻时，先照 `references\重建配方.md` 的两处硬化改 `start.ps1`（关掉 auto-bootstrap、去掉 `--unsafe`）再谈 |
   | `skills\scripts\update-star-history.ps1` | 用 `git credential fill` 读本机 GitHub token 并 Bearer 外发到 api.github.com | **永不执行** |

   报缺失清单时以 `<REPO>\skills\tool-index.md` 为准，并把将要执行的命令一并给用户看。
3. **工具路径只认 `tool-index.md`**，不要猜路径；新装了工具后重跑 `refresh-tool-index.ps1`。
4. **不要预加载整包。** 只读本次任务需要的那几个文件（RULES.md → PRIMARY SKILL.md → 相关
   `references/`），别把 89 个 SKILL.md 全读一遍。
5. 所有 `work\`、`reports\`、`skills\field-journal\` 产物属于本机数据，**不随账本备份**。

## 标准执行链（Windows）

```powershell
$REPO = 'C:\Users\y\.dsh\reverse-skill'

# 1) 定 PRIMARY（读 skills/config/routing.json）
powershell -NoProfile -ExecutionPolicy Bypass -File "$REPO\skills\scripts\master-route.ps1" -Hint "<用户任务原文>"

# 2) 授权门禁：落地当前项目的 work\<case>\scope.md
powershell -NoProfile -ExecutionPolicy Bypass -File "$REPO\skills\scripts\case-init.ps1" `
  -Hint "<任务>" -CaseName <case-name> -ProjectRoot "<当前项目目录>" `
  -Preset offline-sample -Sample "<样本路径>"          # 离线样本
# 或已获授权目标：
#   -AuthGranted -TargetUrl "https://.../" -NetworkProfile authorized_target_only
powershell -NoProfile -ExecutionPolicy Bypass -File "$REPO\skills\scripts\case-guard.ps1" -CaseRoot "<项目>\work\<case>"

# 3) 执行 PRIMARY：打开 "$REPO\skills\<PRIMARY>\SKILL.md"，照它的 ACTION REQUIRED 干活

# 4) 结论按 Evidence → Finding → Path 组织（"$REPO\skills\ops\evidence-finding-path.md"）
```

Linux / macOS / Kali 用对应的 `.sh`（`skills/scripts/master-route.sh`、`case-init.sh`、`case-guard.sh`；
Kali 另有 `kali/scripts/`）。当前会话是 Windows，默认走 PowerShell。

收尾（用户要交付物时）：`docs-generator` 出报告 → `diagram-generator` 至少一张流程图 →
case-review 自检 `python3 "$REPO/skills/case-review/scripts/review_case.py" work/<case> --verify-hashes --strict`
→ 匿名化写回 `skills/field-journal/`。

## 维护

```powershell
$REPO = 'C:\Users\y\.dsh\reverse-skill'
powershell -NoProfile -ExecutionPolicy Bypass -File "$REPO\skills\scripts\refresh-tool-index.ps1"   # 本机工具清单
powershell -NoProfile -ExecutionPolicy Bypass -File "$REPO\skills\scripts\verify-routing-coherence.ps1"  # 路由自洽
git -C $REPO pull --depth 1 --ff-only     # 更新（走代理，见 references\重建配方.md）
```

## 已知坑

- `tool-index.md` 是新克隆里**不存在**的生成文件；没有它路由会缺工具信息 → 先跑 `refresh-tool-index.ps1`。
- 用 `powershell -NoProfile -ExecutionPolicy Bypass -File` 调用，避免执行策略和 profile 干扰。
- 仓库源文件带 UTF-8 BOM，直接用 Windows PowerShell 5.1 读中文才不乱码。
- `CTF-Sandbox-Orchestrator\` 必须与 `skills\` 同级（`routing.md` 里的 `../CTF-Sandbox-Orchestrator/...`
  相对路径依赖这个结构），移动仓库时要整包搬。
- 本机 git 直连 GitHub 会 `Recv failure: Connection was reset`，克隆/更新要走代理：脚本从环境变量
  `REVERSE_SKILL_PROXY` 取（未设则直连）；本机实际代理值见本 skill 的 `references\重建配方.md`。
- **上游仓库本体是真实红队工具包**（含 webshell / 反弹 shell 载荷文本、EDR 规避与攻击链全文、
  一份未脱敏的第三方 pentest 报告）：只在**有明确授权**的目标上使用；`work\`、`reports\`、
  `skills\field-journal\` 里的第三方数据不要外传。若杀毒软件对载荷文本告警，**不要关闭防护**
  （上游 `SECURITY.md` 也是这么写的）。安全审查结论见账本 `skills_backup\INSTALL.md` 的本节。
