# -*- coding: utf-8 -*-
"""fork_close.py - 一台机自己收口它与本仓 origin/main 的分叉。

Why: poke worker 只做 `merge --ff-only`（fleet-hot-sync 也禁 rebase，C-20261104 硬法）。
一台机一旦 ahead>0（本地攒了记账提交），ff 永远失败 -> 它永远拉不到新卡新码，
表面"有卡"实际空转（bm-b 实测 ahead 450 / behind 295）。收口必须由它自己做，
主控禁跨机执行。

Safety first: --apply only when EVERY ahead commit touches nothing but bookkeeping
paths. One real artifact commit and the tool refuses, listing the files - we never
trade a delivered product for a clean history.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Paths that only record state: losing these local commits costs nothing because the
# authoritative copy is rebuilt from the queue/receipts on origin.
BOOKKEEPING = (
    "cph4/fleet/state/",
    "cph4/fleet/lanes/",
    "cph4/fleet/radar/",
    "cph4/fleet/chief/",
    "cph4/fleet/sync/",
    "cph4/fleet/memory-slim/",
    "cph4/fleet/queue-receipts/",
    "cph4/fleet/dispatcher/",
    "cph4/fleet/PRODUCTION-QUEUE.jsonl",
    "cph4/fleet/PRODUCTION-BACKLOG.jsonl",
    "cph4/fleet/MASTER-SCREEN.md",
    "cph4/fleet/DAY-PLAN.md",
    "cph4/fleet/HANDOFF.md",
)
BOOKKEEPING_EXT = (".md", ".json", ".jsonl", ".log", ".db")


def sh(args, timeout=120):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def ahead_commits(base="origin/main"):
    rc, out, _ = sh(["git", "rev-list", "%s..HEAD" % base])
    return out.splitlines() if rc == 0 and out else []


def touched_paths(commits):
    if not commits:
        return []
    rc, out, _ = sh(["git", "diff", "--name-only", "%s..HEAD" % "origin/main"])
    return [x for x in out.splitlines() if x.strip()]


def classify(paths):
    book, real = [], []
    for p in paths:
        if p.startswith(BOOKKEEPING) or (p.startswith("cph4/fleet/") and
                                         p.endswith(BOOKKEEPING_EXT)):
            book.append(p)
        else:
            real.append(p)
    return book, real


def close_out(root=None, base="origin/main", apply_=False, fetch=True):
    """Close this repo's fork if - and only if - every ahead commit is bookkeeping.

    Returns a dict so callers (CLI and fleet_agent's remote `sync` action) share one
    safety rule instead of growing a second, looser implementation.
    """
    global ROOT
    if root:
        ROOT = root
    res = {"root": ROOT, "base": base, "applied": False}
    if fetch:
        rc, _, err = sh(["git", "fetch", "--quiet", "origin", "main"], timeout=180)
        if rc != 0:
            res.update(verdict="E-FETCH", detail=err[:200])
            return res
    brc, behind, _ = sh(["git", "rev-list", "--count", "HEAD..%s" % base])
    if brc != 0:
        res.update(verdict="E-NOBASE", detail="%s missing" % base)
        return res
    commits = ahead_commits(base)
    paths = touched_paths(commits)
    book, real = classify(paths)
    res.update(ahead=len(commits), behind=int(behind or 0), paths=len(paths),
               bookkeeping=len(book), real=len(real), real_paths=real[:20])
    if not commits:
        rc, out, err = sh(["git", "merge", "--ff-only", base])
        res.update(verdict="FF-OK" if rc == 0 else "FF-FAIL",
                   applied=rc == 0, detail=(out or err)[:200])
        return res
    if real:
        res.update(verdict="REFUSE-NON-BOOKKEEPING",
                   detail="ahead commits carry real files; deliver or merge them properly")
        return res
    if not apply_:
        res.update(verdict="WOULD-CLOSE")
        return res
    rc, out, err = sh(["git", "reset", "--mixed", base])
    if rc != 0:
        res.update(verdict="E-RESET", detail=(err or out)[:200])
        return res
    rc2, out2, err2 = sh(["git", "merge", "--ff-only", base])
    res.update(verdict="CLOSED" if rc2 == 0 else "CLOSED-FF-FAIL", applied=rc == 0,
               detail=(out2 or err2)[:160])
    return res


STATE_DIR = os.path.join(ROOT, "cph4", "fleet", "state")



def _node_id():
    """Resolve the fleet node id, not the hostname (hostname put bm-m data under
    'junshengsundeMacBook-Pro' and no consumer could match it)."""
    for k in ("FLUX_NODE", "NODE"):
        v = (os.environ.get(k) or "").strip()
        if v:
            return v
    try:
        cfg = json.load(open(os.path.join(ROOT, "Tools", "fleet-nodes.json"), encoding="utf-8-sig"))
        here = os.path.abspath(ROOT).lower().replace("\\", "/")
        for n in cfg.get("nodes") or []:
            r = str(n.get("root") or "").lower().replace("\\", "/").rstrip("/")
            if r and (r == here or here.endswith(r.split("/")[-1])):
                if r.split("/")[-1].lower() in here:
                    return str(n.get("id"))
    except Exception:
        pass
    import socket
    h = socket.gethostname().lower()
    return "bm-m" if "macbook" in h else h.split(".")[0]


def write_status(res):
    """Persist fork state so other stages can judge it without re-running git.

    Without this file every consumer (root_cause R6, ceo_pilot CLS-1) reported
    UNVERIFIED and the divergence stayed invisible - the box looked merely "slow".
    """
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        p = os.path.join(STATE_DIR, "fork-status.json")
        prev = {}
        try:
            with open(p, encoding="utf-8") as f:
                prev = json.load(f) or {}
        except Exception:
            prev = {}
        nodes = prev.get("nodes") or {}
        node = _node_id()
        nodes[node] = {"ahead": int(res.get("ahead") or 0),
                       "behind": int(res.get("behind") or 0),
                       "real": int(res.get("real") or 0),
                       "verdict": res.get("verdict"),
                       "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "nodes": nodes,
               "note": "只有本机条目由本机写；别机数据由各自上报，缺失即未知"}
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="perform the close-out")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--root", default="", help="repo root (defaults to this script's repo)")
    a = ap.parse_args()
    r = close_out(root=(a.root or None), base=a.base, apply_=a.apply)
    write_status(r)
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r["verdict"] in ("FF-OK", "CLOSED", "WOULD-CLOSE", "ALREADY-CLEAN") else 1


if __name__ == "__main__":
    sys.exit(main())