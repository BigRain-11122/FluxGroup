# -*- coding: utf-8 -*-
"""mv_kf_batch.py - batch Krea2 keyframe generation with the preflight gate in the loop.

Reads a prompts JSON produced by mv_emit_prompts.py:
  [{"id": "...", "prompt": "...", "scene": "...", "light": "...", "shot": "...",
    "angle": "...", "grade": "...", "texture": "..."}]

Every shot must pass Tools/preflight_gate.guard() before it is submitted. Gate ① (source-frame
sign-off) does not apply to text-to-image KFs, so it is passed explicitly with a note; the
token / negative-word / scene-anchor checks are enforced as written.

Usage:
  py mv_kf_batch.py --prompts prompts.json --out D:\\FluxGroup\\media\\mv-test\\xingqing
                     [--only KN01,KN02] [--limit 5] [--unet ...] [--clip ...]
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preflight_gate as G  # noqa: E402


def graph(prompt, seed, unet, clip, w, h):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": unet, "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": clip, "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
            "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0], "negative": ["6", 0],
            "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "mv_kf"}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20260101)
    ap.add_argument("--unet", default="krea2_turbo_int8_convrot.safetensors")
    ap.add_argument("--clip", default="qwen3vl_4b_fp8_scaled.safetensors")
    ap.add_argument("--width", type=int, default=1344)
    ap.add_argument("--height", type=int, default=768)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    gate_log = os.path.join(a.out, "_preflight.jsonl")
    rows = json.load(open(a.prompts, encoding="utf-8"))
    only = set(x.strip() for x in a.only.split(",") if x.strip())

    def post(path, payload):
        req = urllib.request.Request(a.server + path, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=120).read())

    def get(path):
        return json.loads(urllib.request.urlopen(a.server + path, timeout=30).read())

    get("/system_stats")

    done = skipped = failed = 0
    for i, r in enumerate(rows):
        sid = r["id"]
        if only and sid not in only:
            continue
        if a.limit and done >= a.limit:
            break
        dst = os.path.join(a.out, sid + ".png")
        if os.path.isfile(dst) and os.path.getsize(dst) > 50000:
            skipped += 1
            print("SKIP %s (exists)" % sid, flush=True)
            continue

        tokens = {k: r.get(k, "") for k in
                  ("shot", "angle", "move", "grade", "texture", "scene", "light")}
        fails = G.guard(shot_id=sid, prompt_text=r["prompt"], tokens=tokens,
                        kf_verified=True,
                        kf_note="T2I KF: no source frame, gate(1) N/A",
                        kinds=r.get("kinds") or [])
        with open(gate_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": sid, "fails": fails}, ensure_ascii=False) + "\n")
        if fails:
            failed += 1
            print("GATE-FAIL %s :: %s" % (sid, " ; ".join(fails)), flush=True)
            continue

        pid = post("/prompt", {"prompt": graph(r["prompt"], a.seed + i, a.unet, a.clip,
                                               a.width, a.height),
                               "client_id": str(uuid.uuid4())})["prompt_id"]
        t0 = time.time()
        ok = False
        while time.time() - t0 < 600:
            time.sleep(2)
            h = get("/history/" + pid)
            if pid in h:
                st = h[pid].get("status", {})
                if st.get("status_str") == "error":
                    print("ERROR %s :: %s" % (sid, json.dumps(st)[:400]), flush=True)
                    break
                for out in h[pid]["outputs"].values():
                    for img in out.get("images", []):
                        url = "%s/view?filename=%s&subfolder=%s&type=%s" % (
                            a.server, img["filename"], img.get("subfolder", ""),
                            img.get("type", "output"))
                        data = urllib.request.urlopen(url, timeout=120).read()
                        with open(dst, "wb") as f:
                            f.write(data)
                        print("OK %s (%.1fs)" % (sid, time.time() - t0), flush=True)
                        ok = True
                        G.note_burn(sid)
                break
        if ok:
            done += 1
        else:
            failed += 1

    print("SUMMARY done=%d skipped=%d failed=%d out=%s" % (done, skipped, failed, a.out))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())