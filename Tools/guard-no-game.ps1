# guard-no-game.ps1 - hard stop for packaged-game launches on the CEO's work machine.
#
# CEO order 2026-10-28 ("不要再自动化运行游戏包") and 2026-10-29 ("我上班时间不要运行测试游戏"):
# on 2026-10-29 16:06 the MiniGame engine loop launched 吸嘟嘟V0.10.18.exe with -autopilot
# during working hours. Disabling the loop is not enough - the loops re-register themselves,
# so the rule needs an enforcer that does not depend on those loops.
#
# Behaviour: weekdays 09:00-19:00 only. Kills any process whose command line points at a
# built game (UnityPlayer / GimmeAll\Build / -autopilot), and disables the known launcher
# tasks if they came back. Outside work hours it does nothing at all.
# Writes one line per action to .codely-cli\tmp\game-guard.log
$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$logDir = Join-Path $root '.codely-cli\tmp'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir 'game-guard.log'
function Note([string]$m) {
    try { ('{0} {1}' -f (Get-Date -Format s), $m) | Add-Content -LiteralPath $log -Encoding UTF8 } catch { }
}

$now = Get-Date
if ($now.DayOfWeek -eq 'Saturday' -or $now.DayOfWeek -eq 'Sunday') { exit 0 }
if ($now.Hour -lt 9 -or $now.Hour -ge 19) { exit 0 }

$pattern = 'UnityPlayer|GimmeAll.*\\Build\\|GimmeAll.*-autopilot|-autopilot.*GimmeAll'
$killed = 0
Get-CimInstance Win32_Process | Where-Object {
    $_.Name -ne 'powershell.exe' -and $_.Name -ne 'WmiPrvSE.exe' -and
    $_.CommandLine -and ($_.CommandLine -match $pattern)
} | ForEach-Object {
    try {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
        $killed++
        Note ('KILL {0} {1}' -f $_.ProcessId, $_.Name)
    } catch { }
}

# The launcher loops re-register themselves; keep them off during the working day.
$watch = @('MiniGameEngineTick', 'MiniGame-PipelineGate', 'MiniGameGateTick', 'MiniGameAuditTick', 'MiniGameTickWatchdog')
foreach ($t in $watch) {
    $task = Get-ScheduledTask -TaskName $t
    if ($task -and $task.State -ne 'Disabled') {
        try {
            Stop-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
            schtasks /change /tn $t /disable | Out-Null
            Note ('DISABLED-TASK {0} (was {1})' -f $t, $task.State)
        } catch { }
    }
}
exit 0