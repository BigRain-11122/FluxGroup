# peer_wake.ps1 - 让活着的机器去唤醒邻居（无需人工到现场）
# 用法: powershell -ExecutionPolicy Bypass -File Tools\fleet\peer_wake.ps1 -Nodes 100.82.175.0,100.123.74.104
param([string[]]$Nodes = @("100.82.175.0","100.123.74.104"))
$ErrorActionPreference = "SilentlyContinue"
$py = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source }
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$agent = Join-Path $root "Tools\fleet\lane_agent.py"
foreach ($ip in $Nodes) {
  $r = @{ node = $ip }
  $r.smb = (Test-NetConnection -ComputerName $ip -Port 445 -InformationLevel Quiet)
  $r.winrm = (Test-NetConnection -ComputerName $ip -Port 5985 -InformationLevel Quiet)
  $r.ssh = (Test-NetConnection -ComputerName $ip -Port 22 -InformationLevel Quiet)
  $r.winrm_start = $false
  if ($r.winrm) {
    try {
      Invoke-Command -ComputerName $ip -ScriptBlock { param($p,$a,$rt) Start-Process -FilePath $p -ArgumentList @($a,"--node","auto","--root",$rt,"--no-fetch") -WindowStyle Hidden } -ArgumentList $py,$agent,$root -ErrorAction Stop
      $r.winrm_start = $true
    } catch { $r.winrm_err = $_.Exception.Message }
  }
  $r.schtasks = ""
  try { $r.schtasks = (schtasks /S $ip /Query /FO LIST 2>&1 | Select-Object -First 1) } catch {}
  [pscustomobject]$r | ConvertTo-Json -Compress
}
