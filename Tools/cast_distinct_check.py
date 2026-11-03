# -*- coding: utf-8 -*-
"""cast_distinct_check.py - 角色特点机检（CAST-DISTINCTIVENESS-LAW-v1 §二）。

为什么要有它：8 型女主的提示词是人写的，靠自觉就会出现"只换衣服没换脸"，
到出图才发现就白烧一轮 ComfyUI。这里只看文本：结构锚写没写清、跨型三元组撞不撞。

判据（全部可机判）：
1. 每型必须写清 ≥3 个结构锚字段（脸/眼/鼻/唇/发/体型）
2. 脸型、眼型、发型三项必须带限定词（写了字段但没写清=不合格）
3. 同一份清单内任意两型的（脸型, 眼型, 发型）三元组不得完全相同

用法：
  python Tools/cast_distinct_check.py --all              # 查队列里全部 job
  python Tools/cast_distinct_check.py --only T05         # 只查一型
  python Tools/cast_distinct_check.py --all --json out.json

退出码：0 = 全合格；2 = 有不合格项（不许烧卡）；3 = 输入缺失。
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "cph4", "fleet", "mv-lora", "LORA-TRAIN-QUEUE-v1.json")

# 字段 → (出现判据, 取值分类器)。分类器返回 None 表示"写了字段但没写清"。
FACE_RULES = [
    ("small_face_jawline", r"small face[^,.;]*jawline"),
    ("long_narrow", r"long narrow face"),
    ("cheekbone", r"high cheekbones"),
    ("rounded", r"(?:gently )?rounded face"),
    ("oval", r"oval face"),
    ("narrow", r"narrow face(?!d)"),
]
EYE_RULES = [
    ("rounded_almond", r"rounded[- ]almond eyes"),
    ("wide_set", r"wide[- ]set[^,.;]*eyes"),
    ("bright_round", r"bright round eyes"),
    ("long_narrow", r"long narrow eyes"),
    ("downcast", r"calm eyes[^,.;]*looking down"),
    ("smiling_curve", r"eyes curving into a smile"),
    ("upturned_almond", r"upturned almond eyes"),
    ("heavy_lidded", r"heavy[- ]lidded[^,.;]*eyes"),
]
HAIR_RULES = [
    ("blunt_fringe", r"blunt full fringe|blunt at the ends"),
    ("centre_part", r"centre[- ]parted long straight hair"),
    ("half_tied", r"half[- ]tied[^,.;]*hair"),
    ("bob", r"bob cut|chin[- ]length bob"),
    ("high_ponytail", r"high ponytail"),
    ("low_ponytail", r"low ponytail"),
    ("tucked", r"tucked behind one ear"),
    ("wet", r"wet hair"),
]
OTHER_FIELDS = {
    "nose": r"\bnose\b",
    "lips": r"\blips\b",
    "build": r"\bsmall face\b|\bhigh cheekbones\b|\bdelicate features\b",
}


def classify(text, rules):
    for name, pat in rules:
        if re.search(pat, text, re.I):
            return name
    return None


def has_field(text, pat):
    return bool(re.search(pat, text, re.I))


def judge(job):
    base = job.get("base") or ""
    face = classify(base, FACE_RULES)
    eyes = classify(base, EYE_RULES)
    hair = classify(base, HAIR_RULES)
    extra = [k for k, pat in OTHER_FIELDS.items() if has_field(base, pat)]
    anchors = sum(1 for v in (face, eyes, hair) if v) + len(extra)

    gaps = []
    if not face:
        gaps.append("脸型没写清（缺 long narrow / rounded / oval 这类限定词）")
    if not eyes:
        gaps.append("眼型没写清（缺 wide-set / rounded-almond / long narrow 这类限定词）")
    if not hair:
        gaps.append("发型没写清（缺 fringe / ponytail / bob 这类限定词）")
    if anchors < 3:
        gaps.append("结构锚只有 %d 项，要求 ≥3（脸/眼/鼻/唇/发/体型）" % anchors)

    return {
        "id": job.get("id"),
        "type": job.get("name"),
        "triple": [face or "?", eyes or "?", hair or "?"] if (face or eyes or hair) else None,
        "anchors": anchors,
        "gaps": gaps,
        "ok": not gaps,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    if not os.path.exists(QUEUE):
        print("BLOCKED queue missing: %s" % QUEUE)
        return 3
    q = json.load(open(QUEUE, encoding="utf-8"))
    jobs = sorted(q.get("jobs", []), key=lambda j: j.get("order", 0))
    if a.only:
        jobs = [j for j in jobs if j.get("id") == a.only]
        if not jobs:
            print("BLOCKED no such job: %s" % a.only)
            return 3

    rows = [judge(j) for j in jobs]

    # 跨型撞脸：三元组完全相同
    seen = {}
    for r in rows:
        if not r["triple"] or "?" in r["triple"]:
            continue
        key = tuple(r["triple"])
        seen.setdefault(key, []).append(r["id"])
    for key, ids in seen.items():
        if len(ids) > 1:
            for r in rows:
                if r["id"] in ids:
                    r["gaps"].append("与 %s 三元组相同（%s）" % (
                        ",".join([i for i in ids if i != r["id"]]), "/".join(key)))
                    r["ok"] = False

    bad = [r for r in rows if not r["ok"]]
    for r in rows:
        mark = "OK  " if r["ok"] else "FAIL"
        print("%s %-4s %-6s anchors=%d triple=%s" % (
            mark, r["id"], r["type"], r["anchors"],
            "/".join(r["triple"]) if r["triple"] else "-"))
        for g in r["gaps"]:
            print("       - " + g)
    print("\n共 %d 型，合格 %d，不合格 %d" % (len(rows), len(rows) - len(bad), len(bad)))

    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump({"rows": rows, "bad": [r["id"] for r in bad]},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main())