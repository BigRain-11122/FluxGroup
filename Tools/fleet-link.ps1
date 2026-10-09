# fleet-link.ps1 - FleetLink node listener v1.1 (CEO order 2026-10-04:
# decision/dispatch chain + fleet networking - "git feels slow"; full autonomous
# authorization granted; v1.1 = O-20261009-1750 "very fast sync" upgrade).
# Implements state-plane v2 of O-20260928-1855 item 3: 10s-level status read +
# remote ignition/pull channel.
# Law anchors:
#   server-governance v2 - necessity gated by O-1855(3); minimal attack surface:
#     binds tailnet IP + loopback ONLY, allowlisted actions, NO arbitrary exec.
#   silent-run law - scheduled task wraps this via Tools\InvisibleRunner.vbs with
#     5-min keepalive; single instance = port occupancy, BUT v1.1 self-upgrade:
#     a newer script version kills the older listener instance and takes the port.
#   transport clause unchanged - /poke carries SIGNALS ONLY; data stays in git.
#   encoding law - ASCII-only body; roster JSON is ASCII.
# Endpoints:
#   GET  /health  liveness (ok, node, version, ts)
#   GET  /status  live node status (ram/disk/cpu/gpu + heartbeat files + repo_heads
#                 + last_pull stamp), no git wait
#   POST /poke    body {"reason":str,"tasks":[allowlisted names]} - acks FIRST,
#                 then spawns hidden Tools\fleet-poke-worker.ps1 (pull --ff-only +
#                 wake allowlisted tasks). Worker is lock-serialized so pokes
#                 NEVER block the accept loop (v1.0 inline pull blocked /health
#                 for the whole pull = the "timeout while busy" root cause).
param(
  [string]$Root = "C:\Users\sjs20\Desktop\FluxGroup",
  [int]$Port = 8790,
  [string]$NodeId = ""
)

$ErrorActionPreference = 'Continue'
$Dir = Join-Path $env:USERPROFILE '.codely-cli\fleet-link'
if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
$LogF = Join-Path $Dir 'log.jsonl'
$StateF = Join-Path $Dir 'state.json'

function FL-Log([string]$evt, [string]$detail) {
  try {
    $o = [ordered]@{ ts = (Get-Date -Format s); event = $evt; detail = $detail }
    ($o | ConvertTo-Json -Compress) | Add-Content -LiteralPath $LogF -Encoding UTF8
    if ((Get-Item $LogF -ErrorAction SilentlyContinue).Length -gt 100KB) {
      $keep = @((Get-Content -LiteralPath $LogF -Encoding UTF8 | Where-Object { $_ -match '\S' }) | Select-Object -Last 200)
      [IO.File]::WriteAllLines($LogF, $keep, (New-Object System.Text.UTF8Encoding($false)))
    }
  } catch { }
}

# ---- load node roster (self-identify by hostname or explicit NodeId) ----
$node = $null
try {
  $cfgF = Join-Path $Root 'Tools\fleet-nodes.json'
  $cfg = Get-Content -Raw -Encoding UTF8 $cfgF | ConvertFrom-Json
  if ($cfg.PSObject.Properties.Name -contains 'port') { $Port = [int]$cfg.port }
  foreach ($n in @($cfg.nodes)) {
    if ($NodeId -ne '' -and [string]$n.id -eq $NodeId) { $node = $n; break }
    if ($NodeId -eq '' -and [string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $node = $n; $NodeId = [string]$n.id; break }
  }
} catch { FL-Log 'config-fail' ([string]$_.Exception.Message) }
if ($NodeId -eq '') { $NodeId = $env:COMPUTERNAME }

# ---- bind (node tailnet IP + loopback; skip missing) + v1.1 self-upgrade ----
$Vers = '1.2'
$bindIps = @()
if ($node -and [string]$node.tailnet_ip -ne '') { $bindIps += [string]$node.tailnet_ip }
$bindIps += '127.0.0.1'
function Try-Bind([string[]]$ips) {
  $ls = @()
  foreach ($ip in $ips) {
    try {
      $addr = [System.Net.IPAddress]::Parse($ip)
      $l = New-Object System.Net.Sockets.TcpListener($addr, $Port)
      $l.Start(8)
      $ls += $l
    } catch { FL-Log 'bind-fail' ($ip + ':' + $Port + ' ' + ([string]$_.Exception.Message)) }
  }
  return ,@($ls)
}
$listeners = Try-Bind $bindIps
if ($listeners.Count -eq 0) {
  # port taken: if the RUNNING instance is an older version, take over (self-upgrade)
  $runningVers = ''
  try { $runningVers = [string]((Get-Content -Raw $StateF | ConvertFrom-Json).version) } catch { }
  if ($runningVers -ne '' -and $runningVers -ne $Vers) {
    FL-Log 'self-upgrade' ('running=' + $runningVers + ' new=' + $Vers + ' - replacing old listener')
    try {
      $old = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'fleet-link\.ps1' -and $_.ProcessId -ne $PID }
      foreach ($o in @($old)) { try { Stop-Process -Id ([int]$o.ProcessId) -Force -ErrorAction SilentlyContinue } catch { } }
    } catch { }
    Start-Sleep -Milliseconds 1500
    for ($i = 0; $i -lt 10 -and $listeners.Count -eq 0; $i++) {
      Start-Sleep -Milliseconds 500
      $listeners = Try-Bind $bindIps
    }
  }
}
if ($listeners.Count -eq 0) { FL-Log 'exit' 'no bind (already running or port taken)'; exit 0 }

try {
  $st = [ordered]@{ node = $NodeId; host = $env:COMPUTERNAME; port = $Port
                    started = (Get-Date -Format s); version = $Vers; pid = $PID
                    bound = @($listeners | ForEach-Object { [string]$_.LocalEndpoint }) }
  [IO.File]::WriteAllText($StateF, ($st | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
} catch { }
FL-Log 'start' ('node=' + $NodeId + ' listeners=' + $listeners.Count + ' port=' + $Port + ' v=' + $Vers)

# ---- guards & helpers ----
function Test-ClientIp([string]$ip) {
  if ([string]::IsNullOrWhiteSpace($ip)) { return $false }
  if ($ip.StartsWith('127.')) { return $true }
  $p = $ip.Split('.')
  if ($p.Count -ne 4 -or $p[0] -ne '100') { return $false }
  $o2 = 0
  if (-not [int]::TryParse($p[1], [ref]$o2)) { return $false }
  return ($o2 -ge 64 -and $o2 -le 127)
}

function Send-Resp($client, [int]$code, [string]$reason, [string]$json) {
  try {
    $b = [System.Text.Encoding]::UTF8.GetBytes($json)
    $hdr = 'HTTP/1.1 ' + $code + ' ' + $reason + "`r`nContent-Type: application/json`r`nContent-Length: " + $b.Length + "`r`nConnection: close`r`n`r`n"
    $hb = [System.Text.Encoding]::ASCII.GetBytes($hdr)
    $ns = $client.GetStream()
    $ns.Write($hb, 0, $hb.Length)
    $ns.Write($b, 0, $b.Length)
    $ns.Flush()
  } catch { }
  try { $client.Close() } catch { }
}

function Read-Request($client) {
  try {
    $r = New-Object System.IO.StreamReader($client.GetStream(), [System.Text.Encoding]::UTF8)
    $first = $r.ReadLine()
    if (-not $first) { return $null }
    $parts = @($first.Trim() -split '\s+')
    if ($parts.Count -lt 2) { return $null }
    $path = $parts[1]
    $qi = $path.IndexOf('?')
    if ($qi -ge 0) { $path = $path.Substring(0, $qi) }
    $cl = 0
    while ($true) {
      $h = $r.ReadLine()
      if ($null -eq $h -or $h.Trim() -eq '') { break }
      if ($h -match '^Content-Length:\s*(\d+)') { $cl = [int]$Matches[1] }
    }
    $body = ''
    if ($cl -gt 0 -and $cl -lt 4096) {
      $buf = New-Object char[] $cl
      $n = $r.Read($buf, 0, $cl)
      if ($n -gt 0) { $body = -join $buf[0..($n - 1)] }
    }
    return @{ m = $parts[0]; path = $path; body = $body }
  } catch { return $null }
}

function Get-StatusJson() {
  $ramFree = -1.0; $diskFree = -1.0; $cpuLoad = -1; $gpu = ''
  try { $ramFree = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1) } catch { }
  try { $diskFree = [math]::Round((Get-PSDrive C).Free / 1GB, 1) } catch { }
  try {
    $avg = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
    if ($null -ne $avg) { $cpuLoad = [int]$avg }
  } catch { }
  try { $gpu = [string](& nvidia-smi --query-gpu=name,memory.free --format=csv,noheader 2>$null | Select-Object -First 1) } catch { }
  $hb = @()
  if ($node -and ($node.PSObject.Properties.Name -contains 'status_files')) {
    foreach ($rel in @($node.status_files)) {
      $p = Join-Path $Root ([string]$rel)
      if (Test-Path -LiteralPath $p) {
        try {
          $raw = Get-Content -Raw -Encoding UTF8 $p
          if ($raw.Length -gt 2000) { $raw = $raw.Substring(0, 2000) }
          $hb += @{ file = [string]$rel; content = $raw }
        } catch { }
      }
    }
  }
  $o = [ordered]@{ ok = $true; node = $NodeId; host = $env:COMPUTERNAME
                   ts = (Get-Date -Format s); ram_free_gb = $ramFree
                   disk_free_gb = $diskFree; cpu_load_pct = $cpuLoad; gpu = $gpu
                   heartbeats = $hb }
  # v1.1: repo HEADs (fast rev-parse, no network) + last worker stamp -> dispatcher verify
  $repoHeads = @{}
  try {
    if ($node -and ($node.PSObject.Properties.Name -contains 'repos')) {
      foreach ($rel in @($node.repos)) {
        $p = Join-Path $Root ([string]$rel)
        if (Test-Path (Join-Path $p '.git')) {
          $h = ''
          try { $h = [string](& git -C $p rev-parse HEAD) } catch { }
          if ($h) { $repoHeads[[string]$rel] = $h.Trim() }
        }
      }
    }
  } catch { }
  $o.repo_heads = $repoHeads
  try {
    $stampF = Join-Path $Dir ('last-pull-' + $NodeId + '.json')
    if (Test-Path $stampF) { $o.last_pull = (Get-Content -Raw $stampF | ConvertFrom-Json) }
  } catch { }
  return ($o | ConvertTo-Json -Depth 5 -Compress)
}

function Start-PokeWorker([string]$reason, [string[]]$reqTasks, [string[]]$reqRepos) {
  # v1.1: pull+wake runs in a HIDDEN background process - accept loop never blocks.
  # v1.2 (O-20261009-1755 tiers): forced repos ride along; worker allowlists them.
  $worker = Join-Path $Root 'Tools\fleet-poke-worker.ps1'
  if (-not (Test-Path $worker)) { FL-Log 'worker-missing' $worker; return }
  $tj = '[]'
  try { $tj = (@($reqTasks) | ConvertTo-Json -Compress) } catch { }
  if ($tj.Length -gt 900) { $tj = '[]' }
  $rj = '[]'
  try { $rj = (@($reqRepos) | ConvertTo-Json -Compress) } catch { }
  if ($rj.Length -gt 400) { $rj = '[]' }
  try {
    $argz = '-NoProfile -ExecutionPolicy Bypass -File "' + $worker + '" -Root "' + $Root + '" -NodeId ' + $NodeId + ' -Reason "' + $reason + '" -TasksJson "' + $tj + '" -PullReposJson "' + $rj + '"'
    Start-Process -FilePath 'powershell.exe' -ArgumentList $argz -WindowStyle Hidden | Out-Null
    FL-Log 'worker-spawn' ('reason=' + $reason + ' force-repos=' + $rj)
  } catch { FL-Log 'worker-spawn-fail' ([string]$_.Exception.Message) }
}

function Handle-Client($client) {
  $rip = ''
  try { $rip = $client.Client.RemoteEndPoint.Address.ToString() } catch { }
  if (-not (Test-ClientIp $rip)) { Send-Resp $client 403 'Forbidden' '{"ok":false,"err":"forbidden"}'; FL-Log 'deny' $rip; return }
  try { $client.ReceiveTimeout = 8000; $client.SendTimeout = 8000 } catch { }
  $req = Read-Request $client
  if (-not $req) { Send-Resp $client 400 'Bad Request' '{"ok":false,"err":"bad-request"}'; return }
  $path = [string]$req.path
  if ($path -eq '/health') {
    $o = [ordered]@{ ok = $true; node = $NodeId; version = $Vers; ts = (Get-Date -Format s) }
    Send-Resp $client 200 'OK' ($o | ConvertTo-Json -Compress)
    return
  }
  if ($path -eq '/status') { Send-Resp $client 200 'OK' (Get-StatusJson); return }
  if ($path -eq '/poke') {
    if ([string]$req.m -ne 'POST') { Send-Resp $client 405 'Method Not Allowed' '{"ok":false,"err":"post-only"}'; return }
    $reason = 'poke'; $tasks = @(); $repos = @()
    try {
      $b = ([string]$req.body) | ConvertFrom-Json
      if ($b.PSObject.Properties.Name -contains 'reason') { $reason = [string]$b.reason }
      if ($b.PSObject.Properties.Name -contains 'tasks') { $tasks = @($b.tasks) | ForEach-Object { [string]$_ } | Select-Object -First 10 }
      if ($b.PSObject.Properties.Name -contains 'repos') { $repos = @($b.repos) | ForEach-Object { [string]$_ } | Select-Object -First 8 }
    } catch { }
    $o = [ordered]@{ ok = $true; accepted = $true; node = $NodeId; version = $Vers; ts = (Get-Date -Format s) }
    Send-Resp $client 200 'OK' ($o | ConvertTo-Json -Compress)
    Start-PokeWorker $reason $tasks $repos
    return
  }
  Send-Resp $client 404 'Not Found' '{"ok":false,"err":"unknown-endpoint"}'
}

# ---- accept loop ----
$tick = 0
while ($true) {
  $handled = $false
  foreach ($l in $listeners) {
    if ($l.Pending()) {
      $c = $l.AcceptTcpClient()
      $handled = $true
      try { Handle-Client $c } catch { FL-Log 'handle-error' ([string]$_.Exception.Message); try { $c.Close() } catch { } }
    }
  }
  $tick++
  if (($tick % 480) -eq 0) { try { (Get-Item $StateF).LastWriteTime = Get-Date } catch { } }
  if (-not $handled) { Start-Sleep -Milliseconds 250 }
}
