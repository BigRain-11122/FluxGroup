# delivery-watch.ps1 - C-20261016-02 Cure-1: deliverable-existence + P0 deadline sentinel (zero-LLM, deterministic)
# Law: CEO order 2026-10-16 11:5x "root-cure must be a deployed+verified mechanism"; O-20260923 honesty (no paper claims)
# Carrier: bm-a-DeliveryWatch task, every:5m, registered via Tools\task-register.ps1 (U060 silent chain).
# LogonType TRUTH: InteractiveToken (bm-a UAC denies unelevated S4U) - hidden chain = zero flash
# while logged on, no logoff survival; queued in Tools\task-s4u-backlog.md for elevated conversion.
# Watch contracts: cph4\fleet\dispatcher\delivery-watch\<id>.json
#   { id, owner, expected_paths:[repo-relative globs], min_count, dispatch_ts, deadline_ts,
#     min_duration_sec (optional, v1.1): media-duration quality gate - files shorter than this
#     do NOT count toward min_count (jayredo 5.17s lesson: existence-only contracts let
#     short clips silently pad the assembly; O-20261016 CEO mechanism order) }
# States per watch: PENDING -> DELIVERED (>= min_count fresh+long-enough files) | OVERDUE (past deadline)
#   OVERDUE -> FLAG-<id>.txt + ALERTS.md row + one poke per 60min to owner machine (fail-soft)
# PS 5.1 safe. ASCII comments only (encoding law).
$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
$WDir = Join-Path $Root 'cph4\fleet\dispatcher\delivery-watch'
$Dispatch = Join-Path $Root 'Tools\fleet-dispatch.ps1'
if (-not (Test-Path $WDir)) { New-Item -ItemType Directory -Path $WDir -Force | Out-Null }
$Log = Join-Path $WDir 'watch.log'
$Alerts = Join-Path $WDir 'ALERTS.md'

function WLog([string]$s) {
    $line = ("{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $s)
    Add-Content -LiteralPath $Log -Value $line -Encoding UTF8
    if ((Get-Item $Log -EA 0).Length -gt 1MB) {
        $t = Get-Content $Log -EA 0 | Select-Object -Last 200
        Set-Content -LiteralPath $Log -Value $t -Encoding UTF8
    }
}

$now = Get-Date
$changed = $false
Get-ChildItem -LiteralPath $WDir -Filter '*.json' -File -EA 0 | ForEach-Object {
    $jf = $_
    $id = [IO.Path]::GetFileNameWithoutExtension($jf.Name)
    $doneM = Join-Path $WDir ("done-" + $id + ".txt")
    if (Test-Path $doneM) { return }
    try { $c = Get-Content $jf.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { WLog ("PARSE-FAIL " + $id); return }
    $dispatchTs = [datetime]::Parse($c.dispatch_ts, [Globalization.CultureInfo]::InvariantCulture)
    $deadlineTs = [datetime]::Parse($c.deadline_ts, [Globalization.CultureInfo]::InvariantCulture)
    $hasDur = $false; $minDur = 0.0
    if ($c.PSObject.Properties.Name -contains 'min_duration_sec') { $hasDur = $true; $minDur = [double]$c.min_duration_sec }
    $ff = 'C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe'
    $hit = 0; $qfail = @()
    foreach ($p in @($c.expected_paths)) {
        $full = Join-Path $Root ($p -replace '/', '\')
        $items = @()
        if ($full.Contains('*')) { $items = @(Get-ChildItem -Path $full -File -EA 0) }
        else { $g = Get-Item -LiteralPath $full -EA 0; if ($g) { $items = @($g) } }
        foreach ($it in $items) {
            if ($it.LastWriteTime -lt $dispatchTs) { continue }
            if ($hasDur -and (Test-Path -LiteralPath $ff)) {
                $durTxt = (& $ff -i $it.FullName 2>&1 | Select-String -Pattern 'Duration:' | Select-Object -First 1)
                $dur = -1.0
                if ("$durTxt" -match 'Duration:\s*(\d+):(\d+):(\d+\.?\d*)') {
                    $dur = ([int]$matches[1] * 3600) + ([int]$matches[2] * 60) + [double]$matches[3]
                }
                if ($dur -ge 0 -and $dur -lt $minDur) {
                    $qfail += ($it.Name + '=' + [Math]::Round($dur, 2) + 's')
                    continue
                }
            }
            $hit++
        }
    }
    $stateF = Join-Path $WDir ("state-" + $id + ".txt")
    $prev = ''
    if (Test-Path $stateF) { $prev = (Get-Content $stateF -Raw -EA 0) }
    if ($hit -ge [int]$c.min_count) {
        Set-Content -LiteralPath $doneM -Value ("DELIVERED " + $now.ToString('s') + " hit=" + $hit) -Encoding UTF8
        Set-Content -LiteralPath $stateF -Value 'DELIVERED' -Encoding UTF8
        if ($prev -ne 'DELIVERED') { WLog ("DELIVERED " + $id + " hit=" + $hit); $changed = $true }
        return
    }
    if ($now -gt $deadlineTs) {
        $flagF = Join-Path $WDir ("FLAG-" + $id + ".txt")
        $pokeDue = $true
        if (Test-Path $flagF) { $pokeDue = (( $now - (Get-Item $flagF).LastWriteTime).TotalMinutes -ge 60) }
        if (-not (Test-Path $flagF)) {
            Set-Content -LiteralPath $flagF -Value ("OVERDUE id=" + $id + " owner=" + $c.owner + " hit=" + $hit + "/" + $c.min_count + " deadline=" + $c.deadline_ts) -Encoding UTF8
            Add-Content -LiteralPath $Alerts -Value ("| " + $now.ToString('yyyy-MM-dd HH:mm') + " | DELIVERY-OVERDUE | " + $id + " | owner=" + $c.owner + " hit=" + $hit + "/" + $c.min_count + " |") -Encoding UTF8
            WLog ("OVERDUE-ALERT " + $id + " hit=" + $hit + "/" + $c.min_count)
            $changed = $true
        }
        if ($pokeDue) {
            Set-Content -LiteralPath $flagF -Value ("OVERDUE id=" + $id + " owner=" + $c.owner + " hit=" + $hit + "/" + $c.min_count + " deadline=" + $c.deadline_ts + " poked=" + $now.ToString('s')) -Encoding UTF8
            & powershell -NoProfile -ExecutionPolicy Bypass -File $Dispatch -Reason ("delivery overdue: " + $id + " (owner " + $c.owner + ")") -Quiet | Out-Null
            WLog ("OVERDUE-POKE " + $id + " -> " + $c.owner)
        }
    } else {
        $sig = 'PENDING ' + $hit + ' q' + $qfail.Count
        if ($prev -ne $sig) {
            $msg = "PENDING " + $id + " hit=" + $hit + "/" + $c.min_count
            if ($qfail.Count -gt 0) {
                $msg += " QUALITY-FAIL<" + $minDur + "s>: " + ($qfail -join ', ')
                Add-Content -LiteralPath $Alerts -Value ("| " + $now.ToString('yyyy-MM-dd HH:mm') + " | QUALITY-FAIL | " + $id + " | " + ($qfail -join ', ') + " | min=" + $minDur + "s |") -Encoding UTF8
            }
            WLog $msg
            Set-Content -LiteralPath $stateF -Value $sig -Encoding UTF8
            $changed = $true
        }
    }
}
exit 0
