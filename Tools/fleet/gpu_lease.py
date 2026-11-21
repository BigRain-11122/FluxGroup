#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gpu_lease.py — 一块 GPU 一把租约：训练 / 嵌入 / 自举 不许同时抢。

为什么要有（2026-11-21 实测）：训练循环每 5 分钟挑一段，自举和嵌入又各自起进程，
三者抢同一块 GPU。实测训练从 **10 步/分 掉到 3.3 步/分**（同样的 iters 从 45 分钟变 2.5 小时），
而且两个 mlx_lm 同时跑还有 OOM 风险。以前没人管，是因为"谁先起谁占"。

设计：文件锁 + 租约记录（租约只是为了让人能看见谁占着、多久了；真锁靠 flock）。
  · 拿不到就**不抢**：调用方立刻返回"让路"，而不是排队——队也不是它该排的东西。
  · 租约带 TTL：进程被 kill -9 时文件会留旧记录，超过 TTL 视为失效，后面的人可以拿。
  · 同一进程拿同一名字可重入（避免嵌套调用自己锁死自己）。

用法
  import gpu_lease as g
  got, why = g.acquire("train", ttl_s=7200)
  if not got: print(why); return 0
  try: ...
  finally: g.release("train")
  python3 Tools/fleet/gpu_lease.py --status
  python3 Tools/fleet/gpu_lease.py --self-test
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
LOCK = os.path.join(STATE, "gpu.lock")
REC = os.path.join(STATE, "gpu-lease.json")

_handles = {}      # name -> 打开的锁文件句柄（进程内保活）
DEPTH = {}         # name -> 重入计数


def _read():
    try:
        return json.load(open(REC, encoding="utf-8"))
    except Exception:
        return {}


def _write(d):
    os.makedirs(STATE, exist_ok=True)
    tmp = REC + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, REC)


def who():
    """当前租约（含龄期；过期的不算）。"""
    d = _read()
    now = time.time()
    if not d:
        return None
    if float(d.get("expires") or 0) < now:
        return dict(d, stale=True, age_s=round(now - float(d.get("ts") or now), 1))
    return dict(d, stale=False, age_s=round(now - float(d.get("ts") or now), 1))


def acquire(name, ttl_s=3600, wait_s=0):
    """拿租约。返回 (是否拿到, 说明)。wait_s=0 表示不排队，拿不到就让路。"""
    if DEPTH.get(name):
        DEPTH[name] += 1
        return True, "重入（同一进程已持有）"
    os.makedirs(STATE, exist_ok=True)
    fh = open(LOCK, "a+")
    deadline = time.time() + max(0, wait_s)
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.time() >= deadline:
                cur = who()
                fh.close()
                return False, ("GPU 被占用：%s（已 %.0fs）" % (
                    (cur or {}).get("name", "未知"), (cur or {}).get("age_s", 0)))
            time.sleep(2)
    _handles[name] = fh                    # 句柄保活 = 锁保活
    DEPTH[name] = 1
    now = time.time()
    _write({"name": name, "pid": os.getpid(), "ts": now, "expires": now + ttl_s})
    return True, "拿到租约（TTL %ds）" % ttl_s


def release(name):
    if DEPTH.get(name, 0) > 1:
        DEPTH[name] -= 1
        return False
    DEPTH.pop(name, None)
    fh = _handles.pop(name, None)
    if fh is not None:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()
    d = _read()
    if d.get("pid") == os.getpid():
        _write({})
    return True


def self_test():
    """负控：同一进程重入要成功；子进程再来拿必须失败（拿不到就让路）。"""
    import subprocess
    ok1, _ = acquire("t_main", ttl_s=60)
    ok2, why2 = acquire("t_main", ttl_s=60)          # 重入
    code = subprocess.run([sys.executable, os.path.abspath(__file__), "--try", "t_child"],
                          capture_output=True, text=True).returncode
    release("t_main")
    release("t_main")                                 # 第二次应该是清空
    ok3, _ = acquire("t_main", ttl_s=60)
    release("t_main")
    ok = ok1 and ok2 and code == 3 and ok3
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "首拿": ok1, "重入": ok2,
                      "子进程被拒(rc=3)": code == 3, "释放后可再拿": ok3,
                      "重入说明": why2}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--try-acquire", dest="try_name", default="",
                    help="试拿一次（拿不到 rc=3）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.try_name:
        got, why = acquire(a.try_name, ttl_s=60)
        print(why)
        if got:
            release(a.try_name)
        return 0 if got else 3
    cur = who()
    print(json.dumps(cur or {"free": True}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
