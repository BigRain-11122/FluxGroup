# -*- coding: utf-8 -*-
"""mv0001 final build v1 (automated): 768p segment rebuild + interpolation + unified grade + loudness + ASS subtitles."""
import json, os, re, io, subprocess, sys, time

JAY  = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
PLAN = os.path.join(JAY, ".assembly-plan-v2.json")
LRC  = os.path.join(JAY, "lyrics", "爱在西元前.lrc")
SONG = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\audio\mv001_source_320k.mp3"
STILL= r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\drafts\frames\S016_modern_him_v2.png"
MED  = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
SEG  = os.path.join(MED, "final-v1", "seg768")
REL  = os.path.join(MED, "release")
ASS  = os.path.join(MED, "final-v1", "ayxq-subs.ass")
RAW  = os.path.join(MED, "final-v1", "_concat768.mp4")
OUT  = os.path.join(REL, "AXYQ-FINAL-v1-768p.mp4")
for d in (SEG, REL, os.path.dirname(ASS)): os.makedirs(d, exist_ok=True)

W, H, FPS = 1344, 768, 24
plan = json.load(open(PLAN, encoding="utf-8"))

def cdur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",p],
                       capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=60)
    return float(json.loads(r.stdout)["format"]["duration"])

GRADE = "eq=contrast=1.02:saturation=1.04,vignette=0.32"
MI = "minterpolate=fps=24:mi_mode=mci:mc_mode=obmc"   # 便宜档：只在 factor>=1.45 时用
NO_MI = {"S001"}  # 静场长镜不插值（tpad 尾帧定格）

def build_seg(it, i):
    sid, need, treat, path = it["id"], it["dur"], it["treat"], it["path"]
    seg = os.path.join(SEG, sid + ".mp4")
    if os.path.exists(seg) and os.path.getsize(seg) > 5000: return seg
    vf = []
    if treat == "punch": vf.append("crop=1002:573:171:97")
    vf.append(f"scale={W}:{H}"); vf.append(GRADE)
    if treat == "grade_gold":
        vf.append("eq=saturation=1.28:brightness=0.02")
        vf.append("colorbalance=rs=0.12:gs=0.05:bs=-0.12:rm=0.08:bm=-0.08:rh=0.05:bh=-0.05")
    if treat == "dim_ramp": vf.append("fade=t=out:st=0:d=%.3f:color=black" % need)
    vf.append("setsar=1")

    if sid == "S016":
        cmd = ["ffmpeg","-y","-v","error","-loop","1","-i",STILL,
               "-vf",",".join(vf+[f"zoompan=z='1+0.06*on/{int(need*FPS)}':d=1:s={W}x{H}"]),
               "-t","%.3f"%need,"-r",str(FPS),"-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",seg]
        subprocess.run(cmd, capture_output=True, timeout=600); return seg
    if not path or not os.path.exists(path):
        print("BLACK", sid); 
        subprocess.run(["ffmpeg","-y","-v","error","-f","lavfi","-i",f"color=c=black:s={W}x{H}:r={FPS}",
                        "-t","%.3f"%need,"-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",seg],capture_output=True)
        return seg

    avail = cdur(path)
    factor = max(1.0, need / avail)
    use_mi = (factor >= 1.45) and (sid not in NO_MI)
    # Special cases: S001 static hall slowed 2.6x (kills freeze); S046 trims the dark tail then slow-fills (kills black gap).
    if sid == "S001":
        cap = 2.60
        chain = [f"setpts={cap:.4f}*PTS"] + vf
        cmd = ["ffmpeg","-y","-v","error","-i",path,"-vf",",".join(chain),"-t","%.3f"%need,"-an",
               "-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p",seg]
    elif sid == "S046":
        keep = 3.30
        fac = need / keep
        chain = [f"trim=0:{keep}", f"setpts={fac:.4f}*PTS", MI] + vf
        cmd = ["ffmpeg","-y","-v","error","-i",path,"-vf",",".join(chain),"-t","%.3f"%need,"-an",
               "-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p",seg]
    elif treat == "slow" or factor > 1.03:
        if factor <= 1.85:
            chain = [f"setpts={factor:.4f}*PTS"] + ([MI] if use_mi else []) + vf
            cmd = ["ffmpeg","-y","-v","error","-i",path,"-vf",",".join(chain),"-t","%.3f"%need,"-an",
                   "-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p",seg]
        else:
            cap = 1.85
            pad = need - avail*cap
            chain = [f"setpts={cap:.4f}*PTS"] + ([MI] if use_mi else []) + vf + [f"tpad=stop_mode=clone:stop_duration={pad:.3f}"]
            cmd = ["ffmpeg","-y","-v","error","-i",path,"-vf",",".join(chain),"-t","%.3f"%need,"-an",
                   "-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p",seg]
    else:
        ss = max(0.0, (avail - need)/2.0)
        cmd = ["ffmpeg","-y","-v","error","-ss","%.3f"%ss,"-i",path,"-vf",",".join(vf),
               "-t","%.3f"%need,"-an","-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p",seg]
    r = subprocess.run(cmd, capture_output=True, timeout=900)
    if not os.path.exists(seg) or os.path.getsize(seg) < 5000:
        print("SEGFAIL", sid, r.stderr[-200:])
    return seg

# ---------- 1) segments ----------
segs=[]; t0=time.time()
for i,it in enumerate(plan,1):
    segs.append(build_seg(it,i))
    if i % 10 == 0: print(f"[seg {i}/{len(plan)}] {time.time()-t0:.0f}s", flush=True)
print("segments done", flush=True)

# ---------- 2) concat ----------
lst = os.path.join(SEG,"concat.txt")
io.open(lst,"w",encoding="utf-8").write("".join("file '%s'\n" % s.replace("\\","/") for s in segs))
r = subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",lst,"-c","copy",RAW],
                   capture_output=True,text=True,timeout=900)
print("concat:", os.path.exists(RAW), flush=True)

# ---------- 3) subtitles (ASS) ----------
def ts(x):
    h=int(x//3600); m=int(x%3600//60); s=x%60
    return f"{h:d}:{m:02d}:{s:05.2f}"

lrc=[]
for line in io.open(LRC,encoding="utf-8",errors="replace"):
    m=re.match(r"\[(\d+):(\d+\.\d+)\](.+)$", line.strip())
    if m: lrc.append((int(m.group(1))*60+float(m.group(2)), m.group(3).strip()))
lrc.sort()
ev=[]
for i,(st,txt) in enumerate(lrc):
    en = lrc[i+1][0] if i+1 < len(lrc) else min(st+4.0, 234.25)
    en = min(max(en, st+1.2), st+5.5)
    ev.append(f"Dialogue: 0,{ts(st)},{ts(en)},Lyric,,0,0,0,,{{\\fad(150,150)}}{txt}")
head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1344
PlayResY: 768
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,Microsoft YaHei,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,0,0,0,0,100,100,0.6,0,1,0,1.6,2,60,60,66,1
Style: Title,Microsoft YaHei,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,-1,0,0,0,100,100,6,0,1,0,2.4,5,60,60,0,1
Style: SubTitle,Microsoft YaHei,30,&H00E6E6E6,&H00E6E6E6,&H00000000,&H9A000000,0,0,0,0,100,100,2,0,1,0,1.2,5,60,60,0,1
Style: Tag,Microsoft YaHei,20,&H50FFFFFF,&H50FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,22,22,22,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
events = [
 f"Dialogue: 0,{ts(0.8)},{ts(5.2)},Title,,0,0,0,,{{\\pos(672,330)\\fad(420,650)}}爱在西元前",
 f"Dialogue: 0,{ts(1.6)},{ts(5.2)},SubTitle,,0,0,0,,{{\\pos(672,430)\\fad(500,650)}}词 方文山　　曲 周杰伦",
 f"Dialogue: 0,{ts(0)},{ts(234.25)},Tag,,0,0,0,,AI 生成",
] + ev
io.open(ASS,"w",encoding="utf-8").write(head + "\n".join(events))
print("ass:", os.path.exists(ASS), len(ev), "lyric events", flush=True)

# ---------- 4) loudness (two-pass) ----------
r = subprocess.run(["ffmpeg","-hide_banner","-i",SONG,"-af","loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
                    "-f","null","-"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
ln = json.loads(m.group(0)) if m else {}
print("loudnorm measured:", ln.get("input_i"), ln.get("input_tp"), flush=True)
af = (f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={ln.get('input_i',-14)}:"
      f"measured_TP={ln.get('input_tp',0)}:measured_LRA={ln.get('input_lra',11)}:"
      f"measured_thresh={ln.get('input_thresh',-24)}:offset={ln.get('target_offset',0)}:linear=true,alimiter=limit=0.620:level=false")

# ---------- 5) final encode (subtitles + audio; grade already baked into segments) ----------
cmd = ["ffmpeg","-y","-v","error","-i",RAW,"-i",SONG,
       "-vf", "tpad=stop_mode=clone:stop_duration=0.9,ass=ayxq-subs.ass",
       "-af",af,"-map","0:v","-map","1:a",
       "-t","234.25","-r",str(FPS),"-c:v","libx264","-preset","medium","-crf","18",
       "-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-movflags","+faststart",OUT]
r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                   timeout=2400, cwd=os.path.dirname(ASS))
print("final rc=", r.returncode, r.stderr[-400:] if r.returncode else "", flush=True)
if os.path.exists(OUT):
    pr = subprocess.run(["ffprobe","-v","error","-count_frames","-select_streams","v:0",
                         "-show_entries","stream=nb_read_frames,width,height,r_frame_rate",
                         "-show_entries","format=duration,size","-of","json",OUT],
                        capture_output=True,text=True)
    print(pr.stdout.strip())
