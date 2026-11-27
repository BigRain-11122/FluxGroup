# Fold-001 构建入口（骨架；工程未建时拒绝，不假构建）
param(
    [string]$ProjectRoot = "cph4\fleet\game-v2\projects\fold-001\game",
    [string]$OutDir = "cph4\fleet\game-v2\projects\fold-001\Build\Win64",
    [string]$Editor = "C:\Program Files\Tuanjie\Hub\Editor\2022.3.62t17\Editor\Tuanjie.exe"
)

$ErrorActionPreference = "Stop"
$root = "C:\Users\sjs20\Desktop\FluxGroup"
$proj = Join-Path $root $ProjectRoot
$out = Join-Path $root $OutDir

if (-not (Test-Path (Join-Path $proj "ProjectSettings\ProjectVersion.txt"))) {
    Write-Host "NOT-READY: 没有 Unity/团结工程（缺 ProjectSettings/ProjectVersion.txt）：$proj"
    exit 3
}
if (-not (Test-Path $Editor)) {
    Write-Host "NOT-READY: 编辑器不存在：$Editor"
    exit 3
}

$logDir = Join-Path $proj "Logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
New-Item -ItemType Directory -Force $out | Out-Null
$log = Join-Path $logDir "build_win64.log"

$args = @(
    "-batchmode", "-quit", "-nographics",
    "-projectPath", $proj,
    "-executeMethod", "FoldSpike.Editor.FoldBuild.BuildWin64",
    "-logFile", $log
)
$p = Start-Process -FilePath $Editor -ArgumentList $args -PassThru -WindowStyle Hidden
if (-not $p.WaitForExit(900000)) {
    Write-Host "TIMEOUT: 构建超过 900 秒"
    exit 4
}
if ($p.ExitCode -ne 0) {
    Write-Host "FAIL: exit=$($p.ExitCode) log=$log"
    exit 1
}
Write-Host "OK: $out log=$log"
