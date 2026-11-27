# latentsync_weights_dl_c2076.py -- POOL-0016 night-1 weights leg (v1.5 8GB tier), C2076 pre-stow
# Downloads: unet v1.5 + syncnet v1.5 (hf-mirror, UA-header law) + whisper tiny.pt (azureedge primary, hf-mirror fallback).
# Pattern law: musepose_weights_dl precedent -- range-resume 5-retry backoff, per-file min-size gate,
# verdict json + WEIGHTS-VERDICT/WEIGHTS-END sentinel lines. Dest = media/latentsync/checkpoints/.
import os, json, time, urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
LS = os.path.join(REPO, "media", "latentsync")
VD = os.path.join(REPO, "media", "latentsync-deploy", "weights_verdict.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

JOBS = [
    ("unet-v1.5",
     "https://hf-mirror.com/bytedance/LatentSync/resolve/main/checkpoints/latentsync_v1.5/unet.pth",
     os.path.join("checkpoints", "latentsync_v1.5", "unet.pth"), 1000000000),
    ("syncnet-v1.5",
     "https://hf-mirror.com/bytedance/LatentSync/resolve/main/checkpoints/latentsync_v1.5/syncnet.pth",
     os.path.join("checkpoints", "latentsync_v1.5", "syncnet.pth"), 100000000),
    ("whisper-tiny",
     "https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12d04e32d39f3d83e3a860e1c9af5c8bd2ba77f7cd1e7c516b4/tiny.pt",
     os.path.join("checkpoints", "whisper", "tiny.pt"), 140000000),
]
FALLBACK = {
    "whisper-tiny":
        "https://hf-mirror.com/bytedance/LatentSync/resolve/main/checkpoints/whisper/tiny.pt",
}

def log(m):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), m), flush=True)

def dl(url, dest, min_bytes):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(5):
        try:
            part = os.path.getsize(dest) if os.path.exists(dest) else 0
            if part >= min_bytes:
                log("SKIP %s already %d bytes" % (os.path.basename(dest), part))
                return ("ok", part)
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            if part > 0:
                req.add_header("Range", "bytes=%d-" % part)
            with urllib.request.urlopen(req, timeout=60) as r:
                append = part > 0 and r.status == 206
                with open(dest, "ab" if append else "wb") as f:
                    if not append:
                        pass
                    while True:
                        chunk = r.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
            size = os.path.getsize(dest)
            if size >= min_bytes:
                return ("ok", size)
            log("SIZE-LOW %s %d < %d, retry" % (os.path.basename(dest), size, min_bytes))
        except Exception as e:
            log("ERR %s attempt%d %s" % (os.path.basename(dest), attempt + 1, str(e)[:120]))
        time.sleep(8 * (attempt + 1))
    return ("fail", os.path.getsize(dest) if os.path.exists(dest) else 0)

log("WEIGHTS-START LatentSync v1.5 weights leg (POOL-0016 night-1, C2076)")
ok, fail = [], []
for name, url, rel, mins in JOBS:
    st, size = dl(url, os.path.join(LS, rel), mins)
    if st != "ok" and name in FALLBACK:
        log("FALLBACK %s" % name)
        st, size = dl(FALLBACK[name], os.path.join(LS, rel), mins)
    (ok if st == "ok" else fail).append("%s %dB" % (name, size))
    log("%s %s %dB" % (name.upper(), st.upper(), size))
v = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "status": "OK" if not fail else "PARTIAL",
    "ok": ok, "fail": fail,
    "note": ("v1.5 8GB tier weights (unet+syncnet+whisper). Trial leg next: hard_gaps patch "
             "(tokenizers 0.21.x + future + accelerate deps into PYLIBS overlay per deploy_verdict) + "
             "FaceAlignment face-detect swap (EL J-30) + v1.5 inference config/branch reconcile."),
}
with open(VD, "w") as f:
    json.dump(v, f, indent=1)
log("WEIGHTS-VERDICT %s ok=%d fail=%d -> %s" % (v["status"], len(ok), len(fail), VD))
log("WEIGHTS-END status=%s" % v["status"])
