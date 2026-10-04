# fleet-dispatch.ps1 - FleetLink dispatcher v1.0 (CEO order 2026-10-04).
# Pokes all enabled tailnet nodes so they pull immediately + wake allowlisted
# tasks (seconds-level dispatch instead of waiting for the next 10-min tick).
# Called by: interactive sessions after pushing orders/decisions, night rounds,
# and the OrderSentinel hook (new P0/P1/T0/T1 ledger rows -> fleet-wide poke).
# Signals only - git stays the sole data channel (transport clause unchanged).
# Fail-soft: unreachable nodes are logged, never block the caller. Exit 0 always.
param(
  [string]$Root = "C:\Users\sjs20\Desktop\FluxGroup",
  [string]$Reason = "manual",
  [string[]]$Tasks = @(),
  [switch]$Quiet
)
$ErrorActionPreference = 'Continue'
$cfgF = Join-Path $Root 'Tools\fleet-nodes.json'
try {
  $cfg = Get-Content -Raw -Encoding UTF8 $cfgF | ConvertFrom-Json
} catch {
  if (-not $Quiet) { Write-Output ('DISPATCH cfg-fail ' + ([string]$_.Exception.Message)) }
  exit 0
}
$port = 8790
if ($cfg.PSObject.Properties.Name -contains 'port') { $port = [int]$cfg.port }
$results = @()
foreach ($n in @($cfg.nodes)) {
  if ([bool]$n.enabled -ne $true) { continue }
  $ip = [string]$n.tailnet_ip
  if ($ip -eq '') { continue }
  # loopback for self (host match) - avoids tailnet self-routing surprises
  if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $ip = '127.0.0.1' }
  $ok = $false; $detail = ''
  try {
    $body = @{ reason = $Reason; tasks = @($Tasks) } | ConvertTo-Json -Compress
    $r = Invoke-RestMethod -Uri ('http://' + $ip + ':' + $port + '/poke') -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 8
    if ($r.ok) { $ok = $true; $detail = 'accepted' } else { $detail = 'err' }
  } catch {
    $detail = [string]$_.Exception.Message
    if ($detail.Length -gt 80) { $detail = $detail.Substring(0, 80) }
  }
  $results += @{ node = [string]$n.id; ok = $ok; detail = $detail }
}
$okN = @($results | Where-Object { $_.ok }).Count
$line = 'DISPATCH reason=' + $Reason + ' nodes=' + $results.Count + ' ok=' + $okN + ' fail=' + ($results.Count - $okN)
if (-not $Quiet) {
  Write-Output $line
  foreach ($r in $results) { Write-Output ('  ' + $r.node + ' ok=' + $r.ok + ' ' + $r.detail) }
}
try {
  $Dir = Join-Path $env:USERPROFILE '.codely-cli\fleet-link'
  if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
  @{ ts = (Get-Date -Format s); reason = $Reason; line = $line; nodes = $results } | ConvertTo-Json -Compress -Depth 4 | Add-Content -LiteralPath (Join-Path $Dir 'dispatch-log.jsonl') -Encoding UTF8
} catch { }
exit 0
