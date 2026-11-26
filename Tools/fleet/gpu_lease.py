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
# 环境变量覆盖：自检必须在**同一把锁**上验证父子继承。原来只改父进程的全局变量，
# 子进程仍指向线上真锁，于是"无继承的子进程必被拒"这条永远是假红（2026-11-26 实锚）。
LOCK = os.environ.get("FLUX_GPU_LOCK") or os.path.join(STATE, "gpu.lock")
REC = os.environ.get("FLUX_GPU_REC") or os.path.join(STATE, "gpu-lease.json")

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



REAP_LOG = os.path.join(STATE, "gpu-lease-reap.jsonl")


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def _cpu_idle(pid, samples=2, gap=0.5, thr=2.0):
    """进程活着但不在干活？连续采样 CPU% 都低于阈值才算空闲。

    为什么要判空闲：租约超 TTL 只说明"占久了"，不等于"卡住了"。
    长训练会合法地占用一小时以上，不能一过 TTL 就杀。真正的判据是
    "超时 + 不干活"两条同时成立。
    """
    vals = []
    for _ in range(samples):
        out = subprocess.run(["ps", "-o", "%cpu=", "-p", str(int(pid))],
                             capture_output=True, text=True)
        try:
            vals.append(float((out.stdout or "0").strip() or 0))
        except ValueError:
            return False
        time.sleep(gap)
    return bool(vals) and max(vals) < thr


REAPABLE = ("selfgen", "train", "publish", "practice", "collect", "learn")


def _is_self_or_ancestor(pid, hops=8):
    """pid 是不是自己或自己的祖先。

    为什么必须挡：子进程抢锁时，持有者往往正是**它自己的父进程**（父持租约起子进程干活）。
    那种"父进程 CPU 空闲"完全正常（它在等子进程），一旦按"超时+空闲"回收，
    子进程就会杀掉自己的父进程——自检里这条会立刻红（2026-11-26 实锚）。
    """
    cur = os.getpid()
    pid = int(pid)
    for _ in range(hops):
        if cur == pid:
            return True
        if cur <= 1:
            return False
        out = subprocess.run(["ps", "-o", "ppid=", "-p", str(cur)],
                             capture_output=True, text=True)
        try:
            cur = int((out.stdout or "0").strip() or 0)
        except ValueError:
            return False
    return False


def _reap_stale(cur):
    """超 TTL 且空闲的持有者：回收它，让队列继续。

    2026-11-26 实锚：selfgen 卡在 8788 的连接上两小时不返回（CPU 1.6%、无子进程），
    而训练一直在打「GPU 让路：GPU 被占用：selfgen（已 7078s）」——租约的 TTL 写了
    3600 秒，但 flock 由活着的进程持有，过期标记只用于展示、没人据此回收。
    结果是主链路被一个空转进程挡住两小时，谁也不知道。
    """
    if not cur or not cur.get("stale"):
        return False
    pid = int(cur.get("pid") or 0)
    name = str(cur.get("name") or "")
    if not pid or not name or not any(name.startswith(x) for x in REAPABLE):
        return False
    if _is_self_or_ancestor(pid):
        return False                      # 绝不杀自己或祖先
    if not (_pid_alive(pid) and _cpu_idle(pid)):
        return False
    try:
        os.kill(pid, 15)
        time.sleep(1.2)
        if _pid_alive(pid):
            os.kill(pid, 9)
    except Exception:
        return False
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(REAP_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                "reaped": name, "pid": pid,
                                "age_s": cur.get("age_s")}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    print("[lease] 回收僵尸租约 %s(pid=%s, 已 %ss, CPU 空闲)"
          % (name, pid, cur.get("age_s")), flush=True)
    return True


ARBITER_LOG = os.environ.get("FLUX_GPU_ARBITER") or os.path.join(STATE, "arbiter-gpu.jsonl")


def _arbitrate(want, cur):
    """抢不到锁就记一笔在**仲裁方自己的账**上，不写进任何线的台账。

    为什么单独记账（CEO 2026-11-26「经常更新，但不要互相影响 应该各司其职」）：
    原来"谁让路了"散在各线的日志与训练台账里，想知道"今天 GPU 被谁抢走多少时间"
    得先读三份不同格式的日志。让路是仲裁事件，就该记在仲裁账里；各线的台账只记
    自己真正做过的事。记账失败一律吞掉——旁证不许影响抢锁结果。
    """
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(ARBITER_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "want": want,
                "holder": (cur or {}).get("name"), "holder_pid": (cur or {}).get("pid"),
                "holder_age_s": (cur or {}).get("age_s"),
                "holder_stale": bool((cur or {}).get("stale")),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


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
            # 先看持有者是不是"超时 + 空闲"的僵尸；是就回收，然后重试拿锁
            if _reap_stale(who()):
                continue
            if time.time() >= deadline:
                cur = who()
                fh.close()
                _arbitrate(name, cur)
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


def renew(name, ttl_s=None):
    """续约：只有持有者能续。返回是否续上。

    为什么需要它（2026-11-26 实锚）：selfgen 取租约时写死 ttl_s=3*3600，一次卡顿
    就把 GPU 锁满三小时，`_reap_stale` 只在 stale（超 TTL）后才肯介入——于是回收器
    整段时间没有机会。把 TTL 压到 10 分钟 + 每处理一条续一次，才有"健康长跑照样续、
    卡死十分钟自动可回收"的效果；不动回收器的杀进程判据，长训练不受影响。
    """
    if name not in _handles or DEPTH.get(name, 0) <= 0:
        return False               # 不是本进程持的锁，不许替别人续
    d = _read()
    if d.get("pid") != os.getpid() or d.get("name") != name:
        return False
    now = time.time()
    ttl = float(ttl_s if ttl_s is not None else (float(d.get("expires") or 0) - float(d.get("ts") or now)))
    if ttl <= 0:
        return False
    _write({"name": name, "pid": os.getpid(), "ts": now, "expires": now + ttl})
    return True


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
    global LOCK, REC, ARBITER_LOG
    saved = (LOCK, REC, ARBITER_LOG)
    d = tempfile.mkdtemp(prefix="gl-")
    # 生产仲裁账的真实路径（STATE 不参与切换，这里取到的就是线上那一份）
    _prod_arb = os.path.join(STATE, "arbiter-gpu.jsonl")

    def _prod_size():
        try:
            return os.path.getsize(_prod_arb)
        except Exception:
            return 0
    LOCK, REC = os.path.join(d, "gpu.lock"), os.path.join(d, "lease.json")
    # 自检不许写生产仲裁账：闸的纪律里"测试绝不写生产路径"是硬条，
    # 否则每跑一次自检就给自己造一条假的让路记录。
    ARBITER_LOG = os.path.join(d, "arbiter.jsonl")
    try:
        ok1, _ = acquire("t_main", ttl_s=60)
        ok2, why2 = acquire("t_main", ttl_s=60)          # 重入
        _size0 = _prod_size()
        env0 = {k: v for k, v in os.environ.items() if k != ENV_KEY}
        env0["FLUX_GPU_LOCK"] = LOCK
        env0["FLUX_GPU_REC"] = REC
        # 子进程也必须指向临时仲裁账：它抢不到锁时会 _arbitrate，而 ARBITER_LOG
        # 在 import 时按 STATE 算出来，不传环境变量就会写进生产账（自检污染实锚）。
        env0["FLUX_GPU_ARBITER"] = ARBITER_LOG
        code_no = subprocess.run([sys.executable, os.path.abspath(__file__), "--try", "t_main"],
                                 capture_output=True, text=True, env=env0).returncode
        code_yes = subprocess.run([sys.executable, os.path.abspath(__file__), "--try", "t_main"],
                                  capture_output=True, text=True,
                                  env=dict(env0, **{ENV_KEY: "t_main"})).returncode
        release("t_main")
        release("t_main")
        ok3, _ = acquire("t_main", ttl_s=60)
        ok4 = os.environ.get(ENV_KEY, "").find("t_main") >= 0
        # 续约：持有者能续、过期时间被推后；非持有者续不上（负控）
        before = float((_read() or {}).get("expires") or 0)
        time.sleep(0.05)
        ok5 = renew("t_main", ttl_s=600)
        after = float((_read() or {}).get("expires") or 0)
        ok6 = after > before and after - time.time() > 500
        release("t_main")
        ok7 = not renew("t_main", ttl_s=600)        # 已释放 → 不许续
        # 别的车道名也续不上（不是它的锁）
        acquire("t_main", ttl_s=60)
        ok8 = not renew("t_other", ttl_s=600)
        release("t_main")
    finally:
        _size1 = _prod_size()
        LOCK, REC, ARBITER_LOG = saved
    ok9 = (_size1 == _size0)
    ok = (ok1 and ok2 and code_no == 3 and code_yes == 0 and ok3 and ok4
          and ok5 and ok6 and ok7 and ok8 and ok9)
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "首拿": ok1, "重入": ok2,
                      "子进程无继承被拒(rc=3)": code_no == 3,
                      "子进程有继承放行(rc=0)": code_yes == 0,
                      "释放后可再拿": ok3, "环境已标记继承": ok4,
                      "持有者可续约": ok5, "续约推后过期": ok6,
                      "释放后不许续": ok7, "非持有者不许续": ok8,
                      "自检不写生产仲裁账": ok9,
                      "重入说明": why2}, ensure_ascii=False))
    return 0 if ok else 1


def arbiter_report(limit=20):
    """仲裁账摘要：谁抢走了多少时间、被谁挡。只读本模块自己的账。"""
    rows = []
    try:
        for ln in open(ARBITER_LOG, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    continue
    except Exception:
        return {"n": 0, "by_holder": {}, "by_want": {}, "last": []}
    by_h, by_w = {}, {}
    for r in rows:
        by_h[(r.get("holder") or "?")] = by_h.get((r.get("holder") or "?"), 0) + 1
        by_w[(r.get("want") or "?")] = by_w.get((r.get("want") or "?"), 0) + 1
    return {"n": len(rows), "by_holder": dict(sorted(by_h.items(), key=lambda kv: -kv[1])),
            "by_want": dict(sorted(by_w.items(), key=lambda kv: -kv[1])),
            "last": rows[-limit:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--arbiter", action="store_true", help="让路仲裁账摘要")
    ap.add_argument("--try-acquire", dest="try_name", default="",
                    help="试拿一次（拿不到 rc=3）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.arbiter:
        print(json.dumps(arbiter_report(), ensure_ascii=False, indent=1))
        return 0
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
