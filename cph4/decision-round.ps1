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
  & $cli -y -p $prompt *>> $out
  "decision round end $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $out -Append -Encoding utf8
} finally {
  Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
