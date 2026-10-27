# register-nats-bus.ps1 - fleet bus task registration (thin wrapper on the canonical
# Tools\task-register.ps1; AI.md item 7 law: no raw Register-ScheduledTask/schtasks).
# Roles:
#   hub  (bm-a)  -> FluxGroup-NatsBus (server launcher, every:5m self-heal)
#                  + FluxGroup-NatsHB (heartbeat, every:1m, server=127.0.0.1)
#   node (others)-> FluxGroup-NatsHB only, publishing to <-Server> (bm-a hub IP).
# bm-a UAC note: unelevated S4U registration is denied on UAC boxes (10-16 live
# evidence); task-register.ps1 then falls back to InteractiveToken + hidden chain
# (zero flash while logged on) and queues the S4U conversion in
# Tools\task-s4u-backlog.md (any elevated window runs Tools\task-s4u-convert.ps1).
# Each task is fired once at registration (deploy=ignite) - a clean observed run
# is the deployment proof.
# Canon: R-20261019-fleet-realtime-comm-01 (CEO order 2026-10-19 realtime fleet comm).
param(
  [string]$Root = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
  [string]$NodeId = '',
  [string]$Role = 'hub',
  [string]$Server = 'nats://127.0.0.1:4222'
)
$ErrorActionPreference = 'Continue'
$tr = Join-Path $Root 'Tools\task-register.ps1'
if (-not (Test-Path $tr)) { Write-Output 'ERROR: Tools\task-register.ps1 missing'; exit 1 }
if ($NodeId -eq '') {
  try {
    $cfg = Get-Content -Raw -Encoding UTF8 (Join-Path $Root 'Tools\fleet-nodes.json') | ConvertFrom-Json
    foreach ($n in @($cfg.nodes)) { if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $NodeId = [string]$n.id; break } }
  } catch { }
  if ($NodeId -eq '') { $NodeId = $env:COMPUTERNAME }
}
$hbArg = '-Root "' + $Root + '" -NodeId ' + $NodeId + ' -Server "' + $Server + '"'
$jobs = @()
if ($Role -eq 'hub') {
  $jobs += @{ Name = 'FluxGroup-NatsBus'; Script = (Join-Path $Root 'Tools\nats\nats-bus-server.ps1'); Arg = ('-Root "' + $Root + '"'); Trigger = 'every:5m' }
}
$jobs += @{ Name = 'FluxGroup-NatsHB'; Script = (Join-Path $Root 'Tools\nats\nats-heartbeat.ps1'); Arg = $hbArg; Trigger = 'every:1m' }
$bad = 0
foreach ($j in $jobs) {
  if (Get-ScheduledTask -TaskName $j.Name -ErrorAction SilentlyContinue) { Write-Output ('SKIP ' + $j.Name + ' (already registered)'); continue }
  Write-Output ('== registering ' + $j.Name + ' trigger=' + $j.Trigger)
  $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tr -Name $j.Name -Script $j.Script -Trigger $j.Trigger -Arg $j.Arg -Description 'NATS fleet bus (R-20261019-fleet-realtime-comm-01)' 2>&1 | ForEach-Object { [string]$_ }
  $out | Write-Output
  if ($LASTEXITCODE -ne 0) { $bad++; Write-Output ('WARN: ' + $j.Name + ' registration/fire not clean (rc=' + $LASTEXITCODE + ')') }
}
Start-Sleep -Seconds 4
$natsExe = Join-Path $Root 'Tools\nats\bin\nats.exe'
if (Test-Path $natsExe) {
  try { $null = & $natsExe -s $Server kv ls 2>&1; if ($LASTEXITCODE -eq 0) { Write-Output ('BUS OK role=' + $Role + ' node=' + $NodeId + ' server=' + $Server) } else { Write-Output 'BUS PENDING (re-check in 1 min)' } } catch { Write-Output 'BUS PENDING (probe threw)' }
} else { Write-Output 'WARN: nats.exe missing - run Tools\nats\bootstrap-nats.ps1 first' }
if ($bad -gt 0) { exit 2 }
exit 0
