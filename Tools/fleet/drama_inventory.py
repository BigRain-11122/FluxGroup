#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_inventory.py - 短剧/漫剧素材盘点：先找到真目录，再谈质检。

为什么（2026-11-03）：工序表把 TTS 目录写死成 media/drama-tts-batch，而各机实际目录名
不同（bm-b 的 media 在 D 盘），于是第一段就 rc=非零，整条线卡住。工序的第一步应该是
"这台机上到底有什么"，而不是假定路径存在。

用法：
  python drama_inventory.py [--root .] [--out cph4/fleet/queue-receipts/drama-inventory-DATE.json]
Exit: 0 总有结论（找到 0 个目录也 exit 0，报告写明扫了什么）。
"""
import argparse
import json
import os
import sys
import time

PAT = ("drama", "duanju", "tts", "mix", "ep", "episode", "配音", "混音")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    media = os.path.join(a.root, "media")
    found = []
    if os.path.isdir(media):
        for name in sorted(os.listdir(media)):
            p = os.path.join(media, name)
            if not os.path.isdir(p):
                continue
            low = name.lower()
            if not any(k in low for k in PAT):
                continue
            vids = auds = 0
            newest = 0
            for dirpath, _d, files in os.walk(p):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in (".mp4", ".mov", ".mkv"):
                        vids += 1
                    elif ext in (".wav", ".mp3", ".m4a", ".aac", ".flac"):
                        auds += 1
                    else:
                        continue
                    try:
                        newest = max(newest, os.path.getmtime(os.path.join(dirpath, f)))
                    except OSError:
                        pass
            found.append({"dir": p.replace("\\", "/"), "videos": vids, "audio": auds,
                          "newest": time.strftime("%Y-%m-%d %H:%M", time.localtime(newest)) if newest else None})
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "OK", "root": a.root,
           "media_exists": os.path.isdir(media), "dirs": found,
           "summary": {"dirs": len(found), "videos": sum(d["videos"] for d in found),
                       "audio": sum(d["audio"] for d in found)}}
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    print("[drama_inventory] media=%s 目录=%d 视频=%d 音频=%d"
          % ("有" if out["media_exists"] else "无", out["summary"]["dirs"],
             out["summary"]["videos"], out["summary"]["audio"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))