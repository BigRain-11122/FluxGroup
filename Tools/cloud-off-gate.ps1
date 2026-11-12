# T0 CLOUD-OFF gate resolver (CEO 2026-10-20 order, CLOUD-OFF-LOCAL-ONLY-v1;
# canonical helper per D-20261028-08, ported from BigStream's self-tested
# src/os/cloud_off_gate.ps1).
#
# Marker: <FluxGroupRoot>\cph4\fleet\CLOUD-OFF-LOCAL-ONLY-v1.md
#
# Why both seeds: a scheduled task can register a sub-repo through a symlinked
# path (C:\Users\<user>\Desktop\FluxGroup\media -> D:\FluxGroup\media) whose
# ancestor tree carries a stale cph4 mirror without the marker. Walking the
# literal path alone silently finds nothing and the guard never fires. git
# reports the physical toplevel, so its ancestors are searched too.
#
# Usage (dot-source, never copy the logic into callers):
#   . "$PSScriptRoot\..\Tools\cloud-off-gate.ps1"
#   $gate = Resolve-CloudOffGate -ScriptRoot $PSScriptRoot -Project $repo
#   if (Test-CloudOffActive -Gate $gate) { ...suppress cloud spawn... }
#
# Fail-closed: an unresolvable/absent marker is reported by Get-CloudOffStatus
# as status=absent|error so callers can log one line and decide. Callers that
# spawn cloud CLI MUST treat resolution errors as "cloud off".
#
# Pure ASCII (powershell.exe 5.1 decodes BOM-less .ps1 as ANSI/GBK).

function Resolve-CloudOffGate {
    param(
        [string]$ScriptRoot = $PSScriptRoot,
        [string]$Project = '',
        [string]$MarkerName = 'CLOUD-OFF-LOCAL-ONLY-v1.md'
    )

    $seeds = New-Object System.Collections.Generic.List[string]
    if ($ScriptRoot) { $seeds.Add($ScriptRoot) }
    if ($Project) {
        try {
            $top = & git -C $Project rev-parse --show-toplevel 2>$null
            if ($LASTEXITCODE -eq 0 -and $top) {
                $seeds.Add(($top.Trim() -replace '/', '\'))
            }
        } catch { }
    }

    foreach ($seed in $seeds) {
        $cur = $seed
        while ($cur) {
            $marker = Join-Path $cur ('cph4\fleet\' + $MarkerName)
            if (Test-Path $marker) {
                return [pscustomobject]@{
                    Root      = $cur
                    Marker    = $marker
                    Status    = 'found'
                    ResolutionBase = $seed
                }
            }
            $parent = Split-Path -Parent $cur
            if (-not $parent -or $parent -eq $cur) { break }
            $cur = $parent
        }
    }

    return [pscustomobject]@{
        Root      = $null
        Marker    = $null
        Status    = 'absent'
        ResolutionBase = ($seeds -join ';')
    }
}

# One-line log form required by D-20261026-21 ③:
#   resolution_base=<path> marker=<found|absent>
function Format-CloudOffGateLine {
    param([pscustomobject]$Gate)
    if (-not $Gate) { return 'resolution_base= marker=absent' }
    return ('resolution_base=' + $Gate.ResolutionBase + ' marker=' + $Gate.Status)
}

# Fail-closed: only an explicit 'absent' marker lets cloud work through.
# Any resolution error, unreadable state, or malformed gate object = suppress.
function Test-CloudOffActive {
    param([pscustomobject]$Gate, [switch]$FailOpen)
    if ($null -eq $Gate) {
        if ($FailOpen) { return $false }
        return $true
    }
    switch ($Gate.Status) {
        'found'  { return $true }
        'absent' { return $false }
        default  { return $true }
    }
}

# D-20261112-02 (T1-v2) companion switch for automation rounds. The CEO unlock
# (commit 98a3f5ea8, 2026-10-23) retired the CLOUD-OFF marker, so automation
# entry points read an explicit allow switch instead:
#   cph4\fleet\CLOUD-ALLOW-AUTOMATION.md   (present = cloud rounds allowed)
# Fail-closed on every other state: absent marker, unreadable marker, or a
# marker whose mtime sits in the future (clock skew) all suppress the round.
# Negative-control contract per D-20261112-10:
#   present + healthy mtime     -> True  (spawn the CLI)
#   absent                      -> False (suppress + write log)
#   present + future mtime      -> False (clock anomaly, suppress)
# Usage:
#   $gate = Resolve-CloudOffGate -ScriptRoot $PSScriptRoot -Project $Project -MarkerName 'CLOUD-ALLOW-AUTOMATION.md'
#   if (-not (Test-CloudAutomationAllowed -Gate $gate)) { ...suppress + log... }
function Test-CloudAutomationAllowed {
    param([pscustomobject]$Gate)
    if ($null -eq $Gate) { return $false }
    if ($Gate.Status -ne 'found') { return $false }
    if (-not $Gate.Marker) { return $false }
    try {
        $item = Get-Item -LiteralPath $Gate.Marker -ErrorAction Stop
        if ($item.LastWriteTime -gt (Get-Date).AddMinutes(1)) { return $false }
    } catch { return $false }
    return $true
}