# donsetch（donsetch-dsh）—— DSH 插件安装配方

| 项 | 值 |
|---|---|
| 类型 | **DSH 插件**（bundle，不是 skill）+ 可选全局 CLI |
| 优先级 | P2 独立类 |
| 来源（插件壳） | https://github.com/dondai44423/donsetch-dsh —— 安装 spec `github:dondai44423/donsetch-dsh` |
| 来源（本体） | https://github.com/dondai44423/donsetch （Rust 单二进制，AGPL-3.0，发 npm `donsetch` + GitHub Releases） |
| 本机安装日期 | 2026-09-28 |
| 本机实测 | 插件 `dsh plugin add` 5.2 秒装完、未触发 allowBuilds；全局 CLI v4.3.6（ocr/rerank features）；`donsetch doctor` 全绿（经本机内网代理 127.0.0.1:7890） |
| 用途 | 给 DSH agent 提供**本地自研**的网页抓取 / 多引擎搜索 / 爬虫 / PDF OCR / 截图 —— 无需 API key、无账号，自带 Chrome 级 TLS 指纹与反机器人绕过 |

---

## 它做什么

DonSeTch = **The web, for AI agents**。Rust 一个二进制，从零实现（自研 HTTP/2、BoringSSL 驱动 Chrome 真实 TLS 指纹、
自有 HTML→markdown 提取、PDFium 解析 + 像素融合、无头浏览器 Solve-and-Bounce 绕 Cloudflare/DataDome、keyless 搜索聚合 + 本地 ONNX 语义重排）。
本体有 4 个 MCP 工具（`web_fetch` / `web_search` / `web_crawl` / `web_screenshot`）+ 一套 CLI。

donsetch-dsh 是把本体接进 DSH 的一级插件：进程内注册为**原生工具**（非 `mcp__*` 前缀）：

- `donsetch_web_fetch` —— 任意 URL → 干净 markdown；遇反爬自动升级无头浏览器解决并回蹦 cookie；`focus`/`toc`/`section` 省 token；PDF 自动 OCR
- `donsetch_web_search` —— keyless 多引擎（Bing 族/DuckDuckGo/Brave/Mojeek/Google + GitHub/Wikipedia/arXiv 等垂直源）本地合并重排；BYOK 可选（Exa/Tavily/Serper/…）
- `donsetch_web_crawl` —— 同域爬虫，sitemap + 焦点排序 + 续传 token
- `donsetch_status` —— 自诊断（daemon 状态 / 二进制版本 / doctor 输出），插件降级时 agent 自动调它
- 首次启动插件自动从 GitHub Releases 下载本平台二进制并 SHA256 校验；之后按 24h 节流自动升级（`autoUpdate` 可关）

（本体还有 `web_screenshot`，插件壳官方只暴露上述 4 个；另可用全局 CLI 补足截图等能力。）

## 安装

前置：**pnpm**（`dsh plugin` 是它的转发器，本机 12.4.1 ✓）、Node ≥ 22.19；装完**必联网一次**（首次启动下二进制）。

```powershell
# ① DSH 原生插件（agent 用）
dsh plugin --profile web add github:dondai44423/donsetch-dsh

# ② 可选：全局 CLI（命令行直接 fetch/search/crawl + doctor 诊断），本体同一份二进制
npm install -g donsetch
```

- 本机实测：① 5.2 秒装完（git 依赖但 dist/ 已提交，**无 prepare 构建，未触发 `allowBuilds`**，`pnpm-workspace.yaml` 零改动）；
  ② npm 报 `allow-scripts` 警告但二进制已落位（`<npm 根>\node_modules\donsetch\binaries\donsetch.exe`），无需 approve。
- 装完 `~/.dsh/profiles/web/package.json` 应为：`dependencies` 加 `"@dsh-external/donsetch": "github:dondai44423/donsetch-dsh"`，
  `dsh.profile.bundles` 末尾加 `"@dsh-external/donsetch"`（由 dsh 自动 reconcile）。

## 验证

```powershell
donsetch doctor                          # 快速全扫（二进制/网络/TLS/浏览器/搜索健康……）
donsetch --version
dsh --profile web --dump-config | Select-String 'donsetch'
```

本机 `doctor` 全绿：二进制 v4.3.6（19MB）、egress 经 env 代理 127.0.0.1:7890、JA4 = Chrome 指纹、系统 Chromium 已发现
（`C:\Users\y\AppData\Local\ms-playwright\chromium-1187\chrome-win\chrome.exe`）、OCR/rerank 模型首次用才下载。

## 必须重启 DSH

bundle 插件在 profile 启动时组合，**运行中的进程不热加载** —— `dsh web` 重启后会话里才出现 `donsetch_*` 工具。
重启后可用提示词验证：`Use donsetch_web_search to find …`，或直接调 `donsetch_status`。

## 配置（可选，不配即用）

- 插件选项走 bundle patch（`$DSH_HOME/profiles/web/cordis.patch.yml` 或 `$DSH_HOME/cordis.patch.yml` 覆盖）：
  `toolPrefix`（默认 `donsetch`）、`channel`、`autoUpdate`、`callTimeoutMs` 等；环境变量 `DONSETCH_DSH_PREFIX`、`DONSETCH_BIN` 等。
- 本体的键 / 代理 / 登录会话沿用标准 CLI 配置：
  ```powershell
  donsetch keys add exa sk-exa-…          # BYOK 搜索（可选，默认 keyless）
  donsetch keys default local
  donsetch proxy add <url>                # 搜索/爬虫代理池（重式使用建议加，防 IP 限流）
  donsetch login x.com                    # 登录墙后站点（打开你自己的浏览器、自己输凭据，凭据不进 DonSeTch）
  ```
- 首次 OCR/rerank 会下载模型（~24MB rerank + ~37MB OCR，缓存永久）。

## 卸载

```powershell
dsh plugin --profile web remove @dsh-external/donsetch   # 插件
npm uninstall -g donsetch                                 # 全局 CLI（可选）
```

然后重启 dsh。二进制缓存在 `~/.cache/donsetch/`（含 dsh 版本化目录），可手动清。

## 维护提醒

- 升级 = 重跑 `dsh plugin --profile web add github:dondai44423/donsetch-dsh`（spec 不锁版本，取最新）；二进制本体自动更新。
- 插件壳与本体是两套版本线：插件升级不影响二进制，二进制在插件内自动升级。
- 涉及关键配置/能力变化时同步更新本文件与 `INSTALL.md` 小节。
- **不备份**：`node_modules`、插件源码、二进制本体与模型缓存（均可重下）。
