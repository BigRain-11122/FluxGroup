# Group selfaudit scanner v1.0 - anti-hallucination claim sweep (governance §10).
# Sweeps recent commit messages across the 5 repos for CLAIM words, then marks
# each claim's evidence availability. Output: docs/selfaudit-report.md draft for
# the weekly evolution round (governance §10.3 third line of defense).
# ASCII-only (encoding law). READ-ONLY against all repos.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File Tools\selfaudit.ps1 [-Days 1]

param([int]$Days = 1)

$root = Split-Path -Parent $PSScriptRoot   # -> FluxGroup root
$repos = [ordered]@{
  'fluxgroup' = $root
  'minigame'  = (Join-Path $root 'gaming\MiniGame')
  'bigmoney'  = (Join-Path $root 'quant\bigmoney')
  'bigstream' = (Join-Path $root 'media\BigStream')
  'fluxverse' = (Join-Path $root 'gaming\FluxVerse')
}
# claim markers (CJK kept out of this script; matched via codepoints)
$L = [string][char]0x5B8C   # wan-  (part of "wancheng" = completed)
$C = [string][char]0x901A   # tong- (part of "tongguo" = passed)
$claimRe = '(?i)\b(done|PASS|passed|fixed|verified|delivered|completed|shipped)\b|' + $L + '|' + $C
$report = @()
$report += ('# Self-Audit Report (auto-generated) - claims sweep, last ' + $Days + ' day(s)')
$report += ''
$report += '> governance.md section 10 draft. THIRD-LINE defense input for the weekly'
$report += '> evolution round. A claim with NO evidence marker is a hallucination candidate.'
$report += ''
$since = (Get-Date).ToUniversalTime().AddDays(-$Days).ToString('yyyy-MM-ddTHH:mm:ss')
$counts = @{ claims=0; backed=0; bare=0 }

foreach ($name in @($repos.Keys)) {
  $d = $repos[$name]
  if (-not (Test-Path (Join-Path $d '.git'))) { continue }
  $lines = @(& git -C $d log --since="$since" --pretty='%H|%aI|%s' 2>$null)
  if (-not $lines) { continue }
  $repoClaims = 0
  $repoBare = 0
  foreach ($ln in $lines) {
    if (-not $ln) { continue }
    $p = $ln -split '\|', 3
    if ($p.Count -lt 3) { continue }
    $sha = $p[0].Substring(0,10); $when = $p[1]; $msg = $p[2]
    $hit = @([regex]::Matches($msg, $claimRe)).Count
    if ($hit -eq 0) { continue }
    $repoClaims++
    $counts.claims++
    # evidence availability: files touched in that commit
    $files = @(& git -C $d show --stat --pretty='' $p[0] 2>$null)
    $touched = ($files | Where-Object { $_ -match '\|' }).Count
    if ($touched -gt 0) { $counts.backed++ ; $ev = ('files=' + $touched) }
    else { $counts.bare++; $repoBare++; $ev = 'NO-FILES' }
    $short = $msg; if ($short.Length -gt 100) { $short = $short.Substring(0,100) }
    $report += ('- [' + $name + '] ' + $sha + ' ' + $ev + ' :: ' + $short)
  }
  if ($repoClaims -gt 0) { $report += ('  -> repo ' + $name + ': ' + $repoClaims + ' claim(s), ' + $repoBare + ' bare') }
}
$report += ''
$report += ('## Summary: claims=' + $counts.claims + ' evidence-backed=' + $counts.backed + ' bare(no-files)=' + $counts.bare)
$report += '## Round duty: bare claims and keyword-heavy claims get RE-VERIFIED by the evolution round AI (governance 10.3).'
$outFile = Join-Path $root 'docs\selfaudit-report.md'
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($outFile, ($report -join "`r`n") + "`r`n", $utf8)
Write-Output ('selfaudit done: claims=' + $counts.claims + ' backed=' + $counts.backed + ' bare=' + $counts.bare + ' -> docs/selfaudit-report.md')
