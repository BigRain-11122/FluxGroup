# Group fleet utilization audit (CEO order 2026-09-24 ~11:05: unified scheduling + ensure every machine fully used, CPU/GPU/RAM).
# Read-only aggregation of EXISTING heartbeats (MiniGame fleet + BigMoney fleet + BigStream OS loop + BigCompute OS loop) - adds zero collection burden.
# New heartbeat source = add one source line below (open-closed). ASCII-only body (encoding law).

param(
    [switch]$Json,
    [string]$JsonDir = (Join-Path $env:USERPROFILE '.codely-cli\fleet-audit')
)

$ErrorActionPreference = 'Continue'

function Read-JsonSafe([string]$path) {
    try { return (Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json) }
    catch { return $null }
}

function Parse-Seen([string]$s) {
    if ([string]::IsNullOrWhiteSpace($s)) { return $null }
    $d = [DateTime]::MinValue
    if ([DateTime]::TryParse($s, [ref]$d)) { return $d } else { return $null }
}

# ---- PT-10 read-before-fetch law (2026-09-25): machine-read sources come from
# local clones whose pull channel can lag origin for hours -> stale heartbeats
# fabricate STALE/OFFLINE states (patrol PT-20260925-10). Fix: fetch origin refs
# before reading (working tree never touched - read-only law), then read each
# heartbeat freshest-wins across working tree + origin refs by internal ts.
# MiniGame additionally reads machine branches (PT-20260925-12 read-side
# hardening: BG-B/C heartbeat writers push to machine/* while master folding lags).
# git captures UTF-8 blobs: console must be UTF-8 or Chinese fields mojibake.
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false } catch { }

function Sync-Repo([string]$p) {
    if (-not (Test-Path (Join-Path $p '.git'))) { return }
    try { & git -C $p fetch --quiet 2>$null } catch { }
}

function Show-RepoFile([string]$repo, [string]$refPath) {
    try {
        $out = & git -C $repo show $refPath 2>$null
        if (-not $out) { return $null }
        return @($out)
    } catch { return $null }
}

function Parse-JsonLines($lines) {
    try { return (($lines | Out-String) | ConvertFrom-Json) } catch { return $null }
}

# freshest-wins JSON heartbeat across working tree + origin refs (by ts field).
# returns @(object, srcLabel) or @(null, '').
function Get-FreshJson([string]$repo, [string]$wtPath, [string]$relPath, [string[]]$refs, [string]$tsField) {
    $best = $null; $bestTs = [DateTime]::MinValue; $src = ''
    if (Test-Path -LiteralPath $wtPath) {
        $h = Read-JsonSafe $wtPath
        if ($null -ne $h) {
            $best = $h; $src = [IO.Path]::GetFileName($wtPath)
            $t = Parse-Seen ([string]$h.$tsField)
            if ($null -ne $t) { $bestTs = $t }
        }
    }
    foreach ($ref in $refs) {
        $lines = Show-RepoFile $repo ($ref + ':' + $relPath)
        if ($null -eq $lines) { continue }
        $h2 = Parse-JsonLines $lines
        if ($null -eq $h2) { continue }
        $t2 = Parse-Seen ([string]$h2.$tsField)
        if ($null -ne $t2 -and $t2 -gt $bestTs) { $best = $h2; $bestTs = $t2; $src = ([IO.Path]::GetFileName($wtPath) + '@' + $ref) }
    }
    return @($best, $src)
}

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)   # Tools\.. = FluxGroup root
$rows = @()

# --- Source 1: MiniGame fleet heartbeats (gaming/MiniGame/Design/configs/GLOBAL/fleet/*.json) ---
# PT-12: writers push to machine branches; freshest-wins across wt + master + machine/*.
$mgRepo = Join-Path $root 'gaming\MiniGame'
$mgRel = 'Design/configs/GLOBAL/fleet'
$mgDir = Join-Path $mgRepo 'Design\configs\GLOBAL\fleet'
Sync-Repo $mgRepo
if (Test-Path $mgDir) {
    Get-ChildItem $mgDir -Filter *.json | ForEach-Object {
        $pair = Get-FreshJson $mgRepo $_.FullName ($mgRel + '/' + $_.Name) @('origin/master', 'origin/machine/A', 'origin/machine/B', 'origin/machine/C') 'ts'
        $h = $pair[0]; $hSrc = $pair[1]
        if ($null -eq $h) { return }
        $ramPct = '-'; if ($h.ram.free_pct -ne $null) { $ramPct = [string]$h.ram.free_pct }
        $vram = '-';    if ($h.gpu.vram_free_mb -ne $null) { $vram = [string][Math]::Round($h.gpu.vram_free_mb / 1024.0, 1) }
        $gpuU = '-';   if ($h.gpu.util_pct -ne $null) { $gpuU = [string]$h.gpu.util_pct }
        $disk = '-';   if ($h.disk.repo_free_gb -ne $null) { $disk = [string]$h.disk.repo_free_gb }
        $cores = '-';  if ($h.cpu.logical -ne $null) { $cores = [string]$h.cpu.logical }
        $verdict = '-'; if ($h.verdict) { $verdict = [string]$h.verdict }
        $rows += [pscustomobject]@{
            id = ('BG-' + $h.machine_id); last_seen = [string]$h.ts; cores = $cores
            ram_free_pct = $ramPct; vram_free_gb = $vram; gpu_util_pct = $gpuU; disk_free_gb = $disk
            task = $verdict; src = $hSrc
        }
    }
}

# --- Source 2: BigMoney fleet heartbeats (quant/bigmoney/fleet/machines/bm-*.json) ---
# PT-10: freshest-wins across wt + origin/main (pull channel death lags the clone).
$bmRepo = Join-Path $root 'quant\bigmoney'
$bmDir = Join-Path $bmRepo 'fleet\machines'
Sync-Repo $bmRepo
if (Test-Path $bmDir) {
    Get-ChildItem $bmDir -Filter *.json | ForEach-Object {
        $pair = Get-FreshJson $bmRepo $_.FullName ('fleet/machines/' + $_.Name) @('origin/main') 'last_seen'
        $h = $pair[0]; $hSrc = $pair[1]
        if ($null -eq $h) { return }
        $ramPct = '-'
        if ($h.free_ram_gb -ne $null -and $h.total_ram_gb -ne $null) {
            $ramPct = [string][Math]::Round(100.0 * $h.free_ram_gb / $h.total_ram_gb, 0)
        }
        $vram = '-'
        if ($h.gpu_free_vram_gb -ne $null) { $vram = [string][Math]::Round([double]$h.gpu_free_vram_gb, 1) }
        elseif ($h.gpu_free_vram_mb -ne $null) { $vram = [string][Math]::Round($h.gpu_free_vram_mb / 1024.0, 1) }
        $cores = '-'; if ($h.cpu_cores -ne $null) { $cores = [string]$h.cpu_cores }
        elseif ($h.cores -ne $null) { $cores = [string]$h.cores }
        $task = '-'; if ($h.current_task) { $task = ([string]$h.current_task); if ($task.Length -gt 60) { $task = $task.Substring(0, 60) } }
        $verdict = '-'; if ($h.verdict) { $verdict = [string]$h.verdict }
        $rows += [pscustomobject]@{
            id = [string]$h.machine_id; last_seen = [string]$h.last_seen; cores = $cores
            ram_free_pct = $ramPct; vram_free_gb = $vram; gpu_util_pct = '-'; disk_free_gb = '-'
            task = $task; src = $hSrc
        }
    }
}

# --- Source 3: BigStream OS-loop heartbeat (media/BigStream/src/os/state.json + logs/probe-heartbeat.txt) ---
# P-50 order 2026-09-24. PT-10: freshest-wins across wt + origin/main by beat ts.
# Source has NO resource fields (os-protocol: state.json = loop
# ledger only) -> ram/vram/gpu/disk stay '-' (honesty law, no invented numbers).
# Online rule = heartbeat ts freshness <= 20 min (os-protocol S5 fleet comm SLA).
# Freshness evidence: exact beat ts in logs/probe-heartbeat.txt ("YYYY-MM-DD HH:MM:SS
# osloop: ..."); state.json log ts minutes may be masked ("14:3x") -> floored to 14:30
# (age never understated). Freshest of the two wins. current_task = state.json log tail.
function Get-BsStateTs($lines) {
    $h = Parse-JsonLines $lines
    if ($null -eq $h -or -not $h.log) { return $null }
    $best = $null
    foreach ($e in @($h.log)) {
        if ([string]$e -match '^(\d{4}-\d{2}-\d{2}) (\d{2}):(\d)([0-9x])') {
            $mm = 10 * [int]$Matches[3]
            if ($Matches[4] -ne 'x') { $mm = $mm + [int]$Matches[4] }
            $d = [DateTime]::MinValue
            if ([DateTime]::TryParseExact(($Matches[1] + ' ' + $Matches[2] + ('{0:d2}' -f $mm)), 'yyyy-MM-dd HH:mm', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$d)) {
                if ($null -eq $best -or $d -gt $best) { $best = $d }
            }
        }
    }
    return $best
}
function Get-BeatTs($lines) {
    $best = $null
    foreach ($line in @($lines)) {
        if ($line -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ') {
            $d = [DateTime]::MinValue
            if ([DateTime]::TryParseExact($Matches[1], 'yyyy-MM-dd HH:mm:ss', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$d)) { $best = $d }
        }
    }
    return $best
}
function Get-FreshText([string]$repo, [string]$wtPath, [string]$relPath, [string[]]$refs, [scriptblock]$tsFn) {
    $bestLines = $null; $bestTs = [DateTime]::MinValue; $src = ''
    if (Test-Path -LiteralPath $wtPath) {
        $l = @(Get-Content -LiteralPath $wtPath -Encoding UTF8)
        if ($l.Count -gt 0) {
            $bestLines = $l; $src = [IO.Path]::GetFileName($wtPath)
            $t = & $tsFn $l
            if ($null -ne $t) { $bestTs = $t }
        }
    }
    foreach ($ref in $refs) {
        $l2 = Show-RepoFile $repo ($ref + ':' + $relPath)
        if ($null -eq $l2) { continue }
        $t2 = & $tsFn $l2
        if ($null -ne $t2 -and $t2 -gt $bestTs) { $bestLines = $l2; $bestTs = $t2; $src = ([IO.Path]::GetFileName($wtPath) + '@' + $ref) }
    }
    return @($bestLines, $src)
}
$bsRepo = Join-Path $root 'media\BigStream'
Sync-Repo $bsRepo
$bsStatePair = Get-FreshText $bsRepo (Join-Path $root 'media\BigStream\src\os\state.json') 'src/os/state.json' @('origin/main') ${function:Get-BsStateTs}
$bsBeatPair  = Get-FreshText $bsRepo (Join-Path $root 'media\BigStream\logs\probe-heartbeat.txt') 'logs/probe-heartbeat.txt' @('origin/main') ${function:Get-BeatTs}
if ($null -ne $bsStatePair[0]) {
    $h = Parse-JsonLines $bsStatePair[0]
    if ($null -ne $h) {
        $seen = $null
        if ($null -ne $bsBeatPair[0]) {
            foreach ($line in $bsBeatPair[0]) {
                if ($line -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ') {
                    $d = [DateTime]::MinValue
                    if ([DateTime]::TryParseExact($Matches[1], 'yyyy-MM-dd HH:mm:ss', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$d)) { $seen = $d }
                }
            }
        }
        if ($h.log) {
            foreach ($e in @($h.log)) {
                if ([string]$e -match '^(\d{4}-\d{2}-\d{2}) (\d{2}):(\d)([0-9x])') {
                    $mm = 10 * [int]$Matches[3]
                    if ($Matches[4] -ne 'x') { $mm = $mm + [int]$Matches[4] }
                    $d = [DateTime]::MinValue
                    if ([DateTime]::TryParseExact(($Matches[1] + ' ' + $Matches[2] + ('{0:d2}' -f $mm)), 'yyyy-MM-dd HH:mm', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$d)) {
                        if ($null -eq $seen -or $d -gt $seen) { $seen = $d }
                    }
                }
            }
        }
        $lastSeen = ''; $mark = 'NO_TS'
        if ($null -ne $seen) {
            $lastSeen = $seen.ToString('yyyy-MM-dd HH:mm')
            $ageMin = [Math]::Round(([DateTime]::Now - $seen).TotalMinutes, 0)
            if ($ageMin -le 20) { $mark = 'ONLINE(' + $ageMin + 'm)' } else { $mark = 'LATE(' + $ageMin + 'm)' }
        }
        $task = '-'
        if ($h.log) {
            $task = ([string]@($h.log)[-1] -replace '^\d{4}-\d{2}-\d{2} \d{2}:[0-9x]{2}\s*', '')
            if ($task.Length -gt 60) { $task = $task.Substring(0, 60) }
        }
        $task = $mark + ': ' + $task
        $rows += [pscustomobject]@{
            id = 'bigstream'; last_seen = $lastSeen; cores = '-'
            ram_free_pct = '-'; vram_free_gb = '-'; gpu_util_pct = '-'; disk_free_gb = '-'
            task = $task; src = $bsStatePair[1]
        }
    }
}
# --- Source 4: BigCompute OS-loop heartbeat (compute/BigCompute/state/heartbeat.txt + state/rounds.log) ---
# P-50 order 2026-09-24 + PT-10 freshest-wins on the beat file (liveness source;
# rounds.log stays a wt read - task-text tail only, not a freshness input).
# Same method as Source 3: online rule = beat ts freshness
# <= 20 min; beat format "YYYY-MM-DD HH:MM:SS os-loop: <msg>" (exact seconds, no
# masking). No resource fields -> '-'. current_task = state/rounds.log tail
# "done: ..." summary (beat msg as fallback). If the beat file is absent the source
# self-skips (open-closed; add a real heartbeat file to appear in this audit).
$bcRepo = Join-Path $root 'compute\BigCompute'
Sync-Repo $bcRepo
$bcBeatPair = Get-FreshText $bcRepo (Join-Path $root 'compute\BigCompute\state\heartbeat.txt') 'state/heartbeat.txt' @('origin/main') ${function:Get-BeatTs}
if ($null -ne $bcBeatPair[0]) {
    $seen = $null; $beatMsg = '-'
    foreach ($line in $bcBeatPair[0]) {
        if ($line -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.+)$') {
            $d = [DateTime]::MinValue
            if ([DateTime]::TryParseExact($Matches[1], 'yyyy-MM-dd HH:mm:ss', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$d)) { $seen = $d; $beatMsg = $Matches[2] }
        }
    }
    $task = ([string]$beatMsg -replace '^[A-Za-z0-9._-]+:\s*', '')
    $bcRounds = Join-Path $root 'compute\BigCompute\state\rounds.log'
    if (Test-Path $bcRounds) {
        $rLines = @(Get-Content -LiteralPath $bcRounds -Encoding UTF8 | Where-Object { $_ -match '\S' })
        if ($rLines.Count -gt 0) {
            $tail = [string]$rLines[-1]
            if ($tail -match 'done: (.+)$') { $task = $Matches[1] }
            elseif ($tail -match '^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?\s*(.*)$') { $task = $Matches[2] }
        }
    }
    if ($task.Length -gt 60) { $task = $task.Substring(0, 60) }
    $lastSeen = ''; $mark = 'NO_TS'
    if ($null -ne $seen) {
        $lastSeen = $seen.ToString('yyyy-MM-dd HH:mm')
        $ageMin = [Math]::Round(([DateTime]::Now - $seen).TotalMinutes, 0)
        if ($ageMin -le 20) { $mark = 'ONLINE(' + $ageMin + 'm)' } else { $mark = 'LATE(' + $ageMin + 'm)' }
    }
    $task = $mark + ': ' + $task
    $rows += [pscustomobject]@{
        id = 'bigcompute'; last_seen = $lastSeen; cores = '-'
        ram_free_pct = '-'; vram_free_gb = '-'; gpu_util_pct = '-'; disk_free_gb = '-'
        task = $task; src = $bcBeatPair[1]
    }
}

# --- freshness + utilization flags (fleet-allocations 5/6 thresholds) ---
$now = [DateTime]::Now
$flagged = @()
foreach ($r in $rows) {
    $seen = Parse-Seen $r.last_seen
    $ageH = -1
    if ($null -ne $seen) { $ageH = [Math]::Round(($now - $seen).TotalHours, 1) }
    $flag = ''
    if ($ageH -lt 0) { $flag = 'NO_TS' }
    elseif ($ageH -gt 24) { $flag = 'OFFLINE' }
    elseif ($ageH -gt 2) { $flag = 'STALE' }
    else {
        $ram = 100; $vram = 99
        if ($r.ram_free_pct -ne '-') { $ram = [double]$r.ram_free_pct }
        if ($r.vram_free_gb -ne '-') { $vram = [double]$r.vram_free_gb }
        if ($ram -lt 10 -or $vram -lt 1.5) { $flag = 'YELLOW-HEAVY' }
        elseif ($ram -ge 40 -and $vram -ge 6 -and ($r.task -match 'idle' -or $r.task -match 'CLEAN' -or $r.task -match 'OK')) { $flag = 'GREEN-IDLE' }
        else { $flag = 'OK' }
    }
    $flagged += [pscustomobject]@{
        id = $r.id; last_seen = $r.last_seen; age_h = $ageH; cores = $r.cores
        ram_free_pct = $r.ram_free_pct; vram_free_gb = $r.vram_free_gb; gpu_util_pct = $r.gpu_util_pct
        disk_free_gb = $r.disk_free_gb; flag = $flag; task = $r.task
    }
}

Write-Output ('FLEET AUDIT ' + $now.ToString('yyyy-MM-dd HH:mm') + ' - machines: ' + $flagged.Count + ' (fresh<=2h / GREEN-IDLE=inter-borrowable / YELLOW-HEAVY=protect)')
$flagged | Sort-Object id | Format-Table -AutoSize | Out-String -Width 200 | Write-Output

$offline = @($flagged | Where-Object { $_.flag -eq 'OFFLINE' })
$stale   = @($flagged | Where-Object { $_.flag -eq 'STALE' })
$green   = @($flagged | Where-Object { $_.flag -eq 'GREEN-IDLE' })
$heavy   = @($flagged | Where-Object { $_.flag -eq 'YELLOW-HEAVY' })
Write-Output ('SUMMARY offline=' + $offline.Count + ' stale=' + $stale.Count + ' green_idle=' + $green.Count + ' heavy=' + $heavy.Count)
if ($green.Count -gt 0) { Write-Output ('GREEN-IDLE (borrowable / name-owning company may assign work): ' + (($green | ForEach-Object { $_.id }) -join ', ')) }
if ($heavy.Count -gt 0) { Write-Output ('YELLOW-HEAVY (protect per fleet 10, keepwarm valve): ' + (($heavy | ForEach-Object { $_.id }) -join ', ')) }
if ($offline.Count -gt 0 -or $stale.Count -gt 0) { Write-Output ('STALE/OFFLINE (blackout-zone law, name in night report): ' + (((@($offline) + @($stale)) | ForEach-Object { $_.id }) -join ', ')) }
Write-Output 'NOTE: bm-a and BG-A are the same physical box (dual role). CPU util pct is a heartbeat-extension backlog (P-32).'

if ($Json) {
    New-Item -ItemType Directory -Force -Path $JsonDir | Out-Null
    $snap = Join-Path $JsonDir 'last.json'
    $flagged | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $snap -Encoding UTF8
    Write-Output ('JSON snapshot: ' + $snap)
}
