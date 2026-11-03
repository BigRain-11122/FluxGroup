# -*- coding: utf-8 -*-
"""vb_sample.py - partial-download + acoustic profile for candidate long-form audiobooks.

Audiobook videos can be 100+ hours; we only need the first ~8 MB to judge the narrator.
Reports: single-speaker consistency (F0 IQR), background (BGM/room), speech ratio.
"""
import json
import os
import subprocess
import sys
import urllib.request
import wave

import numpy as np

from bilibili_api import video, sync

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
FFMPEG = r"C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe"
OUT = r"E:\Fluxgroup\.codely-cli\voicebank\audiobook_probe"
os.makedirs(OUT, exist_ok=True)


def grab(bvid, sec=120, cap=8 << 20):
    data = sync(video.Video(bvid=bvid).get_download_url(0))
    audios = ((data or {}).get("dash") or {}).get("audio") or []
    if not audios:
        return None, 0
    best = max(audios, key=lambda a: a.get("bandwidth") or 0)
    url = best.get("baseUrl") or best.get("base_url")
    raw = os.path.join(OUT, bvid + ".m4a")
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Referer": "https://www.bilibili.com/"})
    n = 0
    with urllib.request.urlopen(req, timeout=90) as r, open(raw, "wb") as f:
        while n < cap:
            c = r.read(1 << 20)
            if not c:
                break
            f.write(c)
            n += len(c)
    wav = os.path.join(OUT, bvid + ".wav")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", raw, "-t", str(sec),
                    "-ac", "1", "-ar", "16000", wav], check=True)
    return wav, (best.get("bandwidth") or 0)


def profile(wav):
    with wave.open(wav, "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    win, hop = int(0.04 * sr), int(0.02 * sr)
    f0s, sp, sil = [], [], []
    for s in range(0, len(x) - win, hop):
        f = x[s:s + win]
        e = float(np.sqrt(np.mean(f * f)))
        if e < 0.004:
            sil.append(e)
            continue
        fc = f - f.mean()
        ac = np.correlate(fc, fc, "full")[win - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        lo, hi = int(sr / 400), int(sr / 55)
        seg = ac[lo:hi]
        k = int(np.argmax(seg)) + lo
        if ac[k] < 0.33:
            sil.append(e)
            continue
        f0s.append(sr / k)
        sp.append(e)
    if not f0s:
        return None
    f = np.array(f0s)
    q1, q3 = np.percentile(f, [25, 75])
    return {"f0_med": round(float(np.median(f)), 1),
            "f0_iqr": round(float(q3 - q1), 1),
            "f0_iqr_ratio": round(float((q3 - q1) / np.median(f)), 3),
            "speech_ratio": round(len(f0s) / max(1, (len(x) - win) // hop), 3),
            "bg_ratio": round(float(np.mean(sil)) / (np.mean(sp) + 1e-9), 3),
            "dur_s": round(len(x) / sr, 1)}


rows = []
for bvid in sys.argv[1:]:
    try:
        wav, bw = grab(bvid)
        if not wav:
            print(bvid, "NO-AUDIO")
            continue
        p = profile(wav)
        p["bvid"] = bvid
        p["kbps"] = round(bw / 1000)
        rows.append(p)
        print(json.dumps(p, ensure_ascii=False), flush=True)
    except Exception as e:
        print(bvid, "ERR", repr(e)[:140], flush=True)
json.dump(rows, open(os.path.join(OUT, "_probe.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)