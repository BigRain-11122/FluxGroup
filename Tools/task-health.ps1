# Group task health check - scientific automation monitoring (CEO order 2026-09-24 ~14:00).
# Read-only. ASCII-only body (encoding law). Cadence.md 6: five health signals - this tool covers
# the scheduler face (existence / freshness / result codes / disabled-vs-exempt audit);
# output freshness = per-loop ledger timestamps (cadence 6.3), resources = fleet-audit.ps1.

param(
    # known design-state-disabled tasks (cadence ledger - E3 exempt, never auto-heal back on)
    [string[]]$ExemptDisabled = @('MiniGameDailyDigest', 'MoneyAutoGuardian', 'GimmeAll-AutoSentinel', 'CarGZH_DailyReview', 'CarGZH_Erchuang', 'CarGZH_HotWatch', 'CarGZH_MaterialBank', 'CarGZH_MechanismWatch', 'CarGZH_Morning', 'CarGZH_WeeklyEvolve', 'CarGZH_YTRadar')
)

$ErrorActionPreference = 'Continue'
$now = [DateTime]::Now

function Convert-IsoDuration([string]$iso) {
    # ISO8601 duration like PT10M / PT1H / P1D -> minutes. Returns -1 when unparsable.
    if ([string]::IsNullOrWhiteSpace($iso)) { return -1 }
    $total = 0.0
    $num = ''
    foreach ($ch in $iso.ToCharArray()) {
        if ($ch -ge '0' -and $ch -le '9') { $num += $ch; continue }
        $v = 0.0; if ($num) { $v = [double]$num }
        switch ($ch) {
            'H' { $total += $v * 60 }
            'M' { $total += $v }
            'D' { $total += $v * 1440 }
            'W' { $total += $v * 10080 }
        }
        $num = ''
    }
    if ($total -le 0) { return -1 }
    return [Math]::Floor($total)
}

function Get-ExpectedMinutes($task) {
    # smallest repetition across triggers; else derive from trigger class; -1 = event-bound/one-shot (skip freshness)
    # LAW: PS5.1 CIM trigger has NO RepetitionInterval property - it lives at $t.Repetition.Interval (ISO8601).
    $best = -1
    foreach ($t in $task.Triggers) {
        $cls = $t.CimClass.CimClassName
        $rep = -1
        if ($t.Repetition -and $t.Repetition.Interval) { $rep = Convert-IsoDuration $t.Repetition.Interval }
        if ($rep -gt 0) {
            if ($best -lt 0 -or $rep -lt $best) { $best = $rep }
        } elseif ($cls -match 'Daily') { if ($best -lt 0 -or 1440 -lt $best) { $best = 1440 } }
        elseif ($cls -match 'Weekly') { if ($best -lt 0 -or 10080 -lt $best) { $best = 10080 } }
        elseif ($cls -match 'Logon|Boot') { if ($best -lt 0) { $best = -1 } }
    }
    return $best
}

function Decode-Result($code) {
    switch ($code) {
        0 { 'OK' }
        267009 { 'RUNNING' }
        267011 { 'NOT-RUN-YET' }
        267014 { 'TERMINATED' }
        267015 { 'HAS_NOT_RUN' }
        default { ('CODE-' + $code) }
    }
}

$rows = @()
Get-ScheduledTask -TaskPath "\" | Where-Object { $_.TaskName -notmatch '^(Microsoft|OneDrive|Adobe|Google|Edge|NVIDIA|AMD)' } | ForEach-Object {
    $name = $_.TaskName
    if ($ExemptDisabled -contains $name) { return }   # personal + design-state-disabled: out of scope entirely
    $info = $_ | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue
    $exp = Get-ExpectedMinutes $_
    $lastRun = $info.LastRunTime
    $neverRan = ($null -eq $lastRun -or $lastRun.Year -le 1999)
    $ageMin = -1
    if (-not $neverRan) { $ageMin = [Math]::Floor(($now - $lastRun).TotalMinutes) }
    $flag = 'OK'
    if ($_.State -eq 'Disabled') {
        $flag = 'UNEXPECTED-DISABLED'
    } elseif ($neverRan) {
        if ($exp -gt 0) { $flag = 'NEVER-RAN' } else { $flag = 'EVENT-BOUND' }
    } elseif ($exp -gt 0 -and $ageMin -gt (2 * $exp)) {
        $flag = 'STALE'
    }
    $rows += [pscustomobject]@{
        task = $name; state = [string]$_.State
        cadence_min = $(if ($exp -gt 0) { [string]$exp } else { '-' })
        last_run = $(if ($neverRan) { 'never' } else { $lastRun.ToString('MM-dd HH:mm') })
        age_min = $(if ($ageMin -ge 0) { [string]$ageMin } else { '-' })
        result = Decode-Result $info.LastTaskResult
        flag = $flag
    }
}

Write-Output ('TASK HEALTH ' + $now.ToString('yyyy-MM-dd HH:mm') + ' - tasks audited: ' + $rows.Count)
$rows | Sort-Object flag, task | Format-Table -AutoSize | Out-String -Width 200 | Write-Output

$bad = @($rows | Where-Object { $_.flag -ne 'OK' -and $_.flag -ne 'EVENT-BOUND' })
$codes = @($rows | Where-Object { $_.result -like 'CODE-*' })
Write-Output ('SUMMARY unhealthy=' + $bad.Count + ' (of ' + $rows.Count + ')  odd-result-codes=' + $codes.Count)
if ($bad.Count -gt 0) {
    Write-Output ('FLAGS: ' + (($bad | ForEach-Object { ($_.flag + '=' + $_.task) }) -join ', '))
    Write-Output 'Routing: UNEXPECTED-DISABLED/NEVER-RAN/STALE -> night report line + E2; two consecutive nights same flag -> E1 (errors.md circuit-breaker).'
}
if ($codes.Count -gt 0) {
    Write-Output ('RESULT-CODES: ' + (($codes | ForEach-Object { ($_.task + '=' + $_.result) }) -join ', '))
}
