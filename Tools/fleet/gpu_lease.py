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


ENV_KEY = "FLUX_GPU_LEASE"


def _inherited_names():
    return {x for x in (os.environ.get(ENV_KEY) or "").split(":") if x}


def _mark_inherited(name):
    names = _inherited_names() | {name}
    os.environ[ENV_KEY] = ":".join(sorted(names))


def acquire(name, ttl_s=3600, wait_s=0):
    """拿租约。返回 (是否拿到, 说明)。wait_s=0 表示不排队，拿不到就让路。

    继承（2026-11-21 实锚）：常驻会话父进程持着 publish 去起 practice_tick 子进程出稿，
    子进程又来抢同一把锁 → 自己把自己锁死，每条评论都被判 gpu-busy 跳过，
    **而且 rc=0 看着像成功**——闭环断在这里一整天都没人发现。
    正解：父进程拿到租约后把名字写进环境变量，子进程认这个名字为"继承"，
    既能干活，release 时也不会把父进程的锁拆掉。
    """
    if name in _inherited_names():
        DEPTH[name] = DEPTH.get(name, 0) + 1
        return True, "继承父进程的租约（%s）" % name
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
    # 2026-11-22 实锚：训练被 kill 后租约文件留了 4 小时 TTL，出稿以为"train 还在"
    # 干等 90 秒。文件锁已拿到，再看记录里的 pid 死没死——死了就是野记录，覆盖即可。
    try:
        old = _read()
        if old and old.get("pid") and old.get("name") != name:
            try:
                os.kill(int(old["pid"]), 0)
            except Exception:
                _write({})
    except Exception:
        pass
    _handles[name] = fh                    # 句柄保活 = 锁保活
    DEPTH[name] = 1
    now = time.time()
    _write({"name": name, "pid": os.getpid(), "ts": now, "expires": now + ttl_s})
    _mark_inherited(name)          # 传给子进程，避免父子互抢
    return True, "拿到租约（TTL %ds）" % ttl_s


def release(name):
    if name in _inherited_names() and name not in _handles:
        return False               # 继承来的锁不归本进程释放
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
    # 真释放后要把它从继承标记里摘掉，否则同进程再拿会同"继承"而不上锁
    names = _inherited_names() - {name}
    if names:
        os.environ[ENV_KEY] = ":".join(sorted(names))
    else:
        os.environ.pop(ENV_KEY, None)
    return True


def self_test():
    """负控四件：重入必成；**无继承**的子进程必被拒；**有继承**的子进程必放行；
    释放后可再拿。用独立车道名，免得被线上租约带红（2026-11-20 假红教训）。"""
    import subprocess
    import tempfile
    global LOCK, REC
    saved = (LOCK, REC)
    d = tempfile.mkdtemp(prefix="gl-")
    LOCK, REC = os.path.join(d, "gpu.lock"), os.path.join(d, "lease.json")
    try:
        ok1, _ = acquire("t_main", ttl_s=60)
        ok2, why2 = acquire("t_main", ttl_s=60)          # 重入
        env0 = {k: v for k, v in os.environ.items() if k != ENV_KEY}
        code_no = subprocess.run([sys.executable, os.path.abspath(__file__), "--try", "t_main"],
                                 capture_output=True, text=True, env=env0).returncode
        code_yes = subprocess.run([sys.executable, os.path.abspath(__file__), "--try", "t_main"],
                                  capture_output=True, text=True,
                                  env=dict(os.environ, **{ENV_KEY: "t_main"})).returncode
        release("t_main")
        release("t_main")
        ok3, _ = acquire("t_main", ttl_s=60)
        ok4 = os.environ.get(ENV_KEY, "").find("t_main") >= 0
        release("t_main")
    finally:
        LOCK, REC = saved
    ok = ok1 and ok2 and code_no == 3 and code_yes == 0 and ok3 and ok4
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "首拿": ok1, "重入": ok2,
                      "子进程无继承被拒(rc=3)": code_no == 3,
                      "子进程有继承放行(rc=0)": code_yes == 0,
                      "释放后可再拿": ok3, "环境已标记继承": ok4,
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
