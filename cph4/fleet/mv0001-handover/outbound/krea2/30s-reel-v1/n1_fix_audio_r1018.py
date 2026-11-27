# -*- coding: utf-8 -*-
# n1_fix_audio_r1018.py — N1 发布闸音频真峰修复（file-level True Peak ≤ -1.0 dBFS）
# 实测 V5.7 decoded TP=+0.2 dBFS（真峰超满刻度·发布闸 FAIL）→ 定向衰减+复测闭环
# 视频流 100% copy 零重编码；音频 aac 192k 重编码；判据闭环=复测 TP ≤ -1.0
# v2 修正：gain 符号反向 bug（v1 误抬 +1.7dB 被闭环拦截）；目标 -2.0dB 留 AAC 过冲裕度；3 轮迭代保险
import os, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "full_mv_v57.mp4")
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "full_mv_v57_n1.mp4")
GATE = -1.0      # N1 判据线
TARGET_TP = -2.0 # 衰减目标（裕度抗 AAC 再过冲）

def measure(path):
    p = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path,
                       "-af", "ebur128=peak=true", "-f", "null", "-"],
                      capture_output=True, text=True, errors="replace")
    txt = p.stderr
    m = re.search(r"True peak:\s*Peak:\s*([-\d.]+)\s*dBTP", txt)
    if m:
        tp = float(m.group(1))
    else:
        m2 = re.findall(r"TPK:\s*([-\d.]+)\s+([-\d.]+)\s*dBFS", txt)
        tp = max(float(v) for v in m2[-1]) if m2 else None
    mi = re.search(r"I:\s*([-\d.]+)\s*LUFS", txt.split("Summary:")[-1]) if "Summary:" in txt else None
    lufs = float(mi.group(1)) if mi else None
    return tp, lufs

tp0, i0 = measure(SRC)
print("MEASURE source: TP=%s dBTP  I=%s LUFS" % (tp0, i0), flush=True)
if tp0 is None:
    raise SystemExit("FATAL: cannot measure TP")
if tp0 <= GATE:
    print("N1 PASS already (TP=%.1f <= %.1f) — no fix needed" % (tp0, GATE), flush=True)
    sys.exit(0)

att = tp0 - TARGET_TP          # 正数=衰减量（dB）
for attempt in range(1, 4):
    print("ATTEMPT %d: apply -%.2fdB (TP %.1f -> target %.1f)" % (attempt, att, tp0, TARGET_TP), flush=True)
    subprocess.run([FF, "-y", "-i", SRC, "-c:v", "copy", "-af", "volume=-%.2fdB" % att,
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", DST], check=True)
    tp1, i1 = measure(DST)
    print("MEASURE fixed: TP=%.1f dBTP  I=%s LUFS" % (tp1, i1), flush=True)
    if tp1 is not None and tp1 <= GATE:
        print("N1-FIX-OK %s  TP %.1f -> %.1f dBTP  I %.1f -> %s LUFS"
              % (os.path.basename(DST), tp0, tp1, i0, i1), flush=True)
        sys.exit(0)
    att += (tp1 if tp1 is not None else 1.0) - TARGET_TP   # 复测仍超线=累计加衰减重来
raise SystemExit("FATAL: 3 attempts, post-fix TP=%.1f still > %.1f" % (tp1, GATE))
