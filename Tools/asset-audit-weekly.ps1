# asset-audit-weekly.ps1 - weekly Unity asset bloat/convention sentinel
# CEO order 2026-10-19 "form an optimization mechanism, no uncontrolled growth over time".
# Law: cph4/resource-chain.md S3.12 (bloat governance charter).
# Weekly target = gaming\FluxVerse (active dev surface, ~8k images, minutes-level sweep).
# Art Assets (250k+ upstream images, frozen/license-exempt) = monthly night deep sweep
# + intake-time gate (asset-audit skill) - NEVER weekly daytime full sweep (yield law).
# Child script exit propagates (same process): 0 clean / 1 FAIL found / 2 path missing
# -> LastTaskResult surfaces in task-health night report (cadence S6 signal 3).
# Report goes to gitignored tmp (no tracked-file weekly churn); FAIL summaries render
# into the steward-shift report via exit code.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$target = Join-Path $root 'gaming\FluxVerse'
$report = Join-Path $root '.codely-cli\tmp\asset-audit-report.md'
& (Join-Path $here 'asset-audit.ps1') -Path $target -Report $report -ExemptDirs 'ArtPacks,CleanCityv3'
