# -*- coding: ascii -*-
# kn21_kf_retry_c2173.py - re-author the KN21 first frame on the Krea2 lane.
#
# Why: KN21 is a dead take in two directions (see KN21-RETRY-VERDICT-c2172.md).
# With the current KF, 768P int8 collapses into glyph noise and 768P int4 drifts
# into Chinese papercraft/stained-glass/cartoon-face decoration. The KF itself
# reads as a miniature set piece, which is what pushes the 768P model to invent
# decorative props. So the fix is a new first frame with real-scene cues and no
# set-dressing vocabulary.
#
# Reuses the proven Krea2 graph from kf_batch_v21.py (its gen() is nested in main(),
# so submit/poll is written here against the same graph builder).
# Output lands in frames-retry-c2173/ - nothing canonical is overwritten.

import importlib.util
import json
import os
import time
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
KF = os.path.join(HERE, "kf_batch_v21.py")
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "media", "mv-album-001-jay",
                                   "frames-retry-c2173"))
RECEIPT = os.path.join(HERE, "KN21-KF-RETRY-c2173.json")
SERVER = "http://127.0.0.1:8188"
SEEDS = [770112, 770341, 770905]

PROMPT = (
    "35mm film still photograph. A night rooftop in 2001 Taipei: a weathered concrete "
    "parapet with flaking paint and a rusted drain pipe, a single warm-lit window set "
    "back from it, and a folded white paper plane with a small red tail marking resting "
    "on the parapet. Behind, dark water tanks and old apartment blocks dissolve into the "
    "night, a few scattered window lights. Warm 2000 Taiwanese telecine grade, warm skin "
    "tones, milky lifted blacks, visible 35mm film grain. Eye-level view, shallow depth "
    "of field, natural lens falloff. A real place, photographed at night."
)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def post(path, payload):
    req = urllib.request.Request(SERVER + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def get(path):
    return json.loads(urllib.request.urlopen(SERVER + path, timeout=30).read())


def gen(graph, prompt, seed, dst):
    pid = post("/prompt", {"prompt": graph(prompt, seed, False, 0.0),
                           "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(3)
        try:
            h = get("/history/" + pid)
        except Exception:
            continue
        if pid in h:
            for _nid, out in h[pid]["outputs"].items():
                for img in out.get("images", []):
                    data = urllib.request.urlopen(
                        "%s/view?filename=%s&subfolder=%s&type=%s" % (
                            SERVER, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                        timeout=60).read()
                    with open(dst, "wb") as f:
                        f.write(data)
                    return True
            return False
    return False


def main():
    kf = load(KF, "kf_batch_v21")
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for i, seed in enumerate(SEEDS, 1):
        dst = os.path.join(OUT, "KN21_r%d_s%d.png" % (i, seed))
        if os.path.exists(dst) and os.path.getsize(dst) > 100000:
            rows.append({"r": i, "seed": seed, "out": dst,
                         "bytes": os.path.getsize(dst), "skip": True})
            print("SKIP", dst, flush=True)
            continue
        t0 = time.time()
        ok = gen(kf.graph, PROMPT, seed, dst)
        size = os.path.getsize(dst) if os.path.exists(dst) else 0
        rows.append({"r": i, "seed": seed, "out": dst, "bytes": size,
                     "secs": round(time.time() - t0, 1), "ok": ok})
        print("KF %d seed=%d %.1fs %dB ok=%s" % (i, seed, time.time() - t0, size, ok), flush=True)
    ok_n = sum(1 for r in rows if r["bytes"] > 900000)
    payload = {
        "batch": "C2173",
        "shot": "KN21",
        "why": ("re-author the first frame: with the old KF the 768P path produced glyph noise "
                "(int8) or Chinese papercraft drift (int4)"),
        "prompt": PROMPT,
        "words": len(PROMPT.split()),
        "rows": rows,
        "ok_over_900kb": ok_n,
        "note": "candidates only; a plate is picked before any i2v burn",
    }
    with open(RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("KF-RETRY-END ok=%d n=%d" % (ok_n, len(rows)))


if __name__ == "__main__":
    main()