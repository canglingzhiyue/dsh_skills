#Requires -Version 7.0
<#
.SYNOPSIS
    启动 WMPFDebugger（微信小程序 / WMPF 远程调试工具）。

.DESCRIPTION
    必须以 README 规定的顺序操作：
      1) 运行本脚本（启动 debug server 9421 + CDP proxy 62000，并注入 Frida hook）
      2) 打开（或关掉重开）想调试的小程序
      3) 运行 open-devtools.ps1，在浏览器地址栏粘贴链接
    顺序颠倒会导致小程序闪退，需从第 1 步重来。

    权限：Frida 需要与 WeChatAppEx.exe 同等权限。若报
    "Cannot read properties of undefined (reading 'parameters')" 或 attach 失败，
    请用「管理员身份」的 pwsh 7 重新运行本脚本（本机普通权限实测可用）。

.PARAMETER Root
    工具目录，默认 D:\AI_python\reverse\vmpfdebugger。可从 skill 目录直接调用。

.PARAMETER CdpPort
    CDP 代理端口，浏览器端链接用它，默认 62000。

.PARAMETER DebugPort
    小程序回连的调试服务端口，默认 9421（README 注明不要改）。

.PARAMETER AutoDetect
    自动探测 hook 偏移（Windows x64，beta）。WMPF 版本已有内置配置时不需要。

.EXAMPLE
    .\start-debugger.ps1
.EXAMPLE
    .\start-debugger.ps1 -CdpPort 63000 -DebugMain
#>
[CmdletBinding()]
param(
    [string]$Root = 'D:\AI_python\reverse\vmpfdebugger',
    [int]$CdpPort = 62000,
    [int]$DebugPort = 9421,
    [switch]$AutoDetect,
    [switch]$DebugMain,
    [switch]$DebugFrida
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Root)) {
    throw "工具目录不存在：$Root。先跑 scripts\restore.ps1 重建。"
}
Set-Location $Root -ErrorAction Stop

$tsnode = Join-Path $Root 'node_modules\.bin\ts-node.cmd'
if (-not (Test-Path $tsnode)) {
    throw "未找到 ts-node。请在 $Root 执行：corepack yarn install --frozen-lockfile"
}

$tsArgs = @('src/index.ts', '--cdp-port', "$CdpPort", '--debug-port', "$DebugPort")
if ($AutoDetect) { $tsArgs += '--auto-detect' }
if ($DebugMain)  { $tsArgs += '--debug-main' }
if ($DebugFrida) { $tsArgs += '--debug-frida' }

Write-Host "[start] WMPFDebugger  root=$Root" -ForegroundColor Cyan
Write-Host "[start] cdp-port=$CdpPort  debug-port=$DebugPort" -ForegroundColor Cyan
Write-Host "[start] 顺序：本脚本 -> 打开（重开）小程序 -> .\open-devtools.ps1" -ForegroundColor Yellow
Write-Host "[start] 停止：Ctrl+C（会 detach Frida 并关闭两个服务）" -ForegroundColor DarkGray

& $tsnode @tsArgs
