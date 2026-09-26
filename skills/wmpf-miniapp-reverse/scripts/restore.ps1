#Requires -Version 7.0
<#
.SYNOPSIS
    一键重建 WMPFDebugger 环境（微信小程序逆向工具）。

.DESCRIPTION
    按 references\重建配方.md 的顺序执行：
      1) 检查前置（node >= 22 / corepack / git）
      2) clone 上游仓库（已存在则跳过）
      3) 设置代理并 yarn install（frida 预编译二进制 115 MB，**必须**走代理）
      4) 把本 skill 的两个启动脚本落位到工具目录
      5) 校验：tsc --noEmit、ts-node、frida 本地设备
    最后打印仍需手工做的事（打开小程序、粘贴 devtools 链接）。

.PARAMETER Root
    工具目录，默认 D:\AI_python\reverse\vmpfdebugger。

.PARAMETER Proxy
    安装期 HTTP/HTTPS 代理，例如 http://127.0.0.1:7890。
    不给则读 $env:HTTPS_PROXY；都没有时仍会尝试直连（frida 二进制多半会超时）。

.PARAMETER Repo
    上游仓库地址，默认 https://github.com/evi0s/WMPFDebugger.git

.PARAMETER SkipClone
    跳过 clone（工具目录已存在时用）。

.PARAMETER SkipInstall
    跳过 yarn install（只落位脚本与自检）。

.EXAMPLE
    pwsh -File scripts\restore.ps1 -Root D:\AI_python\reverse\vmpfdebugger -Proxy http://127.0.0.1:7890
#>
[CmdletBinding()]
param(
    [string]$Root = 'D:\AI_python\reverse\vmpfdebugger',
    [string]$Proxy = '',
    [string]$Repo = 'https://github.com/evi0s/WMPFDebugger.git',
    [switch]$SkipClone,
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path $PSScriptRoot -Parent
$fail = 0

function Step($msg) { Write-Host "`n=== $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "  [ok] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  [warn] $msg" -ForegroundColor Yellow; $script:fail++ }

# ---------- 1) 前置 ----------
Step "1/5 检查前置依赖"
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) { throw "未找到 node（要求 >= LTS v22）" }
$nodeMajor = [int]((node -v).TrimStart('v').Split('.')[0])
if ($nodeMajor -lt 22) { throw "node 版本过低：$(node -v)，要求 >= 22" }
Ok "node $(node -v)"

if (-not (Get-Command corepack -ErrorAction SilentlyContinue)) { throw "未找到 corepack（随 node 一起分发）" }
Ok "corepack 存在"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "未找到 git" }
Ok "git 存在"

# ---------- 2) clone ----------
Step "2/5 准备工具目录 $Root"
if ($SkipClone) {
    Ok "按 -SkipClone 跳过 clone"
} elseif (Test-Path (Join-Path $Root '.git')) {
    Ok "已是 git 仓库，跳过 clone（需要更新时在目录里 git pull）"
} else {
    if (-not (Test-Path $Root)) { New-Item -ItemType Directory -Force -Path $Root | Out-Null }
    if (Get-ChildItem $Root -Force | Select-Object -First 1) {
        Warn "$Root 非空且不是 git 仓库，跳过 clone（请自行确认目录内容）"
    } else {
        git clone --depth 1 $Repo $Root
        if ($LASTEXITCODE -ne 0) { throw "git clone 失败（exit $LASTEXITCODE）" }
        Ok "clone 完成（main 分支，depth 1）"
    }
}

# ---------- 3) 依赖 ----------
Step "3/5 安装依赖（frida 预编译二进制约 115 MB，需要代理）"
if ($SkipInstall) {
    Ok "按 -SkipInstall 跳过 yarn install"
} else {
    if (-not $Proxy) { $Proxy = $env:HTTPS_PROXY }
    if ($Proxy) {
        $env:HTTP_PROXY = $Proxy
        $env:HTTPS_PROXY = $Proxy
        Ok "代理：$Proxy"
    } else {
        Warn "未提供代理（-Proxy / `$env:HTTPS_PROXY），frida 二进制下载很可能超时"
    }
    $env:COREPACK_ENABLE_DOWNLOAD_PROMPT = '0'
    Push-Location $Root
    try {
        corepack yarn install --frozen-lockfile --non-interactive
        if ($LASTEXITCODE -ne 0) { throw "yarn install 失败（exit $LASTEXITCODE）" }
        Ok "yarn install 完成（yarn.lock 锁定版本，勿删）"
    } finally {
        Pop-Location
    }
}

# ---------- 4) 落位脚本 ----------
Step "4/5 落位启动脚本到工具目录"
foreach ($name in 'start-debugger.ps1', 'open-devtools.ps1') {
    $src = Join-Path $PSScriptRoot $name
    $dst = Join-Path $Root $name
    if (-not (Test-Path $src)) { Warn "skill 里缺少 $name"; continue }
    Copy-Item $src $dst -Force
    Ok "已复制 $name"
}

# ---------- 5) 校验 ----------
Step "5/5 校验"
if (-not (Test-Path (Join-Path $Root 'node_modules'))) {
    Warn "没有 node_modules，跳过校验（先去掉 -SkipInstall 重跑）"
} else {
    Push-Location $Root
    try {
        node node_modules\typescript\bin\tsc --noEmit
        if ($LASTEXITCODE -eq 0) { Ok "tsc --noEmit 通过" } else { Warn "tsc --noEmit 失败（exit $LASTEXITCODE）" }

        & (Join-Path $Root 'node_modules\.bin\ts-node.cmd') --version | Out-Null
        if ($LASTEXITCODE -eq 0) { Ok "ts-node 可用" } else { Warn "ts-node 不可用" }

        $js = 'const f=require("frida");f.getLocalDevice().then(d=>{console.log("  [ok] frida device: "+d.name);process.exit(0)}).catch(e=>{console.log("  [warn] frida 自检失败: "+e.message);process.exit(1)})'
        node -e $js
        if ($LASTEXITCODE -ne 0) { Warn "frida 本地设备不可用" }
    } finally {
        Pop-Location
    }
}

Write-Host "`n=== 完成（warn 数：$fail）" -ForegroundColor Cyan
Write-Host @"

还需手工做的：
  1) 确认微信正在运行（进程 WeChatAppEx.exe），并确认 frida\config\win32\addresses.<WMPF版本>.json 存在
     —— 版本号看任务管理器里 WeChatAppEx 的路径：...\RadiumWMPF\<版本>\extracted\runtime\...
  2) 关掉全局代理 / TUN（否则小程序会闪退）
  3) 启动：  $Root\start-debugger.ps1
  4) 打开（或关掉重开）目标小程序
  5) 打开前端：$Root\open-devtools.ps1  ->  浏览器地址栏 Ctrl+L / Ctrl+V / 回车

排障：node $skillRoot\scripts\probe-cdp.js
"@ -ForegroundColor Gray
