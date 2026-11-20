# PULL-MEDIA.ps1 - content-line asset transfer: bm-a (DASHENG) -> bm-c (FLUXGROUP)
# CEO order 2026-11-20: all self-media / AI drama / short-drama / MV assets move to FLUXGROUP.
# Canon: cph4/fleet/HANDOVER-20261120-CONTENT-TO-VISUAL.md
#
# ASCII ONLY. PS 5.1 decodes BOM-less .ps1 as ANSI; non-ASCII would corrupt quotes.
#
# Usage on FLUXGROUP (dry run, prints plan):
#   powershell -NoProfile -ExecutionPolicy Bypass -File PULL-MEDIA.ps1
# Real run (needs SMB credentials for bm-a first):
#   net use \\100.110.185.62\C$ /user:<admin> <password>     # one time
#   powershell -NoProfile -ExecutionPolicy Bypass -File PULL-MEDIA.ps1 -Apply
param(
  [string]$Source = '\\100.110.185.62\C$\Users\sjs20\Desktop\FluxGroup\media',
  [string]$Dest   = 'K:\Fluxgroup\FluxGroup\media',
  [string[]]$Dirs  = @('BigStream','drama-tools','MV','faces','MUSIC','lora',
                       'mv-test','mv-album-001-jay','kf-ab','meme-daily-v1',
                       'drama-pilot-in','drama-pilot-out','covers'),
  [string]$Receipt = 'cph4\fleet\queue-receipts\HANDOVER-content-bm-c.json',
  [switch]$Apply
)
$ErrorActionPreference = 'Continue'

if (-not (Test-Path $Source)) {
  Write-Host "BLOCKED: source not reachable -> $Source"
  Write-Host "Needs: net use \\100.110.185.62\C$ /user:<admin> <password>"
  exit 2
}
if (-not (Test-Path $Dest)) { Write-Host "BLOCKED: dest missing -> $Dest"; exit 2 }

$rows = @()
foreach ($d in $Dirs) {
  $src = Join-Path $Source $d
  $dst = Join-Path $Dest $d
  if (-not (Test-Path $src)) { Write-Host "SKIP (absent on source): $d"; continue }
  $s = (Get-ChildItem $src -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum)
  Write-Host ("PLAN {0,-20} {1,8} files {2,9:N0} MB -> {3}" -f $d, $s.Count, ($s.Sum/1MB), $dst)
  if ($Apply) {
    # /MIR mirrors; logs/.git/__pycache__ are machine-local noise, never copied.
    $rc = (robocopy $src $dst /MIR /XD logs .git __pycache__ .aihot-tmp .c3-tmp `
            /R:2 /W:2 /MT:8 /NFL /NDL /NP /NJH /NJS) 2>&1
    $code = $LASTEXITCODE   # robocopy: <8 means success
    $t = (Get-ChildItem $dst -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum)
    Write-Host ("DONE {0,-20} rc={1} landed {2} files {3:N0} MB" -f $d, $code, $t.Count, ($t.Sum/1MB))
    $rows += [pscustomobject]@{ dir=$d; robocopy_rc=$code; files=$t.Count; bytes=[int64]$t.Sum }
  }
}

if ($Apply) {
  $out = [pscustomobject]@{
    receipt_id       = 'HANDOVER-content-bm-c'
    order            = 'CEO 2026-11-20 content-line handover to FLUXGROUP'
    node             = 'bm-c'
    source           = $Source
    dest             = $Dest
    finished_at      = (Get-Date).ToString('s')
    dirs             = $rows
    next_steps       = @('register media\BigStream\src\os\register_loop_task.ps1',
                         'start station_agent / FleetLink :8790 so lanes/bm-c.json leaves OFFLINE')
  }
  $dir = Split-Path -Parent $Receipt
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
  $out | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $Receipt
  Write-Host "receipt -> $Receipt"
}
