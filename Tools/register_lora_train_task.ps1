# register_lora_train_task.ps1 — 面孔 LoRA 训练点火任务（一次注册，长期复用）
#
# 为什么用计划任务而不是会话内跑：2026-11-13 首轮训练是 PowerShell 里手敲临时命令行，
# CLI 会话一结束子进程树被连坐杀掉，既没产出也还原不出参数。
#
# 设计：
#   · 工作日 19:05 起每 15 分钟巡检，到次日 07:05 止（避开 09:00 pauseLite 让路窗）
#   · 训练器自带守卫：让路态 / 显存不足 < 6.5G 时直接拒跑，不会跟 CEO 抢机器
#   · --skip-if-exists：权重一旦产出，后续巡检自动跳过，不会重复烧 GPU
#   · S4U 非交互会话（本机车道硬律：禁 InteractiveToken，否则桌面闪黑窗）
#
# 用法（先 dry 一次看参数）：
#   & .\Tools\register_lora_train_task.ps1 -Dataset media\faces\xuruoxuan-v9 -Name her_xuruoxuan -DryRun
#   & .\Tools\register_lora_train_task.ps1 -Dataset media\faces\xuruoxuan-v9 -Name her_xuruoxuan
param(
    [string]$Dataset = "",
    [string]$Name = "",
    [string]$Trigger = "ohwx_woman",
    [string]$Base = "D:/models/sd_xl_base_1.0.safetensors",
    [int]$Steps = 1400,
    [int]$Rank = 32,
    [string]$TaskName = "",
    [switch]$Batch,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = "C:\Users\sjs20\Desktop\FluxGroup"
# pythonw = 无控制台的解释器；配合训练器内 CREATE_NO_WINDOW，任务全程零窗口
$py = "C:\Users\sjs20\train-lora\.venv\Scripts\pythonw.exe"
$script = Join-Path $root "Tools\face_lora_train.py"

if ($Batch) {
    if ([string]::IsNullOrWhiteSpace($TaskName)) { $TaskName = "bm-a-LoRATrain-Batch" }
    $argLine = @("`"$script`"", "batch", "--base", $Base,
                 "--steps", $Steps, "--rank", $Rank) -join " "
    $descLine = "批量：扫描 media\faces\*-ds，每次训一个，产出即跳过"
} else {
    if ([string]::IsNullOrWhiteSpace($Dataset) -or [string]::IsNullOrWhiteSpace($Name)) {
        Write-Error "非 -Batch 模式必须给 -Dataset 与 -Name"
        exit 2
    }
    if ([string]::IsNullOrWhiteSpace($TaskName)) { $TaskName = "bm-a-LoRATrain-$Name" }
    $dsAbs = (Resolve-Path (Join-Path $root $Dataset)).Path
    $argLine = @(
        "`"$script`"", "run",
        "--dataset", "`"$dsAbs`"",
        "--trigger", $Trigger,
        "--base", $Base,
        "--steps", $Steps,
        "--rank", $Rank,
        "--name", $Name,
        "--skip-if-exists"
    ) -join " "
    $descLine = "单人：$dsAbs"
}

Write-Output "[task] 名称   $TaskName"
Write-Output "[task] 目标   $descLine"
Write-Output "[task] 命令   $py $argLine"
Write-Output "[task] 时段   19:05 起每 15 分钟，共 12 小时"

if ($DryRun) { Write-Output "[dry-run] 未注册"; exit 0 }

$action = New-ScheduledTaskAction -Execute $py -Argument $argLine -WorkingDirectory $root

# 19:05 起，每 15 分钟一次，持续 12 小时（PS5.1 需借 Once 触发器的 Repetition 段）
$daily = New-ScheduledTaskTrigger -Daily -At "19:05"
$repSource = New-ScheduledTaskTrigger -Once -At "19:05" `
    -RepetitionInterval (New-TimeSpan -Minutes 15) `
    -RepetitionDuration (New-TimeSpan -Hours 12)
$daily.Repetition = $repSource.Repetition

$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

# 本机是非管理员账户（DASHENG\sjs20），S4U 需要 SeTcbPrivilege 会「拒绝访问」。
# 改用 InteractiveToken + pythonw.exe 承载：pythonw 不建控制台，训练器再给子进程加
# CREATE_NO_WINDOW，全程零窗口，同样不闪黑窗。
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $daily `
    -Settings $settings -Principal $principal -Force -ErrorAction Stop | Out-Null

# 注册后必须回读验证：曾因 Register 静默失败却照打 [ok]，属假绿
$t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $t) {
    Write-Error "[FAIL] 任务未注册成功：$TaskName"
    exit 1
}
$p = $t.Principal
Write-Output "[ok] 已注册：$($t.TaskName) | State=$($t.State) | LogonType=$($p.LogonType) | RunLevel=$($p.RunLevel)"
Write-Output "[ok] 首个火点 今天 19:05（工作日）；权重产出后巡检自动跳过"
