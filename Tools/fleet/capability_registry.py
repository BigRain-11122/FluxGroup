#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capability_registry.py - 机队能力共享台账（谁有什么、能不能接什么活）。

2026-11-10 CEO：机队同步与互相共享要做到极致。
数据来源（全部盘上事实，不猜）：
  - LANES 配置：needs/caps/llm/gpu_hours/enabled
  - lanes/<node>.json：心跳、在办、lane_ok、capacity_note
  - 本机 11434 /api/tags：实际可用的本地模型
输出：state/capabilities.json + CAPABILITIES.md
用途：派单前可查"哪台机能接这类活"，而不是靠猜；缺能力时显式排队。
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
import fleet_lane as fl


def hb_age(node):
    p = os.path.join(F, "lanes", "%s.json" % node)
    try:
        d = json.load(open(p, encoding="utf-8"))
        ts = d.get("ts")
        age = round(time.time() - time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S")))
        return age, d
    except Exception:
        return None, {}


def local_models():
    try:
        d = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3).read())
        return [m.get("name") for m in d.get("models") or []]
    except Exception:
        return []


def beat_local_lane():
    """主控自己也是算力：把 lanes/bm-m.json 的时间戳刷新。
    2026-11-10：bm-m 车道文件曾是 14:31 的旧心跳，派单/台账都误判它离线。"""
    import socket
    if socket.gethostname().lower().find("macbook") < 0 and os.environ.get("FLEET_NODE") != "bm-m":
        return
    p = os.path.join(F, "lanes", "bm-m.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        d = {"node": "bm-m", "jobs": []}
    d["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    d["lane_ok"] = True
    d["idle_reason"] = "control-plane heartbeat"
    d.setdefault("jobs", [])
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    beat_local_lane()
    out = {}
    for n, v in fl.LANES.items():
        age, lane = hb_age(n)
        entry = {
            "enabled": bool(v.get("enabled")),
            "needs": v.get("needs") or [],
            "caps": v.get("caps") or [],
            "gpu_hours": v.get("gpu_hours"),
            "llm": bool(v.get("llm")),
            "llm_fallback": (v.get("llm") or {}).get("fallback") or "",
            "hb_age_s": age,
            "online": age is not None and age < 600,
            "lane_ok": lane.get("lane_ok"),
            "jobs": [j.get("id") for j in (lane.get("jobs") or [])],
            "capacity_note": (lane.get("capacity_note") or "")[:120],
        }
        out[n] = entry
    if "bm-m" in out:
        out["bm-m"]["models"] = local_models()
    # 共享面：谁在给谁提供模型
    out["_shared"] = {
        "hub": "bm-m",
        "gateway": "http://100.75.133.10:8792",
        "model_hub_online": out.get("bm-m", {}).get("online"),
        "lanes_with_llm": [n for n, e in out.items() if isinstance(e, dict) and e.get("llm")],
        "token_env": "FLUX_LLM_TOKEN",
        "note": "各机优先用自己的 11434；没有时才回落 bm-m 网关（需令牌）",
    }
    os.makedirs(STATE, exist_ok=True)
    json.dump(out, open(os.path.join(STATE, "capabilities.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    lines = ["# 机队能力台账（自动生成）", "", "| 节点 | 在线 | 能力 | 本地模型 | 心跳 | 在办 |", "|---|---|---|---|---|---|"]
    for n, e in out.items():
        if n.startswith("_"):
            continue
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            n, "是" if e["online"] else "否", ",".join(e["caps"]),
            ",".join(e.get("models") or []) or "-",
            ("%ss" % e["hb_age_s"]) if e["hb_age_s"] is not None else "-",
            ",".join(e["jobs"]) or "-"))
    open(os.path.join(F, "CAPABILITIES.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    online = [n for n, e in out.items() if not n.startswith("_") and e["online"]]
    print("capabilities: online=%s hub=%s" % (online, out["_shared"]["model_hub_online"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
