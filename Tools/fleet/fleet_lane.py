# -*- coding: utf-8 -*-
"""fleet_lane.py - shared lane vocabulary for the master agent and the lane executors.

Why: the 2026-10-27/28 post-mortems all landed on the same sentence - "there is no
executor and no arbitration, so a signed card never becomes a job". The pieces existed
(queue_claim, backlog_fill, gpu_lease, NATS KV) but nothing owned the decision. This
module is the vocabulary both halves agree on:

  master_agent.py  decides  (single writer of PRODUCTION-QUEUE + cph4/fleet/lanes/*.json)
  lane_agent.py    executes (reads its own lane file, never writes shared state)

Single-writer is deliberate: bm-a/bm-b/bm-c are separate git clones, so two machines
claiming from the same jsonl diverge. Only the master mutates queue state; lanes report
results over NATS KV (raw protocol, no nats.exe needed on remote boxes) and the master
folds them back in.
"""
import json
import os
import socket
import time
from datetime import datetime

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
QUEUE_REL = "cph4/fleet/PRODUCTION-QUEUE.jsonl"
LANE_DIR_REL = "cph4/fleet/lanes"
BACKLOG_REL = "cph4/fleet/PRODUCTION-BACKLOG.jsonl"
RULES_REL = "cph4/fleet/WORK-RULES.jsonl"
POLICY_REL = "cph4/fleet/MODEL-POLICY.json"
JUDGMENT_REL = "cph4/fleet/dispatcher/JUDGMENT-QUEUE.jsonl"
RECEIPT_REL = "cph4/fleet/queue-receipts"
STATE_REL = "cph4/fleet/dispatcher/MASTER-STATE.json"
LOG_REL = "cph4/fleet/dispatcher/MASTER-LOG.md"

HUB_DEFAULT = "100.110.185.62"
PORT_DEFAULT = 4222
KV_BUCKET = "FLEET_STATE"

# Lane capabilities. A lane is a machine role, not a wish: `needs` is matched against
# these, `ram_floor_gb` is the minimum free RAM before the master will assign anything,
# and `gpu_hours` is the CEO work-hour yield window (bm-a is the CEO's own desktop).
#
# Hardware is recorded as measured (nvidia-smi / meminfo), not by model reputation:
#   bm-a RTX 4070 SUPER 12GB / 94GB RAM  - CEO desktop, yields 09-19 weekdays
#   bm-b RTX 3070 8GB / 24GB RAM         - 8GB card: 480p animatic + audio, not 768p
#   bm-c RTX 3070 16GB modded / 24GB RAM - production 768p; RAM is chronically tight
#   bm-m M1 Pro 32GB (MacBook)           - no CUDA: iOS builds, office, CPU text only
#   bm-d 3x V100 48GB / 256GB RAM        - assembly pending; when it joins it is the
#                                          only box that can hold 768p batches + backtests
LANES = {
    "bm-a": {"name_cn": "公司生产力", "needs": ["cpu", "gpu"], "ram_floor_gb": 3.0, "gpu_hours": (9, 19),
             # CEO 2026-10-29: this is his WORK machine - full load only at night.
             # 09:00-19:00 weekdays it takes nothing unless a job is marked day_ok.
             "quiet_hours": (9, 19),
             "enabled": True, "ram_gb": 94, "vram_gb": 12, "cuda": True,
             "caps": ["cpu", "kf768", "i2v768", "audio", "assemble", "llm"],
             "llm": {"endpoint": "http://127.0.0.1:11434", "fallback": "http://100.75.133.10:11434"},
             "roles": "hq-central night gpu", "game_launch_ok": False},
    "bm-b": {"name_cn": "小钢炮", "needs": ["cpu", "gpu"], "ram_floor_gb": 2.0, "gpu_hours": None,
             "enabled": True, "ram_gb": 24, "vram_gb": 8, "cuda": True,
             "caps": ["cpu", "animatic480", "audio", "tts", "llm"],
             "llm": {"endpoint": "http://127.0.0.1:11434", "fallback": "http://100.75.133.10:11434"},
             "roles": "cpu sound / small gpu", "game_launch_ok": False},
    "bm-c": {"name_cn": "传家宝", "needs": ["cpu", "gpu"], "ram_floor_gb": 3.0, "gpu_hours": None,
             "enabled": True, "ram_gb": 24, "vram_gb": 16, "cuda": True,
             "caps": ["cpu", "kf768", "i2v768", "audio", "render", "llm"],
             "llm": {"endpoint": "http://127.0.0.1:11434", "fallback": "http://100.75.133.10:11434"},
             "roles": "gpu production", "game_launch_ok": False},
    # bm-m is a full agent, not a thin client: M1 Pro 32GB runs local models (MLX/Ollama),
    # so it takes text work as well as iOS builds. No CUDA, so never a GPU job.
    # bm-m is the CONTROL PLANE, not a worker (CEO 2026-10-29: 只做调度和 agent 中心,
# 不干重活、不占硬盘). It runs the master, the bus client and light text jobs; it must
# never receive media production, backtests or anything that writes large files.
    "bm-m": {"name_cn": "MacBook Pro", "needs": ["cpu"], "ram_floor_gb": 2.0, "gpu_hours": None,
             "enabled": False, "pending": True, "auto_join": True,
             "ram_gb": 32, "vram_gb": 0, "cuda": False,
             "role_class": "control", "disk_free_min_gb": 20, "max_job_gb": 20,
             "caps": ["cpu", "ios-build", "text", "llm", "audio", "tts"],
             "llm": {"endpoint": "http://127.0.0.1:11434",
                     "model": "qwen3.5:4b",
                     "think": False,
                     "keep_alive": "5m", "num_ctx": 8192,
                     "why": "2026-10-30 实测(M1 Pro 32GB / Ollama 0.40.12 / num_parallel=1 / KV q8_0): 4B 8k=3.3GB 41.6 tok/s、16k=4.0GB 41.7 tok/s、1.3k prompt 预填 314 tok/s；35B-A3B 8k=22.0GB 解码 29-40 tok/s(随温度波动)但预填仅 100 tok/s、冷加载 14-21s、一驻留 swap +2GB(2.8->4.8GB)。差在内存与冷启动不在解码: 同一 1.3k prompt 端到端 8s vs 31s。控制面要判读延迟, 35B 仅人工点名按需加载。"},
             "roles": "control plane / ios / local llm / audio", "game_launch_ok": False},
    "bm-d": {"name_cn": "算力大脑", "needs": ["cpu", "gpu"], "ram_floor_gb": 4.0, "gpu_hours": None,
             "enabled": False, "pending": True, "auto_join": True,
             "ram_gb": 256, "vram_gb": 48, "cuda": True,
             "caps": ["cpu", "kf768", "i2v768", "backtest", "brain", "llm"],
             "llm": {"endpoint": "http://127.0.0.1:11434", "fallback": "http://100.75.133.10:11434"},
             "roles": "brain / backtest / batch", "game_launch_ok": False},
}

ACTIVE_LANES = [n for n, v in LANES.items() if v.get("enabled")]
# A pending box stops being theoretical the moment it reports: no code change needed when
# bm-m finishes its Tailscale join or bm-d comes out of the rack.
AUTO_JOIN = [n for n, v in LANES.items() if v.get("auto_join")]

# Hard red line 2026-10-28 (CEO): never auto-launch a packaged game. Route spawns
# through this deny list before anything runs; a job that trips it fails closed.
GAME_LAUNCH_DENY = ("unityplayer", "gimmeall", "\\build\\", "/build/", ".exe\" -screen")


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def read_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _atomic_tmp(path):
    # A fixed "<path>.tmp" crashed the contingency engine on 2026-10-30: dashboard,
    # member and master all write the same state file, so one process renamed the
    # other's temp file away (FileNotFoundError on os.replace). Unique per writer.
    return "%s.%d.%d.tmp" % (path, os.getpid(), time.time_ns())


def _lock(path, timeout=10.0, stale=180.0):
    """Cross-process guard for read-modify-write on a shared jsonl.

    The 2026-11-02 review found seven scripts rewriting the same queue with no lock, so
    every cycle silently dropped another writer's changes (lost update). A lock file with
    O_EXCL works on Windows and POSIX alike; a stale lock (crashed holder) is reclaimed.
    """
    lockp = path + ".lock"
    t0 = time.time()
    while True:
        try:
            fd = os.open(lockp, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode())
            finally:
                os.close(fd)
            return lockp
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lockp) > stale:
                    os.remove(lockp)
                    continue
            except OSError:
                pass
            if time.time() - t0 > timeout:
                raise TimeoutError("queue busy: %s" % path)
            time.sleep(0.15)


def merge_jsonl(path, rows, key="id"):
    """Commit only the rows this caller touched, merged into what is on disk right now.

    write_jsonl(dump the whole list) is how one leg erased another leg's dispatch inside
    the same pulse cycle. merge_jsonl re-reads under a lock, applies the caller's rows by
    id (new ids appended, touched ids updated, untouched ids left alone) and replaces the
    file atomically.
    """
    lockp = _lock(path)
    try:
        current = read_jsonl(path)
        # Collapse duplicates already on disk before merging (D-R270-QUEUE-DUP-ID):
        # index used to point at the LAST duplicate, so earlier copies could never be
        # replaced and every later write kept them alive - the queue grew 173 -> 314
        # rows with 129 repeated ids while each card was reported as "handled".
        index = {}
        deduped = []
        for r in current:
            if isinstance(r, dict) and r.get(key) is not None:
                k = r[key]
                if k in index:
                    deduped[index[k]] = r      # last write wins, keep original position
                    continue
                index[k] = len(deduped)
            deduped.append(r)
        current = deduped
        for r in rows:
            if not isinstance(r, dict) or r.get(key) is None:
                continue
            k = r[key]
            if k in index:
                prev = current[index[k]]
                # Cancellation is terminal (D-R271-CANCEL-RESURRECTION, 2026-11-03):
                # a lane that claimed the card before the cancel landed wrote RUNNING
                # back over CANCELLED, so the same empty-input card kept burning on
                # three boxes. Only an explicit re-queue may revive it.
                if (isinstance(prev, dict) and prev.get("state") == "CANCELLED"
                        and r.get("state") in ("OPEN", "READY", "RUNNING", "CLAIMED")
                        and not r.get("requeued_by")):
                    r = dict(r)
                    r["state"] = "CANCELLED"
                    r["cancel_kept_by"] = "fleet_lane"
                # Dispatcher card edits must survive stale write-backs
                # (D-R272-STALE-WRITEBACK-CLOBBER, 2026-11-03): a lane that claimed the
                # card before a pin landed writes its pre-edit snapshot back over it, so
                # the pin silently vanished and the card kept burning on boxes that do
                # not hold the input. Compare card_edit_ts; an older/absent stamp means
                # the caller never saw the pin, so the pin wins.
                prev_edit = prev.get("card_edit_ts") if isinstance(prev, dict) else None
                if prev_edit:
                    cur_edit = r.get("card_edit_ts")
                    if not cur_edit or str(cur_edit) < str(prev_edit):
                        r = dict(r)
                        for _k in ("requires", "nodes", "card_edit_ts", "card_edit_by"):
                            if _k in prev:
                                r[_k] = prev[_k]
                        r["pin_kept_by"] = "fleet_lane"
                current[index[k]] = r
            else:
                index[k] = len(current)
                current.append(r)
        write_jsonl(path, current)
        # 影子期（2026-11-03 S1）：每一行变化同时记一条事件。只写不读，生产不再等它；
        # 任何异常都吞掉——事件日志坏了不许影响派单。
        try:
            import flux_eventlog as _ev
            for r in rows:
                if not isinstance(r, dict) or r.get(key) is None:
                    continue
                cid = str(r.get(key))
                pay = {k: r.get(k) for k in ("state", "line", "owner", "rc", "title",
                                             "deliverable", "created_by", "created_at",
                                             "finished_at") if r.get(k) is not None}
                _ev.emit("CARD", cid, r.get("owner") or "", 1, pay)
                if str(r.get("state") or "").upper() in ("RUNNING", "CLAIMED") and r.get("owner"):
                    _ev.emit("CLAIM", cid, r.get("owner"), 1, pay)
        except Exception:
            pass
        return len(rows)
    finally:
        try:
            os.remove(lockp)
        except OSError:
            pass


def prune_jsonl(path, keep):
    """Delete rows under the same lock as merge_jsonl, so the single writer stays single.

    Canary cards and archived rows accumulate; rewriting the file outside the lock is how
    one leg silently restores rows another leg just deleted. keep(row) -> True to retain.
    """
    lockp = _lock(path)
    try:
        current = read_jsonl(path)
        kept = [r for r in current if keep(r)]
        write_jsonl(path, kept)
        return len(current) - len(kept)
    finally:
        try:
            os.remove(lockp)
        except OSError:
            pass


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = _atomic_tmp(path)
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = _atomic_tmp(path)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def lane_file(root, node):
    return os.path.join(root, LANE_DIR_REL.replace("/", os.sep), node + ".json")


def origin_blob(root, rel, timeout=60):
    """Read a file straight from origin/main so a dirty worktree cannot block intake.

    Same reason fleet_agent.py does it: on 2026-10-28 a diverged worktree stopped order
    intake for 11h. Lane intake has the identical failure mode.
    """
    import subprocess
    try:
        p = subprocess.run(["git", "-C", root, "show", "origin/main:" + rel],
                           capture_output=True, timeout=timeout)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.decode("utf-8-sig", "replace")
    except Exception:
        pass
    return None


def lane_payload(root, node, fetch=True):
    """The master's assignment for this node: whichever face is NEWEST wins.

    Origin is preferred because a diverged worktree must not block intake, but on the
    master's own box the local file is written seconds ago and origin lags a push - taking
    origin there hands the lane a stale assignment (2026-10-29, caught in policy test).
    """
    if fetch:
        import subprocess
        try:
            subprocess.run(["git", "-C", root, "fetch", "--quiet", "origin", "main"],
                           timeout=120, capture_output=True)
        except Exception:
            pass
    candidates = []
    raw = origin_blob(root, LANE_DIR_REL + "/" + node + ".json")
    if raw is not None:
        candidates.append(("origin", raw))
    p = lane_file(root, node)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8-sig") as f:
                candidates.append(("worktree", f.read()))
        except Exception:
            pass
    best = None
    for face, text in candidates:
        try:
            obj = json.loads(text)
        except Exception:
            continue
        ts = str(obj.get("ts") or "")
        if best is None or ts >= best[0]:
            best = (ts, face, obj)
    return best[2] if best else None


# ---- NATS raw protocol (no exe required on remote nodes) -------------------------
def _nats_connect(host, port, timeout=3.0):
    s = socket.create_connection((host, port), timeout)
    s.settimeout(timeout)
    buf = b""
    while b"\r\n" not in buf:
        chunk = s.recv(4096)
        if not chunk:
            raise ConnectionError("nats closed during INFO")
        buf += chunk
    s.sendall(b'CONNECT {"verbose":false,"pedantic":false}\r\n')
    return s


def kv_put(key, obj, host=HUB_DEFAULT, port=PORT_DEFAULT, timeout=3.0):
    """Write FLEET_STATE.<key>. KV subjects are plain publishes once the bucket exists."""
    try:
        s = _nats_connect(host, port, timeout)
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        subject = ("$KV.%s.%s" % (KV_BUCKET, key)).encode()
        s.sendall(b"PUB " + subject + b" " + str(len(data)).encode() + b"\r\n" + data + b"\r\nPING\r\n")
        s.close()
        return True
    except Exception:
        return False


def lane_result_key(node):
    return "lane.result.%s" % node


def kv_get(key, host=HUB_DEFAULT, port=PORT_DEFAULT, timeout=3.0):
    """Read FLEET_STATE.<key> with the raw protocol (JetStream direct get).

    Why raw: the Mac must be able to run the master, and there is no nats.exe there (and
    no reason to ship a Windows binary to it). Direct get is enabled on the bus, verified
    2026-10-29; if it ever returns an error this returns None and the caller treats the
    node as unseen rather than inventing a state.
    """
    try:
        s = _nats_connect(host, port, timeout)
        inbox = "_INBOX." + os.urandom(6).hex()
        s.sendall(("SUB %s 1\r\n" % inbox).encode())
        subject = "$JS.API.DIRECT.GET.KV_%s.$KV.%s.%s" % (KV_BUCKET, KV_BUCKET, key)
        s.sendall(("PUB %s %s 0\r\n\r\n" % (subject, inbox)).encode())
        end = time.time() + timeout
        buf = b""
        while time.time() < end:
            while b"\r\n" not in buf:
                chunk = s.recv(65536)
                if not chunk:
                    return None
                buf += chunk
            line, buf = buf.split(b"\r\n", 1)
            if line.startswith(b"MSG "):
                n = int(line.split()[-1])
                while len(buf) < n:
                    buf += s.recv(65536)
                txt = buf[:n].decode("utf-8", "replace")
                s.close()
                return None if '"error"' in txt[:80] else json.loads(txt)
        s.close()
    except Exception:
        pass
    return None


# ---- admission ----------------------------------------------------------------
def cpu_load_pct(root, node):
    """CPU busy percentage, or None when it genuinely cannot be measured.

    Why (2026-11-02): every lane published ram_free_gb but no CPU at all, so the master
    could only aim work by RAM and VRAM - local CPU capacity sat unused while the boxes
    looked "unknown". The straight `os.getloadavg()` fix only works on macOS: Windows has
    no such call, so the except-branch swallowed it and the field stayed null on all three
    Windows nodes. Windows is therefore derived from GetSystemTimes deltas against the
    previous sample (Windows has no instantaneous CPU counter).
    """
    try:
        cores = os.cpu_count() or 1
    except Exception:
        cores = 1
    if os.name != "nt":
        try:
            return int(round(100.0 * min(os.getloadavg()[0], cores) / cores))
        except Exception:
            return None
    # Separate sample file from fleet_hb's: two writers sharing one sample would each
    # consume the other's timestamp and halve every delta window.
    try:
        import ctypes

        class FILETIME(ctypes.Structure):
            _fields_ = [("lo", ctypes.c_uint), ("hi", ctypes.c_uint)]

        def _ticks(ft):
            return (ft.hi << 32) + ft.lo

        idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle),
                                                     ctypes.byref(kernel),
                                                     ctypes.byref(user)):
            return None
        cur = {"idle": _ticks(idle), "total": _ticks(kernel) + _ticks(user)}
        path = os.path.join(root or ROOT_DEFAULT, "Tools", "nats", "data",
                            "cpusample-lane.%s.json" % node)
        prev = None
        try:
            with open(path, encoding="utf-8") as f:
                prev = json.load(f)
        except Exception:
            pass
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cur, f)
        except Exception:
            pass
        if prev and cur["total"] > prev.get("total", 0):
            d_total = cur["total"] - prev["total"]
            d_idle = cur["idle"] - prev.get("idle", 0)
            return int(round(100.0 * (d_total - d_idle) / d_total))
    except Exception:
        pass
    return None


def game_launch_blocked(cmd):
    low = (cmd or "").lower()
    return any(bad in low for bad in GAME_LAUNCH_DENY)


def ram_gate(node, ram_free_gb):
    floor = float((LANES.get(node) or {}).get("ram_floor_gb") or 2.0)
    if ram_free_gb is None:
        return True, "ram-unknown"
    return (float(ram_free_gb) >= floor), "ram %.1f/%.1f GB" % (float(ram_free_gb), floor)


def gpu_window_open(node, when=None):
    """bm-a yields the GPU to the CEO during work hours (09:00-19:00 weekdays)."""
    win = (LANES.get(node) or {}).get("gpu_hours")
    if not win:
        return True
    d = when or datetime.now()
    if d.weekday() >= 5:
        return True
    return not (win[0] <= d.hour < win[1])


def quiet_hours(node, when=None):
    win = (LANES.get(node) or {}).get("quiet_hours")
    if not win:
        return None
    d = when or datetime.now()
    if d.weekday() >= 5:
        return None
    return win if win[0] <= d.hour < win[1] else None


def heavy_allowed(node, when=None):
    """bm-a is the CEO's own desktop: heavy CPU work there also yields 09:00-19:00 weekdays
    (machine-state / AutoYield law: '工作日工作时间把本机算力给我腾出来')."""
    if node != "bm-a":
        return True
    d = when or datetime.now()
    if d.weekday() >= 5:
        return True
    return not (9 <= d.hour < 19)


# ---- model policy (CEO 2026-10-29: master = smartest, lanes = local/cheap) --------
def load_policy(root):
    return read_json(os.path.join(root, POLICY_REL.replace("/", os.sep)), {}) or {}


def _llm_tags(endpoint, timeout=5):
    """Available model names on that box, largest first. Lets a new machine (the Mac) join
    without hardcoding a model name we only guessed."""
    import urllib.request
    try:
        with urllib.request.urlopen(endpoint.rstrip("/") + "/api/tags", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        models = data.get("models") or []
        models.sort(key=lambda m: int(m.get("size") or 0), reverse=True)
        return [m.get("name") for m in models if m.get("name")]
    except Exception:
        return []


def local_llm(prompt, policy=None, timeout=120, node=None):
    """Ask that box's own model. Cheap tier for text work; returns text or None.

    Endpoint/model come from the lane record first, so bm-m (MLX) and bm-d (35B) can differ
    from bm-a. If the configured model is absent, the largest installed one is used -
    hardware changes should not need a code edit. A lane that cannot reach a local model
    fails loudly instead of quietly escalating to a paid cloud call.
    """
    import urllib.request
    pol = (policy or {}).get("lane_local_llm") or {}
    spec = (LANES.get(node or "") or {}).get("llm") or {}
    base = spec.get("endpoint") or pol.get("endpoint") or "http://127.0.0.1:11434"
    model = spec.get("model") or pol.get("model") or ""
    if not model:
        have = _llm_tags(base)
        model = have[0] if have else ""
    # keep_alive: a resident 4B pinned its whole context into 7.5GB of a 12GB card on the
    # CEO's work machine (2026-10-29). Ask for a short lease and a small context so the
    # model gives the VRAM back when nobody is using it.
    _pol = (policy or {}).get("lane_local_llm", {}) or {}
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       # lane spec wins over policy: bm-m keeps its model hot forever,
                       # bm-a/b stay at the conservative 5m lease for their 12GB cards.
                       "keep_alive": spec.get("keep_alive", _pol.get("keep_alive", "5m")),
                       "think": spec.get("think", True),
                       "options": {"num_ctx": int(spec.get("num_ctx", _pol.get("num_ctx", 4096)))},
                       }).encode()
    urls = [base]
    fb = spec.get("fallback") or pol.get("fallback")
    if fb:
        urls.append(fb)          # shared brain: bm-m's resident 35B, reachable over Tailscale
    for u in urls:
        req = urllib.request.Request(u.rstrip("/") + "/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            out = (data.get("response") or "").strip()
            if out:
                return out
        except Exception:
            continue            # own box down -> shared brain; both down -> None (loud)
    return None