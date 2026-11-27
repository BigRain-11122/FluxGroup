# sched-harden-batch.ps1 - 车道任务条件硬化·分批执行器（承 R2.33 事件班 2026-10-26）
# 语义：对 enabled 且非 Microsoft 系的车道任务，补 StartWhenAvailable=True（错过触发恢复后补跑，不再永久丢弃）
#       并把 DisallowStartIfOnBatteries / StopIfGoingOnBatteries 置 False（消 0x800710E0 条件拒绝）。
# 纪律：分批 <=MaxItems/次（禁一次性全量·惊群风险）·每次改前导出 XML 备份·台账记前后值·可逆。
# 用法：
#   -WhatIf            只列清单不动
#   -MaxItems 15       本次处理上限（默认 12）
#   -Lead N            跳过台账里已处理的件（默认全跳过已处理）
#   -Reset             忽略台账（重跑）
# 输出哨兵：HARDEN-RESULT processed=<n> remaining=<m> ledger=<path>
param(
  [int]$MaxItems = 12,
  [switch]$WhatIf,
  [switch]$Reset,
  # 只动机队自有任务；第三方/厂商任务（Adobe/AMD/Office 等）不在射程
  [string[]]$PrefixFilter = @('bm-a-','bm-b-','bm-c-','FluxGroup-','FluxBoard','FluxVerse','HQ-','MiniGame','BigCompute','BigLife','BigStream','BigMoney','BigDomain','BigHouse','Compute','Bma','WT-','MareBackup')
)
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$ledgerPath = Join-Path $root 'media\logs\sched-harden-ledger-20261027.json'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDir = Join-Path $env:TEMP ("sched-batch-backup-" + $stamp)

# 台账
$ledger = @{}
if ((Test-Path $ledgerPath) -and -not $Reset) {
  try {
    $j = Get-Content $ledgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($p in $j.PSObject.Properties) { $ledger[$p.Name] = $p.Value }
  } catch { $ledger = @{} }
}

# 候选：enabled + 非 Microsoft 系 + 缺 StartWhenAvailable 或电池门为真
$cands = @()
foreach ($t in (Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' -and $_.TaskPath -notlike '\Microsoft\*' })) {
  $isFleet = $false
  foreach ($p in $PrefixFilter) { if ($t.TaskName -like ($p + '*')) { $isFleet = $true; break } }
  if (-not $isFleet) { continue }
  $xml = [xml](Export-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath)
  $s = $xml.Task.Settings
  $needSwa = ($s.StartWhenAvailable -ne 'true')
  $needBatt = ($s.DisallowStartIfOnBatteries -eq 'true')
  if (-not ($needSwa -or $needBatt)) { continue }
  if ($ledger.ContainsKey($t.TaskName)) { continue }
  $cands += [pscustomobject]@{
    Name = $t.TaskName; Path = $t.TaskPath
    NeedSWA = $needSwa; NeedBatt = $needBatt
    OldSWA = $s.StartWhenAvailable; OldBatt = $s.DisallowStartIfOnBatteries
  }
}

$batch = $cands | Select-Object -First $MaxItems
"candidates=$($cands.Count) batch=$($batch.Count) ledger=$ledgerPath"
$batch | ForEach-Object { "  - {0} SWA:{1}->true Batt:{2}->false" -f $_.Name, $_.OldSWA, $_.OldBatt }

if ($WhatIf -or $batch.Count -eq 0) {
  "HARDEN-RESULT processed=0 remaining=$($cands.Count) ledger=$ledgerPath"
  exit 0
}

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$done = 0; $fail = @()
foreach ($c in $batch) {
  try {
    $safe = ($c.Name -replace '[\\/:*?"<>|]', '_')
    Export-ScheduledTask -TaskName $c.Name -TaskPath $c.Path | Set-Content -Path (Join-Path $backupDir ($safe + '.xml')) -Encoding UTF8
    $task = Get-ScheduledTask -TaskName $c.Name -TaskPath $c.Path
    $set = $task.Settings
    $set.StartWhenAvailable = $true
    $set.DisallowStartIfOnBatteries = $false
    $set.StopIfGoingOnBatteries = $false
    Set-ScheduledTask -TaskName $c.Name -TaskPath $c.Path -Settings $set | Out-Null
    # 读回验证
    $v = [xml](Export-ScheduledTask -TaskName $c.Name -TaskPath $c.Path)
    if ($v.Task.Settings.StartWhenAvailable -ne 'true') { throw 'readback SWA not true' }
    if ($v.Task.Settings.DisallowStartIfOnBatteries -eq 'true') { throw 'readback Batt still true' }
    $ledger[$c.Name] = @{
      verified = $true; at = (Get-Date -Format 'o'); path = $c.Path
      old = @{ swa = $c.OldSWA; batt = $c.OldBatt }; backup = (Join-Path $backupDir ($safe + '.xml'))
    }
    $done++
  } catch {
    $fail += ($c.Name + ' :: ' + $_.Exception.Message)
  }
}

# 落台账（UTF-8 无 BOM）
$out = $ledger | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText($ledgerPath, $out, (New-Object System.Text.UTF8Encoding($false)))
"BACKUP-DIR $backupDir"
if ($fail.Count -gt 0) { $fail | ForEach-Object { "FAIL $_" } }
$remaining = $cands.Count - $done
# 自停：队列清空即自我停用（不留空转任务）
if ($remaining -le 0) {
  try { Disable-ScheduledTask -TaskName 'HQ-SchedHarden-Batch' -ErrorAction Stop | Out-Null; "SELF-DISABLED HQ-SchedHarden-Batch" } catch {}
}
"HARDEN-RESULT processed=$done remaining=$remaining ledger=$ledgerPath"