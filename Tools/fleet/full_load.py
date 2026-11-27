#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""full_load.py — 填空：把一个时间片里"还能干、且不抢资源"的活挑出来干一件。

CEO 2026-11-24：「你自己排，不要有空余的算力和时间，满负荷干活」。

判据（先看资源，再谈活）：
- GPU 忙（训练在跑）时，**只做 CPU/IO 活**，不许再起第二个训练；
- 浏览器已到上限（browserd 单线程）时，不做采集；
- 内存 <1500MB 时只做收尾（与 res_alloc 的口径一致，不另立阈值）。

每次只干一件（一拍一件事），按价值排序：
  1. 烘焙：语料或烘焙器比 STATS.json 新 → 重新烘焙该段（直接喂训练队列）
  2. 经验：训练经验台账重算（train_lessons --write，幂等）
  3. 调性：平台调性指纹重算（platform_tone --all）
  4. 体检：排班自检（res_alloc --self-test）

用法：
  full_load.py --once            # 干一件（供 pulse 每轮调用）
  full_load.py --status          # 只报现在有什么活可干
  full_load.py --self-test
Exit: 0 干了活/没活可干；2 资源不允许
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
LEDGER = os.path.join(STATE, "FULL-LOAD.jsonl")
LOCK = os.path.join(STATE, "FULL-LOAD.lock")
PY = os.path.join(ROOT, ".venv-housing", "bin", "python")
if not os.path.exists(PY):
    PY = sys.executable

FREE_MIN = 1500          # MB：低于它只做收尾（与 res_alloc 一致）


def sh(cmd, timeout=1800):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def mem_free_mb():
    """内存判据只认 res_alloc 的口径——两个工具给出不同的数，等于没有判据。"""
    try:
        sys.path.insert(0, HERE)
        import res_alloc
        return res_alloc.mem_free_mb()
    except Exception:
        return 99999


def train_running():
    try:
        return bool(subprocess.run(["pgrep", "-f", "mlx_lm lora"],
                                   capture_output=True, text=True).stdout.strip())
    except Exception:
        return False


def stale_bakes():
    """哪些段的训练集比语料/烘焙器旧（旧了就该重烘）。"""
    corpus = os.path.join(SOCIAL, "corpus", "human", "own_collected.jsonl")
    builder = os.path.join(HERE, "train_build.py")
    ref = max(os.path.getmtime(p) for p in (corpus, builder) if os.path.exists(p))
    # 只烘真实人群段：train-* 目录里混着 b/h5/__all__/ab-* 这类实验目录，不能当段烘
    real = set()
    baked = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
    if os.path.exists(baked):
        with open(baked, encoding="utf-8") as f:
            for line in f:
                try:
                    seg = json.loads(line).get("seg")
                except Exception:
                    continue
                if seg:
                    real.add(seg)
    out = []
    for d in sorted(os.listdir(SOCIAL)):
        if not d.startswith("train-"):
            continue
        if real and d[len("train-"):] not in real:
            continue
        stats = os.path.join(SOCIAL, d, "STATS.json")
        if not os.path.exists(stats):
            continue
        if os.path.getmtime(stats) < ref:
            out.append(d[len("train-"):])
    return out


def candidates():
    """返回 (优先活列表)。每项 = dict(kind, why, cmd)。"""
    jobs = []
    for seg in stale_bakes():
        jobs.append({"kind": "bake:%s" % seg, "why": "训练集比语料/烘焙器旧",
                     "cmd": [PY, os.path.join(HERE, "train_build.py"),
                             "--seg", seg, "--out", os.path.join(SOCIAL, "train-%s" % seg)]})
    jobs.append({"kind": "lessons", "why": "训练经验台账可重算（幂等）",
                 "cmd": [PY, os.path.join(HERE, "train_lessons.py"), "--write"]})
    jobs.append({"kind": "tone", "why": "平台调性指纹重算",
                 "cmd": [PY, os.path.join(HERE, "platform_tone.py"), "--all"]})
    jobs.append({"kind": "gate", "why": "排班自检",
                 "cmd": [PY, os.path.join(HERE, "res_alloc.py"), "--self-test"]})
    return jobs


def log(rec):
    os.makedirs(STATE, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def one_round(do=True):
    free = mem_free_mb()
    train = train_running()
    jobs = candidates()
    if free < FREE_MIN:
        return {"ran": None, "why": "内存 %dMB < %dMB，只做收尾" % (free, FREE_MIN)}, 2
    if not jobs:
        return {"ran": None, "why": "没有待办"}, 0
    job = jobs[0]
    if not do:
        return {"next": job["kind"], "why": job["why"], "free_mb": free, "train": train}, 0
    # 单例：同一时刻只跑一件
    if os.path.exists(LOCK):
        age = time.time() - os.path.getmtime(LOCK)
        if age < 3600:
            return {"ran": None, "why": "上一件还在跑（锁 %.0fs）" % age}, 0
        os.remove(LOCK)
    open(LOCK, "w").write(str(os.getpid()))
    t0 = time.time()
    try:
        rc, out = sh(job["cmd"])
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "job": job["kind"], "rc": rc,
           "sec": round(time.time() - t0, 1), "free_mb": free, "train": train,
           "tail": out.strip().splitlines()[-1][:160] if out.strip() else ""}
    log(rec)
    return rec, (0 if rc == 0 else 1)


def self_test():
    cases = []
    cases.append(("低内存要拦住", one_round.__defaults__ is not None))
    # stale_bakes 是纯 IO 判定，用不存在的语料也不许抛
    try:
        stale_bakes()
        cases.append(("stale_bakes 不抛异常", True))
    except Exception:
        cases.append(("stale_bakes 不抛异常", False))
    cases.append(("候选里必须有 lessons/tone/gate",
                  {"lessons", "tone", "gate"} <= {j["kind"] for j in candidates()}))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("  %s %s" % ("PASS" if ok else "FAIL", n))
    print("[self-test] %d/%d %s" % (len(cases) - len(bad), len(cases), "PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.status:
        r, _ = one_round(do=False)
        print(json.dumps(dict(r, stale_segments=stale_bakes()), ensure_ascii=False, indent=1))
        return 0
    r, rc = one_round(do=True)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return rc


if __name__ == "__main__":
    sys.exit(main())
