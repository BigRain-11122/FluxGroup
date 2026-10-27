# fleet-silence-guard.ps1 - assertion gate for the "quiet machine" setup (PR-20261017-02)
# Two defects shipped as a recipe and survived 7 days because nothing verified them:
#   1) WT settings.json windowingBehavior="useExistingQuiet" - not a valid enum value.
#      WT rejects the WHOLE settings file and silently falls back to defaults.
#      Valid values: useNew | useAnyExisting | useExisting
#   2) keeper tab "Start-Sleep -Seconds 2147483647" - int32 max is 2147482+1=2147483
#      for this parameter; the overflow kills the keeper and throws a window on screen.
# This script checks the live WT settings and every wt-park.ps1 copy on disk.
# Exit 0 = all assertions PASS. Exit 1 = violation(s) printed.
# Usage: powershell -File Tools\fleet-silence-guard.ps1 [-ScanRoot K:\Fluxgroup]
param([string]$ScanRoot = '')

$ErrorActionPreference = 'Stop'
$fail = 0
$MAX_SLEEP = 2147483

function Fail([string]$msg) { $script:fail++; Write-Output ('FAIL ' + $msg) }
function Ok([string]$msg) { Write-Output ('ok   ' + $msg) }

# ---- 1. Windows Terminal settings ----
$wtPaths = @(
    (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'),
    (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json'),
    (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\settings.json')
)
$valid = @('useNew', 'useAnyExisting', 'useExisting')
$found = 0
foreach ($p in $wtPaths) {
    if (-not (Test-Path -LiteralPath $p)) { continue }
    $found++
    try {
        $j = Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Fail ('WT settings is not valid JSON: ' + $p + ' :: ' + $_.Exception.Message)
        continue
    }
    $wb = [string]$j.windowingBehavior
    if ($wb -eq '') { Ok ('WT settings has no windowingBehavior (default behaviour): ' + $p) }
    elseif ($valid -contains $wb) { Ok ('WT windowingBehavior=' + $wb + ' :: ' + $p) }
    else { Fail ('WT windowingBehavior="' + $wb + '" is not valid (allowed: ' + ($valid -join '|') + ') :: ' + $p) }
}
if ($found -eq 0) { Ok 'no Windows Terminal settings file on this machine (nothing to check)' }

# ---- 2. every wt-park.ps1 copy on disk ----
if ($ScanRoot -eq '') { $ScanRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
$copies = @(Get-ChildItem -LiteralPath $ScanRoot -Recurse -Filter 'wt-park.ps1' -File -ErrorAction SilentlyContinue)
if ($copies.Count -eq 0) { Fail ('no wt-park.ps1 found under ' + $ScanRoot) }
foreach ($f in $copies) {
    $hits = @(Select-String -LiteralPath $f.FullName -Pattern 'Start-Sleep\s+-Seconds\s+(\d+)' -AllMatches)
    if ($hits.Count -eq 0) { Fail ('no Start-Sleep found in ' + $f.FullName) ; continue }
    foreach ($h in $hits) {
        foreach ($m in $h.Matches) {
            $sec = [int]$m.Groups[1].Value
            if ($sec -gt $MAX_SLEEP) { Fail ('sleep too long (' + $sec + ' > ' + $MAX_SLEEP + ') in ' + $f.FullName) }
            else { Ok ('sleep ' + $sec + ' :: ' + $f.FullName) }
        }
    }
    $bad = @(Select-String -LiteralPath $f.FullName -Pattern 'windowingBehavior=useExistingQuiet')
    if ($bad.Count -gt 0) { Fail ('recipe comment still claims useExistingQuiet: ' + $f.FullName) }
}

Write-Output ('---- fleet-silence-guard: ' + $(if ($fail -eq 0) { 'PASS' } else { 'FAIL (' + $fail + ')' }))
exit ([int]($fail -gt 0))