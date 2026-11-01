# Call Reqable's local HTTP API directly (no MCP needed).
#
# Use when:
#   - mcp__reqable__* tools are not mounted in this session
#   - you need one call inside a bigger PowerShell pipeline
#   - you want to verify the API layer while debugging MCP
#
# Usage:
#   pwsh -NoProfile -File reqable-api.ps1 -Path /capture/live/status
#   pwsh -NoProfile -File reqable-api.ps1 -Path /capture/live/on -Method Post -Body '{}'
#   pwsh -NoProfile -File reqable-api.ps1 -Path /capture/live/filter -Method Post -Body '{"filters":[{"type":"host","hosts":["www.baidu.com"]}]}'
#   pwsh -NoProfile -File reqable-api.ps1 -Path /capture/live/get -Method Post -Body '{"id":2}' -Raw
#
# Notes:
#   - token comes from the user env var REQABLE_TOKEN; never pass it on the command line
#   - port defaults to proxyPort from %APPDATA%\Reqable\config\capture_config (NO extension; fallback 9000)
#   - /capture/live/filter and /capture/live/get ONLY accept POST
param(
  [Parameter(Mandatory = $true)][string]$Path,
  [ValidateSet('Get', 'Post', 'Put', 'Delete')][string]$Method = 'Get',
  [string]$Body = '',
  [int]$Port = 0,
  [switch]$Raw
)

$tok = [Environment]::GetEnvironmentVariable('REQABLE_TOKEN', 'User')
if (-not $tok) { $tok = $env:REQABLE_TOKEN }
if (-not $tok) { Write-Output 'ERROR: REQABLE_TOKEN not set (user env or process env)'; exit 1 }

if ($Port -le 0) {
  $Port = 9000
  $cfg = "$env:APPDATA\Reqable\config\capture_config"
  if (Test-Path $cfg) { try { $Port = (Get-Content $cfg -Raw | ConvertFrom-Json).proxyPort } catch { } }
}

if (-not $Path.StartsWith('/')) { $Path = "/$Path" }
$uri = "http://127.0.0.1:$Port$Path"
$headers = @{ Authorization = "Bearer $tok" }

$params = @{
  Uri             = $uri
  Method          = $Method
  Headers         = $headers
  TimeoutSec      = 30
  SkipHttpErrorCheck = $true
}
if ($Body) { $params.Body = $Body; $params.ContentType = 'application/json' }

try {
  $r = Invoke-WebRequest @params
} catch {
  Write-Output "ERROR: $($_.Exception.Message)"
  exit 2
}

if ($Raw) {
  Write-Output $r.Content
} else {
  Write-Output "HTTP $($r.StatusCode) $Method $Path"
  Write-Output $r.Content
}
if ($r.StatusCode -ge 400) { exit 3 }
