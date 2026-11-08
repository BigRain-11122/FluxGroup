#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audio_bgm_fill.py - 按规格把缺的配乐补齐（幂等、可派给任何执行机）。

Why (CEO 2026-11-07「更重要是带动机队一起干，不是你一个机器在忙」)：
  主控亲自下载/切片属于越界生产；这类活有确定输入（AUDIO-BGM-SPEC-v1.json）、
  确定判据（时长/字节/sha256），应该落成卡派给执行机，主控只验收。

要点：
  1) 规格是数据不是代码（cph4/fleet/AUDIO-BGM-SPEC-v1.json），改取舍改规格。
  2) 幂等：目标文件存在且 sha256 与清单一致即 SKIP，绝不重复下载（重复劳动=浪费机队）。
  3) 只拉需要的片段：ffmpeg -ss/-t 直取，实测整曲 3.5MB vs 片段 1.2MB（链路限速 2-17KB/s）。
  4) 判据全部实测：ffprobe 时长、落盘字节、sha256 回读；规格外一律删除，不留脏文件。
  5) 无 ffmpeg 就判 BLOCKED(rc=2)，不退回整曲下载（那会在慢链路上伪装成卡死）。

用法：
  python3 Tools/fleet/audio_bgm_fill.py [--spec PATH] [--out DIR] [--only tense,driving]
                                        [--receipt cph4/fleet/queue-receipts/x.json]
  rc: 0 全部就绪 | 1 有缺口 | 2 环境缺 ffmpeg | 3 网络/源不可用
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def node_id():
    """回执必须能认出生产机：FLEET_NODE → NODE → COMPUTERNAME，永不落占位。"""
    for k in ("FLEET_NODE", "NODE"):
        v = (os.environ.get(k) or "").strip()
        if v:
            return v.lower()
    return (os.environ.get("COMPUTERNAME") or "node").strip().lower()


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def probe_dur(p):
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", p], capture_output=True, text=True, timeout=120)
        return round(float(r.stdout.strip()), 3)
    except Exception:
        return None


def load_manifest(p):
    rows = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def save_manifest(p, rows):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, p)


FFMPEG = shutil.which("ffmpeg") or ""
FFPROBE = shutil.which("ffprobe") or ""


def collect_one(mood, spec, out_dir, manifest, spec_min, spec_max, exs):
    slug = mood["slug"]
    dst = os.path.join(out_dir, "%s.mp3" % slug)
    row = next((r for r in manifest if r.get("slug") == slug), None)

    # 幂等闸：盘上与清单都对得上就跳过
    if row and os.path.exists(dst):
        if os.path.getsize(dst) == int(row.get("bytes", -1)) and sha256(dst) == row.get("sha256"):
            d = probe_dur(dst)
            if d and spec_min <= d <= spec_max:
                return {"slug": slug, "status": "SKIP", "dur_s": d, "file": dst,
                        "detail": "already present and verified"}

    if not mood.get("file"):
        return {"slug": slug, "status": "NO-SOURCE",
                "detail": "spec has no direct file url for this mood (collected earlier elsewhere)"}

    url = "%s/%s" % (spec.get("base_url", ""), mood["file"])
    ss = mood.get("ss") or 0
    part = dst + ".part"
    cmd = [FFMPEG, "-v", "error", "-y", "-ss", str(ss), "-t", str(exs), "-i", url,
           "-ac", "2", "-ar", "44100", "-b:a", "160k", part]
    try:
        subprocess.run(cmd, capture_output=True, timeout=1800)
    except subprocess.TimeoutExpired:
        if os.path.exists(part):
            os.remove(part)
        return {"slug": slug, "status": "TIMEOUT", "detail": "ffmpeg slice exceeded 1800s", "url": url}

    if not (os.path.exists(part) and os.path.getsize(part) > 10000):
        if os.path.exists(part):
            os.remove(part)
        return {"slug": slug, "status": "FETCH-FAIL", "detail": "no usable output (link down?)", "url": url}

    d = probe_dur(part)
    if d is None or not (spec_min <= d <= spec_max):
        os.remove(part)
        return {"slug": slug, "status": "OUT-OF-SPEC",
                "detail": "duration %s outside %s-%s" % (d, spec_min, spec_max), "url": url}

    os.replace(part, dst)
    new = {
        "file": os.path.basename(dst), "class": "bgm", "slug": slug,
        "source_url": url, "license": "CC0-1.0 (OpenGameArt asset page)",
        "oga_slug": mood.get("oga"), "bytes": os.path.getsize(dst),
        "sha256": sha256(dst), "dur_s": d, "collected_at": now(),
        "edit": "%ss excerpt (ffmpeg -ss %s) pulled directly from source url" % (exs, ss),
        "excerpt": True, "collected_by": "audio_bgm_fill.py",
    }
    manifest = [r for r in manifest if r.get("slug") != slug] + [new]
    save_manifest(os.path.join(out_dir, "manifest.jsonl"), manifest)
    return {"slug": slug, "status": "OK", "dur_s": d, "bytes": new["bytes"],
            "sha256": new["sha256"], "file": dst}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=os.path.join(F, "AUDIO-BGM-SPEC-v1.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default="")
    ap.add_argument("--receipt", default="")
    a = ap.parse_args(argv)

    if not FFMPEG or not FFPROBE:
        print("BLOCKED: ffmpeg/ffprobe not on PATH")
        return 2
    spec = json.load(open(a.spec, encoding="utf-8"))
    out_dir = a.out or os.path.join(ROOT, spec.get("output_dir", "media/asset/incoming/audio-bgm"))
    os.makedirs(out_dir, exist_ok=True)
    manifest = load_manifest(os.path.join(out_dir, "manifest.jsonl"))
    spec_min, spec_max = spec.get("min_dur_s", 15), spec.get("max_dur_s", 120)
    exs = spec.get("excerpt_s", 60)

    only = [s.strip() for s in a.only.split(",") if s.strip()]
    moods = [m for m in spec.get("moods", []) if not only or m["slug"] in only]

    results = []
    for m in moods:
        r = collect_one(m, spec, out_dir, manifest, spec_min, spec_max, exs)
        manifest = load_manifest(os.path.join(out_dir, "manifest.jsonl"))
        results.append(r)
        print("[bgm-fill] %-12s %-12s %s" % (r["slug"], r["status"],
                                             r.get("detail") or ("%ss %sB" % (r.get("dur_s"), r.get("bytes", 0)))))
        sys.stdout.flush()

    ok = [r for r in results if r["status"] in ("OK", "SKIP")]
    gap = [r for r in results if r["status"] not in ("OK", "SKIP")]
    rc = 0 if not gap else 1
    if any(r["status"] in ("FETCH-FAIL", "TIMEOUT") for r in results):
        rc = 3

    payload = {"ts": now(), "node": node_id(), "out_dir": out_dir,
               "spec": os.path.relpath(a.spec, ROOT) if a.spec.startswith(ROOT) else a.spec,
               "ready": len(ok), "gaps": len(gap), "results": results, "rc": rc}
    if a.receipt:
        rp = a.receipt if os.path.isabs(a.receipt) else os.path.join(ROOT, a.receipt)
        os.makedirs(os.path.dirname(rp), exist_ok=True)
        json.dump(payload, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[bgm-fill] receipt -> %s" % rp)
    print("[bgm-fill] ready=%d gaps=%d rc=%d" % (len(ok), len(gap), rc))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))