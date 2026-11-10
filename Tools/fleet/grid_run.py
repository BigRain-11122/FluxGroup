#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grid_run.py - 自动化网格的执行器：按 cadence 跑到期项，不靠人记、不靠会话。

为什么（CEO 2026-11-10「把自动化颗粒度做细做全」）：
  此前自动化是"一堆脚本各自接在脉里"，颗粒度不可见：哪条需求由谁在多长时间内
  核对一次、失败了找谁，散在 200 个工具和几十个 pulse 阶段里。于是缺口只能靠
  demand_audit 事后发现，而且发现后也没有"谁在多久内必须动手"。

本器把「需求 → 检查项 → 频率 → 失败动作」做成一张机读网格
（cph4/fleet/AUTOMATION-GRID-v1.json），自己算到期、自己跑、自己记账、自己升级：

  kind=probe   跑一条命令，rc 0 正常 / 1 警告 / 2 失败
  kind=manual  人/会话判断项：到期写进 escalations，由会话轮处理（不假装自动）
  on_fail      card=写队列卡给执行机 / brain=交给本地大脑判 / ceo=进 CEO 收件箱

用法：
  python3 Tools/fleet/grid_run.py --plan        # 今天哪些到期（只读）
  python3 Tools/fleet/grid_run.py --apply       # 跑到期的项
  python3 Tools/fleet/grid_run.py --apply --force --only A1,F1
Exit: 0 全绿 / 1 有警告 / 2 有失败
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GRID = os.path.join(ROOT, "cph4", "fleet", "AUTOMATION-GRID-v1.json")
STATE = os.path.join(ROOT, "cph4", "fleet", "state", "grid-state.json")
ESC = os.path.join(ROOT, "cph4", "fleet", "state", "grid-escalations.jsonl")
BOARD = os.path.join(ROOT, "cph4", "fleet", "AUTOMATION-GRID.md")
sys.path.insert(0, HERE)


def now():
    return time.time()


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8-sig"))
    except Exception:
        return default


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def run_cmd(cmd, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, shell=isinstance(cmd, str), cwd=ROOT,
                           capture_output=True, text=True, timeout=timeout)
        out = ((p.stdout or "") + (p.stderr or "")).strip()
        return p.returncode, out[-600:], round(time.time() - t0, 1)
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT %ss" % timeout, round(time.time() - t0, 1)
    except Exception as exc:  # noqa: BLE001
        return 125, "%s: %s" % (type(exc).__name__, str(exc)[:120]), round(time.time() - t0, 1)


def escalate(item, status, msg, secs):
    """失败动作：写卡 / 留给大脑 / 进 CEO 收件箱。"""
    how = item.get("on_fail") or "log"
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "id": item["id"],
           "name": item.get("name"), "domain": item.get("domain"), "status": status,
           "msg": msg[:400], "how": how, "secs": secs}
    os.makedirs(os.path.dirname(ESC), exist_ok=True)
    with open(ESC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if how == "card":
        try:
            import fleet_lane as fl
            jid = "GRID-%s-%s" % (item["id"], datetime.now().strftime("%Y%m%dT%H%M"))
            fl.merge_jsonl(os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl"), [{
                "id": jid, "title": "[grid] %s 自愈：%s" % (item["id"], item.get("name")),
                "cmd": item.get("fix") or "python -c \"print('no fix defined')\"",
                "cwd": "", "requires": [], "deliverable": "cph4/fleet/reports/%s.md" % jid.lower(),
                "needs": "cpu", "nodes": ["bm-m"], "prio": "P1", "day_ok": True,
                "heavy": False, "rescue": item.get("rescue", False), "line": "fleet-ops",
                "ok_rc": [0], "created_by": "grid_run", "created_at": fl.now_iso(),
                "why": "网格项 %s 失败：%s" % (item["id"], msg[:200]), "state": "OPEN"}])
            rec["card"] = jid
        except Exception as exc:  # noqa: BLE001
            rec["card_error"] = str(exc)[:160]
    return rec


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    lock = os.path.join(ROOT, "cph4", "fleet", "state", "grid.lock")
    if a.apply and not a.force:
        try:
            if os.path.exists(lock) and now() - os.path.getmtime(lock) < 1800:
                print("[grid] 上一轮还在跑（lock 新鲜），本轮跳过", file=sys.stderr)
                return 0
            open(lock, "w").write(str(os.getpid()))
        except Exception:
            pass
    grid = load(GRID, {})
    items = grid.get("items") or []
    if not items:
        print("[grid] 没有网格定义：%s" % GRID, file=sys.stderr)
        return 2
    st = load(STATE, {})
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    t = now()
    due, rows = [], []
    for it in items:
        if not it.get("enabled", True):
            continue
        if only and it["id"] not in only:
            continue
        last = float((st.get(it["id"]) or {}).get("ts") or 0)
        cad = int(it.get("cadence_s") or 3600)
        is_due = a.force or (t - last >= cad)
        it["_last"] = last
        rows.append({"id": it["id"], "name": it.get("name"), "domain": it.get("domain"),
                     "cadence_s": cad, "due": is_due, "last": last,
                     "status": (st.get(it["id"]) or {}).get("status", "-")})
        if is_due:
            due.append(it)

    if a.plan or not a.apply:
        if a.json:
            print(json.dumps(rows, ensure_ascii=False))
        else:
            print("[grid] 共 %d 项，到期 %d 项" % (len(rows), len(due)))
            for r in due:
                print("  DUE  %-18s %-26s every %-6s last=%s" % (
                    r["id"], (r["name"] or "")[:26], "%ss" % r["cadence_s"],
                    datetime.fromtimestamp(r["last"]).strftime("%m-%d %H:%M") if r.get("last") else "never"))
        if not a.apply:
            return 0

    bad, warn, escs = 0, 0, []
    for it in due:
        kind = it.get("kind") or "probe"
        if kind == "manual":
            rec = escalate(it, "MANUAL", "轮到人工/会话判断：%s" % (it.get("accept") or ""), 0.0)
            st[it["id"]] = {"ts": now(), "status": "MANUAL", "msg": rec["msg"][:200]}
            escs.append(rec)
            continue
        rc, out, secs = run_cmd(it.get("cmd") or "", int(it.get("timeout_s") or 180))
        status = "OK" if rc in (it.get("ok_rc") or [0]) else ("WARN" if rc == 1 else "FAIL")
        if status == "FAIL" and it.get("fix"):
            rc2, out2, s2 = run_cmd(it["fix"], int(it.get("timeout_s") or 180))
            out = (out + " || FIX rc=%s %s" % (rc2, out2))[-600:]
            secs += s2
            if rc2 in (it.get("ok_rc") or [0]):
                status = "FIXED"
        st[it["id"]] = {"ts": now(), "status": status, "rc": rc, "secs": secs,
                        "msg": out[-300:]}
        if status == "FAIL":
            bad += 1
            escs.append(escalate(it, status, out, secs))
        elif status == "WARN":
            warn += 1
        print("[grid] %-18s %-6s %5.1fs %s" % (it["id"], status, secs, out[-100:].replace("\n", " ")))

    save(STATE, st)
    try:
        os.remove(lock)
    except Exception:
        pass
    # 一屏：只写异常与到期，不写成功学
    try:
        fails = [(k, v) for k, v in st.items() if v.get("status") in ("FAIL", "MANUAL")]
        nfail = sum(1 for _, v in fails if v.get("status") == "FAIL")
        nman = sum(1 for _, v in fails if v.get("status") == "MANUAL")
        nwarn = sum(1 for v in st.values() if v.get("status") == "WARN")
        lines = ["# 自动化网格 · %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "", "共 %d 项 · 运行 %d · 失败 %d · 警告 %d · 待判 %d" % (
                     len(items), len(st), nfail, nwarn, nman), ""]
        if fails:
            lines.append("## 需要动作")
            for k, v in fails[:25]:
                lines.append("- **%s** %s · %s" % (k, v.get("status"), (v.get("msg") or "")[:120]))
        else:
            lines.append("## 需要动作\n- 无：所有到期项正常")
        open(BOARD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    except Exception:
        pass
    if bad:
        return 2
    return 1 if warn else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
