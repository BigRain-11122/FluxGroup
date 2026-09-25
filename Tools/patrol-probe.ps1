# patrol-probe.ps1 - Group Patrol mechanical probe v1.0 (CEO order 2026-09-25:
# periodic group-level inspection of every subsidiary + CPH4 labs + rectify).
# Zero-token evidence layer for the patrol model session (patrol-charter.md).
# READ-ONLY against every repo. ASCII-only body (encoding law) - all paths here
# are ASCII; Chinese-named ledger freshness is proxied by directory-newest-file
# scans so no non-ASCII literals ever enter this script.
# Reuses existing group tools as evidence (anti-duplication law #1, cadence.md):
#   Tools/fleet-audit.ps1  - machine heartbeat aggregation (stdout)
#   Tools/task-health.ps1  - scheduler health signals (stdout)
# Output: compact [ENTITY] blocks + [FLEET] [SCHED] [CARRY] blocks on stdout.
param([int]$CarryHours = 24)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot   # -> FluxGroup root

function AgeH([string]$p) {
    if (-not (Test-Path -LiteralPath $p)) { return 'MISSING' }
    try {
        $a = ((Get-Date) - (Get-Item -LiteralPath $p).LastWriteTime).TotalHours
        return ('{0:F1}h' -f [math]::Round($a, 1))
    } catch { return 'ERR' }
}
function DirNewest([string]$p) {
    if (-not (Test-Path -LiteralPath $p)) { return 'MISSING' }
    try {
        $f = Get-ChildItem -LiteralPath $p -File -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $f) { return 'EMPTY' }
        return ('{0:F1}h' -f [math]::Round(((Get-Date) - $f.LastWriteTime).TotalHours, 1))
    } catch { return 'ERR' }
}
function GitBlock([string]$p) {
    if (-not (Test-Path (Join-Path $p '.git'))) { return 'git=NO_REPO' }
    # PT-10 read-before-fetch law: local HEAD lags origin when the clone pull
    # channel stalls; fetch (refs only, working tree untouched) then judge
    # liveness by the freshest of local HEAD vs newest origin tip. Machine
    # branches (MiniGame machine/*) carry writer pushes while master folding lags.
    try { & git -C $p fetch --quiet 2>$null } catch { }
    $last = ''; $c7 = 0; $dirty = 0
    try { $last = (& git -C $p log -1 '--format=%cI' 2>$null) } catch { $last = '' }
    try { $c7 = @(& git -C $p log '--since=7 days ago' '--format=%h' 2>$null).Count } catch { $c7 = 0 }
    try { $dirty = @(& git -C $p status --porcelain 2>$null).Count } catch { $dirty = -1 }
    $tipTs = ''; $tipRef = ''
    try {
        $tipTs = [string](& git -C $p for-each-ref 'refs/remotes/origin' '--sort=-committerdate' '--count=1' '--format=%cI' 2>$null)
        if ($tipTs) {
            $tipRef = [string](& git -C $p for-each-ref 'refs/remotes/origin' '--sort=-committerdate' '--count=1' '--format=%(refname:short)' 2>$null)
            if (-not $tipRef) { $tipRef = 'origin-tip' }
        }
    } catch { $tipTs = ''; $tipRef = '' }
    $useTs = $last; $src = 'local'
    if ($tipTs) {
        $a = $null; $b2 = $null
        try { $a = [DateTimeOffset]::Parse($last) } catch { }
        try { $b2 = [DateTimeOffset]::Parse($tipTs) } catch { }
        if ($null -ne $b2 -and ($null -eq $a -or $b2 -gt $a)) { $useTs = $tipTs; $src = $tipRef }
    }
    $ageH = '-1'
    if ($useTs) {
        try { $c = [DateTimeOffset]::Parse($useTs); $ageH = ('{0:F1}h' -f [math]::Round(((Get-Date) - $c.LocalDateTime).TotalHours, 1)) } catch { $ageH = 'ERR' }
    }
    return ('last_commit=' + $ageH + ' tip=' + $src + ' commits7d=' + $c7 + ' dirty=' + $dirty)
}

Write-Output ('PROBE ts=' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))

# ---- per-entity blocks -------------------------------------------------------
$ents = @(
    @{ n = 'HQ';        sub = '';                     files = @('docs\orders.md', 'docs\decisions.md', 'docs\patrol-ledger.md', 'cph4\evolution-ledger.md'); dirs  = @('docs', 'cph4\registry') },
    @{ n = 'MiniGame';  sub = 'gaming\MiniGame';      files = @('STATUS-c.md', 'state-c.json', '.codely-cli\engine-tick\tick-ledger.txt', 'docs\STATUS.md'); dirs  = @('docs', 'Design\configs\GLOBAL') },
    @{ n = 'FluxVerse'; sub = 'gaming\FluxVerse';     files = @('watch\milestones.json', 'world\world-state.json'); dirs  = @('docs', 'watch') },
    @{ n = 'BigMoney';  sub = 'quant\bigmoney';      files = @(); dirs = @('fleet\orders', 'fleet\machines', 'knowledge') },
    @{ n = 'BigStream'; sub = 'media\BigStream';      files = @(); dirs = @('orders', 'output', 'research') },
    @{ n = 'BigLife';   sub = 'life\BigLife';         files = @('census\export\citizens-light.jsonl'); dirs = @('orders', 'census\export') },
    @{ n = 'BigDomain'; sub = 'domain\BigDomain';     files = @('orders.md', 'HQ-FEEDBACK.md'); dirs  = @('orders', 'src') },
    @{ n = 'BigCompute';sub = 'compute\BigCompute';   files = @(); dirs = @('orders', 'tasks') },
    @{ n = 'CPH4';      sub = 'cph4';                 files = @('evolution-ledger.md'); dirs = @('registry', 'research') }
)
foreach ($e in $ents) {
    $p = if ($e.sub) { Join-Path $root $e.sub } else { $root }
    $line = '[ENTITY ' + $e.n + '] ' + (GitBlock $p)
    foreach ($f in $e.files) { $line += (' file:' + ($f -replace '\\', '/') + '=' + (AgeH (Join-Path $p $f))) }
    foreach ($d in $e.dirs)  { $line += (' dir:' + ($d -replace '\\', '/') + 'newest=' + (DirNewest (Join-Path $p $d))) }
    Write-Output $line
}

# ---- fleet heartbeat aggregation (reuse, no re-collection) -------------------
try {
    Write-Output '[FLEET] fleet-audit.ps1 output:'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'fleet-audit.ps1') 2>$null | Select-Object -First 14 | ForEach-Object { Write-Output ('  ' + [string]$_) }
} catch { Write-Output '[FLEET] probe-fail (tool error, fail-open)' }

# ---- scheduler health (this machine) ----------------------------------------
try {
    Write-Output '[SCHED] task-health.ps1 output:'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'task-health.ps1') 2>$null | Select-Object -First 12 | ForEach-Object { Write-Output ('  ' + [string]$_) }
} catch { Write-Output '[SCHED] probe-fail (tool error, fail-open)' }

# ---- carry-over: open findings from previous patrols -------------------------
try {
    $led = Join-Path $root 'docs\patrol-ledger.md'
    $open = 0; $ids = @()
    if (Test-Path $led) {
        foreach ($ln in (Get-Content $led -Encoding UTF8)) {
            if ($ln -match '^\| (PT-\d{8}-\d+) ') {
                # capture id BEFORE the status match (a second -match overwrites $Matches)
                $ptId = $Matches[1]
                if ($ln -match '\| (OPEN|ESCALATED)[^|]*\|\s*$') { $open++; $ids += $ptId }
            }
        }
    }
    Write-Output ('[CARRY] open_findings=' + $open + (' ids=' + ($ids -join ',')))
} catch { Write-Output '[CARRY] parse-fail (fail-open)' }

Write-Output ('PROBE_DONE ts=' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
