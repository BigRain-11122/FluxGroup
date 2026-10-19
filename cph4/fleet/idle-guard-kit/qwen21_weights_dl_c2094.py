# POOL-0021 leg-1: Qwen-Image-2.1-Turbo int8 four-file weights download (bm-c).
# Order: CEO full-load O-20261019-1935 sec-3 + broadcast O-20261019-2047 sec-2.
# Recipe: cph4/fleet/bm-b-model-stack-20261016.md (bm-b 8G same-stack 20s/img PASS).
# Files: turbo int8 DiT ~6.92G + w4a8 TE ~6.02G + VAE ~0.64G + turbo LoRA ~0.87G.
# Method: probe-first (hf-mirror tree API) -> best-match select -> curl resume
# download with stream guards -> raw-byte min-size gates -> verdict JSON + sentinel.
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
OUT_DIR = os.path.join(REPO, "media", "qwen21-deploy")
VERDICT = os.path.join(OUT_DIR, "weights_verdict.json")
PROBE = os.path.join(OUT_DIR, "tree_probe.json")
MODELS = r"D:\ComfyUI\ComfyUI\models"
MIRROR = "https://hf-mirror.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
SENTINEL = "QWEN21-WEIGHTS-END"
MIN_DISK_FREE = 40 * 1024 ** 3

TARGETS = [
    {"key": "dit", "sub": "diffusion_models",
     "repos": ["Comfy-Org/Qwen-Image-2.1"],
     "want": ["qwen_image_2.1", "int8"], "prefer": ["turbo"],
     "lo": 6_000_000_000, "hi": 9_500_000_000},
    {"key": "te", "sub": "text_encoders",
     "repos": ["Comfy-Org/Qwen-Image-2.1"],
     "want": ["text_encoders", "w4a8"], "prefer": ["qwen3vl"],
     "lo": 5_500_000_000, "hi": 7_000_000_000},
    {"key": "vae", "sub": "vae",
     "repos": ["Comfy-Org/Qwen-Image-2.1"],
     "want": ["vae"], "prefer": ["qwen_image_2.1"],
     "lo": 400_000_000, "hi": 1_000_000_000},
    {"key": "lora", "sub": "loras",
     "repos": ["Comfy-Org/Qwen-Image-2.1"],
     "want": ["lora"], "prefer": ["turbo"],
     "lo": 500_000_000, "hi": 1_200_000_000},
]
# Probe-verified 2026-10-19 22:1x (hf-mirror tree API, this machine):
#   dit  = diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors  7,256,787,829B
#   te   = text_encoders/qwen3vl_8b_w4a8.safetensors                        6,312,105,364B
#          (base TE for TextEncodeQwenImage21; pe_t2i_w4a8 6.72e9B is the
#           prompt-enhancer variant, not the base t2i encode node input)
#   vae  = vae/qwen_image_2.1_vae_bf16.safetensors                            675,509,688B
#   lora = loras/qwen_image_2.1_turbo_lora_avg_rank_178_bf16.safetensors      913,314,512B

# Known-good manifest: the exact four files+sizes probe-verified 2026-10-19
# 22:1x on this machine (three of them landed at exactly these byte sizes).
# Used as probe-failure fallback so a transient tree-API timeout cannot zero
# out the chain while files sit on disk (2026-10-20 00:51 WinError 10060
# relaunch-death evidence: PROBE_FAIL 0/4 + zero download attempts).
KNOWN_FILES = {
    "Comfy-Org/Qwen-Image-2.1": [
        {"path": "diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors",
         "size": 7256787829},
        {"path": "text_encoders/qwen3vl_8b_w4a8.safetensors",
         "size": 6312105364},
        {"path": "vae/qwen_image_2.1_vae_bf16.safetensors",
         "size": 675509688},
        {"path": "loras/qwen_image_2.1_turbo_lora_avg_rank_178_bf16.safetensors",
         "size": 913314512},
    ],
}


def log(msg):
    print(msg, flush=True)


def probe_tree(repo):
    url = MIRROR + "/api/models/" + repo + "/tree/main?recursive=true"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def probe_tree_retry(repo, tries=3, backoff=20):
    # hf-mirror tree API has transient connect-timeout windows; one blip must
    # not kill the chain (2026-10-20 00:51 WinError 10060 evidence above).
    last = None
    for i in range(1, tries + 1):
        try:
            return probe_tree(repo)
        except Exception as e:
            last = e
            log("probe attempt %d/%d FAIL %s %s" % (i, tries, repo, e))
            if i < tries:
                time.sleep(backoff)
    raise last


def select(t, trees):
    cands = []
    for repo in t["repos"]:
        for f in trees.get(repo, []):
            if f.get("type") not in (None, "file"):
                continue
            p = f.get("path", "").lower()
            if not p.endswith(".safetensors"):
                continue
            if t["sub"] not in p:
                continue
            if not all(w in p for w in t["want"]):
                continue
            size = int(f.get("size") or 0)
            if size < t["lo"] or size > t["hi"]:
                continue
            score = sum(1 for w in t["prefer"] if w in p)
            cands.append((score, size, repo, f["path"], size))
    if not cands:
        return None
    cands.sort(key=lambda c: (c[0], c[1]), reverse=True)
    return cands[0]


def download(url, dest, min_bytes):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    last_rc = -1
    for attempt in range(1, 6):
        cmd = ["curl", "-L", "-A", UA, "-C", "-", "--connect-timeout", "30",
               "--speed-limit", "10240", "--speed-time", "30", "--retry", "3",
               "-o", tmp, url]
        r = subprocess.run(cmd, capture_output=True)
        last_rc = r.returncode
        if os.path.exists(tmp) and os.path.getsize(tmp) >= min_bytes:
            shutil.move(tmp, dest)
            return True, os.path.getsize(dest)
        log("attempt %d rc=%s size=%s" % (attempt, r.returncode,
            os.path.getsize(tmp) if os.path.exists(tmp) else 0))
    if os.path.exists(tmp) and os.path.getsize(tmp) >= min_bytes:
        shutil.move(tmp, dest)
        return True, os.path.getsize(dest)
    return False, (os.path.getsize(tmp) if os.path.exists(tmp) else 0), last_rc


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    free = shutil.disk_usage(os.path.splitdrive(MODELS)[0] + "\\").free
    log("disk free on model drive: %.1f GB" % (free / 1024 ** 3))
    if free < MIN_DISK_FREE:
        verdict = {"status": "FAIL", "reason": "disk_free_below_40GB", "free": free}
        json.dump(verdict, open(VERDICT, "w", encoding="utf-8"), indent=1)
        log(SENTINEL + " FAIL disk")
        return 1
    trees = {}
    probe_err = {}
    for t in TARGETS:
        for repo in t["repos"]:
            if repo in trees or repo in probe_err:
                continue
            try:
                trees[repo] = probe_tree_retry(repo)
                log("probe OK %s files=%d" % (repo, len(trees[repo])))
            except Exception as e:
                probe_err[repo] = str(e)
                log("probe FAIL %s %s" % (repo, e))
                if repo in KNOWN_FILES:
                    trees[repo] = KNOWN_FILES[repo]
                    log("probe fallback to known-good manifest %s (%d files)"
                        % (repo, len(trees[repo])))
    json.dump({"trees": {k: [f.get("path") for f in v] for k, v in trees.items()},
               "errors": probe_err}, open(PROBE, "w", encoding="utf-8"), indent=1)
    results = {}
    ok_count = 0
    for t in TARGETS:
        pick = select(t, trees)
        if not pick:
            results[t["key"]] = {"status": "NO_MATCH", "repos": t["repos"],
                                 "want": t["want"], "lo": t["lo"], "hi": t["hi"]}
            log("NO_MATCH for %s (probe evidence in tree_probe.json)" % t["key"])
            continue
        _, _, repo, path, size = pick
        url = MIRROR + "/" + repo + "/resolve/main/" + path
        dest = os.path.join(MODELS, t["sub"], os.path.basename(path))
        if os.path.exists(dest) and os.path.getsize(dest) >= t["lo"]:
            results[t["key"]] = {"status": "ALREADY_OK", "path": dest,
                                 "bytes": os.path.getsize(dest), "url": url}
            ok_count += 1
            log("already in place %s %d" % (dest, os.path.getsize(dest)))
            continue
        log("downloading %s -> %s (expect ~%d B)" % (url, dest, size))
        out = download(url, dest, t["lo"])
        if out[0]:
            results[t["key"]] = {"status": "OK", "path": dest, "bytes": out[1], "url": url}
            ok_count += 1
            log("OK %s %d B" % (dest, out[1]))
        else:
            results[t["key"]] = {"status": "FAIL", "path": dest, "url": url,
                                 "got_bytes": out[1], "curl_rc": out[2] if len(out) > 2 else None}
            log("FAIL %s got=%s" % (dest, out[1]))
    status = "OK" if ok_count == len(TARGETS) else ("PARTIAL" if ok_count else "PROBE_FAIL")
    import datetime
    verdict = {"status": status, "ok": ok_count, "of": len(TARGETS),
               "files": results,
               "ts": datetime.datetime.now().isoformat(timespec="seconds")}
    json.dump(verdict, open(VERDICT, "w", encoding="utf-8"), indent=1)
    log(SENTINEL + " " + status + " %d/%d" % (ok_count, len(TARGETS)))
    return 0 if status == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
