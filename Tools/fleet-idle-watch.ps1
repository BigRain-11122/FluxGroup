# fleet-idle-watch.ps1 - HQ-FleetIdleWatch v3 (CEO order 2026-10-27: idleness must be visible)
# Fixes v2's structural blind spot: v2 could never return IDLE for bm-b (cpu-sound) or
# bm-c (gpu-production, local ComfyUI), so the fleet could sit at 0% forever while the
# watcher reported ALIVE. v3 judges load from each machine's heartbeat JSON (gpu util,
# vram, ram, comfy/batch flags) and only alarms when the lane also has executable work.
# Log: .codely-cli/tmp/fleet-idle-watch/watch.log   State: ...\state.json
$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$logDir = Join-Path $root '.codely-cli\tmp\fleet-idle-watch'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$log = Join-Path $logDir 'watch.log'
$stateFile = Join-Path $logDir 'state.json'
$dispState = Join-Path $root 'cph4\fleet\dispatcher\STATE.json'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
$out = @()

# ---- executable-card counts published by the dispatcher (single source of truth) ----
$exec = @{ 'bm-a' = -1; 'bm-b' = -1; 'bm-c' = -1 }
if (Test-Path $dispState) {
    try {
        $ds = Get-Content $dispState -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($id in @('bm-a', 'bm-b', 'bm-c')) {
            $p = $ds.lanes.PSObject.Properties[$id]
            if ($p) { $exec[$id] = [int]$p.Value.exec }
        }
    } catch { }
}

function TsOnline([string]$ip) {
    try { $ts = (& tailscale status) -join "`n" } catch { return 'unknown' }
    if ($ts -match [regex]::Escape($ip)) {
        if ($ts -match ('(?m)^\s*' + [regex]::Escape($ip) + '.*offline')) { return 'offline' }
        return 'online'
    }
    return 'unknown'
}

function Probe([string]$url) {
    try { $r = Invoke-WebRequest -Uri $url -TimeoutSec 4 -UseBasicParsing; return @{ ok = $true; body = $r.Content } }
    catch { return @{ ok = $false; body = '' } }
}

# ---- heartbeat: age + load fields ----
function Read-Hb([string]$file) {
    $r = @{ age = -1; gpu = -1; vram_used = -1; vram_total = -1; ram_free = -1; comfy = -1; batch = -1; verdict = '' }
    if (-not (Test-Path $file)) { return $r }
    try {
        $j = Get-Content $file -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($k in @('ts', 'clock_read', 'last_seen')) {
            $p = $j.PSObject.Properties[$k]
            if ($p -and $p.Value) { $r.age = [int]((Get-Date) - [datetime]::Parse([string]$p.Value)).TotalMinutes; break }
        }
        if ($j.gpu) {
            if ($null -ne $j.gpu.util_pct) { $r.gpu = [int]$j.gpu.util_pct }
            if ($null -ne $j.gpu.vram_total_mb) { $r.vram_total = [int]$j.gpu.vram_total_mb }
            if ($null -ne $j.gpu.vram_free_mb) { $r.vram_used = [int]$j.gpu.vram_total_mb - [int]$j.gpu.vram_free_mb }
        }
        if ($j.ram -and $null -ne $j.ram.free_pct) { $r.ram_free = [double]$j.ram.free_pct }
        if ($j.load) {
            if ($null -ne $j.load.comfy_server) { $r.comfy = [int]$j.load.comfy_server }
            if ($null -ne $j.load.batchmode) { $r.batch = [int]$j.load.batchmode }
        }
        if ($j.verdict) { $r.verdict = [string]$j.verdict }
    } catch { }
    return $r
}

$machines = @(
    @{ id = 'bm-b'; ip = '100.82.175.0'; lane = 'cpu-sound'; hb = Join-Path $root 'gaming\MiniGame\Design\configs\GLOBAL\fleet\b.json' },
    @{ id = 'bm-c'; ip = '100.123.74.104'; lane = 'gpu-production'; hb = Join-Path $root 'gaming\MiniGame\Design\configs\GLOBAL\fleet\c.json' }
)

$verdicts = @{}
foreach ($m in $machines) {
    $net = TsOnline $m.ip
    $h = Read-Hb $m.hb
    $lst = Probe ("http://{0}:8790/status" -f $m.ip)
    $alive = $lst.ok -or (($h.age -ge 0) -and ($h.age -le 120))

    if ($net -eq 'offline') { $v = 'OFFLINE' }
    elseif (-not $alive) { $v = 'SVC_DOWN' }
    elseif ($h.age -gt 120) { $v = 'HB-STALE' }
    elseif ($h.ram_free -ge 0 -and $h.ram_free -lt 10) { $v = 'BLOCKED-RAM' }
    elseif (($h.gpu -ge 0) -and ($h.gpu -le 5) -and ($h.comfy -le 0) -and ($h.batch -le 0)) { $v = 'GPU-IDLE' }
    elseif ($h.gpu -gt 5) { $v = 'BUSY' }
    else { $v = 'ALIVE' }

    $verdicts[$m.id] = $v
    $workNote = ''
    if ($exec[$m.id] -gt 0) { $workNote = ' exec_cards=' + $exec[$m.id] } else { $workNote = ' exec_cards=' + $exec[$m.id] }
    $out += ("[{0}] {1} verdict={2} net={3} listener={4} gpu_util={5}% vram={6}/{7}MB ram_free={8}% comfy={9} batch={10} hb_age={11}m{12} hb_verdict={13}" -f `
        $stamp, $m.id, $v, $net, $(if ($lst.ok) { 'up' } else { 'down' }), $h.gpu, $h.vram_used, $h.vram_total, $h.ram_free, $h.comfy, $h.batch, $h.age, $workNote, $h.verdict)
}

# ---- bm-a self line: work-hour idle is allowed by CEO law, but never silent ----
$hh = [int](Get-Date -Format 'HH')
$isWeekend = ((Get-Date).DayOfWeek -eq [DayOfWeek]::Saturday) -or ((Get-Date).DayOfWeek -eq [DayOfWeek]::Sunday)
$inWorkWindow = ((-not $isWeekend) -and ($hh -ge 9) -and ($hh -lt 19))
$gpuLine = ''
$gpuUtil = -1
try {
    $gpuLine = (& nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits) -join ''
    if ($gpuLine -match '^\s*(\d+)') { $gpuUtil = [int]$Matches[1] }
} catch { }
if ($inWorkWindow) {
    $verdicts['bm-a'] = 'EXPECTED-IDLE-WORKHOURS'
    $out += ("[{0}] bm-a verdict=EXPECTED-IDLE-WORKHOURS gpu={1} exec_cards={2} (CEO work-hour yield 09:00-19:00)" -f $stamp, $gpuLine, $exec['bm-a'])
} else {
    if (($gpuUtil -ge 0) -and ($gpuUtil -le 20) -and ($exec['bm-a'] -gt 0)) { $verdicts['bm-a'] = 'GPU-IDLE-WORK' }
    elseif ($gpuUtil -gt 20) { $verdicts['bm-a'] = 'BUSY' }
    else { $verdicts['bm-a'] = 'GPU-IDLE' }
    $out += ("[{0}] bm-a verdict={1} gpu={2} exec_cards={3}" -f $stamp, $verdicts['bm-a'], $gpuLine, $exec['bm-a'])
}

# ---- streak + escalation: idle is a failure only when work exists ----
$prev = @{}
if (Test-Path $stateFile) { try { $prev = Get-Content $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch { } }
$warns = @()
$newState = [ordered]@{ ts = (Get-Date).ToString('s'); streaks = @{}; verdicts = @{} }
foreach ($id in @('bm-a', 'bm-b', 'bm-c')) {
    $v = [string]$verdicts[$id]
    $streak = 0
    if ($prev.streaks -and $prev.streaks.PSObject.Properties[$id]) { $streak = [int]$prev.streaks.PSObject.Properties[$id].Value }
    $bad = ($v -in @('OFFLINE', 'SVC_DOWN', 'HB-STALE', 'BLOCKED-RAM', 'GPU-IDLE', 'GPU-IDLE-WORK'))
    if ($bad) { $streak = $streak + 1 } else { $streak = 0 }
    $newState.streaks[$id] = $streak
    $newState.verdicts[$id] = $v
    $hasWork = ($exec[$id] -gt 0)
    if ($hasWork -and ($v -in @('OFFLINE', 'SVC_DOWN', 'HB-STALE', 'BLOCKED-RAM', 'GPU-IDLE', 'GPU-IDLE-WORK'))) {
        $warns += ("{0} verdict={1} streak={2} exec_cards={3}" -f $id, $v, $streak, $exec[$id])
    } elseif ($streak -ge 3) {
        $warns += ("{0} verdict={1} streak={2}" -f $id, $v, $streak)
    }
}
$newState | ConvertTo-Json -Depth 5 | Set-Content -Path $stateFile -Encoding UTF8
if ($warns.Count -gt 0) {
    $out += ("[{0}] **WARN-IDLE-WITH-WORK** {1} -> dispatcher must page lane owner (P1)" -f $stamp, ($warns -join '; '))
}

$existing = @()
if (Test-Path $log) { $existing = @(Get-Content $log -Encoding UTF8) }
$all = $existing + $out
if ($all.Count -gt 400) { $all = $all[-400..-1] }
Set-Content -Path $log -Value $all -Encoding UTF8
Write-Output ($out -join "`n")