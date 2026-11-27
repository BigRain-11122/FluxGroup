# -*- coding: utf-8 -*-
"""face_natural_collect.py — 按「自然美名单」采集+挑人+建集（网络+CPU，不碰 GPU）。

2026-11-18 CEO 令：不再死磕冷门老艺人；多找大家喜欢的网红/素人，**不要科技脸，要自然美女**。
名单=cph4/fleet/mv-album-001-jay/casting-pool-natural-v1.json（key=nt01..，与 180 人名单不撞车）。

关于「自然度」：自动判整容脸/重度美颜在本机没有可靠模型，硬造阈值只会误杀。
这里只做两件事：①采集端避开"网红脸/整容/美颜"类词，只走写真/日常/采访向；
②每人出一条抽检板（media/faces/_boards/ntNN.jpg），自然与否交人眼定——
按 2026-11-16 那条纪律：数字过闸 ≠ 人眼过，人脸类结论必须看图。

用法：
  py Tools/face_natural_collect.py --limit 6
  py Tools/face_natural_collect.py --only nt01,nt04
"""
import argparse
import json
import os
import sys
import time

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
TOOLS = os.path.join(ROOT, "Tools")
FACES = os.path.join(ROOT, "media", "faces")
POOL = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "casting-pool-natural-v1.json")
STATE = os.path.join(FACES, "_batch-state.json")
IMG = (".jpg", ".jpeg", ".png", ".webp")

sys.path.insert(0, TOOLS)
import face_source_batch as B  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 只走"自然感"方向的词；刻意不含 网红脸/整容/美颜/精修/滤镜
# 2026-11-18 精简：原 20 词 × 3 页 = 每人 20-30 分钟，46 人跑不完。
# 保留命中率最高的 10 个——写真/日常/街拍/采访这四类覆盖了绝大部分可用图。
TERMS = "写真,写真集,日常,街拍,素颜,清纯,淡妆,采访,杂志,早期"


def count(d):
    return sum(1 for f in os.listdir(d) if f.lower().endswith(IMG)) if os.path.isdir(d) else 0


def built(key):
    ds = os.path.join(FACES, key + "-ds")
    n = 0
    for base, _, files in os.walk(ds):
        n += sum(1 for f in files if f.lower().endswith(IMG))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default=POOL, help="名单 JSON（可指向 natural / distinct 池）")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--target", type=int, default=60, help="每人过闸可用目标（够训即可，不必追量）")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--min-side", type=int, default=600)
    a = ap.parse_args()

    pool = json.load(open(a.pool, encoding="utf-8"))
    alias = pool.get("alias") or {}
    people = []
    famof = {}
    for fam in pool["families"]:
        if fam.get("id") == "kr":
            continue
        for i, nm in enumerate(fam.get("internal_index_only") or [], 1):
            key = "%s%02d" % (fam["id"], i)
            people.append((key, nm))
            famof[key] = fam["id"]
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    if only:
        people = [p for p in people if p[0] in only]
    else:
        people = [p for p in people if built(p[0]) < 40]
    if a.limit:
        people = people[:a.limit]
    if not people:
        print("没有需要采的人")
        return 0

    if not B.acquire_lock():
        print("[skip] 另一路备料在跑（_batch.lock）")
        return 1
    st = B.load_state()
    try:
        print("待采 %d 人（自然美名单）" % len(people), flush=True)
        for i, (key, name) in enumerate(people, 1):
            t0 = time.time()
            outdir = os.path.join(FACES, key)
            al = alias.get(name, "")
            raw_n = count(os.path.join(outdir, "raw"))
            # 360 对一个人通常只有 100-200 条，采过一次就到顶；重复下载只是把同一批图再拉一遍。
            # 已有 50 张以上就跳过图片阶段，直接挑+建+视频补（视频才是增量）。
            if raw_n < 50:
                cmd = [B.PY, B.COLLECT, "collect", "--person", name,
                       "--pages", str(a.pages), "--want-links", "500",
                       "--target", str(a.target), "--min-side", str(a.min_side),
                       "--terms", TERMS, "--out", outdir]
                if al:
                    cmd += ["--alias", al]
                B.run(cmd, timeout=1800)
            else:
                print("    [跳过图片] %s 已有 raw %d 张，直接挑+视频补" % (name, raw_n), flush=True)
            cur = B.curate_one({"key": key, "name": name})
            made = B.build_one({"key": key, "name": name})
            c = cur[0] if isinstance(cur, tuple) else cur
            m = made[0] if isinstance(made, tuple) else made
            # 图片建成不足 20 张时立刻走视频源（2026-11-18 实测：同一支 MV/剧集片段是
            # 天然干净簇，救回了古畑奈和 0→14、女德尔·塔图 0→10、中谷美纪 0→8）。
            if m < 20:
                vcmd = [B.PY, os.path.join(TOOLS, "face_video_collect.py"),
                        "--person", name, "--max-videos", "5", "--max-sec", "240",
                        "--fps", "0.33", "--out", key]
                if al:
                    vcmd += ["--alias", al]
                print("    [视频补] %s 建成 %d < 20，抽帧补足" % (name, m), flush=True)
                B.run(vcmd, timeout=1800)
                cur = B.curate_one({"key": key, "name": name})
                made = B.build_one({"key": key, "name": name})
                c = cur[0] if isinstance(cur, tuple) else cur
                m = made[0] if isinstance(made, tuple) else made
            e = st.setdefault(key, {})
            e.update({"name": name, "family": famof.get(key, "nt"), "curated": c, "built": m,
                      "trigger": key, "raw": count(os.path.join(outdir, "raw")),
                      "dataset": os.path.join(FACES, key + "-ds"),
                      "updated": "2026-11-18",
                      "status": "ok" if m >= 40 else ("low" if m >= 20 else "insufficient")})
            with open(STATE, "w", encoding="utf-8") as f:
                json.dump(st, f, ensure_ascii=False, indent=1)
            print("[%d/%d] %-6s %-10s 挑 %d · 建成 %d · %.0fs"
                  % (i, len(people), key, name, c, m, time.time() - t0), flush=True)
    finally:
        B.release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
