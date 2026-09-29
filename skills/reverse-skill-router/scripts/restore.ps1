#Requires -Version 7.0
<#
.SYNOPSIS
  重建 reverse-skill 路由包（克隆 → 工具清单 → 路由自检 → 冒烟）。
.DESCRIPTION
  对应 skills/reverse-skill-router/references/重建配方.md。安全约束：
  - 克隆按**审查过的 commit** pin（用 -Commit 覆盖），不追 main 浮动版本；
  - 代理从 -Proxy 或环境变量 REVERSE_SKILL_PROXY 取，**不硬编码**内网地址；
  - 已存在仓库时只刷新 + 自检，加 -Pull 才更新（更新后 commit 变了需重新核对）；
  - **不运行** bootstrap-reverse.*（装工具必须先经用户同意）；
  - **永不运行** update-star-history.ps1（它会读本机 git 凭据并外发）。
.EXAMPLE
  pwsh -NoProfile -File restore.ps1
.EXAMPLE
  $env:REVERSE_SKILL_PROXY='http://<proxy-host>:<port>'; .\restore.ps1
.EXAMPLE
  .\restore.ps1 -Pull      # 显式更新到上游最新
#>
[CmdletBinding()]
param(
    [string] $RepoPath = (Join-Path $env:USERPROFILE '.dsh\reverse-skill'),
    [string] $Proxy    = $env:REVERSE_SKILL_PROXY,
    [string] $Commit   = '7e2097fd90d25c2f976f6eba26d6c00aa88051df',
    [switch] $Pull
)

$ErrorActionPreference = 'Stop'
$RepoUrl = 'https://github.com/zhaoxuya520/reverse-skill.git'
$gitProxy = @()
if (-not [string]::IsNullOrWhiteSpace($Proxy)) { $gitProxy = @('-c', "http.proxy=$Proxy", '-c', "https.proxy=$Proxy") }
function Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }

if (-not (Test-Path (Join-Path $RepoPath 'RULES.md'))) {
    Step "克隆 reverse-skill 到 $RepoPath（pin $($Commit.Substring(0,7))）"
    New-Item -ItemType Directory -Force -Path $RepoPath | Out-Null
    git -C $RepoPath init -q
    git -C $RepoPath remote get-url origin 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { git -C $RepoPath remote add origin $RepoUrl }
    git -C $RepoPath @gitProxy fetch --depth 1 origin $Commit
    if ($LASTEXITCODE -ne 0) { throw "fetch 失败：检查代理（-Proxy 或 `$env:REVERSE_SKILL_PROXY）与网络" }
    git -C $RepoPath checkout -q FETCH_HEAD
}
else {
    Step "仓库已存在：$RepoPath"
    if ($Pull) {
        Step '更新到上游最新（不是审查过的 commit）'
        git -C $RepoPath @gitProxy fetch --depth 1 origin main
        if ($LASTEXITCODE -ne 0) { Write-Warning 'git fetch 失败，继续用当前版本' }
        else {
            git -C $RepoPath checkout -q FETCH_HEAD
            Write-Host ("HEAD 现在是 " + (git -C $RepoPath rev-parse HEAD) + "；与审查过的 " +
                $Commit.Substring(0,7) + " 不同的话，请重新核对再使用") -ForegroundColor Yellow
        }
    }
}

Step '生成本机工具清单 tool-index.md'
pwsh -NoProfile -File (Join-Path $RepoPath 'skills\scripts\refresh-tool-index.ps1')

Step '路由自洽自检'
pwsh -NoProfile -File (Join-Path $RepoPath 'skills\scripts\verify-routing-coherence.ps1')

Step '冒烟：master-route'
$smokeOut = Join-Path $env:TEMP 'rs-smoke'
New-Item -ItemType Directory -Force -Path $smokeOut | Out-Null
pwsh -NoProfile -File (Join-Path $RepoPath 'skills\scripts\master-route.ps1') `
    -Hint 'offline apk reverse jadx' -OutDir $smokeOut

Step ("完成：commit " + (git -C $RepoPath rev-parse --short HEAD))
Write-Host '红线：缺工具先报清单并问用户，不要自行跑 skills\scripts\bootstrap-reverse.ps1；' -ForegroundColor Yellow
Write-Host '      永不运行 skills\scripts\update-star-history.ps1 与 skills\ida-reverse\scripts\install-autostart.ps1。' -ForegroundColor Yellow
