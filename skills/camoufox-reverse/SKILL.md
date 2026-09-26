---
name: camoufox-reverse
description: 本机已装好的 Camoufox 反指纹浏览器 + camoufox-reverse-mcp 逆向环境。当用户要求"用浏览器打开某站"、做 Web/JS 逆向、抓接口签名参数、Hook 函数、JSVMP/混淆分析、绕过 Cloudflare 或反爬、注入登录态、或提到 camoufox / Camoufox / 反指纹浏览器 / trace_property_access 时使用。包含环境位置、控制台入口、必做的预热步骤与已知坑。
---

# Camoufox 逆向环境（本机已配置）

## 位置与入口

| 东西 | 路径 |
|---|---|
| 工作区 | `D:\AI_python\camoufox`（独立 venv + 独立 CPython，不碰 Anaconda） |
| 给人用的控制台 | 桌面「Camoufox 逆向控制台」或 `D:\AI_python\camoufox\camoufox.cmd` |
| **完整说明书（出问题先看）** | `D:\AI_python\camoufox\使用说明.md` |
| MCP 工具 | 会话里以 `mcp__camoufox__*` 暴露（39 个，已在 `~\.dsh\profiles\web\cordis.patch.yml` 配好） |
| 登录态 | `D:\AI_python\camoufox\states\<站点>.json` |
| 自检 / 冒烟 | `bin\check_env.py`、`bin\mcp_smoke_test.py`（后者真跑 MCP 协议） |

## 开工前必做

1. **先跑 `mcp__camoufox__check_environment()`**，确认 `overall_ok` 与 active 引擎。
2. **如果 `launch_browser` 报 JSON-RPC 解析错误 / Invalid JSON**：说明 Camoufox 在下载默认插件
   （uBlock Origin）且把进度打到了 stdout，污染了 stdio 通道。
   让用户在控制台菜单 `[7]`（或跑 `bin\warmup.py`）**预热一次**，之后就好了。
   装机后没预热过的话，第一次启动必然踩这个。

## 项目工作区规范（一个逆向目标 = 一个网站目录）

### 命名：**必须以目标网站名开头**

项目目录名由**目标网站域名**规范化而来：

| 目标网站 | 目录名 |
|---|---|
| `stats.customs.gov.cn` | `stats_customs_gov_cn` |
| `www.example.com` | `example_com`（`www.` 可省） |
| `127.0.0.1:8080` | `127_0_0_1_8080` |

规则：去掉协议与路径；`.` 和 `:` 换成 `_`；全小写。

**不允许**只用任务名 —— `customs_reverse`、`spider`、`project1` 这类名字看不出
是哪个站，隔几天自己都认不出来，多个站还会互相撞名。

两种组织方式，按需选：

- **首选**：一个网站一个目录，站内的逆向 / 取数 / 分析 / 看板用子目录
  （`data\`、`output\`、`debug\`）区分。
- **同一站要拆多个目录时**：用 `<网站名>_<阶段>`，例如
  `stats_customs_gov_cn_reverse`（逆向）、`stats_customs_gov_cn_market`（取数分析）。
  阶段后缀只为区分和排序，**网站名必须排在最前面**。

反例：`customs_reverse` + `customs_market` —— "customs" 太泛看不出是哪个站，
同一个目标散成两处，跨项目引用还得靠 `sys.path` 指回去。

### 位置：**每次建项目之前都要问用户**

不同机器的目录布局不一样，**不要默认工作区根**（本机恰好是
`D:\AI_python\camoufox`，换个环境就不是了）。
建目录之前必须问一句「**项目建到哪个目录**」，拿到路径再动手；
用户已有惯例的，确认一次即可。

### 结构

```
<用户指定目录>\<网站名>\
    <客户端 / 取数脚本>
    操作说明.md      以后逆向这个站读这一份（参数、state 维护、故障排查）
    README.md        分析报告（原理、证据、结论）
    state*.json      会话状态（敏感，勿外传）
    data\            抓到的数据
    output\          分析结果、可视化看板
    debug\           诊断脚本（留作证据）
```

### 收尾清理

**删除与清理一律按 `dev-hygiene` skill 执行**（走 Windows 回收站、禁止 del / rmdir / Remove-Item 等硬删、
豁免清单与"删完报告"的要求都在那份 skill 里），本节只保留逆向场景的落点：

逆向收尾时删掉只服务于定位过程、没有复用价值的东西 —— 一次性探测脚本、
失败实验的中间产物、重复的数据副本、`__pycache__`；
有证据价值的诊断脚本移进 `debug\` 保留。
交付目录最后只剩四类：**可直接用的脚本 + 数据成果 + 分析报告 + 必需的 state**。

> 命名与分目录是为了避免多个项目混在一起：按任务起名会让同一个站散成几处，
> 不同目标的 state 会重名、脚本互相覆盖、样本 JS 分不清属于哪个站，翻旧账时找不到东西。

## 引擎选择

| 场景 | 用法 |
|---|---|
| 常规逆向 | `launch_browser()` —— 官方 `152.0.4-beta.30`（active），headless/有头都正常 |
| 需要引擎层证据（谁读了 Cookie/Canvas/localStorage） | `launch_browser(browser_version="whitenightshadow/152.0.4-beta.30-reverse.5", enable_trace=True)` 然后用 `trace_property_access` |

定制版与 active **version/build 必须一致**（都是 `152.0.4-beta.30`，已满足）。开 tracing 会临时关闭 content sandbox，只做短时分析。

## 典型调用顺序

**找接口签名参数**
```
launch_browser() → inject_hook_preset("xhr") → inject_hook_preset("crypto")
→ navigate(url) → （必要时 import 登录态）→ 触发请求
→ list_network_requests(method="POST") → get_request_initiator(request_id=N)
→ search_code("sign") → hook_function(..., mode="trace", world="main", persistent=True)
→ reload() → get_trace_data(...)
```

**JSVMP / 混淆**
```
launch_browser() → network_capture(action="start") → navigate(url)
→ list_network_requests(resource_type="script")
→ instrumentation(action="install", url_pattern="**/vmp*.js", mode="ast")
→ instrumentation(action="reload") → instrumentation(action="log", type_filter="tap_get")
→ compare_env()
```
签名型反爬（瑞数 / AK）**只用** `instrumentation(install)`；行为型（TK JSVMP / 极验）用
`hook_jsvmp_interpreter(mode="proxy")`。

## 登录态（扫码 / 短信站）

MCP **没有**持久 profile：`launch_browser` 每次都是全新随机指纹，
跨会话登录只能靠 `export_state` / `import_state`：

1. **人工登录**要用户自己操作 → 让他用控制台菜单 `[2]`（普通）或 `[3]`（持久 profile，含 IndexedDB），
   产出 `states\<站点>.json`。AI 无法代扫码。
2. 之后每次：`launch_browser()` → `import_state(state_path="D:\\AI_python\\camoufox\\states\\<站点>.json")` → `navigate(...)`。
   **每次 launch 之后都要重新 import**（没有自动加载）。
3. 关闭浏览器前再 `export_state()` 一次，否则续期的 token 会丢。
4. 若站点把登录放在 IndexedDB，`import_state` 会掉登录 → 改用菜单 `[3]` 的持久 profile。

## 坑（踩过或上游已知）

- 每次 `launch_browser` **指纹随机**，MCP 不能固定；同一 cookie 换指纹更易触发二次验证。
- `export/import_state` 只覆盖 **cookies + localStorage**（无 IndexedDB / sessionStorage）。
- `take_screenshot` 返回 **base64 文本**，不一定能"看见"；要肉眼确认让用户看本地窗口。
- 不要把 `playwright` 升到 1.63+（camoufox 上界 `<1.63`），也不要跑 `playwright install`。
- `camoufox fetch` 会撞 GitHub API 未认证限流（60/h）；装引擎用
  `bin\install-camoufox-browser.py`（直连 release）。
- 别在浏览器运行时清理 trace 目录（Windows 文件锁）。
- 浏览器进程残留时：`Get-Process camoufox | Stop-Process -Force`。

## 验证环境是否完好

```powershell
D:\AI_python\camoufox\.venv\Scripts\python.exe D:\AI_python\camoufox\bin\mcp_smoke_test.py --browser
```

---

## 重建 / 迁移（本 skill 自包含，**不要备份大文件**）

本 skill 目录本身就是这套环境的**轻量备份（约 50 KB）**：

| 路径 | 内容 |
|---|---|
| `scripts\` | 全部自制脚本：`console.ps1`、`check_env.py`、`warmup.py`、`login_session.py`、`mcp_smoke_test.py`、`install-camoufox-browser.py`、`camoufox.cmd` |
| `scripts\restore.ps1` | **一键重建**：建缓存联接 → venv → camoufox → clone MCP → 官方引擎 → 定制版引擎 → 预热 → 冒烟测试 → 打印 DSH 接入片段 |
| `references\使用说明.md` | 完整说明书副本 |
| `references\重建配方.md` | 组件来源、固定 sha256、手动步骤、DSH 接入片段、桌面快捷方式命令 |

**不备份**（都有 release/PyPI 来源，现场重下，合计约 2.2 GB）：
`.venv`（271 MB）、uv 托管的 CPython（61 MB）、浏览器引擎 1.89 GB、MCP 源码（1.6 MB，git 可 clone）。
**永不备份**：`states\*.json` 与 `profiles\` —— 里面是可直接登录的凭据，迁移后重新扫码登录一次即可。

换机器 / 误删后重建：

```powershell
pwsh -File scripts\restore.ps1 -Root D:\AI_python\camoufox
# 只想先跑通 MCP、暂不下载引擎：
pwsh -File scripts\restore.ps1 -SkipEngines
```

> 升级引擎或换版本时，tag / 资产名 / sha256 要同步改**三处**：
> `references\重建配方.md`、`scripts\restore.ps1` 的参数、`使用说明.md` §8。
