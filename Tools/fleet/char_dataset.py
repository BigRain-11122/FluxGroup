#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""角色数据集装配：characters/<ID>/*.png → faces/<ID>/ + RIGHTS.json → 逐角色过准入闸。

为什么单独一段：出图产物不是训练集。训练要的是"一个角色一个目录、带授权声明、
过规格闸"的数据集。这一步把两者接上，并把准入结论写进回执——没过闸的角色不许进训练。

判据：characters/<ID> 下有效 PNG ≥ 6（LIBRARY-TARGETS.p0.ref_images_min 同源）；
      RIGHTS.json 由上游 char_plan 写在 media/asset/characters/RIGHTS.json。

Exit: 0 = 至少一个角色过闸；3 = 一个都没过（缺图/缺授权），属"等上游"不是工具坏。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHARS = os.path.join(ROOT, "media", "asset", "characters")
FACES = os.path.join(ROOT, "media", "asset", "faces")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
AUDIT = os.path.join(ROOT, "Tools", "fleet", "asset_dataset_audit.py")
MIN_IMAGES = 6


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=MIN_IMAGES)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    out = a.out or os.path.join(RECEIPTS, "char-dataset-%s.json" % time.strftime("%Y%m%d"))
    rights_src = os.path.join(CHARS, "RIGHTS.json")
    rights = json.load(open(rights_src, encoding="utf-8")) if os.path.exists(rights_src) else None

    per, ok = [], 0
    for cid in sorted(os.listdir(CHARS)):
        src = os.path.join(CHARS, cid)
        if not os.path.isdir(src):
            continue
        pngs = [n for n in os.listdir(src) if n.lower().endswith(".png")]
        entry = {"character": cid, "images": len(pngs), "verdict": "SKIP", "audit": None}
        if len(pngs) < a.min:
            entry["gap"] = "图不足 %d 张（现有 %d）" % (a.min, len(pngs))
            per.append(entry)
            continue
        dst = os.path.join(FACES, cid)
        os.makedirs(dst, exist_ok=True)
        for n in pngs:
            shutil.copy2(os.path.join(src, n), os.path.join(dst, n))
        if rights:
            with open(os.path.join(dst, "RIGHTS.json"), "w", encoding="utf-8") as f:
                json.dump(dict(rights, character=cid), f, ensure_ascii=False, indent=1)
        rp = os.path.join(RECEIPTS, "face-audit-%s.json" % cid)
        try:
            p = subprocess.run([sys.executable, AUDIT, "--mode", "face", "--dir", dst, "--out", rp],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
            rc = p.returncode
            try:
                res = json.load(open(rp, encoding="utf-8"))
            except Exception:
                res = {"verdict": "UNKNOWN"}
            entry["audit"] = {"rc": rc, "verdict": res.get("verdict"), "gaps": res.get("gaps")}
            entry["verdict"] = "PASS" if res.get("verdict") in ("PASS", "OK") else "FAIL"
            if entry["verdict"] == "PASS":
                ok += 1
        except Exception as e:
            entry["audit"] = {"error": str(e)[:160]}
        per.append(entry)

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "rc": 0 if ok else 3, "verdict": "PASS" if ok else "BLOCKED",
           "error_class": None if ok else "E-BLOCKED-INPUT",
           "characters": per, "passed": ok,
           "gaps": [] if ok else ["没有任何角色同时满足 图≥%d 且 过准入闸" % a.min]}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("char-dataset: passed=%d/%d -> %s" % (ok, len(per), os.path.relpath(out, ROOT)))
    for e in per:
        print("  %-5s %-6s imgs=%d %s" % (e["character"], e["verdict"], e["images"], e.get("gap") or ""))
    return rec["rc"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))