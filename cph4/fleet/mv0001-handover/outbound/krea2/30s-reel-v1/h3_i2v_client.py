# -*- coding: utf-8 -*-
# h3_i2v_client.py - MiniMax-H3 local I2V (first-frame) client for the 30s test reel.
# Base workflow: cph4/fleet/h3-local-test/h3_t2v_local_480p.json (t2v) patched to i2v:
#   + node 16 LoadImage -> node 6 MiniMaxH3ImageToVideo.first_frame
#   + audio chain stripped per CEO audio-track ban (VAEDecodeAudio removed; CreateVideo video-only)
# Prompts assembled via prompt_lexicon build_h3_i2va (official I2VA aligned first line).
# FIFO discipline: never touches other windows' queued items.
import argparse, json, os, shutil, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma")
from prompt_lexicon import (ID_M_2001_BONE, ID_F_VVR, FACE_M_2001, FACE_F_2001, build_h3_i2va, lint)

SERVER = "http://127.0.0.1:8188"
WF_PATH = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\h3-local-test\h3_t2v_local_480p.json"
COMFY_OUTPUT = r"C:\Users\sjs20\comfyui-krea\ComfyUI_windows_portable\ComfyUI\output\h3_local_test"


def http_json(url, payload=None, timeout=30):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def upload_image(path):
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----i2v" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)


def build_wf(image_name, prompt_text, seed, length=124, width=864, height=480):
    with open(WF_PATH, "r", encoding="utf-8") as f:
        wf = json.load(f)
    wf["16"] = {"class_type": "LoadImage", "inputs": {"image": image_name}}
    n6 = wf["6"]["inputs"]
    n6["first_frame"] = ["16", 0]
    n6["prompt"] = prompt_text
    n6["length"] = length
    n6["width"] = width
    n6["height"] = height
    wf["10"]["inputs"]["noise_seed"] = seed
    # strip audio chain (CEO ban): drop VAEDecodeAudio node and its links
    for nid in ("13",):
        wf.pop(nid, None)
    cv = wf["14"]["inputs"]
    for k in list(cv.keys()):
        if isinstance(cv[k], list) and cv[k] and cv[k][0] == "13":
            del cv[k]
    return wf


def run_shot(tag, frame_path, prompt_text, seed, out_dir, length=124):
    img = upload_image(frame_path)
    wf = build_wf(img, prompt_text, seed, length=length)
    hits = lint(prompt_text, mode="video")
    print("[%s] lint=%s" % (tag, hits or "GREEN"), flush=True)
    pid = http_json(SERVER + "/prompt", {"prompt": wf, "client_id": "bma-30s-reel"})["prompt_id"]
    print("[%s] SUBMITTED %s (frame=%s)" % (tag, pid, img), flush=True)
    t0 = time.time()
    while time.time() - t0 < 2400:
        time.sleep(10)
        try:
            hist = http_json(SERVER + "/history/" + pid, timeout=15)
        except urllib.error.URLError:
            continue
        e = hist.get(pid)
        if e is None:
            print("[%s] %4ds running..." % (tag, time.time() - t0), flush=True)
            continue
        if e.get("status", {}).get("status_str") == "error":
            print("[%s] ERROR %s" % (tag, json.dumps(e["status"].get("messages", []))[:400]), flush=True)
            return None
        for nid, out in e["outputs"].items():
            for vid in out.get("gifs", []) or out.get("videos", []) or out.get("images", []):
                src = os.path.join(COMFY_OUTPUT, vid["filename"])
                if not os.path.exists(src):
                    url = SERVER + "/view?filename=%s&subfolder=%s&type=%s" % (
                        vid["filename"], vid.get("subfolder", ""), vid.get("type", "output"))
                    src = None
                    data = urllib.request.urlopen(url, timeout=180).read()
                    dst0 = os.path.join(out_dir, "tmp_" + vid["filename"])
                    open(dst0, "wb").write(data)
                    src = dst0
                dst = os.path.join(out_dir, tag + ".mp4")
                shutil.copyfile(src, dst)
                print("[%s] SAVED %s (%.0fs)" % (tag, dst, time.time() - t0), flush=True)
                return dst
        return None
    print("[%s] TIMEOUT" % tag, flush=True)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\reel-h3")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    # shot prompts: official I2VA structure via lexicon (zero negatives, era-correct)
    P_tablet = build_h3_i2va(
        shot="ecu", angle="eye", move="static",
        id_block=ID_M_2001_BONE,
        action="a hand presses a reed stylus into the wet clay tablet, the flame of the oil lamp flickering gently",
        scene="tablet", light="flame", grade="mono", texture="film_night",
        seconds=5, soundscape="quiet night room tone with faint flame crackle and stylus scraping clay",
        music="N/A (song laid in post)")
    P_goddess = build_h3_i2va(
        shot="med", angle="eye", move="pushin",
        id_block=ID_F_VVR,
        action="she stands half-materialized in the torchlight, her hair and gown barely moving as the light breathes",
        scene="hall", light="godray", grade="bluefire", texture="mist",
        seconds=5, soundscape="deep hall ambience with a faint air shimmer",
        music="N/A (song laid in post)")

    frames = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\quick-reel"
    run_shot("shot1_tablet", os.path.join(frames, "QR_S1_tablet.png"), P_tablet, 7801, args.out)
    run_shot("shot4_goddess", os.path.join(frames, "QR_S3_goddess.png"), P_goddess, 7804, args.out)
    print("H3 I2V REEL PART DONE", flush=True)


if __name__ == "__main__":
    main()
