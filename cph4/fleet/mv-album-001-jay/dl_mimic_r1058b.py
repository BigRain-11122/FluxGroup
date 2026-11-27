# -*- coding: ascii -*-
# dl_mimic_r1058b.py - corrected MimicMotion fetch (bm-c r1058).
# Fixes vs dl_mvtools_r1058.py: correct weight filename MimicMotion_1-1.pth
# (repo Tencent/MimicMotion), clone into a clean dir (pre-created empty
# weights/ dir blocked git clone), DWPose onnx pair for pose extraction.
# Layout per official README:
#   MimicMotion/models/MimicMotion_1-1.pth
#   MimicMotion/models/DWPose/{dw-ll_ucoco_384.onnx, yolox_l.onnx}

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request

BASE = r"K:\Fluxgroup\FluxGroup\media\mvtools"
REPO = os.path.join(BASE, "MimicMotion")
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
LOGPATH = os.path.join(LOGDIR, "dl_mimic_r1058b.log")

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
                    % (os.path.basename(dest), have // 1048576,
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
                        if got - last >= 200 * 1048576:
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
    log("MIMIC-B-START")
    # 1) clean-room clone: remove the stub dir blocking git clone (only if it
    #    contains nothing but an empty weights dir - abort otherwise)
    if not os.path.exists(os.path.join(REPO, ".git")):
        if os.path.exists(REPO):
            entries = []
            for root, dirs, files in os.walk(REPO):
                entries.extend(dirs)
                entries.extend(files)
            if entries == ["weights"] and not os.listdir(os.path.join(REPO, "weights")):
                shutil.rmtree(REPO)
                log("CLONE-PREP removed empty stub dir")
            else:
                log("CLONE-ABORT %s not the expected empty stub: %s" % (REPO, entries))
                return
        try:
            r = subprocess.run(
                ["git", "clone", "--depth", "1",
                 "https://gh-proxy.com/https://github.com/Tencent/MimicMotion.git",
                 REPO], capture_output=True, text=True, timeout=1800)
            log("CLONE rc=%s" % r.returncode)
            if r.returncode != 0:
                log("CLONE-ERR %s" % (r.stderr or "").strip()[:300])
                return
        except Exception as e:
            log("CLONE-EXC %s" % str(e)[:160])
            return
    else:
        log("CLONE-SKIP repo exists")
    # 2) log the repo's environment/requirements for the deps install step
    for fname in ["environment.yaml", "requirements.txt", "README.md",
                  "configs/test.yaml"]:
        p = os.path.join(REPO, fname)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    txt = f.read()
                log("REPO-FILE %s (%dB)" % (fname, len(txt)))
                for line in txt.splitlines()[:80]:
                    log("  | " + line[:160])
            except Exception as e:
                log("REPO-READ-ERR %s %s" % (fname, str(e)[:120]))
        else:
            log("REPO-MISSING %s" % fname)
    # 3) weights
    dl("https://hf-mirror.com/Tencent/MimicMotion/resolve/main/MimicMotion_1-1.pth",
       os.path.join(REPO, "models", "MimicMotion_1-1.pth"), log)
    dl("https://hf-mirror.com/yzd-v/DWPose/resolve/main/dw-ll_ucoco_384.onnx",
       os.path.join(REPO, "models", "DWPose", "dw-ll_ucoco_384.onnx"), log)
    dl("https://hf-mirror.com/yzd-v/DWPose/resolve/main/yolox_l.onnx",
       os.path.join(REPO, "models", "DWPose", "yolox_l.onnx"), log)
    log("MIMIC-B-DONE")


if __name__ == "__main__":
    main()
