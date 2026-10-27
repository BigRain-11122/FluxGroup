# -*- coding: ascii -*-
# bmc_gfpgan_trial_r1058.py - POOL-0017 full-route tier: GFPGAN v1.4 face
# restore trial on xingqing A-batch human frames (bm-c r1058, CEO idle-fill
# order 2026-10-17). Uses the minimal basicsr shim + lazy-arch patched
# gfpgan (basicsr CUDA-ext build unavailable in this env).
# CWD is set so facexlib model_rootpath 'gfpgan/weights' resolves to the
# pre-downloaded detection/parsing weights (no runtime GitHub downloads).
# Outputs: restored frames + before/after board + tier receipt (timings,
# VRAM peaks, face counts). ASCII prints only (PS5.1 GBK law).

import json
import os
import subprocess
import sys
import time

BASE = r"K:\Fluxgroup\FluxGroup\media\mvtools\gfpgan"
os.chdir(BASE)  # facexlib model_rootpath 'gfpgan/weights' is CWD-relative
sys.path.insert(0, os.path.join(BASE, "pylibs"))

SRC = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch"
OUT = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch_s7r\gfpgan"
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
MODEL = os.path.join(BASE, "weights", "GFPGANv1.4.pth")

FRAMES = ["S5-30_s20222", "S0-03_s20027", "S1-09_s20064", "S0-06_s20048"]


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


def vram_used_mb():
    try:
        q = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL).decode("ascii").strip().splitlines()
        return int(q[0].strip())
    except Exception:
        return -1


def main():
    os.makedirs(OUT, exist_ok=True)
    log = Log(os.path.join(LOGDIR, "gfpgan_trial_r1058.log"))
    log("GFPGAN-TRIAL-START")
    import cv2  # noqa (after sys.path insert, embeded cv2)
    import torch
    from gfpgan import GFPGANer
    log("IMPORT-OK torch=%s cuda=%s" % (torch.__version__, torch.cuda.is_available()))
    t0 = time.perf_counter()
    restorer = GFPGANer(model_path=MODEL, upscale=1, arch='clean', channel_multiplier=2)
    log("MODEL-LOAD %.1fs" % (time.perf_counter() - t0))
    rows = []
    board_cells = []
    for name in FRAMES:
        src_path = os.path.join(SRC, name + ".png")
        img = cv2.imread(src_path)
        if img is None:
            log("MISS " + name)
            continue
        t1 = time.perf_counter()
        peak = vram_used_mb()
        try:
            cropped, restored, res = restorer.enhance(
                img, has_aligned=False, only_center_face=False, paste_back=True, weight=0.5)
        except Exception as e:
            log("ENHANCE-FAIL %s: %s" % (name, str(e)[:200]))
            continue
        dt = time.perf_counter() - t1
        cur = vram_used_mb()
        peak = max(peak, cur)
        n_faces = len(restored) if restored is not None else 0
        row = {"frame": name, "sec": round(dt, 2), "faces": n_faces,
               "vram_peak_mb": peak}
        if res is None or n_faces == 0:
            row["note"] = "no face detected - original kept"
            log("OK %s no-face %.2fs" % (name, dt))
            res = img
        else:
            out_path = os.path.join(OUT, name + "_gfpg.png")
            cv2.imwrite(out_path, res)
            row["out"] = os.path.basename(out_path)
            log("OK %s faces=%d %.2fs peak=%dMB" % (name, n_faces, dt, peak))
        rows.append(row)
        # board cells: orig vs restored
        from PIL import Image, ImageDraw
        orig_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res_rgb = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
        cells = []
        for tag, arr in (("orig " + name, orig_rgb), ("gfpgan v1.4", res_rgb)):
            im = Image.fromarray(arr).resize((448, 256), Image.LANCZOS)
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, 448, 16), fill=(0, 0, 0))
            d.text((4, 3), tag, fill=(255, 255, 255))
            cells.append(im)
        board_cells.extend(cells)
    # board: rows of [orig|gfpgan]
    from PIL import Image
    if board_cells:
        bh = 256 * (len(board_cells) // 2)
        board = Image.new("RGB", (896, bh), (24, 24, 24))
        for i, cell in enumerate(board_cells):
            board.paste(cell, ((i % 2) * 448, (i // 2) * 256))
        bpath = os.path.join(OUT, "xq-AB-GFPGAN-BOARD-r1058.jpg")
        board.save(bpath, quality=88)
        log("BOARD %s %dB" % (os.path.basename(bpath), os.path.getsize(bpath)))
    receipt = {
        "trial": "POOL-0017 full-route GFPGAN tier (xingqing A-batch human frames)",
        "runner": "bm-c r1058",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "GFPGANv1.4.pth (clean arch, upscale=1, weight=0.5)",
        "shim": "minimal basicsr (utils/registry/download_util/arch_util) + "
                "lazy-arch gfpgan patches; basicsr CUDA-ext build unavailable",
        "frames": rows,
        "ceo_order": "2026-10-17 13:0x idle-fill order",
    }
    rpath = os.path.join(OUT, "bmc_gfpgan_tier_r1058.json")
    with open(rpath, "w") as f:
        json.dump(receipt, f, indent=1)
    log("GFPGAN-TRIAL-DONE receipt=%s" % rpath)


if __name__ == "__main__":
    main()
