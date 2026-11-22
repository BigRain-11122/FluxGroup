#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_kf_plan.py — D3 关键帧的「剧本 → prompt 表」生成器（产线第一个真断点）。

为什么（2026-11-20 实测）：PROD-DRAMA-EP 的 kf 工序命令指向
  cph4/fleet/out/drama/kf_prompts.json
但全仓没有任何工序产出这个文件，`cph4/fleet/out/drama/` 整目录都不存在。
MSG-20261114-2340 已把这条报给主控（drama-kf 卡连续 rc=1 的真因），至今无人补。
档位：本文件=补缺口，不是新立法。

输入：`cph4/fleet/drama-001-stockera/episodes/EP*.json`
       schema = {ep, title, shots:[{n, dur, kind(in|slow|card), ids[], detail_en, sub, speaker, fx, card}]}
输出：`cph4/fleet/out/drama/<ep>/kf_prompts.json`
       [{id, ep, n, seed, prompt, negative, shot, angle, scene, light, grade, texture,
         dur, sub, speaker, fx, ids, kind, words}]

用法：
  python Tools/fleet/drama_kf_plan.py --eps 1                 # 单集
  python Tools/fleet/drama_kf_plan.py --eps 1-3               # 区间
  python Tools/fleet/drama_kf_plan.py --eps all --out-root cph4/fleet/out/drama
  python Tools/fleet/drama_kf_plan.py --eps 1 --compact       # SD1.5 77-token 压档

铁律：
  - card 镜不产 KF（字卡=装配面·60 集判例）
  - 种子确定性 91000000 + ep*100 + n（与 epburn 线同源，可复刻）
  - 角色锚一律走 drama_canon（单一真值源）
Exit: 0 = 已写出；2 = 没有可用剧本；3 = 某集零可用镜（仍写出空表，供下游判 BLOCKED）
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import drama_canon as C  # noqa: E402

DEFAULT_EPS = os.path.join(ROOT, "cph4", "fleet", "drama-001-stockera", "episodes")
DEFAULT_OUT = os.path.join(ROOT, "cph4", "fleet", "out", "drama")


def parse_eps(txt, eps_dir):
    txt = (txt or "").strip().lower()
    if txt in ("all", "*"):
        nums = sorted(int(f[2:5]) for f in os.listdir(eps_dir)
                      if f.startswith("EP") and f.endswith(".json") and f[2:5].isdigit()
                      and not f.endswith(".off-canon"))
        return nums
    if "-" in txt:
        lo, hi = txt.split("-", 1)
        return list(range(int(lo), int(hi) + 1))
    if "," in txt:
        return [int(x) for x in txt.split(",") if x.strip()]
    return [int(txt)]


def plan_episode(ep, eps_dir, compact=False):
    pj = os.path.join(eps_dir, "EP%03d.json" % ep)
    if not os.path.isfile(pj):
        return None, "EP_JSON_MISSING"
    spec = json.load(open(pj, encoding="utf-8"))
    rows = []
    for s in spec.get("shots", []):
        kind = s.get("kind", "in")
        if kind == "card":
            continue
        n = s.get("n")
        detail = s.get("detail_en") or ""
        if not detail.strip():
            continue
        ids = s.get("ids") or []
        shot, angle = C.shot_tokens(detail, ids)
        rows.append({
            "id": "EP%03d_%02d" % (ep, n),
            "ep": ep,
            "n": n,
            "seed": 91000000 + ep * 100 + n,
            "prompt": C.expand(detail, ids, compact=compact),
            "negative": C.NEG,
            "shot": shot,
            "angle": angle,
            "move": C.move_token(detail),
            "scene": C.scene_token(detail),
            "light": ("night" if any(k in detail.lower() for k in ("night", "rain", "dark")) else "day"),
            "grade": "tw90s_noir",
            "texture": "film_grain",
            "dur": s.get("dur", 0),
            "sub": s.get("sub") or "",
            "speaker": s.get("speaker") or "",
            "fx": s.get("fx") or "",
            "ids": ids,
            "kind": kind,
            "words": len(C.expand(detail, ids, compact=compact).split()),
        })
    return rows, ("OK" if rows else "ZERO_SHOTS")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", default="all", help="1 | 1-3 | 1,2,5 | all")
    ap.add_argument("--eps-dir", default=DEFAULT_EPS)
    ap.add_argument("--out-root", default=DEFAULT_OUT)
    ap.add_argument("--compact", action="store_true", help="SD1.5 77-token 压档")
    ap.add_argument("--limit", type=int, default=0, help="每集最多多少镜（排障用）")
    a = ap.parse_args(argv)

    if not os.path.isdir(a.eps_dir):
        print("PLAN ABORT eps dir missing: %s" % a.eps_dir)
        return 2
    eps = parse_eps(a.eps, a.eps_dir)
    if not eps:
        print("PLAN ABORT no episodes")
        return 2

    total = 0
    bad = []
    for ep in eps:
        rows, status = plan_episode(ep, a.eps_dir, a.compact)
        if rows is None:
            bad.append((ep, status))
            print("EP%03d %s" % (ep, status))
            continue
        if a.limit:
            rows = rows[:a.limit]
        out_dir = os.path.join(a.out_root, "EP%03d" % ep)
        os.makedirs(out_dir, exist_ok=True)
        outp = os.path.join(out_dir, "kf_prompts.json")
        json.dump(rows, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        total += len(rows)
        print("EP%03d %s shots=%d words_max=%d -> %s" % (
            ep, status, len(rows), max([r["words"] for r in rows] or [0]),
            os.path.relpath(outp, ROOT)))
    print("PLAN TOTAL episodes=%d shots=%d bad=%d" % (len(eps) - len(bad), total, len(bad)))
    return 0 if total else 3


if __name__ == "__main__":
    sys.exit(main())
