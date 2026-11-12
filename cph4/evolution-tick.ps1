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
  # T0 cloud gate (D-20261112-02/D-10, T1-v2): CEO unlock (98a3f5ea8) retired the old
  # CLOUD-OFF marker, so the literal-walk guard below was dead code that silently
  # spawned cloud rounds. Automation is local-only unless an explicit allow switch
  # exists: cph4\fleet\CLOUD-ALLOW-AUTOMATION.md (present=allow, absent/anomaly=suppress).
  # Fail-closed; the resolver double-seeds script root + git physical toplevel.
  $__gateTool = Join-Path $Project 'Tools\cloud-off-gate.ps1'
  . $__gateTool
  $__gate = Resolve-CloudOffGate -ScriptRoot $PSScriptRoot -Project $Project -MarkerName 'CLOUD-ALLOW-AUTOMATION.md'
  if (-not (Test-CloudAutomationAllowed -Gate $__gate)) {
      $__cl = Join-Path $Project 'media\logs\cloud-off-suppressed.log'
      $__cd = Split-Path -Parent $__cl
      if (-not (Test-Path $__cd)) { New-Item -ItemType Directory -Force -Path $__cd | Out-Null }
      Add-Content -Path $__cl -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + [System.IO.Path]::GetFileName($PSCommandPath) + ' | suppressed cloud round (local-only, no CLOUD-ALLOW-AUTOMATION.md | ' + (Format-CloudOffGateLine -Gate $__gate) + ')') -Encoding UTF8
      exit 0
  }
  & $cli -y -p $prompt *>> $out
  "evolution round end $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $out -Append -Encoding UTF8
} finally {
  Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
