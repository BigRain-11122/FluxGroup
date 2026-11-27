# -*- coding: utf-8 -*-
"""build_full_mv.py — 《爱在西元前》全片装配（叙述版，52 镜 / 234.25s）。

读 EDIT-PLAN-NARRATIVE.json；分块拼（每块 12 镜）→ 合块 → 全局 90s 胶片调色 + 字层 → 合原曲。
判例：drawtext 的 textfile 一律用**相对名 + cwd=TMP**（绝对路径里的 `K:` 冒号会打断滤镜解析）。
"""
import json
import os
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"K:\Fluxgroup\FluxGroup"
POOL_DIR = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "pool")
PLAN = os.path.join(POOL_DIR, "EDIT-PLAN-NARRATIVE.json")
TMP = r"K:\Fluxgroup\.codely-cli\tmp\fullmv"
OUT = os.path.join(ROOT, "media", "mv0001-handover", "deliverable", "爱在西元前-全片-v1-未审.mp4")
SONG = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "audio", "mv001_source_320k.mp3")
FS = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FSS = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FP = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"
W, H, FPS = 1344, 768, 24
CHUNK = 12

os.makedirs(TMP, exist_ok=True)
plan = json.load(open(PLAN, encoding="utf-8"))["plan"]
NOCAP = {"N02", "R02"}          # 这两条源片自带旧字幕，裁掉底部 12%



def run(cmd, label, timeout=10800, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                       timeout=timeout, cwd=cwd)
    if r.returncode:
        print("[%s] FAIL rc=%d" % (label, r.returncode))
        print((r.stderr or "")[-1500:])
        raise SystemExit(1)
    print("[%s] ok" % label, flush=True)


# ---------- 1) 分块 ----------
chunks, idx = [], 0
while idx < len(plan):
    part = plan[idx:idx + CHUNK]
    idx += CHUNK
    ins, filt = [], ""
    for j, p in enumerate(part):
        src = os.path.join(ROOT, "media", "MV", "mv0001", p["src"])
        dur, avail_src = p["dur"], p["src_dur"]
        in_pt = float(p.get("in_pt") or 0.0)
        in_pt = max(0.0, min(in_pt, max(0.0, avail_src - 1.0)))
        remain = max(0.4, avail_src - in_pt)
        if dur <= remain:
            use, k = dur, 1.0
        else:
            use, k = remain, dur / remain          # 源不够 → 慢放补齐
        punch = float(p.get("punch") or 1.0)
        chain = "[%d:v]trim=%.4f:%.4f,setpts=(PTS-STARTPTS)*%.6f" % (
            j, in_pt, in_pt + use, k)
        if punch > 1.001:                           # 重演换机位：按源尺寸相对推近（兼容 480p 素材）
            chain += (",crop=iw/%.4f:ih/%.4f:(iw-iw/%.4f)/2:(ih-ih/%.4f)/2" %
                      (punch, punch, punch, punch))
        if p["id"] in NOCAP:
            chain += ",crop=iw:ih*0.88:0:0"
        chain += ",fps=%d,scale=%d:%d:flags=lanczos,setsar=1" % (FPS, W, H)
        if p["w"] < 1200:
            chain += ",unsharp=5:5:0.28"
        filt += chain + "[s%d];" % j
        ins.append(src)
    filt += "".join("[s%d]" % j for j in range(len(part))) + \
            "concat=n=%d:v=1:a=0[vout]" % len(part)
    outp = os.path.join(TMP, "chunk%02d.mp4" % len(chunks))
    cmd = [FF, "-y"]
    for s in ins:
        cmd += ["-i", s]
    cmd += ["-filter_complex", filt, "-map", "[vout]",
            "-c:v", "libx264", "-crf", "16", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-r", str(FPS), outp]
    run(cmd, "chunk%d(%d镜)" % (len(chunks), len(part)))
    chunks.append(outp)

lst = os.path.join(TMP, "chunks.txt")
with open(lst, "w", encoding="utf-8") as f:
    for c in chunks:
        f.write("file '%s'\n" % c.replace("\\", "/"))
raw = os.path.join(TMP, "raw.mp4")
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw], "concat_chunks")

# ---------- 2) 调色 + 字层 ----------
TEXTS = {
    "t_credit.txt": "词：方文山　曲：周杰伦",
}
for n, s in TEXTS.items():
    open(os.path.join(TMP, n), "w", encoding="utf-8", newline="\n").write(s)

SS = FSS.replace("\\", "/").replace(":", "\\:")
SR = FS.replace("\\", "/").replace(":", "\\:")

CURVES = ("curves=all='0/0.050 0.20/0.252 0.50/0.545 0.80/0.855 1/1'"
          ":r='0/0.050 0.70/0.712 1/0.978':b='0/0.050 0.70/0.752 1/1'"
          ",eq=contrast=1.05:saturation=1.02")
BAL = "colorbalance=rs=0.055:gs=0.012:bs=-0.030:rm=0.018:gm=0.003:bm=-0.010"
HAL = ("split=2[hb][hs];[hs]colorlevels=rimin=0.82:gimin=0.82:bimin=0.82,"
       "gblur=sigma=11,colorchannelmixer=rr=1.0:gg=0.48:bb=0.18[hg];"
       "[hb][hg]blend=all_mode=screen:all_opacity=0.20")
VIG = "vignette=a=0.28"
WEAVE = ("crop=iw-2:ih-2:x='1+0.5*sin(n/9)':y='1+0.5*sin(n/13)',"
         "scale=%d:%d:flags=bicubic" % (W, H))

fc = (
    "[0:v]%s,%s,%s,noise=alls=4:allf=t+u,%s,%s[v0];\n"
    "[v0]drawtext=fontfile='%s':textfile='t_credit.txt':fontcolor=white@0.90:fontsize=28:"
    "x=(w-text_w)/2:y=h-96:box=1:boxcolor=black@0.34:boxborderw=14:"
    "alpha='if(lt(t,230.6),0,min(1,(t-230.6)/1.2))':enable='gte(t,230.6)'[vout]"
) % (CURVES, BAL, HAL, VIG, WEAVE, SR)

open(os.path.join(TMP, "grade.filter"), "w", encoding="ascii").write(fc)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
run([FF, "-y", "-i", raw, "-i", SONG,
     "-filter_complex_script", "grade.filter",
     "-map", "[vout]", "-map", "1:a",
     "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
     "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-shortest",
     "-movflags", "+faststart", OUT], "final", cwd=TMP)

p = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-count_frames",
                    "-show_entries", "stream=nb_read_frames,width,height",
                    "-show_entries", "format=duration,size",
                    "-of", "default=nw=1", OUT], capture_output=True, text=True)
print(p.stdout.strip())
print("OUT %s  %.1f MB" % (OUT, os.path.getsize(OUT) / 1048576))
