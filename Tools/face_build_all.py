# -*- coding: utf-8 -*-
"""face_build_all.py — 把已挑好的 curated 建成训练数据集（含 caption），不训练、不碰 GPU。

为什么触发词用批次 key（ql01 / tm03 …）而不是统一的 ohwx_woman：
  180 个人各训一条 LoRA，如果共用同一个 token，推理时会互相抢占同一个词面，
  等于没区分。每人一个独占 token 是唯一能并行使用的前提。

用法：
  py Tools/face_build_all.py                 # 全部 curated>=20 的批次
  py Tools/face_build_all.py --min 40        # 只建达标的
  py Tools/face_build_all.py --only ql05,tm01
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
FACES = os.path.join(ROOT, "media", "faces")
PREP = os.path.join(ROOT, "Tools", "face_lora_prep.py")
STATE = os.path.join(FACES, "_batch-state.json")
PY = r"C:\Users\sjs20\train-lora\.venv\Scripts\python.exe"
IMG = (".jpg", ".jpeg", ".png", ".webp")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=20, help="curated 张数下限")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    st = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}

    todo = []
    for name in sorted(os.listdir(FACES)):
        d = os.path.join(FACES, name)
        if not os.path.isdir(d) or name.startswith(("_", ".")) or name.endswith("-ds"):
            continue
        if not re.match(r"^[a-z]{2}\d\d$", name):
            continue
        if only and name not in only:
            continue
        cur = os.path.join(d, "curated")
        if not os.path.isdir(cur):
            continue
        n = sum(1 for f in os.listdir(cur) if f.lower().endswith(IMG))
        if n >= a.min:
            todo.append((name, n))

    print("待建 %d 人（curated>=%d）" % (len(todo), a.min), flush=True)
    ok = 0
    for name, n in todo:
        out = os.path.join(FACES, name + "-ds")
        t0 = time.time()
        p = subprocess.run([PY, PREP, "build", os.path.join(FACES, name, "curated"),
                            "--out", out, "--trigger", name], capture_output=True)
        txt = (p.stdout or b"").decode("utf-8", "replace")
        if "生成" not in txt:
            txt = (p.stdout or b"").decode("gbk", "replace")
        made = 0
        m = re.search(r"生成 (\d+) 张", txt)
        if m:
            made = int(m.group(1))
        else:
            made = sum(1 for f in os.listdir(out) if f.lower().endswith(IMG)) if os.path.isdir(out) else 0
        if made >= a.min:
            ok += 1
        k = st.setdefault(name, {})
        k["trigger"] = name
        k["built"] = made
        k["dataset"] = out
        k["built_at"] = "2026-11-18"
        print("%-8s curated=%3d  建成=%3d  %4.1fs" % (name, n, made, time.time() - t0), flush=True)

    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n合计建成 %d/%d 人（每人独立触发词=批次 key）" % (ok, len(todo)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
