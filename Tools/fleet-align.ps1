# fleet-align.ps1 - one command to put any Windows fleet box under the bm-m master (2026-10-29)
# CEO order: all prohibitions lifted except cloud-token saving; the fleet serves the Mac master.
#
# What it does (idempotent, no cloud, no console windows):
#   1) fetch origin, try the official hot-sync, but never destroy local work
#   2) make sure Tools\fleet\lane_agent.py exists; if the worktree is too stale,
#      build a clean control-plane runtime at C:\Fluxgroup\FleetRuntime and sync it
#   3) make sure HQ-ProductionClaim exists and points at the lane runner
#   4) run heartbeat + POOL claim + a DRY lane tick, then print a receipt JSON
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-align.ps1 -Node bm-c
#   ... -Root K:\Fluxgroup\FluxGroup        (default root is derived from this script)
param(
    [Parameter(Mandatory = $true)][string]$Node,
    [string]$Root = '',
    [string]$Runtime = 'C:\Fluxgroup\FleetRuntime',
    [switch]$RegisterTask
)
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if (-not $Root) {
    $Root = Split-Path -Parent $PSScriptRoot
    if ($Root -match '\\Tools$') { $Root = Split-Path -Parent $Root }
}
$receipt = [ordered]@{ node = $Node; root = $Root; rc = 0; steps = @(); head = $null; lane = $null }

function Step([string]$name, [string]$detail) {
    $receipt.steps += [ordered]@{ step = $name; detail = $detail }
    Write-Output ("[{0}] {1}" -f $name, $detail)
}

# --- python ---------------------------------------------------------------
$py = $null
foreach ($c in @('python', 'C:\Program Files\Python311\python.exe')) {
    try { $v = & $c --version 2>$null; if ($LASTEXITCODE -eq 0) { $py = $c; break } } catch { }
}
if (-not $py) { Step 'python' 'MISSING - install Python 3 first'; $receipt.rc = 2; $receipt | ConvertTo-Json -Depth 5; exit 2 }
Step 'python' $py

# --- 1. fetch + hot-sync --------------------------------------------------
& git -C $Root fetch origin main --quiet 2>$null
$head = (& git -C $Root rev-parse --short HEAD 2>$null)
$behind = (& git -C $Root rev-list --count HEAD..origin/main 2>$null)
Step 'fetch' ("head=$head behind=$behind")
$hot = Join-Path $Root 'Tools\fleet-hot-sync.ps1'
if (Test-Path $hot) {
    try { & $hot *> $null; Step 'hot-sync' 'ran' } catch { Step 'hot-sync' "failed: $($_.Exception.Message)" }
} else { Step 'hot-sync' 'script absent (stale worktree)' }

# --- 2. lane executor -----------------------------------------------------
$lane = Join-Path $Root 'Tools\fleet\lane_agent.py'
if (-not (Test-Path $lane)) {
    Step 'worktree' 'lane_agent.py absent -> building runtime'
    if (-not (Test-Path $Runtime)) {
        & git clone --filter=blob:none --sparse 'https://github.com/BigRain-11122/FluxGroup.git' $Runtime *> $null
    }
    $sync = Join-Path $Root 'Tools\fleet-sync.py'
    if (-not (Test-Path $sync)) {
        New-Item -ItemType Directory -Force -Path (Split-Path $sync) | Out-Null
        & git -C $Root show origin/main:Tools/fleet-sync.py 2>$null | Set-Content -LiteralPath $sync -Encoding UTF8
    }
    & $py $sync --src $Root --dst $Runtime *> $null
    $laneRoot = $Runtime
} else { $laneRoot = $Root }
$laneScript = Join-Path $laneRoot 'Tools\fleet\lane_agent.py'
if (-not (Test-Path $laneScript)) { Step 'lane' 'MISSING after sync'; $receipt.rc = 2; $receipt | ConvertTo-Json -Depth 5; exit 2 }
Step 'lane' $laneScript

# --- 3. claim task --------------------------------------------------------
$taskName = 'HQ-ProductionClaim'
$runner = Join-Path $laneRoot 'Tools\hq-lane-claim.bat'
if (-not (Test-Path $runner)) {
    @(
        '@echo off',
        'cd /d "' + $laneRoot + '" || exit /b 1',
        'set PYTHONIOENCODING=utf-8',
        'set LOG=cph4\fleet\queue-receipts\_lane_task.log',
        'if not exist cph4\fleet\queue-receipts mkdir cph4\fleet\queue-receipts',
        $py + ' Tools\fleet-sync.py --src "' + $Root + '" --dst "' + $laneRoot + '" >> "%LOG%" 2>&1',
        $py + ' Tools\fleet\fleet_hb.py --node ' + $Node + ' --root "%CD%" >> "%LOG%" 2>&1',
        $py + ' Tools\queue_claim.py --pool --node ' + $Node + ' >> "%LOG%" 2>&1',
        $py + ' Tools\fleet\lane_agent.py --node ' + $Node + ' --root "%CD%" --max-seconds 600 >> "%LOG%" 2>&1',
        'exit /b %ERRORLEVEL%'
    ) | Set-Content -LiteralPath $runner -Encoding ASCII
}
$t = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($RegisterTask -and -not $t) {
    $reg = Join-Path $Root 'Tools\task-register.ps1'
    if (Test-Path $reg) {
        & $reg -Name $taskName -Script $runner -Trigger 'every:5m' -Description "lane claim ($Node) aligned to bm-m master"
        Step 'task' 'registered'
    } else { Step 'task' 'task-register.ps1 absent' }
} elseif ($t) { Step 'task' ("present state=" + $t.State) } else { Step 'task' 'absent (re-run with -RegisterTask)' }

# --- 4. live checks -------------------------------------------------------
$env:PYTHONIOENCODING = 'utf-8'
Push-Location $laneRoot
try {
    $hb = & $py 'Tools\fleet\fleet_hb.py' --node $Node --root (Get-Location).Path 2>&1 | Select-Object -Last 1
    Step 'heartbeat' ($hb -join ' ')
    $dry = & $py 'Tools\fleet\lane_agent.py' --node $Node --root (Get-Location).Path --dry 2>&1 | Select-Object -Last 2
} finally { Pop-Location }
$receipt.lane = ($dry -join ' | ')
Step 'lane-dry' $receipt.lane
$receipt.head = $head

$out = Join-Path $Root ("cph4\fleet\queue-receipts\fleet-align-" + $Node + ".json")
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Output ("RECEIPT " + $out)
exit 0