# protected-hash-register.ps1 - hash-anchor registry tool (who-computes of the three-part program)
# BLUEPRINT v2 sec.9 / Phase 1-beta-1 (CEO order O-20261014-1745).
# Three-part program: who-computes = this tool; where-stored = Tools/protected-hash-registry.json
# (tracked in git); baseline = first -Register run hashes everything, later changes compare
# against the baseline.
#
# Protected-list law (BLUEPRINT sec.9, governance seat 1): changes to protected files are
# finalized by CEO order ONLY - panel signatures are nomination; the amendment channel is
# governance sec.9. Drift handling = verify a CEO order number is on file -> re-register with
# -Register (registry records the order) -> no order = restore + report.
#
# Usage (silent-law compliant, no console spawn):
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\protected-hash-register.ps1 -Register
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\protected-hash-register.ps1 -Verify [-SkipMissing]
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\protected-hash-register.ps1 -VerifyFile <repo-relative-path>
#
# Modes: strict = verify FAILS on hash drift; dynamic = report-only (for the auto-regenerated
# visualization artifacts until the per-generation hash log lands inside generate.ps1 - the
# "每次生成留哈希档" integration is a pending MiniGame-lane follow-up).
param([switch]$Register,[switch]$Verify,[string]$VerifyFile,[switch]$SkipMissing)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Registry = Join-Path $PSScriptRoot 'protected-hash-registry.json'

# Protected list (canon = BLUEPRINT v2 sec.9): CHARTER/ROUND (cron-prompt carrier), core Tools
# four (dispatcher/atomic-push/no-reversal/task-register), L0-chain scripts, event/probe/SLI
# enforcement bodies (Phase 1-alpha), metaverse HTML trio + generate.ps1 (CEO first-check entry)
# plus its source pair canonical.html/strings.json/sync-template.ps1 (nomination-face extension,
# closes the real edit surface upstream of the named trio).
$Protected = @(
    @{ path = 'cph4/fleet/dispatcher/CEO-PROXY/CHARTER.md';   mode = 'strict' },
    @{ path = 'cph4/fleet/dispatcher/CEO-PROXY/ROUND.md';     mode = 'strict' },
    @{ path = 'Tools/fleet-dispatcher.ps1';                   mode = 'strict' },
    @{ path = 'Tools/fleet-idle-watch.ps1';                  mode = 'strict' },
    @{ path = 'Tools/fleet-reality.ps1';                     mode = 'strict' },
    @{ path = 'Tools/git-atomic-push.py';                    mode = 'strict' },
    @{ path = 'Tools/git-no-reversal-check.py';              mode = 'strict' },
    @{ path = 'Tools/task-register.ps1';                     mode = 'strict' },
    @{ path = 'Tools/proxy-event-carrier.ps1';                mode = 'strict' },
    @{ path = 'Tools/proxy-probe.ps1';                       mode = 'strict' },
    @{ path = 'Tools/sli-reconcile.ps1';                     mode = 'strict' },
    @{ path = 'cph4/fleet/dispatcher/PATROL-FLEET/BLUEPRINT.md';  mode = 'strict' },
    @{ path = 'cph4/fleet/dispatcher/PATROL-FLEET/CHARTERS.md';    mode = 'strict' },
    @{ path = 'Tools/patrol-fleet-carrier.ps1';               mode = 'strict' },
    @{ path = 'Tools/patrol-fleet-config.json';               mode = 'strict' },
    @{ path = 'gaming/MiniGame/tools/siliconwatch/generate.ps1';      mode = 'strict' },
    @{ path = 'gaming/MiniGame/tools/siliconwatch/canonical.html';    mode = 'strict' },
    @{ path = 'gaming/MiniGame/tools/siliconwatch/strings.json';      mode = 'strict' },
    @{ path = 'gaming/MiniGame/tools/siliconwatch/sync-template.ps1'; mode = 'strict' },
    @{ path = 'gaming/MiniGame/硅基生命元宇宙.template.html';          mode = 'strict' },
    @{ path = 'gaming/MiniGame/硅基生命元宇宙.html';                  mode = 'dynamic' },
    @{ path = 'gaming/MiniGame/硅基生命元宇宙-data.js';               mode = 'dynamic' }
)

function Get-Sha256([string]$abs) {
    $fs = [System.IO.File]::OpenRead($abs)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $hash = $sha.ComputeHash($fs)
        return ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLower()
    } finally { $fs.Close() }
}

function Get-Entry([string]$path) {
    foreach ($e in $Protected) { if ($e.path -eq $path) { return $e } }
    return $null
}

if ($VerifyFile) {
    $e = Get-Entry $VerifyFile
    if (-not $e) { Write-Output ('NOT-IN-LIST: ' + $VerifyFile); exit 1 }
    $abs = Join-Path $Root ($VerifyFile -replace '/', '\')
    if (-not (Test-Path $abs)) { Write-Output ('MISSING: ' + $VerifyFile); exit 1 }
    $h = Get-Sha256 $abs
    Write-Output ($VerifyFile + ' sha256=' + $h)
    if (Test-Path $Registry) {
        $reg = Get-Content $Registry -Raw -Encoding UTF8 | ConvertFrom-Json
        $hit = $null
        foreach ($f in @($reg.files)) { if ($f.path -eq $VerifyFile) { $hit = $f } }
        if ($hit) {
            if ($hit.sha256 -eq $h) { Write-Output 'MATCH baseline'; exit 0 }
            elseif ($hit.mode -eq 'dynamic') { Write-Output 'DYNAMIC-CHANGED (report-only)'; exit 0 }
            else { Write-Output 'DRIFT vs baseline (protected-file change needs CEO order)'; exit 1 }
        }
        Write-Output 'no baseline entry for this path (registry stale?)'; exit 1
    }
    Write-Output 'registry not found - run -Register first'; exit 1
}

if ($Register) {
    $files = @()
    $missing = 0
    foreach ($e in $Protected) {
        $abs = Join-Path $Root ($e.path -replace '/', '\')
        if (-not (Test-Path $abs)) { Write-Output ('MISSING (skipped): ' + $e.path); $missing++; continue }
        $item = Get-Item $abs
        $files += [ordered]@{ path = $e.path; mode = $e.mode; sha256 = (Get-Sha256 $abs); bytes = $item.Length }
    }
    $reg = [ordered]@{
        meta = [ordered]@{
            generated = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
            order = 'O-20261014-2250 (PATROL-FLEET build order: fleet canon x4 added to the list; supersedes the O-20261014-1745 Phase 1-beta-1 baseline)'
            law = 'protected-file changes = CEO order ONLY (panel signature = nomination face; channel = governance sec.9)'
            note = 'strict = verify fails on drift; dynamic = report-only until per-generation hash log lands in generate.ps1 (pending MiniGame-lane integration). Re-register ONLY under a CEO order number - record it in meta.order when superseding.'
        }
        files = $files
    }
    $json = ConvertTo-Json $reg -Depth 5
    [System.IO.File]::WriteAllText($Registry, $json, (New-Object System.Text.UTF8Encoding $false))
    if ($missing -gt 0) { Write-Output ('WARNING: ' + $missing + ' protected file(s) missing on this machine') }
    Write-Output ('REGISTERED ' + $files.Count + '/' + $Protected.Count + ' files -> ' + $Registry)
    exit 0
}

if ($Verify) {
    if (-not (Test-Path $Registry)) { Write-Output 'registry not found - run -Register first'; exit 1 }
    $reg = Get-Content $Registry -Raw -Encoding UTF8 | ConvertFrom-Json
    $drift = 0; $ok = 0; $dyn = 0
    foreach ($f in @($reg.files)) {
        $abs = Join-Path $Root ($f.path -replace '/', '\')
        if (-not (Test-Path $abs)) {
            if ($SkipMissing) { Write-Output ('SKIP-MISSING: ' + $f.path) } else { Write-Output ('DRIFT-MISSING: ' + $f.path); $drift++ }
            continue
        }
        $h = Get-Sha256 $abs
        if ($h -eq $f.sha256) { $ok++; Write-Output ('OK: ' + $f.path) }
        elseif ($f.mode -eq 'dynamic') { $dyn++; Write-Output ('DYNAMIC-CHANGED (report-only): ' + $f.path) }
        else { $drift++; Write-Output ('DRIFT: ' + $f.path + '  baseline=' + $f.sha256.Substring(0,12) + ' now=' + $h.Substring(0,12)) }
    }
    Write-Output ('SUMMARY: ok=' + $ok + ' dynamic-changed=' + $dyn + ' drift=' + $drift + ' (baseline ' + $reg.meta.generated + ')')
    if ($drift -gt 0) { Write-Output 'VERIFY FAIL: protected-file drift - CEO-order-only channel (governance sec.9)'; exit 1 }
    Write-Output 'VERIFY PASS: all strict entries match baseline'
    exit 0
}

Write-Output 'usage: -Register | -Verify [-SkipMissing] | -VerifyFile <repo-relative-path>'
exit 1
