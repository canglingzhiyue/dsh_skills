#Requires -Version 5.1
<#
    Camoufox 逆向控制台 —— 双击 camoufox.cmd 即可打开。

    这里集中了所有"平时会忘、需要时又找不到"的动作：环境自检、
    可视化扫码登录、持久 profile 登录、引擎预热、路径与版本速查。
#>

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py   = Join-Path $Root '.venv\Scripts\python.exe'
$Docs = Join-Path $Root '使用说明.md'

$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

function Write-Header {
    Clear-Host
    Write-Host ''
    Write-Host '  ============================================================' -ForegroundColor DarkCyan
    Write-Host '              Camoufox 逆向控制台  (Windows)' -ForegroundColor Cyan
    Write-Host '  ============================================================' -ForegroundColor DarkCyan
    Write-Host "   工作区: $Root" -ForegroundColor DarkGray
    Write-Host ''
}

function Show-Menu {
    Write-Host '   [1]  环境自检（依赖 / 引擎 / 定制版 / 登录态）' -ForegroundColor White
    Write-Host '   [2]  可视化登录并保存登录态   -> states\<站点>.json' -ForegroundColor White
    Write-Host '   [3]  持久 profile 登录        -> profiles\<站点>\（含 IndexedDB）' -ForegroundColor White
    Write-Host '   [4]  安装信息速查（路径 / 版本 / MCP 配置位置）' -ForegroundColor White
    Write-Host '   [5]  打开使用说明' -ForegroundColor White
    Write-Host '   [6]  打开 states / profiles / logs 目录' -ForegroundColor White
    Write-Host '   [7]  预热引擎缓存（首次装机 / MCP 报 JSON 解析错误时）' -ForegroundColor Yellow
    Write-Host '   [0]  退出' -ForegroundColor DarkGray
    Write-Host ''
}

function Assert-Env {
    if (-not (Test-Path $Py)) {
        Write-Host "  [错误] 找不到虚拟环境解释器：$Py" -ForegroundColor Red
        Write-Host '         请先按 使用说明.md 的「重建环境」一节恢复。' -ForegroundColor Red
        Read-Host '  按回车返回'
        return $false
    }
    return $true
}

function Invoke-Login {
    param([switch]$Persistent)

    $name = Read-Host '  站点标识（英文/数字，例如 douyin、taobao）'
    if ([string]::IsNullOrWhiteSpace($name)) { Write-Host '  已取消' -ForegroundColor DarkGray; return }
    $url = Read-Host '  登录页 URL（例如 https://www.douyin.com）'
    if ([string]::IsNullOrWhiteSpace($url)) { Write-Host '  已取消' -ForegroundColor DarkGray; return }

    $pyArgs = @((Join-Path $Root 'bin\login_session.py'), '--url', $url.Trim(), '--name', $name.Trim())
    if ($Persistent) { $pyArgs += '--persistent' }

    Write-Host ''
    & $Py @pyArgs
}

function Show-InstallInfo {
    Write-Host ''
    Write-Host '  组件位置' -ForegroundColor Cyan
    $rows = @(
        @{ k = 'Python 环境     '; v = (Join-Path $Root '.venv') },
        @{ k = 'MCP server 源码 '; v = (Join-Path $Root 'camoufox-reverse-mcp') },
        @{ k = 'CPython（独立） '; v = (Join-Path $Root '.uv-python') },
        @{ k = '引擎缓存(联接)  '; v = "$env:LOCALAPPDATA\camoufox  ->  $Root\.engine\camoufox" },
        @{ k = '登录态          '; v = (Join-Path $Root 'states') },
        @{ k = '持久 profile    '; v = (Join-Path $Root 'profiles') },
        @{ k = '日志            '; v = (Join-Path $Root 'logs') },
        @{ k = 'DSH 接入配置    '; v = "$env:USERPROFILE\.dsh\profiles\web\cordis.patch.yml" }
    )
    foreach ($row in $rows) { Write-Host ("   {0} {1}" -f $row.k, $row.v) }

    Write-Host ''
    Write-Host '  MCP server 启动命令（DSH 会自动拉起，一般不用手敲）' -ForegroundColor Cyan
    Write-Host "   $Py -m camoufox_reverse_mcp --locale zh-CN"

    if (Test-Path $Py) {
        Write-Host ''
        Write-Host '  版本速查' -ForegroundColor Cyan
        & $Py -c "import importlib.metadata as m
for p in ('camoufox','playwright','camoufox-reverse-mcp','mcp'):
    try: print(f'   {p:<24} {m.version(p)}')
    except Exception: print(f'   {p:<24} 未安装')"
    }
}

function Open-Folders {
    foreach ($dir in @('states', 'profiles', 'logs')) {
        $full = Join-Path $Root $dir
        if (-not (Test-Path $full)) { New-Item -ItemType Directory -Force -Path $full | Out-Null }
    }
    Start-Process explorer.exe $Root
    Write-Host '  已在资源管理器中打开工作区。' -ForegroundColor Green
}

# ---------------------------------------------------------------- main loop
while ($true) {
    Write-Header
    Show-Menu
    $choice = Read-Host '   请选择'

    switch ($choice) {
        '1' { if (Assert-Env) { & $Py (Join-Path $Root 'bin\check_env.py') } }
        '2' { if (Assert-Env) { Invoke-Login } }
        '3' { if (Assert-Env) { Invoke-Login -Persistent } }
        '4' { Show-InstallInfo }
        '5' {
            if (Test-Path $Docs) { Start-Process $Docs }
            else { Write-Host "  说明书还没生成：$Docs" -ForegroundColor Yellow }
        }
        '6' { Open-Folders }
        '7' { if (Assert-Env) { & $Py (Join-Path $Root 'bin\warmup.py') } }
        '0' { break }
        default { Write-Host '  无效选择' -ForegroundColor Yellow }
    }

    if ($choice -eq '0') { break }
    Write-Host ''
    Read-Host '  按回车返回菜单' | Out-Null
}

Write-Host ''
Write-Host '  再见。' -ForegroundColor DarkGray
