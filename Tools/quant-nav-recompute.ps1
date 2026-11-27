# quant-nav-recompute.ps1 -- independent NAV / metric recomputation (external oversight)
# Recompute a trader's equity curve and headline statistics FROM THE RAW MARKS so no
# reported number has to be trusted. Read-only. ASCII-only body (encoding law).
#
#   equity(t) = cash(t) + sum(market_value(t))
#   daily series = last snapshot of each day -> return, max drawdown, vol, extrapolated Sharpe
#   compared against the firm's reported equity and window metrics
param(
  [string]$Repo = '',
  [string]$Out2 = ''
)
$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Repo)) { $Repo = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($Out2)) { $Out2 = Join-Path $Repo 'results\quant-nav-recompute.json' }

$marksDir = Join-Path $Repo 'results\paper\marks'
if (-not (Test-Path $marksDir)) { Write-Output 'no marks dir'; exit 2 }

# ---- pass 1: last snapshot per (day, trader) ----
$lastOfDay = @{}
foreach ($f in (Get-ChildItem $marksDir -File -Filter 'marks-*.jsonl' | Sort-Object Name)) {
  foreach ($line in [IO.File]::ReadLines($f.FullName)) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    try { $o = $line | ConvertFrom-Json } catch { continue }
    if (-not $o.traders) { continue }
    $day = "$($o.date)"; if ($day -notmatch '^\d{4}-\d{2}-\d{2}') { continue }
    foreach ($t in $o.traders.PSObject.Properties) {
      $name = $t.Name; $tr = $t.Value
      $eq = 0.0; if ($null -ne $tr.equity_mark_cny) { $eq = [double]$tr.equity_mark_cny }
      $cash = 0.0; if ($null -ne $tr.cash_cny) { $cash = [double]$tr.cash_cny }
      $sumMv = 0.0; $up = 0
      foreach ($p in $tr.positions) {
        if ($null -eq $p.market_value_cny) { $up++ }
        else { $sumMv += [double]$p.market_value_cny }
      }
      $lastOfDay["$day|$name"] = [ordered]@{ day=$day; trader=$name; reported=$eq; computed=($cash+$sumMv); unpriced=$up }
    }
  }
}

$byTrader = @{}
foreach ($k in ($lastOfDay.Keys | Sort-Object)) {
  $r = $lastOfDay[$k]
  if (-not $byTrader.ContainsKey($r.trader)) { $byTrader[$r.trader] = New-Object System.Collections.ArrayList }
  [void]$byTrader[$r.trader].Add($r)
}

$traderRows = New-Object System.Collections.ArrayList
foreach ($name in ($byTrader.Keys | Sort-Object)) {
  $series = @($byTrader[$name] | Sort-Object day)
  $eqs  = @($series | ForEach-Object { [double]$_.computed })
  $reps = @($series | ForEach-Object { [double]$_.reported })
  $n = $eqs.Count
  if ($n -eq 0) { continue }
  $first = $eqs[0]; $last = $eqs[$n-1]
  $totRet = if ($first -ne 0) { ($last - $first) / $first } else { 0 }
  $peak = $eqs[0]; $mdd = 0.0
  foreach ($e in $eqs) { if ($e -gt $peak) { $peak = $e }; if ($peak -ne 0) { $dd = ($e - $peak) / $peak; if ($dd -lt $mdd) { $mdd = $dd } } }
  $rets = New-Object System.Collections.ArrayList
  for ($i = 1; $i -lt $n; $i++) { if ($eqs[$i-1] -ne 0) { [void]$rets.Add((($eqs[$i] - $eqs[$i-1]) / $eqs[$i-1])) } }
  $mean = if ($rets.Count -gt 0) { ($rets | Measure-Object -Average).Average } else { 0 }
  $sd = 0.0
  if ($rets.Count -gt 1) {
    $s2 = 0.0; foreach ($x in $rets) { $s2 += [math]::Pow(($x - $mean), 2) }
    $sd = [math]::Sqrt($s2 / ($rets.Count - 1))
  }
  $annVol = $sd * [math]::Sqrt(252)
  $annRet = if ($n -gt 1) { [math]::Pow((1 + $totRet), (252.0 / ($n - 1))) - 1 } else { 0 }
  $sharpe = if ($sd -gt 0) { ($mean / $sd) * [math]::Sqrt(252) } else { 0 }
  $unpDays = @($series | Where-Object { $_.unpriced -gt 0 }).Count
  [void]$traderRows.Add([ordered]@{
    trader = $name
    days_observed = $n
    first_day = $series[0].day
    last_day  = $series[$n-1].day
    total_return_recomputed = [math]::Round($totRet, 6)
    max_drawdown_recomputed = [math]::Round($mdd, 6)
    annualised_vol = [math]::Round($annVol, 6)
    annualised_return_not_meaningful = [math]::Round($annRet, 6)
    sharpe_not_meaningful = [math]::Round($sharpe, 4)
    equity_last_recomputed = [math]::Round($last, 2)
    equity_last_reported   = [math]::Round($reps[$n-1], 2)
    recompute_vs_reported_diff = [math]::Round(($last - $reps[$n-1]), 2)
    unpriced_position_days = $unpDays
  })
}

$report = [ordered]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  probe = 'quant-nav-recompute.ps1 v1.0'
  law_ref = 'docs/audit-charter.md Appendix B2 item 1 (return authenticity)'
  repo = $Repo
  traders = $traderRows
  limits = @(
    'annualised figures are extrapolated from a handful of days and are NOT meaningful; printed only to show how absurd the extrapolation is',
    'unpriced positions (mark 0 / market_value null) make recomputed equity an UNDERSTATEMENT; the affected day count is reported per trader',
    'reports only; this tool issues no verdict'
  )
}
[System.IO.File]::WriteAllText($Out2, ($report | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))

Write-Output ('quant-nav-recompute v1.0  ' + $report.generated_utc)
Write-Output ("{0,-24} {1,5} {2,12} {3,12} {4,12} {5,12} {6,5}" -f 'trader','days','totRet','maxDD','eq_rec','eq_rep','unp')
foreach ($t in $traderRows) {
  Write-Output ("{0,-24} {1,5} {2,12} {3,12} {4,12} {5,12} {6,5}" -f $t.trader, $t.days_observed, $t.total_return_recomputed, $t.max_drawdown_recomputed, $t.equity_last_recomputed, $t.equity_last_reported, $t.unpriced_position_days)
}
Write-Output ('-> ' + $Out2)
