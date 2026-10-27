"""C2187 harvest watcher: wait for the KN galaxy chain to finish, then prepare the verdict pack.

Fired detached (pythonw) so the harvest does not need a live CLI window: the chain
writes its clips whenever the GPU finishes, and this watcher turns them into the
same evidence the manual harvest round used to produce by hand - QC frames, the
framing drift gate, and a low-frequency glow measurement per frame.

The glow number is a screening aid only (calibrated on the C2186 pair: known-good
KN17 frames peak at 63/66/76, known-bad KN18 frames at 88/95/102 on the 95th-99th
percentile of the blurred sky luminance). The director eye pass stays the verdict.

Nothing here touches clips-local-768 or the assembly: mapping + re-assembly stay in
the harvest round, after the eye check.
"""

import io
import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
CHAIN_LOG = os.path.join(MEDIA, "logs", "kn-galaxy-c2187.log")
HARVEST_LOG = os.path.join(MEDIA, "logs", "kn-harvest-c2187.log")
QCDIR = os.path.join(MEDIA, "qc-frames-c2187")
CLIP_768 = os.path.join(MEDIA, "clips-local-768", "KN_G3-KN17.mp4")
CLIP_480 = os.path.join(MEDIA, "clips-verify-480", "KN_G3-KN18.mp4")
GATE = os.path.join(PKG, "kn_framing_drift_gate.py")
RECEIPT = os.path.join(PKG, "HARVEST-KN-GALAXY-c2187-AUTO.md")
FLAG = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\wave-harvest-pending.json"
BATCH = "C2187"
TIMES = (1.5, 5.0, 9.0)
GLOW_SCREEN = 82.0  # blurred-sky p99 above this reads as a bright diffuse band
POLL_S = 30
TIMEOUT_S = 7200


def log(line):
    with io.open(HARVEST_LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), line))


def chain_state():
    if not os.path.isfile(CHAIN_LOG):
        return "absent"
    with io.open(CHAIN_LOG, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    if "=== C2187 CHAIN DONE" in txt:
        return "done"
    if "=== C2187 CHAIN ABORT" in txt:
        return "abort"
    return "running"


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_frames,r_frame_rate:format=duration",
         "-of", "json", path],
        capture_output=True, text=True,
    )
    try:
        d = json.loads(out.stdout)
        st = (d.get("streams") or [{}])[0]
        return {
            "w": st.get("width"), "h": st.get("height"),
            "frames": st.get("nb_frames"), "fps": st.get("r_frame_rate"),
            "dur": round(float(d["format"]["duration"]), 3),
            "bytes": os.path.getsize(path),
        }
    except Exception:
        return {"w": None, "h": None, "frames": None, "fps": None, "dur": None,
                "bytes": os.path.getsize(path) if os.path.isfile(path) else 0}


def grab(clip, t, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", clip,
                    "-frames:v", "1", dst], check=True)
    return dst


def glow(path):
    """Low-frequency light field of the sky region (upper 55% of frame)."""
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


def run_gate(scan_dir, glob_pat, out_json):
    cmd = [sys.executable, GATE, "--scan-dir", scan_dir, "--glob", glob_pat,
           "--batch", BATCH, "--out", out_json]
    res = subprocess.run(cmd, capture_output=True, text=True)
    tail = (res.stdout or "").strip().splitlines()[-1:] or [""]
    return {"rc": res.returncode, "tail": tail[0]}


def main():
    log("watcher start, chain state=%s" % chain_state())
    started = time.time()
    while True:
        state = chain_state()
        if state in ("done", "abort"):
            break
        if time.time() - started > TIMEOUT_S:
            log("timeout after %ds while chain state=%s" % (TIMEOUT_S, state))
            return 3
        time.sleep(POLL_S)

    log("chain finished state=%s" % state)
    if state == "abort":
        log("chain aborted - nothing to harvest")
        return 4

    os.makedirs(QCDIR, exist_ok=True)
    clips = [("prod-768", CLIP_768), ("probe-480", CLIP_480)]
    rows = []
    for tag, clip in clips:
        if not os.path.isfile(clip) or os.path.getsize(clip) < 100 * 1024:
            log("MISSING/TOO SMALL %s %s" % (tag, clip))
            rows.append({"tag": tag, "clip": clip, "missing": True})
            continue
        meta = probe(clip)
        frames = []
        for t in TIMES:
            dst = os.path.join(QCDIR, "%s_%s_t%s.png" % (tag, os.path.basename(clip)[:-4], t))
            grab(clip, t, dst)
            g = glow(dst)
            g["t"] = t
            g["file"] = os.path.basename(dst)
            frames.append(g)
        worst = max(f["p99"] for f in frames)
        rows.append({
            "tag": tag, "clip": os.path.basename(clip), "path": clip,
            "meta": meta, "frames": frames, "p99_max": worst,
            "screen": "STARFIELD-LIKE" if worst <= GLOW_SCREEN else "BRIGHT-BAND",
            "screen_threshold": GLOW_SCREEN,
        })
        log("%s %s %s p99_max=%.1f -> %s" % (tag, os.path.basename(clip),
                                             meta, worst, rows[-1]["screen"]))

    gate768 = run_gate(os.path.dirname(CLIP_768), "KN_G3-KN17.mp4",
                       os.path.join(MEDIA, "logs", "kn-framing-c2187-768.json"))
    gate480 = run_gate(os.path.dirname(CLIP_480), "KN_G3-KN18.mp4",
                       os.path.join(MEDIA, "logs", "kn-framing-c2187-480.json"))
    log("gate768 %s" % gate768)
    log("gate480 %s" % gate480)

    payload = {"batch": BATCH, "chain": state, "clips": rows,
               "gates": {"prod-768": gate768, "probe-480": gate480},
               "harvested_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with io.open(os.path.join(MEDIA, "logs", "kn-harvest-c2187.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    lines = ["# Harvest (auto) - KN galaxy C2187", "",
             "- chain state: `%s`" % state,
             "- harvested: %s" % payload["harvested_at"],
             "- glow screening aid only; the director eye pass is still the verdict",
             "- screening line: blurred-sky p99 <= %.0f reads as discrete points, above it reads as a bright diffuse band" % GLOW_SCREEN,
             "- calibrated on C2186 pair: KN17 63/66/76 (PASS), KN18 88/95/102 (FAIL)", ""]
    for r in rows:
        if r.get("missing"):
            lines.append("## %s MISSING" % r["tag"])
            lines.append("")
            continue
        m = r["meta"]
        lines.append("## %s - %s" % (r["tag"], r["clip"]))
        lines.append("")
        lines.append("- %sx%s, %s frames, %s fps, %.2fs, %.1fMB" % (
            m["w"], m["h"], m["frames"], m["fps"], m["dur"], m["bytes"] / 1048576.0))
        lines.append("- screening: **%s** (p99_max %.1f)" % (r["screen"], r["p99_max"]))
        for f in r["frames"]:
            lines.append("  - t=%ss med=%s p95=%s p99=%s (%s)" % (
                f["t"], f["med"], f["p95"], f["p99"], f["file"]))
        lines.append("")
    lines.append("## framing drift gate")
    lines.append("")
    lines.append("- 768: rc=%s `%s`" % (gate768["rc"], gate768["tail"]))
    lines.append("- 480: rc=%s `%s`" % (gate480["rc"], gate480["tail"]))
    lines.append("")
    lines.append("## next (harvest round)")
    lines.append("")
    lines.append("1. Eye-check the 3 frames per clip in `media/mv-album-001-jay/qc-frames-c2187/`.")
    lines.append("2. Both green -> copy into `clips-local-768/` as `KN_A-KN17.mp4` / `KN_A-KN18.mp4`, rerun `kn_full_assembly_c2183.py --encode`.")
    lines.append("3. Director re-pass on film v2, then delete the wave flag.")
    with io.open(RECEIPT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    log("receipt written %s" % RECEIPT)

    if os.path.isfile(FLAG):
        with io.open(FLAG, encoding="utf-8") as fh:
            flag = json.load(fh)
        flag["fired_at"] = payload["harvested_at"]
        flag["what"] = ("C2187 chain finished; QC frames + framing gate + glow screening "
                        "already produced by c2187_kn_harvest_watch.py")
        flag["verdict_paths"] = [RECEIPT,
                                 os.path.join(MEDIA, "logs", "kn-harvest-c2187.json"),
                                 QCDIR]
        flag["harvest_round_task"] = (
            "1) eye-check qc-frames-c2187 frames against the band criteria "
            "(same brightness as sky, pin-point specks, soft open edges, no amber cloud form); "
            "2) both green -> map KN_G3-KN17 -> KN_A-KN17.mp4, KN_G3-KN18 -> KN_A-KN18.mp4, "
            "rerun kn_full_assembly_c2183.py --encode -> film v2; 3) director re-pass; "
            "4) delete this flag file.")
        with io.open(FLAG, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(flag, fh, indent=1, ensure_ascii=False)
        log("wave flag refreshed with prepared verdict pack")

    return 0


if __name__ == "__main__":
    sys.exit(main())