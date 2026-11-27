# sli-reconcile-wrapper.ps1 - HQ-B-ProxySLI daily carrier (MASTER-AGENT BLUEPRINT v2 Phase 1-alpha G4)
# O-20261014-1745 Phase 1-alpha dispatch row 4 (@bm-b external seat).
# Pull the group repo first (git = sole data channel), then run the external-seat
# SLI reconcile which writes + commits + pushes SLI-RECONCILE.md (bm-b lane).
$ErrorActionPreference = 'Continue'
$Root = 'C:\Fluxgroup\FluxGroup'
$git = 'C:\Program Files\Git\cmd\git.exe'
if (Test-Path $git) { & $git -C $Root pull --ff-only 2>&1 | Out-Null }
& (Join-Path $Root 'Tools\sli-reconcile.ps1') @args
