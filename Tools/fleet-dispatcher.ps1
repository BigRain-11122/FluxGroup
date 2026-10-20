# fleet-dispatcher.ps1 - HQ-FleetDispatcher L0 deterministic round
# CEO order O-20261012-2225 / charter: cph4/fleet/dispatcher/DISPATCHER-CHARTER.md
# Layer 0: rules + probes + flags ONLY. Never touches git (L2 owns ledger writes).
# Runs via task-register.ps1 silent chain every 30m + on demand from judgment rounds.
param([string]$PoolPath = '', [switch]$NoWrite)

$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$dir = Join-Path $root 'cph4\fleet\dispatcher'
$poolF = Join-Path $dir 'POOL.json'
if ($PoolPath) { $poolF = $PoolPath }
$logF = Join-Path $dir 'DISPATCH-LOG.md'
$judgF = Join-Path $dir 'NEED-JUDGMENT.md'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
$out = @()

# ---- T0 cloud-off hard gate (CHARTER SS5.6 / CLOUD-OFF-LOCAL-ONLY-v1) ----
# Cards naming a cloud generation/LLM provider are blocked unless they carry a
# cloud_exception field citing the CEO order that authorised it.
# Local-only equivalents (INT8, on-prem, llama.cpp) are not in this list.
$cloudRe = 'seedance|doubao|volcengine|volc-ark|ark\.cn|h3\s*api|h3-api|tripo|rodin|hunyuan|minimax|hailuo|kling|runway|pika|luma|tjgenerators|ai-generator\.tuanjie\.cn|elevenlabs|suno|speech-02|gpt-[3-5]|claude|gemini|anthropic|openai\s*api'
$cloudOff = @()

# ---- lane keyword router (fallback for 'any'/untagged cards) ----
function Route-Lane([string]$text) {
    $t = $text.ToLower()
    if ($t -match 'kf|i2v|lora|768p|video|image|training|upscale|rmbg|comfy|render') { return 'bm-c' }
    if ($t -match 'tts|bgm|music|voice|audio|animatic|480p|speech') { return 'bm-b' }
    if ($t -match 'whisper|anchor|assemble|json|embed|ledger|board|script|review|hub|hq') { return 'bm-a' }
    return 'unknown'
}

# ---- load pool (PS5.1: pipeline-wrapped ConvertFrom-Json collapses arrays - assign first, then type-check) ----
$pool = @()
if (Test-Path $poolF) {
    try {
        $raw = Get-Content $poolF -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($raw -is [array]) { $pool = $raw } else { $pool = @($raw) }
    } catch { $pool = @() }
}

# ---- per-card pass: route + starvation count + overdue chase ----
$open = @{}
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) { $open[$lane] = 0 }
$needJudge = @()
$chase = @()
foreach ($c in $pool) {
    $st = [string]$c.status
    # history (closed/superseded) is evidence, not dispatchable: gate only live cards
    if ($st -ne 'open' -and $st -ne 'assigned') { continue }
    $ctext = ([string]$c.id) + ' ' + ([string]$c.title) + ' ' + ([string]$c.spec) + ' ' + ([string]$c.result_ref)
    if (([string]$c.cloud_exception) -eq '' -and $ctext -match $cloudRe) {
        $cloudOff += ('- [{0}] {1} : cloud model reference without cloud_exception -> blocked (T0 CLOUD-OFF)' -f $stamp, $c.id)
        continue
    }
    if ($st -eq 'assigned') {
        $ca = [string]$c.claimed_at
        if ($ca) {
            try {
                $t = [datetime]::Parse($ca)
                if (((Get-Date) - $t).TotalHours -gt 24) { $chase += ('{0} assigned>24h no closure' -f $c.id) }
            } catch { }
        }
        continue
    }
    if ($st -ne 'open') { continue }
    $lane = [string]$c.lane
    if ($lane -eq 'any' -or $lane -eq '') {
        $lane = Route-Lane (([string]$c.title) + ' ' + ([string]$c.spec))
        if ($lane -eq 'unknown') {
            $needJudge += ('- [{0}] {1} : untagged card -> needs L2 lane ruling (bm-a/bm-b/bm-c per resource-chain SS9.1 v2)' -f $stamp, $c.id)
            continue
        }
    }
    if ($open.ContainsKey($lane)) { $open[$lane] = $open[$lane] + 1 }
}

# ---- machine liveness: reuse IdleWatch latest verdicts (no duplicate probes) ----
if ($cloudOff.Count -gt 0) { $needJudge += $cloudOff }
$watch = Join-Path $root '.codely-cli\tmp\fleet-idle-watch\watch.log'
$verdicts = @{}
if (Test-Path $watch) {
    $lines = @(Get-Content $watch -Tail 8 -Encoding UTF8 | Where-Object { $_ -match 'verdict=' })
    foreach ($l in $lines) {
        foreach ($id in @('bm-a', 'bm-b', 'bm-c')) {
            if ($l -match ('\[' + $id + '\].*verdict=(\S+)')) { $verdicts[$id] = $Matches[1] }
        }
    }
}
$down = @()
foreach ($id in @('bm-a', 'bm-b', 'bm-c')) {
    $v = ''
    if ($verdicts.ContainsKey($id)) { $v = $verdicts[$id] }
    if ($v -eq 'OFFLINE' -or $v -eq 'SVC_DOWN') { $down += ('{0}({1})' -f $id, $v) }
}

# ---- flags ----
if ($down.Count -gt 0) { $out += ('[{0}] FLAG LANE-DOWN: {1} -> L2 chase lane-owner machine (highest priority fix per SS9.1)' -f $stamp, ($down -join ', ')) }
foreach ($lane in @('bm-a', 'bm-b', 'bm-c')) {
    if ($open[$lane] -eq 0) { $out += ('[{0}] FLAG STARVED lane={1} open_cards=0 (empty queue) -> L2 replenish from owner backlog (SS9.6)' -f $stamp, $lane) }
    elseif ($open[$lane] -lt 3) { $out += ('[{0}] NOTE QUEUE-LOW lane={1} open_cards={2} (<3) -> replenish only from real backlog, no synthetic cards (O-20260928-1820)' -f $stamp, $lane, $open[$lane]) }
}
foreach ($ch in $chase) { $out += ('[{0}] FLAG CHASE {1} -> L2 poke owner + escalate' -f $stamp, $ch) }
if ($needJudge.Count -eq 0 -and $out.Count -eq 0) {
    $out += ('[{0}] OK pools: bm-a={1}/3 bm-b={2}/3 bm-c={3}/3 open; all lanes live; no judgment due' -f $stamp, $open['bm-a'], $open['bm-b'], $open['bm-c'])
} else {
    $out += ('[{0}] pools: bm-a={1} bm-b={2} bm-c={3} open; judgment_cards={4} flags={5}' -f $stamp, $open['bm-a'], $open['bm-b'], $open['bm-c'], $needJudge.Count, $out.Count)
}

# ---- write NEED-JUDGMENT (fresh snapshot each round) ----
$jhead = @('# NEED-JUDGMENT - current snapshot (regenerated by L0 every round; L2 resolves then edits POOL.json)')
$jhead += $needJudge
if (-not $NoWrite) { Set-Content -Path $judgF -Value $jhead -Encoding UTF8 }

# ---- append + prune log ----
$existing = @()
if (-not $NoWrite -and (Test-Path $logF)) { $existing = @(Get-Content $logF -Encoding UTF8) }
$all = $existing + $out
if ($all.Count -gt 400) { $all = $all[-400..-1] }
if (-not $NoWrite) { Set-Content -Path $logF -Value $all -Encoding UTF8 }
Write-Output ($out -join "`n")
