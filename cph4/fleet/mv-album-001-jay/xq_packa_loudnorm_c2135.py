# -*- coding: ascii -*-
"""C2135: PACK-A conform v2 - loudness-normalised delivery of the A-pack preview.

Why: the C2133 conform muxed the song with fades only, so its integrated loudness is
whatever the source happened to be. The house finishing standard (MV-PIPELINE-PLAYBOOK
step 5) is loudnorm I=-14 LUFS, TP=-1.5 dBTP, LRA=11. This pass keeps the video stream
untouched (-c:v copy), runs the two-pass loudnorm on the audio, re-applies the original
0.6s / 1.4s fades and re-measures the result with ebur128.

Zero GPU. PASS gate: LOUDNORM-END ok=1.
"""

import json
import os
import re
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
FLEET = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay", "assembly-packA")
SRC = os.path.join(MEDIA, "XQ-PACKA-CONFORM-v1-c2133.mp4")
OUT = os.path.join(MEDIA, "XQ-PACKA-CONFORM-v2-loudnorm-c2135.mp4")
SONG = os.path.join(FLEET, "audio", "\u5468\u6770\u4f26 - \u661f\u6674.mp3")  # Jay - Xingqing
RECEIPT = os.path.join(FLEET, "xq-PACKA-CONFORM-v2-loudnorm-c2135.json")
LOGROOT = os.path.join(REPO, "media", "mv-album-001-jay")
LOG_RUN = os.path.join(LOGROOT, "log-packa-loudnorm-c2135.run.txt")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

TARGET_I = -14.0
TARGET_TP = -1.5
TARGET_LRA = 11.0
FADE_IN = 0.6
FADE_OUT = 1.4


def logline(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (stamp, msg)
    with open(LOG_RUN, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")
    try:
        print(line)
    except Exception:
        pass


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if p.returncode != 0:
        raise RuntimeError("cmd failed (%d): %s\n%s" % (p.returncode, cmd, p.stderr[-2000:]))
    return p.stdout + p.stderr


def probe_duration(path):
    out = run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


def measure_loudness(path):
    out = run([FFMPEG, "-hide_banner", "-nostats", "-i", path,
               "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = out[out.rfind("Summary:"):]
    def grab(key):
        m = re.search(r"%s:\s*(-?[\d.]+)" % re.escape(key), tail)
        return float(m.group(1)) if m else None
    tp_block = tail[tail.rfind("True peak:"):] if "True peak:" in tail else ""
    m = re.search(r"Peak:\s*(-?[\d.]+)", tp_block)
    return {
        "I": grab("I"),
        "LRA": grab("LRA"),
        "True peak": float(m.group(1)) if m else None,
    }


def main():
    for p in (SRC, SONG):
        if not os.path.exists(p):
            logline("MISSING-INPUT %s" % p)
            sys.exit(2)

    dur = probe_duration(SRC)
    before = measure_loudness(SRC)
    logline("SOURCE dur=%.3fs I=%s LRA=%s TP=%s" %
            (dur, before["I"], before["LRA"], before["True peak"]))

    # Pass 1: measure the song segment exactly as long as the film.
    p1 = run([FFMPEG, "-hide_banner", "-nostats", "-i", SONG, "-t", "%.3f" % dur,
              "-af", "loudnorm=I=%.1f:TP=%.1f:LRA=%.1f:print_format=json" %
              (TARGET_I, TARGET_TP, TARGET_LRA),
              "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p1, re.S)
    if not m:
        logline("PASS1-NO-JSON")
        sys.exit(3)
    stats = json.loads(m.group(0))
    logline("PASS1 input_i=%s input_tp=%s input_lra=%s" %
            (stats.get("input_i"), stats.get("input_tp"), stats.get("input_lra")))

    # Pass 2: render normalised audio with the original fades.
    fade_out_start = max(0.0, dur - FADE_OUT)
    # loudnorm (linear) lands I on target; the source is peaky (+2.1 dBTP decoded), so a
    # level=false alimiter at 0.75 trims the remaining overshoot without touching loudness.
    af = ("loudnorm=I=%.1f:TP=%.1f:LRA=%.1f:measured_I=%s:measured_TP=%s:"
          "measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true,"
          "alimiter=limit=0.66:attack=0.1:release=40:level=false,"
          "afade=t=in:st=0:d=%.2f,afade=t=out:st=%.2f:d=%.2f" %
          (TARGET_I, TARGET_TP, TARGET_LRA, stats["input_i"], stats["input_tp"],
           stats["input_lra"], stats["input_thresh"], stats["target_offset"],
           FADE_IN, fade_out_start, FADE_OUT))
    tmp_audio = OUT + ".m4a"
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", SONG,
         "-t", "%.3f" % dur, "-af", af, "-c:a", "aac", "-b:a", "192k", tmp_audio])
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", SRC,
         "-i", tmp_audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-c:a", "copy", OUT])
    os.remove(tmp_audio)

    after = measure_loudness(OUT)
    dur2 = probe_duration(OUT)
    logline("RESULT dur=%.3fs I=%s LRA=%s TP=%s" %
            (dur2, after["I"], after["LRA"], after["True peak"]))

    ok = (after["I"] is not None and abs(after["I"] - TARGET_I) <= 0.6 and
          after["True peak"] is not None and after["True peak"] <= TARGET_TP + 0.2 and
          abs(dur2 - dur) <= 0.2)
    receipt = {
        "batch": "C2135",
        "artifact": OUT,
        "source": SRC,
        "gate": "loudnorm I=-14:TP=-1.5:LRA=11 linear + alimiter 0.66 (level=false)",
        "duration_src_s": round(dur, 3),
        "duration_new_s": round(dur2, 3),
        "loudness_before": before,
        "loudness_after": after,
        "pass1": {k: stats.get(k) for k in ("input_i", "input_tp", "input_lra",
                                            "input_thresh", "target_offset")},
        "fades": {"in": FADE_IN, "out": FADE_OUT},
        "ok": bool(ok),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(RECEIPT, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)

    logline("LOUDNORM-END ok=%d I=%.2f TP=%.2f dur_delta=%.3f" %
            (1 if ok else 0, after["I"] or 0.0, after["True peak"] or 0.0, dur2 - dur))
    if not ok:
        sys.exit(4)


if __name__ == "__main__":
    main()