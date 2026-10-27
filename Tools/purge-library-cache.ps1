# STEP A: Tools/purge-library-cache.ps1 — 清理团结/Unity 工程 Library 缓存（占用者自动跳过）
param([switch]$Apply)
$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$log = Join-Path $root 'Logs\purge-library-20261021.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

# 收集所有工程根（含 Library 的目录）
$libs = Get-ChildItem $root -Recurse -Directory -Filter 'Library' -Force |
        Where-Object { Test-Path (Join-Path $_.Parent.FullName 'ProjectSettings') }

# 正在被编辑器占用的工程路径
$busy = @()
Get-CimInstance Win32_Process -Filter "Name='Tuanjie.exe' OR Name='Unity.exe'" | ForEach-Object {
    if ($_.CommandLine -match '-projectPath\s+"?([^"]+?)(?:\s|$)') { $busy += $matches[1].TrimEnd('\').ToLower() }
}

$total = 0; $freed = 0
foreach ($l in $libs) {
    $proj = $l.Parent.FullName.TrimEnd('\')
    $size = (Get-ChildItem $l.FullName -Recurse -File -Force | Measure-Object Length -Sum).Sum
    $total += $size
    $isBusy = $false
    foreach ($b in $busy) { if ($proj.ToLower() -eq $b -or $b.StartsWith($proj.ToLower())) { $isBusy = $true; break } }
    # 二次闸：TryOpen 独占测试（防命令行没带 -projectPath 的实例）
    if (-not $isBusy) {
        try {
            $fs = [IO.File]::Open((Join-Path $proj 'ProjectSettings\ProjectSettings.asset'), 'Open', 'ReadWrite', 'None')
            $fs.Close()
        } catch { $isBusy = $true }
    }
    $line = '{0} | {1,10:N2} GB | {2}' -f $(if ($isBusy) { 'SKIP-BUSY' } elseif ($Apply) { 'DELETED' } elseif ($PSBoundParameters.ContainsKey('Apply')) { 'DELETE' } else { 'WOULD-DELETE' }), ($size/1GB), $proj
    Add-Content -Path $log -Value $line -Encoding UTF8
    Write-Output $line
    if (-not $isBusy) {
        if ($Apply) { Remove-Item -LiteralPath $l.FullName -Recurse -Force; $freed += $size }
    }
}
'{0} libs total={1:N2} GB' -f $libs.Count, ($total/1GB) | Tee-Object -FilePath $log -Append
if ($Apply) { 'FREED={0:N2} GB' -f ($freed/1GB) | Tee-Object -FilePath $log -Append }
