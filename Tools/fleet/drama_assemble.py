#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_assemble.py - 漫剧装配（和 MV 同一条链：图生视频片段 → 剪辑 → 配音 → 字幕）。

为什么（2026-11-03 CEO 纠正）：漫剧不是"推拉图片"，也不是引擎渲染，就是 MV 那条链——
  关键帧 → 图生视频（i2v）→ 剪辑拼接 → 配音/配乐 → 字幕 → 交付闸。
本脚本只做"装配"这一段：吃已经生成好的 i2v 片段，合成为 1080×1920/30fps 成片，
并保证音轨齐全（人声+音乐，loudnorm -14 LUFS）与字幕烧制。

用法：
  python3 drama_assemble.py --manifest m.json --out sample.mp4 [--qa out-qa.json]

manifest:
{
  "clips": ["c1.mp4", "c2.mp4", "c3.mp4"],     # i2v 生成的片段（顺序即时间线）
  "voice": "voice.mp3", "voice_at": 0.4,
  "music": "music.wav", "music_gain": 0.35,
  "subs": [{"text": "…", "from": 0.2, "to": 3.6}],
  "font": "可选"
}
Exit: 0 成片已出；1 环境/输入问题。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30


def ff():
    for c in (os.environ.get("FFMPEG"), "ffmpeg", "/Users/%s/bin/ffmpeg" % os.environ.get("USER", "")):
        if not c:
            continue
        if os.path.isabs(c) and os.path.exists(c):
            return c
        if shutil.which(c):
            return c
    return None


def run(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def find_font(explicit=None):
    for c in ([explicit] if explicit else []) + [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            r"C:\Windows\Fonts\msyh.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
        if c and os.path.exists(c):
            return c
    return None


def ts(sec):
    return "%d:%02d:%05.2f" % (sec // 3600, (sec % 3600) // 60, sec % 60)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--qa", default="")
    a = ap.parse_args(argv)
    F = ff()
    if not F:
        print("[asm] 没有 ffmpeg")
        return 1
    man = json.load(open(a.manifest, encoding="utf-8-sig"))
    clips = man.get("clips") or []
    if not clips:
        print("[asm] manifest 没有 clips（i2v 片段）")
        return 1
    tmp = tempfile.mkdtemp(prefix="drama_asm_")
    norm = []
    for i, c in enumerate(clips, 1):
        p = os.path.join(tmp, "n%d.mp4" % i)
        rc, out = run([F, "-y", "-i", c, "-vf",
                       "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,format=yuv420p"
                       % (W, H, W, H, FPS),
                       "-an", "-c:v", "libx264", "-crf", "20", p])
        if rc != 0:
            print("[asm] 归一失败 %s: %s" % (c, out[-200:]))
            return 1
        norm.append(p)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in norm:
            f.write("file '%s'\n" % p.replace("\\", "/"))
    silent = os.path.join(tmp, "v.mp4")
    rc, out = run([F, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    if rc != 0:
        print("[asm] 拼接失败：%s" % out[-200:])
        return 1
    # 时长
    rc, out = run([F, "-hide_banner", "-i", silent])
    dur = 0.0
    for line in (out or "").splitlines():
        if "Duration:" in line:
            hh, mm, ss = line.split("Duration:")[1].split(",")[0].strip().split(":")
            dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
            break
    if dur <= 0:
        print("[asm] 读不出时长")
        return 1
    font = find_font(man.get("font"))
    vf = None
    subs = man.get("subs") or []
    if font and subs:
        ass = os.path.join(tmp, "s.ass")
        with open(ass, "w", encoding="utf-8") as f:
            f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\n\n"
                    "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour,"
                    " BackColour, Bold, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                    "Style: D,Default,62,&H00FFFFFF,&H00000000,&H64000000,1,2,60,60,170,1\n\n"
                    "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
                    % (W, H))
            for s in subs:
                st, en = float(s.get("from", 0)), float(s.get("to", dur))
                f.write("Dialogue: 0,%s,%s,D,,0,0,0,,%s\n" % (ts(st), ts(min(en, dur)), s.get("text", "")))
        vf = "ass=%s:fontsdir=%s" % (ass.replace("\\", "/").replace(":", "\\:"),
                                     os.path.dirname(font).replace("\\", "/").replace(":", "\\:"))
    voice = man.get("voice")
    music = man.get("music")
    inputs = ["-i", silent]
    filters = []
    labels = []
    idx = 1
    if voice:
        inputs += ["-i", voice]
        vat = float(man.get("voice_at", 0.3))
        filters.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=%d|%d,volume=1.8[v]"
                       % (idx, int(vat * 1000), int(vat * 1000)))
        labels.append("[v]")
        idx += 1
    if music:
        inputs += ["-stream_loop", "-1", "-i", music]
        g = float(man.get("music_gain", 0.35))
        filters.append("[%d:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=%.2f,atrim=0:%.2f[m]"
                       % (idx, g, dur))
        labels.append("[m]")
        idx += 1
    if labels:
        filters.append("%samix=inputs=%d:duration=first:dropout_transition=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
                       % ("".join(labels), len(labels)))
        audio = ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[a]"]
        af = None
    else:
        audio = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                 "-map", "0:v:0", "-map", "1:a:0"]
        af = None
    cmd = [F, "-y"] + inputs
    if af is None and labels:
        pass
    if vf:
        cmd += ["-vf", vf]
    cmd += audio + ["-t", "%.3f" % dur, "-c:v", "libx264", "-profile:v", "high", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", a.out]
    rc, out = run(cmd)
    if rc != 0:
        print("[asm] 合成失败：%s" % out[-400:])
        return 1
    print("[asm] 成片：%s（%.1fs %dx%d@%d 字幕=%s）" % (a.out, dur, W, H, FPS, "有" if vf else "无"))
    gate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drama_quality_gate.py")
    qa = a.qa or (os.path.splitext(a.out)[0] + "-qa.json")
    rc2, out2 = run([sys.executable, gate, "--in", a.out, "--out", qa])
    print("[asm] 闸：" + ((out2.strip().splitlines() or [""])[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))