# quant-audit-cadence.ps1 -- external quant oversight cadence runner (D-20260930-32)
# Self-driven loop: every N minutes run all read-only probes, append one row per run
# to a JSONL ledger, and print a delta line against the previous run.
# ASCII-only body (encoding law). Reads sibling repos, never writes into them.
param(
  [int]$IntervalSeconds = 600,
  [int]$MaxRuns = 0,                # 0 = run forever
  [string]$Root = ''
)
$ErrorActionPreference = 'Continue'
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = Split-Path -Parent $PSScriptRoot }
$bm = Join-Path $Root 'quant\bigmoney'
$ledger = Join-Path $Root 'docs\audits\quant-audit-cadence.jsonl'
$tmpDir = Join-Path $Root 'docs\audits'

$run = 0
$prev = $null
while ($true) {
  $run++
  $stamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  $row = [ordered]@{ ts_utc = $stamp; run = $run }

  # --- probe A: group deliverable metrics ---
  try {
    $pa = & (Join-Path $Root 'Tools\deliverable-probe.ps1') -Root $Root 2>&1
    $paOut = ($pa | Select-String -Pattern '^TOTAL').Line
    $row.deliverable = "$paOut"
  } catch { $row.deliverable = 'ERROR ' + $_.Exception.Message }

  # --- probe B: quant v1 (equity/unmarked/annualization/snapshots/zero-activity) ---
  try {
    $pb = & (Join-Path $Root 'Tools\quant-audit-probe.ps1') -Repo $bm -Out (Join-Path $tmpDir 'quant-audit-probe-20260930.json') 2>&1
    $row.quant_v1 = (($pb | Where-Object { $_ -match '^Q' }) -join ' ')
  } catch { $row.quant_v1 = 'ERROR ' + $_.Exception.Message }

  # --- probe C: quant v2 (cost/staleness/lockbox/paper fills) ---
  try {
    $pc = & (Join-Path $Root 'Tools\quant-audit-probe-v2.ps1') -Repo $bm -Out (Join-Path $tmpDir 'quant-audit-v2-20260930.json') 2>&1
    $row.quant_v2 = (($pc | Where-Object { $_ -match '^Q' }) -join ' ')
  } catch { $row.quant_v2 = 'ERROR ' + $_.Exception.Message }

  # --- delta vs previous run ---
  $row.delta = if ($prev) { $prev } else { 'baseline' }
  $line = ($row | ConvertTo-Json -Compress)
  Add-Content -Path $ledger -Value $line -Encoding UTF8

  # console line for the operator
  Write-Output ("[$stamp] run=$run")
  Write-Output ('  deliverable : ' + $row.deliverable)
  Write-Output ('  quant v1    : ' + $row.quant_v1)
  Write-Output ('  quant v2    : ' + $row.quant_v2)
  $prev = 'run' + $run

  if ($MaxRuns -gt 0 -and $run -ge $MaxRuns) { break }
  Start-Sleep -Seconds $IntervalSeconds
}
