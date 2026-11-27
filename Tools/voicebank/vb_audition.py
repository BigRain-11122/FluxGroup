# -*- coding: utf-8 -*-
"""vb_audition.py - build a listenable audition pack from screened candidates.

Acoustic scores can rank cleanliness and pitch, not taste. So for every shortlisted
candidate we cut a 12-second, loudness-normalised, 96 kbps mono clip into
voicebank/auditions/ plus an index the reviewer can scan. One listen replaces a
hundred numbers when choosing which voices to train.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

FFMPEG = r"C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe"
VB = os.environ.get("VB_ROOT", r"E:\Fluxgroup\.codely-cli\voicebank")
OUT = os.path.join(VB, os.environ.get("VB_AUDITION_DIR", "auditions"))
TMP = os.path.join(OUT, "_tmp")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SEC, START = 14, 6        # 14 s starting at 6 s, skips intros/jingles


def fetch_segment(row, path):
    from bilibili_api import video, sync
    data = sync(video.Video(bvid=row["bvid"]).get_download_url(0))
    audios = ((data or {}).get("dash") or {}).get("audio") or []
    if not audios:
        raise RuntimeError("no-audio")
    best = max(audios, key=lambda a: a.get("bandwidth") or 0)
    url = best.get("baseUrl") or best.get("base_url")
    raw = path + ".m4a"
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Referer": "https://www.bilibili.com/"})
    # grab enough bytes for start+len (about 190 kbps -> ~24 KB/s)
    need = int((START + SEC + 10) * 24_000)
    n = 0
    with urllib.request.urlopen(req, timeout=60) as r, open(raw, "wb") as f:
        while n < need:
            c = r.read(1 << 20)
            if not c:
                break
            f.write(c)
            n += len(c)
    subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", str(START), "-t", str(SEC),
                    "-i", raw, "-ac", "1", "-ar", "32000",
                    "-af", "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-c:a", "libmp3lame", "-b:a", "96k", path + ".mp3"], check=True)
    os.remove(raw)
    return path + ".mp3"


def safe(s):
    return re.sub(r'[\\/:*?"<>|\s]+', "_", str(s))[:18]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(VB, "screen_pool.json")
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    os.makedirs(TMP, exist_ok=True)
    data = json.load(open(src, encoding="utf-8"))
    rows = data["rows"][:limit]

    index = []
    for i, r in enumerate(rows, 1):
        tag = "%02d_%s_%s_%s" % (i, r["cat"], safe(r["author"]), r["bvid"])
        dst = os.path.join(OUT, tag)
        try:
            if not os.path.exists(dst + ".mp3"):
                fetch_segment(r, dst)
            index.append({"file": tag + ".mp3", "cat": r["cat"], "author": r["author"],
                          "title": r["title"], "bvid": r["bvid"],
                          "f0": r["f0_med"], "sp": r["speech_ratio"], "bg": r["bg_ratio"],
                          "score": r["score"], "dur_min": r["dur"] // 60})
            print("[%d/%d] %s" % (i, len(rows), tag), flush=True)
        except Exception as e:
            print("[%d] FAIL %s %r" % (i, r["bvid"], e), flush=True)

    json.dump(index, open(os.path.join(OUT, "INDEX.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    lines = ["# 试听包（每段 14 秒，-16 LUFS，96kbps）", "",
             "| # | 类别 | 作者 | 标题 | 基频 | 说话 | bg | 文件 |",
             "|---|---|---|---|---|---|---|---|"]
    for k, r in enumerate(index, 1):
        lines.append("| %d | %s | %s | %s | %.0f | %.2f | %.2f | `%s` |" %
                     (k, r["cat"], r["author"], str(r["title"])[:26], r["f0"], r["sp"],
                      r["bg"], r["file"]))
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write("\n".join(lines))
    print("AUDITIONS", len(index), "->", OUT)


if __name__ == "__main__":
    main()