<#
.SYNOPSIS
    从本 skill 自带的轻量备份，重建整套 Camoufox 逆向环境。

.DESCRIPTION
    只重下"有来源"的大件（Python 环境、浏览器引擎、MCP 源码），自制的脚本与说明书
    直接从本 skill 目录复制过去。整套备份不到 100 KB，重建后约 2.2 GB。

    不包含、也不会碰：登录态（states\*.json）与持久 profile（profiles\）——那是本机
    敏感数据，迁移后重新登录一次即可。

.EXAMPLE
    pwsh -File restore.ps1
    pwsh -File restore.ps1 -Root E:\camoufox
    pwsh -File restore.ps1 -SkipEngines          # 只建 venv + MCP
#>
[CmdletBinding()]
param(
    [string]$Root = 'D:\AI_python\camoufox',
    [string]$McpRepo = 'https://github.com/WhiteNightShadow/camoufox-reverse-mcp.git',
    [string]$OfficialTag = 'v152.0.4-beta.30',
    [string]$OfficialAsset = 'camoufox-152.0.4-beta.30-win.x86_64.zip',
    [string]$OfficialSha256 = 'ea52a02fb1cfb1813ef6a326bea03fb2b650c9774143d953a94a27bfc8f10072',
    [string]$ReverseTag = 'v152.0.4-beta.30-reverse.5',
    [string]$ReverseAsset = 'camoufox-152.0.4-beta.30-win.x86_64.zip',
    [string]$ReverseSha256 = 'd73704543a759a224371a8f3019f02ffa3a96fb446b25b7a856f5203b8e2153b',
    [switch]$SkipEngines
)

$ErrorActionPreference = 'Stop'
$SkillDir = Split-Path -Parent $PSScriptRoot          # ...\camoufox-reverse
$RefDir   = Join-Path $SkillDir 'references'
$Venv     = Join-Path $Root '.venv'
$Py       = Join-Path $Venv 'Scripts\python.exe'
$Bin      = Join-Path $Root 'bin'
$Downloads = Join-Path $Root '.downloads'

function Step($n, $text) { Write-Host ''; Write-Host "== [$n] $text" -ForegroundColor Cyan }
function Ok($text)       { Write-Host "   [ OK ] $text" -ForegroundColor Green }
function Warn($text)     { Write-Host "   [WARN] $text" -ForegroundColor Yellow }

function Download-File($url, $out) {
    if ((Test-Path $out) -and (Get-Item $out).Length -gt 0) { Ok "已存在，跳过：$(Split-Path -Leaf $out)"; return }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out) | Out-Null
    Write-Host "   下载 $url"
    & $Py -c "import urllib.request,shutil,sys; r=urllib.request.urlopen(sys.argv[1],timeout=300); f=open(sys.argv[2],'wb'); shutil.copyfileobj(r,f,1048576); f.close()" $url $out
    if ($LASTEXITCODE -ne 0) { throw "下载失败：$url" }
    Ok "已下载 $(Split-Path -Leaf $out)"
}

# ---------------------------------------------------------------- 0. 前置检查
Step 0 '前置检查'
foreach ($tool in @('uv', 'git', 'node')) {
    $cmd = Get-Command $tool -ErrorAction SilentlyContinue
    if ($cmd) { Ok "$tool -> $($cmd.Source)" } else { Warn "$tool 未找到（$tool 相关步骤会跳过或失败）" }
}
New-Item -ItemType Directory -Force -Path $Root, $Bin, $Downloads, (Join-Path $Root 'states'), (Join-Path $Root 'logs') | Out-Null

# ------------------------------------------------- 1. 复制自制的脚本与说明书
Step 1 '复制自制脚本与说明书'
foreach ($file in Get-ChildItem $PSScriptRoot -File) {
    if ($file.Name -eq 'restore.ps1') { continue }
    $dest = if ($file.Extension -eq '.cmd') { Join-Path $Root $file.Name } else { Join-Path $Bin $file.Name }
    Copy-Item $file.FullName $dest -Force
}
foreach ($file in Get-ChildItem $RefDir -File -ErrorAction SilentlyContinue) {
    if ($file.Name -like '*使用说明*') { Copy-Item $file.FullName (Join-Path $Root $file.Name) -Force }
}
Ok '脚本 -> bin\，控制台入口与说明书 -> 工作区根'

# --------------------------------------------- 2. 引擎缓存目录联接（必须先建）
Step 2 '把引擎缓存接到工作区内'
$link   = Join-Path $env:LOCALAPPDATA 'camoufox'
$target = Join-Path $Root '.engine\camoufox'
New-Item -ItemType Directory -Force -Path $target | Out-Null
if (Test-Path $link) {
    $item = Get-Item $link -Force
    if ($item.LinkType -eq 'Junction') { Ok "联接已存在：$link" }
    else { throw "$link 已存在且不是联接；先手工处理（里面可能有引擎数据），再重跑本脚本。" }
} else {
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Ok "已建联接：$link -> $target"
}

# ------------------------------------------------------------ 3. venv + 依赖
Step 3 'Python 环境'
if (Test-Path $Py) {
    Ok "venv 已存在：$Venv"
} else {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) { throw '缺少 uv。请先装 uv（或改用系统 Python: python -m venv .venv）后重跑。' }
    & uv venv --python 3.12 --python-preference only-managed $Venv
    if ($LASTEXITCODE -ne 0) { throw 'uv venv 创建失败' }
    & $Py -m ensurepip --upgrade | Out-Null
    Ok "venv 已创建：$Venv"
}
& $Py -m pip install -q -U "camoufox[geoip]"
Ok 'camoufox[geoip] 就绪'

# --------------------------------------------------------------- 4. MCP 源码
Step 4 'MCP server 源码'
$mcpDir = Join-Path $Root 'camoufox-reverse-mcp'
if (Test-Path (Join-Path $mcpDir '.git')) {
    & git -C $mcpDir pull --ff-only
    Ok '已 git pull 更新'
} else {
    & git clone --depth 1 $McpRepo $mcpDir
    if ($LASTEXITCODE -ne 0) { throw 'git clone 失败' }
    Ok '已 clone'
}
& $Py -m pip install -q -e $mcpDir
Ok 'camoufox-reverse-mcp 已可编辑安装'

if ($SkipEngines) {
    Warn '按 -SkipEngines 跳过引擎下载；浏览器此时不可用。'
} else {
    # ------------------------------------------------------- 5. 官方引擎
    Step 5 "官方引擎 $OfficialTag"
    & $Py (Join-Path $Bin 'install-camoufox-browser.py') $OfficialTag $OfficialAsset $OfficialSha256
    if ($LASTEXITCODE -ne 0) { throw '官方引擎安装失败' }

    # ------------------------------------------------------- 6. 定制版引擎
    Step 6 "定制版引擎 $ReverseTag（77 点引擎追踪）"
    $base = "https://github.com/WhiteNightShadow/camoufox-reverse/releases/download/$ReverseTag"
    Download-File "$base/SHA256SUMS" (Join-Path $Downloads 'SHA256SUMS')
    Download-File "$base/install-camoufox-reverse.py" (Join-Path $Downloads 'install-camoufox-reverse.py')
    Download-File "$base/$ReverseAsset" (Join-Path $Downloads $ReverseAsset)
    & $Py (Join-Path $Downloads 'install-camoufox-reverse.py') (Join-Path $Downloads $ReverseAsset) --sha256 $ReverseSha256
    if ($LASTEXITCODE -ne 0) { throw '定制版引擎安装失败' }
}

# --------------------------------------------------------------- 7. 预热 + 验证
if (-not $SkipEngines) {
    Step 7 '预热引擎缓存（必做，见 使用说明.md §6.1）'
    & $Py (Join-Path $Bin 'warmup.py')
    Step 8 '端到端冒烟测试'
    & $Py (Join-Path $Bin 'mcp_smoke_test.py') --browser
}

# ------------------------------------------------------------------- 收尾
Step 9 '下一步（DSH 接入）'
Write-Host @"
   把下面这段贴进 `$DSH_HOME\profiles\web\cordis.patch.yml`（profile 是 patchReload: live，几秒生效）：

- insert:
    - id: mcp-camoufox-reverse
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: camoufox
        transport: stdio
        command: '$Py'
        args: ['-m', 'camoufox_reverse_mcp', '--locale', 'zh-CN']
        env:
          PYTHONUTF8: '1'
          PYTHONIOENCODING: 'utf-8'
        toolCallTimeoutMs: 120000

   验证： dsh --profile web --dump-config | Select-String 'mcp-camoufox-reverse'
   说明书： $Root\使用说明.md      控制台： $Root\camoufox.cmd
"@ -ForegroundColor Gray
Write-Host '重建完成。' -ForegroundColor Green
