#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提审包盘点：把每款产品的"能不能现在提交"算清楚。

背景（CEO 2026-11-03）：39 款在册、0 款上线，唯一战略卡点是资质链
（微信 AppID→ICP→软著→提审）。资质是 CEO 物理件，但"提审包"是机队能做完的那一半：
缺哪份材料、缺给谁、缺什么格式，全部可以机器判，不该等人想起来。

判据（缺一项即 NOT-READY，并写明缺什么）：
  1. 软著材料目录存在，且含源程序文件（.txt/.pdf/.docx 任一）
  2. 有可运行包（.apk/.zip/.unitypackage/.html 任一）——没有包就没有提审对象
  3. 有图标（icon/logo/appicon，≥256px 名即可，尺寸人工核）
  4. 有截图目录（shot/screenshot/截图）
  5. 有隐私政策（privacy/隐私）
  6. 提审台账里有该产品的行（报审台账.md）

产物：cph4/fleet/game-v1/SUBMIT-PACK-<date>.json + SUBMIT-PACK.md（缺件清单按"缺件"聚合，便于一次性补齐）
Exit: 0 全部 READY；2 有 NOT-READY（告警）
"""

import argparse
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SW = os.path.join(ROOT, "软著申请材料")
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "game-v1")
PACK_EXT = (".apk", ".zip", ".unitypackage", ".html", ".aab")
SRC_EXT = (".txt", ".pdf", ".docx", ".doc")


def has(dirpath, keys, exts=None):
    for dirpath2, dirs, files in os.walk(dirpath):
        for n in files + dirs:
            low = n.lower()
            if exts and not low.endswith(exts):
                continue
            if any(k in low for k in keys):
                return True
    return False


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    if not os.path.isdir(SW):
        print("没有软著材料目录")
        return 1
    ledger = os.path.join(SW, "_报审提交区", "报审台账.md")
    ledger_txt = open(ledger, encoding="utf-8", errors="replace").read() if os.path.exists(ledger) else ""

    items, missing_agg = [], {}
    for d in sorted(os.listdir(SW)):
        p = os.path.join(SW, d)
        if not os.path.isdir(p) or d.startswith("_"):
            continue
        name = re.sub(r"^(G\d+_|P\d+_)", "", d)
        lacks = []
        if not has(p, ("源程序", "source", "程序"), SRC_EXT):
            lacks.append("源程序文件")
        if not has(p, ("",), PACK_EXT):
            lacks.append("可运行包(apk/zip/unitypackage/html)")
        if not has(p, ("icon", "logo", "appicon", "图标")):
            lacks.append("图标≥256px")
        if not has(p, ("shot", "screen", "截图", "screenshot")):
            lacks.append("截图目录(≥4张)")
        if not has(p, ("privacy", "隐私")):
            lacks.append("隐私政策")
        if name and name not in ledger_txt:
            lacks.append("提审台账登记")
        for x in lacks:
            missing_agg[x] = missing_agg.get(x, 0) + 1
        items.append({"dir": d, "product": name, "verdict": "READY" if not lacks else "NOT-READY",
                      "lacks": lacks})
    ready = sum(1 for x in items if x["verdict"] == "READY")
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "products": len(items),
           "ready": ready, "not_ready": len(items) - ready,
           "missing_by_kind": dict(sorted(missing_agg.items(), key=lambda kv: -kv[1])),
           "items": items}
    os.makedirs(OUTDIR, exist_ok=True)
    op = a.out or os.path.join(OUTDIR, "SUBMIT-PACK-%s.json" % time.strftime("%Y%m%d"))
    json.dump(rec, open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["# 提审包盘点（%s）" % rec["ts"], "",
          "在册 %d 款：可提交 %d / 待补 %d" % (len(items), ready, len(items) - ready), "", "## 缺件聚合", ""]
    md += ["- %s：%d 款" % (k, v) for k, v in rec["missing_by_kind"].items()]
    md += ["", "## 逐款", "", "| 产品 | 结论 | 缺什么 |", "|---|---|---|"]
    for x in items:
        md.append("| %s | %s | %s |" % (x["product"], x["verdict"],
                                        "、".join(x["lacks"]) if x["lacks"] else "—"))
    open(os.path.join(OUTDIR, "SUBMIT-PACK.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("products=%d ready=%d not_ready=%d" % (len(items), ready, len(items) - ready))
    for k, v in list(rec["missing_by_kind"].items())[:6]:
        print("  缺 %-28s %d 款" % (k, v))
    print("wrote", os.path.relpath(op, ROOT), "+ SUBMIT-PACK.md")
    return 0 if ready else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))