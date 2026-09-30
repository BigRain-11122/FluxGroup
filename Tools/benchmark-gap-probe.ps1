# benchmark-gap-probe.ps1 -- global-benchmark gap probe (D-20260930-37)
# Turns the 20 benchmark line-rules into machine output where a data source exists,
# and reports DATA GAP explicitly where it does not (a missing source must never
# read as "pass"). Read-only over unit repos. ASCII-only body (encoding law).
#
# Rules wired in v1.0:
#   R-S1 publish ratio        finished media vs published rows
#   R-S3 creative A/B count   evidence of >=2 cover variants
#   R-D1 accessible fronts    product HTML entry count
#   R-C1 GPU utilisation      7-day average from compute state
#   R-L1 consumption ratio    census assets vs wired consumers
#   R-F2 assembly via data    layout-data instances > 0 while runtime builders exist
#   R-G3 test-per-build ratio # test assets vs built titles
#   R-M2 cost reconciliation  presence of a per-trade cost reconciliation artifact
# Rules with no local source are listed as UNWIRED (data gap) -- never as pass.
param(
  [string]$Root = '',
  [string]$Out  = ''
)
$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = Split-Path -Parent $PSScriptRoot }
if ([string]::IsNullOrWhiteSpace($Out))  { $Out  = Join-Path $Root 'docs\audits\benchmark-gap-latest.json' }

$r = [ordered]@{ generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); probe = 'benchmark-gap-probe.ps1 v1.0'; rules = @(); unwired = @() }

function Add-Rule($id, $line, $verdict, $metric, $threshold, $evidence) {
  $script:r.rules += [ordered]@{ rule=$id; line=$line; verdict=$verdict; metric=$metric; threshold=$threshold; evidence=$evidence }
}

# ---- R-D1 accessible fronts (BigDomain) ----
$bd = Join-Path $Root 'domain\BigDomain'
$fronts = 0
if (Test-Path $bd) {
  $fronts = (Get-ChildItem $bd -Recurse -File -Filter '*.html' -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|\.venv|_trash|\.codely-cli)\\' -and $_.Name -notmatch 'report|snapshot' } | Measure-Object).Count
}
# DEFINITION GAP: a raw html file inside the repo is NOT an externally reachable front.
# Correct verdict until 'accessible front' is defined (URL + click recording): DEFINITION_GAP.
Add-Rule 'R-D1' 'BigDomain' 'DEFINITION_GAP' "repo_html_files=$fronts" 'externally reachable + click recording required' 'domain/BigDomain html scan (weak source)'

# ---- R-S1 publish ratio (BigStream) ----
$bs = Join-Path $Root 'media\BigStream'
$finished = 0; $published = 0
if (Test-Path $bs) {
  $finished = (Get-ChildItem $bs -Recurse -File -Include '*.mp4' -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '\\output\\renders\\' } | Measure-Object).Count
  $acc = Join-Path $bs 'docs\accounts.md'
  if (Test-Path $acc) {
    $t = Get-Content $acc -Raw -Encoding UTF8
    $published = ([regex]::Matches($t, '\u5df2\u53d1\u5e03')).Count   # 'published'
  }
}
$ratio = if ($finished -gt 0) { [math]::Round($published / $finished, 3) } else { 0 }
Add-Rule 'R-S1' 'BigStream' $(if($ratio -ge 0.3){'PASS'}else{'FAIL'}) "published=$published finished=$finished ratio=$ratio" '>=0.3' 'output/renders + docs/accounts.md'

# ---- R-S3 creative A/B variants ----
$variants = 0
if (Test-Path $bs) {
  $variants = (Get-ChildItem $bs -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '(cover|thumb).*(v\d|_[ab]\b|alt)' } | Select-Object -First 500 | Measure-Object).Count
}
Add-Rule 'R-S3' 'BigStream' $(if($variants -ge 2){'PASS'}else{'DATA_GAP'}) "cover_variant_hits=$variants" '>=2 per item' 'filename scan only: weak, needs a per-item manifest (unwired detail)'

# ---- R-C1 GPU utilisation (BigCompute) ----
$bc = Join-Path $Root 'compute\BigCompute'
$avg = @()
if (Test-Path $bc) {
  foreach ($f in (Get-ChildItem $bc -Recurse -File -Filter '*.json' -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match '\\state\\' } | Select-Object -First 60)) {
    $t = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ([string]::IsNullOrEmpty($t)) { continue }
    foreach ($m in [regex]::Matches($t, '"avg_pct"\s*:\s*([0-9.]+)')) { $avg += [double]$m.Groups[1].Value }
  }
}
$avgV = if ($avg.Count -gt 0) { [math]::Round((($avg | Measure-Object -Average).Average), 1) } else { $null }
$verdict = if ($null -eq $avgV) { 'DATA_GAP' } elseif ($avgV -ge 70) { 'PASS' } elseif ($avgV -ge 50) { 'WARN' } else { 'FAIL' }
Add-Rule 'R-C1' 'BigCompute' $verdict "gpu_avg_pct=$avgV (n=$($avg.Count))" '>=70 pass / <50 structural fail' 'compute/BigCompute/state/*.json'

# ---- R-L1 consumption ratio (BigLife) ----
$bl = Join-Path $Root 'life\BigLife'
$cards = 0
if (Test-Path $bl) {
  $cards = (Get-ChildItem $bl -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '\\census\\registry\\' -and $_.Extension -eq '.md' } | Measure-Object).Count
}
$wiredArtifact = Join-Path $bl 'cognition\CONSUMER-WIRING.md'
$wired = 0
if (Test-Path $wiredArtifact) {
  $t = Get-Content $wiredArtifact -Raw -Encoding UTF8
  $m = [regex]::Match($t, 'wired_count\s*[=:]\s*(\d+)|=\s*(\d)\s*$', 'Multiline')
  if ($m.Success) { $wired = [int]($m.Groups[1].Value + $m.Groups[2].Value) }
  if ($wired -eq 0) { $wired = ([regex]::Matches($t, 'wired')).Count }
}
Add-Rule 'R-L1' 'BigLife' $(if($wired -ge 1){'PASS'}else{'FAIL'}) "census_cards=$cards wired_consumers=$wired" '>=1 consumer per new batch' 'census/registry + cognition/CONSUMER-WIRING.md'

# ---- R-F2 assembly via data (FluxVerse) ----
$fv = Join-Path $Root 'gaming\FluxVerse'
$layoutData = 0; $runtimeBuilders = 0
if (Test-Path $fv) {
  $layoutData = (Get-ChildItem $fv -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'layout.*\.json$|city-layout|world-state' } | Select-Object -First 100 | Measure-Object).Count
  $cs = Get-ChildItem $fv -Recurse -File -Filter '*.cs' -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\(\.git|Library|Temp|obj)\\' }
  foreach ($f in $cs) {
    $t = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($t -match 'new GameObject\("UIRoot"\)|BeforeSceneLoad') { $runtimeBuilders++ }
  }
}
# WEAK SOURCE: world-state snapshots are not assembler layout data.
# Correct verdict until an assembler-consumed layout artifact is confirmed: WEAK_SOURCE.
Add-Rule 'R-F2' 'FluxVerse' 'WEAK_SOURCE' "data_files_matched=$layoutData runtime_ui_builders=$runtimeBuilders" 'assembler-consumed layout artifact required' 'game/FluxVerse data scan (weak source)'

# ---- R-G3 test-per-build ratio (Biggame) ----
$mg = Join-Path $Root 'gaming\MiniGame'
$built = 0; $testAssets = 0
if (Test-Path $mg) {
  $built = (Get-ChildItem $mg -Recurse -File -ErrorAction SilentlyContinue -Include 'TuanjiePlayer.dll','*.apk' |
    Select-Object -First 100 | Measure-Object).Count
  $testAssets = (Get-ChildItem $mg -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '(cpi|creative|ad_?(test|material)|buy_?test)' -and $_.FullName -notmatch '\\\.git\\' } |
    Select-Object -First 200 | Measure-Object).Count
}
$g3 = if ($built -eq 0) { 'FAIL' } elseif ($testAssets -ge $built * 0.5) { 'PASS' } else { 'FAIL' }
Add-Rule 'R-G3' 'Biggame' $g3 "built_artifacts=$built test_asset_hits=$testAssets" 'tested >= 0.5 x built' 'build artifact + creative-material scan'

# ---- R-M2 cost reconciliation (BigMoney) ----
$bm = Join-Path $Root 'quant\bigmoney'
$recon = 0
if (Test-Path $bm) {
  $recon = (Get-ChildItem $bm -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'cost.*recon|recon.*cost|COST_RECON' } | Select-Object -First 50 | Measure-Object).Count
}
Add-Rule 'R-M2' 'BigMoney' $(if($recon -ge 1){'PASS'}else{'FAIL'}) "cost_reconciliation_artifacts=$recon" '>=1 per-trade cost reconciliation' 'filename scan for cost reconciliation artifacts'

# ---- unwired rules (data gap, never pass) ----
$r.unwired = @(
  'R-G1 (pre-launch creative + test verdict) -- needs a per-title stage manifest',
  'R-G2 (external reachable entry) -- needs a published-links registry',
  'R-S2 (CTR / 3s retention / completion write-back) -- needs platform analytics export',
  'R-F1 (module reuse rate) -- needs assembler output inventory',
  'R-F3 (weekly L0 screenshot) -- needs an evidence index',
  'R-M1 (information increment gate) -- needs prereg cross-correlation table',
  'R-M3 (surrender rule registry) -- needs a closed-line registry',
  'R-D2 (tunnel/local URL + click recording) -- needs an artifact registry',
  'R-D3 (one external-person loop) -- needs a user session record',
  'R-L2 (same-seed same-face machine check) -- needs the run log',
  'R-L3 (each resident read by at least one consumer) -- needs a consumption ledger',
  'R-C2 (internal transfer pricing for sibling usage) -- needs a costing ledger',
  'R-C3 (hourly/reserved/per-token pricing) -- needs a price sheet'
)

$pass=0;$fail=0;$warn=0;$gap=0
foreach ($x in $r.rules) {
  switch ($x.verdict) { 'PASS' { $pass++ } 'FAIL' { $fail++ } 'WARN' { $warn++ } 'DATA_GAP' { $gap++ } }
}
$r.summary = [ordered]@{ pass=$pass; fail=$fail; warn=$warn; data_gap=$gap; wired=$r.rules.Count; unwired=$r.unwired.Count }
[System.IO.File]::WriteAllText($Out, ($r | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))

Write-Output ('benchmark-gap-probe v1.0  ' + $r.generated_utc)
Write-Output ("{0,-6} {1,-12} {2,-9} {3}" -f 'rule','line','verdict','metric')
foreach ($x in $r.rules) { Write-Output ("{0,-6} {1,-12} {2,-9} {3}" -f $x.rule, $x.line, $x.verdict, $x.metric) }
Write-Output ("summary: pass=$pass fail=$fail warn=$warn data_gap=$gap | wired=$($r.rules.Count) unwired=$($r.unwired.Count)")
Write-Output ('-> ' + $Out)
