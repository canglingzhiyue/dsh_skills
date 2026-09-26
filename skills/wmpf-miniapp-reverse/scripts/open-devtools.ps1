#Requires -Version 7.0
<#
.SYNOPSIS
    打开调试前端：把 devtools:// 链接复制到剪贴板（并可选打开浏览器窗口）。

.DESCRIPTION
    关键限制：Chromium 系浏览器**不接受命令行/外部导航到 devtools://**
    （实测 Chrome for Testing 148 会忽略该 URL 直接开新标签页）。
    必须由用户在地址栏手工粘贴，因此本脚本只负责：
      1) 把链接放进剪贴板
      2) 打开一个浏览器窗口（默认 Edge，本机已验证可用）
      3) 提示用户 Ctrl+L -> Ctrl+V -> Enter

    前提：start-debugger.ps1 已在运行，且**小程序已经打开**（日志里出现过
    "[miniapp] miniapp client connected"）。

.PARAMETER CdpPort
    必须与 start-debugger.ps1 的 -CdpPort 一致，默认 62000。

.PARAMETER Browser
    浏览器可执行文件路径。默认自动选择：Edge -> playwright chromium。

.PARAMETER NoBrowser
    只复制链接，不打开浏览器。

.PARAMETER AutoPaste
    实验性：尝试自动激活浏览器窗口并粘贴。焦点可能落到别的窗口，默认关闭。

.EXAMPLE
    .\open-devtools.ps1
#>
[CmdletBinding()]
param(
    [int]$CdpPort = 62000,
    [string]$Browser,
    [switch]$NoBrowser,
    [switch]$AutoPaste
)

$ErrorActionPreference = 'Stop'

$url = "devtools://devtools/bundled/inspector.html?ws=127.0.0.1:$CdpPort"
Set-Clipboard -Value $url

Write-Host "[devtools] 链接已复制到剪贴板：" -ForegroundColor Cyan
Write-Host "           $url" -ForegroundColor White

if ($NoBrowser) {
    Write-Host "[devtools] 已按 -NoBrowser 跳过打开浏览器。请手动打开浏览器后粘贴。" -ForegroundColor Yellow
    return
}

if (-not $Browser) {
    $candidates = @(
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "$env:LOCALAPPDATA\ms-playwright\chromium-1223\chrome-win64\chrome.exe",
        "$env:LOCALAPPDATA\ms-playwright\chromium-1187\chrome-win\chrome.exe"
    )
    $Browser = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $Browser -or -not (Test-Path $Browser)) {
    Write-Host "[devtools] 未找到可用的 Chromium 浏览器，请手动打开并粘贴上面的链接。" -ForegroundColor Yellow
    return
}

Write-Host "[devtools] 浏览器：$Browser" -ForegroundColor DarkGray
$proc = Start-Process -FilePath $Browser -ArgumentList '--new-window' -PassThru

if ($AutoPaste) {
    Start-Sleep -Seconds 3
    $shell = New-Object -ComObject WScript.Shell
    if ($shell.AppActivate($proc.Id)) {
        Start-Sleep -Milliseconds 800
        $shell.SendKeys('^l'); Start-Sleep -Milliseconds 400
        $shell.SendKeys('^v'); Start-Sleep -Milliseconds 400
        $shell.SendKeys('{ENTER}')
        Write-Host "[devtools] 已尝试自动粘贴（若焦点被抢走请手工粘贴）。" -ForegroundColor Yellow
        return
    }
    Write-Host "[devtools] 自动激活窗口失败，请手工粘贴。" -ForegroundColor Yellow
}

Write-Host "[devtools] 请在浏览器窗口按 Ctrl+L，再按 Ctrl+V，最后回车。" -ForegroundColor Yellow
