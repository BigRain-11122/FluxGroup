# cn-market-rules-probe.ps1 -- China A-share rule compliance probe (external oversight, DOMESTIC rule set)
# Purpose: catch the failure modes that GLOBAL backtest practice does not cover but A-share
# rules make material. Read-only. ASCII-only body (encoding law).
#
#   CN1 one-price days      : high == low and the close moved -> limit-locked or suspended.
#                             A backtest that fills on such a bar is fiction: at limit-up you
#                             cannot buy, at limit-down you cannot sell. This is the DOMESTIC
#                             look-ahead that a "close vs open" check can never see.
#   CN2 limit moves         : close-to-close move at/over the board band (+-10%).
#   CN3 tick alignment      : every price must be a multiple of the fund tick (0.001).
#   CN4 T+0 / T+1 split     : which symbols may trade intraday and which may not (a T+1 name
#                             used with an intraday signal is an untradeable backtest).
#   CN5 local holiday gaps  : trading-day gaps larger than a weekend = closures that must be
#                             in the calendar, otherwise holding-period math (T+1, N-day holds)
#                             silently drifts.
param(
  [string]$Repo = '',
  [string]$Out  = '',
  [int]$MaxFiles = 200
)
$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Repo)) { $Repo = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($Out))  { $Out  = Join-Path $Repo 'results\cn-market-rules-probe.json' }

$daily = Join-Path $Repo 'data\daily'
$t0 = @('511260','511090','511010','518880','159934','513100','513500','513050','513180','159920','513520','511880','511990')

$perFile = New-Object System.Collections.ArrayList
$onePriced = New-Object System.Collections.ArrayList
$limitMoves = New-Object System.Collections.ArrayList
$tickBad = New-Object System.Collections.ArrayList
$holidayGaps = New-Object System.Collections.ArrayList
$t0InUniverse = New-Object System.Collections.ArrayList
$t1InUniverse = New-Object System.Collections.ArrayList

$files = @(Get-ChildItem $daily -File -Filter '*.csv' -ErrorAction SilentlyContinue |
  Where-Object { $_.BaseName -match '^\d{6}$' } | Sort-Object Name | Select-Object -First $MaxFiles)

foreach ($f in $files) {
  $code = $f.BaseName
  if ($t0 -contains $code) { [void]$t0InUniverse.Add($code) } else { [void]$t1InUniverse.Add($code) }

  $prevClose = $null
  $prevDate = $null
  $bars = 0; $op = 0; $lm = 0; $tb = 0; $hg = 0
  foreach ($line in [IO.File]::ReadLines($f.FullName)) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $p = $line.Split(',')
    if ($p.Count -lt 5) { continue }
    if ($p[0] -eq 'date') { continue }
    $d = $p[0]; $o = $p[1]; $h = $p[2]; $l = $p[3]; $c = $p[4]
    $vv = 0.0; $ok = [double]::TryParse($c, [ref]$vv)
    if (-not $ok) { continue }
    $bars++

    # CN3 tick alignment (0.001 for funds)
    foreach ($px in @($o,$h,$l,$c)) {
      $x = 0.0; if ([double]::TryParse($px, [ref]$x)) {
        $r = [math]::Round($x * 1000.0, 4)
        if ([math]::Abs($r - [math]::Round($r)) -gt 1e-6) { $tb++ }
      }
    }

    # CN1 one-price day
    $hh = 0.0; $ll = 0.0; [void][double]::TryParse($h,[ref]$hh); [void][double]::TryParse($l,[ref]$ll)
    if ($hh -gt 0 -and $hh -eq $ll -and $null -ne $prevClose -and [math]::Abs($vv - $prevClose) -gt 1e-9) {
      $op++
      if ($onePriced.Count -lt 40) { [void]$onePriced.Add([ordered]@{ symbol=$code; date=$d; price=$vv; prev_close=$prevClose; pct=[math]::Round(($vv-$prevClose)/$prevClose*100,2) }) }
    }

    # CN2 limit move vs board band (ETF 10%)
    if ($null -ne $prevClose -and $prevClose -gt 0) {
      $chg = ($vv - $prevClose) / $prevClose
      if ([math]::Abs($chg) -ge 0.095) {
        $lm++
        if ($limitMoves.Count -lt 40) { [void]$limitMoves.Add([ordered]@{ symbol=$code; date=$d; pct=[math]::Round($chg*100,2); high=$hh; low=$ll; one_price=($hh -eq $ll) }) }
      }
    }

    # CN5 holiday gap. DOMESTIC CALIBRATION (v1.0 bug fixed): CN holidays routinely create
    # 4-8 calendar-day closures (Spring Festival ~9, National Day ~9, May Day ~5, Qingming ~4).
    # v1.0 used >4 days and produced 1255 false hits. The correct flag is a gap that is NOT
    # explainable by a known CN holiday pattern, i.e. > 12 calendar days, or a gap that lands
    # inside a trading month without a holiday. Threshold set to 12 with the holiday list noted.
    if ($null -ne $prevDate) {
      $dt1 = [datetime]::MinValue; $dt2 = [datetime]::MinValue
      if ([datetime]::TryParse($prevDate,[ref]$dt1) -and [datetime]::TryParse($d,[ref]$dt2)) {
        if (($dt2 - $dt1).TotalDays -gt 12) {
          $hg++
          if ($holidayGaps.Count -lt 20) { [void]$holidayGaps.Add([ordered]@{ symbol=$code; from=$prevDate; to=$d; calendar_days=[int]($dt2-$dt1).TotalDays; note='exceeds any known CN holiday closure' }) }
        }
      }
    }

    $prevClose = $vv; $prevDate = $d
  }
  [void]$perFile.Add([ordered]@{ symbol=$code; bars=$bars; one_price_days=$op; limit_moves=$lm; tick_off_grid=$tb; holiday_gaps=$hg; is_t0=($t0 -contains $code) })
}

$sumOne = 0; $sumLim = 0; $sumTick = 0; $sumGap = 0; $sumBars = 0
foreach ($x in $perFile) { $sumOne += $x.one_price_days; $sumLim += $x.limit_moves; $sumTick += $x.tick_off_grid; $sumGap += $x.holiday_gaps; $sumBars += $x.bars }

$worst = @($perFile | Sort-Object one_price_days -Descending | Select-Object -First 10)

$report = [ordered]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  probe = 'cn-market-rules-probe.ps1 v1.0 (domestic rule set)'
  law_ref = 'docs/audit-charter.md Appendix B2 item 4 (data integrity) + D-20260930-38'
  repo = $Repo
  files_scanned = $perFile.Count
  bars_scanned = $sumBars
  summary = [ordered]@{
    CN1_one_price_days = $sumOne
    CN2_limit_moves_ge_9p5pct = $sumLim
    CN3_tick_off_grid = $sumTick
    CN5_holiday_gaps = $sumGap
    T0_symbols_in_universe = $t0InUniverse.Count
    T1_symbols_in_universe = $t1InUniverse.Count
  }
  T0_symbols = $t0InUniverse
  CN1_samples = $onePriced
  CN2_samples = $limitMoves
  CN5_samples = ($holidayGaps | Select-Object -First 8)
  worst_symbols = $worst
  per_file = $perFile
  notes = @(
    'CN1 matters because at a limit-locked bar there is no counterparty: a buy fill at the limit-up price or a sell fill at the limit-down price is fiction. A close-vs-open look-ahead test cannot detect this; it is a domestic-market-specific untradeability trap.',
    'CN4: an intraday (same-day exit) signal applied to a non-T0 symbol is untradeable under T+1 and must be rejected at preregistration.',
    'This probe reports; it does not accuse. Every sample row is a date any reviewer can open in the CSV.'
  )
}
$dir = Split-Path $Out -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
[System.IO.File]::WriteAllText($Out, ($report | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))

Write-Output ('cn-market-rules-probe v1.0  ' + $report.generated_utc)
Write-Output ('files=' + $perFile.Count + '  bars=' + $sumBars)
Write-Output ('CN1 one-price days            = ' + $sumOne)
Write-Output ('CN2 limit moves (>=9.5%)      = ' + $sumLim)
Write-Output ('CN3 tick off grid (0.001)     = ' + $sumTick)
Write-Output ('CN5 holiday gaps (>12 days)   = ' + $sumGap)
Write-Output ('T0 symbols in universe        = ' + $t0InUniverse.Count + ' / T1 = ' + $t1InUniverse.Count)
Write-Output 'worst CN1 symbols:'
foreach ($w in $worst) { if ($w.one_price_days -gt 0) { Write-Output ('  ' + $w.symbol + '  one_price=' + $w.one_price_days + '  limit_moves=' + $w.limit_moves + '  bars=' + $w.bars + '  t0=' + $w.is_t0) } }
Write-Output ('-> ' + $Out)
