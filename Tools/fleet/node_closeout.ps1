# node_closeout.ps1 - one-time close-out for a box whose repo has diverged.
# Why: the poke worker only does `git merge --ff-only`, and fleet-hot-sync forbids
# rebase (C-20261104). A box that has any local commits ahead can therefore never
# receive new code - that is the single structural reason "we fixed it but the machine
# still runs old code".
#
# What it does (in this order, all idempotent):
#   1. keep a rescue branch (salvage-auto-YYYYMMDD) so no local commit is lost untracked
#   2. fetch origin main
#   3. reset --mixed origin/main  <- commits go, WORKING TREE FILES STAY (never --hard)
#   4. verify HEAD == origin/main and report ahead/behind
#   5. write a receipt under cph4\fleet\queue-receipts\ so the master can verify on disk
#
# Never: --hard, rebase, push, or touching scheduled tasks (bm-a may be paused by CEO order).
# Pure ASCII on purpose: PowerShell 5.1 reads BOM-less .ps1 as GBK and Chinese comments
# swallow quote bytes.
param(
  [string]$Root = '',
  [switch]$WhatIf
)
$ErrorActionPreference = 'Continue'
if (-not $Root) {
  # common roots on the fleet; first one that is a git repo wins
  $cands = @('C:\Fluxgroup\FluxGroup', 'C:/Fluxgroup/FluxGroup',
             'C:\Users\sjs20\Desktop\FluxGroup', 'K:/Fluxgroup/FluxGroup',
             'K:\Fluxgroup\FluxGroup')
  foreach ($c in $cands) { if (Test-Path (Join-Path $c '.git')) { $Root = $c; break } }
}
if (-not $Root -or -not (Test-Path (Join-Path $Root '.git'))) {
  Write-Output 'E-NOROOT: pass -Root <repo path>'
  exit 2
}
$node = if ($env:COMPUTERNAME) { $env:COMPUTERNAME.ToLower() } else { 'unknown' }
$git = 'git'
function G([string[]]$a) { & $git -C $Root @a 2>&1 | ForEach-Object { [string]$_ } }

Write-Output ('== closeout start root=' + $Root)

# 1 rescue branch (never delete local history without a pointer)
$tag = 'salvage-auto-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$null = G @('branch', $tag)
Write-Output ('rescue branch: ' + $tag)

# 2 fetch
$f = G @('fetch', 'origin', 'main')
if ($LASTEXITCODE -ne 0) { Write-Output ('E-FETCH: ' + ($f -join ' | ')); exit 3 }

$ahead = (G @('rev-list', '--count', 'origin/main..HEAD')) -join ''
$behind = (G @('rev-list', '--count', 'HEAD..origin/main')) -join ''
Write-Output ('before: ahead=' + $ahead + ' behind=' + $behind)

if ($WhatIf) { Write-Output 'WHATIF: would reset --mixed origin/main'; exit 0 }

# 3 reset --mixed (commits dropped, files kept)
$r = G @('reset', '--mixed', 'origin/main')
Write-Output ('reset: ' + (($r | Select-Object -First 2) -join ' | '))

# 4 verify
$head = (G @('rev-parse', 'HEAD')) -join ''
$orig = (G @('rev-parse', 'origin/main')) -join ''
$ok = ($head.Trim() -eq $orig.Trim())
Write-Output ('after: head=' + $head.Substring(0, [Math]::Min(8, $head.Length)) +
              ' origin=' + $orig.Substring(0, [Math]::Min(8, $orig.Length)) +
              ' clean=' + $ok)

# 5 receipt (master verifies on disk, not on self-report)
$dir = Join-Path $Root 'cph4\fleet\queue-receipts'
try {
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  $rec = [ordered]@{
    node            = $node
    ts              = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
    kind            = 'closeout'
    root            = $Root
    rescue_branch   = $tag
    ahead_before    = $ahead
    behind_before   = $behind
    head_after      = $head
    origin_main     = $orig
    fast_forward_ok = $ok
    python = (& python --version 2>&1 | ForEach-Object { [string]$_ }) -join ''
    git    = (& git --version 2>&1 | ForEach-Object { [string]$_ }) -join ''
  }
  $p = Join-Path $dir ('closeout-' + $node + '.json')
  # ASCII, not UTF8: PS 5.1 UTF8 adds a BOM and the master's json.load(utf-8) fails on it
  ($rec | ConvertTo-Json -Depth 3) | Set-Content -Path $p -Encoding ASCII
  Write-Output ('receipt: ' + $p)
} catch { Write-Output ('W-RECEIPT: ' + $_.Exception.Message) }

if ($ok) { Write-Output 'CLOSED: box can now receive code on the next poke'; exit 0 }
Write-Output 'E-STILL-DIVERGED: check for pre-commit hooks or a protected branch'
exit 1