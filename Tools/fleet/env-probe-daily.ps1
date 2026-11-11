# env-probe-daily.ps1 — 每台 Windows 机每日自采 AI 运行环境（CEO 2026-11-11「随时更新」）
#
# 做什么：跑 Tools/fleet/env_probe.py 写 cph4/fleet/env/<station>.json，
#         再把该文件与当前分支同步（有远端就 push，没有就等下一次同步任务带走）。
# 不做什么：不装软件、不改配置、不碰 GPU；只读环境。
#
# 装法（每台 Windows 机执行一次，管理员不需要；用当前用户即可）：
#   $root = "C:\Users\sjs20\Desktop\FluxGroup"      # 改成该机实际仓库路径
#   schtasks /Create /SC DAILY /ST 08:20 /TN "FluxGroup-EnvProbe" `
#       /TR "powershell -NoProfile -ExecutionPolicy Bypass -File `"$root\Tools\fleet\env-probe-daily.ps1`"" /F
# 手动跑一次：
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet\env-probe-daily.ps1
#
param(
    [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$Station  = $env:FLEET_STATION
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

# 找 python：Windows 上没有 python3，实测 rc=9009
$py = $null
foreach ($cand in @("python", "py")) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cand; break }
}
if (-not $py) { Write-Output "ENV-PROBE: 找不到 python，跳过"; exit 2 }

if ($Station) { $env:FLEET_STATION = $Station }

$out = & $py "Tools/fleet/env_probe.py" --write 2>&1
Write-Output $out
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 2) {
    Write-Output "ENV-PROBE: 采集异常 rc=$LASTEXITCODE"
    exit $LASTEXITCODE
}

# 只提交这一份事实文件，不碰别的东西
git add "cph4/fleet/env/*.json" 2>$null
$changed = git status --porcelain "cph4/fleet/env" 2>$null
if ($changed) {
    git -c user.name="fleet-env-probe" -c user.email="probe@local" `
        commit -m "chore(env): $env:COMPUTERNAME 环境探针快照" 2>&1 | Out-Null
    git pull --rebase --autostash 2>&1 | Out-Null
    git push 2>&1 | Out-Null
    Write-Output "ENV-PROBE: 已提交并尝试推送"
} else {
    Write-Output "ENV-PROBE: 环境无变化，不提交"
}
exit 0
