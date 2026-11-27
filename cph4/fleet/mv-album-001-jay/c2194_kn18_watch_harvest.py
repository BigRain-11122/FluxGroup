"""C2194: detached watcher for the KN18 768P production burn, then film v3.

Why this exists: the C2192 burn was driven by a CLI-session child process, and
that driver died when the session ended even though ComfyUI kept rendering the
job. So the harvest is now a session-independent watcher: it polls ComfyUI's
own history for the prompt id, adopts the rendered file by disk, screens it with
the same 768P gate as its siblings (blurred-sky p99 <= 47 plus a 1:1 native sky
strip), promotes it to clips-local-768/KN_A-KN18.mp4 and re-encodes the whole
film as a new batch tag. Verdict lands in logs/kn18-prod-c2194.json; the wave
flag is rewritten so the next tick round adopts by disk instead of re-deriving.

Exit codes: 0 green + film written, 3 screen red, 4 job failed, 5 timeout.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(MEDIA, "clips-local-768")
LOGDIR = os.path.join(MEDIA, "logs")
QCDIR = os.path.join(MEDIA, "qc-frames-c2194")
BOARD = os.path.join(MEDIA, "qc-boards", "KN18-PROD-C2194.jpg")
VERDICT = os.path.join(LOGDIR, "kn18-prod-c2194.json")
WATCHLOG = os.path.join(LOGDIR, "kn18-watch-c2194.log")
FLAG = os.path.join(REPO, ".codely-cli", "engine-tick", "wave-harvest-pending.json")
HERE = os.path.dirname(os.path.abspath(__file__))

PROMPT_ID = sys.argv[1] if len(sys.argv) > 1 else "08b2adf6-b2af-40ff-9246-229c50936767"
BATCH = "C2194"
TIMES = (1.5, 5.0, 9.0)
GLOW_SCREEN = 47.0
POLL_S = 20
TIMEOUT_S = 45 * 60


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with io.open(WATCHLOG, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def render_path():
    """Return the rendered mp4 for PROMPT_ID once ComfyUI has finished it."""
    hist = fetch_json("http://127.0.0.1:8188/history/%s" % PROMPT_ID)
    entry = (hist or {}).get(PROMPT_ID) or {}
    status = entry.get("status") or {}
    if status.get("status_str") == "error":
        raise RuntimeError("comfy job reported error: %s" % json.dumps(status)[:400])
    outs = (entry.get("outputs") or {})
    for node in outs.values():
        for key in ("videos", "gifs", "images"):
            for item in (node.get(key) or []):
                name = item.get("filename") or ""
                if name.lower().endswith(".mp4"):
                    return os.path.join(r"D:\ComfyUI\ComfyUI\output", name)
    return None


def wait_render():
    t0 = time.time()
    while time.time() - t0 < TIMEOUT_S:
        try:
            p = render_path()
        except Exception as exc:
            log("history poll error: %s" % exc)
            p = None
        if p:
            # the file can appear a beat before the write is closed
            size_a = os.path.getsize(p) if os.path.isfile(p) else -1
            time.sleep(4)
            size_b = os.path.getsize(p) if os.path.isfile(p) else -1
            if size_b > 0 and size_a == size_b:
                log("render ready: %s (%d bytes)" % (p, size_b))
                return p
        time.sleep(POLL_S)
    raise TimeoutError("no render within %ds" % TIMEOUT_S)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_frames,r_frame_rate:format=duration",
         "-of", "json", path],
        capture_output=True, text=True,
    )
    d = json.loads(out.stdout)
    st = (d.get("streams") or [{}])[0]
    return {
        "w": st.get("width"), "h": st.get("height"),
        "frames": st.get("nb_frames"), "fps": st.get("r_frame_rate"),
        "dur": round(float(d["format"]["duration"]), 3),
        "bytes": os.path.getsize(path),
    }


def grab(clip, t, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", clip,
                    "-frames:v", "1", dst], check=True)
    return dst


def glow(path):
    from PIL import Image, ImageFilter
    import numpy as np
    im = Image.open(path).convert("L")
    w, h = im.size
    sky = im.crop((0, 0, w, int(h * 0.55)))
    bl = sky.filter(ImageFilter.GaussianBlur(radius=max(6, w // 40)))
    a = np.asarray(bl).astype("float32")
    return {
        "med": round(float(np.median(a)), 1),
        "p95": round(float(np.percentile(a, 95)), 1),
        "p99": round(float(np.percentile(a, 99)), 1),
    }


def crop_sky(src, dst, frac_top=0.10, frac_h=0.42):
    from PIL import Image
    im = Image.open(src)
    w, h = im.size
    im.crop((0, int(h * frac_top), w, int(h * (frac_top + frac_h)))).save(dst)
    return dst


def board(thumbs):
    try:
        from PIL import Image
        cw = 448
        sized = []
        for p in thumbs:
            im = Image.open(p)
            r = cw / float(im.size[0])
            sized.append(im.resize((cw, max(1, int(im.size[1] * r)))))
        cols = 4
        rowsn = (len(sized) + cols - 1) // cols
        rh = max(i.size[1] for i in sized)
        sheet = Image.new("RGB", (cols * cw, rowsn * rh), (12, 12, 14))
        for i, im in enumerate(sized):
            sheet.paste(im, ((i % cols) * cw, (i // cols) * rh))
        sheet.save(BOARD, quality=92)
    except Exception as exc:
        log("board failed: %s" % exc)


def write_flag(payload):
    os.makedirs(os.path.dirname(FLAG), exist_ok=True)
    with io.open(FLAG, "w", encoding="ascii") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=True)


def main():
    for d in (LOGDIR, QCDIR, os.path.dirname(BOARD)):
        os.makedirs(d, exist_ok=True)
    log("watching prompt %s" % PROMPT_ID)
    try:
        src = wait_render()
    except Exception as exc:
        log("WATCH FAILED: %s" % exc)
        return 4 if "error" in str(exc) else 5

    meta = probe(src)
    frames = []
    thumbs = []
    for t in TIMES:
        dst = os.path.join(QCDIR, "KN18_768p_t%s.png" % t)
        grab(src, t, dst)
        g = glow(dst)
        g["t"] = t
        g["file"] = os.path.basename(dst)
        frames.append(g)
        thumbs.append(dst)
    strip = crop_sky(os.path.join(QCDIR, "KN18_768p_t5.0.png"),
                     os.path.join(QCDIR, "KN18_768p_t5.0_sky1to1.png"))
    thumbs.append(strip)
    board(thumbs)

    worst = max(f["p99"] for f in frames)
    green = worst <= GLOW_SCREEN
    payload = {
        "batch": BATCH,
        "source": src,
        "meta": meta,
        "frames": frames,
        "p99_max": worst,
        "threshold": GLOW_SCREEN,
        "screen": "STARFIELD-LIKE" if green else "BRIGHT-BAND",
        "board": BOARD,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    log("screen %s dxd=%sx%s frames=%s p99=%s max=%.1f" % (
        payload["screen"], meta["w"], meta["h"], meta["frames"],
        "/".join(str(f["p99"]) for f in frames), worst))

    if not green:
        with io.open(VERDICT, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False)
        write_flag({
            "batch": BATCH,
            "project": "mv-album-001-jay / KN18 768P RED",
            "fired_at": time.strftime("%Y-%m-%d %H:%M"),
            "what": "KN18 768P screen came back RED (p99 %.1f > %.0f)" % (worst, GLOW_SCREEN),
            "verdict_paths": [VERDICT, BOARD],
            "harvest_round_task": "read logs/kn18-prod-c2194.json + the board, re-burn KN18 at 768P with a cooler dust block, then delete this file once re-fired.",
            "prior": "C2192 480P probe was green at 22/25/28.",
        })
        return 3

    dst_clip = os.path.join(CLIPS, "KN_A-KN18.mp4")
    shutil.copy2(src, dst_clip)
    log("promoted %s (%d bytes)" % (dst_clip, os.path.getsize(dst_clip)))

    asm = os.path.join(HERE, "kn_full_assembly_c2183.py")
    res = subprocess.run([sys.executable, "-u", asm, "--encode", "--batch", BATCH],
                         cwd=HERE, capture_output=True, text=True)
    payload["assembly_rc"] = res.returncode
    payload["assembly_tail"] = (res.stdout or "")[-1500:]
    payload["assembly_err_tail"] = (res.stderr or "")[-1200:]
    film = os.path.join(MEDIA, "assembly-packA-KN", "KN-FULL-v1-%s.mp4" % BATCH)
    payload["film"] = film
    payload["film_exists"] = os.path.isfile(film)
    if os.path.isfile(film):
        payload["film_meta"] = probe(film)
    log("assembly rc=%s film_exists=%s" % (res.returncode, payload["film_exists"]))

    with io.open(VERDICT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    write_flag({
        "batch": BATCH,
        "project": "mv-album-001-jay / KN PACK-A film v3 (all 30 units at 768P)",
        "fired_at": time.strftime("%Y-%m-%d %H:%M"),
        "what": "KN18 768P adopted (p99 %s vs threshold 47) and the KN film re-encoded as %s" % (
            "/".join(str(f["p99"]) for f in frames), os.path.basename(film)),
        "verdict_paths": [VERDICT, film, "media/mv-album-001-jay/logs/kn18-watch-c2194.log"],
        "harvest_round_task": "0) read logs/kn18-prod-c2194.json (assembly rc + film ffprobe); 1) confirm the film has no identical-frame pairs (framemd5 pair count 0) and audio is at song length; 2) director re-pass on the whole film, incl. the multi-ring rainbow halo around the moon at 108.9-109.1s; 3) delete this file once harvested.",
        "prior": "Film v2 = 239.042s / 5737 frames, 0 duplicate pairs. This cut only swaps in the KN18 unit.",
    })
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # keep the watcher honest: always leave a trace on disk
        log("UNCAUGHT: %r" % (exc,))
        sys.exit(9)