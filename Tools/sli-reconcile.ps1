# sli-reconcile.ps1 - external-seat SLI reconciliation (G4: audit OUTSIDE the proxy seat)
# Phase 1-alpha of MASTER-AGENT BLUEPRINT v2 (O-20261014-1745). Deployed on bm-b via task-register
# (daily run), per the @bm-b orders row. Reads the group repo AFTER pull (git = sole data channel),
# computes the seat's SLI evidence lines, writes SLI-RECONCILE.md, and commits+pushes it (bm-b lane).
# Report format follows CHARTER section 6 (green-rate, avg calls per shift, freshness lines).
param([string]$Root = 'C:\Fluxgroup\FluxGroup')

$ErrorActionPreference = 'Stop'
$today  = Get-Date -Format 'yyyy-MM-dd'
$stamp  = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$logMd  = Join-Path $Root 'cph4\fleet\dispatcher\CEO-PROXY\LOG.md'
$dlMd   = Join-Path $Root 'cph4\fleet\dispatcher\DISPATCH-LOG.md'
$njMd   = Join-Path $Root 'cph4\fleet\dispatcher\NEED-JUDGMENT.md'
$outMd  = Join-Path $Root 'cph4\fleet\dispatcher\SLI-RECONCILE.md'
$probeHb = Join-Path $Root 'media\logs\proxy-probe-heartbeat.txt'
$carrierHb = Join-Path $Root 'media\logs\event-carrier-heartbeat.txt'

$shiftsToday = 0; $green = 0; $standard = 0; $event = 0; $callSum = 0
if (Test-Path $logMd) {
    foreach ($l in (Get-Content $logMd -Encoding UTF8)) {
        if ($l -match '## Round.*' + [regex]::Escape($today)) { $shiftsToday++ }
        if ($l -match '\|') {
            if ($l -match '绿') { $green++ } elseif ($l -match '标准') { $standard++ } elseif ($l -match '事件') { $event++ }
            if ($l -match '(\d+)\s*调用|调用数[:=]\s*(\d+)') {
                $n = $Matches[1]; if (-not $n) { $n = $Matches[2] }
                if ($n) { $callSum += [int]$n }
        }
    }
}
}
$typedTotal = $green + $standard + $event
$avgCalls = 0
if ($typedTotal -gt 0) { $avgCalls = [math]::Round($callSum / $typedTotal, 1) }
$greenRate = 0
if ($typedTotal -gt 0) { $greenRate = [math]::Round(100 * $green / $typedTotal, 0) }

$logAge = -1
if (Test-Path $logMd) { $logAge = [math]::Round(((Get-Date) - (Get-Item $logMd).LastWriteTime).TotalHours, 1) }
$dlAge = -1
if (Test-Path $dlMd) { $dlAge = [math]::Round(((Get-Date) - (Get-Item $dlMd).LastWriteTime).TotalHours, 1) }
$njItems = 0
if (Test-Path $njMd) {
    foreach ($l in (Get-Content $njMd -Encoding UTF8)) { $t = $l.Trim(); if ($t -and -not $t.StartsWith('#')) { $njItems++ } }
}
$probeAge = 'n/a'
if (Test-Path $probeHb) { $probeAge = ([math]::Round(((Get-Date) - (Get-Item $probeHb).LastWriteTime).TotalHours,1)).ToString() + 'h' }
$carrierAge = 'n/a'
if (Test-Path $carrierHb) { $carrierAge = ([math]::Round(((Get-Date) - (Get-Item $carrierHb).LastWriteTime).TotalMinutes,0)).ToString() + 'min' }

$lines = @()
$lines += '# SLI-RECONCILE (external seat)'
$lines += ''
$lines += ('> Generated ' + $stamp + ' by bm-b external reconciliation task (BLUEPRINT v2 Phase 1-alpha, G4).')
$lines += ('> Data source: group repo after pull. Parser is best-effort v1 - the seat step-9 loop refines it.')
$lines += ''
$lines += ('- Date: ' + $today)
$lines += ('- SLI-1 proxy LOG.md age: ' + $logAge + 'h (alarm >26h)')
$lines += ('- SLI-1b L0 DISPATCH-LOG.md age: ' + $dlAge + 'h (alarm >3h)')
$lines += ('- Shift lines typed today: green=' + $green + ' standard=' + $standard + ' event=' + $event + ' total=' + $typedTotal)
$lines += ('- Green rate: ' + $greenRate + '% (health band 40-70)')
$lines += ('- Avg calls per typed shift: ' + $avgCalls + ' (target <=12)')
$lines += ('- NEED-JUDGMENT open items: ' + $njItems)
$lines += ('- Probe heartbeat age: ' + $probeAge + ' | Carrier heartbeat age: ' + $carrierAge)
$lines += ''
$lines += '## Verdict line'
if ($logAge -gt 26) { $lines += '- RED: proxy silent death suspected (>26h)' }
elseif ($dlAge -gt 3) { $lines += '- RED: L0 down suspected (>3h)' }
else { $lines += '- GREEN (freshness lines ok)' }

[IO.File]::WriteAllLines($outMd, $lines)

# commit + push from bm-b lane (git push handled by bm-b session policy; scheduled task only writes + commits)
$g = 'C:\Program Files\Git\cmd\git.exe'
if (Test-Path $g) {
    & $g -C $Root add cph4/fleet/dispatcher/SLI-RECONCILE.md 2>&1 | Out-Null
    & $g -C $Root commit -m ('sli-reconcile: external seat report ' + $today + ' (BLUEPRINT v2 G4)') -- cph4/fleet/dispatcher/SLI-RECONCILE.md 2>&1 | Out-Null
    & $g -C $Root push origin HEAD:refs/heads/main 2>&1 | Out-Null
    Write-Output 'COMMIT+PUSH attempted (bm-b lane policy: push may be deferred to bm-b session)'
} else {
    Write-Output 'git not found - report written only'
}
Write-Output ('REPORT: ' + $outMd)
