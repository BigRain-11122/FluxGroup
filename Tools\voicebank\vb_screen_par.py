# -*- coding: utf-8 -*-
"""vb_screen_par.py - parallel acoustic screening of talent candidates.

Each worker: grab the first ~8 MB of the DASH audio -> decode 90 s -> measure
  speech_ratio  : talk density (talk-show vs. music/edit heavy)
  f0_med / iqr   : pitch centre and spread (timbre class + expressiveness)
  bg_ratio       : silence-vs-speech energy (BGM / room noise)
Then rank per category with a composite that prefers studio-clean, talk-dense,
pitch-distinctive sources — the only audible proxy we have without listening.
"""
import json
import multiprocessing as mp
import os
import subprocess
import sys
import urllib.request
import wave

import numpy as np

FFMPEG = r"C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\FFMPEG.exe".replace("FFMPEG", "ffmpeg")
TMP = r"E:\Fluxgroup\.codely-cli\voicebank\_screen_tmp"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SEC, CAP = 90, 8 << 20


def grab_and_measure(row):
    bvid = row["bvid"]
    try:
        from bilibili_api import video, sync
        data = sync(video.Video(bvid=bvid).get_download_url(0))
        audios = ((data or {}).get("dash") or {}).get("audio") or []
        if not audios:
            return dict(row, error="no-audio")
        best = max(audios, key=lambda a: a.get("bandwidth") or 0)
        url = best.get("baseUrl") or best.get("base_url")
        raw = os.path.join(TMP, bvid + ".m4a")
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                  "Referer": "https://www.bilibili.com/"})
        n = 0
        with urllib.request.urlopen(req, timeout=60) as r, open(raw, "wb") as f:
            while n < CAP:
                c = r.read(1 << 20)
                if not c:
                    break
                f.write(c)
                n += len(c)
        wav = os.path.join(TMP, bvid + ".wav")
        subprocess.run([FFMPEG, "-y", "-v", "error", "-i", raw, "-t", str(SEC),
                        "-ac", "1", "-ar", "16000", wav], check=True)
        m = measure(wav)
        for p in (raw, wav):
            try:
                os.remove(p)
            except OSError:
                pass
        if not m:
            return dict(row, error="no-voice")
        return dict(row, kbps=round((best.get("bandwidth") or 0) / 1000), **m)
    except Exception as e:
        return dict(row, error=repr(e)[:120])


def measure(wav):
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
        k = int(np.argmax(ac[lo:hi])) + lo
        if ac[k] < 0.33:
            sil.append(e)
            continue
        f0s.append(sr / k)
        sp.append(e)
    if not f0s:
        return None
    f = np.array(f0s)
    q1, q3 = np.percentile(f, [25, 75])
    med = float(np.median(f))
    sp_ratio = len(f0s) / max(1, (len(x) - win) // hop)
    bg = float(np.mean(sil)) / (float(np.mean(sp)) + 1e-9) if sp and sil else 0.5
    f0_dist = min(abs(med - 115), abs(med - 240))   # distance from stock TTS centres
    score = sp_ratio + min(f0_dist, 60) / 60.0 + 2 * ((q3 - q1) / med) - 3 * max(0.0, bg - 0.05)
    return {"f0_med": round(med, 1), "f0_iqr_ratio": round(float((q3 - q1) / med), 3),
            "speech_ratio": round(sp_ratio, 3), "bg_ratio": round(bg, 3),
            "score": round(score, 3)}


def main():
    pool_file = sys.argv[1]
    out_file = sys.argv[2]
    per_cat = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    jobs = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    os.makedirs(TMP, exist_ok=True)
    rows = json.load(open(pool_file, encoding="utf-8"))["rows"]

    picked, by_cat = [], {}
    for r in sorted(rows, key=lambda x: -x["play"]):
        c = r["cat"]
        by_cat.setdefault(c, 0)
        if by_cat[c] >= per_cat:
            continue
        by_cat[c] += 1
        picked.append(r)

    print("candidates=%d screening=%d jobs=%d" % (len(rows), len(picked), jobs), flush=True)
    ctx = mp.get_context("spawn")
    with ctx.Pool(jobs) as p:
        results = []
        for i, r in enumerate(p.map(grab_and_measure, picked), 1):
            results.append(r)
            if i % 10 == 0:
                print("  ...%d/%d" % (i, len(picked)), flush=True)
    ok = [r for r in results if "error" not in r]
    ok.sort(key=lambda r: -r["score"])
    json.dump({"screened": len(results), "ok": len(ok), "rows": ok,
               "failed": [r for r in results if "error" in r]},
              open(out_file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for cat in ("audiobook", "radio", "anchor", "dubbing", "uplive", "actor", "timbre"):
        best = [r for r in ok if r["cat"] == cat][:5]
        print("[%s] %d ok" % (cat, len([r for r in ok if r["cat"] == cat])))
        for r in best:
            print("   %.2f f0=%5.1f sp=%.2f bg=%.2f %s" %
                  (r["score"], r["f0_med"], r["speech_ratio"], r["bg_ratio"], r["bvid"]))


if __name__ == "__main__":
    main()