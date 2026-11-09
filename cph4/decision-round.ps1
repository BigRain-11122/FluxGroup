# FluxGroup decision round - daily group adjudication round (CEO order 2026-09-24:
# subsidiaries report daily by 23:00; at 00:00 the group thinks through all open
# problems, researches externally, decides rationally at group level; subsidiaries
# execute and may veto with reasons, re-filing for the next batch).
# ENCODING RULE: pure ASCII (PS 5.1 GBK trap). Chinese mandate lives in
# decision-round-prompt.txt (UTF-8, explicit encoding).
# Lock 30 min. Scheduled daily 00:00 via silent VBS wrapper (silence law).
$ErrorActionPreference = 'Continue'
$Project = Split-Path -Parent $PSScriptRoot
$Lock = Join-Path $Project '.codely-cli\decision-round.lock'
$Stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
if (Test-Path $Lock) {
  $age = ((Get-Date) - (Get-Item $Lock).LastWriteTime).TotalMinutes
  if ($age -lt 30) { exit 0 }
}
New-Item -ItemType File -Path $Lock -Force | Out-Null
try {
  $promptFile = Join-Path $PSScriptRoot 'decision-round-prompt.txt'
  if (-not (Test-Path $promptFile)) { exit 2 }
  $prompt = Get-Content $promptFile -Raw -Encoding UTF8
  $out = Join-Path $Project '.codely-cli\decision-round-last.log'
  $cli = (Get-Command codely -ErrorAction SilentlyContinue).Source
  if (-not $cli) { "FATAL: codely not found at $Stamp" | Out-File $out -Encoding utf8; exit 2 }
  "decision round start $Stamp" | Out-File $out -Encoding utf8
  # D-20261109-07 (2026-11-09 12:0x): durable per-run trace; last.log is overwritten each run,
  # so round gaps (11-07 two rounds, 11-09 00:00) could not be attributed either way.
  $runsDir = Join-Path $Project 'cph4\logs'
  if (-not (Test-Path $runsDir)) { New-Item -ItemType Directory -Force -Path $runsDir | Out-Null }
  $runs = Join-Path $runsDir 'decision-round-runs.log'
  Add-Content -Path $runs -Value ('start ' + $Stamp) -Encoding UTF8
  # T0 CLOUD-OFF guard (CEO 2026-10-20): automation is local-only; never spawn the cloud CLI.
  $__co = $PSScriptRoot
  while ($__co -and -not (Test-Path (Join-Path $__co 'cph4\fleet\CLOUD-OFF-LOCAL-ONLY-v1.md'))) { $__co = Split-Path -Parent $__co }
  if ($__co) {
      $__cl = Join-Path $__co 'media\logs\cloud-off-suppressed.log'
      $__cd = Split-Path -Parent $__cl
      if (-not (Test-Path $__cd)) { New-Item -ItemType Directory -Force -Path $__cd | Out-Null }
      Add-Content -Path $__cl -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + [System.IO.Path]::GetFileName($PSCommandPath) + ' | suppressed cloud round (T0)') -Encoding UTF8
      Add-Content -Path $runs -Value ('suppressed-cloud ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) -Encoding UTF8
      exit 0
  }
  & $cli -y -p $prompt *>> $out
  $rc = $LASTEXITCODE
  "decision round end $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $out -Append -Encoding utf8
  Add-Content -Path $runs -Value ('end ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' rc=' + $rc) -Encoding UTF8
} finally {
  Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
