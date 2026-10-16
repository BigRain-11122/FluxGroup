<#
.SYNOPSIS
  content-gc.ps1 - 自媒体线废资源清理器 v1（CONTENT-GC-POLICY-v1.md 执行器）
  CEO 令 2026-10-16 21:3x「自媒体清理机制」。
.NOTES
  默认 WhatIf 报表模式（只列不动刀）；-Apply 才执行删除。
  S0 禁删白名单内置；删除目标限定枚举路径（禁自由参数路径——bm-b r834 整树删除事故判例）。
  报表落 cph4/fleet/gc-reports/GC-<yyyyMMdd-HHmm>.md。
  PS5.1 兼容（无三元·无 &&）。
#>
param(
    [switch]$Apply,
    [int]$AutoSavesKeepDays = 3,
    [int]$LogsKeepDays = 7
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot   # FluxGroup root
Set-Location $root

# ---- S0 禁删白名单（CONTENT-GC-POLICY §二·硬编码禁参数化）----
$S0 = @(
    'media\MUSIC',
    'media\BigStream\data\assets',
    'media\drama-pilot-out',
    'media\mv-album-001-jay',
    'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\frames_full',   # 装配 KF 源件库
    'cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\cloudv2'  # 21 条在位源件
)

function Test-S0 {
    param([string]$Path)
    foreach ($p in $script:S0) {
        $full = Join-Path $root $p
        if ($Path -eq $full -or $Path.StartsWith($full + '\')) { return $true }
    }
    return $false
}

# ---- 枚举删除目标（W1 会话噪声 >N 天 / W3 日志 >N 天 / tmp 全量）----
$cutoffAS = (Get-Date).AddDays(-$AutoSavesKeepDays)
$cutoffLG = (Get-Date).AddDays(-$LogsKeepDays)

$targets = @()

function Add-Dir {
    param([string]$Path, [string]$Class)
    if (Test-Path $Path) {
        $script:targets += @{ Path = $Path; Class = $Class }
    }
}

# W1 会话噪声
Add-Dir (Join-Path $root 'media\BigStream\.codely-cli\auto-saves') 'W1-auto-saves'
# W3 日志
Add-Dir (Join-Path $root 'media\BigStream\logs') 'W3-logs'
Add-Dir (Join-Path $root 'media\logs') 'W3-logs'
# tmp 全量（W1）
Add-Dir (Join-Path $root 'media\BigStream\.c3-tmp') 'W1-tmp'
Add-Dir (Join-Path $root 'media\BigStream\.aihot-tmp') 'W1-tmp'

# ---- S3 候选报表面（只列不删）----
$s3Candidates = @(
    'media\BigStream\data\storylines',
    'media\BigStream\output\renders',
    'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\qc_v4_frames',
    'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\_superseded'
)

$report = New-Object System.Collections.ArrayList
$totalBytes = 0
$totalFiles = 0
$deletedFiles = 0
$deletedBytes = 0

[void]$report.Add('# GC 报告 - ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + (' (mode={0})' -f $(if ($Apply) { 'APPLY' } else { 'WHATIF' })))
[void]$report.Add('')
[void]$report.Add('## S1 删除执行面（W1/W3 按保留线）')
[void]$report.Add('')
[void]$report.Add('| 类 | 路径 | 件数 | MB | 动作 |')
[void]$report.Add('|---|---|---|---|---|')

foreach ($t in $targets) {
    $dir = $t.Path
    if (Test-S0 $dir) { [void]$report.Add("| S0-HIT(跳过) | $dir | - | - | 禁删白名单 |"); continue }
    if ($t.Class -eq 'W1-tmp') {
        $files = Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue
    } else {
        $cut = $(if ($t.Class -eq 'W1-auto-saves') { $cutoffAS } else { $cutoffLG })
        $files = Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cut }
    }
    if ($null -eq $files) { $files = @() }
    $bytes = ($files | Measure-Object Length -Sum).Sum
    if ($null -eq $bytes) { $bytes = 0 }
    $mb = [math]::Round($bytes / 1MB)
    $totalBytes += $bytes
    $totalFiles += $files.Count
    $action = $(if ($Apply) { 'DELETED' } else { 'would-delete' })
    if ($Apply -and $files.Count -gt 0) {
        $files | Remove-Item -Force -ErrorAction SilentlyContinue
        # 清空目录
        Get-ChildItem $dir -Directory -Recurse -ErrorAction SilentlyContinue |
            Sort-Object { $_.FullName.Length } -Descending |
            Where-Object { (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue).Count -eq 0 } |
            Remove-Item -Force -ErrorAction SilentlyContinue
        $deletedFiles += $files.Count
        $deletedBytes += $bytes
    }
    [void]$report.Add("| $($t.Class) | $($dir.Replace($root, '.')) | $($files.Count) | $mb | $action |")
}

[void]$report.Add('')
[void]$report.Add('## S3 候选清单（只列不删·待治理窗/CEO 裁）')
[void]$report.Add('')
[void]$report.Add('| 路径 | 件数 | MB | 备注 |')
[void]$report.Add('|---|---|---|---|')

foreach ($c in $s3Candidates) {
    $dir = Join-Path $root $c
    if (Test-Path $dir) {
        $files = @(Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue)
        $mb = [math]::Round((($files | Measure-Object Length -Sum).Sum) / 1MB)
        [void]$report.Add("| $($c.Replace($root, '.')) | $($files.Count) | $mb | S3 候选·删前引用检查 |")
    }
}

[void]$report.Add('')
[void]$report.Add(('## 合计: {0} 件 / {1:N0} MB（{2}）' -f $totalFiles, ($totalBytes / 1MB), $(if ($Apply) { "已删 $deletedFiles 件 / $([math]::Round($deletedBytes/1MB)) MB" } else { 'WHATIF 未动刀' })))

# ---- 报表落盘 ----
$repDir = Join-Path $root 'cph4\fleet\gc-reports'
if (-not (Test-Path $repDir)) { New-Item -ItemType Directory -Path $repDir | Out-Null }
$repFile = Join-Path $repDir ('GC-' + (Get-Date -Format 'yyyyMMdd-HHmm') + '.md')
[IO.File]::WriteAllText($repFile, ($report -join "`r`n"))
Write-Output ('REPORT: ' + $repFile)
Write-Output ($report -join "`r`n")
Write-Output ('SUMMARY: ' + $totalFiles + ' files / ' + [math]::Round($totalBytes / 1MB) + ' MB' + $(if ($Apply) { ' -> DELETED' } else { ' -> WHATIF' }))
