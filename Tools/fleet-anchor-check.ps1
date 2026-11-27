# fleet-anchor-check.ps1 - one-shot, self-contained anchor readiness report v1.0
# Paste-run on ANY fleet machine (Windows PowerShell). Read-only. No repo needed.
# It prints a report, saves it to Desktop\fleet-anchor-report.txt and copies it
# to the clipboard so it can be pasted back to the coordinator.
# ASCII-only body; PS 5.1 safe.
$ErrorActionPreference = 'Continue'

$L = @()
$r = @{}
$L += '=== FLEET ANCHOR REPORT ==='
$L += 'host=' + $env:COMPUTERNAME + ' user=' + $env:USERNAME + ' when=' + (Get-Date -Format s)

$ts = @('C:\Program Files\Tailscale\tailscale.exe', 'C:\Program Files (x86)\Tailscale\tailscale.exe') |
  Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$L += 'ts_exe=' + $ts

if ($ts) {
  $ver = (& $ts version 2>&1 | Select-Object -First 1)
  $L += 'ts_version=' + [string]$ver
  $svc = Get-Service Tailscale -ErrorAction SilentlyContinue
  $sv = 'missing'; if ($svc) { $sv = [string]$svc.Status }
  $L += 'ts_service=' + $sv

  $nc = (& $ts netcheck 2>&1 | Out-String)
  foreach ($k in @('UDP', 'IPv4', 'IPv6', 'MappingVariesByDestIP', 'PortMapping', 'Nearest DERP')) {
    $val = ''
    foreach ($ln in ($nc -split "`r?`n")) {
      if ($ln -match ('\*\s*' + [regex]::Escape($k) + ':\s*(.*)$')) { $val = $Matches[1].Trim(); break }
    }
    $r[$k] = $val
    $L += $k + '=' + $val
  }
  $d = @()
  foreach ($m in [regex]::Matches($nc, '-\s*(\w+):\s*([\d.]+)ms')) { $d += ($m.Groups[1].Value + '=' + $m.Groups[2].Value + 'ms') }
  if ($d.Count -gt 0) { $n = [Math]::Min(4, $d.Count - 1); $L += 'derp=' + ($d[0..$n] -join ', ') }

  $pref = $null
  try { $pref = (& $ts debug prefs 2>$null | Out-String | ConvertFrom-Json) } catch { }
  if ($pref) {
    $L += 'prefs route_all=' + $pref.RouteAll + ' exit_node=' + [string]$pref.ExitNodeIP + ' corp_dns=' + $pref.CorpDNS + ' run_ssh=' + $pref.RunSSH
  }

  $st = $null
  try { $st = (& $ts status --json 2>$null | Out-String | ConvertFrom-Json) } catch { }
  if ($st) {
    $selfIp = (@($st.Self.TailscaleIPs) | Where-Object { $_ -notmatch ':' }) -join ','
    $selfDns = ([string]$st.Self.DNSName).TrimEnd('.')
    $L += 'self=' + $st.Self.HostName + ' dns=' + $selfDns + ' ip=' + $selfIp
    foreach ($pp in $st.Peer.PSObject.Properties) {
      $p = $pp.Value
      if (-not $p.Online) { continue }
      $pdns = ([string]$p.DNSName).TrimEnd('.')
      if ($pdns -eq '') { $pdns = [string]$p.HostName }
      $ppath = 'relay:' + [string]$p.Relay
      if ($p.CurAddr) { $ppath = 'direct' }
      $L += 'peer=' + $pdns + ' path=' + $ppath
    }
  }
}

$cfg = Get-NetIPConfiguration -ErrorAction SilentlyContinue |
  Where-Object { $_.NetAdapter.Status -eq 'Up' -and $_.InterfaceAlias -notlike '*Tailscale*' } |
  Select-Object -First 1
if ($cfg) {
  $L += 'lan_ip=' + ((@($cfg.IPv4Address.IPAddress)) -join ',') + ' gw=' + ((@($cfg.IPv4DefaultGateway.NextHop)) -join ',')
  $gw = @($cfg.IPv4DefaultGateway.NextHop) | Select-Object -First 1
  if ($gw) {
    $nb = Get-NetNeighbor -IPAddress $gw -ErrorAction SilentlyContinue
    if ($nb) { $L += 'gw_mac=' + [string]$nb.LinkLayerAddress }
  }
}

$ads = @(Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Up' })
foreach ($a in $ads) { $L += 'adapter=' + $a.Name + ' | ' + $a.InterfaceDescription }
$vpn = @($ads | Where-Object {
    $txt = [string]$_.Name + ' ' + [string]$_.InterfaceDescription
    if ($txt -match 'Tailscale') { return $false }
    return ($txt -match 'TAP-Windows|WireGuard|OpenVPN|Clash|V2Ray|Xray|sing-box|Surge|Shadow|Netch|Proxifier|ZeroTier|Hamachi|VPN')
  } | ForEach-Object { $_.Name })
$L += 'vpn_adapters=' + ($vpn -join '; ')

$v6 = @(Get-NetIPAddress -AddressFamily IPv6 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -notmatch '^(fe80|fd|::1)' -and $_.InterfaceAlias -notlike '*Loopback*' } |
  ForEach-Object { $_.InterfaceAlias + ':' + $_.IPAddress })
$r['v6_global'] = ($v6 -join '; ')
$L += 'ipv6_global=' + $r['v6_global']

$eg = $null
try { $eg = Invoke-RestMethod -Uri 'https://ipinfo.io/json' -TimeoutSec 8 } catch { }
if ($eg) {
  $r['country'] = [string]$eg.country
  $L += 'egress=' + $eg.ip + ' ' + $eg.country + ' ' + $eg.city + ' ' + $eg.org
} else {
  $L += 'egress=ERR'
}

$L += 'trace_to_ct_dns:'
$tr = (tracert -d -h 5 -w 800 114.114.114.114) 2>&1 | Select-Object -First 9
foreach ($x in $tr) { $L += '  ' + [string]$x }

$fw = @(Get-NetFirewallRule -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName -like 'Tailscale*' } |
  ForEach-Object { $_.DisplayName + '(' + $_.Direction + '/' + $_.Action + '/' + $_.Profile + ')' })
$L += 'fw=' + ($fw -join ', ')

$li = @(Get-NetTCPConnection -State Listen -LocalPort 8790 -ErrorAction SilentlyContinue)
$L += 'listen8790=' + ($li.Count -gt 0)

$L += 'ram_gb=' + [Math]::Round((Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue).TotalPhysicalMemory / 1GB, 0)
$dsk = Get-PSDrive -Name ($env:SystemDrive.Substring(0, 1)) -ErrorAction SilentlyContinue
if ($dsk) { $L += 'disk_free_gb=' + [Math]::Round($dsk.Free / 1GB, 0) }
$g = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue |
  ForEach-Object { $_.Name } |
  Where-Object { $_ -notmatch 'Virtual|GameViewer|Remote|Basic' })
$L += 'gpu=' + ($g -join '; ')

$pm = ''; if ($r.ContainsKey('PortMapping')) { $pm = $r['PortMapping'] }
$hint = 'unknown'
if ($pm -ne '') { $hint = 'STRONG: port mapping present (UPnP/PMP/PCP)' }
elseif ($r['IPv6'] -match '^yes') { $hint = 'IPV6-ONLY: works with IPv6 peers only' }
elseif ($r['MappingVariesByDestIP'] -eq 'false') { $hint = 'MEDIUM: cone NAT, hole punching possible' }
elseif ($r['MappingVariesByDestIP'] -eq 'true') { $hint = 'WEAK: symmetric NAT, need port forward or public IPv4' }
$L += '--- VERDICT ---'
$L += 'anchor_hint=' + $hint
$L += 'vpn_suspected=' + ($vpn.Count -gt 0) + ' egress_cn=' + ($r['country'] -eq 'CN')
$L += '=== END ==='

$out = $L -join "`r`n"
$desk = [Environment]::GetFolderPath('Desktop')
$file = Join-Path $desk 'fleet-anchor-report.txt'
try { [IO.File]::WriteAllText($file, $out, (New-Object Text.UTF8Encoding($false))) } catch { }
try { Set-Clipboard -Value $out } catch { }
$out
''
'SAVED: ' + $file
'COPIED TO CLIPBOARD - paste it back to the coordinator.'
