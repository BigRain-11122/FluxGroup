# -*- coding: utf-8 -*-
# make_v56src_v59_r1019.py — V5.9 SING3b 段选重切（缺陷③复发修复·零烧·2026-10-19）
# Why：制监对抗审查 REJECT（SUPERVISOR-REVIEW §四 R1）——现行 V56_SING1_reprise_v59.mp4 为
#      「选段执行错件」（0/6 开口·锈红上衣·出处不可追溯），宣称切点「源 1.20-3.30s」上游实测为真
#      （制监六时点 4/6 明确开口·含完整开合周期；导演席原生 tile 0.6-2.4 窗 8/10 开口互证）。
#      修复=按宣称切点正确执行：源 SING1_torch_song_v2_s9013.mp4 1.20-3.30s 段 + punch-in 1.124x。
# crop 重定（R1 指令「勿照抄 2.88 段的 74:42」）：按 1.20-3.30 段构图实测脸位（f_10 原生 bbox
#      x 0.36-0.55·y 0.08-0.38·嘴 (0.505,0.285)）→ x 74→40（脸中心 612px 居中·火炬仍落右三分线），
#      y=42 保留仰头段头顶余量（发顶 61px>42 ✓）。
# 断言（出生地闸·J-41）：产出即回验——时长 2.05-2.15s + 5 帧原生抽检（制监实测时点·期望 ≥3/5 开口），
#      防「选段执行错件/no-op 重切」二犯；人工 analyze 复核 tile 后才准 --swap 换装。
# 用法：python make_v56src_v59_r1019.py            # 只产 staging + 自检抽帧（不动在审文件）
#       python make_v56src_v59_r1019.py --swap     # 备份错件→staging 入位（须先过 tile 人工复核）
import os, subprocess, sys, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\jayredo\SING1_torch_song_v2_s9013.mp4"
FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
V56SRC = os.path.join(HERE, "v56src")
FINAL = os.path.join(V56SRC, "V56_SING1_reprise_v59.mp4")
STAGE = os.path.join(V56SRC, "V56_SING1_reprise_v59_new.mp4")
BAK = os.path.join(V56SRC, "V56_SING1_reprise_v59_wrongfile_r1019.bak.mp4")
CHK = r"C:\Users\sjs20\AppData\Local\Temp\sing3b_fix\newrepr"
T0, T1 = 1.20, 3.30
VF = "crop=1196:684:40:42,scale=1344:768:flags=lanczos,eq=brightness=-0.02:saturation=1.03"

SWAP = "--swap" in sys.argv
if SWAP:
    assert os.path.isfile(STAGE), "FATAL swap: staging missing - run emit first"
    if os.path.isfile(FINAL) and not os.path.isfile(BAK):
        shutil.copy2(FINAL, BAK)
        print("BACKUP wrongfile ->", os.path.basename(BAK), flush=True)
    os.replace(STAGE, FINAL)
    print("SWAP-OK -> V56_SING1_reprise_v59.mp4 (src 1.20-3.30s·crop x40)", flush=True)
    sys.exit(0)

os.makedirs(CHK, exist_ok=True)
cmd = [FF, "-y", "-loglevel", "error", "-ss", "%.2f" % T0, "-t", "%.2f" % (T1 - T0), "-i", SRC,
       "-vf", VF, "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-an", STAGE]
subprocess.run(cmd, check=True)
r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", STAGE],
                  capture_output=True, text=True)
dur = float(r.stdout.strip())
assert 1.95 <= dur <= 2.15, "FATAL stage dur %.3f out of 2.10 range" % dur
print("STAGE-EMIT dur=%.3f src=%.2f-%.2f punch-in 1.124x crop=1196:684:40:42" % (dur, T0, T1), flush=True)

# 自检抽帧（制监六时点换算到段内：src-1.20）＝1.30/1.65/2.00/2.40/2.80 → 0.10/0.45/0.80/1.20/1.60
# 期望：0.10 开·0.45 开·0.80 闭(收合相)·1.20 开·1.60 开 → ≥4/5 开口（闸线 ≥3/5）
for i, tt in enumerate((0.10, 0.45, 0.80, 1.20, 1.60)):
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "%.2f" % tt, "-i", STAGE,
                    "-frames:v", "1", "-q:v", "3", os.path.join(CHK, "n_%02d.jpg" % i)], check=True)
subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", "1",
                "-i", os.path.join(CHK, "n_%02d.jpg"),
                "-vf", "crop=480:300:478:49,tile=5x1", "-frames:v", "1", "-q:v", "3",
                os.path.join(CHK, "newrepr_mouth_tile.jpg")], check=True)
print("CHECK-TILE -> %s (expect n1/n2/n4/n5 open, n3=close; gate >=3/5 open)" % os.path.join(CHK, "newrepr_mouth_tile.jpg"), flush=True)
