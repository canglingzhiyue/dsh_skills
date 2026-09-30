#Requires -Version 7
<#
.SYNOPSIS
  anything-analyzer 内置 MCP Server 探活脚本。
.DESCRIPTION
  读 %APPDATA%\anything-analyzer\mcp-server-config.json，依次检查：
    1) 配置文件存在且 enabled=true
    2) MCP 端口有监听（GUI 应用在运行）
    3) MCP 协议握手成功并能列出工具
  退出码 0 = 可用；1 = 未就绪。
  token 从配置文件读取，脚本本身不含任何凭据。
.EXAMPLE
  pwsh -File probe-mcp.ps1
  pwsh -File probe-mcp.ps1 -Quiet   # 只返回退出码
#>
[CmdletBinding()]
param([switch]$Quiet)

$ErrorActionPreference = 'Stop'

function Fail([string]$msg) {
  if (-not $Quiet) { Write-Host "[analyzer] $msg" -ForegroundColor Red }
  exit 1
}

$cfgPath = Join-Path $env:APPDATA 'anything-analyzer\mcp-server-config.json'
if (-not (Test-Path $cfgPath)) { Fail "未找到配置 $cfgPath —— 应用尚未安装或从未启动过" }

$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
if (-not $cfg.enabled) { Fail "MCP Server 未启用 (enabled=false)，改 $cfgPath 后重启应用" }

$bindHost = if ($cfg.host -and $cfg.host -ne '0.0.0.0') { $cfg.host } else { '127.0.0.1' }
$base = "http://${bindHost}:$($cfg.port)/mcp"

# 1) 端口探活
$listening = $false
try {
  $listening = [bool](Get-NetTCPConnection -State Listen -LocalPort $cfg.port -ErrorAction Stop |
                      Where-Object { $_.LocalAddress -in @($bindHost, '0.0.0.0', '::') })
} catch { $listening = $false }
if (-not $listening) {
  Fail "端口 $bindHost`:$($cfg.port) 无监听 —— GUI 应用没在运行。启动后重试（见本 skill scripts\start-analyzer.ps1）"
}

# 2) MCP 协议握手
$tmp = Join-Path $env:TEMP ("analyzer-probe-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
  $initFile = Join-Path $tmp 'init.json'
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}' |
    Set-Content -Path $initFile -Encoding ascii -NoNewline

  $hFile = Join-Path $tmp 'h.txt'
  $auth = "Authorization: Bearer $($cfg.authToken)"
  $initBody = Join-Path $tmp 'init-body.txt'
  & curl.exe -s -D $hFile -o $initBody -X POST $base -H $auth -H 'Content-Type: application/json' `
      -H 'Accept: application/json, text/event-stream' --data-binary "@$initFile"
  if ($LASTEXITCODE -ne 0) { Fail "initialize 请求失败 (curl exit $LASTEXITCODE)" }

  $m = Select-String -Path $hFile -Pattern '^mcp-session-id:\s*(.+)$' -CaseSensitive:$false
  if (-not $m) { Fail "initialize 未返回 mcp-session-id —— 认证失败？检查 authToken 是否与配置文件一致" }
  $sid = $m.Matches[0].Groups[1].Value.Trim()

  $tlFile = Join-Path $tmp 'tl.json'
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' |
    Set-Content -Path $tlFile -Encoding ascii -NoNewline
  $out = & curl.exe -s -X POST $base -H $auth -H 'Content-Type: application/json' `
      -H 'Accept: application/json, text/event-stream' -H "mcp-session-id: $sid" --data-binary "@$tlFile"

  $names = [regex]::Matches($out, '"name":"([a-z_]+)"') | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique
  if ($names.Count -eq 0) { Fail "tools/list 未返回工具 —— 响应片段: $($out.Substring(0, [Math]::Min(200, $out.Length)))" }

  if (-not $Quiet) {
    Write-Host "[analyzer] MCP 在线: $base" -ForegroundColor Green
    Write-Host "[analyzer] 工具数: $($names.Count)" -ForegroundColor Green
    Write-Host ("[analyzer] " + ($names -join ', '))
  }
  exit 0
} finally {
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}
