# -*- coding: ascii -*-
# dl_svd_r1058.py - SVD img2vid-xt-1-1 fp16 base prefetch (bm-c r1058).
# Scope note: MimicMotion loads UNet weights from MimicMotion_1-1.pth itself;
# loader.py only reads SVD unet/config.json. So the fp16 unet safetensors
# (2.4GB) is NOT needed. Required set = vae fp16 + image_encoder fp16 + 4
# config files ~= 1.5GB total (2.4GB saved vs original plan).
# Layout: MimicMotion/models/svd-img2vid-xt-1-1/<hf repo structure>
# Writes .download_ok.json marker when every file passes size check.

import json
import os
import socket
import subprocess
import time
import urllib.request

BASE = r"K:\Fluxgroup\FluxGroup\media\mvtools"
REPO = os.path.join(BASE, "MimicMotion")
DEST = os.path.join(REPO, "models", "svd-img2vid-xt-1-1")
MARKER = os.path.join(DEST, ".download_ok.json")
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
LOGPATH = os.path.join(LOGDIR, "dl_svd_r1058.log")

URL_BASE = "https://hf-mirror.com/stabilityai/stable-video-diffusion-img2vid-xt-1-1/resolve/main"

FILES = [
    "unet/config.json",
    "vae/config.json",
    "vae/diffusion_pytorch_model.fp16.safetensors",
    "image_encoder/config.json",
    "image_encoder/model.fp16.safetensors",
    "scheduler/scheduler_config.json",
    "feature_extractor/preprocessor_config.json",
    "LICENSE.md",
]

socket.setdefaulttimeout(90)


class Log:
    def __init__(self, path):
        self.f = open(path, "a", encoding="ascii", errors="replace")

    def __call__(self, msg):
        line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
        try:
            print(line)
        except Exception:
            pass
        self.f.write(line + "\n")
        self.f.flush()


def dl(url, dest, log, tries=8):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(1, tries + 1):
        have = os.path.getsize(dest) if os.path.exists(dest) else 0
        headers = {"User-Agent": "Mozilla/5.0"}
        if have > 0:
            headers["Range"] = "bytes=%d-" % have
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                total = r.headers.get("Content-Length")
                crange = r.headers.get("Content-Range")
                mode = "ab"
                if have > 0 and not crange:
                    have = 0
                    mode = "wb"
                expected = have + int(total) if total else -1
                log("DL-START %s have=%dMB expected=%sMB attempt=%d"
                    % (dest.replace(DEST + os.sep, ""), have // 1048576,
                       (expected // 1048576) if expected > 0 else "?", attempt))
                t0 = time.perf_counter()
                got = 0
                last = 0
                with open(dest, mode) as f:
                    while True:
                        chunk = r.read(1048576)
                        if not chunk:
                            break
                        f.write(chunk)
                        got += len(chunk)
                        if got - last >= 100 * 1048576:
                            last = got
                            el = time.perf_counter() - t0
                            log("DL-... %s %dMB %.2fMB/s"
                                % (os.path.basename(dest), (have + got) // 1048576,
                                   got / 1048576 / max(el, 0.1)))
                size = os.path.getsize(dest)
                if expected > 0 and size != expected:
                    log("DL-PARTIAL %s size=%d expected=%d - retry"
                        % (os.path.basename(dest), size, expected))
                    time.sleep(6)
                    continue
                el = time.perf_counter() - t0
                log("DL-OK %s %dB %.2fMB/s avg"
                    % (os.path.basename(dest), size,
                       (size - have) / 1048576 / max(el, 0.1)))
                return size
        except Exception as e:
            log("DL-ERR %s attempt=%d: %s" % (os.path.basename(dest), attempt,
                                               str(e)[:160]))
            time.sleep(8)
    log("DL-FAIL %s after %d tries" % (os.path.basename(dest), tries))
    return -1


def main():
    log = Log(LOGPATH)
    log("SVD-START dest=%s" % DEST)
    sizes = {}
    ok = True
    for rel in FILES:
        url = "%s/%s" % (URL_BASE, rel)
        dest = os.path.join(DEST, *rel.split("/"))
        rc = dl(url, dest, log)
        if rc < 0:
            ok = False
        else:
            sizes[rel] = rc
    if ok:
        with open(MARKER, "w", encoding="ascii") as f:
            json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "files": sizes}, f,
                      indent=1)
        log("SVD-OK marker written, %d files" % len(sizes))
        log("SVD-DONE")
    else:
        log("SVD-DONE-WITH-FAILURES (runner may relaunch this script; resume-safe)")


if __name__ == "__main__":
    main()
