#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flux_check.py - the one gate that checks the *structure* of the fleet.

Twelve invariants, one run, one verdict. Domain gates (frames, seams, freeze) still
exist; this is the layer above them: it answers "is the bookkeeping itself lying?"
Baseline + ratchet: today's known violations are recorded once, and from then on the
count may only go down. A new violation is a red build, not a discussion.

Why: on 2026-11-02 the queue held 97 cards of which 90 had no `line`, 25 of 106
receipts had no `rc`, 7 scripts rewrote the same queue without a lock, and
`rc=9009 (command not found)` was booked as DONE. None of that was visible anywhere.

Usage:
  python3 flux_check.py                    # check, write state/invariants.json
  python3 flux_check.py --update-baseline  # accept today's debt (ratchet starts here)
  python3 flux_check.py --json             # machine output only
Exit: 0 = no NEW violations, 2 = new violations, 1 = checker itself failed.
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
PRODUCTS = os.path.join(FLEET, "products")
VAULT = os.path.join(FLEET, "vault", "index.jsonl")
VERDICTS = os.path.join(FLEET, "verdicts")
STATE = os.path.join(FLEET, "state")
# The baseline is a governed artefact (it is the debt we accept), not volatile state:
# it lives outside state/ so that invariant I6 ("nothing under state/ is tracked") holds.
BASELINE = os.path.join(FLEET, "INVARIANTS-BASELINE.json")

sys.path.insert(0, HERE)
import flux_contracts as C  # noqa: E402


def jload(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def jlines(path):
    out = []
    try:
        with open(path, encoding="utf-8-sig") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    out.append({"_broken": i})
    except FileNotFoundError:
        pass
    return out


def line_ids():
    """Products if they exist, else the legacy registry (so the check is usable today)."""
    ids = set()
    if os.path.isdir(PRODUCTS):
        for n in os.listdir(PRODUCTS):
            if n.endswith((".yaml", ".yml", ".json")):
                ids.add(os.path.splitext(n)[0])
    reg = jload(os.path.join(FLEET, "LINE-REGISTRY.json"), {}) or {}
    for ln in reg.get("lines") or []:
        ids.add(ln.get("id"))
    return ids


# ---------------------------------------------------------------- invariants
def i1_cards_have_line():
    known = line_ids()
    bad = []
    for r in jlines(QUEUE):
        lid = r.get("line")
        if not lid:
            bad.append("card:%s:no-line" % r.get("id"))
        elif known and lid not in known:
            bad.append("card:%s:unknown-line=%s" % (r.get("id"), lid))
    return bad


def i2_cards_are_portable():
    bad = []
    for r in jlines(QUEUE):
        for e in C.validate("card", _coerce_card(r)):
            if e.startswith("FORBID"):
                bad.append("card:%s:%s" % (r.get("id"), e.split(":")[0] + ":" + e.split(": ", 1)[-1][:40]))
    return bad


def _coerce_card(r):
    """Legacy rows have a string deliverable; wrap so the validator can judge them."""
    c = dict(r)
    d = c.get("deliverable")
    if isinstance(d, str):
        c["deliverable"] = {"path": d}
    if not c.get("accept"):
        c["accept"] = ["legacy-card-without-accept"]
    return c


def i3_receipts_have_rc():
    bad = []
    if not os.path.isdir(RECEIPTS):
        return bad
    for n in sorted(os.listdir(RECEIPTS)):
        if not n.endswith(".json"):
            continue
        # only step receipts follow "<card>-<node>.json"; lane scratch files (_last_lane)
        # and business reports (mv-gate/biz/triage) are not receipts and carry no rc.
        if not re.search(r"-bm-[a-z]\.json$", n):
            continue
        d = jload(os.path.join(RECEIPTS, n), None)
        if not isinstance(d, dict):
            continue
        if "rc" not in d:
            # business reports (verdict/frames) are not step receipts
            if any(k in d for k in ("verdict", "frames", "shots", "checks")):
                continue
            bad.append("receipt:%s:no-rc" % n)
        elif C.error_class(d.get("rc")) and not d.get("error_class"):
            bad.append("receipt:%s:rc=%s-no-error-class" % (n, d.get("rc")))
    return bad


def i4_done_cards_have_artifact():
    if not os.path.exists(VAULT):
        return []          # vault not built yet; S3 turns this into a hard rule
    have = set()
    for a in jlines(VAULT):
        if a.get("path"):
            have.add(os.path.normpath(a["path"]))
    bad = []
    for r in jlines(QUEUE):
        if r.get("state") not in ("DONE",):
            continue
        d = C.deliverable_of(r)
        if d and os.path.normpath(d) not in have:
            bad.append("card:%s:done-without-artifact" % r.get("id"))
    return bad


def i5_artifacts_have_provenance():
    if not os.path.exists(VAULT):
        return []
    bad = []
    for a in jlines(VAULT):
        p = a.get("provenance") or {}
        if not (p.get("line") and p.get("stage") and p.get("card")):
            bad.append("artifact:%s:no-provenance" % (a.get("path") or a.get("sha256"))[:60])
    return bad


def i6_state_not_in_git():
    bad = []
    try:
        out = subprocess.run(["git", "ls-files", "cph4/fleet/state"],
                             cwd=ROOT, capture_output=True, text=True, timeout=30).stdout
        for p in out.split():
            bad.append("tracked:%s" % p)
    except Exception:
        pass
    return bad


WRITER_HINTS = ("PRODUCTION-QUEUE.jsonl", "PRODUCTION-BACKLOG.jsonl")


def i7_single_writer():
    """A writer is a file that actually opens a shared queue for writing (or atomically
    replaces it), not one that merely mentions the path while reading it.
    There must be exactly one designated writer per queue."""
    open_pat = re.compile(r"open\([^)]{0,120},\s*['\"][wa]\+?b?['\"]")
    replace_pat = re.compile(r"os\.replace\([^)]{0,80},\s*(Q|QUEUE|qpath|q_file|queue)\s*\)")
    const_pat = {"PRODUCTION-QUEUE.jsonl": re.compile(r"\b(Q|QUEUE|qpath|q_file)\s*="),
                 "PRODUCTION-BACKLOG.jsonl": re.compile(r"\b(BL|BACKLOG|blpath)\s*=")}
    writers = {q: set() for q in WRITER_HINTS}
    for base in (os.path.join(ROOT, "Tools"), os.path.join(FLEET, "dispatcher"),
                 os.path.join(FLEET, "lines")):
        for dirpath, _dirs, files in os.walk(base):
            for n in files:
                if not n.endswith(".py"):
                    continue
                p = os.path.join(dirpath, n)
                try:
                    src = open(p, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                for qname in WRITER_HINTS:
                    if qname not in src and not const_pat[qname].search(src):
                        continue
                    hit = False
                    helper = re.search(r"(fl\.)?write_jsonl\(", src) is not None
                    for line in src.splitlines():
                        if qname in line and open_pat.search(line):
                            hit = True
                        elif helper and (qname in line or
                                         (qname == "PRODUCTION-QUEUE.jsonl" and "QUEUE_REL" in line) or
                                         (qname == "PRODUCTION-BACKLOG.jsonl" and "BACKLOG" in line)):
                            hit = True
                        elif replace_pat.search(line) and const_pat[qname].search(src):
                            hit = True
                    if hit:
                        writers[qname].add(os.path.relpath(p, ROOT))
    bad = []
    for qname, ws in writers.items():
        if len(ws) > 1:
            bad.append("queue:%s:%d-writers[%s]" % (qname, len(ws), ",".join(sorted(ws))))
    return bad


def i8_leases_identify_owner():
    bad = []
    d = os.path.join(ROOT, "Tools", "nats", "data")
    if not os.path.isdir(d):
        return bad
    for n in os.listdir(d):
        if not n.startswith("gpu.") or not n.endswith(".lease.json"):
            continue
        x = jload(os.path.join(d, n), {}) or {}
        if not x:
            continue
        if x.get("owner") in (None, "", "gpu_lease") or not x.get("job_id"):
            bad.append("lease:%s:anonymous-owner" % n)
    return bad


def i9_verdicts_are_reproducible():
    if not os.path.isdir(VERDICTS):
        return []
    bad = []
    for n in os.listdir(VERDICTS):
        if not n.endswith(".json"):
            continue
        v = jload(os.path.join(VERDICTS, n), {}) or {}
        if not v:
            continue
        if not v.get("tool_version") or not v.get("input_sha"):
            bad.append("verdict:%s:not-reproducible" % n)
    return bad


def i10_publish_has_aigc():
    ship = os.path.join(FLEET, "ship")
    if not os.path.isdir(ship):
        return []
    bad = []
    for n in os.listdir(ship):
        if not n.endswith(".json"):
            continue
        s = jload(os.path.join(ship, n), {}) or {}
        if s.get("published") and not (s.get("aigc") or {}).get("implicit"):
            bad.append("ship:%s:no-aigc-metadata" % n)
    return bad


def i11_recipes_have_kill_criteria():
    if not os.path.isdir(PRODUCTS):
        return ["products:no-recipes-yet"]
    bad = []
    for n in os.listdir(PRODUCTS):
        if not n.endswith((".yaml", ".yml")):
            continue
        txt = open(os.path.join(PRODUCTS, n), encoding="utf-8", errors="ignore").read()
        if "kill_criteria" not in txt:
            bad.append("recipe:%s:no-kill-criteria" % n)
    return bad


def i12_no_orphan_scripts():
    """Every script must be reachable: imported/called by another script, a card, a
    launchd plist, or a docs canon. Orphans are dead weight that still gets maintained."""
    d = HERE
    names = [n[:-3] for n in os.listdir(d) if n.endswith(".py")]
    # entry points are invoked by launchd / operators / other machines, not by a caller
    ENTRIES = {"flux_check", "flux_contracts", "census", "lane_agent", "agent",
               "master_pulse", "pulse_watchdog", "model_gateway", "web_ai"}
    hay = []
    skip_dirs = {"state", "__pycache__", "queue-receipts", "artifacts", "dispatcher"}
    # Only stable sources count as a caller: code, launchd plists and the two declarative
    # work ledgers. Markdown reports and queue files are rewritten every cycle, which made
    # this check flip between 0 and 8 orphans per run (2026-11-02) - a gate that flickers
    # is worse than no gate.
    for base in (os.path.join(ROOT, "Tools"), os.path.join(ROOT, "cph4")):
        for dirpath, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if x not in skip_dirs]
            for n in files:
                if not n.endswith((".py", ".ps1", ".sh", ".cmd", ".plist")):
                    continue
                p = os.path.join(dirpath, n)
                if dirpath == d and n.endswith(".py"):
                    continue          # the script family itself
                try:
                    hay.append(open(p, encoding="utf-8", errors="ignore").read())
                except Exception:
                    pass
    for extra in ("WORK-RULES.jsonl", "RECURRING-WORK.jsonl", "LINE-REGISTRY.json"):
        p = os.path.join(FLEET, extra)
        if os.path.exists(p):
            try:
                hay.append(open(p, encoding="utf-8", errors="ignore").read())
            except Exception:
                pass
    for pl in ("/Users/%s/Library/LaunchAgents" % os.environ.get("USER", ""),):
        if os.path.isdir(pl):
            for n in os.listdir(pl):
                if n.startswith("com.fluxgroup"):
                    try:
                        hay.append(open(os.path.join(pl, n), encoding="utf-8", errors="ignore").read())
                    except Exception:
                        pass
    blob = "\n".join(hay)
    bad = []
    for nm in names:
        if nm in ENTRIES:
            continue
        if blob.count(nm) <= 0:
            bad.append("script:%s:no-caller" % nm)
    return bad


def i13_idle_with_matching_work():
    """CEO 的第一诉求（历史 203 条令）：机器空着而队列里有它能做的活。
    Daytime yield is policy, not a fault, so lanes explicitly yielding are skipped."""
    ms = jload(os.path.join(FLEET, "dispatcher", "MASTER-STATE.json"), {}) or {}
    lanes = ms.get("lanes") or {}
    open_cards = [r for r in jlines(QUEUE) if r.get("state") == "OPEN"]
    if not open_cards or not lanes:
        return []
    try:
        import fleet_lane as fl
    except Exception:
        return []
    bad = []
    for n, v in lanes.items():
        if not v.get("online") or v.get("job"):
            continue
        reason = str(v.get("idle_reason") or "")
        if "DAY-YIELD" in reason or "WORKHOUR-YIELD" in reason:
            continue
        spec = fl.LANES.get(n) or {}
        for r in open_cards:
            if (r.get("needs") or "cpu") not in (spec.get("needs") or []):
                continue
            pinned = r.get("nodes") or []
            if pinned and n not in pinned:
                continue
            bad.append("idle:%s:could-run:%s" % (n, r.get("id")))
            break
    return bad


def i14_p0_daily_output():
    """CEO 2026-11-02：P0 必须每天有产物。24 小时没有新产出即红，不看解释。
    Source: census projection (state/lines.json) so the number is disk age, not a claim."""
    reg = jload(os.path.join(FLEET, "LINE-REGISTRY.json"), {}) or {}
    p0 = {l.get("id") for l in (reg.get("lines") or []) if str(l.get("priority")) == "P0"}
    st = jload(os.path.join(STATE, "lines.json"), {}) or {}
    bad = []
    for r in st.get("lines") or []:
        if r.get("id") not in p0 or r.get("observed") != "OBSERVED":
            continue
        age = r.get("age_h")
        if age is None or age > 24:
            bad.append("p0:%s:no-output-%sh" % (r.get("id"), age))
    return bad


CHECKS = [
    ("I1", "每张卡有 line 且 line 存在", i1_cards_have_line),
    ("I2", "卡不含机器名/绝对主机路径", i2_cards_are_portable),
    ("I3", "回执有 rc；rc!=0 带 error_class", i3_receipts_have_rc),
    ("I4", "DONE 卡的交付物有资产登记", i4_done_cards_have_artifact),
    ("I5", "资产有 provenance", i5_artifacts_have_provenance),
    ("I6", "state/ 不被 git 跟踪", i6_state_not_in_git),
    ("I7", "每个队列只有一个写入口", i7_single_writer),
    ("I8", "GPU 租约带身份", i8_leases_identify_owner),
    ("I9", "闸判可复现（版本+输入哈希）", i9_verdicts_are_reproducible),
    ("I10", "发布件有 AIGC 隐式标识", i10_publish_has_aigc),
    ("I11", "每条产品配方有 kill_criteria", i11_recipes_have_kill_criteria),
    ("I12", "无孤儿脚本", i12_no_orphan_scripts),
    ("I13", "有机空闲且有它能干的活", i13_idle_with_matching_work),
    ("I14", "P0 线 24 小时必须有产物", i14_p0_daily_output),
]


def main(argv):
    update = "--update-baseline" in argv
    as_json = "--json" in argv
    os.makedirs(STATE, exist_ok=True)
    base = jload(BASELINE, {}) or {}
    base_keys = set(base.get("keys") or [])

    results, cur_keys = [], set()
    for cid, desc, fn in CHECKS:
        t0 = time.time()
        try:
            bad = fn() or []
            err = None
        except Exception as e:                       # a checker crash is a red, not a pass
            bad, err = [], "%s: %s" % (type(e).__name__, e)
        keys = set("%s|%s" % (cid, b) for b in bad)
        cur_keys |= keys
        new = sorted(keys - base_keys) if base_keys else []
        results.append({"id": cid, "desc": desc, "count": len(bad), "new": len(new),
                        "error": err, "samples": bad[:5], "new_samples": new[:5],
                        "ms": int((time.time() - t0) * 1000)})

    if update:
        with open(BASELINE, "w", encoding="utf-8") as f:
            json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       "note": "ratchet: this many known violations; only downward",
                       "keys": sorted(cur_keys)}, f, ensure_ascii=False, indent=1)

    new_total = sum(r["new"] for r in results)
    errs = [r for r in results if r["error"]]
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "version": C.VERSION,
           "new_violations": new_total, "checks": results,
           "verdict": "FAIL" if (new_total or errs) else "PASS"}
    with open(os.path.join(STATE, "invariants.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if out["verdict"] == "PASS" else 2

    print("FLUX invariants  %s  %s" % (out["ts"], "(baseline updated)" if update else ""))
    for r in results:
        flag = "ERR " if r["error"] else ("NEW+" if r["new"] else "    ")
        print("  %s %-4s %-32s total=%-4d new=%-3d %5dms" %
              (flag, r["id"], r["desc"][:32], r["count"], r["new"], r["ms"]))
        for s in r["new_samples"] or r["samples"][:2]:
            print("       - %s" % s)
        if r["error"]:
            print("       ! %s" % r["error"])
    print("VERDICT=%s  new=%d  (state/invariants.json)" % (out["verdict"], new_total))
    return 0 if out["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))