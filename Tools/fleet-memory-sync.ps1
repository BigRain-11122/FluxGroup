# fleet-memory-sync.ps1 - RETIRED (no-op) per CEO order 2026-10-18 00:2x
# (R-20261018-memory-control-01, memory-governance direct order, dismantle piece).
# Root cause this removes: union REPLACE-DOWN re-inflated every machine's L0 to the
# canonical (375,794B / 322 entries) between gate runs - gate cuts were undone in hours
# (bm-b gate-log 2026-10-18 02:30/06:30/07:40 all started from the same 375,794B face).
# Dismantle state per order text:
#   - this script = no-op (retired; callers in fleet-poke-worker.ps1 / fleet-dispatch.ps1
#     keep calling harmlessly - Test-Path passes, zero effects)
#   - canonical frozen at cph4/fleet/memory/archive/CODELY-fleet-global.md (git mv)
#   - each machine L0 now locally governed: Tools/memory-budget-gate.py + per-machine 4h
#     S4U gate + memory-curator skill (five-questions + L0/L1/L2 routing)
# Prior union code preserved verbatim in git history (archive-not-erase law R1).
# Landed from bm-b r1002 (fleet rollout four-piece; bm-a claimed-local v1.9 worker
# still carries the union block on origin - harmless once this stub is on disk).
param([string]$Root = "", [string]$LocalMem = "", [string]$CanonRel = "", [string]$TombRel = "", [switch]$RecordRemoval, [switch]$Quiet)
Write-Output 'MEMSYNC RETIRED no-op (CEO order 2026-10-18 00:2x; canonical frozen at cph4/fleet/memory/archive/)'
exit 0
