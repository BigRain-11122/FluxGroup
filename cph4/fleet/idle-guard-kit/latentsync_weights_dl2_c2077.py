# latentsync_weights_dl2_c2077.py -- POOL-0016 night-1 weights leg v2 (v1.5 8GB tier), C2077 pre-stow.
# Root fix of latentsync_weights_dl_c2076 FAIL 0/3: all three URLs were wrong (repo guess
# bytedance/LatentSync + path guess latentsync_v1.5/* + whisper azureedge hash typo).
# C2077 hf-mirror tree API probe evidence (ByteDance/LatentSync-1.5, 200 OK):
#   latentsync_unet.pt        5072348184  (repo root)
#   whisper/tiny.pt             75572083  (whisper true source = same repo, not azureedge)
#   auxiliary/2DFAN4-cd938726ad.zip  96316515  (face_alignment 1.4.1 landmark model, J-30 swap pre-seed)
#   auxiliary/s3fd-619a316812.pth    89843225  (face_alignment 1.4.1 SFD detector, J-30 swap pre-seed)
# stable_syncnet.pt (1.6GB) = eval-only, NOT needed by inference.sh -- skipped to save bandwidth.
# Pattern law: musepose_weights_dl + c2076 dl() verbatim (range-resume 5-retry, UA header law,
# per-file min-size gate). Verdict weights2_verdict.json + WEIGHTS2-VERDICT/WEIGHTS2-END sentinels.
import os, json, time, urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
LS = os.path.join(REPO, "media", "latentsync")
VD = os.path.join(REPO, "media", "latentsync-deploy", "weights2_verdict.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BASE = "https://hf-mirror.com/ByteDance/LatentSync-1.5/resolve/main/"

JOBS = [
    ("unet-v1.5", BASE + "latentsync_unet.pt",
     os.path.join("checkpoints", "latentsync_unet.pt"), 5000000000, 5072348184),
    ("whisper-tiny", BASE + "whisper/tiny.pt",
     os.path.join("checkpoints", "whisper", "tiny.pt"), 70000000, 75572083),
    ("fan2d4-cd938726ad", BASE + "auxiliary/2DFAN4-cd938726ad.zip",
     os.path.join("checkpoints", "aux", "2DFAN4-cd938726ad.zip"), 90000000, 96316515),
    ("sfd-619a316812", BASE + "auxiliary/s3fd-619a316812.pth",
     os.path.join("checkpoints", "aux", "s3fd-619a316812.pth"), 80000000, 89843225),
]

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

log("WEIGHTS2-START LatentSync v1.5 weights leg v2 (POOL-0016 night-1, C2077, probe-verified URLs)")
ok, fail = [], []
for name, url, rel, mins, expected in JOBS:
    st, size = dl(url, os.path.join(LS, rel), mins)
    tag = "%s %dB" % (name, size)
    if st == "ok":
        if expected and size != expected:
            tag += " SIZE-MISMATCH expected=%d" % expected
        ok.append(tag)
    else:
        fail.append(tag)
    log("%s %s %dB" % (name.upper(), st.upper(), size))
v = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "status": "OK" if not fail else "PARTIAL",
    "ok": ok, "fail": fail,
    "note": ("v1.5 8GB tier weights dl2 (probe-verified ByteDance/LatentSync-1.5). unet+whisper = "
             "inference critical path (inference.sh precedent); aux 2DFAN4+s3fd = face_alignment 1.4.1 "
             "model pre-seed for J-30 insightface swap (removes runtime download risk inside trial cap). "
             "stable_syncnet.pt 1.6GB eval-only skipped. Trial leg next: hard_gaps patch verdict + v1.5 "
             "config reconcile (GitHub tag v1.5 configs/unet/stage2.yaml vs local v1.6 clone) + "
             "FaceAlignment shim for latentsync/utils/face_detector.py."),
}
with open(VD, "w") as f:
    json.dump(v, f, indent=1)
log("WEIGHTS2-VERDICT %s ok=%d fail=%d -> %s" % (v["status"], len(ok), len(fail), VD))
log("WEIGHTS2-END status=%s" % v["status"])
