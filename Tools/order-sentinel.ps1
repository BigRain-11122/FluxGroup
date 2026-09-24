# order-sentinel.ps1 - FluxGroup Order Sentinel (CEO flow-speed order 2026-09-24 ~21:35)
# Purpose: wake target OS loops within ~2min when new P0/P1/T0/T1 rows land in the
#          evolution ledger, instead of waiting for the next 10-min round.
# Laws: silent (schtasks -WindowStyle Hidden per CEO silence law), single-instance
#       lock 2min, ASCII-only body (encoding law - Chinese company tags live in
#       order-sentinel-map.json), idempotent wake-once per ledger line count.
# Level filter: P0/P1/T0/T1 rows only (T2/P2 ride the shift rounds by design).
param([string]$Root = "C:\Users\sjs20\Desktop\FluxGroup")
$ErrorActionPreference = 'SilentlyContinue'
$Dir    = Join-Path $Root '.codely-cli\sentinel'
$Lock   = Join-Path $Dir 'lock'
$StateF = Join-Path $Dir 'state.json'
$LogF   = Join-Path $Dir 'log.txt'
$MapF   = Join-Path $Root 'Tools\order-sentinel-map.json'
$Ledger = Join-Path $Root 'cph4\evolution-ledger.md'
if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
if (Test-Path $Lock) {
  $ageMin = ((Get-Date) - (Get-Item $Lock).LastWriteTime).TotalMinutes
  if ($ageMin -lt 2) { exit 0 }
  Remove-Item $Lock -Force
}
Set-Content -Path $Lock -Value "pid=$PID ts=$(Get-Date -Format s)" -Encoding ASCII
try {
  if (-not (Test-Path $MapF)) { exit 0 }
  $map = Get-Content -Raw -Encoding UTF8 $MapF | ConvertFrom-Json
  $lines = [System.IO.File]::ReadAllLines($Ledger, [System.Text.Encoding]::UTF8)
  $n = $lines.Count
  $seen = 0
  if (Test-Path $StateF) { $seen = [int](Get-Content -Raw $StateF | ConvertFrom-Json).seen }
  if ($seen -lt 0) { $seen = 0 }
  if ($seen -ge $n) {
    Set-Content -Path $StateF -Value ('{"seen":' + $n + '}') -Encoding ASCII
    exit 0
  }
  $wake = @{}
  for ($i = $seen; $i -lt $n; $i++) {
    $ln = $lines[$i]
    if ($ln -notlike '| P-20*') { continue }
    if ($ln -notmatch '\| (P[01]|T[01])') { continue }
    foreach ($p in $map.PSObject.Properties) {
      if ($ln -match [regex]::Escape($p.Name)) {
        foreach ($t in $p.Value) { if ($t) { $wake[$t] = 1 } }
      }
    }
  }
  Set-Content -Path $StateF -Value ('{"seen":' + $n + '}') -Encoding ASCII
  $fired = @()
  foreach ($t in $wake.Keys) {
    $task = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
    if (-not $task) { $fired += ($t + ':NO-TASK'); continue }
    if ($task.State.ToString() -eq 'Running') { $fired += ($t + ':busy-skip'); continue }
    Start-ScheduledTask -TaskName $t
    $fired += ($t + ':WAKE')
  }
  if ($fired.Count -gt 0) {
    $entry = "$(Get-Date -Format s) seen=$n -> $($fired -join ',')"
    Add-Content -Path $LogF -Value $entry -Encoding UTF8
    if ((Get-Item $LogF -ErrorAction SilentlyContinue).Length -gt 100KB) {
      Set-Content -Path $LogF -Value $entry -Encoding UTF8
    }
  }
} finally { Remove-Item $Lock -Force -ErrorAction SilentlyContinue }
