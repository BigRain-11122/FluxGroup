# ceo-use-pause-resume.ps1 - reverse the ad-hoc "CEO use pause" batch disable
# Root cause (2026-11-07 night round): the 2026-11-06 11:5x CEO-use pause disabled
# ~80 tasks INCLUDING bm-a-AutoYield-WorkEnd (the 19:00 auto-resume valve), so nothing
# ever re-enabled them -> group froze 21h (bm-a heartbeat STALE). machine-state.ps1
# -Mode resume only knows its own 17-task sidecar, not this list.
#
# Usage (in-process per U060 law, no console spawn):
#   & "<root>\.codely-cli\ceo-use-pause-resume.ps1" -DryRun
#   & "<root>\.codely-cli\ceo-use-pause-resume.ps1"
# Exemptions: DESIGNED-DISABLED (BoardForge / PopupWitness / Ollama keepwarm lanes)
# and FluxVerse-DevLoop (CEO stop-and-retarget, keepdown until new mandate).
param([switch]$DryRun, [string]$ListFile)

$ErrorActionPreference = "Stop"
if (-not $ListFile) {
  $ListFile = Get-ChildItem (Join-Path $PSScriptRoot "tmp") -Filter "ceo-use-pause-*-tasks.json" -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $ListFile -or -not (Test-Path $ListFile)) { Write-Output "[ceo-resume] no pause manifest found"; exit 1 }

$exempt = @(
  "MiniGameBoardForge","MiniGamePopupWitness","MiniGameOllamaKeepWarm","MiniGameOllamaServe",
  "FluxVerse-DevLoop"
)
$manifest = Get-Content $ListFile -Raw | ConvertFrom-Json
$targets  = @($manifest.disabled) | Where-Object { $_ -and ($exempt -notcontains $_) }
Write-Output ("[ceo-resume] manifest=" + (Split-Path $ListFile -Leaf) + " ts=" + $manifest.ts + " targets=" + $targets.Count + " dryrun=" + [bool]$DryRun)

$ok = 0; $fail = 0
foreach ($t in $targets) {
  $task = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
  if (-not $task) { Write-Output "[ceo-resume] MISSING: $t"; $fail++; continue }
  if ($task.State -ne "Disabled") { Write-Output "[ceo-resume] already-active: $t ($($task.State))"; $ok++; continue }
  if ($DryRun) { Write-Output "[ceo-resume] would-enable: $t"; $ok++; continue }
  try {
    Enable-ScheduledTask -TaskName $t -ErrorAction Stop | Out-Null
    $ok++
  } catch {
    Write-Output "[ceo-resume] WARN enable ${t}: $($_.Exception.Message)"
    $fail++
  }
}
Write-Output "[ceo-resume] DONE enabled/already=$ok failed=$fail"
# Sentinel so the next night round can tell whether the reverse actually ran.
$stamp = Join-Path $PSScriptRoot "tmp\ceo-use-pause-resume.last.json"
"{""ts"":""$(Get-Date -Format o)"",""manifest"":""$(Split-Path $ListFile -Leaf)"",""enabled"":$ok,""failed"":$fail,""dryrun"":$([bool]$DryRun)}" |
  Set-Content -Path $stamp -Encoding UTF8