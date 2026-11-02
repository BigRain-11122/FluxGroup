#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H3 local t2v smoke-test launcher (O-20261009-1746, bm-a lane).

Submits the API-format workflow h3_t2v_local_480p.json to the local ComfyUI
server (shared 8188, FIFO -- never touches other windows' queued items),
polls until done, then copies the MP4 into cph4 fleet delivery outbound/local/.

Usage (portable python or any py3):
  python h3_t2v_client.py [--seed 20261009] [--server http://127.0.0.1:8188]
                          [--wait 3600] [--dry-run]

Notes:
- Model set = 8G quant recipe (int4 convrot DiT + nvfp4 TE + fp16 video VAE
  + fp32 audio VAE + 4-step turbo LoRA @768p class). 864x480 / 124 frames
  (= ~5s @24fps, 17k+5 grid) / 4 steps.
- First run pays model-load (~19.5GB dynamic offload on 12GB card).
- Print output is ASCII-only (GBK console safety).
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
WF_PATH = os.path.join(HERE, "h3_t2v_local_480p.json")
OUTBOUND_LOCAL = os.path.join(HERE, "outbound", "local")
COMFY_OUTPUT = r"C:\Users\sjs20\comfyui-krea\ComfyUI_windows_portable\ComfyUI\output\h3_local_test"
CLIENT_ID = "bma-h3-local-test"
POLL_SEC = 10


def http_json(url, payload=None, timeout=30):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261009)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--wait", type=int, default=3600)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(WF_PATH, "r", encoding="utf-8") as f:
        wf = json.load(f)
    wf["10"]["inputs"]["noise_seed"] = args.seed

    if args.dry_run:
        print("DRY-RUN OK: workflow parsed, nodes=%d, seed=%d" % (len(wf), args.seed))
        return 0

    t0 = time.time()
    resp = http_json(args.server + "/prompt", {"prompt": wf, "client_id": CLIENT_ID})
    pid = resp.get("prompt_id")
    if not pid:
        print("SUBMIT FAILED: %s" % resp)
        return 2
    print("SUBMITTED prompt_id=%s seed=%d" % (pid, args.seed))
    print("QUEUE (behind any in-flight items, FIFO):")

    while True:
        time.sleep(POLL_SEC)
        try:
            hist = http_json(args.server + "/history/" + pid, timeout=15)
        except urllib.error.URLError:
            print("POLL ERR (server busy?), retrying...")
            continue
        entry = hist.get(pid)
        if entry is None:
            print("[%4ds] running..." % (time.time() - t0))
            continue
        status = entry.get("status", {})
        if not status.get("completed", False):
            print("[%4ds] not completed: %s" % (time.time() - t0, json.dumps(status)[:300]))
            return 3
        outputs = entry.get("outputs", {})
        saved = []
        for node_out in outputs.values():
            for item in (node_out.get("videos") or []):
                saved.append(item)  # dict: filename/subfolder/type
        print("DONE in %.0fs, saved=%s" % (time.time() - t0, json.dumps(saved)[:300]))
        os.makedirs(OUTBOUND_LOCAL, exist_ok=True)
        copied = []
        for item in saved:
            src = os.path.join(COMFY_OUTPUT, item.get("filename", ""))
            if os.path.isfile(src):
                dst = os.path.join(OUTBOUND_LOCAL, item.get("filename", ""))
                shutil.copy2(src, dst)
                copied.append(dst)
        for p in copied:
            print("DELIVERED: %s" % p)
        return 0 if copied else 4


if __name__ == "__main__":
    sys.exit(main())
