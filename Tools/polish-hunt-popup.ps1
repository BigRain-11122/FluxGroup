# 弹窗抓凶手脚本 —— 双击运行 30 秒，把结果发我
# 作用：每 200ms 扫一次进程，发现 WindowsTerminal / conhost / git / UGit 等，
#       立即沿父进程链向上追溯，把完整链条写进日志。
# 输出：C:\Users\sjs20\Desktop\FluxGroup\docs\audits\popup-hunt.log

$ErrorActionPreference = 'SilentlyContinue'
$out = "C:\Users\sjs20\Desktop\FluxGroup\docs\audits\popup-hunt.log"
$dur = 30   # 监视秒数

"=== 弹窗抓凶手  开始 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  监视 ${dur}s ===" |
  Set-Content $out -Encoding UTF8

function Get-Proc([int]$pid_) {
  try { Get-CimInstance Win32_Process -Filter "ProcessId=$pid_" -ErrorAction Stop } catch { $null }
}

$seen = @{}
$end = (Get-Date).AddSeconds($dur)
$watch = 'WindowsTerminal|wt|conhost|git|bash|sh|UGit|node|python|pwsh|powershell|cmd|Code|Codey'

while ((Get-Date) -lt $end) {
  $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
           Where-Object { $_.Name -match $watch }
  foreach ($p in $procs) {
    $key = "$($p.ProcessId)"
    if ($seen.ContainsKey($key)) { continue }
    $seen[$key] = 1
    # 沿父链上溯 5 层
    $chain = @()
    $cur = $p
    for ($i = 0; $i -lt 5 -and $cur; $i++) {
      $cmd = [string]$cur.CommandLine
      if ($cmd.Length -gt 110) { $cmd = $cmd.Substring(0, 110) + '…' }
      $chain += ("    " * $i) + "└ $($cur.Name) (PID=$($cur.ProcessId)) $cmd"
      if (-not $cur.ParentProcessId -or $cur.ParentProcessId -eq 0) { break }
      $cur = Get-Proc ([int]$cur.ParentProcessId)
    }
    $ts = Get-Date -Format 'HH:mm:ss.fff'
    "--- [$ts] 新进程 ---" | Add-Content $out -Encoding UTF8
    $chain | Add-Content $out -Encoding UTF8
  }
  Start-Sleep -Milliseconds 200
}

"=== 结束 $(Get-Date -Format 'HH:mm:ss') ===" | Add-Content $out -Encoding UTF8
Write-Host "完成。日志: $out" -ForegroundColor Green
Write-Host "请把日志内容发给 AI。" -ForegroundColor Yellow
Start-Sleep -Seconds 2
