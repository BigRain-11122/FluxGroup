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
# 双闸律（10-06 C 机配方）：①ToastEnabled ②NOC_GLOBAL_SETTING_TOASTS_ENABLED=系统勿扰总闸
# （12:2x 复发实锚：bm-a 曾只设①漏②=弹窗复发根源——两道全无条件写）
$pushKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\PushNotifications'
if (-not (Test-Path $pushKey)) { New-Item $pushKey -Force | Out-Null }
New-ItemProperty $pushKey -Name ToastEnabled -Value 0 -PropertyType DWord -Force | Out-Null
New-ItemProperty $pushKey -Name AllowToasts -Value 0 -PropertyType DWord -Force | Out-Null
$report.toast_gate = [int](Get-ItemProperty $pushKey).ToastEnabled

$nocKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings'
if (-not (Test-Path $nocKey)) { New-Item $nocKey -Force | Out-Null }
New-ItemProperty $nocKey -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -Value 0 -PropertyType DWord -Force | Out-Null
$report.noc_gate = [int](Get-ItemProperty $nocKey).NOC_GLOBAL_SETTING_TOASTS_ENABLED

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
