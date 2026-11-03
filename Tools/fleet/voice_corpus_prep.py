#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_corpus_prep.py - 音色语料工程（纯 CPU，可跨机分片并行）。

为什么（2026-11-03 CEO「CPU 的算力很强，所有机队都可以去烧音色库」）：
  烧音色库的工作量里，八成是"把脏音频变成训练语料"——转码、静音切分、去静音段、
  削波检查、出清单。这一步纯 CPU、可断点续跑、可按分片拆到多台机同时跑；
  只有最后 SoVITS/GPT 微调那一小步需要 GPU。所以"所有机队烧音色库"的可行形态是：
  所有机器分片做语料工程 → 有 GPU 的机器做微调。

做法：
  media/asset/inbox/  →  逐个文件转为 24k 单声道 wav，按静音切成 2–12 秒片段
  →  media/asset/voices/<组名>/sliced/*.wav + index.json + RIGHTS.json 模板

**不做 loudnorm**：响度归一化会把动态压平，而"反播音腔"闸判的正是 LRA 与停顿密度。
训练语料要保留原始起伏，只做削波检查。

分片（所有机队并行）：
  --shard 0/4 / 1/4 / 2/4 / 3/4   # 按文件名哈希取模，天然均衡且不重复

用法：
  python3 voice_corpus_prep.py --inbox media/asset/inbox --group commonvoice-zh --shard 0/4
  python3 voice_corpus_prep.py --inbox media/asset/inbox --group my-voice      # 单片全跑
Exit: 0 有产出；3 没有可处理输入（等上游投料，不算失败）；1 环境问题。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

AUD_EXT = (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".opus", ".wma")
MIN_SEG, MAX_SEG = 2.0, 12.0
SIL_DB, SIL_DUR = -35, 0.45
PEAK_LIMIT = 0.99          # 削波检查，只报不改


def ff(name="ffmpeg"):
    for c in (os.environ.get(name.upper()) or "", name):
        if not c:
            continue
        if os.path.isabs(c) and os.path.exists(c):
            return c
        if shutil.which(c):
            return c
    return None


FFMPEG = ff("ffmpeg")


def run(cmd, timeout=3600):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def duration(path):
    rc, out = run([FFMPEG, "-hide_banner", "-i", path], 120)
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0


def silence_spans(path):
    """返回 [(start,end)] 静音区间。"""
    rc, out = run([FFMPEG, "-hide_banner", "-i", path, "-af",
                   "silencedetect=n=%ddB:d=%.2f" % (SIL_DB, SIL_DUR), "-f", "null", "-"], 1800)
    spans, cur = [], None
    for line in out.splitlines():
        m = re.search(r"silence_start:\s*([\d.]+)", line)
        if m:
            cur = float(m.group(1))
            continue
        m = re.search(r"silence_end:\s*([\d.]+)", line)
        if m and cur is not None:
            spans.append((cur, float(m.group(1))))
            cur = None
    return spans


def split_points(total, spans):
    """静音区间 → 切点列表；过长的非静音段再按 MAX_SEG 硬切。"""
    segs, cursor = [], 0.0
    for s, e in spans:
        if s - cursor >= MIN_SEG:
            segs.append((cursor, s))
        cursor = max(cursor, e)
    if total - cursor >= MIN_SEG - 0.05:
        segs.append((cursor, total))
    out = []
    for s, e in segs:
        while e - s > MAX_SEG:
            out.append((s, s + MAX_SEG))
            s += MAX_SEG
        # 浮点容差：ffmpeg 报的时长常是 23.999 之类，用严格 >=2.0 会静默丢掉尾部片段
        if e - s >= MIN_SEG - 0.05:
            out.append((s, e))
    return out


def peak_warn(path):
    rc, out = run([FFMPEG, "-hide_banner", "-i", path, "-af", "volumedetect", "-f", "null", "-"], 600)
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", out)
    return float(m.group(1)) if m else None


def shard_of(name, idx, n):
    h = int(hashlib.sha1(name.encode("utf-8")).hexdigest(), 16)
    return h % n == idx


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", default="media/asset/inbox")
    ap.add_argument("--group", required=True, help="这批语料的组名，落在 media/asset/voices/<group>/")
    ap.add_argument("--shard", default="0/1", help="i/n，本机只处理 1/n 的文件")
    ap.add_argument("--out", default="")
    ap.add_argument("--receipt", default="")
    a = ap.parse_args(argv)
    if not FFMPEG:
        print("没有 ffmpeg（rc=1）")
        return 1
    try:
        si, sn = (int(x) for x in a.shard.split("/"))
        assert 0 <= si < sn
    except Exception:
        print("--shard 格式应为 i/n（rc=1）")
        return 1

    inbox = os.path.abspath(a.inbox)
    group_dir = os.path.abspath(a.out or os.path.join("media", "asset", "voices", a.group))
    sliced = os.path.join(group_dir, "sliced")
    os.makedirs(sliced, exist_ok=True)

    files = []
    if os.path.isdir(inbox):
        for n in sorted(os.listdir(inbox)):
            p = os.path.join(inbox, n)
            if os.path.isfile(p) and n.lower().endswith(AUD_EXT):
                files.append(p)
    mine = [p for p in files if shard_of(os.path.basename(p), si, sn)]

    receipt = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "group": a.group,
               "shard": a.shard, "inbox": os.path.relpath(inbox),
               "inbox_files": len(files), "my_files": len(mine),
               "segments": 0, "skipped_files": [], "peak_warnings": []}

    if not mine:
        # 没有可处理输入 = 等投料，不是失败（否则每天一片假红）
        receipt.update({"verdict": "BLOCKED", "status": "BLOCKED",
                        "gaps": ["inbox 里没有本分片的音频（%s，总 %d 个文件）" % (inbox, len(files))]})
        emit(receipt, a.receipt)
        print("[corpus] 本分片无输入（inbox 共 %d 个文件）——等投料，rc=3" % len(files))
        return 3

    made = 0
    for p in mine:
        base = os.path.splitext(os.path.basename(p))[0]
        dur = duration(p)
        if dur < MIN_SEG:
            receipt["skipped_files"].append([os.path.basename(p), "太短 %.1fs" % dur])
            continue
        spans = silence_spans(p)
        segs = split_points(dur, spans)
        if not segs:
            receipt["skipped_files"].append([os.path.basename(p), "切不出 2–12s 的片段"])
            continue
        pk = peak_warn(p)
        if pk is not None and pk >= -0.1:
            receipt["peak_warnings"].append([os.path.basename(p), pk])
        for i, (s, e) in enumerate(segs):
            outp = os.path.join(sliced, "%s_%03d.wav" % (base, i))
            if os.path.exists(outp) and os.path.getsize(outp) > 1024:
                made += 1          # 断点续跑：已切过的不重切
                continue
            rc, out = run([FFMPEG, "-v", "error", "-y", "-ss", "%.3f" % s, "-t", "%.3f" % (e - s),
                           "-i", p, "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", outp], 900)
            if rc == 0 and os.path.exists(outp):
                made += 1
            else:
                receipt["skipped_files"].append([os.path.basename(p), "片段 %d 切失败" % i])

    # 清单
    seg_files = sorted(os.listdir(sliced))
    total_s = 0.0
    rows = []
    for n in seg_files:
        d = duration(os.path.join(sliced, n))
        total_s += d
        rows.append({"file": n, "dur": round(d, 2)})
    with open(os.path.join(group_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"group": a.group, "created": receipt["ts"], "total_s": round(total_s, 1),
                   "count": len(rows), "segments": rows}, f, ensure_ascii=False, indent=1)

    # 授权模板：故意留空 license，让闸把它拦下来，等人填真实来源
    rp = os.path.join(group_dir, "RIGHTS.json")
    if not os.path.exists(rp):
        with open(rp, "w", encoding="utf-8") as f:
            json.dump({"source": "", "license": "unknown", "real_person": None,
                       "consent": None,
                       "note": "必须填真实来源与授权；license 见 SOURCES-V1.md 白名单，"
                               "未知或真人无同意会被 asset_dataset_audit 判 FAIL"},
                      f, ensure_ascii=False, indent=1)

    receipt.update({"segments": len(rows), "total_s": round(total_s, 1),
                    "sliced_dir": os.path.relpath(sliced),
                    "verdict": "PASS" if rows else "FAIL",
                    "gaps": [] if rows else ["一条片段都没切出来"]})
    receipt["status"] = receipt["verdict"]
    emit(receipt, a.receipt)
    print("[corpus] %s 分片 %s：文件 %d → 片段 %d（%.1fs）"
          % (a.group, a.shard, len(mine), len(rows), total_s))
    return 0 if rows else 1


def emit(rec, path):
    if not path:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))