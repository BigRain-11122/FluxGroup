# order-sentinel.ps1 - FluxGroup Order Sentinel v1.3 (CEO order 2026-10-09 ~23:3x, C-20261009-04)
# v1.3 = blind-spot root fix. Evidence that forced this version: last wake in the
#   log was 2026-09-29 18:56 while state stayed {"day":"1009","max":0} - the ledger
#   had switched from TABLE rows (`| P-... |`) to BULLET rows (`- **P-...**`) and the
#   v1.2.2 regex `^\| P-2026-` matched NOTHING for 10 days. All CEO orders in that
#   window were delivered only by the 10-min pull cadence (or manual pokes).
# Changes:
#   1. dual row format: bullet `- **P-2026-...` AND legacy table `| P-2026-...`.
#   2. dual ledger scan: cph4/evolution-ledger.md P- rows PLUS docs/orders.md
#      registry CEO rows (rows without a P- twin never woke before).
#   3. SET cursor (the v1.2.2-noted "v1.3 candidate"): state = set of seen row keys;
#      every tick rescans the WHOLE files and wakes only keys absent from the set.
#      Position-independent, renumber-proof, heals the "late row with number <=
#      curMax never wakes" hole. Receipt edits touch status cells only -> keys stay
#      stable -> no re-wake. Rows archived out of the file drop from the set and,
#      if ever resurrected, legitimately re-wake. First run after migration =
#      BASELINE (no wake, no storm).
#   4. level gate on P- rows kept (P0/P1/T0/T1 only, first 400 chars; false-positive
#      cost = one harmless idle wake, false-negative cost = the 10-day blindness
#      above - we bias toward waking).
#   5. Disabled scheduled tasks are skipped ('off-skip'): CEO freeze orders (e.g.
#      BigLife census freeze) must never be re-armed by a mere ping.
#   6. map v2 routes: @company -> { machine: [tasks] }. LOCAL machine tasks wake
#      directly; REMOTE machine tasks are passed to fleet-dispatch via -Tasks so
#      poked nodes not only pull within seconds but also START the matching
#      allowlisted tasks (worker filters against node wake_tasks - safe).
#   7. broadcast keys (@liu-si style, defined in the map) wake every company loop.
# Conventions kept: P2/T2 never wake; @CPH4/@HQ = session-class faces with no
# schedulable task (manual-immediate law); wake-once via set cursor; 1-min stale
# lock; try/finally lock release; fail-soft dispatch hook; VBS-silent task (U060).
param([string]$Root = "C:\Users\sjs20\Desktop\FluxGroup")
$ErrorActionPreference = 'SilentlyContinue'
$Dir    = Join-Path $Root '.codely-cli\sentinel'
$Lock   = Join-Path $Dir 'lock'
$StateF = Join-Path $Dir 'state.json'
$LogF   = Join-Path $Dir 'log.txt'
$MapF   = Join-Path $Root 'Tools\order-sentinel-map.json'
$Ledger = Join-Path $Root 'cph4\evolution-ledger.md'
$Orders = Join-Path $Root 'docs\orders.md'
if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
function SL-Log([string]$msg) {
  Add-Content -Path $LogF -Value ("$(Get-Date -Format s) " + $msg) -Encoding UTF8
  if ((Get-Item $LogF -ErrorAction SilentlyContinue).Length -gt 100KB) {
    Set-Content -Path $LogF -Value ("$(Get-Date -Format s) " + $msg) -Encoding UTF8
  }
}
if (Test-Path $Lock) {
  $ageMin = ((Get-Date) - (Get-Item $Lock).LastWriteTime).TotalMinutes
  if ($ageMin -lt 1) { exit 0 }
  Remove-Item $Lock -Force
}
Set-Content -Path $Lock -Value "pid=$PID ts=$(Get-Date -Format s)" -Encoding ASCII
try {
  # ---- map (v2 routes; v1 flat-map backward compat) ----
  if (-not (Test-Path $MapF)) { SL-Log 'FATAL map missing'; return }
  try { $map = Get-Content -Raw -Encoding UTF8 $MapF | ConvertFrom-Json }
  catch { SL-Log ('FATAL map parse: ' + $_.Exception.Message); return }
  $routes = $map
  if ($map.PSObject.Properties.Name -contains 'routes') { $routes = $map.routes }

  # ---- local machine id (fleet-nodes.json host match; default bm-a) ----
  $LocalId = 'bm-a'
  try {
    $nc = Get-Content -Raw -Encoding UTF8 (Join-Path $Root 'Tools\fleet-nodes.json') | ConvertFrom-Json
    foreach ($n in @($nc.nodes)) {
      if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $LocalId = [string]$n.id; break }
    }
  } catch { }

  # ---- gather qualifying rows (set: key -> line) ----
  $keys = @{}
  $levelRx = '(?<![A-Za-z0-9])(P[01]|T[01])(?![0-9A-Za-z])'
  if (Test-Path $Ledger) {
    foreach ($ln in [System.IO.File]::ReadAllLines($Ledger, [System.Text.Encoding]::UTF8)) {
      $id = $null
      if ($ln -match '^- \*\*P-2026-\d{2}-\d{2}-\d{1,3}') { $id = $Matches[0] -replace '^- \*\*', '' }
      elseif ($ln -match '^\| P-2026-\d{2}-\d{2}-\d{1,3}') { $id = $Matches[0] -replace '^\| ', '' }
      if (-not $id) { continue }
      $head = $ln
      if ($head.Length -gt 400) { $head = $head.Substring(0, 400) }
      if ($head -notmatch $levelRx) { continue }
      if (-not $keys.ContainsKey($id)) { $keys[$id] = $ln }
    }
  }
  if (Test-Path $Orders) {
    foreach ($ln in [System.IO.File]::ReadAllLines($Orders, [System.Text.Encoding]::UTF8)) {
      if ($ln -notmatch '^\| ?(?:\d{4}-)?\d{2}-\d{2}[ ~]') { continue }
      $t = $ln.Trim()
      $k = $t.Substring(0, [Math]::Min(60, $t.Length))
      if (-not $keys.ContainsKey($k)) { $keys[$k] = $ln }
    }
  }

  # ---- load previous seen-set (v1.3 format) / migrate ----
  $seen = @{}
  $baseline = $false
  if (Test-Path $StateF) {
    try {
      $cur = Get-Content -Raw $StateF | ConvertFrom-Json
      if (($cur.PSObject.Properties.Name -contains 'seen') -and ($cur.seen -is [array])) {
        foreach ($s in @($cur.seen)) { if ($s) { $seen[[string]$s] = 1 } }
      } else { $baseline = $true }
    } catch { $baseline = $true }
  } else { $baseline = $true }

  # ---- resolve routes for unseen keys ----
  $wakeLocal = @{}
  $wakeRemote = @{}
  if (-not $baseline) {
    foreach ($k in $keys.Keys) {
      if ($seen.ContainsKey($k)) { continue }
      $ln = $keys[$k]
      foreach ($p in $routes.PSObject.Properties) {
        if ($ln -notmatch [regex]::Escape($p.Name)) { continue }
        $val = $p.Value
        if ($val -is [array]) { foreach ($t in @($val)) { if ($t) { $wakeLocal[[string]$t] = 1 } } }
        else {
          foreach ($m in $val.PSObject.Properties) {
            foreach ($t in @($m.Value)) {
              if (-not $t) { continue }
              if ([string]$m.Name -eq $LocalId) { $wakeLocal[[string]$t] = 1 }
              else { $wakeRemote[[string]$t] = 1 }
            }
          }
        }
      }
    }
  }

  # ---- persist new seen-set (exact current row keys) ----
  $arr = @($keys.Keys)
  $json = ''
  try { $json = ConvertTo-Json -InputObject (@{ seen = $arr; ver = 3 }) -Compress } catch { }
  if ($json) { Set-Content -Path $StateF -Value $json -Encoding UTF8 }

  # ---- wake local tasks (skip disabled = CEO freeze faces) ----
  $fired = @()
  if ($baseline) {
    SL-Log ('v1.3 baseline: rows=' + $keys.Count + ' (migration, no wake)')
  } else {
    foreach ($t in $wakeLocal.Keys) {
      $task = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
      if (-not $task) { $fired += ($t + ':NO-TASK'); continue }
      if ($task.State.ToString() -eq 'Running') { $fired += ($t + ':busy-skip'); continue }
      if ($task.State.ToString() -eq 'Disabled') { $fired += ($t + ':off-skip'); continue }
      Start-ScheduledTask -TaskName $t
      $fired += ($t + ':WAKE')
    }
    if ($fired.Count -gt 0) { SL-Log ('seen=' + $keys.Count + ' -> ' + ($fired -join ',')) }
    elseif ($seen.Count -eq 0 -and $keys.Count -gt 0) { SL-Log ('v1.3 first-ok: rows=' + $keys.Count + ' no-wake-keys') }
  }

  # ---- fleet hook: poke all tailnet nodes + pass remote tasks (fail-soft) ----
  if ($fired.Count -gt 0 -or $wakeRemote.Count -gt 0) {
    try {
      $fd = Join-Path $Root 'Tools\fleet-dispatch.ps1'
      if (Test-Path $fd) {
        $dp = @{ Root = $Root; Reason = 'order-sentinel'; Quiet = $true }
        if ($wakeRemote.Count -gt 0) { $dp['Tasks'] = @($wakeRemote.Keys) }
        & $fd @dp | Out-Null
      }
    } catch { }
  }
} finally { Remove-Item $Lock -Force -ErrorAction SilentlyContinue }
