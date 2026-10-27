# oversight_deploy.ps1 - the deployed oversight writer must be THIS repo's source
#
# WHY (2026-10-28, bm-b r1195)
# ---------------------------
# The hourly task does not run the repo copy. It runs a DEPLOYED copy under
# <KRoot>\.codely-cli\oversight-<M>\fleet-oversight.ps1, and nothing kept that
# copy in step with Tools/fleet-oversight.ps1. So when D-20261028-02 fixed the
# machine-health writer (machine-keyed map, adopt-only-ts, never propagate
# damage), the fix landed in the repo and the *running* code stayed at v1.0 --
# and one hour later it re-broke fleet/machine-health.json with the exact
# {"value": ...} nesting the fix removed. Same family as the "worker reads the
# code that was on disk when it spawned" pit: a deployed copy is a second code
# face and needs its own drift check.
#
# MODES
#   powershell Tools/oversight_deploy.ps1 -M bm-b            # deploy + verify
#   powershell Tools/oversight_deploy.ps1 -M bm-b -Check     # drift check only
#
# -Check exits 0 when the deployed copy is byte-identical to the source (CR
# normalised), 1 when it drifts, 2 when it has never been deployed. The smoke
# leg in the BigMoney repo calls -Check, so a stale deployed writer is RED
# instead of silently rewriting a shared face.
param(
  [string]$M = "bm-c",
  [string]$KRoot = "",
  [switch]$Check
)
$ErrorActionPreference = 'Stop'

if (-not $KRoot) {
  # KRoot is the parent of this group repo: <KRoot>\FluxGroup\Tools\this-file
  $KRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}
$src = Join-Path $PSScriptRoot 'fleet-oversight.ps1'
# The live task's directory drops the dashes from the machine id (bm-b -> oversight-bmb,
# registered 2026-10-11). Deploying to oversight-bm-b wrote a copy no task ever reads,
# which is the very drift this tool exists to catch -- so resolve the live suffix first:
# an already-deployed dashed-stripped dir wins, and only then fall back to the raw id.
$suffix = $M -replace '-', ''
$dashedDir = Join-Path $KRoot ('.codely-cli\oversight-' + $M)
$plainDir = Join-Path $KRoot ('.codely-cli\oversight-' + $suffix)
$dstDir = if ((Test-Path -LiteralPath $dashedDir) -and -not (Test-Path -LiteralPath $plainDir)) { $dashedDir } else { $plainDir }
$dst = Join-Path $dstDir 'fleet-oversight.ps1'

if (-not (Test-Path -LiteralPath $src)) { Write-Output ("oversight-deploy: source missing: " + $src); exit 2 }
$srcText = ([IO.File]::ReadAllText($src)) -replace "`r`n", "`n"

$deployed = $false
$dstText = ''
if (Test-Path -LiteralPath $dst) {
  $deployed = $true
  $bytes = [IO.File]::ReadAllBytes($dst)
  if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
    $dstText = [Text.Encoding]::Unicode.GetString($bytes, 2, $bytes.Length - 2)
  } else {
    $dstText = [Text.Encoding]::UTF8.GetString($bytes)
  }
  $dstText = $dstText -replace "`r`n", "`n"
}

if ($Check) {
  if (-not $deployed) { Write-Output ("oversight-deploy: NOT DEPLOYED for " + $M + " -> " + $dst); exit 2 }
  if ($srcText -ne $dstText) {
    Write-Output ("oversight-deploy: DRIFT for " + $M + " -- deployed copy is not this repo's source (" + $dst + ")")
    exit 1
  }
  Write-Output ("oversight-deploy: OK " + $M + " deployed copy matches source (" + $srcText.Length + " chars)")
  exit 0
}

New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
# UTF-8 with BOM: the writer contains CJK comments and PowerShell 5.1 mis-reads
# BOM-less UTF-8 as ANSI (mojibake in strings that reach a written face).
[IO.File]::WriteAllText($dst, $srcText, (New-Object System.Text.UTF8Encoding $true))

$after = ([IO.File]::ReadAllText($dst)) -replace "`r`n", "`n"
if ($after -ne $srcText) {
  Write-Output ("oversight-deploy: FAIL verify after write (" + $dst + ")")
  exit 1
}
Write-Output ("oversight-deploy: deployed " + $M + " -> " + $dst + " (" + $srcText.Length + " chars, verified)")
exit 0