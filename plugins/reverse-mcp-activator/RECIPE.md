# reverse-mcp-activator —— 自研 DSH 插件（第四类资产的实际承载者）

> **一句话**：把逆向模式那 5 个 MCP 服务器的启动时机，从「`dsh web` 启动时」挪回「新开逆向模式会话时」。

## 为什么需要它（2026-10-09）

DSH 0.2.0 起，agent preset registry **在启动期就急切挂载所有已声明 preset**：

```
AgentPresetRegistry.register() → activate() → mountPreset()   // 启动期，无条件
```

`mountPreset()` 会对 composition 里每个**未禁用**的行调用插件激活 —— 也就是说
`.agent-presets` 目录扫描时代的「reading never mounts：读文件不挂载，只有新会话真的
选中才 compose」**已经完全不存在**。

后果（用户 2026-10-09 实测反馈）：`dsh web` 一启动就把 5 个 MCP 全部拉起 ——
9~13 个进程、约 300 MB 常驻，且 IDA 的 `uvx` 在无代理时反复重试 PyPI
（`6 × ~17s`，日志刷屏）。这正是 2026-10-02 那次「MCP 移入 preset」要解决的问题。

**结论：0.2.0 下，只要 MCP 行写在任何 composition 里，就一定会随启动拉起。**
要恢复按需，只能把挂载动作从「声明式行」搬进「运行时插件」—— 即本插件。

## 它做什么

| 阶段 | 行为 |
|---|---|
| 启动 | 只加载插件自身（几毫秒），**不碰任何 MCP** |
| 普通会话（standard 等） | 什么都不做 |
| **逆向模式会话创建** | 把 5 个 MCP 客户端挂到**该会话自己的作用域**上 |
| 会话销毁 | 作用域下沉 → MCP 插件卸载 → 服务器进程退出 |

关键机制：

1. 监听 `agent/created` —— 该事件是 **serial 且被 await**（`@deepseek-ai/dsh-agent` 的
   文档原话：「Listeners run in order and are awaited before creation resolves.
   AgentLoop holds queued input until all listeners finish」），所以逆向会话的
  第一条消息就带得上工具，不需要用户"等一会再发"。
2. 用 registry 的 `agentPresets.composedPreset(agent.ctx)` 认出目标 preset；
3. 对 `agent.ctx` 调 `ctx.plugin(McpClient, server)`。`ToolRuntime.register()` 按
   **调用方 ctx 的 scope** 落层，所以工具只进这个会话的 scope 层 —— 普通会话看不到
   `mcp__*`（实测全局视图里 0 个），也不会互相污染。
4. 并发挂载 + `startupTimeoutMs` 超时放行：慢的服务器（camoufox 冷启动、IDA 的 uvx
   解析）不阻塞会话创建，留在后台继续；每个服务器都配 `failOnStartupError: false`，
   连不上只是静默少工具。

## 安装（新环境）

### 1. 放源码

```powershell
# 本仓库的 plugins\reverse-mcp-activator\ 就是完整源码，直接复制
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.dsh\plugins\reverse-mcp-activator" | Out-Null
Copy-Item "D:\AI_python\skills_backup\plugins\reverse-mcp-activator\*" `
          "$env:USERPROFILE\.dsh\plugins\reverse-mcp-activator\" -Force
```

不需要 `pnpm install`、不需要进 profile 的 `dependencies`：loader 对 `file://` 形式的
行 `name` 直接 `import()`（见 `cordis-plugin-loader` 的 `EntryTree.import`）。

### 2. 在 profile patch 里加一行

`config\cordis.patch.yml` 末尾已经带好这一行（`reverse-mcp-activator`），整段复制即可。

```yaml
- insert:
    - id: reverse-mcp-activator
      name: 'file:///C:/Users/y/.dsh/plugins/reverse-mcp-activator/index.mjs'
      config:
        presetId: reverse
        profileName: web
        startupTimeoutMs: 5000
        servers:
          - serverName: camoufox
            transport: stdio
            ...
```

- **换机器要改**：`name` 里的绝对路径，以及每个 server 的 `command` / `args` 绝对路径。
- `servers` 的每一项就是标准 `@deepseek-ai/dsh-mcp-client` 的 config（原来写在
  preset composition 里的那 5 段，2026-10-09 原样迁过来）。
- `startupTimeoutMs`：会话创建最多等这么久（等齐快的几台；慢的转后台）。默认 5000。

### 3. 重启 DSH 并验证

重启后按顺序看（**从弱到强**）：

1. `dsh --profile web --dump-config` 输出里有 `reverse-mcp-activator` 行；
2. **启动日志里不该有任何 MCP 字样**（这是本插件存在的全部意义）；开一个普通会话
   同样不该有；
3. 新开一个「逆向模式」会话 → 启动日志出现各 MCP 的启动特征
   （`[wireshark-mcp-lite] tshark:`、`JADX-AI-MCP` 的 banner 等），会话里出现
   `mcp__camoufox__*` / `mcp__jadx__*` / `mcp__ida__*` / `mcp__analyzer__*` /
   `mcp__wireshark__*`。

## 前置与依赖

- 各 MCP 服务器自己的运行时（camoufox 环境、jadx-mcp-server、IDA + idalib、
  Anything Analyzer GUI、wireshark-mcp-lite 的 `.venv`）—— 见 `INSTALL.md` 的「MCP」一节。
- 本插件自身只依赖 `@deepseek-ai/dsh-mcp-client`，用 `createRequire` 以 profile 目录为
  解析根载入（插件在 `$DSH_HOME\plugins\` 下解析不到 DSH 的包）。

## 踩过的坑（复用本配方时别再踩）

1. **类的 `apply()` 不会被调用**。DSH 内置类插件走 `[Service.init]` 生成器（见
   `@deepseek-ai/dsh-agent-preset`），而本插件在 `$DSH_HOME\plugins\` 下解析不到
   `@deepseek-ai/cordis`、拿不到那个 symbol。**用函数式插件**。
   实测现象：模块日志打出来了（`module loaded`），但 `apply() entered` 永远是 0。
2. **模块级 `export const inject` 不生效**。必须用 `ctx.inject([...], (scoped) => …)`。
   陷阱：`ctx.get('x')` 绕过 inject 检查照样能取到服务，所以"看起来能用"，直到访问
   `ctx.tools` 这类属性才抛 `cannot get property "tools" without inject`。
3. **不要用 junction 把临时 HOME 的 profile 目录指到真实 profile**（debug 时踩过）：
   写 `临时路径\cordis.patch.yml` 会穿透链接改掉**线上真文件**。隔离测试要么复制
   profile 文件、只 junction `node_modules`，要么别 junction 目录本身。
4. **验证要区分"启动不带 MCP"和"逆向会话带 MCP"两个方向**：只测后者会漏掉回归，
   只测前者会漏掉功能失效。
