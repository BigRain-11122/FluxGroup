# 注册「地产线每日拉取」计划任务
# 用 pythonw（无控制台）运行，避免在 CEO 桌面闪黑窗。
# 22:10 执行：过了 CEO 让路令的 19:00 resume 时点，也过了当日成交结算。
# 卸载：schtasks /Delete /TN "FluxGroup-HouseDailyPull" /F

$ErrorActionPreference = 'Stop'
$root   = 'C:\Users\sjs20\Desktop\FluxGroup'
$script = Join-Path $root 'Tools\house\daily_pull.py'
$log    = Join-Path $root 'house\realestate\logs'

if (-not (Test-Path $script)) { throw "找不到脚本 $script" }
New-Item -ItemType Directory -Force -Path $log | Out-Null

# 优先用 pythonw（GUI 子系统，不建控制台窗口）
$py = (Get-Command python -ErrorAction Stop).Source
$pyw = Join-Path (Split-Path $py) 'pythonw.exe'
if (-not (Test-Path $pyw)) {
    Write-Warning "找不到 pythonw.exe，退回 python.exe（会闪窗）"
    $pyw = $py
}

$taskName = 'FluxGroup-HouseDailyPull'
$action   = "`"$pyw`" `"$script`""

Write-Output "pythonw : $pyw"
Write-Output "script  : $script"
Write-Output "action  : $action"

& schtasks.exe /Create /TN $taskName /TR $action /SC DAILY /ST 22:10 /F | Out-Host
if ($LASTEXITCODE -ne 0) { throw "schtasks 创建失败 rc=$LASTEXITCODE" }

# 回读验证（不能只看创建成功）
$q = & schtasks.exe /Query /TN $taskName /FO LIST
$q | Out-Host
$ok = ($q -match 'Ready|就绪|正在运行|Running') -and ($q -match '22:10')
Write-Output ("`n[VERIFY] " + $(if ($ok) { 'PASS 已就绪且时点 22:10' } else { 'CHECK 请人工确认状态与时间' }))
