# fleet-board.ps1 - Fleet overview board generator (CEO order 2026-10-21 "fleet
# sync must be visible at a glance; 及时同步信息和指令").
# Produces a single self-contained HTML (fleet-board.html) + raw JSON
# (fleet-board.json) under the fleet/ dir. Run by hand / on demand; intentionally
# NOT registered as a scheduled task (CEO pause order 10-21: no new auto tasks).
# Reuses: Tools\fleet-nodes.json (roster), FleetLink /health + /status on 8790,
# orders.md tail (last order row), .codely-cli\fleet-liveness\alerts.jsonl and
# .codely-cli\fleet-link\dispatch-log.jsonl tails.
# ASCII-only body (encoding law). PS5.1 compatible.
#
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-board.ps1
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $PSScriptRoot
$cfgF = Join-Path $root 'Tools\fleet-nodes.json'
if (-not (Test-Path -LiteralPath $cfgF)) { Write-Output 'BOARD cfg-fail: fleet-nodes.json missing'; exit 0 }
try { $cfg = Get-Content -LiteralPath $cfgF -Raw -Encoding UTF8 | ConvertFrom-Json } catch { Write-Output ('BOARD cfg-fail ' + [string]$_.Exception.Message); exit 0 }

$port = 8790
if ($cfg.PSObject.Properties.Name -contains 'port') { $port = [int]$cfg.port }
$now = Get-Date
$cutoff = $now.AddMinutes(-15)

$states = @()

foreach ($n in @($cfg.nodes)) {
  if ([bool]$n.enabled -ne $true) { continue }
  $st = @{ id = [string]$n.id; lane = [string]$n.lane; ip = [string]$n.tailnet_ip; online = $false; health = ''; status = ''; ram = ''; disk = ''; cpu = ''; gpu = ''; head = ''; pull = ''; note = '' }
  $ip = [string]$n.tailnet_ip
  if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $ip = '127.0.0.1' }
  $st.ip = $ip
  # health probe
  try {
    $h = Invoke-RestMethod -Uri ('http://' + $ip + ':' + $port + '/health') -Method Get -TimeoutSec 4
    $st.health = [string]$h.node + ' ts=' + [string]$h.ts
  } catch { $st.note = 'health-fail ' + ([string]$_.Exception.Message) }
  # status probe
  try {
    $s = Invoke-RestMethod -Uri ('http://' + $ip + ':' + $port + '/status') -Method Get -TimeoutSec 6
    foreach ($k in @('node','version','ts')) { if ($s.PSObject.Properties.Name -contains $k) { $st[$k] = [string]$s.$k } }
    foreach ($k in @('ram','disk','cpu','gpu')) { if ($s.PSObject.Properties.Name -contains $k) { try { $st[$k] = ($s.$k | ConvertTo-Json -Compress -Depth 3) } catch { } } }
    if ($s.PSObject.Properties.Name -contains 'repo_heads') {
      $p = $s.repo_heads.PSObject.Properties['.']
      if ($p -and $p.Value) { $st.head = [string]$p.Value }
    }
    if ($s.PSObject.Properties.Name -contains 'last_pull') {
      $lp = $s.last_pull
      if ($lp) {
        if ($lp.PSObject.Properties.Name -contains 'pulled_at') { $st.pull = [string]$lp.pulled_at }
        if ($lp.PSObject.Properties.Name -contains 'origin_main' -and $st.head -eq '') { $st.head = [string]$lp.origin_main }
      }
    }
    $st.online = $true
  } catch { $st.note = ($st.note + ' | status-fail ' + ([string]$_.Exception.Message)).Trim(' |') }

  # freshness vs 15min cutoff (health ts parse)
  if ($st.health -match 'ts=([\dT:\-.]+)') {
    try { $ht = [datetime]$Matches[1]; if ($ht -lt $cutoff) { $st.note = ($st.note + ' | stale-health ' + $ht.ToString('HH:mm')).Trim(' |') } } catch { }
  }
  $states += $st
}

# bm-a local extras
$lastOrder = ''
$orderFile = Join-Path $root 'docs\orders.md'
if (Test-Path -LiteralPath $orderFile) {
  $tailLines = [System.IO.File]::ReadAllLines($orderFile)
  if ($tailLines.Length -gt 0) {
    $tail = $tailLines[$tailLines.Length - 1]
    if ($tail.Length -gt 400) { $tail = $tail.Substring(0, 400) + '...' }
    $lastOrder = $tail
  }
}
$alerts = @()
$aFile = Join-Path $env:USERPROFILE '.codely-cli\fleet-liveness\alerts.jsonl'
if (Test-Path -LiteralPath $aFile) {
  # Use .NET reader: Get-Content attaches PS* NoteProperties to each line; those
  # explode ConvertTo-Json output (PS5.1 real bug seen 10-21, 17.9MB board).
  $alerts = @([System.IO.File]::ReadAllLines($aFile) | Where-Object { $_ -match '\S' } | Select-Object -Last 5)
}
$dispatch = @()
$dFile = Join-Path $env:USERPROFILE '.codely-cli\fleet-link\dispatch-log.jsonl'
if (Test-Path -LiteralPath $dFile) {
  $dispatch = @([System.IO.File]::ReadAllLines($dFile) | Where-Object { $_ -match '\S' } | Select-Object -Last 3)
}

$data = @{
  generated = $now.ToString('yyyy-MM-dd HH:mm:ss')
  node_count = $states.Count
  online_count = @($states | Where-Object { $_.online }).Count
  states = $states
  last_order = $lastOrder
  alerts = $alerts
  dispatch = $dispatch
}
$json = $data | ConvertTo-Json -Compress -Depth 6
$outDir = Join-Path $root 'fleet'
if (-not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$jsonPath = Join-Path $outDir 'fleet-board.json'
[System.IO.File]::WriteAllText($jsonPath, $json, (New-Object System.Text.UTF8Encoding($false)))

# self-contained HTML (ASCII body; CJK labels are \u escapes interpreted by JS)
$html = @"
<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>FluxGroup Fleet Board</title>
<style>
body{background:#0d1117;color:#c9d1d9;font-family:'Segoe UI',system-ui,sans-serif;margin:0;padding:20px}
h1{font-size:18px;color:#e6edf3;margin:0 0 4px}
.meta{color:#8b949e;font-size:12px;margin-bottom:14px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin-bottom:10px}
.g{color:#3fb950}.r{color:#f85149}.y{color:#d29922}.dim{color:#8b949e;font-size:12px}
table{border-collapse:collapse;width:100%;font-size:13px}
td,th{padding:4px 8px;border-bottom:1px solid #21262d;text-align:left;vertical-align:top}
th{color:#8b949e;font-weight:600;width:110px}
code{color:#79c0ff;word-break:break-all}
.ok{color:#3fb950;font-weight:700}
</style></head><body>
<h1>FluxGroup Fleet Board</h1>
<div class="meta" id="meta"></div>
<div id="cards"></div>
<h1 style="margin-top:16px">Last Order</h1>
<div class="card"><code id="ord"></code></div>
<h1>Dispatch Log (tail)</h1>
<div class="card"><code id="disp"></code></div>
<h1>Alerts (tail)</h1>
<div class="card"><code id="alerts"></code></div>
<script>
var DATA = $json;
var CARD = {};
document.getElementById('meta').textContent = 'generated ' + DATA.generated + ' | nodes ' + DATA.node_count + ' | online ' + DATA.online_count;
var cards = '';
DATA.states.forEach(function(s){
  var on = s.online ? '<span class="ok">ONLINE</span>' : '<span class="r">OFFLINE</span>';
  cards += '<div class="card"><table>' +
    '<tr><th>' + s.id + ' (' + s.lane + ')</th><td>' + on + ' <span class="dim">ip ' + s.ip + '</span></td></tr>' +
    '<tr><th>\u72b6\u6001(status)</th><td><code>' + (s.status || '-') + '</code></td></tr>' +
    '<tr><th>\u5fc3\u8df3(health)</th><td><code>' + (s.health || '-') + '</code></td></tr>' +
    '<tr><th>\u5934(HEAD)</th><td><code>' + (s.head || '-') + '</code></td></tr>' +
    '<tr><th>\u62c9\u53d6(pull)</th><td><code>' + (s.pull || '-') + '</code></td></tr>' +
    '<tr><th>\u8d44\u6e90(res)</th><td><span class="dim">' + (s.ram ? 'ram ' + s.ram : '') + (s.disk ? ' | disk ' + s.disk : '') + (s.cpu ? ' | cpu ' + s.cpu : '') + (s.gpu ? ' | gpu ' + s.gpu : '') + '</span></td></tr>' +
    (s.note ? '<tr><th>\u5907\u6ce8(note)</th><td class="y">' + s.note + '</td></tr>' : '') +
    '</table></div>';
});
document.getElementById('cards').innerHTML = cards;
document.getElementById('ord').textContent = DATA.last_order || '-';
document.getElementById('disp').textContent = (DATA.dispatch && DATA.dispatch.length ? DATA.dispatch.join('\n') : '-');
document.getElementById('alerts').textContent = (DATA.alerts && DATA.alerts.length ? DATA.alerts.join('\n') : '-');
</script>
</body></html>
"@
$htmlPath = Join-Path $outDir 'fleet-board.html'
[System.IO.File]::WriteAllText($htmlPath, $html, (New-Object System.Text.UTF8Encoding($false)))

Write-Output ('BOARD generated -> ' + $htmlPath)
Write-Output ('  json -> ' + $jsonPath + ' | nodes=' + $states.Count + ' online=' + @($states | Where-Object { $_.online }).Count)