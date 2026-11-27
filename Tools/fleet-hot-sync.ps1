# fleet-hot-sync.ps1 - bring a node's command plane to origin/main without losing local work.
# Why: every machine appends to docs/orders.md, so the worktree diverges; FleetLink then
# reports "updated-kept-local" and the node never receives new orders/tools.
# This does fetch -> merge --ff-only (no rebase: C-20261104 hard law). If it cannot fast-forward
# it stops and lists the files; it never rebases and never hard-resets, so no local round
# bookkeeping is destroyed and no conflict marker can be left in shared ledgers.
param(
    [string]$Root = '',
    [switch]$Push
)
$ErrorActionPreference = 'Continue'
if (-not $Root) { $Root = Split-Path -Parent $PSScriptRoot }
$git = 'git'
$before = ''
try { $before = [string](& $git -C $Root rev-parse --short HEAD) } catch { }
& $git -C $Root fetch origin main 2>&1 | Out-Null
$ahead = 0; $behind = 0
try {
    $ahead = [int](& $git -C $Root rev-list --count 'origin/main..HEAD')
    $behind = [int](& $git -C $Root rev-list --count 'HEAD..origin/main')
} catch { }
Write-Output ("HOT-SYNC start head=$before ahead=$ahead behind=$behind")
if ($behind -eq 0) { Write-Output 'HOT-SYNC already current'; exit 0 }

# 2026-11-05 R9: 禁 rebase（C-20261104 硬律）。rebase.autostash 的 autostash pop 冲突会把
# <<<<<<< Updated upstream / >>>>>>> Stashed changes 标记留在共享台账里，而读队列的脚本
# try/except 静默跳行 = 卡片消失 + STARVED 假红（本班 30 分钟内实测 3 次）。改用 --ff-only。
& $git -C $Root merge --ff-only origin/main 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    $un = @(& $git -C $Root diff --name-only --diff-filter=U)
    Write-Output ('HOT-SYNC NOT-FF files=' + ($un -join ','))
    Write-Output 'No rebase (hard law 2026-11-04). Commit or discard local edits, then rerun with -Push.'
    exit 1
}
$after = [string](& $git -C $Root rev-parse --short HEAD)
Write-Output ("HOT-SYNC ok head=$after")
if ($Push) {
    & $git -C $Root push origin HEAD:main 2>&1 | Out-Null
    Write-Output ('HOT-SYNC push rc=' + $LASTEXITCODE)
}
exit 0