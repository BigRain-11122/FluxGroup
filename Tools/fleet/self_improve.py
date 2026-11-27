# -*- coding: utf-8 -*-
"""self_improve.py - 机队自改（runs ON THE WORKER BOX, by the lane agent).

CEO 2026-11-06: "你不仅要自己改进，主要是拉着机队一起改。"

Each box fixes its own three chronic defects instead of waiting for the master to
hand-fix it (master is forbidden from cross-box surgery):

  1. RELOAD  - executor started before the code it runs was last edited
               ("入库 ≠ 重载": a fix that never reloads is worth zero).
  2. SHELLS  - lane cards that carry only a box state and no `cmd` (the 347-card
               incident: the lane scans them, skips them, and the box self-reports
               SELF-DISPATCH while the queue has work).
  3. DEPS    - missing binaries the repo already knows how to install (env_selfheal).

Dry-run by default. `--apply` performs the repair. Every run writes a receipt under
cph4/fleet/queue-receipts/ so the master verifies on disk, not on self-report.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fleet_lane as fl

RECEIPT_DIR = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
# Code that the running executor actually imports. A change here without a reload
# is the defect this tool exists for.
CODE_REL = [
    "Tools/fleet/lane_agent.py",
    "Tools/fleet/fleet_lane.py",
    "Tools/fleet/agent.py",
]
# A receipt older than this means the executor is very likely stale even when mtimes
# are equal (e.g. files restored by git checkout keep old mtime).
STALE_RECEIPT_S = 6 * 3600


def _sh(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout, shell=isinstance(cmd, str))
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, "EXC: %s" % e


def code_age_s():
    """Seconds since the newest file of the executor's own code was edited."""
    newest = 0.0
    seen = 0
    for rel in CODE_REL:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if os.path.exists(p):
            newest = max(newest, os.path.getmtime(p))
            seen += 1
    if not seen:
        return None
    return max(0.0, time.time() - newest)


def newest_receipt_age_s():
    """Age of the newest receipt written by real work - NOT by this tool.

    度量不能自指（2026-11-05 铁律）: including self-improve receipts makes this check
    read its own output and call a stale executor fresh forever.
    """
    if not os.path.isdir(RECEIPT_DIR):
        return None
    newest = 0.0
    for f in os.listdir(RECEIPT_DIR):
        if f.startswith("self-improve-"):
            continue
        p = os.path.join(RECEIPT_DIR, f)
        if os.path.isfile(p):
            newest = max(newest, os.path.getmtime(p))
    if not newest:
        return None
    return max(0.0, time.time() - newest)


def reload_targets(node):
    """Restart commands for this box's executor. Discovered, never guessed blind.

    darwin: launchd labels under ~/Library/LaunchAgents matching the node/lane.
    windows: scheduled tasks matching FluxGroup-Lane / the node id.
    """
    targets = []
    if sys.platform == "darwin":
        d = os.path.expanduser("~/Library/LaunchAgents")
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if not f.endswith(".plist"):
                    continue
                low = f.lower()
                if "fluxgroup" in low and ("lane" in low or node in low):
                    label = f[:-6]
                    targets.append({"kind": "launchd", "id": label,
                                    "cmd": ["launchctl", "kickstart", "-k",
                                            "gui/%d/%s" % (os.getuid(), label)]})
    elif os.name == "nt":
        rc, out = _sh(["schtasks", "/Query", "/FO", "CSV", "/NH"], timeout=120)
        if rc == 0:
            for line in out.splitlines():
                name = (line.split(",")[0] or "").strip('"')
                low = name.lower()
                if "fluxgroup-lane" in low or ("lane" in low and node.lower() in low):
                    targets.append({"kind": "schtasks", "id": name,
                                    "cmd": ["schtasks", "/End", "/TN", name],
                                    "then": ["schtasks", "/Run", "/TN", name]})
    return targets


def check_reload(node, apply_):
    age = code_age_s()
    rec_age = newest_receipt_age_s()
    item = {"check": "reload", "code_age_s": None if age is None else round(age),
           "receipt_age_s": None if rec_age is None else round(rec_age),
           "targets": [], "acted": False, "note": ""}
    if age is None:
        item["note"] = "code files missing -> cannot judge (CARD-DEFECT: wrong root or repo)"
        item["verdict"] = "SKIP"
        return item
    stale = rec_age is None or rec_age > max(age, STALE_RECEIPT_S)
    item["stale"] = bool(stale)
    if not stale:
        item["verdict"] = "OK"
        item["note"] = "executor produced a receipt after the last code edit"
        return item

    targets = reload_targets(node)
    item["targets"] = [t["id"] for t in targets]
    if not targets:
        item["verdict"] = "NEED-RELOAD"
        item["note"] = ("code newer than receipts and no restart unit found - "
                        "executor is running old code; register the lane task")
        return item
    if not apply_:
        item["verdict"] = "WOULD-RELOAD"
        return item

    results = []
    for t in targets:
        rc, out = _sh(t["cmd"], timeout=120)
        if rc == 0 and t.get("then"):
            rc2, out2 = _sh(t["then"], timeout=120)
            out = (out + "\n" + out2).strip()
            rc = rc or rc2
        results.append({"id": t["id"], "rc": rc, "out": out.strip()[:400]})
    item["acted"] = True
    item["results"] = results
    item["verdict"] = "RELOADED" if any(r["rc"] == 0 for r in results) else "RELOAD-FAILED"
    return item


def check_shells(node, apply_):
    """Cards handed to this box that carry no `cmd` - scanned and skipped silently."""
    item = {"check": "shells", "cards": 0, "shells": 0, "ids": [], "acted": False}
    try:
        payload = fl.lane_payload(ROOT, node, fetch=False) or {}
    except Exception as e:
        item["verdict"] = "SKIP"
        item["note"] = "lane payload unreadable: %s" % e
        return item
    cards = payload.get("cards") or payload.get("jobs") or []
    if not isinstance(cards, list):
        cards = []
    shells = []
    for c in cards:
        if not isinstance(c, dict):
            continue
        if not str(c.get("cmd") or "").strip():
            shells.append(str(c.get("id") or "?"))
    item["cards"] = len(cards)
    item["shells"] = len(shells)
    item["ids"] = shells[:20]
    if not cards:
        item["verdict"] = "OK"
        item["note"] = "no assignment on this lane (not a shell problem)"
    elif not shells:
        item["verdict"] = "OK"
    elif not apply_:
        item["verdict"] = "WOULD-PRUNE"
        item["note"] = "shell cards carry state but no cmd; prune so the lane stops counting them"
    else:
        kept = [c for c in cards
                if not isinstance(c, dict) or str(c.get("cmd") or "").strip()]
        payload["cards"] = kept
        payload["ts"] = fl.now_iso()
        payload["pruned_shells"] = item["ids"]
        fl.write_json(fl.lane_file(ROOT, node), payload)
        item["acted"] = True
        item["kept"] = len(kept)
        item["verdict"] = "PRUNED"
    return item


def _quiet(*_a, **_k):
    return None


def check_deps(apply_):
    item = {"check": "deps", "missing": [], "acted": False}
    try:
        import env_selfheal
    except Exception as e:
        item["verdict"] = "SKIP"
        item["note"] = "env_selfheal unavailable: %s" % e
        return item
    missing = [t for t in env_selfheal.DEPS if not env_selfheal.have(t)]
    # `python` is a Windows-only name; posix boxes ship `python3` and the executor
    # already rewrites python3<->python both ways (lane_agent D-WIN-PY3). Reporting
    # it missing on a Mac is a false alarm that would look like a real install fix.
    if os.name != "nt" and "python3" in (os.environ.get("PATH") or "") and \
            __import__("shutil").which("python3"):
        missing = [t for t in missing if t != "python"]
    item["missing"] = missing
    if not missing:
        item["verdict"] = "OK"
        return item
    if not apply_:
        item["verdict"] = "WOULD-INSTALL"
        return item
    healed = []
    for tool in missing:
        try:
            # ensure() returns (ok, detail). Wrapping it in bool() made every install
            # "succeed" (a non-empty tuple is always true) - the first bm-m run reported
            # INSTALLED for a tool it never installed.
            ok, detail = env_selfheal.ensure(tool, log=_quiet)
            healed.append({"tool": tool, "ok": bool(ok), "detail": str(detail)[:200]})
        except Exception as e:
            healed.append({"tool": tool, "ok": False, "err": str(e)[:200]})
    item["acted"] = True
    item["results"] = healed
    item["verdict"] = "INSTALLED" if all(h["ok"] for h in healed) else "INSTALL-PARTIAL"
    return item


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default=os.environ.get("FLUX_NODE", "").strip())
    ap.add_argument("--apply", action="store_true", help="perform repairs (default dry-run)")
    ap.add_argument("--only", default="", help="comma list: reload,shells,deps")
    ap.add_argument("--out", default="",
                    help="fixed receipt path (relative to repo root); default is timestamped")
    a = ap.parse_args()

    node = a.node or os.environ.get("COMPUTERNAME", "").strip().lower()
    if not node:
        print("E-NONODE: pass --node <id> (the master's card does)")
        return 2
    only = {x.strip() for x in a.only.split(",") if x.strip()}

    checks = []
    if not only or "reload" in only:
        checks.append(check_reload(node, a.apply))
    if not only or "shells" in only:
        checks.append(check_shells(node, a.apply))
    if not only or "deps" in only:
        checks.append(check_deps(a.apply))

    # dry-run must not claim health: "would prune" is an open defect, not a green
    # (2026-11-06 假绿复盘: a report that says OK while a repair is pending is a lie).
    good = {"OK"} if not a.apply else {"OK", "RELOADED", "PRUNED", "INSTALLED"}
    verdict = "SELF-OK" if all(c.get("verdict") in good for c in checks) else "SELF-GAPS"
    receipt = {"node": node, "ts": fl.now_iso(), "mode": "apply" if a.apply else "dry-run",
               "verdict": verdict, "checks": checks}
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    if a.out:
        path = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out.replace("/", os.sep))
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    else:
        path = os.path.join(RECEIPT_DIR, "self-improve-%s-%s.json" % (node, stamp))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": verdict, "receipt": os.path.relpath(path, ROOT),
                      "checks": [(c["check"], c.get("verdict")) for c in checks]},
                     ensure_ascii=False))
    return 0 if verdict == "SELF-OK" else 1


if __name__ == "__main__":
    sys.exit(main())