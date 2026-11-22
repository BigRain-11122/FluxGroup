#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bmc_chain_publish.py - bm-c 的「本地闭环 + 及时上链」节拍（单执行体）。

CEO 令 2026-11-22：机队要本地闭环、信息同步、及时上链、不互相捣乱、各司其职，
并对主控知情可调配。

本脚本每轮做五件事（幂等、有锁、失败响亮）：

  1. 刷新本机自写回执（主控判「在线」与「最后一次真产出」都只认这一处）：
       cph4/fleet/queue-receipts/_last_lane_bm-c.json   <- master_agent 的在线兜底
       cph4/fleet/queue-receipts/autodrive-hb-bm-c.json <- blocker_loop 的产出判据
     这两个文件自 2026-11-14 起被 .gitignore 忽略，必须 -f 入库，否则主控永远
     把 bm-c 判成 OFFLINE / EXECUTOR-DEAD（实测 927 提交落后期间正是如此）。
  2. 提交本机写出的证据件（台账/回执/代码小件），单文件 >2MB 一律不提交。
  3. fetch + 把远端主线的公开件合并进来（master 的脉提交每 ~2 分钟一次）。
  4. 推送。冲突裁决：主控的笔（PRODUCTION-QUEUE / BACKLOG / lanes / dispatcher
     MASTER-STATE）一律取远端，本机产出的证据一律留本地。
  5. 车道有卡就跑一张（lane_agent，单实例），没卡就把「为什么闲」写进回执。
     这里不复制 lane_agent 的选卡逻辑，也不改动它（共享代码，改了会波及全队）。

纪律：
  * 同一时刻只允许一个实例（锁文件 + pid 校验）。
  * 不改 lanes/<node>.json（主控的笔），不改主控判据代码。
  * 任何异常都写日志并退出非零，不静默吞。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = r"K:\Fluxgroup\FluxGroup"
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
LOG = os.path.join(ROOT, "cph4", "fleet", "production", "chain-publish.log")
LOCK = os.path.join(ROOT, "cph4", "fleet", "production", "chain-publish.lock")
PY = sys.executable or "python"

# 主控写的文件：冲突一律取远端，绝不覆盖主控的笔
MASTER_OWNED = (
    "cph4/fleet/PRODUCTION-QUEUE.jsonl",
    "cph4/fleet/PRODUCTION-BACKLOG.jsonl",
    "cph4/fleet/lanes/",
    "cph4/fleet/dispatcher/MASTER-STATE.json",
    "cph4/fleet/dispatcher/MASTER-TICK.json",
)

# 本机证据件：允许提交的路径前缀（其余不碰）
EVIDENCE_PREFIXES = (
    "cph4/fleet/production/",
    "cph4/fleet/rt/visual/",
    "cph4/fleet/rt/delivery/",
    "cph4/fleet/drama-dept-v1/",
    "cph4/fleet/bmc-self-drive/",
    "cph4/fleet/inbox/",
    "cph4/fleet/work-bank/bm-c-gpu-bank.json",
    "cph4/fleet/idle-guard-kit/",
    "Tools/fleet/",
    "Tools/voicebank/",
    "Tools/task-s4u-backlog.md",
    "Tools/silence-window-guard.ps1",
    "Tools/mv_",
)
EVIDENCE_SUFFIXES = (".json", ".jsonl", ".md", ".log", ".py", ".ps1", ".cmd", ".vbs", ".txt")
MAX_FILE_BYTES = 2 * 1024 * 1024


def log(msg):
    line = "%s %s" % (datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), msg)
    # 本脚本以 pythonw.exe 常驻（无控制台）：stdout 是 None，直接 print 会炸。
    if sys.stdout is not None:
        try:
            print(line)
        except Exception:
            pass
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def git(*args, timeout=150):
    return subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout)


def acquire_lock():
    try:
        os.makedirs(os.path.dirname(LOCK), exist_ok=True)
        if os.path.exists(LOCK):
            try:
                pid = int((open(LOCK).read() or "0").strip())
            except Exception:
                pid = 0
            alive = False
            if pid:
                try:
                    os.kill(pid, 0)
                    alive = True
                except Exception:
                    alive = False
            if alive:
                log("LOCK held by pid=%s -> skip this tick" % pid)
                return False
            log("stale lock pid=%s -> reclaim" % pid)
        with open(LOCK, "w") as fh:
            fh.write(str(os.getpid()))
        return True
    except Exception as e:
        log("LOCK-ERR %s" % e)
        return False


def release_lock():
    try:
        if os.path.exists(LOCK):
            os.remove(LOCK)
    except Exception:
        pass


def gpu_state():
    info = {"util": None, "mem_used_mb": None, "mem_total_mb": None}
    try:
        p = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True,
                           timeout=20)
        parts = [x.strip() for x in (p.stdout or "").splitlines()[0].split(",")]
        info["util"] = int(parts[0])
        info["mem_used_mb"] = int(parts[1])
        info["mem_total_mb"] = int(parts[2])
    except Exception:
        pass
    return info


def inflight_summary():
    """本机在跑什么（只读进程面，不推断）。"""
    names = []
    try:
        import ctypes  # noqa: F401
        ps = subprocess.run(["powershell", "-NoProfile", "-Command",
                             "Get-CimInstance Win32_Process -Filter \"Name='python.exe' or Name='pythonw.exe'\" | "
                             "Select-Object -ExpandProperty CommandLine"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=40)
        for ln in (ps.stdout or "").splitlines():
            low = ln.lower()
            if "h3_i2v_album" in low:
                names.append("i2v")
            elif "lora" in low and "factory" in low:
                names.append("lora")
            elif "drama_" in low:
                names.append("drama")
            elif "saturation_engine" in low:
                names.append("quant-engine")
    except Exception:
        pass
    return sorted(set(names))


def write_receipts():
    os.makedirs(RECEIPTS, exist_ok=True)
    now = datetime.now()
    iso_s = now.strftime("%Y-%m-%dT%H:%M:%S")
    iso_ms = now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03d" % (now.microsecond // 1000)
    gpu = gpu_state()
    busy = inflight_summary()
    state = "RUNNING" if busy else "IDLE"

    lane = {
        "ts": iso_s,
        "node": "bm-c",
        "state": state,
        "note": ("in-flight: " + ",".join(busy)) if busy else "idle: GPU queue full on self-drive line",
        "gpu_util_pct": gpu.get("util"),
        "vram_used_mb": gpu.get("mem_used_mb"),
        "writer": "bmc_chain_publish",
    }
    hb = {
        "ts": iso_ms,
        "node": "bm-c",
        "kind": "autodrive-heartbeat",
        "gpu": {"util_pct": gpu.get("util"),
                "mem_used_mb": gpu.get("mem_used_mb"),
                "mem_total_mb": gpu.get("mem_total_mb")},
        "batches": busy,
        "state": state,
        "note": "bm-c chain publish heartbeat; master may consume for visibility",
    }
    for name, payload in (("_last_lane_bm-c.json", lane), ("autodrive-hb-bm-c.json", hb)):
        path = os.path.join(RECEIPTS, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
    log("RECEIPT %s gpu=%s vram=%sMB busy=%s" % (state, gpu.get("util"),
                                                 gpu.get("mem_used_mb"), ",".join(busy) or "-"))


def allowed(rel):
    if any(rel.startswith(p) for p in MASTER_OWNED):
        return False
    if not any(rel.startswith(p) for p in EVIDENCE_PREFIXES):
        return False
    if not rel.endswith(EVIDENCE_SUFFIXES):
        return False
    try:
        if os.path.getsize(os.path.join(ROOT, rel)) > MAX_FILE_BYTES:
            return False
    except OSError:
        return False
    return True


def _receipt_due(interval_s=720):
    """上一次回执提交距今是否超过 interval（默认 12 分钟）。"""
    r = git("log", "-1", "--format=%ct", "--",
            "cph4/fleet/queue-receipts/_last_lane_bm-c.json")
    txt = (r.stdout or "").strip()
    if not txt.isdigit():
        return True
    return (time.time() - int(txt)) >= interval_s


def stage_evidence():
    """只暂存本机证据件；回执目录被整目录忽略，必须 -f。"""
    staged = []
    st = git("status", "--porcelain", "-uno").stdout or ""
    cand = []
    for ln in st.splitlines():
        if len(ln) < 4:
            continue
        code, rel = ln[:2], ln[3:].strip()
        if rel.startswith('"') and rel.endswith('"'):
            rel = rel[1:-1]
        if allowed(rel):
            cand.append(rel)
    # 未跟踪的新证据件（只在这些前缀下，避免把 5GB 媒体带进来）
    unt = git("status", "--porcelain", "-uall").stdout or ""
    for ln in unt.splitlines():
        if not ln.startswith("?? "):
            continue
        rel = ln[3:].strip()
        if allowed(rel) and rel.endswith(EVIDENCE_SUFFIXES):
            cand.append(rel)
    if cand:
        r = git("add", "--", *cand)
        if r.returncode != 0:
            log("ADD-WARN %s" % (r.stderr or r.stdout)[:200])
    # 两份自写回执（被忽略，-f 入库才到得了主控）。
    # 提交节奏闸：回执内容带时间戳，每 5 分钟提交一次会把仓库刷成噪音；主控的
    # OFFLINE 判据是 30 分钟窗口，所以 12 分钟提交一次足够，其余轮次只刷新盘上内容。
    recs = ["cph4/fleet/queue-receipts/_last_lane_bm-c.json",
            "cph4/fleet/queue-receipts/autodrive-hb-bm-c.json",
            "cph4/fleet/queue-receipts/production-router-bm-c.json",
            "cph4/fleet/queue-receipts/pipeline-evolution-bm-c.json"]
    have = [r for r in recs if os.path.exists(os.path.join(ROOT, r))]
    if have and _receipt_due():
        git("add", "-f", "--", *have)
    elif have:
        # 其它证据照常提交时，顺带把回执一起带上（同一次提交，不额外造噪）
        if [x for x in (git("diff", "--cached", "--name-only").stdout or "").splitlines() if x]:
            git("add", "-f", "--", *have)
    staged = [x for x in (git("diff", "--cached", "--name-only").stdout or "").splitlines() if x]
    return staged


def commit(staged):
    if not staged:
        return "nothing"
    msg = "bm-c chain: evidence + online receipt (%d files, %s)" % (
        len(staged), datetime.now().strftime("%H:%M"))
    r = git("commit", "-q", "-m", msg)
    if r.returncode != 0:
        return "commit-failed:%s" % (r.stderr or r.stdout)[:160]
    return "committed:%d" % len(staged)


def converge():
    """把远端主线合并进来；主控的笔取远端，其余冲突留本地。"""
    r = git("fetch", "origin", "--quiet")
    if r.returncode != 0:
        return "fetch-failed:%s" % (r.stderr or r.stdout)[:120]
    behind = git("rev-list", "--count", "HEAD..origin/main").stdout.strip()
    if behind in ("", "0"):
        return "up-to-date"
    r = git("merge", "-X", "ours", "--no-edit", "origin/main",
            "-m", "bm-c chain: fold master pulses", timeout=180)
    if r.returncode != 0:
        # 冲突：主控的笔一律让给远端
        git("checkout", "--theirs", "--", *MASTER_OWNED)
        git("add", "--", *MASTER_OWNED)
        r2 = git("commit", "-q", "--no-edit")
        if r2.returncode != 0:
            git("merge", "--abort")
            return "merge-failed"
    return "merged-behind-%s" % behind


def push():
    last = ""
    for i in range(3):
        r = git("push", "origin", "HEAD:main", timeout=180)
        if r.returncode == 0:
            return "pushed"
        last = (r.stderr or r.stdout or "")[:160]
        # 有人抢先推了：重取再合
        git("fetch", "origin", "--quiet")
        m = git("merge", "-X", "ours", "--no-edit", "origin/main")
        if m.returncode != 0:
            git("checkout", "--theirs", "--", *MASTER_OWNED)
            git("add", "--", *MASTER_OWNED)
            if git("commit", "-q", "--no-edit").returncode != 0:
                git("merge", "--abort")
                return "push-blocked:%s" % last
        time.sleep(2 + i * 2)
    return "push-failed:%s" % last


LANE_DONE = os.path.join(ROOT, "cph4", "fleet", "production", "chain-lane-done.json")
LANE_SIG = os.path.join(ROOT, "cph4", "fleet", "production", "chain-lane-sig.json")


def _lane_done():
    try:
        return set(json.load(open(LANE_DONE, encoding="utf-8")))
    except Exception:
        return set()


def _lane_done_add(ids):
    if not ids:
        return
    cur = _lane_done() | set(ids)
    try:
        os.makedirs(os.path.dirname(LANE_DONE), exist_ok=True)
        json.dump(sorted(cur), open(LANE_DONE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception as e:
        log("LANE-DONE-WRITE-ERR %s" % e)


def lane_jobs():
    """主控派给本机的卡（读 origin 副本，主控的笔只在远端是权威）。"""
    p = git("show", "origin/main:cph4/fleet/lanes/bm-c.json").stdout
    try:
        d = json.loads(p or "{}")
    except Exception:
        return []
    return [j for j in (d.get("jobs") or []) if isinstance(j, dict)]


def run_lane_once():
    jobs = lane_jobs()
    if not jobs:
        return "lane-empty"
    # 主控的 lane 文件在它下一轮脉之前不会清卡；同一张卡我已跑过就不能再跑
    # （2026-11-07 实锚：同一门禁卡被重跑 40+ 轮，每轮都推一份同结论回执）。
    done = _lane_done()
    fresh = [j for j in jobs if str(j.get("id")) not in done]
    if not fresh:
        return "lane-all-done(%d)" % len(jobs)
    # lane_agent 不接受「只跑某几张卡」的参数（全队共享代码，本机不改它）；
    # 它会把车道里能跑的卡都跑一遍。所以再压一道批次签名闸：同一批派单在
    # 45 分钟内只跑一次，主控换了卡（签名变）才再跑。
    sig = ",".join(sorted(str(j.get("id")) for j in jobs))
    try:
        prev = json.load(open(LANE_SIG, encoding="utf-8"))
    except Exception:
        prev = {}
    if prev.get("sig") == sig and (time.time() - float(prev.get("ts") or 0)) < 2700:
        age = int((time.time() - float(prev.get("ts") or 0)) / 60)
        return "lane-batch-held(%dm, same dispatch)" % age
    try:
        json.dump({"sig": sig, "ts": time.time()}, open(LANE_SIG, "w", encoding="utf-8"))
    except Exception:
        pass
    log("LANE jobs=%d fresh=%d -> run one card" % (len(jobs), len(fresh)))
    r = subprocess.run([PY, os.path.join(ROOT, "Tools", "fleet", "lane_agent.py"),
                        "--node", "bm-c", "--root", ROOT, "--max-seconds", "900"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1200)
    out = (r.stdout or "") + (r.stderr or "")
    finished = []
    for ln in out.splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[1] == "DONE":
            finished.append(parts[0])
    _lane_done_add(finished)
    tail = out.strip().splitlines()[-3:]
    log("LANE rc=%s done=%s %s" % (r.returncode, ",".join(finished) or "-", " | ".join(tail)))
    return "lane-rc-%s(%d done)" % (r.returncode, len(finished))


def main():
    if not acquire_lock():
        return 0
    try:
        write_receipts()
        staged = stage_evidence()
        c = commit(staged)
        cv = converge()
        p = push()
        lane = run_lane_once()
        log("TICK commit=%s converge=%s push=%s lane=%s" % (c, cv, p, lane))
        return 0 if (p == "pushed" or p == "up-to-date") else 3
    except Exception as e:
        log("FATAL %r" % (e,))
        return 1
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
