#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_dataset_audit.py - 训练数据集准入闸（人脸/语音），只卡"明显不合格"。

为什么（2026-11-03 CEO：「我很讨厌和别的 ai 一样的 ai 脸和声音，去烧各种有自己特色的」）：
  讨厌的东西不是靠"提示词写得花"解决的，先决条件是**数据集本身不像 AI 默认审美**。
  这批数据集一旦是网红脸/磨皮图，或者播音腔朗读，后面训出来的 LoRA 与音色必然平庸，
  再调参也救不回来。所以在训练之前先过闸：不合格的数据集不许进训练，省掉几小时 GPU。

判据（只用 ffmpeg + 纯 Python，不依赖 numpy/PIL，机队任何机器都能跑）：

  face 模式（角色 LoRA 数据集）
    1. 张数 ≥ 12（少于 12 张训不出稳定角色）
    2. 短边 ≥ 768（低于此训练出来糊）
    3. 近似重复率 ≤ 30%（同一张图换背景/换尺寸=假多样性，靠 dHash 判）
    4. 细节能量中位数 ≥ 阈值（磨皮/美颜会把高频细节抹平，拉普拉斯方差会掉）

  voice 模式（音色数据集）
    1. 总时长 ≥ 60 秒且条数 ≥ 8（GPT-SoVITS 少样本下限）
    2. 单条时长 2–12 秒占比 ≥ 80%（太长爆显存，太短学不到韵律）
    3. 停顿密度 ≥ 6 次/分钟（播音腔特征之一是"一口气念完、停顿规律稀薄"）
    4. 响度动态 LRA ≥ 5 LU（播音腔被压得很平；生活化录音起伏更大）

这些只是**排除明显不合格**，不能证明"有特色"——有没有特色最终只能人看/人听。
所以本闸的 PASS 语义是"允许进入训练"，不是"这数据集很好"。

用法：
  python3 asset_dataset_audit.py --mode face  --dir <图片目录> [--out receipts/x.json]
  python3 asset_dataset_audit.py --mode voice --dir <音频目录> [--out receipts/x.json]
Exit: 0 PASS；1 FAIL（列缺口）；2 目录不存在/不可读。
"""
import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
AUD_EXT = (".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg")

FACE_MIN_COUNT = 12
FACE_MIN_SIDE = 768
FACE_MAX_DUP_RATIO = 0.30
FACE_MIN_TEXTURE = 12.0          # 拉普拉斯方差中位数（0-255 灰度尺度）

VOICE_MIN_TOTAL_S = 60.0
VOICE_MIN_COUNT = 8
VOICE_OK_LEN = (2.0, 12.0)
VOICE_MIN_OK_RATIO = 0.80
VOICE_MIN_PAUSE_PER_MIN = 6.0
VOICE_MIN_LRA = 5.0


def ff(name):
    for c in (os.environ.get(name.upper()) or "", name):
        if not c:
            continue
        if os.path.isabs(c) and os.path.exists(c):
            return c
        if shutil.which(c):
            return c
    return None


FFMPEG = ff("ffmpeg")
FFPROBE = ff("ffprobe")


def run(cmd, timeout=300, binary=False):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        out = r.stdout if binary else (r.stdout or b"").decode("utf-8", "replace")
        err = (r.stderr or b"").decode("utf-8", "replace")
        return r.returncode, out, err
    except Exception as e:
        return 1, (b"" if binary else ""), str(e)


def probe(path):
    """返回 (w,h,duration)。ffprobe 优先，缺失时解析 ffmpeg -i。"""
    if FFPROBE:
        rc, out, _ = run([FFPROBE, "-v", "error", "-show_streams", "-show_format",
                          "-of", "json", path], 60)
        if rc == 0:
            try:
                d = json.loads(out)
                v = next((s for s in d.get("streams") or [] if s.get("codec_type") == "video"), {})
                dur = float((d.get("format") or {}).get("duration") or 0)
                return (int(v.get("width") or 0), int(v.get("height") or 0), dur)
            except Exception:
                pass
    rc, out, err = run([FFMPEG, "-hide_banner", "-i", path], 60)
    text = (out or "") + (err or "")
    d = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", text)
    dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", text)
    return (int(m.group(1)) if m else 0, int(m.group(2)) if m else 0, dur)


def dhash(path):
    """按 8x8 差分哈希判近似重复；解码交给 ffmpeg，本机无需 PIL。"""
    rc, out, _ = run([FFMPEG, "-v", "error", "-i", path, "-vf", "scale=9:8,format=gray",
                      "-f", "rawvideo", "-"], 60, binary=True)
    if rc != 0 or len(out) < 72:
        return None
    px = struct.unpack("72B", out[:72])
    bits = 0
    i = 0
    for row in range(8):
        for col in range(8):
            left = px[row * 9 + col]
            right = px[row * 9 + col + 1]
            bits |= (1 if left > right else 0) << i
            i += 1
    return bits


def texture_energy(path):
    """拉普拉斯方差近似：磨皮/美颜会把它压得很低。"""
    rc, out, _ = run([FFMPEG, "-v", "error", "-i", path, "-vf",
                      "scale=256:256:force_original_aspect_ratio=increase,crop=256:256,format=gray",
                      "-f", "rawvideo", "-"], 60, binary=True)
    if rc != 0 or len(out) < 256 * 256:
        return None
    W = 256
    px = out[:W * W]
    vals = []
    for y in range(1, W - 1):
        base = y * W
        for x in range(1, W - 1):
            c = px[base + x]
            lap = 4 * c - px[base + x - 1] - px[base + x + 1] - px[base - W + x] - px[base + W + x]
            vals.append(lap * lap)
    if not vals:
        return None
    vals.sort()
    return float(vals[len(vals) // 2])


def audit_face(d):
    gaps, files = [], []
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n)
        if os.path.isfile(p) and n.lower().endswith(IMG_EXT):
            files.append(p)
    if len(files) < FACE_MIN_COUNT:
        gaps.append("张数 %d < %d（训不出稳定角色）" % (len(files), FACE_MIN_COUNT))
    sizes, tex, hashes = [], [], []
    for p in files:
        w, h, _ = probe(p)
        if w and h:
            sizes.append(min(w, h))
        t = texture_energy(p)
        if t is not None:
            tex.append(t)
        hs = dhash(p)
        if hs is not None:
            hashes.append(hs)
    small = [s for s in sizes if s < FACE_MIN_SIDE]
    if small:
        gaps.append("%d/%d 张短边 < %d" % (len(small), len(sizes) or 1, FACE_MIN_SIDE))
    dup = 0
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            if bin(hashes[i] ^ hashes[j]).count("1") <= 4:
                dup += 1
    dup_ratio = (dup / max(1, len(hashes) * (len(hashes) - 1) / 2.0))
    if dup_ratio > FACE_MAX_DUP_RATIO:
        gaps.append("近似重复率 %.0f%% > %.0f%%（同一张图换背景=假多样性）"
                    % (dup_ratio * 100, FACE_MAX_DUP_RATIO * 100))
    tex_med = sorted(tex)[len(tex) // 2] if tex else None
    if tex_med is not None and tex_med < FACE_MIN_TEXTURE:
        gaps.append("细节能量中位数 %.1f < %.1f（磨皮/美颜脸，训出来就是 AI 脸）"
                    % (tex_med, FACE_MIN_TEXTURE))
    return {"mode": "face", "count": len(files), "min_side": min(sizes) if sizes else None,
            "dup_ratio": round(dup_ratio, 3), "texture_median": tex_med}, gaps


def audit_voice(d):
    gaps, files = [], []
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n)
        if os.path.isfile(p) and n.lower().endswith(AUD_EXT):
            files.append(p)
    if len(files) < VOICE_MIN_COUNT:
        gaps.append("条数 %d < %d" % (len(files), VOICE_MIN_COUNT))
    total, ok_len, pauses, lras = 0.0, 0, 0, []
    for p in files:
        _, _, dur = probe(p)
        total += dur
        if VOICE_OK_LEN[0] <= dur <= VOICE_OK_LEN[1]:
            ok_len += 1
        rc, out, err = run([FFMPEG, "-hide_banner", "-i", p, "-af",
                            "silencedetect=n=-35dB:d=0.35", "-f", "null", "-"], 180)
        pauses += len(re.findall(r"silence_start", (out or "") + (err or "")))
        rc, out, err = run([FFMPEG, "-hide_banner", "-i", p, "-af",
                            "loudnorm=print_format=json", "-f", "null", "-"], 180)
        m = re.search(r'"input_lra"\s*:\s*"?(-?[\d.]+)"?', (out or "") + (err or ""))
        if m:
            lras.append(float(m.group(1)))
    if total < VOICE_MIN_TOTAL_S:
        gaps.append("总时长 %.0fs < %.0fs" % (total, VOICE_MIN_TOTAL_S))
    ok_ratio = ok_len / max(1, len(files))
    if ok_ratio < VOICE_MIN_OK_RATIO:
        gaps.append("2–12 秒条目占比 %.0f%% < %.0f%%（太长爆显存/太短学不到韵律）"
                    % (ok_ratio * 100, VOICE_MIN_OK_RATIO * 100))
    per_min = pauses / max(1e-6, total / 60.0) if total else 0
    if per_min < VOICE_MIN_PAUSE_PER_MIN:
        gaps.append("停顿密度 %.1f 次/分 < %.0f（一口气念完=播音腔特征）"
                    % (per_min, VOICE_MIN_PAUSE_PER_MIN))
    lra_med = sorted(lras)[len(lras) // 2] if lras else None
    if lra_med is not None and lra_med < VOICE_MIN_LRA:
        gaps.append("响度动态 LRA %.1f LU < %.0f（被压得太平=播音腔）" % (lra_med, VOICE_MIN_LRA))
    return {"mode": "voice", "count": len(files), "total_s": round(total, 1),
            "ok_len_ratio": round(ok_ratio, 3), "pauses_per_min": round(per_min, 1),
            "lra_median": lra_med}, gaps


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["face", "voice"])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": a.mode, "dir": a.dir,
               "verdict": "BLOCKED", "status": "BLOCKED",
               "gaps": ["目录不存在：%s" % a.dir]}
        emit(out, a.out)
        print("目录不存在：%s" % a.dir)
        return 2
    if not FFMPEG:
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": a.mode, "dir": a.dir,
               "verdict": "BLOCKED", "status": "BLOCKED", "gaps": ["没有 ffmpeg"]}
        emit(out, a.out)
        print("没有 ffmpeg，无法审计")
        return 2
    measured, gaps = audit_face(a.dir) if a.mode == "face" else audit_voice(a.dir)
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "dir": a.dir,
           "spec": "ASSET-DATASET-GATE-v1", "measured": measured,
           "verdict": "PASS" if not gaps else "FAIL", "gaps": gaps,
           "note": "PASS=允许进训练，不代表这数据集有特色；特色只能人看/人听"}
    out["status"] = out["verdict"]
    emit(out, a.out)
    print("%s %s  %s" % ("DATASET", out["verdict"], a.dir))
    print("  " + json.dumps(measured, ensure_ascii=False))
    for g in gaps:
        print("  ! " + g)
    return 0 if not gaps else 1


def emit(out, path):
    if not path:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))