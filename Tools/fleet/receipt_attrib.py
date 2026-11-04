#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回执失败归因：把 rc≠0 的回执按错误码归类，并列出缺 error_class 的清单。

为什么要有这件：架构 v2 §八 定的「失败分类学」到目前为止只是纸面——
rc=1/2/127 走同一条收口路径，retry_reason 是自由文本，阻塞原因无法统计。
没有这张表，"为什么总在失败"只能靠感觉。

判据（可机器复核）：
  - 每份可解析回执都必须有 rc
  - rc≠0 的必须带 error_class，且落在 8 类之内
  - 分类只能按 rc 与 error_class 判，不做语义猜测（语义判断交判断席，不交本脚本）

用法：
  python3 Tools/fleet/receipt_attrib.py --out cph4/fleet/queue-receipts/receipt-attrib-YYYYMMDD.json
rc: 0=已出表 2=发现不合规回执（告警，不阻断）
"""

import argparse
import glob
import json
import os
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RC_CLASS = {0: "E-OK", 2: "E-CONTRACT", 3: "E-BLOCKED-INPUT", 124: "E-TIMEOUT",
            126: "E-MODEL", 127: "E-PATH", 9009: "E-PATH"}
# 判据只认 flux_contracts 一处（2026-11-04：这里曾自己抄一份旧表，把 E-INPUT 判成非法类）。
try:
    import flux_contracts as _fc
    KNOWN = set(_fc.ERROR_CLASSES)
except Exception:
    KNOWN = {"E-OK", "E-CONTRACT", "E-PATH", "E-MEM", "E-MODEL", "E-QUOTA",
             "E-TIMEOUT", "E-COMPLIANCE", "E-ARTIFACT", "E-BLOCKED-INPUT", "E-INPUT",
             "E-UNKNOWN"}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    files = sorted(glob.glob(os.path.join(ROOT, "cph4", "fleet", "queue-receipts", "*.json")))
    bad, no_rc, no_class, wrong_class = [], [], [], []
    other = []          # 目录里的工具产物（体检/索引/漏斗），不是执行回执
    rcs = Counter()
    for p in files:
        d = None
        raw = b""
        # Windows/PowerShell 写出来的 JSON 常是 UTF-16 带 BOM（实测 fleet-align-*.json），
        # 只按 utf-8 读会把它误判成"坏 JSON"——真债要被看见，不能和编码问题混在一起。
        for enc in ("utf-8-sig", "utf-16", "utf-8"):
            try:
                with open(p, "rb") as f:
                    raw = f.read()
                d = json.loads(raw.decode(enc))
                break
            except Exception:
                d = None
        if d is None:
            if raw.lstrip()[:1] not in (b"{", b"["):
                # 扩展名是 .json 但内容是文本/表格：写错格式，不是坏 JSON。
                other.append(os.path.basename(p))
            else:
                bad.append(p)
            continue
        if not isinstance(d, dict):
            other.append(os.path.basename(p))
            continue
        # 回执的判据是"有 id + 有 node"（lane_agent 写的那份）。
        # 2026-11-04 实锚：不加这一层，工具产物（inference-audit/asset-index/FUNNEL 等）
        # 全被算成"缺 rc 的回执"，70 条假红把真债埋掉了——红必须可解释，否则等于没有。
        if not (d.get("id") and d.get("node")):
            other.append(os.path.basename(p))
            continue
        rc = d.get("rc")
        if rc is None:
            no_rc.append(os.path.basename(p))
            continue
        try:
            rc = int(rc)
        except (TypeError, ValueError):
            no_rc.append(os.path.basename(p))
            continue
        rcs[rc] += 1
        if rc != 0:
            ec = d.get("error_class")
            if not ec:
                no_class.append(os.path.basename(p))
            elif ec not in KNOWN:
                wrong_class.append((os.path.basename(p), ec))
    fails = sorted({("%d -> %s" % (r, RC_CLASS.get(r, "E-UNKNOWN"))) for r in rcs if r != 0})
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "receipts": len(files) - len(other) - len(bad), "files_scanned": len(files),
           "non_receipt_files": len(other), "unparseable": bad,
           "missing_rc": no_rc, "rc_hist": dict(sorted(rcs.items())),
           "fail_rc_map": fails, "fail_no_error_class": no_class,
           "error_class_not_in_taxonomy": wrong_class,
           "verdict": "PASS" if not (bad or no_rc or no_class or wrong_class) else "GAPS"}
    print("receipts=%d（另有工具产物 %d 不计） rc0=%d fail=%d  missing_rc=%d no_error_class=%d bad_json=%d"
          % (len(files) - len(other) - len(bad), len(other), rcs.get(0, 0), len(fails),
             len(no_rc), len(no_class), len(bad)))
    print("fail rc: " + (", ".join(fails) or "none"))
    if no_class:
        print("rc!=0 但缺 error_class: " + ", ".join(no_class[:6]) + (" ..." if len(no_class) > 6 else ""))
    op = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(op), exist_ok=True)
    with open(op, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote", os.path.relpath(op, ROOT), "verdict=%s" % out["verdict"])
    return 2 if out["verdict"] != "PASS" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))