# -*- coding: utf-8 -*-
# fix_v3_final.py — V3 终剪 A 块丢失事故修复（O-20261015-1040 窗口内修复件）
# 病根：T_glyphs 切 1.40s 而叠化数学按 2.20s 设计 → xfade2 偏移越 [at] 尾 → A 块(0-38.8s)被吞
#       + E04/R06/N05 三镜源料不足窗需（-3.23s）
# 修法：T 重切 2.20s + 三镜定格尾补 + B 块重 concat + 终装重跑 → 全片 234.25s 守恒
import os, re, subprocess, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
sys.path.insert(0, HERE)
import build_full_mv_v2 as v2

W, H, CRF, PRE = 1344, 768, 17, "fast"
FF = v2.FF

def dur_of(p):
    r = subprocess.run([FF, "-i", p], capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return float(m.group(1)) * 3600 + float(m.group(2)) * 60 + float(m.group(3)) if m else None

def retime_pad(src, dst, want, v):
    """按表速度慢放，不足定格补到 want 秒（tpad clone 尾帧）"""
    base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24"
            % (W, H, W, H))
    L = dur_of(src)
    avail = L / v
    pad = max(0.0, round(want - avail, 3))
    vf = "minterpolate=fps=48:mi_mode=mci,setpts=PTS/%.4f,%s,tpad=stop_mode=clone:stop_duration=%.3f" % (v, base, pad)
    subprocess.run([FF, "-y", "-i", src, "-an", "-vf", vf, "-t", "%.4f" % want,
                    "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
                    "-pix_fmt", "yuv420p", dst], check=True, capture_output=True)
    a = dur_of(dst)
    print("  %s src=%.2f avail=%.2f pad=%.2f -> actual=%.2f (want %.2f)" % (
        os.path.basename(dst), L, avail, pad, a, want))
    assert a is not None and a >= want - 0.05, "segment still short: " + dst

# ---- 1) T 桥重切 2.20s（叠化数学正身）----
print("T bridge re-cut:")
t_src = v2.find_src("KFT_glyphs.mp4")
assert t_src, "KFT_glyphs source missing"
t_dst = os.path.join(v2.D_CUT, "v3cut_T_glyphs.mp4")
v3_retime = None
# 2.20 film @0.90 → 源需 ≥1.98s；-t 2.20 截足
base = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H))
subprocess.run([FF, "-y", "-i", t_src, "-an",
               "-vf", "minterpolate=fps=48:mi_mode=mci,setpts=PTS/0.9000,%s" % base,
               "-t", "2.2000", "-c:v", "libx264", "-preset", PRE, "-crf", str(CRF),
               "-pix_fmt", "yuv420p", t_dst], check=True, capture_output=True)
print("  T src=%.2f -> cut=%.2f (need 2.20)" % (dur_of(t_src), dur_of(t_dst)))
assert dur_of(t_dst) >= 2.18, "T cut still short"

# ---- 2) 三缺料镜定格尾补 ----
print("short-segment pads:")
for sid, want, v in (("E04_replay_faces", 7.18, 0.87),
                     ("R06_museum_verse", 6.84, 0.92),
                     ("N05_dead_language", 6.88, 0.85)):
    src = v2.find_src(sid + ".mp4")
    assert src, sid + " source missing"
    retime_pad(src, os.path.join(v2.D_CUT, "v3cut_%s.mp4" % sid), want, v)

# ---- 3) A/B 块重 concat（切件已替换·序=装配器同序）----
import build_full_mv_v3 as v3m
rows = v3m.build_rows_v3()
resolved = []
for r in rows:
    src = v2.find_src(r[4])
    if src is None:
        if r[5]:
            continue
        raise SystemExit("FATAL missing " + r[0])
    resolved.append([r[0], r[1], r[2], r[3], src, r[5]])
cuts = {}
for sid, t0, t1, v, src, is_new in resolved:
    cuts[sid] = (os.path.join(v2.D_CUT, "v3cut_%s.mp4" % sid.replace("@", "_at_")), t0, t1, v)
A_ids = sorted([c for c in cuts if cuts[c][1] < 38.82], key=lambda c: cuts[c][1])
T_id = "T_glyphs"
B_ids = sorted([c for c in cuts if cuts[c][1] >= 40.22 and c != T_id], key=lambda c: cuts[c][1])
A = os.path.join(v2.D_CUT, "v3_blockA.mp4")
B = os.path.join(v2.D_CUT, "v3_blockB.mp4")
v2.concat([cuts[c][0] for c in A_ids], A)
v2.concat([cuts[c][0] for c in B_ids], B)
print("blocks: A=%.2f T=%.2f B=%.2f" % (dur_of(A), dur_of(t_dst), dur_of(B)))

# ---- 4) 终装重跑（fc 与原装一致·final_len=234.25）----
final_len = 234.25
lenA = sum(cuts[c][2] - cuts[c][1] for c in A_ids)
lenB = sum(cuts[c][2] - cuts[c][1] for c in B_ids)
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
out = os.path.join(HERE, "full_mv_v3_final.mp4")
a_fade_st = final_len - 2.75
subprocess.run([FF, "-y",
    "-i", A, "-i", cuts[T_id][0], "-i", B, "-i", v2.SONG, "-i", v2.S9_TEXT,
    "-filter_complex", fc, "-map", "[v]", "-map", "3:a",
    "-af", "afade=t=in:st=0:d=0.8,afade=t=out:st=%.2f:d=2.5" % a_fade_st,
    "-c:v", "libx264", "-preset", PRE, "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
print("DONE %s" % out)
print("FINAL-LEN %.2f" % dur_of(out))
