---
name: wmpf-miniapp-reverse
description: 本机已装好的 WMPFDebugger 微信小程序逆向环境（Frida 注入 WeChatAppEx + CDP 代理 + 浏览器内置 DevTools）。当用户要求调试或逆向微信小程序、抓小程序接口与签名参数、Hook 小程序函数、分析小程序 JS、定位加密逻辑、用 DevTools 调试小程序，或提到 WMPF / WeChatAppEx / 小程序调试 / devtools:// / wxapkg 时使用。含环境位置、三步启动流程（顺序敏感）、CDP 调试手法、WMPF 版本适配与已知坑。
---

# 微信小程序逆向（WMPFDebugger + CDP，本机已配置）

## 位置与入口

| 东西 | 路径 |
|---|---|
| 工具目录 | `D:\AI_python\reverse\vmpfdebugger`（上游 [evi0s/WMPFDebugger](https://github.com/evi0s/WMPFDebugger)，GPLv2） |
| 启动调试器 | `.\start-debugger.ps1` |
| 打开调试前端 | `.\open-devtools.ps1` |
| **完整交接文档（出问题先看）** | `D:\AI_python\reverse\vmpfdebugger\HANDOVER.md` |
| 本 skill 的脚本备份 | `scripts\`：`restore.ps1`（一键重建）、`probe-cdp.js`（链路排障）、两个启动脚本 |
| 重建配方 / 详细说明 | `references\重建配方.md`、`references\使用说明.md` |

## 原理（一句话）

Frida 注入 `WeChatAppEx.exe`，patch 掉小程序调试协议（私有 protobuf）里的 CDP 过滤器与条件判断，
让小程序把调试连接发到本机额外端口 **9421**；工具把该私有协议翻译成标准 CDP，在 **62000** 上
暴露给浏览器的内置 DevTools 前端。**所以调试手段就是标准 DevTools** —— Sources / Console /
Network / Debugger 都能用。

## 适用与边界

- 目标：本机微信 4.x 的 WMPF 小程序（进程名 `WeChatAppEx.exe`）。
- 本机实测可用版本：**WMPF 16467**（微信 4.x，`D:\Program Files\Tencent\Weixin`）。
- 只调试**你有权调试**的小程序（自己的、或已获授权的）。涉及第三方目标时先走
  `reverse-skill-router` 的授权门禁（case-init），不要用它破解他人小程序、绕过付费或风控。
- 上游 GPLv2：改动或分发衍生版本必须保留版权与贡献者署名。
- `src\third-party\` 里的协议实现提取自微信开发者工具，版权属腾讯。

## 开工前必做

1. **查 WMPF 版本**：任务管理器 → `WeChatAppEx` 进程 → 右键「打开文件所在的位置」，路径里
   `RadiumWMPF` 与 `extracted` 之间的数字就是版本（本机为 `…\RadiumWMPF\16467\extracted\runtime\…`）。
   对照工具里的 `frida\config\win32\addresses.<版本>.json` —— 文件不存在就会报
   `[frida] version config not found: <版本>`。
2. **关掉全局代理 / TUN**（Yakit、Clash 全局模式等）：会出现
   `Invalid WebSocket frame: invalid opcode 0`，小程序闪退。规则模式一般没事。
3. **顺序**：先启动调试器 → 再（重新）打开小程序 → 最后开 DevTools。颠倒会让小程序闪退。
   注入发生之后才打开的小程序才算数；**已经在跑的小程序必须关掉重开**。

## 标准流程（三步，顺序不能反）

```powershell
cd D:\AI_python\reverse\vmpfdebugger

# ① 启动调试器（保持窗口开着；停止用 Ctrl+C）
.\start-debugger.ps1
#   可选：-DebugMain（打印 CDP 消息流，排障用）、-DebugFrida、-CdpPort 63000、-AutoDetect

# ② 在微信里打开（或关掉重开）目标小程序，等界面完全加载

# ③ 另开一个 pwsh 窗口，打开调试前端
.\open-devtools.ps1
#   链接自动进剪贴板并弹 Edge 新窗口 → Ctrl+L → Ctrl+V → 回车
#   或手工在浏览器地址栏粘贴：
#   devtools://devtools/bundled/inspector.html?ws=127.0.0.1:62000
```

**`devtools://` 只能手工粘贴**：把它当命令行参数传给浏览器会被忽略（实测 Chrome for Testing 148
直接落到 `chrome://newtab/`）。这就是 `open-devtools.ps1` 只做「复制 + 开窗口 + 提示」的原因。

## 验证点（看日志，别靠猜）

| 调试器窗口出现 | 含义 |
|---|---|
| `[server] debug server running on ws://localhost:9421` | 等小程序回连 |
| `[frida] script loaded, WMPF version: 16467, pid: <pid>` | 注入成功（attach 到 WMPF 主进程） |
| `[miniapp] miniapp client connected` | 小程序已连上 —— **必须先看到这句**，再开第 ③ 步 |
| `[cdp] CDP client connected` | 浏览器 DevTools 前端已连上 |

第 ③ 步快速检查链路（不用看浏览器）：

```powershell
node $DSH_HOME\skills\wmpf-miniapp-reverse\scripts\probe-cdp.js
# 期望：RECEIVED 若干条消息，其中有对 Runtime.enable 的 {"id":900001,"result":{}} 响应
# 没有响应 = 小程序没连上或没在运行
```

## 调试前端里能做什么

| 面板 | 小程序场景下的情况 |
|---|---|
| **Sources** | 小程序 JS（appservice 代码）都在这里，可下断点、Pretty print 压缩代码 |
| **Console** | 在小程序运行时直接求值；断点命中后可读写作用域变量 |
| **Network** | 小程序发起的请求（**内嵌 WebView 的请求看不到**，那是独立进程） |
| **Debugger / Call Stack** | 断点、条件断点、XHR/fetch 断点、事件监听断点 |
| Elements | **基本是空的**：小程序不是 DOM 环境，别在这里找东西 |

## 常用逆向手法

1. **定位接口与参数**：Network 面板找到目标请求 → 看 Payload 与 Initiator → 在 Sources 里
   对发起处下断点，复现操作后读调用栈。
2. **抓签名 / 加密**：Sources 里全局搜索 `sign`、`encrypt`、`md5`、`timestamp`、`nonce` 等关键词
   → 下断点 → 单步或跳到调用栈上层读入参。
3. **运行时取值**：Console 里直接算；或断点命中后在 Console 访问当前作用域变量。
4. **Hook 目标函数**：Console 里保存原函数再包一层，例如
   ```js
   const _f = SomeObj.target; SomeObj.target = function(...a){ console.log('args', a); return _f.apply(this, a); };
   ```
5. **压缩代码**：Sources 左下角 `{}`（Pretty print）格式化后再搜索/断点。

## 排障速查

| 现象 | 处理 |
|---|---|
| DevTools 页面空白 | 前端抢在小程序连上之前发了初始化命令，命令被丢弃。**在 DevTools 页面按 `F5` 刷新一次**；确认日志里已有 `miniapp client connected` |
| 小程序闪退 | 顺序错了（必须"先调试器→再小程序→最后 DevTools"）；或开了全局代理/TUN |
| `version config not found: XXXXX` | 微信升级带来未适配的 WMPF 版本 → 试 `-AutoDetect`（Win x64，beta）、等上游适配、或按上游 `ADAPTATION.md` 自己找偏移量 |
| attach 失败 / `Cannot read properties of undefined (reading 'parameters')` | 权限不足 → 用管理员身份的 pwsh 7 重跑 `start-debugger.ps1`（本机普通权限实测可用，多数情况不需要） |
| 启动成功但 Network 没流量 | 小程序内嵌 WebView 是独立进程，走上游 `EXTENSION.md` 的方案 |
| 端口被占用 | 上次的调试器没停干净：`Get-CimInstance Win32_Process -Filter "Name='node.exe'" \| Where-Object CommandLine -match 'src[\\/]index\.ts'` 找到后 `Stop-Process` |
| 小程序一直加载中 | 先关调试器 → 打开小程序让它正常加载一次 → 再按三步重来 |

## 与其他 skill 的配合

- **WebView / 公众号 H5 里的页面** → 用 `camoufox-reverse`（浏览器侧逆向、Hook、JSVMP）。
- **需要二进制 / APK / 更深层分析**，或目标授权流程 → 走 `reverse-skill-router` 的路由与 case-init 门禁。
- **删除、清理、HANDOVER 文档** → 按 `dev-hygiene`（回收站删除、pwsh 7、每项目一份 `HANDOVER.md`）。

### 项目工作区规范

沿用 `camoufox-reverse` 的规则：一个目标一个目录、**建目录之前先问用户位置**、目录名以目标开头。
小程序没有域名，用**小程序名或 AppID** 规范化（AppID 形如 `wx1234567890abcdef` 原样小写；
中文名用其拼音或直接问用户偏好），例如 `wx1234567890abcdef_reverse`。站内产物用
`data\`、`output\`、`debug\` 分目录；一次性探测脚本收尾时清掉，有证据价值的进 `debug\`。

## 包文件（wxapkg）说明

本 skill **只覆盖运行时调试**，不含小程序包（`.wxapkg`）的离线解密/解包：那需要另外的工具链，
本机未安装。确实需要离线解包时**先问用户**再评估装什么，不要凭空猜步骤。

---

## 重建 / 迁移（本 skill 自包含）

本 skill 目录是这套环境的轻量备份（约 30 KB）：

| 路径 | 内容 |
|---|---|
| `scripts\restore.ps1` | **一键重建**：clone 仓库 → 装依赖 → 落位两个启动脚本 → 类型检查 → frida 自检 |
| `scripts\start-debugger.ps1`、`scripts\open-debugger.ps1` | 启动脚本的权威副本（带 `-Root` 参数，可直接从 skill 目录调用） |
| `scripts\probe-cdp.js` | 链路排障探针 |
| `references\重建配方.md` | 仓库来源、依赖与版本、代理要求、分步命令、验证、WMPF 适配 |
| `references\使用说明.md` | 完整说明书（流程、CDP 手法、日志解读、FAQ 摘要） |

**不备份**：`node_modules\`（148.5 MB，其中 frida 预编译二进制 115 MB，装一次要下 GitHub
release、**必须带代理**）、`screenshots\`（上游自带的说明图，约 12 MB）。

换机器 / 误删后重建：

```powershell
pwsh -File scripts\restore.ps1 -Root D:\AI_python\reverse\vmpfdebugger `
     -Proxy http://127.0.0.1:7890
```

> **维护提醒**：`$Root` 下的两个启动脚本是"活"的，本 skill 的 `scripts\` 是备份副本。
> 改了任一处要**同步另一处**，并重新整份复制到 `local\skill\wmpf-miniapp-reverse\`、
> 在 `SKILLS.md` 追加一行日志（属「已记账 skill 被修改」）。上游仓库更新用 `git pull`。
