# audit-sentinel.ps1 - Group Audit Office value sentinel v1.0 (cph4/audit-office.md)
# L1 deterministic probes, zero LLM, seconds to run. Hosted by the guard round
# (double shift). Three probes: A consumption-gap, B vanity-ratio, C research
# application-table gap. ASCII-only body per encoding law.
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$flags = 0

# --- Probe A: consumption gap - transferred ledger rows older than 14 days still not executed ---
Write-Output '=== PROBE A: consumption-gap (transferred >14d not executed) ==='
$cutoff = (Get-Date).AddDays(-14)
$pattern = '^\| P-(\d{4})-(\d{2})-(\d{2})-(\d+) \| (\d{2})-(\d{2}) \|'
foreach ($ln in (Get-Content (Join-Path $root 'cph4\evolution-ledger.md') -Encoding UTF8)) {
  if ($ln -match $pattern) {
    $rowDate = Get-Date -Year ([int]$Matches[1]) -Month ([int]$Matches[2]) -Day ([int]$Matches[3])
    if ($rowDate -lt $cutoff -and $ln -match '\| transferred') {
      $pid = $Matches[1] + '-' + $Matches[2] + '-' + $Matches[3] + '-' + $Matches[4]
      $age = [int]((Get-Date) - $rowDate).TotalDays
      Write-Output ('FLAG A: ' + $pid + ' transferred age=' + $age + 'd - dispatched, never closed (consumption gap / self-congratulation suspect)')
      $flags++
    }
  }
}
if ($flags -eq 0) { Write-Output 'OK A: no stale transferred rows' }

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
