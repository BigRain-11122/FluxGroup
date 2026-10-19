# fleet-live-status.ps1 - one-screen live fleet state from the NATS bus (KV FLEET_STATE).
# Face of the new bus: any session/agent runs this to see all machines' live
# state (ms-fresh from KV, TTL-expiry = dead node shows MISSING/STALE).
# Canon: R-20261019-fleet-realtime-comm-01 (CEO order 2026-10-19 realtime fleet comm).
param(
  [string]$Root = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
  [string]$Server = 'nats://127.0.0.1:4222'
)
$ErrorActionPreference = 'Continue'
$nats = Join-Path $Root 'Tools\nats\bin\nats.exe'
if (-not (Test-Path $nats)) { Write-Output 'nats.exe missing - run Tools\nats\bootstrap-nats.ps1'; exit 1 }
$cfg = $null
try { $cfg = Get-Content -Raw -Encoding UTF8 (Join-Path $Root 'Tools\fleet-nodes.json') | ConvertFrom-Json } catch { }
if (-not $cfg) { Write-Output 'fleet-nodes.json unreadable'; exit 1 }
Write-Output ('FLEET LIVE STATE @ ' + (Get-Date -Format s) + '  (source: NATS KV FLEET_STATE, TTL 10m)')
foreach ($n in @($cfg.nodes)) {
  $id = [string]$n.id
  $out = ''
  try { $raw = & $nats -s $Server kv get FLEET_STATE ("state." + $id) 2>$null; $out = [string](@($raw) | Where-Object { $_ -match '^\{' } | Select-Object -First 1) } catch { }
  if ($out) {
    try {
      $s = $out | ConvertFrom-Json
      $age = [math]::Round(((Get-Date) - ([datetime]$s.ts)).TotalSeconds, 0)
      Write-Output ('{0,-6} ts={1} age={2,5}s ram_free={3}GB cpu={4}% disk_free={5}GB host={6}' -f $s.node, $s.ts, $age, $s.ram_free_gb, $s.cpu_load_pct, $s.disk_free_gb, $s.host)
    } catch { Write-Output ('{0,-6} KV-PARSE-FAIL RAW: {1}' -f $id, $out) }
  } else {
    Write-Output ('{0,-6} MISSING/STALE (no KV heartbeat within TTL or node not on bus yet)' -f $id)
  }
}
exit 0
