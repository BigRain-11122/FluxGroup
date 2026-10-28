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
        [string]$Project = ''
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
            $marker = Join-Path $cur 'cph4\fleet\CLOUD-OFF-LOCAL-ONLY-v1.md'
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