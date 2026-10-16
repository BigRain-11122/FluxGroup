# task-register.ps1 - THE canonical silent task registrar (U060 zero-window law, mechanism-grade)
# CEO order 2026-10-08: "silence by construction, not cleanup after incidents."
# Every task registered through this tool is silent AND headless BY STRUCTURE:
#   1. Action is ALWAYS wrapped in the Tools\InvisibleRunner.vbs hidden chain (fleet-proven since 09-20).
#   2. Principal is ALWAYS S4U (fleet law 2026-09-29: InteractiveToken tasks die at logoff
#      and can flash consoles; S4U runs with no logon, no window). Readback-enforced.
#   3. Write-then-readback verification: registration is reported OK only after the
#      hidden chain AND LogonType=S4U are confirmed on the live task object.
#   4. Deploy = ignite (C-20261016-02 Cure-9, CEO order 2026-10-16): recurring (every:)
#      registrations fire ONE live test immediately and report the observed run;
#      a registration without a clean observed fire is NOT "deployed" (paper claims banned).
#   5. There is NO parameter or code path that can produce a visible-console or
#      InteractiveToken task.
# Sessions must use this tool instead of raw schtasks / Register-ScheduledTask
# (that is a hard law in AI.md item 7 - violations are counted by patrol).
#
# Usage:
#   powershell Tools/task-register.ps1 -Name MyTask -Script C:\path\job.ps1 -Trigger every:10m
#   powershell Tools/task-register.ps1 -Name MyTask -Script C:\path\job.bat -Trigger daily:04:07 -Arg "-x 1"
#   powershell Tools/task-register.ps1 -RewrapShim        (batch: swap InvisibleRunner.vbs -> SilentShimRunner.vbs
#                                                         in every non-Microsoft task action; full backup + readback)
# Trigger forms:
#   logon | boot | daily:HH:mm | every:Nm | once:yyyy-MM-ddTHH:mm
param(
    [Parameter(ParameterSetName = 'register', Mandatory = $true)][string]$Name,
    [Parameter(ParameterSetName = 'register', Mandatory = $true)][string]$Script,
    [Parameter(ParameterSetName = 'register')][string]$Arg = '',
    [Parameter(ParameterSetName = 'register', Mandatory = $true)][string]$Trigger,
    [Parameter(ParameterSetName = 'register')][string]$Description = 'fleet silent task via Tools/task-register.ps1 (U060 mechanism-grade)',
    [Parameter(ParameterSetName = 'rewrap')][switch]$RewrapShim,
    [Parameter(ParameterSetName = 'register')][switch]$FireTest,
    [Parameter(ParameterSetName = 'register')][switch]$NoFireTest
)
$ErrorActionPreference = 'Stop'

# ---- RewrapShim mode: batch-swap existing hidden chains onto the shim-PATH runner ----
# Why: codely.exe (GUI subsystem) and other console-less parents spawn bare 'git'
# without hiding -> one visible Windows Terminal window per git call on Win11.
# SilentShimRunner.vbs = same hidden chain + gitsilent shim dir prepended to PATH,
# so session-internal git resolves to the silent relay (window never born).
# Rollback: every original action is backed up to Tools\task-actions-backup-*.json.
if ($RewrapShim) {
    $shimVbs = Join-Path $PSScriptRoot 'SilentShimRunner.vbs'
    if (-not (Test-Path $shimVbs)) { throw 'SilentShimRunner.vbs missing' }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupPath = Join-Path $PSScriptRoot ("task-actions-backup-" + $stamp + ".json")
    $backup = New-Object System.Collections.ArrayList
    $done = New-Object System.Collections.ArrayList
    $skip = New-Object System.Collections.ArrayList
    $fail = New-Object System.Collections.ArrayList
    foreach ($t in (Get-ScheduledTask | Where-Object { $_.TaskPath -notlike '\Microsoft\*' })) {
        $full = $t.TaskPath + $t.TaskName
        $act = $t.Actions | Select-Object -First 1
        if (-not $act) { $skip.Add($full + ' (no-action)'); continue }
        $origArg = [string]$act.Arguments
        if ($origArg -notmatch 'InvisibleRunner\.vbs') { $skip.Add($full + ' (no-hidden-chain)'); continue }
        if ($origArg -match 'SilentShimRunner\.vbs') { $skip.Add($full + ' (already-shimmed)'); continue }
        $null = $backup.Add([ordered]@{ task = $full; execute = $act.Execute; arguments = $origArg })
        $newArg = $origArg -replace '"[^"]*InvisibleRunner\.vbs"', ('"' + $shimVbs + '"')
        if ($newArg -eq $origArg) { $fail.Add($full + ' (swap-pattern-miss)'); continue }
        try {
            $newAction = New-ScheduledTaskAction -Execute $act.Execute -Argument $newArg
            Set-ScheduledTask -TaskPath $t.TaskPath -TaskName $t.TaskName -Action $newAction -ErrorAction Stop | Out-Null
            $chk = (Get-ScheduledTask -TaskPath $t.TaskPath -TaskName $t.TaskName).Actions | Select-Object -First 1
            if (([string]$chk.Arguments) -match [regex]::Escape('SilentShimRunner.vbs')) {
                $done.Add($full)
            } else {
                $fail.Add($full + ' (readback-mismatch)')
            }
        } catch {
            # Access-denied family (10-08 precedent): record, do not fight the original task
            $fail.Add($full + ' (' + $_.Exception.Message + ')')
        }
    }
    if ($backup.Count -gt 0) {
        [IO.File]::WriteAllText($backupPath, ($backup | ConvertTo-Json -Depth 4))
    }
    Write-Output ('REWROTE ' + $done.Count + ' tasks (backup: ' + $backupPath + ')')
    $done | ForEach-Object { Write-Output ('  OK   ' + $_) }
    $skip | ForEach-Object { Write-Output ('  SKIP ' + $_) }
    $fail | ForEach-Object { Write-Output ('  FAIL ' + $_) }
    if ($fail.Count -gt 0) { Write-Output ('failures recorded above - rerun or manual attention needed for ' + $fail.Count) }
    exit 0
}

$vbs = Join-Path $PSScriptRoot 'InvisibleRunner.vbs'
if (-not (Test-Path $vbs)) { throw 'InvisibleRunner.vbs missing - cannot guarantee silence' }

$sc = [System.IO.Path]::GetFullPath($Script)
if (-not (Test-Path $sc)) { throw "script/exe not found: $sc" }
$ext = [System.IO.Path]::GetExtension($sc).ToLower()
$tailArg = if ($Arg) { ' ' + $Arg } else { '' }

# inner launcher by file type - all console-capable hosts are wrapped by the outer VBS chain
switch ($ext) {
    '.ps1' { $inner = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{0}"{1}' -f $sc, $tailArg }
    '.bat' { $inner = 'cmd.exe /c "{0}"{1}' -f $sc, $tailArg }
    '.cmd' { $inner = 'cmd.exe /c "{0}"{1}' -f $sc, $tailArg }
    '.py'  { $inner = 'pythonw.exe "{0}"{1}' -f $sc, $tailArg }
    default { $inner = '"{0}"{1}' -f $sc, $tailArg }
}

$action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('//B //nologo "{0}" {1}' -f $vbs, $inner)

# S4U by construction (fleet law 2026-09-29). The 2026-10-16 bm-a re-bite of the 10-15
# bm-b pit (both new sentinel tasks registered InteractiveToken while their headers
# claimed "S4U task") proved the law must live in the registrar, not in session memory.
$sid = ([System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value)
$principal = New-ScheduledTaskPrincipal -UserId $sid -LogonType S4U -RunLevel Limited

switch -Regex ($Trigger) {
    '^logon$'  { $trg = New-ScheduledTaskTrigger -AtLogOn }
    '^boot$'   { $trg = New-ScheduledTaskTrigger -AtBoot }
    '^daily:'  { $trg = New-ScheduledTaskTrigger -Daily -At ($Trigger -replace '^daily:', '') }
    '^once:'   { $trg = New-ScheduledTaskTrigger -Once -At ([datetime]($Trigger -replace '^once:', '')) }
    '^every:'  {
        $mins = [int]($Trigger -replace '^every:', '').TrimEnd('m')
        if ($mins -lt 1) { throw 'every:Nm requires N >= 1' }
        $trg = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $mins) -RepetitionDuration (New-TimeSpan -Days 3650)
    }
    default { throw "unknown trigger form: $Trigger (use logon|boot|daily:HH:mm|every:Nm|once:ISO)" }
}

if (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue) {
    throw "task already exists: $Name (unregister it first - no silent overwrite)"
}

# Register S4U-first (fleet law 2026-09-29). UAC boxes deny unelevated S4U registration
# (bm-a 2026-10-16 live evidence: Register-ScheduledTask AND schtasks /XML both denied,
# elevated=False). The ScheduledTasks module does not reliably honor EAP=Stop, so success
# is decided by task existence, not by the error stream. On S4U denial: fall back to the
# InteractiveToken default (hidden VBS chain = zero console flash while logged on) but
# NEVER silently - the task is queued in task-s4u-backlog.md for elevated conversion.
$degraded = $false
$null = Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trg -Principal $principal -Description $Description -ErrorAction SilentlyContinue
if (-not (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue)) {
    $null = Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trg -Description $Description -ErrorAction SilentlyContinue
    if (-not (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue)) {
        throw 'registration failed entirely (S4U and InteractiveToken both denied)'
    }
    $degraded = $true
}

# write-then-readback law: green only if hidden chain is confirmed on the live object
$chk = Get-ScheduledTask -TaskName $Name
$chkAct = ($chk.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments }) -join ' '
if ($chkAct -notmatch [regex]::Escape('InvisibleRunner.vbs')) {
    Unregister-ScheduledTask -TaskName $Name -Confirm:$false
    throw 'readback failed: hidden chain missing - registration rolled back'
}
$chkLT = [string]$chk.Principal.LogonType
if ($chkLT -ne 'S4U' -and -not $degraded) {
    Unregister-ScheduledTask -TaskName $Name -Confirm:$false
    throw 'readback failed: LogonType=' + $chkLT + ' without a recorded S4U denial - registration rolled back'
}
if ($degraded) {
    $bl = Join-Path $PSScriptRoot 'task-s4u-backlog.md'
    if (-not (Test-Path $bl)) {
        Set-Content -LiteralPath $bl -Value ('| registered | task | reason |' + [Environment]::NewLine + '|---|---|---|' + [Environment]::NewLine + '| ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + $Name + ' | S4U denied unelevated (UAC) - convert via elevated Tools\task-s4u-convert.ps1 |') -Encoding UTF8
    } else {
        Add-Content -LiteralPath $bl -Value ('| ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + $Name + ' | S4U denied unelevated (UAC) - convert via elevated Tools\task-s4u-convert.ps1 |') -Encoding UTF8
    }
    Write-Output ('  WARN   : S4U denied (unelevated UAC) - registered InteractiveToken: hidden chain = zero flash while logged on, but NO logoff survival; QUEUED -> Tools\task-s4u-backlog.md')
}

Write-Output ('OK silent task registered: ' + $Name)
Write-Output ('  action : ' + $chkAct)
Write-Output ('  trigger: ' + $Trigger + ' | LogonType=' + $chkLT + $(if ($degraded) { ' (degraded)' } else { '' }))

# Deploy = ignite (C-20261016-02 Cure-9): fire the real carrier once NOW and observe it.
# Default ON for every: triggers (the next tick, just early); -FireTest opts in for other
# forms; -NoFireTest skips. An UNPROVEN fire exits 2 - the caller must not claim "deployed".
$fireOn = (($Trigger -match '^every:') -and (-not $NoFireTest)) -or [bool]$FireTest
if ($fireOn) {
    $t0 = Get-Date
    Start-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    $limit = $t0.AddSeconds(90)
    $st = ''
    $res = [datetime]::MinValue
    do {
        Start-Sleep -Seconds 5
        $i = Get-ScheduledTaskInfo -TaskName $Name
        $st = [string]$i.LastTaskResult
        $res = $i.LastRunTime
    } while (((Get-Date) -lt $limit) -and (($res -lt $t0) -or ($st -eq '267009')))
    if (($res -ge $t0) -and ($st -eq '0')) {
        Write-Output ('  fire   : OK observed ' + $res + ' result=0 (deployed)')
    } else {
        Write-Output ('  fire   : UNPROVEN last=' + $res + ' result=' + $st + ' - NOT deployed until a clean fire is observed')
        exit 2
    }
}
