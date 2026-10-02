#Requires -Version 7.0
<#
.SYNOPSIS
    逆向模式能力扫描器 —— 生成 capabilities.json / capabilities.md，并做悬空引用检查。

.DESCRIPTION
    本机工具、MCP 挂载、DSH 插件、模拟器与技能的**唯一事实源**由本脚本生成。
    技能正文不写死本机工具：装了新工具后重跑本脚本，逆向模式就"知道"它了。

    只读探测：不安装任何东西，不修改任何被探测对象，不写被探测目录之外的路径。
    唯一的副作用是 `adb devices` 会拉起 adb server（可用 -SkipDevice 跳过）。

.PARAMETER DshHome
    DSH 主目录。默认取 $env:DSH_HOME，否则 ~\.dsh

.PARAMETER OutDir
    输出目录。默认 <DshHome>\reverse

.PARAMETER SkipDevice
    跳过 adb 设备探测（不启动 adb server）。

.EXAMPLE
    pwsh -File scan-capabilities.ps1

.EXAMPLE
    pwsh -File scan-capabilities.ps1 -SkipDevice -OutDir D:\tmp\cap
#>
[CmdletBinding()]
param(
    [string]$DshHome = $(if ($env:DSH_HOME) { $env:DSH_HOME } else { Join-Path $HOME '.dsh' }),
    [string]$OutDir,
    [switch]$SkipDevice
)

$ErrorActionPreference = 'Continue'
if (-not $OutDir) { $OutDir = Join-Path $DshHome 'reverse' }
$SkillRoot = Join-Path $DshHome 'skills'
$ProfilesRoot = Join-Path $DshHome 'profiles'
$generatedAt = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')

# ── helpers ─────────────────────────────────────────────────────────────────

function Resolve-Candidate {
    param([string]$Spec)
    if ([string]::IsNullOrWhiteSpace($Spec)) { return $null }
    if ($Spec -match '[\*\?]') {
        $hits = @(Get-ChildItem -Path $Spec -ErrorAction SilentlyContinue | Sort-Object FullName)
        if ($hits.Count -eq 0) { return $null }
        return $hits[-1].FullName
    }
    if (Test-Path -LiteralPath $Spec) { return (Get-Item -LiteralPath $Spec).FullName }
    return $null
}

function Invoke-Probe {
    param([string]$Exe, [string[]]$Argv, [int]$TimeoutMs = 5000)
    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $Exe
        if ($Argv) { foreach ($a in $Argv) { $psi.ArgumentList.Add($a) } }
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        $outTask = $proc.StandardOutput.ReadToEndAsync()
        $errTask = $proc.StandardError.ReadToEndAsync()
        if (-not $proc.WaitForExit($TimeoutMs)) {
            try { $proc.Kill($true) } catch { }
            return $null
        }
        $txt = ($outTask.Result + "`n" + $errTask.Result).Trim()
        if ([string]::IsNullOrWhiteSpace($txt)) { return $null }
        return (($txt -split "`r?`n") | Where-Object { $_.Trim() } | Select-Object -First 1).Trim()
    }
    catch { return $null }
}

function Test-ListeningPort {
    param([int]$Port)
    try {
        $c = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
        return [bool]$c
    }
    catch { return $false }
}

# ── 1. 工具候选表 ───────────────────────────────────────────────────────────
# Paths 支持通配符（取排序后最后一个，即最高版本目录）；Cmd 用于 PATH 查找。

$specs = @(
    # Android / 设备
    @{ n = 'adb';            k = 'android'; p = @('D:\ProgramsDev\adb\adb.exe'); c = 'adb'; v = @('version') }
    @{ n = 'apksigner';      k = 'android'; p = @('D:\ProgramsDev\Android\SDK\build-tools\*\apksigner.bat'); c = 'apksigner'; v = @() }
    @{ n = 'zipalign';       k = 'android'; p = @('D:\ProgramsDev\Android\SDK\build-tools\*\zipalign.exe'); c = 'zipalign'; v = @() }
    @{ n = 'aapt2';          k = 'android'; p = @('D:\ProgramsDev\Android\SDK\build-tools\*\aapt2.exe'); c = 'aapt2'; v = @() }
    @{ n = 'jadx-gui';       k = 'android'; p = @('D:\ProgramsDev\jadx-gui-1.5.2-with-jre-win\jadx-gui-1.5.2.exe'); c = ''; v = @() }
    @{ n = 'jadx-cli-jar';   k = 'android'; p = @('D:\ProgramsDev\jadx-gui-1.5.2-with-jre-win\lib\jadx-gui-1.5.2-all.jar'); c = ''; v = @() }
    @{ n = 'apktool';        k = 'android'; p = @(); c = 'apktool'; v = @() }
    @{ n = 'frida-cli';      k = 'android'; p = @(); c = 'frida'; v = @('--version') }
    @{ n = 'objection';      k = 'android'; p = @(); c = 'objection'; v = @('version') }
    @{ n = 'scrcpy';         k = 'android'; p = @(); c = 'scrcpy'; v = @('--version') }
    @{ n = 'ldconsole';      k = 'android'; p = @('D:\leidian\LDPlayer9\ldconsole.exe'); c = ''; v = @() }
    @{ n = 'android-sdk';    k = 'android'; p = @('D:\ProgramsDev\Android\SDK'); c = ''; v = @() }
    @{ n = 'emulator';       k = 'android'; p = @('D:\ProgramsDev\Android\SDK\emulator\emulator.exe'); c = ''; v = @() }
    @{ n = 'firerpa-venv';   k = 'android'; p = @('D:\AI_python\firerpa\.venv\Scripts\python.exe'); c = ''; v = @('-V') }
    # 二进制 / 原生
    @{ n = 'ida';            k = 'binary';  p = @('D:\ProgramsDev\IDA Professional 9.4\ida.exe'); c = ''; v = @() }
    @{ n = 'idalib';         k = 'binary';  p = @('D:\ProgramsDev\IDA Professional 9.4\idalib.dll'); c = ''; v = @() }
    @{ n = 'ghidra';         k = 'binary';  p = @(); c = 'ghidraRun'; v = @() }
    @{ n = 'radare2';        k = 'binary';  p = @(); c = 'r2'; v = @('-v') }
    @{ n = 'x64dbg';         k = 'binary';  p = @(); c = 'x64dbg'; v = @() }
    @{ n = 'dnSpy';          k = 'binary';  p = @(); c = 'dnSpy'; v = @() }
    # Web / 小程序
    @{ n = 'wmpfdebugger';   k = 'web';     p = @('D:\AI_python\reverse\vmpfdebugger\package.json'); c = ''; v = @() }
    @{ n = 'camoufox-venv';  k = 'web';     p = @('D:\AI_python\camoufox\.venv\Scripts\python.exe'); c = ''; v = @('-V') }
    @{ n = 'camoufox-cmd';   k = 'web';     p = @('D:\AI_python\camoufox\camoufox.cmd'); c = ''; v = @() }
    # 网络 / 抓包
    @{ n = 'mitmdump';       k = 'network'; p = @('C:\Users\y\.local\bin\mitmdump.exe'); c = 'mitmdump'; v = @('--version') }
    @{ n = 'fiddler';        k = 'network'; p = @('D:\ProgramsDev\Fiddler\Fiddler.exe'); c = ''; v = @() }
    @{ n = 'reqable';        k = 'network'; p = @('D:\ProgramsDev\reqable\Reqable.exe'); c = ''; v = @() }
    # 运行时
    @{ n = 'pwsh';           k = 'runtime'; p = @(); c = 'pwsh'; v = @('-NoProfile', '-Command', '$PSVersionTable.PSVersion.ToString()') }
    @{ n = 'uv';             k = 'runtime'; p = @(); c = 'uv'; v = @('--version') }
    @{ n = 'uvx';            k = 'runtime'; p = @(); c = 'uvx'; v = @('--version') }
    @{ n = 'python';         k = 'runtime'; p = @(); c = 'python'; v = @('--version') }
    @{ n = 'node';           k = 'runtime'; p = @(); c = 'node'; v = @('--version') }
    @{ n = 'pnpm';           k = 'runtime'; p = @(); c = 'pnpm'; v = @('--version') }
    @{ n = 'java';           k = 'runtime'; p = @(); c = 'java'; v = @('-version') }
    @{ n = 'git';            k = 'runtime'; p = @(); c = 'git'; v = @('--version') }
)

$tools = @()
foreach ($s in $specs) {
    $path = $null
    foreach ($cand in @($s.p)) {
        $path = Resolve-Candidate -Spec $cand
        if ($path) { break }
    }
    $via = 'path-file'
    if (-not $path -and $s.c) {
        $cmd = Get-Command $s.c -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { $path = $cmd.Source; $via = 'PATH' }
    }
    # （历史）anaconda 曾是本机 PATH 上 python/uv/uvx 的实际来源；2026-09-30 已整机移除，
    # 当 python/pip 用。这里如实记录并告警，而不是隐藏——隐藏会让"MCP 依赖
    # anaconda 里的 uv"变成幽灵依赖。检测逻辑保留，用于识别新引入的同类污染。
    $risk = $null
    if ($path -and $path -match '\\anaconda') {
        $risk = 'anaconda：dev-hygiene 禁止当 python/pip 用；此处仅作事实记录'
    }
    $entry = [ordered]@{
        name    = $s.n
        kind    = $s.k
        status  = if ($path) { 'present' } else { 'missing' }
        path    = $path
        via     = if ($path) { $via } else { $null }
        version = $null
        risk    = $risk
    }
    if ($path -and $s.v -and $s.v.Count -gt 0) {
        $entry.version = Invoke-Probe -Exe $path -Argv @($s.v)
    }
    $tools += $entry
}

# ── 2. MCP 挂载（从 profile 的 cordis.patch.yml + agent preset 的 composition 解析） ──
#
# MCP 能挂在两层，**语义完全不同，必须分开标注**：
#   - profile 层（host 组装）：`dsh web` 一启动就 spawn 全部服务器，所有会话都能
#     看到它的工具 —— 代价是常驻进程与启动期同步等待（dsh-mcp-client 的 apply()
#     要等「连接 + tools/list」完成，且没有懒加载配置项）。layer = 'profile'。
#   - agent preset 层：只有**新会话真的选中该 preset** 时才 compose（`dsh-agent-presets`
#     的 "reading never mounts" —— preset 是 DSH 里唯一的惰性挂载点），所以进程
#     按需启动，工具也只对该 preset 的会话可见。layer = 'preset'。
#
# 2026-10-02 起本机 4 个逆向 MCP 全部从 profile 层移入 preset `reverse`：
# 于是 `dsh web` 启动与普通会话零 MCP 进程，只有「逆向模式」会话才拉起它们。
# 用工具前先看**层**这一列 —— preset 层的 MCP 在普通会话里根本不存在，
# 要调用它必须先新开一个逆向模式会话。

$mcpPorts = @{ 'jadx' = 8650; 'ida' = 0; 'camoufox' = 0; 'analyzer' = 23816 }

function Read-McpFromFile {
    <#
      解析一个 composition 文件里的 dsh-mcp-client 条目。
      只认「出现 serverName: 之后紧邻的缩进键」，所以同文件里别的列表项不会误入。
    #>
    param([string]$Path, [string]$Layer, [string]$Owner)
    $found = @()
    if (-not (Test-Path -LiteralPath $Path)) { return $found }
    $cur = $null
    foreach ($ln in @(Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
        if ($ln -match 'serverName:\s*''?([A-Za-z0-9_\-]+)''?') {
            if ($cur) { $found += $cur }
            $cur = [ordered]@{
                serverName = $Matches[1]; layer = $Layer; owner = $Owner
                profile = $(if ($Layer -eq 'profile') { $Owner } else { $null })
                preset = $(if ($Layer -eq 'preset') { $Owner } else { $null })
                command = $null; transport = $null; url = $null
                args = @(); timeoutMs = $null; failOnStartupError = $null
                externalPrerequisite = $null; probe = $null
            }
            continue
        }
        if (-not $cur) { continue }
        # 遇到下一个顶层条目（`- id:` / `- name:`）说明本行已结束
        if ($ln -match '^-\s+(id|name):') { $found += $cur; $cur = $null; continue }
        if ($ln -match 'transport:\s*''?([A-Za-z\-]+)''?\s*$') { $cur.transport = $Matches[1].Trim(); continue }
        if ($ln -match 'url:\s*''?([^''\r\n]+?)''?\s*$') { $cur.url = $Matches[1].Trim(); continue }
        if ($ln -match 'command:\s*''?([^''\r\n]+?)''?\s*$') { $cur.command = $Matches[1].Trim(); continue }
        if ($ln -match '^\s+-\s+''?([^'':\r\n]+?)''?\s*$') { $cur.args += $Matches[1].Trim(); continue }
        if ($ln -match 'toolCallTimeoutMs:\s*(\d+)') { $cur.timeoutMs = [int]$Matches[1]; continue }
        if ($ln -match 'failOnStartupError:\s*(\S+)') { $cur.failOnStartupError = $Matches[1]; continue }
    }
    if ($cur) { $found += $cur }
    return $found
}

$mcp = @()
# profile 层：host 组装，启动即拉起
if (Test-Path -LiteralPath $ProfilesRoot) {
    foreach ($prof in @(Get-ChildItem -LiteralPath $ProfilesRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'node_modules' })) {
        $mcp += Read-McpFromFile -Path (Join-Path $prof.FullName 'cordis.patch.yml') -Layer 'profile' -Owner $prof.Name
    }
}
# preset 层：按需，只在选中该 preset 的新会话里存在
$AgentsRoot = Join-Path $DshHome '.agent-presets'
if (Test-Path -LiteralPath $AgentsRoot) {
    foreach ($preset in @(Get-ChildItem -LiteralPath $AgentsRoot -Directory -ErrorAction SilentlyContinue)) {
        $mcp += Read-McpFromFile -Path (Join-Path $preset.FullName 'agent.cordis.yml') -Layer 'preset' -Owner $preset.Name
    }
}

foreach ($m in $mcp) {
    switch ($m.serverName) {
        'jadx' { $m.externalPrerequisite = 'JADX-GUI 必须开启并装 jadx-ai-mcp 插件（默认 127.0.0.1:8650）' }
        'ida' { $m.externalPrerequisite = '本机 IDA 9.4 + idalib（路径见 %APPDATA%\Hex-Rays\IDA Pro\ida-config.json）' }
        'camoufox' { $m.externalPrerequisite = 'D:\AI_python\camoufox 独立 venv；首次使用先预热' }
        'analyzer' { $m.externalPrerequisite = 'Anything Analyzer GUI 必须处于运行状态（MCP Server 跑在 Electron 主进程里）；探活 pwsh -File $env:USERPROFILE\.dsh\skills\anything-analyzer\scripts\probe-mcp.ps1' }
        default { $m.externalPrerequisite = $null }
    }
    if ($mcpPorts.ContainsKey($m.serverName) -and $mcpPorts[$m.serverName] -gt 0) {
        $m.probe = "port $($mcpPorts[$m.serverName]) listening = $(Test-ListeningPort -Port $mcpPorts[$m.serverName])"
    }
}

# ── 3. DSH 插件（profile 里非 @deepseek-ai/* 的依赖） ───────────────────────

$plugins = @()
if (Test-Path -LiteralPath $ProfilesRoot) {
    foreach ($prof in @(Get-ChildItem -LiteralPath $ProfilesRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'node_modules' })) {
        $pkgPath = Join-Path $prof.FullName 'package.json'
        if (-not (Test-Path -LiteralPath $pkgPath)) { continue }
        try { $pkg = Get-Content -LiteralPath $pkgPath -Raw | ConvertFrom-Json } catch { continue }
        $deps = @{}
        if ($pkg.dependencies) { $pkg.dependencies.PSObject.Properties | ForEach-Object { $deps[$_.Name] = $_.Value } }
        $bundles = @()
        if ($pkg.dsh -and $pkg.dsh.profile -and $pkg.dsh.profile.bundles) { $bundles = @($pkg.dsh.profile.bundles) }
        foreach ($name in $deps.Keys) {
            if ($name -like '@deepseek-ai/*') { continue }
            $plugins += [ordered]@{
                profile = $prof.Name; name = $name; spec = $deps[$name]
                bundle = ($bundles -contains $name)
            }
        }
    }
}

# ── 4. 技能 ─────────────────────────────────────────────────────────────────

$skills = @()
foreach ($d in @(Get-ChildItem -LiteralPath $SkillRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name)) {
    $sk = Join-Path $d.FullName 'SKILL.md'
    $hasSk = Test-Path -LiteralPath $sk
    $bytes = 0; $desc = ''; $files = 0
    $files = @(Get-ChildItem -LiteralPath $d.FullName -Recurse -File -ErrorAction SilentlyContinue).Count
    if ($hasSk) {
        $bytes = (Get-Item -LiteralPath $sk).Length
        $head = @(Get-Content -LiteralPath $sk -TotalCount 12 -ErrorAction SilentlyContinue)
        for ($i = 0; $i -lt $head.Count; $i++) {
            if ($head[$i] -match '^description:\s*(.+)$') {
                $desc = $Matches[1].Trim().Trim('"', "'")
                if ($desc -in @('>-', '|', '|-', '>')) {
                    $buf = @()
                    for ($j = $i + 1; $j -lt $head.Count; $j++) {
                        if ($head[$j] -match '^\S') { break }
                        $buf += $head[$j].Trim()
                    }
                    $desc = ($buf -join ' ')
                }
                break
            }
        }
    }
    $skills += [ordered]@{ name = $d.Name; hasSkillMd = $hasSk; skillMdBytes = $bytes; files = $files; description = $desc }
}

# ── 5. 设备 ─────────────────────────────────────────────────────────────────

$devices = @()
$adbTool = $tools | Where-Object { $_.name -eq 'adb' -and $_.status -eq 'present' } | Select-Object -First 1
if ($adbTool -and -not $SkipDevice) {
    try {
        $raw = & $adbTool.path devices -l 2>&1 | Select-Object -Skip 1
        foreach ($line in @($raw)) {
            $t = "$line".Trim()
            if (-not $t) { continue }
            $parts = $t -split '\s+'
            $devices += [ordered]@{ serial = $parts[0]; state = $parts[1]; detail = ($parts[2..($parts.Count - 1)] -join ' ') }
        }
    }
    catch { }
}

# ── 6. 域注册表 + 悬空引用检查 ──────────────────────────────────────────────

$domains = @()
$dangling = @()
$registryPath = Join-Path $SkillRoot 'reverse-skill-router\references\domain-registry.json'
if (Test-Path -LiteralPath $registryPath) {
    try {
        $reg = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
        foreach ($d in @($reg.domains)) {
            $prim = @($d.primarySkills); $sup = @($d.supportingSkills)
            $present = @(); $missing = @()
            foreach ($n in ($prim + $sup)) {
                if (Test-Path -LiteralPath (Join-Path $SkillRoot $n)) { $present += $n } else { $missing += $n }
            }
            if ($missing.Count -gt 0) {
                $dangling += [ordered]@{ domain = $d.id; missingSkills = $missing; fix = 'install the skill, restore it from the inventory, or update references/domain-registry.json' }
            }
            $domains += [ordered]@{
                id = $d.id; label = $d.label; depth = $d.depth
                primarySkills = $prim; supportingSkills = $sup
                supportRoles = $d.supportRoles
                present = $present; missing = $missing
            }
        }
    }
    catch {
        $dangling += [ordered]@{ domain = '*'; missingSkills = @(); fix = "domain-registry.json 解析失败：$($_.Exception.Message)" }
    }
}
else {
    $dangling += [ordered]@{ domain = '*'; missingSkills = @(); fix = "缺少域注册表：$registryPath" }
}

# ── 7. 告警 ─────────────────────────────────────────────────────────────────

$warnings = @()
foreach ($t in $tools) {
    if ($t.status -eq 'missing' -and $t.kind -in @('android')) {
        $warnings += "工具缺失：$($t.name)（Android 域的部分流程会降级，见 apk-reverse/references/toolchain.md）"
    }
    if ($t.risk) {
        $warnings += "anaconda 污染：$($t.name) 解析到 $($t.path) —— 不得用它装 python 包（dev-hygiene 红线）；MCP 若依赖它，属幽灵依赖：anaconda 升级或卸载会连带打断 MCP"
    }
}
foreach ($m in $mcp) {
    if ($m.probe -match 'listening = False') {
        # preset 层的 MCP 是**按需**的：没有逆向模式会话在跑时，它的进程本来就不该存在
        # —— 端口没监听是正常态，不是故障。只有 profile（常驻）层才说明前置真的缺失。
        $suffix = if ($m.layer -eq 'preset') {
            "（注意：该 MCP 挂在 preset ``$($m.preset)``，属**按需**启动 —— 没有逆向模式会话在跑时它本就不该监听，此告警属正常态；先新建/使用一个逆向模式会话再复测）"
        } else { '' }
        $warnings += "MCP [$($m.serverName)] 外部前置未就绪：$($m.externalPrerequisite)$suffix"
    }
    if ($m.failOnStartupError -eq 'false') {
        $where = if ($m.layer -eq 'preset') { "preset ``$($m.preset)``，按需" } else { 'profile 层，常驻' }
        $warnings += "MCP [$($m.serverName)]（$where）配了 failOnStartupError: false —— 前置缺失时它静默失效，用工具前先探活"
    }
}
if ($dangling.Count -gt 0) { $warnings += "存在悬空技能引用 $($dangling.Count) 条（见 danglingReferences）" }

# ── 8. 输出 ─────────────────────────────────────────────────────────────────

$cap = [ordered]@{
    schemaVersion    = 1
    generatedAt      = $generatedAt
    generatedBy      = $MyInvocation.MyCommand.Path
    host             = [ordered]@{
        os       = 'Windows'
        dshHome  = $DshHome
        pwsh     = $PSVersionTable.PSVersion.ToString()
        profiles = @(Get-ChildItem -LiteralPath $ProfilesRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'node_modules' } | ForEach-Object { $_.Name })
    }
    mcpServers       = $mcp
    skills           = $skills
    plugins          = $plugins
    tools            = $tools
    devices          = $devices
    domains          = $domains
    danglingReferences = $dangling
    warnings         = $warnings
}

if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
$jsonPath = Join-Path $OutDir 'capabilities.json'
$mdPath = Join-Path $OutDir 'capabilities.md'
$cap | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding utf8

# 人读版
$md = [System.Collections.Generic.List[string]]::new()
$md.Add('# 本机逆向能力清单')
$md.Add('')
$md.Add("> **自动生成，请勿手改。** 由 ``reverse-skill-router\scripts\scan-capabilities.ps1`` 生成于 $generatedAt。")
$md.Add('> 装了新工具 / 新挂了 MCP / 增删了技能之后，重跑该脚本即可让逆向模式知道；技能正文不写死本机路径。')
$md.Add('')
$md.Add('## 0. 概览')
$md.Add('')
$md.Add("- OS: Windows ｜ DSH_HOME: ``$DshHome`` ｜ pwsh: $($PSVersionTable.PSVersion) ｜ profile: $((@(Get-ChildItem -LiteralPath $ProfilesRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'node_modules' } | ForEach-Object { $_.Name })) -join ', ')")
$md.Add("- 域就绪度：" + ((@($domains | ForEach-Object { "$($_.id)=$($_.depth)" })) -join ' ｜ '))
$md.Add("- MCP: $(@($mcp).Count) ｜ 技能: $(@($skills).Count) ｜ 插件: $(@($plugins).Count) ｜ 设备: $(@($devices).Count)")
$md.Add('')
$md.Add('## 1. MCP 服务器（模型可直接调用）')
$md.Add('')
$md.Add('> **先看「层」这一列**：`profile` = 常驻（`dsh web` 启动即拉起，所有会话可见）；')
$md.Add('> `preset:<id>` = **按需**（只有选中该 preset 的新会话才 compose，普通会话里不存在这组工具）。')
$md.Add('')
$md.Add('| serverName | 层 | 归属 | command | 外部前置 | 探测 |')
$md.Add('|---|---|---|---|---|---|')
foreach ($m in $mcp) {
    $probeText = if ([string]::IsNullOrWhiteSpace($m.probe)) { '-' } else { $m.probe }
    # stdio 挂载显示 command；streamable-http 挂载没有 command，显示 url
    $cmdText = if ($m.command) { $m.command } elseif ($m.url) { "$($m.transport) $($m.url)" } else { '' }
    $layerText = if ($m.layer -eq 'preset') { "preset:$($m.preset)" } else { 'profile（常驻）' }
    $ownerText = if ($m.layer -eq 'preset') { '预设会话' } else { $m.profile }
    $md.Add("| ``$($m.serverName)`` | $layerText | $ownerText | ``$cmdText`` | $($m.externalPrerequisite) | $probeText |")
}
$md.Add('')
$md.Add('## 2. 本机工具')
$md.Add('')
$md.Add('| 名称 | 类别 | 状态 | 路径 | 版本 | 风险 |')
$md.Add('|---|---|---|---|---|---|')
foreach ($t in ($tools | Sort-Object kind, name)) {
    $md.Add("| $($t.name) | $($t.kind) | $($t.status) | ``$($t.path)`` | $($t.version) | $($t.risk) |")
}
$md.Add('')
$md.Add('## 3. DSH 插件（非 @deepseek-ai/*）')
$md.Add('')
$md.Add('| 包 | profile | 来源 spec | 是否 bundle |')
$md.Add('|---|---|---|---|')
foreach ($p in $plugins) {
    $md.Add("| ``$($p.name)`` | $($p.profile) | ``$($p.spec)`` | $($p.bundle) |")
}
$md.Add('')
$md.Add('## 4. 技能')
$md.Add('')
$md.Add('| 技能 | SKILL.md 字节 | 文件数 | 说明 |')
$md.Add('|---|---|---|---|')
foreach ($s in $skills) {
    $d = $s.description; if ($d.Length -gt 160) { $d = $d.Substring(0, 157) + '...' }
    $md.Add("| $($s.name) | $($s.skillMdBytes) | $($s.files) | $d |")
}
$md.Add('')
$md.Add('## 5. 设备与模拟器')
$md.Add('')
if ($devices.Count -eq 0) { $md.Add('（未探测到设备；-SkipDevice 时本行恒为空）') }
else {
    $md.Add('| serial | state | detail |')
    $md.Add('|---|---|---|')
    foreach ($d in $devices) { $md.Add("| ``$($d.serial)`` | $($d.state) | $($d.detail) |") }
}
$md.Add('')
$md.Add('## 6. 域注册表')
$md.Add('')
$md.Add('| 域 | 深度 | 主技能 | 支撑技能 | 缺失 |')
$md.Add('|---|---|---|---|---|')
foreach ($d in $domains) {
    $md.Add("| $($d.label) (``$($d.id)``) | $($d.depth) | $($d.primarySkills -join ', ') | $($d.supportingSkills -join ', ') | $($d.missing -join ', ') |")
}
$md.Add('')
$md.Add('### 支撑技能角色')
$md.Add('')
foreach ($d in $domains) {
    if ($d.supportRoles) {
        foreach ($p in $d.supportRoles.PSObject.Properties) {
            $md.Add("- **$($d.id) / $($p.Name)**：$($p.Value)")
        }
    }
}
$md.Add('')
$md.Add('## 7. 告警')
$md.Add('')
if ($warnings.Count -eq 0) { $md.Add('无。') }
else { foreach ($w in $warnings) { $md.Add("- $w") } }
$md.Add('')
if ($dangling.Count -gt 0) {
    $md.Add('### 悬空技能引用（必须修）')
    $md.Add('')
    foreach ($dg in $dangling) { $md.Add("- 域 ``$($dg.domain)``：缺少 $($dg.missingSkills -join ', ') —— $($dg.fix)") }
    $md.Add('')
}
$md | Set-Content -LiteralPath $mdPath -Encoding utf8

Write-Host "capabilities.json -> $jsonPath"
Write-Host "capabilities.md   -> $mdPath"
Write-Host ("tools: {0} present / {1} missing | skills: {2} | mcp: {3} | devices: {4} | warnings: {5}" -f `
    (@($tools | Where-Object { $_.status -eq 'present' }).Count), (@($tools | Where-Object { $_.status -eq 'missing' }).Count), `
    @($skills).Count, @($mcp).Count, @($devices).Count, @($warnings).Count)
