# fleet-anchor-bmc.ps1 - make this node the fleet network anchor (CEO order 2026-11-27).
# Idempotent, reversible, ASCII-only body (fleet encoding law).
#
# Roles: bm-c = anchor. Production lane (gpu-production) is NOT changed by this script.
#
#   -Status       show relay prefs, detected stable public IPv6, per-peer path
#   -Enable       turn on the peer relay listener (UDP <Port>) -- safe, local only
#   -Advertise    ALSO advertise the stable public IPv6 as a relay endpoint
#                 (only do this when inbound really works; see the flip test below)
#   -Unadvertise  stop advertising endpoints, keep the listener
#   -Disable      disable the relay server completely
#
# Reachability flip test (the only reliable proof):
#   bm-c advertises its endpoint -> if peers keep DIRECT paths, inbound works;
#   if peers drop from direct to relay, inbound is BLOCKED (router/firewall).
#   2026-11-27 measured: advertise -> bm-b fell from direct 11ms to relay sfo 308ms;
#   unadvertise -> direct 11ms came back. So bm-c inbound is currently blocked.
#
# After the router step (UDP 41641 -> 192.168.1.4, or IPv6 inbound allowed),
# re-run with -Advertise and confirm peers show direct.

param(
  [switch]$Status,
  [switch]$Enable,
  [switch]$Advertise,
  [switch]$Unadvertise,
  [switch]$Disable,
  [int]$Port = 41641
)

$ErrorActionPreference = 'Continue'

$Ts = @(
  'C:\Program Files\Tailscale\tailscale.exe',
  'C:\Program Files (x86)\Tailscale\tailscale.exe'
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Ts) { Write-Output 'FATAL tailscale.exe not found'; exit 1 }

function Get-StableV6 {
  # Stable (non-temporary) global address: SLAAC with SuffixOrigin=Link.
  # Temporary/privacy addresses use SuffixOrigin=Random and rotate hourly.
  $a = Get-NetIPAddress -AddressFamily IPv6 -ErrorAction SilentlyContinue |
    Where-Object {
      $_.PrefixOrigin -eq 'RouterAdvertisement' -and
      $_.SuffixOrigin -eq 'Link' -and
      $_.AddressState -eq 'Preferred' -and
      $_.IPAddress -notlike 'fe80*' -and
      $_.IPAddress -notlike 'fd*'
    } | Sort-Object { $_.ValidLifetime.TotalSeconds } -Descending | Select-Object -First 1
  if ($a) { return [string]$a.IPAddress }
  return ''
}

function Show-Status {
  $prefs = (& $Ts debug prefs 2>&1 | Out-String | ConvertFrom-Json)
  $self = (& $Ts status --json 2>&1 | Out-String | ConvertFrom-Json)
  $v6 = Get-StableV6
  Write-Output ('node=' + $self.Self.HostName + ' dns=' + $self.Self.DNSName)
  Write-Output ('relay_port=' + $prefs.RelayServerPort)
  Write-Output ('static_endpoints=' + (@($prefs.RelayServerStaticEndpoints) -join ','))
  Write-Output ('stable_v6=' + $(if ($v6) { $v6 } else { 'NONE' }))
  Write-Output 'peers:'
  $self.Peer.PSObject.Properties.Value | Sort-Object HostName | ForEach-Object {
    $path = if ($_.CurAddr) { 'direct ' + $_.CurAddr } else { 'relay ' + $_.Relay }
    Write-Output ('  ' + $_.HostName + ' online=' + $_.Online + ' ' + $path)
  }
  $advertising = (@($prefs.RelayServerStaticEndpoints) -join '').Trim().Length -gt 0
  if ($advertising) {
    $anyDirect = @($self.Peer.PSObject.Properties.Value | Where-Object { $_.Online -and $_.CurAddr }).Count -gt 0
    if ($anyDirect) { Write-Output 'VERDICT advertising + some peer direct -> inbound reachable' }
    else { Write-Output 'VERDICT advertising but NO peer direct -> inbound likely BLOCKED, run -Unadvertise' }
  } else {
    Write-Output 'VERDICT not advertising (listener only)'
  }
}

if ($Status -or (-not $Enable -and -not $Advertise -and -not $Unadvertise -and -not $Disable)) {
  Show-Status
  exit 0
}

if ($Disable) {
  & $Ts set --relay-server-port '' --relay-server-static-endpoints '' 2>&1 | Out-String
  Write-Output ('DISABLED rc=' + $LASTEXITCODE)
  exit 0
}

if ($Enable) {
  & $Ts set --relay-server-port $Port 2>&1 | Out-String
  Write-Output ('ENABLE port=' + $Port + ' rc=' + $LASTEXITCODE + ' (listener only, no endpoint advertised)')
}

if ($Unadvertise) {
  & $Ts set --relay-server-static-endpoints '' 2>&1 | Out-String
  Write-Output ('UNADVERTISE rc=' + $LASTEXITCODE)
}

if ($Advertise) {
  $v6 = Get-StableV6
  if (-not $v6) {
    Write-Output 'SKIP advertise: no stable public IPv6 (SuffixOrigin=Link) found'
  } else {
    $ep = '[' + $v6 + ']:' + $Port
    & $Ts set --relay-server-port $Port --relay-server-static-endpoints $ep 2>&1 | Out-String
    Write-Output ('ADVERTISE ' + $ep + ' rc=' + $LASTEXITCODE)
    Write-Output 'Now verify: run -Status after 60s. Peers staying direct = inbound OK;'
    Write-Output 'peers falling back to relay = inbound blocked, run -Unadvertise immediately.'
  }
}

Show-Status
