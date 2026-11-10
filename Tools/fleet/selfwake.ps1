# selfwake.ps1 - Windows 自唤醒：执行器掉线自己回来（装一次）
# 管理员 PowerShell:  powershell -ExecutionPolicy Bypass -File Tools\fleet\selfwake.ps1 -Node bm-b
param(
  [Parameter(Mandatory=$true)][string]$Node,
  [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
  [int]$EveryMinutes = 5
)
$ErrorActionPreference = "SilentlyContinue"
$py = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source }
if (-not $py) { Write-Error "python not found"; exit 1 }
$agent = Join-Path $Root "Tools\fleet\lane_agent.py"
$log = Join-Path $env:TEMP ("fleet-lane-" + $Node + ".log")
$taskName = "FluxGroup-FleetLane-" + $Node
Start-Process -FilePath $py -ArgumentList @($agent, "--node", $Node, "--root", $Root, "--no-fetch") -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError ($log + ".err")
$arg = [char]34 + $agent + [char]34 + " --node " + $Node + " --root " + [char]34 + $Root + [char]34 + " --no-fetch"
$action = New-ScheduledTaskAction -Execute $py -Argument $arg
$trigger1 = New-ScheduledTaskTrigger -AtLogOn
$trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $EveryMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($trigger1,$trigger2) -Settings $settings -Force | Out-Null
Write-Output ("selfwake installed: " + $taskName + " (node=" + $Node + ", every " + $EveryMinutes + " min)")
