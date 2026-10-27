# fleet-hot-sync.ps1 - bring a node's command plane to origin/main without losing local work.
# Why: every machine appends to docs/orders.md, so the worktree diverges; FleetLink then
# reports "updated-kept-local" and the node never receives new orders/tools.
# This does fetch -> rebase (autostash). On conflict it stops and lists the files; it never
# hard-resets, so no local round bookkeeping is destroyed.
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

& $git -C $Root -c rebase.autostash=true rebase origin/main 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    $un = @(& $git -C $Root diff --name-only --diff-filter=U)
    Write-Output ('HOT-SYNC CONFLICT files=' + ($un -join ','))
    Write-Output 'Resolve markers (keep both sides), git add <files>, git rebase --continue, then rerun with -Push'
    exit 1
}
$after = [string](& $git -C $Root rev-parse --short HEAD)
Write-Output ("HOT-SYNC ok head=$after")
if ($Push) {
    & $git -C $Root push origin HEAD:main 2>&1 | Out-Null
    Write-Output ('HOT-SYNC push rc=' + $LASTEXITCODE)
}
exit 0