#Requires -Version 7.0
<#
.SYNOPSIS
    删除文件 / 目录 —— 默认送进 Windows 回收站，绝不静默硬删。

.DESCRIPTION
    dev-hygiene 的唯一删除实现。失败即抛异常并停止，不会降级成永久删除。
    只有显式 -HardDelete（且属于"可重建的大体积产物"豁免清单）才永久删除，且必须给出 -Reason。

.PARAMETER Path
    要删除的路径，支持多项、通配符与相对路径。找不到任何匹配项则报错且不删任何东西。

.PARAMETER HardDelete
    永久删除（绕过回收站）。仅用于豁免清单：项目 .venv、uv 缓存、node_modules、构建中间物，
    以及 %TEMP% 下本次会话自建的临时文件。

.PARAMETER Reason
    配合 -HardDelete 必填：说明它为什么属于豁免清单。

.EXAMPLE
    pwsh -File Remove-ToRecycleBin.ps1 '.\__pycache__' '.\tmp' -WhatIf

.EXAMPLE
    pwsh -File Remove-ToRecycleBin.ps1 '.\__pycache__'

.EXAMPLE
    # 在 pwsh 会话内直接调用时，才可以用 -Path 数组
    & .\Remove-ToRecycleBin.ps1 -Path '.\tmp', '.\a.txt' -WhatIf

.EXAMPLE
    pwsh -File Remove-ToRecycleBin.ps1 '.\.venv' -HardDelete -Reason '项目完事；uv.lock 与 HANDOVER 重建命令已实测'

.NOTES
    PowerShell 不允许重复指定同一个命名参数（`-Path a -Path b` 会报错），
    而从 pwsh 外部经 `pwsh -File` 调用时逗号数组也传不进去（会被当成单个字符串 "a,b"）。
    因此：外部调用一律用位置参数，会话内才用 -Path 数组。
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Low')]
param(
    # 支持三种调用形式：重复 -Path a -Path b / 位置参数 a b / 会话内 & 调用时 -Path a,b
    [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)]
    [string[]] $Path,

    [switch] $HardDelete,

    [string] $Reason,

    [switch] $Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($HardDelete -and [string]::IsNullOrWhiteSpace($Reason)) {
    throw '-HardDelete 必须同时给出 -Reason（说明它为什么属于豁免清单：.venv / uv 缓存 / node_modules / 构建中间物 / %TEMP% 本次临时文件）'
}

Add-Type -AssemblyName Microsoft.VisualBasic

# 先全部解析，任何一项找不到就整体中止，避免"删一半"
$targets = [System.Collections.Generic.List[System.IO.FileSystemInfo]]::new()
foreach ($p in $Path) {
    $found = @(Get-Item -Path $p -Force -ErrorAction SilentlyContinue)
    if ($found.Count -eq 0) { throw "找不到要删除的路径：$p —— 已中止，未删除任何东西" }
    foreach ($f in $found) { $targets.Add($f) }
}

$totalBytes = 0
$deleted = 0

foreach ($item in $targets) {
    $size = 0
    if ($item.PSIsContainer) {
        # 空目录时 Measure-Object 不产生 Sum 属性，StrictMode 下直接取 .Sum 会抛错，
        # 因此先取回对象再判断属性是否存在（0 项 => 大小 0）。
        $measured = @(Get-ChildItem -LiteralPath $item.FullName -Recurse -Force -File -ErrorAction SilentlyContinue |
                      Measure-Object -Property Length -Sum)
        $sum = if ($measured.Count -gt 0 -and $null -ne $measured[0].PSObject.Properties['Sum']) {
            $measured[0].Sum
        } else { 0 }
        if ($null -ne $sum) { $size = [int64]$sum }
    }
    else {
        $size = [int64]$item.Length
    }
    $totalBytes += $size

    $verb = if ($HardDelete) { '永久删除（豁免清单）' } else { '移入回收站' }
    if (-not $PSCmdlet.ShouldProcess($item.FullName, $verb)) { continue }

    if ($item.PSIsContainer) {
        if ($HardDelete) { [System.IO.Directory]::Delete($item.FullName, $true) }
        else { [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($item.FullName, 'OnlyErrorDialogs', 'SendToRecycleBin') }
    }
    else {
        if ($HardDelete) { [System.IO.File]::Delete($item.FullName) }
        else { [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($item.FullName, 'OnlyErrorDialogs', 'SendToRecycleBin') }
    }

    if (Test-Path -LiteralPath $item.FullName) {
        throw "删除失败（路径仍然存在）：$($item.FullName) —— 已停止，不做任何降级处理"
    }

    $deleted++
    if (-not $Quiet) {
        Write-Host ('{0}：{1}  ({2:N2} MB)' -f $verb, $item.FullName, ($size / 1MB))
    }
}

if (-not $Quiet) {
    Write-Host ('完成：{0} 项，合计 {1:N2} MB{2}' -f $deleted, ($totalBytes / 1MB),
        $(if ($HardDelete) { '（永久删除，不可还原）' } else { '（在回收站，可还原）' }))
}
