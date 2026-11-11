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
$ceoWaits = @{}; $execRef = @{}; $execCmd = @{}; $busy = @{}
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) {
    $open[$lane] = 0; $exec[$lane] = 0; $blocked[$lane] = 0
    $ceoWaits[$lane] = 0; $execRef[$lane] = @(); $execCmd[$lane] = 0
}
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

    if ($why) {
        $blocked[$lane] = $blocked[$lane] + 1; $blockedDetail += ('{0}[{1}]' -f $c.id, $why)
        # A card held by a CEO physical item is not a supply failure - it is a legitimate
        # wait (zero-chase law). Counted apart so the flag can say WAITING-CEO, not STARVED.
        if ($why -match 'CEO-PHYSICAL') { $ceoWaits[$lane] = $ceoWaits[$lane] + 1 }
    }
    else {
        $exec[$lane] = $exec[$lane] + 1
        if ($c.cmd) { $execCmd[$lane] = $execCmd[$lane] + 1 }
        $jr = [string]$c.job_ref
        if (-not $jr) { $jr = [string]$c.job_id }
        if ($jr) { $execRef[$lane] = @($execRef[$lane]) + $jr }
    }
}

# ---- production queue supply (the actual work source) ----
$qOpen = 0; $qRun = 0; $qTotal = 0
$runLane = @{}; $qState = @{}
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) { $runLane[$lane] = 0 }
if (Test-Path $queueF) {
    foreach ($line in @(Get-Content $queueF -Encoding UTF8 | Where-Object { $_ -match '\S' })) {
        try {
            $r = $line | ConvertFrom-Json; $qTotal = $qTotal + 1
            $qState[[string]$r.id] = [string]$r.state
            if ($r.state -eq 'OPEN') { $qOpen = $qOpen + 1 }
            elseif ($r.state -eq 'RUNNING') {
                $qRun = $qRun + 1
                # A lane with a RUNNING job of its own is busy with declared work. Before
                # 2026-11-07 the flag ignored this and called every such lane STARVED.
                $o = [string]$r.owner
                if ($runLane.ContainsKey($o)) { $runLane[$o] = $runLane[$o] + 1 }
            }
        } catch { }
    }
}
# ---- lane-file work (the master's own assignment face) ----
# queue RUNNING is not the only way a lane is busy: the master assigns through
# cph4/fleet/lanes/<node>.json and lane_agent runs it without touching the shared queue.
# Counting only queue rows made an assigned-and-running lane look starved (2026-11-07).
# A lane file older than 30 minutes is stale and is NOT evidence of work.
$laneJobs = @{}
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) {
    $laneJobs[$lane] = 0
    $lf = Join-Path $root ('cph4\fleet\lanes\' + $lane + '.json')
    if (Test-Path $lf) {
        try {
            $lj = Get-Content $lf -Raw -Encoding UTF8 | ConvertFrom-Json
            $fresh = $true
            if ($lj.ts) { try { $fresh = (((Get-Date) - [datetime]$lj.ts).TotalMinutes -lt 30) } catch { } }
            if ($fresh) { $laneJobs[$lane] = @($lj.jobs).Count }
        } catch { }
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
    # 同一缺口不许报两遍（2026-11-12 事件班）：整机离线（LANE-DOWN）时缺心跳是必然结果，
    # 不是时钟缺陷。旧实现把它算进 missing，于是 bm-b 物理离线期间每 10 分钟刷一条
    # CLOCK-UNALIGNED P1 与 LANE-DOWN 并列，两条红指向同一个断电的盒子，噪音把真红埋掉。
    $clockMissingLive = 0
    if ($ck -and $ck.nodes) {
        foreach ($nd in @($ck.nodes)) {
            if ([string]$nd.status -ne 'MISSING') { continue }
            $nm = [string]$nd.node
            if ($verdicts.ContainsKey($nm) -and ($verdicts[$nm] -in @('OFFLINE', 'SVC_DOWN', 'HB-STALE'))) { continue }
            $clockMissingLive = $clockMissingLive + 1
        }
    } else {
        $clockMissingLive = $clockMissing
    }
    if ($clockOld -gt 0 -or $clockMissingLive -gt 0) {
        $out += ('[{0}] FLAG CLOCK-UNALIGNED old_schema={1} missing={2} -> P1 upgrade node heartbeat to v2 (ms ts+offset)' -f $stamp, $clockOld, $clockMissingLive)
    } elseif ($clockMissing -gt 0) {
        $out += ('[{0}] INFO CLOCK-MISSING-DERIVED missing={1} all-on-down-lanes -> no action (LANE-DOWN already carries it)' -f $stamp, $clockMissing)
    }
} elseif ($clockHigh -gt 0) {
    # Precision-aware: a 300ms offset on a relay path with +/-200ms precision is physics,
    # not a defect. Only the report's SKEW-HIGH verdict (beyond 2*precision+20) is a P1.
    $out += ('[{0}] FLAG CLOCK-SKEW max={1}ms precision=+/-{2}ms -> check hub path or node clock' -f $stamp, $clockSkew, $clockPrec)
}

# ---- flags ----
# 2026-11-07 event round: five P1s repeated every 10 minutes for hours while the fleet was
# demonstrably working. Three of them were the flag's own defects, not the fleet's:
#   * STARVED-EXEC fired on a lane whose only open card was held by CEO-PHYSICAL, and on a
#     lane that was at that moment RUNNING a declared job (owner+lane match).
#   * IDLE-WITH-WORK used the GPU verdict on bm-b, whose lane is cpu-sound - a CPU job on a
#     GPU-idle box is normal, not an idle machine.
#   * A POOL card can be OPEN with a job_ref pointing at a FAILED/nonexistent job: it then
#     counts as "executable work" forever while nothing can run. That is phantom supply.
$idleBad = @('OFFLINE', 'SVC_DOWN', 'HB-STALE', 'GPU-IDLE', 'GPU-IDLE-WORK', 'BLOCKED-RAM')
$gpuVerdictLanes = @('bm-a', 'bm-c')   # bm-b is cpu-sound: its GPU idleness says nothing
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) {
    if ($verdicts[$lane] -eq 'OFFLINE' -or $verdicts[$lane] -eq 'SVC_DOWN' -or $verdicts[$lane] -eq 'HB-STALE') {
        $out += ('[{0}] FLAG LANE-DOWN lane={1} verdict={2} -> P1 page lane owner' -f $stamp, $lane, $verdicts[$lane])
    } elseif ($verdicts[$lane] -eq 'BLOCKED-RAM') {
        $out += ('[{0}] FLAG BLOCKED-RAM lane={1} -> P1 free memory before assigning' -f $stamp, $lane)
    }
    # phantom supply: cards count as executable but none has a leg that can actually run
    $liveRefs = 0
    foreach ($jr in @($execRef[$lane])) {
        if ($jr -and $qState.ContainsKey($jr) -and $qState[$jr] -in @('OPEN', 'RUNNING')) { $liveRefs = $liveRefs + 1 }
    }
    if (($exec[$lane] -gt 0) -and ($execCmd[$lane] -eq 0) -and ($liveRefs -eq 0)) {
        $out += ('[{0}] FLAG POOL-PHANTOM lane={1} exec_cards={2} live_legs=0 -> P1 card has no runnable job_ref (materialize a queue job or close it)' -f $stamp, $lane, $exec[$lane])
    }
    $busy[$lane] = $runLane[$lane] + $laneJobs[$lane]
    if (($verdicts[$lane] -in @('GPU-IDLE', 'GPU-IDLE-WORK')) -and ($exec[$lane] -gt 0) -and ($busy[$lane] -eq 0) -and ($gpuVerdictLanes -contains $lane)) {
        $out += ('[{0}] FLAG IDLE-WITH-WORK lane={1} exec_cards={2} -> P1 claim now (work exists, machine idle)' -f $stamp, $lane, $exec[$lane])
    }
    if (($exec[$lane] -gt 0) -and ($capacity[$lane] -eq 0)) {
        $out += ('[{0}] FLAG CAPACITY-BLOCKED lane={1} exec_cards={2} dispatchable=0 -> P1 free capacity or reroute' -f $stamp, $lane, $exec[$lane])
    }
    if ($exec[$lane] -eq 0) {
        if ($busy[$lane] -gt 0) {
            # busy on declared work: no flag, the pools line already shows running=N
        } elseif (($open[$lane] -gt 0) -and ($ceoWaits[$lane] -eq $open[$lane])) {
            $out += ('[{0}] INFO WAITING-CEO lane={1} open={2} all CEO-physical -> registered, zero chase' -f $stamp, $lane, $open[$lane])
        } else {
            $out += ('[{0}] FLAG STARVED-EXEC lane={1} open_cards={2} blocked={3} running={4} -> P1 supply failure: no executable card' -f $stamp, $lane, $open[$lane], $blocked[$lane], $busy[$lane])
        }
    }
}
if ($qOpen -eq 0) {
    $out += ('[{0}] FLAG SUPPLY-DRY production_queue_open=0 total={1} last_claim={2} -> P1 refill from real backlog' -f $stamp, $qTotal, $lastClaim)
}
foreach ($ch in $chase) { $out += ('[{0}] FLAG CHASE {1} -> poke owner + escalate' -f $stamp, $ch) }
foreach ($bd in $blockedDetail) { $needJudge += ('- {0} blocked: {1}' -f $bd, $stamp) }

$flagN = @($out | Where-Object { $_ -match '\] FLAG ' }).Count
$allGreen = $true
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) { if (($exec[$lane] -le 0) -and ($busy[$lane] -le 0)) { $allGreen = $false } }
if ($qOpen -le 0) { $allGreen = $false }
if ($flagN -gt 0) { $allGreen = $false }
if ($allGreen) {
    $out += ('[{0}] OK supply: bm-a={1} bm-b={2} bm-c={3} exec; queue_open={4}; lanes busy' -f $stamp, $exec['bm-a'], $exec['bm-b'], $exec['bm-c'], $qOpen)
} else {
    $out += ('[{0}] pools: bm-a={1}open/{2}exec/{3}run bm-b={4}open/{5}exec/{6}run bm-c={7}open/{8}exec/{9}run; queue_open={10} run={11} lanejobs: a={16} b={17} c={18}; idle: a={12} b={13} c={14}; flags={15}' -f `
        $stamp, $open['bm-a'], $exec['bm-a'], $runLane['bm-a'], $open['bm-b'], $exec['bm-b'], $runLane['bm-b'], $open['bm-c'], $exec['bm-c'], $runLane['bm-c'], $qOpen, $qRun, $verdicts['bm-a'], $verdicts['bm-b'], $verdicts['bm-c'], $flagN, $laneJobs['bm-a'], $laneJobs['bm-b'], $laneJobs['bm-c'])
}

# ---- machine-readable state for idle-watch / rounds / dashboards ----
$state = [ordered]@{
    ts = (Get-Date).ToString('s')
    work_window = $workWindow
    lanes = [ordered]@{
        'bm-a' = [ordered]@{ open = $open['bm-a']; exec = $exec['bm-a']; blocked = $blocked['bm-a']; ceo_wait = $ceoWaits['bm-a']; running = $runLane['bm-a']; lane_jobs = $laneJobs['bm-a']; dispatchable = $capacity['bm-a']; idle = $verdicts['bm-a'] }
        'bm-b' = [ordered]@{ open = $open['bm-b']; exec = $exec['bm-b']; blocked = $blocked['bm-b']; ceo_wait = $ceoWaits['bm-b']; running = $runLane['bm-b']; lane_jobs = $laneJobs['bm-b']; dispatchable = $capacity['bm-b']; idle = $verdicts['bm-b'] }
        'bm-c' = [ordered]@{ open = $open['bm-c']; exec = $exec['bm-c']; blocked = $blocked['bm-c']; ceo_wait = $ceoWaits['bm-c']; running = $runLane['bm-c']; lane_jobs = $laneJobs['bm-c']; dispatchable = $capacity['bm-c']; idle = $verdicts['bm-c'] }
    }
    queue = [ordered]@{ total = $qTotal; open = $qOpen; running = $qRun; last_claim = $lastClaim }
    flags = $flagN
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