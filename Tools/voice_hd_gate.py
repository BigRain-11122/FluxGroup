# -*- coding: utf-8 -*-
"""voice_hd_gate.py - 音色质检（CAST-DISTINCTIVENESS-LAW-v1 §三/§四）。

CEO 令 2026-11-03：「音色也要高清，没有杂音。」
现有 tts_batch_check.py 只数文件在不在，判不了音质；这里补音质这一层。

**两档口径（2026-11-04 按真实素材标定后重写）**
- --profile source（默认）：判「素材本身有没有硬伤」——削波、DC 偏移、采样率低于平台下限、真峰值顶头。
  底噪/SNR 只报告不判决：本机 10 条真实云端 TTS 用窗口分位法量出的 SNR 中位 15.2 dB，
  该数在连续语音上被系统性低估（无静音段时"最静窗"仍是语音），拿它当硬门会误杀好素材。
  → 判据宁缺勿假：测不准的项不进判决（同 ai_smell_gate 强弱证据分离的教训）。
- --profile delivery：判「成片能不能交」——48k、≥192kbps、-14 LUFS ±1、真峰值 ≤ -1 dBTP。

标定依据（2026-11-03 实测，media/BigStream 真实云端 TTS 10 条）：
  采样率 22.05–24 kHz / 码率 47–59 kbps / 峰值 -23.2…-0.01 dBFS /
  底噪 -58…-17.4 dBFS / SNR(窗口分位法) 12.2–31.5 dB / LUFS -48.5…-16.2。
  结论：现有云端 TTS 属「低档素材」（24k/48k），这是生产事实不是测量误差——
  要 48k 就得换 TTS 出档设置，属于产线决策，不是把闸调宽能解决的。

用法：
  python Tools/voice_hd_gate.py --dir <音频目录> [--profile source|delivery]
      [--out r.json] [--voice-map map.json]
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

# 硬门（可机判、无争议）
HARD = {
    "source": {
        "sample_rate_min": 22050,   # 低于此值高频明显被切（现有云端 TTS 实测下限 22050）
        "peak_dbfs_max": -0.1,      # 顶到 0 会削波
        "clip_ratio_max": 0.0002,   # 削波样本 ≤0.02%
        "dc_max": 0.005,
        "min_duration_s": 0.3,
    },
    "delivery": {
        "sample_rate_min": 48000,
        "sample_rate_expect": 48000,
        "lossy_bitrate_min": 192000,
        "peak_dbfs_max": -1.0,      # 真峰值 -1 dBTP
        "clip_ratio_max": 0.0001,
        "dc_max": 0.002,
        "lufs_target": -14.0,
        "lufs_tol": 1.0,
        "min_duration_s": 0.3,
    },
}
# 报告项（测不准或未标定，只提示不判决）
SOFT_NOTE = {
    "noise_floor_dbfs": "底噪（最静 0.5s 窗）——无静音段时会被高估，只作提示",
    "snr_db": "SNR（窗口分位法）——连续语音上系统性低估，未做听感标定，不作放行依据",
    "lufs": "素材响度——装配统一 loudnorm，仅素材档提示",
}


def which(name):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        for ext in (".exe", ""):
            c = os.path.join(p, name + ext)
            if os.path.exists(c):
                return c
    return None


FFMPEG = which("ffmpeg")
FFPROBE = which("ffprobe")


def probe(path):
    if FFPROBE:
        r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a:0",
                            "-show_entries",
                            "stream=sample_rate,channels,bit_rate,bits_per_sample,bits_per_raw_sample,sample_fmt,codec_name",
                            "-of", "json", path], capture_output=True, text=True)
        try:
            st = json.loads(r.stdout)["streams"][0]
            bits = int(st.get("bits_per_sample") or st.get("bits_per_raw_sample") or 0)
            return {"sr": int(st.get("sample_rate") or 0), "ch": int(st.get("channels") or 0),
                    "codec": st.get("codec_name"), "bitrate": int(st.get("bit_rate") or 0),
                    "bits": bits, "fmt": st.get("sample_fmt")}
        except Exception:
            pass
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True)
    m = re.search(r"Audio: (\w+).*?, (\d+) Hz, (\w+)(?:, (\d+) kb/s)?", r.stderr)
    codec, sr, _l, kbps = m.groups() if m else (None, 0, None, None)
    return {"sr": int(sr or 0), "ch": 0, "codec": codec,
            "bitrate": int(kbps or 0) * 1000, "bits": 0, "fmt": None}


def loudness(path):
    """LUFS(I) 与真峰值，用 loudnorm 的测量结果（与装配链同一把尺）。"""
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", path, "-af",
                        "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        return None, None
    try:
        d = json.loads(m.group(0))
        return float(d["input_i"]), float(d["input_tp"])
    except Exception:
        return None, None


def decode(path):
    r = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32) if r.returncode == 0 and r.stdout else None


def dbfs(x):
    return 20.0 * np.log10(max(float(x), 1e-12))


def silence_gaps(x):
    """真正的静音段（≤ -50 dBFS 的 0.3s 窗）数量——有静音才量得出底噪。"""
    win = int(0.3 * SR)
    if len(x) < win:
        return 0
    n = len(x) // win
    frames = x[: n * win].reshape(n, win)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    return int(np.sum(20 * np.log10(np.maximum(rms, 1e-12)) <= -50))


def analyse(path):
    meta = probe(path)
    x = decode(path)
    rep = dict(meta)
    if x is None or len(x) < SR * 0.2:
        rep["error"] = "decode failed or too short"
        return rep
    dur = len(x) / SR
    rep["duration_s"] = round(dur, 2)
    peak = float(np.max(np.abs(x)))
    rep["peak_dbfs"] = round(dbfs(peak), 2)
    rep["clip_ratio"] = round(float(np.mean(np.abs(x) >= 0.999)), 6)
    rep["dc_offset"] = round(float(abs(np.mean(x))), 6)

    win = int(0.5 * SR)
    if len(x) >= win:
        n = len(x) // win
        rms = np.sqrt(np.mean(x[: n * win].reshape(n, win) ** 2, axis=1))
        rep["noise_floor_dbfs"] = round(dbfs(float(np.percentile(rms, 10))), 1)
        rep["snr_db"] = round(dbfs(float(np.percentile(rms, 90))) -
                              dbfs(float(np.percentile(rms, 10))), 1)
    rep["silence_gaps"] = silence_gaps(x)

    # 音色指纹：40ms 帧自相关 f0 + 频谱质心
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
    rep["f0_median_hz"] = round(float(np.median(f0s)), 1) if f0s else None
    rep["centroid_hz"] = round(float(np.median(cents)), 0) if cents else None

    lufs, tp = loudness(path)
    rep["lufs"] = lufs
    rep["true_peak_dbtp"] = tp
    return rep


def judge(rep, profile):
    th = HARD[profile]
    bad = []
    if rep.get("error"):
        return [rep["error"]]
    if rep.get("duration_s", 0) < th["min_duration_s"]:
        bad.append("时长 %.2fs < %.1fs（几乎是空文件）" % (rep["duration_s"], th["min_duration_s"]))
    if rep["sr"] < th["sample_rate_min"]:
        bad.append("采样率 %d < %d" % (rep["sr"], th["sample_rate_min"]))
    if rep["clip_ratio"] > th["clip_ratio_max"]:
        bad.append("削波样本 %.3f%% > %.3f%%" % (rep["clip_ratio"] * 100, th["clip_ratio_max"] * 100))
    if rep["dc_offset"] > th["dc_max"]:
        bad.append("DC 偏移 %.4f > %.3f" % (rep["dc_offset"], th["dc_max"]))

    codec = (rep.get("codec") or "").lower()
    if profile == "delivery":
        if rep.get("true_peak_dbtp") is not None and rep["true_peak_dbtp"] > th["peak_dbfs_max"]:
            bad.append("真峰值 %.2f dBTP > %.1f（会被转码削波）" % (rep["true_peak_dbtp"], th["peak_dbfs_max"]))
        elif rep.get("true_peak_dbtp") is None and rep["peak_dbfs"] > th["peak_dbfs_max"]:
            bad.append("峰值 %.2f dBFS 顶头" % rep["peak_dbfs"])
        if codec in ("mp3", "aac", "opus", "vorbis") and rep.get("bitrate") and \
                rep["bitrate"] < th["lossy_bitrate_min"]:
            bad.append("有损码率 %d kbps < %d" % (rep["bitrate"] // 1000, th["lossy_bitrate_min"] // 1000))
        if rep.get("lufs") is None:
            bad.append("量不出响度（loudnorm 失败）")
        elif abs(rep["lufs"] - th["lufs_target"]) > th["lufs_tol"]:
            bad.append("响度 %.1f LUFS 偏离 %.0f±%.0f（交付必须归一）"
                       % (rep["lufs"], th["lufs_target"], th["lufs_tol"]))
    else:
        if rep["peak_dbfs"] > th["peak_dbfs_max"]:
            bad.append("峰值 %.2f dBFS 顶头" % rep["peak_dbfs"])
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--profile", choices=["source", "delivery"], default="source")
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

    rows, bad_files, notes = [], [], set()
    for p in sorted(files):
        rep = analyse(p)
        gaps = judge(rep, a.profile)
        rep["file"] = os.path.relpath(p, a.dir)
        rep["gaps"] = gaps
        rep["ok"] = not gaps
        rows.append(rep)
        if gaps:
            bad_files.append(rep["file"])
        print("%s %-28s sr=%s kbps=%s peak=%s lufs=%s tp=%s" % (
            "PASS" if rep["ok"] else "FAIL", rep["file"], rep.get("sr"),
            (rep.get("bitrate") or 0) // 1000, rep.get("peak_dbfs"),
            rep.get("lufs"), rep.get("true_peak_dbtp")))
        for g in gaps:
            print("      - " + g)
        if rep.get("silence_gaps", 0) == 0:
            notes.add("无静音段的文件：底噪/SNR 不可信，已不进判决")

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
        "dir": a.dir, "profile": a.profile, "files": len(rows),
        "pass": len(rows) - len(bad_files), "fail": len(bad_files),
        "bad_files": bad_files, "voice_dupes": dup, "notes": sorted(notes),
        "not_judged": SOFT_NOTE if a.profile == "source" else {},
        "rows": rows, "verdict": "PASS" if not bad_files and not dup else "FAIL",
    }
    print("\n%s [%s] %d/%d 合格%s" % (result["verdict"], a.profile, result["pass"],
                                      result["files"],
                                      "" if not dup else "，另有 %d 组音色撞车" % len(dup)))
    for n in result["notes"]:
        print("  注：" + n)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(result, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())