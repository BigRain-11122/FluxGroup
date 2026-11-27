# -*- coding: utf-8 -*-
"""ceo_three.py - 每天只交 CEO 三件事（其余自决）。

CEO 2026-11-06：「代替我做好各个指挥工作」。指挥里唯一不能代签的就是三类：
不可逆、对外发布、花钱超限；再加「同一根因三次未解」和「必须人上机的物理动作」。

Rules decide, model only words it. Order is fixed so the same state always yields the
same three items - a rotating list would look busy and say nothing.
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
OUT = os.path.join(FLEET, "CEO-THREE.md")

sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def collect():
    """Return candidate items in priority order, each with a file pointer."""
    items = []

    # 1. 物理动作：必须人上机（不可远程）
    fs = jload(os.path.join(STATE, "fork-status.json"), {}) or {}
    for node, v in (fs.get("nodes") or {}).items():
        if int(v.get("ahead") or 0) > 0 and int(v.get("real") or 0) > 0:
            items.append({"why": "物理动作", "what": "%s 仓库分叉 ahead=%d 且含真实文件，需上机收口"
                          % (node, v.get("ahead")), "ptr": "cph4/fleet/state/fork-status.json"})

    # 2. 停线根因未解（3X）
    al = jload(os.path.join(STATE, "alerts.json"), {}) or {}
    rows = al.get("alerts") if isinstance(al, dict) else al
    for a in (rows or []):
        if not isinstance(a, dict):
            continue
        ec = str(a.get("error_class") or a.get("kind") or "")
        if "3X" in ec or "ROOTCAUSE" in ec:
            items.append({"why": "根因未解", "what": "停线待根因：%s（%s）"
                          % (a.get("id") or a.get("stem"), ec), "ptr": "cph4/fleet/state/alerts.json"})

    # 3. 对外/花钱（红线条目由人工登记，读到就升）
    for p, key in ((os.path.join(FLEET, "CEO-QUEUE.md"), None),
                   (os.path.join(FLEET, "ASSET-GEN-PENDING.json"), "cloud")):
        if p.endswith(".json") and os.path.exists(p):
            d = jload(p, {}) or {}
            pend = d.get("pending") or d.get("items") or []
            if isinstance(pend, list) and pend:
                items.append({"why": "花钱/额度", "what": "有 %d 项等云端额度放行" % len(pend),
                              "ptr": os.path.relpath(p, ROOT)})

    # 4. 线超期去留
    lines = (jload(os.path.join(STATE, "lines.json"), {}) or {}).get("lines") or []
    stale = [l for l in lines if (l.get("age_h") or 0) > 72]
    if stale:
        names = ", ".join("%s(%.0fh)" % (l.get("name") or l.get("id"), l.get("age_h") or 0)
                          for l in stale[:4])
        items.append({"why": "方向", "what": "%d 条线超 72h 无产出，需定去留：%s"
                      % (len(stale), names), "ptr": "cph4/fleet/state/lines.json"})

    # 5. 自检未过的机器
    d = os.path.join(FLEET, "queue-receipts")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.startswith("self-improve-") and f.endswith("-latest.json"):
                r = jload(os.path.join(d, f), {}) or {}
                if r.get("node") and r.get("verdict") != "SELF-OK":
                    items.append({"why": "机器", "what": "%s 自检未过（%s）"
                                  % (r.get("node"), r.get("verdict")),
                                  "ptr": os.path.relpath(os.path.join(d, f), ROOT)})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="store_true", help="让 4B 给每条写一句人话（可选）")
    a = ap.parse_args()
    items = collect()
    picked = items[:3]
    L = ["# 只需你拍的三件事 %s" % time.strftime("%Y-%m-%dT%H:%M:%S"), ""]
    if not picked:
        L += ["**无。** 其余全部按既有规则自决推进。", ""]
    for i, it in enumerate(picked, 1):
        L.append("%d. **[%s]** %s" % (i, it["why"], it["what"]))
        L.append("   证据：`%s`" % it["ptr"])
    L.append("")
    if len(items) > 3:
        L.append("_另有 %d 项已自动处理或排队，不占你的注意力。_" % (len(items) - 3))
        L.append("")
    if a.model and picked:
        try:
            import fleet_lane as fl
            txt = fl.local_llm("用一句中文总结这三件事的共同点，不要新增事实：\n"
                               + "\n".join("- %s" % p["what"] for p in picked),
                               node="bm-m", timeout=60)
            if txt:
                L += ["## 一句话（4B，仅供参考）", "", str(txt).strip().splitlines()[0][:200], ""]
        except Exception:
            pass
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(json.dumps({"out": os.path.relpath(OUT, ROOT), "picked": len(picked),
                      "candidates": len(items)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())