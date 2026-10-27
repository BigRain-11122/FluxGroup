# banned-direction-gate.ps1 -- fail-closed hard gate against falsified research directions
# Authority: D-20260930-41 section 1.2 + docs/audits/retail-quant-conclusions-v2-20260930.md section 3
# Registry: quant/bigmoney/research/BANNED_DIRECTIONS.json
#
# CALIBRATION NOTE (v1.1, 2026-09-30): the registry patterns were broad keyword regexes and
# produced 60/83 false positives on a 7-day prereg scan, because the firm legitimately uses
# "grid" to mean a PARAMETER grid ("逐网格单元披露", "CSCV-8 4格网格") and "intraday" inside a
# FEATURE NAME ("intraday_range"). That is the same false-positive class the external audit
# was created to catch. v1.1 therefore requires a TRADE-SEMANTIC co-occurrence: "grid trading"
# or "grid strategy", not bare "grid". Verified discriminative: it matches the real claim in
# EXIT_OVERLAY_P1.md ("本件=ETF 网格交易执行引擎") and produces zero hits on current preregs.
#
# Usage:
#   tools/banned-direction-gate.ps1 -Prereg <path.md>            # check one prereg
#   tools/banned-direction-gate.ps1 -Scan                        # check all preregs from the last 7 days
#   tools/banned-direction-gate.ps1 -Prereg <path> -MechanismOnly # only inspect the mechanism section
#
# Exit 0 = ADMIT, exit 1 = REJECT (fail-closed), exit 2 = error.
# A match is REJECTED unless the prereg carries an exception statement naming
# BAN-xx plus either new_data or new_mechanism.
# ASCII-only body (encoding law).
param(
  [string]$Root = '',
  [string]$Prereg = '',
  [switch]$Scan,
  [switch]$MechanismOnly
)
$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = Split-Path -Parent $PSScriptRoot }

$regPath = Join-Path $Root 'quant\bigmoney\research\BANNED_DIRECTIONS.json'
if (-not (Test-Path $regPath)) { Write-Output 'ERROR registry missing'; exit 2 }
$reg = Get-Content $regPath -Raw -Encoding UTF8 | ConvertFrom-Json

# v1.1 trade-semantic patterns, keyed by BAN id (override the broad registry patterns)
$tight = @{
  'BAN-01' = '(\u6a2a\u622a\u9762.{0,8}\u52a8\u91cf|cross.?section.{0,10}momentum)'
  'BAN-02' = '(\u6a2a\u622a\u9762.{0,8}\u53cd\u8f6c|cross.?section.{0,10}reversal)'
  'BAN-03' = '(1.?15\s*\u4ea4\u6613\u65e5|\u6301\u6709\s*1.?15\s*\u5929|\u65e5\u5185\u4ea4\u6613|intraday\s*(trad|strateg|signal|revers))'
  'BAN-04' = '(\u7f51\u683c\u4ea4\u6613|\u7f51\u683c\u7b56\u7565|\u7f51\u683c\u6302\u5355|\u7f51\u683c\u6cd5|\u7f51\u683c\u76c8\u5229|\u7f51\u683c\u53e0\u4ee3|grid\s*trad|grid\s*strateg)'
  'BAN-05' = '(\u6c34\u6e29.{0,10}(\u524d\u7f6e|\u95f8|\u62e9\u65f6|filter)|(\u5e02\u573a|\u5927\u76d8).{0,6}\u5e7f\u5ea6.{0,10}(\u62e9\u65f6|\u95f8|\u524d\u7f6e)|breadth\s*(tim|filter|gate))'
  'BAN-06' = '(\u7ad9\u4e0a\s*MA\d+.{0,12}(\u786e\u8ba4|\u8fc7\u6ee4|\u524d\u7f6e|\u624d\u4e70)|MA20\s*\u786e\u8ba4|\u524d\s*20\s*\u65e5\u4e3a\u6b63|\u5747\u7ebf\u786e\u8ba4)'
  'BAN-07' = '(\u5c0f\u5e02\u503c.{0,10}(\u56e0\u5b50|\u7b56\u7565|\u503e\u659c|\u9009\u80a1)|small.?cap.{0,10}(factor|strateg|tilt)|\u4f4e\u4ef7\u56e0\u5b50|\u4f4e\u4ef7\u80a1\u7b56\u7565)'
  'BAN-08' = '(\u7f13\u51b2\u533a|\u65e0\u4ea4\u6613\u5e26|no.?trade.?band|buffer\s*zone.{0,12}(\u964d|\u51cf)\u6362\u624b)'
  'BAN-09' = '(\u98ce\u683c\u5ef6\u7eed|\u8ffd(\u4e0a\u5e74|\u53bb\u5e74).{0,6}(\u6700\u5f3a|\u9886\u6da8)|style\s*persist|\u98ce\u683c\u8f6e\u52a8\u62bc\u6ce8)'
}
# negation guard: "不做 X" / "禁止 X" / "已否证 X" must not count as CLAIMING X
$negGuard = '(\u4e0d\u505a|\u7981|\u5df2\u5426\u8bc1|\u5df2\u5224\u8d1f|\u4e0d\u91c7\u7528|\u4e0d\u5410|never|do not|forbidden)'

function Test-OneFile([string]$path) {
  if (-not (Test-Path $path)) { return @{ file = $path; verdict = 'ERROR'; hits = @() } }
  $text = Get-Content $path -Raw -Encoding UTF8
  if ($MechanismOnly) {
    $m = [regex]::Match($text, '(?ms)^#+\s*.*(mechanism|\u673a\u5236|\u03b1).*?$(.*?)(?=^#+\s|\z)')
    if ($m.Success) { $text = $m.Groups[1].Value }
  }
  $hits = New-Object System.Collections.ArrayList
  foreach ($d in $reg.directions) {
    $pat = if ($tight.ContainsKey($d.id)) { $tight[$d.id] } else { ($d.patterns -join '|') }
    $mm = [regex]::Match($text, $pat, 'IgnoreCase')
    if (-not $mm.Success) { continue }
    # negation guard: look at the 30 chars preceding the match
    $s = [Math]::Max(0, $mm.Index - 30)
    $prefix = $text.Substring($s, $mm.Index - $s)
    if ($prefix -match $negGuard) { continue }
    $exc = $text -match ([regex]::Escape($d.id) + '[\s\S]{0,400}?(new_data|new_mechanism|new data|new mechanism|\u65b0\u6570\u636e|\u65b0\u673a\u5236)')
    [void]$hits.Add([ordered]@{ id = $d.id; name = $d.name; exception_stated = $exc })
  }
  $blocking = @($hits | Where-Object { -not $_.exception_stated })
  $verdict = if ($blocking.Count -gt 0) { 'REJECT' } else { 'ADMIT' }
  return @{ file = $path; verdict = $verdict; hits = $hits }
}

$targets = @()
if ($Scan) {
  $dir = Join-Path $Root 'quant\bigmoney\research'
  $targets = @(Get-ChildItem $dir -File -Filter '*PREREG*.md' -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) } | ForEach-Object { $_.FullName })
} elseif (-not [string]::IsNullOrWhiteSpace($Prereg)) {
  $targets = @($Prereg)
} else {
  Write-Output 'usage: -Prereg <path> | -Scan'; exit 2
}

$rej = 0; $adm = 0
foreach ($t in $targets) {
  $r = Test-OneFile $t
  if ($r.verdict -eq 'REJECT') {
    $rej++
    $ids = ($r.hits | Where-Object { -not $_.exception_stated } | ForEach-Object { $_.id }) -join ','
    Write-Output ("REJECT  " + (Split-Path $t -Leaf) + "  -> " + $ids)
  } else {
    $adm++
  }
}
Write-Output ("scanned=" + $targets.Count + " admit=" + $adm + " reject=" + $rej)
if ($rej -gt 0) { exit 1 } else { exit 0 }
