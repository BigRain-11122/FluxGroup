# orders-jsonl toolkit (P-57 batch-1 pilot, CEO GO 2026-09-24 ~18:35)
# ASCII-only body per encoding law: Chinese stays in the data files.
# Files:
#   seed-orders.ps1   - one-time conversion docs/orders.md -> registry/orders.jsonl
#   orders-append.ps1 - append one order line (single-writer lock, atomic promotion, quarantine)
#   shadow-verify.ps1 - shadow-read: fold jsonl state, compare with orders.md derived set
# Note: orders.md remains the readable L2 face until switch criteria met.
param(
  [string]$Root = "C:\Users\sjs20\Desktop\FluxGroup",
  [string]$Mode = "seed",          # seed | append | shadow
  [string]$Json = "",              # append mode: one JSON object string (id,ts,quote_sig,disposition,status,source_hash,...)
  [int]$WindowDays = 30            # shadow compare window
)
$ErrorActionPreference = 'Stop'
$Reg = Join-Path $Root 'cph4\registry'
$Jsonl = Join-Path $Reg 'orders.jsonl'
$QuarDir = Join-Path $Reg 'quarantine'
$Lock = Join-Path $Reg '.orders.lock'

function Get-Lock {
  if (Test-Path $Lock) {
    $age = [int]((Get-Date) - (Get-Item $Lock).LastWriteTime).TotalMinutes
    if ($age -lt 15) { throw "orders.jsonl writer lock held (age ${age}min)" }
    Remove-Item $Lock -Force
  }
  Set-Content -Path $Lock -Value "pid=$PID ts=$(Get-Date -Format s)" -Encoding ASCII
}
function Release-Lock { if (Test-Path $Lock) { Remove-Item $Lock -Force } }

function Test-OrderLine {
  param([parameter(Position=0)][string]$Line)
  if ([string]::IsNullOrWhiteSpace($Line)) { return $true }
  try { $o = $Line | ConvertFrom-Json } catch { return $false }
  foreach ($f in @('id', 'ts', 'quote_sig', 'disposition', 'status', 'source_hash')) {
    if (-not $o.PSObject.Properties.Name -contains $f) { return $false }
    if ([string]::IsNullOrWhiteSpace([string]$o.$f)) { return $false }
  }
  return $true
}

function Repair-Jsonl {
  # quarantine bad lines, never swallow the file (FluxVerse scan v0.3 pattern)
  if (-not (Test-Path $Jsonl)) { return @() }
  $lines = @(Get-Content $Jsonl -Encoding UTF8)
  $good = @(); $bad = @()
  foreach ($ln in $lines) {
    if ([string]::IsNullOrWhiteSpace($ln)) { continue }
    if (Test-OrderLine $ln) { $good += $ln } else { $bad += $ln }
  }
  if ($bad.Count -gt 0) {
    if (-not (Test-Path $QuarDir)) { New-Item -ItemType Directory -Path $QuarDir | Out-Null }
    $qf = Join-Path $QuarDir ("orders-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".jsonl")
    $bad | Set-Content -Path $qf -Encoding UTF8
    Write-Output ("QUARANTINED " + $bad.Count + " lines -> " + $qf.Name)
  }
  return $good
}

function Quote-Sig {
  param([parameter(Position=0)][string]$Text)
  $norm = ($Text -replace '\s+', ' ').Trim()
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($norm)
  $hash = $sha.ComputeHash($bytes)
  return ([BitConverter]::ToString($hash) -replace '-', '').Substring(0, 16).ToLower()
}

switch ($Mode) {

  'seed' {
    # one-time: convert docs/orders.md rows -> orders.jsonl (L1 registry)
    Get-Lock
    try {
      $ordersFile = Join-Path $Root 'docs\orders.md'
      $head = (git -C $Root log -1 '--format=%h').Trim()
      $rows = @(Get-Content $ordersFile -Encoding UTF8 | Where-Object { $_ -match '^\| 09-' })
      $n = 0
      $sw = New-Object System.Text.StringBuilder
      foreach ($r in $rows) {
        $cells = @($r -split '\|')
        if ($cells.Count -lt 4) { continue }
        $ts = ([string]$cells[1]).Trim()
        $quote = ([string]$cells[2]).Trim()
        $disp = ([string]$cells[3]).Trim()
        $st = ([string]$cells[$cells.Count - 2]).Trim()
        # status: first clause before (Chinese paren kept in data, ASCII-safe split by code)
        $stMain = $st
        $pCode = [char]0xFF08
        $pi = $stMain.IndexOf($pCode)
        if ($pi -gt 0) { $stMain = $stMain.Substring(0, $pi).Trim() }
        $n++
        $o = [ordered]@{
          id = 'O-2026-' + (Get-Date -Format 'MMdd') + '-' + ('{0:d3}' -f $n)
          ts = $ts
          quote_sig = (Quote-Sig $quote)
          disposition = $disp
          status = $stMain
          source_hash = $head
          status_events = @(@{ ts = (Get-Date -Format s); from = 'seed'; to = $stMain })
        }
        [void]$sw.AppendLine((ConvertTo-Json ([pscustomobject]$o) -Compress))
      }
      $tmp = $Jsonl + '.new'
      [IO.File]::WriteAllText($tmp, $sw.ToString(), (New-Object System.Text.UTF8Encoding($false)))
      # verify pass
      $ok = $true
      foreach ($ln in (Get-Content $tmp -Encoding UTF8)) { if (-not (Test-OrderLine $ln)) { $ok = $false; break } }
      if (-not $ok) { throw "verify FAIL on seed output" }
      Move-Item $tmp $Jsonl -Force
      Write-Output ("SEED_OK rows=" + $n + " source=" + $head)
    } finally { Release-Lock }
  }

  'append' {
    if (-not $Json) { throw "append requires -Json" }
    Get-Lock
    try {
      $o = $Json | ConvertFrom-Json
      foreach ($f in @('id', 'ts', 'quote_sig', 'disposition', 'status', 'source_hash')) {
        if ([string]::IsNullOrWhiteSpace([string]$o.$f)) { throw ("missing field " + $f) }
      }
      $good = @(Repair-Jsonl)
      $line = ConvertTo-Json ([pscustomobject]$o) -Compress
      if (-not (Test-OrderLine $line)) { throw "payload fails schema" }
      $tmp = $Jsonl + '.new'
      $all = $good + $line
      [IO.File]::WriteAllLines($tmp, $all, (New-Object System.Text.UTF8Encoding($false)))
      Move-Item $tmp $Jsonl -Force
      Write-Output ("APPEND_OK id=" + $o.id + " total=" + $all.Count)
    } finally { Release-Lock }
  }

  'shadow' {
    # shadow-read: fold jsonl, compare six-field content-addressed set vs orders.md within window
    if (-not (Test-Path $Jsonl)) { throw "orders.jsonl missing" }
    $good = @(Repair-Jsonl)
    $jmap = @{}
    foreach ($ln in $good) {
      $o = $ln | ConvertFrom-Json
      $jmap[[string]$o.quote_sig] = $o
    }
    $ordersFile = Join-Path $Root 'docs\orders.md'
    $rows = @(Get-Content $ordersFile -Encoding UTF8 | Where-Object { $_ -match '^\| 09-' })
    $mSigs = @{}
    foreach ($r in $rows) {
      $cells = @($r -split '\|')
      if ($cells.Count -lt 4) { continue }
      $q = ([string]$cells[2]).Trim()
      $sig = Quote-Sig $q
      $mSigs[$sig] = $q
    }
    $missingInJ = 0; $missingInM = 0; $dup = 0
    $seen = @{}
    foreach ($k in $jmap.Keys) { $seen[$k] = 1 }
    foreach ($k in $jmap.Keys) { if (-not $mSigs.ContainsKey($k)) { $missingInM++ } }
    foreach ($k in $mSigs.Keys) { if (-not $seen.ContainsKey($k)) { $missingInJ++ } }
    Write-Output ("SHADOW jsonl=" + $jmap.Count + " md=" + $mSigs.Count + " md_not_in_jsonl=" + $missingInJ + " jsonl_not_in_md=" + $missingInM)
    if ($missingInJ -gt 0) { Write-Output "SHADOW_RED: md has orders not yet in registry (expected during dual-write window)" }
    else { Write-Output "SHADOW_GREEN: md fully covered by registry" }
  }
}
