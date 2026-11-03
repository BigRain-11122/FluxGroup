# -*- coding: utf-8 -*-
"""voice_hd_gate.py - 音色高清无杂音机检（CAST-DISTINCTIVENESS-LAW-v1 §三/§四）。

CEO 令 2026-11-03：「音色也要高清，没有杂音。」
现有 tts_batch_check.py 只数文件在不在，判不了音质；这里补音质这一层。

判据（全部可机判，阈值写在 LAW §三）：
  采样率 >= 44100（正片目标 48000） / wav 位深 >= 16 / 有损码率 >= 192k
  峰值 <= -0.5 dBFS / 削波样本 <= 0.05% / DC 偏移 |mean| <= 0.002
  底噪（最静 0.5s）<= -55 dBFS 且不得是数字静音（>= -90 dBFS）
  信噪比（语音帧 - 底噪）>= 30 dB

角色音色特点（§四）：
  输出每条音频的指纹（中位 f0 / 频谱质心 / 语速代理）
  给了 --voice-map 时检查同一 voice_id 不得复用于两个有名字的角色

用法：
  python Tools/voice_hd_gate.py --dir <音频目录> [--out r.json] [--voice-map map.json]
退出码：0 全过；2 有不合格；3 没有可判对象（目录缺失/无音频）
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np

AUDIO_EXT = (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus")
SR = 16000
TH = {
    "sample_rate_min": 44100,
    "peak_dbfs_max": -0.5,
    "clip_ratio_max": 0.0005,
    "dc_max": 0.002,
    "noise_floor_dbfs_max": -55.0,
    "noise_floor_dbfs_min": -90.0,
    "snr_db_min": 30.0,
    "lossy_bitrate_min": 192000,
    "wav_bits_min": 16,
}


def which(name):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        c = os.path.join(p, name + ".exe")
        if os.path.exists(c):
            return c
    return None


FFMPEG = which("ffmpeg")
FFPROBE = which("ffprobe")


def probe(path):
    """优先 ffprobe；没有就解析 ffmpeg -i 的 stderr（本机与 Mac 都要能跑）。"""
    if FFPROBE:
        r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a:0",
                            "-show_entries", "stream=sample_rate,channels,bit_rate,bits_per_raw_sample,codec_name",
                            "-of", "json", path], capture_output=True, text=True)
        try:
            st = json.loads(r.stdout)["streams"][0]
            return {
                "sr": int(st.get("sample_rate") or 0),
                "ch": int(st.get("channels") or 0),
                "codec": st.get("codec_name"),
                "bitrate": int(st.get("bit_rate") or 0),
                "bits": int(st.get("bits_per_raw_sample") or 0),
            }
        except Exception:
            pass
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True)
    txt = r.stderr
    m = re.search(r"Audio: (\w+).*?, (\d+) Hz, (\w+)(?:, (\d+) kb/s)?", txt)
    if not m:
        return {"sr": 0, "ch": 0, "codec": None, "bitrate": 0, "bits": 0}
    codec, sr, _layout, kbps = m.groups()
    return {"sr": int(sr), "ch": 0, "codec": codec, "bitrate": int(kbps or 0) * 1000, "bits": 0}


def decode(path):
    r = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return None
    return np.frombuffer(r.stdout, dtype=np.float32)


def dbfs(x):
    return 20.0 * np.log10(max(float(x), 1e-12))


def analyse(x, meta):
    dur = len(x) / SR if x is not None else 0.0
    out = {"duration_s": round(dur, 2), **{k: meta[k] for k in ("sr", "codec", "bitrate", "bits")}}
    if x is None or dur <= 0.05:
        out["error"] = "decode failed or too short"
        return out

    peak = float(np.max(np.abs(x)))
    out["peak_dbfs"] = round(dbfs(peak), 2)
    out["clip_ratio"] = round(float(np.mean(np.abs(x) >= 0.999)), 6)
    out["dc_offset"] = round(float(abs(np.mean(x))), 6)

    # 底噪：0.5 秒窗的最小 RMS；SNR：语音帧 RMS 中位数 - 底噪
    win = int(0.5 * SR)
    if len(x) >= win:
        frames = x[: len(x) // win * win].reshape(-1, win)
        rms_win = np.sqrt(np.mean(frames ** 2, axis=1))
        nf = float(np.min(rms_win))
        speech = float(np.median(rms_win[rms_win > np.percentile(rms_win, 60)])) if len(rms_win) > 3 else float(np.max(rms_win))
    else:
        nf = float(np.sqrt(np.mean(x ** 2)))
        speech = nf
    out["noise_floor_dbfs"] = round(dbfs(nf), 2)
    out["snr_db"] = round(dbfs(speech) - dbfs(nf), 2)

    # 指纹：40ms 帧自相关求 f0 + 频谱质心
    hop = int(0.04 * SR)
    f0s, cents = [], []
    for i in range(0, max(1, len(x) - hop), hop * 2):
        seg = x[i:i + hop]
        if len(seg) < hop or np.sqrt(np.mean(seg ** 2)) < 0.01:
            continue
        seg = seg - seg.mean()
        ac = np.correlate(seg, seg, mode="full")[hop - 1:]
        lo, hi = int(SR / 400), min(len(ac) - 1, int(SR / 70))
        if hi <= lo:
            continue
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[0] > 0 and ac[k] / ac[0] > 0.3:
            f0s.append(SR / k)
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        fr = np.fft.rfftfreq(len(seg), 1.0 / SR)
        if spec.sum() > 0:
            cents.append(float((spec * fr).sum() / spec.sum()))
    out["f0_median_hz"] = round(float(np.median(f0s)), 1) if f0s else None
    out["centroid_hz"] = round(float(np.median(cents)), 0) if cents else None
    return out


def judge(rep):
    bad = []
    if rep.get("error"):
        return [rep["error"]]
    if rep["sr"] < TH["sample_rate_min"]:
        bad.append("采样率 %d < %d" % (rep["sr"], TH["sample_rate_min"]))
    if rep["peak_dbfs"] > TH["peak_dbfs_max"]:
        bad.append("峰值 %.2f dBFS 顶到 0，会削波" % rep["peak_dbfs"])
    if rep["clip_ratio"] > TH["clip_ratio_max"]:
        bad.append("削波样本 %.3f%% > %.2f%%" % (rep["clip_ratio"] * 100, TH["clip_ratio_max"] * 100))
    if rep["dc_offset"] > TH["dc_max"]:
        bad.append("DC 偏移 %.4f > %.3f" % (rep["dc_offset"], TH["dc_max"]))
    nf = rep["noise_floor_dbfs"]
    if nf > TH["noise_floor_dbfs_max"]:
        bad.append("底噪 %.1f dBFS 偏高（> %.0f）= 房间/电流噪声进片" % (nf, TH["noise_floor_dbfs_max"]))
    if nf < TH["noise_floor_dbfs_min"]:
        bad.append("底噪 %.1f dBFS 太低（数字静音）= 过度降噪，听感塑料" % nf)
    if rep["snr_db"] < TH["snr_db_min"]:
        bad.append("信噪比 %.1f dB < %.0f，台词糊在底噪里" % (rep["snr_db"], TH["snr_db_min"]))
    codec = (rep.get("codec") or "").lower()
    if codec in ("mp3", "aac", "opus", "vorbis") and rep["bitrate"] and rep["bitrate"] < TH["lossy_bitrate_min"]:
        bad.append("有损码率 %d kbps < %d" % (rep["bitrate"] // 1000, TH["lossy_bitrate_min"] // 1000))
    if codec in ("pcm_s16le", "pcm_s24le", "pcm_s32le", "flac") and rep["bits"] and rep["bits"] < TH["wav_bits_min"]:
        bad.append("位深 %d bit < %d" % (rep["bits"], TH["wav_bits_min"]))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--voice-map", default="", help='json: {"角色名":"voice_id", ...}')
    a = ap.parse_args()

    if not FFMPEG:
        print(json.dumps({"verdict": "BLOCKED", "error": "ffmpeg not found"}, ensure_ascii=False))
        return 3
    if not os.path.isdir(a.dir):
        print(json.dumps({"verdict": "BLOCKED", "error": "dir missing: %s" % a.dir}, ensure_ascii=False))
        return 3

    files = []
    for root, _d, names in os.walk(a.dir):
        for n in names:
            if n.lower().endswith(AUDIO_EXT):
                files.append(os.path.join(root, n))
    if not files:
        print(json.dumps({"verdict": "BLOCKED", "error": "no audio in %s" % a.dir}, ensure_ascii=False))
        return 3

    rows, bad_files = [], []
    for p in sorted(files):
        rep = analyse(decode(p), probe(p))
        gaps = judge(rep)
        rep["file"] = os.path.relpath(p, a.dir)
        rep["gaps"] = gaps
        rep["ok"] = not gaps
        rows.append(rep)
        if gaps:
            bad_files.append(rep["file"])
        print("%s %s f0=%s noise=%s snr=%s" % (
            "PASS" if rep["ok"] else "FAIL", rep["file"],
            rep.get("f0_median_hz"), rep.get("noise_floor_dbfs"), rep.get("snr_db")))
        for g in gaps:
            print("      - " + g)

    dup = []
    if a.voice_map and os.path.exists(a.voice_map):
        vm = json.load(open(a.voice_map, encoding="utf-8"))
        used = {}
        for who, vid in vm.items():
            if vid:
                used.setdefault(vid, []).append(who)
        for vid, who in used.items():
            if len(who) > 1:
                dup.append({"voice_id": vid, "characters": who})

    result = {
        "dir": a.dir, "files": len(rows), "pass": len(rows) - len(bad_files),
        "fail": len(bad_files), "bad_files": bad_files,
        "voice_dupes": dup, "rows": rows,
        "verdict": "PASS" if not bad_files and not dup else "FAIL",
    }
    print("\n%s %d/%d 合格%s" % (result["verdict"], result["pass"], result["files"],
                                 "" if not dup else "，另有 %d 组音色撞车" % len(dup)))
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(result, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())