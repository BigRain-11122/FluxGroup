# local_cleanup_r1020.ps1 - bm-a local purge after the CEO uploads deliverables.
# Two-step by design: report first, delete only when an upload receipt exists.
#   report :   .\local_cleanup_r1020.ps1
#   dry run:   .\local_cleanup_r1020.ps1 -AfterUpload -Purge -WhatIf
#   delete :   .\local_cleanup_r1020.ps1 -AfterUpload -Purge
# The receipt (default .uploaded-ok.json at repo root) is the human gate: we do
# not try to guess whether a netdisk upload succeeded. Deleting is irreversible,
# so a missing receipt always aborts.
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [string]$Root = "",
  [switch]$AfterUpload,
  [switch]$Purge,
  [string]$Receipt = ""
)

$ErrorActionPreference = 'Stop'
if (-not $Root) { $Root = Split-Path -Parent $PSScriptRoot }
if (-not $Receipt) { $Receipt = Join-Path $Root '.uploaded-ok.json' }

# --- A: deliverables that must be verifiably uploaded before anything is purged
$MustUpload = @(
  'cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v511_wmvs_aigc.mp4',
  'cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v511_n1.mp4',
  'cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v511.mp4'
)

# --- C: rebuildable / re-downloadable. Never a delivery artifact.
$PurgeDirs = @(
  'cph4/labbench',
  'life/BigLife/.codely-cli/labbench',
  'media/hardware-staging',
  'Tools/nats/data',
  (Join-Path $env:USERPROFILE '.codely-cli\tmp'),
  (Join-Path $env:LOCALAPPDATA 'Temp')
)

# --- D: hard protection - refuse to run if any of these is in a purge path
$Forbidden = @('.git', 'media/MUSIC', 'media/BigStream/data/assets', '.codely-cli/memory',
               'cph4/fleet/inbox', 'CLOUD-OFF', 'MACHINE-ROLE')

function Get-SizeGB([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return 0.0 }
  $sum = (Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum).Sum
  if (-not $sum) { return 0.0 }
  return [math]::Round($sum / 1GB, 2)
}

function Test-IsForbidden([string]$Path) {
  $p = $Path.Replace('\', '/')
  foreach ($f in $Forbidden) { if ($p -like "*$f*") { return $true } }
  return $false
}

function Show-Report {
  Write-Output ''
  Write-Output '=== A. must upload (deleting these loses them) ==='
  $missing = 0
  foreach ($rel in $MustUpload) {
    $full = Join-Path $Root $rel
    if (Test-Path -LiteralPath $full) {
      $mb = [math]::Round((Get-Item -LiteralPath $full).Length / 1MB)
      Write-Output ('  {0,6} MB  {1}' -f $mb, $rel)
    } else {
      Write-Output ('  MISSING    {0}' -f $rel)
      $missing++
    }
  }

  Write-Output ''
  Write-Output '=== C. rebuildable, safe to purge after upload ==='
  $total = 0.0
  foreach ($d in $PurgeDirs) {
    $full = if ([System.IO.Path]::IsPathRooted($d)) { $d } else { Join-Path $Root $d }
    $gb = Get-SizeGB $full
    $total += $gb
    $flag = if (Test-IsForbidden $full) { ' [FORBIDDEN-PATH]' } else { '' }
    Write-Output ('  {0,7} GB  {1}{2}' -f $gb, $d, $flag)
  }
  Write-Output ('  ---------')
  Write-Output ('  {0,7} GB  total' -f [math]::Round($total, 2))

  $free = (Get-PSDrive ($Root.Substring(0, 1))).Free / 1GB
  Write-Output ''
  Write-Output ('free space now: {0} GB ; expected after purge: {1} GB' -f `
    [math]::Round($free, 1), [math]::Round($free + $total, 1))
  if ($missing -gt 0) { Write-Output ("WARNING: {0} A-class file(s) not on disk - check the manifest before uploading." -f $missing) }
}

function Read-Receipt {
  if (-not (Test-Path -LiteralPath $Receipt)) {
    throw ("ABORT: no upload receipt at {0}. Write it only after the netdisk upload is verified." -f $Receipt)
  }
  $raw = Get-Content -LiteralPath $Receipt -Raw -Encoding UTF8
  $obj = $raw | ConvertFrom-Json
  if (-not $obj.uploaded) { throw 'ABORT: receipt has no "uploaded" array.' }
  return @($obj.uploaded | ForEach-Object { [string]$_ })
}

function Assert-Uploaded([string[]]$Uploaded) {
  $norm = $Uploaded | ForEach-Object { $_.Replace('\', '/').Trim() }
  $notCovered = @()
  foreach ($rel in $MustUpload) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $rel))) { continue }   # absent = nothing to protect
    if ($norm -notcontains $rel) { $notCovered += $rel }
  }
  if ($notCovered.Count -gt 0) {
    $notCovered | ForEach-Object { Write-Output ('  NOT COVERED: ' + $_) }
    throw 'ABORT: receipt does not cover every A-class file that exists on disk.'
  }
}

Show-Report

if (-not $Purge) {
  Write-Output ''
  Write-Output 'report-only mode. Nothing was deleted.'
  exit 0
}
if (-not $AfterUpload) {
  Write-Output ''
  Write-Output 'ABORT: -Purge requires -AfterUpload (receipt gate).'
  exit 2
}

Write-Output ''
Write-Output '=== verifying upload receipt ==='
$uploaded = Read-Receipt
Assert-Uploaded $uploaded
Write-Output ('receipt OK: {0} path(s) declared uploaded' -f $uploaded.Count)

$logDir = Join-Path $Root 'media\logs'
if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logF = Join-Path $logDir ('local-cleanup-{0}.log' -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
$freed = 0.0

foreach ($d in $PurgeDirs) {
  $full = if ([System.IO.Path]::IsPathRooted($d)) { $d } else { Join-Path $Root $d }
  if (-not (Test-Path -LiteralPath $full)) { continue }
  if (Test-IsForbidden $full) {
    Add-Content -LiteralPath $logF -Value ('SKIP-FORBIDDEN {0}' -f $full) -Encoding UTF8
    Write-Output ('  SKIP (protected): {0}' -f $d)
    continue
  }
  $gb = Get-SizeGB $full
  if ($PSCmdlet.ShouldProcess($full, ('remove {0} GB' -f $gb))) {
    try {
      Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction Stop
      $freed += $gb
      Add-Content -LiteralPath $logF -Value ('REMOVED {0} GB {1}' -f $gb, $full) -Encoding UTF8
      Write-Output ('  removed {0} GB  {1}' -f $gb, $d)
    } catch {
      Add-Content -LiteralPath $logF -Value ('FAIL {0} :: {1}' -f $full, $_.Exception.Message) -Encoding UTF8
      Write-Output ('  FAIL   {0} :: {1}' -f $d, $_.Exception.Message)
    }
  }
}

Write-Output ''
Write-Output ('purged {0} GB (log: {1})' -f [math]::Round($freed, 2), $logF)

# --- C2: dependency and bytecode trees anywhere under the repo (rebuildable) ---
$depNames = @('.venv', 'node_modules', '__pycache__')
$depTargets = Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force -ErrorAction SilentlyContinue |
              Where-Object { $depNames -contains $_.Name }
foreach ($t in $depTargets) {
  if (Test-IsForbidden $t.FullName) { continue }
  $gb = Get-SizeGB $t.FullName
  if ($PSCmdlet.ShouldProcess($t.FullName, ('remove {0} GB' -f $gb))) {
    try {
      Remove-Item -LiteralPath $t.FullName -Recurse -Force -ErrorAction Stop
      $freed += $gb
      Add-Content -LiteralPath $logF -Value ('REMOVED-DEP {0} GB {1}' -f $gb, $t.FullName) -Encoding UTF8
      Write-Output ('  removed {0} GB  {1}' -f $gb, $t.FullName.Replace($Root, '.'))
    } catch {
      Add-Content -LiteralPath $logF -Value ('FAIL-DEP {0} :: {1}' -f $t.FullName, $_.Exception.Message) -Encoding UTF8
    }
  }
}

Write-Output ''
Write-Output ('total reclaimed {0} GB' -f [math]::Round($freed, 2))
Write-Output 'post-check: git status / inbox / memory must still be intact.'