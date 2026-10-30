#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_health.py - 60s 高频机队健康与产出检查（bm-m 主控自检）
每轮核对：各机心跳新鲜度 / bm-m 本地产出增量 / 队列状态 / 总控脉。
输出追加到 /tmp/fleet-health.log，供主控与班报查证。zero-LLM 零网络外呼。
"""
import os, sys, time, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(ROOT, "Tools", "fleet") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
import fleet_lane as fl

LOG = "/tmp/fleet-health.log"

# 上一轮 bm-m 产出快照（回执目录文件数+最大 mtime）
RECEIPT_DIR = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
SNAP = "/tmp/fleet-health-snap.json"

def receipt_snapshot():
    n = 0; mx = 0.0
    if os.path.isdir(RECEIPT_DIR):
        for f in os.listdir(RECEIPT_DIR):
            p = os.path.join(RECEIPT_DIR, f)
            if os.path.isfile(p):
                n += 1
                mx = max(mx, os.path.getmtime(p))
    return {"n": n, "mtime": mx}

def main():
    now = int(time.time() * 1000)
    lines = []
    # 1) 各机心跳新鲜度
    for node in ("bm-a", "bm-b", "bm-c", "bm-m"):
        s = fl.kv_get("state." + node)
        if not s:
            lines.append("%s HB=dead" % node)
            continue
        age = (now - int(s.get("ts_utc_ms") or 0)) / 1000.0
        on = age <= 900
        lines.append("%s HB=%.0fs %s ram=%sG gpu=%s" % (
            node, age, "ONLINE" if on else "STALE",
            s.get("ram_free_gb"), s.get("gpu_util_pct")))
    # 2) bm-m 本地产出增量
    snap = receipt_snapshot()
    prev = {}
    if os.path.exists(SNAP):
        try: prev = json.load(open(SNAP))
        except Exception: prev = {}
    new_files = 0
    if prev:
        if snap["n"] > prev.get("n", 0): new_files = snap["n"] - prev.get("n", 0)
        if snap["mtime"] > prev.get("mtime", 0): new_files = max(new_files, 1)
    json.dump(snap, open(SNAP, "w"))
    lines.append("bm-m 本地回执= %d 件（较上轮 +%d）" % (snap["n"], new_files))
    # 3) 队列
    try:
        rows = fl.read_jsonl(os.path.join(ROOT, fl.QUEUE_REL.replace("/", os.sep)))
        from collections import Counter
        q = Counter(r.get("state") for r in rows)
        lines.append("队列 %s" % dict(q))
    except Exception as e:
        lines.append("队列读失败 %s" % e)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (ts, " | ".join(lines)))
    # 异常横幅：离线/无产出只打一次
    flags = [l for l in lines if "STALE" in l or "HB=dead" in l]
    if flags:
        with open("/tmp/fleet-health-flags.log", "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (ts, "; ".join(flags)))
    print(" | ".join(lines))

if __name__ == "__main__":
    main()
