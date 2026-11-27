# -*- coding: utf-8 -*-
"""vb_bulk_fetch.py - download max-bitrate DASH audio for a list of bvids.

Quality notes: Bilibili caps audio at ~184 kbps AAC for these uploads (no FLAC lane),
so the ceiling is set by the source. We take the highest-bandwidth lane every time and
never transcode on the way down.
"""
import json
import os
import sys
import urllib.request

from bilibili_api import video, sync

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

mid = sys.argv[1]
outdir = sys.argv[2]
src = sys.argv[3]
os.makedirs(outdir, exist_ok=True)
rows = json.load(open(src, encoding="utf-8"))["videos"]

report = []
for i, r in enumerate(rows, 1):
    bvid = r["bvid"]
    dst = os.path.join(outdir, "%02d_%s.m4a" % (i, bvid))
    if os.path.exists(dst) and os.path.getsize(dst) > 200_000:
        report.append({"bvid": bvid, "file": dst, "cached": True})
        continue
    try:
        data = sync(video.Video(bvid=bvid).get_download_url(0))
        audios = ((data or {}).get("dash") or {}).get("audio") or []
        if not audios:
            report.append({"bvid": bvid, "error": "no-audio"})
            continue
        best = max(audios, key=lambda a: a.get("bandwidth") or 0)
        url = best.get("baseUrl") or best.get("base_url")
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                  "Referer": "https://www.bilibili.com/"})
        n = 0
        with urllib.request.urlopen(req, timeout=90) as resp, open(dst, "wb") as f:
            while True:
                c = resp.read(1 << 20)
                if not c:
                    break
                f.write(c)
                n += len(c)
        report.append({"bvid": bvid, "file": dst, "bytes": n,
                       "kbps": round((best.get("bandwidth") or 0) / 1000),
                       "title": r.get("title", "")[:40]})
        print("[%d/%d] %s %.1fMB %dkbps" % (i, len(rows), bvid, n / 1e6,
                                            (best.get("bandwidth") or 0) // 1000), flush=True)
    except Exception as e:
        report.append({"bvid": bvid, "error": repr(e)[:160]})
        print("[%d] %s ERR %r" % (i, bvid, e), flush=True)

json.dump(report, open(os.path.join(outdir, "_fetch.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("DONE", len(report))