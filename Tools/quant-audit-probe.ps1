# quant-audit-probe.ps1 -- independent quant audit probe (external expert, 2026-09-30)
# READ-ONLY over a quant repo's paper-trading artifacts. Recomputes what the firm
# reports and flags inconsistencies a human CEO cannot see.
#
# Checks (all machine-verifiable):
#   Q1 equity consistency : reported equity_mark_cny vs cash + sum(market_value_cny)
#   Q2 unmarked weight    : positions marked=true but mark=0 / market_value null,
#                           and the capital weight they silently remove from equity
#   Q3 annualization floor: annualized metrics computed on fewer bars than a sane floor
#   Q4 snapshot inflation : intraday marks written with no material change
#   Q5 zero-activity      : registered traders with no closed trades and no fills
#
# ASCII-only body per the group encoding law. Output: one UTF-8 JSON artifact.
param(
  [string]$Repo = '',
  [string]$Out  = '',
  [int]$MinBarsForAnnual = 20,     # below this, annualized figures are meaningless
  [double]$MaterialMove = 0.0005   # 5bp equity change threshold for "material"
)
$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Repo)) { $Repo = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($Out))  { $Out  = Join-Path $Repo 'results\quant-audit-probe.json' }

$marksDir = Join-Path $Repo 'results\paper\marks'
$paperDir = Join-Path $Repo 'results\paper'
$findings = @()
$flags = [ordered]@{ Q1_equity_mismatch = 0; Q2_unmarked_positions = 0; Q2_unmarked_weight_pct = 0.0; Q3_annualization_below_floor = 0; Q4_redundant_snapshots = 0; Q5_zero_activity_traders = 0 }

# ---------- Q1 / Q2 : equity consistency and unmarked weight ----------
$snapTotal = 0
$snapByDay = @{}
$prevEquity = @{}
$redundant = 0
$unmarkedWeightSum = @()
$mismatchRows = @()

if (Test-Path $marksDir) {
  $files = Get-ChildItem $marksDir -File -Filter 'marks-*.jsonl' | Sort-Object Name
  foreach ($f in $files) {
    foreach ($line in [IO.File]::ReadLines($f.FullName)) {
      if ([string]::IsNullOrWhiteSpace($line)) { continue }
      try { $o = $line | ConvertFrom-Json } catch { continue }
      if (-not $o.traders) { continue }
      $snapTotal++
      $day = "$($o.date)"
      if (-not $snapByDay.ContainsKey($day)) { $snapByDay[$day] = 0 }
      $snapByDay[$day]++

      foreach ($t in $o.traders.PSObject.Properties) {
        $name = $t.Name; $tr = $t.Value
        $cash = [double]$tr.cash_cny
        $rep  = [double]$tr.equity_mark_cny
        $sumMv = 0.0; $unmarked = 0; $unmarkedMvEstimate = 0.0
        foreach ($p in $tr.positions) {
          $mv = $p.market_value_cny
          if ($null -eq $mv) {
            $unmarked++
            # estimate the omitted value at cost (conservative, disclosed as such)
            $unmarkedMvEstimate += ([double]$p.quantity * [double]$p.cost_price)
          } else { $sumMv += [double]$mv }
        }
        $calc = $cash + $sumMv
        if ([math]::Abs($calc - $rep) -gt 0.02) {
          $flags.Q1_equity_mismatch++
          $mismatchRows += [ordered]@{ file=$f.Name; ts="$($o.ts)"; trader=$name; reported=[math]::Round($rep,2); recomputed=[math]::Round($calc,2); diff=[math]::Round($calc-$rep,2) }
        }
        if ($unmarked -gt 0) {
          $flags.Q2_unmarked_positions++
          $unmarkedWeightSum += $unmarkedMvEstimate
        }
        # Q4 redundant snapshot: same day, same trader, equity move below threshold
        $key = "$day|$name"
        if ($prevEquity.ContainsKey($key)) {
          $prev = $prevEquity[$key]
          if ($prev -ne 0) {
            $mv2 = [math]::Abs(($rep - $prev) / $prev)
            if ($mv2 -lt $MaterialMove) { $redundant++ }
          }
        }
        $prevEquity[$key] = $rep
      }
    }
  }
}
$flags.Q4_redundant_snapshots = $redundant
if ($unmarkedWeightSum.Count -gt 0) {
  $avgUnmarked = ($unmarkedWeightSum | Measure-Object -Average).Average
  $flags.Q2_unmarked_weight_pct = [math]::Round(100.0 * $avgUnmarked / 1000000.0, 2)
}

# ---------- Q3 : annualization on too few bars ----------
if (Test-Path $paperDir) {
  foreach ($pf in (Get-ChildItem $paperDir -File -Filter '*_paper.json')) {
    try { $j = Get-Content $pf.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { continue }
    $bars = 0
    if ($j.PSObject.Properties.Name -contains 'bars') { $bars = [int]$j.bars }
    $ann = $null
    $wm = $j.window_metrics
    if ($wm -and ($wm.PSObject.Properties.Name -contains 'annual_return')) { $ann = [double]$wm.annual_return }
    if ($bars -lt $MinBarsForAnnual) {
      $flags.Q3_annualization_below_floor++
      $findings += [ordered]@{
        id='Q3'; trader=$pf.BaseName; bars=$bars; floor=$MinBarsForAnnual
        reported_annual_return=$ann
        note='annualized statistic on fewer bars than the floor - mathematically meaningless, must not be quoted to CEO'
      }
    }
  }
}

# ---------- Q5 : registered traders with zero activity ----------
if (Test-Path $paperDir) {
  foreach ($pf in (Get-ChildItem $paperDir -File -Filter '*_paper.json')) {
    try { $j = Get-Content $pf.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { continue }
    $ntr = 0; if ($j.window_metrics -and ($j.window_metrics.PSObject.Properties.Name -contains 'num_trades')) { $ntr = [int]$j.window_metrics.num_trades }
    $npos = 0; if ($j.open_positions) { $npos = @($j.open_positions).Count }
    $months = 0; if ($j.PSObject.Properties.Name -contains 'months_tracked') { $months = [int]$j.months_tracked }
    if ($ntr -eq 0 -and $npos -eq 0 -and $months -eq 0) {
      $flags.Q5_zero_activity_traders++
      $findings += [ordered]@{ id='Q5'; trader=$pf.BaseName; closed_trades=0; open_positions=0; months_tracked=0; note='flat at initial cash - registered but not trading' }
    }
  }
}

$report = [ordered]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  probe         = 'quant-audit-probe.ps1 v1.0'
  law_ref       = 'D-20260930-27 (external quant oversight) / audit-charter Appendix A'
  repo          = $Repo
  snapshots     = $snapTotal
  snapshots_by_day = $snapByDay
  flags         = $flags
  equity_mismatch_rows = $mismatchRows | Select-Object -First 20
  findings      = $findings
  note          = 'Q2 unmarked weight is estimated at COST (disclosed as an estimate, not a market value). All checks are read-only.'
}
$json = $report | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($Out, $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Output ('quant-audit-probe v1.0 ' + $report.generated_utc + '  repo=' + (Split-Path $Repo -Leaf))
Write-Output ('snapshots=' + $snapTotal + '  days=' + $snapByDay.Count)
Write-Output ('Q1 equity_mismatch=' + $flags.Q1_equity_mismatch)
Write-Output ('Q2 unmarked_position_rows=' + $flags.Q2_unmarked_positions + '  est_weight_pct_of_1M=' + $flags.Q2_unmarked_weight_pct)
Write-Output ('Q3 annualized_below_' + $MinBarsForAnnual + '_bars=' + $flags.Q3_annualization_below_floor)
Write-Output ('Q4 redundant_snapshots=' + $flags.Q4_redundant_snapshots)
Write-Output ('Q5 zero_activity_traders=' + $flags.Q5_zero_activity_traders)
Write-Output ('-> ' + $Out)
