#Requires -Version 7
<#
.SYNOPSIS
  启动 Anything Analyzer GUI 并等待其内置 MCP Server 就绪。
.DESCRIPTION
  MCP Server 跑在 Electron 主进程里：GUI 不开，MCP 就不在。
  本脚本幂等：已在运行则直接进入等待；启动后轮询 probe-mcp.ps1 直到就绪或超时。
.PARAMETER ExePath
  可执行文件路径。缺省时按常见位置探测。
.PARAMETER TimeoutSec
  等待 MCP 就绪的最长秒数，默认 60。
.EXAMPLE
  pwsh -File start-analyzer.ps1
  pwsh -File start-analyzer.ps1 -ExePath 'D:\ProgramsDev\AnythingAnalyzer\Anything Analyzer.exe'
#>
[CmdletBinding()]
param(
  [string]$ExePath,
  [int]$TimeoutSec = 60
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$probe = Join-Path $here 'probe-mcp.ps1'

function Resolve-Exe([string]$hint) {
  if ($hint) {
    if (Test-Path $hint) { return $hint }
    throw "指定的 ExePath 不存在: $hint"
  }
  $candidates = @(
    'D:\ProgramsDev\AnythingAnalyzer\Anything Analyzer.exe',
    (Join-Path $env:LOCALAPPDATA 'Programs\Anything Analyzer\Anything Analyzer.exe'),
    (Join-Path ${env:ProgramFiles} 'Anything Analyzer\Anything Analyzer.exe')
  )
  foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
  throw '找不到 Anything Analyzer.exe —— 用 -ExePath 显式指定'
}

$exe = Resolve-Exe $ExePath

$running = Get-Process -Name 'Anything Analyzer' -ErrorAction SilentlyContinue
if (-not $running) {
  Write-Host "[analyzer] 启动 $exe" -ForegroundColor Cyan
  Start-Process -FilePath $exe | Out-Null
} else {
  Write-Host "[analyzer] 已在运行 (pid $($running[0].Id))，等待 MCP 就绪" -ForegroundColor Cyan
}

$deadline = (Get-Date).AddSeconds($TimeoutSec)
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 2
  & pwsh -NoProfile -File $probe -Quiet
  if ($LASTEXITCODE -eq 0) {
    & pwsh -NoProfile -File $probe
    exit 0
  }
}

Write-Host "[analyzer] 等待 ${TimeoutSec}s 后 MCP 仍未就绪" -ForegroundColor Red
& pwsh -NoProfile -File $probe
exit 1
