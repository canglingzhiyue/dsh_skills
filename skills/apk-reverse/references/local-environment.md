# 本机环境实测（本机融合层 —— 上游 SKILL.md 不知道的事实）

> 本文件是**本机融合层**，不属于上游 `apk-reverse`。上游重新安装会覆盖技能目录，
> 恢复时按账本 `skills_backup` 的 `SKILL.md` 记账条目一并还原。
>
> 事实源优先级：`$DSH_HOME\reverse\capabilities.md`（自动生成，实时） > 本文件（手工更新快照） > 上游任何 `tool-index.md`。

## 1. 本机可用的 Android 逆向底座（2026-09-29 实测）

| 能力 | 本机状态 | 位置 / 入口 |
|---|---|---|
| **jadx MCP** | 在线 | JADX-GUI 1.5.2 + `jadx-ai-mcp` 插件，监听 `127.0.0.1:8650`；工具以 `mcp__jadx__*` 暴露。**需 JADX-GUI 保持开启** |
| **IDA MCP** | 在线 | `uvx ida-mcp stdio --agent=dsh`，依赖本机 IDA 9.4 + `idalib.dll`（`D:\ProgramsDev\IDA Professional 9.4`）。工具以 `mcp__ida__*` 暴露 |
| adb | 1.0.41 | `D:\ProgramsDev\adb\adb.exe`（**不要**用雷电自带的 `D:\leidian\LDPlayer9\adb.exe`，它会抢 5037 端口互杀） |
| apksigner / zipalign / aapt2 | present | `D:\ProgramsDev\Android\SDK\build-tools\36.1.0\` |
| jadx CLI（间接） | present | 无 `jadx` CLI，但可用 `java -jar D:\ProgramsDev\jadx-gui-1.5.2-with-jre-win\lib\jadx-gui-1.5.2-all.jar` 走批处理 |
| IDA GUI | present | `D:\ProgramsDev\IDA Professional 9.4\ida.exe`（GUI 插件 `ida-mcp` 已装） |
| Android SDK / emulator | present | `D:\ProgramsDev\Android\SDK`（`emulator.exe` 在 `emulator\`） |
| 雷电模拟器 | present | `D:\leidian\LDPlayer9\ldconsole.exe` |
| 真机 | 见 capabilities | `adb devices -l` 实测过一台 Xiaomi MI 8 SE（`sirius`），root 情况以 `adb shell su -c id` 实测为准 |
| scrcpy | 3.3.1 | 投屏/录制，`D:\ProgramsDev\scrcpy-win64-v3.3.1\...\scrcpy.exe` |
| 抓包 | present | mitmproxy 12.2.3（`C:\Users\y\.local\bin\mitmdump.exe`）、Fiddler、Reqable |

**本机缺失**（上游文档常默认它们存在，别假设）：`apktool`、`frida` CLI、`objection`、Ghidra、radare2、x64dbg、dnSpy、Charles、Wireshark。
→ 重打包不要依赖 apktool 的 `b` 流程，优先用 `scripts\repack.py`；Frida 只有 WMPFDebugger 内置的 Node 绑定（`D:\AI_python\reverse\vmpfdebugger`），**设备侧动态调试需要先另行准备 frida-server**。

## 2. 与上游 SKILL.md 冲突的口径（以本机为准）

- 上游第 84 行写：*"`jadx` is a readable viewer of last resort, never the source of truth and never the entry point of a recon"*。
  **本机修正**：jadx **MCP** 是一个可用的**结构化查询入口**（`get_all_classes` / `search_classes_by_keyword` / `get_method_by_name` / `get_xrefs_to_*`），在做"先索引后精读"时比 grep 一个导出的 dex 更便宜。上游反对的是"**先整包导出再 grep**"这种做法，不是反对用 jadx 定位——两者并不矛盾，但不要让本技能退化成"jadx 导出 + grep"。
  同时：本机没有 `droidasc` / `ddc`（上游首选的索引器），所以本机的 recon 入口顺序是 **jadx MCP 结构化查询 → IDA MCP（native / .so）→ 上游 `scripts\dexutil.py` 等离线脚本**。
- 上游第 1 步要求先跑 `scripts\doctor.py --json`。**仍然要跑**，但它只知道自己那套脚本与 PATH，**不知道本机的 MCP、模拟器与真机**；把它的输出与 `capabilities.md` 合起来才是完整的"环境真相与能力清单"（G2 闸门）。
- 上游 `evidence\known-limitations.md` 承认它从未端到端跑通 packer / VMP / tamper-suicide 等路线。本机同样**没有**这些路线的实测记录——按 §3 的纪律如实标注。

## 3. Python 与脚本执行纪律

- **`uv` / `uvx` = `C:\Users\y\.local\bin\uv.exe`**（独立安装的 uv 0.12.20）—— **2026-09-30 已把 anaconda 整机移除**，`D:\ProgramsDev\anaconda3` 不复存在。PATH 上**已无 `python`**：只剩 `C:\Users\y\AppData\Local\Microsoft\WindowsApps\python.exe` 这个 0 字节 Store 存根，**不可用**。项目内一律 `uv venv` + `uv pip install`（清华源）建 `.venv`，并始终用绝对路径或 `uv run`。
- **（2026-09-30 已修）幽灵依赖解除**：`~/.dsh/profiles/web/cordis.patch.yml` 里 jadx / ida 两个 MCP 的 `command` 已从裸 `uv` / `uvx` 改为绝对路径 `C:\Users\y\.local\bin\uv.exe` / `uvx.exe`，不再依赖 anaconda 目录。MCP 起不来时先查该路径是否存在、以及 `uv cache` 里那两个缓存环境是否还在。
- 含中文路径会让部分 Python 工具崩（`import lamda` 的 `UnicodeEncodeError` 是实测过的），所以案件与脚本目录一律落纯 ASCII 的 `D:\AI_python\reverse-cases\`。
- 脚本执行分级见 `reverse-skill-router` 技能 §6：设备/网络绑定脚本（真机 dump、抓包、重打包、`adb install`）**执行前需要一次显式确认**；误跑 `coldstart.py` 这类脚本会留下孤儿 `adb logcat` 进程与近 1 MB 的 logcat 垃圾。

## 4. 更新方式

本文件不自动更新。工具环境变化后：
1. 重跑 `pwsh -File $env:USERPROFILE\.dsh\skills\reverse-skill-router\scripts\scan-capabilities.ps1`；
2. 若变化影响本文件的结论（例如装了 apktool / frida CLI、换了设备、MCP 端口变了），手工改本文件；
3. 新增的固有能力缺口照 §1 表格补行，不要写成"应该没问题"。
