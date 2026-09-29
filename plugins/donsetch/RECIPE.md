# donsetch（donsetch-dsh）—— DSH 插件安装配方

> **状态：已于 2026-09-28 卸载（用户评估后弃用）**。重新启用：`dsh plugin --profile web add github:dondai44423/donsetch-dsh`
> 装回 profile，按下方「本机必做」配好代理池；二进制缓存会自动重建。本配方**仅作恢复参考**。

| 项 | 值 |
|---|---|
| 类型 | **DSH 插件**（bundle，不是 skill） |
| 优先级 | P2 独立类 |
| 来源（插件壳） | https://github.com/dondai44423/donsetch-dsh —— 安装 spec `github:dondai44423/donsetch-dsh` |
| 来源（本体） | https://github.com/dondai44423/donsetch （Rust 单二进制，AGPL-3.0，发 npm `donsetch` + GitHub Releases） |
| 本机安装日期 | 2026-09-28 |
| 本机变更 | 2026-09-28 安装同日先应用户要求卸载全局 CLI；随后**用户弃用，当日整体卸载**：`dsh plugin --profile web remove @dsh-external/donsetch`，回收站清理 `~\.cache\donsetch`（38.9MB）+ `%LOCALAPPDATA%\donsetch`（48.3MB），daemon 进程已终止 |
| 用途 | 给 DSH agent 提供**本地自研**的网页抓取 / 多引擎搜索 / 爬虫 / PDF OCR —— 零 API key、零账号，自带 Chrome 级 TLS 指纹与反机器人绕过；配合 `web-search-router` skill 自动路由 |

---

## 它做什么

DonSeTch = **The web, for AI agents**。Rust 一个二进制，从零实现（自研 HTTP/2、BoringSSL 驱动 Chrome 真实 TLS 指纹、
自有 HTML→markdown 提取、PDFium 解析 + 像素融合、无头浏览器 Solve-and-Bounce 绕 Cloudflare/DataDome、keyless 搜索聚合 + 本地 ONNX 语义重排）。
本体有 4 个 MCP 工具（`web_fetch` / `web_search` / `web_crawl` / `web_screenshot`）。

donsetch-dsh 把本体接进 DSH 为**进程内原生工具**（非 `mcp__*` 前缀）：

- `donsetch_web_fetch` —— URL → 干净 markdown；反爬自动升级无头浏览器 Solve-and-Bounce；`focus`/`toc`/`section` 省 token；PDF 自动 OCR
- `donsetch_web_search` —— keyless 多引擎（Bing 族/DuckDuckGo/Brave/Mojeek/Google + GitHub/Wikipedia/arXiv 等垂直源）本地合并重排；BYOK 可选
- `donsetch_web_crawl` —— 同域爬虫（sitemap + 焦点排序 + 续传 token + 节奏控制）
- `donsetch_status` —— 自诊断（daemon / 二进制版本 / doctor 输出），插件降级时 agent 自动调它
- 首次启动插件自动从 GitHub Releases 下载本平台二进制并 SHA256 校验；24h 节流自动升级（`autoUpdate` 可关）

> **本机（2026-09-28 起）没有全局 CLI**：命令行验证 / doctor / login / keys 等都用插件内置二进制
> （见下方「用内置二进制跑 CLI 操作」）。截图工具 `web_screenshot` 插件壳未暴露，CLI 又已卸载 → 本机不可用。

## 安装

前置：**pnpm**、Node ≥ 22.19；装完**首次启动必须联网**（下二进制）。

```powershell
dsh plugin --profile web add github:dondai44423/donsetch-dsh
```

- git 依赖但 `dist/` 已提交 → **没有 prepare 构建，不触发 `allowBuilds`**（本机实测 5.2 秒装完，`pnpm-workspace.yaml` 零改动）。
- 装完 `~/.dsh/profiles/web/package.json` 应为：`dependencies` 加 `"@dsh-external/donsetch": "github:dondai44423/donsetch-dsh"`，
  `dsh.profile.bundles` 末尾加 `"@dsh-external/donsetch"`（由 dsh 自动 reconcile）。

## 用内置二进制跑 CLI 操作（本机无全局 CLI）

插件下载的二进制在缓存里（dsh web 重启后首次使用 `donsetch_*` 工具时生成）。定位与调用：

```powershell
$d = Get-ChildItem "$env:USERPROFILE\.cache\donsetch" -Recurse -Filter donsetch.exe -ErrorAction SilentlyContinue | Select-Object -First 1
& $d.FullName doctor            # 健康检查
& $d.FullName login <域名>       # 登录墙站点：弹出真实浏览器等用户登录（cookie 入 vault，fetch 自动带）
& $d.FullName login --status <域名>
& $d.FullName keys add <provider> <key>   # BYOK（可选，默认 keyless）
```

## 代理 / 受限网络下的首次安装（本机坑，2026-09-28 实测）

插件的二进制下载器走 `node:https.request`（`dist/binary.js` 的 `httpGet`），**不读** `HTTP_PROXY` / `HTTPS_PROXY` /
`NODE_USE_ENV_PROXY`（Node 24 的 `NODE_USE_ENV_PROXY=1` 只作用于 `fetch` / undici）。**需要代理才能出网的机器，
插件首次 boot 必然下载失败**：

```
state: could not reach https://github.com/dondai44423/donsetch/releases/download (network down?) while installing donsetch v4.3.6
registered tools (0): (none)
```

- 该失败**被插件缓存**，运行中不重试（`donsetch_status` 一直回同一条旧错）→ **只能重启 dsh web**。
- 绕法（本机实测可行）：用能走代理的 `fetch` 下载 release tarball + 官方 `.sha256` 校验，解包后
  **整目录**落位到 `%USERPROFILE%\.cache\donsetch\dsh\bin\<version>\` —— 这是 `resolveBinary` 的**第 2 优先级**
  （扫该目录，取目录名可解析 semver 里最新的一个），命中就不再下载。
- ⚠️ **必须整目录**：`donsetch.exe` + `onnxruntime.dll` + `pdfium.dll`。
  **只放 exe 会启动即退出、无任何输出、exit 1**（本机踩过，别重复）。
- 目录名用纯 semver（如 `4.3.7`）。插件 pinned 是 `v4.3.6`，但 resolve 取"已装最新"，放更新的版本即可；
  autoUpdate 检查后也会跳过。
- 重启前预检（很有用）：直接对该二进制跑 stdio MCP —— `initialize` 应回 `donsetch 4.3.7`，
  `tools/list` 应回 4 个工具（`web_fetch` / `web_search` / `web_crawl` / `web_screenshot`）。
- 顺带一条观察：本机 `node:https.request` 直连 `api.github.com` 返回 **403**（说明**我的 shell 环境**里 https 能到达 GitHub，
  只是 API 拒绝无 UA 的 HEAD）；但 **dsh web 进程的环境未必相同** —— 不必在这上面排查，手动放二进制最快。

## 验证

- 插件层：`dsh --profile web --dump-config | Select-String 'donsetch'`；
- 运行期：**重启 dsh web** 后会话出现 `donsetch_*` 工具，先调 `donsetch_status`；
- 本机安装时 `doctor` 实测全绿（二进制 v4.3.6 / egress 经 env 代理 127.0.0.1:7890 / JA4 = Chrome 指纹 /
  系统 Chromium 已发现 / OCR+rerank 模型首次使用才下载）。

## 必须重启 DSH

bundle 插件在 profile 启动时组合，**运行中的进程不热加载** —— `dsh web` 重启后 `donsetch_*` 工具才出现。

## 登录墙（本机标准流程，用户硬性要求）

见 `web-search-router` skill 的「登录墙 SOP」：命中 401/403/跳转登录/付费墙 → 内置二进制跑 `donsetch login <域名>`
→ **弹出真实浏览器，停下告知用户登录、等用户确认后再继续** → cookie 入 vault → `donsetch_web_fetch` 自动带登录态重试。
凭据只由用户在浏览器里输入，agent 不接触密码、不截图、不抓键盘。

## 本机必做：给 daemon 配代理池（国外站，2026-09-28 实测）

donsetch daemon 由 dsh 进程 spawn，**不继承你 shell 里的 `HTTPS_PROXY`** —— 于是国外站直连：超时、空结果、
搜索后端大面积不可用。修法（**不需要重启**，插件监视配置后热切 daemon）：

```powershell
$d = Get-ChildItem "$env:USERPROFILE\.cache\donsetch" -Recurse -Filter donsetch.exe | Select-Object -First 1
& $d.FullName proxy add http://127.0.0.1:7890      # 可加 --no-check 跳过探测
& $d.FullName proxy list                            # 配置落在 %LOCALAPPDATA%\donsetch\proxies.txt
```

⚠️ `proxy add` / `proxy check` 可能报 **`dead no exit IP returned`** —— 那是它的探测端点被 Clash 规则直连所致，
**不代表代理不可用**：本机加完后实测 `donsetch_web_fetch` 抓 `https://news.ycombinator.com` 成功、
`crawl` 用 `full` 模式抓到 `docs.python.org` 正文。要跳过探测就加 `--no-check`。

**能力边界（诚实记录）**：Cloudflare **交互式挑战**（Turnstile 等）解不了，报
`blocked … interactive captcha or challenge could not be solved automatically … Use an Agent browser` ——
这时改走本机 `camoufox-reverse`（反指纹浏览器 MCP）或让用户人工处理，**别死循环重试**。
另：`crawl` 的 `mode="map"` 在没有 sitemap 的站会返回空 URL 列表（不是故障），要正文用 `mode="full"`。

## 配置（可选，不配即用）

- 插件选项走 bundle patch（`toolPrefix` / `channel` / `autoUpdate` / `callTimeoutMs` 等）；
  环境变量 `DONSETCH_DSH_PREFIX`、`DONSETCH_BIN`（可指向本地二进制）等。
- 本体键 / 代理 / 登录会话走内置二进制的 `keys` / `proxy` / `login` 子命令。

## 卸载

```powershell
dsh plugin --profile web remove @dsh-external/donsetch
```

然后重启 dsh。二进制缓存 `~/.cache/donsetch/` 可手动清。

## 维护提醒

- 升级 = 重跑 `dsh plugin --profile web add github:dondai44423/donsetch-dsh`（spec 不锁版本，取最新）；二进制本体自动更新。
- 插件壳与本体是两套版本线：插件升级不影响二进制，二进制在插件内自动升级。
- 涉及关键配置/能力变化时同步更新本文件、`INSTALL.md` 小节与 `web-search-router` skill。
- **不备份**：`node_modules`、插件源码、二进制本体与模型缓存（均可重下）。
