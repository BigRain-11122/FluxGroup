# fleet-idle-watch.ps1 - HQ-FleetIdleWatch v3 (CEO order O-20261012-1505 anti-idle + role-map O-20261012-2215 / C-20261012-03 per-lane verdicts;
# v3 2026-10-18 auto-revive, bm-a fleet-ops seat, CEO order "solve it at the root")
# Runs every 15 min via task-register.ps1 (silent chain). Probes fleet machines, logs verdicts,
# escalates on repeated idle/unreachable. bm-a work-hour idle is EXPECTED (CEO use-machine law).
# Log: .codely-cli/tmp/fleet-idle-watch/watch.log (auto-pruned to 400 lines)
#
# v3 CHANGE (root-cure companion to fleet-poke-worker v1.10/v1.11 and
# iteration_loop.ps1 v2): the watcher no longer only LOGS - it is the
# standing AUTOMATIC RESPONDER. When a machine's listener is up but its
# lane heartbeat is frozen (BM lane >120 min via true origin blob read
# after a read-only fetch; MiniGame lane >240 min via local copy) or an
# IDLE verdict streaks >=3, the watcher sends that node a poke with
# tasks=[its roster wake_tasks]. The node's own worker then applies the
# EVIDENCE-GATED revival (Running+stale -> HUNG-RESTART, Ready -> WAKE),
# so a closed window or a killed session self-heals in <=15-30 min with
# zero human/bm-a-seat action. Rate-limited: one revive poke per machine
# per 30 min. Listener-down (SVC_DOWN) / OFFLINE can not be poked -
# logged only (the node's own FluxGroup-FleetLink keepalive heals its
# listener). Evidence-gated, fail-safe: any probe failure = no poke.
$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$logDir = Join-Path $root '.codely-cli\tmp\fleet-idle-watch'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$log = Join-Path $logDir 'watch.log'
$state = Join-Path $logDir 'state.json'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
$out = @()

# ---- v3: roster (wake_tasks + port) for auto-revive pokes ----
$wake = @{}
$port = 8790
try {
    $roster = Get-Content -Raw (Join-Path $root 'Tools\fleet-nodes.json') | ConvertFrom-Json
    if ($roster.PSObject.Properties.Name -contains 'port') { $port = [int]$roster.port }
    foreach ($n in @($roster.nodes)) { $wake[([string]$n.id)] = @($n.wake_tasks) | ForEach-Object { [string]$_ } }
} catch { }

# ---- reachability (tailscale status text) ----
$ts = (& tailscale status) -join "`n"
function TsOnline([string]$ip) {
    if ($ts -match [regex]::Escape($ip)) {
        if ($ts -match ('(?m)^\s*' + [regex]::Escape($ip) + '.*offline')) { return 'offline' }
        return 'online'
    }
    return 'unknown'
}

# ---- HTTP probe helper ----
function Probe([string]$url) {
    try {
        $r = Invoke-WebRequest -Uri $url -TimeoutSec 4 -UseBasicParsing
        return @{ ok = $true; body = $r.Content }
    } catch {
        return @{ ok = $false; body = '' }
    }
}

# ---- heartbeat age from local synced copy ----
function HbAge([string]$file) {
    if (-not (Test-Path $file)) { return -1 }
    try {
        $j = Get-Content $file -Raw | ConvertFrom-Json
        $tsf = $null
        foreach ($k in @('ts','clock_read','last_seen')) {
            $p = $j.PSObject.Properties[$k]
            if ($p -and $p.Value) { $tsf = $p.Value; break }
        }
        if (-not $tsf) { return -2 }
        $t = [datetime]::Parse($tsf)
        if ($t -is [datetime]) { return [int]((Get-Date) - $t).TotalMinutes }
        return -3
    } catch { return -4 }
}

# ---- v3: BM-lane heartbeat age from TRUE origin blob (read-only fetch + show;
# falls back to the local synced copy on fetch failure - local copy lags by
# pull cadence, origin read has no lag). judge-from-remote-truth law applied. ----
$gitExe = 'C:\Program Files\Git\cmd\git.exe'
$bmRepo = Join-Path $root 'quant\bigmoney'
function BmHbAge([string]$id) {
    if (Test-Path $bmRepo) {
        try {
            $null = & $gitExe -C $bmRepo fetch origin 2>&1
            $blobLines = & $gitExe -C $bmRepo show ('origin/main:fleet/machines/' + $id + '.json') 2>&1
            $txt = [string]::Join("`n", @($blobLines))
            $m = [regex]::Match($txt, '"last_seen"\s*:\s*"([^"]+)"')
            if (-not $m.Success) { $m = [regex]::Match($txt, '"clock_read"\s*:\s*"([^"]+)"') }
            if ($m.Success) {
                $t = [datetime]::Parse($m.Groups[1].Value)
                return [int]((Get-Date) - $t).TotalMinutes
            }
        } catch { }
    }
    return (HbAge (Join-Path $bmRepo ('fleet\machines\' + $id + '.json')))
}

$machines = @(
    @{ id = 'bm-b'; ip = '100.82.175.0'; lane = 'cpu-sound'; hb = Join-Path $root 'gaming\MiniGame\Design\configs\GLOBAL\fleet\b.json' },
    @{ id = 'bm-c'; ip = '100.123.74.104'; lane = 'gpu-production'; hb = Join-Path $root 'gaming\MiniGame\Design\configs\GLOBAL\fleet\c.json' }
)

$verdicts = @{}
$hbAges = @{}
$bmAges = @{}
$lstOk = @{}
foreach ($m in $machines) {
    $net = TsOnline $m.ip
    $lst = Probe ("http://{0}:8790/status" -f $m.ip)
    $q = Probe ("http://{0}:8188/queue" -f $m.ip)
    $qr = 0; $qp = 0; $vramUsed = -1
    if ($q.ok) {
        try {
            $qj = $q.body | ConvertFrom-Json
            $rp = $qj.PSObject.Properties['queue_running']
            if ($rp) { $qr = @($rp.Value).Count }
            $pp = $qj.PSObject.Properties['queue_pending']
            if ($pp) { $qp = @($pp.Value).Count }
        } catch { $qr = -1 }
        try {
            $sj = (Probe ("http://{0}:8188/system_stats" -f $m.ip)).body | ConvertFrom-Json
            $dev = $sj.devices | Select-Object -First 1
            if ($dev) { $vramUsed = [int]($dev.vram_total - $dev.vram_free) }
        } catch { }
    }
    $hbAge = HbAge $m.hb
    $bmAge = BmHbAge $m.id
    $hbAges[$m.id] = $hbAge
    $bmAges[$m.id] = $bmAge
    $lstOk[$m.id] = [bool]$lst.ok
    $busy = $false
    if ($q.ok -and (($qr -gt 0) -or ($qp -gt 0))) { $busy = $true }
    if ($vramUsed -gt 2000) { $busy = $true }
    # v2 role-aware verdicts (O-20261012-2215 / C-20261012-03): lanes differ.
    # bm-b = cpu-sound lane: no ComfyUI by design -> 8188 probe failing is expected.
    # bm-c = gpu-production lane: ComfyUI binds 127.0.0.1 -> remote probe structurally
    # fails; GPU idleness is judged on-machine (lane duty: loop reports GPU into heartbeat).
    # Liveness = FleetLink listener OR fresh heartbeat (<=60m). Streak escalation counts
    # only OFFLINE / SVC_DOWN / IDLE.
    $alive = ($lst.ok) -or (($hbAge -ge 0) -and ($hbAge -le 60)) -or (($bmAge -ge 0) -and ($bmAge -le 60))
    if ($net -eq 'offline') { $v = 'OFFLINE' }
    elseif (-not $alive) { $v = 'SVC_DOWN' }
    elseif ($m.lane -eq 'gpu-production') {
        if ($q.ok) { if ($busy) { $v = 'BUSY' } else { $v = 'IDLE' } }
        else { $v = 'ALIVE-LOCAL-COMFY' }
    }
    else { $v = 'ALIVE-CPU-LANE' }
    $hbNote = ''
    if ($hbAge -gt 240) { $hbNote = ' **HB-STALE**' }
    $bmNote = ''
    if ($bmAge -gt 120) { $bmNote = ' **BM-HB-STALE**' }
    $verdicts[$m.id] = $v
    $out += ("[{0}] {1} verdict={2} net={3} listener={4} comfy_queue=run:{5}/pend:{6} vram_used={7} hb_age={8}m bm_hb_age={9}m{10}{11}" -f $stamp, $m.id, $v, $net, $(if ($lst.ok) { 'up' } else { 'down' }), $qr, $qp, $vramUsed, $hbAge, $bmAge, $hbNote, $bmNote)
}

# ---- bm-a self line (work-hour idle = EXPECTED per CEO law) ----
$bmAwindow = 'work-hours-expected-idle'
$hh = [int](Get-Date -Format 'HH')
$isWeekend = ((Get-Date).DayOfWeek -eq [DayOfWeek] 'Saturday') -or ((Get-Date).DayOfWeek -eq [DayOfWeek] 'Sunday')
if ($isWeekend -or ($hh -lt 8)) { $bmAwindow = 'job-window' }
$aUtil = ''
try { $aUtil = (& nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader) } catch { }
$out += ("[{0}] bm-a window={1} (CEO-rule: weekday work hours = no jobs) gpu={2}" -f $stamp, $bmAwindow, $aUtil)

# ---- escalation: streak counting per machine + v3 auto-revive ----
$st = [pscustomobject]@{}
if (Test-Path $state) {
    try { $st = Get-Content $state -Raw | ConvertFrom-Json } catch { $st = [pscustomobject]@{} }
}
if (-not $st) { $st = [pscustomobject]@{} }
$warns = @()
$now = Get-Date
foreach ($m in $machines) {
    $v = $verdicts[$m.id]
    $prev = 0
    if ($st.PSObject.Properties[$m.id]) { $prev = [int]$st.PSObject.Properties[$m.id].Value }
    if (($v -eq 'IDLE') -or ($v -eq 'SVC_DOWN') -or ($v -eq 'OFFLINE')) { $prev = $prev + 1 } else { $prev = 0 }
    $st | Add-Member -NotePropertyName $m.id -NotePropertyValue $prev -Force
    if ($prev -ge 3) { $warns += ("{0} streak={1} verdict={2}" -f $m.id, $prev, $v) }

    # ---- v3 auto-revive (CEO "solve it at the root" 2026-10-18): evidence-gated,
    # rate-limited (>=30 min per machine). Only when the listener answers - the
    # node's own worker applies the revival gates (v1.10/v1.11 run-age guard).
    $rvKey = 'revive_' + $m.id
    $lastRv = [datetime]::MinValue
    if ($st.PSObject.Properties[$rvKey] -and $st.PSObject.Properties[$rvKey].Value) {
        try { $lastRv = [datetime]$st.PSObject.Properties[$rvKey].Value } catch { }
    }
    $staleBm = ([int]$bmAges[$m.id] -gt 120)
    $staleMg = ([int]$hbAges[$m.id] -gt 240)
    $idleStreak = ($prev -ge 3) -and ($v -eq 'IDLE')
    $needRevive = ([bool]$lstOk[$m.id]) -and ($staleBm -or $staleMg -or $idleStreak) -and ($wake[$m.id]) -and (($now - $lastRv).TotalMinutes -ge 30)
    if ($needRevive) {
        $body = @{ reason = ('idlewatch-auto-revive ' + $stamp); tasks = @($wake[$m.id]); repos = @('.') } | ConvertTo-Json -Compress
        try {
            $null = Invoke-RestMethod -Uri ('http://{0}:{1}/poke' -f $m.ip, $port) -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 20
            $st | Add-Member -NotePropertyName $rvKey -NotePropertyValue ($now.ToString('s')) -Force
            $out += ("[{0}] AUTO-REVIVE {1}: poke SENT tasks={2} (bm_hb={3}m mg_hb={4}m verdict={5} streak={6}) - node worker applies v1.10/v1.11 evidence gates" -f $stamp, $m.id, @($wake[$m.id]).Count, $bmAges[$m.id], $hbAges[$m.id], $v, $prev)
        } catch {
            $out += ("[{0}] AUTO-REVIVE {1}: poke FAILED {2}" -f $stamp, $m.id, [string]$_.Exception.Message)
        }
    }
}
$st | ConvertTo-Json | Set-Content -Path $state -Encoding UTF8
if ($warns.Count -gt 0) {
    $out += ("[{0}] **WARN** idle/unreachable >=3 consecutive checks: {1} -> escalated to AUTO-REVIVE (v3) + duty-window report" -f $stamp, ($warns -join '; '))
}

# ---- write + prune ----
$existing = @()
if (Test-Path $log) { $existing = Get-Content $log }
$all = $existing + $out
if ($all.Count -gt 400) { $all = $all[-400..-1] }
Set-Content -Path $log -Value $all -Encoding UTF8
Write-Output ($out -join "`n")
