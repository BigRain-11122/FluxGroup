# process_purge_r1020.ps1 - drop process artifacts, keep finals and in-flight work.
# CEO 2026-10-20: "过程文件都删了，只保留最终版本，开发进行中的素材还是要保留".
#
# Classification is objective, never a judgement call at delete time:
#   PROCESS  = name matches a process pattern (probe/frames/takes/review dumps/
#              caches/temp) AND is not protected below
#   FINAL    = newest generation of a deliverable (v511 family) -> kept
#   IN-FLIGHT= touched within -KeepDays, or referenced by an open POOL card,
#              or under a protected tree -> kept
# Recency wins over pattern: a fresh probe dir is still in-flight material.
#
# Dry run by default. -Execute actually deletes. Everything is logged.
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [string]$Root = "",
  [int]$KeepDays = 7,
  [switch]$Execute
)

$ErrorActionPreference = 'Continue'
if (-not $Root) { $Root = Split-Path -Parent $PSScriptRoot }

# Never touched, whatever the pattern says. Compared as normalized substrings
# (forward slashes) so a trailing-backslash regex can never blow up.
$Protected = @(
  '/.git/', '/media/MUSIC/', '/media/BigStream/data/assets/',
  '/.codely-cli/memory/', '/cph4/fleet/inbox/', '/CLOUD-OFF',
  'MACHINE-ROLE', '.uploaded-ok.json'
)

# Process-shaped directories (regex on the leaf name).
$ProcessDirRx = @(
  '^_proxycheck$', '.*_probe$', '.*_probe_.*', '.*_frames$', '.*_frames_.*',
  '^frames_full$', '^final_review_.*', '^rt_boards$', '^rt_frames$', '^rt2_frames$',
  '^v\d+_probe$', '^v\d+takes$', '^v\d+src$', '^qc-v\d+-audit$', '^cloudv2$',
  '^scratch$', '^_cut$', '^_tmp$', '^\.venv$', '^node_modules$', '^__pycache__$'
)

# Process-shaped files (regex on the file name).
$ProcessFileRx = @(
  '\.bak-\d{8}-\d{4}$', '\.pid$', '^.*_try\d+.*\.log$', '^v\d+dryrun\.log$',
  '^rt_spec_(head|tail)\.png$', '^rt_audio_(head|tail)\.mp3$',
  '^rt_v\d+_global\.jpg$', '^PROGRESS-BOARD-.*\.jpg$'
)

# Historical deliverable generations kept only as the newest family.
$KeepNewestFamily = 'full_mv_v511'

function Get-SizeGB([string]$Path) {
  $s = (Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
  if (-not $s) { return 0.0 }
  return [math]::Round($s / 1GB, 2)
}

function Test-Protected([string]$Path) {
  $norm = $Path.Replace('\', '/')
  foreach ($p in $Protected) { if ($norm.Contains($p)) { return $true } }
  return $false
}

# --- open POOL cards = work in flight -> their paths are protected
$poolPaths = @()
$poolF = Join-Path $Root 'cph4\fleet\dispatcher\POOL.json'
if (Test-Path -LiteralPath $poolF) {
  try {
    $cards = Get-Content -LiteralPath $poolF -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($c in $cards) {
      if ($c.status -notin @('open', 'in-flight', 'queued', 'claimed')) { continue }
      foreach ($field in @('title', 'spec', 'acceptance', 'notes')) {
        if ($c.$field) { $poolPaths += [string]$c.$field }
      }
    }
  } catch { Write-Output ('POOL read failed: ' + $_.Exception.Message) }
}

function Test-InFlightRef([string]$Path) {
  $rel = $Path.Replace($Root, '').Replace('\', '/')
  $leaf = Split-Path $Path -Leaf
  foreach ($blob in $poolPaths) {
    if ($blob -and ($blob.Contains($rel) -or $blob.Contains($leaf))) { return $true }
  }
  return $false
}

$cutoff = (Get-Date).AddDays(-1 * [Math]::Abs($KeepDays))
$candidates = New-Object System.Collections.ArrayList

# Targeted enumeration, not a full-tree walk: a repo-wide -Recurse over venvs and
# model caches takes minutes and tells us nothing new. These are the known
# production output roots, plus a bounded dependency sweep.
# Only the SHIPPED line is in scope: mv0001 reached v5.11 as final, so its
# probes / frame dumps / take attempts / review dumps are process leftovers.
# In-flight work (星晴 PACK-B assembly segments, W2 KF packs) is NOT scanned at
# all - deleting those would damage production, not clean up after it.
$scanRoots = @(
  'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1',
  'cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\cloudv2'
)

function Add-Candidate($item) {
  if (Test-Protected $item.FullName) { return }
  if ($item.LastWriteTime -gt $cutoff) { return }
  if (Test-InFlightRef $item.FullName) { return }
  $leaf = $item.Name
  if ($item.PSIsContainer) {
    foreach ($rx in $ProcessDirRx) {
      if ($leaf -match $rx) {
        [void]$candidates.Add([pscustomobject]@{ Kind = 'DIR'; Path = $item.FullName; GB = (Get-SizeGB $item.FullName) })
        return
      }
    }
  } else {
    foreach ($rx in $ProcessFileRx) {
      if ($leaf -match $rx) {
        [void]$candidates.Add([pscustomobject]@{ Kind = 'FILE'; Path = $item.FullName; GB = [math]::Round($item.Length / 1GB, 3) })
        return
      }
    }
    if ($leaf -match '^full_mv_v(?!511).*\.mp4$') {
      [void]$candidates.Add([pscustomobject]@{ Kind = 'HISTORICAL'; Path = $item.FullName; GB = [math]::Round($item.Length / 1GB, 3) })
    }
  }
}

foreach ($r in $scanRoots) {
  $full = Join-Path $Root $r
  if (-not (Test-Path -LiteralPath $full)) { continue }
  Get-ChildItem -LiteralPath $full -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.git\\' } |
    ForEach-Object { Add-Candidate $_ }
}

# Dependency trees: bounded depth so we never walk a model cache.
foreach ($r in @('.', 'gaming', 'media', 'cph4', 'quant', 'life')) {
  $full = Join-Path $Root $r
  if (-not (Test-Path -LiteralPath $full)) { continue }
  Get-ChildItem -LiteralPath $full -Directory -Depth 5 -Force -ErrorAction SilentlyContinue |
    Where-Object { $depNames -contains $_.Name } |
    ForEach-Object { Add-Candidate $_ }
}

# Drop candidates nested inside another candidate (count the parent only).
$sorted = $candidates | Sort-Object { $_.Path.Length }
$kept = New-Object System.Collections.ArrayList
foreach ($c in $sorted) {
  $nested = $false
  foreach ($k in $kept) { if ($c.Path.StartsWith($k.Path + '\')) { $nested = $true; break } }
  if (-not $nested) { [void]$kept.Add($c) }
}

$total = ($kept | Measure-Object -Property GB -Sum).Sum
Write-Output ''
Write-Output ('process-artifact candidates: {0} items, {1} GB' -f $kept.Count, [math]::Round($total, 2))
Write-Output ('keep window: anything modified after {0} is treated as in-flight' -f $cutoff.ToString('yyyy-MM-dd HH:mm'))
Write-Output ''
$kept | Sort-Object GB -Descending | Select-Object -First 25 |
  ForEach-Object { Write-Output ('  {0,7} GB  {1}  {2}' -f $_.GB, $_.Kind, $_.Path.Replace($Root, '.')) }

$logDir = Join-Path $Root 'media\logs'
if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logF = Join-Path $logDir ('process-purge-{0}.log' -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
$kept | Sort-Object Path | ForEach-Object { Add-Content -LiteralPath $logF -Value ('PLAN {0} GB {1}' -f $_.GB, $_.Path) -Encoding UTF8 }
Write-Output ''
Write-Output ('plan written: ' + $logF)

if (-not $Execute) {
  Write-Output ''
  Write-Output 'dry run only. Re-run with -Execute to delete.'
  exit 0
}

$freed = 0.0
foreach ($c in ($kept | Sort-Object Path -Descending)) {
  if (Test-Protected $c.Path) { continue }
  if (-not $PSCmdlet.ShouldProcess($c.Path, ('remove {0} GB' -f $c.GB))) { continue }
  try {
    Remove-Item -LiteralPath $c.Path -Recurse -Force -ErrorAction Stop
    $freed += $c.GB
    Add-Content -LiteralPath $logF -Value ('DELETED {0} GB {1}' -f $c.GB, $c.Path) -Encoding UTF8
  } catch {
    Add-Content -LiteralPath $logF -Value ('FAIL {0} :: {1}' -f $c.Path, $_.Exception.Message) -Encoding UTF8
  }
}
Write-Output ''
Write-Output ('deleted {0} GB (log: {1})' -f [math]::Round($freed, 2), $logF)