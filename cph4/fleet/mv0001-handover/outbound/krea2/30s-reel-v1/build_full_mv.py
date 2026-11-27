# -*- coding: utf-8 -*-
# build_full_mv.py - 爱在西元前 全曲成品装配（CEO令 10-10 20:5x）
# 输入: mv_full_shots.py 全曲表(64镜=44新+20复用·whisper 词级卡点) + cloud-v4/(旧11源) + cloud-v4-full/(新44源)
# 结构: 硬切为主 + T桥金字=全片唯一叠化(xfade×2·承30s正典) + S9金字层(词起字起词尽字散)
# 变速律(v4.5): 逐镜速度 + S6段内burst + Z04定格收(trim→tpad 正法·勿用-t截tpad)
# finishing(v4.4克制档): 罩染减半/黑位0.010/饱和.97/暗角PI5/颗粒alls6
# BGM=原曲全窗0-234.25(画面+歌律·零AI音轨)·首尾fade
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mv_full_shots import (NEW, REUSE, TXT_IN_ST, TXT_IN_D, TXT_OUT_ST, TXT_OUT_D,
                           S6_SEGS, XF_T1, XF_T2, FILM_END)

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
D_OLD = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\cloud-v4"
D_NEW = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\cloud-v4-full"
D_CUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\full-cut"
OUT_DIR = HERE
SONG = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\audio\mv001_source_320k.mp3"
S9_TEXT = os.path.join(OUT_DIR, "s9_lyric.png")
XF = 0.4
os.makedirs(D_CUT, exist_ok=True)


def src_of(sid):
    for d in (D_NEW, D_OLD):
        p = os.path.join(d, sid + ".mp4")
        if os.path.isfile(p):
            return p
    raise SystemExit("MISSING SOURCE " + sid)


def retime(src, dst, ss, film_dur, v, extra=""):
    vf = ("setpts=PTS/%.4f,scale=1344:768:force_original_aspect_ratio=decrease,"
          "pad=1344:768:(ow-iw)/2:(oh-ih)/2,fps=24%s" % (v, extra))
    cmd = [FF, "-y", "-ss", "%.4f" % ss, "-i", src, "-t", "%.4f" % film_dur, "-an",
           "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "17",
           "-pix_fmt", "yuv420p", dst]
    subprocess.run(cmd, check=True, capture_output=True)


def concat(files, out):
    lst = os.path.join(D_CUT, "list_" + os.path.basename(out) + ".txt")
    with open(lst, "w") as f:
        for x in files:
            f.write("file '" + x.replace("'", "'\"'\"'") + "'\n")
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                   check=True, capture_output=True)


def main():
    rows = [(r[0], r[1], r[2], r[3], r[4], True) for r in NEW]      # new: 5元组
    rows += [(r[0], r[1], r[2], r[3], r[4], False) for r in REUSE]  # reuse: src名在第5位
    rows.sort(key=lambda r: r[1])

    cuts = {}
    for sid, t0, t1, v, fifth, is_new in rows:
        dur = round(t1 - t0, 4)
        src = src_of(fifth if is_new is False else sid)
        dst = os.path.join(D_CUT, "cut_" + sid + ".mp4")
        if sid == "S6_chisel":
            pieces = []
            for i, (ss, fd, sv) in enumerate(S6_SEGS):
                p = os.path.join(D_CUT, "cut_s6_%d.mp4" % i)
                retime(src, p, ss, fd, sv)
                pieces.append(p)
            concat(pieces, dst)
            print("cut %s burst" % sid, flush=True)
        elif sid == "Z04_glyph_remains":
            # 定格收: 链内 trim 截走段 → tpad 接定格(输出-t帽会连坐截定格·判例在案)
            walk = dur - 0.50
            retime(src, dst, 0.0, dur, v,
                   extra=",trim=duration=%.4f,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.50" % walk)
            print("cut %s walk+freeze" % sid, flush=True)
        else:
            retime(src, dst, 0.0, dur, v)
            print("cut %s %.2fs@%.2fx" % (sid, dur, v), flush=True)
        cuts[sid] = dst

    # 分块: A=INT+S1..S7 | T | B=其余
    A_ids = [r[0] for r in rows if r[1] < 38.82]
    T_id = "T_glyphs"
    B_ids = [r[0] for r in rows if r[1] >= 40.22]
    # S7 肩膀(36.92-38.82)已在 A 内; T(38.82-40.22)独立; B 从 S8(40.22)起
    A = os.path.join(D_CUT, "blockA.mp4")
    B = os.path.join(D_CUT, "blockB.mp4")
    concat([cuts[i] for i in A_ids], A)
    concat([cuts[i] for i in B_ids], B)
    T = cuts[T_id]
    print("blocks built", flush=True)

    lenA = sum(round(r[2] - r[1], 4) for r in rows if r[1] < 38.82)
    lenB = sum(round(r[2] - r[1], 4) for r in rows if r[1] >= 40.22)
    lenAT = lenA + 2.20 - XF
    final_len = lenAT + lenB - XF
    print("lenA=%.2f lenAT=%.2f lenB=%.2f film=%.2f (target %.2f)" % (lenA, lenAT, lenB, final_len, FILM_END), flush=True)
    off1, off2 = XF_T1, XF_T2

    fin = ("colorbalance=rs=.03:gs=.005:bs=-.03:rm=.02:gm=.005:bm=-.02:rh=.04:gh=.01:bh=-.05,"
           "curves=all='0/0.010 0.5/0.50 1/0.99',"
           "eq=saturation=.97,"
           "vignette=PI/5,"
           "noise=alls=6:allf=t+u,format=yuv420p")
    fade_out_st = final_len - 2.25
    fc = (
        "[0:v][1:v]xfade=transition=fade:duration=%f:offset=%.2f[at];"
        "[at][2:v]xfade=transition=fade:duration=%f:offset=%.2f[ab];"
        "[ab]fade=t=in:st=0:d=1.2,fade=t=out:st=%.2f:d=2.0[base];"
        "[4:v]format=rgba,fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tex];"
        "[base][tex]overlay=0:0:enable='between(t,%.2f,%.2f)'[ov];"
        "[ov]%s[v]"
        % (XF, off1, XF, off2, fade_out_st,
           TXT_IN_ST, TXT_IN_D, TXT_OUT_ST, TXT_OUT_D,
           TXT_IN_ST, TXT_OUT_ST + TXT_OUT_D, fin)
    )
    out = os.path.join(OUT_DIR, "full_mv_v1.mp4")
    a_fade_st = final_len - 2.75
    cmd = [FF, "-y",
           "-i", A, "-i", T, "-i", B,
           "-t", "%.2f" % final_len, "-i", SONG,
           "-loop", "1", "-framerate", "24", "-i", S9_TEXT,
           "-filter_complex",
           fc + ";[3:a]afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=%.2f[a]"
           % (a_fade_st, final_len - a_fade_st),
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        sys.stderr.write((e.stderr or b"").decode("utf-8", "replace")[-4000:])
        sys.exit(1)
    print("FINAL", out, flush=True)


if __name__ == "__main__":
    main()
