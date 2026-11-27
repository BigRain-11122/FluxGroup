# -*- coding: utf-8 -*-
"""face_video_fill.py — 批量用视频抽帧补人，补完立刻重挑重建（网络+CPU，不碰 GPU）。

针对"图片搜索已采尽但数据集还差几张"的人：360 图库对同一个人通常只有 100-200 条，
反复重采是重复下载。视频源（老 MV/采访/剧集/写真花絮）能提供同一人连续多角度的帧，
实测 720p 下入帧率约 10%（118 帧过 12 张），一个人跑 6 个视频约能补 20-40 张候选。

按 built 升序处理——先救"差几张就够"的人，性价比最高。

用法：
  py Tools/face_video_fill.py --limit 6
  py Tools/face_video_fill.py --only tm01,tm06 --videos 6
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
TOOLS = os.path.join(ROOT, "Tools")
FACES = os.path.join(ROOT, "media", "faces")
STATE = os.path.join(FACES, "_batch-state.json")
PY = r"C:\Users\sjs20\train-lora\.venv\Scripts\python.exe"
VIDEO = os.path.join(TOOLS, "face_video_collect.py")
PREP = os.path.join(TOOLS, "face_lora_prep.py")
POOL = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "casting-pool-v1.json")
IMG = (".jpg", ".jpeg", ".png", ".webp")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def built_count(key):
    ds = os.path.join(FACES, key + "-ds")
    n = 0
    for base, _, files in os.walk(ds):
        n += sum(1 for f in files if f.lower().endswith(IMG))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--videos", type=int, default=6)
    ap.add_argument("--max-sec", type=int, default=240)
    ap.add_argument("--fps", type=float, default=0.33)
    ap.add_argument("--goal", type=int, default=20)
    a = ap.parse_args()

    pool = json.load(open(POOL, encoding="utf-8"))
    alias, names = {}, {}
    for fam in pool["families"]:
        if fam["id"] == "kr":
            continue
        for i, nm in enumerate(fam.get("internal_index_only") or [], 1):
            k = "%s%02d" % (fam["id"], i)
            names[k] = nm
    sys.path.insert(0, TOOLS)
    import face_source_batch as B
    alias = B.ALIAS

    st = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    todo = []
    for k, nm in names.items():
        if only and k not in only:
            continue
        b = built_count(k)
        if b < a.goal:
            todo.append((b, k, nm))
    todo.sort()
    todo = todo[:a.limit] if not only else todo
    print("待补 %d 人（视频源）" % len(todo), flush=True)

    for i, (b0, k, nm) in enumerate(todo, 1):
        t0 = time.time()
        cmd = [PY, VIDEO, "--person", nm, "--max-videos", str(a.videos),
               "--max-sec", str(a.max_sec), "--fps", str(a.fps), "--out", k]
        if alias.get(nm):
            cmd += ["--alias", alias[nm]]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        p = subprocess.run(cmd, capture_output=True, env=env,
                           creationflags=0x08000000 if os.name == "nt" else 0)
        txt = (p.stdout or b"").decode("utf-8", "replace")
        newly = ""
        for ln in txt.splitlines():
            if "合计本次新增" in ln:
                newly = ln.strip()
        cur = os.path.join(FACES, k, "curated")
        subprocess.run([PY, PREP, "curate", os.path.join(FACES, k, "raw"), "--out", cur,
                        "--keep", "45", "--board", os.path.join(FACES, "_boards", k + ".jpg")],
                       capture_output=True, creationflags=0x08000000 if os.name == "nt" else 0)
        ds = os.path.join(FACES, k + "-ds")
        subprocess.run([PY, PREP, "build", cur, "--out", ds, "--trigger", k],
                       capture_output=True, creationflags=0x08000000 if os.name == "nt" else 0)
        b1 = built_count(k)
        e = st.setdefault(k, {})
        e["name"] = nm
        e["built"] = b1
        e["trigger"] = k
        e["dataset"] = ds
        e["updated"] = "2026-11-18"
        e["status"] = "ok" if b1 >= 40 else ("low" if b1 >= 20 else "insufficient")
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
        print("[%d/%d] %-6s %-10s built %d->%d · %s · %.0fs"
              % (i, len(todo), k, nm, b0, b1, newly or "无新增", time.time() - t0), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
