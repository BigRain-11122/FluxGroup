#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_view.py - 主控一屏：对每台机、每个任务面了如指掌。

回答三个问题：
  1 每台机现在什么状态：能不能接活、有多少卡、最后回执多久前、本地模型通不通
  2 每个任务面卡在哪：59 道工序分别由谁承接、产物在不在、有没有产物契约
  3 哪些事必须主控出手：无主工序 / 无产物契约 / 有活没人干 / 队列堆积

数据全来自盘上事实（分片、回执、配置），不读心跳、不信自述。
用法：
  python3 Tools/fleet/fleet_view.py            # 人读一屏
  python3 Tools/fleet/fleet_view.py --json     # 机读
  python3 Tools/fleet/fleet_view.py --gaps     # 只看需要主控介入的
  python3 Tools/fleet/fleet_view.py --self-test
返回码：0 无需介入 / 1 有 GAP 需主控
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _base(root=None):
    return os.path.join(root or ROOT, "cph4", "fleet")


def _j(name, root=None, default=None):
    try:
        with open(os.path.join(_base(root), name), encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def _age_h(p):
    if not os.path.exists(p):
        return None
    return round((time.time() - os.path.getmtime(p)) / 3600, 1)


def _newest(paths):
    ts = [os.path.getmtime(p) for p in paths if os.path.exists(p)]
    return round((time.time() - max(ts)) / 3600, 1) if ts else None


def _alive(url, timeout=0.8):
    try:
        with urllib.request.urlopen(url + "/api/tags", timeout=timeout) as r:
            r.read(32)
        return True
    except Exception:
        return False


def snapshot(root=None, check_net=True):
    b = _base(root)
    stations = (_j("STATIONS.json", root) or {}).get("stations") or []
    tax = _j("TAXONOMY-v1.json", root) or {}
    products = (_j("PRODUCTS.json", root) or {}).get("products") or []
    teams = (_j("AGENT-TEAMS-v1.json", root) or {}).get("teams") or {}
    types = {t["id"]: t for t in tax.get("task_types") or []}
    smap = tax.get("stage_map") or {}

    machines, gaps = [], []
    for s in stations:
        sid = s["id"]
        q = _rows(os.path.join(b, "rt", sid, "queue.jsonl"))
        st = {}
        for r in q:
            st[r.get("state")] = st.get(r.get("state"), 0) + 1
        last_receipt = _newest(glob.glob(os.path.join(b, "rt", sid, "receipts", "*")))
        local = (s.get("local_model") or {})
        url = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"
        net = _alive(url) if check_net else None
        types_ok = sum(1 for t in types.values() if sid in (t.get("stations") or []))
        stages = sum(1 for p in products for stg in (p.get("stages") or [])
                     if sid in ((types.get((smap.get(p["id"]) or {}).get(stg)) or {}).get("stations") or []))
        row = {"station": sid, "machine": s.get("machine"), "status": s.get("status"),
               "blocked_scope": s.get("blocked_scope"), "slots": s.get("slots"),
               "shifts": s.get("shifts"), "seats": len(teams.get(sid) or []),
               "task_types": types_ok, "stages": stages,
               "queue": {"open": st.get("OPEN", 0), "running": st.get("RUNNING", 0),
                         "done": st.get("DONE", 0), "blocked": st.get("BLOCKED", 0),
                         "failed": st.get("FAILED", 0), "total": len(q)},
               "last_receipt_h": last_receipt,
               "local_model": local.get("model"), "model_alive": net}
        machines.append(row)
        if (s.get("status") or "") not in ("ready", "ready_paused", "online",
                                           "network_ok_not_registered"):
            gaps.append({"kind": "MACHINE-DOWN", "who": sid, "why": s.get("status")})
        if row["queue"]["open"] and (s.get("status") or "") not in ("ready", "ready_paused"):
            gaps.append({"kind": "WORK-QUEUED-NO-WORKER", "who": sid,
                         "why": "%d 张 OPEN 但机器状态 %s" % (row["queue"]["open"], s.get("status"))})
        if last_receipt is not None and last_receipt > 24 and q:
            gaps.append({"kind": "NO-RECEIPT-24H", "who": sid,
                         "why": "最后回执 %.1fh 前" % last_receipt})

    surfaces, no_out, no_owner = [], [], []
    for p in products:
        outs = p.get("outputs") or {}
        for stg in (p.get("stages") or []):
            tid = (smap.get(p["id"]) or {}).get(stg)
            t = types.get(tid) or {}
            owners = t.get("stations") or []
            rel = outs.get(stg)
            age = _age_h(os.path.join(root or ROOT, rel)) if rel else None
            surfaces.append({"product": p["id"], "stage": stg, "task_type": tid,
                             "owners": owners, "output": rel, "age_h": age})
            if not owners and not t.get("human"):
                no_owner.append("%s/%s(%s)" % (p["id"], stg, tid))
            if not rel:
                no_out.append("%s/%s" % (p["id"], stg))
    for x in no_owner:
        gaps.append({"kind": "NO-OWNER", "who": x, "why": "没有工位承接"})
    if no_out:
        gaps.append({"kind": "NO-OUTPUT-CONTRACT", "who": "%d 道工序" % len(no_out),
                     "why": "没写产物路径，自驱无从下手（例：%s）" % ", ".join(no_out[:3])})
    return {"machines": machines, "surfaces": surfaces, "gaps": gaps,
            "no_output": no_out, "counts": {"stages": len(surfaces),
                                            "with_output": len(surfaces) - len(no_out)}}


def render(snap):
    L = ["== 机队一屏（盘上事实）==", ""]
    L.append("%-9s %-6s %-26s %-3s %-4s %-5s %s" % (
        "工位", "机器", "状态", "席", "类型", "工序", "队列 O/R/D/B  | 回执 | 模型"))
    for m in snap["machines"]:
        q = m["queue"]
        L.append("%-9s %-6s %-26s %-3s %-4s %-5s %d/%d/%d/%d | %s | %s" % (
            m["station"], m["machine"], (m["status"] or "")[:26], m["seats"],
            m["task_types"], m["stages"], q["open"], q["running"], q["done"], q["blocked"],
            ("%.1fh" % m["last_receipt_h"]) if m["last_receipt_h"] is not None else "无",
            ("通" if m["model_alive"] else "不通") if m["model_alive"] is not None else "未查"))
    c = snap["counts"]
    L += ["", "任务面：%d 道工序，其中 %d 道有产物契约（缺 %d）" % (
        c["stages"], c["with_output"], c["stages"] - c["with_output"]), ""]
    L.append("== 需要主控介入 ==")
    if not snap["gaps"]:
        L.append("（无）")
    else:
        seen = set()
        for g in snap["gaps"]:
            key = (g["kind"], g["who"])
            if key in seen:
                continue
            seen.add(key)
            L.append("- [%s] %s：%s" % (g["kind"], g["who"], g["why"]))
    return "\n".join(L) + "\n"


def self_test():
    import tempfile
    ok = total = 0

    def chk(n, c):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s" % ("ok  " if c else "FAIL", n))

    with tempfile.TemporaryDirectory() as td:
        b = os.path.join(td, "cph4", "fleet")
        os.makedirs(os.path.join(b, "rt", "visual", "receipts"))
        json.dump({"stations": [
            {"id": "visual", "machine": "传家宝", "status": "blocked_no_comfyui",
             "blocked_scope": "gpu", "slots": 6, "shifts": ["00-24"]},
            {"id": "control", "machine": "MacBook", "status": "ready_paused",
             "blocked_scope": "none", "slots": 4, "shifts": ["00-24"]}]},
            open(os.path.join(b, "STATIONS.json"), "w"))
        json.dump({"task_types": [
            {"id": "T-A", "stations": ["visual"]},
            {"id": "T-B", "stations": []},
            {"id": "T-CEO", "stations": [], "human": True}],
            "stage_map": {"P": {"s1": "T-A", "s2": "T-B", "s3": "T-CEO"}}},
            open(os.path.join(b, "TAXONOMY-v1.json"), "w"))
        json.dump({"products": [{"id": "P", "stages": ["s1", "s2", "s3"],
                                 "outputs": {"s1": "out/x.bin"}}]},
                  open(os.path.join(b, "PRODUCTS.json"), "w"))
        json.dump({"teams": {"visual": [{"id": "V"}], "control": []}},
                  open(os.path.join(b, "AGENT-TEAMS-v1.json"), "w"))
        with open(os.path.join(b, "rt", "visual", "queue.jsonl"), "w") as f:
            f.write(json.dumps({"id": "x", "state": "OPEN"}) + "\n")

        snap = snapshot(td, check_net=False)
        kinds = {g["kind"] for g in snap["gaps"]}
        chk("机器降级被标 MACHINE-DOWN", "MACHINE-DOWN" in kinds)
        chk("有 OPEN 但机器不可用 -> WORK-QUEUED-NO-WORKER",
            "WORK-QUEUED-NO-WORKER" in kinds)
        chk("无承接工位 -> NO-OWNER（CEO 物理件不算）",
            "NO-OWNER" in kinds and "PROD" not in "".join(snap["no_output"]))
        chk("只统计 CEO 物理件以外的无主工序", len([g for g in snap["gaps"]
                                              if g["kind"] == "NO-OWNER"]) == 1)
        chk("产物契约统计正确", snap["counts"] == {"stages": 3, "with_output": 1})
        chk("一屏含机器名", "传家宝" in render(snap))
        chk("队列计数正确", snap["machines"][0]["queue"]["open"] == 1)

    print("[fleet_view] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gaps", action="store_true")
    ap.add_argument("--no-net", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    snap = snapshot(a.root, check_net=not a.no_net)
    if a.json:
        print(json.dumps(snap["gaps"] if a.gaps else snap, ensure_ascii=False, indent=1))
    elif a.gaps:
        for g in snap["gaps"]:
            print("[%s] %s：%s" % (g["kind"], g["who"], g["why"]))
    else:
        print(render(snap), end="")
    return 1 if snap["gaps"] else 0


if __name__ == "__main__":
    sys.exit(main())
