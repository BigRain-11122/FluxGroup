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
RECEIPT_REL = "cph4/fleet/queue-receipts"
STATE_REL = "cph4/fleet/dispatcher/MASTER-STATE.json"
LOG_REL = "cph4/fleet/dispatcher/MASTER-LOG.md"

HUB_DEFAULT = "100.110.185.62"
PORT_DEFAULT = 4222
KV_BUCKET = "FLEET_STATE"

# Lane capabilities. A lane is a machine role, not a wish: `needs` is matched against
# these, `ram_floor_gb` is the minimum free RAM before the master will assign anything,
# and `gpu_hours` is the CEO work-hour yield window (bm-a is the CEO's own desktop).
LANES = {
    "bm-a": {"needs": ["cpu", "gpu"], "ram_floor_gb": 3.0, "gpu_hours": (9, 19),
             "enabled": True, "roles": "hq-central night gpu", "game_launch_ok": False},
    "bm-b": {"needs": ["cpu", "gpu"], "ram_floor_gb": 2.0, "gpu_hours": None,
             "enabled": True, "roles": "cpu sound / small gpu", "game_launch_ok": False},
    "bm-c": {"needs": ["cpu", "gpu"], "ram_floor_gb": 3.0, "gpu_hours": None,
             "enabled": True, "roles": "gpu production", "game_launch_ok": False},
    "bm-m": {"needs": ["cpu"], "ram_floor_gb": 2.0, "gpu_hours": None,
             "enabled": False, "roles": "master control / ios", "game_launch_ok": False},
    "bm-d": {"needs": ["cpu", "gpu"], "ram_floor_gb": 4.0, "gpu_hours": None,
             "enabled": False, "roles": "brain / backtest", "game_launch_ok": False},
}

ACTIVE_LANES = [n for n, v in LANES.items() if v.get("enabled")]

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


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
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
    tmp = path + ".tmp"
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
    """The master's assignment for this node: origin blob first, worktree as fallback."""
    if fetch:
        import subprocess
        try:
            subprocess.run(["git", "-C", root, "fetch", "--quiet", "origin", "main"],
                           timeout=120, capture_output=True)
        except Exception:
            pass
    raw = origin_blob(root, LANE_DIR_REL + "/" + node + ".json")
    if raw is None:
        p = lane_file(root, node)
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8-sig") as f:
                    raw = f.read()
            except Exception:
                return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


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


# ---- admission ----------------------------------------------------------------
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


def heavy_allowed(node, when=None):
    """bm-a is the CEO's own desktop: heavy CPU work there also yields 09:00-19:00 weekdays
    (machine-state / AutoYield law: '工作日工作时间把本机算力给我腾出来')."""
    if node != "bm-a":
        return True
    d = when or datetime.now()
    if d.weekday() >= 5:
        return True
    return not (9 <= d.hour < 19)