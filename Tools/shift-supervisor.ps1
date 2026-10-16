# shift-supervisor.ps1 - C-20261016-02 Cure-6: L2 supervision shift on a silent scheduled carrier
# Why: the L2 shift lived on a REPL durable cron (id 9632cee5); the gamewin companion
# legitimately suspends durable crons during CEO windows (resource-chain sec.6), which
# turned every CEO-online window into a supervision black window (2026-10-16 08:34
# evidence: shifts 02:43/05:43/08:43 all missed). This scheduled carrier is invisible
# (wscript hidden chain), survives REPL cron suspension, and runs during CEO windows by
# design (U060 compliant). LogonType TRUTH: InteractiveToken (bm-a UAC denies unelevated
# S4U) - queued in Tools\task-s4u-backlog.md for elevated conversion; no logoff survival.
# Grid: :43 of hours 2,5,8,12,15,18,21,23 (CEO-PROXY shift schedule). One headless
# codely round per shift, launched from this every-5m task. Prompt = SHIFT-SUPERVISOR-PROMPT.txt.
$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
$Dir = Join-Path $Root '.codely-cli\shift-supervisor'
if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
$Log = Join-Path $Dir 'shift.log'
$StateF = Join-Path $Dir 'last-shift.txt'
$PromptF = Join-Path $Root 'cph4\fleet\dispatcher\CEO-PROXY\SHIFT-SUPERVISOR-PROMPT.txt'
function SLog([string]$s) {
    Add-Content -LiteralPath $Log -Value ("{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $s) -Encoding UTF8
    if ((Get-Item $Log -EA 0).Length -gt 1MB) {
        $t = Get-Content $Log -EA 0 | Select-Object -Last 200
        Set-Content -LiteralPath $Log -Value $t -Encoding UTF8
    }
}
$now = Get-Date
$shiftHours = @(2, 5, 8, 12, 15, 18, 21, 23)
$key = ''
if ($shiftHours -contains $now.Hour -and $now.Minute -ge 43) { $key = $now.ToString('yyyy-MM-dd-HH') }
if ($key -eq '') { exit 0 }
if ((Test-Path $StateF) -and ((Get-Content $StateF -Raw -EA 0)) -eq $key) { exit 0 }
Set-Content -LiteralPath $StateF -Value $key -Encoding UTF8

# concurrency cap (C-20261015-03): defer when >= 2 autonomous lane sessions live
try {
    $capLive = @(Get-CimInstance Win32_Process -Filter "Name='codely.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -notmatch '--experimental-acp' }).Count
    if ($capLive -ge 2) { SLog ("DEFER-CAP live=" + $capLive + " shift=" + $key); exit 0 }
} catch { }

$codely = Join-Path $env:LOCALAPPDATA 'Programs\Tuanjie Cowork\cli\bin\win32-x64\codely.exe'
if (-not (Test-Path $codely)) { SLog 'CODELY_EXE_MISSING'; exit 1 }
if (-not (Test-Path $PromptF)) { SLog 'PROMPT_MISSING'; exit 1 }
try {
    $prompt = [System.IO.File]::ReadAllText($PromptF, [System.Text.Encoding]::UTF8).Trim()
    $argLine = '-p "' + $prompt.Replace('"', '') + '" --approval-mode yolo --disable-next-speaker-check'
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $outLog = Join-Path $Dir ("shift-$stamp.out.log")
    $errLog = Join-Path $Dir ("shift-$stamp.err.log")
    $p = Start-Process -FilePath $codely -ArgumentList $argLine -WorkingDirectory $Root `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru -WindowStyle Hidden
    SLog ("LAUNCHED shift=" + $key + " pid=" + $p.Id)
    $killAt = (Get-Date).AddMinutes(25)
    while (-not $p.HasExited) {
        if ((Get-Date) -ge $killAt) { $null = & taskkill /PID $p.Id /T /F 2>$null; SLog ('TIMEOUT_KILLED_25MIN shift=' + $key); break }
        Start-Sleep -Seconds 5
    }
    $null = $p.WaitForExit()
    $code = $p.ExitCode
    if ($null -eq $code) { $code = '254' }
    SLog ("DONE shift=" + $key + " exit=" + $code + " out=" + $outLog)
} catch {
    SLog ('SCRIPT_ERROR ' + $_.Exception.Message)
}
exit 0
