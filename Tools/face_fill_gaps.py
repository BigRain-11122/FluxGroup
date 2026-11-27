# -*- coding: utf-8 -*-
"""face_fill_gaps.py — 只对"数据集不够"的人补采，采完立刻重挑重建（网络+CPU，不碰 GPU）。

为什么单写一个：batch 的 --retry-low 按 curated 张数判断，而真正卡住训练的是
**build 之后的张数**（curate 过了还要过清晰度/侧脸/脸宽三关）。这里直接用 built 判断，
并且复用 batch 的别名表——日系人物靠原名（沢尻エリカ / 中条あやみ）才有图。

用法：
  py Tools/face_fill_gaps.py                 # 全部 built<20 的人
  py Tools/face_fill_gaps.py --limit 10      # 先做最缺的 10 个
  py Tools/face_fill_gaps.py --only rx03,rx05
  py Tools/face_fill_gaps.py --rounds 2 --min-side 800
"""
import argparse
import json
import os
import sys
import time

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
sys.path.insert(0, os.path.join(ROOT, "Tools"))
import face_source_batch as B  # noqa: E402  复用别名表/采集/挑选/建集

FACES = os.path.join(ROOT, "media", "faces")
IMG = (".jpg", ".jpeg", ".png", ".webp")


def built_count(key):
    ds = os.path.join(FACES, key + "-ds")
    n = 0
    for base, _, files in os.walk(ds):
        n += sum(1 for f in files if f.lower().endswith(IMG))
    return n


def raw_count(key):
    p = os.path.join(FACES, key, "raw")
    return sum(1 for f in os.listdir(p) if f.lower().endswith(IMG)) if os.path.isdir(p) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--min-side", type=int, default=600,
                    help="源图短边下限。别往高调：采集器按内容哈希命名，历史上调过 800 会删掉存量图")
    ap.add_argument("--goal", type=int, default=20, help="built 达到此数即视为够")
    a = ap.parse_args()

    if not B.acquire_lock():
        print("[skip] 另一路备料在跑（_batch.lock）")
        return 1
    try:
        people = {p["key"]: p for p in B.load_people()}
        st = B.load_state()
        only = {x.strip() for x in a.only.split(",") if x.strip()}
        todo = []
        for key, p in people.items():
            if only and key not in only:
                continue
            b = built_count(key)
            if b < a.goal:
                todo.append((b, raw_count(key), key, p))
        todo.sort(key=lambda t: (t[0], t[1]))     # 最缺的先采
        if a.limit:
            todo = todo[:a.limit]
        print("待补 %d 人（built<%d）" % (len(todo), a.goal), flush=True)

        for i, (b0, r0, key, p) in enumerate(todo, 1):
            t0 = time.time()
            B.TARGET = B.TARGET              # 保持模块级目标
            alias = B.ALIAS.get(p["name"], "")
            outdir = os.path.join(FACES, key)
            cmd = [B.PY, B.COLLECT, "collect", "--person", p["name"],
                   "--pages", "4", "--want-links", "600", "--target", str(B.TARGET),
                   "--min-side", str(a.min_side), "--out", outdir]
            if alias:
                cmd += ["--alias", alias]
            rc, out = B.run(cmd, timeout=1800)
            r1 = raw_count(key)
            cur = B.curate_one(p)
            made = B.build_one(p)
            k = st.setdefault(key, {})
            k["name"] = p["name"]
            k["family"] = p["family"]
            k["raw"] = r1
            k["curated"] = cur[0] if isinstance(cur, tuple) else cur
            k["built"] = made[0] if isinstance(made, tuple) else made
            k["trigger"] = key
            k["updated"] = "2026-11-18"
            k["status"] = "ok" if k["built"] >= 40 else ("low" if k["built"] >= 20 else "insufficient")
            B.save_state(st)
            print("[%d/%d] %-6s %-10s raw %d->%d · built %d->%d · %.0fs"
                  % (i, len(todo), key, p["name"], r0, r1, b0, k["built"], time.time() - t0), flush=True)
    finally:
        B.release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
