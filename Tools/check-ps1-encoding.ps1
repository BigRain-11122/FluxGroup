# check-ps1-encoding.ps1 —— 查（并可选修）无 BOM 的 .ps1
#
# 为什么（2026-11-18 实测）：
#   中文 Windows 上，PowerShell 5.1 读「无 BOM 的 UTF-8」.ps1 时按系统 ANSI(GBK) 解码。
#   一旦文件里有中文，字节错位会把引号/括号吞掉，解析出假语法错：
#     实测 Tools/fleet/enable-remote-exec.ps1 无 BOM 时 ParseFile 报
#     「参数列表中缺少参量 @ line 75」，加 BOM 后同一份内容 OK。
#   计划任务用 powershell -File 调脚本时同样按此规则读 → 脚本会静默坏掉或根本起不来。
#
# 用法：
#   powershell -NoProfile -ExecutionPolicy Bypass -File check-ps1-encoding.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File check-ps1-encoding.ps1 -Fix
#   powershell -NoProfile -ExecutionPolicy Bypass -File check-ps1-encoding.ps1 -Root Tools -Quiet
#
# 判据：无 BOM 且含非 ASCII 字节 = 风险件；纯 ASCII 的无 BOM 文件不受影响（无需改）。
# 退出码：0 无风险件；1 有风险件（-Fix 时改为修复后的复查结果）

param(
  [string]$Root = ".",
  [switch]$Fix,
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path $Root).Path
$risk = New-Object System.Collections.ArrayList
$fixed = New-Object System.Collections.ArrayList

foreach ($f in (Get-ChildItem -Path $rootPath -Recurse -Filter *.ps1 -File -ErrorAction SilentlyContinue)) {
  if ($f.FullName -match "\\_pub\\|\\_wt-|\\node_modules\\") { continue }
  $b = [IO.File]::ReadAllBytes($f.FullName)
  if ($b.Length -eq 0) { continue }
  $hasBom = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
  if ($hasBom) { continue }
  $nonAscii = $false
  foreach ($x in $b) { if ($x -gt 0x7F) { $nonAscii = $true; break } }
  if (-not $nonAscii) { continue }

  [void]$risk.Add($f.FullName)

  if ($Fix) {
    try {
      $txt = [Text.Encoding]::UTF8.GetString($b)
      [IO.File]::WriteAllText($f.FullName, $txt, (New-Object Text.UTF8Encoding($true)))
      [void]$fixed.Add($f.FullName)
    } catch {
      Write-Host "FAIL 无法修 $($f.FullName): $($_.Exception.Message)"
    }
  }
}

$rel = { param($p) $p.Replace($rootPath, ".") }

if (-not $Quiet) {
  if ($risk.Count -eq 0) {
    Write-Host "OK 无风险件（无 BOM 且含中文的 .ps1 = 0）"
  } else {
    Write-Host "RISK 无 BOM 且含非 ASCII 的 .ps1：$($risk.Count) 个"
    $risk | ForEach-Object { Write-Host ("  - " + (& $rel $_)) }
    if ($Fix) { Write-Host "FIXED $($fixed.Count) 个（已补 BOM，内容未改）" }
    else { Write-Host "修法：加 -Fix 重跑（只补 BOM，不改内容）" }
  }
}

if ($risk.Count -gt 0 -and -not $Fix) { exit 1 }
exit 0
