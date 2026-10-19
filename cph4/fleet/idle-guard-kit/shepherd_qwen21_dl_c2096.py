# qwen21 weights download shepherd (bm-c, batch C2096).
# Context: armed runner qwen21_weights_dl_c2094.py (idle-guard spawned) had a
# connect-phase curl hang (41 min at 0 bytes, killed surgically 22:49), then
# hf-mirror throttle pattern: fresh connection bursts ~22MB/s for ~2.5GB,
# then grinds ~0.2MB/s. curl speed-guard (10KB/s floor) never fires on the
# grind, so without recycling the ~15GB set would take ~20h vs ~30min.
# This shepherd recycles the runner's curl child when a 60s window shows
# less than 50MB growth (forces runner attempt++ -> fresh burst connection
# with -C - resume). SAFE BY DESIGN: single runner PID verified, kills only
# its curl child, never relaunches the runner (two runners would interleave
# writes on the same .part = corruption). Exits when the verdict JSON lands.
# Kill cap 12 (per-file runner budget is 5 attempts; .part persistence makes
# a FAIL verdict recoverable by next-round relaunch).
# Log: media/qwen21-deploy/shepherd.log (ASCII only).

import os
import subprocess
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUT_DIR = os.path.join(REPO, "media", "qwen21-deploy")
VERDICT = os.path.join(OUT_DIR, "weights_verdict.json")
LOG = os.path.join(OUT_DIR, "shepherd.log")
RUNNER_TOKEN = "qwen21_weights_dl_c2094.py"
MODELS = r"D:\ComfyUI\ComfyUI\models"
SUBS = ["diffusion_models", "text_encoders", "vae", "loras"]
WINDOW = 60                      # seconds per sample
KILL_THRESHOLD = 50 * 1024 * 1024  # bytes growth per window
KILL_CAP = 12


def log(msg):
    line = "%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    with open(LOG, "a", encoding="ascii", errors="replace") as f:
        f.write(line)


def qwen_bytes():
    total = 0
    for sub in SUBS:
        d = os.path.join(MODELS, sub)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            p = os.path.join(d, name)
            if name.endswith(".part") or (
                    name.endswith(".safetensors") and "qwen" in name.lower()):
                total += os.path.getsize(p)
    return total


def runner_pid():
    # probe python.exe only -> no self-match (shepherd queried via powershell)
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
         "Where-Object {$_.CommandLine -like '*" + RUNNER_TOKEN + "*'}).ProcessId"],
        capture_output=True, text=True).stdout.strip()
    return out if out else None


def kill_curl_child(parent):
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "$c=Get-CimInstance Win32_Process -Filter 'ParentProcessId=" +
         str(parent) + "' | Where-Object {$_.Name -eq 'curl.exe'}; "
         "$c | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; "
         "($c | Measure-Object).Count"],
        capture_output=True, text=True).stdout.strip()
    return out


def main():
    log("shepherd start pid=%d window=%ds cap=%d" % (os.getpid(), WINDOW, KILL_CAP))
    kills = 0
    last = qwen_bytes()
    while kills < KILL_CAP:
        time.sleep(WINDOW)
        if os.path.exists(VERDICT):
            log("verdict present -> exit")
            return 0
        total = qwen_bytes()
        growth = total - last
        last = total
        pid = runner_pid()
        if pid is None:
            log("runner not visible growth=%dB (between attempts or gone)" % growth)
            continue
        if growth < KILL_THRESHOLD:
            n = kill_curl_child(pid)
            if n and n.strip() not in ("0", ""):
                kills += 1
                log("slow %dB/window -> killed curl x%s (kill %d/%d) pid=%s"
                    % (growth, n.strip(), kills, KILL_CAP, pid))
            else:
                log("slow %dB/window but no curl child (runner working) pid=%s"
                    % (growth, pid))
        else:
            log("ok growth=%dB/window kills=%d/%d" % (growth, kills, KILL_CAP))
    log("kill cap %d reached -> exit (runner grinds on; next round may relaunch)" % KILL_CAP)
    return 0


if __name__ == "__main__":
    main()
