#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""org_design_check.py - 九家公司顶层设计的机读体检。

为什么（2026-11-03 CEO「梳理每个子公司，实验室的公司级顶层设计」）：
  设计文档最大的风险不是写不出来，是写完就烂——没人读、没人验收、缺项永远缺着。
  本工具只做一件事：把 ORG-REGISTRY.json 的八个必答项逐条核对，缺项点名，不代写。

判据：
  1. 每家的 design_doc 在盘
  2. 8 问（product/buyer/first_artifact/judge/lane/money_compliance/kill_criteria/gaps）都非空且不含"待答"
  3. design_status=DONE 的必须八问齐；PENDING 的只报进度，不算失败

Exit: 0 全部齐；2 有缺项（告警，不阻断派单）。
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(ROOT, "cph4", "fleet", "company", "ORG-REGISTRY.json")
FIELDS = ["product", "buyer", "first_artifact", "judge", "lane",
          "money_compliance", "kill_criteria", "gaps"]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.exists(REG):
        print("[orgs] 登记表不存在：%s（rc=2）" % REG)
        return 2
    reg = json.load(open(REG, encoding="utf-8"))
    orgs = reg.get("orgs") or []
    rows, gaps = [], []
    for o in orgs:
        miss = [f for f in FIELDS if not (str(o.get(f) or "").strip())
                or "待答" in str(o.get(f))]
        doc = o.get("design_doc") or ""
        doc_ok = bool(doc) and os.path.exists(os.path.join(ROOT, doc))
        status = o.get("design_status") or "PENDING"
        if status == "DONE":
            if not doc_ok:
                gaps.append("%s：标 DONE 但设计正文不在盘（%s）" % (o.get("id"), doc))
            if miss:
                gaps.append("%s：标 DONE 但八问缺 %d 项（%s）" % (o.get("id"), len(miss), ",".join(miss)))
        rows.append({"id": o.get("id"), "name": o.get("name"), "status": status,
                     "doc_ok": doc_ok, "missing_fields": miss,
                     "order": (reg.get("order") or []).index(o.get("id"))
                     if o.get("id") in (reg.get("order") or []) else 99})
    rows.sort(key=lambda r: r["order"])
    done = [r for r in rows if r["status"] == "DONE"]
    pend = [r for r in rows if r["status"] != "DONE"]
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "total": len(rows),
           "done": len(done), "pending": len(pend), "gaps": gaps, "rows": rows,
           "verdict": "PASS" if not gaps else "GAPS"}
    if a.out:
        d = os.path.dirname(os.path.abspath(a.out))
        if d:
            os.makedirs(d, exist_ok=True)
        json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[orgs] 设计 %d/%d 完成，待做 %d" % (len(done), len(rows), len(pend)))
        for r in pend:
            print("  . %-12s %s" % (r["id"], r["name"]))
        for g in gaps:
            print("  ! " + g)
    return 0 if not gaps else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))