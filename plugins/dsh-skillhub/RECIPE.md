# dsh-skillhub —— DSH 插件安装配方

| 项 | 值 |
|---|---|
| 类型 | **DSH 插件**（不是 skill；bundle + client UI） |
| 优先级 | P2 独立类 |
| 来源 | https://github.com/aa2246740/dsh-skillhub · npm `@aa2246740/dsh-skillhub` |
| 用途 | 本机已有 Skills（`~/.agents/skills` + `$DSH_HOME/skills`）与运行中的 MCP 服务的**统一开关面板**：设置页 `skill&mcp` 全局层 + 输入框上方「技能」胶囊的本项目／本对话层，纯可见性控制、不改磁盘文件 |
| 本机记录日期 | 2026-10-27 |
| 本机版本 | `1.0.7`（DSH `0.2.0-rc.2`） |

---

## 为什么插件要有自己的目录

插件不是"复制到 skill 根"就能用的东西：它要装进 **profile 的依赖**并由 profile 的 `bundles` 列表加载，
装完还必须**重启 DSH**。所以插件的"备份"= **安装配方 + profile 配置片段**，而不是文件副本。
本目录只放配方：`node_modules` 里的构建产物可以重装，不入备份。

## 安装

前置：`dsh plugin` 只是 pnpm 的转发器，机器上必须有 pnpm（`pnpm -v` 能跑；没有就 `npm install -g pnpm`）。

```powershell
dsh plugin --profile web add @aa2246740/dsh-skillhub
```

**spec 不锁版本**（重装即升级到最新版）。但要先按下面的**版本对照**确认当前 DSH 能装哪个版本 ——
装错版本 DSH 会在启动时**整行拒绝**，表现为「装了但完全没有入口」，刷新页面或重启都不恢复：

| DSH 版本 | 可装的插件版本 |
|---|---|
| 0.2.0-rc.x | `1.0.4` 及以上（推荐最新；本机 1.0.7） |
| 0.1.7-rc.x | `1.0.2`（1.0.4+ 不兼容） |
| 0.1.5 | `1.0.1` |

> npm 包（非 git prepare）**不需要** `allowBuilds`：`main` 分支与 npm 包里都自带编译好的 `lib/`，
> 普通使用不需要 pnpm 构建、不需要 DSHX。

### ⚠ 本机特有的前置：把 `@deepseek-ai/schemastery` 抬到 3.18.5

**只装插件会加载失败，必须先做这一步。** 现象与根因（2026-10-27 实测）：

```
dsh: warning: 1 entry did not activate
dsh-skillhub (@aa2246740/dsh-skillhub): failed to import
```

插件运行时 `import { scopeOf } from '@deepseek-ai/dsh-scope'` 与 `import z from '@deepseek-ai/schemastery'`。
`@howmp/dsh-pentest` 的 `dependencies` 会把 `@deepseek-ai/schemastery@3.18.1` 拉到 profile 顶层
（`nodeLinker: hoisted`），而插件的 `Config = z.object({ enabled: z.boolean().default(true).volatile() })`
用到 **3.18.4 才有的 `Schema.volatile()`** —— 3.18.1 没有，模块求值即抛
`z.boolean(...).default(...).volatile is not a function`。host 自带的 3.18.5 在插件之后才被解析，
救不了它（profile 本地 node_modules 优先）。

做法：在 `~/.dsh/profiles/web/package.json` 的 `dependencies` 里显式加一行，再跑一次 install：

```json
{
  "dependencies": {
    "@aa2246740/dsh-skillhub": "1.0.7",
    "@deepseek-ai/schemastery": "3.18.5"
  }
}
```

```powershell
dsh plugin --profile web install
```

`3.18.5` 与 host 的 `@deepseek-ai/schemastery` 同版本；`dsh-pentest` 声明的 `^3.18.1` 也满足，会被
提升到同一份上（**实测 pentest 仍正常加载**：临时实例启动日志没有 "did not activate" 警告）。

自检（不启动 DSH，秒级）：

```powershell
cd "$env:USERPROFILE\.dsh\profiles\web"
node --input-type=module -e "const m = await import('@aa2246740/dsh-skillhub'); console.log('OK', Object.keys(m).join(','))"
# 期望：OK Config,apply,attachAgentProvider,inject,name
```

## 装完应该长成什么样

`~/.dsh/profiles/web/package.json`：

```json
{
  "dsh": {
    "profile": {
      "bundles": [
        "@deepseek-ai/dsh-base",
        "@deepseek-ai/dsh-web-app",
        "@aa2246740/dsh-skillhub"
      ],
      "patchReload": "live"
    }
  },
  "dependencies": {
    "@aa2246740/dsh-skillhub": "1.0.7",
    "@deepseek-ai/schemastery": "3.18.5"
  }
}
```

`bundles` 末尾那一条由 dsh 安装后自动 reconcile，不用手改；但**核对时以它为准** —— 少了它插件不会加载。
插件自己的 `cordis.patch.yml` 只有一行 `insert: [{ id: dsh-skillhub, name: '@aa2246740/dsh-skillhub' }]`，
不需要额外的 profile 补丁。

## 验证

1) 组合检查（不启动服务）：

```powershell
dsh --profile web --dump-config | Select-String 'dsh-skillhub' -Context 1,2
# 期望：`# == @aa2246740/dsh-skillhub` 段落 + `- id: dsh-skillhub`
```

2) 真实加载（另起一个临时实例，不影响正在跑的 3080）：

```powershell
$env:DSH_WEB_URL=''   # 别让它继承旧实例的 URL
dsh web --no-open --port 3099
# 期望启动日志出现两行，且没有 "did not activate"：
#   [my-plugins/dsh-skillhub] loaded
#   [my-plugins/dsh-skillhub] http /skillhub
```

3) HTTP 端到端（要带 web 的浏览器会话 cookie：先 `GET /?token=<token>` 换 303 + cookie，再用 cookie 请求）：

| 端点 | 期望 |
|---|---|
| `GET /skillhub/catalog` | 200，`tree` 里两个 root（`~/.agents/skills` 与 `$DSH_HOME/skills`）、每个技能带 `gate` |
| `GET /skillhub/mcp/catalog` | 200，`servers: []` 属正常（见下方「本机 MCP 现状」） |
| 首页 HTML | `__DSH_BOOT__` / preload 里含 `@aa2246740/dsh-skillhub/client.js`；该 combo URL 请求返回 200 |

4) **必须重启 DSH**（重开 `dsh web`）：bundle 层在 profile 启动时组合，运行中的进程不会热加载这个插件。
重启后 UI 里应有 **设置 → `skill&mcp`** 页与输入框上方的「技能」胶囊。

## 操作语义（用的人要知道的三层传导）

| 操作层级 | 影响范围 | 说明 |
|---|---|---|
| 全局 (Global) | 全局 + 所有项目 + 所有对话 | 基准值，重复设同值也会向下同步 |
| 本项目 (Project) | 当前项目 + 该项目下所有对话 | 不影响其他项目 |
| 本对话 (Chat) | 仅当前对话 | 临时覆盖 |
| 新建继承 | 自动向下继承 | 新项目继承全局，新会话继承所属项目 |

数据存在 `$DSH_HOME/skillhub/`（**用户数据，不入本仓库**；迁移时不需要删除，也不影响原始技能文件）。
纯可见性控制 —— 它注册一个 skill provider 与一层 MCP 工具 `restrict`，**不增删改磁盘上的任何技能目录**。

## 本机适配备注

- **技能根**：`~/.agents/skills`（54 个，ClawHub 装的）+ `$DSH_HOME/skills`（11 个，本仓库镜像的那批）。
  两处都会列出来，按 `home` 字段区分（`agent` / `dsh`）。
- **10 个 broken 条目属既有问题**（不是插件造成的）：上游技能的 frontmatter `name` 不合规（如 `Code`、
  `Memory`、`FFmpeg Video Editor`）或缺 frontmatter（`debug-pro-1.0.0`、`test-runner-1.0.0`）。
  SkillHub 会把它们列成 `kind: broken` 并给出原因，**不会静默吞掉**。
- **MCP 页签在本机为空的正常态**：本机的 6 个 MCP 不走 profile 层，也不走 `dsh-mcp-client` 的常驻行，
  而是自研插件 `reverse-mcp-activator` 在**逆向模式会话创建时**才 `ctx.plugin(McpClient, server)` 挂载。
  插件靠扫 loader registry 里 `runtime.name === 'mcp-client'` 的 fiber 来发现服务，所以：
  **只有存在逆向模式会话时 MCP 页签才有内容**，普通会话里 `servers: []` 符合预期。
- `~/.agents/skills` 里的软链接包（如 `ego-browser` → `C:\Users\y\.local\share\ego\ego-skills`）能被正确识别为
  `link.kind: symlink`，不影响开关。

## 升级 / 卸载

```powershell
# 升级（重跑同一条，spec 不锁版本）
dsh plugin --profile web add @aa2246740/dsh-skillhub

# 卸载
dsh plugin --profile web remove @aa2246740/dsh-skillhub
```

两者都要**重启 DSH**。卸载时若 `@deepseek-ai/schemastery` 已不再被别的插件需要，可以把它那一行一并删掉
（本机仍有 `dsh-pentest` 依赖它，**不要删**）。`$DSH_HOME/skillhub/` 是开关数据，卸载不自动清理，
需要还原默认可见性时删掉即可。

## 小坑

- **`@aa2246740/dsh-skillhub` 与旧别名 `dsh-skillhub` 不能并存**：从 1.0.4 或更早迁移时先
  `dsh plugin --profile web remove dsh-skillhub`（或旧作用域名）再装新的，否则两份安装互相打架。
- 装到**哪个 profile 就只对那个 profile 生效**：本机是 `web`。桌面 App 用自己的 Desktop profile，
  Web 命令装不进桌面端，反之亦然。
- `dsh --dump-config` 会重写 profile 的 `cordis.yml`，沙箱内会因写 profile 目录被拒 → 需要 danger-full-access。
- 客户端 bundle 是**组合请求** `plugins/??<mod1>/client.js,<mod2>/client.js&rev=…`：用 PowerShell 的
  `Invoke-WebRequest` 拼这个 URL 容易把 `??` 弄坏而得到 404，**探活请用 `curl.exe` 或 node 的 `fetch`**。
