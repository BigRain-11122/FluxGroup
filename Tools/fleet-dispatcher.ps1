# fleet-dispatcher.ps1 - HQ-FleetDispatcher L0 deterministic round (v2, 2026-10-27)
# CEO order 2026-10-27: an "open" card is not work; idle with work is a P1, not a NOTE.
# v1 counted every status=open card as supply and only appended QUEUE-LOW lines, so the
# fleet could sit at 0% with 8 "open" cards for days while the log looked normal.
# v2 adds: executable predicate, production-queue supply check, idle-with-work alarm,
# machine-readable STATE.json (single source for idle-watch / proxy-carrier / rounds).
# Layer 0: rules + probes + flags ONLY. Never touches git (L2 owns ledger writes).
$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$dir = Join-Path $root 'cph4\fleet\dispatcher'
$poolF = Join-Path $dir 'POOL.json'
$queueF = Join-Path $root 'cph4\fleet\PRODUCTION-QUEUE.jsonl'
$claimF = Join-Path $root 'cph4\fleet\queue-receipts\_last_claim.json'
$idleF = Join-Path $root '.codely-cli\tmp\fleet-idle-watch\state.json'
$stateF = Join-Path $dir 'STATE.json'
$clockF = Join-Path $dir 'CLOCK-SKEW.json'
$logF = Join-Path $dir 'DISPATCH-LOG.md'
$judgF = Join-Path $dir 'NEED-JUDGMENT.md'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
$out = @()

function Route-Lane([string]$text) {
    $t = $text.ToLower()
    if ($t -match 'kf|i2v|lora|768p|video|image|training|upscale|rmbg|comfy|render') { return 'bm-c' }
    if ($t -match 'tts|bgm|music|voice|audio|animatic|480p|speech|whisper|allin1') { return 'bm-b' }
    if ($t -match 'whisper|anchor|assemble|json|embed|ledger|board|script|review|hub|hq') { return 'bm-a' }
    return 'unknown'
}

function Is-GpuCard([string]$text) {
    return ($text.ToLower() -match 'kf|i2v|lora|768p|comfy|render|upscale|training|gpu')
}

# ---- load pool ----
$pool = @()
if (Test-Path $poolF) {
    try {
        $raw = Get-Content $poolF -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($raw -is [array]) { $pool = $raw } else { $pool = @($raw) }
    } catch { $pool = @() }
}
$statusById = @{}
foreach ($c in $pool) { $statusById[[string]$c.id] = [string]$c.status }

# ---- per-card pass: route / open / executable ----
$open = @{}; $exec = @{}; $blocked = @{}
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) { $open[$lane] = 0; $exec[$lane] = 0; $blocked[$lane] = 0 }
$needJudge = @(); $chase = @(); $blockedDetail = @()
$hh = [int](Get-Date -Format 'HH')
$isWeekend = ((Get-Date).DayOfWeek -eq [DayOfWeek]::Saturday) -or ((Get-Date).DayOfWeek -eq [DayOfWeek]::Sunday)
$workWindow = ((-not $isWeekend) -and ($hh -ge 9) -and ($hh -lt 19))

foreach ($c in $pool) {
    $st = [string]$c.status
    if ($st -eq 'assigned') {
        $ca = [string]$c.claimed_at
        if ($ca) { try { if (((Get-Date) - [datetime]::Parse($ca)).TotalHours -gt 24) { $chase += ('{0} assigned>24h no closure' -f $c.id) } } catch { } }
        continue
    }
    if ($st -ne 'open') { continue }

    $lane = [string]$c.lane
    if ($lane -eq 'any' -or $lane -eq '') {
        $lane = Route-Lane (([string]$c.title) + ' ' + ([string]$c.spec))
        if ($lane -eq 'unknown') { $needJudge += ('- [{0}] {1} : untagged card -> needs L2 lane ruling' -f $stamp, $c.id); continue }
    }
    if (-not $open.ContainsKey($lane)) { $lane = 'bm-a' }
    $open[$lane] = $open[$lane] + 1

    $why = ''
    $deps = @($c.depends_on)
    foreach ($d in $deps) {
        if ($d -and $statusById.ContainsKey([string]$d) -and $statusById[[string]$d] -notin @('done', 'closed-superseded', 'closed-stale')) { $why = 'dep:' + $d; break }
    }
    if (-not $why -and $c.blocked_by) { $b = @($c.blocked_by | Where-Object { $_ }); if ($b.Count -gt 0) { $why = 'blocked_by:' + ($b -join ',') } }
    if (-not $why -and $c.deadline) { try { if ([datetime]::Parse([string]$c.deadline) -lt (Get-Date)) { $why = 'deadline-expired' } } catch { } }
    if (-not $why -and $lane -eq 'bm-a' -and $workWindow -and (Is-GpuCard (([string]$c.title) + ' ' + ([string]$c.spec)))) { $why = 'bm-a-workhour-gpu-yield' }

    if ($why) { $blocked[$lane] = $blocked[$lane] + 1; $blockedDetail += ('{0}[{1}]' -f $c.id, $why) }
    else { $exec[$lane] = $exec[$lane] + 1 }
}

# ---- production queue supply (the actual work source) ----
$qOpen = 0; $qRun = 0; $qTotal = 0
if (Test-Path $queueF) {
    foreach ($line in @(Get-Content $queueF -Encoding UTF8 | Where-Object { $_ -match '\S' })) {
        try { $r = $line | ConvertFrom-Json; $qTotal = $qTotal + 1; if ($r.state -eq 'OPEN') { $qOpen = $qOpen + 1 } elseif ($r.state -eq 'RUNNING') { $qRun = $qRun + 1 } } catch { }
    }
}
$lastClaim = ''
if (Test-Path $claimF) {
    try { $lc = Get-Content $claimF -Raw -Encoding UTF8 | ConvertFrom-Json; $lastClaim = [string]$lc.state + '@' + [string]$lc.ts } catch { }
}

# ---- idle verdicts (idle-watch state.json) ----
$verdicts = @{}
if (Test-Path $idleF) {
    try { $is = Get-Content $idleF -Raw -Encoding UTF8 | ConvertFrom-Json; foreach ($id in @('bm-a', 'bm-b', 'bm-c')) { $p = $is.verdicts.PSObject.Properties[$id]; if ($p) { $verdicts[$id] = [string]$p.Value } } } catch { }
}

# ---- capacity: a card is not dispatchable on a RAM/offline-blocked lane ----
$capacity = @{}
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) {
    if ($verdicts[$lane] -in @('BLOCKED-RAM', 'OFFLINE', 'SVC_DOWN', 'HB-STALE')) { $capacity[$lane] = 0 }
    else { $capacity[$lane] = $exec[$lane] }
}

# ---- clock alignment (fleet-clock report writes CLOCK-SKEW.json every 5m) ----
$clockOld = 0; $clockSkew = 0.0; $clockMissing = 0; $clockHigh = 0; $clockPrec = 0.0
if (Test-Path $clockF) {
    try {
        $ck = Get-Content $clockF -Raw -Encoding UTF8 | ConvertFrom-Json
        $clockOld = [int]$ck.old_schema
        $clockSkew = [double]$ck.max_abs_offset_ms
        $clockMissing = [int]$ck.missing
        if ($ck.nodes) {
            $clockHigh = @($ck.nodes | Where-Object { $_.status -eq 'SKEW-HIGH' }).Count
            $pm = @($ck.nodes | Where-Object { $null -ne $_.precision_ms } | ForEach-Object { [double]$_.precision_ms })
            if ($pm.Count -gt 0) { $clockPrec = ($pm | Measure-Object -Maximum).Maximum }
        }
    } catch { }
}
if ($clockOld -gt 0 -or $clockMissing -gt 0) {
    $out += ('[{0}] FLAG CLOCK-UNALIGNED old_schema={1} missing={2} -> P1 upgrade node heartbeat to v2 (ms ts+offset)' -f $stamp, $clockOld, $clockMissing)
} elseif ($clockHigh -gt 0) {
    # Precision-aware: a 300ms offset on a relay path with +/-200ms precision is physics,
    # not a defect. Only the report's SKEW-HIGH verdict (beyond 2*precision+20) is a P1.
    $out += ('[{0}] FLAG CLOCK-SKEW max={1}ms precision=+/-{2}ms -> check hub path or node clock' -f $stamp, $clockSkew, $clockPrec)
}

# ---- flags ----
$idleBad = @('OFFLINE', 'SVC_DOWN', 'HB-STALE', 'GPU-IDLE', 'GPU-IDLE-WORK', 'BLOCKED-RAM')
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) {
    if ($verdicts[$lane] -eq 'OFFLINE' -or $verdicts[$lane] -eq 'SVC_DOWN' -or $verdicts[$lane] -eq 'HB-STALE') {
        $out += ('[{0}] FLAG LANE-DOWN lane={1} verdict={2} -> P1 page lane owner' -f $stamp, $lane, $verdicts[$lane])
    } elseif ($verdicts[$lane] -eq 'BLOCKED-RAM') {
        $out += ('[{0}] FLAG BLOCKED-RAM lane={1} -> P1 free memory before assigning' -f $stamp, $lane)
    }
    if (($verdicts[$lane] -in @('GPU-IDLE', 'GPU-IDLE-WORK')) -and ($exec[$lane] -gt 0)) {
        $out += ('[{0}] FLAG IDLE-WITH-WORK lane={1} exec_cards={2} -> P1 claim now (work exists, machine idle)' -f $stamp, $lane, $exec[$lane])
    }
    if (($exec[$lane] -gt 0) -and ($capacity[$lane] -eq 0)) {
        $out += ('[{0}] FLAG CAPACITY-BLOCKED lane={1} exec_cards={2} dispatchable=0 -> P1 free capacity or reroute' -f $stamp, $lane, $exec[$lane])
    }
    if ($exec[$lane] -eq 0) {
        $out += ('[{0}] FLAG STARVED-EXEC lane={1} open_cards={2} blocked={3} -> P1 supply failure: no executable card' -f $stamp, $lane, $open[$lane], $blocked[$lane])
    }
}
if ($qOpen -eq 0) {
    $out += ('[{0}] FLAG SUPPLY-DRY production_queue_open=0 total={1} last_claim={2} -> P1 refill from real backlog' -f $stamp, $qTotal, $lastClaim)
}
foreach ($ch in $chase) { $out += ('[{0}] FLAG CHASE {1} -> poke owner + escalate' -f $stamp, $ch) }
foreach ($bd in $blockedDetail) { $needJudge += ('- {0} blocked: {1}' -f $bd, $stamp) }

$allGreen = $true
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) { if ($exec[$lane] -le 0) { $allGreen = $false } }
if ($qOpen -le 0) { $allGreen = $false }
if ($out.Count -gt 0) { $allGreen = $false }
if ($allGreen) {
    $out += ('[{0}] OK supply: bm-a={1} bm-b={2} bm-c={3} exec; queue_open={4}; lanes busy' -f $stamp, $exec['bm-a'], $exec['bm-b'], $exec['bm-c'], $qOpen)
} else {
    $out += ('[{0}] pools: bm-a={1}open/{2}exec bm-b={3}open/{4}exec bm-c={5}open/{6}exec; queue_open={7} run={8}; idle: a={9} b={10} c={11}; flags={12}' -f `
        $stamp, $open['bm-a'], $exec['bm-a'], $open['bm-b'], $exec['bm-b'], $open['bm-c'], $exec['bm-c'], $qOpen, $qRun, $verdicts['bm-a'], $verdicts['bm-b'], $verdicts['bm-c'], $out.Count)
}

# ---- machine-readable state for idle-watch / rounds / dashboards ----
$state = [ordered]@{
    ts = (Get-Date).ToString('s')
    work_window = $workWindow
    lanes = [ordered]@{
        'bm-a' = [ordered]@{ open = $open['bm-a']; exec = $exec['bm-a']; blocked = $blocked['bm-a']; dispatchable = $capacity['bm-a']; idle = $verdicts['bm-a'] }
        'bm-b' = [ordered]@{ open = $open['bm-b']; exec = $exec['bm-b']; blocked = $blocked['bm-b']; dispatchable = $capacity['bm-b']; idle = $verdicts['bm-b'] }
        'bm-c' = [ordered]@{ open = $open['bm-c']; exec = $exec['bm-c']; blocked = $blocked['bm-c']; dispatchable = $capacity['bm-c']; idle = $verdicts['bm-c'] }
    }
    queue = [ordered]@{ total = $qTotal; open = $qOpen; running = $qRun; last_claim = $lastClaim }
    flags = $out.Count
}
$state | ConvertTo-Json -Depth 6 | Set-Content -Path $stateF -Encoding UTF8

# ---- NEED-JUDGMENT snapshot ----
$jhead = @('# NEED-JUDGMENT - current snapshot (regenerated by L0 every round; L2 resolves then edits POOL.json)')
$jhead += $needJudge
if ($needJudge.Count -eq 0) { $jhead += '- none' }
Set-Content -Path $judgF -Value $jhead -Encoding UTF8

# ---- append + prune log ----
$existing = @()
if (Test-Path $logF) { $existing = @(Get-Content $logF -Encoding UTF8) }
$all = $existing + $out
if ($all.Count -gt 400) { $all = $all[-400..-1] }
Set-Content -Path $logF -Value $all -Encoding UTF8
Write-Output ($out -join "`n")