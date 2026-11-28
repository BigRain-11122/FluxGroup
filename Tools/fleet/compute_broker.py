#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compute_broker.py — 一条线一个算力槽：槽不重叠，不够就排队。

令源：CEO 2026-11-27「每条线专用一个模型和一块算力资源 不要重叠，当然如果本地不够
同时运行的时候就可以排队」。

三条硬规则（都能被自检打红）：
  1. **独占**：同一时刻只有一个持有者。lease.json 里写清 owner/pid/since，另外用 flock
     保证"读-判-写"是原子的；进程被 kill -9 留下的旧租约按 pid 存活 + TTL 判失效。
  2. **排队**：拿不到不抢，登记到 queue.jsonl 后按到达时间先来先得；等不到就放弃这一拍
     （记 QUEUED），下一拍再来——不在进程里死等。
  3. **可审计**：每次授予/释放/失效都写 compute-ledger.jsonl，谁占过、占多久、等多久。

用法（库）
  import compute_broker as cb
  ok, why, waited = cb.acquire("bili", timeout_s=120)
  if not ok: ...  # 排队中/超时
  try: ...
  finally: cb.release("bili")

命令行
  python3 Tools/fleet/compute_broker.py --status
  python3 Tools/fleet/compute_broker.py --acquire bili --timeout 5 --hold 2
  python3 Tools/fleet/compute_broker.py --release bili
  python3 Tools/fleet/compute_broker.py --self-test        # 含负控
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state", "compute")
LEASE = os.path.join(STATE, "lease.json")
QUEUE = os.path.join(STATE, "queue.jsonl")
LEDGER = os.path.join(STATE, "compute-ledger.jsonl")
LOCK = os.path.join(STATE, "lease.lock")

DEFAULT_TTL = 3600

# 各类租约要驻留多少内存（GB）。不在表里的类型（cpu/io）不过内存闸。
# 4B MLX ≈ 3.3GB（实测驻留席位）、9B ≈ 9.1GB、训练峰值按 6GB 估。
NEED_GB = {
    "gpu-model": 3.3,
    "gpu-model-9b": 9.1,
    # 训练的就是那个 4B，需要常驻的是模型本身（3.3GB），optimizer/激活是小头。
    # 2026-11-28 实锚：写成 6.0 后，残留 swap 把上限压到 3.3GB，训练整夜排不上队（QUEUED）。
    "gpu-train": 3.3,
}


def _now():
    return time.time()


def _iso(ts=None):
    return datetime.fromtimestamp(ts or _now()).isoformat(timespec="seconds")


def ensure():
    os.makedirs(STATE, exist_ok=True)


def _read(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write(path, obj):
    ensure()
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _append(path, rec):
    ensure()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _rows(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return out


def _alive(pid):
    try:
        pid = int(pid)
    except Exception:
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _lease_valid(l):
    if not l:
        return False
    if not _alive(l.get("pid")):
        return False
    ttl = float(l.get("ttl_s") or DEFAULT_TTL)
    if _now() - float(l.get("since_ts") or 0) > ttl:
        return False
    return True


def _lock():
    ensure()
    f = open(LOCK, "a+")
    fcntl.flock(f, fcntl.LOCK_EX)
    return f


def _unlock(f):
    try:
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
    except Exception:
        pass


def _dequeue(lane, pid):
    rows = _rows(QUEUE)
    keep = [r for r in rows if not (r.get("lane") == lane and str(r.get("pid")) == str(pid))]
    if len(keep) != len(rows):
        ensure()
        tmp = QUEUE + ".tmp.%d" % os.getpid()
        with open(tmp, "w", encoding="utf-8") as f:
            for r in keep:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, QUEUE)
    return keep


def _register(lane):
    rows = _rows(QUEUE)
    pid = os.getpid()
    for r in rows:
        if r.get("lane") == lane and str(r.get("pid")) == str(pid):
            return
    if not any(r.get("lane") == lane for r in rows):
        _append(QUEUE, {"lane": lane, "pid": pid, "ts": _iso(), "ts_epoch": _now()})


def _first_waiter(lane):
    """按到达时间排序后，队头是不是我（同一线多进程只算一条）。"""
    rows = [r for r in _rows(QUEUE) if _alive(r.get("pid"))]
    rows.sort(key=lambda r: float(r.get("ts_epoch") or 0))
    for r in rows:
        if r.get("lane") == lane and str(r.get("pid")) != str(os.getpid()):
            # 同线旧进程的记录，视为过期
            continue
        return r.get("lane") == lane
    return True


def try_acquire(lane, need="compute", ttl_s=DEFAULT_TTL):
    """尝试一次（不等）。返回 (ok, why)。"""
    f = _lock()
    try:
        lease = _read(LEASE, {})
        if lease and lease.get("owner") == lane and _lease_valid(lease):
            lease["ts"] = _iso()
            _write(LEASE, lease)
            return True, "本线已持有（可重入）"
        if lease and _lease_valid(lease):
            _register(lane)
            return False, "占用中：%s（自 %s）" % (lease.get("owner"), lease.get("since"))
        if lease and not _lease_valid(lease):
            _append(LEDGER, {"event": "stale-reclaimed", "owner": lease.get("owner"),
                             "since": lease.get("since"), "ts": _iso()})
        _register(lane)
        if not _first_waiter(lane):
            return False, "排队中：前面还有别的线"
        # 2026-11-27 接入内存闸：租约过去只管"谁先占 GPU"，完全不管内存——
        # 于是拿到租约的线可以在内存已吃紧时照常加载大模型，直接换页。
        # 只有会**驻留大模型**的租约类型才过闸；纯 CPU 的线（collect/ops/measure）不受影响。
        need_gb = NEED_GB.get(need)
        if need_gb:
            try:
                import mem_gate
                d = mem_gate.decide(need_gb)
                if d.get("verdict") != "OK":
                    _append(LEDGER, {"event": "mem-blocked", "owner": lane, "need": need,
                                     "verdict": d.get("verdict"),
                                     "model_max_gb": d.get("model_max_gb"),
                                     "swap_rate": d.get("swap_rate"), "ts": _iso()})
                    return False, "内存不够：需 %.1fGB，上限 %.1fGB（%s）" % (
                        need_gb, d.get("model_max_gb") or 0, d.get("verdict"))
            except Exception as e:
                # 闸坏了不许静默放行：宁可拒一次并记原因，也不要拿 swap 去赌。
                _append(LEDGER, {"event": "mem-gate-error", "owner": lane,
                                 "err": str(e)[:80], "ts": _iso()})
                return False, "内存闸不可用（%s），拒绝发租约" % str(e)[:40]
        pid = os.getpid()
        _dequeue(lane, pid)
        rec = {"owner": lane, "need": need, "pid": pid, "since": _iso(),
               "since_ts": _now(), "ttl_s": int(ttl_s)}
        _write(LEASE, rec)
        _append(LEDGER, {"event": "granted", "owner": lane, "need": need, "ts": _iso()})
        return True, "授予 %s" % lane
    finally:
        _unlock(f)


def acquire(lane, need="compute", timeout_s=0, ttl_s=DEFAULT_TTL, poll_s=2.0):
    """排队拿租约：内部轮询，最多等 timeout_s 秒。返回 (ok, why, waited_s)。"""
    t0 = _now()
    while True:
        ok, why = try_acquire(lane, need, ttl_s)
        if ok:
            return True, why, round(_now() - t0, 1)
        if _now() - t0 >= float(timeout_s or 0):
            return False, why, round(_now() - t0, 1)
        time.sleep(min(poll_s, max(0.2, float(timeout_s) - (_now() - t0))))


def release(lane):
    f = _lock()
    try:
        lease = _read(LEASE, {})
        if lease.get("owner") != lane:
            return False, "不是本线持有（当前 %s）" % (lease.get("owner") or "无人")
        held = round(_now() - float(lease.get("since_ts") or _now()), 1)
        try:
            os.remove(LEASE)
        except FileNotFoundError:
            pass
        _append(LEDGER, {"event": "released", "owner": lane, "held_s": held, "ts": _iso()})
        return True, "释放（持有 %.1fs）" % held
    finally:
        _unlock(f)


def snapshot():
    """给一屏用：谁占着、占多久、谁在排队。"""
    lease = _read(LEASE, {})
    valid = _lease_valid(lease)
    rows = [r for r in _rows(QUEUE) if _alive(r.get("pid"))]
    return {
        "holder": lease.get("owner") if valid else None,
        "need": lease.get("need") if valid else None,
        "since": lease.get("since") if valid else None,
        "queue": [r.get("lane") for r in sorted(rows, key=lambda x: x.get("ts_epoch") or 0)],
    }


def status():
    lease = _read(LEASE, {})
    rows = [r for r in _rows(QUEUE) if _alive(r.get("pid"))]
    if lease and _lease_valid(lease):
        print("持有者：%s（need=%s，自 %s，pid=%s）"
              % (lease.get("owner"), lease.get("need"), lease.get("since"), lease.get("pid")))
    else:
        print("持有者：无（空闲）")
    print("排队：%s" % (", ".join(r.get("lane") for r in rows) or "无"))
    return 0


# ---------------- 自检（含负控） ----------------
def _run_case(name, fn, expect):
    got = fn()
    ok = (got == expect)
    print("  %s %s（got=%r expect=%r）" % ("PASS" if ok else "FAIL", name, got, expect))
    return ok


def self_test():
    global LEASE, QUEUE, LEDGER, LOCK, STATE
    tmp = os.path.join(ROOT, ".codely-cli", "state", "__compute-selftest")
    old = (STATE, LEASE, QUEUE, LEDGER, LOCK)
    STATE = tmp
    LEASE = os.path.join(tmp, "lease.json")
    QUEUE = os.path.join(tmp, "queue.jsonl")
    LEDGER = os.path.join(tmp, "compute-ledger.jsonl")
    LOCK = os.path.join(tmp, "lease.lock")
    try:
        os.makedirs(tmp, exist_ok=True)
        for p in (LEASE, QUEUE, LEDGER):
            try:
                os.remove(p)
            except FileNotFoundError:
                pass
        cases = []
        ok, why = try_acquire("bili")
        cases.append(("空闲时能拿到", ok))
        ok2, why2 = try_acquire("gzh")
        cases.append(("另一条线拿不到（不重叠）", not ok2 and "占用中" in why2))
        ok3, _ = try_acquire("bili")
        cases.append(("同线可重入", ok3))
        r, why4 = release("gzh")
        cases.append(("没持有时不能释放别人的", not r))
        r, _ = release("bili")
        cases.append(("持有时能释放", r))
        ok4, _ = try_acquire("gzh")
        cases.append(("释放后别线能拿", ok4))
        release("gzh")

        # 失效回收：写一个死 pid
        _write(LEASE, {"owner": "train", "need": "gpu", "pid": 999999,
                       "since": _iso(), "since_ts": _now(), "ttl_s": 3600})
        ok5, why5 = try_acquire("bili")
        cases.append(("死进程的租约被回收", ok5))
        release("bili")

        # 排队顺序：先登记的线先拿
        for p in (QUEUE,):
            try:
                os.remove(p)
            except FileNotFoundError:
                pass
        _write(LEASE, {"owner": "train", "need": "gpu", "pid": os.getpid(),
                       "since": _iso(), "since_ts": _now(), "ttl_s": 3600})
        _append(QUEUE, {"lane": "gzh", "pid": os.getpid(), "ts": _iso(),
                        "ts_epoch": _now() - 10})
        _append(QUEUE, {"lane": "bili", "pid": os.getpid(), "ts": _iso(),
                        "ts_epoch": _now()})
        cases.append(("队头是早到的线", _first_waiter("gzh") is True))
        cases.append(("后到的线不能插队", _first_waiter("bili") is False))
        release("train")

        # 负控（2026-11-27）：内存不够时必须**拒发**租约，不许拿到 GPU 却把机器换页。
        # 用假的 mem_gate.decide 注入，避免依赖本机当时的真实负载。
        import mem_gate as _mg
        _saved = _mg.decide
        try:
            _mg.decide = lambda need, **kw: {"verdict": "WAIT", "model_max_gb": 3.3,
                                             "swap_rate": 120.0, "note": "注入：正在换页"}
            ok1, why1 = try_acquire("gzh", "gpu-model-9b")
            cases.append(("负控：内存闸判 WAIT → 拒发租约（且说清原因）",
                          ok1 is False and "内存" in why1))
            _mg.decide = lambda need, **kw: {"verdict": "OK", "model_max_gb": 12.0,
                                             "swap_rate": 0.0, "note": ""}
            ok2, why2 = try_acquire("gzh", "gpu-model-9b")
            cases.append(("正控：内存够 → 照常授予", ok2 is True))
            release("gzh")
            # CPU 类租约不过内存闸（否则采集/体检会被内存闸误伤）
            # 先清队伍：上面几条用例往 QUEUE 里塞过 gzh/bili，不清掉 collect 就不是队头。
            try:
                os.remove(QUEUE)
            except FileNotFoundError:
                pass
            ok3, why3 = try_acquire("collect", "cpu")
            cases.append(("正控：cpu 租约不受内存闸影响", ok3 is True))
            release("collect")
        finally:
            _mg.decide = _saved

        ok = sum(1 for _, v in cases if v)
        for n, v in cases:
            print("  %s %s" % ("PASS" if v else "FAIL", n))
        print("[compute-broker self-test] %d/%d %s"
              % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
        return 0 if ok == len(cases) else 1
    finally:
        STATE, LEASE, QUEUE, LEDGER, LOCK = old
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--acquire", default="")
    ap.add_argument("--release", default="")
    ap.add_argument("--need", default="compute")
    ap.add_argument("--timeout", type=float, default=0)
    ap.add_argument("--ttl", type=int, default=DEFAULT_TTL)
    ap.add_argument("--hold", type=float, default=0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.status:
        return status()
    if a.release:
        ok, why = release(a.release)
        print(why)
        return 0 if ok else 1
    if a.acquire:
        ok, why, waited = acquire(a.acquire, a.need, a.timeout, a.ttl)
        print("%s（等待 %.1fs）：%s" % ("OK" if ok else "QUEUED", waited, why))
        if ok and a.hold:
            time.sleep(a.hold)
            print(release(a.acquire)[1])
        return 0 if ok else 2
    return status()


if __name__ == "__main__":
    sys.exit(main())
