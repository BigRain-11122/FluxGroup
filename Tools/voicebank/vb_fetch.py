# -*- coding: utf-8 -*-
"""vb_fetch.py - download one Bilibili video's DASH audio (runs under venv_bili).

Kept as a separate process because the training runtime has faster-whisper/torch but no
bilibili_api, and venv_bili has bilibili_api but no numpy/torch. Mixing them in one
interpreter is what would otherwise force a second install of a 2.5GB torch.
"""
import sys
import urllib.request

from bilibili_api import video, sync

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

bvid, out = sys.argv[1], sys.argv[2]
v = video.Video(bvid=bvid)
data = sync(v.get_download_url(0))
audios = ((data or {}).get("dash") or {}).get("audio") or []
if not audios:
    print("NO-AUDIO")
    sys.exit(2)
best = max(audios, key=lambda a: a.get("bandwidth") or 0)
url = best.get("baseUrl") or best.get("base_url")
req = urllib.request.Request(url, headers={"User-Agent": UA,
                                          "Referer": "https://www.bilibili.com/"})
n = 0
with urllib.request.urlopen(req, timeout=90) as r, open(out, "wb") as f:
    while True:
        c = r.read(1 << 20)
        if not c:
            break
        f.write(c)
        n += len(c)
print("OK", n, best.get("bandwidth"))