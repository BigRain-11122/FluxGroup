"""Bank surgery for C2170: pre-stow the pseudo-text guard, gate the unwired conform job.

Run: python c2170_bank_surgery.py [--dry-run]
Idempotent: re-running updates the same job ids instead of appending twins.
"""
import json
import os
import sys

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
PY = r"D:\ComfyUI\python_embeded\python.exe"
GUARD = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit\kn_pseudo_guard_c2170.py"
LOGS = "media/mv-album-001-jay/logs"


def guard_job():
    return {
        "id": "kn-pseudo-guard-c2170",
        "status": "pending",
        "priority": 1,
        "auth": "C2170",
        "require": {},
        "cmd": [PY, GUARD],
        "log_out": LOGS + "/kn_pseudo_guard.out.log",
        "log_err": LOGS + "/kn_pseudo_guard.err.log",
        "note": ("Zero GPU. Scans every landed KN_A-*.mp4 for the C2170 "
                 "subtitle-band pseudo-text class (KN02 is a confirmed hit: a "
                 "generated caption strip, clean keyframe, so it is a generator "
                 "prior). Writes evidence-c2170/pseudotext-guard.json with "
                 "halt_recommended. Never kills a burn."),
        "claimed_ts": None,
        "claimed_by": None,
        "done_ts": None,
        "done_note": None,
    }


def main():
    dry = "--dry-run" in sys.argv
    with open(BANK, encoding="utf-8") as f:
        bank = json.load(f)
    jobs = bank["jobs"]
    ids = {j["id"]: j for j in jobs}

    # 1) pre-stow / refresh the guard job
    g = guard_job()
    if "kn-pseudo-guard-c2170" in ids:
        cur = ids["kn-pseudo-guard-c2170"]
        if cur.get("status") in ("pending", "claimed"):
            g["status"] = cur["status"]
            g["claimed_ts"] = cur.get("claimed_ts")
            g["claimed_by"] = cur.get("claimed_by")
        jobs[jobs.index(cur)] = g
        action = "updated"
    else:
        jobs.append(g)
        action = "appended"

    # 2) gate the unwired conform job: it must not fire before the harvest
    #    verdict exists, and its cmd stays empty until the script is authored
    #    (bmc_idleguard now skips empty-cmd jobs instead of crashing).
    conf = ids.get("kn-pa-station4-conform-author-c2169")
    conf_note = "gated"
    if conf is not None:
        conf["require"] = {"files_at_least": [
            ["cph4/fleet/mv-album-001-jay", "KN-PA768-HARVEST-c2169.json", 1]]}
        conf["note"] = (str(conf.get("note") or "") +
                        " | C2170: require-gated on the harvest verdict; cmd is "
                        "still empty (script not authored) and the idle guard now "
                        "skips empty-cmd jobs instead of crashing on them.")

    print("GUARD_JOB %s status=%s" % (action, g["status"]))
    print("CONFORM_JOB %s require=%s cmd_empty=%s"
          % (conf_note, bool(conf["require"]), not conf.get("cmd") if conf else None))
    print("BANK_JOBS %d" % len(jobs))
    if dry:
        print("DRY-RUN: not written")
        return 0
    with open(BANK, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=1)
    print("BANK_WRITTEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())