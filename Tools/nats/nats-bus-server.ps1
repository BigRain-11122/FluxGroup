# nats-bus-server.ps1 - NATS bus server carrier (task FluxGroup-NatsBus, every:5m self-heal).
# v2 (2026-10-19): runs nats-server.exe IN-PROCESS - the task instance IS the server
# lifetime (FleetLink-listener pattern). v1 spawned the server via Start-Process
# -PassThru; inside the VBS hidden chain that Start-Process call HUNG (12:08:08
# instance stuck Running for 3.5h -> every later start refused 0x800710E0 under
# default MultipleInstances=IgnoreNew). In-process removes Start-Process from the
# path entirely: crash -> script exits -> next 5-min tick restarts. Port occupancy
# still guards double-start (a second tick fails fast to bind and exits).
# Canon: R-20261019-fleet-realtime-comm-01 (CEO order 2026-10-19 realtime fleet comm).
param(
  [string]$Root = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
)
$ErrorActionPreference = 'Continue'
$data = Join-Path $Root 'Tools\nats\data'
New-Object -ItemType Directory -Force -Path $data -ErrorAction SilentlyContinue | Out-Null
if (-not (Test-Path $data)) { New-Item -ItemType Directory -Force -Path $data | Out-Null }
$srvExe = Join-Path $Root 'Tools\nats\bin\nats-server.exe'
$evtF = Join-Path $data 'bus-events.log'
function Bus-Log([string]$evt, [string]$detail) {
  try { $o = [ordered]@{ ts = (Get-Date -Format s); event = $evt; detail = $detail }; ($o | ConvertTo-Json -Compress) | Add-Content -LiteralPath $evtF -Encoding UTF8 } catch { }
}
function Port-Open([int]$port) {
  $c = New-Object System.Net.Sockets.TcpClient
  try { $r = $c.BeginConnect('127.0.0.1', $port, $null, $null); $ok = $r.AsyncWaitHandle.WaitOne(400); if ($ok -and $c.Connected) { return $true } } catch { } finally { try { $c.Close() } catch { } }
  return $false
}
if (-not (Test-Path $srvExe)) { Bus-Log 'server-exe-missing' $srvExe; exit 1 }
if (Port-Open 4222) { exit 0 }
Bus-Log 'server-start' 'port 4222 closed, starting nats-server (in-process)'
& $srvExe -p 4222 -js -n fleetbus -sd $data -l (Join-Path $data 'nats-server.log')
Bus-Log 'server-exited' ('code=' + $LASTEXITCODE)
exit $LASTEXITCODE
