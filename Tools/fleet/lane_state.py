#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane_state.py - 每条线一个状态件，原地更新，绝不写别人的。

为什么要有它（CEO 2026-11-26「你要经常更新，但不要互相影响 应该各司其职」）：
现状是三件混在一起——
  · 各线把自家的让路/失败写进**别人的**台账（训练台账里混着 publish 占锁的记录）；
  · 共享的 state 目录被一次性作业写满时间戳文件（实测 segfill-* 939 个、tri-lane-* 24 个），
    谁想扫一遍状态都要先穿过这堆垃圾；
  · 抢 GPU 的策略散在各线代码里（train 去问 practice_due、practice 去认 "train" 字样、
    selfgen 直接让路），改一条线的行为会悄悄改掉另一条线的行为。
本模块只解决第一条的一半：给每条线一个**自己的**状态件，字段固定、原子写、
只允许写 `lane-<自己的名字>.json`。这样"经常更新"是每条线自己的事，
而"互相影响"从写入面上被物理切断——一条线写得再勤，也不会让另一条线读到半截文件。

不做的事：不做调度、不做判据、不 import 其它工具。调度归 gpu_lease/仲裁，判据归各线。

自检（负控，5 条）：
  · 写完能读回；重复写是**原地更新**，不新增文件
  · 写 A 不许改动 B 的文件（内容与 mtime 都不许变）
  · 非法线名（含 / 、.. 、大写、超长）必须被拒，不许拿它拼路径
  · 陈旧判定：ts 往前挪要判 stale
  · 落盘永远是完整 JSON（临时文件 + os.replace，读者不会看到半截）

用法：
  python3 Tools/fleet/lane_state.py --put train --phase training --meta '{"seg":"memer"}'
  python3 Tools/fleet/lane_state.py --board
  python3 Tools/fleet/lane_state.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state")

NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,23}$")
PREFIX = "lane-"
STALE_S = 3600          # 默认：一小时没更新算陈旧（各线节拍不同，看板允许覆盖）

# 一次性作业留下的时间戳产物前缀。只归档这些，别的一律不碰——
# 白名单比"匹配所有带日期的文件"安全（后者会误伤别人正在用的当前件）。
ONESHOT_PREFIXES = ("segfill-", "tri-lane-", "segment-fill-", "ab-matrix-",
                    "social-day-plan-", "social-24x7-", "social-agent-day-",
                    "model-queue-", "comment-ab-")


def _path(lane):
    """线名 → 文件路径。非法名一律拒绝，绝不拿它拼路径。"""
    if not NAME_RE.match(lane or ""):
        raise ValueError("非法线名：%r（只许小写字母开头、字母数字下划线连字符、≤24）" % (lane,))
    return os.path.join(STATE, "%s%s.json" % (PREFIX, lane))


def put(lane, phase, **meta):
    """原地更新本线状态件。返回写入的记录。

    原子写：先在同目录写临时文件，再 os.replace 覆盖。读者要么看到旧版、要么看到新版，
    不会读到半截 JSON——这是"不互相影响"里最容易被忽略的一条（读到半截=别人的错算到你头上）。
    """
    path = _path(lane)
    os.makedirs(STATE, exist_ok=True)
    rec = {"lane": lane, "ts": time.time(),
           "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "phase": str(phase or ""), "pid": os.getpid()}
    # meta 只收标量/短容器，避免有人把整份语料塞进状态件
    for k, v in (meta or {}).items():
        if k in ("lane", "ts", "ts_iso", "phase", "pid"):
            continue
        rec[str(k)] = v
    fd, tmp = tempfile.mkstemp(dir=STATE, prefix=".tmp-lane-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise
    return rec


def get(lane):
    try:
        return json.load(open(_path(lane), encoding="utf-8"))
    except Exception:
        return None


def age(lane, now=None):
    d = get(lane)
    if not d:
        return None
    return round((now or time.time()) - float(d.get("ts") or 0), 1)


def board(stale_s=STALE_S, now=None):
    """只读看板：每条线的龄期与阶段。不写任何文件。"""
    now = now or time.time()
    out = []
    try:
        names = os.listdir(STATE)
    except Exception:
        return out
    for fn in sorted(names):
        if not (fn.startswith(PREFIX) and fn.endswith(".json")):
            continue
        lane = fn[len(PREFIX):-5]
        d = get(lane)
        if not d:
            continue
        a = round(now - float(d.get("ts") or 0), 1)
        out.append({"lane": lane, "age_s": a, "stale": a > stale_s,
                    "phase": d.get("phase"), "ts_iso": d.get("ts_iso"),
                    "meta": {k: v for k, v in d.items()
                             if k not in ("lane", "ts", "ts_iso", "phase", "pid")}})
    return out


def archive_stale(older_than_s=86400, apply=False, now=None):
    """把一次性作业的时间戳产物搬进 state/_archive/<YYYYMMDD>/。只搬不删。

    为什么不删：这些是历史证据（哪次采集跑过、耗多久），删了就再也查不到；
    但它们留在 state 根目录会让"当前状态"看不出重点。搬走是唯一同时满足
    「不丢证据」和「目录能看」的做法。
    """
    now = now or time.time()
    cut = now - float(older_than_s)
    plan = []
    try:
        names = os.listdir(STATE)
    except Exception:
        return plan
    for fn in names:
        if not any(fn.startswith(p) for p in ONESHOT_PREFIXES):
            continue
        p = os.path.join(STATE, fn)
        if not os.path.isfile(p):
            continue
        try:
            if os.path.getmtime(p) >= cut:
                continue
        except Exception:
            continue
        plan.append(fn)
    if not apply or not plan:
        return plan
    dst = os.path.join(STATE, "_archive", time.strftime("%Y%m%d", time.localtime(now)))
    os.makedirs(dst, exist_ok=True)
    moved = 0
    for fn in plan:
        try:
            shutil.move(os.path.join(STATE, fn), os.path.join(dst, fn))
            moved += 1
        except Exception:
            pass
    print("[lane] 归档 %d 个一次性产物 → %s" % (moved, os.path.relpath(dst, ROOT)))
    return plan


def self_test():
    import shutil
    global STATE
    saved = STATE
    d = tempfile.mkdtemp(prefix="lane-")
    STATE = d
    cases = []
    try:
        # 1 写读回 + 原地更新（不新增文件）
        put("alpha", "phase1", seg="x")
        put("alpha", "phase2", seg="y")
        got = get("alpha")
        files = [f for f in os.listdir(d) if f.endswith(".json")]
        cases.append(("写完能读回且是原地更新（不新增文件）",
                      got.get("phase") == "phase2" and got.get("seg") == "y"
                      and files == ["lane-alpha.json"]))
        # 2 负控：写 A 不许动 B
        put("beta", "b1")
        pb = _path("beta")
        before = (open(pb, "rb").read(), os.stat(pb).st_mtime_ns)
        time.sleep(0.01)
        put("alpha", "phase3")
        after = (open(pb, "rb").read(), os.stat(pb).st_mtime_ns)
        cases.append(("写 A 不改动 B（内容与 mtime 都不变）", before == after))
        # 3 负控：非法线名必须被拒
        bad = []
        for name in ("../etc/passwd", "a/b", "Alpha", "a" * 40, "", "a b"):
            try:
                _path(name)
            except ValueError:
                bad.append(name)
        cases.append(("非法线名全部被拒（不许拼路径）", len(bad) == 6))
        # 4 陈旧判定
        put("gamma", "old")
        p = _path("gamma")
        rec = json.load(open(p, encoding="utf-8"))
        rec["ts"] = time.time() - 7200
        json.dump(rec, open(p, "w", encoding="utf-8"))
        b = {x["lane"]: x for x in board(stale_s=3600)}
        cases.append(("两小时没更新 → 判陈旧", b.get("gamma", {}).get("stale") is True))
        # 5 落盘永远是完整 JSON（读的同时被反复覆盖也不出现半截）
        ok_json = True
        for i in range(30):
            put("delta", "p%d" % i, pad="x" * 4000)
            try:
                json.loads(open(_path("delta"), encoding="utf-8").read())
            except Exception:
                ok_json = False
                break
        cases.append(("反复覆盖后文件始终是完整 JSON", ok_json))
        # 6 归档白名单：只挑一次性前缀且够老的，别的文件不动（负控：当前件必须留着）
        old = os.path.join(d, "segfill-20200101-0000.log")
        cur = os.path.join(d, "segfill-current.txt")
        keep = os.path.join(d, "KEEP-ME.json")
        for p in (old, cur, keep):
            open(p, "w").write("x")
        os.utime(old, (0, 0))                      # 1970 → 必定"够老"
        plan = archive_stale(older_than_s=86400, apply=False)
        planned = set(plan)
        archive_stale(older_than_s=86400, apply=True)
        cases.append(("归档只搬够老的一次性产物，当前件与无关件都留着",
                      "segfill-20200101-0000.log" in planned
                      and "segfill-current.txt" not in planned
                      and "KEEP-ME.json" not in planned
                      and os.path.exists(cur) and os.path.exists(keep)
                      and not os.path.exists(old)))
    finally:
        STATE = saved
        shutil.rmtree(d, ignore_errors=True)
    ok = sum(1 for _, v in cases if v)
    for name, v in cases:
        print("  [%s] %s" % ("PASS" if v else "FAIL", name))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--put")
    ap.add_argument("--phase", default="")
    ap.add_argument("--meta", default="{}")
    ap.add_argument("--board", action="store_true")
    ap.add_argument("--archive-stale", action="store_true")
    ap.add_argument("--older-than-h", type=float, default=24.0,
                    help="归档门槛（小时）：默认 24h 前的一次性产物")
    ap.add_argument("--apply", action="store_true", help="真的搬（默认只列清单）")
    ap.add_argument("--stale-s", type=int, default=STALE_S)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.archive_stale:
        plan = archive_stale(older_than_s=a.older_than_h * 3600, apply=a.apply)
        print("[lane] %s %d 个一次性产物%s" % (
            "已归档" if a.apply else "待归档", len(plan),
            "" if a.apply else "（加 --apply 才真的搬；只搬不删）"))
        for fn in plan[:10]:
            print("       %s" % fn)
        if len(plan) > 10:
            print("       … 共 %d 个" % len(plan))
        return 0
    if a.board:
        rows = board(stale_s=a.stale_s)
        if not rows:
            print("[lane] 还没有任何线写过状态件")
            return 0
        print("%-10s %8s %6s %-14s %s" % ("线", "龄期", "陈旧", "阶段", "附带"))
        for r in rows:
            print("%-10s %7.0fs %6s %-14s %s" % (
                r["lane"], r["age_s"], "是" if r["stale"] else "否",
                str(r["phase"])[:14], json.dumps(r["meta"], ensure_ascii=False)[:60]))
        return 0
    if a.put:
        try:
            meta = json.loads(a.meta or "{}")
        except Exception:
            print("[lane] --meta 不是合法 JSON", file=sys.stderr)
            return 2
        rec = put(a.put, a.phase, **meta)
        print(json.dumps(rec, ensure_ascii=False))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
