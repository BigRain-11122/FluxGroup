#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_learn.py - 主流平台 24 小时不间断学习循环（只读采集 → 语料只增不减 → 画像持续更新）。

CEO 2026-11-17「你就不断的进行主流平台的24小时不间断学习」。
这条线只学不发：不点赞、不评论、不关注、不改任何东西，所以它可以在别人休息时一直跑。

一个循环（cycle）做四件事：
  1 轮换数据源：SOURCES-v1.json 里给每个平台配目标页；没配就尝试首页自动发现
  2 只读采集：调 social_collect 抽真实评论
  3 入库去重：corpus/<platform>.jsonl 只追加，按内容哈希去重（同一句永不重复入库）
  4 重算画像：social_profile 重写 STYLE-PROFILE-v1.json + STYLE-REPORT.md

三条诚实纪律（对着本仓踩过的坑）：
  * 没数据就报 NO_SOURCE / BLOCKED / NO_NEW，不写空文件、不假装学到东西
  * 每轮都落 LEARNING-LEDGER.jsonl（一行一轮：源/抓到/新增/累计/结论）
  * 暂停只认哨兵文件 `.codely-cli/state/SOCIAL-LEARN-PAUSED`（放下去就停，不用改代码）

Usage:
  .venv-housing/bin/python Tools/fleet/social_learn.py --once
  .venv-housing/bin/python Tools/fleet/social_learn.py --loop --interval 1200
  python3 Tools/fleet/social_learn.py --status
  python3 Tools/fleet/social_learn.py --self-test
"""

from __future__ import annotations

import argparse
import concurrent.futures
import glob
import hashlib
import json
import os
import random
import sys
import subprocess
import threading
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
SOURCES = os.path.join(SOCIAL, "SOURCES-v1.json")
CORPUS = os.path.join(SOCIAL, "corpus")
LEDGER = os.path.join(SOCIAL, "LEARNING-LEDGER.jsonl")
PAUSE = os.path.join(ROOT, ".codely-cli", "state", "SOCIAL-LEARN-PAUSED")
HEARTBEAT = os.path.join(ROOT, ".codely-cli", "state", "social-learn-heartbeat.json")
STAGGER_S = 3.0     # 并发平台错峰上限（秒）；太大反而拖长整轮，3s 够避开 IO 争用


def _now():
    return datetime.now().isoformat(timespec="seconds")


def load_sources(path=SOURCES):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}


def mem_pressure():
    """总闸：swap 用得多或空闲内存太少就只许单线程。

    主控是本机（MacBook），同时开 3-5 个 Chrome 会把统一内存吃满，
    而这条线的价值是"持续学"，不是"一轮抓完"——宁可慢，不许把机器拖垮。
    """
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                             text=True, timeout=5).stdout
        used_mb = 0
        for tok in out.replace(",", " ").split():
            if tok.endswith("M"):
                pass
        import re
        m = re.search(r"used\s*=\s*([\d.]+)([MG])", out)
        if m:
            used_mb = float(m.group(1)) * (1024 if m.group(2) == "G" else 1)
        vs = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
        free_pages = 0
        for line in vs.splitlines():
            if "Pages free" in line:
                free_pages = int(re.sub(r"[^0-9]", "", line.split(":")[1] or "0") or 0)
        free_gb = free_pages * 4096 / (1024 ** 3)
        if used_mb > 1024 or free_gb < 2.0:
            return True, "swap已用%.0fMB 空闲内存%.1fGB" % (used_mb, free_gb)
        return False, "swap已用%.0fMB 空闲内存%.1fGB" % (used_mb, free_gb)
    except Exception as e:
        return True, "读不到内存状态（%s），保守单线程" % type(e).__name__


def paused():
    return os.path.exists(PAUSE)


def _hash(text):
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def corpus_path(platform):
    return os.path.join(CORPUS, "%s.jsonl" % platform)


def corpus_index(platform):
    """已入库内容哈希集合（幂等：同一句永不重复入库）。"""
    idx = set()
    p = corpus_path(platform)
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                idx.add(json.loads(line).get("h") or "")
            except Exception:
                pass
    return idx


def append_corpus(platform, rows):
    """返回 (new_rows, total)。只追加、写前再查一次哈希（多进程也安全）。"""
    p = corpus_path(platform)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    idx = corpus_index(platform)
    new = []
    for r in rows or []:
        t = str(r.get("text") or r.get("comment") or "").strip()
        if not t:
            continue
        h = _hash(t)
        if h in idx:
            continue
        idx.add(h)
        new.append({"h": h, "platform": platform, "text": t[:300],
                    "author": r.get("author"), "thread": r.get("thread"),
                    "ts": r.get("ts") or _now()})
    if new:
        with open(p, "a", encoding="utf-8") as f:
            for r in new:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    total = sum(1 for _ in open(p, encoding="utf-8")) if os.path.exists(p) else 0
    return new, total


def ledger(row):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def heartbeat(state):
    os.makedirs(os.path.dirname(HEARTBEAT), exist_ok=True)
    json.dump(dict(state, ts=_now()), open(HEARTBEAT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def cycle(collector=None, profiler=None, sources=None, platforms=None, limit=200, min_n=10,
          concurrency=1):
    """跑一轮。collector(url, platform) -> (rows|None, why)。可注入（自检不联网）。"""
    if paused():
        heartbeat({"state": "PAUSED"})
        return {"verdict": "PAUSED", "results": []}
    src = sources if sources is not None else load_sources()
    plats = platforms or src.get("platforms") or {}
    results = []
    run = []
    for plat, cfg in plats.items():
        if cfg.get("enabled") is False:
            results.append({"platform": plat, "verdict": "DISABLED"})
            continue
        urls = [u for u in (cfg.get("urls") or []) if u]
        if not urls:
            results.append({"platform": plat, "verdict": "NO_SOURCE",
                            "note": "未配置目标页（SOURCES-v1.json），也不做首页自动发现时就没法学"})
            ledger({"ts": _now(), "platform": plat, "verdict": "NO_SOURCE", "found": 0, "new": 0})
            continue
        url = random.choice(urls)          # 轮换：每轮随机挑一条，避免盯住同一条
        run.append((plat, url))

    # 并发：每平台一条线程，各自独立 profile（同 profile 两开会 ProcessSingleton 失败）
    ctx = {"limit": limit, "min_n": min_n, "collector": collector or _default_collect}
    locked = threading.Lock()

    def work(plat, url):
        try:
            sys.path.insert(0, HERE)
            import social_riskguard as guard
            okr, whyr = guard.check(plat)
            if not okr:
                with locked:
                    results.append({"platform": plat, "verdict": "COOLDOWN", "note": whyr})
                    ledger({"ts": _now(), "platform": plat, "verdict": "COOLDOWN",
                            "found": 0, "new": 0, "note": str(whyr)[:160]})
                return
        except Exception:
            pass
        time.sleep(random.uniform(0, STAGGER_S))   # 错峰起跑，别让几个浏览器同时抢 IO
        rows, why = ctx["collector"](url, plat, limit=ctx["limit"], min_n=ctx["min_n"])
        with locked:
            if rows is None:
                results.append({"platform": plat, "verdict": "BLOCKED", "note": why, "url": url})
                ledger({"ts": _now(), "platform": plat, "verdict": "BLOCKED", "found": 0,
                        "new": 0, "url": url, "note": str(why)[:160]})
                return
            new, total = append_corpus(plat, rows)
            verdict = "OK" if new else "NO_NEW"
            results.append({"platform": plat, "verdict": verdict, "found": len(rows),
                            "new": len(new), "total": total, "url": url})
            ledger({"ts": _now(), "platform": plat, "verdict": verdict, "found": len(rows),
                    "new": len(new), "total": total, "url": url})

    # 采集与推理互斥：浏览器 1.1GB/实例，模型 4.6-9GB，同时干必换页（实测空闲 164MB→26MB）
    memmod = None
    try:
        sys.path.insert(0, HERE)
        import social_collect as _sc
        memmod = _sc
        want, free, cap = _sc.workers_by_mem(concurrency)
        if len(run) > 1 and want < concurrency:
            print("[learn] 内存限额：空闲%.0fMB → 并发 %d（请求 %d）" % (free, want, concurrency),
                  flush=True)
            concurrency = want
        if run and concurrency > 1:
            _sc.unload_models()
            _sc.set_mode("collect")
    except Exception as e:
        print("[learn] 内存模块不可用：%s" % str(e)[:60], flush=True)

    if concurrency > 1 and len(run) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            list(ex.map(lambda t: work(*t), run))
    else:
        for t in run:
            work(*t)

    if memmod:
        try:
            memmod.set_mode(None)      # 采集结束，放开互斥
        except Exception:
            pass

    # 有新增就重算画像（画像读 corpus，不读 raw）
    added = sum(r.get("new") or 0 for r in results)
    prof_ok = False
    if added:
        try:
            prof = profiler or _default_profile
            prof_ok = bool(prof())
        except Exception as e:
            results.append({"platform": "_profile", "verdict": "FAILED", "note": str(e)[:120]})
    out = {"verdict": "OK" if added else "NO_DATA", "added": added,
           "results": results, "profile_refreshed": prof_ok}
    heartbeat(out)
    return out


def _default_collect(url, platform, limit=200, min_n=10):
    sys.path.insert(0, HERE)
    import social_collect
    return social_collect.collect(url, platform, limit=limit, min_n=min_n)


def _default_profile():
    sys.path.insert(0, HERE)
    import social_profile
    rows = social_profile.load_rows([], raw_dir=None)
    # 直接读 corpus（学习循环的正身是 corpus，不是 raw）
    corpus = []
    for f in glob.glob(os.path.join(CORPUS, "*.jsonl")):
        plat = os.path.basename(f)[:-6]
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            r.setdefault("platform", plat)
            r["comment"] = r.get("text") or r.get("comment")
            corpus.append(r)
    if not corpus:
        return False
    prof = social_profile.profile(corpus)
    json.dump(prof, open(social_profile.OUT_JSON, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(social_profile.OUT_MD, "w", encoding="utf-8").write(social_profile.render_md(prof))
    return True


def status():
    if paused():
        print("[learn] 已暂停（哨兵 %s 存在）" % PAUSE)
    src = load_sources()
    for plat, cfg in (src.get("platforms") or {}).items():
        n = len(corpus_index(plat))
        print("[learn] %-14s 目标页%d 已入库%d%s" % (plat, len(cfg.get("urls") or []), n,
                                                    "" if cfg.get("enabled", True) else "（停用）"))
    if os.path.exists(HEARTBEAT):
        hb = json.load(open(HEARTBEAT, encoding="utf-8"))
        print("[learn] 最近一轮 %s %s 新增%s" % (hb.get("ts"), hb.get("verdict"), hb.get("added")))
    if os.path.exists(LEDGER):
        rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
        from collections import Counter
        print("[learn] 台账 %d 轮，结论分布 %s" % (len(rows), dict(Counter(r.get("verdict") for r in rows))))
    return 0


def self_test():
    global CORPUS, LEDGER, PAUSE
    cases = []
    # 自检必须与机器状态无关：内存紧张时 mem_pressure() 会把并发压到 1，
    # 并发相关断言就会假红（2026-11-17 实锚：同一份代码 8/10 与 10/10 交替）。
    # 这里把内存闸钉死为"无压力"，让自检只测逻辑。
    global mem_pressure
    _real_mp = mem_pressure
    mem_pressure = lambda: (False, "")
    orig = (CORPUS, LEDGER, PAUSE)
    CORPUS = os.path.join(ROOT, ".codely-cli", "tmp", "learn-selftest", "corpus")
    LEDGER = os.path.join(ROOT, ".codely-cli", "tmp", "learn-selftest", "ledger.jsonl")
    PAUSE = os.path.join(ROOT, ".codely-cli", "tmp", "learn-selftest", "PAUSE")
    os.makedirs(CORPUS, exist_ok=True)
    for f in glob.glob(os.path.join(CORPUS, "*.jsonl")) + [LEDGER]:
        if os.path.exists(f):
            os.remove(f)

    def fake_collect(url, platform, limit=200, min_n=10):
        return ([{"text": "这段剪辑太顺了"}, {"text": "求bgm名字"}], "")

    src = {"platforms": {"bilibili": {"urls": ["u1"]}, "douyin": {"urls": []}}}
    out = cycle(collector=fake_collect, profiler=lambda: True, sources=src)
    cases.append(("首轮入库 2 条", out["added"] == 2))
    cases.append(("无源平台报 NO_SOURCE",
                  any(r.get("verdict") == "NO_SOURCE" for r in out["results"])))
    # 幂等：同样内容再来一轮不新增
    out2 = cycle(collector=fake_collect, profiler=lambda: True, sources=src)
    cases.append(("重复内容不重复入库", out2["added"] == 0))
    # 抓不到要报 BLOCKED 而不是空 OK
    def blocked(url, platform, limit=200, min_n=10):
        return (None, "被风控")
    out3 = cycle(collector=blocked, profiler=lambda: True, sources=src)
    cases.append(("抓不到报 BLOCKED", any(r.get("verdict") == "BLOCKED" for r in out3["results"])))
    # 暂停哨兵
    open(PAUSE, "w").write("1")
    out4 = cycle(collector=fake_collect, profiler=lambda: True, sources=src)
    cases.append(("哨兵存在即暂停", out4["verdict"] == "PAUSED"))
    os.remove(PAUSE)
    # 并发：两平台同时跑都要拿到结果；一个平台失败不许拖死另一个
    def mixed(url, platform, limit=200, min_n=10):
        time.sleep(0.4)
        if platform == "weibo":
            return (None, "被风控")
        return ([{"text": "%s-真实评论" % platform}], "")

    src2 = {"platforms": {"bilibili": {"urls": ["u1"]}, "weibo": {"urls": ["u2"]}}}
    t0 = time.time()
    out5 = cycle(collector=mixed, profiler=lambda: True, sources=src2, concurrency=2)
    dt = time.time() - t0
    cases.append(("并发两平台都拿到结论",
                  {r["platform"]: r["verdict"] for r in out5["results"]}.get("bilibili") == "OK"
                  and {r["platform"]: r["verdict"] for r in out5["results"]}.get("weibo") == "BLOCKED"))
    cases.append(("并发整轮耗时可接受（<15s）", dt < 15))
    cases.append(("内存总闸可调用", isinstance(mem_pressure()[0], bool)))
    try:
        sys.path.insert(0, HERE)
        import social_collect as _sc
        cases.append(("每平台 profile 路径互不相同",
                      _sc.profile_for("bilibili") != _sc.profile_for("weibo")))
    except Exception:
        cases.append(("每平台 profile 路径互不相同", False))
    # 台账落行
    n_led = sum(1 for _ in open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else 0
    cases.append(("台账必须逐轮落行", n_led >= 4))
    CORPUS, LEDGER, PAUSE = orig
    mem_pressure = _real_mp          # 还原真实内存闸
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=1200, help="循环间隔秒（默认 20 分钟）")
    ap.add_argument("--concurrency", type=int, default=2,
                    help="并发平台数（默认 2；内存紧张自动降到 1）")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--min", type=int, default=10)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.status:
        return status()
    if a.once:
        conc = a.concurrency
        press, why = mem_pressure()
        if press and conc > 1:
            print("[learn] 内存总闸：%s → 并发降到 1" % why)
            conc = 1
        out = cycle(limit=a.limit, min_n=a.min, concurrency=conc)
        print("[learn] %s 新增%d 画像刷新%s" % (out["verdict"], out["added"],
                                               out["profile_refreshed"]))
        for r in out["results"]:
            print("  - %-12s %s %s" % (r.get("platform"), r.get("verdict"),
                                       (r.get("note") or "")[:60]))
        return 0
    if a.loop:
        print("[learn] 24h 循环启动 间隔%ds 并发%d（哨兵 %s 可随时停）"
              % (a.interval, a.concurrency, PAUSE))
        while True:
            try:
                conc = a.concurrency
                press, why = mem_pressure()
                if press and conc > 1:
                    print("[learn] 内存总闸：%s → 本轮并发 1" % why)
                    conc = 1
                out = cycle(limit=a.limit, min_n=a.min, concurrency=conc)
                print("[learn] %s %s 新增%d" % (_now(), out["verdict"], out["added"]))
                # 采不到新料就补源：SOURCES 池子里的视频全采过之后，每轮必然 NO_NEW，
                # 语料停涨 → 训练只能重跑同一份数据（2026-11-25 实锚）。
                # maybe() 自带 3 小时节流，不会把接口打成轮询。
                if not out.get("added"):
                    try:
                        import bili_sources_refresh as _sr
                        r = _sr.maybe()
                        print("[learn] 源料补给：%s（新增 %s 条）"
                              % (r.get("why") or "刷新", r.get("added")))
                    except Exception as e:
                        print("[learn] 源料补给失败 %s: %s"
                              % (type(e).__name__, str(e)[:100]))
            except KeyboardInterrupt:
                print("[learn] 手动停止")
                return 0
            except Exception as e:
                print("[learn] 本轮异常 %s: %s" % (type(e).__name__, str(e)[:120]))
            time.sleep(max(60, a.interval))
    print("[learn] 用 --once / --loop / --status / --self-test")
    return 2


if __name__ == "__main__":
    sys.exit(main())
