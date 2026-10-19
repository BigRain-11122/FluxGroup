# -*- coding: utf-8 -*-
# bmc_idleguard.py -- 10分钟闲置守卫 v1.0 (bm-c·CEO 2026-10-18 硬SLA「不要出现10分钟以上的闲置」)
# 纪律: 尊重machine-state.flag=paused让路(CEO游戏窗零动作)·只在真闲置>=10min时认领银行在档活·CREATE_NO_WINDOW全程无窗
# 车道: GPU(pythonw烧批在跑/ComfyUI队列非空/util>=20%=忙) + CPU(saturation_engine死=>自动复活)
import json, os, subprocess, sys, time, urllib.request

REPO = r"K:\Fluxgroup\FluxGroup"
FLAG = r"K:\Fluxgroup\.codely-cli\machine-state.flag"
BANK = os.path.join(REPO, "cph4", "fleet", "work-bank", "bm-c-gpu-bank.json")
STATE = os.path.join(REPO, "media", "mv-album-001-jay", "idleguard-state.json")
LOG = os.path.join(REPO, "media", "MV", "mv0001", "logs", "idleguard.log")
PYW = r"D:\ComfyUI\python_embeded\pythonw.exe"
SYS_PY = r"C:\Users\Dasheng\AppData\Local\Programs\Python\Python313\python.exe"
SAT_ENGINE = os.path.join(REPO, "quant", "bigmoney", "Tools", "saturation_engine.py")
NO_WINDOW = 0x08000000

def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        open(LOG, "a", encoding="utf-8").write("%s %s\n" % (time.strftime("%m-%d %H:%M:%S"), msg))
    except Exception:
        pass

def read_json(p, default):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default

def write_json(p, d):
    tmp = p + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)

def procs_alive(pattern):
    # C2059 fix: probe self-match -- the spawned powershell query process itself
    # carries PATTERN in its command line (so busy was always True and the guard
    # never fired/never logged), and the BigMoney loop CLI prompt text contains
    # 'saturation_engine'. Restrict matches to python/pythonw process names:
    # real targets (burn runners, SatEngine) are pythonw.exe/python.exe.
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match '%s' -and $_.Name -match 'python'} | Select-Object -First 1 | ForEach-Object {$_.ProcessId}" % pattern],
                             capture_output=True, text=True, creationflags=NO_WINDOW, timeout=30).stdout.strip()
        return bool(out)
    except Exception:
        return True  # 探针失败=保守判忙

def gpu_util():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader"],
                             capture_output=True, text=True, creationflags=NO_WINDOW, timeout=15).stdout.strip()
        return int(out.split("\n")[0].replace("%", "").strip())
    except Exception:
        return 100  # 探针失败=保守判忙

def queue_busy():
    try:
        q = json.loads(urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=8).read())
        return bool(q.get("queue_running") or q.get("queue_pending"))
    except Exception:
        return False  # ComfyUI不在=队列面无忙

# ---------- 1) CEO让路窗: 零动作 ----------
try:
    if "paused" in open(FLAG, "r", encoding="utf-8", errors="replace").read():
        st = read_json(STATE, {})
        if st.get("idle_since"):
            st["idle_since"] = None
            write_json(STATE, st)
        log("paused-window, zero action")
        sys.exit(0)
except Exception:
    pass

# ---------- 2) CPU车道: SatEngine死=>10分钟内复活 ----------
if not procs_alive("saturation_engine"):
    try:
        subprocess.Popen([SYS_PY, SAT_ENGINE, "run"], creationflags=NO_WINDOW,
                         stdout=open(os.devnull, "w"), stderr=subprocess.DEVNULL)
        log("CPU lane: saturation_engine relaunched")
    except Exception as e:
        log("CPU lane relaunch FAIL: %r" % e)

# ---------- 2.5) QW21 download chain self-heal (C2099; deploy-dir gate = no-op on other machines) ----------
def qw21_selfheal():
    # media/ is gitignored -> qwen21-deploy dir exists only on the machine that
    # fired the download; on any other machine this section is a silent no-op.
    out_dir = os.path.join(REPO, "media", "qwen21-deploy")
    if not os.path.isdir(out_dir):
        return
    if procs_alive("qwen21_weights_dl"):
        return  # runner in flight (TE/VAE/LoRA grind or DiT resume)
    verdict_p = os.path.join(out_dir, "weights_verdict.json")
    st_p = os.path.join(out_dir, "selfheal_state.json")
    script = os.path.join(REPO, "cph4", "fleet", "idle-guard-kit", "qwen21_weights_dl_c2094.py")
    cap = 6  # ~30 DiT attempts total with the runner's internal x5; beyond = M1 escalation
    verdict = read_json(verdict_p, None)
    if verdict is not None and verdict.get("reason") == "disk_free_below_40GB":
        esc_p = os.path.join(out_dir, "ESCALATION-needed.json")
        if not os.path.exists(esc_p):
            write_json(esc_p, {"reason": "disk_free_below_40GB", "verdict": verdict,
                               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
        log("QW21 disk-full verdict -> ESCALATION file, no relaunch")
        return
    if verdict is not None and verdict.get("status") == "OK":
        # harvest: flip bank job to done + machine receipt (idempotent, steady no-op after)
        receipt_p = os.path.join(out_dir, "weights_receipt.json")
        bank = read_json(BANK, {"jobs": []})
        job = next((j for j in bank.get("jobs", []) if j.get("id") == "qwen21-weights-dl"), None)
        if job is None:
            return  # bank restructured; nothing to harvest
        if job.get("status") == "done" and os.path.exists(receipt_p):
            return  # harvest already complete
        job["status"] = "done"
        job["done_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        job["done_note"] = "guard harvest C2099: weights_verdict.json OK (%s/%s files)" % (
            verdict.get("ok", "?"), verdict.get("of", "?"))
        write_json(BANK, bank)
        if not os.path.exists(receipt_p):
            write_json(receipt_p, {"status": "OK", "verdict": verdict,
                                   "receipt_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                   "bank_flipped": True})
        log("QW21 weights OK -> bank flip done + receipt written")
        return
    # runner dead with non-OK verdict (PARTIAL/PROBE_FAIL) or crash (no verdict):
    # relaunch the runner; curl -C - resumes every .part file in place.
    st = read_json(st_p, {})
    n = int(st.get("relaunch_count", 0))
    if n >= cap:
        esc_p = os.path.join(out_dir, "ESCALATION-needed.json")
        if not os.path.exists(esc_p):
            write_json(esc_p, {"reason": "relaunch cap reached (%d)" % cap,
                               "verdict": verdict,
                               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
        log("QW21 relaunch cap reached -> ESCALATION file (M1 pickup)")
        return
    st["relaunch_count"] = n + 1
    st["relaunch_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    st["last_status"] = (verdict or {}).get("status", "crash-no-verdict")
    write_json(st_p, st)
    os.makedirs(out_dir, exist_ok=True)
    lo = open(os.path.join(out_dir, "log-weights-relaunch-%d.out.txt" % (n + 1)), "wb")
    le = open(os.path.join(out_dir, "log-weights-relaunch-%d.err.txt" % (n + 1)), "wb")
    subprocess.Popen([PYW, script], creationflags=NO_WINDOW, stdout=lo, stderr=le)
    log("QW21 relaunch #%d fired (resume .parts, last_status=%s)" % (
        n + 1, (verdict or {}).get("status", "crash-no-verdict")))

try:
    qw21_selfheal()
except Exception as e:
    log("QW21 selfheal FAIL (guard core unaffected): %r" % (e,))

# ---------- 3) GPU车道: 忙/闲两跳判定 ----------
busy = procs_alive("h3_i2v_album") or procs_alive("bmc_packA_chain") or procs_alive("qwen21_weights_dl") or queue_busy() or gpu_util() >= 20
st = read_json(STATE, {})
now = time.time()
if busy:
    if st.get("idle_since"):
        st["idle_since"] = None
        write_json(STATE, st)
    log("busy, no claim") if "--verbose" in sys.argv else None
    sys.exit(0)
if not st.get("idle_since"):
    st["idle_since"] = now
    write_json(STATE, st)
    log("idle tick 1 (marking)")
    sys.exit(0)
if now - st["idle_since"] < 600:
    log("idle %.0fs (<10min, wait)" % (now - st["idle_since"]))
    sys.exit(0)

# ---------- 4) 闲置>=10min: 从工作银行认领首个就绪活 ----------
bank = read_json(BANK, {"jobs": []})
claimed = None
for job in bank.get("jobs", []):
    if job.get("status") != "pending":
        continue
    req = job.get("require", {})
    ok = True
    for d, pat, n in req.get("files_at_least", []):
        cnt = len([f for f in os.listdir(os.path.join(REPO, d)) if f.endswith(pat)]) if os.path.isdir(os.path.join(REPO, d)) else 0
        if cnt < n:
            ok = False
            break
    if ok:
        claimed = job
        break
if not claimed:
    log("idle >=10min but bank EMPTY -- PRODUCER VIOLATION (预挂律)")
    sys.exit(0)
claimed["status"] = "claimed"
claimed["claimed_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
for job in bank["jobs"]:
    if job.get("id") == claimed["id"]:
        job.update(claimed)
write_json(BANK, bank)
# C2075 root-fix: log dir missing -> open() crashed AFTER the bank was flipped to
# claimed, leaving a dead-claimed job the guard can never re-claim (13:21 latentsync-deploy
# live case: no log line, no fire, 4x PRODUCER-VIOLATION after). makedirs first; any
# failure rolls the job back to pending so the next cycle retries instead of stalling.
try:
    os.makedirs(os.path.dirname(os.path.join(REPO, claimed["log_out"])), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.join(REPO, claimed["log_err"])), exist_ok=True)
    lo = open(os.path.join(REPO, claimed["log_out"]), "wb")
    le = open(os.path.join(REPO, claimed["log_err"]), "wb")
    subprocess.Popen(claimed["cmd"], creationflags=NO_WINDOW, stdout=lo, stderr=le)
except Exception as e:
    for job in bank["jobs"]:
        if job.get("id") == claimed["id"]:
            job["status"] = "pending"
            job["rearm_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            job["rearm_note"] = "guard fire-fail rollback: %r" % (e,)
    write_json(BANK, bank)
    log("FIRE-FAIL rollback->pending: %s %r" % (claimed["id"], e))
    sys.exit(1)
idle_min = (now - (st.get("_idle_since") or now)) / 60
st["idle_since"] = None
st["last_claim"] = claimed["id"]
write_json(STATE, st)
log("CLAIMED+FIRED: %s (idle %.1f min)" % (claimed["id"], idle_min))
