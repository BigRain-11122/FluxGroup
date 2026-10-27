# nats-heartbeat.ps1 - fleet live-state heartbeat (task FluxGroup-NatsHB, PT1M).
# Publishes machine state to NATS KV FLEET_STATE (key state.<node>, bucket TTL 10m:
# a key alive = machine heartbeating within TTL; a dead/paused-offline node's key
# expires by itself = liveness semantics without any manual freshness probe) and
# to event subject hb.<node>. Hub role (server on 127.0.0.1) self-heals the bus
# task when the server is down; client nodes only log hub-unreachable.
# Canon: R-20261019-fleet-realtime-comm-01 (CEO order 2026-10-19 realtime fleet comm).
param(
  [string]$Root = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
  [string]$NodeId = '',
  [string]$Server = 'nats://127.0.0.1:4222'
)
$ErrorActionPreference = 'Continue'
$nats = Join-Path $Root 'Tools\nats\bin\nats.exe'
if (-not (Test-Path $nats)) { exit 1 }
$dataDir = Join-Path $Root 'Tools\nats\data'
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$evtF = Join-Path $dataDir 'bus-events.log'
function HB-Log([string]$evt, [string]$detail) {
  try { $o = [ordered]@{ ts = (Get-Date -Format s); event = $evt; detail = $detail }; ($o | ConvertTo-Json -Compress) | Add-Content -LiteralPath $evtF -Encoding UTF8 } catch { }
}
if ($NodeId -eq '') {
  try {
    $cfg = Get-Content -Raw -Encoding UTF8 (Join-Path $Root 'Tools\fleet-nodes.json') | ConvertFrom-Json
    foreach ($n in @($cfg.nodes)) { if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $NodeId = [string]$n.id; break } }
  } catch { }
  if ($NodeId -eq '') { $NodeId = $env:COMPUTERNAME }
}
$alive = $false
try { $null = & $nats -s $Server kv ls 2>&1; if ($LASTEXITCODE -eq 0) { $alive = $true } } catch { }
if (-not $alive -and ($Server -match '127\.0\.0\.1')) {
  try { Start-ScheduledTask -TaskName 'FluxGroup-NatsBus' } catch { }
  Start-Sleep -Seconds 3
  try { $null = & $nats -s $Server kv ls 2>&1; if ($LASTEXITCODE -eq 0) { $alive = $true } } catch { }
  HB-Log 'hb-hub-revive' ('node=' + $NodeId + ' alive=' + $alive)
}
if (-not $alive) { HB-Log 'hb-server-unreachable' ('node=' + $NodeId + ' server=' + $Server); exit 1 }
try { & $nats -s $Server kv add FLEET_STATE --ttl 10m | Out-Null } catch { }
try { & $nats -s $Server kv add FLEET_ORDERS | Out-Null } catch { }
$ramFree = $null; try { $ramFree = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB, 1) } catch { }
$cpu = $null; try { $cpu = [int](Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average } catch { }
$diskFree = $null
try {
  $q = (Split-Path $Root -Qualifier); $q = $q.TrimEnd(':')
  $drv = Get-PSDrive -Name $q -ErrorAction SilentlyContinue
  if ($drv) { $diskFree = [math]::Round($drv.Free/1GB, 1) }
} catch { }
# --- millisecond timestamp + sequence + hub clock offset (2026-10-27 alignment fix) ---
$seqF = Join-Path $dataDir ('seq.' + $NodeId + '.txt')
$seq = 0
if (Test-Path $seqF) { try { $seq = [int](Get-Content $seqF -Raw) } catch { } }
$seq = $seq + 1
Set-Content -Path $seqF -Value $seq -Encoding UTF8
$probe = Join-Path $Root 'Tools\nats\clock-probe-nats.ps1'
$offMs = $null; $rttMs = $null
try {
  & $probe -Hub '100.110.185.62' -Port 4222 -OutFile (Join-Path $dataDir 'clock-offset.json') | Out-Null
  $cj = Get-Content -Raw -Encoding UTF8 (Join-Path $dataDir 'clock-offset.json') | ConvertFrom-Json
  if ($cj.ok) { $offMs = $cj.offset_ms; $rttMs = $cj.precision_ms }
} catch { }
$goodF = Join-Path $dataDir 'clock-offset-good.json'
$offAgeS = 0
# Precision gate: a relayed path can return +/-400ms precision and point estimates that
# scatter by the same magnitude (measured here: +16 / +204 / -114ms). Publishing such a
# number as "the offset" is worse than publishing nothing, because the dispatcher's
# skew gate (2*precision+20) never trips and a consumer would "correct" by noise.
$offTrusted = ($null -ne $offMs -and $null -ne $rttMs -and [double]$rttMs -le 150)
if ($offTrusted) {
  try {
    [ordered]@{ ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fff'); offset_ms = $offMs;
                precision_ms = $rttMs } |
      ConvertTo-Json -Compress | Set-Content -LiteralPath $goodF -Encoding UTF8
  } catch { }
} else {
  # Transient probe failure OR an imprecise path: carry the last trusted reading and
  # disclose its age. A null offset would instead be read as the OLD schema by the
  # clock report, which re-flags a healthy v2 node as CLOCK-UNALIGNED forever.
  try {
    $prev = Get-Content -Raw -Encoding UTF8 $goodF -ErrorAction SilentlyContinue | ConvertFrom-Json
    if ($prev.offset_ms -ne $null) {
      $offMs = $prev.offset_ms
      $rttMs = $prev.precision_ms
      try { $offAgeS = [int]((Get-Date) - [datetime]$prev.ts).TotalSeconds } catch { $offAgeS = -1 }
      HB-Log 'hb-clock-carryforward' ('node=' + $NodeId + ' offset=' + $offMs + ' age_s=' + $offAgeS)
    }
  } catch { }
  # No trusted reading has ever landed on this path: publish the fresh measurement and
  # let clock_offset_trusted=false carry the caveat. A null here would be read as "old
  # schema" and would flag a genuinely-v2 node as unaligned - the defect this round fixed.
  if ($null -eq $offMs) { HB-Log 'hb-clock-imprecise' ('node=' + $NodeId + ' precision_ms=' + $rttMs) }
}
$gpuUtil = $null; $vramUsed = $null; $vramTotal = $null
try {
  $g = [string](& nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>$null | Select-Object -First 1)
  if ($g) { $p = $g -split ','; $gpuUtil = [int]$p[0].Trim(); $vramUsed = [int]$p[1].Trim(); $vramTotal = [int]$p[2].Trim() }
} catch { }
$state = [ordered]@{
  node = $NodeId
  host = $env:COMPUTERNAME
  ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fff')
  ts_utc_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  seq = $seq
  clock_offset_ms = $offMs
  clock_rtt_ms = $rttMs
  clock_offset_age_s = $offAgeS
  clock_offset_trusted = $offTrusted
  ram_free_gb = $ramFree
  cpu_load_pct = $cpu
  disk_free_gb = $diskFree
  gpu_util_pct = $gpuUtil
  vram_used_mb = $vramUsed
  vram_total_mb = $vramTotal
}
$json = ($state | ConvertTo-Json -Compress)
# PS5.1 native-argv quoting bug (10-19 live evidence): bare double quotes in the
# JSON are eaten by the child's CommandLineToArgvW - the KV value landed quote-less
# ({node:bm-a,...}) and broke every JSON consumer. Escape quotes as \" so the
# child receives them literally.
$jsonEsc = $json -replace '"', '\"'
& $nats -s $Server kv put FLEET_STATE ("state." + $NodeId) $jsonEsc | Out-Null
if ($LASTEXITCODE -ne 0) { HB-Log 'hb-kvput-fail' ('node=' + $NodeId + ' rc=' + $LASTEXITCODE); exit 1 }
& $nats -s $Server pub ("hb." + $NodeId) $jsonEsc | Out-Null
exit 0
