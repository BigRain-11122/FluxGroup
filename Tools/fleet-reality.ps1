# fleet-reality.ps1 - Fleet reality probe v1.0 (CEO order 2026-10-10 ~00:4x
# "好好梳理" -> O-20261010-0045; law anchor: governance 10.2 fresh-verification
# law, enforcement-strengthening file, T2, 7-day veto window).
# THE single source of truth for any report about FLEET / MACHINE / PHYSICAL-ITEM
# state. Roster notes (fleet-nodes.json "note") are HISTORY, not state - they are
# snapshots that rot; this probe is the live picture. Any window about to report
# machine status, offline/online claims, or "pending CEO physical items" MUST run
# this first and cite its output timestamp. No timestamp in the report = violation
# (fresh-verification law enforcement face).
# What it checks per roster node (read-only, fail-soft, ASCII output):
#   - tailnet membership (tailscale status) + UNROSTERED peer catch (new machines
#     joining the tailnet are visible immediately even before anyone edits roster)
#   - listener :8790 TCP + /health (version) + CLOCK SKEW (remote ts vs local now
#     - a fast/slow node clock corrupts heartbeat freshness and git timestamps)
#   - /status (ram/disk, last worker pull, repo head) vs local origin/main head
#   - heartbeat file age (LOCAL mtime - trusted over remote-written ts fields)
param([string]$Root = "C:\Users\sjs20\Desktop\FluxGroup")
$ErrorActionPreference = 'SilentlyContinue'
$now = Get-Date
$rosterF = Join-Path $Root 'Tools\fleet-nodes.json'
if (-not (Test-Path $rosterF)) { Write-Output 'REALITY FATAL: roster missing'; exit 0 }
$roster = Get-Content -Raw -Encoding UTF8 $rosterF | ConvertFrom-Json
$port = 8790
if ($roster.PSObject.Properties.Name -contains 'port') { $port = [int]$roster.port }

function Test-PortQ([string]$ip, [int]$p, [int]$ms = 1500) {
  $c = New-Object System.Net.Sockets.TcpClient
  try {
    $iar = $c.BeginConnect($ip, $p, $null, $null)
    if ($iar.AsyncWaitHandle.WaitOne($ms) -and $c.Connected) { return $true }
  } catch { } finally { try { $c.Close() } catch { } }
  return $false
}

# ---- tailnet peers (ip -> name) ----
$peers = @{}
$tsExe = 'C:\Program Files\Tailscale\tailscale.exe'
if (-not (Test-Path $tsExe)) { $tsExe = (Get-Command tailscale -ErrorAction SilentlyContinue).Source }
if ($tsExe) {
  foreach ($ln in @(& $tsExe status 2>$null)) {
    $p = @($ln -split '\s+')
    if ($p.Count -ge 2 -and $p[0] -match '^100\.') { $peers[$p[0]] = $p[1] }
  }
}

# ---- local origin/main head of the command-plane repo ----
$originHead = ''
try { $originHead = [string](& 'C:\Program Files\Git\cmd\git.exe' -C $Root rev-parse --short=8 origin/main) } catch { }

Write-Output ('REALITY probe ' + $now.ToString('s') + '  (cite THIS, not roster notes)')
Write-Output ('local ' + $env:COMPUTERNAME + ' origin/main=' + $originHead)

foreach ($n in @($roster.nodes)) {
  $id = [string]$n.id
  $ip = [string]$n.tailnet_ip
  $out = $id
  if ($ip -eq '') { $out += ' no-ip'; Write-Output $out; continue }
  # tailnet membership
  $seenName = ''
  if ($peers.ContainsKey($ip)) { $seenName = [string]$peers[$ip]; $out += ' tailnet=Y' }
  else { $out += ' tailnet=N' }
  # probe target (self -> loopback)
  $tip = $ip
  if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $tip = '127.0.0.1' }
  # tcp + health
  if (Test-PortQ $tip $port) {
    $out += ' :8790=Y'
    try {
      $h = Invoke-RestMethod -Uri ('http://' + $tip + ':' + $port + '/health') -Method Get -TimeoutSec 6
      $out += (' v' + [string]$h.version)
      $rts = [datetime]::Parse([string]$h.ts, [System.Globalization.CultureInfo]::InvariantCulture)
      $skew = [int]((($rts - $now).TotalMinutes))
      $out += (' skew=' + $skew + 'm')
      if ([math]::Abs($skew) -gt 15) { $out += ' [CLOCK-SKEW owner: w32tm /resync]' }
    } catch { $out += ' health=err' }
    # status: last pull + heads + heartbeat age
    try {
      $s = Invoke-RestMethod -Uri ('http://' + $tip + ':' + $port + '/status') -Method Get -TimeoutSec 8
      if ($s.PSObject.Properties.Name -contains 'last_pull') {
        $lp = $s.last_pull
        $pullTxt = ''
        if ($lp.pulls) { $pullTxt = [string]::Join(',', @($lp.pulls)) }
        $out += (' pull[' + [string]$lp.reason + ']=' + $pullTxt)
        $p9 = $lp.repo_heads.PSObject.Properties['.']
        if ($p9) {
          $sh = ([string]$p9.Value)
          $out += (' head=' + $sh.Substring(0, [Math]::Min(8, $sh.Length)))
          if ($originHead -ne '' -and $sh.Length -ge 8) {
            if ($sh.Substring(0, 8) -eq $originHead) { $out += '=origin' } else { $out += '=behind' }
          }
        }
      }
      if (@($n.status_files).Count -gt 0) {
        $hbp = Join-Path $Root ([string]@($n.status_files)[0])
        if (Test-Path $hbp) {
          $age = [int]((($now - (Get-Item $hbp).LastWriteTime).TotalMinutes))
          $out += (' hb_age=' + $age + 'm')
        } else { $out += ' hb=file-none' }
      }
    } catch { }
  } else { $out += ' :8790=N' }
  if ($seenName -ne '' -and $seenName -ne $id) { $out += (' ts-name=' + $seenName) }
  Write-Output $out
}

# ---- tailnet peers NOT in roster (new machines become visible here first) ----
$rosterIps = @()
foreach ($n in @($roster.nodes)) { $rosterIps += [string]$n.tailnet_ip }
foreach ($k in $peers.Keys) {
  if ($rosterIps -notcontains $k) { Write-Output ('UNROSTERED tailnet peer: ' + $k + ' ' + $peers[$k] + ' - adopt per fleet-nodes SOP') }
}
Write-Output ('END reality ' + (Get-Date -Format s) + ' - reports citing fleet state MUST carry this timestamp')
exit 0
