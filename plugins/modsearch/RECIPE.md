# modsearch —— DSH 插件安装配方

| 项 | 值 |
|---|---|
| 类型 | **DSH 插件**（原生 bundle，不是 skill） |
| 优先级 | P2 独立类 |
| 来源 | https://github.com/liustack/modsearch · npm `@liustack/modsearch` |
| 锁定的版本 | **5.10.3**（必须写死，理由见下） |
| 本机安装日期 | 2026-09-13（5.10.2）；2026-09-16 升级到 5.10.3 |
| 本机实测 | 5.10.2：dump-config 组合 ✅ / `doctor` ✅ / 真实搜索 ✅；5.10.3：升级后 dump-config 组合 ✅ |
| 用途 | 给不能联网的模型补上 web 搜索、X 搜索、单页抓取；免费、免注册、免 API key |

---

## 它做什么

dsh 内置的 `web_search` 在 API 侧没有真正的联网搜索能力。这个 bundle 贡献两个 patch：

1. 把 dsh web seam 的 `searchProvider` 指向 `modsearch`；
2. 把包根挂载为 `modsearch` 插件。

装完后：内置 `web_search` 改走 ModSearch 引擎链（**保留 dsh 原生引用卡片**），并新增两个工具
`x_search`（X/Twitter，需要 Grok Build）与 `read_page`（单页精读，可带问题聚焦）。
默认引擎 = **Firecrawl keyless**：每月 1000 免费额度、免注册免 key，装上即用。

> 副作用要记住：它**替换了所有会话的 web_search provider**。

## 安装

前置：**Node ≥ 22.13**（`doctor` 会检查；本机 Node 24 ✓）、pnpm（`dsh plugin` 是它的转发器，本机 12.4.1 ✓）。

```powershell
dsh plugin --profile web add '@liustack/modsearch@5.10.3'
```

- **版本必须写死**：pnpm 的 `minimumReleaseAge` 会把 `@latest` 拦回较旧的版本。
  升级时换版本号，并同步本文件与 `INSTALL.md` 小节。
- 本机实测：**4.2 秒**装完，**没有**触发 pnpm 的 `allowBuilds` 拦截（npm 包，不是 git prepare 依赖）。
- **升级实测（2026-09-16，5.10.2 → 5.10.3，1.9 秒）**：pnpm 会自动往
  `~/.dsh/profiles/web/pnpm-workspace.yaml` 追加一条
  `minimumReleaseAgeExclude: ['@liustack/modsearch@5.10.3']`。这是 pnpm 对"版本比
  `minimumReleaseAge` 新"的正常放行记录，**不是** `allowBuilds` 构建拦截，无需手工处理；
  新环境若被 pnpm 拦版本，可照此手工补同一把键再重跑。
  本次升级后 `pnpm-workspace.yaml` 相对升级前**只多了这 2 行**，`dump-config` 里
  `searchProvider: modsearch` 与 modsearch 插件行都在。

装完 `~/.dsh/profiles/web/package.json` 应为：

```json
{
  "dsh": { "profile": { "bundles": [
      "@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app", "dsh-think-zh", "@liustack/modsearch"
  ] } },
  "dependencies": {
    "@liustack/modsearch": "5.10.3",
    "dsh-think-zh": "github:Len7183/DSH-Think-zh"
  }
}
```

`bundles` 末尾那条由 dsh 自动 reconcile；**少了它插件不会加载**。

## 验证（不用重启的两步）

```powershell
dsh plugin --profile web list --depth 0
dsh --profile web --dump-config | Select-String 'modsearch|searchProvider'
```

dump 里应同时出现（本机实测都在）：
- `# == @deepseek-ai/dsh-base, patched by @liustack/modsearch` 与 `searchProvider: modsearch`；
- `# == @liustack/modsearch` / `- id: modsearch` / `name: '@liustack/modsearch'`。

CLI 端到端（前者离线、后者花一次免费额度）：

```powershell
npx -y @liustack/modsearch@5.10.3 doctor
npx -y @liustack/modsearch@5.10.3 -q "current Node.js LTS version"
```

本机 `doctor` 结果：`Node status: OK`、`search resolved: firecrawl (READY keyless)`、
`fetch resolved: firecrawl` + `local READY`、`social (none available)`（没装 grok，正常）。
真实搜索返回 8 条带 URL 的结果 ✅。

## 必须重启 DSH

**bundle 列表在 profile 启动时组合，运行中的进程不会热加载。**
装完必须重启 dsh（`dsh web` / `dsh --profile web`）才生效。

重启后用三个提示词验运行期行为：
1. `Search the web for the current Node.js LTS release and cite the sources.` → 走原生 `web_search` 卡片；
2. `Search X for recent posts from @deepseek_ai.` → `x_search`；
3. `Read https://example.com and summarize the page.` → `read_page`。

## 配置（可选，不配也能用）

配置：`~/.modsearch/config.json`（0600；不存在则跑默认值）。
环境变量优先：`TAVILY_API_KEY`、`EXA_API_KEY`、`FIRECRAWL_API_KEY`（可逗号分隔多个 key，失败自动轮换）。

```powershell
modsearch config set engine antigravity-cli        # 或 tavily / exa / firecrawl / grok-cli
modsearch config set tavily.apiKey <key>           # 1000 credits/月，免卡
modsearch config set exa.apiKey <key>              # $10/月额度
modsearch config set firecrawl.apiKey <key>        # 在 keyless 之上再加 1000/月
modsearch config set firecrawl.keylessFetch false  # 抓页只走本地，不把 URL 发给 Firecrawl 云
modsearch config set cooldown off
```

dsh web 的 UI 另有 **Settings → Plugins → Search engine (ModSearch)** 卡片，改的是同一个 config.json，
经插件注册的 `/modsearch/config` 回环路由（只应答同源回环请求，其它 403）。

### 插件开关（profile patch，一般不需要）

```yaml
- id: modsearch
  config:
    searchProvider: true      # 关掉它必须同时把 web seam 指回别的 provider
    xSearch: true
    readPage: true
    settingsCard: true
    providerTimeoutMs: 55000
```

> dsh 的 patch 行会**整块替换**目标行的 `config`，要写就把需要的值都写上。

## 卸载

```powershell
dsh plugin --profile web remove @liustack/modsearch
```

然后重启 dsh。bundle 自带的 `searchProvider: modsearch` patch 会随它一起消失；
**只有你自己在 `cordis.patch.yml` 里覆盖过 `searchProvider` 时才需要手动改回**，
否则 web seam 会指向一个不存在的 provider。

## 兼容性备注（重要）

上游文档说当前 bundle 是针对 **`@deepseek-ai/dsh 0.1.0-rc.7`** 检查的；本机 dsh 是
**`0.1.5-rc.1`**（更新）。本机实测**组合检查通过**（dump-config 里那两项都在），
但运行期行为（原生 `web_search` 是否真的切到 modsearch）要**重启后**才能确认。

**0.1.6-alpha.1 预检（2026-09-16，用隔离副本实测，本机未升级）**：
用 0.1.6-alpha.1 对同一 profile 跑 `--dump-config` 成功，`searchProvider: modsearch` 与
modsearch 插件行都还在；两版 dump 的差异全部落在 dsh 自带行（新增 ptc-runtime / workflow-ptc /
image-offload / mcp-resources / 终端与归档会话 UI，移除 workflow-worker-thread / code-runtime），
**没有触及 web seam 的 `searchProvider` 键**。所以 modsearch 不构成升级到 0.1.6 的阻碍。

上游列出的已知失败信号：
- `declares no dsh.bundle` → 装到了旧版本，按写死的版本重装；
- `web seam has no registerSearchProvider` → dsh 改动了这个预览接口：`x_search` / `read_page` 仍会注册，
  web 搜索会被跳过并留一条可见日志。**重启后若 dsh 的搜索没走 modsearch，先查这条。**

## 小坑

`dsh --profile web --dump-config` 会重写 profile 的 `cordis.yml`；在沙箱里跑会因写 profile 目录被拒，
需要放宽到 danger-full-access。
