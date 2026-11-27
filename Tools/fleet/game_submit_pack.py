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
    ap.add_argument("--strict", action="store_true",
                    help="没有可提交款时返回 rc=2（CI 语义）；盘点本身默认 rc=0")
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
    # 2026-11-07：卡上 accept 明确要求「与上一版对比写出增减，不许照抄旧数」。只给当日快照
    # 等于把"变化"这项验收交给读的人自己算，机检无从核验——所以对比要由工具自己写进产物。
    cmp_ = None
    try:
        prevs = sorted(x for x in os.listdir(OUTDIR)
                       if re.match(r"^SUBMIT-PACK-\d{8}\.json$", x)
                       and os.path.join(OUTDIR, x) != op)
        if prevs:
            prev_path = os.path.join(OUTDIR, prevs[-1])
            prev = json.load(open(prev_path, encoding="utf-8"))
            pk = prev.get("missing_by_kind") or {}
            kinds = set(pk) | set(rec["missing_by_kind"])
            cmp_ = {
                "against": os.path.basename(prev_path),
                "products": {"prev": prev.get("products"), "now": len(items)},
                "ready": {"prev": prev.get("ready"), "now": ready},
                "missing_by_kind": {
                    k: {"prev": pk.get(k, 0), "now": rec["missing_by_kind"].get(k, 0),
                        "delta": rec["missing_by_kind"].get(k, 0) - pk.get(k, 0)}
                    for k in sorted(kinds)
                },
            }
            rec["compare"] = cmp_
    except Exception as e:
        rec["compare_error"] = str(e)[:120]
    # 2026-11-12 实证：交付工位首卡跑这里 rc=1——`--out cph4/fleet/out/game-submit/list.json`
    # 的父目录不存在，json.dump 直接 FileNotFoundError。产物目录属于本工具职责，先建后写。
    os.makedirs(os.path.dirname(os.path.abspath(op)) or ".", exist_ok=True)
    json.dump(rec, open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["# 提审包盘点（%s）" % rec["ts"], "",
          "在册 %d 款：可提交 %d / 待补 %d" % (len(items), ready, len(items) - ready), "", "## 缺件聚合", ""]
    md += ["- %s：%d 款" % (k, v) for k, v in rec["missing_by_kind"].items()]
    if cmp_:
        d_ready = cmp_["ready"]["now"] - (cmp_["ready"]["prev"] or 0)
        md += ["", "## 与上一版对比（%s）" % cmp_["against"], "",
               "- 在册款数：%s → %s" % (cmp_["products"]["prev"], cmp_["products"]["now"]),
               "- 可提交：%s → %s（%+d）" % (cmp_["ready"]["prev"], cmp_["ready"]["now"], d_ready),
               "", "| 缺件类型 | 上一版 | 本次 | 增减 |", "|---|---|---|---|"]
        for k, v in cmp_["missing_by_kind"].items():
            md.append("| %s | %s | %s | %+d |" % (k, v["prev"], v["now"], v["delta"]))
    md += ["", "## 逐款", "", "| 产品 | 结论 | 缺什么 |", "|---|---|---|"]
    for x in items:
        md.append("| %s | %s | %s |" % (x["product"], x["verdict"],
                                        "、".join(x["lacks"]) if x["lacks"] else "—"))
    open(os.path.join(OUTDIR, "SUBMIT-PACK.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("products=%d ready=%d not_ready=%d" % (len(items), ready, len(items) - ready))
    for k, v in list(rec["missing_by_kind"].items())[:6]:
        print("  缺 %-28s %d 款" % (k, v))
    print("wrote", os.path.relpath(op, ROOT), "+ SUBMIT-PACK.md")
    if cmp_:
        print("对比 %s：可提交 %s -> %s" % (cmp_["against"], cmp_["ready"]["prev"], ready))
    # 2026-11-07：本卡是「盘点/枚举缺口」，盘点成功本身就是成功。旧的 `return 0 if ready else 2`
    # 让"一条都没齐"变成脚本失败 → 车道每轮判 E-CONTRACT 无限重试（实测 bm-m 连续两次
    # rc=2 0.1s）。rc=2 只保留给真正的机制故障；需要 CI 语义时用 --strict。
    return 2 if (a.strict and not ready) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))