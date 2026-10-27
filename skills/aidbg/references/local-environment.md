# aidbg 本机环境与重建配方

本文件是 `aidbg` skill 的配套环境说明：**装在哪、怎么重建、怎么挂 MCP、怎么验、坑在哪**。
skill 正文只写怎么用；这里写怎么把它装回来。

## 1. 本机现状（实测 2026-10-26）

| 项 | 值 |
|---|---|
| 可执行文件 | `D:\AI_python\reverse\aidbg\aidbg.exe` |
| 版本 | `0.4.0`（`aidbg.exe --version` → `aidbg 0.4.0`） |
| 大小 | 1,715,200 B |
| SHA256 | `FCD5A086251CFA5B910851E136142C2F80AE66A043E6477003D7F7A7DBD28A6E` |
| 依赖 | 仅 `KERNEL32` / `dbghelp` / `ucrtbase` —— **零 VC 运行时依赖**，Win10+ 拷过去就能跑 |
| 上游 | <https://github.com/A-new/aidbg>（MIT 风格的公开仓库；见仓库 README 致谢与许可） |
| 构建工具链 | **本机没有 MSVC / CMake** → 不本地构建，只用 release 单文件 |

放在 `D:\AI_python\reverse\` 下是为了和本机其它逆向环境（`vmpfdebugger` 等）同目录族；
路径里**没有中文**，这是刻意的（本机中文路径坑见 `dev-hygiene`）。

## 2. 从零重建（新机器 / 重装）

只有两步，**不要 clone 整个仓库、不要编译**：

```powershell
# 1) 建目录并下载当前 release 的单文件 exe
$dir = 'D:\AI_python\reverse\aidbg'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Invoke-WebRequest -Uri 'https://github.com/A-new/aidbg/releases/latest/download/aidbg.exe' `
  -OutFile (Join-Path $dir 'aidbg.exe') -TimeoutSec 180

# 2) 校验并冒烟
(Get-FileHash (Join-Path $dir 'aidbg.exe') -Algorithm SHA256).Hash
& (Join-Path $dir 'aidbg.exe') --version        # 期望：aidbg <版本号>
```

- 本机 **2026-10-26 实测可直连下载**（不需要代理）。若换环境下载被 reset，走
  `$env:REVERSE_SKILL_PROXY` 里的代理。
- `latest/download/aidbg.exe` 每次取最新版；要复现本机这份就换成
  `releases/download/v0.4.0/aidbg.exe` 并核对上面的 SHA256。

**冒烟测试**（不需要自己的样本，用系统自带的 `whoami.exe`）：

```powershell
$aidbg = 'D:\AI_python\reverse\aidbg\aidbg.exe'
& $aidbg --json -c "file C:\Windows\System32\whoami.exe" -c "run" -c "regs rip rsp" -c "modules" -c "kill"
```

期望：至少 4 行 `"ok":true`；`run` 那行 `session.state` = `paused`、`stop_reason` = `entry`；
`modules` 里能看到 `whoami.exe` 与 `ntdll.dll`。中间夹一行
`{"kind":"event","event":"warning","text":"fixed base skipped for a system file..."}` 是正常的（见 §6）。

## 3. 更新到新版

同一套动作，覆盖即可（exe 单文件、无注册表、无安装器）：

```powershell
$exe = 'D:\AI_python\reverse\aidbg\aidbg.exe'
$old = (Get-FileHash $exe -Algorithm SHA256).Hash
Invoke-WebRequest 'https://github.com/A-new/aidbg/releases/latest/download/aidbg.exe' -OutFile $exe -TimeoutSec 180
& $exe --version
"old=$old new=$((Get-FileHash $exe -Algorithm SHA256).Hash)"
```

升级后**顺手做两件事**：① 上面那条冒烟测试重跑一遍；② 把本文件 §1 的版本 / 大小 / SHA256
改成新值（这三个数是"这一份"的指纹，不改就变成谎话）。上游 `skills/aidbg/SKILL.md` 若同时更新了
命令表，把它并进 `references\commands.md`（本机版保留了上游原文 + 「本机」补充行）。

## 4. MCP 挂载（本机已配：`reverse-mcp-activator`，逆向会话创建时按需启动）

`serverName: aidbg`，13 个工具（`aidbg_session` / `aidbg_execute` / `aidbg_breakpoint` /
`aidbg_registers` / `aidbg_memory` / `aidbg_disasm` / `aidbg_stack` / `aidbg_cfg` /
`aidbg_modules` / `aidbg_eval` / `aidbg_exceptions` / `aidbg_snapshot` / `aidbg_command`）。

**挂在哪**（⚠ 别挂错层，本机 2026-10-09 之后 MCP 不再写在 composition 里）：
`$DSH_HOME\profiles\web\cordis.patch.yml` 里自研插件行 `reverse-mcp-activator` 的
`config.servers` 数组末尾，条目形如：

```yaml
          # mcp-aidbg（Windows x86/x64 调试器，2026-10-26 新增）
          - serverName: aidbg
            transport: stdio
            command: 'D:\AI_python\reverse\aidbg\aidbg.exe'
            args:
              - '--mcp'
            toolCallTimeoutMs: 120000
            failOnStartupError: false
```

- **为什么是这个层，而不是 preset composition**：DSH 0.2.0 的 preset registry 在**启动期就
  急切挂载所有已声明 preset**，写在 composition 里的 `dsh-mcp-client` 行必然随 `dsh web` 拉起
  （本机实测 10 进程 / 约 300 MB、启动慢 9~13 秒）。`reverse-mcp-activator` 是 host 层的一行
  插件：启动只加载自身，监听 `agent/created`，**只有逆向模式会话创建时**才
  `ctx.plugin(McpClient, server)` 把服务器挂到该会话作用域 —— 进程随会话存亡，工具只对该会话可见。
  `presets\reverse\agent.cordis.yml` 里剩下的 MCP 行是 **2026-10-09 迁移遗留的历史参考副本、不生效**，
  别往那里加（加了不会报错，但也不会生效）。
- **`failOnStartupError: false`**：exe 被移走 / 被杀软隔离时**静默失效、不拦会话创建**。
  代价是"工具不在"不会报错 —— 所以用前先探活（§5）。
- **普通会话里没有** `mcp__aidbg__*`（只有逆向模式会话有）；不想开逆向会话就直接走 CLI
  （`SKILL.md` 的方式 A）。
- **`--mcp` 只起 JSON-RPC 服务、不自动开调试会话**：目标要在会话里用
  `aidbg_session(action="file"/"run")` 才起来。所以它空闲时几乎不占资源。
- **改完要重启 DSH 才稳**：本机该 profile 是 `patchReload: live`（patch 变更会热组合），
  但插件 config 变更是否重新 `apply()` 没实测 —— 别赌，重启一次再验证。

手工验证 stdio 握手（不依赖 DSH，直接问它）：

```powershell
$exe = 'D:\AI_python\reverse\aidbg\aidbg.exe'
@(
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}',
  '{"jsonrpc":"2.0","method":"notifications/initialized"}',
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
) | & $exe --mcp
```

期望：第一行 `serverInfo.name = "aidbg"`、`version = "0.4.0"`；第二行 `tools` 数组 **13 个**。
本机 2026-10-26 实测通过。

## 5. 装完怎么算成功（四条，都要过）

1. `aidbg.exe --version` 打印版本号；
2. §2 的 `whoami.exe` 冒烟：`run` 停在 `entry`、`modules` 有内容、退出码 0；
3. MCP 握手返回 13 个工具（§4 的探活命令）；
4. **新开一个「逆向模式」会话**，工具列表里出现 `mcp__aidbg__*`。
   （`preset_probe` 在现行 DSH 里不存在，别找它；能力扫描器查得到 activator 层的**挂载行**
   与工具 exe 的探活结果，但**查不到工具是否真在会话里可见** —— 只有真实会话能证明。）

CLI 路径（方式 A）不依赖 3、4 两条，**只要 1、2 过了就能干活**。

## 6. 已知坑（都实测过）

| 现象 | 真因 | 处理 |
|---|---|---|
| 输出里夹 `{"kind":"event","event":"debug_string","text":"...δָ���Ĵ���"}` 这种乱码 | 目标进程经 `OutputDebugString` 吐的**中文是 GBK**，aidbg 原样透传，不转码 | 当噪声过滤：只读 `"ok":true` 的行，或按 `"kind":"event"` 跳过。**不要**当错误去查 |
| 调试 `C:\Windows\System32\*` 时报 `fixed base skipped for a system file`，`slide` 非零 | 系统文件不允许改映像基址，退化成 ASLR | 正常事件。要"运行期地址 == IDA 静态地址"就调试**自己的副本**（拷到 `data\` 再调）；要安静加 `--aslr` |
| `Start-Process -ArgumentList` 传含空格参数，目标路径被切断 | PowerShell 不会替你加引号 | 含空格的命令行走 `--script` 文件（一行一条命令），别拼 `-c` |
| 以为要 `build.bat` 才能用 | 本机没有 MSVC / CMake | **不构建**。release 单文件就是成品，见 §2 |
| 目标路径含中文 | 未验证（本机没实测） | 先复制到纯 ASCII 路径再调试；这条是**推断**，不是实测结论 |
| `--pretty` 之后解析器报错 | `--pretty` 是美化输出 = 多行，破坏 JSONL | 机器解析一律 `--json`，不加 `--pretty` |
| 高权限目标 attach 失败 | 调试器要 `DebugActiveProcess` 权限，跨用户 / 提权进程不够 | 直接告诉用户需要提权，别在工具侧绕 |

## 7. 不备份的东西

- **`aidbg.exe` 本体（1.7 MB）不进账本仓库**：它有 release 来源、一条 `Invoke-WebRequest` 就能重取，
  按 `skills-inventory` 的「有来源的只记配方」处理。本文件的 §1 + §2 就是那份配方。
- 上游仓库整包（`src/`、`third_party/zydis`、`Manual.md` 等）**不落地**：需要读手册时
  `web_fetch` 上游 `Manual.md`，不要 clone 下来（本机没有 MSVC，clone 了也编译不了）。
- 调试产物（dump 出来的 PE、补丁副本、`notes save` 的 json）属于**案件产物**，
  落案件库 `D:\AI_python\reverse-cases\<case-id>\output\`，不进 skill 目录、不进账本。
