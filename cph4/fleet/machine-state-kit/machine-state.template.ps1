# machine-state.template.ps1 - CEO 用机让路律 single-machine switch (fleet kit template)
# LAW: resource-chain.md §六 CEO 用机让路律 (2026-10-06, council C-20261006-01 PASS).
# CEO standing order: whichever machine HEARS "wo yao da youxi / wo yao gongzuo" pauses
# THAT machine only (all other machines keep full-speed operation); "quanmian kaigong"
# (full mobilization) = local resume + broadcast fleet O-token -> every machine resumes.
# REFERENCE IMPLEMENTATION (field-tested): bm-c K:\Fluxgroup\.codely-cli\machine-state.ps1 v2.
# DEPLOY: copy this file + gamewin_cron_suspend.py into <Fluxgroup root>\.codely-cli\ as
# machine-state.ps1, then LOCALIZE the three blocks marked ##LOCALIZE below. Idempotent.
# Usage (in-process per U060 law, NO console spawn): & "<root>\.codely-cli\machine-state.ps1" -Mode pause|pauseLite|resume|status
# v5 2026-10-15: +pauseLite mode (O-20261015-1500 CEO approved): work-hours auto-yield -
#   stops heavy brain llama-server + ComfyUI + GPU tasks + cron, KEEPS the Ollama
#   small-model light face alive. Manual word pause = full stop (unchanged).
#   bm-a AutoYield schedule: weekdays 09:00 pauseLite / 19:00 resume.
# v6 2026-10-15 (bm-a live evidence, CEO 16:23 re-order): revival-gap fix - (a) any
#   brain-watchdog task (e.g. bm-a-CoderServe PT10M) MUST be in the LOCALIZE-1 disable
#   list, else it relaunches the killed brain <=10min after pause/pauseLite; (b) pause/
#   pauseLite now write engine-tick\keepwarm.pause valve (bm-a: coder-serve's flag check
#   never fired because the dir did not even exist) and resume removes the valve.
# v6.1 2026-10-18 (D-20261016-06 three-task revival-gap root fix, mirror of bm-a live v6.1):
#   pause/pauseLite write a disable-manifest sidecar (machine-state.disabled.json); resume
#   reverse-revives from that manifest (union with the LOCALIZE-1 static list) + self-verifies
#   each revived task state + consumes the manifest. Gap evidence: 10-15 14:4x pause cascade
#   disabled tasks beyond the static list; static-list resume never re-enabled them
#   (E1 confirmed D-20261016-06; manual-enable fallback held Ready meanwhile).

param([Parameter(Mandatory=$true)][ValidateSet("pause","pauseLite","resume","status")][string]$Mode)

$ErrorActionPreference = "Continue"

##LOCALIZE-1: this machine's GPU production Task Scheduler task names (self-report list)
$tasks = @("<LOCALIZE: your GPU production task names + brain-watchdog task if any (v6: e.g. bm-a-CoderServe must be IN this list, else it revives the killed brain after pause)>")

##LOCALIZE-2: this machine's LLM stack (comment out lines that do not apply; declare honestly)
$ollamaExe = "<LOCALIZE: ollama.exe full path>"
$pinModel  = "<LOCALIZE: resident small-fast model, e.g. qwen3:4b-instruct (heavy brain lives on the brain box / :8090)>"
$brainMarker = "<LOCALIZE: heavy-brain llama-server command-line marker, e.g. llamacpp-b11429 (Ollama runners must NOT match)>"
$keepAliveTask = "<LOCALIZE: ComfyUI/keepalive task name>"

# Portable paths: this script lives at <Fluxgroup root>\.codely-cli\machine-state.ps1
$cronPy = Join-Path $PSScriptRoot "gamewin_cron_suspend.py"

function Kill-GpuHolders {
    # ollama parent + llama-server children (kill-parent-leaves-child pit, 3x proven 10-06)
    # v4 2026-10-07: tray app FIRST (7th respawn source, C-machine live evidence: killing
    # serve alone -> "ollama app.exe" explorer-autostart relaunches a fresh serve within
    # seconds). Kill order = tray app -> serve -> runner, family-wide re-verify.
    Get-Process -Name "ollama app" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
    # ComfyUI python (match command line; harmless if this machine has no ComfyUI)
    Get-CimInstance Win32_Process -Filter "name='python.exe'" |
        Where-Object { $_.CommandLine -match "ComfyUI" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

function Get-VramUsedMB {
    $line = nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
    return [int]($line | Select-Object -First 1)
}

if ($Mode -eq "status") {
    $vram = Get-VramUsedMB
    $ollamaUp = $false
    try { Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 | Out-Null; $ollamaUp = $true } catch {}
    $comfyUp = $false
    try { Invoke-RestMethod -Uri "http://127.0.0.1:8188/system_stats" -TimeoutSec 3 | Out-Null; $comfyUp = $true } catch {}
    $taskState = (Get-ScheduledTask -TaskName $tasks -ErrorAction SilentlyContinue | ForEach-Object { $_.TaskName + "=" + $_.State }) -join " "
    $flagPath = Join-Path $PSScriptRoot "machine-state.flag"
    if (Test-Path $flagPath) { Write-Output ("FLAG: " + (Get-Content $flagPath -Raw).Trim()) }
    Write-Output ("STATE: vramUsedMB={0} ollama={1} comfy={2} tasks[{3}]" -f $vram, $ollamaUp, $comfyUp, $taskState)
    try { Write-Output ("CRON: " + (& python $cronPy status)) } catch { Write-Output "CRON: unknown" }
    if (-not $ollamaUp -and -not $comfyUp) { Write-Output "MODE=pause" }
    elseif ($ollamaUp -and $vram -gt 10000) { Write-Output "MODE=resume" }
    else { Write-Output "MODE=mixed" }
    return
}

if ($Mode -eq "pause") {
    # v6: hold the brain-watchdog valve (create dir first - missing dir = silent no-op pit)
    $null = New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot "engine-tick")
    Set-Content -Path (Join-Path $PSScriptRoot "engine-tick\keepwarm.pause") -Value "paused $(Get-Date -Format o)" -Encoding ASCII
    Write-Output "[pause] stopping ollama + llama-server + comfyui ..."
    Kill-GpuHolders
    $disabled = @()
    foreach ($t in $tasks) { try { Disable-ScheduledTask -TaskName $t -ErrorAction Stop | Out-Null; $disabled += $t; Write-Output "[pause] disabled: $t" } catch { Write-Output "[pause] WARN disable ${t}: $($_.Exception.Message)" } }
    try { Set-Content -Path (Join-Path $PSScriptRoot "machine-state.disabled.json") -Value $disabled -Encoding ASCII; Write-Output ("[pause] v6.1 sidecar: " + @($disabled).Count + " task(s) recorded for resume reversal") } catch { Write-Output "[pause] WARN sidecar write: $($_.Exception.Message)" }
    try { Write-Output ("[pause] cron: " + (& python $cronPy suspend)) } catch { Write-Output "[pause] WARN cron suspend: $($_.Exception.Message)" }
    Start-Sleep -Seconds 4
    # hard verification: OUR holders must be gone (process-face, not absolute vram -
    # gaming window keeps vram legitimately used by CEO's own apps)
    $residue = Get-Process llama-server,ollama,"ollama app" -ErrorAction SilentlyContinue
    $comfyResidue = Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -match "ComfyUI" }
    $guard = 0
    while (($residue -or $comfyResidue) -and $guard -lt 3) {
        Get-Process -Name "ollama app" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Get-Process llama-server,ollama -ErrorAction SilentlyContinue | Stop-Process -Force
        Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -match "ComfyUI" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 4
        $residue = Get-Process llama-server,ollama,"ollama app" -ErrorAction SilentlyContinue
        $comfyResidue = Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -match "ComfyUI" }
        $guard++
    }
    if ($residue -or $comfyResidue) { Write-Output "[pause] FAIL: production residue still alive - manual check"; exit 1 }
    $vram = Get-VramUsedMB
    Write-Output ("[pause] OK production-clean (vramUsedMB={0} = CEO desktop/gaming face, none ours)" -f $vram)
    return
}

if ($Mode -eq "pauseLite") {
    # v5 2026-10-15 (O-20261015-1500): heavy yield, light face kept (small-model QA lane stays).
    # v6: hold the brain-watchdog valve during the work-hours yield as well
    $null = New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot "engine-tick")
    Set-Content -Path (Join-Path $PSScriptRoot "engine-tick\keepwarm.pause") -Value "pausedLite $(Get-Date -Format o)" -Encoding ASCII
    Write-Output "[pauseLite] stopping heavy brain + comfyui + GPU tasks (ollama light face kept) ..."
    Get-CimInstance Win32_Process -Filter "name='llama-server.exe'" |
        Where-Object { $_.CommandLine -match $brainMarker } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Get-CimInstance Win32_Process -Filter "name='python.exe'" |
        Where-Object { $_.CommandLine -match "ComfyUI" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    $disabled = @()
    foreach ($t in $tasks) { try { Disable-ScheduledTask -TaskName $t -ErrorAction Stop | Out-Null; $disabled += $t } catch { Write-Output "[pauseLite] WARN disable ${t}: $($_.Exception.Message)" } }
    try { Set-Content -Path (Join-Path $PSScriptRoot "machine-state.disabled.json") -Value $disabled -Encoding ASCII } catch { Write-Output "[pauseLite] WARN sidecar write: $($_.Exception.Message)" }
    try { Write-Output ("[pauseLite] cron: " + (& python $cronPy suspend)) } catch { Write-Output "[pauseLite] WARN cron suspend: $($_.Exception.Message)" }
    Start-Sleep -Seconds 2
    $brainResidue = Get-CimInstance Win32_Process -Filter "name='llama-server.exe'" | Where-Object { $_.CommandLine -match $brainMarker }
    if ($brainResidue) { Write-Output "[pauseLite] FAIL: brain residue alive - manual check"; exit 1 }
    $vram = Get-VramUsedMB
    Write-Output ("[pauseLite] OK heavy-clean, light face kept (vramUsedMB={0})" -f $vram)
    return
}

if ($Mode -eq "resume") {
    # v6: release the brain-watchdog valve so the heavy brain may return for the night window
    Remove-Item -Path (Join-Path $PSScriptRoot "engine-tick\keepwarm.pause") -Force -ErrorAction SilentlyContinue
    # v6.1: reverse-revive from pause sidecar (union with static list), then self-verify
    $sidecar = Join-Path $PSScriptRoot "machine-state.disabled.json"
    $revive = @($tasks)
    if (Test-Path $sidecar) {
        $prevDis = @(Get-Content -Path $sidecar -EA 0 | Where-Object { $_ -and $_.Trim() -ne '' })
        if (@($prevDis).Count -gt 0) { $revive = @(@($tasks) + @($prevDis) | Select-Object -Unique) }
        Write-Output ("[resume] v6.1 sidecar: " + @($prevDis).Count + " task(s) recorded at last pause")
    }
    Write-Output "[resume] enabling production tasks ..."
    foreach ($t in $revive) { try { Enable-ScheduledTask -TaskName $t -ErrorAction Stop | Out-Null; Write-Output "[resume] enabled: $t" } catch { Write-Output "[resume] WARN enable ${t}: $($_.Exception.Message)" } }
    foreach ($t in $revive) { try { $st = (Get-ScheduledTask -TaskName $t -ErrorAction Stop).State; Write-Output "[resume] verify: $t=$st" } catch { Write-Output "[resume] VERIFY-FAIL ${t}: $($_.Exception.Message)" } }
    if (Test-Path $sidecar) { try { Remove-Item -Path $sidecar -Force -ErrorAction Stop; Write-Output "[resume] v6.1 sidecar consumed" } catch { Write-Output "[resume] WARN sidecar consume: $($_.Exception.Message)" } }
    try { Write-Output ("[resume] cron: " + (& python $cronPy restore)) } catch { Write-Output "[resume] WARN cron restore: $($_.Exception.Message)" }
    if ($pinModel -and $pinModel -notmatch "^<") {
        $env:OLLAMA_HOST = "0.0.0.0"
        if (-not (Get-Process ollama -ErrorAction SilentlyContinue)) {
            Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
            Write-Output "[resume] ollama serve started"
        }
        $ok = $false
        foreach ($i in 1..12) {
            Start-Sleep -Seconds 3
            try {
                $body = '{"model":"' + $pinModel + '","prompt":"ping","stream":false,"keep_alive":-1}'
                $r = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 240
                if ($r.done) { $ok = $true; break }
            } catch {}
        }
        if ($ok) { Write-Output "[resume] resident model pinned: $pinModel keep_alive=forever" }
        else { Write-Output "[resume] WARN model pin pending (API not up yet) - retry next window" }
    }
    if ($keepAliveTask -and $keepAliveTask -notmatch "^<") {
        try { Start-ScheduledTask -TaskName $keepAliveTask -ErrorAction Stop; Write-Output "[resume] keepalive kicked" } catch { Write-Output "[resume] WARN keepalive kick: $($_.Exception.Message)" }
    }
    $vram = Get-VramUsedMB
    Write-Output ("[resume] OK vramUsedMB={0}" -f $vram)
    return
}
