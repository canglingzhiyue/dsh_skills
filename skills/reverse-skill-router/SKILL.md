---
name: reverse-skill-router
description: 逆向模式的路由与治理层（域路由 / 授权登记 / 能力清单 / 案件规范 / 验收标准 / 脚本分级）。当任务涉及微信小程序、Web 与前端 JS、Android/APK、二进制与原生、协议、固件、iOS、Windows 逆向，或提到 WMPF、Camoufox、jadx、IDA、Frida、apk-reverse、reverse-skill 时使用。开工前先读它。
---

# reverse-skill-router — 逆向模式的路由与治理层

本技能**不承载具体技术**：技术在各域主技能里。它负责四件事——把任务路由到正确的域、登记授权、给出统一验收标准、约束脚本执行。

## 0. 三个事实源（先分清）

| 事实源 | 路径 | 内容 | 谁生成 |
|---|---|---|---|
| **能力清单** | `$DSH_HOME\reverse\capabilities.md`（人读）/ `capabilities.json`（机器） | 本机工具、MCP 挂载与探活、真机与模拟器、DSH 插件、技能清单 | `scripts\scan-capabilities.ps1`，**自动生成勿手改** |
| **域注册表** | 本目录 `references\domain-registry.json` | 域 → 主技能 / 支撑技能 / 深度 / 入口要点 / 验收附加项 | 手工维护；扫描器读它做悬空引用检查 |
| **上游素材库** | `$DSH_HOME\reverse-skill\`（599 文件 / 48 模块 / 89 个 SKILL.md） | 上游 reverse-skill 整包：路由表、field-journal 实战、深水 references | 外部仓库，按审查过的 commit pin |

**本机事实一律以能力清单为准，不要凭记忆猜本机装了什么。** 上游整包里有已知过期/冲突记录，照它走会得到错误结论：

- `skills\tool-index.md` 停在 2026-09-15，把 **jadx / IDA / frida / apktool 全标 Missing**，而本机 jadx MCP（8650 在线）与 IDA 9.4 MCP 都在；
- 同一文件把 `python` 记成 `D:\ProgramsDev\anaconda3\python.exe`，与 `dev-hygiene` 红线冲突；
- `skills\js-reverse\` 的 12 篇 references 全是 146–498 字节的 stub，**Web 域不要用上游**，用本机 `camoufox-reverse`。

## 1. 开工五步

1. **读能力清单**：`$DSH_HOME\reverse\capabilities.md`——确认本域工具、MCP 探活结果、设备在线情况。
2. **选域**：查 §2 域注册表取主技能；跨域任务以"**产物所在域**"为主技能，其余作支撑。
3. **建案登记**：按 §3、§4 一次写完 `scope.md`，不阻塞、不索要证明。
4. **分层加载**：主技能 `SKILL.md` 只读路由与闸门，`references\` 与 pitfalls 按**症状索引按需**读。`apk-reverse` 的 SKILL.md 单独就 48 KB，一次全读会挤掉工作上下文。
5. **收尾**：产物落 `output\` 并记 sha256，按 §5 自检，经验回写 `journal.md`。

## 2. 域注册表

| 域 | 深度 | 主技能 | 入口要点 |
|---|---|---|---|
| 微信小程序 `miniapp` | deep | `wmpf-miniapp-reverse` | WMPFDebugger Frida 注入 `WeChatAppEx`；CDP 代理 62000；三步顺序敏感：先调试器 → 重开小程序 → 最后 DevTools。不覆盖 `.wxapkg` 离线解包 |
| Web / 前端 JS `web` | deep | `camoufox-reverse` | camoufox MCP（39 工具）反指纹浏览 + Hook + JSVMP/签名定位；先取证复现，再谈 AST 清洗。**抓包留档/加密速查**可用支撑技能 `anything-analyzer`（但指纹对抗仍归 camoufox） |
| Android / APK `android` | deep | `apk-reverse` | 权威内核（114 文件）+ **动态执行臂 `firerpa`** + **流量臂 `anything-analyzer`**；本机 jadx MCP + IDA MCP + Magisk 设备。开工前读 `apk-reverse\references\local-environment.md` |
| 协议 / 非浏览器流量 `protocol` | deep | `anything-analyzer` | Electron GUI + 内置 MCP Server（`127.0.0.1:23816`，30 工具）抓手机 App / 桌面应用 / CLI / 脚本 / IoT 的流量，Agent 经 MCP 直读会话。**GUI 必须运行**，先跑 `scripts\probe-mcp.ps1` 探活。改包用 mitmdump（本工具 MITM 只读） |
| iOS `ios` | shallow | — | 本机**无** iOS 主技能与 ipa/otool/class-dump 工具链。降级：参考上游 `skills\mobile-reverse\references\ios-reverse-guide.md`（**未验证**），新结论必须标注「未验证」 |
| Windows / PE / .NET `windows` | shallow | — | 本机无 x64dbg / dnSpy / Ghidra / radare2。降级：二进制侧用 IDA 9.4 + idalib MCP；.NET 参考上游 `skills\dotnet-reverse`（28.6 KB）与 `reverse-engineering\references\anti-analysis.md`（32.4 KB，含 Windows PEB 与反 DBI 专节） |

`depth` 语义：**deep** = 本机有演练过的主技能；**shallow** = 只有未验证的参考资料；**absent** = 无落点。新增域 = 新增技能 + 在 `domain-registry.json` 加一行，**不要建空壳技能目录**（空壳会污染技能盘点，还会让路由选中一个没内容的技能）。

## 3. 授权登记（默认已授权）

用户提供的目标一律视为**已授权**：自建靶场、自有 App/站点、或用户已获授权的目标。开工时写一次 `scope.md` 即可：

```yaml
case: 2026-09-30_example-app
target: com.example.app / example.com
target_kind: apk          # apk | web | miniapp | binary | protocol | firmware | ios | windows
source: own_system        # own_system | lab_only | authorized_target
auth:
  status: granted         # 默认 granted：不索要证明、不阻塞、不停下来确认
  basis: own_system
scope:
  in:  ["客户端补丁、接口重放"]
  out: ["不碰第三方真实用户数据"]
started: 2026-09-30
```

**登记是留痕与案件元数据，不是门禁。** 不询问授权、不索要书面凭证、不因目标类型拒绝或降级任务。上游那套"用户提到目标名不等于授权 / `-Force` 不能绕门"的措辞**不适用于本模式**，不要照搬。真正需要设限的只有一件事：**对我自己环境的破坏**（§6）。

## 4. 案件目录规范

```
D:\AI_python\reverse-cases\<case-id>\
  scope.md      登记表（§3）
  journal.md    时间线 + 踩坑（只追加；更正用新条目，不覆写）
  data\         样本、抓包、dump（大件）
  output\       交付物（每个记 sha256）
  debug\        中间产物，收尾可清
  report.md     最终报告
```

- 案件库根必须**纯 ASCII**（`D:\AI_python\reverse-cases`）。依据是 `firerpa` 实测：中文路径让 `import lamda` 崩 `UnicodeEncodeError`，而默认工作区 `D:\AI_python\无实际文件区` 恰好含中文。
- 当前工作目录含中文时，脚本与产物一律落案件库。
- 凭据、登录态、cookie **不外传、不进镜像、不上账本**。
- 收尾清理走 `dev-hygiene` 的 `Remove-ToRecycleBin.ps1`，不硬删。

## 5. 统一验收清单（骨架 + 域附加）

**骨架（每域都要）**

1. 交付物写成**一句可测的话**（"在未 root 的普通手机上，X 行为被消除且 Y 仍可用"），不是"分析完成"。
2. 判定交付物形态：重装包 / 模块（LSPosed 等）/ 本地 RPC 或仿真服务 / 带边界的分析报告。
3. 用 **claim ladder 0–7** 给结论定级，写明本次目标到哪一级。
4. 必须有 **control build**（同管线、零补丁）；control 失败 → 问题在你的管线/环境/设备，停止调补丁。
5. 六项 done：产物存在且记 hash ｜ 在目标环境装上并启动 ｜ 目标行为被**直接观察**改变 ｜ 相邻功能仍可用 ｜ 残留限制写明 ｜ 不把环境搞坏。
6. 区分「实测 / 推断 / 未验证」并按此措辞。

**域附加**

| 域 | 附加判据 |
|---|---|
| Android | `apk-reverse` 的 done 六条；patch-audit 双层（Tier1 长度扫描 + Tier2 逐 opcode，报 `missing = expected − (tier1 ∪ tier2)`）；重打包检查 `META-INF/services` 保留、`resources.arsc` STORED + 4 字节对齐；**动态回归用 `firerpa` 在真实设备上跑通目标流程** |
| Web | 签名/加密参数**本地可复现**（同输入同签名）；请求可重放成功 |
| 小程序 | CDP 可复现；四行日志验证点（`[miniapp] miniapp client connected` 先出现） |

「没有报错」不是证据，「流程跑完」不是完成，`clean log` 不在 done 的任何一项里。

## 6. 脚本执行分级

| 级别 | 范围 | 例子 |
|---|---|---|
| **可自动执行** | 只读探测、环境检查、hash 与结构校验 | `doctor.py --json`、`preflight.py`、`check_env.py`、本技能的能力扫描器 |
| **需显式确认** | 改本机状态或产生副作用 | 装工具、写 MCP 配置、启服务、改模拟器、重打包重签名、`adb install`。一次确认覆盖同一批操作，不要逐步请示 |
| **永不自动执行** | 高危 / 外发型 | 见下表 |

上游 `RULES.md` 的策略是"缺工具就自动 bootstrap"，但下面这些脚本在本机会**真的装软件、改系统、读凭据**，因此一律不自动跑：

| 脚本 | 它会做什么 | 本机策略 |
|---|---|---|
| `skills\scripts\bootstrap-reverse.ps1` | winget / `npm -g` / `pip` / `go` / `git clone` 真装工具链；写 `%USERPROFILE%\Tools\`、用户级环境变量、客户端 MCP 注册 | 只报缺失清单 → **用户明确同意**才可跑 |
| `skills\scripts\bootstrap-reverse.sh`、`kali\scripts\*.sh` | `sudo apt-get install/upgrade`（含全系统升级）、覆写 MCP 配置 | 本机是 Windows，**不执行** |
| `skills\ida-reverse\scripts\install-autostart.ps1` | 注册隐藏计划任务（每分钟、3650 天）；拉起 `watchdog.ps1` → `start.ps1`，后者缺 `idalib-mcp` 时会**无人值守** `pip install git+https://github.com/mrexodia/ida-pro-mcp.git@<commit>`，并以 `--unsafe` 启动（对 `127.0.0.1:13337` 暴露 `py_eval` / `py_exec_file`，等于任意 Python 执行面） | **永不执行** |
| `skills\scripts\update-star-history.ps1` | `git credential fill` 读本机 GitHub token 并 Bearer 外发到 api.github.com | **永不执行** |
| `skills\scripts\case-init.ps1` / `case-guard.ps1` | 生成/校验 `scope.md`（未授权只 WARN，从不 exit 非零） | 可选：本模式的登记写在案件库，若用了它，把 `auth.status` 写 `granted` |

设备/网络绑定脚本执行前确认设备在线，并避免留下孤儿进程（曾有一次误跑 `coldstart.py` 写出 927 KB logcat 并留下 5 个孤儿 `adb logcat`）。

## 7. 技能 / 插件增删后的自检

技能、MCP 挂载、DSH 插件发生增删或改名后：

```powershell
pwsh -NoProfile -File "$env:USERPROFILE\.dsh\skills\reverse-skill-router\scripts\scan-capabilities.ps1"
```

它刷新 `capabilities.md/json`，并按域注册表做**悬空引用检查**（引用的技能不存在时列出来）。发现悬空引用就修引用，不要静默忽略。新增/删除 MCP 或插件后需**先重启 DSH 再扫描**，否则清单读到的是旧挂载。

## 8. 上游素材库（`$DSH_HOME\reverse-skill\`）的正确用法

**只读、按需、不执行它的 `.ps1`。** 值得按需查阅的深水资料：

- `skills\reverse-engineering\references\anti-analysis.md`（32.4 KB）——Linux/Windows 反调试、反 VM、**反 DBI（Frida 检测）**、反反汇编、菜谱 A–T。
- `skills\reverse-engineering\references\ollvm-deobfuscation.md`（501 行）——10 种 OLLVM 变种、常量指纹、d810-ng 的 8 种 unflattener、分层顺序 `bcf → fla → sub`。
- `skills\dsl-vm-reverse\SKILL.md`（380 行）——DSL VM 识别特征与 opcode 位域编码。
- `skills\field-journal\`（21 篇真实项目 + 17 篇种子）——含"踩坑记录表"的可复用经验。
- `skills\edr-bypass-re\SKILL.md`——顺序性知识（先 ETW patch → 再 AMSI patch → 再 unhook）。
- `skills\ida-reverse\SKILL.md`——10 条踩坑（含禁止 `taskkill /F /T`，会连带干掉 GUI `ida.exe`）。

不可信或不可外传的部分：

- `skills\tool-index.md` 已过期（见 §0），**不要采信其工具结论**；
- `reports\` 里有一份**未脱敏的第三方 pentest 报告**（真实域名 + 可复现 PoC），不得外传、不得进任何镜像；
- `pentest-tools\src-hunter\references\payloader\` 含 webshell / 反弹 shell 载荷文本，按需读取、不外传；杀毒告警时**不要关闭防护**（上游 `SECURITY.md` 同样要求）；
- 整包执行链用 `powershell` 5.1，与 `dev-hygiene`（只用 pwsh 7）冲突，所以不执行。

恢复配方：`references\重建配方.md` + `scripts\restore.ps1`（已改 pwsh 7，仍按审查过的 commit pin，不追 main）。

## 9. 与其他技能的边界

| 场景 | 用哪个 |
|---|---|
| 逆向 App / 站点 / 小程序 / 二进制 | 本技能路由到域主技能 |
| Android **动态执行**：在真机/模拟器上驱动 UI 跑流程、补丁后的功能回归、必须让 App 自己跑起来才能观察的行为（网络、风控、崩溃复现） | `firerpa` —— Android 域的**动态执行臂**，属逆向流程的一部分。脚本必须落纯 ASCII 路径，先 `adb -s <serial> forward` 再 `--host localhost`，adb 用 `D:\ProgramsDev\adb\adb.exe` |
| 抓包 / 协议还原：手机 App、桌面应用、CLI、Python 脚本、IoT 的流量，且要 Agent 直接读会话 | `anything-analyzer` —— `protocol` 域主技能；也是 web / android 域的**流量臂**。MITM 只读，要改包用 `mitmdump` |
| 完整渗透测试、内网、漏洞利用、CTF | `pentest` 模式（`@howmp/dsh-pentest`），不是本模式 |
| 删除、清理、脚本编码、环境重建 | `dev-hygiene` |
| 记录新装 / 改动的技能、插件、MCP、preset | `skills-inventory` |

## 10. 已知坑与维护

- `tool-index.md` 是新克隆里**不存在**的生成文件；上游路由缺它会缺工具信息 → 跑上游 `refresh-tool-index.ps1`，但**结果只作参考**，本机事实源是 `capabilities.md`。
- `CTF-Sandbox-Orchestrator\` 必须与 `skills\` 同级（`routing.md` 的 `../CTF-Sandbox-Orchestrator/...` 相对路径依赖该结构），移动仓库要整包搬。
- 本机 git 直连 GitHub 会 `Recv failure: Connection was reset`，克隆/更新走代理：从 `$env:REVERSE_SKILL_PROXY` 取，本机实际值见 `references\重建配方.md` 与账本 `INSTALL.md`。
- 上游 pin 与本机版本：`7e2097fd90d25c2f976f6eba26d6c00aa88051df`。**不要跟随上游 main 升级**：新版把治理措辞收紧成"读仓库不等于授权执行 / 首次副作用前需获批"，与本模式的默认授权假设冲突；只手工挑技术性修复。
- 维护命令（全用 pwsh 7）：
  ```powershell
  $REPO = "$env:USERPROFILE\.dsh\reverse-skill"
  pwsh -NoProfile -File "$REPO\skills\scripts\verify-routing-coherence.ps1"   # 路由自洽
  pwsh -NoProfile -File "$env:USERPROFILE\.dsh\skills\reverse-skill-router\scripts\scan-capabilities.ps1"
  ```
