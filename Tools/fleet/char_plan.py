#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""角色包出图计划器：把 CHARACTERS-V1.json 变成可执行的提示词包（确定性，不调模型）。

为什么要有这一层：直接让模型"随便出 20 张脸"，出的一定是同一种 AI 脸。
角色包的可复用性来自「设定卡固定 + 视角固定 + 缺陷固定」，出图只是执行。
本工具只做拼装：角色设定 × 视角 × 负面词 × 一致性锚点 → 每角色一份 JSON 提示词包。

产物：media/asset/characters/<ID>/PROMPTS.json（每角色 12 视角）
     cph4/fleet/queue-receipts/char-gen-plan-<date>.json（汇总回执，进 git）

用法：
  python3 Tools/fleet/char_plan.py                 # 只生成提示词包
  python3 Tools/fleet/char_plan.py --only CH03     # 单个角色
"""

import argparse
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1", "CHARACTERS-V1.json")
OUTBASE = os.path.join(ROOT, "media", "asset", "characters")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")

VIEW_TEXT = {
    "front": "front view, looking straight at camera, neutral expression, head and shoulders",
    "three_quarter_left": "three-quarter view turned 45 degrees to viewer's left, neutral expression",
    "three_quarter_right": "three-quarter view turned 45 degrees to viewer's right, neutral expression",
    "profile_left": "full side profile facing viewer's left, neutral expression",
    "profile_right": "full side profile facing viewer's right, neutral expression",
    "back": "back view, showing hair length and clothing back",
    "expression_soft": "front view, soft restrained smile, eyes relaxed",
    "expression_smile": "front view, open genuine smile, eyes crinkled",
    "expression_tense": "front view, tense jaw, lips pressed, slight frown",
    "low_angle": "camera slightly below eye level looking up, head and shoulders",
    "high_angle": "camera slightly above eye level looking down, head and shoulders",
    "mid_shot": "waist-up mid shot, relaxed posture, hands out of frame",
}

# 12 视角是数据集准入闸的下限（ASSET-DATASET-GATE-v1 / LIBRARY-TARGETS p0.ref_images_min=12）。
# 6 视角恒定 passed=0（2026-11-04 实证：8 角色各 6 张全部 FAIL「张数 6 < 12」），故补足到 12。
VIEWS = ("front", "three_quarter_left", "three_quarter_right", "profile_left", "profile_right",
         "back", "expression_soft", "expression_smile", "expression_tense",
         "low_angle", "high_angle", "mid_shot")


def build(c):
    head = ("photorealistic portrait of a %d year old %s %s, %s, original character design, "
            "%s, %s, %s, %s" % (c["age"], c["region"], c["gender"], c["role"],
                                c["build"], c["face"], c["skin"], c["hair"]))
    prompts = {}
    for v in VIEWS:
        prompts[v] = {
            "positive": "%s, %s, wearing %s, %s, natural window light, 85mm, shallow depth of field, "
                        "visible skin texture with pores and uneven tone, film grain" % (head, VIEW_TEXT[v], c["outfit"], v),
            "negative": ("airbrushed skin, plastic skin, perfect symmetry, doll face, over-smooth, "
                         "heavy makeup, celebrity likeness, real person, watermark, text, logo, "
                         "extra fingers, deformed ears"),
        }
    return {
        "character": c["id"], "name": c["name"], "views": prompts,
        "consistency": {"seed": int(hashlib.sha1(c["id"].encode("utf-8")).hexdigest()[:8], 16) % 2147483647,
                        "anchors": [c["face"], c["skin"], c["flaw"]],
                        "note": "同一角色 12 视角必须同 seed 组 + 同一 LoRA/参考图；跨视角不许改缺陷"},
        "dataset_meta": {"source": "own_generated", "license": "own", "real_person": False,
                         "consent": None, "flaw_markers": c["flaw"], "avoids": c["avoids"]},
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    spec = json.load(open(SPEC, encoding="utf-8"))
    # CHARACTERS-V1.json 的设计字段是中文，SDXL 读不懂会出成通用脸；有英译就覆盖过去。
    en_path = os.path.join(os.path.dirname(SPEC), "CHARACTERS-EN-v1.json")
    if os.path.exists(en_path):
        try:
            en = json.load(open(en_path, encoding="utf-8")).get("characters") or {}
        except Exception:
            en = {}
        for c in spec["characters"]:
            c.update({k: v for k, v in (en.get(c["id"]) or {}).items() if v})
    made, summary = [], []
    for c in spec["characters"]:
        if a.only and c["id"] != a.only:
            continue
        pack = build(c)
        d = os.path.join(OUTBASE, c["id"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "PROMPTS.json"), "w", encoding="utf-8") as f:
            json.dump(pack, f, ensure_ascii=False, indent=1)
        made.append(c["id"])
        summary.append({"character": c["id"], "name": c["name"], "views": len(pack["views"]),
                        "dir": os.path.relpath(d, ROOT)})
    # 出图需要的授权声明：RIGHTS.json（数据集准入闸会读它）
    rights = os.path.join(OUTBASE, "RIGHTS.json")
    if not os.path.exists(rights):
        with open(rights, "w", encoding="utf-8") as f:
            json.dump({"source": "own_generated", "license": "own", "real_person": False,
                       "consent": None,
                       "note": "全部为原创角色设计，无真人照片输入；如需真人素材必须本人书面授权"},
                      f, ensure_ascii=False, indent=1)
    os.makedirs(RECEIPTS, exist_ok=True)
    op = os.path.join(RECEIPTS, "char-gen-plan-%s.json" % time.strftime("%Y-%m-%d"))
    with open(op, "w", encoding="utf-8") as f:
        json.dump({"rc": 0, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                   "characters": summary, "views_per_character": len(VIEWS),
                   "total_images_needed": len(summary) * len(VIEWS)}, f, ensure_ascii=False, indent=1)
    print("char-plan: %d 角色 × %d 视角 = %d 张" % (len(summary), len(VIEWS), len(summary) * len(VIEWS)))
    print("wrote PROMPTS.json ->", os.path.relpath(OUTBASE, ROOT))
    print("receipt", os.path.relpath(op, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))