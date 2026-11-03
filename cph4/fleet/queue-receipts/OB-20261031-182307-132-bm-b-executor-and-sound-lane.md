# OB-20261031-182307-132 + OB-20261031-174059-609 — bm-b receipt

Node: bm-b (Windows, C:\Fluxgroup\FluxGroup)
Written: 2026-11-01T02:4x+08:00 (round r1344, bm-b)

## 18:23 执行器统一令 (OB-20261031-182307-132)

| step | state | evidence |
|---|---|---|
| `python Tools\fleet\agent.py --node bm-b` runs | **OK** | `agent bm-b hb=0(HB bm-b seq=1 offset=2844.4ms) lane=...` at 02:40; after the fix below the lane closes its card: `R-TTS1202R-VERIFY-20261031 DONE rc=0 0.1s deliverable=True` |
| heartbeat + claim both work (<=30s) | **OK** | whole tick 9.7s; `lane_agent --dry` selects the card `R-TTS1202R-VERIFY-20261031` |
| registered as the single resident task, every 5 min | **already in place, no-op** | `FluxGroup-Agent-bm-b` Ready, LogonType=S4U, action `wscript //B InvisibleRunner.vbs pythonw.exe Tools\fleet\agent.py --node bm-b --no-pull`, LastRun 02:21:32 rc=0, NextRun 02:26:31 |
| old HQ-ProductionClaim disabled | **already Disabled** | `HQ-ProductionClaim` State=Disabled (S4U) |
| receipt | this file | `cph4/fleet/queue-receipts/` |

### Why the executor had been "alive with an empty log" (two defects, both below the task layer)

1. **The lane card carried the Mac's working directory.** The bm-b lane payload says
   `cwd: /Users/junsheng.sun/FluxGroup`. On Windows `CreateProcess` raises
   `NotADirectoryError [WinError 267]` before the command starts, so every 5-minute tick exited
   rc=1 having run nothing. Patched in `Tools/fleet/lane_agent.py`: an unusable `cwd` falls back to
   the repo root, the substitution is printed, and both values are recorded in the receipt
   (`cwd_asked` / `cwd_used`). Upstream `origin/main` still has the unguarded
   `cwd=job.get("cwd") or root`, so the same card will fail the same way on any Windows node -- this
   patch should be taken upstream.
2. **This worktree is 1,493 commits behind origin/main**, so `Tools/fleet/tts_batch_check.py`
   (tracked upstream since at least 10-31) was missing on disk and the card died on "can't open
   file". Restored the canonical blob (`git show origin/main:Tools/fleet/tts_batch_check.py`) rather
   than shipping a second implementation of the same tool; the local draft was discarded per the
   no-duplicate-development law.

Both fixes are **working-tree only, deliberately not committed**: these paths are tracked upstream
and committing a 1,493-behind fork of the fleet executor would fork the canonical chain. See
"Needs a real pull" below.

### The job's deliverable (canonical tool, real numbers)

`cph4/fleet/queue-receipts/Q-TTS-1202R-bm-b-verify.md` (written by the task itself, verdict from the
batch directory):

* `media/drama-tts-out/r1202_ep001_060`: **1036 audio files, 147,430,476 bytes (147.4 MB)**
* newest write age **4357 min (~3.0 days)** -> `COMPLETE-STOPPED`
* so the batch finished writing three days ago while the claim sat in RUNNING for two hours: the
  claim died on pickup, which is exactly the case this tool was written for. Nothing was re-run.

A deeper manifest-level pass was also run for this receipt and is NOT published as a tool (it would
be a second implementation): the batch's own `MANIFEST-r998.json` lists 1036 lines, **all 1036 have
their wav on disk**, 0 unreadable headers, **0 headers disagreeing with the stated `audio_s`**
(0.15s tolerance), and **108 lines are more than 1.0s longer than the shot they are cut into**
(EP001 n1 5.91s > 3s and so on) -- a mixing disclosure, not a synthesis failure.

## 17:40 全面开工 resume (OB-20261031-174059-609)

| step | state | evidence |
|---|---|---|
| `machine-state.ps1 -Mode resume` | **already resumed** | `C:\Fluxgroup\.codely-cli\machine-state.flag` = `resumed 2026-10-30T11:13:04` |
| bm-b lane (配音/混音/词锚/声音) executable work taken at round start | **OK** | the sound-lane card above was claimed and completed this round; `bm-b-SoundLane` Ready, LastRun 02:24:24 rc=0 |

No GPU work started (bm-b GPU parked, C-20261014-01); no cloud call made.

## Needs a real pull (flag for the dispatcher, not fixed here)

`git rev-list --left-right --count HEAD...origin/main` on this worktree = **12 ahead / 1493 behind**.
Every fleet tool on this box is therefore an old revision: local `lane_agent.py` is 15,029 bytes
against upstream's 28,996. A pull is a dispatcher decision (it changes the executor that runs every
5 minutes and the tree is shared with the sound lane), so this round did not take it -- but the
1,493-commit lag is a machine-level defect of the same family as the two above.