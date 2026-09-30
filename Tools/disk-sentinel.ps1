# disk-sentinel.ps1 - Proactive disk guard v1.0 (CPH4 Labs, CEO order 2026-09-30:
# "cleanup must be front-loaded and timely; disk space is very limited; set it up
# scientifically"). Tiered-response science (resource-chain sec.3 sec.11.9):
#   tier 1 (this tool, 5min)  - disk-level ladders + age-gated Class-A auto-trim
#   tier 2 (guard rounds, 2x/day) - area caps + ledger growth trend lines
#   tier 3 (pipeline batches) - batch-end self-clean (sec.11.8)
#   tier 4 (Sunday)           - deep sweep (disk-sweep.ps1)
# Ladders are derived from worst measured burn (56GB/night): warn->red ~1.5 nights,
# red->floor ~2 nights of runway always preserved. In-flight protection stays:
# fresh files (<gate) inside active experiment areas are never touched.
# Actions log to fleet-liveness alerts.jsonl (charter sec.5/7) + state file.
# ASCII-only body (encoding law). PS 5.1 safe. Single-flight lock 4 min.

param(
    [double]$WarnFreeGB = 700,
    [double]$RedFreeGB  = 620,
    [double]$FloorFreeGB = 500,
    [string]$StateDir = (Join-Path $env:USERPROFILE '.codely-cli\fleet-liveness')
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$now = Get-Date

# single-flight lock (stale takeover 4 min)
$lockPath = Join-Path $env:TEMP 'disk-sentinel.lock'
if (Test-Path $lockPath) {
    try { if (((Get-Date) - (Get-Item $lockPath).LastWriteTime).TotalMinutes -lt 4) { exit 0 } } catch { }
}
try { Set-Content -LiteralPath $lockPath -Value 'run' -ErrorAction Stop } catch { exit 0 }
if (-not (Test-Path $StateDir)) { New-Item -ItemType Directory -Path $StateDir -Force | Out-Null }

$free = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
$tier = 'OK'
if ($free -lt $FloorFreeGB) { $tier = 'FLOOR' }
elseif ($free -lt $RedFreeGB) { $tier = 'RED' }
elseif ($free -lt $WarnFreeGB) { $tier = 'WARN' }

$actions = @()
$trimmed = 0
function Trim-Dir($path, $gateHours, $label) {
    if (-not (Test-Path -LiteralPath $path)) { return }
    $cutoff = (Get-Date).AddHours(-1 * $gateHours)
    $old = @(Get-ChildItem -LiteralPath $path -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff })
    if ($old.Count -eq 0) { return }
    $sz = ($old | Measure-Object Length -Sum).Sum; if (-not $sz) { $sz = 0 }
    $old | Remove-Item -Force -ErrorAction SilentlyContinue
    $script:trimmed += $sz
    $script:actions += ('trim ' + $label + ': ' + $old.Count + ' files ' + [math]::Round($sz / 1MB) + 'MB')
}
function Get-FreeMB($path) {
    if (-not (Test-Path -LiteralPath $path)) { return 0 }
    $b = (Get-ChildItem -LiteralPath $path -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    if (-not $b) { $b = 0 }
    [math]::Round($b / 1MB)
}

# ---- Class-A trims (age-gated; gates tighten as tier escalates) ----
$gateTemp  = 168; if ($tier -eq 'RED' -or $tier -eq 'FLOOR') { $gateTemp = 48 }
$gateTrash = 168; if ($tier -eq 'RED' -or $tier -eq 'FLOOR') { $gateTrash = 48 }
Trim-Dir (Join-Path $env:LOCALAPPDATA 'Temp') $gateTemp 'win-temp'
Trim-Dir (Join-Path $root 'docs\_trash') $gateTrash 'trash-quarantine'
Trim-Dir (Join-Path $root '.codely-cli\audio-staging') 24 'audio-staging'
Trim-Dir (Join-Path $env:USERPROFILE '.cache\huggingface') 1 'hf-cache'
# download corpses inside experiment-area caches (in-flight resumes protected by age gate)
$gateCorpse = 48; if ($tier -eq 'RED' -or $tier -eq 'FLOOR') { $gateCorpse = 24 }
$lb = Join-Path $root '.codely-cli\labbench'
if (Test-Path $lb) {
    $old = @(Get-ChildItem $lb -Recurse -File -Force -Filter '*.incomplete' -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-1 * $gateCorpse) })
    if ($old.Count -gt 0) {
        $sz = ($old | Measure-Object Length -Sum).Sum; if (-not $sz) { $sz = 0 }
        $old | Remove-Item -Force -ErrorAction SilentlyContinue
        $trimmed += $sz
        $actions += ('trim incomplete-corpses: ' + $old.Count + ' files ' + [math]::Round($sz / 1MB) + 'MB')
    }
}

# ---- escalation ladders ----
if ($tier -ne 'OK') {
    $sig = 'disk-' + $tier + '|' + $free
    $alertsPath = Join-Path $StateDir 'alerts.jsonl'
    $statePath  = Join-Path $StateDir 'disk-sentinel.json'
    $lastSig = ''
    $lastTs = [DateTime]::MinValue
    if (Test-Path $statePath) {
        try { $s = Get-Content $statePath -Raw -Encoding UTF8 | ConvertFrom-Json; $lastSig = [string]$s.sig; $lastTs = [DateTime]::ParseExact([string]$s.ts, 'yyyy-MM-dd HH:mm:ss', $null) } catch { }
    }
    $throttleMin = 120; if ($tier -eq 'FLOOR') { $throttleMin = 60 }
    $escalate = ($sig -ne $lastSig) -or (((Get-Date) - $lastTs).TotalMinutes -ge $throttleMin)
    if ($escalate) {
        $line = '{"ts":"' + $now.ToString('yyyy-MM-dd HH:mm:ss') + '","src":"disk-sentinel","type":"disk-' + $tier.ToLower() + '","detail":"free=' + $free + 'GB ladder ' + $FloorFreeGB + '/' + $RedFreeGB + '/' + $WarnFreeGB + ' - class-A trimmed this cycle"}'
        Add-Content -LiteralPath $alertsPath -Value $line -Encoding UTF8
    }
}

# ---- state file ----
@{ ts = $now.ToString('yyyy-MM-dd HH:mm:ss'); free = $free; tier = $tier; trimmedMB = [math]::Round($trimmed / 1MB); sig = 'disk-' + $tier + '|' + $free; actions = $actions } |
    ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $StateDir 'disk-sentinel.json') -Encoding UTF8
Remove-Item $lockPath -Force -ErrorAction SilentlyContinue
Write-Output ('DISK SENTINEL ' + $now.ToString('yyyy-MM-dd HH:mm') + ' free=' + $free + 'GB tier=' + $tier + ' trimmed=' + [math]::Round($trimmed / 1MB) + 'MB actions=' + $actions.Count)
