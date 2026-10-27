---
name: aidbg
description: Drive the aidbg AI-first Windows x86/x64 debugger (JSONL CLI + 13-tool MCP) to debug and reverse-engineer PE exe/dll targets: breakpoints (soft/hard/memory/conditional), step and run-until, registers/memory/stack/CFG/PEB-TEB, IAT trace and rebuild, PE dump, tracked byte patching (undo, bake into a patched copy), snapshots with stepback, anti-anti-debug hide/detect. Use when debugging, tracing, unpacking, patching, or explaining the runtime behaviour of a Windows binary on this machine.
---

# aidbg —— 面向 AI 的 Windows x86/x64 命令行调试器

**本机已装**：`D:\AI_python\reverse\aidbg\aidbg.exe`（v0.4.0，单文件、零 VC 运行时依赖）。
上游 <https://github.com/A-new/aidbg>。

| 需要什么 | 去哪看 |
|---|---|
| 全部命令与参数 | `references\commands.md` |
| 本机环境、更新配方、MCP 挂载、实测坑 | `references\local-environment.md` |
| 完整手册（输出契约逐字段、表达式文法） | 上游 `Manual.md`（本机未落地，需要时 `web_fetch` 取） |

## 什么时候用它

- Windows PE（exe / dll）的**运行时**行为：某个值为什么变、谁写的、走到哪一步崩、这个分支为什么不进
- 脱壳 / dump：IAT 扫描 → 引用定位 → 重建 → `dump` 出可运行 PE
- 字节补丁：`patch` 写内存自动留存原始字节 → `patch file` 烘焙成独立可运行副本
- 反反调试：`detect`（al-khaser 清单自查）+ `hide profile`（ScyllaHide 兼容档）
- 快照回退：每个停点自动快照，`stepback` 往回走

**不该用它**：纯静态分析（PE 结构 / 反汇编先看 IDA MCP）、Android / .NET 反编译（jadx / dnSpy 系）、
内核调试、非 Windows 目标。

## 两种驱动方式（选一个，别混着来）

### A. CLI + JSONL —— 默认路径，最可靠

一条命令一行 JSON，直接解析。批量用多个 `-c`，长流程用 `--script` 文件：

```powershell
$aidbg = 'D:\AI_python\reverse\aidbg\aidbg.exe'
& $aidbg --json -c "file C:\path\target.exe" -c "run" -c "modules" -c "disasm 16" -c "stack 8" -c "kill"
```

`--script` 文件里一行一条命令、`#` 开头是注释 —— **含空格的 `-c` 行优先用脚本文件**，
免得在 PowerShell 里被引号规则咬到：

```powershell
& $aidbg --json --script .\probe.ajs
```

### B. MCP（13 个结构化工具，只在**逆向模式**会话里存在）

由自研插件 `reverse-mcp-activator` 在**逆向模式会话创建时**挂到该会话作用域
（配置在 `$DSH_HOME\profiles\web\cordis.patch.yml` 的 activator `config.servers` 里，
**不是** preset composition —— 那里的是历史副本，改了不起作用）。

`mcp__aidbg__*`：`aidbg_session` / `aidbg_execute` / `aidbg_breakpoint` / `aidbg_registers` /
`aidbg_memory` / `aidbg_disasm` / `aidbg_stack` / `aidbg_cfg` / `aidbg_modules` / `aidbg_eval` /
`aidbg_exceptions` / `aidbg_snapshot` / `aidbg_command`（兜底，原样跑任意 CLI 命令）。

会话是**有状态**的：先 `aidbg_session(action="file", exe=...)` → `action="run"`，
之后所有工具都作用在同一个目标上；`aidbg_command` 兜底时命令语法与 CLI 完全一致。

> 普通（非逆向模式）会话里**没有**这组工具 —— 那是按需挂载的设计，不是坏了。
> 要用就新开一个「逆向模式」会话，或直接用方式 A 走 CLI。

## 工作流（两种方式都适用）

1. **一次调用批量做完**，不要一条一条问。默认值已经适合分析：固定基址（运行期地址与 IDA/Ghidra
   静态地址逐字节一致）+ `--hide standard`。
2. **先勘察再动手**：`info`（会话状态）/ `modules`（base、image_base、slide）/ `disasm` / `flow`（CFG）/
   `stack` / `symbols <mask>`。每条响应都带 `session`；**只有 `state:paused` 才接受读写**。
   > `run` 之前设的断点回 `resolved:false` 是**正常**的（pending，模块加载时才下钩），不是符号缺失。
   > 想确认 PDB 是否解析成功，用 `disasm <symbol>` 或 `eval <symbol>`；`symbols <mask>` 只是枚举，可能合法地空。
3. **用表达式，别手算地址**：`break main`、`read rdx 64`、`[rbp-0x20]`、`sample.dll+0x2300`；
   `label addr name` 起的名字也能在表达式里用。
4. **让引擎自己循环**：`cond`（逐次条件）、`stepuntil` / `rununtil <expr> max=N`、
   `bpcmd <id> <cmd>`（命中即执行），别在外部轮询。`bpcmd` 里**刻意禁止**执行控制类命令。
   数调用次数 / 抓参数：入口下一个断点读 `rcx/rdx/r8/r9`，`ret` 处下一个读 `rax`，中间用 `continue`，
   最后 `bl` 看 `hit_count`（它是权威计数）。
5. **限制输出量**：`mem` 默认 64 字节；列表用 `max=N`；`search` 必须显式写 `max=N`。
6. **落盘结论**：`label` / `comment` + `notes save file.json`，下次 `notes load` 接着用。
7. **补丁流程**：`patch <addr> <hexbytes>`（等同 `write`，但写模块内存会自动记录原始字节，锚定
   module+RVA）→ 现场验证 → `patch list` / `patch undo <id|*>` 管理 → `patch file out.exe` 烘焙成
   独立可运行副本（原文件不动）。要导出整个解包镜像时改用 `dump`。
8. **硬化目标**：先 `detect`；有检查命中就 `hide profile vmp|themida|obsidium`（或 `hide set <key> 1`）
   再 `detect` 复测。**如实报告没覆盖的部分**：直接系统调用绕过 L2、时序检查、ntdll 完整性扫描能看见 INT3 钩子。

## 输出契约（要点）

- 一行一个 JSON：`{ok, cmd, data, error?, session}`；错误带 `error.code` / `error.message`；
  异步事件是 `{"kind":"event",...}` 行（**解析前先按 `kind` 过滤**）。
- 地址与 64 位值是**十六进制字符串**（`"0x7ff6..."`）；计数是数字；字节串是空格分隔的大写 hex。
- `session` 恒带 `state` / `stop_reason` / `rip` / `arch`（x86 还是 x64 决定寄存器名）/ `detail`。
- 退出码：`0` 全部成功，`1` 有命令失败，`2` 用法错误。
- `--pretty` 会多行输出，**解析用 `--json`，不要加 `--pretty`**。

## 失败处理

| `error.code` | 怎么办 |
|---|---|
| `not_paused` | 先 `continue` / 单步；目标是运行态 |
| `no_target` | `file` + `run`，或 `attach <pid>` |
| `eval_failed` / `bad_address` | 简化表达式；按 `arch` 核对寄存器名 |
| `unknown_type` / `no_type` | 试 `whatis`，或退成普通 `eval`；可能没 PDB |
| `condition_not_met` | 抬 `max=`，或把 `stepuntil` 换成 `rununtil` |
| `read_failed` | 地址可能没映射：先 `regions` |

`warning` 事件 `fixed base skipped/unavailable`（系统文件、被锁镜像）**不是失败**：目标带 ASLR 起、
slide 非零，启动继续；要安静就加 `--aslr`。

运行卡住时，怀疑目标把线程藏了（`ThreadHideFromDebugger`，而当前会话没开 hide 钩子）或 DLL 宿主在空转
（`kill` 结束它）。用 `continue <timeout_ms>` 避免无限等。

## 本机硬约束（实测，违反会浪费时间）

1. **别尝试本地构建**：本机没有 MSVC / CMake，上游 `build.bat` 跑不通。直接用 release 单文件 exe，
   更新走 `references\local-environment.md` 的下载配方。
2. **本机 PowerShell 7 传参**：`& $aidbg --json -c "file C:\x y\t.exe"` 这种数组传参没问题；
   但 `Start-Process -ArgumentList` **不会**给含空格的参数加引号 —— 含空格的一律走 `--script` 文件。
3. **`debug_string` 事件里的中文是 GBK 乱码**（conhost 的输出原样透传）。这是噪声不是错误：
   按 `"kind":"event"` 过滤掉，或只读 `"ok":true` 的行。
4. **目标路径含中文未验证**：本机没实测过中文路径目标；先复制到纯 ASCII 路径再调试（标注「未验证」）。
5. 调试器自身要对目标有 `DebugActiveProcess` 权限：同用户进程没问题，跨用户 / 提权目标需要提权，
   别在这上面绕，直接告诉用户。
