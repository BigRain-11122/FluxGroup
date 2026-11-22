# musepose_weights_dl.py -- MusePose night3 weights downloader (bm-c C2064 pre-stow)
# Law: hf-mirror map for HF files (HEAD probe showed 429 rate-limit; GET uses
# backoff+resume), openmmlab direct for yolox; curl -C - 5-retry law encoded as
# Range-resume loop; per-file min-size gate; final WEIGHTS-VERDICT line + JSON
# for the harvest round. ASCII-only output (B1324 purge law).
import json, os, time, urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
PW = os.path.join(REPO, "media", "musepose", "pretrained_weights")
DEPLOY = os.path.join(REPO, "media", "musepose-deploy")

MB = 1024 * 1024
FILES = [
    # (url, dest_rel, min_bytes, final_rename_or_None)
    ("https://download.openmmlab.com/mmdetection/v2.0/yolox/yolox_l_8x8_300e_coco/yolox_l_8x8_300e_coco_20211126_140236-d3bd2b23.pth",
     os.path.join("dwpose", "yolox_l_8x8_300e_coco_20211126_140236-d3bd2b23.pth"), 100 * MB, "yolox_l_8x8_300e_coco.pth"),
    ("https://hf-mirror.com/yzd-v/DWPose/resolve/main/dw-ll_ucoco_384.pth",
     os.path.join("dwpose", "dw-ll_ucoco_384.pth"), 100 * MB, None),
    ("https://hf-mirror.com/TMElyralab/MusePose/resolve/main/MusePose/denoising_unet.pth",
     os.path.join("MusePose", "denoising_unet.pth"), 100 * MB, None),
    ("https://hf-mirror.com/TMElyralab/MusePose/resolve/main/MusePose/motion_module.pth",
     os.path.join("MusePose", "motion_module.pth"), 50 * MB, None),
    ("https://hf-mirror.com/TMElyralab/MusePose/resolve/main/MusePose/pose_guider.pth",
     os.path.join("MusePose", "pose_guider.pth"), 10 * MB, None),
    ("https://hf-mirror.com/TMElyralab/MusePose/resolve/main/MusePose/reference_unet.pth",
     os.path.join("MusePose", "reference_unet.pth"), 100 * MB, None),
    ("https://hf-mirror.com/lambdalabs/sd-image-variations-diffusers/resolve/main/unet/diffusion_pytorch_model.bin",
     os.path.join("sd-image-variations-diffusers", "unet", "diffusion_pytorch_model.bin"), 100 * MB, None),
    ("https://hf-mirror.com/lambdalabs/sd-image-variations-diffusers/resolve/main/image_encoder/pytorch_model.bin",
     os.path.join("image_encoder", "pytorch_model.bin"), 100 * MB, None),
    ("https://hf-mirror.com/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.bin",
     os.path.join("sd-vae-ft-mse", "diffusion_pytorch_model.bin"), 100 * MB, None),
    ("https://hf-mirror.com/lambdalabs/sd-image-variations-diffusers/resolve/main/unet/config.json",
     os.path.join("sd-image-variations-diffusers", "unet", "config.json"), 50, None),
    ("https://hf-mirror.com/lambdalabs/sd-image-variations-diffusers/resolve/main/image_encoder/config.json",
     os.path.join("image_encoder", "config.json"), 50, None),
    ("https://hf-mirror.com/stabilityai/sd-vae-ft-mse/resolve/main/config.json",
     os.path.join("sd-vae-ft-mse", "config.json"), 50, None),
]

BACKOFF = [5, 10, 20, 40, 60]
CHUNK = 1024 * 1024


def fetch(url, dest, min_bytes):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(5):
        have = os.path.getsize(dest) if os.path.exists(dest) else 0
        try:
            req = urllib.request.Request(url)
            if have:
                req.add_header("Range", "bytes=%d-" % have)
            with urllib.request.urlopen(req, timeout=60) as r:
                code = r.status if hasattr(r, "status") else r.getcode()
                cr = r.headers.get("Content-Range", "")
                if "/" in cr:
                    expected = int(cr.split("/")[-1])
                else:
                    expected = int(r.headers.get("Content-Length", "0") or 0)
                if have and code == 200:
                    # server ignored Range -> restart whole file
                    mode, have = "wb", 0
                elif have and code == 416:
                    return True, "already-complete size=%d" % os.path.getsize(dest)
                else:
                    mode = "ab" if have else "wb"
                print("GET %s code=%s have=%d expected=%d" % (os.path.basename(dest), code, have, expected), flush=True)
                with open(dest, mode) as f:
                    while True:
                        b = r.read(CHUNK)
                        if not b:
                            break
                        f.write(b)
            size = os.path.getsize(dest)
            if size >= min_bytes:
                return True, "ok size=%d" % size
            print("SIZE-FAIL %s got=%d min=%d" % (os.path.basename(dest), size, min_bytes), flush=True)
        except Exception as e:
            print("ERR %s attempt=%d %r" % (os.path.basename(dest), attempt + 1, e), flush=True)
        if attempt < 4:
            time.sleep(BACKOFF[attempt])
    return False, "failed-5-attempts"


def main():
    results = {}
    for url, rel, minb, final in FILES:
        dest = os.path.join(PW, rel)
        ok, note = fetch(url, dest, minb)
        if ok and final:
            dst = os.path.join(os.path.dirname(dest), final)
            if os.path.exists(dest) and not os.path.exists(dst):
                os.replace(dest, dst)
                print("RENAME %s -> %s" % (os.path.basename(dest), final), flush=True)
        results[rel.replace("\\", "/")] = {"ok": ok, "note": note, "url": url}
        print("FILE-DONE %s ok=%s %s" % (rel.replace("\\", "/"), ok, note), flush=True)
    ok_n = sum(1 for v in results.values() if v["ok"])
    missing = [k for k, v in results.items() if not v["ok"]]
    os.makedirs(DEPLOY, exist_ok=True)
    with open(os.path.join(DEPLOY, "weights_verdict.json"), "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "ok": ok_n,
                    "total": len(FILES), "missing": missing, "results": results},
                   f, indent=1, ensure_ascii=False)
    print("WEIGHTS-VERDICT: %s %d/%d missing=%s" % ("OK" if ok_n == len(FILES) else "PARTIAL",
          ok_n, len(FILES), ",".join(missing) or "none"), flush=True)


if __name__ == "__main__":
    main()
