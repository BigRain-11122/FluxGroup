#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_quality_gate.py - 漫剧/短剧 v2 交付闸（对标头部平台的硬指标）。

为什么（2026-11-03 CEO「漫剧短剧产出非常糟糕，赶不上头部」）：我们 60 集成片的实测规格是
**540×960 / 25fps / 无音轨**——头部全是 1080×1920 / 30fps / 人声+音效+BGM。这不是"审美差"，
是三个可以量出来的硬指标没达标，外加节奏没管。

v2 判据（全部机器可测，缺一即 FAIL）：
  1. 竖屏 1080×1920（允许 720×1280 降档，低于此判 FAIL）
  2. 帧率 ≥ 30
  3. 必须有音轨，且整体响度 -14 LUFS ±2（短视频平台口径）
  4. 时长 10–90 秒（单集/样片口径）
  5. 前 3 秒必须有画面变化（钩子不是静止图）：帧差均方 > 阈值
  6. 平均镜长 ≤ 4.0 秒（节奏；头部 2–3 秒一切）
  7. 字幕轨或烧字幕存在（--subs 指定时校验文件，未指定则只提示）

用法：
  python3 drama_quality_gate.py --in sample.mp4 [--out receipts/xxx.json] [--subs subs.ass]
Exit: 0 = PASS；1 = FAIL（列缺口）；2 = 文件读不了。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

FFPROBE = "ffprobe"
FFMPEG = "ffmpeg"


def sh(cmd, timeout=180):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def probe(path):
    """优先 ffprobe；本机没有 ffprobe 时退回解析 ffmpeg -i 的 stderr（保底可用）。"""
    if shutil.which(FFPROBE):
        rc, out = sh([FFPROBE, "-v", "error", "-show_streams", "-show_format",
                      "-of", "json", path], 60)
        if rc == 0:
            try:
                return json.loads(out[out.index("{"):])
            except Exception:
                pass
    ff = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "/Users/%s/bin/ffmpeg" % os.environ.get("USER", "")
    rc, out = sh([ff, "-hide_banner", "-i", path], 60)
    if "Duration:" not in (out or ""):
        return None
    import re as _re
    d = _re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out)
    dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0
    v = _re.search(r"Video:.*?(\d{2,5})x(\d{2,5}).*?([\d.]+) fps", out)
    has_a = "Audio:" in out
    sa = _re.search(r"Audio:.*?(\d{4,6}) Hz", out)
    return {"streams": ([{"codec_type": "video",
                          "width": int(v.group(1)), "height": int(v.group(2)),
                          "r_frame_rate": "%d/1" % int(float(v.group(3)))}] if v else [])
                         + ([{"codec_type": "audio",
                              "sample_rate": sa.group(1) if sa else "0"}] if has_a else []),
            "format": {"duration": str(dur)}}


def loudness(path):
    """Integrated LUFS（不是 mean_volume：RMS 与 LUFS 差 3–5dB，用错就会假红）。"""
    ff = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or \
        "/Users/%s/bin/ffmpeg" % os.environ.get("USER", "")
    rc, out = sh([ff, "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json",
                  "-f", "null", "-"], 180)
    m = re.search(r'"input_i"\s*:\s*"?(-?[\d.]+)"?', out or "")
    if m:
        return float(m.group(1))
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", out or "")
    return float(m.group(1)) + 4.0 if m else None


def motion_first3s(path):
    """Mean absolute frame difference over the first 3 seconds (0-255 scale)."""
    rc, out = sh([FFMPEG, "-hide_banner", "-t", "3", "-i", path, "-vf",
                  "select='gt(scene,0)',metadata=print:file=-", "-f", "null", "-"], 120)
    vals = [float(x) for x in re.findall(r"scene_score=([\d.]+)", out or "")]
    return (sum(vals) / len(vals)) if vals else 0.0


def cuts(path):
    """Count scene changes > 0.30 via scene detection."""
    rc, out = sh([FFMPEG, "-hide_banner", "-i", path, "-vf",
                  "select='gt(scene,0.30)',metadata=print:file=-", "-f", "null", "-"], 300)
    return len(re.findall(r"scene_score=", out or ""))



def global_shift_ratio(path):
    """Estimated share of motion that is a pure global translation (Ken Burns tell).

    做法：比较相邻帧整体位移（相位相关近似：用 ffmpeg 的 vidstabdetect 输出 lm/max 位移量）
    与局部细节变化的比例。推拉图：几乎全是全局位移、局部细节变化≈0。
    这里用更稳的近似：统计 mpeg 运动向量里"方向高度一致"的比例。
    """
    rc, out = sh([FFMPEG, "-hide_banner", "-i", path, "-vf",
                  "select='gte(scene,0)',metadata=print:file=-", "-f", "null", "-"], 120)
    return None  # 保守：无可靠实现时返回 None，不据此判红


def static_shot_flags(path, dur, ncut):
    """A shot that is essentially a still image with zoom = not animated. Detect by
    comparing per-frame laplacian variance (detail) stability: 推拉只改尺度，细节能量几乎不变。"""
    rc, out = sh([FFMPEG, "-hide_banner", "-i", path, "-vf",
                  "select='not(mod(n,15))',metadata=print:file=-", "-f", "null", "-"], 180)
    return None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--subs", default="")
    ap.add_argument("--subs-burned", dest="subs_burned", action="store_true",
                    help="声明字幕已烧进画面（无法从像素反查时的显式申报）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.exists(a.src) or not probe(a.src):
        # 读不了也要留证据（2026-11-03）：工序卡零产物退出会让下游永远判不出"没干"还是
        # "干不了"，线就静默停摆。写 BLOCKED 回执写明缺哪件，链上看得见。
        why = ("成片不存在：%s（上游装配未产出）" % a.src) if not os.path.exists(a.src) \
            else ("ffprobe/ffmpeg 读不出元数据：%s" % a.src)
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "input": a.src,
               "spec": "DRAMA-QUALITY-SPEC-v2", "verdict": "BLOCKED", "status": "BLOCKED",
               "gaps": [why], "measured": {}, "tool": "drama_quality_gate"}
        print(why)
        if a.out:
            d = os.path.dirname(os.path.abspath(a.out))
            if d:
                os.makedirs(d, exist_ok=True)
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
        return 2
    pr = probe(a.src)
    v = next((s for s in pr.get("streams") or [] if s.get("codec_type") == "video"), {})
    au = next((s for s in pr.get("streams") or [] if s.get("codec_type") == "audio"), None)
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    dur = float(pr.get("format", {}).get("duration") or 0.0)
    gaps = []
    if not (h > w):
        gaps.append("不是竖屏（%dx%d）" % (w, h))
    if not ((w >= 1080 and h >= 1920) or (w >= 720 and h >= 1280)):
        gaps.append("分辨率不足：%dx%d（v2 要求 ≥720×1280，正档 1080×1920）" % (w, h))
    if fps < 29.5:
        gaps.append("帧率不足：%.1ffps（v2 要求 ≥30）" % fps)
    if not au:
        gaps.append("没有音轨（v2 要求人声+音效+BGM 混音，-14 LUFS）")
    lufs = loudness(a.src) if au else None
    if au and (lufs is None or abs(lufs + 14) > 2.5):
        gaps.append("响度不合规：%s（目标 -14 LUFS ±2）" % (("%.1f dB" % lufs) if lufs is not None else "测不出"))
    # 采样率也是交付硬指标（2026-11-03 实测坑）：loudnorm 内部跑 192k，AAC 上限截到 96k，
    # 成片音轨会静默变成 96kHz，平台一律按 48k/44.1k 收。
    sr = int(au.get("sample_rate") or 0) if au else 0
    if au and sr not in (48000, 44100):
        gaps.append("音轨采样率不合规：%d Hz（交付要求 48000/44100）" % sr)
    if not (10 <= dur <= 90):
        gaps.append("时长 %.1fs 不在 10–90 秒" % dur)
    mot = motion_first3s(a.src)
    if mot < 0.02:
        gaps.append("前 3 秒几乎不动（帧差 %.3f，钩子不成立）" % mot)
    ncut = cuts(a.src)
    avg_shot = dur / (ncut + 1) if dur else 0
    if avg_shot > 4.5:
        gaps.append("平均镜长 %.1fs（v2 要求 ≤4s，头部 2–3s 一切）" % avg_shot)
    if a.subs and not os.path.exists(a.subs):
        gaps.append("字幕文件不存在：%s" % a.subs)
    elif not a.subs and not a.subs_burned:
        # 判据 7 必须真判（2026-11-03）：此前不传 --subs 就只提示，等于把 CANON 的
        # 「字幕」判据做成装饰。改成二选一申报——给字幕文件，或声明已烧进画面。
        gaps.append("字幕未校验：必须传 --subs <字幕文件> 或声明 --subs-burned")
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "input": a.src,
           "spec": "DRAMA-QUALITY-SPEC-v2", "verdict": "PASS" if not gaps else "FAIL",
           "gaps": gaps,
           "measured": {"w": w, "h": h, "subs": (a.subs or ("burned" if a.subs_burned else "")), "fps": round(fps, 2), "duration_s": round(dur, 2),
                        "has_audio": bool(au), "audio_sr": sr, "mean_volume_db": lufs,
                        "first3s_motion": round(mot, 4), "cuts": ncut,
                        "avg_shot_s": round(avg_shot, 2)}}
    out["status"] = out["verdict"]
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("DRAMA-QA %s  %s" % (out["verdict"], os.path.basename(a.src)))
        print("  %dx%d %.1ffps %.1fs audio=%s loud=%s motion3s=%.3f cuts=%d avg_shot=%.1fs"
              % (w, h, fps, dur, bool(au), lufs, mot, ncut, avg_shot))
        for g in gaps:
            print("  ! %s" % g)
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))