# fleet-sync-pusher.ps1 - FleetLink outbound HOT-file pusher v1.0 (CEO order
# O-20261016-1215 millisecond mandate; root-cure of the 2026-10-16 CEO check
# "is fleet sync fastest/most effective"): v1.8 ran poll+push INLINE in the
# listener accept loop, so a slow/failing 703KB orders.md push over the degraded
# DERP relay (8s socket timeout) blocked /health and /poke for the whole push -
# the signal plane was starved by the data plane (live evidence 2026-10-16:
# bm-a /health 20s timeout; 193 push-fail + 77 reject vs 3 successes).
# This process owns the OUTBOUND side completely:
#   - spawned + supervised by fleet-link.ps1 v1.9 (heartbeat pusher.json;
#     listener respawns when stale >90s); single-flight via pid-verified lock
#   - 2s poll on the /sync allowlist; pusher-state.json is pusher-owned
#     (pushed marks + 60s backoff), sync-state.json stays listener-owned
#     (applied hashes) and is READ-ONLY here - zero write contention
#   - 30s socket timeouts (relay-grade transport; 8s killed 700KB pushes)
#   - gzip body when the peer runs >=1.9 (703KB markdown ~ 130KB on the wire),
#     plain content for older peers (v1.8 receives plain fine)
#   - version self-check every 60s: exits when a newer pusher ships via git,
#     the listener respawns the new file (no task dependency)
# v1.3 (2026-10-16 fleet-linkup order "all permissions granted"): (1) skip-log
#   path bug - $rel was undefined in Poll-Publish, logs printed an empty path;
#   (2) FAILED /health probe no longer pins a peer as "legacy" for 10min -
#   over the degraded DERP relay an 8s probe miss made bm-c (already 1.9.2)
#   look legacy, so the 369KB orders.md rode git for hours; failed-probe cache
#   TTL is now 60s, probe timeout 8->12s; (3) peer version changes are logged
#   (peer-vers) for the audit plane. Skip semantics stay conservative: unknown
#   version + >200KB body still skips (a gz-only body into a pre-1.9 peer
#   would "succeed" with applied=0 and poison the pushed marks - data black
#   hole, never blind-send gz).
# v1.4 (2026-10-16 fleet-linkup live-fire): wire-size precheck - orders.md is
#   711KB utf-8; gz+base64+JSON still puts 445KB on the wire, ABOVE the peer
#   v1.9.2 262144 fast-reject line, so every push bounced in ~1s forever
#   (live probe 20:11: HTTP 200 body-too-large). The audit doc's "~130KB on the
#   wire" claim for orders.md is hereby corrected - it never actually landed.
#   Now: a gzipped body that still exceeds the fast-reject line skips honestly
#   (git carries) instead of bouncing forever; fail logs carry the path too.
#   orders.md hot-push unlocks only after the 10-19 slimming batch reaches
#   base64(gzip(utf8)) <= 256KB (needs ~43% cut at current content).
# PS 5.1 safe: ASCII-only body; allowlist mirrors fleet-link.ps1 v1.9 (mirror
# law: change BOTH when the /sync face changes).
param(
  [string]$Root = (Split-Path -Parent $PSScriptRoot),
  [int]$Port = 8790,
  [string]$NodeId = ""
)
$ErrorActionPreference = 'Continue'
$Dir = Join-Path $env:USERPROFILE '.codely-cli\fleet-link'
if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
$Vers = '1.4'
$LogF = Join-Path $Dir 'log.jsonl'
$SyncStateF = Join-Path $Dir 'sync-state.json'
$PushStateF = Join-Path $Dir 'pusher-state.json'
$HbF = Join-Path $Dir 'pusher.json'
$LockF = Join-Path $Dir 'pusher.lock'

function PS-Log([string]$evt, [string]$detail) {
  try {
    $o = [ordered]@{ ts = (Get-Date -Format s); event = $evt; detail = $detail }
    ($o | ConvertTo-Json -Compress) | Add-Content -LiteralPath $LogF -Encoding UTF8
  } catch { }
}

# ---- roster: resolve self + peers + port (mirrors listener) ----
$node = $null
$peers = @()
try {
  $cfg = Get-Content -Raw -Encoding UTF8 (Join-Path $Root 'Tools\fleet-nodes.json') | ConvertFrom-Json
  if ($cfg.PSObject.Properties.Name -contains 'port') { $Port = [int]$cfg.port }
  foreach ($n in @($cfg.nodes)) {
    if ($NodeId -ne '' -and [string]$n.id -eq $NodeId) { $node = $n; break }
    if ($NodeId -eq '' -and [string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $node = $n; $NodeId = [string]$n.id; break }
  }
  foreach ($n in @($cfg.nodes)) {
    if (([bool]$n.enabled) -and ([string]$n.id -ne $NodeId) -and [string]$n.tailnet_ip -ne '') { $peers += $n }
  }
} catch { PS-Log 'config-fail' ([string]$_.Exception.Message) }
if ($NodeId -eq '') { $NodeId = $env:COMPUTERNAME }

# /sync allowlist - MIRROR of fleet-link.ps1 v1.9 $SyncAllowUnion (mirror law)
$SyncAllowUnion = @(
  'docs/orders.md',
  'cph4/fleet/mv0001-handover/outbound/krea2/kf-demo-20261012/bmc/I2V-URL-INDEX.md',
  'cph4/fleet/dispatcher/CEO-PROXY/LOG.md',
  'cph4/fleet/dispatcher/PATROL-FLEET/LOG.md'
)
$SyncAllowFullPrefix = 'cph4/fleet/dispatcher/delivery-watch/'

# ---- single-flight lock (pid-verified) ----
if (Test-Path $LockF) {
  try {
    $opid = 0
    try { $opid = [int]((Get-Content -Raw $LockF | ConvertFrom-Json).pid) } catch { }
    $age = 999
    try { $age = ((Get-Date) - (Get-Item $LockF).LastWriteTime).TotalSeconds } catch { }
    $alive = $false
    if ($opid -gt 0 -and $opid -ne $PID) { $alive = [bool](Get-Process -Id $opid -ErrorAction SilentlyContinue) }
    if ($age -lt 30 -and $alive) { PS-Log 'exit' 'another pusher is alive'; exit 0 }
  } catch { }
}
function Touch-Lock() {
  try {
    $o = [ordered]@{ pid = $PID; ts = (Get-Date -Format s) }
    [IO.File]::WriteAllText($LockF, ($o | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
  } catch { }
}
function Touch-Hb() {
  try {
    $o = [ordered]@{ node = $NodeId; pid = $PID; ts = (Get-Date -Format s); version = $Vers }
    [IO.File]::WriteAllText($HbF, ($o | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
  } catch { }
}

function Gz-Compress([string]$text) {
  $inBytes = [System.Text.Encoding]::UTF8.GetBytes($text)
  $ms = New-Object System.IO.MemoryStream
  $gz = New-Object System.IO.Compression.GZipStream($ms, [System.IO.Compression.CompressionLevel]::Optimal)
  $gz.Write($inBytes, 0, $inBytes.Length)
  $gz.Close()
  return [Convert]::ToBase64String($ms.ToArray())
}

# ---- state: pusher-owned pushed/backoff + listener-owned applied (read-only) ----
function Load-PushState() {
  $o = @{ pushed = @{}; lastTry = @{} }
  $seedF = $PushStateF
  if (-not (Test-Path $seedF)) { $seedF = $SyncStateF }   # legacy v1.8 carry-over seed
  try {
    if (Test-Path $seedF) {
      $raw = Get-Content -Raw -Encoding UTF8 $seedF | ConvertFrom-Json
      if ($raw.pushed) {
        foreach ($pp in $raw.pushed.PSObject.Properties) {
          $inner = @{}
          if ($pp.Value) { foreach ($pr in $pp.Value.PSObject.Properties) { $inner[$pr.Name] = [string]$pr.Value } }
          $o.pushed[$pp.Name] = $inner
        }
      }
      if ($raw.lastTry) { foreach ($pr in $raw.lastTry.PSObject.Properties) { $o.lastTry[$pr.Name] = [long]$pr.Value } }
    }
  } catch { }
  return $o
}
function Save-PushState($s) {
  try { [IO.File]::WriteAllText($PushStateF, ($s | ConvertTo-Json -Depth 6 -Compress), (New-Object System.Text.UTF8Encoding($false))) } catch { }
}
function Load-Applied() {
  $h = @{}
  try {
    if (Test-Path $SyncStateF) {
      $raw = Get-Content -Raw -Encoding UTF8 $SyncStateF | ConvertFrom-Json
      if ($raw.applied) { foreach ($pr in $raw.applied.PSObject.Properties) { $h[$pr.Name] = [string]$pr.Value } }
    }
  } catch { }
  return $h
}
function Sync-HashFile([string]$p) {
  try { return [string](Get-FileHash -LiteralPath $p -Algorithm MD5).Hash } catch { return '' }
}

# ---- peer version cache (gzip eligibility), 10min TTL on SUCCESS, 60s on failure ----
$script:VersCache = @{}
$script:VersLogged = @{}
function Get-PeerVers($peer) {
  $k = [string]$peer.id
  $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  if ($script:VersCache.ContainsKey($k)) {
    $c = $script:VersCache[$k]
    $ttl = 600
    if ([string]$c.vers -eq '') { $ttl = 60 }   # v1.3: probe miss != legacy peer - retry after 60s
    if (($now - [long]$c.ts) -lt $ttl) { return [string]$c.vers }
  }
  $v = ''
  try { $r = Invoke-RestMethod -Uri ('http://' + [string]$peer.tailnet_ip + ':' + $Port + '/health') -TimeoutSec 12; $v = [string]$r.version } catch { }
  $script:VersCache[$k] = @{ ts = $now; vers = $v }
  if ($v -ne '' -and [string]$script:VersLogged[$k] -ne $v) {
    $script:VersLogged[$k] = $v
    PS-Log 'peer-vers' ($k + ' v' + $v)
  }
  return $v
}

function Push-SyncOne([string]$rel, [string]$kind, [string]$content, $peer, [string]$peerVers) {
  try {
    $t0 = Get-Date
    $bodyObj = @{ path = $rel; mode = $kind; src = $NodeId }
    $useGz = $false
    try { if ($peerVers -ne '' -and ([version]$peerVers -ge [version]'1.9')) { $useGz = $true } } catch { }
    if ($useGz) { $bodyObj.gz = (Gz-Compress $content) } else { $bodyObj.content = $content }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($bodyObj | ConvertTo-Json -Compress))
    # v1.4: wire-size precheck - the peer 1.9.2 fast-reject line (262144) applies
    # to Content-Length, i.e. the base64(gzip(...)) envelope, not the raw text.
    # A body above it bounces in ~1s forever; skip honestly and let git carry.
    if ($bytes.Length -gt 262144) {
      PS-Log 'sync-push-skip' ($rel + ' -> ' + [string]$peer.id + ' oversize-on-wire ' + $bytes.Length + 'B (git carries)')
      return @{ ok = $false }
    }
    $c = New-Object System.Net.Sockets.TcpClient
    $c.ReceiveTimeout = 30000; $c.SendTimeout = 30000
    $c.Connect([string]$peer.tailnet_ip, $Port)
    $hdr = 'POST /sync HTTP/1.1' + "`r`n" + 'Content-Type: application/json' + "`r`n" + 'Content-Length: ' + $bytes.Length + "`r`n" + 'Connection: close' + "`r`n`r`n"
    $ns = $c.GetStream()
    $hb = [System.Text.Encoding]::ASCII.GetBytes($hdr)
    $ns.Write($hb, 0, $hb.Length)
    $ns.Write($bytes, 0, $bytes.Length)
    $ns.Flush()
    $r = New-Object System.IO.StreamReader($ns, [System.Text.Encoding]::UTF8)
    $resp = $r.ReadToEnd()
    $c.Close()
    $ms = [int]((Get-Date) - $t0).TotalMilliseconds
    $m = ''
    try { $m = [regex]::Match($resp, '"applied":(\d+)').Groups[1].Value } catch { }
    if ($m -eq '') { PS-Log 'sync-push-reject' ($rel + ' -> ' + [string]$peer.id + ' ms=' + $ms); return @{ ok = $false } }
    PS-Log 'sync-push' ($rel + ' -> ' + [string]$peer.id + ' applied=' + $m + ' gz=' + $useGz + ' bytes=' + $bytes.Length + ' rtt_ms=' + $ms)
    return @{ ok = $true; applied = $m }
  } catch { PS-Log 'sync-push-fail' ([string]$peer.id + ' ' + $rel + ' ' + ([string]$_.Exception.Message)); return @{ ok = $false } }
}

function Poll-Publish() {
  $rels = @()
  foreach ($a in $SyncAllowUnion) { $rels += @{ rel = $a; kind = 'union' } }
  try {
    $dwDir = Join-Path $Root ($SyncAllowFullPrefix -replace '/', '\')
    if (Test-Path $dwDir) {
      foreach ($f in @(Get-ChildItem -LiteralPath $dwDir -Filter '*.json' -File)) {
        $rels += @{ rel = ($SyncAllowFullPrefix + $f.Name); kind = 'full' }
      }
    }
  } catch { }
  if ($peers.Count -eq 0) { return }
  $applied = Load-Applied
  $st = Load-PushState
  $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  $dirty = $false
  foreach ($e in $rels) {
    $p = Join-Path $Root ([string]$e.rel -replace '/', '\')
    if (-not (Test-Path -LiteralPath $p)) { continue }
    $h = Sync-HashFile $p
    if ($h -eq '') { continue }
    if ([string]$applied[[string]$e.rel] -eq $h) { continue }  # echo of what a peer sent us
    foreach ($peer in $peers) {
      $pk = [string]$peer.id
      if (-not $st.pushed.ContainsKey($pk)) { $st.pushed[$pk] = @{} }
      if ([string]$st.pushed[$pk][[string]$e.rel] -eq $h) { continue }  # this peer already has it
      $lk = $pk + '|' + [string]$e.rel
      if ($st.lastTry.ContainsKey($lk) -and (($now - [long]$st.lastTry[$lk]) -lt 60)) { continue }  # 60s backoff
      $st.lastTry[$lk] = $now
      $pv = Get-PeerVers $peer
      $content = [IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
      # v1.2: a >200KB PLAIN body into a pre-1.9 peer jams ITS accept loop (each
      # attempt blocks its single-threaded read up to the 8s socket timeout,
      # back-to-back retries starve its /health). Skip and let the 10-min git
      # plane carry the delta until the peer upgrades (O-20261016-1745 heal).
      $gzOk = $false
      try { if ($pv -ne '' -and ([version]$pv -ge [version]'1.9')) { $gzOk = $true } } catch { }
      if (-not $gzOk -and $content.Length -gt 200000) {
        PS-Log 'sync-push-skip' ([string]$e.rel + ' -> ' + $pk + ' legacy-or-unverified-peer oversize ' + $content.Length + 'B (git carries)')
        $dirty = $true
        Touch-Lock
        Touch-Hb
        continue
      }
      $r = Push-SyncOne ([string]$e.rel) ([string]$e.kind) $content $peer $pv
      if ($r.ok) { $st.pushed[$pk][[string]$e.rel] = $h }
      $dirty = $true
      # v1.1: a single push attempt can run ~30-50s over a degraded relay - touch
      # lock+heartbeat after EVERY attempt so the listener's staleness check
      # (90s) never misreads a busy pusher as dead and spawns a duplicate.
      Touch-Lock
      Touch-Hb
    }
  }
  if ($dirty) { Save-PushState $st }
}

# ---- v1.1: ownership convergence - if another pusher holds a FRESH lock, this
# one is the redundant duplicate -> exit so exactly one pusher survives. ----
function Test-StillOwner() {
  try {
    if (Test-Path $LockF) {
      $olk = Get-Content -Raw $LockF | ConvertFrom-Json
      $opid = 0
      try { $opid = [int]$olk.pid } catch { }
      $oage = 999
      try { $oage = ((Get-Date) - (Get-Item $LockF).LastWriteTime).TotalSeconds } catch { }
      if ($opid -gt 0 -and $opid -ne $PID -and $oage -lt 60 -and (Get-Process -Id $opid -ErrorAction SilentlyContinue)) { return $false }
    }
  } catch { }
  return $true
}

# ---- version self-check: newer pusher shipped via git -> exit, listener respawns ----
function Check-MyVersion() {
  try {
    $m = [regex]::Match([IO.File]::ReadAllText($PSCommandPath), "\`$Vers\s*=\s*'([0-9.]+)'")
    if ($m.Success -and $m.Groups[1].Value -ne $Vers) { PS-Log 'self-refresh' ($Vers + ' -> ' + $m.Groups[1].Value); exit 0 }
  } catch { }
}

PS-Log 'pusher-start' ('node=' + $NodeId + ' peers=' + $peers.Count + ' v=' + $Vers)
Touch-Lock
Touch-Hb
$iter = 0
while ($true) {
  $iter++
  if (-not (Test-StillOwner)) { PS-Log 'exit' 'another pusher owns the lock'; exit 0 }
  try { Poll-Publish } catch { PS-Log 'poll-error' ([string]$_.Exception.Message) }
  Touch-Lock
  Touch-Hb
  if (($iter % 30) -eq 0) { Check-MyVersion }
  Start-Sleep -Milliseconds 2000
}
