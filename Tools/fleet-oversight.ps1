# fleet-oversight.ps1 - Idle/Spin Oversight Inspector v1.0
# CEO order 2026-10-11 21:1x "committee must run a standing top-level mechanism,
# frequent checks on fleet idle compute / subsidiary business / research, no spin"
# -> council case C-20261011-02 D1 (commit db04310). Law anchor: resource-chain
# anti-idle lineage (C-20261001-03 / 07-05 / 10-02 / 10-04 / 11-01).
# DESIGN (v1 boundary, deliberate):
#   - READ-ONLY. Zero remediation, zero production writes. Enforcement stays with
#     the patrol auto-replenish step (C-20261010-02) and the decision rounds; this
#     tool only upgrades their data source from 12h-cadence to 1h-cadence.
#   - Session-independent: registered through Tools/task-register.ps1 (schtasks,
#     hidden chain). Survives CLI death - the 3rd "session death = pump death"
#     recurrence (2026-10-11 sentinel df35676f) is what this exists to end.
#   - Three probe lines per bill D3 quantified criteria + infrastructure
#     self-watch ("who watches the watchmen": previous watch file age -> red).
#   - Yield exemption built-in: any of the six GPU production tasks Disabled
#     means machine-state pause (CEO using machine) -> lanes report YIELD, never
#     red. Let-path is legal, not idleness.
# Outputs (all fail-soft, atomic where possible):
#   <Root>\fleet\oversight\idle-watch-<M>.json        (board + committee feed)
#   <Root>\fleet\oversight\RED-FLAGS-<M>.md           (rolling red-flag digest)
#   <Root>\quant\bigmoney\fleet\machine-health.json  (append, revive hourly ledger)
#   <Root>\fleet\oversight\oversight-run.log         (tail-50 run log)
# Usage:
#   powershell -File Tools\fleet-oversight.ps1                 # bm-c default
#   powershell -File Tools\fleet-oversight.ps1 -M bm-a -Root C:\Users\sjs20\Desktop\FluxGroup
param(
  [string]$M = "bm-c",
  [string]$Root = "K:\Fluxgroup\FluxGroup",
  [string]$KRoot = "K:\Fluxgroup"
)
$ErrorActionPreference = 'SilentlyContinue'
$GIT = 'C:\Program Files\Git\cmd\git.exe'
$now = Get-Date
$outDir = Join-Path $Root 'fleet\oversight'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$watchPath = Join-Path $outDir ("idle-watch-" + $M + ".json")

# ---- single-flight lock (stale takeover 4 min) ----
$lockPath = Join-Path $env:TEMP ("fleet-oversight-" + $M + ".lock")
if (Test-Path $lockPath) {
  try { if (((Get-Date) - (Get-Item $lockPath).LastWriteTime).TotalMinutes -lt 4) { exit 0 } } catch { }
}
try { Set-Content -LiteralPath $lockPath -Value 'run' -ErrorAction Stop } catch { exit 0 }

function LogLine([string]$s) {
  try {
    Add-Content -LiteralPath (Join-Path $outDir 'oversight-run.log') -Value ((Get-Date -Format s) + ' ' + $s) -Encoding UTF8
    $lf = Join-Path $outDir 'oversight-run.log'
    if (Test-Path $lf) {
      $ll = @((Get-Content -LiteralPath $lf) | Where-Object { $_ -match '\S' })
      if ($ll.Count -gt 50) { [IO.File]::WriteAllLines($lf, ($ll | Select-Object -Last 50)) }
    }
  } catch { }
}

# ---- previous watch age (infrastructure self-watch) ----
$prevAgeH = -1.0
$prevLanes = @{}
$prevFlagCodes = @()
if (Test-Path $watchPath) {
  try {
    $prevAgeH = [Math]::Round(((Get-Date) - (Get-Item $watchPath).LastWriteTime).TotalHours, 2)
    $pv = Get-Content -LiteralPath $watchPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($k in @('cpu','gpu','llm')) { if ($pv.lanes.PSObject.Properties.Name -contains $k) { $prevLanes[$k] = [string]$pv.lanes.$k } }
    foreach ($f in @($pv.red_flags)) { $prevFlagCodes += [string]$f.code }
  } catch { }
}

# ---- family-disabled count (NOT yield by itself: authored-pause marker is the only
# whitelist; unexpected disables must stay RED-flagged, e.g. bm-a blackout case) ----
$familyDisabled = 0
foreach ($t in @('MiniGameComfyDraftTick','MiniGameComfyKeepAlive','MiniGameComfyRamGuard','MiniGameOllamaServe','MiniGameOllamaKeepWarm','MiniGameLocalCoderPump','BigCompute-OSLoop','BigCompute-OSLoop-PM','BigCompute-CleanWindowProbe','BigCompute-GPU-IdleWatch','BigCompute-OrderSentinel','BigCompute-ResidentQA')) {
  if ([string]((Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue).State) -eq 'Disabled') { $familyDisabled++ }
}

# ---- CPU / GPU / RAM ----
$cpuPct = -1
try { $cpuPct = [int](Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average } catch { }
$gpuUtil = -1; $vramUsed = -1; $vramTotal = -1
try {
  $g = & nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>$null
  if ($g -match '^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)') { $gpuUtil = [int]$Matches[1]; $vramUsed = [int]$Matches[2]; $vramTotal = [int]$Matches[3] }
} catch { }
$ramFreeGb = -1
try { $ramFreeGb = [Math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1) } catch { }

# ---- engine (BigMoney saturation lane) ----
$eng = @{ alive = $null; queue = -1; burns = -1; py = -1; front = -1 }
$engPath = Join-Path $Root ("quant\bigmoney\results\saturation_engine_state." + $M + ".json")
if (Test-Path $engPath) {
  try {
    $e = Get-Content -LiteralPath $engPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $eng.alive = [bool]$e.alive
    $eng.queue = @($e.queue_next).Count
    $eng.burns = @($e.burns_active).Count
    $eng.py = [int]$e.py_cpu_pct
  } catch { }
}
try {
  $front = -1
  Get-ChildItem (Join-Path $Root 'quant\bigmoney\results\perpetual_faces') -Filter 'n1_w*_results.json' -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -match 'n1_w(\d+)_results\.json$') { $n = [int]$Matches[1]; if ($n -gt $front) { $front = $n } }
  }
  $eng.front = $front
} catch { }

# ---- LLM pin / ComfyUI / GPU batch ----
$pinned = $false
try {
  # C-20261016-05 dual-mode alignment: LLM lane is GREEN when ANY model is
  # resident in llm-mode (27b fill-in per C-20261016-03; 35b retired 10-14).
  # In gen-mode ollama is stopped by design - the gpuBatch branch carries OFFLOAD.
  $ps = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/ps' -TimeoutSec 4
  if (@($ps.models).Count -gt 0) { $pinned = $true }
} catch { }
$comfy = $false
try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 4 -UseBasicParsing; if ($r.StatusCode -eq 200) { $comfy = $true } } catch { }
$gpuBatch = ''
try {
  foreach ($p in @(Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" -ErrorAction SilentlyContinue)) {
    $cl = [string]$p.CommandLine
    if ($cl -match 'h3_i2v_album') { $gpuBatch = 'album-i2v'; break }
    elseif ($cl -match 'kf_batch|mv_full_kf') { $gpuBatch = 'kf-batch'; break }
    elseif ($cl -match 'musubi|tuner') { $gpuBatch = 'lora-train'; break }
  }
} catch { }

# ---- infrastructure: durable cron expiry face / cloudF / liveness ----
$cronJobs = -1; $cronDaysLeft = -1
$cronF = ''
foreach ($cand in @((Join-Path $KRoot '.codely-cli\scheduled_tasks.json'), (Join-Path $Root '.codely-cli\scheduled_tasks.json'), (Join-Path (Split-Path $Root) '.codely-cli\scheduled_tasks.json'))) {
  if (Test-Path $cand) { $cronF = $cand; break }
}
if ($cronF -ne '') {
  try {
    $cj = Get-Content -LiteralPath $cronF -Raw -Encoding UTF8 | ConvertFrom-Json
    $jobs = @()
    if ($cj.PSObject.Properties.Name -contains 'tasks') { $jobs = @($cj.tasks.PSObject.Properties | ForEach-Object { $_.Value }) }
    elseif ($cj.PSObject.Properties.Name -contains 'jobs') { $jobs = @($cj.jobs.PSObject.Properties | ForEach-Object { $_.Value }) }
    else { $jobs = @($cj.PSObject.Properties | ForEach-Object { $_.Value }) }
    $cronJobs = $jobs.Count
    $minEpoch = [double]::MaxValue
    foreach ($j in $jobs) { try { $ms = [double]$j.createdAt; if ($ms -gt 0 -and $ms -lt $minEpoch) { $minEpoch = $ms } } catch { } }
    if ($minEpoch -lt [double]::MaxValue) {
      $expireAt = [DateTimeOffset]::FromUnixTimeMilliseconds([long]$minEpoch).LocalDateTime.AddDays(7)
      $cronDaysLeft = [Math]::Round(($expireAt - $now).TotalDays, 1)
    }
  } catch { }
}
$cloudf = -1
$miniRoot = Join-Path $Root 'gaming\MiniGame'
if (-not (Test-Path $miniRoot)) { $miniRoot = Join-Path (Split-Path $Root) 'MiniGame' }
$cfPath = Join-Path $miniRoot ('.codely-cli\engine-tick\cloudF-queue-' + $M.Substring($M.Length - 1) + '.jsonl')
if (Test-Path $cfPath) {
  try {
    $n = 0
    foreach ($ln in (Get-Content -LiteralPath $cfPath -Encoding UTF8)) { if ($ln -match '"status"\s*:\s*"pending"') { $n++ } }
    $cloudf = $n
  } catch { }
}
$liveVerdict = 'none'; $liveAgeH = -1
$liveF = Join-Path $env:USERPROFILE '.codely-cli\fleet-liveness\liveness.json'
if (Test-Path $liveF) {
  try {
    $lv = Get-Content -LiteralPath $liveF -Raw -Encoding UTF8 | ConvertFrom-Json
    $liveVerdict = [string]$lv.verdict
    $liveAgeH = [Math]::Round(((Get-Date) - (Get-Item $liveF).LastWriteTime).TotalHours, 1)
  } catch { }
}

# ---- subsidiaries: local commit counts (NO fetch; deep audit stays with patrol) ----
# Layout truth (bm-c probe 2026-10-11): real repo paths are compute\BigCompute,
# life\BigLife, domain\BigDomain, media\BigStream (outer dirs are NOT repos - a bare
# `git -C compute` silently walks UP to the HQ repo and returns HQ counts = false GREEN).
# BigStream production lands mostly in HQ cph4 paths, so its count merges own-repo
# with the HQ production pathspec (max) to avoid false stall while lines are hot.
$subs = @()
$repoMap = @(
  @{ n = 'BigCompute'; p = 'compute\BigCompute'; inHQ = $false },
  @{ n = 'BigDomain';   p = 'domain\BigDomain';   inHQ = $false },
  @{ n = 'BigLife';     p = 'life\BigLife';      inHQ = $false },
  @{ n = 'BigStream';   p = 'media\BigStream';   inHQ = $false; hqspec = 'cph4/fleet/meme-daily-v1 cph4/fleet/shortvideo-dept cph4/fleet/mv-album-001-jay cph4/fleet/mv0001-handover cph4/fleet/h3-local-test' },
  @{ n = 'BigMoney';    p = 'quant\bigmoney';    inHQ = $false },
  @{ n = 'MiniGame';    p = 'gaming\MiniGame';    inHQ = $false },
  @{ n = 'FluxVerse';   p = 'gaming\FluxVerse';   inHQ = $false }
)
foreach ($r in $repoMap) {
  $c24 = -1; $c48 = -1; $status = 'SKIP'
  $rp = Join-Path $Root $r.p
  $hasGit = ([System.IO.Directory]::Exists((Join-Path $rp '.git')) -or [System.IO.File]::Exists((Join-Path $rp '.git')))
  if ($hasGit) {
    $c24 = @(& $GIT -C $rp log --oneline '--since=24 hours ago' 2>$null).Count
    $c48 = @(& $GIT -C $rp log --oneline '--since=48 hours ago' 2>$null).Count
    if ($r.hqspec) {
      $hpaths = @(([string]$r.hqspec) -split ' ')
      $h24 = @(& $GIT -C $Root log --oneline '--since=24 hours ago' -- $hpaths 2>$null).Count
      if ($h24 -gt $c24) { $c24 = $h24 }
      $h48 = @(& $GIT -C $Root log --oneline '--since=48 hours ago' -- $hpaths 2>$null).Count
      if ($h48 -gt $c48) { $c48 = $h48 }
    }
    if ($c24 -gt 0) { $status = 'GREEN' } elseif ($c48 -gt 0) { $status = 'AMBER' } else { $status = 'RED' }
  }
  # exemption face (declared freezes/right-of-way: fleet/oversight/exemptions.json,
  # maintained by windows/rounds - keeps honest data while avoiding false alarms)
  $exNote = ''
  $exF = Join-Path $Root 'fleet\oversight\exemptions.json'
  if (Test-Path $exF) {
    try {
      $ex = Get-Content -LiteralPath $exF -Raw -Encoding UTF8 | ConvertFrom-Json
      $ep = $ex.PSObject.Properties | Where-Object { $_.Name -eq $r.n }
      if ($ep -and $status -ne 'SKIP' -and $status -ne 'GREEN') { $status = 'EXEMPT'; $exNote = [string]$ep.Value.reason }
    } catch { }
  }
  $subs += @{ name = $r.n; repo = ([string]$r.p); c24 = $c24; c48 = $c48; status = $status; note = $exNote }
}
# BigHouse: no local clone on this machine fleet-wide state via ls-remote sha watch
$bhPath = Join-Path $Root 'house\BigHouse'
if ([System.IO.Directory]::Exists((Join-Path $bhPath '.git'))) {
  $c24 = @(& $GIT -C $bhPath log --oneline --since='24 hours ago' 2>$null).Count
  $c48 = @(& $GIT -C $bhPath log --oneline --since='48 hours ago' 2>$null).Count
  $st = 'RED'; if ($c24 -gt 0) { $st = 'GREEN' } elseif ($c48 -gt 0) { $st = 'AMBER' }
  $subs += @{ name = 'BigHouse'; repo = 'house\BigHouse'; c24 = $c24; c48 = $c48; status = $st }
} else {
  $subs += @{ name = 'BigHouse'; repo = '(no-local-clone)'; c24 = -1; c48 = -1; status = 'SKIP' }
}

# ---- research freshness proxy (deep OSS audit stays with patrol) ----
$research72 = 0
try { $research72 = @(& $GIT -C $Root log --oneline --since='72 hours ago' -- cph4/research docs/research 2>$null).Count } catch { }
$researchStatus = 'AMBER'; if ($research72 -gt 0) { $researchStatus = 'GREEN' }

# ---- yield resolution (authored pause only; see familyDisabled note) ----
$pauseMarker = ''
$mf = Join-Path $KRoot '.codely-cli\machine-state.flag'
if (-not (Test-Path $mf)) { $mf = Join-Path $Root '.codely-cli\machine-state.flag' }
if (Test-Path $mf) { try { $pauseMarker = ([string](Get-Content -LiteralPath $mf -Raw -Encoding UTF8)).Trim() } catch { } }
$yield = $false
$yieldNote = ''
if ($pauseMarker -like 'paused*') { $yield = $true; $yieldNote = 'marker' }
elseif (-not $pinned -and -not $comfy -and $familyDisabled -ge 4) { $yield = $true; $yieldNote = 'unmarked-pause-face' }

# ---- lane verdicts (D3 criteria; RED needs 2 consecutive bad reads) ----
function WasBad($k) { return ($prevLanes.ContainsKey($k) -and $prevLanes[$k] -in @('AMBER', 'RED')) }
$laneCpu = 'GREEN'; $laneGpu = 'GREEN'; $laneLlm = 'GREEN'
if ($yield) { $laneCpu = 'YIELD'; $laneGpu = 'YIELD'; $laneLlm = 'YIELD' }
else {
  if ($eng.queue -gt 0 -or $eng.burns -gt 0 -or $cpuPct -ge 50) { $laneCpu = 'GREEN' }
  elseif ($gpuBatch -ne '' -and $cpuPct -ge 30) { $laneCpu = 'GREEN' }
  else {
    $laneCpu = 'AMBER'
    if (WasBad('cpu')) { $laneCpu = 'RED' }
  }
  if ($gpuBatch -ne '' -or $gpuUtil -ge 20) { $laneGpu = 'GREEN' }
  else {
    $laneGpu = 'AMBER'
    if (WasBad('gpu')) { $laneGpu = 'RED' }
  }
  if ($pinned) { $laneLlm = 'GREEN' }
  elseif ($gpuBatch -ne '') { $laneLlm = 'OFFLOAD' }
  else {
    $laneLlm = 'AMBER'
    if (WasBad('llm')) { $laneLlm = 'RED' }
  }
}

# ---- red flags ----
$flags = @()
function AddFlag([string]$code, [string]$line, [string]$detail) {
  $script:flags += @{ code = $code; line = $line; detail = $detail }
}
if ($laneCpu -eq 'RED') { AddFlag 'CPU_LANE_EMPTY' 'fleet' ("cpu=" + $cpuPct + "% engine_queue=" + $eng.queue + " wave_front=" + $eng.front) }
if ($laneGpu -eq 'RED') { AddFlag 'GPU_LANE_EMPTY' 'fleet' ("gpu_util=" + $gpuUtil + "% vram_used=" + $vramUsed + "MB comfy=" + $comfy) }
if ($laneLlm -eq 'RED') { AddFlag 'LLM_UNPINNED' 'fleet' 'no resident LLM in llm-mode, no gpu batch, not yield (C-03 dual-mode)' }
foreach ($s in $subs) { if ($s.status -eq 'RED') { AddFlag 'SUBSIDIARY_STALL' ('subs/' + $s.name) ("c24=" + $s.c24 + " c48=" + $s.c48) } }
if ($researchStatus -eq 'AMBER') { AddFlag 'RESEARCH_STALE' 'research' 'no research-path commits in 72h' }
if ($prevAgeH -gt 2.5) { AddFlag 'INSPECTOR_STALLED' 'infra' ("previous watch age " + $prevAgeH + "h - who watches the watchmen") }
if ($eng.alive -eq $false) { AddFlag 'ENGINE_DOWN' 'fleet' 'saturation engine alive=false' }
if ($yield -and $yieldNote -eq 'unmarked-pause-face') { AddFlag 'PAUSE_UNMARKED' 'infra' 'pause-like face without machine-state marker - patch marker leg on this machine' }
if ($familyDisabled -ge 4 -and -not $yield) { AddFlag 'FAMILY_TASKS_DISABLED' 'infra' ("familyDisabled=" + $familyDisabled + " without pause marker - unexpected disable, owner must self-certify") }
if ($cronDaysLeft -ge 0 -and $cronDaysLeft -lt 2) { AddFlag 'CRON_EVAL_DUE' 'infra' ("durable cron days_left_min=" + $cronDaysLeft + " (per D4: per-band eval due 10-12)") }
if ($cloudf -gt 30) { AddFlag 'CLOUDF_BACKLOG' 'infra' ("pending=" + $cloudf + " (drain needs idle CLI window)") }
if ($liveVerdict -eq 'RED') { AddFlag 'FLEET_LIVENESS_RED' 'infra' ('liveness verdict RED (age ' + $liveAgeH + 'h)') }

# ---- publish watch json ----
$snap = @{
  machine   = $M
  ts        = $now.ToString('yyyy-MM-dd HH:mm:ss')
  yield_mode = $yield
  yield_note = $yieldNote
  cpu       = @{ load_pct = $cpuPct }
  gpu       = @{ util_pct = $gpuUtil; vram_used_mb = $vramUsed; vram_total_mb = $vramTotal; batch = $gpuBatch }
  ram_free_gb = $ramFreeGb
  engine    = $eng
  llm       = @{ pinned_llm = $pinned; pinned_35b = $pinned }   # pinned_35b dual-write kept one round (C-05; 35b retired 10-14)
  comfy     = @{ alive = $comfy }
  infra     = @{ prev_watch_age_h = $prevAgeH; cron_jobs = $cronJobs; cron_days_left_min = $cronDaysLeft; cloudf_pending = $cloudf; liveness = $liveVerdict; liveness_age_h = $liveAgeH; family_disabled = $familyDisabled }
  subsidiaries = $subs
  research  = @{ fresh72 = $research72; status = $researchStatus }
  lanes     = @{ cpu = $laneCpu; gpu = $laneGpu; llm = $laneLlm }
  red_flags = $flags
}
$tmp = $watchPath + '.tmp'
[IO.File]::WriteAllText($tmp, ($snap | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding $false))
Move-Item -LiteralPath $tmp -Destination $watchPath -Force

# ---- red-flag digest (rolling) ----
if ($flags.Count -gt 0) {
  $rfPath = Join-Path $outDir ("RED-FLAGS-" + $M + ".md")
  $head = ("# RED FLAGS - " + $M + " (rolling, newest first; consumed by patrol auto-replenish + decision rounds)`n`n")
  $rows = @()
  foreach ($f in $flags) { $rows += ("- " + $now.ToString('MM-dd HH:mm') + " [" + $f.code + "] " + $f.line + " - " + $f.detail) }
  $old = @()
  if (Test-Path $rfPath) { $old = @((Get-Content -LiteralPath $rfPath -Encoding UTF8) | Where-Object { $_ -match '^- ' }) }
  [IO.File]::WriteAllText($rfPath, ($head + (($rows + $old) | Select-Object -First 120) -join "`n") + "`n", (New-Object System.Text.UTF8Encoding $false))
}

# ---- machine-health.json append (revive hourly ledger, C-20261001-03) ----
$mhPath = Join-Path $Root 'quant\bigmoney\fleet\machine-health.json'
try {
  $overall = 'GREEN'
  foreach ($f in $flags) { if ($f.line -eq 'fleet') { $overall = 'RED' } }
  if ($overall -eq 'GREEN' -and $flags.Count -gt 0) { $overall = 'AMBER' }
  if ($yield) { $overall = 'YIELD' }
  $work = ("oversight: cpu=" + $laneCpu + " gpu=" + $laneGpu + " llm=" + $laneLlm + " engine_q=" + $eng.queue + " wave=" + $eng.front + " flags=" + $flags.Count)
  $row = @{ ts = $now.ToString('yyyy-MM-dd HH:mm') }
  $row[$M] = @{ util = $overall.ToLower(); work = $work; ram_free_gb = $ramFreeGb; gpu_free_gb = [Math]::Round(($vramTotal - $vramUsed) / 1024, 1) }
  $rows = @()
  if (Test-Path $mhPath) {
    try { $rows = @(Get-Content -LiteralPath $mhPath -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { $rows = @() }
  }
  $rows += $row
  if ($rows.Count -gt 400) { $rows = $rows | Select-Object -Last 400 }
  $tmp2 = $mhPath + '.tmp'
  [IO.File]::WriteAllText($tmp2, ($rows | ConvertTo-Json -Depth 8), (New-Object System.Text.UTF8Encoding $false))
  Move-Item -LiteralPath $tmp2 -Destination $mhPath -Force
} catch { LogLine ('machine-health append fail: ' + $_.Exception.Message) }

LogLine ("run ok cpu=" + $cpuPct + "% gpu=" + $gpuUtil + "% lanes " + $laneCpu + "/" + $laneGpu + "/" + $laneLlm + " flags=" + $flags.Count + " yield=" + $yield)
try { Remove-Item -LiteralPath $lockPath -ErrorAction SilentlyContinue } catch { }
Write-Output ("OVERSIGHT " + $now.ToString('s') + " machine=" + $M + " lanes cpu=" + $laneCpu + " gpu=" + $laneGpu + " llm=" + $laneLlm + " flags=" + $flags.Count)
exit 0
