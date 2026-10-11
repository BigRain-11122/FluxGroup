# FluxGroup night round - daily headless self-reaction round (CPH4 evolution engine)
# Lightweight daily sibling of the weekly evolution tick. CEO order 2026-09-23:
# build mechanisms tonight + keep iterating self-reaction overnight. The night
# round senses, nudges stalled transfers, fixes T2/T3 drift in its own lane and
# files a short night report. Full four-step legislation stays with the weekly
# round (charter: cph4/evolution.md sec 1/5).
# ENCODING RULE: pure ASCII (PS 5.1 GBK trap, group law). Chinese mandate lives
# in night-round-prompt.txt (UTF-8, read with explicit encoding).
# Lock 60 min (a slow round must not collide with the next). Scheduled daily
# 03:07 via silent VBS wrapper (silence law).
$ErrorActionPreference = 'Continue'
$Project = Split-Path -Parent $PSScriptRoot
$Lock = Join-Path $Project '.codely-cli\night-round.lock'
$Stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
if (Test-Path $Lock) {
  $age = ((Get-Date) - (Get-Item $Lock).LastWriteTime).TotalMinutes
  if ($age -lt 60) { exit 0 }
}
New-Item -ItemType File -Path $Lock -Force | Out-Null
try {
  $promptFile = Join-Path $PSScriptRoot 'night-round-prompt.txt'
  if (-not (Test-Path $promptFile)) { exit 2 }
  $prompt = Get-Content $promptFile -Raw -Encoding UTF8
  $out = Join-Path $Project '.codely-cli\night-round-last.log'
  $cli = (Get-Command codely -ErrorAction SilentlyContinue).Source
  if (-not $cli) { "FATAL: codely not found at $Stamp" | Out-File $out -Encoding utf8; exit 2 }
  "night round start $Stamp" | Out-File $out -Encoding utf8
  & $cli -y -p $prompt *>> $out
  "night round end $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $out -Append -Encoding utf8
} finally {
  Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
