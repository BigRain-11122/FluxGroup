# openclaw-gateway-runner.ps1 - HQ-OpenClawGateway idempotent keepalive runner (S4U-safe, zero-window)
# WorkBuddy upgrade Phase 1 (CEO order 2026-10-19, canon = cph4/fleet/WORKBUDDY-UPGRADE-PLAN-v1.md).
# Started by task-register.ps1 hidden chain (every:10m). Deliberately does NOT use `openclaw gateway
# install` (raw schtasks task = violates the U060 task-register single-door law).
# Behavior: if port 18789 already listening -> exit 0 (idempotent). Else wait for the tailnet
# interface (gateway binds to it, <=300s), then start `openclaw gateway run` as a detached hidden
# process (survives this runner's exit). Logs -> %USERPROFILE%\.openclaw\gateway-run.*.log
$ErrorActionPreference = 'Continue'
$port   = 18789
$oc     = Join-Path $env:APPDATA 'npm\openclaw.cmd'
$logDir = Join-Path $env:USERPROFILE '.openclaw'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$outLog = Join-Path $logDir 'gateway-run.out.log'
$errLog = Join-Path $logDir 'gateway-run.err.log'

# 0. canon sync (git = single source of truth): AGENTS.md/SOUL.md/skills -> workspace, every start
$src = 'C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\workbuddy-gateway'
if (Test-Path (Join-Path $src 'AGENTS.md')) {
    $ws = Join-Path $logDir 'workspace'
    New-Item -ItemType Directory -Force -Path (Join-Path $ws 'skills') | Out-Null
    Copy-Item (Join-Path $src '*.md') $ws -Force
    Copy-Item (Join-Path $src 'skills\*') (Join-Path $ws 'skills') -Recurse -Force
}

# 1. idempotent guard: gateway already up?
if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) { exit 0 }
if (-not (Test-Path $oc)) { exit 0 }

# 2. wait for tailnet interface (bind target) - up to 300s
$deadline = (Get-Date).AddSeconds(300)
while ((Get-Date) -lt $deadline) {
    $ts = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -like '100.*' }
    if ($ts) { break }
    Start-Sleep -Seconds 10
}

# 3. start detached hidden gateway process
Start-Process -WindowStyle Hidden -FilePath "$env:ComSpec" -ArgumentList '/c', "`"$oc`" gateway run" -RedirectStandardOutput $outLog -RedirectStandardError $errLog
exit 0
