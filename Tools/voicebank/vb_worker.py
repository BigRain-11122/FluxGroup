# -*- coding: utf-8 -*-
"""vb_worker.py - CPU-only corpus builder that any fleet node can run.

Why this shape: the fleet has no bulk file channel (SMB admin shares need credentials we
do not hold; FleetLink /sync only carries <=256 KB repo files). So instead of shipping
audio between machines, every node downloads its own assigned videos and produces its own
corpus shard. Only the segment folder + list.txt need to reach the trainer afterwards,
and that step is deliberately left outside this script.

Usage on any node:
  python vb_worker.py --voice v07 --bvids BV1xx,BV1yy --minutes 20 --out E:\\voicebank\\shards
  python vb_worker.py --voice v07 --bvids-file jobs_v07.txt ...

It reuses the same acoustic gates as vb_build (44.1 kHz, denoise, F0 band per speaker),
so shards from different machines are interchangeable.
"""
import argparse
import json
import os
import subprocess
import sys
import time

VB_BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vb_build.py")
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voicebank", "shards")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def log(p, m):
    line = "%s %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch(bvid, dst):
    """Download one video's max-bitrate DASH audio (bilibili_api in this interpreter)."""
    import urllib.request
    from bilibili_api import video, sync
    data = sync(video.Video(bvid=bvid).get_download_url(0))
    audios = ((data or {}).get("dash") or {}).get("audio") or []
    if not audios:
        raise RuntimeError("no dash audio")
    best = max(audios, key=lambda a: a.get("bandwidth") or 0)
    url = best.get("baseUrl") or best.get("base_url")
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Referer": "https://www.bilibili.com/"})
    n = 0
    with urllib.request.urlopen(req, timeout=90) as r, open(dst, "wb") as f:
        while True:
            c = r.read(1 << 20)
            if not c:
                break
            f.write(c)
            n += len(c)
    return n, best.get("bandwidth") or 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--bvids", default="")
    ap.add_argument("--bvids-file", default="")
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) // 2))
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--raw-only", action="store_true",
                    help="download only; corpus build is run separately")
    a = ap.parse_args()

    bvids = [b for b in (a.bvids or "").split(",") if b.strip()]
    if a.bvids_file:
        bvids += [l.strip() for l in open(a.bvids_file, encoding="utf-8") if l.strip()]
    if not bvids:
        print("no bvids")
        return 2

    raw = os.path.join(a.out, a.voice, "raw")
    os.makedirs(raw, exist_ok=True)
    logpath = os.path.join(a.out, a.voice, "worker.log")
    log(logpath, "worker start voice=%s bvids=%d jobs=%d cpus=%d"
        % (a.voice, len(bvids), a.jobs, os.cpu_count() or 0))

    got = 0
    for i, bv in enumerate(bvids, 1):
        dst = os.path.join(raw, "%02d_%s.m4a" % (i, bv))
        if os.path.exists(dst) and os.path.getsize(dst) > 200_000:
            got += 1
            continue
        try:
            n, bw = fetch(bv, dst)
            got += 1
            log(logpath, "fetch %s %.1fMB %dkbps" % (bv, n / 1e6, bw // 1000))
        except Exception as e:
            log(logpath, "fetch FAIL %s %r" % (bv, repr(e)[:120]))
    if got == 0:
        log(logpath, "no audio fetched")
        return 3
    if a.raw_only:
        log(logpath, "raw-only done: %s" % raw)
        return 0

    cmd = [sys.executable, VB_BUILD, "--voice", a.voice, "--raw", raw,
           "--minutes", str(a.minutes), "--jobs", str(a.jobs), "--corpus-only"]
    log(logpath, "run vb_build: %s" % " ".join(cmd[1:]))
    rc = subprocess.call(cmd)
    log(logpath, "vb_build rc=%d" % rc)
    if rc == 0:
        manifest = {
            "voice": a.voice, "node": os.environ.get("COMPUTERNAME", ""),
            "seg_dir": os.path.join(a.out, a.voice, "seg"),
            "list": os.path.join(a.out, a.voice, "exp", "list.txt"),
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        json.dump(manifest, open(os.path.join(a.out, a.voice, "SHARD.json"), "w",
                                encoding="utf-8"), ensure_ascii=False, indent=1)
        log(logpath, "SHARD READY %s" % os.path.join(a.out, a.voice, "SHARD.json"))
    return rc


sys.exit(main())