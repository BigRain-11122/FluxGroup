# -*- coding: utf-8 -*-
# build_full_mv_v2.py — 08:30 死线装配器（O-20261012-2305·CEO 明朝成片令）
# 输入: DL 段目录（bm-c CDN 段收片）+ fleet-shots/FLUXGROUP（11 REUSE 源 mp4）
# 表: mv_full_shots v1.1 + v2 补丁（INT 线换新帧/C01 换新段/D03 拆 D03b/E01b 拆 E01c）
# 变速律: v<0.96 一律 minterpolate 插值（O-20261011 整改令）·缺源兜底=前镜微伸
# finishing=v4.4 克制档 + S9 金字层 + T 桥 xfade×2 + Z04 定格收 + BGM 全窗（承 v1 正典）
import os, subprocess, sys

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
sys.path.insert(0, HERE)
from mv_full_shots import (NEW, REUSE, TXT_IN_ST, TXT_IN_D, TXT_OUT_ST, TXT_OUT_D,
                           S6_SEGS, XF_T1, XF_T2, FILM_END)

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
DL = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments"
CLOUD = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\cloudv2"
D_OLD = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\cloud-v4"  # O-20261014-1045 shou-bian: tmp-sweep-zone -> media safe zone
FLUX = os.path.join(HERE, "fleet-shots", "FLUXGROUP")
D_CUT = os.path.join(DL, "_cut")
OUT_DIR = HERE
SONG = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\audio\mv001_source_320k.mp3"
S9_TEXT = os.path.join(OUT_DIR, "s9_lyric.png")
XF = 0.4
FAST = os.environ.get("NO_MINTERP") == "1"   # 时间不够时置 1 跳过插值（匀速顿挫风险回归）
os.makedirs(D_CUT, exist_ok=True)
os.makedirs(DL, exist_ok=True)

# ---- v2 补丁表（新 INT 线/C01/D03b/E01c——id, t0, t1, speed, src_mp4, is_new） ----
DROP_NEW = {"INT1_hall_breath", "INT2_row_wake", "INT3_her_walk", "INT4_first_reflection",
            "INT5_approach", "C01_carver_face", "D03_two_worlds"}
E01B_NEW_END = 191.60

def build_rows():
    rows = []
    for sid, t0, t1, v, k, iv in NEW:
        if sid in DROP_NEW:
            continue
        if sid == "E03_gaze_meet" or True:
            rows.append([sid, t0, t1, v, sid + ".mp4", True])
    # v2 INT 线（同窗换新）
    rows.append(["INT1_desk_breath",   0.00,  3.50, 0.85, "INT1_desk_breath.mp4",   True])
    rows.append(["INT2_paper_fight",   3.50,  7.50, 0.92, "INT2_paper_fight.mp4",   True])
    rows.append(["INT3_photo_stare",   7.50, 11.50, 0.90, "INT3_photo_stare.mp4",   True])
    rows.append(["INT4_rubbing_glow", 11.50, 14.60, 0.95, "INT4_rubbing_glow.mp4",  True])
    rows.append(["INT5_head_bow",     14.60, 17.50, 0.88, "INT5_head_bow.mp4",      True])
    rows.append(["C01_carver_face",   77.34, 80.18, 0.90, "C01_carver_face.mp4",    True])
    # D03 拆：本体缩窗 + D03b 直视锚
    rows.append(["D03_two_worlds", 147.84, 150.54, 0.85, "D03_two_worlds.mp4", True])
    rows.append(["D03b_direct_gaze", 150.54, 152.14, 0.90, "D03b_direct_gaze.mp4", True])
    # E01b 拆：本体缩窗 + E01c 落笔
    for sid, t0, t1, v, src in REUSE:
        if sid == "E01b_sand":
            rows.append([sid, t0, E01B_NEW_END, v, src + ".mp4", False])
            rows.append(["E01c_first_line", E01B_NEW_END, t1, 0.90, "E01c_first_line.mp4", True])
        else:
            rows.append([sid, t0, t1, v, src + ".mp4", False])
    rows.sort(key=lambda r: r[1])
    return rows

def find_src(fname):
    # 搜索序：cloudv2（云端定版·回炉律换优优先）→ DL（bm-c CDN 段）→ D_OLD（REUSE 11 源 KF 系）→ FLUX
    for d in (CLOUD, DL, D_OLD, FLUX):
        p = os.path.join(d, fname)
        if os.path.isfile(p):
            return p
    return None

def retime(src, dst, ss, film_dur, v):
    base = ("scale=1344:768:force_original_aspect_ratio=decrease,"
            "pad=1344:768:(ow-iw)/2:(oh-ih)/2,fps=24")
    if v < 0.96 and not FAST:
        vf = "minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f,%s" % (v, base)
    else:
        vf = "setpts=PTS/%.4f,%s" % (v, base)
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
    rows = build_rows()
    # 缺源兜底：合并进前镜（前镜 t1 延伸覆盖）——死线铁律：全片 234.25s 无缝
    resolved = []
    merged_note = []
    for r in rows:
        src = find_src(r[4])
        if src is None:
            if resolved:
                prev = resolved[-1]
                prev[2] = r[2]
                merged_note.append("%s -> merged into %s" % (r[0], prev[0]))
                continue
            else:
                raise SystemExit("FATAL: first shot missing: " + r[0])
        resolved.append([r[0], r[1], r[2], r[3], src, r[5]])
    for m in merged_note:
        print("FALLBACK-MERGE " + m, flush=True)

    cuts = {}
    for sid, t0, t1, v, src, is_new in resolved:
        dur = round(t1 - t0, 4)
        dst = os.path.join(D_CUT, "cut_" + sid + ".mp4")
        if sid == "S6_chisel":
            pieces = []
            for i, (ss, fd, sv) in enumerate(S6_SEGS):
                p = os.path.join(D_CUT, "cut_s6_%d.mp4" % i)
                retime(src, p, ss, fd, sv)
                pieces.append(p)
            concat(pieces, dst)
        elif sid == "Z04_glyph_remains":
            walk = dur - 0.50
            tmp = os.path.join(D_CUT, "z04_walk.mp4")
            retime(src, tmp, 0.0, dur, v)
            subprocess.run([FF, "-y", "-i", tmp, "-vf",
                            "trim=duration=%.4f,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.50" % walk,
                            "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", dst],
                           check=True, capture_output=True)
        else:
            retime(src, dst, 0.0, dur, v)
        print("cut %s %.2fs@%.2fx" % (sid, dur, v), flush=True)
        cuts[sid] = dst

    A_ids = [r[0] for r in resolved if r[1] < 38.82]
    T_id = "T_glyphs"
    B_ids = [r[0] for r in resolved if r[1] >= 40.22]
    A = os.path.join(D_CUT, "blockA.mp4")
    B = os.path.join(D_CUT, "blockB.mp4")
    concat([cuts[i] for i in A_ids], A)
    concat([cuts[i] for i in B_ids], B)
    T = cuts[T_id]
    print("blocks built", flush=True)

    lenA = sum(round(r[2] - r[1], 4) for r in resolved if r[1] < 38.82)
    lenB = sum(round(r[2] - r[1], 4) for r in resolved if r[1] >= 40.22)
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
    out = os.path.join(OUT_DIR, "full_mv_v2_20261013.mp4")
    a_fade_st = final_len - 2.75
    cmd = [FF, "-y",
           "-i", A, "-i", T, "-i", B,
           "-i", SONG, "-i", S9_TEXT,
           "-filter_complex", fc,
           "-map", "[v]", "-map", "3:a",
           "-af", "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5" % a_fade_st,
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    subprocess.run(cmd, check=True)
    print("DONE " + out, flush=True)
    print("LEN=%.2f" % final_len, flush=True)

if __name__ == "__main__":
    main()
