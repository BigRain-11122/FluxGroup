# order-sentinel.ps1 - FluxGroup Order Sentinel v1.2 (CEO flow-speed order 2026-09-24 ~21:35)
# v1.2 fix (same night, honest log): v1.1 used a LINE-COUNT cursor - blind to mid-file
#   inserts (the ledger grows by inserting P-rows in the table area, so a tail cursor
#   only ever scanned shifted old lines and never saw new rows). Cursor is now
#   (day, max-P-number) parsed from row IDs: every tick rescans ALL of today's rows
#   whose ID number exceeds the cursor - position-independent by design.
#   New-day rollover: baseline to current max without waking (prevents day-start storm).
#   Legacy {seen:N} state auto-migrates to the new format as a no-wake baseline.
# v1.1 fixes (kept): single-case map keys (PS5.1 ConvertFrom-Json keys are
#   case-insensitive -> duplicate-case keys = terminating parse error), `return`
#   inside try (PS5.1 `exit` skips finally -> lock leak), stale-lock threshold 1min,
#   map load try/catch with FATAL log line instead of silent death.
# v1.2.2 note (2026-09-26 multi-writer battle): rows that arrive at line-start
#   LATE (fused mid-line during rebase churn, then unfused) with a number <= the
#   cursor max are NEVER woken (cursor only scans num > curMax) - after any
#   ledger row re-insert/renumber, check row-number vs state.json max and
#   manually Start-ScheduledTask if below; structural fix (content-hash cursor)
#   = v1.3 candidate, not yet law.
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
  if ($ageMin -lt 1) { exit 0 }
  Remove-Item $Lock -Force
}
Set-Content -Path $Lock -Value "pid=$PID ts=$(Get-Date -Format s)" -Encoding ASCII
try {
  if (-not (Test-Path $MapF)) {
    Add-Content -Path $LogF -Value "$(Get-Date -Format s) FATAL map missing" -Encoding UTF8
    return
  }
  try { $map = Get-Content -Raw -Encoding UTF8 $MapF | ConvertFrom-Json }
  catch {
    Add-Content -Path $LogF -Value "$(Get-Date -Format s) FATAL map parse: $($_.Exception.Message)" -Encoding UTF8
    return
  }
  $today = Get-Date -Format 'MMdd'
  $curDay = ''; $curMax = 0
  if (Test-Path $StateF) {
    try {
      $cur = Get-Content -Raw $StateF | ConvertFrom-Json
      if ($cur.PSObject.Properties.Name -contains 'day') { $curDay = [string]$cur.day; $curMax = [int]$cur.max }
      elseif ($cur.PSObject.Properties.Name -contains 'seen') { $curDay = $today; $curMax = 999 }
    } catch {}
  }
  $lines = [System.IO.File]::ReadAllLines($Ledger, [System.Text.Encoding]::UTF8)
  $rows = @(); $dayMax = 0
  foreach ($ln in $lines) {
    if ($ln -notmatch '^\| P-2026-(\d{2})-(\d{2})-(\d{1,3})') { continue }
    if (($Matches[1] + $Matches[2]) -ne $today) { continue }
    $num = [int]$Matches[3]
    $rows += ,@($num, $ln)
    if ($num -gt $dayMax) { $dayMax = $num }
  }
  if ($curDay -ne $today) { $curMax = 0 }
  $wake = @{}
  foreach ($r in $rows) {
    $num = $r[0]; $ln = $r[1]
    if ($num -le $curMax) { continue }
    if ($ln -notmatch '\| (P[01]|T[01])') { continue }
    foreach ($p in $map.PSObject.Properties) {
      if ($ln -match [regex]::Escape($p.Name)) {
        foreach ($t in $p.Value) { if ($t) { $wake[$t] = 1 } }
      }
    }
  }
  Set-Content -Path $StateF -Value ('{"day":"' + $today + '","max":' + $dayMax + '}') -Encoding ASCII
  $fired = @()
  foreach ($t in $wake.Keys) {
    $task = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
    if (-not $task) { $fired += ($t + ':NO-TASK'); continue }
    if ($task.State.ToString() -eq 'Running') { $fired += ($t + ':busy-skip'); continue }
    Start-ScheduledTask -TaskName $t
    $fired += ($t + ':WAKE')
  }
  if ($fired.Count -gt 0) {
    $entry = "$(Get-Date -Format s) seen=day:$today max:$dayMax -> $($fired -join ',')"
    Add-Content -Path $LogF -Value $entry -Encoding UTF8
    if ((Get-Item $LogF -ErrorAction SilentlyContinue).Length -gt 100KB) {
      Set-Content -Path $LogF -Value $entry -Encoding UTF8
    }
  }
} finally { Remove-Item $Lock -Force -ErrorAction SilentlyContinue }
