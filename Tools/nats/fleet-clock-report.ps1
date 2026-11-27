# fleet-clock-report.ps1 - read the three node states from NATS KV and report clock
# alignment. Corrected hub time = node ts_utc_ms + clock_offset_ms. Skew = |offset|.
# A node still on the old schema (no ts_utc_ms / offset) is reported as v1-old, not green.
param(
    [string]$Server = 'nats://127.0.0.1:4222',
    [string]$OutFile = ''
)
$ErrorActionPreference = 'Continue'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not $OutFile) { $OutFile = Join-Path $root 'cph4\fleet\dispatcher\CLOCK-SKEW.json' }
$nats = Join-Path $root 'Tools\nats\bin\nats.exe'
$now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$rows = @()
$maxSkew = 0.0
$old = 0; $missing = 0

foreach ($n in @('bm-a', 'bm-b', 'bm-c')) {
    $raw = @(& $nats -s $Server kv get FLEET_STATE ("state." + $n) --raw 2>&1)
    $line = ($raw | Where-Object { $_ -match '^\s*\{' } | Select-Object -Last 1)
    $j = $null
    if ($line) { try { $j = $line | ConvertFrom-Json } catch { } }
    if (-not $j) {
        $rows += [pscustomobject]@{ node = $n; status = 'MISSING'; ts = $null; corrected_ts = $null; age_ms = $null; offset_ms = $null; precision_ms = $null; seq = $null }
        $missing++
        continue
    }
    $off = $null; $prec = $null
    if ($j.PSObject.Properties['clock_offset_ms']) { $off = $j.clock_offset_ms }
    if ($j.PSObject.Properties['clock_rtt_ms']) { $prec = $j.clock_rtt_ms }
    if ($null -eq $off -or -not $j.PSObject.Properties['ts_utc_ms']) {
        $rows += [pscustomobject]@{ node = $n; status = 'V1-OLD-SCHEMA'; ts = $j.ts; corrected_ts = $null; age_ms = $null; offset_ms = $null; precision_ms = $null; seq = $null }
        $old++
        continue
    }
    $ts = [int64]$j.ts_utc_ms
    $corrected = $ts + [double]$off
    $age = $now - $corrected
    $absOff = [math]::Abs([double]$off)
    if ($absOff -gt $maxSkew) { $maxSkew = $absOff }
    $status = 'OK'
    if ($prec -and ($absOff -gt (2 * [double]$prec + 20))) { $status = 'SKEW-HIGH' }
    $rows += [pscustomobject]@{
        node = $n; status = $status; ts = $j.ts
        corrected_ts = [math]::Round($corrected, 0)
        age_ms = [math]::Round($age, 0)
        offset_ms = [double]$off; precision_ms = $prec; seq = $j.seq
    }
}

$report = [ordered]@{
    ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fff')
    hub_now_ms = $now
    max_abs_offset_ms = [math]::Round($maxSkew, 1)
    old_schema = $old
    missing = $missing
    nodes = $rows
}
$dir = Split-Path $OutFile -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$report | ConvertTo-Json -Depth 4 | Set-Content -Path $OutFile -Encoding UTF8

foreach ($r in $rows) {
    if ($r.status -eq 'MISSING' -or $r.status -eq 'V1-OLD-SCHEMA') {
        Write-Output ("{0,-5} {1,-14} ts={2}" -f $r.node, $r.status, $r.ts)
    } else {
        Write-Output ("{0,-5} {1,-10} offset={2,7}ms precision=±{3}ms age={4}ms seq={5}" -f $r.node, $r.status, $r.offset_ms, $r.precision_ms, $r.age_ms, $r.seq)
    }
}
Write-Output ("MAX-ABS-OFFSET {0}ms old={1} missing={2}" -f [math]::Round($maxSkew, 1), $old, $missing)