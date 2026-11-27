#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ri_dept.py - 研究创新席：登记、工单状态机、体检、清算、供卡。

为什么（2026-11-02 CEO 令）：每个子公司要有自己的研究创新部门管本业务的创新/调研/赋能/工具，
实验室管更整体更宏大的生产力。但"创新"最容易变成写文档，所以这里只认三件事：
  1) 席位边界是路径白名单（组级不许写 Tools/fleet）；
  2) 一条活只有四种状态，PROBE 必须有能跑的命令或在盘的产物；
  3) 记分只有采纳率——ADOPTED 必须指向真的用了它的卡/回执。

章程：cph4/fleet/RI-DEPT-v1.md；登记：cph4/fleet/ri/registry.json。
本工具被 flux_check.py 的 I17/I18/I19 直接调用，逻辑只此一份。

用法：
  python3 ri_dept.py status
  python3 ri_dept.py check [--json]
  python3 ri_dept.py new --seat ri-game --title "10 秒爽点" --hypothesis "..." --source URL
  python3 ri_dept.py brief --seat ri-content --file path/to/brief.md
  python3 ri_dept.py probe --id RI-C-001 --cmd "python3 Tools/ri/content/x.py" --evidence <path>
  python3 ri_dept.py adopt --id RI-C-001 --ref card:R-XXX
  python3 ri_dept.py kill  --id RI-C-001 --reason "..."
  python3 ri_dept.py settle [--dry]
  python3 ri_dept.py feed
Exit: 0 = ok, 2 = violations, 1 = tool failure.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
RI = os.path.join(FLEET, "ri")
REGISTRY = os.path.join(RI, "registry.json")
PRODUCTS = os.path.join(FLEET, "products")
PROPOSALS = os.path.join(RI, "PROPOSALS.json")

STAGES = ["IDEA", "SCOUT", "PROBE", "ADOPTED", "KILLED"]
OPEN_STAGES = ("IDEA", "SCOUT")
LIVE_STAGES = ("IDEA", "SCOUT", "PROBE")
REQUIRED = ("id", "group", "level", "status", "created", "owner", "lane",
            "scope", "writes", "forbid", "cadence", "acceptance", "kpi", "supersedes")


def jload(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def jdump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def today():
    return date.today().isoformat()


def age_days(stamp):
    """Age in days from an ISO date/datetime string; None if unparseable."""
    if not stamp:
        return None
    try:
        s = str(stamp).replace("Z", "").strip()
        if "T" in s or " " in s:
            s = s.replace(" ", "T").split(".")[0]
            d = datetime.fromisoformat(s).date()
        else:
            d = date.fromisoformat(s[:10])
        return (date.today() - d).days
    except Exception:
        return None


def registry():
    return jload(REGISTRY, {}) or {}


def seats(reg=None):
    return list((reg if reg is not None else registry()).get("seats") or [])


def seat_of(sid, reg=None):
    for s in seats(reg):
        if s.get("id") == sid:
            return s
    return None


def seat_dir(seat):
    """目录名取席位后缀（ri-lab → lab），与 registry.writes 里的白名单路径一致，
    不能直接用 group：实验室的 group 是 platform，目录是 lab。"""
    sid = str(seat.get("id") or "")
    name = sid[3:] if sid.startswith("ri-") else (seat.get("group") or sid)
    return os.path.join(RI, name)


def tickets(seat):
    d = os.path.join(seat_dir(seat), "tickets")
    out = []
    if not os.path.isdir(d):
        return out
    for n in sorted(os.listdir(d)):
        if not n.endswith(".json"):
            continue
        t = jload(os.path.join(d, n), None)
        if isinstance(t, dict):
            t["_path"] = os.path.join(d, n)
            out.append(t)
    return out


def all_tickets(reg=None):
    out = []
    for s in seats(reg):
        out.extend(tickets(s))
    return out


# ------------------------------------------------------------------ checks
def check_seats():
    """I17：active 产品组都有席位，且登记字段齐全、一进一出有交代。"""
    reg = registry()
    if not reg:
        return ["registry:missing"]
    bad = []
    ss = seats(reg)
    if not ss:
        bad.append("registry:no-seats")
    ids = [s.get("id") for s in ss]
    for i in set(x for x in ids if ids.count(x) > 1):
        bad.append("seat:%s:duplicate-id" % i)
    for s in ss:
        for k in REQUIRED:
            if s.get(k) in (None, "", [], {}):
                bad.append("seat:%s:missing-%s" % (s.get("id"), k))
        if s.get("level") not in ("group", "platform"):
            bad.append("seat:%s:bad-level" % s.get("id"))
        if s.get("status") not in ("ACTIVE", "PROXY", "PAUSED"):
            bad.append("seat:%s:bad-status" % s.get("id"))
        kpi = s.get("kpi") or {}
        if not (0 < float(kpi.get("adoption_rate_min") or 0) <= 1):
            bad.append("seat:%s:kpi-not-a-rate" % s.get("id"))
    # active 产品组必须有人管创新
    if os.path.isdir(PRODUCTS):
        for n in sorted(os.listdir(PRODUCTS)):
            if not n.endswith((".yaml", ".yml")):
                continue
            txt = open(os.path.join(PRODUCTS, n), encoding="utf-8", errors="ignore").read()
            pid = (re.search(r"^product:\s*(\S+)", txt, re.M) or [None, None])[1]
            st = (re.search(r"^status:\s*(\S+)", txt, re.M) or [None, ""])[1].strip("'\"")
            if not pid or st != "active":
                continue
            cover = [s for s in ss if s.get("group") == pid and s.get("status") in ("ACTIVE", "PROXY")]
            if not cover:
                bad.append("product:%s:no-ri-seat" % pid)
    return bad


ALLOWED_GROUP = ("cph4/fleet/ri/", "Tools/ri/")
ALLOWED_PLATFORM = ("Tools/fleet", "cph4/fleet/lab", "cph4/fleet/ri/lab")
PLATFORM_CORE = ("Tools/fleet",)


def check_scope():
    """I18：组级席不许写平台路径；forbid 不许出现在 writes；工单不许碰平台核心。"""
    bad = []
    for s in seats():
        w = [str(x) for x in (s.get("writes") or [])]
        f = [str(x) for x in (s.get("forbid") or [])]
        grp = str(s.get("group") or "")
        if not w:
            bad.append("seat:%s:no-writes" % s.get("id"))
        for p in w:
            if s.get("level") == "group":
                ok = p.startswith("cph4/fleet/ri/%s" % grp) or p.startswith("Tools/ri/%s" % grp)
                if not ok:
                    bad.append("seat:%s:write-out-of-scope:%s" % (s.get("id"), p))
            else:
                if not any(p.startswith(a) for a in ALLOWED_PLATFORM):
                    bad.append("seat:%s:write-out-of-scope:%s" % (s.get("id"), p))
        for p in f:
            if any(p.startswith(x) or x.startswith(p) for x in w):
                bad.append("seat:%s:forbid-inside-writes:%s" % (s.get("id"), p))
        # 工单声明的 touched 路径也要守边
        if s.get("level") == "group":
            for t in tickets(s):
                for p in (t.get("touches") or []):
                    if any(str(p).startswith(c) for c in PLATFORM_CORE):
                        bad.append("ticket:%s:touches-platform:%s" % (t.get("id"), p))
    return bad


def check_liveness():
    """I19：不许空转。简报超期、IDEA/SCOUT 超期、PROBE 过截止日、ADOPTED 无采纳凭据。"""
    bad = []
    for s in seats():
        cd = s.get("cadence") or {}
        brief_days = int(cd.get("brief_days") or 7)
        probe_days = int(cd.get("probe_deadline_days") or 45)
        created_age = age_days(s.get("created"))
        warmup = created_age is not None and created_age <= brief_days
        # 简报新鲜度（热身期内不判）
        d = os.path.join(seat_dir(s), "briefs")
        newest = None
        if os.path.isdir(d):
            for n in os.listdir(d):
                if n.endswith(".md"):
                    m = os.path.getmtime(os.path.join(d, n))
                    newest = m if newest is None or m > newest else newest
        if not warmup:
            if newest is None:
                bad.append("seat:%s:no-brief" % s.get("id"))
            elif (time.time() - newest) / 86400.0 > brief_days:
                bad.append("seat:%s:brief-stale>%dd" % (s.get("id"), brief_days))
        for t in tickets(s):
            st = t.get("stage")
            if st not in STAGES:
                bad.append("ticket:%s:bad-stage=%s" % (t.get("id"), st))
                continue
            a = age_days(t.get("touched") or t.get("opened"))
            if st in OPEN_STAGES and a is not None and a > 14:
                bad.append("ticket:%s:%s-stale>14d" % (t.get("id"), st))
            if st == "PROBE":
                if a is not None and a > probe_days:
                    bad.append("ticket:%s:probe-expired>%dd" % (t.get("id"), probe_days))
                ev = (t.get("probe") or {}).get("evidence")
                if not ev or not os.path.exists(os.path.join(ROOT, ev)):
                    bad.append("ticket:%s:probe-evidence-missing" % t.get("id"))
            if st == "ADOPTED" and not (t.get("adoption") or {}).get("ref"):
                bad.append("ticket:%s:adopted-without-ref" % t.get("id"))
    return bad


def metrics():
    """采纳率只算结算过的：ADOPTED / (ADOPTED + KILLED)。"""
    out = []
    for s in seats():
        ts = tickets(s)
        ad = len([t for t in ts if t.get("stage") == "ADOPTED"])
        ki = len([t for t in ts if t.get("stage") == "KILLED"])
        live = len([t for t in ts if t.get("stage") in LIVE_STAGES])
        rate = (float(ad) / (ad + ki)) if (ad + ki) else None
        floor = float((s.get("kpi") or {}).get("adoption_rate_min") or 0)
        out.append({"seat": s.get("id"), "group": s.get("group"), "status": s.get("status"),
                    "adopted": ad, "killed": ki, "live": live,
                    "adoption_rate": rate, "floor": floor,
                    "ok": (rate is None) or (rate >= floor)})
    return out


# ------------------------------------------------------------------ commands
def cmd_status(argv):
    rows = []
    for s in seats():
        ts = tickets(s)
        oldest = None
        for t in ts:
            if t.get("stage") in LIVE_STAGES:
                a = age_days(t.get("touched") or t.get("opened"))
                if a is not None and (oldest is None or a > oldest):
                    oldest = a
        rows.append({"seat": s.get("id"), "name": s.get("name"), "level": s.get("level"),
                     "status": s.get("status"), "tickets": len(ts), "oldest_live_d": oldest,
                     "writes": len(s.get("writes") or [])})
    m = metrics()
    print("研究创新席  %s  registry=%s" % (today(), os.path.relpath(REGISTRY, ROOT)))
    print("  %-12s %-6s %-7s %-4s %-6s %s" % ("seat", "level", "status", "卡", "最老", "采纳率"))
    for r, x in zip(rows, m):
        rate = "%.0f%%" % (x["adoption_rate"] * 100) if x["adoption_rate"] is not None else "-"
        print("  %-12s %-6s %-7s %-4d %-6s %s%s" % (
            r["seat"], r["level"], r["status"], r["tickets"],
            ("%dd" % r["oldest_live_d"]) if r["oldest_live_d"] is not None else "-",
            rate, "" if x["ok"] else "  (低于下限 %.0f%%)" % (x["floor"] * 100)))
    bad = check_seats() + check_scope() + check_liveness()
    print("  I17/I18/I19: %s" % ("PASS" if not bad else "FAIL %d 条" % len(bad)))
    for b in bad[:8]:
        print("   - %s" % b)
    return 0 if not bad else 2


def cmd_check(argv):
    bad = {"I17": check_seats(), "I18": check_scope(), "I19": check_liveness()}
    total = sum(len(v) for v in bad.values())
    n_feed = len(_write_proposals())      # 派生件，顺手刷新，保证派单方有得读
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "violations": total,
           "verdict": "PASS" if total == 0 else "FAIL", "checks": bad,
           "seats": metrics(), "proposals": n_feed}
    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("RI 体检 %s" % out["ts"])
        for k, v in bad.items():
            print("  %s %-6s %d" % ("OK  " if not v else "FAIL", k, len(v)))
            for x in v[:6]:
                print("       - %s" % x)
        print("VERDICT=%s  可派PROBE=%d" % (out["verdict"], n_feed))
    return 0 if total == 0 else 2


def _next_id(seat):
    ts = tickets(seat)
    prefix = "RI-%s-" % (str(seat.get("group") or "x")[:1].upper())
    nums = [int(t["id"].rsplit("-", 1)[-1]) for t in ts
            if str(t.get("id", "")).startswith(prefix) and t["id"].rsplit("-", 1)[-1].isdigit()]
    return "%s%03d" % (prefix, (max(nums) + 1) if nums else 1)


def _save_ticket(seat, t):
    jdump(os.path.join(seat_dir(seat), "tickets", t["id"] + ".json"), t)
    return t


def cmd_new(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seat", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--hypothesis", required=True)
    ap.add_argument("--source", action="append", default=[])
    ap.add_argument("--stage", default="SCOUT", choices=["IDEA", "SCOUT"])
    ap.add_argument("--due", default="")
    a = ap.parse_args(argv)
    seat = seat_of(a.seat)
    if not seat:
        print("没有这个席位：%s" % a.seat)
        return 1
    if a.stage == "SCOUT" and not a.source:
        print("SCOUT 必须给 --source（证据来源），否则就是空想")
        return 1
    t = {"id": _next_id(seat), "seat": seat["id"], "group": seat.get("group"),
         "title": a.title, "stage": a.stage, "hypothesis": a.hypothesis,
         "sources": a.source, "opened": today(), "touched": today(),
         "due": a.due, "touches": [], "probe": {}, "adoption": {}, "kill": {}}
    _save_ticket(seat, t)
    print("已开工单 %s [%s] %s" % (t["id"], t["stage"], t["title"]))
    return 0


def cmd_brief(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seat", required=True)
    ap.add_argument("--file", required=True)
    a = ap.parse_args(argv)
    seat = seat_of(a.seat)
    if not seat:
        print("没有这个席位：%s" % a.seat)
        return 1
    src = a.file if os.path.isabs(a.file) else os.path.join(ROOT, a.file)
    if not os.path.exists(src):
        print("简报源文件不存在：%s" % src)
        return 1
    body = open(src, encoding="utf-8").read()
    if len(body.strip()) < 80:
        print("简报太短（%d 字符），不像一份能给建议的东西" % len(body.strip()))
        return 1
    d = os.path.join(seat_dir(seat), "briefs")
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, "BRIEF-%s.md" % today())
    with open(dst, "w", encoding="utf-8") as f:
        f.write(body if body.endswith("\n") else body + "\n")
    print("已落简报 %s（%d 字符）" % (os.path.relpath(dst, ROOT), len(body)))
    return 0


def _find(tid):
    for s in seats():
        for t in tickets(s):
            if t.get("id") == tid:
                return s, t
    return None, None


def cmd_probe(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--cmd", default="")
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    seat, t = _find(a.id)
    if not t:
        print("没有这张工单：%s" % a.id)
        return 1
    ev = a.evidence if os.path.isabs(a.evidence) else os.path.join(ROOT, a.evidence)
    if not os.path.exists(ev):
        print("证据不在盘：%s（PROBE 必须给真产物，不能给计划）" % a.evidence)
        return 1
    t["stage"] = "PROBE"
    t["probe"] = {"cmd": a.cmd, "evidence": os.path.relpath(ev, ROOT), "note": a.note}
    t["touched"] = today()
    _save_ticket(seat, t)
    print("%s → PROBE  证据=%s" % (t["id"], t["probe"]["evidence"]))
    return 0


def cmd_adopt(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--ref", required=True)
    a = ap.parse_args(argv)
    seat, t = _find(a.id)
    if not t:
        print("没有这张工单：%s" % a.id)
        return 1
    if not (t.get("probe") or {}).get("evidence"):
        print("还没过 PROBE，不能直接 ADOPTED（先给能跑的证据）")
        return 1
    t["stage"] = "ADOPTED"
    t["adoption"] = {"ref": a.ref, "at": today()}
    t["touched"] = today()
    _save_ticket(seat, t)
    print("%s → ADOPTED  采纳方=%s" % (t["id"], a.ref))
    return 0


def cmd_kill(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--reason", required=True)
    a = ap.parse_args(argv)
    seat, t = _find(a.id)
    if not t:
        print("没有这张工单：%s" % a.id)
        return 1
    t["stage"] = "KILLED"
    t["kill"] = {"reason": a.reason, "at": today()}
    t["touched"] = today()
    _save_ticket(seat, t)
    print("%s → KILLED  %s" % (t["id"], a.reason))
    return 0


def cmd_settle(argv):
    dry = "--dry" in argv
    killed = []
    for s in seats():
        probe_days = int((s.get("cadence") or {}).get("probe_deadline_days") or 45)
        for t in tickets(s):
            st = t.get("stage")
            a = age_days(t.get("touched") or t.get("opened"))
            if a is None:
                continue
            reason = None
            if st in OPEN_STAGES and a > 14:
                reason = "auto-settle: %s 停留 %d 天无 probe" % (st, a)
            elif st == "PROBE" and a > probe_days:
                reason = "auto-settle: PROBE %d 天未被采纳（上限 %d）" % (a, probe_days)
            if not reason:
                continue
            killed.append((s, t, reason))
            if not dry:
                t["stage"] = "KILLED"
                t["kill"] = {"reason": reason, "at": today()}
                t["touched"] = today()
                _save_ticket(s, t)
    print("清算：%d 张到期%s" % (len(killed), "（dry）" if dry else ""))
    for s, t, r in killed:
        print("  - %s  %s" % (t.get("id"), r))
    return 0


def _write_proposals():
    """只产 PROPOSALS.json，不写队列（I7 单写入口）。"""
    items = []
    for s in seats():
        if s.get("status") == "PAUSED":
            continue
        for t in tickets(s):
            if t.get("stage") != "PROBE":
                continue
            p = t.get("probe") or {}
            if not p.get("cmd") or not p.get("evidence"):
                continue
            items.append({"ticket": t.get("id"), "seat": s.get("id"), "group": s.get("group"),
                          "title": t.get("title"), "cmd": p["cmd"], "evidence": p["evidence"],
                          "note": p.get("note") or "", "since": t.get("touched")})
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "count": len(items), "items": items,
           "note": "派单方从此处择取；RI 不直接写队列（I7）。"}
    jdump(PROPOSALS, out)
    return items


def cmd_feed(argv):
    items = _write_proposals()
    print("PROPOSALS.json: %d 项可派" % len(items))
    for i in items[:10]:
        print("  - %s %s：%s" % (i["ticket"], i["group"], i["cmd"][:70]))
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    fn = {"status": cmd_status, "check": cmd_check, "new": cmd_new, "brief": cmd_brief,
          "probe": cmd_probe, "adopt": cmd_adopt, "kill": cmd_kill,
          "settle": cmd_settle, "feed": cmd_feed}.get(cmd)
    if not fn:
        print("未知命令：%s" % cmd)
        print(__doc__)
        return 1
    try:
        return fn(rest)
    except SystemExit as e:
        return int(e.code or 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))