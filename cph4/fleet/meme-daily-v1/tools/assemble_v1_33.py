#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assemble_v1_33.py - meme V1《慢慢踩》v3.3 确定性装配器（bm-c 接管版·O-20261011-1436 §2）
依据=topics/v1-shots-v33.json（PREPRO-V1.md v3.3 CERTIFIED 六拍 14.1s·J-M19 平台机制三刀改）
律=J-M10 乐句终止式收束（BGM 静点切·非包络）/J-M13 暗衬底带+粗黑字幕/wordmark+热线错峰/C6 零AI合成/C7 标识卡
用法: python assemble_v1_33.py --repo K:/Fluxgroup/FluxGroup --media <repo>/media/meme-daily-v1/v1-zunjie-brake --out <同 media>/final
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
GOLD = "{\\c&H0000D7FF&}"
WHITE = "{\\c&H00FFFFFF&}"

def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, cwd=cwd)
    if r.returncode != 0:
        sys.exit("FFMPEG FAIL: " + " ".join(cmd) + "\n" + r.stderr.decode("utf-8", "replace")[-1800:])

def dur_of(ff, path):
    r = subprocess.run([ff, "-i", path], capture_output=True)
    m = re.search(rb"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", r.stderr)
    if not m:
        sys.exit("无法读时长: " + path)
    h, mi, s, cs = (int(x) for x in m.groups())
    return h * 3600 + mi * 60 + s + cs / 100.0

def ass_time(t):
    t = max(0.0, t)
    return "%d:%02d:%05.2f" % (int(t // 3600), int(t % 3600 // 60), t % 60)

def wav_rms_windows(path, win=0.02):
    with wave.open(path, "rb") as w:
        sr = w.getframerate(); nch = w.getnchannels(); sw = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    assert sw == 2, "需要 16bit wav"
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, nch)
    mono = x.mean(axis=1)
    n = int(sr * win)
    rms = np.sqrt((mono[: len(mono) // n * n].reshape(-1, n) ** 2).mean(axis=1))
    return rms, sr, win

def quietest_in(rms, sr, win, lo, hi):
    a, b = int(lo / win), min(int(hi / win), len(rms) - 1)
    seg = rms[a:b]
    return (int(np.argmin(seg)) + a) * win + win / 2.0   # 返回中心秒

def build_ass(spec, total):
    FN = "Microsoft YaHei"
    styles = [
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Big,%s,44,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,8,0,2,40,40,240,1" % FN,
        "Style: Gold,%s,44,&H0000D7FF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,8,0,2,40,40,240,1" % FN,
        "Style: Wall,%s,58,&H00FFFFFF,&H000000FF,&H60000000,&H00000000,-1,0,0,0,100,100,2,0,1,4,0,8,40,40,150,1" % FN,
        "Style: Small,%s,27,&H00F2F2F2,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,6,0,2,40,40,210,1" % FN,
        "Style: Data,%s,30,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,6,0,7,40,40,0,1" % FN,
        "Style: WMK,%s,36,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,6,0,1,3,0,2,40,40,150,1" % FN,
        "Style: WM,%s,20,&H60FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,1,20,20,26,1" % FN,
    ]
    ev = ["Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for sub in spec["subtitles"]:
        text = sub["text"].replace("{Y}", GOLD).replace("{W}", WHITE)
        pos = ("{\\pos(%d,%d)}" % tuple(sub["pos"])) if sub.get("pos") else ""
        ev.append("Dialogue: 0,%s,%s,%s,,0,0,0,,%s%s" % (ass_time(sub["t"][0]), ass_time(sub["t"][1]), sub["style"], pos, text))
    ev.append("Dialogue: 0,%s,%s,WM,,0,0,0,,%s" % (ass_time(0), ass_time(total + 0.2), spec["watermark"]))
    return "\n".join(["[Script Info]", "ScriptType: v4.00+", "PlayResX: 720", "PlayResY: 1280",
                      "WrapStyle: 2", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]"] + styles + ["", "[Events]"] + ev) + "\n"

def font(sz, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, sz)

def c6_frames(spec, media, work, n=18):
    c6 = spec["c6"]; base = os.path.join(media, c6["base_frame"])
    img = Image.open(base).convert("RGB").resize((720, 1280), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(0.12)          # 变灰
    img = ImageEnhance.Brightness(img).enhance(0.72)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, 719, 1279], fill=(30, 30, 30, 70))  # 灰罩
    # 系统级禁止徽标（P2 修项 2026-10-17：平台下架通用视觉=深底圆盘+红环+45°斜杠·替代原手绘全幅大叉）
    bx, by, r = 360, 596, 190
    d.ellipse([bx - r, by - r, bx + r, by + r], fill=(16, 16, 18, 242))
    d.ellipse([bx - r, by - r, bx + r, by + r], outline=(198, 40, 40, 255), width=22)
    s = int((r - 11) * 0.7071)
    d.line([bx - s, by - s, bx + s, by + s], fill=(198, 40, 40, 255), width=22)
    # AIGC 角标（置顶层）
    d.rectangle([14, 14, 14 + 118, 14 + 44], fill=(0, 0, 0, 190))
    d.text((24, 20), c6["badge"], font=font(26), fill=(255, 255, 255))
    # 底部暗带：下架说明 + 评论条 + 进度条
    d.rectangle([0, 900, 719, 1279], fill=(8, 8, 8, 235))
    d.text((360, 930), c6["takedown_text"], font=font(28), fill=(150, 150, 150), anchor="mm")
    # 评论条（高对比首读）：灰头像圆点+灰名条+白粗字
    d.ellipse([70, 1000, 118, 1048], fill=(90, 90, 90))
    d.rectangle([132, 1010, 292, 1022], fill=(90, 90, 90))
    d.text((70, 1085), c6["comment_text"], font=font(46), fill=(255, 255, 255), anchor="lm")
    seq = os.path.join(work, "c6"); os.makedirs(seq, exist_ok=True)
    p0, p1 = c6["progress_from"], c6["progress_to"]
    for i in range(n):
        f = img.copy(); dd = ImageDraw.Draw(f, "RGBA")
        p = p0 + (p1 - p0) * i / (n - 1)
        dd.rectangle([40, 1216, 680, 1230], fill=(70, 70, 70, 255))
        dd.rectangle([40, 1216, int(40 + 640 * p), 1230], fill=(255, 255, 255, 230))
        dd.text((52, 1190), "00:0%d / 0:42" % (7 + (1 if i % 6 == 5 else 0)), font=font(20, False), fill=(160, 160, 160))
        f.save(os.path.join(seq, "c6_%03d.png" % i))
    return seq

def c7_frames(spec, work):
    c7 = spec["c7"]
    img = Image.new("RGB", (720, 1280), (0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((360, 640), c7["text"], font=font(30), fill=(255, 255, 255), anchor="mm")
    seq = os.path.join(work, "c7"); os.makedirs(seq, exist_ok=True)
    for i in range(15):
        img.save(os.path.join(seq, "c7_%03d.png" % i))
    return seq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--media", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ff = shutil.which("ffmpeg") or sys.exit("ffmpeg 不在 PATH")
    spec = json.load(open(os.path.join(a.repo, "cph4", "fleet", "meme-daily-v1", "topics", "v1-shots-v33.json"), encoding="utf-8"))
    W, H = spec["resolution"]; FPS = spec["fps"]; TOTAL = spec["duration"]
    media, out = os.path.abspath(a.media), os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    work = tempfile.mkdtemp(prefix="v133_")
    try:
        norm = []
        # 1) 片段规整
        for s in spec["shots"]:
            if str(s["src"]).startswith("gen:"):
                continue
            src = os.path.join(media, s["src"]); dst = os.path.join(work, "n_%s.mp4" % s["id"])
            vf = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,setsar=1" % (W, H, W, H, FPS)
            run([ff, "-y", "-i", src, "-ss", str(s["trim"][0]), "-t", "%.3f" % (s["trim"][1] - s["trim"][0]),
                 "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", dst])
            norm.append(dst); print("  shot %s ok" % s["id"], flush=True)
        # 2) C6/C7 合成段
        c6s = c6_frames(spec, media, work)
        c6v = os.path.join(work, "n_C6.mp4")
        run([ff, "-y", "-framerate", str(spec["c6"]["fps"]), "-i", os.path.join(c6s, "c6_%03d.png"),
             "-t", "1.2", "-vf", "fps=%d,setsar=1" % FPS, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", c6v])
        norm.append(c6v)
        c7s = c7_frames(spec, work)
        c7v = os.path.join(work, "n_C7.mp4")
        run([ff, "-y", "-framerate", "30", "-i", os.path.join(c7s, "c7_%03d.png"),
             "-t", "0.5", "-vf", "fps=%d,setsar=1" % FPS, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", c7v])
        norm.append(c7v)
        # 3) concat（按 spec 顺序：C1..C5 + C6 + C7）
        order = [s["id"] for s in spec["shots"]]
        lst = os.path.join(work, "list.txt")
        with open(lst, "w", encoding="utf-8") as f:
            for sid in order:
                f.write("file '%s'\n" % os.path.join(work, ("n_%s.mp4" % sid)).replace("\\", "/"))
        concat = os.path.join(work, "concat.mp4")
        run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", concat])
        # 4) 字幕烧制（J-M19 粗黑+暗衬底带）
        with open(os.path.join(work, "subs.ass"), "w", encoding="utf-8") as f:
            f.write(build_ass(spec, TOTAL))
        subs = os.path.join(work, "subs.mp4")
        run([ff, "-y", "-i", concat, "-vf", "ass=subs.ass", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", subs], cwd=work)
        # 5) 旁白轨（预压句间静音 → atempo 装窗 → 定点 adelay）
        #    实锚（10-11）：qwen 语速带大停顿（seg3 实音 3.4s+停顿 2.3s）——先 silenceremove 压句间停顿再装窗
        ins, fc = [], []
        for i, seg in enumerate(spec["narration_segments"]):
            src = os.path.join(media, seg["file"])
            tmp = os.path.join(work, "t_seg%d.wav" % i)
            run([ff, "-y", "-i", src, "-af",
                 "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                 "silenceremove=stop_periods=-1:stop_duration=0.15:stop_threshold=-38dB",
                 "-ac", "1", "-ar", "44100", tmp])
            d = dur_of(ff, tmp)
            f = d / seg["max_dur"] if seg["max_dur"] else 1.0
            chain = "[%d:a]" % (i + 1)
            if f > 1.001:
                f = min(f, 1.20)
                chain += "atempo=%.4f," % f
                print("  %s 压静音后 %.2fs / 窗 %.2fs -> atempo %.3f" % (seg["id"], d, seg["max_dur"], f), flush=True)
            elif f < 1.0:
                print("  %s 压静音后 %.2fs / 窗 %.2fs (直接放)" % (seg["id"], d, seg["max_dur"]), flush=True)
            chain += "adelay=%d|%d,apad[s%d]" % (int(seg["at"] * 1000), int(seg["at"] * 1000), i)
            fc.append(chain); ins.append(tmp)
        fc.append("[s0][s1][s2][s3]amix=inputs=4:normalize=0[narr]")
        # 6) BGM 轨（乐句终止式=静点切 J-M10 + 拍5 极轻回归）
        bg = spec["bgm"]; bgp = os.path.join(media, bg["file"])
        rms, sr, win = wav_rms_windows(bgp)
        cp = quietest_in(rms, sr, win, *bg["exit_window"])
        f0 = quietest_in(rms, sr, win, 3.0, 5.5)
        print("  BGM 静点切 @%.2fs（乐句终止式）·回归段 @%.2fs" % (cp, f0), flush=True)
        b = len(ins) + 1                                     # 输入 0=视频·1..4=旁白·b=BGM
        ins.append(bgp)
        fc.append("[%d:a]atrim=0:%.3f,asetpts=PTS-STARTPTS,volume=%ddB,afade=t=in:d=0.4,apad[g1]" % (b, cp, bg["gain_db"]))
        fc.append("[%d:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,volume=%ddB,afade=t=in:d=0.3,afade=t=out:st=%.2f:d=0.3,adelay=%d|%d,apad[g2]"
                  % (b, f0, f0 + bg["return_dur"], bg["return_gain_db"], bg["return_dur"] - 0.3,
                     int(bg["return_at"] * 1000), int(bg["return_at"] * 1000)))
        fc.append("[g1][g2]amix=inputs=2:normalize=0[bgm]")
        fc.append("[narr][bgm]amix=inputs=2:normalize=0,alimiter=limit=0.95,atrim=0:%.2f[a]" % TOTAL)
        final = os.path.join(out, "v1-%s-final.mp4" % spec["slug"])
        cmd = [ff, "-y", "-i", subs]
        for p in ins:
            cmd += ["-i", p]
        cmd += ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", "%.2f" % TOTAL,
                "-movflags", "+faststart", final]
        run(cmd)
        print("DONE %s dur=%.1fs size=%.1fMB" % (final, dur_of(ff, final), os.path.getsize(final) / 1e6), flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    main()
