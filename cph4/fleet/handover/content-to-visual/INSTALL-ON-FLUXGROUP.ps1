# INSTALL-ON-FLUXGROUP.ps1 - receiver-side installer for the 2026-11-20 content-line handover.
# Runs ON FLUXGROUP (bm-c). Takes the archives that arrived via Taildrop, verifies their
# sha256 against MANIFEST.json, extracts them into the repo media tree, and writes a receipt.
#
# ASCII ONLY (PS 5.1 decodes BOM-less .ps1 as ANSI; non-ASCII would corrupt quotes).
#
# Typical flow (whatever put the files there - Taildrop lands in Downloads by default):
#   powershell -NoProfile -ExecutionPolicy Bypass -File INSTALL-ON-FLUXGROUP.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File INSTALL-ON-FLUXGROUP.ps1 -Src 'C:\Users\sjs20\Downloads' -Apply
param(
  [string]$Src     = (Join-Path $env:USERPROFILE 'Downloads'),
  [string]$Repo    = 'K:\Fluxgroup\FluxGroup',
  [string]$Receipt = 'cph4\fleet\queue-receipts\HANDOVER-content-bm-c.json',
  [switch]$Apply
)
$ErrorActionPreference = 'Continue'
function Say($m) { Write-Host $m }

if (-not (Test-Path $Repo)) { Say "BLOCKED: repo not found -> $Repo"; exit 2 }
$media = Join-Path $Repo 'media'
if (-not (Test-Path $media)) { New-Item -ItemType Directory -Force $media | Out-Null }

$manPath = Join-Path $Src 'MANIFEST.json'
if (-not (Test-Path $manPath)) {
  Say "BLOCKED: MANIFEST.json not found in $Src"
  Say "It ships next to the archives; copy it there first."
  exit 2
}
$man = Get-Content $manPath -Raw -Encoding UTF8 | ConvertFrom-Json

$rows = @()
$fail = 0
foreach ($a in $man.archives) {
  $zip = Join-Path $Src $a.name
  if (-not (Test-Path $zip)) { Say ("MISSING  {0}" -f $a.name); $fail++; $rows += [pscustomobject]@{name=$a.name;status='missing'}; continue }
  $got = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
  if ($got -ne $a.sha256.ToLower()) {
    Say ("HASH-BAD {0}  expected {1} got {2}" -f $a.name, $a.sha256, $got)
    $fail++; $rows += [pscustomobject]@{name=$a.name;status='hash-mismatch'}; continue
  }
  Say ("OK       {0}  {1:N0} MB" -f $a.name, ((Get-Item $zip).Length / 1MB))
  if ($Apply) {
    # Archives are built relative to the repo root: media/... paths inside.
    Expand-Archive -LiteralPath $zip -DestinationPath $Repo -Force -ErrorAction Continue
    Say ("EXTRACT  {0} -> {1}" -f $a.name, $Repo)
    $rows += [pscustomobject]@{name=$a.name;status='extracted';sha256=$got}
  } else {
    $rows += [pscustomobject]@{name=$a.name;status='verified-dryrun';sha256=$got}
  }
}

if ($Apply) {
  # Post-install facts the fleet needs: the content line now lives here.
  $checks = [ordered]@{}
  foreach ($d in @('BigStream','MV','drama-tools','MUSIC','faces','lora','meme-daily-v1','mv-album-001-jay')) {
    $p = Join-Path $media $d
    if (Test-Path $p) {
      $s = (Get-ChildItem $p -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum)
      $checks[$d] = [pscustomobject]@{ files = $s.Count; bytes = [int64]$s.Sum }
    } else { $checks[$d] = 'absent' }
  }
  $out = [pscustomobject]@{
    receipt_id  = 'HANDOVER-content-bm-c'
    order       = 'CEO 2026-11-20 content-line handover to FLUXGROUP'
    node        = 'bm-c'
    installed_at= (Get-Date).ToString('s')
    source_dir  = $Src
    repo        = $Repo
    archives    = $rows
    media       = $checks
    failures    = $fail
    next_steps  = @(
      'register media\BigStream\src\os\register_loop_task.ps1 (content line OS loop)',
      'start station_agent / FleetLink :8790 so lanes\bm-c.json leaves OFFLINE',
      'push this receipt to origin, then bm-a may delete its frozen copy'
    )
  }
  $rp = Join-Path $Repo $Receipt
  $rd = Split-Path -Parent $rp
  if (-not (Test-Path $rd)) { New-Item -ItemType Directory -Force $rd | Out-Null }
  $out | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $rp
  Say "receipt -> $rp"
}

if ($fail -gt 0) { Say "RESULT: $fail archive(s) failed - do NOT delete the sender copy yet"; exit 3 }
Say 'RESULT: all archives verified'
