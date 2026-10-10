# fleet-mechanism-audit.ps1 - Group mechanism FUNCTIONAL liveness audit v1.0
# (council case C-20261010-01; cadence.md sec6 signal-4 L3 carrier; R4 family
#  root fix: "mechanism ran" != "mechanism works").
# Division of labor: task-health.ps1 covers PROCESS liveness (task exists, ran,
# exit code). THIS tool covers FUNCTIONAL liveness: the mechanism actually
# produced evidence of correct work. Evidence that forced it:
#   - OrderSentinel ran green every 2 min for 10 days while functionally blind
#     (log silent since 2026-09-29, C-20261009-04 E1) - task-health was green.
#   - vbs silence guard showed fake green for 7 days (P-2026-10-08-17).
#   - BigLife PoolGenLoop idled, audit-sentinel threshold drift, external-audit
#     shift gaps, ollama wedged 2h22m (D-20261010-10) - same class.
# Probes (read-only, in-process, ASCII-only body per encoding law):
#   1. sentinel_state  : .codely-cli\sentinel\state.json mtime <= 5 min
#   2. sentinel_log   : log tail date <= 26 h (v1.3.1 writes a daily HEARTBEAT
#                        line, so quiet days still prove the scanner lives)
#   3. fleetlink_state : listener state.json mtime <= 10 min (5-min keepalive)
#   4. silence_audit   : patrol\silence-audit.json age <= 25 h (guard daily floor)
#   5. patrol_stamp    : patrol\patrol-stamp.json present, age <= 8 d (F-09 law)
# Night round runs this in step 3 (机制自检). STALE/MISSING -> night report.
param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Continue'
$now = Get-Date
$flags = 0

function Probe([string]$name, [string]$detail) {
  Write-Output ('MECH {0} {1}' -f $name, $detail)
}

# 1) OrderSentinel state freshness (2-min tick writes state each run)
$st = Join-Path $Root '.codely-cli\sentinel\state.json'
if (Test-Path -LiteralPath $st) {
  $age = ($now - (Get-Item -LiteralPath $st).LastWriteTime).TotalMinutes
  if ($age -le 5) { Probe 'sentinel_state' ('OK age_min=' + [int]$age) }
  else { $script:flags++; Probe 'sentinel_state' ('STALE age_min=' + [int]$age) }
} else { $script:flags++; Probe 'sentinel_state' 'MISSING' }

# 2) OrderSentinel functional heartbeat (the C-20261009-04 E1 hole this exists for)
$lg = Join-Path $Root '.codely-cli\sentinel\log.txt'
if (Test-Path -LiteralPath $lg) {
  $last = Get-Content -LiteralPath $lg -Tail 1
  $lastDate = $null
  if ($last -match '^(\d{4}-\d{2}-\d{2})') { $lastDate = $Matches[1] }
  $hAge = 999
  if ($lastDate) { $hAge = ($now - [datetime]$lastDate).TotalHours }
  if ($hAge -le 26) { Probe 'sentinel_log' ('OK tail=' + $lastDate) }
  else { $script:flags++; Probe 'sentinel_log' ('STALE tail_hours=' + [int]$hAge + ' (C-04 blind class)') }
} else { $script:flags++; Probe 'sentinel_log' 'MISSING' }

# 3) FleetLink listener state freshness (5-min keepalive writes state)
$fl = $null
foreach ($c in @((Join-Path $env:USERPROFILE '.codely-cli\fleet-link\state.json'), (Join-Path $Root '.codely-cli\fleet-link\state.json'))) {
  if (Test-Path -LiteralPath $c) { $fl = $c; break }
}
if ($fl) {
  $age = ($now - (Get-Item -LiteralPath $fl).LastWriteTime).TotalMinutes
  if ($age -le 10) { Probe 'fleetlink_state' ('OK age_min=' + [int]$age) }
  else { $script:flags++; Probe 'fleetlink_state' ('STALE age_min=' + [int]$age) }
} else { Probe 'fleetlink_state' 'SKIP file not found' }

# 4) Silence guard audit freshness (HQ-SilenceGuard-Lane PT1M + daily 04:07)
$sa = Join-Path $Root '.codely-cli\patrol\silence-audit.json'
if (Test-Path -LiteralPath $sa) {
  $age = ($now - (Get-Item -LiteralPath $sa).LastWriteTime).TotalHours
  if ($age -le 25) { Probe 'silence_audit' ('OK age_h=' + [int]$age) }
  else { $script:flags++; Probe 'silence_audit' ('STALE age_h=' + [int]$age) }
} else { $script:flags++; Probe 'silence_audit' 'MISSING' }

# 5) Patrol claim stamp (F-09 law, <= 8 d; while missing this probe keeps a
#    known-open E1 visible EVERY shift instead of only on patrol day)
$ps = Join-Path $Root '.codely-cli\patrol\patrol-stamp.json'
if (Test-Path -LiteralPath $ps) {
  $age = ($now - (Get-Item -LiteralPath $ps).LastWriteTime).TotalDays
  if ($age -le 8) { Probe 'patrol_stamp' ('OK age_d=' + [int]$age) }
  else { $script:flags++; Probe 'patrol_stamp' ('STALE age_d=' + [int]$age) }
} else { $script:flags++; Probe 'patrol_stamp' 'MISSING (F-09 E1 open)' }

Write-Output ('MECHANISM AUDIT ' + $now.ToString('yyyy-MM-dd HH:mm') + ' flags=' + $flags)
