#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_report.py - 把"结构断言"和"通信体检"合成一行，交给脉冲，不制造假降级。

为什么：两者在有问题时返回 2。直接接进脉冲会把整个调度面标成 DEGRADED（看起来像
中枢坏了），实际上只是业务面有红。这里统一成"永远 0，但把红写在尾巴上"。

输出：一行摘要 + cph4/fleet/state/gate-report.json
"""
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")


def run(name):
    p = os.path.join(HERE, name)
    try:
        r = subprocess.run([sys.executable, p, "--json"], capture_output=True,
                           text=True, timeout=120)
        start = r.stdout.find("{")
        return json.loads(r.stdout[start:]) if start >= 0 else {}
    except Exception as e:
        return {"_error": str(e)[:120]}


def main():
    os.makedirs(STATE, exist_ok=True)
    inv = run("flux_check.py")
    com = run("comms_check.py")
    red = [(c.get("id"), c.get("count")) for c in (inv.get("checks") or []) if c.get("count")]
    bad_nodes = [n for n in (com.get("nodes") or []) if n.get("flags")]
    out = {"ts": datetime.now().isoformat(timespec="seconds"),
           "invariants": {"verdict": inv.get("verdict"),
                          "new": inv.get("new_violations"),
                          "red": red},
           "comms": {"incoherent": com.get("incoherent"),
                     "nodes": [{"node": n.get("node"), "flags": n.get("flags")} for n in bad_nodes]},
           "queue": com.get("queue")}
    with open(os.path.join(STATE, "gate-report.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    line = "gate: %s 红%d项 %s | comms %d台不一致 %s" % (
        out["invariants"]["verdict"], len(red),
        ",".join("%s x%s" % (i, n) for i, n in red[:4]) or "-",
        out["comms"]["incoherent"],
        ",".join("%s(%s)" % (n["node"], "、".join(n["flags"])[:24]) for n in bad_nodes[:3]) or "-")
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())