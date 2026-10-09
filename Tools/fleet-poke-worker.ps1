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
  [string]$TasksJson = "[]",
  [string]$PullReposJson = "[]"
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

# ---- pull policy (O-20261009-1755 sync tiers): HOT = node.poke_repos + explicitly
# forced repos (request must be allowlisted against node.repos). WARM repos are
# pulled by their OWN loop tasks on round cadence - NOT duplicated here. The
# stamp below still reports ALL registered repo HEADs (rev-parse is cheap). ----
$git = 'git'
$heads = @()
$force = @()
try { $force = @((($PullReposJson) | ConvertFrom-Json) | ForEach-Object { [string]$_ }) } catch { }
$force = @($force | Where-Object { $_ -and $_.Trim() -ne '' })
$pullSet = @()
if ($node -and ($node.PSObject.Properties.Name -contains 'poke_repos')) { $pullSet = @($node.poke_repos) | ForEach-Object { [string]$_ } }
if ($pullSet.Count -eq 0) { $pullSet = @('.') }
foreach ($f in $force) {
  $fs = [string]$f
  $registered = ($node -and ($node.PSObject.Properties.Name -contains 'repos') -and (@($node.repos) -contains $fs))
  if ($registered -and ($pullSet -notcontains $fs)) { $pullSet += $fs }
  elseif (-not $registered) { $heads += ($fs + ':force-deny') }
}
foreach ($rel in $pullSet) {
    $p = Join-Path $Root ([string]$rel)
    if (-not (Test-Path (Join-Path $p '.git'))) { $heads += ([string]$rel + ':no-repo'); continue }
    $lines = @()
    try { $lines = @(& $git -C $p pull --ff-only 2>&1 | ForEach-Object { [string]$_ }) } catch { $lines = @([string]$_.Exception.Message) }
    $s = $lines -join ' | '
    if ($s -match 'up to date') { $heads += ([string]$rel + ':current') }
    elseif ($s -match 'Fast-forward') { $heads += ([string]$rel + ':updated') }
    elseif ($s -match 'would be overwritten by merge') {
      # v1.2 (O-20261009-1755): dirty in-flight files (usually session CODELY.md
      # memory) must NEVER block the command plane and NEVER be lost.
      # Directed autostash: stash ONLY the blocking paths -> ff-merge -> pop.
      # Pop conflict (upstream touched same file): keep the LOCAL session
      # version (theirs in stash-pop = stashed local edits); upstream version
      # stays in history; owning window commits its version at round end.
      $block = @()
      $inBlock = $false
      foreach ($ln in $lines) {
        if ($ln -match 'would be overwritten by merge') { $inBlock = $true; continue }
        if ($inBlock) {
          if ($ln -match '^\s+(\S+)\s*$') { $block += $Matches[1]; continue }
          $inBlock = $false
        }
      }
      $block = @($block | Where-Object { $_ -and (Test-Path (Join-Path $p $_)) } | Select-Object -First 12)
      if ($block.Count -eq 0) {
        $heads += ([string]$rel + ':fail')
        WK-Log 'pull-fail' ([string]$rel + ' ' + $s.Substring(0, [Math]::Min(200, $s.Length)))
        continue
      }
      $tag = 'fleet-autostash-' + (Get-Date -Format 'yyyyMMddHHmmss')
      $stashArgs = @('-C', $p, 'stash', 'push', '-m', $tag, '--') + $block
      $null = & $git @stashArgs 2>&1
      $mlines = @(& $git -C $p merge --ff-only origin/main 2>&1 | ForEach-Object { [string]$_ })
      $m = $mlines -join ' | '
      if ($m -match 'Fast-forward|up to date|Already up to date') {
        $plines = @(& $git -C $p stash pop 2>&1 | ForEach-Object { [string]$_ })
        $pop = $plines -join ' | '
        if ($pop -match 'CONFLICT') {
          foreach ($bf in $block) { $null = & $git -C $p checkout --theirs -- $bf 2>&1 }
          $unstageArgs = @('-C', $p, 'restore', '--staged', '--') + $block
          $null = & $git @unstageArgs 2>&1
          $null = & $git -C $p stash drop 2>&1
          $heads += ([string]$rel + ':updated-kept-local')
          WK-Log 'autostash-conflict-kept-local' ([string]$rel + ' ' + ($block -join ','))
        } else { $heads += ([string]$rel + ':updated-restored-inflight') }
      } else {
        # merge still failed - restore stashed edits immediately (never hold them)
        $null = & $git -C $p stash pop 2>&1
        $heads += ([string]$rel + ':fail')
        WK-Log 'pull-fail' ([string]$rel + ' ' + $s.Substring(0, [Math]::Min(200, $s.Length)))
      }
    }
    else {
      $heads += ([string]$rel + ':fail')
      if ($s.Length -gt 200) { $s = $s.Substring(0, 200) }
      WK-Log 'pull-fail' ([string]$rel + ' ' + $s)
    }
}

# ---- global memory union-sync (O-20261009-1845: CEO pain point "memory missing on
# other fleet machines" - the global CODELY.md never traveled. Runs AFTER pulls so
# fresh canonical entries flow down to this machine, and this machine's local-only
# entries flow up to the canonical + commit+push. Fail-soft: never blocks wake.) ----
try {
  $memSync = Join-Path $Root 'Tools\fleet-memory-sync.ps1'
  if (Test-Path $memSync) {
    $null = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $memSync -Root $Root -Quiet 2>&1
  }
} catch { WK-Log 'memsync-fail' ([string]$_.Exception.Message) }

# ---- wake allowlisted tasks ----
$woke = @()
$reqTasks = @()
try { $reqTasks = @((($TasksJson) | ConvertFrom-Json) | ForEach-Object { [string]$_ }) } catch { }
$reqTasks = @($reqTasks | Where-Object { $_ -and $_.Trim() -ne '' })
$allow = @()
if ($node -and ($node.PSObject.Properties.Name -contains 'wake_tasks')) { $allow = @($node.wake_tasks) | ForEach-Object { [string]$_ } }
foreach ($t in $reqTasks) {
  $ts = [string]$t
  if ($allow -notcontains $ts) { $woke += ($ts + ':deny'); continue }
  $task = Get-ScheduledTask -TaskName $ts -ErrorAction SilentlyContinue
  if (-not $task) { $woke += ($ts + ':no-task'); continue }
  if ($task.State.ToString() -eq 'Running') { $woke += ($ts + ':busy-skip'); continue }
  # v1.3 (C-20261009-04): CEO freeze faces (design-state Disabled tasks) must not
  # be re-armed by a remote wake - same off-skip protection as the local sentinel.
  if ($task.State.ToString() -eq 'Disabled') { $woke += ($ts + ':off-skip'); continue }
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
