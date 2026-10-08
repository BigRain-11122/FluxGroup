# silence-enforce.ps1 - Fleet silence root-cure (CEO order 10-08, U060 escalation)
# Idempotent, silent, machine-agnostic. Re-asserts gates (self-heal vs OS resets),
# audits scheduled tasks for console-flash violations, writes compliance JSON.
# Invoked via wscript //B //nologo chain (Tools/silence-enforce.vbs) or directly.
$ErrorActionPreference = 'SilentlyContinue'
$hostName = $env:COMPUTERNAME
$report = [ordered]@{
    host       = $hostName
    ts         = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    toast_gate = $null
    noc_gate   = $null
    task_violations = @()
    quark_updater_killed = $null
}

# 1) Global toast gates (re-assert every run - OS updates may reset them)
$pushKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\PushNotifications'
if (-not (Test-Path $pushKey)) { New-Item $pushKey -Force | Out-Null }
Set-ItemProperty $pushKey -Name ToastEnabled -Value 0 -Type DWord
Set-ItemProperty $pushKey -Name AllowToasts -Value 0 -Type DWord
$report.toast_gate = [int](Get-ItemProperty $pushKey).ToastEnabled

# NOC gate (ximalaya-family; set wherever the vendor key exists - absent = n/a)
$noc = Get-ChildItem 'HKCU:\Software' -Recurse -Depth 5 -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'GLOBAL_SETTING_TOASTS' } | Select-Object -First 2
if ($noc) {
    foreach ($k in $noc) { Set-ItemProperty $k.PSPath -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -Value 0 -Type DWord -ErrorAction SilentlyContinue }
    $report.noc_gate = 'set0'
} else { $report.noc_gate = 'absent' }

# 2) QuarkUpdater popup source (updater only - main app untouched)
foreach ($t in (Get-ScheduledTask -TaskPath '\QuarkUpdaterUser\*' -ErrorAction SilentlyContinue)) {
    if ($t.State -ne 'Disabled') { Disable-ScheduledTask -TaskPath $t.TaskPath -TaskName $t.TaskName | Out-Null }
}
Remove-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'QuarkUpdaterTaskUser1.0.0.21' -ErrorAction SilentlyContinue
$quarkTask = Get-ScheduledTask -TaskPath '\QuarkUpdaterUser\*' -ErrorAction SilentlyContinue
$report.quark_updater_killed = if ($quarkTask) { ($quarkTask.State -eq 'Disabled').ToString() } else { 'no-task' }

# 3) Task audit: non-Microsoft tasks spawning consoles directly (flash-window risk)
$tasks = schtasks /query /fo csv /v 2>$null | ConvertFrom-Csv
foreach ($t in $tasks) {
    $name = $t.TaskName; $act = $t.'Task To Run'
    if (-not $act) { continue }
    if ($name -like '\Microsoft\*') { continue }
    if ($act -match 'powershell\.exe|cmd\.exe|pwsh|\.ps1|\.bat|\.cmd' -and $act -notmatch 'wscript|mshta') {
        $report.task_violations += $name
    }
}

# 4) Write compliance JSON (patrol consumes; fleet status plane)
$outDir = Join-Path $PSScriptRoot '..\.codely-cli\patrol'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$jsonPath = Join-Path $outDir 'silence-audit.json'
[IO.File]::WriteAllText($jsonPath, ($report | ConvertTo-Json -Compress))
