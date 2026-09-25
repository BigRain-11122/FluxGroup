# fleet-liveness-watch.ps1 - Fleet Liveness Watch v1.0 (CEO order U205 2026-09-25:
# fleet info must stay unobstructed; no silent offline / missing-heartbeat states.
# Charter: docs/fleet-liveness-charter.md. REUSES (anti-dup law #1):
#   fleet-audit.ps1  - heartbeat aggregation (-Json snapshot)
#   task-health.ps1  - scheduler five-signal face (SUMMARY/FLAGS stdout lines)
#   docs/patrol-ledger.md - OPEN/ESCALATED rows = ready-made remediation notes
# Host-scope auto-heal = THIS machine's info-chain tasks only (F-08 law):
#   MiniGameEngineTick / MiniGameCockpitBeat / MiniGameCeoDeskServer.
# Cross-host remediation is never attempted here - annotate + escalate.
# ASCII-only body (encoding law). Single-flight lock, stale takeover 4 min.
param(
    [string]$JsonDir = (Join-Path $env:USERPROFILE '.codely-cli\fleet-liveness'),
    [int]$DeskPort = 8791,
    [int]$PatrolThrottleMin = 120
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot   # Tools\.. = FluxGroup root

# ---- single-flight lock (stale takeover 4 min) ----
$lockPath = Join-Path $env:TEMP 'fleet-liveness-watch.lock'
if (Test-Path $lockPath) {
    try {
        $la = ((Get-Date) - (Get-Item $lockPath).LastWriteTime).TotalMinutes
        if ($la -lt 4) { Write-Output 'LIVENESS SKIP: previous run holds the lock'; exit 0 }
    } catch { }
}
try { Set-Content -LiteralPath $lockPath -Value ('run ' + (Get-Date -Format s)) -ErrorAction Stop } catch { Write-Output 'LIVENESS SKIP: lock write fail'; exit 0 }

$actions = @()
function Add-Action([string]$what, [string]$detail) {
    $script:actions += @{ ts = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); do = $what; detail = $detail }
    Write-Output ('ACTION ' + $what + ' ' + $detail)
}

# ---- 1) heartbeat aggregation (reuse, in-process: zero child consoles) ----
$auditSnap = Join-Path $env:USERPROFILE '.codely-cli\fleet-audit\last.json'
try { & (Join-Path $PSScriptRoot 'fleet-audit.ps1') -Json 2>$null | Out-Null } catch { }
$ErrorActionPreference = 'Continue'
$auditRows = @()
if (Test-Path -LiteralPath $auditSnap) {
    try {
        $parsed = Get-Content -LiteralPath $auditSnap -Raw -Encoding UTF8 | ConvertFrom-Json
        # PS5.1 law: top-level JSON array arrives as ONE Object[] (not unrolled) -
        # flatten one level so both PS5.1 and PS7 shapes yield the row set.
        foreach ($p in @($parsed)) {
            if ($p -is [System.Array]) { $auditRows += @($p) } else { $auditRows += $p }
        }
    } catch { $auditRows = @() }
}

# ---- 2) scheduler face (reuse; parse stable SUMMARY/FLAGS lines; in-process) ----
$schedUnhealthy = -1; $schedFlags = ''
try {
    $th = & (Join-Path $PSScriptRoot 'task-health.ps1') 2>$null
    foreach ($ln in @($th)) {
        if ($ln -match '^SUMMARY unhealthy=(\d+)') { $schedUnhealthy = [int]$Matches[1] }
        if ($ln -match '^FLAGS: (.+)$') { $schedFlags = $Matches[1] }
    }
} catch { }
$ErrorActionPreference = 'Continue'

# ---- 3) open PT rows -> entity remediation map ----
# PT-10: fetch + read origin/main rows too (local HQ clone can lag between
# patrol rounds), merge-union with wt (wt wins on same id). PT-13: status cells
# may carry annotations ("OPEN (in-window...)") - prefix-match the cell, do not
# require a bare OPEN|ESCALATED token.
$entPT = @{}
try {
    $led = Join-Path $root 'docs\patrol-ledger.md'
    $ledLines = @()
    if (Test-Path -LiteralPath $led) { $ledLines += @(Get-Content -LiteralPath $led -Encoding UTF8) }
    try {
        & git -C $root fetch --quiet 2>$null
        $ol = & git -C $root show 'origin/main:docs/patrol-ledger.md' 2>$null
        if ($ol) {
            foreach ($ln in @($ol)) {
                if ($ln -match '^\|\s*(PT-\d{8}-\d+)\s*\|' -and $ledLines -notcontains $ln) { $ledLines += $ln }
            }
        }
    } catch { }
    foreach ($ln in $ledLines) {
        $ptId = ''
        if ($ln -match '^\|\s*(PT-\d{8}-\d+)\s*\|') { $ptId = $Matches[1] } else { continue }
        if ($ln -notmatch '\|\s*(OPEN|ESCALATED)\b[^|]*\|') { continue }
        $cols = $ln -split '\|'
        if ($cols.Count -ge 4) {
            $ent = ([string]$cols[3]).Trim()
            if ($ent) { if (-not $entPT[$ent]) { $entPT[$ent] = @() }; $entPT[$ent] += $ptId }
        }
    }
} catch { }

# ---- entity map ----
function Ent-Of([string]$id) {
    if ($id -like 'BG-*') { return 'MiniGame' }
    if ($id -like 'bm-*') { return 'BigMoney' }
    if ($id -eq 'bigstream') { return 'BigStream' }
    if ($id -eq 'bigcompute') { return 'BigCompute' }
    return ''
}

# ---- alerts bookkeeping ----
New-Item -ItemType Directory -Force -Path $JsonDir | Out-Null
$alertsFile = Join-Path $JsonDir 'alerts.jsonl'

# ---- 4) grade + annotate + heal + escalate ----
$GOOD = @('OK', 'GREEN-IDLE', 'YELLOW-HEAVY')
$machines = @()
$verdict = 'GREEN'
foreach ($r in $auditRows) {
    $id = [string]$r.id
    $flag = [string]$r.flag
    $note = ''
    if ($GOOD -notcontains $flag) {
        if ($flag -eq 'OFFLINE' -or $flag -eq 'NO_TS') { $verdict = 'RED' }
        elseif ($verdict -eq 'GREEN') { $verdict = 'AMBER' }
        $ent = Ent-Of $id
        if ($ent -and $entPT.ContainsKey($ent) -and @($entPT[$ent]).Count -gt 0) {
            $note = ('rectifying ' + ((@($entPT[$ent]) | Select-Object -First 2) -join ','))
        } else {
            # unannotated bad state -> alert + throttled patrol trigger
            $lastAlert = $null
            if (Test-Path -LiteralPath $alertsFile) {
                foreach ($al in ((Get-Content -LiteralPath $alertsFile -Encoding UTF8) | Where-Object { $_ -match '\S' })) {
                    try { $ao = $al | ConvertFrom-Json; if ([string]$ao.id -eq $id) { $lastAlert = $ao } } catch { }
                }
            }
            $fresh = $false
            if ($lastAlert -and $lastAlert.ts) {
                try { $fresh = (((Get-Date) - [datetime]$lastAlert.ts).TotalMinutes -lt $PatrolThrottleMin) } catch { $fresh = $false }
            }
            $note = 'escalated'
            Add-Action 'alert' ($id + ' flag=' + $flag + ' no PT cover - alert recorded')
            try {
                @{ ts = (Get-Date -Format s); id = $id; flag = $flag } | ConvertTo-Json -Compress | Add-Content -LiteralPath $alertsFile -Encoding UTF8
                $allLines = @((Get-Content -LiteralPath $alertsFile -Encoding UTF8) | Where-Object { $_ -match '\S' })
                if ($allLines.Count -gt 200) { [IO.File]::WriteAllLines($alertsFile, ($allLines | Select-Object -Last 200)) }
            } catch { }
            if (-not $fresh) {
                try {
                    Start-ScheduledTask -TaskName 'FluxGroup-PatrolRound' -ErrorAction Stop
                    Add-Action 'escalate-patrol' ($id + ' flag=' + $flag + ' - patrol triggered (runner claim-stamp may skip = honest)')
                } catch { Add-Action 'escalate-patrol-fail' ($id + ' trigger error') }
            }
        }
    }
    # BG-C host-scope self-heal (info-chain restart, Ready-state only)
    if ($id -eq 'BG-C' -and $GOOD -notcontains $flag) {
        foreach ($tn in @('MiniGameEngineTick', 'MiniGameCockpitBeat')) {
            try {
                $t = Get-ScheduledTask -TaskName $tn -ErrorAction Stop
                if ($t.State -eq 'Ready') {
                    Start-ScheduledTask -TaskName $tn
                    Add-Action 'self-heal' ($tn + ' restarted (BG-C flag=' + $flag + ')')
                }
            } catch { }
        }
    }
    $machines += @{ id = $id; flag = $flag; last_seen = [string]$r.last_seen; note = $note }
}

# ---- 5) info-chain probes (C host) ----
# CeoDesk health -> restart when dead
$deskOk = $false
try {
    $h = Invoke-RestMethod -Uri ('http://127.0.0.1:' + $DeskPort + '/api/health') -TimeoutSec 3 -ErrorAction Stop
    $deskOk = $true
} catch { $deskOk = $false }
if (-not $deskOk) {
    try {
        $t = Get-ScheduledTask -TaskName 'MiniGameCeoDeskServer' -ErrorAction Stop
        if ($t.State -eq 'Ready') {
            Start-ScheduledTask -TaskName 'MiniGameCeoDeskServer'
            Add-Action 'self-heal' 'MiniGameCeoDeskServer restarted (health probe failed)'
        } else { Add-Action 'observe' ('MiniGameCeoDeskServer state=' + $t.State + ' but health probe failed (owner-lane signal)') }
    } catch { }
}
# flagged info-chain tasks from task-health -> restart when Ready
if ($schedFlags) {
    foreach ($tn in @('MiniGameEngineTick', 'MiniGameCockpitBeat', 'MiniGameCeoDeskServer')) {
        if ($schedFlags -match ('[=(]' + $tn + '([,=\s]|$)') -or $schedFlags -match ($tn + '=')) {
            try {
                $t = Get-ScheduledTask -TaskName $tn -ErrorAction Stop
                if ($t.State -eq 'Ready') {
                    Start-ScheduledTask -TaskName $tn
                    Add-Action 'self-heal' ($tn + ' restarted (task-health flag)')
                }
            } catch { }
        }
    }
}
if ($schedUnhealthy -gt 0 -and $verdict -eq 'GREEN') { $verdict = 'AMBER' }

# ---- 6) publish liveness.json ----
$snap = @{
    ts = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    verdict = $verdict
    machines = $machines
    sched = @{ unhealthy = $schedUnhealthy; flags = $schedFlags }
    desk_health = $deskOk
    actions = $actions
}
try {
    [IO.File]::WriteAllText((Join-Path $JsonDir 'liveness.json'), ($snap | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding $false))
} catch { }

Write-Output ('LIVENESS ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' verdict=' + $verdict + ' machines=' + $machines.Count + ' sched_unhealthy=' + $schedUnhealthy + ' actions=' + $actions.Count)
try { Remove-Item -LiteralPath $lockPath -ErrorAction SilentlyContinue } catch { }
