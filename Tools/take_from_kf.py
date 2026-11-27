# -*- coding: utf-8 -*-
"""take_from_kf.py - burn one local H3 i2v take from an arbitrary keyframe.

Generalises the v729 single-shot script so any KF can be turned into a take without
copying that file again: uploads the KF, sets the motion prompt / length / seed on the
existing local H3 workflow, waits, saves the clip.

Usage:
  py Tools/take_from_kf.py --kf <png> --out <mp4> --prompt "<motion>" [--length 39] [--seed N]
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "outbound", "krea2",
                  "30s-reel-v1", "h3_i2v_local_768p_v4.json")


def http_json(url, payload=None, timeout=60):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def upload_image(server, path):
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----take" + uuid.uuid4().hex
    body = (('--%s\r\nContent-Disposition: form-data; name="image"; filename="%s"\r\n'
             'Content-Type: image/png\r\n\r\n') % (boundary, fn)).encode() + data + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(server + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--kf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--length", type=int, default=39)
    ap.add_argument("--width", type=int, default=1344)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--budget", type=int, default=2400)
    a = ap.parse_args()

    if not os.path.isfile(a.kf):
        sys.exit("KF missing: " + a.kf)
    if os.path.isfile(a.out) and os.path.getsize(a.out) > 100000:
        print("SKIP exists ->", a.out)
        return 0
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)

    http_json(a.server + "/system_stats")
    img = upload_image(a.server, a.kf)
    seed = a.seed or (hash(os.path.basename(a.out)) & 0x7FFFFFFF)
    wf = json.load(open(WF, "r", encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = a.prompt
    n6["length"] = a.length
    n6["width"] = a.width
    n6["height"] = a.height
    wf["10"]["inputs"]["noise_seed"] = seed

    pid = http_json(a.server + "/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())})["prompt_id"]
    print("prompt_id %s seed %d kf=%s" % (pid, seed, os.path.basename(a.kf)), flush=True)
    t0 = time.time()
    while time.time() - t0 < a.budget:
        time.sleep(8)
        try:
            h = http_json(a.server + "/history/" + pid, timeout=40)
        except Exception:
            continue
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR:", json.dumps(h[pid]["status"].get("messages", []))[:400])
                return 1
            for _nid, out in h[pid]["outputs"].items():
                for v in (out.get("gifs") or out.get("videos") or out.get("images") or []):
                    url = "%s/view?filename=%s&subfolder=%s&type=%s" % (
                        a.server, v["filename"], v.get("subfolder", ""), v.get("type", "output"))
                    open(a.out, "wb").write(urllib.request.urlopen(url, timeout=300).read())
                    print("SAVED %s (%.0fs, %d bytes)" % (a.out, time.time() - t0,
                                                          os.path.getsize(a.out)), flush=True)
                    return 0
    print("TIMEOUT after %ds" % a.budget)
    return 1


if __name__ == "__main__":
    sys.exit(main())
