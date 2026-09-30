# deliverable-probe.ps1 -- XL-7 deliverable north-star probe (D-20260930-06)
# Reads every unit repo READ-ONLY and emits machine-checkable numbers:
#   A) accessible fronts  (product HTML/entry files a human can open)
#   B) published items    (real platform link / published evidence)
#   C) real receipts      (settled-money evidence)
#   D) process-vs-product commit ratio (root causes R2/R3)
# Encoding law: this body is ASCII-ONLY. CJK literals are written as \uXXXX
# regex escapes so codepoint-construction survives both pwsh7 and PS5.1.
# No repo writes. Only output artifact = one UTF-8 JSON data file.
param(
  [string]$Root = '',
  [string]$Out  = ''
)

$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Root)) {
  $Root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
}
if ([string]::IsNullOrWhiteSpace($Out)) {
  $Out = Join-Path $Root 'docs\audits\deliverable-metrics.json'
}

$units = @(
  @{ n='Biggame';    p='gaming\MiniGame' },
  @{ n='FluxVerse';  p='gaming\FluxVerse' },
  @{ n='BigMoney';   p='quant\bigmoney' },
  @{ n='BigStream';  p='media\BigStream' },
  @{ n='BigDomain';  p='domain\BigDomain' },
  @{ n='BigLife';    p='life\BigLife' },
  @{ n='BigCompute'; p='compute\BigCompute' }
)

# Heavy / irrelevant trees never walked
$skipRe = '\\(\.git|Library|Temp|obj|Builds?|node_modules|\.venv|venv|__pycache__|\.codely-cli|_archive|_trash|\.c3-tmp|\.lc\d+-tmp|\.bs\d+-tmp|\.s\d+-tmp|\.sc\d+-tmp|\.react-tmp|Art Assets|Money02|Money0923|legacy|data)\\'

# ---- evidence patterns (ASCII source; CJK via codepoint escapes) ----
# published:  published | 已发布 | 发布链接 | platform_url | post_url | 播放量 | views
# STRICT: evidence must be a structured field carrying a NUMBER, or a real link.
# Prose mentions of a word inside law text are NOT evidence (v1.0 lesson: two
# false positives came from "settled criterion" and a law-citation sentence).
# published: quoted platform URL, or a platform+link/播放量 field with a number
$pubPat  = 'https?://[^\s"'']*(?:shipinhao|weixin|mp\.weixin|douyin|bilibili|xiaohongshu|kuaishou|zhihu|toutiao|weibo|youtube|tiktok)[^\s"'']*' +
           '|"\s*\u5df2\u53d1\u5e03\s*"\s*:\s*(?:true|[1-9])' +
           '|"\s*\u64ad\u653e\u91cf\s*"\s*:\s*[1-9]'
# receipts: quoted money field carrying a non-zero number
$cashPat = '"\s*(?:total_revenue_cny|total_receipts_cny|gmv_cny|revenue_cny|settled_amount|paid_amount_cny|received_cny|net_income_cny)\s*"\s*:\s*-?[1-9]' +
           '|"\s*(?:\u6210\u4ea4\u989d|\u5b9e\u6536|\u5230\u8d26\u91d1\u989d|\u56de\u6b3e)\s*"\s*:\s*-?[1-9]'
# negative markers that mean "not yet real"
$negPat  = '\u672a\u6d4b\u91cf|\u672a\u4e0a\u7ebf|\u672a\u6ce8\u518c|PENDING|pending|not_set|BLOCKED'

$evidenceRels = @(
  'output\finished.md', 'docs\accounts.md', 'output\analytics.md',
  'output\schedule.md', 'output\readiness.md',
  'state\status-export.json', 'docs\status-export.json',
  'state\month-end-202609.json', 'output\reports'
)

function Get-EntryFiles {
  param([string]$UnitPath)
  $found = New-Object System.Collections.ArrayList
  $roots = @('', 'output', 'src', 'public', 'web', 'dist', 'site', 'www', 'lobby')
  foreach ($r in $roots) {
    $base = if ($r -eq '') { $UnitPath } else { Join-Path $UnitPath $r }
    if (-not (Test-Path $base)) { continue }
    $depthSets = @($base)
    foreach ($d in (Get-ChildItem $base -Directory -ErrorAction SilentlyContinue)) {
      if ($d.FullName -match $skipRe) { continue }
      $depthSets += $d.FullName
    }
    foreach ($bd in $depthSets) {
      foreach ($f in (Get-ChildItem $bd -File -Filter '*.html' -ErrorAction SilentlyContinue)) {
        if ($f.FullName -match $skipRe) { continue }
        if ($f.Name -match 'daily[-_]?\d|daily-report|snapshot|dashboard|kanban|\.template\.|\.tmp\.|\.bak') { continue }
        [void]$found.Add($f)
      }
    }
  }
  return ($found | Sort-Object FullName -Unique)
}

function Get-CommitRatio {
  param([string]$UnitPath)
  if (-not (Test-Path (Join-Path $UnitPath '.git'))) { return $null }
  $subs = git -C $UnitPath log --since='2026-09-29 00:00' --format='%s' 2>$null
  if (-not $subs) { return $null }
  $tot = ($subs | Measure-Object).Count
  $over = ($subs | Where-Object {
    $_ -match 'state|carry|snapshot|rebase|collis|conflict|heartbeat|sync|claim|idle|waiting-state|autofill tick|S0 '
  }).Count
  return [ordered]@{
    commits_48h  = $tot
    overhead_48h = $over
    overhead_pct = if ($tot -gt 0) { [math]::Round(100.0 * $over / $tot, 1) } else { 0 }
  }
}

$report = [ordered]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  probe         = 'deliverable-probe.ps1 v1.1 (XL-7)'
  law_ref       = 'D-20260930-06 XL-7 / docs/audits/group-wide-audit-improvement-list-20260930.md'
  engine        = $PSVersionTable.PSVersion.ToString()
  units         = @()
  totals        = [ordered]@{ accessible_fronts = 0; published_items = 0; real_receipts = 0 }
}

foreach ($u in $units) {
  $up = Join-Path $Root $u.p
  if (-not (Test-Path $up)) {
    $report.units += [ordered]@{ unit = $u.n; path = $u.p; status = 'MISSING' }
    continue
  }

  $entries    = Get-EntryFiles -UnitPath $up
  $entryNames = @($entries | ForEach-Object { $_.Name } | Select-Object -First 8)

  $pubHits = 0; $cashHits = 0; $negHits = 0; $scanned = @()
  foreach ($rel in $evidenceRels) {
    $fp = Join-Path $up $rel
    if (-not (Test-Path $fp)) { continue }
    $items = @()
    if ((Get-Item $fp).PSIsContainer) {
      $items = Get-ChildItem $fp -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20
    } else {
      $items = @(Get-Item $fp)
    }
    foreach ($it in $items) {
      if ($it.Length -gt 400000) { continue }
      $scanned += ($it.FullName.Substring($up.Length).TrimStart('\'))
      $txt = Get-Content $it.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
      if ([string]::IsNullOrEmpty($txt)) { continue }
      if ($txt -match $pubPat)  { $pubHits++ }
      if ($txt -match $cashPat) { $cashHits++ }
      if ($txt -match $negPat)  { $negHits++ }
    }
  }

  $ratio = Get-CommitRatio -UnitPath $up

  $report.units += [ordered]@{
    unit              = $u.n
    path              = $u.p
    status            = 'OK'
    accessible_fronts = $entries.Count
    front_samples     = $entryNames
    published_items   = $pubHits
    real_receipts     = $cashHits
    negative_markers  = $negHits
    evidence_scanned  = $scanned
    commits           = $ratio
  }
  $report.totals.accessible_fronts += $entries.Count
  $report.totals.published_items   += $pubHits
  $report.totals.real_receipts     += $cashHits
}

$report.note = 'published_items/real_receipts are EVIDENCE-HIT counts over declared files, not audited truths; 0 = not found (negative evidence, governance 10). accessible_fronts counts product HTML entry files only (report/snapshot/dashboard names excluded).'

$json = $report | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($Out, $json, (New-Object System.Text.UTF8Encoding($false)))

# ---- compact stdout (no alignment operator: PS uses {n,-w} only) ----
Write-Output ('XL-7 probe ' + $report.generated_utc + '  engine=' + $report.engine)
$fmt = '{0,-12} {1,6} {2,7} {3,8} {4,7} {5,8}'
Write-Output ($fmt -f 'unit', 'fronts', 'pubbed', 'receipts', 'neg', 'ovh%')
foreach ($r in $report.units) {
  if ($r.status -ne 'OK') { Write-Output ($r.unit + ' ' + $r.status); continue }
  $pct = if ($r.commits) { $r.commits.overhead_pct } else { '-' }
  Write-Output ($fmt -f $r.unit, $r.accessible_fronts, $r.published_items, $r.real_receipts, $r.negative_markers, $pct)
}
Write-Output ('TOTAL fronts=' + $report.totals.accessible_fronts + ' pubbed_evidence=' + $report.totals.published_items + ' receipts_evidence=' + $report.totals.real_receipts)
Write-Output ('-> ' + $Out)
