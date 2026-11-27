# musepose_weights_dl2.py -- MusePose night3 straggler downloader (bm-c C2065)
# Root cause fixed: lambdalabs/sd-image-variations-diffusers main branch only
# ships README (hf-mirror API tree probe); all 5 missing files live in the
# camenduru/MusePose mirror repo (tree probe-verified 200, C2065 probe4) plus
# ModelScope stabilityai/sd-vae-ft-mse for the vae config. UA header law added
# (hf-mirror 403 face was UA-related, probe-verified 200 with browser UA).
# Verdict merge: patches the 5 entries inside existing weights_verdict.json.
# ASCII-only output (B1324 purge law). Range-resume 5-retry per dl1 engine.
import json, os, time, urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
PW = os.path.join(REPO, "media", "musepose", "pretrained_weights")
DEPLOY = os.path.join(REPO, "media", "musepose-deploy")
MB = 1024 * 1024
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"
CAM = "https://hf-mirror.com/camenduru/MusePose/resolve/main/"

# (url_candidates, dest_rel, min_bytes)
FILES = [
    ([CAM + "sd-image-variations-diffusers/diffusion_pytorch_model.bin"],
     os.path.join("sd-image-variations-diffusers", "unet", "diffusion_pytorch_model.bin"), 100 * MB),
    ([CAM + "sd-image-variations-diffusers/config.json"],
     os.path.join("sd-image-variations-diffusers", "unet", "config.json"), 50),
    ([CAM + "image_encoder/pytorch_model.bin"],
     os.path.join("image_encoder", "pytorch_model.bin"), 100 * MB),
    ([CAM + "image_encoder/config.json"],
     os.path.join("image_encoder", "config.json"), 50),
    (["https://modelscope.cn/models/stabilityai/sd-vae-ft-mse/resolve/master/config.json",
      CAM + "sd-vae-ft-mse/config.json",
      "https://hf-mirror.com/stabilityai/sd-vae-ft-mse/resolve/main/config.json"],
     os.path.join("sd-vae-ft-mse", "config.json"), 50),
]

BACKOFF = [5, 10, 20, 40, 60]
CHUNK = 1024 * 1024


def fetch(urls, dest, min_bytes):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    last_err = None
    for url in urls:
        for attempt in range(5):
            have = os.path.getsize(dest) if os.path.exists(dest) else 0
            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", UA)
                if have:
                    req.add_header("Range", "bytes=%d-" % have)
                with urllib.request.urlopen(req, timeout=60) as r:
                    code = r.status if hasattr(r, "status") else r.getcode()
                    cr = r.headers.get("Content-Range", "")
                    expected = int(cr.split("/")[-1]) if "/" in cr else int(r.headers.get("Content-Length", "0") or 0)
                    if have and code == 200:
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
                    return True, "ok size=%d src=%s" % (size, url.rsplit("/", 2)[-2] if "/" in url else url)
                print("SIZE-FAIL %s got=%d min=%d" % (os.path.basename(dest), size, min_bytes), flush=True)
            except Exception as e:
                last_err = e
                print("ERR %s attempt=%d %r" % (os.path.basename(dest), attempt + 1, e), flush=True)
            if attempt < 4:
                time.sleep(BACKOFF[attempt])
    return False, "failed-all-sources %r" % last_err


def main():
    results = {}
    for urls, rel, minb in FILES:
        dest = os.path.join(PW, rel)
        ok, note = fetch(urls, dest, minb)
        results[rel.replace("\\", "/")] = {"ok": ok, "note": note, "url": urls[0]}
        print("FILE-DONE %s ok=%s %s" % (rel.replace("\\", "/"), ok, note), flush=True)
    # merge into existing verdict (dl1 wrote the other 7)
    vpath = os.path.join(DEPLOY, "weights_verdict.json")
    verdict = {}
    if os.path.exists(vpath):
        with open(vpath, "r", encoding="utf-8") as f:
            try:
                verdict = json.load(f)
            except Exception:
                verdict = {}
    res = verdict.get("results", {})
    if not isinstance(res, dict):
        res = {}
    res.update(results)
    missing = sorted(k for k, v in res.items() if not v.get("ok"))
    verdict.update({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ok": sum(1 for v in res.values() if v.get("ok")),
        "total": len(res),
        "missing": missing,
        "results": res,
    })
    os.makedirs(DEPLOY, exist_ok=True)
    with open(vpath, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=1, ensure_ascii=False)
    print("WEIGHTS-VERDICT2: %s %d/%d missing=%s" % ("OK" if not missing else "PARTIAL",
          verdict["ok"], verdict["total"], ",".join(missing) or "none"), flush=True)


if __name__ == "__main__":
    main()
