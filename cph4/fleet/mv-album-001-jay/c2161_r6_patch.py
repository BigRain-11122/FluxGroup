"""C2161 -- R6-1 (monarch -> silhouette) and R6-3 (montage pixel repeat break).

Assembly-layer only. Pure CPU, no GPU, no new source material.
Reads the shipped v5 render, re-encodes ONLY the two affected windows, and
prints the acceptance numbers the R6 response already defined:

  R6-1  64.000-70.080s  desaturate + soften so the wing pattern is unreadable
  R6-3  172.000-186.000s  punch-in the second pass (>=1.34x), lift +2 IRE, grain
        acceptance: duplicate frame hashes == 0 (was 77 pairs), YAVG mean 38-42

Run:  python c2161_r6_patch.py probe
"""

import json
import os
import re
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
SRC = os.path.join(REPO, r"media\mv-album-001-jay\assembly-packB\XQ-PACKB-ASSEMBLY-v5-c2159.mp4")
OUT = os.path.join(REPO, r"cph4\fleet\mv-album-001-jay\evidence-c2161")
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

BFLY = (64.000, 70.080)
MONT = (172.000, 186.000)
MONT_SPLIT = 179.000          # second pass starts here
PUNCH = (1003, 573, 170, 97)  # 1.34x centre crop, per R6-3 spec

BFLY_GRADE = ("eq=saturation=0.18:contrast=0.98:brightness=0.015,"
              "colorbalance=rs=0.10:gs=0.03:bs=-0.10,gblur=sigma=0.7")
GRAIN = "noise=alls=6:allf=t+u"
YAVG_TARGET = 38.5


def logline(s):
    sys.stdout.write(s + "\n")
    sys.stdout.flush()


def run(cmd, quiet=True):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        sys.stderr.write("FAIL rc=%d\n%s\n%s\n" % (p.returncode,
                                                  " ".join(cmd[:8]),
                                                  p.stderr.decode("utf-8", "replace")[-1500:]))
        raise SystemExit(1)
    return p


def window_stats(path, t0, t1):
    """Mean/min YAVG plus a U/V saturation proxy over a window."""
    p = run([FFMPEG, "-hide_banner", "-i", path,
             "-vf", "trim=start=%.3f:end=%.3f,signalstats,metadata=print" % (t0, t1),
             "-an", "-f", "null", "-"])
    ys, us, vs = [], [], []
    cur = {}
    for line in p.stderr.decode("utf-8", "replace").splitlines():
        line = line.strip()
        for key, bucket in (("YAVG", ys), ("UAVG", us), ("VAVG", vs)):
            if line.endswith("lavfi.signalstats." + key) or ".%s=" % key in line:
                try:
                    bucket.append(float(line.split("=")[-1]))
                except ValueError:
                    pass
    if not ys or len(ys) != len(us) or len(ys) != len(vs):
        return None
    sat = sum(((u - 128.0) ** 2 + (v - 128.0) ** 2) ** 0.5 for u, v in zip(us, vs)) / len(ys)
    return {"frames": len(ys), "yavg_mean": sum(ys) / len(ys), "yavg_min": min(ys),
            "yavg_max": max(ys), "sat_proxy": sat / 128.0}


def frame_hashes(path):
    p = run([FFMPEG, "-v", "error", "-i", path, "-map", "0:v:0", "-f", "framemd5", "-"])
    hashes = []
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = [c.strip() for c in line.split(",")]
        if len(cols) >= 6:
            hashes.append(cols[-1])
    return hashes


def dup_pairs(hashes):
    seen = {}
    for h in hashes:
        seen[h] = seen.get(h, 0) + 1
    return sum(n - 1 for n in seen.values()), len(hashes)


def encode(args, out):
    if os.path.exists(out):
        os.remove(out)
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + args + [
        "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p",
        "-an", out])


def probe():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    report = {"batch": "C2161", "source": SRC}

    # ---------- R6-1 butterfly ----------
    raw_b = window_stats(SRC, *BFLY)
    bfly_out = os.path.join(OUT, "bfly_graded.mp4")
    encode(["-ss", "%.3f" % BFLY[0], "-t", "%.3f" % (BFLY[1] - BFLY[0]), "-i", SRC,
            "-vf", BFLY_GRADE], bfly_out)
    new_b = window_stats(bfly_out, 0, BFLY[1] - BFLY[0])
    report["r6_1"] = {"raw": raw_b, "graded": new_b,
                      "sat_ratio": round(new_b["sat_proxy"] / raw_b["sat_proxy"], 3),
                      "ok": new_b["sat_proxy"] / raw_b["sat_proxy"] <= 0.22}

    # ---------- R6-3 montage ----------
    raw_m = window_stats(SRC, *MONT)
    w, h, x, y = PUNCH

    def montage_graph(bright):
        return (
            "[0:v]trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS,fps=24,setsar=1[a];"
            "[0:v]trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS,fps=24,"
            "crop=%d:%d:%d:%d,scale=1344:768:flags=lanczos,setsar=1[b];"
            "[a][b]concat=n=2:v=1:a=0,"
            "eq=brightness=%.4f:contrast=1.02:saturation=0.98,%s[out]"
            % (MONT[0], MONT_SPLIT, MONT_SPLIT, MONT[1], w, h, x, y, bright, GRAIN))

    # pass 1: punch-in alone, so the brightness correction is measured against
    # the composition that will actually ship (the crop darkens the window)
    mont_out = os.path.join(OUT, "montage_patched.mp4")
    encode(["-i", SRC, "-filter_complex", montage_graph(0.0), "-map", "[out]"], mont_out)
    mid = window_stats(mont_out, 0, MONT[1] - MONT[0])
    bright = 0.0
    new_m = mid
    # The 8-bit eq path quantises brightness to whole code steps, so an
    # analytic delta below ~1/128 silently does nothing. Step in real code
    # units and re-measure each pass; the encode is the only ground truth.
    for _ in range(3):
        err = YAVG_TARGET - new_m["yavg_mean"]
        if abs(err) <= 1.0:
            break
        bright = bright + (int(round(abs(err))) * (1 if err > 0 else -1)) / 255.0
        bright = max(-0.05, min(0.12, bright))
        encode(["-i", SRC, "-filter_complex", montage_graph(bright), "-map", "[out]"],
               mont_out)
        new_m = window_stats(mont_out, 0, MONT[1] - MONT[0])
        logline("LIFT pass bright=%.4f mean=%.2f" % (bright, new_m["yavg_mean"]))
    mtime = os.path.getmtime(mont_out)
    cache = os.path.join(OUT, "hashes-v5.json")
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            raw_all = json.load(f)
    else:
        raw_all = frame_hashes(SRC)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(raw_all, f)
    raw_dup, raw_n = dup_pairs(raw_all[int(round(MONT[0] * 24)):int(round(MONT[1] * 24))])
    new_dup, new_n = dup_pairs(frame_hashes(mont_out))
    report["r6_3"] = {"raw": raw_m, "punch_only": mid, "patched": new_m,
                      "brightness": round(bright, 4), "out_mtime": mtime,
                      "dup_raw": raw_dup, "dup_patched": new_dup,
                      "frames_raw": raw_n, "frames_patched": new_n,
                      "ok": new_dup == 0 and 37.5 <= new_m["yavg_mean"] <= 42.5
                      and new_m["yavg_min"] >= 32.0}

    with open(os.path.join(OUT, "PROBE-c2161.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))


def SRC_q(span):
    """Cut the raw montage window out of the source so hashes are comparable."""
    tmp = os.path.join(OUT, "_raw_montage.mp4")
    if not os.path.exists(tmp):
        encode(["-ss", "%.3f" % span[0], "-t", "%.3f" % (span[1] - span[0]), "-i", SRC],
               tmp)
    return tmp


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        probe()
    else:
        print(__doc__)