# dsh-ctx-router —— 自制原生 DSH 插件（**源件唯一副本在本目录**）

**状态：现役。** 取代 `plugins\context-mode-dsh-hook\`（Claude Code hook 桥接方案，
在本机 DSH 0.1.5-rc 上**不可用**，原因见下）。

## 它解决什么

上下文保护：凡是"为了得出结论而读"的大块原始数据（递归列目录、无上限日志、整文件
dump、宽范围检索），直接在会话里读会把原始字节灌满上下文。本插件挂在 DSH 自己的
拦截缝上，把这类**工具调用**拦下并改道 context-mode 沙箱（`ctx_*`），原始字节留在
沙箱、只把结论取回。

## 为什么不用 Claude Code hook 桥接（重要，勿重蹈）

`@deepseek-ai/dsh-hooks-claude-code` 的 `inject = ["shell", "sessionProjections"]`。
cordis 的语义是**声明的服务不满足就永远等待、`apply` 根本不执行**（既不报错也不警告）。
本机实测：

- 插件包能正常 `import`（在依赖闭包里，`profiles\node_modules` 有有效 junction），
  **loader 不报错**；
- 但 `apply` 从不执行 → 配置不读、**一个 hook 都不注册**；
- 证据：会话 `session.v3.jsonl.zstd` 里 hook 事件 = **0**，`SessionStart` 也不触发；
  `configPath` 故意指向不存在的文件也**不产生任何警告**（正是 apply 没跑的旁证）。

顺带确认：loader 对**解析不到的包**是 **fail-loud 直接退出**（实测 `ERR_MODULE_NOT_FOUND`
终止启动），所以"没报错"恰恰说明包解析没问题 —— 卡住的是 `inject`。

试过并**排除**的原因：YAML 缩进/格式；`insert` 语义（`applyEntryPatches` 里无 `id` 的
insert 就是 `data.push(...insert)` 插到顶层）；行 `id` 与插件内部 `name` 同名；
`configPath` 相对/绝对；hooks.json 语法；matcher 写法；profile 差异（用 `hooktest`
隔离 profile 复现，并确认同一 insert 里的 MCP 条目**正常工作**，即 insert 机制无辜）。

**结论：走 DSH 原生插件，挂 `tools/pre-execute`，不依赖任何服务。**

## 拦截缝契约（来自 @deepseek-ai/dsh-tools）

```
waterfall(carrier, 'tools/pre-execute', exec, () => ({ kind: 'allow' }))
denialReason = decision.kind === 'allow' ? guardReason(exec) : decision.reason
```

- handler 形如 `(exec, next)`；
- 返回 `{ kind: 'deny', reason }` → 拦下，`reason` 以 `Error: <reason>` 回给模型；
- `{ kind: 'ask', ... }` 走用户批准；terminal 默认 `{ kind: 'allow' }`。
- `exec` 实测字段：`token, callId, rootCallId, name, signal, agent, deferContext,
  concludeTurn, arguments`；工具名在 `exec.name`，参数在 `exec.arguments`。

## 文件

| 文件 | 作用 | 落位 |
|---|---|---|
| `lib\index.js` | 插件本体（拦截判断 + 引导文案） | `$DSH_HOME\plugins\dsh-ctx-router\lib\index.js` |
| `package.json` | 包元数据（`type: module`） | `$DSH_HOME\plugins\dsh-ctx-router\package.json` |
| `RECIPE.md` | 本文件 | 仅账本 |

## 安装

```powershell
# 1) 落位（本目录就是源码唯一副本）
$dst = "$env:USERPROFILE\.dsh\plugins\dsh-ctx-router"
New-Item -ItemType Directory -Force "$dst\lib" | Out-Null
Copy-Item .\lib\index.js "$dst\lib\" -Force
Copy-Item .\package.json "$dst\" -Force

# 2) 挂进 profile：cordis.patch.yml 末尾追加（注意 file:/// 是三斜杠）
#    - insert:
#        - id: ctx-router
#          name: 'file:///C:/Users/y/.dsh/plugins/dsh-ctx-router/lib/index.js'
```

**不需要 `dsh plugin add`**：`insert` 的 `name` 直接写 `file:///` URL 即可，cordis
loader 用 `import()` 加载（实测有效），省掉 pnpm 依赖与 `allowBuilds`。路径里的用户名
按本机调整。

**生效方式（两种改动行为不同，均已实测）**：

- **改 `cordis.patch.yml`（挂载配置）→ 热重载立即生效，不用重启。** 本机 profile 设了
  `patchReload: live`；实测改完配置后，同一会话的下一条命令立刻被拦。
- **改插件源码 `lib\index.js` → 必须重启 DSH。** 热重载只重放**配置补丁**，不会重新
  `import` 已经加载过的模块（ESM 模块缓存）—— 实测：改完源码后拦截日志仍是旧格式，
  重启后才变成新格式。
- 若某台机器 profile 是 `startup`，则两种改动都需要重启。

## 拦截范围

`pwsh` / `bash` 命令命中任一条 → 拦：
`curl` / `wget` / `iwr` / `irm`、`Invoke-WebRequest` / `Invoke-RestMethod`、
`Get-Content -Raw`、`cat` / `type`、`rg` / `Select-String` / `findstr`、
`docker logs` / `kubectl logs` / `journalctl`、无 `-n|--max-count` 的 `git log`、
无 `--stat` 的 `git diff`、`find` / `Get-ChildItem -Recurse`。

`read` 不带 `limit` / `offset` 且目标文件 > **256 KB** → 拦。

**不拦**：`grep` / `glob` / `web_fetch` / `edit` / `write` 以及任何改状态的操作。

## 逃生舱（不会死锁）

- 命令里含 `ctx-allow` → 放行；
- `read` 显式带 `limit` / `offset` → 放行；
- 插件内部 **fail-open**：任何意外都 `next()` 放行，绝不阻断会话。

## 验证

```powershell
# ① 应被拦（命令里含 Select-String / -Recurse 等）
#    → 工具返回 Error，开头是 "ctx-router: 这次调用会把大量原始输出灌进上下文…"
# ② 应放行：pwd
# ③ 拦截日志（每次一行）
Get-Content "$env:USERPROFILE\.dsh\context-mode\ctx-router.log"
# ④ 配置树里应出现该行（在沙箱里跑，否则会被自己拦）
dsh --profile web --dump-config | Select-String 'ctx-router'
```

实测记录（2026-09-28）：`Get-ChildItem <dir> -Recurse -File` 被拦并在
`ctx-router.log` 记下 `DENY tool=pwsh`；`pwd` 正常放行；`--dump-config` 里该行位于
配置树第 644-645 行（`id: ctx-router` + `name: file:///...`）。

## 已知边界

- 判断是**启发式正则**，不是语义分析：命令经变量拼接绕过正则时不拦（fail-open 的代价）。
- 只覆盖 `pwsh` / `bash` / `read`；`grep` 工具未拦（其输出通常有界）。
- deny 之后模型可能换一条更精确的命令继续 —— 这本身就是期望的引导效果。
- 若 DSH 调整 `tools/pre-execute` 的决策形状，需复核 `lib\index.js`。
