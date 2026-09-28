---
name: web-search-router
description: 联网检索自动路由 —— 按意图在 dsh web_search（modsearch 引擎）、x_search、read_page 与 donsetch_web_search/fetch/crawl 之间自动选工具；命中登录墙时自动调 donsetch login 弹出真实浏览器等用户登录后再继续。触发词：搜索、查一下、查资料、检索、找信息、搜一下、网页内容、抓取、爬取、被墙、需要登录的网站、登录后抓取、PDF 内容，或任何需要上网获取信息的任务。
---

# Web Search Router —— 联网检索自动路由

**用户不会、也不该手动指定工具名（比如 `donsetch_web_search`）。** 凡是上网获取信息的任务，
由你按下面的路由表**自动选工具**。遇到需要登录的站点，走「登录墙 SOP」：**弹出真实浏览器、等用户登录、再继续**。

## 0. 先判意图，再选工具

| 意图 | 工具 | 为什么 |
|---|---|---|
| 快问快答 / 普通关键词搜索（时效信息、新闻、一般查询） | `web_search`（被 modsearch 插件接管，走 Firecrawl keyless） | 快、省额度、保留 dsh 原生引用卡片 |
| 搜 X / Twitter 上的内容 | `x_search` | modsearch 专用 |
| 读单个网页正文 / 单页精读（可带问题聚焦） | `read_page`（普通站点）；反爬 / JS 壳 / PDF → `donsetch_web_fetch` | read_page 轻量；donsetch 能绕墙、能 OCR |
| 需要多引擎交叉验证、技术向检索、更多权威源 | `donsetch_web_search` | 10+ 引擎本地合并 + 语义重排，技术向更准 |
| 整站 URL 地图 / 同域爬取 | `donsetch_web_crawl` | 唯一爬虫（sitemap + 焦点排序 + 续传） |
| 页面被 Cloudflare / DataDome 等拦、需 JS 渲染、PDF（含扫描件） | `donsetch_web_fetch` | 本地无头浏览器 Solve-and-Bounce + PDF OCR |
| 命中 401 / 403 / 跳转登录 / 付费墙 | **先走下方「登录墙 SOP」** | 先登录、再抓取 |

**原则**：能用轻工具就不用重工具（省额度、省时间）；但**一旦轻工具明显不够（墙、JS 壳、PDF、要登录），立即切 donsetch，不要反复失败**。

## 1. 登录墙 SOP（用户的硬性要求：弹出网页、等登录、再继续）

触发信号：HTTP 401/403、跳转到 `/login`、正文提示"需要登录/订阅"、抓取结果为空但明显有内容、`read_page` / `web_search` 都拿不到正文。

1. **不要放弃，也不要伪造登录。** 用 **donsetch 插件的内置二进制**跑登录（本机已卸载全局 CLI，二进制由插件下载在缓存里）：

```powershell
# 定位插件下载的二进制（dsh web 重启后、首次使用 donsetch_* 工具时生成）
$d = Get-ChildItem "$env:USERPROFILE\.cache\donsetch" -Recurse -Filter donsetch.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $d) { Write-Host '二进制尚未下载：先重启 dsh web，调用一次 donsetch_status 后再试'; exit 1 }
& $d.FullName login <目标站点域名>
```

2. 该命令会在**用户桌面弹出一个真实浏览器窗口**（专用 profile）。**立即停下，明确告诉用户**：
   "已弹出屏幕上的浏览器窗口，请登录 `<域名>`；登录完成后告诉我，我继续抓取。" —— **等待用户回复，不要自作主张继续。**
3. 用户确认后，登录 cookie 已存入 donsetch 的 cookie vault，`donsetch_web_fetch` 对**同一域名**自动携带登录态。
4. 重试抓取：`donsetch_web_fetch`（url=该页面）。仍不行 → `donsetch login --status <域名>` 查会话状态，把结果如实报给用户。

补充：
- 登录态只覆盖你登录过的域名；凭据只由用户在浏览器里输入，**agent 不接触密码、不截图、不抓键盘**。
- 多个站点一次办：跑 `donsetch login`（不带域名）打开多标签，全登完按一次回车。

## 2. 失败降级

- `donsetch_web_search` 结果弱 / 超时 → 回退 `web_search`，反之亦然。
- **国外站点空结果 / 超时**：donsetch 是**本地出网**，daemon 由 dsh 启动、**不继承 shell 代理** ——
  先确认代理池已配（`<内置二进制> proxy add http://127.0.0.1:7890`，落在 `%LOCALAPPDATA%\donsetch\proxies.txt`，
  改完热生效、不用重启）；探测报 `dead no exit IP returned` 不代表代理不可用。
- **Cloudflare 交互式挑战**（报 `blocked … interactive captcha or challenge could not be solved automatically`
  或提示 "Use an Agent browser"）：donsetch 的自动绕过到此为止 —— **不要死循环重试**；
  改走本机 **`camoufox-reverse`**（反指纹浏览器 + MCP）打开该页，或如实告诉用户需要人工处理。
- `donsetch_web_crawl` 的 `mode="map"` 在无 sitemap 的站会返回空 URL 列表（不是故障）→ 要正文改用 `mode="full"`。
- donsetch 工具不可用（未重启 / 二进制缺失）→ 用 `web_search` / `read_page` 顶住并提醒用户重启 dsh web 后 donsetch 才可用。

## 3. 什么时候不要走本路由

- 只检索本地文件 / 代码库 → 用文件与代码工具，不要上网。
- 用户明确点名某个工具 → 听用户的。
- 逆向 / 渗透类目标 → 走 `reverse-skill-router` 的授权门禁，不归本路由。
