#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""handoff.py - 交接一屏：新会话 3 分钟接上。

为什么：上下文一断就要重读几千行文档，等于每次重新上岗。这里只写四段：
在产、待判、阻塞、下一步——全部来自磁盘事实，不写判断。

输出：cph4/fleet/HANDOFF.md（进 git，随仓分发）
用法：python3 handoff.py [--json]
"""
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def jlines(p):
    out = []
    try:
        for l in open(p, encoding="utf-8-sig"):
            l = l.strip()
            if l:
                out.append(json.loads(l))
    except Exception:
        pass
    return out


def main(argv):
    queue = jlines(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    inv = jload(os.path.join(STATE, "invariants.json"), {}) or {}
    com = jload(os.path.join(STATE, "comms.json"), {}) or {}
    met = jload(os.path.join(STATE, "metrics.json"), {}) or {}
    ship = []
    d = os.path.join(FLEET, "ship")
    if os.path.isdir(d):
        for n in os.listdir(d):
            if n.endswith(".json"):
                ship.append(jload(os.path.join(d, n), {}) or {})

    running = [r for r in queue if r.get("state") == "RUNNING"]
    opens = [r for r in queue if r.get("state") == "OPEN"]
    red = [(c.get("id"), c.get("count")) for c in (inv.get("checks") or []) if c.get("count")]
    bad_nodes = [n for n in (com.get("nodes") or []) if n.get("flags")]
    nexts = [r for r in met.get("lines") or [] if r.get("priority") == "P0"]

    L = ["# 交接一屏（%s）" % datetime.now().strftime("%Y-%m-%d %H:%M"), "",
         "> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。", "",
         "## 一、在产（%d 张）" % len(running), ""]
    for r in running[:10]:
        L.append("- `%s` %s（%s，%s 分钟租约）" % (r.get("id"), r.get("title"),
                                                r.get("owner") or "?",
                                                r.get("lease_minutes") or "?"))
    L += ["", "## 二、待判（%d 张在队列等机器）" % len(opens), ""]
    for r in opens[:10]:
        L.append("- `%s` %s（%s）" % (r.get("id"), r.get("title"), r.get("line") or "无归属"))
    L += ["", "## 三、阻塞（%d 项断言红 / %d 台机不一致）" % (len(red), len(bad_nodes)), ""]
    for i, n in red:
        L.append("- 断言 %s：%s 条" % (i, n))
    for n in bad_nodes[:5]:
        L.append("- 机器 %s：%s" % (n.get("node"), "、".join(n.get("flags") or [])))
    if not red and not bad_nodes:
        L.append("- 无")
    L += ["", "## 四、下一步（P0 两线）", ""]
    for r in nexts:
        L.append("- %s：过闸率 %s，返工 %s，产出年龄 %s" % (
            r.get("line"), r.get("first_pass_rate_pct"), r.get("rework"),
            r.get("output_age_h")))
    L += ["", "## 五、已发布（%d 条）" % len(ship), ""]
    for s in ship:
        L.append("- %s %s（%s）" % (s.get("work"), s.get("current_version"), s.get("platform")))
    if not ship:
        L.append("- 还没有任何发布")
    L += ["", "---", "生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。"]

    md = "\n".join(L) + "\n"
    open(os.path.join(FLEET, "HANDOFF.md"), "w", encoding="utf-8").write(md)
    if "--json" in argv:
        print(json.dumps({"running": len(running), "open": len(opens), "red": red,
                          "bad_nodes": len(bad_nodes), "ship": len(ship)},
                         ensure_ascii=False, indent=1))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))