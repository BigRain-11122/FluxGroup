# 注册游戏子公司轻量循环任务（需管理员一次）
# 原则：S4U + InvisibleRunner，不弹窗；白天让路，任务放在 07:00–08:30。

$ErrorActionPreference = "Stop"
$root = "C:\Users\sjs20\Desktop\FluxGroup"
$python = (Get-Command python).Source
$vbs = Join-Path $root "Tools\InvisibleRunner.vbs"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "需要管理员权限一次：注册 S4U 计划任务。当前未注册。"
    exit 2
}

function Register-Loop($name, $trigger, $scriptArgs) {
    $action = New-ScheduledTaskAction -Execute "wscript.exe" `
        -Argument ("//B //nologo `"$vbs`" `"$python`" " + $scriptArgs) `
        -WorkingDirectory $root
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Write-Host "registered: $name"
}

$dailyRadar = New-ScheduledTaskTrigger -Daily -At "08:10"
$dailyWarden = New-ScheduledTaskTrigger -Daily -At "07:05"
$weeklyRadar = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "08:20"

Register-Loop "Game-RadarDaily" $dailyRadar "Tools\gds\system_radar.py --daily"
Register-Loop "Game-RadarWeekly" $weeklyRadar "Tools\gds\system_radar.py"
Register-Loop "Game-WardenDaily" $dailyWarden "Tools\agents\contract_lint.py"

Write-Host "完成。重任务（构建/闸）待 Fold 工程建好后再注册。"
