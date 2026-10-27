# quant-oversight-digest.ps1 -- 量化研究轨道监督·机器摘要（外审专用·省 token）
# 由 Windows 计划任务周期运行；只写一个极短摘要文件，外审每轮只读这一行。
# 监督项对应 D-20260930-41 §6 五机制 + 跨起点 §1.3 + 数据缺口 §3。
# ASCII-only body (encoding law).
param(
  [string]$Root = '',
  [string]$Out  = ''
)
$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = Split-Path -Parent $PSScriptRoot }
if ([string]::IsNullOrWhiteSpace($Out))  { $Out  = Join-Path $Root 'docs\audits\oversight-digest.txt' }

$log = Join-Path $Root 'docs\audits\oversight-digest.jsonl'
$now = Get-Date
$ts  = $now.ToString('yyyy-MM-ddTHH:mm:ss')

# ---- A 引用率核查：新预注册中"引用机构结论"的比例 ----
$preregDir = Join-Path $Root 'quant\bigmoney\research'
$recent = @()
if (Test-Path $preregDir) {
  $recent = @(Get-ChildItem $preregDir -File -Filter '*PREREG*.md' -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt $now.AddDays(-7) })
}
$citedN = 0
foreach ($f in $recent) {
  $t = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
  if ($t -match '申万|东方证券|私募排排|S&P|AQR|Harvey|Lopez|引用|机构') { $citedN++ }
}
$citeRate = if ($recent.Count -gt 0) { [math]::Round($citedN / $recent.Count * 100, 0) } else { 0 }

# ---- B 单起点检查：新交付件是否含跨起点/滚动窗口 ----
$delivDir = Join-Path $Root 'quant\bigmoney\research'
$singleStartRisk = 0
foreach ($f in $recent) {
  $t = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
  if ($t -match '年化|CAGR|Sharpe' -and $t -notmatch '跨起点|滚动|全起点|rolling|cross.start') { $singleStartRisk++ }
}

# ---- C 试验量闸：账本 N 的 30 日增量 ----
$ledger = Get-ChildItem (Join-Path $Root 'quant\bigmoney\results') -File -Filter 'gate_attrition.json' -ErrorAction SilentlyContinue | Select-Object -First 1
$nTrials = 0
if ($ledger) {
  $t = Get-Content $ledger.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
  $m = [regex]::Match($t, '"batch_trials"\s*:\s*(\d+)')
  if (-not $m.Success) { $m = [regex]::Match($t, '"n_eff"\s*:\s*(\d+)') }
  if ($m.Success) { $nTrials = [int]$m.Groups[1].Value }
}

# ---- D 否证清单闸：新预注册是否命中九方向禁开清单 ----
$banned = '横截面动量|横截面反转|网格|水温|站上MA20|确认型|小市值|低价因子|缓冲降换手'
$bannedHit = 0
foreach ($f in $recent) {
  $t = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
  if ($t -match $banned) { $bannedHit++ }
}

# ---- E 数据缺口台账（§3 六项）----
$gaps = @()
$chk = @{
  'PE/PB/ROE/股息率' = 'quant\bigmoney\data\fundamental\valuation.csv'
  '退市股行情'       = 'quant\bigmoney\data\fundamental\delisted'
  '逐日ST状态'       = 'quant\bigmoney\data\fundamental\st_history.csv'
  '指数成分史'       = 'quant\bigmoney\data\basic\index_membership.csv'
  '2016前ETF日线'    = 'quant\bigmoney\data\daily_pre2016'
  '真实成交回报'     = 'quant\bigmoney\results\fills'
}
foreach ($k in $chk.Keys) {
  if (-not (Test-Path (Join-Path $Root $chk[$k]))) { $gaps += $k }
}

# ---- 跨起点复核状态 ----
$xsFile = Join-Path $Root 'docs\audits\cross-start-validation-20260930.txt'
$xsDone = Test-Path $xsFile

# ---- 汇总（一行 + JSONL 追加）----
$sev = 'OK'
if ($singleStartRisk -gt 0 -or $bannedHit -gt 0) { $sev = 'ATTENTION' }
$line = "$ts | SEV=$sev | prereg7d=$($recent.Count) citeRate=${citeRate}% | singleStartRisk=$singleStartRisk | bannedHit=$bannedHit | gaps=$($gaps.Count)/6 | xstart=$xsDone"

Set-Content -Path $Out -Value $line -Encoding UTF8
$obj = [ordered]@{ ts=$ts; sev=$sev; prereg_7d=$recent.Count; cite_rate_pct=$citeRate
  single_start_risk=$singleStartRisk; banned_hit=$bannedHit; gaps=$gaps; xstart_done=$xsDone }
($obj | ConvertTo-Json -Compress) | Add-Content -Path $log -Encoding UTF8
Write-Output $line
