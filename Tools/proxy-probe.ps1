# proxy-probe.ps1 - HQ-MA-ProxyProbe action body (G13 monitor-the-monitor)
# Phase 1-alpha of MASTER-AGENT BLUEPRINT v2 (O-20261014-1745). Registered ONLY via Tools/task-register.ps1 (U060).
# Watches: proxy shift log freshness (6h), L0 dispatch log freshness (3h), event-carrier heartbeat (2h).
# 2026-10-25 R2.29 (T1): shift-log threshold 26h -> 6h. Why: the 8-shift durable cron only fires while a
# Codely REPL sits idle, and no persistent REPL exists here, so the probe->carrier path is the ONLY driver.
# At 26h the effective metronome was ~1 event shift/day, which left the receipt radar ("unacked >2h => poke")
# and the deadline radar 26h coarse - blind by construction. 6h x carrier daily cap 6 = at most 4 shifts/day.
# Alarms -> proxy-probe-alarms.log (append) + proxy-probe-current.json (overwrite snapshot, consumed by the
# carrier) + NEED-JUDGMENT.md (best-effort, L0 may regenerate it). Own heartbeat for the morning shift check.
$ErrorActionPreference = 'Stop'
$root  = 'C:\Users\sjs20\Desktop\FluxGroup'
$pmlog = Join-Path $root 'cph4\fleet\dispatcher\CEO-PROXY\LOG.md'
$dl    = Join-Path $root 'cph4\fleet\dispatcher\DISPATCH-LOG.md'
$cb    = Join-Path $root 'media\logs\event-carrier-heartbeat.txt'
$hb    = Join-Path $root 'media\logs\proxy-probe-heartbeat.txt'
$alarms = Join-Path $root 'media\logs\proxy-probe-alarms.log'
$current = Join-Path $root 'media\logs\proxy-probe-current.json'
$nj    = Join-Path $root 'cph4\fleet\dispatcher\NEED-JUDGMENT.md'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$found = @()

if (Test-Path $pmlog) {
    $age = ((Get-Date) - (Get-Item $pmlog).LastWriteTime).TotalHours
    if ($age -gt 26) { $found += ('PROXY-SILENT-DEATH: CEO-PROXY/LOG.md age {0:N1}h (>26h)' -f $age) }
    elseif ($age -gt 6) { $found += ('SHIFT-OVERDUE: CEO-PROXY/LOG.md age {0:N1}h (>6h)' -f $age) }
} else { $found += 'PROXY-SILENT-DEATH: CEO-PROXY/LOG.md missing' }

if (Test-Path $dl) {
    $age2 = ((Get-Date) - (Get-Item $dl).LastWriteTime).TotalHours
    if ($age2 -gt 3) { $found += ('L0-DOWN: DISPATCH-LOG.md age {0:N1}h (>3h)' -f $age2) }
} else { $found += 'L0-DOWN: DISPATCH-LOG.md missing' }

if (Test-Path $cb) {
    $age3 = ((Get-Date) - (Get-Item $cb).LastWriteTime).TotalMinutes
    if ($age3 -gt 120) { $found += ('EVENT-CARRIER-DOWN: heartbeat age {0:N0}min (>120)' -f $age3) }
} else {
    # first-boot artifact: carrier never ran yet != carrier down (v1.1 - log only, no alarm)
    Add-Content -Path $alarms -Value ("$stamp | INFO carrier heartbeat not present yet (first boot - no alarm)") -Encoding UTF8
}

foreach ($a in $found) {
    Add-Content -Path $alarms -Value ("$stamp | $a") -Encoding UTF8
    Add-Content -Path $nj -Value ("[$stamp][PROBE] $a (probe alarm -> carrier/patrol revive path)") -Encoding UTF8
}
$snap = @{ stamp = $stamp; alarms = $found } | ConvertTo-Json
Set-Content -Path $current -Value $snap -Encoding UTF8
Set-Content -Path $hb -Value "alive $stamp alarms=$($found.Count)" -Encoding UTF8
exit 0
