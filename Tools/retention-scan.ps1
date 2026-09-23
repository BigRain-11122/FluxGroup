# Group retention probe v0.1 - resource watermark scan (cph4/retention.md).
# READ-ONLY measurement of group tree hotspots: sizes, growth vs last run,
# watermark checks (age/size per retention.md sec 4 table). Writes local
# snapshot JSON under .codely-cli\retention\ (gitignored - the report itself
# must not bloat git) and prints a report for the weekly evolution round.
# ASCII-only (encoding law). THIS TOOL NEVER DELETES - measure only,
# except rotating its own snapshot files (keep last 12).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File Tools\retention-scan.ps1

param([string]$Root)

$ErrorActionPreference = 'SilentlyContinue'
if(-not $Root){ $Root = Split-Path -Parent $PSScriptRoot }   # -> FluxGroup root
$outDir = Join-Path $Root '.codely-cli\retention'
if(-not (Test-Path $outDir)){ New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

# hotspot table: relpath + retention tier (cph4/retention.md sec 1/2)
$targets = @(
  @{p='cph4';    t='R1'},
  @{p='docs';    t='R1'},
  @{p='.codely'; t='R3'},
  @{p='.codely-cli'; t='R3'},
  @{p='gaming\MiniGame'; t='MIX'},
  @{p='gaming\MiniGame\Art Assets'; t='R2'},
  @{p='gaming\MiniGame\Font Assets'; t='R2'},
  @{p='gaming\MiniGame\projects'; t='MIX'},
  @{p='gaming\MiniGame\Software'; t='R3'},
  @{p='gaming\MiniGame\.git'; t='R1'},
  @{p='gaming\MiniGame\.codely-cli'; t='R3'},
  @{p='gaming\FluxVerse'; t='MIX'},
  @{p='gaming\FluxVerse\world'; t='R1/R3'},
  @{p='gaming\FluxVerse\logs'; t='R3'},
  @{p='gaming\FluxVerse\.codely-cli'; t='R3'},
  @{p='media'; t='MIX'},
  @{p='quant\bigmoney'; t='MIX'},
  @{p='quant\bigmoney\Money02'; t='R2-inflight'},
  @{p='quant\bigmoney\Money0923'; t='R2'},
  @{p='quant\bigmoney\.git'; t='R1'},
  @{p='quant\bigmoney\.codely-cli'; t='R3'},
  @{p='quant\bigmoney\data'; t='R1'}
)

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$prev = $null
$prevPath = Join-Path $outDir 'latest.json'
if(Test-Path $prevPath){ $prev = Get-Content $prevPath -Raw | ConvertFrom-Json }

$rows = @()
foreach($t in $targets){
  $full = Join-Path $Root $t.p
  if(-not (Test-Path $full)){ continue }
  $m = Get-ChildItem -Recurse -Force -File $full | Measure-Object -Property Length -Sum
  $mb = [math]::Round(($m.Sum/1MB),1)
  $rows += [ordered]@{ path=$t.p; tier=$t.t; mb=$mb; files=$m.Count }
}

# ---- watermark checks (thresholds mirror cph4/retention.md sec 4 table) ----
$flags = @()
$now = Get-Date
$limit30 = $now.AddDays(-30)
$limit14 = $now.AddDays(-14)

# auto-saves: age per repo (30d watermark)
$asDirs = @('.codely-cli\auto-saves','gaming\MiniGame\.codely-cli\auto-saves','gaming\FluxVerse\.codely-cli\auto-saves','quant\bigmoney\.codely-cli\auto-saves','media\BigStream\.codely-cli\auto-saves')
foreach($d in $asDirs){
  $full = Join-Path $Root $d
  if(Test-Path $full){
    $fs = @(Get-ChildItem -Recurse -Force -File $full)
    $old = @($fs | Where-Object { $_.LastWriteTime -lt $limit30 })
    if($old.Count -gt 0){ $flags += ('AUTO_SAVES_OLD: {0}/{1} files older than 30d in {2}' -f $old.Count, $fs.Count, $d) }
  }
}

# clipboard (30d watermark)
$clip = Join-Path $Root '.codely\clipboard'
if(Test-Path $clip){
  $old = @(Get-ChildItem -Recurse -Force -File $clip | Where-Object { $_.LastWriteTime -lt $limit30 })
  if($old.Count -gt 0){ $flags += ('CLIPBOARD_OLD: {0} files older than 30d' -f $old.Count) }
}

# world jsonl (100MB watermark -> rotate)
$wdir = Join-Path $Root 'gaming\FluxVerse\world'
if(Test-Path $wdir){
  Get-ChildItem -Force -File $wdir -Filter '*.jsonl' | ForEach-Object {
    $mb = [math]::Round($_.Length/1MB,2)
    if($mb -gt 100){ $flags += ('JSONL_BIG: world\{0} = {1} MB (watermark 100MB -> rotate)' -f $_.Name, $mb) }
  }
}

# old logs (14d watermark, FluxVerse)
$lDir = Join-Path $Root 'gaming\FluxVerse\logs'
if(Test-Path $lDir){
  $old = @(Get-ChildItem -Recurse -Force -File $lDir | Where-Object { $_.LastWriteTime -lt $limit14 })
  if($old.Count -gt 0){ $flags += ('LOGS_OLD: {0} log files older than 14d (FluxVerse\logs)' -f $old.Count) }
}

# git size (2GB watermark -> git gc, never delete history)
foreach($r in $rows){ if($r.path -like '*.git' -and $r.mb -gt 2048){ $flags += ('GIT_BIG: {0} = {1} MB (watermark 2GB -> git gc)' -f $r.path, $r.mb) } }

# disk free (20GB watermark -> P0-Resource)
$drvLetter = $Root.Substring(0,1)
$drv = Get-PSDrive -Name $drvLetter
$freeGB = [math]::Round($drv.Free/1GB,1)
if($freeGB -lt 20){ $flags += ('DISK_LOW: drive {0}: free {1} GB (<20GB -> P0-Resource)' -f $drvLetter, $freeGB) }

$sw.Stop()

# ---- report ----
$report = @()
$report += ('# Retention scan ' + $stamp + '  (elapsed ' + [math]::Round($sw.Elapsed.TotalSeconds,0) + 's, host ' + $env:COMPUTERNAME + ')')
$report += ''
$report += 'path | tier | MB | files | deltaMB_vs_last'
foreach($r in $rows){
  $d = '-'
  if($prev){
    $pv = @($prev.hotspots | Where-Object { $_.path -eq $r.path })
    if($pv.Count -gt 0){ $d = [string]([math]::Round(($r.mb - $pv[0].mb),1)) }
  }
  $report += ('{0} | {1} | {2} | {3} | {4}' -f $r.path, $r.tier, $r.mb, $r.files, $d)
}
$report += ''
$report += ('drive {0}: free {1} GB' -f $drvLetter, $freeGB)
if($flags.Count -gt 0){
  $report += ''
  $report += 'WATERMARK FLAGS:'
  foreach($f in $flags){ $report += ('- ' + $f) }
} else {
  $report += ''
  $report += 'WATERMARK FLAGS: none'
}

# persist snapshot (ascii; latest.json drives next-run delta)
$snap = [ordered]@{ stamp=$stamp; host=$env:COMPUTERNAME; drive_free_gb=$freeGB; hotspots=$rows; flags=$flags }
$json = $snap | ConvertTo-Json -Depth 4
$json | Out-File -FilePath (Join-Path $outDir ('snapshot-' + $stamp + '.json')) -Encoding ascii
$json | Out-File -FilePath $prevPath -Encoding ascii
# rotate own snapshots: keep last 12
Get-ChildItem $outDir -Filter 'snapshot-*.json' | Sort-Object Name -Descending | Select-Object -Skip 12 | Remove-Item -Force

foreach($line in $report){ Write-Output $line }
