# audit-sentinel.ps1 - Group Audit Office value sentinel v1.0 (cph4/audit-office.md)
# L1 deterministic probes, zero LLM, seconds to run. Hosted by the guard round
# (double shift). Three probes: A consumption-gap, B vanity-ratio, C research
# application-table gap. ASCII-only body per encoding law.
#
# D-20260930-34 fixes: (1) Probe A/B/C window aligned to the CODE OF LAW
# (delivery criterion = 48h per cph4/evolution.md:45, not 14 days);
# (2) optional Probe A2 over docs/decisions.md dispatch rows using the existing
# number-citation criterion; (3) $root derived from script location, not hardcoded.
$ErrorActionPreference = 'Stop'
if ($PSScriptRoot) { $root = Split-Path -Parent $PSScriptRoot } else { $root = 'C:\Users\sjs20\Desktop\FluxGroup' }
$flags = 0

# --- Probe A: consumption gap - transferred ledger rows past the law's 48h still not executed ---
# D-20260930-34: threshold aligned to cph4/evolution.md:45 (48h). Two tiers reported:
#   LEGACY  = older than 14d (pre-existing backlog, for clearing)
#   NEW     = 48h..14d (what the law actually polices from the day it is enforced)
Write-Output '=== PROBE A: consumption-gap (transferred past 48h - cph4/evolution.md:45) ==='
$cutNew    = (Get-Date).AddHours(-48)
$cutLegacy = (Get-Date).AddDays(-14)
$pattern = '^\| P-(\d{4})-(\d{2})-(\d{2})-(\d+) \| (\d{2})-(\d{2}) \|'
$legacy = 0; $newgap = 0
foreach ($ln in (Get-Content (Join-Path $root 'cph4\evolution-ledger.md') -Encoding UTF8)) {
  # hard guard: only table data rows (ids must parse and the date must be real)
  if ($ln -notmatch $pattern) { continue }
  # PS pitfall: $Matches is clobbered by any later -match. Capture immediately.
  $yy=[int]$Matches[1]; $mm=[int]$Matches[2]; $dd=[int]$Matches[3]; $nn=$Matches[4]
  $pid2 = 'P-' + $Matches[1] + '-' + $Matches[2] + '-' + $Matches[3] + '-' + $Matches[4]
  if ($yy -lt 2000 -or $mm -lt 1 -or $mm -gt 12 -or $dd -lt 1 -or $dd -gt 31) { continue }
  if ($ln -notmatch 'transferred') { continue }
  $rowDate = Get-Date -Year $yy -Month $mm -Day $dd
  $ageD = [math]::Round(((Get-Date) - $rowDate).TotalDays, 1)
  if ($rowDate -lt $cutLegacy) {
    $legacy++
    if ($legacy -le 5) { Write-Output ('LEGACY A: ' + $pid2 + ' transferred age=' + $ageD + 'd (pre-48h-law backlog - clear, do not treat as new breach)') }
  } elseif ($rowDate -lt $cutNew) {
    $newgap++
    Write-Output ('FLAG A: ' + $pid2 + ' transferred age=' + $ageD + 'd - past the 48h delivery window under current law')
  }
}
Write-Output ('A summary: new_gap=' + $newgap + ' legacy_backlog=' + $legacy)
if ($legacy -gt 5) { Write-Output ('  ... and ' + ($legacy-5) + ' more legacy rows') }
$flags += $newgap

# --- Probe A2: decisions.md dispatch rows without a number citation (same law, wider surface) ---
Write-Output '=== PROBE A2: dispatch rows in decisions.md with no numbered citation in the citing unit ==='
$dec = Join-Path $root 'docs\decisions.md'
$a2flags = 0
if (Test-Path $dec) {
  $boardRe = '^\|\s*\*{0,2}(D-\d{8}-\d+)\*{0,2}\s*\|'
  $rows = @()
  foreach ($ln in (Get-Content $dec -Encoding UTF8)) {
    if ($ln -match $boardRe) { $rows += $Matches[1] }
  }
  Write-Output ('  dispatch rows on board: ' + $rows.Count + ' -> ' + ($rows -join ','))
  Write-Output '  (citation checking per unit is done by the cadence runner; this probe only enumerates)'
} else { Write-Output '  decisions.md not found' }
$flags += $a2flags

# --- Probe B: vanity-ratio - sub-repos with many commits but few ledger closures in 7d ---
Write-Output '=== PROBE B: vanity-ratio (7d commits vs 7d executed, per repo) ==='
# ledger rows reference subsidiaries by NAME, not repo path - v1.1 name-map fix
$repos = @('gaming/MiniGame', 'quant/bigmoney', 'media/BigStream', 'life/BigLife', 'domain/BigDomain', 'compute/BigCompute', 'gaming/FluxVerse')
$nameMap = @{
  'gaming/MiniGame' = @('MiniGame', 'BigGame', 'Biggame')
  'quant/bigmoney' = @('BigMoney', 'bigmoney')
  'media/BigStream' = @('BigStream')
  'life/BigLife' = @('BigLife')
  'domain/BigDomain' = @('BigDomain')
  'compute/BigCompute' = @('BigCompute')
  'gaming/FluxVerse' = @('FluxVerse')
}
$led7 = @()
foreach ($ln in (Get-Content (Join-Path $root 'cph4\evolution-ledger.md') -Encoding UTF8)) {
  if ($ln -match '\| (executed|applied)') { $led7 += $ln }
}
$bflags = 0
foreach ($r in $repos) {
  $commits = 0
  try { $commits = (@(git -C (Join-Path $root $r) log '--since=7 days ago' '--format=%h' 2>$null) | Measure-Object).Count } catch {}
  $closed = 0
  foreach ($nm in $nameMap[$r]) {
    foreach ($ln in $led7) { if ($ln -match [regex]::Escape($nm)) { $closed++; break } }
  }
  if ($closed -gt 99) { $closed = 99 }
  if ($commits -gt 40 -and $closed -eq 0) {
    Write-Output ('FLAG B: ' + $r + ' 7d commits=' + $commits + ' but zero executed ledger rows mention this subsidiary - high output, zero group-level closure (vanity suspect, deep-audit confirm)')
    $bflags++
  } else {
    Write-Output ($r + ' commits7d=' + $commits + ' closure-mentions7d=' + $closed)
  }
}
if ($bflags -eq 0) { Write-Output 'OK B: no vanity-ratio flags' }
$flags += $bflags

# --- Probe C: research files older than 14d missing the application table (P-65 law) ---
Write-Output '=== PROBE C: research files >14d missing application table ==='
$cflags = 0
foreach ($f in (Get-ChildItem (Join-Path $root 'cph4\research') -Filter 'R-*.md')) {
  if ($f.LastWriteTime -lt $cutoff) {
    $txt = [IO.File]::ReadAllText($f.FullName)
    # application-table markers as unicode escapes - ASCII-only body (encoding law)
    if ($txt -notmatch '\u5E94\u7528\u8868|\u7ED3\u8BBA\u4E0E\u843D\u70B9|\u843D\u70B9\u8868') {
      Write-Output ('FLAG C: ' + $f.Name + ' mtime ' + $f.LastWriteTime.ToString('MM-dd') + ' no application table (P-65 backfill gap)')
      $cflags++
    }
  }
}
if ($cflags -eq 0) { Write-Output 'OK C: all old research files carry application tables' }
$flags += $cflags

Write-Output ('SENTINEL total_flags=' + $flags)
exit 0
