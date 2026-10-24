# kn_interim_cut_c2173.py - interim cut of the KN 768P wave while it is still burning.
# Purpose: the wave lands ~10-17 min per unit, so nothing watchable exists for ~3h.
# This lays every landed unit on its AUTHORED song clock (start/end read straight out of
# 可爱女人-shots-v2.py) instead of inventing an order, keeps a slate card in the slot of
# the one unit that is knowingly defective (KN02, burned caption + push-in, staged for
# re-burn), and muxes the song from 0 so the result can be judged in real time.
# NOT a delivery: no DIRECTOR-REVIEW, name carries INTERIM and the landed count.
import glob
import io
import json
import os
import re
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(ALBUM, "clips-local-768")
OUT = os.path.join(ALBUM, "interim-c2173")
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
SHOTS = glob.glob(os.path.join(OUTDIR, "*shots-v2.py"))[0]
SONG = os.path.join(OUTDIR, "audio", "周杰伦 - 可爱女人.mp3")
W, H, FPS = 1344, 768, 24
DEFECT = {"KN02"}          # knowingly bad, staged for re-burn: slate instead of footage
FONT = r"C:\Windows\Fonts\msyh.ttc"


def sh(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=cwd)
    if p.returncode != 0:
        print("FFMPEG-FAIL rc=%d\n%s\n%s" % (p.returncode, " ".join(cmd[:12]), p.stderr[-1200:]))
        sys.exit(1)


def timeline():
    text = io.open(SHOTS, encoding="utf-8").read()
    rows = re.findall(r'\("(KN\d+[a-z]?)",\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)', text)
    first = {}
    for shot, s, e, sp in rows:
        if shot in first:      # later tuples are montage re-uses, not the first pass
            continue
        first[shot] = (float(s), float(e), float(sp))
    return first


def slate(sec, label, dest):
    # ffmpeg filter args take a Windows drive colon as "\:" - pass relative names instead
    io.open(os.path.join(OUT, "_slate.txt"), "w", encoding="utf-8").write(label)
    sh([r"C:\Program Files\ffmpeg\bin\ffmpeg.exe", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=0x101010:s=%dx%d:r=%d:d=%.3f" % (W, H, FPS, sec),
        "-vf", "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':textfile='_slate.txt':"
               "fontcolor=0x9a9a9a:fontsize=34:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        os.path.basename(dest)], cwd=OUT)


def segment(clip, speed, dur, dest):
    sh([r"C:\Program Files\ffmpeg\bin\ffmpeg.exe", "-y", "-hide_banner", "-loglevel", "error",
        "-i", clip, "-vf", "setpts=PTS*%.4f,fps=%d,scale=%d:%d" % (speed, FPS, W, H),
        "-t", "%.3f" % dur, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", dest])


def main():
    os.makedirs(OUT, exist_ok=True)
    tl = timeline()
    parts, rows = [], []
    shot_names = sorted([k for k in tl if re.match(r"^KN\d+$", k)], key=lambda s: int(s[2:]))
    for shot in shot_names:
        clip = os.path.join(CLIPS, "KN_A-%s.mp4" % shot)
        if not os.path.exists(clip):
            continue
        start, end, speed = tl[shot]
        dur = round(end - start, 3)
        dest = os.path.join(OUT, "seg-%s.mp4" % shot)
        if shot in DEFECT:
            slate(dur, "%s - re-burn staged (burned-in caption)" % shot, dest)
            rows.append({"shot": shot, "t0": start, "win_s": dur, "status": "SLATE-DEFECT"})
        else:
            segment(clip, speed, dur, dest)
            rows.append({"shot": shot, "t0": start, "win_s": dur, "speed": speed,
                         "status": "INCLUDED"})
        parts.append(dest)
    if not parts:
        print("NO_LANDED")
        return 1
    total = max(r["t0"] + r["win_s"] for r in rows)
    lst = os.path.join(OUT, "_concat.txt")
    io.open(lst, "w", encoding="utf-8", newline="\n").write(
        "".join("file '%s'\n" % p.replace("\\", "/") for p in parts))
    silent = os.path.join(OUT, "_video.mp4")
    sh([r"C:\Program Files\ffmpeg\bin\ffmpeg.exe", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    final = os.path.join(OUT, "KN-768P-INTERIM-%dof30-%s.mp4" % (len(rows), "c2173"))
    sh([r"C:\Program Files\ffmpeg\bin\ffmpeg.exe", "-y", "-hide_banner", "-loglevel", "error",
        "-i", silent, "-ss", "0", "-t", "%.3f" % total, "-i", SONG,
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-af", "afade=t=in:st=0:d=0.4,afade=t=out:st=%.2f:d=1.2" % (total - 1.2),
        "-shortest", "-movflags", "+faststart", final])
    probe = subprocess.run([r"C:\Program Files\ffmpeg\bin\ffprobe.exe", "-v", "error",
                            "-show_entries", "format=duration,size", "-of", "json", final],
                           capture_output=True, text=True).stdout
    meta = json.loads(probe).get("format", {})
    rec = {"final": final, "units": len(rows), "timeline_end_s": round(total, 3),
           "duration_s": float(meta.get("duration", 0)), "bytes": int(meta.get("size", 0)),
           "rows": rows}
    io.open(os.path.join(ALBUM, "evidence-c2173", "interim-cut.json"), "w",
            encoding="utf-8").write(json.dumps(rec, ensure_ascii=False, indent=1))
    print(json.dumps({k: rec[k] for k in ("final", "units", "duration_s", "bytes")},
                     ensure_ascii=False))
    print("INTERIM-END")
    return 0


if __name__ == "__main__":
    sys.exit(main())