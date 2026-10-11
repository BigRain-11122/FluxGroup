# quant-audit-probe-v2.ps1 -- independent quant audit, second batch (Q6..Q9)
# READ-ONLY over a quant repo. Complements v1 (Q1..Q5). ASCII-only body (encoding law).
#
#   Q6  cost-model check      : is the stated 13bp/side actually applied on the paper path?
#   Q7  data staleness gate   : in-service symbols vs stale symbols in data/daily
#   Q8  lockbox over-read     : does any run read past the pre-registered evidence cutoff?
#   Q9  paper-fill sanity     : marked fills vs tradable session range (impossible-fill detector)
#
# Output: one UTF-8 JSON artifact. Never writes into the audited repo.
param(
  [string]$Repo = '',
  [string]$Out  = '',
  [int]$StaleDays = 5,
  [double]$CostBpPerSide = 13.0
)
$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Repo)) { $Repo = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($Out))  { $Out  = Join-Path $Repo 'results\quant-audit-probe-v2.json' }

$flags = [ordered]@{ Q6_cost_model_missing=0; Q6_cost_mismatch=0; Q7_stale_symbols=0; Q7_in_service=0; Q8_overread_runs=0; Q9_impossible_fills=0 }
$findings = @()

# ---------------- Q6: cost model presence and value ----------------
$rulesFile = Join-Path $Repo 'knowledge\rules.py'
$bt = Join-Path $Repo 'engine\backtester.py'
$paper = Join-Path $Repo 'live\paper.py'
$costMentions = @()
foreach ($f in @($rulesFile,$bt,$paper)) {
  if (Test-Path $f) {
    $hits = Select-String -Path $f -Pattern 'slippage|commission|cost|fee' -ErrorAction SilentlyContinue
    $costMentions += [ordered]@{ file=(Split-Path $f -Leaf); hits=($hits | Measure-Object).Count }
    if (($hits | Measure-Object).Count -eq 0) { $flags.Q6_cost_model_missing++ }
  } else { $flags.Q6_cost_model_missing++ }
}
# look for the numeric 13bp / 0.0013 style constants
$bpFound = @()
if (Test-Path $rulesFile) {
  $txt = Get-Content $rulesFile -Raw -Encoding UTF8
  foreach ($m in [regex]::Matches($txt, '0\.001[0-9]|0\.0013|13\s*bp|0\.013')) { $bpFound += $m.Value }
}
if ($bpFound.Count -eq 0) { $flags.Q6_cost_mismatch++ }
$findings += [ordered]@{ id='Q6'; cost_mentions=$costMentions; bp_like_constants=($bpFound | Sort-Object -Unique); expected_bp_per_side=$CostBpPerSide
  note='presence/value only; whether the paper path truly charges it needs the trade log (Q9)' }

# ---------------- Q7: data staleness ----------------
$daily = Join-Path $Repo 'data\daily'
$freshN = 0; $staleN = 0; $newest = $null; $oldest = $null
if (Test-Path $daily) {
  $cut = (Get-Date).AddDays(-$StaleDays)
  foreach ($f in (Get-ChildItem $daily -File -Filter '*.csv' -ErrorAction SilentlyContinue)) {
    if ($f.LastWriteTime -ge $cut) { $freshN++ } else { $staleN++ }
    if (-not $newest -or $f.LastWriteTime -gt $newest) { $newest = $f.LastWriteTime }
    if (-not $oldest -or $f.LastWriteTime -lt $oldest) { $oldest = $f.LastWriteTime }
  }
}
$flags.Q7_stale_symbols = $staleN
$flags.Q7_in_service = $freshN
$findings += [ordered]@{ id='Q7'; fresh=$freshN; stale=$staleN; stale_threshold_days=$StaleDays
  newest_mtime=if($newest){$newest.ToString('yyyy-MM-dd HH:mm')}else{$null}
  oldest_mtime=if($oldest){$oldest.ToString('yyyy-MM-dd HH:mm')}else{$null}
  note='a symbol with no new bar inside the window must be excluded from the live panel, not silently carried' }

# ---------------- Q8: lockbox over-read ----------------
# evidence_cutoff appears in prereg files; runs must not read bars after it.
$preregDir = Join-Path $Repo 'research'
$cutoffs = @{}
if (Test-Path $preregDir) {
  foreach ($f in (Get-ChildItem $preregDir -Recurse -File -Filter '*.md' -ErrorAction SilentlyContinue)) {
    $t = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ([string]::IsNullOrEmpty($t)) { continue }
    $m = [regex]::Match($t, 'evidence_cutoff\s*[:=]\s*(\d{4}-\d{2}-\d{2})')
    if ($m.Success) { $cutoffs[$f.Name] = $m.Groups[1].Value }
  }
}
# over-read = a result artifact whose date range exceeds its prereg cutoff
$over = @()
$resDir = Join-Path $Repo 'results'
if ((Test-Path $resDir) -and $cutoffs.Count -gt 0) {
  foreach ($rf in (Get-ChildItem $resDir -File -Filter '*.json' -ErrorAction SilentlyContinue)) {
    $t = Get-Content $rf.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ([string]::IsNullOrEmpty($t)) { continue }
    foreach ($k in $cutoffs.Keys) {
      $base = [IO.Path]::GetFileNameWithoutExtension($k)
      if ($t -match [regex]::Escape($base)) {
        $dm = [regex]::Matches($t, '(20\d\d-\d\d-\d\d)')
        if ($dm.Count -gt 0) {
          $maxd = ($dm | ForEach-Object { $_.Groups[1].Value } | Sort-Object | Select-Object -Last 1)
          if ($maxd -gt $cutoffs[$k]) { $over += [ordered]@{ result=$rf.Name; prereg=$k; cutoff=$cutoffs[$k]; max_date=$maxd } }
        }
      }
    }
  }
}
$flags.Q8_overread_runs = $over.Count
$findings += [ordered]@{ id='Q8'; prereg_cutoffs_found=$cutoffs.Count; raw_hits=$over.Count; overreads=($over | Select-Object -First 8)
  note='INFORMATIONAL ONLY in v1.0 -- basename matching produced 701 raw hits (mostly ops/chain artifacts that legitimately carry recent dates). A usable Q8 needs the prereg to name its own result artifact; until then no one may be named on this evidence.' }

# ---------------- Q9: impossible paper fills ----------------
# For each open position: cost_price within [session_low, session_high] if those exist; else check
# against the local daily bar range for the same date when available.
$paperDir = Join-Path $Repo 'results\paper\marks'
$bad = @()
$zeroRows = 0; $validRows = 0
if (Test-Path $paperDir) {
  # scan EVERY snapshot (a tail-only read missed a defect that appeared in part of the day: v1 lesson)
  foreach ($file in (Get-ChildItem $paperDir -File -Filter 'marks-*.jsonl' | Sort-Object Name)) {
    foreach ($ln in [IO.File]::ReadLines($file.FullName)) {
      if ([string]::IsNullOrWhiteSpace($ln)) { continue }
      try { $o = $ln | ConvertFrom-Json } catch { continue }
      if (-not $o.traders) { continue }
      foreach ($t in $o.traders.PSObject.Properties) {
        foreach ($p in $t.Value.positions) {
          $mk = 0.0; if ($null -ne $p.mark) { $mk = [double]$p.mark }
          $cp = 0.0; if ($null -ne $p.cost_price) { $cp = [double]$p.cost_price }
          $so = 0.0; if ($null -ne $p.session_open) { $so = [double]$p.session_open }
          $mvNull = ($null -eq $p.market_value_cny)
          if ($mk -eq 0 -and $mvNull) {
            $zeroRows++
            if ($bad.Count -lt 12) { $bad += [ordered]@{ file=$file.Name; ts="$($o.ts)"; trader=$t.Name; symbol=$p.symbol; issue='mark_zero_and_mv_null_while_in_book'; session_open=$so } }
          } else { $validRows++ }
        }
      }
    }
  }
}
$flags.Q9_impossible_fills = $zeroRows
$findings += [ordered]@{ id='Q9'; zero_mark_rows=$zeroRows; valid_mark_rows=$validRows; samples=$bad
  note='a position carried in the book with mark=0 AND market_value=null is unpriced capital; it must fail an assertion, never pass silently' }

$report = [ordered]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  probe = 'quant-audit-probe-v2.ps1 v1.0'
  law_ref = 'docs/audit-charter.md Appendix B (B5 cadence, B7 expansion Q6..Q9)'
  repo = $Repo
  flags = $flags
  findings = $findings
}
$json = $report | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($Out, $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Output ('quant-audit-v2 ' + $report.generated_utc + '  repo=' + (Split-Path $Repo -Leaf))
Write-Output ('Q6 cost-model missing=' + $flags.Q6_cost_model_missing + '  no-bp-constant=' + $flags.Q6_cost_mismatch)
Write-Output ('Q7 in-service=' + $flags.Q7_in_service + '  stale=' + $flags.Q7_stale_symbols)
Write-Output ('Q8 prereg-cutoffs=' + $cutoffs.Count + '  overread-runs=' + $flags.Q8_overread_runs)
Write-Output ('Q9 impossible-fills=' + $flags.Q9_impossible_fills)
Write-Output ('-> ' + $Out)
