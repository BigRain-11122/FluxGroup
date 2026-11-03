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
Exit: 0 成片已出；1 环境问题（无 ffmpeg/合成失败）；3 输入未到位（manifest 或片段缺）。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30


def video_codec_args(ffmpeg):
    """硬件编码优先（2026-11-03 实测 M1 Pro：libx264 preset slow 6.95s/50s CPU，
    h264_videotoolbox 2.07s/2.3s CPU —— 墙钟 3x、CPU 省 20 倍）。
    交付兼容性优先时不想要硬件编码，设环境变量 ASSEMBLE_ENCODER=libx264 即可。"""
    want = (os.environ.get("ASSEMBLE_ENCODER") or "auto").lower()
    if want == "libx264":
        return ["-c:v", "libx264", "-crf", "19", "-profile:v", "high"]
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True,
                           text=True, timeout=30)
        if "h264_videotoolbox" in (r.stdout or ""):
            return ["-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1"]
    except Exception:
        pass
    return ["-c:v", "libx264", "-crf", "19", "-profile:v", "high"]


def blocked(qa, why, src=None):
    """输入未到位时也要留证据：写一份 BLOCKED 回执，写明缺什么。

    2026-11-03 教训：工序卡若在缺素材时"零产物退出"，下游永远判不出是没干还是干不了，
    线会静默停摆。回执就是"我跑过了、卡在这一项"的机器可读说法。
    """
    import time
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "input": src or "",
           "spec": "DRAMA-QUALITY-SPEC-v2", "verdict": "BLOCKED", "status": "BLOCKED",
           "rc": 3, "error_class": "E-BLOCKED-INPUT",
           "gaps": [why], "tool": "drama_assemble"}
    if qa:
        d = os.path.dirname(os.path.abspath(qa))
        if d:
            os.makedirs(d, exist_ok=True)
        try:
            with open(qa, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
        except Exception:
            pass
    return out


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
        print("[asm] 没有 ffmpeg（环境问题，rc=1）")
        return 1
    # rc=3 = 输入还没到位（manifest 或片段没生成），不是工具坏。
    # 工序卡按 ok_rc=[0,3] 判：缺素材记"等上游"，不制造每天必红的假红。
    if not os.path.exists(a.manifest):
        print("[asm] manifest 不存在：%s（上游 i2v 片段未生成，rc=3）" % a.manifest)
        blocked(a.qa, "manifest 不存在：%s（上游 i2v 片段未生成）" % a.manifest)
        return 3
    man = json.load(open(a.manifest, encoding="utf-8-sig"))
    clips = man.get("clips") or []
    if not clips:
        print("[asm] manifest 没有 clips（i2v 片段未生成，rc=3）")
        blocked(a.qa, "manifest 没有 clips（i2v 片段未生成）", a.manifest)
        return 3
    missing = [c for c in clips if not os.path.exists(c)]
    if missing:
        print("[asm] 片段不在盘：%s（rc=3）" % ", ".join(missing[:3]))
        blocked(a.qa, "片段不在盘：%s" % ", ".join(missing[:3]), a.manifest)
        return 3
    tmp = tempfile.mkdtemp(prefix="drama_asm_")
    norm = []
    for i, c in enumerate(clips, 1):
        p = os.path.join(tmp, "n%d.mp4" % i)
        rc, out = run([F, "-y", "-i", c, "-vf",
                       "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,format=yuv420p"
                       % (W, H, W, H, FPS),
                       "-an"] + video_codec_args(F) + [p])
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
        # loudnorm 内部跑 192k，AAC 上限截到 96k → 交付音轨会变成 96kHz。
        # 必须显式收敛回 48k（平台一律按 48k/44.1k 收）。
        filters.append("%samix=inputs=%d:duration=first:dropout_transition=0,"
                       "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
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
    cmd += audio + ["-t", "%.3f" % dur] + video_codec_args(F) + [
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        "-movflags", "+faststart", a.out]
    rc, out = run(cmd)
    if rc != 0:
        print("[asm] 合成失败：%s" % out[-400:])
        return 1
    print("[asm] 成片：%s（%.1fs %dx%d@%d 字幕=%s）" % (a.out, dur, W, H, FPS, "有" if vf else "无"))
    gate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drama_quality_gate.py")
    qa = a.qa or (os.path.splitext(a.out)[0] + "-qa.json")
    rc2, out2 = run([sys.executable, gate, "--in", a.out, "--out", qa] +
                    (["--subs-burned"] if vf else []))
    print("[asm] 闸：" + ((out2.strip().splitlines() or [""])[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))