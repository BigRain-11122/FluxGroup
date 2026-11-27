#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collect_full_mv.py — 《爱在西元前》全量件接收器（bm-a → bm-c 走 git transfer/）。

收件规格（承 O 令 OB-20261124-223249-233）：
  transfer/INVENTORY.json          全量清单（先到）
  transfer/*.mp4                   单片（<=90MB，时长>=200s 视为全片）
  transfer/parts/ + MANIFEST.json  分片（sha256 + 顺序 + 还原命令）
  transfer/src/                    装配链源件（脚本/时间线/字幕/字层/title）
  transfer/BATCH-n-DONE.json       批次完成标记

每次调用：
  1) 有 INVENTORY → 统计件数与总体积写 status
  2) 有 manifest+parts → 校验 sha256 → concat → 落到 deliverable/
  3) 有单片全片 → 复制落 deliverable/
  4) 有 src/ → 逐件抄进 cph4/fleet/mv0001-handover/from-bma/（保留层级）
  5) 有 BATCH 标记 → 计入 status
永远 rc=0（收件是长期哨，找不到就是还没到）。
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = r"K:\Fluxgroup\FluxGroup"
TRANSFER = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "transfer")
DEST_DIR = os.path.join(ROOT, "media", "mv0001-handover", "deliverable")
INBOX_SRC = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "from-bma")
ART = os.path.join(ROOT, "cph4", "fleet", "selfmedia", "artifacts")
STATUS = os.path.join(ART, "full-mv-collect.json")
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FP = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"


def sha(p, limit=None):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
            if limit and f.tell() > limit:
                break
    return h.hexdigest()


def dur(p):
    try:
        o = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", p], capture_output=True, text=True, timeout=60).stdout
        return float(o.strip())
    except Exception:
        return 0.0


def main():
    os.makedirs(ART, exist_ok=True)
    st = {"scanned_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "transfer_exists": os.path.isdir(TRANSFER)}

    if not os.path.isdir(TRANSFER):
        json.dump(st, open(STATUS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("NO-TRANSFER-DIR（bm-a 尚未推送）")
        return 0

    files = sorted(os.listdir(TRANSFER))
    st["files"] = files

    # 1) 清单
    inv = os.path.join(TRANSFER, "INVENTORY.json")
    if os.path.exists(inv):
        try:
            d = json.load(open(inv, encoding="utf-8"))
            items = d if isinstance(d, list) else (d.get("files") or d.get("items") or [])
            tot = sum(int(i.get("bytes") or i.get("size") or 0) for i in items if isinstance(i, dict))
            st["inventory"] = {"items": len(items), "total_mb": round(tot / 1048576, 1)}
        except Exception as e:
            st["inventory_error"] = str(e)

    # 2) 分片
    man = os.path.join(TRANSFER, "MANIFEST.json")
    if os.path.exists(man):
        try:
            m = json.load(open(man, encoding="utf-8"))
            parts = m.get("parts") or m.get("chunks") or []
            paths, bad = [], []
            for p in parts:
                name = p if isinstance(p, str) else (p.get("file") or p.get("name"))
                want = "" if isinstance(p, str) else (p.get("sha256") or "")
                fp = os.path.join(TRANSFER, name) if os.path.isabs(name) is False else name
                if not os.path.exists(fp):
                    fp = os.path.join(TRANSFER, "parts", os.path.basename(name))
                if not os.path.exists(fp):
                    bad.append({"missing": name})
                    continue
                if want and sha(fp) != want.lower():
                    bad.append({"sha_mismatch": name})
                    continue
                paths.append(fp)
            st["manifest"] = {"parts": len(parts), "verified": len(paths), "bad": bad[:5]}
            if paths and not bad:
                out = os.path.join(DEST_DIR, "爱在西元前-全片-最新.mp4")
                os.makedirs(DEST_DIR, exist_ok=True)
                lst = os.path.join(ART, "concat.txt")
                with open(lst, "w", encoding="utf-8") as f:
                    for p in paths:
                        f.write("file '%s'\n" % p.replace("\\", "/"))
                subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst,
                                "-c", "copy", out], capture_output=True, timeout=3600)
                dd = dur(out)
                if dd >= 200:
                    st["collected"] = {"mode": "concat", "parts": len(paths),
                                       "out": os.path.relpath(out, ROOT),
                                       "duration_s": round(dd, 2),
                                       "bytes": os.path.getsize(out)}
        except Exception as e:
            st["manifest_error"] = str(e)

    # 3) 单片全片
    if "collected" not in st:
        for p in sorted(glob.glob(os.path.join(TRANSFER, "*.mp4")), key=os.path.getsize, reverse=True):
            d = dur(p)
            if d >= 200:
                out = os.path.join(DEST_DIR, "爱在西元前-全片-最新.mp4")
                os.makedirs(DEST_DIR, exist_ok=True)
                shutil.copy2(p, out)
                st["collected"] = {"mode": "single", "src": os.path.basename(p),
                                   "out": os.path.relpath(out, ROOT),
                                   "duration_s": round(d, 2), "bytes": os.path.getsize(out)}
                break

    # 4) 源件入库
    src = os.path.join(TRANSFER, "src")
    if os.path.isdir(src):
        n = 0
        for dp, dn, fn in os.walk(src):
            rel = os.path.relpath(dp, src)
            tgt = os.path.join(INBOX_SRC, rel) if rel != "." else INBOX_SRC
            os.makedirs(tgt, exist_ok=True)
            for f in fn:
                s = os.path.join(dp, f)
                t = os.path.join(tgt, f)
                if not os.path.exists(t) or os.path.getsize(t) != os.path.getsize(s):
                    shutil.copy2(s, t)
                    n += 1
        st["src_ingested"] = n

    # 4b) 直推收件口（artifact_intake）来的件
    intake_root = os.path.join(ROOT, "media", "inbox", "intake")
    got = []
    if os.path.isdir(intake_root):
        for dp, dn, fn in os.walk(intake_root):
            for f in fn:
                if not f.lower().endswith((".mp4", ".mov", ".mkv")):
                    continue
                if "MV0001" not in f and "mv0001" not in f and "西元前" not in f:
                    continue
                got.append(os.path.join(dp, f))
    if got:
        st["intake_videos"] = [{"file": os.path.basename(x),
                                "mb": round(os.path.getsize(x) / 1048576, 1)} for x in got]
        best = max(got, key=os.path.getsize)
        d = dur(best)
        st["intake_best_duration_s"] = round(d, 2)
        if d >= 200 and "collected" not in st:
            out = os.path.join(DEST_DIR, "爱在西元前-全片-最新.mp4")
            os.makedirs(DEST_DIR, exist_ok=True)
            shutil.copy2(best, out)
            st["collected"] = {"mode": "intake", "src": os.path.basename(best),
                               "out": os.path.relpath(out, ROOT),
                               "duration_s": round(d, 2), "bytes": os.path.getsize(out)}

    # 5) 批次标记
    batches = [f for f in files if f.startswith("BATCH-") and f.endswith("-DONE.json")]
    st["batches"] = batches

    json.dump(st, open(STATUS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("COLLECT scanned=%d files | inventory=%s | collected=%s | src=%s | batches=%d"
          % (len(files), st.get("inventory"), st.get("collected"),
             st.get("src_ingested", 0), len(batches)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
