# fleet-net-doctor.ps1 - Per-node network verdict for the FluxGroup fleet v1.0
# Run this on EVERY machine. It is read-only: no settings are changed.
# Why (2026-11-27 audit): direct-vs-relay is decided by each node's NAT, IPv6,
# port mapping, VPN/TUN capture and DERP home. A single per-node report makes
# "what does this machine need" mechanical instead of guesswork.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-net-doctor.ps1
#   ... -Json           machine-readable
#   ... -NoProbe        skip peer 8790 TCP probes (faster)
#
# ASCII-only body (encoding law); PS 5.1 safe; no child consoles.
param(
  [switch]$Json,
  [switch]$NoProbe
)

$ErrorActionPreference = 'Continue'

$Ts = @("C:\Program Files\Tailscale\tailscale.exe", "C:\Program Files (x86)\Tailscale\tailscale.exe") |
  Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

function Get-NcField([string]$text, [string]$key) {
  foreach ($l in ($text -split "`r?`n")) {
    if ($l -match ('\*\s*' + [regex]::Escape($key) + ':\s*(.*)$')) { return $Matches[1].Trim() }
  }
  return ''
}

$r = [ordered]@{}
$r.host = $env:COMPUTERNAME
$r.when = (Get-Date -Format s)
$r.os = 'windows'

if (-not $Ts) {
  $r.error = 'tailscale.exe not found'
} else {
  $r.ts_version = [string]((& $Ts version 2>&1) | Select-Object -First 1)
  $svc = Get-Service Tailscale -ErrorAction SilentlyContinue
  $svcStatus = 'missing'
  if ($svc) { $svcStatus = [string]$svc.Status }
  $r.ts_service = $svcStatus

  $st = $null
  try { $st = (& $Ts status --json 2>$null | Out-String) | ConvertFrom-Json } catch { }
  if ($st) {
    $r.node = $st.Self.HostName
    $r.dns = ([string]$st.Self.DNSName).TrimEnd('.')
    $r.ip = (@($st.Self.TailscaleIPs) | Where-Object { $_ -notmatch ':' }) -join ','
    $r.magicdns = $st.MagicDNSSuffix
    $peers = @()
    foreach ($pp in $st.Peer.PSObject.Properties) {
      $p = $pp.Value
      $ppath = 'relay'
      if ($p.CurAddr) { $ppath = 'direct' }
      $pip = @($p.TailscaleIPs) | Where-Object { $_ -notmatch ':' } | Select-Object -First 1
      $pdns = ([string]$p.DNSName).TrimEnd('.')
      if ($pdns -eq '') { $pdns = [string]$p.HostName }
      $peers += [ordered]@{
        host = $p.HostName
        dns = $pdns
        ip = [string]$pip
        online = [bool]$p.Online
        path = $ppath
        relay = [string]$p.Relay
        addr = [string]$p.CurAddr
        os = [string]$p.OS
      }
    }
    $r.peers = $peers
  }

  $nc = (& $Ts netcheck 2>&1 | Out-String)
  $r.netcheck_raw = $nc.Trim()
  $r.udp = Get-NcField $nc 'UDP'
  $r.ipv4 = Get-NcField $nc 'IPv4'
  $r.ipv6 = Get-NcField $nc 'IPv6'
  $r.nat_symmetric = Get-NcField $nc 'MappingVariesByDestIP'
  $r.portmapping = Get-NcField $nc 'PortMapping'
  $r.derp_nearest = Get-NcField $nc 'Nearest DERP'
  $derp = @()
  foreach ($m in [regex]::Matches($nc, '-\s*(\w+):\s*([\d.]+)ms')) {
    $derp += [ordered]@{ code = $m.Groups[1].Value; ms = [double]$m.Groups[2].Value }
  }
  $r.derp = @($derp | Sort-Object { $_.ms } | Select-Object -First 5)

  $prefs = $null
  try { $prefs = (& $Ts debug prefs 2>$null | Out-String) | ConvertFrom-Json } catch { }
  if ($prefs) {
    $r.route_all = [bool]$prefs.RouteAll
    $r.exit_node = [string]$prefs.ExitNodeIP
    $r.corp_dns = [bool]$prefs.CorpDNS
    $r.run_ssh = [bool]$prefs.RunSSH
  }
}

$ipcfg = Get-NetIPConfiguration -ErrorAction SilentlyContinue | Where-Object { $_.NetAdapter.Status -eq 'Up' -and $_.InterfaceAlias -notlike '*Tailscale*' -and $_.InterfaceAlias -notlike '*vEthernet*' } | Select-Object -First 1
if ($ipcfg) {
  $r.lan_ip = @($ipcfg.IPv4Address.IPAddress) -join ','
  $r.gateway = @($ipcfg.IPv4DefaultGateway.NextHop) -join ','
  $gw = @($ipcfg.IPv4DefaultGateway.NextHop) | Select-Object -First 1
  if ($gw) {
    $nb = Get-NetNeighbor -IPAddress $gw -ErrorAction SilentlyContinue
    if ($nb) { $r.gateway_mac = [string]$nb.LinkLayerAddress }
  }
}

$r.egress = $null
try {
  $e = Invoke-RestMethod -Uri 'https://ipinfo.io/json' -TimeoutSec 6
  $r.egress = [ordered]@{ ip = [string]$e.ip; country = [string]$e.country; city = [string]$e.city; org = [string]$e.org }
} catch { }

$fw = @()
foreach ($rule in @(Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like 'Tailscale*' })) {
  $fw += [ordered]@{ name = [string]$rule.DisplayName; dir = [string]$rule.Direction; action = [string]$rule.Action; enabled = [bool]$rule.Enabled; profile = [string]$rule.Profile }
}
$r.firewall = $fw

$listen = @(Get-NetTCPConnection -State Listen -LocalPort 8790 -ErrorAction SilentlyContinue)
$r.fleetlink_listen = ($listen.Count -gt 0)
$r.fleetlink_bind = (@($listen | ForEach-Object { [string]$_.LocalAddress }) -join ',')

$probe = @()
if ((-not $NoProbe) -and $st) {
  foreach ($pp in @($r.peers)) {
    if (-not $pp.online) { continue }
    # use the IP captured with THIS peer row - host names are not unique (two bm-m)
    $ip = [string]$pp.ip
    if (-not $ip) { continue }
    $ok = $false
    try {
      $c = New-Object Net.Sockets.TcpClient
      $ar = $c.BeginConnect($ip, 8790, $null, $null)
      if ($ar.AsyncWaitHandle.WaitOne(1200)) { $c.EndConnect($ar); $ok = $true }
      $c.Close()
    } catch { }
    $probe += [ordered]@{ host = $pp.host; dns = $pp.dns; ip = $ip; port8790 = $ok }
  }
}
$r.peer_fleetlink = $probe

$r.ram_gb = [Math]::Round((Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue).TotalPhysicalMemory / 1GB, 0)
$d = Get-PSDrive -Name ($env:SystemDrive.Substring(0, 1)) -ErrorAction SilentlyContinue
if ($d) { $r.system_disk_free_gb = [Math]::Round($d.Free / 1GB, 0) }
$gpus = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | ForEach-Object { [string]$_.Name })
$realGpu = @($gpus | Where-Object { $_ -notmatch 'Virtual|GameViewer|Remote|Basic Display|Parsec|Sunshine' })
$gpuPick = ($gpus -join ', ')
if ($realGpu.Count -gt 0) { $gpuPick = ($realGpu -join '; ') }
$r.gpu = $gpuPick

# ---- verdicts ----
$v = @()
$directPeers = @($r.peers | Where-Object { $_.path -eq 'direct' })
$relayPeers = @($r.peers | Where-Object { $_.path -eq 'relay' })
if ($directPeers.Count -gt 0) { $v += ('direct_ok: ' + (($directPeers | ForEach-Object { $_.dns + '(' + $_.ip + ')' }) -join ',')) }
if ($relayPeers.Count -gt 0) { $v += ('relayed: ' + (($relayPeers | ForEach-Object { $_.dns + '(' + $_.ip + ')->' + $_.relay }) -join ',')) }

$canHost = $false
if ($r.ipv6 -match '^yes') { $canHost = $true }
if ($r.portmapping -ne '') { $canHost = $true }
if ($r.nat_symmetric -eq 'false' -and $r.udp -eq 'true') { $canHost = $true }
$ch = 'no'
if ($canHost) { $ch = 'yes' }
$v += 'can_host_direct: ' + $ch

if ($r.egress -and $r.egress.country -and $r.egress.country -ne 'CN') {
  $v += ('egress_outside_cn: ' + $r.egress.country + ' ' + $r.egress.org + ' -> if a VPN/TUN client runs here, exclude tailscaled from it')
}
if (-not $r.fleetlink_listen) { $v += 'fleetlink: local 8790 NOT listening -> run Tools/fleet-link.ps1 and check task FluxGroup-FleetLink' }
$down = @($r.peer_fleetlink | Where-Object { -not $_.port8790 })
if ($down.Count -gt 0) { $v += ('fleetlink_peer_down: ' + (($down | ForEach-Object { $_.dns + '(' + $_.ip + ')' }) -join ',') + ' -> restart fleet-link there') }
if ($r.ts_service -ne 'Running') { $v += ('tailscale_service: ' + $r.ts_service + ' -> start service / register S4U task') }
$r.verdict = $v

if ($Json) {
  $r | ConvertTo-Json -Depth 8
  return
}

'== ' + $r.host + ' =='
'when=' + $r.when + ' os=' + $r.os + ' ts=' + $r.ts_version + ' service=' + $r.ts_service
'node=' + $r.node + ' dns=' + $r.dns + ' ip=' + $r.ip + ' magicdns=' + $r.magicdns
foreach ($p in @($r.peers)) { ('peer {0,-24} {1,-6} {2,-7} relay={3}' -f ($p.dns + '(' + $p.ip + ')'), $p.online, $p.path, $p.relay) }
'netcheck: udp=' + $r.udp + ' ipv4=' + $r.ipv4 + ' ipv6=' + $r.ipv6
'nat: symmetric=' + $r.nat_symmetric + ' portmapping=[' + $r.portmapping + '] nearest_derp=' + $r.derp_nearest
foreach ($d in @($r.derp)) { ('derp {0} {1}ms' -f $d.code, $d.ms) }
if ($r.egress) { 'egress=' + $r.egress.ip + ' ' + $r.egress.country + ' ' + $r.egress.city + ' ' + $r.egress.org }
'lan=' + $r.lan_ip + ' gw=' + $r.gateway + ' gw_mac=' + $r.gateway_mac
'fw_rules=' + (@($r.firewall | ForEach-Object { $_.name + '(' + $_.action + '/' + $_.profile + ')' }) -join ',')
'prefs: route_all=' + $r.route_all + ' exit_node=' + $r.exit_node + ' corp_dns=' + $r.corp_dns + ' run_ssh=' + $r.run_ssh
'fleetlink: listen8790=' + $r.fleetlink_listen + ' bind=' + $r.fleetlink_bind
foreach ($p in @($r.peer_fleetlink)) { ('fleetlink {0} {1}:8790={2}' -f $p.host, $p.ip, $p.port8790) }
'cap: ram=' + $r.ram_gb + 'GB disk_free=' + $r.system_disk_free_gb + 'GB gpu=' + $r.gpu
'VERDICT:'
foreach ($line in @($r.verdict)) { '  - ' + $line }
