# -*- coding: utf-8 -*-
# build_full_mv_v3.py — V3 挂点装配器（O-20261014 导演席装配站）
# 法：V3 七新镜「邻窗切分插入」——挂点处切邻槽窗插新镜（溢出顺延吃下一槽头）
#     总长守恒 234.25s·词级卡点零漂移·A/B 块净时长不变→T 桥 xfade 偏移零改
# 源：v2 正典 import 复用（find_src/concat/paths/锚点常量/finishing 链）
# 模式：PROXY=1 → 预览代理档（960x540·crf22·veryfast·结构/节奏验证·O-20261014-1325 低清验证律）
#       默认 → 终版（1344x768·crf17/18·fast·全 finishing）
# SIL4：探针结论前 NO_SIL4=1 缺省不插（窗自动还原零缝）
import os, subprocess, sys

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
sys.path.insert(0, HERE)
import build_full_mv_v2 as v2

PROXY = os.environ.get("PROXY") == "1"
NO_SIL4 = os.environ.get("NO_SIL4") == "1"

# ---- V3 插入表（挂点/窗长正身=V3-NEWKF-PACK §装配挂点 + 导演席窗长裁定）----
V3_INSERTS = [
    # (insert_id, src_filename, t_anchor, dur, speed)
    ("SIL1_v4b", "SIL1_stele_backlit_v4b_s9021.mp4",      29.0, 1.8, 1.0),
    ("SIL2_v4",  "SIL2_ots_crowd_v4_s9018.mp4",           44.0, 1.8, 1.0),
    ("SING1_v2", "SING1_torch_song_v2_s9013.mp4",         78.0, 2.5, 1.0),
    ("SIL3_v2",  "SIL3_case_rim_v2_s9013.mp4",           152.0, 1.6, 1.0),
    ("SING2",    "SING2_firepit_song_s9014.mp4",          180.0, 2.0, 1.0),
    ("SING3b_v4","SING3_morning_song_open_v4_s9019.mp4",  197.0, 2.0, 1.0),
]
if not NO_SIL4:
    V3_INSERTS.append(("SIL4", "SIL4_crowd_edge_s9013.mp4", 207.0, 1.8, 1.0))

def build_rows_v3():
    """v2 行全局切分插入：原槽窗被插入区间啃洞（溢出跨槽照啃）·插入行独立发射
    返回 (sid, t0, t1, speed, src_file, is_new) 绝对窗序列·后窗零漂移"""
    rows = sorted(v2.build_rows(), key=lambda r: r[1])
    ins = sorted(V3_INSERTS, key=lambda x: x[2])
    out = []
    for r in rows:
        segs = [(r[1], r[2])]
        for iid, fn, a, d, v in ins:
            if a >= r[2] or a + d <= r[1]:
                continue
            newsegs = []
            for s, e in segs:
                if a + d <= s or a >= e:
                    newsegs.append((s, e)); continue
                if s < a: newsegs.append((s, a))
                if a + d < e: newsegs.append((a + d, e))
            segs = newsegs
        for i, (s, e) in enumerate(sorted(segs)):
            if e - s > 0.01:
                sid = r[0] if len(segs) == 1 else "%s_p%d" % (r[0], i)
                out.append([sid, s, e, r[3], r[4], r[5]])
    for iid, fn, a, d, v in ins:
        out.append(["%s@%d" % (iid, int(a)), a, a + d, v, fn, True])
    out.sort(key=lambda r: r[1])
    return out

def retime3(src, dst, ss, film_dur, v, W, H, CRF, PRE):
    base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24"
            % (W, H, W, H))
    vf = base if (v >= 0.96 or v2.FAST) else ("minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f,%s" % (v, base))
    subprocess.run([v2.FF, "-y", "-ss", "%.4f" % ss, "-i", src, "-t", "%.4f" % film_dur, "-an",
                    "-vf", vf, "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                    "-pix_fmt", "yuv420p", dst], check=True, capture_output=True)

def main():
    rows = build_rows_v3()
    resolved, merged = [], []
    for r in rows:
        src = v2.find_src(r[4])
        if src is None:
            if r[5]:   # 插入镜缺源=跳过（窗自动还原）·终版前必到货
                print("SKIP-INSERT %s (src missing)" % r[0], flush=True)
                continue
            if resolved:
                prev = resolved[-1]; prev[2] = r[2]
                merged.append("%s->%s" % (r[0], prev[0])); continue
            raise SystemExit("FATAL first shot missing " + r[0])
        resolved.append([r[0], r[1], r[2], r[3], src, r[5]])
    for m in merged: print("FALLBACK-MERGE " + m, flush=True)
    total = sum(r[2] - r[1] for r in resolved)
    print("V3 SEGMENTS %d total=%.2f target=%.2f" % (len(resolved), total, v2.FILM_END), flush=True)

    if PROXY: W, H, CRF, PRE = 960, 540, 22, "veryfast"
    else:     W, H, CRF, PRE = 1344, 768, 17, "fast"

    cuts = {}
    for sid, t0, t1, v, src, is_new in resolved:
        dur = round(t1 - t0, 4)
        dst = os.path.join(v2.D_CUT, "v3cut_%s.mp4" % sid.replace("@", "_at_"))
        if sid == "S6_chisel":
            pieces = []
            for i, (ss, fd, sv) in enumerate(v2.S6_SEGS):
                p = os.path.join(v2.D_CUT, "v3_s6_%d.mp4" % i)
                retime3(src, p, ss, fd, sv, W, H, CRF, PRE); pieces.append(p)
            v2.concat(pieces, dst)
        elif sid == "Z04_glyph_remains":
            walk = dur - 0.50
            tmp = os.path.join(v2.D_CUT, "v3_z04.mp4")
            retime3(src, tmp, 0.0, dur, v, W, H, CRF, PRE)
            subprocess.run([v2.FF, "-y", "-i", tmp, "-vf",
                "trim=duration=%.4f,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.50" % walk,
                "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF), "-pix_fmt", "yuv420p", dst],
                check=True, capture_output=True)
        else:
            retime3(src, dst, 0.0, dur, v, W, H, CRF, PRE)
        print("cut %s %.2fs@%.2fx" % (sid, dur, v), flush=True)
        cuts[sid] = (dst, t0, t1, v)

    A_ids = sorted([c for c in cuts if cuts[c][1] < 38.82], key=lambda c: cuts[c][1])
    T_id = "T_glyphs"
    B_ids = sorted([c for c in cuts if cuts[c][1] >= 40.22 and c != T_id], key=lambda c: cuts[c][1])
    A = os.path.join(v2.D_CUT, "v3_blockA.mp4")
    B = os.path.join(v2.D_CUT, "v3_blockB.mp4")
    v2.concat([cuts[c][0] for c in A_ids], A)
    v2.concat([cuts[c][0] for c in B_ids], B)
    print("blocks built A=%d B=%d" % (len(A_ids), len(B_ids)), flush=True)

    lenA = sum(cuts[c][2] - cuts[c][1] for c in A_ids)
    lenB = sum(cuts[c][2] - cuts[c][1] for c in B_ids)
    lenAT = lenA + 2.20 - v2.XF
    final_len = lenAT + lenB - v2.XF
    print("lenA=%.2f lenAT=%.2f lenB=%.2f film=%.2f (target %.2f)" % (
        lenA, lenAT, lenB, final_len, v2.FILM_END), flush=True)

    fin = ("colorbalance=rs=.03:gs=.005:bs=-.03:rm=.02:gm=.005:bm=-.02:rh=.04:gh=.01:bh=-.05,"
           "curves=all='0/0.010 0.5/0.50 1/0.99',eq=saturation=.97,vignette=PI/5,"
           "noise=alls=6:allf=t+u,format=yuv420p")
    fade_out_st = final_len - 2.25
    fc = ("[0:v][1:v]xfade=transition=fade:duration=%f:offset=%.2f[at];"
          "[at][2:v]xfade=transition=fade:duration=%f:offset=%.2f[ab];"
          "[ab]fade=t=in:st=0:d=1.2,fade=t=out:st=%.2f:d=2.0[base];"
          "[4:v]format=rgba,fade=t=in:st=%.2f:d=%.2f:alpha=1,fade=t=out:st=%.2f:d=%.2f:alpha=1[tex];"
          "[base][tex]overlay=0:0:enable='between(t,%.2f,%.2f)'[ov];"
          "[ov]%s[v]"
          % (v2.XF, v2.XF_T1, v2.XF, v2.XF_T2, fade_out_st,
             v2.TXT_IN_ST, v2.TXT_IN_D, v2.TXT_OUT_ST, v2.TXT_OUT_D,
             v2.TXT_IN_ST, v2.TXT_OUT_ST + v2.TXT_OUT_D, fin))
    out = os.path.join(HERE, "full_mv_v3_preview.mp4" if PROXY else "full_mv_v3_final.mp4")
    a_fade_st = final_len - 2.75
    subprocess.run([v2.FF, "-y",
        "-i", A, "-i", cuts[T_id][0], "-i", B, "-i", v2.SONG, "-i", v2.S9_TEXT,
        "-filter_complex", fc, "-map", "[v]", "-map", "3:a",
        "-af", "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5" % a_fade_st,
        "-c:v", "libx264", "-preset", PRE, "-crf", "22" if PROXY else "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", out],
        check=True)
    print("DONE %s" % out, flush=True)
    print("LEN=%.2f" % final_len, flush=True)

if __name__ == "__main__":
    main()
