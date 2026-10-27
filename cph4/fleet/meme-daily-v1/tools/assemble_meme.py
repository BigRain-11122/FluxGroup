#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assemble_meme.py - meme-daily-v1 确定性装配器
用法（机队各机）:
  python tools/assemble_meme.py --topic v1 --media <该片媒体夹> --out <该片交付夹> [--time-scale 1.05] [--ffmpeg <ffmpeg.exe>] [--dry-run]
输入（--media 夹内）: S1.mp4…S5.mp4 / narration.mp3 / bgm.wav（文件名以 topics/vN-shots.json 为准）
输出（--out 夹）: <topic>-<slug>-final.mp4（720x1280 竖屏·大字幕·旁白+BGM 混音·AIGC 水印）
时间缩放: --time-scale = 旁白实测时长/计划时长（>8% 偏离时用，字幕时间轴整体缩放）
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

FONT = "Microsoft YaHei"
YELLOW = "{\\c&H0000D7FF&}"   # FFD700 黄（BGR 序）
WHITE = "{\\c&H00FFFFFF&}"
RED = "{\\c&H0000FF&}"      # FF0000 红（BGR 序·爆词）

def find_ffmpeg(explicit):
    if explicit:
        return explicit
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    sys.exit("ffmpeg 未找到：装 imageio-ffmpeg（python -m pip install imageio-ffmpeg）或用 --ffmpeg 指路径")

def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, cwd=cwd)
    if r.returncode != 0:
        sys.exit("FFMPEG FAIL: " + " ".join(cmd) + "\n" + r.stderr.decode("utf-8", "replace")[-2000:])

def duration_of(ff, path):
    r = subprocess.run([ff, "-i", path], capture_output=True)
    m = re.search(rb"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", r.stderr)
    if not m:
        sys.exit("无法读时长: " + path)
    h, mi, s, cs = (int(x) for x in m.groups())
    return h * 3600 + mi * 60 + s + cs / 100.0

def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)

def build_ass(spec, total, scale):
    big = spec.get("subtitle_style_big", {})
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 720", "PlayResY: 1280",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Big,%s,%d,&H00FFFFFF,&H000000FF,&H00000000,&H78000000,-1,0,0,0,100,100,1,0,1,4,1,2,40,40,%d,1" % (FONT, big.get("fontsize", 62), big.get("marginv", 300)),
        "Style: Quote,%s,52,&H0000D7FF&,&H000000FF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,3,0,0,5,40,40,0,1" % FONT,
        "Style: Small,%s,32,&H00FFFFFF,&H000000FF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,3,0,2,40,40,0,1" % FONT,
        "Style: WM,%s,20,&H00E8E8E8,&H000000FF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,3,2,0,1,22,22,26,1" % FONT,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for idx, sub in enumerate(spec["subtitles"]):
        t1 = sub["t"][0] * scale; t2 = sub["t"][1] * scale
        text = sub["text"].replace("{Y}", YELLOW).replace("{W}", WHITE).replace("{R}", RED).replace("\\N", "\\N")
        # 反AI感字幕微倾斜：奇数卡 -1.2°（去模板完美感）
        if idx % 2 == 1:
            text = "{\\frz-1.2}" + text
        lines.append("Dialogue: 0,%s,%s,%s,,0,0,0,,%s" % (ass_time(t1), ass_time(t2), sub.get("style", "Big"), text))
    lines.append("Dialogue: 0,%s,%s,WM,,0,0,0,,%s" % (ass_time(0), ass_time(total + 0.2), spec.get("watermark", "AI 生成｜本片为AI创作演绎")))
    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    ap.add_argument("--topic", required=True, choices=["v1", "v2", "v3"])
    ap.add_argument("--media", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--time-scale", type=float, default=1.0)
    ap.add_argument("--ffmpeg", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    spec_path = os.path.join(a.repo, "topics", "%s-shots.json" % a.topic)
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    W, H = spec["resolution"]; FPS = spec["fps"]
    media = os.path.abspath(a.media); out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    ff = find_ffmpeg(a.ffmpeg)

    # 计划总长
    total = sum(s["trim"][1] - s["trim"][0] for s in spec["shots"])
    print("PLAN %s total=%.1fs shots=%d subs=%d scale=%.3f" % (a.topic, total, len(spec["shots"]), len(spec["subtitles"]), a.time_scale))
    if a.dry_run:
        return

    work = tempfile.mkdtemp(prefix="meme_%s_" % a.topic)
    try:
        # 1) 逐镜规整：裁剪+竖屏填充+fps+去音轨
        norm = []
        for s in spec["shots"]:
            src = os.path.join(media, s["file"])
            if not os.path.isfile(src):
                sys.exit("缺镜头文件: " + src)
            dst = os.path.join(work, "n_%s.mp4" % s["id"])
            vf = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,setsar=1" % (W, H, W, H, FPS)
            ft = s.get("freeze_tail")
            if ft:
                vf += ",tpad=stop_mode=clone:stop_duration=%.2f" % ft
            run([ff, "-y", "-i", src, "-ss", str(s["trim"][0]), "-t", str(s["trim"][1] - s["trim"][0]),
                 "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", dst])
            norm.append(dst)
            dur_s = s["trim"][1] - s["trim"][0] + (ft or 0)
            print("  shot %s ok (%.1fs)" % (s["id"], dur_s))

        # 2) concat（同参编码直连）
        lst = os.path.join(work, "list.txt")
        with open(lst, "w", encoding="utf-8") as f:
            for p in norm:
                f.write("file '%s'\n" % p.replace("\\", "/").replace("'", "'\\''"))
        concat = os.path.join(work, "concat.mp4")
        run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", concat])

        # 3) 字幕+AIGC 水印（cwd=work 用相对路径规避 ass 滤镜路径转义）
        with open(os.path.join(work, "subs.ass"), "w", encoding="utf-8") as f:
            f.write(build_ass(spec, total, a.time_scale))
        subs = os.path.join(work, "subs.mp4")
        # finishing 站：字幕层之上统一暖饱和+黑位轻抬+暗角+轻颗粒（承 30s-reel v4.3 调色席：五镜熔成一张拷贝·最便宜去AI手段·颗粒置最后不被调色扭曲）
        fin = "ass=subs.ass,eq=saturation=1.06:gamma=1.02,colorbalance=rs=0.03:bs=-0.03,vignette=PI/5.5,noise=alls=4:allf=t"
        run([ff, "-y", "-i", concat, "-vf", fin, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", subs], cwd=work)

        # 4) 混音：旁白（支持 narration_segments 分段定点=抑扬顿挫剪控）+ BGM 低增益淡入出+duck + sfx 定点，钳到片长
        bgm = os.path.join(media, spec.get("bgm_file", "bgm.wav"))
        if not os.path.isfile(bgm):
            sys.exit("缺音频文件: " + bgm)
        segs = spec.get("narration_segments")
        if segs:
            inputs = ["-i", subs]
            narr_tracks = []
            for i, sg in enumerate(segs):
                p = os.path.join(media, sg["file"])
                if not os.path.isfile(p):
                    sys.exit("缺旁白分段: " + p)
                inputs += ["-i", p]
                narr_tracks.append(sg)
        else:
            narr = os.path.join(media, spec.get("narration_file", "narration.mp3"))
            if not os.path.isfile(narr):
                sys.exit("缺音频文件: " + narr)
            inputs = ["-i", subs, "-i", narr]
            narr_tracks = None
        inputs += ["-i", bgm]
        sfxs = spec.get("sfx", [])
        for s in sfxs:
            p = os.path.join(media, s["file"])
            if not os.path.isfile(p):
                print("  WARN 缺音效件(跳过): " + s["file"])
                continue
            inputs += ["-i", p]
        dur = duration_of(ff, subs)
        g = spec.get("bgm_gain_db", -13)
        fade_out_start = max(0.0, dur - 0.9)
        duck = spec.get("bgm_duck")
        bgm_chain = "volume=%ddB,afade=t=in:d=0.4,afade=t=out:st=%.2f:d=0.9" % (g, fade_out_start)
        if duck and duck[1] > duck[0]:
            d0, d1 = duck
            bgm_chain += ",volume=0:enable='between(t,%.2f,%.2f)'" % (d0, d1)
        mix_labels = []
        fc = ""
        if narr_tracks:
            for i, sg in enumerate(narr_tracks):
                ms = int(sg.get("t", 0) * 1000)
                fc += "[%d:a]adelay=%d|%d,apad[ns%d];" % (1 + i, ms, ms, i)
                mix_labels.append("[ns%d]" % i)
        else:
            fc += "[1:a]adelay=150|150,apad[na];"
            mix_labels.append("[na]")
        bidx = 1 + (len(narr_tracks) if narr_tracks else 1)
        fc += "[%d:a]%s,apad[ba];" % (bidx, bgm_chain)
        mix_labels.append("[ba]")
        sfx_i = 0
        for s in sfxs:
            p = os.path.join(media, s["file"])
            if not os.path.isfile(p):
                continue
            src = bidx + 1 + sfx_i
            ms = int(s["t"][0] * 1000)
            gain = s.get("gain_db", 0)
            fc += "[%d:a]volume=%sdB,adelay=%d|%d,apad[s%d];" % (src, gain, ms, ms, sfx_i)
            mix_labels.append("[s%d]" % sfx_i)
            sfx_i += 1
        fc += "%samix=inputs=%d:duration=longest:dropout_transition=0,alimiter=limit=0.95[a]" % (
            "".join(mix_labels), len(mix_labels))
        final = os.path.join(out, "%s-%s-final.mp4" % (spec["topic"], spec["slug"]))
        run([ff, "-y"] + inputs + ["-filter_complex", fc,
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
             "-t", "%.2f" % dur, "-movflags", "+faststart", final])
        sz = os.path.getsize(final) / 1e6
        print("DONE %s  dur=%.1fs  size=%.1fMB" % (final, dur, sz))
        if sz > 50:
            print("WARN 单件 >50MB：建议 -crf 23 重出（>95MB 禁入 git）")
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    main()
