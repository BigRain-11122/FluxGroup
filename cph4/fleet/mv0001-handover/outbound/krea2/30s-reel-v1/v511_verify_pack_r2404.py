# -*- coding: utf-8 -*-
# r2404 verify pack: PTS scan json + XFS cut board + split dense board + grade sample board
import os, subprocess, json, io

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "full_mv_v511_proxy.mp4")
OUT = os.path.join(HERE, "_proxycheck")
os.makedirs(OUT, exist_ok=True)

CUTS = [21.900, 38.820, 40.220, 44.000, 47.500, 80.180, 102.880,
        110.520, 126.320, 131.720, 152.000, 187.260, 191.600, 227.500]
SPLITS = [("N05", 65.4445), ("N06", 71.4940), ("R05", 129.2392), ("R06", 135.1400)]
# amber zone = Babylon / stele interiors; cool zone = museum hall / night wide
AMBER = [8.0, 63.0, 133.0]
COOL = [40.5, 106.0, 205.0]


def grab(t, name):
    dst = os.path.join(OUT, name)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % t, "-i", SRC,
                    "-frames:v", "1", "-q:v", "3", dst], check=True)
    return dst


def stack(paths, cols, dst):
    inputs = []
    for p in paths:
        inputs += ["-i", p]
    n = len(paths)
    layout = "|".join("%s_%s" % ("w0" * (i % cols) if i % cols else "0",
                                 "h0*%d" % (i // cols) if i // cols else "0")
                      for i in range(n))
    layout = "|".join(("0" if i % cols == 0 else "w0") + "_" + ("0" if i // cols == 0 else "h0*%d" % (i // cols))
                      for i in range(n))
    fc = "".join("[%d]" % i for i in range(n)) + "xstack=inputs=%d:layout=%s" % (n, layout)
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs +
                   ["-filter_complex", fc, "-q:v", "3", dst], check=True)


def main():
    # 1) PTS scan
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "frame=pts_time", "-of", "csv=p=0", SRC],
                       capture_output=True, text=True)
    ts = sorted(float(x) for x in r.stdout.replace(",", " ").split() if x.strip())
    steps = [(i, round(ts[i] - ts[i - 1], 6)) for i in range(1, len(ts))]
    bad = [(i, d) for i, d in steps if abs(d - 1 / 24.0) > 0.008]
    meta = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_name,width,height,r_frame_rate,nb_frames",
         "-of", "json", SRC], capture_output=True, text=True).stdout)
    pack = {"file": "full_mv_v511_proxy.mp4", "ffprobe": meta,
            "frames": len(ts), "first": ts[0], "last": ts[-1],
            "pts_nonuniform_steps": len(bad), "pts_anomalies_sample": bad[:5],
            "expected_fps_step": 1 / 24.0, "tolerance": 0.008,
            "verdict": "PASS" if not bad else "FAIL"}
    with io.open(os.path.join(HERE, "v511_verify_pack_r2404.json"), "w",
                 encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, indent=1)
    print("PTS frames=%d anomalies=%d verdict=%s" % (len(ts), len(bad), pack["verdict"]))

    # 2) XFS 14 cut motion board: before / after (+/-0.21s)
    xfs = []
    for i, c in enumerate(CUTS):
        a = grab(c - 0.21, "x%02d_a.jpg" % i)
        b = grab(c + 0.21, "x%02d_b.jpg" % i)
        xfs += [a, b]
    stack(xfs, 2, os.path.join(OUT, "XFS-CUT-BOARD.jpg"))

    # 3) split dense board: 4 splits x (pre, mid, post)
    sp = []
    for name, c in SPLITS:
        for off, tag in ((-0.25, "a"), (0.0, "m"), (0.25, "b")):
            sp.append(grab(c + off, "s_%s_%s.jpg" % (name, tag)))
    stack(sp, 3, os.path.join(OUT, "SPLIT-DENSE-BOARD.jpg"))

    # 4) grade reference board: 3 amber + 3 cool = 6 cells
    g = []
    for i, t in enumerate(AMBER):
        g.append(grab(t, "g_amber_%d.jpg" % i))
    for i, t in enumerate(COOL):
        g.append(grab(t, "g_cool_%d.jpg" % i))
    stack(g, 3, os.path.join(OUT, "GRADE-DUAL-BOARD.jpg"))
    print("boards written to", OUT)


if __name__ == "__main__":
    main()