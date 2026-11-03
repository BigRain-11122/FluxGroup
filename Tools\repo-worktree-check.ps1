# repo-worktree-check.ps1 - 主工作树洁净度体检（2026-11-03 立）
#
# 为什么需要：C:\Fluxgroup\FluxGroup 长期有 2000+ 条脏记录，其中 2243 条是"索引里有、
# 工作树里没有"（2026-10-xx 整树删除事故残留）。git status 因此失去信噪比，任何
# "谁改了什么"的判读都不可靠。执行面已迁到 FleetRuntime / FleetAgent 干净克隆，
# 主树只作归档 —— 但归档树也必须能量出真实偏差。
#
# 默认只报不改。要恢复被删的受版本控制文件，显式加 -Restore（git 对象里可回滚）。
#
# 用法:
#   powershell -File Tools/repo-worktree-check.ps1
#   powershell -File Tools/repo-worktree-check.ps1 -Restore
param(
    [switch]$Restore,
    [switch]$Json,
    [string]$Root = ""
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

if (-not $Root) { $Root = (Split-Path $PSScriptRoot -Parent) }
if (-not (Test-Path (Join-Path $Root '.git'))) {
    Write-Output "NOT-A-REPO $Root"
    exit 2
}

# 有别的 git 进程在写时不要动工作树（CAS 外科推送会短暂持锁）。
$gitProcs = @(Get-CimInstance Win32_Process -Filter "name='git.exe'" -ErrorAction SilentlyContinue)
$foreign = @($gitProcs | Where-Object { $_.CommandLine -and $_.CommandLine -notmatch 'repo-worktree-check' })
if ($Restore -and $foreign.Count -gt 0) {
    Write-Output "REFUSE-RESTORE git.exe in flight=$($foreign.Count) (先等它结束，避免抢锁)"
    exit 3
}

$lines = @(& git -C $Root status --porcelain 2>$null)
$byCode = @{}
$missing = 0      # deleted in worktree but present in index: fatal for `git status` truth
$restorable = 0
foreach ($ln in $lines) {
    if (-not $ln) { continue }
    $code = $ln.Substring(0, [Math]::Min(2, $ln.Length))
    if (-not $byCode.ContainsKey($code)) { $byCode[$code] = 0 }
    $byCode[$code]++
    if ($code -match 'D') { $missing++ }
    if ($code -match '^( D|AD|MD|MM|M |A |AM)') { $restorable++ }
}

$head = (& git -C $Root rev-parse --short HEAD 2>$null)
$origin = (& git -C $Root rev-parse --short origin/main 2>$null)
$aheadBehind = (& git -C $Root rev-list --left-right --count HEAD...origin/main 2>$null)

$report = [ordered]@{
    stamp           = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
    root            = $Root
    head            = $head
    origin_main     = $origin
    ahead_behind    = ($aheadBehind -join ' ')
    dirty_total     = $lines.Count
    by_code         = $byCode
    deleted_in_tree = $missing
    restorable      = $restorable
    restore_applied = [bool]$Restore
}

if ($Json) {
    $report | ConvertTo-Json -Depth 4
} else {
    Write-Output ("WORKTREE $($report.stamp) head=$head origin=$origin ahead/behind=$($report.ahead_behind)")
    Write-Output ("  dirty=$($lines.Count) deleted_in_tree=$missing restorable=$restorable")
    foreach ($k in ($byCode.Keys | Sort-Object)) { Write-Output ("  {0,-4} {1}" -f $k, $byCode[$k]) }
    if ($missing -gt 200) {
        Write-Output "  ALERT 大量受版本控制文件在工作树缺失 -> git status 已不可作判读依据"
        Write-Output "        （执行面请用 FleetRuntime / FleetAgent；需要恢复时显式 -Restore）"
    }
}

if ($Restore) {
    & git -C $Root checkout -- . 2>$null
    $after = @(& git -C $Root status --porcelain 2>$null)
    Write-Output ("RESTORE-DONE before={0} after={1}" -f $lines.Count, $after.Count)
}

exit 0