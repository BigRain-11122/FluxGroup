#Requires -Version 5.1
<#
artifact_push.ps1 - send this machine's real outputs to the MacBook Pro intake
(see cph4/fleet/ARTIFACT-BACKUP-RULES-v1.md for the contract).

Why: lane_agent.git_publish skips media/, gaming/ and quant/, and queue deliverables
mostly point at each box's local disk (D:\, C:\Fluxgroup, K:\, D:\FleetWorker). So the
actual videos, voice batches and reports never reached the control plane - "DONE but no
file on disk" came from exactly that gap. This script closes it by pushing the bytes.

Two artefacts are produced per node, both inside the repo so the Mac can see coverage:
  cph4/fleet/artifacts/<node>/MANIFEST.jsonl  what this box declares it produced
  cph4/fleet/artifacts/<node>/PUSHED.jsonl    what actually made it to the drive

Usage:
  powershell -ExecutionPolicy Bypass -File Tools\fleet\artifact_push.ps1 `
      -Root C:\Fluxgroup\FluxGroup -Node bm-b
  ... -WhatIf     list only, send nothing
  ... -MaxMB 4096 only push files up to 4 GB (default 2048)

Exit codes: 0 = ok (including "nothing to do"), 1 = at least one push failed,
2 = intake unreachable.
#>
param(
  [string]$Root = "",
  [Parameter(Mandatory = $true)][ValidateSet("bm-a", "bm-b", "bm-c", "bm-d")][string]$Node,
  [string]$Intake = "http://100.75.133.10:11436",
  [int]$MaxMB = 2048,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path }
$art   = Join-Path $Root "cph4\fleet\artifacts\$Node"
$man   = Join-Path $art "MANIFEST.jsonl"
$pushed= Join-Path $art "PUSHED.jsonl"
$queue = Join-Path $Root "cph4\fleet\PRODUCTION-QUEUE.jsonl"
New-Item -ItemType Directory -Force -Path $art | Out-Null

function Get-Sha256([string]$p) { (Get-FileHash -Path $p -Algorithm SHA256).Hash.ToLower() }

# ---- already pushed? key = sha256|bytes ---------------------------------------------
$done = @{}
if (Test-Path $pushed) {
  foreach ($ln in Get-Content -LiteralPath $pushed -Encoding UTF8) {
    if (-not $ln.Trim()) { continue }
    try { $o = $ln | ConvertFrom-Json; $done[("{0}|{1}" -f $o.sha256, $o.bytes)] = $true } catch { }
  }
}

# ---- what does the queue say this box owes? -----------------------------------------
$targets = New-Object System.Collections.ArrayList
if (Test-Path $queue) {
  foreach ($ln in Get-Content -LiteralPath $queue -Encoding UTF8) {
    if (-not $ln.Trim()) { continue }
    try { $j = $ln | ConvertFrom-Json } catch { continue }
    $dl = [string]$j.deliverable
    if (-not $dl) { continue }
    $owns = @()
    if ($j.nodes) { $owns += $j.nodes }
    if ($j.owner) { $owns += $j.owner }
    if ($owns -notcontains $Node) { continue }
    # only paths that live on THIS box (drive letter) or are repo-relative
    $p = $dl
    if ($p -match '^[A-Za-z]:') {
      if (-not (Test-Path -LiteralPath $p)) { continue }
    } else {
      $p = Join-Path $Root ($dl -replace '/', '\')
      if (-not (Test-Path -LiteralPath $p)) { continue }
    }
    [void]$targets.Add([pscustomobject]@{ card = $j.id; path = $p })
  }
}

# ---- expand directories into files --------------------------------------------------
$files = New-Object System.Collections.ArrayList
foreach ($t in $targets) {
  $item = Get-Item -LiteralPath $t.path
  if ($item.PSIsContainer) {
    Get-ChildItem -LiteralPath $t.path -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Length -gt 0 } |
      ForEach-Object { [void]$files.Add([pscustomobject]@{ card = $t.card; file = $_ }) }
  } else {
    [void]$files.Add([pscustomobject]@{ card = $t.card; file = $item })
  }
}

Write-Host ("[artifact_push] node={0} candidates={1} already-pushed={2}" -f $Node, $files.Count, $done.Count)

$maxBytes = [int64]$MaxMB * 1MB
$sent = 0; $skip = 0; $fail = 0
$manLines = New-Object System.Collections.ArrayList

foreach ($f in $files) {
  $fi = $f.file
  $size = [int64]$fi.Length
  $sha = Get-Sha256 $fi.FullName
  [void]$manLines.Add((@{ card = $f.card; path = $fi.FullName; bytes = $size; sha256 = $sha
      mtime = $fi.LastWriteTime.ToString("s"); node = $Node } | ConvertTo-Json -Compress))

  if ($size -gt $maxBytes) { Write-Host ("  SKIP too-big {0} ({1:N1} MB)" -f $fi.Name, ($size / 1MB)); $skip++; continue }
  if ($done.ContainsKey(("{0}|{1}" -f $sha, $size))) { $skip++; continue }
  if ($WhatIf) { Write-Host ("  DRY {0} {1:N1} MB" -f $fi.Name, ($size / 1MB)); $sent++; continue }

  $url = "{0}/artifact?node={1}&card={2}&name={3}" -f $Intake.TrimEnd('/'), $Node,
         [uri]::EscapeDataString($f.card), [uri]::EscapeDataString($fi.Name)
  try {
    $r = Invoke-WebRequest -Uri $url -Method Put -InFile $fi.FullName `
           -Headers @{ "X-Sha256" = $sha } -UseBasicParsing -TimeoutSec 3600
    if ($r.StatusCode -eq 200) {
      $line = @{ ts = (Get-Date).ToString("s"); card = $f.card; name = $fi.Name
                 bytes = $size; sha256 = $sha; stored = $fi.FullName } | ConvertTo-Json -Compress
      Add-Content -LiteralPath $pushed -Value $line -Encoding UTF8
      $sent++
      Write-Host ("  OK {0} {1:N1} MB" -f $fi.Name, ($size / 1MB))
    } else {
      $fail++; Write-Host ("  FAIL {0} HTTP {1}" -f $fi.Name, $r.StatusCode)
    }
  } catch {
    $fail++
    Write-Host ("  FAIL {0} {1}" -f $fi.Name, $_.Exception.Message)
  }
}

Set-Content -LiteralPath $man -Value ($manLines -join "`r`n") -Encoding UTF8
Write-Host ("[artifact_push] sent={0} skipped={1} failed={2} manifest={3}" -f $sent, $skip, $fail, $manLines.Count)
if ($fail -gt 0) { exit 1 }
exit 0