#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""biggame_onepager.py - 把 submit-pack 的 JSON 压成一页提审材料（Markdown）。

为什么单独成文件：2026-11-10 把这段逻辑写成 `python -c "..."` 塞进卡里，
引号在 JSON→cmd.exe→python 三层转义中被打散，卡「跑了」但不出产物，白占车道。
成文件后本机可自证，卡里只留一行调用。
用法：python Tools/fleet/biggame_onepager.py --src <submit-pack.json> --out <md>
"""
import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="cph4/fleet/reports/submit-pack-20261110.json")
    ap.add_argument("--out", default="cph4/fleet/reports/biggame-submit-onepager.md")
    a = ap.parse_args()
    if not os.path.exists(a.src):
        print("[onepager] 缺输入 %s" % a.src, file=sys.stderr)
        return 2
    d = json.load(open(a.src, encoding="utf-8"))
    items = d.get("items") or []
    lines = ["# biggame 提审一页 · %s" % (d.get("ts") or ""), "",
             "可提交 **%s** / 共 **%s**" % (d.get("ready"), d.get("products")), "",
             "| 产品 | 判定 | 缺什么 |", "|---|---|---|"]
    for it in items:
        lines.append("| %s | %s | %s |" % (it.get("product"), it.get("verdict"),
                                           "、".join(it.get("lacks") or []) or "—"))
    gaps = d.get("missing_by_kind") or {}
    if gaps:
        lines += ["", "## 缺口汇总", ""]
        lines += ["- %s：%s 款" % (k, v) for k, v in gaps.items()]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("[onepager] %s -> %s (%d products)" % (a.src, a.out, len(items)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
