# integrity-sentinel.ps1 - Group system-integrity tripwire v1.0 (council audit batch
# 2026-09-29). Trigger: two unexplained integrity events in two days - 09-28 10:03-10:12
# ~30 scheduled tasks mass-disabled (found 9h later, cause unknown), and 09-29 15:35-15:44
# an external sync storm destroyed 8 tracked engine files + 9 runtime state files in
# compute/BigCompute (found by manual audit). This tool cuts detection latency from
# hours to <=5min and leaves a forensic trail.
# Probes (read-only except alert sink):
#   1) scheduler diff   - task Disabled<->Enabled transitions, task disappearance,
#                        mass-event storm signature (>=5 transitions in one tick)
#   2) deletion scan   - git tracked-file deletions (D-lines) across the 8 repos
# Alert sink = fleet-liveness alerts.jsonl (docs/fleet-liveness-charter.md sec 5/7
# contract); consumed by guard round / patrol / CEO surfaces.
# Anti-dup: reuses no other mechanism's scope (task-health = nightly full audit;
# this = 5min delta tripwire). ASCII-only body (encoding law, PS 5.1 safe).
# Single-flight lock 4 min stale takeover. T2 + 7-day CEO veto window (cadence.md).

param(
    [string]$StateDir = (Join-Path $env:USERPROFILE '.codely-cli\fleet-liveness'),
    [int]$ThrottleMin = 120
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$now = Get-Date

# ---- single-flight lock (stale takeover 4 min) ----
$lockPath = Join-Path $env:TEMP 'integrity-sentinel.lock'
if (Test-Path $lockPath) {
    try { if (((Get-Date) - (Get-Item $lockPath).LastWriteTime).TotalMinutes -lt 4) { exit 0 } } catch { }
}
try { Set-Content -LiteralPath $lockPath -Value 'run' -ErrorAction Stop } catch { exit 0 }

if (-not (Test-Path $StateDir)) { New-Item -ItemType Directory -Path $StateDir -Force | Out-Null }
$alertsPath  = Join-Path $StateDir 'alerts.jsonl'
$schedPath   = Join-Path $StateDir 'integrity-sched.json'
$alertedPath = Join-Path $StateDir 'integrity-alerted.json'

$alerts = @()
function Add-Alert([string]$type, [string]$detail) {
    $script:alerts += @{ ts = $now.ToString('yyyy-MM-dd HH:mm:ss'); type = $type; detail = $detail }
}

# ---- probe 1: scheduler state diff (Disabled-flag + existence only; Ready<->Running is noise) ----
$transitions = 0
try {
    $prev = @{}
    if (Test-Path $schedPath) {
        $raw = Get-Content -LiteralPath $schedPath -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($p in @($raw)) {
            if ($p -is [System.Array]) { foreach ($q in @($p)) { $prev[[string]$q.name] = [string]$q.state } }
            else { $prev[[string]$p.name] = [string]$p.state }
        }
    }
    $cur = @{}
    $curRows = @()
    foreach ($t in @(Get-ScheduledTask -TaskPath '\' -ErrorAction SilentlyContinue)) {
        if ($t.TaskName -match '^(Microsoft|OneDrive|Adobe|Google|Edge|NVIDIA|AMD)') { continue }
        $cur[$t.TaskName] = [string]$t.State
        $curRows += @{ name = $t.TaskName; state = [string]$t.State }
    }
    foreach ($k in @($cur.Keys)) {
        if (-not $prev.ContainsKey($k)) { continue }
        $wasDis = ($prev[$k] -eq 'Disabled'); $isDis = ($cur[$k] -eq 'Disabled')
        if ($wasDis -eq $isDis) { continue }
        $transitions++
        if ($wasDis -and -not $isDis) { Add-Alert 'sched-enabled' $k }
        elseif (-not $wasDis -and $isDis) { Add-Alert 'sched-disabled' $k }
    }
    foreach ($k in @($prev.Keys)) {
        if (-not $cur.ContainsKey($k)) { Add-Alert 'sched-deleted' $k; $transitions++ }
    }
    ConvertTo-Json -InputObject $curRows -Compress | Set-Content -LiteralPath $schedPath -Encoding UTF8
} catch {
    Add-Alert 'sched-probe-error' ($_.Exception.Message -replace '\r|\n',' ')
}

# ---- probe 2: tracked-file deletion scan (straight D-lines; renames are "R" and skipped) ----
$repos = @('gaming/MiniGame', 'quant/bigmoney', 'media/BigStream', 'life/BigLife', 'domain/BigDomain', 'compute/BigCompute', 'gaming/FluxVerse')
foreach ($r in $repos) {
    try {
        $st = & git -C (Join-Path $root ($r -replace '/', '\')) status --porcelain 2>$null
        foreach ($ln in @($st)) {
            if ($ln -match '^( D|D )') { Add-Alert 'tracked-deleted' ($r + ': ' + (($ln -replace '^( D|D )', '').Trim())) }
        }
    } catch { }
}
try {
    $st = & git -C $root status --porcelain 2>$null
    foreach ($ln in @($st)) {
        if ($ln -match '^( D|D )') { Add-Alert 'tracked-deleted' ('HQ: ' + (($ln -replace '^( D|D )', '').Trim())) }
    }
} catch { }

# ---- storm signature (09-28 precedent: ~30 tasks flipped in one window) ----
if ($transitions -ge 5) { Add-Alert 'sched-storm' ($transitions.ToString() + ' scheduler flips in one 5min tick - mass event, check alerts above') }

# ---- throttle map (same signature silent for $ThrottleMin) + sink ----
$alerted = @{}
if (Test-Path $alertedPath) {
    try {
        $ao = Get-Content -LiteralPath $alertedPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($ao) { $ao.PSObject.Properties | ForEach-Object { $alerted[$_.Name] = [string]$_.Value } }
    } catch { }
}
$emitted = 0
foreach ($a in $alerts) {
    $sig = $a.type + '|' + $a.detail
    if ($alerted.ContainsKey($sig)) {
        try {
            if ($alerted[$sig] -match '^\d{4}-\d{2}-\d{2} ' -and (((Get-Date) - [DateTime]::ParseExact($alerted[$sig], 'yyyy-MM-dd HH:mm:ss', $null)).TotalMinutes -lt $ThrottleMin)) { continue }
        } catch { }
    }
    $detail = $a.detail -replace '\\', '\\\\' -replace '"', '\"'
    $line = '{"ts":"' + $a.ts + '","src":"integrity-sentinel","type":"' + $a.type + '","detail":"' + $detail + '"}'
    Add-Content -LiteralPath $alertsPath -Value $line -Encoding UTF8
    $alerted[$sig] = $now.ToString('yyyy-MM-dd HH:mm:ss')
    $emitted++
}
# prune throttle map entries older than 24h (bounded state file)
$pruned = @{}
foreach ($k in @($alerted.Keys)) {
    try { if (((Get-Date) - [DateTime]::ParseExact($alerted[$k], 'yyyy-MM-dd HH:mm:ss', $null)).TotalHours -lt 24) { $pruned[$k] = $alerted[$k] } } catch { }
}
ConvertTo-Json -InputObject $pruned -Compress | Set-Content -LiteralPath $alertedPath -Encoding UTF8
Remove-Item $lockPath -Force -ErrorAction SilentlyContinue
Write-Output ('INTEGRITY ' + $now.ToString('yyyy-MM-dd HH:mm') + ' alerts-emitted=' + $emitted + ' (probes: scheduler diff + 8-repo tracked-deletion scan)')
