<#
  install.ps1 —— 从 dsh_skills 仓库一键恢复 DSH 环境（skill + MCP + 第三方插件 + 常驻规则）

  用法：
    pwsh -File install.ps1                  # 执行（会先备份现有配置）
    pwsh -File install.ps1 -DryRun          # 只打印将要做的事，不落盘
    pwsh -File install.ps1 -SkipPlugins     # 跳过插件安装（没有 pnpm/网络时）
    pwsh -File install.ps1 -DshHome D:\x\.dsh -Profile web

  做得到的：skill 内容、常驻规则、DSH 设置、profile 配置、agent preset（**4 个 MCP 的挂载就在
  presets\reverse\ 里**，2026-10-02 起从 profile 层移入，按需启动）、第三方插件安装。
  做不到的：各 skill 背后的运行时（GB 级，需联网重建）与登录态 —— 见脚本末尾的待办清单。
  永不恢复：凭据（.credentials.yaml）、登录 session —— 需人工填。

  注意：本文件含中文，必须保存为 UTF-8 with BOM（Windows PowerShell 5.1 会按 ANSI 解析无 BOM 的中文）。
#>
[CmdletBinding()]
param(
  [string]$DshHome = "$env:USERPROFILE\.dsh",
  [string]$Profile = 'web',
  [switch]$DryRun,
  [switch]$SkipSkills,
  [switch]$SkipPresets,
  [switch]$SkipConfig,
  [switch]$SkipPlugins
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

function Step($n, $msg) { Write-Host "`n=== [$n] $msg ===" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "  [ok]   $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  [warn] $m" -ForegroundColor Yellow }
function Info($m) { Write-Host "         $m" -ForegroundColor Gray }
function Die($m)  { Write-Host "  [fail] $m" -ForegroundColor Red; exit 1 }

function Copy-IfChanged($src, $dst) {
  if (-not (Test-Path $src)) { Warn "源不存在，跳过：$src"; return }
  $dir = Split-Path $dst -Parent
  if (-not (Test-Path $dir)) { if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $dir | Out-Null } }
  if ((Test-Path $dst) -and ((Get-FileHash $src).Hash -eq (Get-FileHash $dst).Hash)) { Ok "已一致，跳过：$dst"; return }
  if ($DryRun) { Info "将写入：$dst"; return }
  Copy-Item $src $dst -Force
  Ok "写入：$dst"
}

Write-Host "dsh_skills 一键恢复" -ForegroundColor White
Write-Host "  仓库根    : $Root"
Write-Host "  DSH_HOME  : $DshHome"
Write-Host "  profile   : $Profile"
if ($DryRun) { Write-Host "  *** DRY RUN —— 不会写任何文件 ***" -ForegroundColor Yellow }

# ---------------------------------------------------------------- 0. 前置检查
Step 0 '前置检查'

if ($PSVersionTable.PSVersion.Major -lt 7) { Warn "当前 PowerShell $($PSVersionTable.PSVersion)，建议 pwsh 7" }
else { Ok "pwsh $($PSVersionTable.PSVersion)" }

foreach ($c in @('git', 'node')) {
  if (Get-Command $c -ErrorAction SilentlyContinue) { Ok "$c 可用" } else { Warn "$c 缺失 —— 相关步骤会失败" }
}
if (Get-Command pnpm -ErrorAction SilentlyContinue) { Ok 'pnpm 可用' } else { Warn 'pnpm 缺失 —— 插件装不了（dsh plugin 依赖它）' }
if (Get-Command uv -ErrorAction SilentlyContinue) { Ok 'uv 可用' } else { Warn 'uv 缺失 —— 部分运行时的重建需要它' }
if (Get-Command dsh -ErrorAction SilentlyContinue) { Ok 'dsh 可用' } else { Warn 'dsh 不在 PATH —— 插件需手动装' }
if (-not (Test-Path $DshHome)) { Die "DSH_HOME 不存在：$DshHome（先安装并启动一次 DSH）" }

$profileDir = Join-Path $DshHome "profiles\$Profile"
if (-not (Test-Path $profileDir)) { Warn "profile 目录不存在：$profileDir（会在需要时创建）" }

# ---------------------------------------------------------------- 备份现有配置
Step 1 '备份现有配置'

$bk = Join-Path $DshHome "_restore_backup_$stamp"
$toBackup = @(
  (Join-Path $DshHome 'AGENTS.md'),
  (Join-Path $DshHome 'settings.yaml'),
  (Join-Path $profileDir 'cordis.patch.yml'),
  (Join-Path $profileDir 'package.json'),
  (Join-Path $profileDir 'pnpm-workspace.yaml'),
  (Join-Path $profileDir 'cordis.yml')
)
$existing = $toBackup | Where-Object { Test-Path $_ }
if ($existing.Count -eq 0) { Ok '没有需要备份的现有配置（全新环境）' }
elseif ($DryRun) { Info "将备份 $($existing.Count) 个文件到 $bk" }
else {
  New-Item -ItemType Directory -Force -Path $bk | Out-Null
  foreach ($f in $existing) { Copy-Item $f (Join-Path $bk (Split-Path $f -Leaf)) -Force }
  Ok "已备份 $($existing.Count) 个文件 → $bk"
  Info '（出错时可从这里还原；确认无误后可删）'
}

# ---------------------------------------------------------------- 2. skill
if (-not $SkipSkills) {
  Step 2 '恢复 skill → $DSH_HOME/skills/'
  $src = Join-Path $Root 'skills'
  if (-not (Test-Path $src)) { Warn "仓库里没有 skills/，跳过" }
  else {
    $names = Get-ChildItem $src -Directory | Select-Object -ExpandProperty Name
    Info "共 $($names.Count) 个：$($names -join '、')"
    foreach ($n in $names) {
      $s = Join-Path $src $n
      $d = Join-Path $DshHome "skills\$n"
      if ($DryRun) { Info "将复制 $n → $d" ; continue }
      New-Item -ItemType Directory -Force -Path $d | Out-Null
      Copy-Item "$s\*" $d -Recurse -Force
      Ok "$n（$((Get-ChildItem -Recurse $s -File).Count) 文件）"
    }
  }
} else { Step 2 '恢复 skill —— 已跳过' }

# ------------------------------------------------- 2b. agent preset（第四类资产）
if (-not $SkipPresets) {
  Step '2b' '恢复 agent preset → $DSH_HOME/.agent-presets/'
  $psrc = Join-Path $Root 'presets'
  if (-not (Test-Path $psrc)) { Warn '仓库里没有 presets/，跳过' }
  else {
    $ids = Get-ChildItem $psrc -Directory | Select-Object -ExpandProperty Name
    Info "共 $($ids.Count) 个：$($ids -join '、')"
    foreach ($id in $ids) {
      $s = Join-Path $psrc $id
      $d = Join-Path $DshHome ".agent-presets\$id"
      if ($DryRun) { Info "将复制 preset $id → $d" ; continue }
      New-Item -ItemType Directory -Force -Path $d | Out-Null
      Copy-Item "$s\*" $d -Recurse -Force
      Ok "preset $id（$((Get-ChildItem -Recurse $s -File).Count) 文件）"
    }
    Warn 'preset 只是 composition：它引用的 skill 必须先装好'
    Warn '本机 4 个逆向 MCP 的挂载就在 presets\reverse\ 里 —— 装 preset 即装好 MCP（按需启动）'
    Warn '验证挂载请新开一个该 preset 的会话（preset_probe 已不存在）；roster 的 broken:false 不算验证'
    Warn '逆向模式的 persona 第一步要读 $DSH_HOME\reverse\capabilities.md —— 需跑一次 scan-capabilities.ps1 生成它'
  }
} else { Step '2b' '恢复 agent preset —— 已跳过' }

# ---------------------------------------------------------------- 3. 常驻规则 + DSH 设置
if (-not $SkipConfig) {
  Step 3 '恢复常驻规则与 DSH 设置'
  Copy-IfChanged (Join-Path $Root 'config\AGENTS.md')    (Join-Path $DshHome 'AGENTS.md')
  Copy-IfChanged (Join-Path $Root 'config\settings.yaml') (Join-Path $DshHome 'settings.yaml')
  Info '注意：settings.yaml 里的模型 provider 按本机情况保留了原值，新环境可能要改'
  Info '注意：AGENTS.md 顶部的「账本目录」路径需按新环境改'
} else { Step 3 '恢复配置 —— 已跳过' }

# ---------------------------------------------------------------- 4. MCP 挂载 + profile 配置
if (-not $SkipConfig) {
  Step 4 '恢复 MCP 挂载与 profile 配置'
  if (-not (Test-Path $profileDir)) { if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $profileDir | Out-Null } }
  Copy-IfChanged (Join-Path $Root 'config\cordis.patch.yml')            (Join-Path $profileDir 'cordis.patch.yml')
  Copy-IfChanged (Join-Path $Root 'config\profile\package.json')        (Join-Path $profileDir 'package.json')
  Copy-IfChanged (Join-Path $Root 'config\profile\pnpm-workspace.yaml') (Join-Path $profileDir 'pnpm-workspace.yaml')
  Copy-IfChanged (Join-Path $Root 'config\profile\cordis.yml')          (Join-Path $profileDir 'cordis.yml')
  # MCP 挂载现在有两层：profile（常驻）与 agent preset（按需）。两层都要报，
  # 否则 2026-10-02 迁移后这里会显示"一个都没有"。
  $mcpSources = @()
  $profilePatch = Join-Path $Root 'config\cordis.patch.yml'
  if (Test-Path $profilePatch) { $mcpSources += $profilePatch }
  $presetsDir = Join-Path $Root 'presets'
  if (Test-Path $presetsDir) { $mcpSources += @(Get-ChildItem $presetsDir -Recurse -Filter 'agent.cordis.yml' -File | Select-Object -ExpandProperty FullName) }
  $mcp = @()
  foreach ($src in $mcpSources) {
    $layer = if ($src -eq $profilePatch) { 'profile/常驻' } else { "preset/按需($(Split-Path (Split-Path $src -Parent) -Leaf))" }
    $names = (Select-String -Path $src -Pattern 'serverName:\s*''?([A-Za-z0-9_\-]+)' -AllMatches).Matches |
             ForEach-Object { $_.Groups[1].Value }
    foreach ($n in $names) { $mcp += "$n [$layer]" }
  }
  if ($mcp.Count -gt 0) { Ok "MCP 挂载：$($mcp -join '、')" } else { Warn '没扫到任何 MCP 挂载 —— 检查 config 与 presets' }
  Warn '这些 MCP 依赖外部运行时（如 D:\AI_python\camoufox、jadx-mcp-server）—— 见末尾待办'
  Warn 'preset 层的是按需启动：只有新开该 preset 的会话才会拉起；普通会话看不到这些 mcp__* 工具'
} else { Step 4 '恢复 MCP/profile —— 已跳过' }

# ---------------------------------------------------------------- 5. 第三方插件
if (-not $SkipPlugins) {
  Step 5 "安装第三方插件（profile: $Profile）"
  $specs = @(
    'github:Len7183/DSH-Think-zh',
    '@liustack/modsearch@5.10.3',
    'github:CAOGGL/dsh-ding',
    'https://github.com/howmp/dsh-pentest/releases/latest/download/dsh-pentest.tar.gz'
  )
  Info 'spec 的权威来源是 plugins/<name>/RECIPE.md —— 若不一致以 RECIPE 为准'
  if (-not (Get-Command dsh -ErrorAction SilentlyContinue)) {
    Warn 'dsh 不在 PATH，跳过插件安装'
  } else {
    foreach ($sp in $specs) {
      if ($DryRun) { Info "将执行：dsh plugin --profile $Profile add $sp" ; continue }
      Info "dsh plugin --profile $Profile add $sp"
      & dsh plugin --profile $Profile add $sp
      if ($LASTEXITCODE -ne 0) { Warn "安装失败（$sp）—— 见 plugins/*/RECIPE.md 的排错与 allowBuilds 说明" }
      else { Ok "已装 $sp" }
    }
  }
  Warn '插件装在 profile 的 bundle 层，运行中不热加载 —— 装完必须重启 DSH'
} else { Step 5 '安装插件 —— 已跳过' }

# ---------------------------------------------------------------- 6. 待办清单
Step 6 '还需人工完成的部分（脚本代替不了）'
Write-Host @'
  1) 重建各 skill 背后的运行时（体积大，需联网；部分需要代理）
       firerpa            : uv venv + uv pip install "lamda[full]"（约 160 MB）
                            见 skills/firerpa/SKILL.md §2.5
       camoufox-reverse   : 浏览器引擎 + venv（约 2.3 GB），跑它自带的 scripts\restore.ps1
       wmpf-miniapp-reverse: WMPFDebugger + node_modules（约 165 MB），跑 scripts\restore.ps1（需代理）
       reverse-skill-router: git clone 上游仓库到 $DSH_HOME\reverse-skill（约 12 MB），跑 scripts\restore.ps1
       jadx MCP           : D:\AI_python\MCP\MCP合集\jadx-mcp-server（uv 环境，约 41 MB）
       ida MCP            : 需本机 IDA 9.4+ 且 idalib 已激活（跑一次 <IDADIR>\idalib\python\py-activate-idalib.py，
                            路径写进 %APPDATA%\HexRays\IDA Pro\ida-config.json）；MCP 本体由 uvx 跑 PyPI 包，
                            没有独立运行时目录。GUI 插件可选（**装完重启 IDA**）：
                            uvx ida-hcli plugin install 'ida-mcp@https://github.com/hexrayssa/ida-mcp'
                            报 PEP 668 / not a virtual environment 时先跑：uvx ida-hcli ida python create-environment
                            （hcli 不读 git 代理，需自行给 HTTP_PROXY/HTTPS_PROXY）
       context-mode MCP   : 已按用户要求于 2026-09-29 整体卸载（弃用）。恢复机器时**不要安装**；
                            它当初是为了省上下文（沙箱跑代码只回传结论），用户实测后认为用处不大。
                            另：曾为它写过自动路由插件 ctx-router（已一并卸载）。仅当用户重新要求时才装：
                            npm install -g context-mode + profile 挂 mcp-context-mode + 重建 ctx-router
                            （配方在 git 历史里：git show c3eab63 --stat；账本 plugins\ 两个自制件目录
                            已随卸载移入回收站，可用 git checkout c3eab63 -- plugins/ 取回）
       donsetch 插件      : 已按用户要求于 2026-09-28 卸载（弃用）。恢复机器时**不要安装**；
                             仅当用户重新要求时：dsh plugin --profile web add github:dondai44423/donsetch-dsh
                             （配方见 plugins\donsetch\RECIPE.md；装后需给 daemon 配代理池）
  2) 凭据（永不进仓库，必须手填）
       $DSH_HOME\.credentials.yaml —— DEEPSEEK_API_KEY / CLAUDEX_API_KEY / DS_1ZHE_API_KEY
  3) 登录态（永不进仓库）
       camoufox 的 states\ / profiles\ —— 需要重新登录目标站点
  4) 检查并修改硬编码路径
       presets\reverse\agent.cordis.yml 里的 D:\AI_python\... 路径（4 个 MCP 的 command/args 都在这）
       AGENTS.md 顶部的「账本目录」路径
       settings.yaml 里的 provider / baseURL
  4b) analyzer 的凭据（可选，仅在启用鉴权时需要）
       $DSH_HOME\.env 里加 ANALYZER_MCP_TOKEN=<token>（取自 %APPDATA%\anything-analyzer\
       mcp-server-config.json 的 authToken）。**不入仓库**；.env 只在启动时读取 → 需重启 DSH
  5) 重启 DSH —— 插件在启动时组合（MCP 现在挂在 agent preset 里 = 按需，不需要重启就生效；
     profile 补丁 patchReload:live 时热加载；插件目录类改动仍需重启）
'@ -ForegroundColor Gray

Write-Host "`n完成（自动部分）。" -ForegroundColor White
if ($existing.Count -gt 0) { Write-Host "原配置备份在：$bk" -ForegroundColor Gray }
