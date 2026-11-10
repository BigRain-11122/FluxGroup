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
import re
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
    "bm-a": {"name_cn": "公司生产力", "needs": ["cpu", "gpu"], "ram_floor_gb": 1.0, "gpu_hours": (9, 19),
             # CEO 2026-10-29: this is his WORK machine - full load only at night.
             # 09:00-19:00 weekdays it takes nothing unless a job is marked day_ok.
             "quiet_hours": (9, 19),
             "enabled": True, "ram_gb": 94, "vram_gb": 12, "cuda": True,
             "os": "windows",
             "caps": ["cpu", "kf768", "i2v768", "audio", "assemble", "llm"],
             "llm": {"endpoint": "http://127.0.0.1:11434",
                     # 跨机一律走网关（8792）：裸 11434 无认证无白名单，任何机器
                     # 都能要求 35B 或把对照档拉起来顶掉常驻（2026-11-08 实锚）。
                     "fallback": "http://100.75.133.10:8792",
                     "token_env": "FLUX_LLM_TOKEN"},
             "roles": "hq-central night gpu", "game_launch_ok": False},
    "bm-b": {"name_cn": "小钢炮", "needs": ["cpu", "gpu"], "ram_floor_gb": 2.0, "gpu_hours": None,
             "enabled": True, "ram_gb": 24, "vram_gb": 8, "cuda": True,
             "os": "windows",
             "caps": ["cpu", "animatic480", "audio", "tts", "llm"],
             "llm": {"endpoint": "http://127.0.0.1:11434",
                     # 跨机一律走网关（8792）：裸 11434 无认证无白名单，任何机器
                     # 都能要求 35B 或把对照档拉起来顶掉常驻（2026-11-08 实锚）。
                     "fallback": "http://100.75.133.10:8792",
                     "token_env": "FLUX_LLM_TOKEN"},
             "roles": "cpu sound / small gpu", "game_launch_ok": False},
    # 绰号唯一来源就在这张表：bm-c=传家宝（16GB 显卡的出图/归集/验收机）、bm-b=小钢炮。
    # 2026-11-08 实测 comms_check.py / lib_consolidate.py / ARCHITECTURE-v2 曾把两者整套写反，
    # 判据=派给传家宝的活含 16G LoRA/ComfyUI/36 图标，8GB 的 bm-b 做不了。别在别处再定义绰号。
    "bm-c": {"name_cn": "传家宝", "needs": ["cpu", "gpu"], "ram_floor_gb": 1.0, "gpu_hours": None,
             "enabled": True, "ram_gb": 24, "vram_gb": 16, "cuda": True,
             "os": "windows",
             "caps": ["cpu", "kf768", "i2v768", "audio", "render", "llm"],
             "llm": {"endpoint": "http://127.0.0.1:11434",
                     # 跨机一律走网关（8792）：裸 11434 无认证无白名单，任何机器
                     # 都能要求 35B 或把对照档拉起来顶掉常驻（2026-11-08 实锚）。
                     "fallback": "http://100.75.133.10:8792",
                     "token_env": "FLUX_LLM_TOKEN"},
             "roles": "gpu production", "game_launch_ok": False},
    # bm-m is a full agent, not a thin client: M1 Pro 32GB runs local models (MLX/Ollama),
    # so it takes text work as well as iOS builds. No CUDA, so never a GPU job.
    # bm-m is the CONTROL PLANE, not a worker (CEO 2026-10-29: 只做调度和 agent 中心,
# 不干重活、不占硬盘). It runs the master, the bus client and light text jobs; it must
# never receive media production, backtests or anything that writes large files.
    "bm-m": {"name_cn": "MacBook Pro", "needs": ["cpu"], "ram_floor_gb": 2.0, "gpu_hours": None,
             "enabled": True, "pending": False, "auto_join": True,
             "ram_gb": 32, "vram_gb": 0, "cuda": False,
             "os": "darwin",
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
             "os": "windows",
             "caps": ["cpu", "kf768", "i2v768", "backtest", "brain", "llm"],
             "llm": {"endpoint": "http://127.0.0.1:11434",
                     # 跨机一律走网关（8792）：裸 11434 无认证无白名单，任何机器
                     # 都能要求 35B 或把对照档拉起来顶掉常驻（2026-11-08 实锚）。
                     "fallback": "http://100.75.133.10:8792",
                     "token_env": "FLUX_LLM_TOKEN"},
             "roles": "brain / backtest / batch", "game_launch_ok": False},
}

# 模型名唯一来源=cph4/fleet/LOCAL-MODEL-POLICY.json（2026-11-03 实测：同一个"现役模型"
# 曾在 6 个工具里各写一遍，改策略不生效）。这里只覆盖本机控制面的 llm.model，读不到就保留原值。
try:
    import model_policy as _mp
    _m = _mp.resident()
    if _m:
        LANES["bm-m"]["llm"]["model"] = _m
except Exception:
    pass

ACTIVE_LANES = [n for n, v in LANES.items() if v.get("enabled")]
def node_os(node):
    return ((LANES.get(node) or {}).get("os") or "").lower()


_WIN_PATH_RE = re.compile(r"(^|[\s\"'\-(])[A-Za-z]:[\\/]")
_WIN_CMD_RE = re.compile(r"(^|[\s\"/])powershell(\.exe)?\b", re.I)

# Trees that only exist on a production box. The control plane (bm-m) keeps a sparse
# checkout: Tools/ and cph4/, never media/ quant/ gaming/. A command that reads from
# those can only run where that tree really is.
_LOCAL_TREE_PREFIXES = ("media/", "quant/", "gaming/", "content/", "assets/")
_INPUT_FLAGS = ("--dir", "--in", "--inbox", "--input", "--src", "--from", "-i")
_OUTPUT_FLAGS = ("--out", "--outdir", "--output", "-o", "--to")


def infer_node_os(card):
    """Infer the required OS when a card forgets to declare node_os.

    Why: 2026-11-03 - C-TTS-QC-ALL / C-INFRA-AUDIT-* were pinned to Windows boxes, the
    pinned lane was busy, lane_agent fell back to the Mac, and every run died with
    E-INPUT (missing media/, or a C:/ path that does not exist). The receipts proved it
    three times each. A card carrying a Windows drive path or invoking powershell is a
    Windows card whether or not it says so.
    """
    card = card or {}
    want = str(card.get("node_os") or "").lower()
    if want:
        return want
    blob = " ".join(str(card.get(k) or "") for k in ("cmd", "cwd", "deliverable"))
    if _WIN_PATH_RE.search(blob) or _WIN_CMD_RE.search(blob) or ".cmd" in blob.lower():
        return "windows"
    if "python3 " in blob or "python3/" in blob:
        # 2026-11-04 bm-b hygiene (discipline law clause 6): python3 exists on no Windows
        # box in this fleet - CHK-RECEIPT-20261103 fell back to bm-b and died rc=9009 twice.
        return "macos"
    return ""


def _norm_os(x):
    """OS 名称归一（2026-11-05 实测 bug）：推断侧返回 "macos"，车道表里写的是
    platform.system() 的 "darwin"——两者不相等，于是所有 cmd 含 python3 的卡在这台
    Mac 上永远被判"不属于本机 OS"，一条都跑不了。"""
    x = str(x or "").lower()
    return {"darwin": "macos", "osx": "macos", "win32": "windows", "win": "windows"}.get(x, x)


def card_os_ok(card, node):
    """A card that must run on one OS may only run there.

    `nodes` is a preference and may fall back to any capable lane - right for capacity,
    wrong for "audit the Windows box's ollama". On 2026-11-03 three Windows audit cards
    fell back to the Mac three times and each guard BLOCKED receipt was booked as
    delivery. Cards that depend on the machine's own OS declare node_os and wait; cards
    that forget are inferred from their command.
    """
    want = _norm_os(infer_node_os(card))
    return (not want) or _norm_os(node_os(node)) == want


def implicit_inputs(card):
    """Production paths a command reads without declaring them in `requires`.

    Why: the same 2026-11-03 incident. `--dir media/drama-tts-out` was a hard input but
    the card had `requires: []`, so a box with no media/ tree still claimed it and wrote
    a MISSING receipt. Deriving input paths makes "this box cannot see the data" a skip
    instead of a failure. A card that really generates the tree can opt out with
    remote_data: true; output flags are never treated as inputs.
    """
    card = card or {}
    if card.get("remote_data"):
        return []
    toks = str(card.get("cmd") or "").replace('"', " ").replace("'", " ").split()
    out = []
    for i, tok in enumerate(toks):
        t = tok.strip().replace("\\", "/")
        flag = t.lower()
        if flag in _OUTPUT_FLAGS:
            continue
        cand = None
        if flag in _INPUT_FLAGS and i + 1 < len(toks):
            cand = toks[i + 1].strip().replace("\\", "/")
        elif not t.startswith("-"):
            cand = t
        if not cand:
            continue
        cand = cand.lstrip("./").rstrip("/")
        if cand.startswith(_LOCAL_TREE_PREFIXES) and not cand.startswith("cph4/"):
            if cand not in out:
                out.append(cand)
    return out


def requires_bin_ok(card):
    """Card-declared binaries must exist on the executing box (ffmpeg lesson).

    Why: asset_dataset_audit / voice_corpus_prep ran on the Mac and returned
    "没有 ffmpeg" - a capability fact that was knowable in advance. Declaring
    `requires_bin` turns it into a skip on boxes that cannot do the job, instead of a
    failed card that has to be requeued by hand.
    """
    import shutil as _sh
    for b in (card or {}).get("requires_bin") or []:
        if _sh.which(b) is None:
            return False
    return True


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
    # 2026-11-10 CEO-PROXY 事件班：共享队列在并发 merge 时会被并集写入同 id 两行
    # （主控脉每轮 merge 都可能再引入，清一次又长回来）。读端按 id 收敛为最后一条、
    # 位置取首次出现，让重复行对全体消费者无害；写端仍走 merge_jsonl 的 collapse。
    index = {}
    out = []
    for r in rows:
        if isinstance(r, dict) and r.get("id") is not None:
            k = r["id"]
            if k in index:
                out[index[k]] = r
                continue
            index[k] = len(out)
        out.append(r)
    return out


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


def normalize_line(r):
    """把卡面的 line 归一成 LINE-REGISTRY 里的真 id（唯一归一入口，2026-11-03）。

    实测：I1 的不合规卡全部来自"生成器各写各的"——backlog_fill 把 voicebank 写进卡，
    而 registry 里只有 asset-lib；night_fill/workgen 生成的基建卡干脆不带 line。
    逐个改生成器=打地鼠，改在唯一写入口（merge_jsonl）才是一次性。

    规则只有两条，都可解释：
      1. 旧线名 → 现役 id（别名表；未登记的新名一律不猜）
      2. 基建类卡（无 line）→ fleet-ops（它们确实是平台运维活，不是业务产出）
    不做的是：不按标题猜业务线，不给业务卡编 line——猜错比缺失更坏。
    """
    if not isinstance(r, dict):
        return r
    ALIAS = {
        "voicebank": "asset-lib",
        "voice": "asset-lib",
        "quant": "bigmoney",
        "mv": "bigstream-mv",
        "duanju": "bigstream-duanju",
        "drama": "bigstream-drama",
        "car-gaming": "car-gaming",
        "city": "fluxverse",
    }
    ln = (r.get("line") or "").strip()
    if ln in ALIAS:
        r["line"] = ALIAS[ln]
        return r
    if ln:
        return r
    cid = str(r.get("id") or "")
    INFRA = ("CHK-", "CANARY-", "EVAL-", "DUPES-", "RECEIPT-", "SKILL-", "BANK-", "LINE-TRIAGE-")
    if cid.startswith(INFRA):
        r["line"] = "fleet-ops"
    # 2026-11-10 根治：prompt 型卡如果没写 model，车道不会执行（lane_agent 只认
    # model=local-small 才走本地模型），会空转到租约过期再被停线。唯一写入口补齐。
    if isinstance(r, dict) and str(r.get("prompt") or "").strip()             and not str(r.get("cmd") or "").strip() and not r.get("model"):
        r["model"] = "local-small"
        if not (r.get("nodes") or r.get("hard_nodes")):
            r["nodes"] = ["bm-m"]
    return r


LEDGER_SIBLING = {"PRODUCTION-QUEUE.jsonl": "PRODUCTION-BACKLOG.jsonl",
                  "PRODUCTION-BACKLOG.jsonl": "PRODUCTION-QUEUE.jsonl"}
# 队列是状态权威（2026-11-05 契约 §五）：备队列里同一 id 只能是同一状态的声明镜像。
LEDGER_AUTHORITY = {"PRODUCTION-QUEUE.jsonl", "PRODUCTION-BACKLOG.jsonl"}
# 能上车道执行的状态；进入这些状态却没有 cmd/prompt 的卡 = 空壳（详见 merge_jsonl 闸）
DISPATCHABLE = {"OPEN", "READY", "CLAIMED", "RUNNING"}


def _mirror_ledger(path, rows, key):
    """把本次写入的 id 状态同步到另一本账，缺行则补一行声明镜像。

    为什么（2026-11-05 十轮演练实证）：造卡器有十几个（line_agents:recurring、
    line_plan、workgen、prep_work、unlock…），每个都只写自己那本账；于是同一 id
    一边 ARCHIVED、一边 READY，A2/A7 每轮先红，自愈只是把红刷掉，漂移照样复发。
    修单个造卡器只能修一处，正法是在唯一写入口做镜像：谁写都要两本账同镜。
    """
    sib = os.path.join(os.path.dirname(path), LEDGER_SIBLING[os.path.basename(path)])
    try:
        cur = read_jsonl(sib)
    except Exception:
        return
    idx = {}
    for i, r in enumerate(cur):
        if isinstance(r, dict) and r.get(key) is not None:
            idx[r[key]] = i
    upd, auth_is_queue = [], os.path.basename(path) == "PRODUCTION-QUEUE.jsonl"
    for r in rows:
        if not isinstance(r, dict) or r.get(key) is None:
            continue
        k, st = r[key], r.get("state")
        if not st or k not in idx:
            continue
        srow = cur[idx[k]]
        if isinstance(srow, dict) and srow.get("state") != st:
            m = {"state": st, "mirrored_from": "PRODUCTION-QUEUE" if auth_is_queue else
                 "PRODUCTION-BACKLOG"}
            if auth_is_queue:
                for _k in ("note", "closed_at", "error_class", "retries", "owner"):
                    if _k in r:
                        m[_k] = r[_k]
            else:
                m["note"] = "备队列声明被队列状态覆盖（队列为权威）"
            m[key] = k
            upd.append(m)
    if upd:
        merge_jsonl(sib, upd, key=key, mirror=False)


def merge_jsonl(path, rows, key="id", mirror=True):
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
            r = normalize_line(r)
            if isinstance(r, dict) and str(r.get("prompt") or "").strip() and not str(r.get("cmd") or "").strip() and not r.get("model"):
                r["model"] = "local-small"
                if not (r.get("nodes") or r.get("hard_nodes")):
                    r["nodes"] = ["bm-m"]
            if not isinstance(r, dict) or r.get(key) is None:
                continue
            k = r[key]
            if k in index:
                prev = current[index[k]]
                # Cancellation/archival is terminal (D-R271-CANCEL-RESURRECTION,
                # 2026-11-03；2026-11-07 补 ARCHIVED)：a lane that claimed the card
                # before the cancel/archive landed wrote RUNNING back over it, so the
                # same empty-input card kept burning on three boxes. Only an explicit
                # re-queue may revive it. 实锚：bigstream-mv-gate 卡 23:4x 被归档后又被
                # 旧 claim 写回 RUNNING，继续指一个不存在的成片。
                _prev_st = (prev.get("state") if isinstance(prev, dict) else None)
                if (_prev_st in ("CANCELLED", "ARCHIVED")
                        and r.get("state") in ("OPEN", "READY", "RUNNING", "CLAIMED")
                        and not r.get("requeued_by")):
                    r = dict(r)
                    r["state"] = _prev_st
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
                # Field-level inheritance (D-20261106-SHELL-CARDS, 2026-11-06): callers
                # that only touch state write {id, state, owner, note} and used to replace
                # the whole row, wiping cmd/title/nodes/line/deliverable. That is how 347
                # cards became shells (state without cmd) which the lane scans and skips -
                # the box then self-reports SELF-DISPATCH while the queue has work.
                # Missing key = "not my business, keep it"; an explicit null still clears.
                if isinstance(prev, dict):
                    r = dict(r)
                    for _k, _v in prev.items():
                        if _k not in r:
                            r[_k] = _v
                current[index[k]] = r
            else:
                index[k] = len(current)
                current.append(r)
        # Shell-card gate (D-20261106-SHELL-CARDS): a card that can be dispatched but
        # carries neither `cmd` nor `prompt` is a defect born in a writer, not a job.
        # Shipping it to a lane means the box scans it, skips it, and reports
        # SELF-DISPATCH - which is how five cards sat OPEN and were re-assigned to bm-b
        # every round with nothing to run (the E-ARTIFACT/E-INPUT noise).
        for _r in current:
            if not isinstance(_r, dict):
                continue
            _st = str(_r.get("state") or "").upper()
            if _st not in DISPATCHABLE:
                continue
            if str(_r.get("cmd") or "").strip() or str(_r.get("prompt") or "").strip():
                continue
            _r["state"] = "CARD-DEFECT"
            _r["note"] = ("CARD-DEFECT: dispatchable card without cmd/prompt "
                          "(shell card; was %s; D-20261106-SHELL-CARDS)" % _st)
        write_jsonl(path, current)
        if mirror and os.path.basename(path) in LEDGER_AUTHORITY:
            try:
                _mirror_ledger(path, rows, key)
            except Exception:
                pass
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
# 熔断（2026-11-07 实测）：hub 不可达时 create_connection 每次要等满 timeout，
# 而 master 一轮要 kv_get 8 次 → 单阶段白烧 36s（占整轮一半）。这里按 host 记
# 失败时间：失败后 180 秒内所有调用立即失败，不再逐个等超时；到期自动重试一次。
_HUB_DOWN = {}          # (host, port) -> 到期时间戳
HUB_COOLDOWN_S = 180.0


def hub_down(host, port):
    return _HUB_DOWN.get((host, port), 0) > time.time()


def hub_mark_down(host, port):
    _HUB_DOWN[(host, port)] = time.time() + HUB_COOLDOWN_S


def hub_mark_up(host, port):
    _HUB_DOWN.pop((host, port), None)


def _nats_connect(host, port, timeout=3.0):
    """建连并完成 NATS 握手；任何失败都记入熔断，避免同一轮反复等超时。

    实测（2026-11-07）：hub 上 TCP 能连但服务器不回 INFO，失败点在 recv 而不是
    create_connection；只对连接异常记熔断等于没记——8 次 kv_get 仍各等 1 秒。
    """
    if hub_down(host, port):
        raise ConnectionError("nats hub cooling down after failure (%s:%s)" % (host, port))
    try:
        s = socket.create_connection((host, port), timeout)
        s.settimeout(timeout)
        buf = b""
        while b"\r\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                raise ConnectionError("nats closed during INFO")
            buf += chunk
        s.sendall(b'CONNECT {"verbose":false,"pedantic":false}\r\n')
    except Exception:
        hub_mark_down(host, port)
        raise
    hub_mark_up(host, port)
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
        # 2026-11-06 实测修正：macOS/Linux 的 loadavg 包含「不可中断 I/O 等待」，一个
        # 狂扫磁盘的系统进程就能把 load 顶到 ≥cores，本函数报 100%，master 的
        # CPU-SATURATED 闸随即停掉全部 CPU 活——bm-m 车道因此整天 LANE-IDLE 而机器
        # 实际只有 13% 忙（同一刻实测：loadavg 6.98/10 核 = 70%，ps 口径 13%）。
        # 改为实测 CPU 忙占比（各进程 %cpu 之和 / 核数），ps 不可用时再退回 loadavg。
        try:
            import subprocess
            out = subprocess.run(["ps", "-Ao", "pcpu="], capture_output=True,
                                 text=True, timeout=10).stdout
            tot = 0.0
            for x in out.split():
                try:
                    tot += float(x)
                except Exception:
                    pass
            busy = int(round(min(100.0, tot / cores)))
            if busy >= 0:
                return busy
        except Exception:
            pass
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
        # 跨机端点必须带令牌：2026-11-08 实测这里每 20-60 秒打一次 /api/tags 不带 header，
        # 一晚上被网关拒了 800+ 次（日志 UA=Python-urllib），既是噪音也让人误判"网关坏了"。
        req = urllib.request.Request(endpoint.rstrip("/") + "/api/tags")
        if "127.0.0.1" not in endpoint and "localhost" not in endpoint:
            try:
                import llm_client
                _t = llm_client.token()
                if not _t:
                    return []          # 没钥匙就不发请求（缺料，不是故障）
                req.add_header("X-Flux-Token", _t)
            except Exception:
                pass
        with urllib.request.urlopen(req, timeout=timeout) as r:
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
        if "127.0.0.1" not in u and "localhost" not in u:
            # 跨机一律走网关客户端：它会带 X-Flux-Token，没令牌就地判缺料(rc=3)、
            # 不再空打。2026-11-08 实锚：这里的回落没有令牌头，一天被拒 830 次。
            import llm_client
            r = llm_client.generate(prompt, model=model, endpoint=u, timeout=timeout)
            if r.get("ok"):
                return r.get("text")
            continue
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
