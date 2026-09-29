# reverse —— 「逆向模式」agent preset（第四类资产）

本目录是 preset `reverse` 的整份副本，恢复方式见 `INSTALL.md` 的「reverse（逆向模式）」一节。

## 这是什么

一个 **DSH agent preset**，在会话选择器里显示为「逆向模式」。它不是 skill、不是 DSH 插件、不是 MCP 挂载
—— 这三类都不覆盖它：

| 资产类型 | 住哪 | 换机器会自己回来吗 |
|---|---|---|
| skill | `$DSH_HOME\skills\<name>\` | 会（本仓库 `skills\` 镜像） |
| DSH 插件 | profile 的 `package.json` / `bundles` | 会（`install.ps1` 装） |
| MCP 挂载 | profile 的 `cordis.patch.yml` | 会（`install.ps1` 拷配置） |
| **agent preset** | `$DSH_HOME\.agent-presets\<id>\` | **不会** —— 只有本目录这份副本能带回去 |

## 内容

| 文件 | 说明 |
|---|---|
| `agent.cordis.yml` | composition：DSH 自带 `standard` 骨架 + 逆向 persona（身份、默认已授权、开工五步、验收骨架、脚本分级、增删自检、事实纪律） |
| `preset.yml` | 显示名与描述（会话选择器里显示「逆向模式」） |

**没有**注册任何服务或工具，所以不需要 `isolate` realm —— 不要往里加服务行。

## 依赖（必须先装）

`reverse-skill-router`、`apk-reverse`、`camoufox-reverse`、`wmpf-miniapp-reverse`、`firerpa`。
iOS 与 Windows 域当前为 `shallow` 降级（见 `reverse-skill-router\references\domain-registry.json`）。

## 恢复步骤（四步）

```powershell
# 1) 复制回 preset 根
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.dsh\.agent-presets\reverse" | Out-Null
Copy-Item (Join-Path $PSScriptRoot '*') "$env:USERPROFILE\.dsh\.agent-presets\reverse\" -Force

# 2) 验证挂载（等价于会话启动的真实挂载校验）
#    用 preset_probe 工具：action=validate, id=reverse  →  期望 mounted OK: reverse

# 3) 生成能力清单（persona 第一步就要读它）
pwsh -NoProfile -File "$env:USERPROFILE\.dsh\skills\reverse-skill-router\scripts\scan-capabilities.ps1"

# 4) 新开一个会话，预设选「逆向模式」，确认 persona 与工具列表
```

## 不要做

- 不要编辑 DSH 部署自带的 preset（`standard` / `ptc` / `minimal` / `cordis`）：升级会覆盖，
  改坏 `cordis` 还会让 preset 创作能力失效。
- 不要把本机工具路径写进 composition：本机状态由 `$DSH_HOME\reverse\capabilities.md` 提供，
  那正是"装了新工具不用改 preset"的原因。

## 维护

改完 composition：① `preset_probe validate reverse`；② 整份复制回本目录并核对 SHA256；
③ 在账本 `SKILLS.md` 追加一行日志。
