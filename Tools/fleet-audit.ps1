# Group fleet utilization audit (CEO order 2026-09-24 ~11:05: unified scheduling + ensure every machine fully used, CPU/GPU/RAM).
# Read-only aggregation of EXISTING heartbeats (MiniGame fleet + BigMoney fleet) - adds zero collection burden.
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

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)   # Tools\.. = FluxGroup root
$rows = @()

# --- Source 1: MiniGame fleet heartbeats (gaming/MiniGame/Design/configs/GLOBAL/fleet/*.json) ---
$mgDir = Join-Path $root 'gaming\MiniGame\Design\configs\GLOBAL\fleet'
if (Test-Path $mgDir) {
    Get-ChildItem $mgDir -Filter *.json | ForEach-Object {
        $h = Read-JsonSafe $_.FullName
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
            task = $verdict; src = $_.Name
        }
    }
}

# --- Source 2: BigMoney fleet heartbeats (quant/bigmoney/fleet/machines/bm-*.json) ---
$bmDir = Join-Path $root 'quant\bigmoney\fleet\machines'
if (Test-Path $bmDir) {
    Get-ChildItem $bmDir -Filter *.json | ForEach-Object {
        $h = Read-JsonSafe $_.FullName
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
            task = $task; src = $_.Name
        }
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
