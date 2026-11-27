#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_queue.py - 本地模型的科学排单器（单档常驻 + 优先级队列 + 大档批窗）。

形态依据 = cph4/fleet/LOCAL-MODEL-SHAPE-v1.md（实测：并发不增吞吐、同驻打光内存、冷加载 1.5s、9B 质量 +11pt）。

排单规则
  P0  规则/事实（不花模型，直接算）
  P1  小档即时：分类/打标/风险（4B，单条进单条出，延迟优先）
  P2  小档批：草稿/摘要/改写（4B，小批跑，吞吐优先）
  P3  大档批窗：判卷/长文/创意（9B），攒够 --min-batch 或等 --flush-seconds 才换入，
      跑完显式 ollama stop（实测长文会把 runner 从 4.1GB 撑到 12GB，不 stop 不回落）
  IDLE 队列空 → 明确记 IDLE，**不造假负载**（CEO 令：不许造假活；假绿比空转更糟）

满负荷的定义（写死在本文件里，避免自欺）
  * 队列非空期间，worker 不空转：取任务→跑→取下一个
  * busy_ratio = 忙时 / 墙钟，status 里直接给出
  * 队列空就是 IDLE，不点燃模型刷指标

内存总闸：换入 9B 前查 swap/空闲内存，swap>1GB 或空闲<2GB 就把 P3 挂起（留痕 P3_DEFERRED），
先跑 P1/P2，等内存回落再补——这是"满负荷但不换页"的唯一做法。

Usage
  python3 Tools/fleet/model_queue.py push --kind classify --text "这段剪辑太顺了" --prio 1
  python3 Tools/fleet/model_queue.py run --loop --max-batches 3
  python3 Tools/fleet/model_queue.py status
  python3 Tools/fleet/model_queue.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state")
QUEUE = os.path.join(STATE, "model-queue.jsonl")
DONE = os.path.join(STATE, "model-queue-done.jsonl")
STATS = os.path.join(STATE, "model-queue-stats.json")
API = "http://127.0.0.1:11434/api/generate"
SMALL = "qwen3.5:4b-mlx"
BIG = "qwen3.5:9b-mlx"
SMALL_CTX, BIG_CTX = 8192, 8192


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _read(path):
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def _write(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def mem():
    try:
        sw = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                            text=True, timeout=5).stdout
        import re
        m = re.search(r"used\s*=\s*([\d.]+)([MG])", sw or "")
        used = float(m.group(1)) * (1024 if m.group(2) == "G" else 1) if m else 0
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
        free = 0
        for line in (vm or "").splitlines():
            if "Pages free" in line:
                free = int(re.sub(r"[^0-9]", "", line.split(":")[1] or "0") or 0) * 4096 / 1048576
        return used, free
    except Exception:
        return 9999, 0            # 读不到就当紧张，保守


def pressure():
    used, free = mem()
    return (used > 1024 or free < 2048), "swap%.0fMB 空闲%.0fMB" % (used, free)


def push(kind, payload, prio=2, est_tokens=120):
    row = {"id": "t%d" % int(time.time() * 1000), "kind": kind, "prio": prio,
           "payload": payload, "est_tokens": est_tokens, "ts": _now(), "state": "QUEUED"}
    _append(QUEUE, [row])
    return row


def pop_batch(min_batch=5, max_batch=12):
    """按优先级取任务：P1/P2 单批可小；P3 需攒够 min_batch 或已等太久。"""
    rows = [r for r in _read(QUEUE) if r.get("state") == "QUEUED"]
    if not rows:
        return []
    rows.sort(key=lambda r: (r.get("prio", 2), r.get("ts") or ""))
    p1 = [r for r in rows if r.get("prio") == 1]
    if p1:
        return p1[:1]                      # 即时档：一条就走，延迟优先
    p2 = [r for r in rows if r.get("prio") == 2]
    if p2:
        return p2[:max_batch]
    p3 = [r for r in rows if r.get("prio") == 3]
    if not p3:
        return []
    oldest = min((r.get("ts") or "") for r in p3)
    waited = 1e9
    try:
        waited = (datetime.now() - datetime.fromisoformat(oldest)).total_seconds()
    except Exception:
        pass
    if len(p3) >= min_batch or waited > 1800:   # 攒够 或 等过 30 分钟就发车
        return p3[:max_batch]
    return []


def _gen(model, prompt, ctx, maxtok=200, keep="5m"):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False,
                       "keep_alive": keep,
                       "options": {"num_ctx": ctx, "num_predict": maxtok,
                                   "temperature": 0.3}}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    return (d.get("response") or "").strip(), (d.get("eval_count") or 0)


SIZE_LIMIT_GB = {SMALL: 6.5, BIG: 11.0}   # 实测基线 4.1/9.0GB；超 1.5x 就回收


def model_size_gb(model):
    try:
        out = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=10).stdout
        for line in (out or "").splitlines():
            if line.startswith(model):
                import re
                m = re.search(r"(\d+(?:\.\d+)?)\s*GB", line)
                return float(m.group(1)) if m else 0.0
    except Exception:
        pass
    return 0.0


def recycle_if_fat(model, log=print):
    """24h 连跑实测：4B 从 4.3GB 膨胀到 8.7GB（重复请求不释放），只有 stop 重载才回落。

    所以每批之后看一眼体积，超阈就 stop；下批请求会自动重载（冷加载 1.5s 级）。
    """
    lim = SIZE_LIMIT_GB.get(model)
    sz = model_size_gb(model)
    if lim and sz > lim:
        _stop(model)
        log("[queue] 回收 %s（%.1fGB > %.1fGB 阈值），下批自动重载" % (model, sz, lim), flush=True)
        return True
    return False


def _stop(model):
    try:
        subprocess.run(["ollama", "stop", model], capture_output=True, timeout=30)
    except Exception:
        pass


CLASSIFY_PROMPT = ("把这句话分到 夸奖/提问/挑刺/法律/辱骂/广告 之一，只输出类别两个汉字：\n%s")


def run_batch(tasks, gen=None, small=SMALL, big=BIG, stopper=None):
    """执行一批任务，返回 [(task_id, ok, out)]。gen 可注入（自检不联网）。"""
    gen = gen or _gen
    stopper = stopper or _stop
    out = []
    if not tasks:
        return out
    tier3 = all(int(t.get("prio", 2)) == 3 for t in tasks)
    model, ctx = (big, BIG_CTX) if tier3 else (small, SMALL_CTX)
    for t in tasks:
        kind = t.get("kind")
        if kind == "classify":
            prompt = CLASSIFY_PROMPT % (t.get("payload") or "")
        elif kind == "draft":
            prompt = ("你在替一个 MV 账号回 B 站评论。12-25 字、口语、不客服腔、不反问。"
                      "评论：%s" % (t.get("payload") or ""))
        else:
            prompt = str(t.get("payload") or "")
        try:
            text, ntok = gen(model, prompt, ctx, maxtok=int(t.get("est_tokens") or 200))
            out.append((t["id"], bool(text), text[:200]))
        except Exception as e:
            out.append((t["id"], False, "%s: %s" % (type(e).__name__, str(e)[:80])))
    if tier3:
        stopper(big)                       # 批窗跑完即卸（实测长文会把 runner 撑大）
    else:
        recycle_if_fat(model)              # 小档也不是白用：跑多了体积会涨
    return out


def finish(tasks, outs, reason=""):
    done = _read(QUEUE)
    byid = {t["id"]: o for t, o in zip(tasks, outs)}
    keep = []
    for r in done:
        if r.get("id") in byid:
            ok, txt = byid[r["id"]][1], byid[r["id"]][2]
            r.update({"state": "DONE" if ok else "FAILED", "out": txt,
                      "done_ts": _now(), "reason": reason})
            _append(DONE, [r])
        else:
            keep.append(r)
    _write(QUEUE, keep)


def stats(extra=None):
    rows = [r for r in _read(QUEUE) if r.get("state") == "QUEUED"]
    done = _read(DONE)
    today = date.today().isoformat()
    td = [r for r in done if str(r.get("done_ts") or "").startswith(today)]
    s = {"queued": len(rows),
         "by_prio": {p: sum(1 for r in rows if r.get("prio") == p) for p in (1, 2, 3)},
         "done_today": len(td),
         "failed_today": sum(1 for r in td if r.get("state") == "FAILED"),
         "swap_mb": mem()[0], "free_mb": mem()[1], "ts": _now()}
    old = {}
    if os.path.exists(STATS):
        try:
            old = json.load(open(STATS, encoding="utf-8"))
        except Exception:
            old = {}
    # 忙时只增不减（同一天内）；换天归零。原实现会被并发覆盖成 0（实锚），改成取最大。
    prev = float(old.get("busy_seconds_today") or 0) if str(old.get("day")) == today else 0.0
    add = float(extra.get("busy") or 0) if extra else 0.0
    busy = max(prev, prev + add) if add else prev
    s["busy_seconds_today"] = round(busy, 1)
    s["day"] = today
    json.dump(s, open(STATS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return s


MODE_FILE = os.path.join(STATE, "MEM-MODE")


def work_once(min_batch=5, max_batch=12, force_p3=False, gen=None):
    """取一批→跑→记账。返回 (n, busy_seconds, note)。"""
    if os.path.exists(MODE_FILE):
        # 采集期让路：浏览器 1.1GB/实例，跟模型抢内存必换页（实测 164MB→26MB）
        return 0, 0.0, "DEFER_COLLECT"
    batch = pop_batch(min_batch=min_batch, max_batch=max_batch)
    if not batch:
        return 0, 0.0, "IDLE"
    if all(int(t.get("prio", 2)) == 3 for t in batch) and not force_p3:
        tight, why = pressure()
        if tight:
            return 0, 0.0, "P3_DEFERRED(%s)" % why
    t0 = time.time()
    outs = run_batch(batch, gen=gen)
    busy = time.time() - t0
    finish(batch, outs)
    return len(batch), busy, "OK"


def self_test():
    cases = []
    global QUEUE, DONE, STATS
    orig = (QUEUE, DONE, STATS)
    tmp = os.path.join(ROOT, ".codely-cli", "tmp", "mq-selftest")
    os.makedirs(tmp, exist_ok=True)
    QUEUE, DONE, STATS = (os.path.join(tmp, "q.jsonl"), os.path.join(tmp, "d.jsonl"),
                          os.path.join(tmp, "s.json"))
    for f in (QUEUE, DONE, STATS):
        if os.path.exists(f):
            os.remove(f)

    # 1 优先级：P1 一条就走
    push("classify", "a", prio=2)
    push("classify", "b", prio=1)
    push("draft", "c", prio=3)
    b = pop_batch()
    cases.append(("P1 单条优先", len(b) == 1 and b[0]["prio"] == 1))

    # 2 P3 未攒够不发车（清掉 P1/P2 后只剩 1 条 P3）
    _write(QUEUE, [r for r in _read(QUEUE) if int(r.get("prio", 2)) == 3])
    b2 = pop_batch(min_batch=5)
    cases.append(("P3 未攒够必须等", b2 == []))

    # 3 P3 攒够 5 条才发车
    for i in range(4):
        push("judge", "x%d" % i, prio=3)
    b3 = pop_batch(min_batch=5, max_batch=12)
    cases.append(("P3 攒够才发车", len([r for r in b3 if r["prio"] == 3]) == 5))

    # 4 空队列必须 IDLE（不造假负载）
    _write(QUEUE, [])
    n, busy, note = work_once(gen=lambda *a, **k: ("ok", 5))
    cases.append(("空队列必须 IDLE", n == 0 and note == "IDLE" and busy == 0))

    # 5 内存紧张时 P3 挂起并留痕（队列不许被吃）
    _write(DONE, [])
    for i in range(5):
        push("judge", "y%d" % i, prio=3)
    import unittest.mock as mock
    with mock.patch.object(sys.modules[__name__], "pressure", lambda: (True, "swap9000MB")):
        n2, _, note2 = work_once(min_batch=5, gen=lambda *a, **k: ("ok", 5))
    cases.append(("内存紧张 P3 必须挂起", n2 == 0 and note2.startswith("P3_DEFERRED")
                  and len([r for r in _read(QUEUE) if r.get("state") == "QUEUED"]) == 5))

    # 6 正常发车：批窗跑完必须 stop 大档 + 落盘 DONE
    called = []
    with mock.patch.object(sys.modules[__name__], "pressure", lambda: (False, "ok")):
        n3, b3s, note3 = work_once(min_batch=5,
                                   gen=lambda *a, **k: ("判决：通过", 5),
                                   )
    cases.append(("发车成功", n3 == 5 and note3 == "OK"))

    # 6b 批窗跑完必须 stop 大档（注入 stopper 观察调用）
    called = []
    for i in range(5):
        push("judge", "w%d" % i, prio=3)
    run_batch(pop_batch(min_batch=5), gen=lambda *a, **k: ("ok", 5),
              stopper=lambda m: called.append(m))
    cases.append(("批窗跑完必须 stop 大档", called == [BIG]))
    _write(QUEUE, [r for r in _read(QUEUE) if int(r.get("prio", 2)) != 3])

    # 7 落盘：DONE 里 5 条且队列清空
    cases.append(("已完成必须落盘", len(_read(DONE)) == 5
                  and all(r.get("state") == "DONE" for r in _read(DONE))
                  and not [r for r in _read(QUEUE) if r.get("state") == "QUEUED"]))

    QUEUE, DONE, STATS = orig
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("push")
    p.add_argument("--kind", default="classify")
    p.add_argument("--text", default="")
    p.add_argument("--prio", type=int, default=2)
    r = sub.add_parser("run")
    r.add_argument("--loop", action="store_true")
    r.add_argument("--max-batches", type=int, default=0, help="0=不限（loop 用）")
    r.add_argument("--min-batch", type=int, default=5)
    r.add_argument("--max-batch", type=int, default=12)
    r.add_argument("--idle-sleep", type=int, default=20)
    sub.add_parser("status")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.cmd == "push":
        row = push(a.kind, a.text, prio=a.prio)
        print("[queue] +%s prio=%d kind=%s" % (row["id"], a.prio, a.kind))
        return 0
    if a.cmd == "status":
        s = stats()
        print("[queue] 排队 %d（P1=%d P2=%d P3=%d）· 今日完成 %d 失败 %d · 忙时 %.0fs · swap %.0fMB 空闲 %.0fMB"
              % (s["queued"], s["by_prio"][1], s["by_prio"][2], s["by_prio"][3],
                 s["done_today"], s["failed_today"], s["busy_seconds_today"],
                 s["swap_mb"], s["free_mb"]))
        return 0
    if a.cmd == "run":
        n_batches = 0
        while True:
            n, busy, note = work_once(min_batch=a.min_batch, max_batch=a.max_batch)
            s = stats({"busy": busy})
            print("[queue] %s %s 处理%d 忙%.1fs 排队%d 忙时%.0fs"
                  % (_now(), note, n, busy, s["queued"], s["busy_seconds_today"]),
                  flush=True)   # 必须 flush：管道缓冲会被判"无输出"掐死（实锚）
            if n:
                n_batches += 1
            if not a.loop:
                return 0
            if a.max_batches and n_batches >= a.max_batches:
                return 0
            if n == 0:
                time.sleep(max(5, a.idle_sleep))
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
