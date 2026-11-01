# Reqable MCP health probe.
#
# What it does
#   1. checks mcp-server.exe exists and REQABLE_TOKEN is set
#   2. checks the Reqable GUI process is alive and the API port answers
#   3. performs a real MCP stdio handshake: initialize -> tools/list -> tools/call
#   4. prints PASS/FAIL lines and exits non-zero on failure
#
# Usage
#   pwsh -NoProfile -File probe-mcp.ps1
#   pwsh -NoProfile -File probe-mcp.ps1 -Scope minimal
#   pwsh -NoProfile -File probe-mcp.ps1 -ApiPort 9000
#
# Exit codes: 0 = all good, 1 = token/exe missing, 2 = GUI/API down, 3 = MCP failure
param(
  [string]$Scope = 'all',
  [int]$ApiPort = 0,
  [string]$Exe = 'D:\ProgramsDev\reqable\mcp-server.exe'
)

$fail = 0
function Ok($m)   { Write-Output "PASS: $m" }
function Bad($m)  { Write-Output "FAIL: $m"; $script:fail++ }

# ---- 1. exe + token ----
if (-not (Test-Path $Exe)) { Bad "mcp-server.exe not found: $Exe"; exit 1 }
Ok "mcp-server.exe found"

$tok = [Environment]::GetEnvironmentVariable('REQABLE_TOKEN', 'User')
if (-not $tok) { $tok = $env:REQABLE_TOKEN }
if (-not $tok) { Bad 'REQABLE_TOKEN not set (user env or process env)'; exit 1 }
Ok "REQABLE_TOKEN present ($($tok.Length) chars)"

# ---- 2. GUI + API port ----
$proc = Get-Process Reqable -ErrorAction SilentlyContinue
if (-not $proc) { Bad 'Reqable GUI is not running - start D:\ProgramsDev\reqable\Reqable.exe first' }
else { Ok "Reqable GUI running (pid $($proc.Id -join ','))" }

if ($ApiPort -le 0) {
  $cfg = "$env:APPDATA\Reqable\config\capture_config.json"
  $ApiPort = 9000
  if (Test-Path $cfg) {
    try { $ApiPort = (Get-Content $cfg -Raw | ConvertFrom-Json).proxyPort } catch { }
  }
}
$h = @{ Authorization = "Bearer $tok" }
try {
  $r = Invoke-WebRequest "http://127.0.0.1:$ApiPort/capture/live/status" -Headers $h -TimeoutSec 8 -SkipHttpErrorCheck
  if ($r.StatusCode -eq 200) { Ok "API $($ApiPort) reachable: $($r.Content)" }
  elseif ($r.StatusCode -eq 401) { Bad "API $ApiPort rejected token (401) - regenerate REQABLE_TOKEN" }
  else { Bad "API $ApiPort returned HTTP $($r.StatusCode)" }
} catch { Bad "API $ApiPort unreachable on 127.0.0.1 (GUI not ready?): $($_.Exception.Message)" }

# ---- 3. MCP stdio handshake ----
if ($fail -gt 0 -and -not $proc) { Write-Output 'SKIP: MCP handshake (GUI down)'; exit 2 }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $Exe
$psi.Arguments = "--scope $Scope"
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.EnvironmentVariables['REQABLE_TOKEN'] = $tok
$p = [System.Diagnostics.Process]::Start($psi)

function Send([string]$json) { $p.StandardInput.WriteLine($json); $p.StandardInput.Flush() }
function ReadId([int]$expectId, [int]$timeoutMs = 15000) {
  $deadline = (Get-Date).AddMilliseconds($timeoutMs)
  while ((Get-Date) -lt $deadline) {
    $t = $p.StandardOutput.ReadLineAsync()
    if (-not $t.Wait(2000)) { continue }
    $l = $t.Result
    if ($null -eq $l) { return $null }
    try { $j = $l | ConvertFrom-Json; if ($j.id -eq $expectId) { return $j } } catch { }
  }
  return $null
}

Send '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"dsh-probe","version":"1.0"}}}'
$init = ReadId 1
if ($init) { Ok "MCP initialize: $($init.result.serverInfo.name) v$($init.result.serverInfo.version)" }
else { Bad 'MCP initialize timed out' }

Send '{"jsonrpc":"2.0","method":"notifications/initialized"}'
Send '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
$tl = ReadId 2 20000
if ($tl) {
  $n = $tl.result.tools.Count
  if ($Scope -eq 'all' -and $n -ne 146) { Write-Output "WARN: scope=all expected 146 tools, got $n (version drift?)" }
  if ($Scope -eq 'minimal' -and $n -ne 48) { Write-Output "WARN: scope=minimal expected 48 tools, got $n (version drift?)" }
  Ok "tools/list returned $n tools (scope=$Scope)"
} else { Bad 'tools/list timed out' }

Send '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"capture_live_status","arguments":{}}}'
$call = ReadId 3 20000
if ($call -and $call.result) { Ok "tools/call capture_live_status -> $(($call.result | ConvertTo-Json -Depth 6 -Compress))" }
elseif ($call -and $call.error) { Bad "tools/call failed: $(($call.error | ConvertTo-Json -Depth 6 -Compress))" }
else { Bad 'tools/call timed out' }

try { if (-not $p.HasExited) { $p.Kill() } } catch { }

Write-Output ''
if ($fail -eq 0) { Write-Output 'RESULT: OK - Reqable MCP is usable'; exit 0 }
else { Write-Output "RESULT: FAIL ($fail problem(s))"; exit 3 }
