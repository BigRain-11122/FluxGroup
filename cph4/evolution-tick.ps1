# FluxGroup evolution tick - weekly headless codely round (CPH4 evolution engine)
# ENCODING RULE: this file must stay PURE ASCII (PS 5.1 GBK trap, group law)
# Chinese mandate lives in evolution-tick-prompt.txt (UTF-8, read with explicit encoding)
$ErrorActionPreference = 'Continue'
$Project = Split-Path -Parent $PSScriptRoot
$Lock = Join-Path $Project '.codely-cli\evolution.lock'
$Stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
if (Test-Path $Lock) {
  $age = ((Get-Date) - (Get-Item $Lock).LastWriteTime).TotalMinutes
  if ($age -lt 120) { exit 0 }
}
New-Item -ItemType File -Path $Lock -Force | Out-Null
try {
  $promptFile = Join-Path $PSScriptRoot 'evolution-tick-prompt.txt'
  if (-not (Test-Path $promptFile)) { exit 2 }
  $prompt = Get-Content $promptFile -Raw -Encoding UTF8
  $out = Join-Path $Project '.codely-cli\evolution-last.log'
  $cli = (Get-Command codely -ErrorAction SilentlyContinue).Source
  if (-not $cli) { "FATAL: codely not found at $Stamp" | Out-File $out -Encoding UTF8; exit 2 }
  "evolution round start $Stamp" | Out-File $out -Encoding UTF8
  & $cli -y -p $prompt *>> $out
  "evolution round end $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $out -Append -Encoding UTF8
} finally {
  Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
