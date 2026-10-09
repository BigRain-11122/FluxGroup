# fleet-poke-worker.ps1 - FleetLink background pull+wake worker v1.1 (CEO order O-20261009-1750 "very fast sync").
# Spawned hidden by the listener's /poke handler so the accept loop NEVER blocks on
# git pulls (v1.0 inline pull blocked /health for the whole pull duration - the
# "timeout while busy" root cause). Lock-serialized: one worker at a time per node;
# a fresh lock means a pull is already in flight (it fetches the newest anyway).
#   - lock file   : ~\.codely-cli\fleet-link\worker.lock  (stale >10min = crashed worker, reclaimed)
#   - stamp file  : ~\.codely-cli\fleet-link\last-pull-<node>.json (ts + repo HEADs -> /status)
# Law anchors unchanged: signals only, data stays in git; allowlisted tasks only.
param(
  [string]$Root = "C:\Users\sjs20\Desktop\FluxGroup",
  [string]$NodeId = "",
  [string]$Reason = "poke",
  [string]$TasksJson = "[]"
)
$ErrorActionPreference = 'Continue'
$Dir = Join-Path $env:USERPROFILE '.codely-cli\fleet-link'
if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
$LogF = Join-Path $Dir 'log.jsonl'
$LockF = Join-Path $Dir 'worker.lock'
$StampF = Join-Path $Dir ('last-pull-' + $NodeId + '.json')

function WK-Log([string]$evt, [string]$detail) {
  try {
    $o = [ordered]@{ ts = (Get-Date -Format s); event = $evt; detail = $detail }
    ($o | ConvertTo-Json -Compress) | Add-Content -LiteralPath $LogF -Encoding UTF8
  } catch { }
}

# ---- single-flight lock ----
if (Test-Path $LockF) {
  try {
    $age = ((Get-Date) - (Get-Item $LockF).LastWriteTime).TotalMinutes
    if ($age -lt 10) { WK-Log 'worker-skip' ('lock fresh ' + [math]::Round($age, 1) + 'm'); exit 0 }
    Remove-Item $LockF -Force -ErrorAction SilentlyContinue
  } catch { }
}
try { Set-Content -LiteralPath $LockF -Value ("pid=" + $PID + " reason=" + $Reason) -Encoding ASCII } catch { }

# ---- roster ----
$node = $null
try {
  $cfg = Get-Content -Raw -Encoding UTF8 (Join-Path $Root 'Tools\fleet-nodes.json') | ConvertFrom-Json
  foreach ($n in @($cfg.nodes)) {
    if ($NodeId -ne '' -and [string]$n.id -eq $NodeId) { $node = $n; break }
    if ($NodeId -eq '' -and [string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $node = $n; $NodeId = [string]$n.id; break }
  }
} catch { }
if ($NodeId -eq '') { $NodeId = $env:COMPUTERNAME }

# ---- pull all registered repos (fast: git pull --ff-only) ----
$git = 'git'
$heads = @()
if ($node -and ($node.PSObject.Properties.Name -contains 'repos')) {
  foreach ($rel in @($node.repos)) {
    $p = Join-Path $Root ([string]$rel)
    if (-not (Test-Path (Join-Path $p '.git'))) { $heads += ([string]$rel + ':no-repo'); continue }
    $s = ''
    try { $s = [string]((& $git -C $p pull --ff-only 2>&1 | ForEach-Object { [string]$_ }) -join ' | ') } catch { $s = [string]$_.Exception.Message }
    if ($s -match 'up to date') { $heads += ([string]$rel + ':current') }
    elseif ($s -match 'Fast-forward') { $heads += ([string]$rel + ':updated') }
    else {
      $heads += ([string]$rel + ':fail')
      if ($s.Length -gt 200) { $s = $s.Substring(0, 200) }
      WK-Log 'pull-fail' ([string]$rel + ' ' + $s)
    }
  }
}

# ---- wake allowlisted tasks ----
$woke = @()
$reqTasks = @()
try { $reqTasks = @((($TasksJson) | ConvertFrom-Json) | ForEach-Object { [string]$_ }) } catch { }
$allow = @()
if ($node -and ($node.PSObject.Properties.Name -contains 'wake_tasks')) { $allow = @($node.wake_tasks) | ForEach-Object { [string]$_ } }
foreach ($t in $reqTasks) {
  $ts = [string]$t
  if ($allow -notcontains $ts) { $woke += ($ts + ':deny'); continue }
  $task = Get-ScheduledTask -TaskName $ts -ErrorAction SilentlyContinue
  if (-not $task) { $woke += ($ts + ':no-task'); continue }
  if ($task.State.ToString() -eq 'Running') { $woke += ($ts + ':busy-skip'); continue }
  try { Start-ScheduledTask -TaskName $ts; $woke += ($ts + ':WAKE') } catch { $woke += ($ts + ':wake-fail') }
}

# ---- stamp (repo HEADs for /status + dispatcher verification) ----
$repoHeads = @{}
try {
  if ($node -and ($node.PSObject.Properties.Name -contains 'repos')) {
    foreach ($rel in @($node.repos)) {
      $p = Join-Path $Root ([string]$rel)
      if (Test-Path (Join-Path $p '.git')) {
        $h = ''
        try { $h = [string](& $git -C $p rev-parse HEAD) } catch { }
        if ($h) { $repoHeads[[string]$rel] = $h.Trim() }
      }
    }
  }
} catch { }
try {
  $st = [ordered]@{ node = $NodeId; ts = (Get-Date -Format s); reason = $Reason
                    pulls = @($heads); wakes = @($woke); repo_heads = $repoHeads }
  [IO.File]::WriteAllText($StampF, ($st | ConvertTo-Json -Depth 4 -Compress), (New-Object System.Text.UTF8Encoding($false)))
} catch { }
WK-Log 'worker-done' ('reason=' + $Reason + ' pull=' + ($heads -join ' ') + ' wake=' + ($woke -join ' '))
try { Remove-Item $LockF -Force -ErrorAction SilentlyContinue } catch { }
exit 0
