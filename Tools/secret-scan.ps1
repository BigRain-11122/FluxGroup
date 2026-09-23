# secret-scan.ps1 - Group secret-leak gate (governance 7 / versioning 4.2)
# Scans recent commit diffs of all group repos for high-confidence secret patterns.
# Read-only. No popups (silence law). Report -> .codely-cli\secret-scan\ (gitignored).
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File Tools\secret-scan.ps1 [-Days 1]
# Exit:   0 = clean, 2 = high-confidence hits found (night round logs to ledger).
# New repo onboarding = add one line to $repos below (governance 2 registry).

param([int]$Days = 1)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot   # group repo root
$since = (Get-Date).AddDays(-$Days).ToString('yyyy-MM-dd')

$repos = @(
    $root,
    (Join-Path $root 'gaming\MiniGame'),
    (Join-Path $root 'quant\bigmoney'),
    (Join-Path $root 'media\BigStream'),
    (Join-Path $root 'gaming\FluxVerse'),
    (Join-Path $root 'domain\BigDomain'),
    (Join-Path $root 'life\BigLife')
)

# high-confidence patterns (P0). key: regex. id used for reporting.
$patterns = [ordered]@{
    'aws-access-key'  = 'AKIA[0-9A-Z]{16}'
    'github-pat'      = 'gh[pousr]_[A-Za-z0-9]{20,}'
    'openai-key'      = 'sk-(proj-)?[A-Za-z0-9]{20,}'
    'slack-token'     = 'xox[baprs]-[A-Za-z0-9-]{10,}'
    'telegram-bot'    = '\b[0-9]{8,10}:AA[A-Za-z0-9_-]{33}'
    'private-key-blk' = '-----BEGIN [A-Z ]*PRIVATE KEY-----'
}
$reList = @($patterns.Keys | ForEach-Object { $patterns[$_] })

$outDir = Join-Path $root '.codely-cli\secret-scan'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$report = Join-Path $outDir ("report-$stamp.txt")
$hits = @()
$scanned = 0

foreach ($repo in $repos) {
    if (-not (Test-Path (Join-Path $repo '.git'))) { continue }
    $scanned++
    $name = Split-Path -Leaf $repo
    if ($name -eq 'FluxGroup') { $name = 'HQ(FluxGroup)' }
    # stream: Select-String over git log -p (works identically on PS5.1/7, no array-capture quirks)
    $found = git -C $repo log --since=$since -p --no-color --diff-filter=AM 2>$null |
             Select-String -Pattern $reList -AllMatches
    foreach ($f in $found) {
        foreach ($m in $f.Matches) {
            $id = $null
            foreach ($k in $patterns.Keys) { if ($m.Value -match $patterns[$k]) { $id = $k; break } }
            $ln = $f.Line
            # long-line / base64 gate: real secrets sit on short lines; megabyte
            # base64 data-URIs cause regex false positives -> classify as P2 review
            if ($ln.Length -gt 1000 -or $ln -match 'base64,') {
                $hits += ("[P2-review] {0} | {1} | long/base64 line len={2} (weekly round review)" -f $name, $id, $ln.Length)
            } else {
                $hits += ("[P0] {0} | {1} | {2}" -f $name, $id, $ln.Trim())
            }
        }
    }
}

$header = "secret-scan $stamp | window=$Days day(s) | repos scanned: $scanned | hits: $($hits.Count) | P0: $(@($hits | Where-Object { $_.StartsWith('[P0]') }).Count) P2: $(@($hits | Where-Object { $_.StartsWith('[P2]') }).Count)"
$lines = @($header) + $hits
Set-Content -Path $report -Value $lines -Encoding ascii
Write-Output $header
if ($hits.Count -gt 0) {
    # cap stdout at 40 lines to respect silence/effort law; full list always in report file
    $hits | Select-Object -First 40 | ForEach-Object { Write-Output $_ }
    if ($hits.Count -gt 40) { Write-Output ("... full list in report: {0}" -f $report) }
    if (@($hits | Where-Object { $_.StartsWith('[P0]') }).Count -gt 0) { exit 2 }
    exit 0
}
exit 0
