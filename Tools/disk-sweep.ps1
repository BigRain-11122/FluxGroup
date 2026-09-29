# disk-sweep.ps1 - Group decisive disk census + Class-A sweeper v1.0 (CPH4 Labs)
# Charter: cph4/resource-chain.md sec.3 sec.11 (CEO order 2026-09-29 decisiveness law:
# "manage and clean decisively, do not be too conservative").
# Census: suspect-list size report + ollama model face + per-repo auto-saves face.
# -Sweep additionally executes Class-A direct-clean (regenerable-by-nature classes,
# no quarantine per the same order) with one receipt line per action.
# Class-B (unused models / closed spikes / big binaries) = REPORT ONLY here;
# judgement + purge dating stays with the rounds (in-flight-reference gate first).
# Read-only unless -Sweep. ASCII-only body (encoding law). PS 5.1 safe.

param([switch]$Sweep)

$root = Split-Path -Parent $PSScriptRoot
$free0 = (Get-PSDrive C).Free
function MB($p) {
    if (-not (Test-Path -LiteralPath $p)) { return -1 }
    $b = (Get-ChildItem -LiteralPath $p -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    if (-not $b) { $b = 0 }
    [math]::Round($b / 1MB)
}
Write-Output ('DISK SWEEP ' + (Get-Date -Format 'yyyy-MM-dd HH:mm') + ' free=' + [math]::Round($free0 / 1GB) + 'GB sweep=' + $Sweep.IsPresent)

$suspects = [ordered]@{
    'docs/_trash'       = 'docs\_trash'
    'labbench'          = '.codely-cli\labbench'
    'audio-staging'     = '.codely-cli\audio-staging'
    'root-hf-cache'     = 'HFCACHE'
    'win-temp'          = 'WINTEMP'
    'minigame-git'      = 'gaming\MiniGame\.git'
    'minigame-projects' = 'gaming\MiniGame\projects'
    'media'             = 'media'
}
foreach ($k in @($suspects.Keys)) {
    $v = $suspects[$k]
    if ($v -eq 'HFCACHE') { $p = Join-Path $env:USERPROFILE '.cache\huggingface' }
    elseif ($v -eq 'WINTEMP') { $p = Join-Path $env:LOCALAPPDATA 'Temp' }
    else { $p = Join-Path $root $v }
    $m = MB $p
    Write-Output ('{0,-18} {1,8} MB' -f $k, $m)
}

Write-Output '--- labbench experiment areas (sec.11.7: >5GB closed spike = purge review)'
Get-ChildItem (Join-Path $root '.codely-cli\labbench') -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $m = MB $_.FullName
    if ($m -gt 10) { Write-Output ('labbench/' + $_.Name + ' = ' + $m + 'MB') }
}

Write-Output '--- ollama model face (matrix reconciliation = round judgement)'
try { $om = & ollama list 2>$null; if ($om) { $om | Write-Output } } catch { }

Write-Output '--- per-repo auto-saves (watermark 30d / 500 files)'
foreach ($r in @('gaming\MiniGame', 'quant\bigmoney', 'media\BigStream', 'life\BigLife', 'domain\BigDomain', 'compute\BigCompute', 'gaming\FluxVerse')) {
    $m = MB (Join-Path $root ($r + '\.codely-cli\auto-saves'))
    if ($m -gt 0) { Write-Output ('auto-saves ' + $r + ' = ' + $m + 'MB') }
}

if (-not $Sweep) {
    Write-Output 'CENSUS-ONLY (add -Sweep to execute Class-A decisive clean per resource-chain sec.11)'
    return
}

# ---- Class-A direct-clean (CEO decisiveness order: no quarantine for regenerable classes) ----
# A1 quarantine-expired: docs/_trash files older than 7 days (mtime proxy)
$t = Join-Path $root 'docs\_trash'
if (Test-Path $t) {
    $old = @(Get-ChildItem $t -Recurse -File -Force -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) })
    if ($old.Count -gt 0) {
        $sz = ($old | Measure-Object Length -Sum).Sum; if (-not $sz) { $sz = 0 }
        $old | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Output ('SWEEP A1 quarantine-expired: ' + $old.Count + ' files ' + [math]::Round($sz / 1MB) + 'MB')
    }
}
# A2 windows temp older than 7 days
$old = @(Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Temp') -Recurse -File -Force -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) })
if ($old.Count -gt 0) {
    $sz = ($old | Measure-Object Length -Sum).Sum; if (-not $sz) { $sz = 0 }
    $old | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Output ('SWEEP A2 win-temp>7d: ' + $old.Count + ' files ' + [math]::Round($sz / 1MB) + 'MB')
}
# A3 root hf cache (re-downloadable)
$hf = Join-Path $env:USERPROFILE '.cache\huggingface'
if (Test-Path $hf) {
    $m = MB $hf
    Remove-Item $hf -Recurse -Force -ErrorAction SilentlyContinue
    if ($m -gt 0) { Write-Output ('SWEEP A3 hf-cache: ' + $m + 'MB') }
}
# A4 audio staging (transit zone)
$asg = Join-Path $root '.codely-cli\audio-staging'
if (Test-Path $asg) {
    $m = MB $asg
    Remove-Item (Join-Path $asg '*') -Recurse -Force -ErrorAction SilentlyContinue
    if ($m -gt 0) { Write-Output ('SWEEP A4 audio-staging: ' + $m + 'MB') }
}
# A5 .incomplete download corpses older than 48h under .codely-cli (in-flight resumes protected by age gate)
$old = @(Get-ChildItem (Join-Path $root '.codely-cli') -Recurse -File -Force -Filter '*.incomplete' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-48) })
if ($old.Count -gt 0) {
    $sz = ($old | Measure-Object Length -Sum).Sum; if (-not $sz) { $sz = 0 }
    $old | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Output ('SWEEP A5 incomplete-corpses>48h: ' + $old.Count + ' files ' + [math]::Round($sz / 1MB) + 'MB')
}
Write-Output ('SWEEP DONE freed=' + [math]::Round(((Get-PSDrive C).Free - $free0) / 1MB) + 'MB free=' + [math]::Round((Get-PSDrive C).Free / 1GB) + 'GB')
