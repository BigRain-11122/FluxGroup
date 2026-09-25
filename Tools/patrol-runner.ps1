# patrol-runner.ps1 - Group Patrol runner v1.0 (CEO order 2026-09-25).
# Wrapper for one headless patrol session (EngineTick pattern): single-flight
# lock + cross-machine claim stamp (cadence F-09) + zero-token probe + model
# session spawn (40-min hard timeout) + PATROL_DONE oracle + runtime ledger.
# Hosted anywhere (charter section 6); another machine seeing a fresh stamp
# (<20h) skips its weekly fire. ASCII-only body (encoding law).
# OS task: FluxGroup-PatrolRound weekly Mon 09:23 + manual Start-ScheduledTask.
param([switch]$Force)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot   # -> FluxGroup root
$runDir = Join-Path $root '.codely-cli\patrol'
if (-not (Test-Path $runDir)) { New-Item -ItemType Directory -Force -Path $runDir | Out-Null }
$lockFile = Join-Path $runDir 'patrol.lock'
$stampFile = Join-Path $runDir 'patrol-stamp.json'
$rtLedger = Join-Path $runDir 'patrol-ledger.txt'
$promptFile = Join-Path $PSScriptRoot 'patrol-prompt.txt'

# codely exe: same resolution chain as MiniGame EngineTick (machine.json then
# LOCALAPPDATA fallback) so any fleet machine can host this runner.
$codely = Join-Path $env:LOCALAPPDATA 'Programs\Tuanjie Cowork\cli\bin\win32-x64\codely.exe'
$mj = Join-Path $root 'gaming\MiniGame\tools\machine.json'
if (Test-Path $mj) {
    try { $j = Get-Content -Raw -Encoding UTF8 -Path $mj | ConvertFrom-Json; if ($j.codely_cli) { $codely = $j.codely_cli } } catch { }
}

# 1. single-flight lock (2h stale guard)
if (Test-Path $lockFile) {
    $age = (Get-Date) - (Get-Item $lockFile).LastWriteTime
    if ($age.TotalMinutes -lt 120) {
        Add-Content -Path $rtLedger -Value ('{0} | SKIP lock held (age {1:F0} min)' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $age.TotalMinutes)
        exit 0
    }
}

# 2. cross-machine claim stamp: a patrol ran <20h ago anywhere -> skip (weekly
#    task, one sweep per period fleet-wide). -Force overrides (manual re-run).
$stamp = $null
try { if (Test-Path $stampFile) { $stamp = Get-Content -Raw -Encoding UTF8 $stampFile | ConvertFrom-Json } } catch { $stamp = $null }
if (-not $Force -and $stamp -and $stamp.ts) {
    try {
        $sAge = ((Get-Date) - [DateTimeOffset]::Parse([string]$stamp.ts)).TotalHours
        if ($sAge -lt 20) {
            Add-Content -Path $rtLedger -Value ('{0} | SKIP stamp fresh (ts={1} host={2} age {3:F1}h)' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $stamp.ts, $stamp.host, $sAge)
            exit 0
        }
    } catch { }
}
Set-Content -Path $lockFile -Value (Get-Date -Format 'o')
try {
    $stampObj = [pscustomobject]@{ ts = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); host = $env:COMPUTERNAME }
    [IO.File]::WriteAllText($stampFile, ($stampObj | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
} catch { }

# 3. zero-token probe -> file the model session reads
$stampId = Get-Date -Format 'yyyyMMdd-HHmmss'
$probeOut = Join-Path $runDir ('probe-' + $stampId + '.txt')
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'patrol-probe.ps1') 2>$null | Out-File -FilePath $probeOut -Encoding UTF8

# 4. spawn the patrol model session
$exitInfo = 'UNKNOWN'
function Count-Done([string]$path) {
    $n = 0
    try { if (Test-Path $path) { $n = ([regex]::Matches((Get-Content $path -Raw -ErrorAction SilentlyContinue), 'PATROL_DONE')).Count } } catch { $n = 0 }
    return $n
}
$doneBefore = Count-Done $rtLedger
try {
    $prompt = [IO.File]::ReadAllText($promptFile, [System.Text.Encoding]::UTF8)
    $prompt = $prompt.Replace('__PROBE_FILE__', $probeOut).Replace('__RUN_ID__', $stampId)
    $argLine = '-p "' + $prompt.Replace('"', '').Replace("`r", ' ').Replace("`n", ' ') + '" --approval-mode yolo --disable-next-speaker-check'
    $outLog = Join-Path $runDir ('patrol-' + $stampId + '.out.log')
    $errLog = Join-Path $runDir ('patrol-' + $stampId + '.err.log')
    $p = Start-Process -FilePath $codely -ArgumentList $argLine -WorkingDirectory $root `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru -WindowStyle Hidden
    $killAt = (Get-Date).AddMinutes(40)
    $refreshAt = (Get-Date).AddMinutes(5)
    while (-not $p.HasExited) {
        if ((Get-Date) -ge $killAt) {
            $null = & taskkill /PID $p.Id /T /F 2>$null
            $exitInfo = 'EXIT_254_TIMEOUT_KILLED_40MIN'
            break
        }
        if ((Get-Date) -ge $refreshAt) { (Get-Item $lockFile).LastWriteTime = Get-Date; $refreshAt = (Get-Date).AddMinutes(5) }
        Start-Sleep -Seconds 5
    }
    $null = $p.WaitForExit()
    if ($exitInfo -eq 'UNKNOWN') {
        if ($null -ne $p.ExitCode) { $exitInfo = 'EXIT_' + $p.ExitCode } else { $exitInfo = 'EXIT_254_nullcode' }
    }
    # success oracle: PATROL_DONE marker delta in the runtime ledger (count
    # before/after - a stale marker from an older round never fakes a DONE).
    $doneNow = Count-Done $rtLedger
    if ($doneNow -gt $doneBefore) { $exitInfo = $exitInfo + ' DONE_SEEN' } else { $exitInfo = $exitInfo + ' NO_DONE_SUSPECT_CRASH' }
} catch {
    $exitInfo = 'SCRIPT_ERROR: ' + $_.Exception.Message + ' | exe=' + $codely
} finally {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}

Add-Content -Path $rtLedger -Value ('{0} | patrol {1} | {2} | probe={3}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $stampId, $exitInfo, $probeOut)
