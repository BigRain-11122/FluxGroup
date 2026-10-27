# openclaw-model-switch.ps1 - Gateway primary model day/night auto-switch (WorkBuddy Phase 1.5)
# Night (19:07): prefer bm-a CoderServe 35B (:8090) when it is actually serving (AutoYield resume).
# Day (09:07): if 35B is down (weekday pauseLite) fall back to Ollama qwen3:4b light model; if 35B
# is still alive (weekend/holiday) keep it. Health-aware and idempotent; hot-applies via OpenClaw
# config hot reload. Called by HQ-OpenClaw-ModelDay/ModelNight scheduled tasks (task-register door).
param([Parameter(Mandatory = $true)][ValidateSet('day', 'night')][string]$Mode)
$ErrorActionPreference = 'Continue'
$oc = Join-Path $env:APPDATA 'npm\openclaw.cmd'
$big = 'bma-coder/qwen36-35b'
$small = 'ollama4b/qwen3:4b-instruct'
$alive = $false
try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8090/health' -TimeoutSec 4; $alive = $true } catch { }
$target = ''
if ($Mode -eq 'night') { if ($alive) { $target = $big } }
else { if (-not $alive) { $target = $small } }
if ($target -eq '') {
    Write-Output ("MODEL-SWITCH $Mode no-op (35B alive=$alive)")
    exit 0
}
& $oc config set agents.defaults.model.primary $target
Write-Output ("MODEL-SWITCH $Mode -> $target (35B alive=$alive)")
exit 0
