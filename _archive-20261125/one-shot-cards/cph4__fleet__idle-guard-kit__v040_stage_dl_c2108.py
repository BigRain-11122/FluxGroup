# v040_stage_dl_c2108.py -- pre-stow ComfyUI 0.40.0 windows portable (parallel stage, do NOT touch prod 0.36 at D:\ComfyUI)
# Law refs: gh-proxy prefix fastest (bm-a 2026-10-09 law); curl resume + speed guards; verdict JSON + sentinel for harvest.
# Legs after (next bank item): unzip + extra_model_paths.yaml -> D:\ComfyUI\ComfyUI\models + port 8199 first-launch + qwen21 t2i smoke.
import json, os, subprocess, sys, time, urllib.request

STAGE = r"K:\Fluxgroup\Tools\v040_stage"
ZIP = os.path.join(STAGE, "ComfyUI_windows_portable_0.40.zip")
VERDICT = r"K:\Fluxgroup\FluxGroup\media\qwen21-deploy\v040_stage_verdict.json"
OUT = r"K:\Fluxgroup\FluxGroup\media\qwen21-deploy\log-v040-stage-c2108.out.txt"
ERR = r"K:\Fluxgroup\FluxGroup\media\qwen21-deploy\log-v040-stage-c2108.err.txt"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
GH_PROXY = "https://gh-proxy.com/"
TAGS = ["0.40", "0.40.0"]

def log(msg):
    with open(OUT, "a", encoding="ascii", errors="replace") as f:
        f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), str(msg)))

def probe_asset():
    # primary: anonymous GitHub API (api.github.com always-alive per fleet law); fallback: expanded_assets HTML scrape via gh-proxy
    for tag in TAGS:
        api = "https://api.github.com/repos/comfyanonymous/ComfyUI/releases/tags/" + tag
        try:
            req = urllib.request.Request(api, headers=UA)
            data = json.load(urllib.request.urlopen(req, timeout=30))
            cands = [a for a in data.get("assets", [])
                     if a["name"].lower().endswith(".zip")
                     and "portable" in a["name"].lower()
                     and ("nvidia" in a["name"].lower() or "cu12" in a["name"].lower())]
            if cands:
                a = max(cands, key=lambda x: x["size"])
                return a["browser_download_url"], int(a["size"]), a["name"], "api:" + tag
        except Exception as e:
            log("API probe fail %s: %r" % (tag, e))
        try:
            html_url = GH_PROXY + "https://github.com/comfyanonymous/ComfyUI/releases/expanded_assets/" + tag
            req = urllib.request.Request(html_url, headers=UA)
            html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
            import re
            hrefs = re.findall(r'href="(/comfyanonymous/ComfyUI/releases/download/[^"]+\.zip)"', html)
            nvidia = [h for h in hrefs if "nvidia" in h.lower() or "cu12" in h.lower()]
            pick = (nvidia or hrefs)
            if pick:
                path = max(pick, key=len)
                dl = "https://github.com" + path
                return dl, 0, path.rsplit("/", 1)[-1], "html:" + tag
        except Exception as e:
            log("HTML probe fail %s: %r" % (tag, e))
    return None, 0, None, None

def main():
    os.makedirs(STAGE, exist_ok=True)
    log("V040-STAGE-START stage=%s" % STAGE)
    dl, expected, name, src = probe_asset()
    if not dl:
        log("FATAL no asset found via api/html probes")
        write_verdict("FAIL", 0, expected, name, src)
        return 1
    log("asset=%s expected=%dB via=%s" % (name, expected, src))
    proxied = dl if dl.startswith(GH_PROXY) else GH_PROXY + dl
    ok = False
    for attempt in range(1, 7):
        have = os.path.getsize(ZIP) if os.path.exists(ZIP) else 0
        if expected and have == expected:
            ok = True
            break
        if expected and have > expected:
            os.remove(ZIP)
            have = 0
        log("curl attempt %d resume_from=%dB" % (attempt, have))
        cmd = ["curl.exe", "-L", "--fail", "-C", "-", "--speed-time", "60",
               "--speed-limit", "20000", "--connect-timeout", "30",
               "-A", UA["User-Agent"], "-o", ZIP, proxied]
        with open(ERR, "ab") as ef:
            rc = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=ef)
        have2 = os.path.getsize(ZIP) if os.path.exists(ZIP) else 0
        log("curl rc=%d now=%dB" % (rc, have2))
        if expected and have2 == expected:
            ok = True
            break
        if not expected and rc == 0:
            ok = True
            break
        time.sleep(min(20 * attempt, 90))
    size = os.path.getsize(ZIP) if os.path.exists(ZIP) else 0
    status = "OK" if ok else "PARTIAL"
    write_verdict(status, size, expected, name, src)
    log("V040-STAGE-END status=%s size=%dB expected=%dB" % (status, size, expected))
    return 0 if ok else 2

def write_verdict(status, size, expected, name, src):
    v = {"status": status, "zip": ZIP, "bytes": size, "expected_bytes": expected,
         "asset": name, "probe_source": src,
         "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "note": "pre-stow per bm-b same-stack recipe cph4/fleet/bm-b-model-stack-20261016.md; next legs: unzip + extra_model_paths.yaml to D:\\ComfyUI\\ComfyUI\\models + port 8199 first launch + qwen21 t2i smoke"}
    os.makedirs(os.path.dirname(VERDICT), exist_ok=True)
    with open(VERDICT, "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    sys.exit(main())
