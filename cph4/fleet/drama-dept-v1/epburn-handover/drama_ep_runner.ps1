# drama_ep_runner.ps1 v2.3 - EP image burn self-healing loop (8min tick, lane GPU-clear resistant, self-stop at 60eps)
# v2.1: all python calls wrapped with hard timeout watchdog - a hung burn/check can no longer freeze the tick chain
# (lesson 2026-10-16 10:46: burn python hung on dead comfy socket -> IgnoreNew blocked every later tick)
# v2.2: post-startup probe + one same-tick respawn (lesson 2026-10-17 02:46: env killed comfy ~30s after birth ->
#       SERVER_WAIT_TIMEOUT burned the whole tick; now attempt 2 revives the tick instead of wasting it)
# v2.3: mid-burn server death -> time-budgeted same-tick respawn + second burn pass
# (lesson 2026-10-17 02:54: env killed comfy 2min into the burn window -> tick idle after 28 frames;
#  IgnoreNew task policy tolerates the bounded overrun, no double-instance risk)
$ErrorActionPreference = 'Continue'
$py = 'C:\Fluxgroup\MiniGame\Tools\ComfyUI_windows_portable\python_embeded\python.exe'
$dir = 'C:\Fluxgroup\MiniGame\Tools\comfy'
$epsDir = 'C:\Fluxgroup\FluxGroup\cph4\fleet\drama-001-stockera\episodes'
$log = 'C:\Fluxgroup\FluxGroup\media\drama-eps\runner.log'
$blog = "$dir\drama-ep-burn.log"
New-Item -ItemType Directory -Path (Split-Path $log) -Force | Out-Null

function Log($m) { Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format s), $m) -Encoding UTF8 }

function RunPy([string[]]$pyargs, [int]$timeoutSec) {
  $script:lastExit = 1
  $po = Start-Process -FilePath $py -ArgumentList $pyargs -NoNewWindow -RedirectStandardOutput "$dir\pyout.tmp" -RedirectStandardError "$dir\pyerr.tmp" -PassThru
  if (-not $po.WaitForExit($timeoutSec * 1000)) {
    try { Stop-Process -Id $po.Id -Force } catch {}
    Log 'PY_TIMEOUT_KILL'
  }
  $txt = ''
  if (Test-Path "$dir\pyout.tmp") { $txt = Get-Content "$dir\pyout.tmp" -Raw }
  if (Test-Path "$dir\pyerr.tmp") { Add-Content -Path $blog -Value (Get-Content "$dir\pyerr.tmp") }
  if ($txt) { Add-Content -Path $blog -Value $txt }
  $script:lastExit = $po.ExitCode
  return $txt
}

$t0 = Get-Date
Log 'EP_RUNNER_TICK'
# early exit when no episode json landed yet
$jsons = @(Get-ChildItem $epsDir -Filter 'EP*.json' -ErrorAction SilentlyContinue)
if ($jsons.Count -eq 0) { Log 'NO_JSONS_YET'; Log 'EP_RUNNER_TICK_DONE'; exit 0 }
# completion sentinel: 60 jsons + 0 missing images -> self-disable
if ($jsons.Count -ge 60) {
  $chk = RunPy @('-s', "$dir\drama_ep_burn.py", '1', '60', '--check') 60
  if ("$chk" -match 'EPBURN_REMAIN 0') { Log 'ALL_60_DONE_SELFSTOP'; schtasks /Change /TN 'drama-EPBurn-oneshot' /DISABLE 2>&1 | Out-Null; exit 0 }
}
# restart comfy server if down (lane-clear self-heal point); v2.2: probe after warmup, respawn once if died
$up = $false
try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8198/system_stats' -TimeoutSec 5; $up = $true } catch {}
if (-not $up) {
  for ($attempt = 1; $attempt -le 2; $attempt++) {
    Log ("comfy_server_restart attempt=" + $attempt)
    $p = Start-Process -FilePath $py -ArgumentList '-s','C:\Fluxgroup\MiniGame\Tools\ComfyUI_windows_portable\ComfyUI\main.py','--port','8198','--listen','127.0.0.1' -WorkingDirectory 'C:\Fluxgroup\MiniGame\Tools\ComfyUI_windows_portable\ComfyUI' -WindowStyle Hidden -RedirectStandardOutput "$dir\drama-comfy-server5.out.log" -RedirectStandardError "$dir\drama-comfy-server5.err.log" -PassThru
    Log ("comfy_pid=" + $p.Id)
    Start-Sleep -Seconds 45
    $ok = $false
    try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8198/system_stats' -TimeoutSec 5; $ok = $true } catch {}
    if ($ok) { Log 'comfy_startup_ok'; break }
    Log 'comfy_startup_died_respawn'
    try { Stop-Process -Id $p.Id -Force } catch {}
    Start-Sleep -Seconds 3
  }
} else { Log 'comfy_server_alive' }
# resume-safe burn across the whole range (skips existing >10KB files), 330s hard watchdog
$null = RunPy @('-s', "$dir\drama_ep_burn.py", '1', '60') 330
Log ("ep_burn_exit=" + $script:lastExit)
# v2.3: mid-burn server death -> time-budgeted same-tick respawn + second burn pass
$up = $false
try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8198/system_stats' -TimeoutSec 5; $up = $true } catch {}
if (-not $up) {
  $elapsed = [int]((Get-Date) - $t0).TotalSeconds
  $left = 420 - $elapsed
  if ($left -ge 150) {
    Log 'comfy_midburn_death_respawn'
    $p = Start-Process -FilePath $py -ArgumentList '-s','C:\Fluxgroup\MiniGame\Tools\ComfyUI_windows_portable\ComfyUI\main.py','--port','8198','--listen','127.0.0.1' -WorkingDirectory 'C:\Fluxgroup\MiniGame\Tools\ComfyUI_windows_portable\ComfyUI' -WindowStyle Hidden -RedirectStandardOutput "$dir\drama-comfy-server5.out.log" -RedirectStandardError "$dir\drama-comfy-server5.err.log" -PassThru
    Log ("comfy_pid=" + $p.Id)
    Start-Sleep -Seconds 45
    $ok2 = $false
    try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8198/system_stats' -TimeoutSec 5; $ok2 = $true } catch {}
    if ($ok2) {
      $null = RunPy @('-s', "$dir\drama_ep_burn.py", '1', '60') ([Math]::Max(120, $left - 90))
      Log ("ep_burn_exit2=" + $script:lastExit)
    } else { Log 'comfy_respawn2_dead_skip' }
  } else { Log 'midburn_death_no_budget' }
}
$null = RunPy @('-s', "$dir\drama_ep_burn.py", '1', '60', '--check') 60
Log 'EP_RUNNER_TICK_DONE'
