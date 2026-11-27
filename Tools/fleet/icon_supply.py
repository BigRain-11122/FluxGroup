#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图标补件管线（biggame 提审缺口 L1 件）。

背景（CEO 2026-11-09 14:05 原话「我需要你开始7x24小时推进，自己写好计划，然后开始调度」）：
SUBMIT-PACK 显示 34/36 款缺「图标≥256px」。软著目录内几乎无可用图源，
图标需生成。本工具是其中的确定性一半：

  1. --manifest : 从最新 SUBMIT-PACK-*.json 取缺图标清单，逐款读软件设计说明书
                  首段提炼主题句，产 ICON-JOBS-<date>.json（出图工单，供 L0 出图轮消费）。
  2. --verify   : 检查每款产品目录下是否存在名字含 icon/logo/appicon 且
                  实测尺寸 ≥256px 的图片（sips 实测，不信文件名），产 ICON-RECEIPT-<date>.json。

判据与 game_submit_pack.py 保持同源：名字含 icon/logo/appicon；尺寸是真读出来的。
G09_GimmeAll 的签章.jpg 是签字页不是图标，不得作图源（名单已排除）。

Exit: 0 正常；2 有待办（manifest 有缺口或 verify 有未过款）。
"""

import glob
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SW = os.path.join(ROOT, "软著申请材料")
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "game-v1")

# 出图工单的美术口径（写死在工单里，出图轮不许自造风格）
STYLE = (
    "mobile game app icon, square, bold flat illustration, single centered subject, "
    "vibrant colors, clean silhouette readable at small size, no text, no watermark, "
    "subtle rounded highlight, casual game art style"
)
BANNED_SOURCES = ("签章",)


def latest_pack():
    packs = sorted(glob.glob(os.path.join(OUTDIR, "SUBMIT-PACK-????????.json")))
    if not packs:
        raise SystemExit("no SUBMIT-PACK found; run game_submit_pack.py first")
    return packs[-1]


def theme_line(product_dir):
    """读产品目录下的软件设计说明书首段，提炼一句主题。"""
    for f in glob.glob(os.path.join(SW, product_dir, "*设计说明书*")):
        if not f.endswith(".md"):
            continue
        try:
            txt = open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        m = re.search(r"软件概述", txt)
        seg = txt[m.end():m.end() + 400] if m else txt[:400]
        seg = re.sub(r"\s+", " ", seg).strip()
        if seg:
            return seg[:200]
    return ""


def build_manifest():
    pack = json.load(open(latest_pack(), encoding="utf-8"))
    jobs, done = [], []
    for it in pack.get("items", []):
        if "图标≥256px" not in it.get("lacks", []):
            done.append(it["dir"])
            continue
        theme = theme_line(it["dir"])
        jobs.append({
            "dir": it["dir"],
            "product": it["product"],
            "theme": theme,
            "icon_path": os.path.join(SW, it["dir"], "icon_512.png"),
            "prompt_hint": "%s | %s" % (it["product"], theme or "casual mini game"),
            "style": STYLE,
            "status": "PENDING",
        })
    out = os.path.join(OUTDIR, "ICON-JOBS-%s.json" % time.strftime("%Y%m%d"))
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "source": os.path.basename(latest_pack()),
           "need": len(jobs), "already_ok": len(done), "jobs": jobs,
           "rules": {
               "size": "1024x1024 generated, resized to 512x512 png on save",
               "name": "icon_512.png at product dir root",
               "credit_note": "L0 出图轮消耗 WorkBuddy 出图额度，约 5-10 credits/张；批量前需 CEO 确认规模",
               "banned_sources": list(BANNED_SOURCES),
           }}
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("need=%d already_ok=%d wrote %s" % (len(jobs), len(done), os.path.relpath(out, ROOT)))
    return 0 if not jobs else 2


def real_size(p):
    try:
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", p],
                             capture_output=True, text=True, timeout=10).stdout
        w = h = 0
        for line in out.splitlines():
            if "pixelWidth" in line:
                w = int(line.split()[-1])
            if "pixelHeight" in line:
                h = int(line.split()[-1])
        return w, h
    except Exception:
        return 0, 0


def verify():
    pack = json.load(open(latest_pack(), encoding="utf-8"))
    rows, bad = [], []
    for it in pack.get("items", []):
        if "图标≥256px" not in it.get("lacks", []):
            continue
        d = os.path.join(SW, it["dir"])
        found = []
        for root, _dirs, files in os.walk(d):
            for f in files:
                low = f.lower()
                if not low.endswith((".png", ".jpg", ".jpeg")):
                    continue
                if not any(k in low for k in ("icon", "logo", "appicon")):
                    continue
                w, h = real_size(os.path.join(root, f))
                found.append({"file": f, "w": w, "h": h, "ok": w >= 256 and h >= 256})
        ok = any(x["ok"] for x in found)
        rows.append({"dir": it["dir"], "ok": ok, "icons": found})
        if not ok:
            bad.append(it["dir"])
    out = os.path.join(OUTDIR, "ICON-RECEIPT-%s.json" % time.strftime("%Y%m%d"))
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "source": os.path.basename(latest_pack()),
               "checked": len(rows), "ok": len(rows) - len(bad), "bad": bad, "rows": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("checked=%d ok=%d bad=%d wrote %s" % (len(rows), len(rows) - len(bad), len(bad),
                                                os.path.relpath(out, ROOT)))
    for b in bad[:10]:
        print("  BAD", b)
    return 0 if not bad else 2


def main(argv):
    if "--manifest" in argv:
        return build_manifest()
    if "--verify" in argv:
        return verify()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
