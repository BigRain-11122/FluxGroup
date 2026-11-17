#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_agent_day.py — 养号线的单一执行体：按矩阵时间表串行跑循环任务。

为什么不给每个任务加一个 launchd：launchd 一多，"谁在跑、跑到哪、谁跟谁抢内存"就没人
说得清；本仓既有做法是一个身体承载全部阶段（主控脉就是这么干的）。所以这里只有一条
plist，按 SOCIAL-AUTOMATION-MATRIX-v1.json 的 every_s 判"这轮该谁跑"，串行执行。

三条硬约束：
  1 串行 + 内存互斥：同一时刻只跑一个任务；mem=collect / mem=train 相邻必等（32GB 会换页）。
  2 判据认产出：每个任务跑完只记 rc + 产出文件的行数/mtime，不记"进程活着"。
  3 静默 + 让路：哨兵 SOCIAL-AGENT-PAUSED 存在即整轮跳过，不弹窗不发声。

用法：
  python3 Tools/fleet/social_agent_day.py --once        # 跑一轮（到点才跑）
  python3 Tools/fleet/social_agent_day.py --loop        # 常驻（plist 用它）
  python3 Tools/fleet/social_agent_day.py --force <id>  # 强制跑某任务
  python3 Tools/fleet/social_agent_day.py --due         # 只列这轮该跑什么
  python3 Tools/fleet/social_agent_day.py --self-test
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
MATRIX = os.path.join(SOCIAL, "SOCIAL-AUTOMATION-MATRIX-v1.json")
STATE = os.path.join(ROOT, ".codely-cli", "state")
DAYSTATE = os.path.join(STATE, "social-agent-day.json")
PAUSE = os.path.join(STATE, "SOCIAL-AGENT-PAUSED")
LEDGER = os.path.join(SOCIAL, "AGENT-DAY-LEDGER.jsonl")
MEM_MODE = os.path.join(STATE, "MEM-MODE")
BUDGET_S = 1800          # 单任务硬超时：训练会很久，靠 train_pipe 自己的门兜，这里只防挂死


def load_matrix(path=MATRIX):
    return json.load(open(path, encoding="utf-8"))


def _load_state():
    if os.path.exists(DAYSTATE):
        try:
            return json.load(open(DAYSTATE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(d):
    os.makedirs(STATE, exist_ok=True)
    tmp = DAYSTATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, DAYSTATE)


def _log(row):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def due_tasks(matrix, state, now=None, force=None):
    """按 every_s 判到期；force 指定则只返回它。返回按 priority 升序（0 最先）。"""
    now = now or time.time()
    out = []
    for t in matrix["tasks"]:
        if force and t["id"] != force:
            continue
        last = (state.get(t["id"]) or {}).get("ts") or 0
        if not (force or in_window(t, now)):
            continue
        if force or now - last >= t.get("every_s", 3600):
            out.append(t)
    out.sort(key=lambda t: t.get("priority", 99))
    return out


def in_window(task, now=None):
    """窗口判定（本地时间 HH:MM，支持跨零点）。没声明就是全天可跑。"""
    w = task.get("window")
    if not w:
        return True
    lt = time.localtime(now or time.time())
    cur = lt.tm_hour * 60 + lt.tm_min

    def mins(x):
        h, m = x.split(":")
        return int(h) * 60 + int(m)

    a, b = mins(w["from"]), mins(w["to"])
    return (a <= cur < b) if a <= b else (cur >= a or cur < b)


def mem_conflict(task, running_mem=None):
    """collect 与 train 不许相邻：两者吃同一池内存（实测换页）。"""
    m = task.get("mem", "none")
    if m == "none" or running_mem in (None, "none"):
        return False
    return m != running_mem


def run_task(task, timeout=BUDGET_S):
    t0 = time.time()
    argv = list(task["cmd"])
    if argv and argv[0] == "python3":
        argv[0] = sys.executable
    try:
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        rc, tail = r.returncode, ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        note = tail[-1][:180] if tail else ""
    except subprocess.TimeoutExpired:
        rc, note = 124, "TIMEOUT %ds" % timeout
    except Exception as e:
        rc, note = 1, "ERR %s" % str(e)[:120]
    return {"rc": rc, "note": note, "secs": round(time.time() - t0, 1)}


def evidence_facts(task):
    """只取产出面的小事实（行数/mtime）。优先用机读的 evidence_paths；
    没写就退回从描述里猜——但描述文字猜不出来，所以矩阵里必须写路径。"""
    out = {}
    for rel in (task.get("evidence_paths") or []):
        fp = os.path.join(ROOT, rel)
        if not os.path.isfile(fp):
            continue
        try:
            n = sum(1 for _ in open(fp, encoding="utf-8", errors="replace")) \
                if fp.endswith((".jsonl", ".md", ".txt")) else None
        except Exception:
            n = None
        out[rel] = {"mtime": int(os.path.getmtime(fp)), "lines": n}
    if out:
        return out
    p = task.get("evidence") or ""
    for token in p.replace(",", " ").split():
        for cand in (token, token.lstrip("+")):
            fp = os.path.join(ROOT, cand)
            if os.path.isfile(fp):
                try:
                    n = sum(1 for _ in open(fp, encoding="utf-8", errors="replace")) \
                        if fp.endswith((".jsonl", ".md", ".txt")) else None
                except Exception:
                    n = None
                out[cand] = {"mtime": int(os.path.getmtime(fp)), "lines": n}
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--force", default=None)
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    matrix = load_matrix()
    if a.due:
        st = _load_state()
        for t in due_tasks(matrix, st, force=a.force):
            print("  %-16s %s" % (t["id"], t.get("what", "")[:40]))
        return 0

    while True:
        run_once(matrix, force=a.force)
        if not a.loop:
            return 0
        time.sleep(max(20, a.interval))


def run_once(matrix, force=None):
    if os.path.exists(PAUSE):
        print("[day] 哨兵存在（CEO 让路令），整轮跳过")
        return 0
    st = _load_state()
    tasks = due_tasks(matrix, st, force=force)
    if not tasks:
        print("[day] 无到期任务")
        return 0
    ran_mem = "none"
    for t in tasks:
        if mem_conflict(t, ran_mem):
            print("[day] %s 与上一个任务内存冲突（%s vs %s），本轮跳过"
                  % (t["id"], t.get("mem"), ran_mem))
            continue
        print("[day] 跑 %-16s %s" % (t["id"], t.get("what", "")[:40]), flush=True)
        res = run_task(t, timeout=t.get("timeout_s", BUDGET_S))
        ev = evidence_facts(t)
        st[t["id"]] = dict(res, ts=time.time(), mem=t.get("mem", "none"), evidence=ev)
        _save_state(st)
        _log(dict(res, ts=time.strftime("%Y-%m-%dT%H:%M:%S"), id=t["id"],
                  mem=t.get("mem", "none"), evidence=ev))
        print("[day] %-16s rc=%s %.0fs %s" % (t["id"], res["rc"], res["secs"], res["note"][:80]),
              flush=True)
        ran_mem = t.get("mem", "none")
    return 0


def self_test():
    m = {"tasks": [
        {"id": "a", "cmd": ["true"], "every_s": 60, "priority": 2, "mem": "none"},
        {"id": "b", "cmd": ["true"], "every_s": 60, "priority": 1, "mem": "collect"},
        {"id": "c", "cmd": ["true"], "every_s": 3600, "priority": 3, "mem": "train"},
    ]}
    cases = []
    # 期望值手算一遍再写：last 缺省=0，now=5000 时 a/b(60s) 与 c(3600s) 都到期
    d = due_tasks(m, {}, now=5000)
    cases.append(("全到期按 priority 排序", [t["id"] for t in d] == ["b", "a", "c"]))
    # now=5000: a 才过 20s（未到 60）→ 不算；b 过 100s → 算；c 过 1000s（未到 3600）→ 不算
    d2 = due_tasks(m, {"a": {"ts": 4980}, "b": {"ts": 4900}, "c": {"ts": 4000}}, now=5000)
    cases.append(("只返回到期项", [t["id"] for t in d2] == ["b"]))
    cases.append(("c 未到期（3600）", "c" not in [t["id"] for t in due_tasks(
        m, {"c": {"ts": 4000}}, now=5000)]))
    cases.append(("c 到期（3700s 前跑过）", "c" in [t["id"] for t in due_tasks(
        m, {"c": {"ts": 1300}}, now=5000)]))
    cases.append(("force 只跑指定", [t["id"] for t in due_tasks(m, {}, now=0, force="c")] == ["c"]))
    cases.append(("collect 与 train 互斥", mem_conflict({"mem": "train"}, "collect")))
    cases.append(("collect 与 none 不冲突", not mem_conflict({"mem": "collect"}, "none")))
    cases.append(("同类型连续不冲突", not mem_conflict({"mem": "collect"}, "collect")))
    # 窗口：白天不许跑重活，凌晨可以
    w = {"id": "night", "cmd": ["true"], "every_s": 60, "priority": 1,
         "window": {"from": "01:00", "to": "08:00"}}
    import time as _t
    def _mk(h, m):
        lt = _t.localtime()
        return _t.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, h, m, 0, 0, 0, -1))
    cases.append(("窗口内可跑", in_window(w, _mk(3, 0))))
    cases.append(("窗口外不跑", not in_window(w, _mk(14, 0))))
    cases.append(("无窗口=全天", in_window({"id": "x"}, _mk(14, 0))))
    w2 = {"id": "wrap", "window": {"from": "22:00", "to": "02:00"}}
    cases.append(("跨零点窗口 23 点可跑", in_window(w2, _mk(23, 0))))
    cases.append(("跨零点窗口 12 点不跑", not in_window(w2, _mk(12, 0))))

    # 交付真跑的 rc 判定
    r = run_task({"cmd": ["python3", "-c", "print('ok')"], "evidence": ""}, timeout=30)
    cases.append(("真命令 rc=0", r["rc"] == 0))
    r2 = run_task({"cmd": ["python3", "-c", "import sys;sys.exit(3)"], "evidence": ""}, timeout=30)
    cases.append(("失败命令 rc 透出", r2["rc"] == 3))
    r3 = run_task({"cmd": ["python3", "-c", "import time;time.sleep(5)"], "evidence": ""},
                  timeout=1)
    cases.append(("超时判 124", r3["rc"] == 124))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
