#!/usr/bin/env pwsh
# resume-local-business.ps1 - undo Tools/pause-local-business.ps1 (CEO 2026-10-29).
# Reads the recorded list; enabling only what was switched off, never guessing.
$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$f = Join-Path $root '.codely-cli\tmp\paused-business.json'
if (-not (Test-Path $f)) { "no pause record ($f)"; exit 1 }
$rec = Get-Content -Raw -Encoding UTF8 $f | ConvertFrom-Json
$on = @()
foreach ($n in @($rec.paused)) {
    $t = Get-ScheduledTask -TaskName $n
    if (-not $t) { continue }
    schtasks /change /tn $n /enable | Out-Null
    if ((Get-ScheduledTask -TaskName $n).State -ne 'Disabled') { $on += $n }
}
@{ ts = (Get-Date -Format s); mode = 'resume-all-business'; resumed = $on } |
    ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $f -Encoding UTF8
"resumed=$($on.Count) of $($rec.paused.Count)"