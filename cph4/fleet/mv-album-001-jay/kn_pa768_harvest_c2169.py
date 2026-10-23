# kn_pa768_harvest_c2169.py - KN A-pack 768P wave harvest (batch C2169).
# Zero-GPU station-3 gate. Waits for the burning 30-unit wave, then per clip:
# ffprobe, frame-hash duplicate run (the "tape repeat" defect), three native
# frame pulls, and two contact boards. Verdict JSON is machine readable so the
# next round only has to read the summary, not the pixels.
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import kn_pseudotext_probe as PTP   # C2170: subtitle-band pseudo-text gate

REPO = r"K:\Fluxgroup\FluxGroup"
MANIFEST = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "local-i2v", "run-bmc-kn-i2v.json")
OUT_DIR = os.path.join(REPO, "media", "mv-album-001-jay", "clips-local-768")
LOG = os.path.join(REPO, "media", "mv-album-001-jay", "logs", "kn_i2v_768p_wave.out.log")
EVID = os.path.join(REPO, "media", "mv-album-001-jay", "evidence-c2169")
VERDICT = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "KN-PA768-HARVEST-c2169.json")
EXPECT_RES = (1344, 768)
MIN_BYTES = 400000
MIN_FRAMES = 80
MAX_DUP_RUN_S = 0.35
WAIT_MAX = 4 * 3600
STABLE_S = 90


def logline(msg):
    print("[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    sys.stdout.flush()


def unit_ids():
    d = json.load(open(MANIFEST, encoding="utf-8"))
    return [u["id"] for u in d["units"]]


def lane_done():
    if not os.path.exists(LOG):
        return False
    tail = open(LOG, encoding="utf-8", errors="replace").read()[-4000:]
    return "ALBUM LANE DONE" in tail


def all_stable(ids):
    sizes = {}
    for _ in range(2):
        snap = {}
        for i in ids:
            p = os.path.join(OUT_DIR, i + ".mp4")
            if not os.path.exists(p):
                return False
            snap[i] = os.path.getsize(p)
        if sizes and snap == sizes:
            return True
        sizes = snap
        time.sleep(STABLE_S / 2.0)
    return False


def probe(path):
    cmd = ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
           "-show_entries", "format=duration,size", "-of", "json", path]
    d = json.loads(subprocess.check_output(cmd).decode("utf-8", "replace"))
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {
        "res": "%sx%s" % (st["width"], st["height"]),
        "fps": round(float(num) / float(den), 3),
        "frames": int(st.get("nb_read_frames") or 0),
        "duration": round(float(d["format"]["duration"]), 3),
        "bytes": int(d["format"]["size"]),
    }


def dup_run(path, fps):
    """Longest run of identical consecutive frame hashes, in seconds."""
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-an", "-f", "framemd5", "-"]
    out = subprocess.check_output(cmd).decode("utf-8", "replace")
    hashes = []
    for line in out.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 6:
            hashes.append(parts[-1])
    best, run = 0, 1
    for a, b in zip(hashes, hashes[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    return {"hash_frames": len(hashes), "max_run_frames": best,
            "max_run_s": round(best / float(fps or 24), 3)}


def pull_frames(clip, uid, info):
    rows = []
    for frac in (0.25, 0.55, 0.85):
        ts = round(info["duration"] * frac, 3)
        out = os.path.join(EVID, "%s_%05.2fs.png" % (uid, ts))
        subprocess.check_call(["ffmpeg", "-v", "error", "-ss", "%.3f" % ts, "-i", clip,
                               "-frames:v", "1", "-y", out])
        rows.append({"t": ts, "path": out, "bytes": os.path.getsize(out)})
    return rows


def board(frames, out_path, cols, title):
    from PIL import Image, ImageDraw, ImageFont
    tw, th = 424, 242
    label_h = 26
    rows = (len(frames) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * tw, rows * (th + label_h)), (18, 18, 20))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for idx, row in enumerate(frames):
        img = Image.open(row["path"]).convert("RGB").resize((tw, th), Image.LANCZOS)
        x = (idx % cols) * tw
        y = (idx // cols) * (th + label_h)
        canvas.paste(img, (x, y))
        draw.text((x + 6, y + th + 4), row["id"], fill=(235, 235, 235), font=font)
    canvas.save(out_path, quality=90)
    return {"board": out_path, "tiles": len(frames), "bytes": os.path.getsize(out_path), "title": title}


def main():
    os.makedirs(EVID, exist_ok=True)
    ids = unit_ids()
    logline("UNITS %d" % len(ids))
    t0 = time.time()
    while time.time() - t0 < WAIT_MAX:
        if lane_done() or all_stable(ids):
            break
        time.sleep(60)
    if not all(os.path.exists(os.path.join(OUT_DIR, i + ".mp4")) for i in ids):
        logline("HARVEST_INCOMPLETE after %ds - some units missing" % WAIT_MAX)
        return 2

    rows, tiles = [], []
    for uid in ids:
        clip = os.path.join(OUT_DIR, uid + ".mp4")
        info = probe(clip)
        dup = dup_run(clip, info["fps"])
        ptxt = PTP.scan(clip, step=6)
        frames = pull_frames(clip, uid, info)
        fail = []
        if (info["res"] != "%dx%d" % EXPECT_RES):
            fail.append("res=%s" % info["res"])
        if info["bytes"] < MIN_BYTES:
            fail.append("bytes=%d" % info["bytes"])
        if info["frames"] < MIN_FRAMES:
            fail.append("frames=%d" % info["frames"])
        if dup["max_run_s"] > MAX_DUP_RUN_S:
            fail.append("dup_run=%.3fs" % dup["max_run_s"])
        if ptxt["verdict"] == "SUSPECT":
            fail.append("pseudo_text cov=%.2f" % ptxt["coverage"])
        rows.append({"id": uid, "clip": clip, "probe": info, "dup": dup,
                     "pseudo_text": ptxt,
                     "frames": frames, "fail": fail, "verdict": "PASS" if not fail else "CHECK"})
        tiles.append(frames[1])
        logline("%s %s frames=%d dup_run=%.3fs ptxt=%s bytes=%d %s" % (
            uid, "PASS" if not fail else "CHECK", info["frames"], dup["max_run_s"],
            ptxt["verdict"], info["bytes"], ",".join(fail) or ""))

    half = (len(tiles) + 1) // 2
    boards = [board(tiles[:half], os.path.join(EVID, "KN-PA768-BOARD-1-c2169.jpg"), 5, "KN 768P board 1"),
              board(tiles[half:], os.path.join(EVID, "KN-PA768-BOARD-2-c2169.jpg"), 5, "KN 768P board 2")]

    ok = sum(1 for r in rows if r["verdict"] == "PASS")
    summary = {"batch": "C2169", "wave": "kn-i2v-packA-768", "units": len(rows),
               "pass": ok, "check": len(rows) - ok,
               "boards": boards, "rows": rows,
               "gate": "PASS if pass==units; CHECK rows need a native-frame read before assembly"}
    with open(VERDICT, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    logline("HARVEST-END ok=%d check=%d verdict=%s" % (ok, len(rows) - ok, VERDICT))
    return 0


if __name__ == "__main__":
    sys.exit(main())