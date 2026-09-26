# dsh-ding —— DSH 插件安装记录

| 项 | 值 |
|---|---|
| 类型 | **DSH 插件**（原生 bundle，带 web 客户端插件；不是 skill） |
| 优先级 | P2 独立类 |
| 来源 | https://github.com/CAOGGL/dsh-ding |
| 安装日期 | 2026-09-16（本机当时装到 v1.0.2） |
| 用途 | 对话完成 / 长任务运行中 / Agent 提问 / 工具审批等待时提醒：提示音 + Windows 原生通知；WebUI 顶栏铃铛可调开关、音量、音效 |

## 安装（取最新版，不锁版本）

前置：**pnpm**（`dsh plugin` 只是它的转发器）、**Windows**（通知走 PowerShell + WinRT toast）。

```powershell
dsh plugin --profile web add github:CAOGGL/dsh-ding
```

**升级也重跑这一条**：它取仓库默认分支的最新 commit，不用改本文件、不用记版本号。

装完 `~/.dsh/profiles/web/package.json` 里应有：`dependencies` 的
`"dsh-ding": "github:CAOGGL/dsh-ding"`，以及 `dsh.profile.bundles` 里的 `"dsh-ding"`
（少了它插件不会加载）。包体在 `~/.dsh/profiles/web/node_modules/dsh-ding/`。

> 只有当 pnpm 拦构建时（报 `allowBuilds`）才需要多一步：把报错里给出的**那个确切键**
> （含它解析到的 commit，**必须带引号**）写进 `~/.dsh/profiles/web/pnpm-workspace.yaml` 再重跑。
> 本机装 v1.0.2 时**未**触发（包内自带预构建 `lib\index.js` / `lib\client.js`，`package.json` 无 `scripts`）。

## 验证

```powershell
dsh plugin --profile web list --depth 0
dsh --profile web --dump-config | Select-String 'dsh-ding'
```

然后**必须重启 DSH**（bundle 列表在 profile 启动时组合，运行中不热加载）。重启后：对话页顶栏出现
铃铛；跑一轮对话并切到别的窗口，结束时应响铃 + 弹通知；点通知应拉起浏览器直达该会话。

## 卸载

```powershell
dsh plugin --profile web remove dsh-ding     # 然后重启 dsh
```

它在运行期还会留下（不自动清，重装会重建）：开始菜单快捷方式 `dsh-ding-notifier.lnk`、
`HKCU:\Software\Classes\dsh-ding` 协议、`~/.dsh/profiles/web/data/dsh-ding.json` 与 `data/sounds\`、
`%TEMP%\dsh-ding-*.log`。要清就按需删——**本机删除一律走 `dev-hygiene` 的
`scripts\Remove-ToRecycleBin.ps1`**。
