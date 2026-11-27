# perf_max.ps1 - raise this Windows box to maximum performance (reversible)
# Order: OB-20261103-1240-BMB-PERF-MAX (CEO 2026-11-03 "b 把本机的性能释放调到最高")
#
# What it changes (all reversible, none of it touches Defender / Windows Update):
#   1. power plan -> Ultimate Performance (falls back to High performance)
#   2. CPU min/max state 100%, aggressive boost, active cooling
#   3. no disk sleep, no USB selective suspend
#   4. Windows Power Throttling off (registry)
#   5. NVIDIA persistence mode on (keeps clocks ready, no overclock)
# Rollback:  powercfg /setactive SCHEME_BALANCED
#            reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling" /v PowerThrottlingOff /f
#            nvidia-smi -pm 0

param([string]$Node = "bm-b", [string]$Repo = "")

$ErrorActionPreference = "Continue"
if (-not $Repo) { $Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path }
Set-Location $Repo
$logDir = Join-Path $Repo "cph4\fleet\queue-receipts"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$log = Join-Path $logDir ("perf-max-{0}-{1}.log" -f $Node, (Get-Date -Format "yyyyMMdd-HHmmss"))

function Say([string]$m) {
    Write-Host $m
    Add-Content -Path $log -Value $m -Encoding UTF8
}

$rc = 0
Say "================================================"
Say (" perf_max node={0}" -f $Node)
Say (" host={0}" -f $env:COMPUTERNAME)
Say (" repo={0}" -f $Repo)
Say (" log ={0}" -f $log)
Say "================================================"

# --- 0. admin check -------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Say "ERROR: not running as Administrator. Right-click the launcher -> Run as administrator."
    exit 2
}

# --- 1. power plan -------------------------------------------------------
Say ""
Say "[1/5] power plan"
$before = (powercfg /getactivescheme) 2>&1
Say ("  current: {0}" -f $before)

$ultimateGuid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
$dup = (powercfg -duplicatescheme $ultimateGuid) 2>&1
Say ("  duplicatescheme: {0}" -f ($dup -join " "))
$target = $null
$m = [regex]::Match(($dup -join " "), "([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")
if ($m.Success) { $target = $m.Groups[1].Value }

if ($target) {
    powercfg /setactive $target 2>&1 | Out-Null
    Say ("  activated Ultimate Performance: {0}" -f $target)
} else {
    # already exists or unsupported -> High performance
    $list = (powercfg /list) 2>&1 | Out-String
    $mm = [regex]::Match($list, "([0-9a-fA-F-]{36})\s*\(Ultimate Performance\)")
    if ($mm.Success) {
        $target = $mm.Groups[1].Value
        powercfg /setactive $target 2>&1 | Out-Null
        Say ("  activated existing Ultimate Performance: {0}" -f $target)
    } else {
        powercfg /setactive SCHEME_MIN 2>&1 | Out-Null
        $target = "SCHEME_MIN"
        Say "  Ultimate Performance unavailable -> High performance (SCHEME_MIN)"
    }
}
Say ("  now: {0}" -f ((powercfg /getactivescheme) 2>&1))

# --- 2. CPU --------------------------------------------------------------
Say ""
Say "[2/5] CPU state / boost / cooling"
$subProc = "54533251-82be-4824-96c1-47b60b740d00"
$settings = @(
    @{ name = "PROCTHROTTLEMIN"; label = "min state 100%" },
    @{ name = "PROCTHROTTLEMAX"; label = "max state 100%" }
)
foreach ($s in $settings) {
    $out = (powercfg /setacvalueindex $target $subProc $($s.name) 100) 2>&1
    if ($LASTEXITCODE -ne 0) { Say ("  WARN {0} failed: {1}" -f $s.label, ($out -join " ")) } else { Say ("  ok {0}" -f $s.label) }
}
# aggressive boost + active cooling (some laptops reject; report instead of failing the run)
$boost = (powercfg /setacvalueindex $target $subProc PERFBOOSTMODE 2) 2>&1
Say ("  boost mode aggressive: rc={0} {1}" -f $LASTEXITCODE, ($boost -join " "))
$cool = (powercfg /setacvalueindex $target $subProc SYSCOOLPOL 1) 2>&1
Say ("  cooling active: rc={0} {1}" -f $LASTEXITCODE, ($cool -join " "))

# --- 3. disk / usb -------------------------------------------------------
Say ""
Say "[3/5] disk + USB never suspend"
$subDisk = "0012ee47-9041-4b5d-9b77-535fba8b1442"
$out = (powercfg /setacvalueindex $target $subDisk DISKIDLE 0) 2>&1
Say ("  disk idle = never: rc={0} {1}" -f $LASTEXITCODE, ($out -join " "))
$subUsb = "2a737441-1930-4402-8d77-b2bebba308a3"
$out = (powercfg /setacvalueindex $target $subUsb 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0) 2>&1
Say ("  USB selective suspend off: rc={0} {1}" -f $LASTEXITCODE, ($out -join " "))
powercfg /setactive $target 2>&1 | Out-Null
Say "  re-applied active scheme"

# --- 4. Windows power throttling ----------------------------------------
Say ""
Say "[4/5] Windows Power Throttling off"
$regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling"
try {
    if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
    New-ItemProperty -Path $regPath -Name "PowerThrottlingOff" -Value 1 -PropertyType DWord -Force | Out-Null
    Say "  PowerThrottlingOff = 1"
} catch {
    Say ("  WARN registry: {0}" -f $_.Exception.Message)
}

# --- 5. GPU persistence --------------------------------------------------
Say ""
Say "[5/5] GPU"
$smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($smi) {
    $gpu = (nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader) 2>&1
    Say ("  gpu: {0}" -f ($gpu -join " "))
    $pm = (nvidia-smi -pm 1) 2>&1
    Say ("  persistence mode on: rc={0} {1}" -f $LASTEXITCODE, ($pm -join " "))
} else {
    Say "  nvidia-smi not found (no NVIDIA driver?) - skipped"
}

# --- verdict -------------------------------------------------------------
Say ""
$after = (powercfg /getactivescheme) 2>&1
$nowPlan = ($after | Out-String).Trim()
Say ("FINAL PLAN: {0}" -f $nowPlan)
if ($nowPlan -match "Ultimate|High performance|高性能|卓越") { Say "RESULT: PERF-MAX APPLIED" } else { Say "RESULT: PLAN NOT UPGRADED - check the log" ; $rc = 1 }

# ack
$py = (Get-Command python -ErrorAction SilentlyContinue)
$pycmd = if ($py) { "python" } else { "py -3" }
$ackArgs = @("Tools\fleet\ack_write.py", "--id", "OB-20261103-1240-BMB-PERF-MAX", "--node", $Node, "--rc", "$rc", "--log", $log, "--root", ".")
try {
    & cmd /c "$pycmd $($ackArgs -join ' ')"
} catch {
    Say ("ack write failed: {0}" -f $_.Exception.Message)
}
Say ""
Say "Rollback: powercfg /setactive SCHEME_BALANCED"
Read-Host "Press Enter to close" | Out-Null
exit $rc