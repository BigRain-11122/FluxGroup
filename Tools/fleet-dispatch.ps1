# fleet-dispatch.ps1 - FleetLink dispatcher v1.1 (CEO order 2026-10-04; v1.1 = O-20261009-1750 "very fast sync").
# Pokes all enabled tailnet nodes so they pull immediately + wake allowlisted
# tasks (seconds-level dispatch instead of waiting for the next 10-min tick).
# v1.1 upgrades:
#   - timeout 8s -> 25s default (-TimeoutSec), retry x2 with 3s backoff
#     (busy nodes under GPU/render load answer slowly but DO answer)
#   - -ExpectSha verification loop: after an accepted poke, polls the node's
#     /status repo_heads until the total repo HEAD matches the sha we pushed ->
#     reports SYNCED <elapsed>s / PENDING (machine-verifiable fast sync)
#   - per-node sync state written to dispatch-log.jsonl (watchdog consumable)
# Called by: interactive sessions after pushing orders/decisions, night rounds,
# and the OrderSentinel hook (new P0/P1/T0/T1 ledger rows -> fleet-wide poke).
# Signals only - git stays the sole data channel (transport clause unchanged).
# Fail-soft: unreachable nodes are logged, never block the caller. Exit 0 always.
param(
  [string]$Root = "C:\Users\sjs20\Desktop\FluxGroup",
  [string]$Reason = "manual",
  [string[]]$Tasks = @(),
  [int]$TimeoutSec = 25,
  [string]$ExpectSha = "",
  [int]$VerifyWaitSec = 60,
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
if ($ExpectSha -eq '') { try { $ExpectSha = [string](& 'C:\Program Files\Git\cmd\git.exe' -C $Root rev-parse HEAD) } catch { } }

function Poke-Node([string]$ip) {
  $body = @{ reason = $Reason; tasks = @($Tasks) } | ConvertTo-Json -Compress
  $r = Invoke-RestMethod -Uri ('http://' + $ip + ':' + $port + '/poke') -Method Post -Body $body -ContentType 'application/json' -TimeoutSec $TimeoutSec
  if ($r.ok) { return 'ok' }
  return 'err'
}
function Get-NodeHead([string]$ip) {
  $s = Invoke-RestMethod -Uri ('http://' + $ip + ':' + $port + '/status') -Method Get -TimeoutSec 15
  if ($s.PSObject.Properties.Name -contains 'repo_heads') { return [string]$s.repo_heads['.'] }
  return ''
}

$results = @()
foreach ($n in @($cfg.nodes)) {
  if ([bool]$n.enabled -ne $true) { continue }
  $ip = [string]$n.tailnet_ip
  if ($ip -eq '') { continue }
  if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $ip = '127.0.0.1' }
  $ok = $false; $detail = ''; $sync = ''; $elapsed = -1
  for ($attempt = 1; $attempt -le 3 -and -not $ok; $attempt++) {
    try {
      $r = Poke-Node $ip
      if ($r -eq 'ok') { $ok = $true; $detail = 'accepted' }
      else { $detail = 'err-resp' }
    } catch {
      $detail = [string]$_.Exception.Message
      if ($detail.Length -gt 80) { $detail = $detail.Substring(0, 80) }
      if ($attempt -lt 3) { Start-Sleep -Seconds 3 }
    }
  }
  if ($ok -and $ExpectSha -ne '') {
    $t0 = Get-Date
    $sync = 'VERIFY-SKIP'
    for ($i = 0; $i -lt ([int]($VerifyWaitSec / 5) + 1); $i++) {
      try {
        $h = Get-NodeHead $ip
        if ($h -eq '') { $sync = 'no-heads(old-listener)'; break }
        if ($h -eq $ExpectSha) { $elapsed = [int]((Get-Date) - $t0).TotalSeconds; $sync = 'SYNCED ' + $elapsed + 's'; break }
        $sync = 'PENDING head=' + $h.Substring(0, [Math]::Min(8, $h.Length))
      } catch { $sync = 'verify-err ' + ([string]$_.Exception.Message).Substring(0, 40) }
      Start-Sleep -Seconds 5
    }
  }
  $results += @{ node = [string]$n.id; ok = $ok; detail = $detail; sync = $sync }
}
$okN = @($results | Where-Object { $_.ok }).Count
$line = 'DISPATCH reason=' + $Reason + ' nodes=' + $results.Count + ' ok=' + $okN + ' fail=' + ($results.Count - $okN) + ' sha=' + ($ExpectSha.Substring(0, [Math]::Min(8, $ExpectSha.Length)))
if (-not $Quiet) {
  Write-Output $line
  foreach ($r in $results) { Write-Output ('  ' + $r.node + ' ok=' + $r.ok + ' ' + $r.detail + ' ' + $r.sync) }
}
try {
  $Dir = Join-Path $env:USERPROFILE '.codely-cli\fleet-link'
  if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
  @{ ts = (Get-Date -Format s); reason = $Reason; line = $line; sha = $ExpectSha; nodes = $results } | ConvertTo-Json -Compress -Depth 4 | Add-Content -LiteralPath (Join-Path $Dir 'dispatch-log.jsonl') -Encoding UTF8
} catch { }
exit 0
