# -*- coding: utf-8 -*-
# build_30s_reel.py - assemble the 30s test reel: zoompan shots + H3 shots + original song BGM.
# Timeline (song 0:00-0:30, intro piano + first verse "古巴比伦王颁布了汉摩拉比法典..."):
#   0-5s   shot1 tablet ecu      (H3 i2v, dynamic flame/hand)
#   5-10s  shot2 hall wide       (zoompan slow push)
#   10-15s shot3 scribe medium   (zoompan lateral drift)
#   15-20s shot4 goddess         (H3 i2v, breathing light)
#   20-25s shot5 campus bike     (zoompan pull-out feel)
#   25-30s shot6 museum          (zoompan slow push + fade out)
# 864x480@24fps, fade in/out, loudness-normalized BGM. Low-precision by CEO order.
import os, subprocess, sys

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
BASE = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out"
FRAMES = os.path.join(BASE, "quick-reel")
H3DIR = os.path.join(BASE, "reel-h3")
OUT = os.path.join(BASE, "30s-reel")
os.makedirs(OUT, exist_ok=True)
SONG = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\audio\mv001_source_320k.mp3"

W, H, FPS, DUR = 864, 480, 24, 5

def zoompan(frame, out_mp4, mode="push", dur=DUR):
    # Ken Burns from still: slow push-in / lateral drift; 1344x768 source -> 864x480 crop window
    if mode == "push":
        z = "zoompan=z='min(1+0.12*on/{N},1.13)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={N}:s={W}x{H}:fps={F}"
    elif mode == "drift":
        z = "zoompan=z=1.10:x='iw/2-(iw/zoom/2)+({N}-on)*2.2':y='ih/2-(ih/zoom/2)':d={N}:s={W}x{H}:fps={F}"
    elif mode == "pull":
        z = "zoompan=z='max(1.13-0.12*on/{N},1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={N}:s={W}x{H}:fps={F}"
    else:
        raise ValueError(mode)
    z = z.format(N=DUR * FPS, W=W, H=H, F=FPS)
    vf = ("scale=1728:986," + z +  # upscale source so crop window never exceeds frame
          ",format=yuv420p")
    cmd = [FF, "-y", "-loop", "1", "-i", frame, "-vf", vf,
           "-t", str(DUR), "-r", str(FPS), "-c:v", "libx264", "-preset", "fast",
           "-crf", "23", "-an", out_mp4]
    subprocess.run(cmd, check=True, capture_output=True)
    print("ZOOMPAN ok:", out_mp4, flush=True)

def main():
    # 1) zoompan shots (2 hall, 3 scribe-locked, 5 bike-locked, 6 museum-locked)
    # cast frames use the face-locked versions (CEO consistency order)
    zp = [
        ("QR_S4_hall.png",          "shot2_hall.mp4",   "push"),
        ("QR_S2_scribe_locked.png", "shot3_scribe.mp4", "drift"),
        ("QR_S6_bike_locked.png",   "shot5_bike.mp4",   "pull"),
        ("QR_S5_museum_locked.png", "shot6_museum.mp4", "push"),
    ]
    for frame, out, mode in zp:
        zoompan(os.path.join(FRAMES, frame), os.path.join(OUT, out), mode)

    # 2) H3 shots (dynamic) live in H3DIR: shot1 tablet (no face, stable) + shot4 goddess (face-locked rerun)
    h3_required = ["shot1_tablet.mp4", "shot4_goddess.mp4"]
    for f in h3_required:
        if not os.path.exists(os.path.join(H3DIR, f)):
            print("MISSING H3 shot:", os.path.join(H3DIR, f), flush=True)
            sys.exit(1)

    # 3) normalize every part to identical codec/size/fps for concat
    order = [(os.path.join(H3DIR, "shot1_tablet.mp4")),
             os.path.join(OUT, "shot2_hall.mp4"),
             os.path.join(OUT, "shot3_scribe.mp4"),
             os.path.join(H3DIR, "shot4_goddess.mp4"),
             os.path.join(OUT, "shot5_bike.mp4"),
             os.path.join(OUT, "shot6_museum.mp4")]
    for p in order:
        if not os.path.exists(p):
            print("MISSING PART:", p, flush=True)
            sys.exit(1)
    norm = []
    for i, p in enumerate(order):
        n = os.path.join(OUT, "n%d.mp4" % i)
        cmd = [FF, "-y", "-i", p, "-vf", "scale=%d:%d,format=yuv420p,fps=%d" % (W, H, FPS),
               "-t", str(DUR), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "23", n]
        subprocess.run(cmd, check=True, capture_output=True)
        norm.append(n)

    # 4) concat
    lst = os.path.join(OUT, "concat.txt")
    with open(lst, "w") as f:
        for n in norm:
            f.write("file '%s'\n" % n.replace("'", "'\\''"))
    silent = os.path.join(OUT, "video_only.mp4")
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent],
                   check=True, capture_output=True)
    print("CONCAT ok:", silent, flush=True)

    # 5) BGM: first 30s of the song, loudness fit, fade in/out; mux
    final = os.path.join(BASE, "爱在西元前-30s-test-reel.mp4")
    af = ("atrim=0:30,asetpts=N/SR/TB,volume=0.9,"
          "afade=t=in:st=0:d=1,afade=t=out:st=28:d=2")
    subprocess.run([FF, "-y", "-i", silent, "-i", SONG,
                    "-vf", "fade=t=in:st=0:d=0.8,fade=t=out:st=28.5:d=1.5",
                    "-af", af, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", final],
                   check=True, capture_output=True)
    print("FINAL REEL:", final, flush=True)
    print("SIZE: %.1f MB" % (os.path.getsize(final) / 1e6), flush=True)

main()
