# -*- coding: utf-8 -*-
"""w2_kf_batch.py - KF batch client for the W2 songs (龙卷风 / 简单爱).

Reuses kf_batch_v21's ComfyUI graph + SKIP semantics so the two new shot
modules need no glue of their own. Armed but not fired: the KF-PACK-A packs
are still awaiting the layer-3 director sign (L2 verdicts say 禁烧制).

Usage:
    python w2_kf_batch.py --song lj --dry-run      # list jobs, no GPU
    python w2_kf_batch.py --song jd --only T01,T03 # burn a subset
    python w2_kf_batch.py --song lj                # burn all missing frames
"""
import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kf_batch_v21 as KB

SERVER = "http://127.0.0.1:8188"

SONGS = {
    "lj": ("龙卷风-shots-v2.py", "LJ"),
    "jd": ("简单爱-shots-v2.py", "JD"),
}
OUT_DIR = KB.REPO_MEDIA


def load_shots(fname):
    path = os.path.join(HERE, fname)
    spec = importlib.util.spec_from_file_location("w2_" + os.path.splitext(fname)[0].replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_jobs(mod):
    jobs = {}
    for t in getattr(mod, "NEW"):
        sid, prompt = t[0], t[5]
        jobs[sid] = prompt
    return jobs


def burn(prompt, seed, use_jman, strength, dst):
    """Submit one KF job and poll it; returns True when the PNG lands."""
    payload = {"prompt": KB.graph(prompt, seed, use_jman, strength),
               "client_id": str(uuid.uuid4())}
    req = urllib.request.Request(SERVER + "/prompt", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req, timeout=120).read())["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(3)
        try:
            h = json.loads(urllib.request.urlopen(SERVER + "/history/" + pid, timeout=30).read())
        except Exception:
            continue
        if pid not in h:
            continue
        for _, out in h[pid]["outputs"].items():
            for img in out.get("images", []):
                data = urllib.request.urlopen(
                    "%s/view?filename=%s&subfolder=%s&type=%s" % (
                        SERVER, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                    timeout=120).read()
                open(dst, "wb").write(data)
                return True
        return False
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--song", required=True, choices=sorted(SONGS))
    ap.add_argument("--only", default="")
    ap.add_argument("--strength", type=float, default=0.8)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    fname, tag = SONGS[a.song]
    mod = load_shots(fname)
    jobs = build_jobs(mod)
    order = [t[0] for t in getattr(mod, "NEW")]
    queue = [x.strip() for x in a.only.split(",") if x.strip()] if a.only else order
    unknown = [q for q in queue if q not in jobs]
    if unknown:
        sys.exit("unknown shot ids: %s" % unknown)

    os.makedirs(OUT_DIR, exist_ok=True)
    todo = []
    for sid in queue:
        dst = os.path.join(OUT_DIR, "%s_%s.png" % (tag, sid))
        if os.path.isfile(dst) and os.path.getsize(dst) > 100000:
            print("SKIP %s (exists %dKB)" % (sid, os.path.getsize(dst) // 1024))
            continue
        todo.append(sid)

    print("song=%s jobs=%d queued=%d missing=%d" % (a.song, len(jobs), len(queue), len(todo)))
    if a.dry_run:
        for sid in todo:
            print("  WOULD-BURN %s_%s.png  %d chars" % (tag, sid, len(jobs[sid])))
        print("DRY-RUN OK (no GPU touched)")
        return 0

    ok = fail = 0
    for i, sid in enumerate(todo, 1):
        dst = os.path.join(OUT_DIR, "%s_%s.png" % (tag, sid))
        seed = 410000 + order.index(sid)
        prompt = jobs[sid]
        use_jman = "jman" in prompt
        good = burn(prompt, seed, use_jman, a.strength, dst)
        ok += 1 if good else 0
        fail += 0 if good else 1
        print("[%d/%d] %s %s" % (i, len(todo), sid, "OK" if good else "FAIL"), flush=True)
    print("W2-KF DONE ok=%d fail=%d -> %s" % (ok, fail, OUT_DIR))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())