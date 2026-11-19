#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""segment_fill.py - 按"人群缺口"定向找视频，把缺料段的人喂进来。

决策依据（2026-11-19）：本线是 GPU 密集（训练 3.0-3.5s/步、出稿 3-8s/条），
CPU 侧的活（48k 行加工）只要 0.3 秒——硬塞 ASR 那类活属"造假活"。
真正卡住的是**语料结构**：PASS 仅 17%、generic 75%、6 个段缺料
（family 9 / traditional 1 / critic 31 / requester 37 / student 48 / beginner 51）。
所以把机器时间花在"按缺口找视频"上：既吃 CPU/IO，又直接抬高段位覆盖。

关键词→人群的映射来自 AUDIENCE-SEGMENTS 的 signals（不另发明词表）。

用法：
  .venv-housing/bin/python Tools/fleet/segment_fill.py --top 3            # 补最缺的三段
  .venv-housing/bin/python Tools/fleet/segment_fill.py --seg family --dry
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
PERSONAS = os.path.join(SOCIAL, "SEGMENT-PERSONAS-v1.json")
STATE = os.path.join(ROOT, ".codely-cli", "state")
PY = sys.executable

# 每段给 1-2 个"能招来这群人"的搜索词（由 signals 派生，外加场景词）
GAP_KEYWORDS = {
    "beginner": ["零基础 剪辑教程", "新手 剪映 入门"],
    "student": ["学生党 剪辑", "宿舍 拍视频 剪辑"],
    "requester": ["求 BGM 剪辑", "求 素材 剪辑 教程"],
    "critic": ["剪辑 翻车", "调色 崩了"],
    "family": ["亲子 vlog 剪辑", "家庭 记录 视频"],
    "traditional": ["MV 剪輯 教學", "剪片 教學 台灣"],
}


def gaps(top=3):
    try:
        d = json.load(open(PERSONAS, encoding="utf-8"))
    except Exception:
        return []
    segs = d.get("segments") or {}
    lack = [((v.get("n") or 0), k) for k, v in segs.items() if v and v.get("insufficient")]
    lack.sort()
    return [k for _, k in lack[:top]]


def fill(seg, dry=False):
    kws = GAP_KEYWORDS.get(seg) or []
    out = {"seg": seg, "keywords": kws, "urls": 0, "why": ""}
    for kw in kws:
        if dry:
            out["why"] = "dry"
            continue
        p = subprocess.run([PY, os.path.join(HERE, "social_collect.py"),
                            "--discover-public", kw], cwd=ROOT,
                           capture_output=True, text=True, timeout=600)
        txt = (p.stdout or "") + (p.stderr or "")
        n = 0
        for line in txt.splitlines():
            if "发现" in line and "公开视频" in line:
                try:
                    n = int(line.split("发现")[1].split("个")[0].strip())
                except Exception:
                    n = 0
        out["urls"] += n
        out["why"] += ("%s→%d " % (kw, n))
        time.sleep(5)      # 搜索之间留间隔，别把风控招来
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--seg", default="")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    segs = [a.seg] if a.seg else gaps(a.top)
    if not segs:
        print("[fill] 没有缺料段（或画像件缺失）")
        return 0
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "filled": []}
    for s in segs:
        r = fill(s, dry=a.dry)
        rec["filled"].append(r)
        print("[fill] %-12s 关键词 %s → 新增源 %d（%s）"
              % (s, r["keywords"], r["urls"], r["why"].strip() or "-"))
    os.makedirs(STATE, exist_ok=True)
    path = os.path.join(STATE, "segment-fill-%s.json" % time.strftime("%Y%m%d-%H%M%S"))
    json.dump(rec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[fill] 记账 %s" % os.path.relpath(path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
