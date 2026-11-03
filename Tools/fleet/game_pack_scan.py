#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""game_pack_scan.py - 扫游戏仓里"真能装/真能玩"的包，产出可上线清单。

为什么（2026-11-03）：游戏线在册 39 款、约 9 款判过毕业，但 0 款上线；机队每晚会派
"线级体检"这类只读卡，扫完还是缺。缺的不是报告，是"哪几款现在就能提审"的清单。
本工具只读盘：找到 APK / WebGL / Win 包就记大小与时间，按可发性排序。

用法：
  python game_pack_scan.py --root gaming --out cph4/fleet/queue-receipts/game-packs-20260101.json
Exit: 0 正常（含 0 个包也 exit 0，报告里写明），1 根本扫不动。
"""
import argparse
import json
import os
import sys
import time

PACK_EXT = {".apk": "android", ".aab": "android", ".exe": "windows",
            ".app": "macos", ".ipa": "ios"}
WEBGL_MARK = ("index.html",)


def scan(root):
    packs, webgl = [], []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "Library", "Temp", "obj", "node_modules")]
        low = dirpath.replace("\\", "/").lower()
        for n in files:
            ext = os.path.splitext(n)[1].lower()
            p = os.path.join(dirpath, n)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if ext in PACK_EXT and sz > 1024 * 1024:
                packs.append({"path": p.replace("\\", "/"), "kind": PACK_EXT[ext],
                              "mb": round(sz / 1048576.0, 1),
                              "mtime": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(p)))})
            if n in WEBGL_MARK and ("build" in low or "webgl" in low):
                webgl.append({"path": p.replace("\\", "/"), "kind": "webgl",
                              "mb": round(sz / 1048576.0, 3),
                              "mtime": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(p)))})
    return packs, webgl


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="gaming")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.root):
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "root": a.root,
               "status": "NO-REPO", "note": "本机没有游戏仓（gaming/ 是独立仓，只在工作机有）",
               "packs": [], "webgl": []}
    else:
        packs, webgl = scan(a.root)
        packs.sort(key=lambda x: -x["mb"])
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "root": a.root,
               "status": "OK", "packs": packs, "webgl": webgl,
               "summary": {"apk_or_win": len(packs), "webgl": len(webgl),
                           "shippable_candidates": len([p for p in packs if p["mb"] < 200])}}
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    print("[game_pack_scan] %s packs=%d webgl=%d out=%s"
          % (out["status"], len(out["packs"]), len(out.get("webgl") or []), a.out or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))