---
name: firerpa
description: Create FIRERPA / lamda Android automation scripts for Android apps and UI workflows. Use when the user wants to automate an Android app task, inspect UI state, build a selector-driven flow, or write a reusable device automation script.
---

# FIRERPA / lamda — self-contained operating manual (this machine)

> **本 skill 自包含**：本机环境、连接路径、每次干活的 SOP、CLI/API 手册、任务配方、排障，
> 全部在这一个文件里。**加载本 skill 后直接照此执行，不需要再读其他文件。**
>
> 只有需要更深细节时才去查（都不是必读）：`client/client.py`（Python API 权威）、
> `scripts/firerpa.py`（CLI 权威）、`client/rpc/*.proto`（字段权威）、
> `references/reference.md`（浓缩速查）、`references/llms-full.txt`（官方文档全文 541 节）。

---

## 0. 铁律 — 先看完这一节，违反任何一条都会返工

### 0.1 连接三条

| # | 铁律 | 为什么 |
|---|---|---|
| 1 | **解释器一律用** `D:\AI_python\firerpa\.venv\Scripts\python.exe`（CPython 3.12.13 / `lamda==10.8`） | PATH 上的 `python`/`python3` 是 **Anaconda base，没有 `lamda`** → 用必 `ImportError` |
| 2 | **先建端口通道，`--host` 一律 `localhost`**：`adb -s emulator-5562 forward tcp:65000 tcp:65000` | 模拟器 IP `172.16.1.4` 是 **NAT 网段，PC 直连不通**（实测 `TcpTestSucceeded=False`）。转发在模拟器/adb 重启后失效，连不上时**第一件事就是重跑它** |
| 3 | **adb 一律用系统全路径** `D:\ProgramsDev\adb\adb.exe` | 雷电自带的 `D:\leidian\LDPlayer9\adb.exe` 会与它**抢 5037 端口互杀**（两个进程实测同时在跑） |

### 0.2 脚本三条

| # | 铁律 | 为什么 |
|---|---|---|
| 4 | **交付物必须是落盘的脚本文件**，不是一次性 `python -c`、heredoc、临时探测脚本 | 本 skill 的产出就是「可复用的自动化脚本」 |
| 5 | **脚本必须落在纯 ASCII 路径**（本机约定 `D:\AI_python\firerpa\`） | ⚠️ 放进含中文的路径 —— **包括会话工作区 `D:\AI_python\无实际文件区`** —— 会让 `import lamda` **直接崩**，详见 §8.1 |
| 6 | **选择器必须来自 `dump` 出来的 `ui.xml`** | 不许凭记忆、文档或其它框架的习惯猜 |

### 0.3 `--host` 不许猜

**Do not guess `--host`.** If the user did not provide a host → stop and ask:

> Please provide the FIRERPA device address (IP or hostname). You can copy the Console URL from the app. If certificates or a non-default port are enabled, also provide the `lamda.pem` path and port number.

本机默认目标是雷电模拟器，走 `localhost` + adb forward；但**换了设备必须重新确认**。

### 0.4 一分钟上手（最常用的四条）

```powershell
$py  = 'D:\AI_python\firerpa\.venv\Scripts\python.exe'
$cli = "$env:USERPROFILE\.dsh\skills\firerpa\scripts\firerpa.py"
$S   = 'emulator-5562'
$adb = 'D:\ProgramsDev\adb\adb.exe'

& $adb -s $S forward tcp:65000 tcp:65000     # ① 重建端口通道
& $py $cli server-info --host localhost      # ② 连通性（永远先跑这条）
& $py $cli device-info --host localhost      # ③ 看设备
& $py $cli dump --host localhost -o ui.xml   # ④ 抓 UI 树（写选择器前必做，输出用 ASCII 路径）
```

---

## 1. 架构：两个部分，别搞混

| 部分 | 是什么 | 在哪 | 本机状态 |
|---|---|---|---|
| **server（服务端）** | 跑在**安卓设备上**的原生服务（含 Frida、内置 ADB、终端） | 设备内 `/data/<随机目录>` | ✅ 已装：`firerpa.apk` → 包名 `com.firerpa` |
| **client（客户端）** | PC 上的 Python 库 `lamda`，通过 gRPC 调 server | PC 的 Python 环境 | ✅ 已装：`lamda==10.8` |

类比：**手机 = 浏览器，FIRERPA server = WebDriver，`lamda` = Selenium**。

- 服务端**默认不启用认证**：同网段知道 IP+端口的人都能连、能调 API、能开终端。⚠️ 见 §9。
- 端口固定 **65000**（可在服务端配置里改）。
- 服务端支持 root 与 shell 两种身份；**要全部能力就用 root**。本机是 root。
- FIRERPA 功能上是常见安卓自动化栈（Appium / uiautomator2 / AutoJS + mitmproxy + frida + adb）的**超集**：
  自动化、抓包 MITM、Frida Hook、代理/VPN、远程桌面、MCP/Agent、160+ API 都在一个服务里。

---

## 2. 本机环境现状（✅ 全部实测 2026-09-26）

### 2.1 设备：雷电模拟器 9

| 项 | 值 | 怎么得到的 |
|---|---|---|
| 安装目录 | `D:\leidian\LDPlayer9\` | 进程路径 |
| **adb 序列号** | **`emulator-5562`**（**不是默认 5555**） | `adb devices` |
| 架构 ABI | **`x86_64`** | `getprop ro.product.cpu.abi` |
| Android | **9（SDK 28）** | `getprop ro.build.version.sdk` |
| 型号（伪装） | `GM1910` | `getprop ro.product.model` |
| root | **Magisk 可用**，`uid=0(root) context=u:r:magisk:s0` | `su -c id` |
| 屏幕 | **1080 x 1920**、density 480 | `device-info` / `wm size` |
| 内部 IP | `172.16.1.4/24`（wlan0，**NAT 网段**） | `ip -4 addr` |

> ⚠️ 本机 **ABA 是狐狸面具（Magisk）改了包名做防检测**。装 FIRERPA 会引入 Frida 相关特征，
> 有被目标 app 检测到的可能 —— **动手前先跟用户确认**，别在被保护的模拟器上乱装。

### 2.2 两个 adb 会互杀（必读坑）

| adb | 路径 | 版本 |
|---|---|---|
| 系统 adb | `D:\ProgramsDev\adb\adb.exe` | 1.0.41 / 36.0.0 ✅ **用它** |
| 雷电自带 | `D:\leidian\LDPlayer9\adb.exe` | 随雷电版本 |

实测两个 `adb.exe` 进程**同时在跑**。不同版本的 adb server 抢同一个 5037 端口，先启动的会把后启动的 kill 掉，
表现为 `adb devices` 时好时坏、或 `device offline`。**对策**：全程固定用系统 adb 全路径，异常时先

```powershell
& 'D:\ProgramsDev\adb\adb.exe' kill-server
& 'D:\ProgramsDev\adb\adb.exe' start-server
& 'D:\ProgramsDev\adb\adb.exe' devices -l
```

### 2.3 网络：PC **连不上**模拟器的 65000，必须转发（最关键的一条）

✅实测：`Test-NetConnection 172.16.1.4 -Port 65000` → `TcpTestSucceeded = False`

`172.16.1.x` 是雷电内部的 NAT 网段，PC 没有到它的路由。所以：

```powershell
& 'D:\ProgramsDev\adb\adb.exe' -s emulator-5562 forward tcp:65000 tcp:65000
& $py $cli server-info --host localhost     # ✅ 通
```

- 用 `--host localhost` 而**不是** `127.0.0.1`：官方明确某些工具（如抓包）靠 `localhost` 字面量判断是否走 USB。
- 若哪天给模拟器开了**桥接模式**拿到真实局域网 IP，就可直连 `--host <那个IP>`，不必转发。

### 2.4 服务端安装结果（✅实测）

| 项 | 值 |
|---|---|
| 安装包 | `firerpa.apk`，8,411,050 字节（8.4 MB） |
| 来源 | `https://device-farm.com/assets/apk/firerpa.apk` |
| 包名 | **`com.firerpa`** |
| 主 Activity | `com.firerpa/.MainActivity` |
| 服务目录 | **`/data/89frma`**（⚠️ **随机化**，不是文档里的 `/data/server`） |
| 服务进程 | `lamda` |
| 监听 | `0.0.0.0:65000` + `:::65000` |
| 服务版本 | **10.8** |
| 身份 / ABI | `root` / `x86_64` |
| 开机自启 | ON |
| 启动按钮 resourceId | **`com.firerpa:id/startButton`**（**优先用它**，坐标会随界面语言/布局变） |

> ⚠️ **卸载时别照文档删 `/data/server`**：本机服务目录是随机化的 `/data/89frma`。
> 正确做法见 §10。

### 2.5 客户端 Python 环境（✅实测）

```powershell
$py = 'D:\AI_python\firerpa\.venv\Scripts\python.exe'   # CPython 3.12.13（uv 托管）
```

- `lamda==10.8`（+ `frida 17.19.0` / `grpcio` / `cryptography` / `protobuf` 等，共 15 包，约 **160 MB**）
- ⚠️ PATH 上的 `python` 是 Anaconda base，**没装 `lamda`** —— 始终用上面的绝对路径。
- 重建：

```powershell
uv venv --python 3.12 --python-preference only-managed D:\AI_python\firerpa\.venv
uv pip install --python D:\AI_python\firerpa\.venv\Scripts\python.exe `
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple "lamda[full]"
```

---

## 3. 首次接入 SOP（从零到第一条命令）

设备换新、模拟器重装、或换机器时**严格按顺序**做，每步通过再下一步：

| # | 做什么 | 命令 | 通过标准 |
|---|---|---|---|
| 1 | 确认设备在 | `& $adb devices -l` | 看到 `emulator-5562  device` |
| 2 | 确认服务端已装 | `& $adb -s emulator-5562 shell pm list packages` | 含 `package:com.firerpa` |
| 3 | 确认服务在跑 | `& $adb -s emulator-5562 shell "su -c 'netstat -tlnp \| grep 65000'"` | `lamda` 在 LISTEN |
| 4 | **建端口通道** | `& $adb -s emulator-5562 forward tcp:65000 tcp:65000` | 输出 `65000` |
| 5 | 连通性探针 | `& $py $cli server-info --host localhost` | `version=10.8` |
| 6 | 设备信息 | `& $py $cli device-info --host localhost` | `display=1080x1920` |
| 7 | 抓 UI 树 | `& $py $cli dump --host localhost -o ui.xml` | 生成非空 `ui.xml` |

**第 3 步不通过 → 先把服务拉起来**（§3.1），不要继续往下。

### 3.1 服务端没跑起来时怎么拉

**方式 A（本机用的，推荐）**：点 APP 按钮

```powershell
& $adb -s emulator-5562 shell monkey -p com.firerpa -c android.intent.category.LAUNCHER 1
# 优先用 resourceId 定位启动按钮：com.firerpa:id/startButton
# 或先看界面：adb -s emulator-5562 exec-out uiautomator dump /dev/tty   ← 免落盘、绕开中文路径问题
# 兜底坐标（会变，别写死）：312,1667 与 312,1314 都实测成功过
# 状态会先变 CHECKING，几秒后变"运行中"
```

首次点 Start Service 若没反应，可能是 Magisk 授权弹窗挡着 → 看屏幕点「允许」。

**方式 B**：命令行直接拉起（需要知道随机服务目录）

```powershell
& $adb -s emulator-5562 shell "su -c 'sh /data/89frma/server/bin/launch.sh'"
# 期望输出含 llllaamDaa started
```

启动失败对照：

| 输出 | 含义 |
|---|---|
| `already running` | 已在运行 |
| `not run as root/shell` | 身份不对 |
| `unsupported sdk` | 安卓版本不支持 |
| `abi not match` | 装错了架构的包 |
| `file broken` | 文件损坏，重装 |

### 3.2 服务端没装时怎么装

**方式 A：APK（本机用的，最省事）** —— APP 会自己按设备 ABI 下服务端

```powershell
# ① 下 APK（本机 shell 的 TLS 是坏的，用 python urllib；见 §8.1）
python -c "import urllib.request;urllib.request.urlretrieve('https://device-farm.com/assets/apk/firerpa.apk', r'firerpa.apk')"
# ② 装
& $adb -s emulator-5562 install -r firerpa.apk
# ③ 打开 APP（com.firerpa）→ 若提示 Install required 就点 Download now
# ④ 回控制台确认 IDENTITY=root、ABI=x86_64 → 点 Start Service
```

**方式 B：Magisk 模块**（可开机自启）
下 `lamda-magisk-module.zip` → Magisk App → 模块 → 从存储安装 → **重启** →
**重启后 30 秒**服务才起，等 1~2 分钟再连。只支持 Magisk App 安装。

**方式 C：手动**
下 `lamda-server-x86_64.tar.gz`（本机是 **x86_64**，**不是**文档示例里的 arm64-v8a！）→
`adb push` 到 `/data/local/tmp` → `tar -C /data -xzf ...` → 删压缩包。
老设备自带 `tar` 解不开 `.tar.gz` 时，用 release v10.0 的 `busybox-x86_64`。

### 3.3 模拟器网络前提（换模拟器时看）

- **雷电 / 夜神**：实例设置里装驱动 → 开**桥接模式** → 重启系统。
- **AVD（Android Studio）**：`adb forward tcp:65000 tcp:65000` 后用 `localhost`。
- **架构**：新建模拟器选 64 位 → `x86_64`；32 位 → `x86`。装错架构服务起不来。
- **实体机**：PC 与手机同一局域网即可直连。
- 服务端口被转发或原本绑定环回时，**建议用 `localhost` 而非 `127.0.0.1`**。

---

## 4. 每次干活的标准流程（SOP）

**每一次都走这条路**：

```
① 连通性      server-info        ← 不通就排障，别往下写代码
② 目标确认    app-list / app-check（指定了 app 时必做，校验包名与版本）
③ 打开目标    app-start，或脚本里 app.start()
④ 抓 UI 树    dump -o ui.xml     ← 选择器的唯一合法来源
⑤ 读 ui.xml   从 resource-id / text / content-desc 里挑选择器
⑥ 写脚本      落盘的 .py（ASCII 路径）；设备初始化处 d.set_debug_log_enabled(True)
⑦ 跑脚本      用 §0.1 那个解释器
⑧ 验证        app-current / dump / exists / screenshot 复核状态
```

```bash
CLI="scripts/firerpa.py"
OUT_DIR=".firerpa"
mkdir -p "$OUT_DIR"

python3 "$CLI" dump --host 192.168.0.2 -o "$OUT_DIR/ui.xml"
python3 "$CLI" screenshot --host 192.168.0.2 -o "$OUT_DIR/screen.jpg"
python3 "$CLI" app-list --host 192.168.0.2
python3 "$CLI" app-check --host 192.168.0.2 --package com.example.app
python3 "$CLI" selector-info --host 192.168.0.2 --resource-id "com.example:id/title"
python3 "$CLI" get-text --host 192.168.0.2 --resource-id "com.example:id/input"
python3 "$CLI" set-text --host 192.168.0.2 --resource-id "com.example:id/input" --value "hello"
python3 "$CLI" exists --host 192.168.0.2 --text "Sign in"
python3 "$CLI" click --host 192.168.0.2 --resource-id "com.example:id/btn"
python3 "$CLI" device-info --host 192.168.0.2
python3 "$CLI" app-current --host 192.168.0.2
python3 your_task.py
python3 "$CLI" dump --host 192.168.0.2 -o "$OUT_DIR/verify.xml"
```

Then **Read** output files: `ui.xml` first; `screen.jpg` only if screenshot was run.

### 4.1 用途与边界（Purpose and boundaries）

**Use the unified CLI `scripts/firerpa.py` via Shell.** Do not reimplement device calls inline.
This skill is only for producing automation script files. The final deliverable must be a saved,
reusable script file. Do not treat one-off live control, transient shell driving, or non-persisted
device manipulation as the result.

Rules:

1. Stay inside the user-requested task. Do not add side experiments, alternate flows, unrelated app tests, or demo scenarios.
2. The CLI in `scripts/firerpa.py` is the required path for device inspection and operational checks.
3. Do not use inline `Device(...)` probes, `python -c`, heredoc snippets, temporary inspection scripts, or virtual-display test harnesses for quick validation.
4. Only write a separate Python script for the actual automation task logic.
5. Do not substitute manual control for script delivery.
6. If the task is under-specified, ask or stop at the narrowest correct implementation rather than inventing surrounding behavior.

`scripts/firerpa.py` 覆盖的能力：连通性/服务检查（`server-info`、`device-info`）、App 预检
（`app-list`、`app-check`、`app-current`）、App 控制（`app-start`、`app-stop`）、UI 检查（`dump`、`screenshot`）、
选择器检查与交互（`exists`、`wait-exists`、`wait-gone`、`selector-info`、`get-text`、`set-text`、
`clear-text`、`click`、`tap-bounds-center`、`scroll-to`）、设备动作（`press`、`wait-idle`、`wake`、`sleep`）、
设备命令执行（`shell`）。

### 4.2 硬性规则（Hard rules）

1. No host → ask the user. Connection failed → troubleshoot first.
2. Complete connectivity checks before selector discovery.
3. First UI inspection call must be `firerpa dump` or `app-start` then `dump`.
4. Read `ui.xml` before writing selectors.
5. Never guess selectors from docs or memory.
6. Always deliver a persisted script file.
7. In the delivered automation script, enable lamda debug logging with `d.set_debug_log_enabled(True)` near device initialization unless the user explicitly asks to suppress logs.
8. Prefer element-driven interactions over key presses whenever a stable selector-driven path exists.
9. Use `press` only for navigation or dismissal when element-driven interaction is unavailable or clearly less reliable.
10. Never assume `ENTER` is a safe submit action; prefer explicit element-based submission and treat `ENTER` as ambiguous.
11. After any `press`, verify the resulting visible state before continuing.
12. Do not add `d.set_debug_log_enabled(True)` to CLI inspection commands, ad hoc validation snippets, or non-deliverable helper code.
13. Always verify both action success and result reasonableness after running the script.
14. Do not keep retrying validation loops; when blocked, stop with enough information for the user to judge the next step.

本机补充：

15. **Scripts must live on an ASCII-only path**（本机约定 `D:\AI_python\firerpa\`）—— 放进含中文的路径
    （包括会话工作区）会让 `import lamda` 直接崩，见 §8.1。

### 4.3 验证标准（Verification standard）

Self-verification is required.

1. Do not treat script execution without errors as proof of success.
2. After running the script, verify both action success and result reasonableness.
3. Prefer verification through `scripts/firerpa.py` state checks such as `dump`, `screenshot`, `exists`, `app-current`, `device-info`, and `app-check`.
4. If the task changes UI state, re-dump the UI and confirm the expected state transition.
5. If the task writes text, sends content, changes settings, opens a page, or triggers navigation, verify the resulting visible state or app state accordingly.
6. Do not rely only on prints from the task script when a device-side state check is available.
7. If verification is inconclusive, say so and return control rather than claiming success.
8. Do not loop indefinitely on retries, validation attempts, or alternate checks.
9. If conditions are not met, verification fails, or the next action requires a user decision, stop and report what was checked, what failed, and what the user should decide or do next.

### 4.4 交互规则（Interaction rules）

Drive the flow from observable device state, not guesswork.

1. Prefer the most stable selector available. `resourceId` or another strong identifier usually beats visible text.
2. When text is dynamic, `textContains` or `textMatches` may be appropriate if they are the most reliable way to identify the target.
3. A matched element is not automatically the correct element; constrain high-risk actions and verify the result.
4. Re-locate elements after page changes, scrolling, or refreshes instead of relying on stale element objects.
5. Do not assume element operations implicitly wait long enough. Use explicit checks such as `wait_for_exists(timeout)` when the next step depends on state.
6. Do not treat `exists()` as proof that an element is ready for interaction; it only proves a match was found.
7. Do not use fixed `sleep()` as the primary synchronization strategy. If a short sleep is used as a supplement, follow it with an explicit state check.
8. Prefer `set_text()` for text entry and explicit submit, confirm, save, or send elements for business actions.
9. Do not use `press` as the primary way to submit text, confirm forms, or trigger business actions when a stable element interaction is available.
10. Do not assume `ENTER` means submit. It may insert a newline, confirm IME composition, trigger a search/send action, or do nothing.
11. Do not assume the intended element owns focus. Soft keyboards, dialogs, overlays, and custom views can redirect or consume key events.
12. Treat `BACK`, `HOME`, and `ENTER` as high-ambiguity actions. Use `press` only for explicit navigation or dismissal, and verify the resulting visible state before continuing.
13. Do not use coordinate-driven interaction as a normal path when selector-driven interaction is available.
14. Do not treat screenshot capture as proof that the target page is loaded or correct.
15. Do not treat text entry success as proof that the business action was submitted or completed.
16. Check app context at critical boundaries. Treat permission pages, system dialogs, and intermediate system surfaces as separate contexts, and identify blockers before continuing if the flow leaves the expected app or screen family.

### 4.5 目标 App 纪律（Target-app discipline）

If the user specified a target app, package, activity, or workflow context, keep all task logic,
verification, and examples anchored to that target.

1. Do not substitute a different app just because it is easier to test.
2. Do not switch to unrelated system apps, browsers, launchers, or demo apps unless the user explicitly asked for those apps.
3. Do not use unrelated apps to "verify the environment" when the requested task is about a different target app.
4. If the target app cannot be reached, is missing, is version-mismatched, or is blocked by a user-control gate, stop and report that exact blocker instead of drifting into another app.
5. If examples are app-specific, keep the examples aligned with the user's requested target or use neutral placeholders like `com.example.app`.

**Allowed inspection path**：只用 `scripts/firerpa.py` 做设备检查、App 预检、选择器检查与操作验证；
可用命令面 = §5 的 26 个子命令。

**App prechecks**：

1. Use `app-list` to inspect installed user apps.
2. Use `app-check` before app-specific automation when the package/name is user-provided, ambiguous, or version-sensitive.
3. If the target app does not exist in user apps, stop and tell the user to install it.
4. If the requested `versionName` does not match, stop and tell the user to install or reinstall the expected version.
5. Do not continue into selectors, navigation, or script writing for a missing or mismatched target app.
6. Do not replace a blocked target app with a different app for testing or demonstration.

### 4.6 连接与预检排障顺序（Connection and app prechecks）

If connection fails, do not continue with automation design. Walk the user through the following
checks in order and retry the smallest useful command after each confirmed fix.

1. **Confirm target address** — check whether `--host` is present; ask the user for the Console URL / device IP / hostname / forwarding target. Do not guess LAN IPs, localhost forwarding, or public endpoints.
2. **Test the service with a minimal command** — prefer `firerpa.py server-info`; then `device-info`; only move to `dump` after basic connectivity works.
3. **Check whether the service is installed on the device** — ask; if unsure, have the user verify in the FIRERPA app. If not installed, stop and guide installation first (§3.2).
4. **Guide installation when missing** — confirm device architecture if manual package selection is needed; confirm the service started; confirm the exposed host/port.
5. **Check whether the service is running** — if installed but stopped, start it first (§3.1); if reconfigured or restarted, re-check host/port/certificate.
6. **Check port and forwarding path** — default port `65000`; with ADB forward prefer `localhost` and verify the forward target; with frp/Hub/VPN confirm the externally exposed host/port rather than the device LAN address.
7. **Check certificate / TLS mode** — if the error mentions TLS/SSL/certificate/handshake/verify, ask whether certificates were configured; if TLS is on, require the matching `--certificate /path/to/lamda.pem`; if off, do not invent certificate settings.
8. **Retry after each confirmed fix** — retry `server-info`, then `device-info`, then `dump`; only after one succeeds may you write selectors or automation code.
9. **Escalation boundary** — if the user cannot confirm installed/running/reachable, switch into troubleshooting guidance mode rather than code-writing mode. Do not fabricate installation status, port config, or certificate state.

### 4.7 从 ui.xml 到选择器

| ui.xml 里的属性 | lamda 选择器参数 |
|---|---|
| `resource-id` | `resourceId` |
| `content-desc` | `description` |
| `text` | `text` |
| `class` | `className` |

**优先级**：`resourceId` > `text` > `description` > `textContains`（模糊兜底）。
`resourceId` **不保证唯一**，同屏可能有多个同 id 元素 → 用 `selector-info` 看匹配数。

完整 `Selector` 可选参数：

| Match Type | Description |
|---|---|
| `text` | Exact text match |
| `textContains` | Text contains match |
| `textStartsWith` | Text starts with match |
| `textMatches` | Text regex match |
| `className` / `classNameMatches` | Class name match |
| `description` / `descriptionContains` / `descriptionStartsWith` / `descriptionMatches` | Description match |
| `resourceId` / `resourceIdMatches` | Resource ID match |
| `clickable` / `longClickable` / `scrollable` / `checkable` | State flags |
| `enabled` / `checked` / `focused` / `selected` | State flags |
| `packageName` / `packageNameMatches` | Package match |
| `index` / `instance` | Positional match |

### 4.8 禁用 API 猜测（Forbidden API guesses）

Do not import habits or syntax from Appium, Selenium, Playwright, uiautomator2, or other Android automation wrappers.

| Wrong | Correct |
|-------|---------|
| `driver.find_element(...)` | `d(text="...")`, `d(resourceId="...")`, `d(description="...")` |
| `driver.find_elements(...)` | `d(...).count()`, `d(...).get(idx)`, `for x in d(...): ...` |
| `el.input_text()` | `el.set_text()` |
| `el.clear_text()` | `el.clear_text_field()` |
| `d.shell("cmd")` | `d.execute_script("cmd")` |
| `app.clear_data()` | `app.reset()` |
| `wait_for_element(...)` | `el.wait_for_exists(timeout)` |
| XPath selectors / XPath-derived queries | selectors built from `ui.xml` fields such as `text`, `resourceId`, `description`, and `className` |

### 4.9 Proto 字段访问规则

Many return values in `lamda` are protobuf-backed objects. Field access must follow the proto definitions and generated client exactly.

1. Never guess field names from habits in Appium, Selenium, Playwright, uiautomator2, Java beans, Python dicts, or snake_case conventions.
2. Confirm field names in `client/client.py` first; read `client/rpc/*.proto` when the generated wrapper is not enough.
3. Keep the field name exactly as exposed by the client or proto-backed object.
4. If a field is not verified in source, do not access it.
5. Treat proto results as typed objects unless the source clearly shows a dict/list shape.
6. Printed protobuf output may omit empty / false fields; omission in `print(obj)` does not mean the field is unavailable.
7. Do not mix selector field names with `info()` field names.

| Wrong | Correct |
|-------|---------|
| `info.package_name` | `info.packageName` |
| `info.current_package_name` | `info.currentPackageName` |
| `result["stdout"]` | `result.stdout` |
| `app_info["packageName"]` | `app_info.packageName` |
| `d(resourceName="...")` | `d(resourceId="...")` |
| `info.resourceId` | `info.resourceName` |
| guessed snake_case / dict-style fields | source-verified proto/client fields only |

### 4.10 允许的常用 API（优先用这些）

**Device**

- `d(...)`, `d.set_debug_log_enabled(True)`, `d.dump_window_hierarchy(...)`, `d.screenshot(...)`
- `d.device_info()`, `d.current_application()`, `d.application(...)`, `d.get_application_by_name(...)`
- `d.execute_script(...)`, `d.wait_for_idle(...)`, `d.press_key(...)`, `d.wake_up()`, `d.sleep()`

**Element**

- `el.click()`, `el.click_exists()`, `el.long_click()`, `el.exists()`, `el.info()`
- `el.get_text()`, `el.set_text()`, `el.clear_text_field()`
- `el.wait_for_exists(timeout)`, `el.wait_until_gone(timeout)`, `el.scroll_to(...)`, `el.swipe(...)`, `el.drag_to(...)`

Unless the task clearly requires something else **and** the alternative has been verified in `client/client.py`.

### 4.11 特殊边界

#### Watcher rules

Use watchers only when the task clearly benefits from automatic interruption handling or appearance counting.

1. Register watchers near the start of the script, not midway through normal business logic.
2. Before a new run, clear old watcher state with `d.remove_all_watchers()` unless persistence is explicitly desired.
3. Registering a watcher is not enough: **enable the watcher loop and then enable the watcher itself**.
4. Too many watchers can affect performance; keep the set minimal and task-specific.
5. If a watcher can cause destructive navigation or clicks, state that risk in comments or surrounding logic.

```python
d.remove_all_watchers()
d.register_click_target_selector_watcher("AcceptAgreement", [Selector(textContains="User Agreement")], Selector(textContains="Accept", clickable=True))
d.set_watcher_loop_enabled(True)
d.set_watcher_enabled("AcceptAgreement", True)
```

#### User-control boundaries

If the target app blocks progress with a gate that normally requires user control, treat that as a
handoff boundary unless the user explicitly asked for handling logic and the gate can be passed
through normal visible UI without unstable hacks.

Examples: forced update / login / OTP·SMS·email verification / CAPTCHA / biometric·passcode /
real-name verification / device-binding confirmation / permission prompts requiring deliberate user
choice / terms·policy gates that cannot be stably skipped.

1. First determine whether the gate is optional, skippable through normal UI, or mandatory.
2. If the gate is optional and the skip path is visible in normal UI, you may automate that normal skip path.
3. If the gate is mandatory and progress cannot continue without user participation, stop and return control to the user.
4. If you tried the normal visible path and the app still blocks progress, stop and return control to the user.
5. Do not invent brittle bypasses, hidden activities, package tampering, network blocking tricks, credential stuffing, token reuse, or reverse-engineering workarounds unless the user explicitly requested that class of work.
6. When returning control, say clearly which gate blocked progress and what the user needs to complete manually before automation can resume.

#### Authoring display and OCR policy

During script authoring and verification, always inspect and parse the UI from the **default display
(main screen)**. If the user wants final execution on a virtual display, apply that only in the
delivered task script after selectors and flow have already been verified from the main screen.

Use standard UI selectors first. Only move to OCR or image matching when the app does not expose a usable Android View tree.

1. Authoring-time inspection path: main-screen `dump` → read `ui.xml` → selector-based automation design.
2. Authoring-time screenshots and quick validation should also use the default display, not a virtual display.
3. If the user wants final execution on a virtual display, keep authoring-time selector discovery on the main screen and only wrap the final task logic with `create_virtual_display()`.
4. If the UI is custom-drawn, game-like, or `dump` is empty / insufficient, use main-screen screenshot + OCR or image matching for authoring-time analysis.
5. OCR selectors are limited; do not assume they support the full selector API.
6. In multi-device or clustered scenarios, prefer a custom HTTP OCR backend over loading heavy local OCR models in each process.
7. A virtual display instance `vd` is for final automation on that display. **Global-effect operations must still use the original device instance `d`.**
8. Watchers registered on `vd` affect that virtual display, not the main screen.
9. Do not create a separate virtual-display validation script unless the user explicitly asked for a dedicated virtual-display test.

```python
base = Device("example.local")
with base.create_virtual_display() as vd:
    vd.application("com.example.app").start()
    vd(textContains="Target Action").click()
```

---

## 5. CLI 命令手册（`scripts/firerpa.py`）

**通用参数**（放子命令**前面**）：`--host`（必给，本机 `localhost`）、`--port`（默认 65000）、
`--certificate`（启用 TLS 时的 `lamda.pem` 路径）。
也可用环境变量 `DEVICE` / `PORT` / `CERTIFICATE` 代替。

```bash
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] dump [-o FILE] [-z]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] screenshot [-o FILE] [-q N] [--left --top --right --bottom]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] app-start (-p PKG [-u USER] | -n NAME)
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] app-stop  (-p PKG [-u USER] | -n NAME)
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] app-list [-u USER]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] app-check (-p PKG | -n NAME) [-u USER] [--version VERSION]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] device-info
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] app-current
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] server-info
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] wake
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] sleep
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] press KEY_BACK|KEY_HOME|...
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] shell "command" [-t SEC]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] wait-idle [MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] wait-exists (--text T | --resource-id ID | ...) [--timeout MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] wait-gone (--text T | --resource-id ID | ...) [--timeout MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] selector-info (--text T | --resource-id ID | ...) [--timeout MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] get-text (--text T | --resource-id ID | ...) [--timeout MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] set-text (--text T | --resource-id ID | ...) --value TEXT [--timeout MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] clear-text (--text T | --resource-id ID | ...) [--timeout MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] tap-bounds-center (--text T | --resource-id ID | ...) [--timeout MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] assert-app-current --package PKG
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] click (--text T | --resource-id ID | ...) [--timeout MS]
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] exists  (--text T | --resource-id ID | ...)
python3 scripts/firerpa.py [--host HOST] [--port PORT] [--certificate FILE] scroll-to (--text T | ...) [--scrollable] [--horizontal]
```

**什么时候用哪个**：

| 命令 | 作用 | 何时用 |
|---|---|---|
| `server-info` | 服务端版本/架构/是否 TLS | **每次连接的第一条** |
| `device-info` | 屏幕、亮度、前台包名 | 确认设备与分辨率 |
| `app-current` | 当前前台包名 | 验证「跳转成功了吗」 |
| `app-list` | 已安装用户 app | 找包名 |
| `app-check` | 校验装没装 / 版本 | **app 自动化前必做** |
| `app-start` / `app-stop` | 启动 / 强停 app | 把目标拉到前台 / 要干净起点 |
| `dump` | 抓 UI 树 XML | **写选择器前必做** |
| `screenshot` | 截图 | XML 空 / 不够时 |
| `exists` | 元素存在吗（退出码 0/1） | 条件判断 |
| `wait-exists` / `wait-gone` | 等出现 / 等消失 | 页面加载同步、等弹窗结束 |
| `selector-info` | 匹配数 + 首个信息 | **判断选择器唯一性** |
| `get-text` / `set-text` / `clear-text` | 读 / 填 / 清空 | 取数据、输入 |
| `click` / `tap-bounds-center` | 点元素 / 点包围盒中心 | 点击（后者是 `click` 不稳时的退路） |
| `scroll-to` | 滚到目标出现 | 长列表 |
| `assert-app-current` | 断言前台包名 | 脚本 / 校验里断言 |
| `wait-idle` | 等界面静止 | 替代瞎 sleep |
| `press` | 按物理键 | 仅导航 / 关闭，**press 后要验证** |
| `wake` / `sleep` | 亮屏 / 熄屏 | 屏幕状态控制 |
| `shell` | 设备上执行命令 | 取设备侧信息 |

Deps: `pip3 install -r requirements.txt` — Only `scripts/firerpa.py`, single self-contained CLI.

**✅ 实测输出样例**（本机）：

```text
$ firerpa.py server-info --host localhost
version=10.8
unique_id=6ab75f6f-0797-4917-abba-11cafa394166
architecture=x86_64
secure=False

$ firerpa.py device-info --host localhost
package=com.firerpa
display=1080x1920
screen_on=True
orientation_natural=True

$ firerpa.py app-current --host localhost
com.android.settings
```

---

## 6. Python API 手册（按场景）

### 6.1 连接与入口

```python
from lamda.client import *
d = Device("localhost")                                  # 本机（已 adb forward）
d = Device("192.168.0.2", port=65001)                    # 换端口
d = Device("host", certificate="/path/to/lamda.pem")     # 开了 TLS
d.set_debug_log_enabled(True)                            # 交付脚本里要开
```

多数 API 返回 **native proto 类**，可直接按属性取值，或查 `client/rpc/*.proto` 看有哪些字段：

```python
>>> result = status.get_battery_info()
>>> print(result.batt_percent)
100
```

### 6.2 设备与屏幕

```python
d.device_info()            # displayWidth/displayHeight/screenOn/currentPackageName...
d.server_info()
d.wake_up() / d.sleep() / d.is_screen_on() / d.is_screen_locked()
d.screenshot(quality, bound=None).save("out.png")
d.dump_window_hierarchy(compressed=False)     # 返回 BytesIO 的 XML
d.wait_for_idle(timeout_ms)
d.press_key(Keys.KEY_BACK) / d.press_keycode(code, meta=0)
d.get_clipboard() / d.set_clipboard(text)
d.show_toast(text, duration=ToastDuration.TD_SHORT) / d.get_last_toast()
d.beep()                                       # 多设备时找机器
d.open_notification() / d.open_quick_settings()
d.freeze_rotation(freeze=True) / d.set_orientation(orien=Orientation.ORIEN_NATURE)
d.find_similar_image(data, threshold=0.0, distance=250, ...)   # 找图，返回 bounds
```

### 6.3 选择器与元素

```python
el = d(text="同意")
el = d(resourceId="com.xxx:id/btn", clickable=True)
el = d(text="同意", resourceId="com.tencent.news:id/btm_first_agree")
el = d(className="android.widget.EditText")

el.exists()                     # bool
d(resourceId="x").count()       # 匹配数量
d(resourceId="x").get(0)        # 第 idx 个
for e in d(className="android.widget.TextView"): ...   # 迭代

el.click() / el.click_exists() / el.long_click()
el.click(corner=Corner.COR_TOPLEFT)     # 也可 COR_CENTER / COR_BOTTOMRIGHT
el.get_text() / el.set_text("hi") / el.clear_text_field()
el.wait_for_exists(15*1000)     # ⚠️ 毫秒！
el.wait_until_gone(timeout)
el.scroll_to(...) / el.swipe(...) / el.drag_to(...)

info = el.info()                # bounds/className/clickable/enabled/packageName/resourceName/text
info.bounds.center().x          # 中心点
info.bounds.corner("top-left")  # 四角：top-left/top-right/bottom-left/bottom-right
info.bounds.width / info.bounds.height
```

**链式定位**（重复元素或无特征控件）：`child(...)` / `sibling(...)`
（例：账号框是登录框的 child；用户名与密码互为 sibling）。它们本身就是元素，可继续做任何元素操作。

### 6.4 坐标与区域

```python
Point(x=100, y=100)
Bound(top=0, left=0, right=540, bottom=960)
```

- 原点**永远取当前方向的左上角**（横屏竖屏、自动旋转都一样）。
- `Bound` 四个值**都是到屏幕左 / 上边的距离**：`top` 到屏幕顶、`left` 到屏幕左、
  `right` 到屏幕左、`bottom` 到屏幕顶。

### 6.5 滑动与手势

```python
d().swipe()                                   # 默认整屏滑一下
d.drag(PointA, PointB, step=32) / d.swipe(A, B, step=32)
d.swipe_points(*points, step=32)
d().fling(...)                                # 惯性快滑
d().scroll(...)                               # 更机械的滑动
# 多点触控：录制 / 回放 / 程序构造 / 二进制持久化（压力 z: 1-255，默认 128）
```

多点触控要点：`record()` 后需在设备上真实操作，超时 120 秒；全部手指抬起才结束。

### 6.6 App 操作

```python
app = d.application("com.taobao.taobao")      # 按包名
app = d.get_application_by_name("淘宝")        # 按名字
app.is_installed() / app.info().versionName / app.info().packageName
app.start() / app.stop() / app.reset()        # reset = 清数据
app.is_foreground()
d.current_application()                       # ⚠️ 见下方实测
app.grant_permission(...) / app.revoke_permission(...) / app.list_permissions()
app.enable() / app.disable()
d.launch_activity(...)                        # 可启动非导出 Activity
```

> ⚠️ **实测差异**：`d.current_application()` 返回 **`Application:com.android.settings:0@0`**
> （带前缀与 uid/pid），而 CLI 的 `app-current` 只打印**纯包名** `com.android.settings`。
> 做字符串比较时注意这个差异。

### 6.7 文件与命令

```python
d.download_file(remote, local) / d.download_file(...) 到内存 / 到描述符
d.upload_file(local, remote) / 从内存 / 从描述符
d.delete_file(path) / d.modify_file_permissions(...) / d.get_file_info(path)
d.execute_script("id")            # 前台执行，返回结果对象（.stdout）
d.execute_script_background(...)  # 后台执行
```

### 6.8 按需特性（非本机实测，用到再查细节）

- **OCR 文字识别**：后端可选 paddleocr / easyocr / 自建 HTTP；**选择器能力有限**，别当万能。
- **图像匹配**：模板 / SIFT，**在设备端算**，不吃 PC 资源；SIFT 对旋转缩放光照更稳。
- **虚拟屏**：`create_virtual_display()` 后台跑 app，不影响主屏；`vd` 只做显示相关，**全局操作仍用 `d`**。
- **抓包 MITM**：一键装系统根证书 + 设代理 + 退出还原；支持全局 / 按包、QUIC 降级、共享 mitmweb。
- **Frida**：内置（不用 frida-server），连接走 token；支持持久化脚本、RPC 转 Python 方法。
- **代理 / VPN / frp / tunnel2 / mDNS**：设备侧 HTTP·HTTPS·SOCKS5·Shadowsocks、OpenVPN 客户端、
  frp 内网穿透、设备 HTTP 反向代理（出口 IP 与手机一致）、mDNS 设备发现（默认关）。
- **内置终端 / ADB / SSH**：终端含 strace、tcpdump、frida-tools、Python 栈、sqlite3 加密库
  （wxsqlite / sqlcipher / sqlcrypto，可读微信、企业微信、阿里系加密库 —— 需自备密钥）。
- **系统级扩展**：`setprop` 写 `ro.*`、Settings API、SELinux 域管理、静默授权、启停用应用、二进制 patch。

---

## 7. 任务配方

### 7.1 启动 app 并确认页面就绪（✅ 实测骨架）

```python
from lamda.client import *
import time

d = Device("localhost")
d.set_debug_log_enabled(True)

app = d.application("com.android.settings")
print("is_installed:", app.is_installed())
print("versionName :", app.info().versionName)

app.stop(); time.sleep(1)
app.start(); time.sleep(4)

info = d.device_info()
print("screen      :", info.displayWidth, "x", info.displayHeight)
print("current_app :", d.current_application())
```

✅ 实测输出：

```text
is_installed: True
versionName : 9
screen      : 1080 x 1920
current_app : Application:com.android.settings:0@0
```

CLI 复核：`app-current --host localhost` → `com.android.settings`

### 7.2 搜索类流程（官方样例 `search_in_taobao.py` 的骨架）

标准骨架：**校验安装 → 校验版本 → 停 → 起 → 等 → 验首页 → 点击输入 → 等激活 → 填词 → 提交 → 等结果**

```python
d = Device("localhost")
app = d.application("com.taobao.taobao")
if not app.is_installed(): exit("app 没装")
if app.info().versionName != "10.48.0": exit("版本不符，要求 10.48.0")

app.stop(); time.sleep(1.5)
app.start(); time.sleep(10)                      # 等 app 起完

if not d(description="我的淘宝").exists():        # 先验证在首页
    exit("不在首页")

d(description="搜索栏").click()                   # 激活输入
d(resourceId="com.taobao.taobao:id/searchbtn").wait_for_exists(15*1000)
d(resourceId="com.taobao.taobao:id/searchEdit").set_text("苹果手机")
d(resourceId="com.taobao.taobao:id/searchbtn").click()   # 明确的提交元素
d(description="筛选").wait_for_exists(15*1000)           # 等结果出现
d().swipe()
```

要点：**先验证在哪个页面**，再动手；提交用**明确的按钮元素**，不用 `ENTER`。

### 7.3 处理弹窗（协议 / 更新 / 广告）

用 Watcher（§4.11），或简单场景直接：

```python
if d(textContains="同意").exists():
    d(textContains="同意", clickable=True).click()
```

**强制更新、登录、验证码等关卡 → 停手交还用户**（§4.11 user-control boundaries），不要硬绕。

---

## 8. 排障手册

### 8.1 本机特有问题（与 FIRERPA 无关，但一定撞上）

**shell 的 TLS 是坏的**：

- `Invoke-WebRequest` → `Authentication failed`
- `curl.exe` → `schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS (0x8009030E)`
- `git clone https://…` → `cannot create standard input pipe for remote-https: Permission denied`（沙箱管道边界）

**可行通道**：用 python 的 `urllib.request` 下载（APK 与仓库 zip 都是这么拉下来的）。
⚠️ 只用它下载，**不要用 Anaconda 的 pip 装东西**。

**`adb pull` 到含中文的路径会失败**（`cannot create file/directory`）→ 先 pull 到纯 ASCII 目录再拷。

**⚠️ 最坑的一条：交付脚本落在含中文的路径下，`import lamda` 直接崩**（实测）

`lamda` 导入时会用 `grpc_tools.protoc` 动态编译 proto，它对**每一个 `sys.path` 条目**做
`path.encode("ascii")`：

```text
UnicodeEncodeError: 'ascii' codec can't encode characters in position 13-18
  ... grpc_tools\protoc.py, line 159, in exec_module
      [path.encode("ascii") for path in sys.path],
```

**它死在任何设备调用之前**，症状看起来像「环境坏了 / lamda 装错了」，其实纯粹是路径问题。所以：

- ✅ 交付脚本放**纯 ASCII 目录** —— 本机约定放 `D:\AI_python\firerpa\`
- ❌ **绝对不要**把脚本放进会话工作区 `D:\AI_python\无实际文件区`（路径含中文）→ 必崩
- CLI `scripts\firerpa.py` 本身在 `C:\Users\y\.dsh\...`（ASCII），**不受影响**
- `dump -o` / `screenshot -o` 的输出路径同样用 ASCII
- 想取设备侧 UI 树又完全不落 PC 盘：`adb exec-out uiautomator dump /dev/tty`

根因与官方文档 Troubleshooting 那条（「`sys.path` 含中文字符导致 gRPC 编码错误」）**是同一件事**。

### 8.2 连接类

| 症状 | 先查 | 处理 |
|---|---|---|
| `error: cannot connect to grpc://localhost:65000` | 转发还在吗 | 重跑 `adb -s emulator-5562 forward tcp:65000 tcp:65000` |
| 同上 | 服务在跑吗 | `adb shell "su -c 'netstat -tlnp \| grep 65000'"` → 没有就启动服务（§3.1） |
| 提示 TLS/SSL/handshake | 服务端开了证书吗 | 要 `--certificate /path/to/lamda.pem`，端口可能也变了 |
| `adb devices` 空 / 时好时坏 | 两个 adb 打架 | 固定用系统 adb 全路径，`kill-server` 后重来 |
| 直连设备 IP 不通 | 是不是模拟器 NAT | 走 adb forward（本机就是这种情况） |
| `Service Unavailable` | 环境配置没做完 | 确认设备能上公网、防火墙没挡 |
| 服务起不来且崩在 avtab / SELinux policy | 是不是 KernelSU 旧版 | 升级 KSU；或换 Magisk；或降级为 shell 权限运行 |
| 服务起来后 app 崩溃 / 被检测异常 | Frida 特征 | 升级到最新版；10.0 起 `enhanced-stealth-mode` 已移除 |

### 8.3 自动化类

| 症状 | 原因 | 处理 |
|---|---|---|
| 选择器匹配 0 个 | 选择器不是从 `ui.xml` 来的 | 重新 `dump`，照 `resource-id` / `text` 原样抄 |
| 匹配多个 | `resourceId` 不唯一 | 加 `clickable`/`className` 约束，或用 `child`/`sibling`，或 `.get(idx)` |
| `dump` 空 / 很少 | 界面自绘（游戏）或 WebView | 用 `screenshot` + OCR / 图像匹配 |
| 点了没反应 | 元素被遮挡，或 `exists` 但不可点 | 先 `wait-idle`，再 `selector-info` 看 bounds，退到 `tap-bounds-center` |
| 输入没进去 | 输入框没激活 | 先 `click()` 激活，再 `set_text()` |
| 元素对象失效 | 页面变了 | **重新定位**，别复用旧对象 |
| 脚本没报错但没效果 | 没做结果验证 | 用 `app-current` / `dump` / `exists` 复核状态 |
| 抓包抓不到 | 证书校验 / 前后处理 | 先确认是全局还是单 app 抓不到；app 若做了证书校验需逆向绕过；抓包前**强停目标 app** 再重开 |

---

## 9. 安全与反检测（动手前必读）

- ⚠️ **服务端默认无认证**：同网段任何人都能连、能调 API、能开终端。
  不可信网络务必开**服务证书**（TLS + 密码），客户端用 `certificate=` 连；
  证书由 `tools/cert.py <主机名>` 生成 → `mydevice.local.pem`（内含默认登录密码）。
  注意区分：**服务证书**（加密 FIRERPA 通信链路）≠ **MITM 抓包证书**（装进安卓系统信任库供抓包）。
- ⚠️ **FIRERPA 带 Frida**，部分 app 会检测到（官方 FAQ 明确提到「检测工具发现异常特征」）。
  本机环境有**狐狸面具改包名防检测**的诉求 → **动手前先问用户**，别在被保护的模拟器上乱装。
- 只做**用户自己设备上、用户明确要求**的自动化；登录态、密码、token 一律不写入脚本或备份。
- 本机服务目录是随机化的 `/data/89frma`。

---

## 10. 卸载与还原（本机）

```powershell
$adb = 'D:\ProgramsDev\adb\adb.exe'
# ① 先停服务，等 30 秒让服务优雅退出
& $adb -s emulator-5562 shell monkey -p com.firerpa -c android.intent.category.LAUNCHER 1
#    APP → 点 "Stop Service"
Start-Sleep -Seconds 30

# ② 删服务目录（⚠️ 本机是随机目录，不是 /data/server）
& $adb -s emulator-5562 shell "su -c 'rm -rf /data/89frma /data/usr'"

# ③ 卸载 APP
& $adb -s emulator-5562 uninstall com.firerpa

# ④ 撤掉端口转发
& $adb -s emulator-5562 forward --remove-all
```

通用形式是 `rm -rf /data/server /data/usr`（shell 身份下是 `/data/local/tmp/usr`）；
**APK 安装的随机目录名以 APP 里「Service directory」显示为准**，先看一眼再删。
Magisk 装的就直接在 Magisk App 里移除模块。

---

## 11. 资料优先级（Source of truth）

Lookup priority:

1. `scripts/firerpa.py` for CLI workflow and command syntax
2. `client/client.py` for Python API method names and object behavior
3. `client/rpc/*.proto` for field names, message shapes, and enum names
4. `references/reference.md` for condensed reminders
5. `references/llms-full.txt` only for supplemental background and examples

Rules:

1. If memory, examples, or external docs conflict with local code, follow local code.
2. If a method, selector pattern, field, or enum name is not confirmed in local source, treat it as unavailable.
3. For non-trivial API usage, read `client/client.py` first.
4. Do not use `references/llms-full.txt` as the source of truth for API names, CLI syntax, or proto field names when local code disagrees.

**本文档的分工**：本文件的「本机环境 / 连接路径 / SOP / 配方 / 排障」是本机适配层，权威；
但**API 名 / CLI 语法 / proto 字段名**以上面 1–3 为准。冲突时改本文件，不要按记忆写代码。

---

## 12. 交付前检查清单（Pre-output checklist）

- [ ] Selectors came from `ui.xml`, not guesswork
- [ ] A reusable automation script file was written to disk as the final deliverable
- [ ] **该脚本落在纯 ASCII 路径**（不是含中文的会话工作区）
- [ ] The delivered automation script enables `d.set_debug_log_enabled(True)` near device initialization unless the user asked not to log
- [ ] Every non-trivial API name and field access was verified against local source
- [ ] The script, verification steps, and examples stayed anchored to the user-specified target app
- [ ] Element operations were preferred over key presses wherever a stable selector-driven path existed
- [ ] No ambiguous key press such as `ENTER` was used as a guessed submit action
- [ ] Any `press` step was followed by a visible state verification before continuing
- [ ] Target user app existence and requested version were verified before app-specific automation
- [ ] User-control gates were either handled through a normal visible path or handed back to the user
- [ ] Post-run verification checked both whether the action succeeded and whether the resulting state was reasonable
- [ ] Blocking conditions were reported clearly instead of triggering repeated validation loops
- [ ] No ad hoc inspection script or unrelated validation flow was added where `scripts/firerpa.py` already provides the needed path
- [ ] OCR / image matching was used only when selector-based automation was not sufficient
- [ ] Authoring-time UI parsing and validation used the main screen, even if the final script targets a virtual display
- [ ] Virtual-display code did not move global-effect operations from `d` to `vd`
- [ ] Debug / verification steps use `scripts/firerpa.py`, not inline inspection code

---

## 13. 维护提醒

- **本文件是自包含的**：改完直接生效，没有第二个文件要同步。但它是**本机适配层**，
  改动要在 `D:\AI_python\skills_backup\SKILLS.md` 追加一行日志，
  并把本文件整份复制到 `D:\AI_python\skills_backup\local\skill\firerpa\`。
- **上游更新时**：重取 `firerpa/SKILL.md` 会**覆盖掉本文件的本机内容**（§0 铁律、§2 环境实测、
  §3 接入、§5 的实测输出、§8.1 本机坑、§10 卸载…）。备份目录里有本文件的完整副本可盖回。
- **环境变了**（换模拟器 / 服务端升级 / 端口或目录变化）→ §2 与 §3 的实测值会过期：
  重跑 §3 的 7 步验收并更新 §2，再重新备份。

---

## Resources

- **CLI:** [scripts/firerpa.py](scripts/firerpa.py)
- **API:** [client/client.py](client/client.py)
- **Index:** [reference.md](references/reference.md)
- **官方文档全文:** [llms-full.txt](references/llms-full.txt)
- **官方站点:** https://device-farm.com/docs/zh/
- **上游仓库:** https://github.com/firerpa/lamda
