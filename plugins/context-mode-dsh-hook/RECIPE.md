# context-mode-dsh-hook —— 自制适配层（**已废弃**，唯一副本仍在本目录存档）

> ⚠️ **本方案已废弃（2026-09-28 当日即被取代）**：`@deepseek-ai/dsh-hooks-claude-code` 的
> `inject = ["shell", "sessionProjections"]` 在本机 profile 里不满足，cordis 会让插件**永远等待、
> `apply` 永不执行** —— 插件能正常 `import`（loader 不报错），但**一个 hook 都不注册**，配置根本不读。
> 实测证据见 `plugins\dsh-ctx-router\RECIPE.md` 的「为什么不用 Claude Code hook 桥接」一节
> （会话日志 hook 事件 = 0；`configPath` 指向不存在文件也无任何警告）。
> **现役方案是 `plugins\dsh-ctx-router\`（原生 DSH 插件，挂 `tools/pre-execute`）。**
> 本目录仅作历史存档，**新环境不要再安装这一套**。

## 这是什么（历史方案，仅供追溯）

让 `context-mode`（MCP 挂载，见 `SKILLS.md`）的**自动路由**在 DSH 上真正生效的一层薄适配。

## 为什么需要它（不是多此一举）

context-mode 自带的 `hooks/hooks.json` 是给 **Claude Code** 用的，它的 PreToolUse hook
用一张**写死的**平台工具名别名表（`hooks/core/routing.mjs` 里的 `TOOL_ALIASES`）识别工具，
表里只有 Claude Code 的 `Bash` / `Read` / `Grep` / `WebFetch` / `Glob` 等，
**没有** DSH 的 `pwsh` / `read` / `grep`，也**没有**配置扩展点。
结果：官方 hook 收到 DSH 的工具名 → 认不出来 → 直接放行，等于没装。

另外，DSH 的 hook 拦截缝**默认是空的** —— `@deepseek-ai/dsh-hooks-claude-code`
不在 `--dump-default-config` 的默认 bundle 里，属于**可选桥接插件**，必须自己挂。

## 由哪几块组成

| 文件 | 作用 | 落在哪 |
|---|---|---|
| `dsh-pretooluse-hook.mjs` | 自制判断逻辑：这次调用会不会把大块原始数据灌进上下文 | `$DSH_HOME\context-mode\dsh-pretooluse-hook.mjs` |
| `dsh-hooks.json` | Claude Code 格式的 hook 配置，**matcher 用 DSH 的真实工具名** `pwsh` / `read` | `$DSH_HOME\context-mode\dsh-hooks.json` |
| `@deepseek-ai/dsh-hooks-claude-code` | DSH 自带的桥接插件（**DSH 自带，不备份**），把上面的配置接到 DSH 的拦截缝 | profile 的 `cordis.patch.yml` |

`cordis.patch.yml` 里的挂载条目：

```yaml
- insert:
    - id: hooks-claude-code
      name: '@deepseek-ai/dsh-hooks-claude-code'
      config:
        configPath: 'C:\Users\y\.dsh\context-mode\dsh-hooks.json'
        defaultTimeoutMs: 15000
```

## 重建步骤（新环境）

```powershell
# 1) 自制件落位（本目录两个文件）
Copy-Item .\dsh-pretooluse-hook.mjs "$env:USERPROFILE\.dsh\context-mode\" -Force
Copy-Item .\dsh-hooks.json         "$env:USERPROFILE\.dsh\context-mode\" -Force

# 2) 确认 dsh-hooks.json 里的 node 与脚本绝对路径与本机一致
#    （本机 node = D:\ProgramsDev\nodejs\node.exe，非此路径要改）

# 3) 挂载桥接插件：把上面那段 yaml 加进 profile 的 cordis.patch.yml
#    （已随 config\cordis.patch.yml 一起恢复）

# 4) 重启 DSH —— 桥接在启动时读取 configPath，只读一次，热加载不生效
```

## 拦截范围与逃生舱

**拦**（duń 明确是"抓数据"的）：

- `pwsh`：`curl` / `wget` / `Invoke-WebRequest` / `Invoke-RestMethod` /
  `Get-Content -Raw` / `cat` / `type` / `Select-String` / `rg` / `findstr` /
  `docker logs` / `kubectl logs` / `journalctl` / 无上限的 `git log`、`git diff` /
  `find` / `Get-ChildItem -Recurse`
- `read`：未带 `limit`/`offset` 且文件 > 256 KB

**不拦**：`grep`、`web_fetch`、`glob`、`edit`、`write`，以及改状态的操作
（构建、测试、写文件、建目录）—— DSH 侧这些输出本就有溢写与裁剪。
`grep` 尤其不拦：它的返回行数天然有限，且 DSH 侧已有裁剪。

**逃生舱（避免死锁）**：

- 命令里含 `ctx-allow`（如 `curl ... # ctx-allow`）→ 放行
- `read` 显式带 `limit` 或 `offset`（即主动分块读）→ 放行
- hook 自身崩溃 / 解析失败 → **fail-open**（不输出、exit 0），绝不阻断会话

## 验证

**离线单测**（不依赖 DSH，随时可跑）：

```powershell
$hook = "$env:USERPROFILE\.dsh\context-mode\dsh-pretooluse-hook.mjs"
$node = 'D:\ProgramsDev\nodejs\node.exe'

# 应 deny
'{"hook_event_name":"PreToolUse","tool_name":"pwsh","tool_input":{"command":"Get-ChildItem C:\\x -Recurse"}}' | & $node $hook
'{"hook_event_name":"PreToolUse","tool_name":"read","tool_input":{"file_path":"<一个>256KB的文件>"}}' | & $node $hook

# 应放行（无输出）
'{"hook_event_name":"PreToolUse","tool_name":"pwsh","tool_input":{"command":"git status --short"}}' | & $node $hook
'{"hook_event_name":"PreToolUse","tool_name":"pwsh","tool_input":{"command":"curl https://x  # ctx-allow"}}' | & $node $hook
'{"hook_event_name":"PreToolUse","tool_name":"read","tool_input":{"file_path":"<大文件>","limit":100}}' | & $node $hook
```

**端到端**（**必须重启 DSH 之后**）：在会话里发一条命中特征的命令
（例如 `Get-ChildItem -Recurse` 某个目录），应当被 deny，理由里给出 `ctx_batch_execute` 等替代。

判断桥接是否已加载的最快办法 —— 看当前会话日志里有没有 hook 事件：

```powershell
# 本项目会话目录（中文项目名被转义成 ~XXXX 形式）
$d = "$env:USERPROFILE\.dsh\sessions\--D-AI_python-~65E0~5B9E~9645~6587~4EF6~533A--"
# 取最新会话目录里的 session.v3.jsonl.zstd，解压后 grep hook
```

**没有任何 hook 事件 = 桥接没加载**（本适配层挂上之前就是这样）。

## 已知边界

- `defaultTimeoutMs: 15000` —— 本适配层是纯本地文件 stat + 正则，正常在 100 ms 内返回。
- 只接了 `PreToolUse`。context-mode 的 `SessionStart` 上下文注入、`PostToolUse` 会话捕获
  在本机**未接**：那两处依赖它自己的会话/转写格式，且官方 `SessionStart` 注入的是
  Claude Code 专属的 `<context_window_protection>` 提示块（工具名也是 Claude Code 风格）。
  常驻的 `AGENTS.md` 规则已覆盖同样的引导作用。
- 这是**自制件**：context-mode 升级不受影响（没改它的源码），
  但若官方调整工具名或路由语义，本适配层需复核。
