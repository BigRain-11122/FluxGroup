# task-register.ps1 - THE canonical silent task registrar (U060 zero-window law, mechanism-grade)
# CEO order 2026-10-08: "silence by construction, not cleanup after incidents."
# Every task registered through this tool is silent BY STRUCTURE:
#   1. Action is ALWAYS wrapped in the Tools\InvisibleRunner.vbs hidden chain (fleet-proven since 09-20).
#   2. Write-then-readback verification: registration is reported OK only after the
#      hidden chain is confirmed present on the task object.
#   3. There is NO parameter or code path that can produce a visible-console task.
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
    [Parameter(ParameterSetName = 'rewrap')][switch]$RewrapShim
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

Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trg -Description $Description | Out-Null

# write-then-readback law: green only if the hidden chain is confirmed on the live object
$chk = Get-ScheduledTask -TaskName $Name
$chkAct = ($chk.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments }) -join ' '
if ($chkAct -notmatch [regex]::Escape('InvisibleRunner.vbs')) {
    Unregister-ScheduledTask -TaskName $Name -Confirm:$false
    throw 'readback failed: hidden chain missing - registration rolled back'
}

Write-Output ('OK silent task registered: ' + $Name)
Write-Output ('  action : ' + $chkAct)
Write-Output ('  trigger: ' + $Trigger)
