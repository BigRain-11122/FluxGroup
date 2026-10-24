# fleet-poke-worker.ps1 - FleetLink background pull+wake worker v1.8 (CEO order O-20261009-1750 "very fast sync").
# v1.8 (2026-10-17 force-repos concat fix, bm-b live-fire x2): with a single-element
# poke_repos (all nodes use ['.']) the pipeline `@($node.poke_repos) | ForEach-Object`
# UNROLLED the array into a scalar string, so `$pullSet += $fs` did string CONCATENATION
# ('.' + 'quant/bigmoney' = '.quant/bigmoney' -> ':no-repo' on both the v1.8 listener at
# 21:52 and the v1.9.3 listener at 08:33) - the force-repos COLD-tier pull channel was
# broken fleet-wide since v1.5. Array-wrap @(...) keeps $pullSet an array. Normal '.'
# HOT pulls were unaffected (a scalar still iterates fine), which is why this hid until
# first live use.
# v1.6 (2026-10-16 fleet-linkup order): lock now stores its pid - a FRESH lock
# owned by a DEAD process (crashed worker) no longer blocks pokes for 10min;
# the stale-but-fresh lock is reclaimed immediately and the takeover is logged
# (lock-reclaim). Live-owner semantics unchanged. Backward compatible: parses
# legacy "pid=N" text locks too.
# v1.7 (2026-10-16 bm-b blood-swap live-fire): the listener freshness gate now
# VERIFIES each spawn tier by watching the local /health version actually flip
# before trusting it; silent-start failures fall through to the next tier (bm-b
# 20:18 evidence: gate fired, tier-2 register reported success, listener stayed
# v1.8 - Interactive-principal tasks never start without an interactive logon
# session). Gate trigger widened: also fires when the LIVE /health version
# differs from the on-disk version (covers a dead same-version listener and a
# stale-version listener holding the port while state.json lies either way).
# v1.5 (2026-10-16 CEO check "is fleet sync fastest/most effective" - bm-c stuck on
# v1.7 root cure): listener freshness gate - if the on-disk fleet-link.ps1 version
# is newer than the RUNNING listener (state.json), start a fresh instance; the
# existing port-contention self-upgrade replaces the old one. This is the remote
# upgrade channel for nodes whose FluxGroup-FleetLink keepalive task is not
# cycling (bm-c: task trigger dead, listener frozen on v1.7, large-body /sync
# rejected forever). If the task is MISSING, re-registers it via
# register-fleet-link.ps1 (idempotent) so 5-min supervision is healed too.
# v1.1 = O-20261009-1750 "very fast sync" upgrade).
# Spawned hidden by the listener's /poke handler so the accept loop NEVER blocks on
# git pulls (v1.0 inline pull blocked /health for the whole pull duration - the
# "timeout while busy" root cause). Lock-serialized: one worker at a time per node;
# a fresh lock means a pull is already in flight (it fetches the newest anyway).
#   - lock file   : ~\.codely-cli\fleet-link\worker.lock  (stale >10min = crashed worker, reclaimed)
#   - stamp file  : ~\.codely-cli\fleet-link\last-pull-<node>.json (ts + repo HEADs -> /status)
# Law anchors unchanged: signals only, data stays in git; allowlisted tasks only.
param(
  [string]$Root = (Split-Path -Parent $PSScriptRoot),
  [string]$NodeId = "",
  [string]$Reason = "poke",
  [string]$TasksJson = "[]",
  [string]$PullReposJson = "[]",
  [string]$TasksB64 = "",
  [string]$ReposB64 = ""
)
# v1.3 (C-20261009-04): base64 channel from listener v1.4 - the old quoted
# -TasksJson argument embedded JSON double-quotes inside a quoted -ArgumentList
# string, which broke param binding (workers always received []). Legacy params
# still honored for older listeners.
if ($TasksB64 -ne "") { try { $TasksJson = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($TasksB64)) } catch { } }
if ($ReposB64 -ne "") { try { $PullReposJson = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($ReposB64)) } catch { } }
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

# ---- v1.7: live listener version probe + version-flip watcher (gate ground truth) ----
function WK-ListenerPort() {
  $p = 8790
  try { if ($cfg -and ($cfg.PSObject.Properties.Name -contains 'port')) { $p = [int]$cfg.port } } catch { }
  return $p
}
function WK-LiveListenerVers() {
  try {
    $h = Invoke-RestMethod -Uri ('http://127.0.0.1:' + (WK-ListenerPort) + '/health') -TimeoutSec 3
    return [string]$h.version
  } catch { return '' }
}
function WK-WaitListenerVers([string]$want, [int]$secs) {
  $deadline = (Get-Date).AddSeconds($secs)
  while ((Get-Date) -lt $deadline) {
    if ((WK-LiveListenerVers) -eq $want) { return $true }
    Start-Sleep -Milliseconds 700
  }
  return $false
}

# ---- single-flight lock (v1.6: pid-verified - a fresh lock owned by a dead
# process is reclaimed immediately instead of blocking pokes for 10min) ----
if (Test-Path $LockF) {
  try {
    $age = ((Get-Date) - (Get-Item $LockF).LastWriteTime).TotalMinutes
    $olk = Get-Content -Raw -LiteralPath $LockF -ErrorAction SilentlyContinue
    $opid = 0
    try { $opid = [int]($olk | ConvertFrom-Json).pid } catch { if ($olk -match 'pid=(\d+)') { $opid = [int]$Matches[1] } }
    $alive = $false
    if ($opid -gt 0) { $alive = [bool](Get-Process -Id $opid -ErrorAction SilentlyContinue) }
    if ($alive -and $age -lt 10) { WK-Log 'worker-skip' ('lock fresh ' + [math]::Round($age, 1) + 'm pid=' + $opid); exit 0 }
    WK-Log 'lock-reclaim' ('age=' + [math]::Round($age, 1) + 'm pid=' + $opid + ' alive=' + $alive)
    Remove-Item $LockF -Force -ErrorAction SilentlyContinue
  } catch { }
}
try { [IO.File]::WriteAllText($LockF, ('{"pid":' + $PID + ',"ts":"' + (Get-Date -Format s) + '","reason":"' + $Reason + '"}'), (New-Object System.Text.UTF8Encoding($false))) } catch { }

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
if ($node -and ($node.PSObject.Properties.Name -contains 'poke_repos')) { $pullSet = @(@($node.poke_repos) | ForEach-Object { [string]$_ }) }
if ($pullSet.Count -eq 0) { $pullSet = @('.') }
foreach ($f in $force) {
  $fs = [string]$f
  $registered = ($node -and ($node.PSObject.Properties.Name -contains 'repos') -and (@($node.repos) -contains $fs))
  if ($registered -and ($pullSet -notcontains $fs)) { $pullSet += $fs }
  elseif (-not $registered) { $heads += ($fs + ':force-deny') }
}
foreach ($rel in $pullSet) {
    $p = Join-Path $Root ([string]$rel)
    if (-not (Test-Path (Join-Path $p '.git'))) {
      # v1.9.5 (CEO fleet full-sync 2026-10-24): self-heal a MISSING registered
      # repo instead of reporting :no-repo forever. Clone URL comes from the
      # roster (Tools/fleet-nodes.json repo_urls) so no machine needs a local
      # URL list; blob-less clone keeps the initial transfer small. Gated by
      # autoclone=true (default off) so a full media repo is never pulled onto
      # a box that did not ask for it. Runs peer-side per poke - git stays the
      # sole data channel, no remote command plane is introduced.
      $url = ''
      try {
        $cfgNow = Get-Content -Raw -Encoding UTF8 (Join-Path $Root 'Tools\fleet-nodes.json') | ConvertFrom-Json
        if ($cfgNow.PSObject.Properties.Name -contains 'repo_urls' -and $cfgNow.repo_urls.PSObject.Properties.Name -contains [string]$rel) {
          $url = [string]$cfgNow.repo_urls.([string]$rel)
        }
        $autoOn = $false
        if ($node -and ($node.PSObject.Properties.Name -contains 'autoclone')) { $autoOn = [bool]$node.autoclone }
        if (-not $autoOn -and $cfgNow.PSObject.Properties.Name -contains 'autoclone_default') { $autoOn = [bool]$cfgNow.autoclone_default }
      } catch { $url = '' }
      if ($url -ne '') {
        try { New-Item -ItemType Directory -Path (Split-Path -Parent $p) -Force | Out-Null } catch { }
        $cl = @()
        try { $cl = @(& $git clone --filter=blob:none $url $p 2>&1 | ForEach-Object { [string]$_ }) } catch { $cl = @([string]$_.Exception.Message) }
        if (Test-Path (Join-Path $p '.git')) { $heads += ([string]$rel + ':cloned'); continue }
        $heads += ([string]$rel + ':clone-fail')
        continue
      }
      $heads += ([string]$rel + ':no-repo'); continue
    }
    $lines = @()
    # v1.9.6 (CEO full-sync 2026-10-24): a repo whose remote.origin.fetch does NOT
    # map its own branch (bm-c MiniGame pulls `machine/C` but the config only maps
    # master) reports "Already up to date" forever while the tracking ref stays
    # stale - a silent black hole. Explicit single-branch fetch (server-advertised
    # ref only, safe on blobless promisor clones per FleetPush's U104(3) rule)
    # before the pull keeps the tracking ref honest.
    try {
      $br = @(& $git -C $p rev-parse --abbrev-ref HEAD 2>$null | ForEach-Object { [string]$_ })[0]
      if ($br -and $br -ne 'HEAD') {
        # v1.9.6c: retry x3 like FleetPush's U104(3) rule - a blobless promisor
        # clone rejects a lazy backfill negotiation wholesale ("not our ref") on
        # the first try and then succeeds; without the retry the tracking ref
        # never moves and every later merge reports "Already up to date".
        $spec = "+refs/heads/" + $br + ":refs/remotes/origin/" + $br
        foreach ($t in 1..3) {
          $null = & $git -C $p fetch origin $spec 2>&1
          if ($LASTEXITCODE -eq 0) { break }
          Start-Sleep -Seconds 4
        }
      }
    } catch { }
    # v1.9.6b: merge the freshly fetched tracking ref explicitly (a bare
    # `git pull` resolves the upstream from config and misses the ref we just
    # refreshed when the clone is single-branch).
    try {
      if ($br -and $br -ne 'HEAD') { $lines = @(& $git -C $p merge --ff-only ("origin/" + $br) 2>&1 | ForEach-Object { [string]$_ }) }
      else { $lines = @(& $git -C $p pull --ff-only 2>&1 | ForEach-Object { [string]$_ }) }
    } catch { $lines = @([string]$_.Exception.Message) }
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

# ---- v1.5 listener freshness gate: upgrade/revive the local listener when a
# newer fleet-link.ps1 shipped via git (runs AFTER pulls so the newest code is on
# disk; zero side effects when versions already match). Try the scheduled task
# first (durable), then idempotent re-registration (heals a missing task), then a
# raw hidden instance as last resort. v1.7: every tier is VERIFIED against the
# live /health version; failures fall through to the next tier. ----
try {
  $flScript = Join-Path $Root 'Tools\fleet-link.ps1'
  $stateF2 = Join-Path $Dir 'state.json'
  if (Test-Path $flScript) {
    $diskVers = ''
    $m = [regex]::Match([IO.File]::ReadAllText($flScript), "\`$Vers\s*=\s*'([0-9.]+)'")
    if ($m.Success) { $diskVers = $m.Groups[1].Value }
    $runVers = ''
    if (Test-Path $stateF2) { try { $runVers = [string]((Get-Content -Raw $stateF2 | ConvertFrom-Json).version) } catch { } }
    $liveVers = WK-LiveListenerVers
    $need = $false
    if ($diskVers -ne '') {
      if ($runVers -ne '' -and ([version]$diskVers -gt [version]$runVers)) { $need = $true }
      elseif ($liveVers -ne $diskVers) { $need = $true }
    }
    if ($need) {
      # v1.7: verify each tier actually flipped the listener; fall through on
      # failure. Misfires are harmless - a same-version extra instance exits
      # 'no bind' via port contention, and a takeover replaces the old listener.
      $tiers = @()
      $ok = $false
      try { Start-ScheduledTask -TaskName 'FluxGroup-FleetLink' -ErrorAction Stop; $tiers += 'task:start'; $ok = WK-WaitListenerVers $diskVers 15 } catch { $tiers += 'task:fail' }
      if (-not $ok) {
        try {
          $reg = Join-Path $Root 'Tools\register-fleet-link.ps1'
          if (Test-Path $reg) { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $reg -Root $Root 2>&1 | Out-Null; $tiers += 'reg:run'; $ok = WK-WaitListenerVers $diskVers 15 }
        } catch { $tiers += 'reg:fail' }
      }
      if (-not $ok) {
        $argz = '-NoProfile -ExecutionPolicy Bypass -File "' + $flScript + '" -Root "' + $Root + '" -NodeId ' + $NodeId
        Start-Process -FilePath 'powershell.exe' -ArgumentList $argz -WindowStyle Hidden | Out-Null
        $tiers += 'raw:spawn'
        $ok = WK-WaitListenerVers $diskVers 20
      }
      WK-Log 'listener-refresh' ('running=' + $runVers + ' live=' + $liveVers + ' disk=' + $diskVers + ' tiers=' + ($tiers -join ' ') + ' upgraded=' + $ok)
    }
  }
} catch { WK-Log 'listener-refresh-fail' ([string]$_.Exception.Message) }

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
  # v1.4 stamp: origin_main = fetched canonical head (local main may run AHEAD via
  # memory-union commits - node still synced; dispatcher verify reads this field).
  $om = ''
  try { $om = [string](& $git -C $Root rev-parse origin/main) } catch { }
  $st = [ordered]@{ node = $NodeId; ts = (Get-Date -Format s); reason = $Reason
                    pulls = @($heads); wakes = @($woke); repo_heads = $repoHeads
                    origin_main = $om }
  [IO.File]::WriteAllText($StampF, ($st | ConvertTo-Json -Depth 4 -Compress), (New-Object System.Text.UTF8Encoding($false)))
} catch { }
WK-Log 'worker-done' ('reason=' + $Reason + ' pull=' + ($heads -join ' ') + ' wake=' + ($woke -join ' '))
try { Remove-Item $LockF -Force -ErrorAction SilentlyContinue } catch { }
exit 0
