#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_guard.py — 养号线只读守卫：把"做对了没有"变成落盘判据。

为什么要有（2026-11-21 实测）：`agent_audit.py` 原来只认三件事——执行体在、证据在、
证据新鲜。结果 12/12 全绿，而两个号**当天一条评论都没发出去**（comments-sent 最近一条
78.7 小时前）。文件被 daemon 碰过就记 OK，等于只审计了"有人动过"，没审计"动对了"。

分工（这一条要守住，否则又变回互相洗白）：
  · social_guard = 判据提供者：领域规则、阈值、取样，全部只读，不产内容、不占 GPU；
  · agent_audit  = 契约执行者：只判"执行体在不在 / 证据新不新 / pass 映射是不是 true"。
所以本文件**不许**写任何内容、不许调模型、不许改账号与配置，只读盘 + 算数 + 落证据。

五组检查（每组一份证据，pass 映射给 agent_audit 断言用）：
  corpus    CR01–CR08  语料污染、烘焙、简报、人设隔离、多样性、缺陷率
  train     TR01–TR06  epoch、判据质量、配方一致、ACTIVE 指针、评测功率、租约
  accounts  AC01–AC05  活人节奏、跨号同视频、同 mid 多 profile、夜间静默、不删重发
  sends     SD01–SD06  评论出稿龄期、失败归因、连续真失败、引流硬拒、配额、副动作
  sched     SC01–SC04  spec 声明与实载一致、rc 异常、重复出稿引擎、审计自检

三态：ok=True 通过 / False 不通过 / None 无法测量（SKIP，**不许当通过**）。
  SKIP 必须写 reason，因为"量不到"和"做对了"是两件事（2026-11-20 假绿教训）。

用法
  python3 Tools/fleet/social_guard.py --all            # 跑五组并落证据
  python3 Tools/fleet/social_guard.py --group corpus   # 单组
  python3 Tools/fleet/social_guard.py --all --json
  python3 Tools/fleet/social_guard.py --self-test      # 每种判据都有"改坏必须红"负控
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import plistlib
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(SOCIAL, "state")
HEALTH = os.path.join(ROOT, ".codely-cli", "state", "HEALTH.json")
GPU_REC = os.path.join(ROOT, "cph4", "fleet", "state", "gpu-lease.json")
ACCFILE = os.path.expanduser("~/.fluxgroup/bili-accounts.json")
PY = sys.executable

# 起源时段：按 2026-11-21 activity_clock 实测，1–6 点接近 0，深夜开窗最像脚本
NIGHT_HOURS = (1, 2, 3, 4, 5, 6)

# 已声明退役/被取代的调度器：它们若还在跑，说明旧引擎复活或一次性任务没卸
RETIRED_SCHEDULERS = {
    "com.fluxgroup.practice10": "CEO 2026-11-18「实战十轮」一次性任务，跑完就该 bootout；"
                                "留在列表里下次 bootstrap 会再发十条（真发，不是演练）",
    "com.fluxgroup.usersession": "2026-11-20 停用（被 agent_daemon 取代）",
    "com.fluxgroup.social24x7": "2026-11-20 停用（与 socialloop 重复）",
    "com.fluxgroup.socialagentday": "2026-11-20 停用（与 agent-acct* 重复）",
    "com.fluxgroup.sociallearn": "2026-11-20 停用（训练让路期）",
}


# ---------------------------------------------------------------- 基础读盘
def _j(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _rows(path, limit=None):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []
    return out[-limit:] if limit else out


def _glob_rows(pattern):
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, pattern) if not os.path.isabs(pattern) else pattern)):
        out.extend(_rows(p))
    return out


def _age_h(ts):
    """ISO 字符串或 epoch 秒 → 小时龄期；取不到返回 None。"""
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            return (time.time() - float(ts)) / 3600
        s = str(ts).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        if d.tzinfo:
            d = d.replace(tzinfo=None)
        return (datetime.now() - d).total_seconds() / 3600
    except Exception:
        return None


def _mtime_h(path):
    try:
        return (time.time() - os.path.getmtime(path)) / 3600
    except Exception:
        return None


def _newest(pattern):
    hits = glob.glob(os.path.join(ROOT, pattern) if not os.path.isabs(pattern) else pattern)
    return max(hits, key=lambda p: os.path.getmtime(p)) if hits else None


def _mk(cid, name, ok, sev, detail="", n=None):
    """ok: True/False/None(SKIP)。SKIP 必须在 detail 里写清为什么量不到。"""
    return {"id": cid, "name": name, "ok": ok, "sev": sev, "detail": detail, "n": n}


def _import(name):
    sys.path.insert(0, HERE)
    try:
        return __import__(name)
    except Exception:
        return None


# ---------------------------------------------------------------- corpus
def corpus_checks():
    out = []
    tb = _import("train_build")

    # CR01 生成侧 AI 腔命中率（闸之前；只认 ai_rate 的落盘）
    files = sorted(glob.glob(os.path.join(STATE, "AI-RATE-*.json")),
                   key=lambda p: os.path.getmtime(p))
    files = [f for f in files if (_mtime_h(f) or 1e9) <= 48]
    if not files:
        out.append(_mk("CR01", "生成侧 AI 腔命中率", None, "P1",
                       "48h 内无 AI-RATE 落盘（ai_rate.py --json-out），量不到≠通过"))
    else:
        f = files[-1]
        d = _j(f, {}) or {}
        rate = d.get("ai_hit_rate")
        ok = None if rate is None else (float(rate) <= 0.05)
        out.append(_mk("CR01", "生成侧 AI 腔命中率", ok, "P1",
                       "%s ai_hit=%.1f%%（线 ≤5%%）%s" % (
                           os.path.basename(f), 100 * float(rate or 0),
                           "" if ok else " 命中词=%s" % (d.get("ai_hit_words") or [])[:2]),
                       d.get("n")))

    # CR02 语料侧污染率（实战回流 + 最新自举；用 AI_SMELL_CORPUS 而非输出级严表）
    targets = [os.path.join(SOCIAL, "corpus", "human", "own_practice.jsonl")]
    sg = sorted(glob.glob(os.path.join(SOCIAL, "corpus", "human", "selfgen-*.jsonl")),
                key=lambda p: os.path.getmtime(p))[-1:]
    targets += sg
    if not tb:
        out.append(_mk("CR02", "语料侧 AI 腔污染率", None, "P1", "train_build 导入失败，量不到"))
    elif not any(os.path.exists(t) for t in targets):
        out.append(_mk("CR02", "语料侧 AI 腔污染率", None, "P1", "没有可巡检的语料文件"))
    else:
        rows, hits, reasons = 0, 0, {}
        for t in targets:
            for r in _rows(t):
                text = r.get("text") or ""
                if not text:
                    continue
                rows += 1
                why = tb.ai_smell(text)
                if why:
                    hits += 1
                    reasons[why[:14]] = reasons.get(why[:14], 0) + 1
        rate = hits / rows if rows else 0.0
        out.append(_mk("CR02", "语料侧 AI 腔污染率", rate <= 0.05, "P1",
                       "%.1f%%（线 ≤5%%）%d/%d 行%s" % (
                           100 * rate, hits, rows,
                           (" 主因=" + json.dumps(sorted(reasons.items(), key=lambda x: -x[1])[:3],
                                                 ensure_ascii=False)) if hits else ""),
                       rows))

    # CR03 烘焙新鲜 + 分段（新语料进不了训练集的第一症状）
    baked = os.path.join(SOCIAL, "corpus", "human", "BAKED-stats.json")
    b = _j(baked, {})
    if not b:
        out.append(_mk("CR03", "烘焙与分段", False, "P1", "BAKED-stats.json 缺失"))
    else:
        age = _mtime_h(baked)
        segs = b.get("segments") or {}
        verdicts = b.get("verdicts") or {}
        ok = (age is not None and age <= 6 and (b.get("rows") or 0) > 0
              and len(segs) >= 6 and bool(verdicts))
        out.append(_mk("CR03", "烘焙与分段", ok, "P1",
                       "%.1fh前 rows=%s 段=%d verdict=%d" % (
                           age or -1, b.get("rows"), len(segs), len(verdicts)),
                       b.get("rows")))

    # CR04 内容简报覆盖（没标题就等于没内容，只能泛泛而谈）
    briefs = (_j(os.path.join(SOCIAL, "VIDEO-BRIEFS.json"), {}) or {}).get("briefs") or {}
    if not briefs:
        out.append(_mk("CR04", "内容简报覆盖", False, "P2", "VIDEO-BRIEFS.json 空"))
    else:
        cov = sum(1 for v in briefs.values()
                  if isinstance(v, dict) and (v.get("topics") or v.get("desc")))
        rate = cov / len(briefs)
        out.append(_mk("CR04", "内容简报覆盖", rate >= 0.9, "P2",
                       "%.1f%% 有话题或简介（线 ≥90%%），%d 条" % (100 * rate, len(briefs)), len(briefs)))

    # CR05 人设隔离：acct1 亲笔样句不许进共享训练集（否则新号被训成老号口吻）
    # 判据要先剥掉 [doge] 这类表情码——它们人人都在用，按 5 字符算会把「[doge]」判成抄句。
    def _plain(s):
        return re.sub(r"\[[^\]]{1,8}\]", "", str(s))

    persona = _j(os.path.join(SOCIAL, "HUMAN-PERSONA-v1.json"), {}) or {}
    few = [_plain(s) for s in (persona.get("fewshot") or []) if isinstance(s, str)]
    run = _j(_newest(os.path.join(SOCIAL, "train", "RUNS", "*", "RUN.json")) or "", {}) or {}
    data_dir = ""
    argv = run.get("argv") or []
    for i, a in enumerate(argv):
        if a == "--data" and i + 1 < len(argv):
            data_dir = argv[i + 1]
    train_jsonl = os.path.join(data_dir, "train.jsonl") if data_dir else ""
    if not few or not train_jsonl or not os.path.exists(train_jsonl):
        out.append(_mk("CR05", "人设隔离（亲笔样句不入共享集）", None, "P1",
                       "缺样句或训练集路径，量不到（样句=%d）" % len(few)))
    else:
        # 只有「≥6 个连续字完全相同」才算抄；表情码已剥、标点不计
        grams = set()
        for s in few:
            s = re.sub(r"[，。！？、,.!?~～\s]", "", s)
            for i in range(len(s) - 5):
                grams.add(s[i:i + 6])
        hits, sample = 0, []
        for r in _rows(train_jsonl):
            for m in (r.get("messages") or []):
                if m.get("role") != "assistant":
                    continue
                t = re.sub(r"[，。！？、,.!?~～\s]", "", _plain(m.get("content") or ""))
                got = [t[i:i + 6] for i in range(len(t) - 5) if t[i:i + 6] in grams]
                if got:
                    hits += 1
                    if len(sample) < 3:
                        sample.append(got[0])
        out.append(_mk("CR05", "人设隔离（亲笔样句不入共享集）", hits == 0, "P1",
                       "命中 %d 条（线 0）%s" % (hits, ("，如 " + "/".join(sample)) if sample else ""),
                       hits))

    # CR06 采集新鲜（语料只减不增 = 训练在吃老本）
    rows = _rows(os.path.join(SOCIAL, "SOCIAL-LOOP-LEDGER.jsonl"), 400)
    ph = [r for r in rows if str(r.get("phase", "")) in ("collect", "learn", "harvest")]
    recent = [r for r in ph if (_age_h(r.get("ts")) or 1e9) <= 24]
    out.append(_mk("CR06", "采集新鲜（24h）", len(recent) >= 1, "P1",
                   "24h 内采集 %d 次 / 总 %d 次" % (len(recent), len(ph)), len(recent)))

    # CR07 多样性三项核心（真实：陈述 49%、短评 38%、长度跨度 7→22）
    div = _j(os.path.join(STATE, "DIVERSITY.json"), {}) or {}
    trains = [x for x in (div.get("train") or []) if isinstance(x, dict)]
    allseg = next((x for x in trains if x.get("seg") in ("__all__", "all")), None)
    if not allseg:
        out.append(_mk("CR07", "多样性三项核心", None, "P2", "DIVERSITY.json 无全段数据"))
    else:
        st, sh, sp = (allseg.get("shape_top"), allseg.get("short_share"),
                      allseg.get("len_span"))
        ok = (st is not None and st <= 0.60 and sh is not None and sh >= 0.25
              and sp is not None and sp >= 12)
        out.append(_mk("CR07", "多样性三项核心", ok, "P2",
                       "陈述 %.0f%%(≤60) 短评 %.0f%%(≥25) 跨度 %s(≥12)" % (
                           100 * (st or 0), 100 * (sh or 0), sp), allseg.get("n")))

    # CR08 生成侧缺陷率（占位符/烂梗/破损表情码，闸之前就错的东西）
    if not files:
        out.append(_mk("CR08", "生成侧缺陷率", None, "P1", "48h 内无 AI-RATE 落盘"))
    else:
        d = _j(files[-1], {}) or {}
        rate = d.get("defect_rate")
        out.append(_mk("CR08", "生成侧缺陷率", None if rate is None else (float(rate) <= 0.05),
                       "P1", "%.1f%%（线 ≤5%%）%s" % (
                           100 * float(rate or 0),
                           (" 主因=" + str((d.get("defect_words") or [])[:3])) if rate else ""),
                       d.get("n")))
    return out


# ---------------------------------------------------------------- train
def train_checks():
    out = []
    runs = sorted(glob.glob(os.path.join(SOCIAL, "train", "RUNS", "*", "RUN.json")),
                  key=lambda p: os.path.getmtime(p))
    run = _j(runs[-1], {}) if runs else None

    # TR01 epoch：iters ÷ 训练行数，3–5 才算真看过几遍（实测 1.1 与 0.49 都是白跑）
    if not run or not run.get("train_rows"):
        out.append(_mk("TR01", "训练容量（epoch 3–5）", None, "P2", "无 RUN.json，量不到"))
    else:
        ep = float(run.get("iters") or 0) / float(run["train_rows"])
        out.append(_mk("TR01", "训练容量（epoch 3–5）", 3 <= ep <= 5, "P2",
                       "iters=%s rows=%s → %.2f epoch" % (
                           run.get("iters"), run["train_rows"], ep), run.get("train_rows")))

    # TR02 轮次判据质量：verdict 必须合法；KEEP/REJECT 必须有 val_min；让路/失败必须有 why。
    # 这条防的是 2026-11-17 那个假绿：loss 行带 ANSI 色码没剥，val_min 静默记 None 还判 KEEP。
    rows = _rows(os.path.join(SOCIAL, "train", "TRAIN-LOOP-LEDGER.jsonl"), 5)
    KNOWN = {"KEEP", "REJECT", "BASELINE", "PLUMBING", "BLOCKED", "TRAIN-FAIL", "NO-DATA"}
    if not rows:
        out.append(_mk("TR02", "轮次判据质量", False, "P1", "TRAIN-LOOP-LEDGER 空"))
    else:
        bad = []
        for r in rows:
            v = r.get("verdict")
            if v not in KNOWN:
                bad.append("%s verdict=%r" % (r.get("seg"), v))
            elif v in ("KEEP", "REJECT") and r.get("val_min") is None:
                bad.append("%s %s 缺 val_min" % (r.get("seg"), v))
            elif v in ("BLOCKED", "TRAIN-FAIL") and not (r.get("why") or "").strip():
                bad.append("%s %s 缺 why" % (r.get("seg"), v))
        out.append(_mk("TR02", "轮次判据质量", not bad, "P1",
                       "近 %d 轮：%s" % (len(rows), ("；".join(bad[:4])) if bad else "判据齐全"),
                       len(rows)))

    # TR03 配方一致：有数据但配方 != 当前 RECIPE 的段必须重造（v5 的 3 项改动还没落到各段）
    tb = _import("train_build")
    st = _j(os.path.join(SOCIAL, "train", "LOOP-STATE.json"), {}) or {}
    segs = st.get("segments") or {}
    if not tb or not segs:
        out.append(_mk("TR03", "配方一致（RECIPE）", None, "P1", "缺 LOOP-STATE 或 train_build"))
    else:
        stale = [k for k, v in segs.items()
                 if isinstance(v, dict) and (v.get("rows") or 0) > 0
                 and (v.get("recipe") or "") != tb.RECIPE]
        out.append(_mk("TR03", "配方一致（RECIPE=%s）" % tb.RECIPE, not stale, "P1",
                       "需重造 %d 段%s" % (len(stale), ("：" + ", ".join(stale[:8])) if stale else ""),
                       len(segs)))

    # TR04 ACTIVE 指针一致（出稿用哪个适配器只认这个文件）
    act = _j(os.path.join(SOCIAL, "train", "ACTIVE.json"), {}) or {}
    mode = act.get("mode")
    if mode == "base":
        ok, why = (act.get("run") in ("", None)), "base 模式 run 必须为空"
    elif mode == "lora":
        rd = os.path.join(ROOT, act.get("run") or "")
        ok, why = os.path.isdir(rd), "lora 模式 run 目录必须存在"
    else:
        ok, why = False, "mode 只能是 base/lora（实际 %r）" % mode
    out.append(_mk("TR04", "ACTIVE 指针一致", ok, "P1",
                   "%s（%s，%s）" % (why, mode, act.get("switched_at"))))

    # TR05 评测功率：n=10 的噪声大于判定阈值（79.9 vs 55.9 实锚）
    ev = _j(os.path.join(SOCIAL, "train", "SEGMENT-EVAL.json"), {}) or {}
    entries = [x for k in ("base", "lora") for x in (ev.get(k) or []) if isinstance(x, dict)]
    ns = [x.get("n") for x in entries if x.get("n") is not None]
    if not ns:
        out.append(_mk("TR05", "评测功率（n≥30）", None, "P2", "SEGMENT-EVAL 无样本数"))
    else:
        out.append(_mk("TR05", "评测功率（n≥30）", min(ns) >= 30, "P2",
                       "最小 n=%d，%d 组（线 ≥30）" % (min(ns), len(ns)), len(ns)))

    # TR06 租约：同时最多一个持有者，且持有者进程还活着（野锁会让全队永久让路）
    rec = _j(GPU_REC, {}) or {}
    holders = {}
    for k, v in rec.items():
        if isinstance(v, dict) and not k.startswith("_"):
            ttl = float(v.get("ttl_s") or 0)
            if not ttl or (time.time() - float(v.get("ts") or 0)) <= ttl:
                holders[k] = v
    if not holders:
        out.append(_mk("TR06", "GPU 租约健康", True, "P1", "当前无持有者"))
    else:
        dead = []
        for k, v in holders.items():
            pid = v.get("pid")
            alive = False
            if pid:
                try:
                    os.kill(int(pid), 0)
                    alive = True
                except Exception:
                    alive = False
            if not alive:
                dead.append(k)
        ok = len(holders) <= 1 and not dead
        out.append(_mk("TR06", "GPU 租约健康", ok, "P1",
                       "持有=%s%s" % (list(holders), ("，死锁：" + ",".join(dead)) if dead else "")),
                       len(holders))
    return out


# ---------------------------------------------------------------- accounts
def account_checks():
    out = []
    health = _j(HEALTH, {}) or {}
    accts = [a for a in (health.get("accounts") or []) if isinstance(a, dict)]
    clock = (_j(os.path.join(SOCIAL, "ACTIVITY-CLOCK.json"), {}) or {}).get("index") or {}
    idx_now = clock.get(str(datetime.now().hour))

    # AC01 活着且真的在动：心跳在、PID 在，但 14 小时没动作 = 假活
    if not accts:
        out.append(_mk("AC01", "活人节奏（alive+在动）", False, "P1", "HEALTH 无账号"))
    else:
        limit = 2.0 if (idx_now is None or float(idx_now) > 0.5) else 6.0
        bad = []
        for a in accts:
            age = _age_h(a.get("last_ts"))
            if not a.get("alive"):
                bad.append("%s 进程不在" % a.get("alias"))
            elif age is not None and age > limit:
                bad.append("%s %.1fh 没动作" % (a.get("alias"), age))
        out.append(_mk("AC01", "活人节奏（alive+在动）", not bad, "P1",
                       "；".join(bad) if bad else "两号均在活动（上限 %.0fh）" % limit, len(accts)))

    # AC02 跨号同一视频（两个人不会同一分钟摸同一条）
    led = [r for r in _rows(os.path.join(SOCIAL, "USER-AGENT-LEDGER.jsonl"), 800)
           if (_age_h(r.get("ts")) or 1e9) <= 24]
    per = {}
    for r in led:
        if r.get("aid") and r.get("account"):
            per.setdefault(str(r["aid"]), set()).add(r["account"])
    dup = {k: sorted(v) for k, v in per.items() if len(v) > 1}
    out.append(_mk("AC02", "跨号隔离（24h 不同视频）", not dup, "P0",
                   ("同视频被两号碰过 %d 条：%s" % (len(dup), list(dup)[:2])) if dup
                   else "24h 内 %d 条视频无跨号重叠" % len(per), len(per)))

    # AC03 同一 mid 不许出现在两个活跃 alias（同号两 profile = 自造两套设备指纹）
    acc = _j(ACCFILE, {}) or {}
    table = acc.get("accounts") or {}
    active_aliases = {a.get("alias") for a in accts}
    by_mid = {}
    for alias, v in table.items():
        if isinstance(v, dict) and v.get("mid") and alias in active_aliases:
            by_mid.setdefault(str(v["mid"]), []).append(alias)
    if not by_mid:
        out.append(_mk("AC03", "同 mid 单 profile", None, "P0",
                       "账号表无可用 mid（%d 条），量不到" % len(table)))
    else:
        bad = {m: a for m, a in by_mid.items() if len(a) > 1}
        out.append(_mk("AC03", "同 mid 单 profile", not bad, "P0",
                       ("同 mid 多活跃 profile：%s" % list(bad.values())[:2]) if bad
                       else "%d 个 mid 各一个活跃 profile" % len(by_mid), len(by_mid)))

    # AC04 夜间静默（1–6 点动作数必须为 0；深夜开窗是最像脚本的行为）
    rows7 = [r for r in _rows(os.path.join(SOCIAL, "USER-AGENT-LEDGER.jsonl"), 4000)
             if (_age_h(r.get("ts")) or 1e9) <= 24 * 7]
    night = []
    for r in rows7:
        try:
            h = datetime.fromisoformat(str(r.get("ts"))).hour
        except Exception:
            continue
        if h in NIGHT_HOURS:
            night.append(r)
    out.append(_mk("AC04", "夜间静默（1–6 点）", not night, "P0",
                   "近 7 天夜间动作 %d 次%s" % (
                       len(night), ("，如 " + str(night[-1].get("ts")) + " " + str(night[-1].get("action")))
                       if night else ""), len(rows7)))

    # AC05 同视频不重复评论（7 天 ≤1 条）：B站把重复评论判「无关」折叠，
    # 折叠后删了重发可能触发 5 日评论限制 + 关联视频永久降权（2026-11-20 实锚）。
    sent = _rows(os.path.join(SOCIAL, "comments-sent.jsonl"))
    recent = [r for r in sent if (_age_h(r.get("ts")) or 1e9) <= 24 * 7]
    cnt = {}
    for r in recent:
        if r.get("ok"):
            cnt[str(r.get("aid"))] = cnt.get(str(r.get("aid")), 0) + 1
    dup = {k: v for k, v in cnt.items() if v > 1}
    out.append(_mk("AC05", "同视频 7 天 ≤1 条评论", not dup, "P1",
                   ("重复评论：%s" % {k: v for k, v in list(dup.items())[:2]}) if dup
                   else "近 7 天 %d 条已发无重复" % len(cnt), len(cnt)))
    return out


# ---------------------------------------------------------------- sends
def send_checks():
    out = []
    sent = _rows(os.path.join(SOCIAL, "comments-sent.jsonl"))
    oks = [r for r in sent if r.get("ok")]

    # SD01 评论出稿龄期：今天真正发出去一条才算履职（点赞弹幕不能顶替）
    if not oks:
        out.append(_mk("SD01", "评论出稿（24h 至少 1 条）", False, "P1", "从未成功发送过评论"))
    else:
        age = _age_h(oks[-1].get("ts")) or 1e9
        out.append(_mk("SD01", "评论出稿（24h 至少 1 条）", age <= 24, "P1",
                       "最近一条 %.1fh 前（%s）" % (age, str(oks[-1].get("ts"))), len(oks)))

    # SD02 失败归因：每条失败必须带 why，且能归到 rhythm/risk/login/other
    prac = [r for r in _rows(os.path.join(SOCIAL, "practice-log.jsonl"), 3000)
            if (_age_h(r.get("ts")) or 1e9) <= 24 * 7]
    fails = [r for r in prac if r.get("action") == "fail"]
    no_why = [r for r in fails if not (r.get("why") or "").strip()]
    if not fails:
        out.append(_mk("SD02", "失败归因齐全", True, "P1", "近 7 天无失败记录"))
    else:
        out.append(_mk("SD02", "失败归因齐全", not no_why, "P1",
                       "%d 条失败，%d 条无 why" % (len(fails), len(no_why)), len(fails)))

    # SD03 连续真失败：只有风控/登录类连续 2 次才停；"距上帖 8 分钟"是自家节律，不算
    real = [r for r in fails if any(k in str(r.get("why", ""))
                                    for k in ("风控", "risk", "登录", "login", "验证", "captcha"))]
    streak = 0
    for r in reversed(fails):
        hit = any(k in str(r.get("why", "")) for k in ("风控", "risk", "登录", "login", "验证", "captcha"))
        if hit:
            streak += 1
        else:
            break
    out.append(_mk("SD03", "连续真失败 <2", streak < 2, "P1",
                   "近 7 天真失败 %d 条，尾部连续 %d" % (len(real), streak), len(real)))

    # SD04 引流硬拒回归：CEO 令不做引流，词表必须 3/3 拦住
    ct = _import("comment_taste")
    samples = ["互关吗宝子", "想要原曲可以私信我", "这个我分享给你呀"]
    if not ct or not getattr(ct, "DRAIN", None):
        out.append(_mk("SD04", "引流硬拒回归 3/3", None, "P0", "comment_taste 导入失败"))
    else:
        blocked = 0
        for s in samples:
            hits = [w for w in ct.DRAIN if w in s]
            if hits:
                blocked += 1
        out.append(_mk("SD04", "引流硬拒回归 3/3", blocked == 3, "P0",
                       "拦住 %d/3" % blocked, 3))

    # SD05 配额（按号，超配额比不发更危险）
    health = _j(HEALTH, {}) or {}
    bad, detail = [], []
    for a in (health.get("accounts") or []):
        n = ((a.get("today") or {}).get("comment"))
        detail.append("%s=%s" % (a.get("alias"), n))
        if n is not None and int(n) > 20:
            bad.append(a.get("alias"))
    out.append(_mk("SD05", "评论配额（≤20/号/天）", not bad, "P1",
                   "今日 %s" % ", ".join(detail) if detail else "HEALTH 无账号", len(detail)))

    # SD06 副动作（只点赞不说话 = 机器人；活人三件套都要有）
    need = {"watch": 10, "like": 5, "danmaku": 3}
    bad = []
    for a in (health.get("accounts") or []):
        t = a.get("today") or {}
        lack = [k for k, v in need.items() if int(t.get(k) or 0) < v]
        if lack:
            bad.append("%s 缺 %s" % (a.get("alias"), ",".join(lack)))
    out.append(_mk("SD06", "副动作齐（看/赞/弹幕）", not bad, "P1",
                   "；".join(bad) if bad else "两号三类动作齐", len(health.get("accounts") or [])))
    return out


# ---------------------------------------------------------------- schedulers
def _loaded_fluxgroup():
    try:
        p = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    rows = {}
    for line in (p.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and "fluxgroup" in parts[2]:
            pid, rc, label = parts[0].strip(), parts[1].strip(), parts[2].strip()
            rows[label] = {"pid": None if pid in ("-", "") else int(pid),
                           "rc": None if rc in ("-", "") else int(rc)}
    return rows


def scheduler_checks(spec=None):
    out = []
    loaded = _loaded_fluxgroup()
    spec = spec if spec is not None else (_j(os.path.join(SOCIAL, "AGENT-SPEC-v2.json"), {}) or {})
    declared = {}
    for d in (spec.get("duties") or []):
        for s in (d.get("schedulers") or []):
            declared.setdefault(s, []).append(d.get("id"))
    if loaded is None:
        out.append(_mk("SC01", "声明与实载一致", None, "P2", "launchctl 不可用"))
        return out

    unknown = sorted(set(loaded) - set(declared) - set(RETIRED_SCHEDULERS))
    missing = sorted(set(declared) - set(loaded))
    out.append(_mk("SC01", "声明与实载一致", not missing, "P2",
                   "未归类 %d 个%s；应载未载 %d 个%s" % (
                       len(unknown), ("：" + ",".join(x.replace("com.fluxgroup.", "") for x in unknown[:6])) if unknown else "",
                       len(missing), ("：" + ",".join(x.replace("com.fluxgroup.", "") for x in missing[:6])) if missing else ""),
                   len(declared)))

    revived = sorted(set(loaded) & set(RETIRED_SCHEDULERS))
    out.append(_mk("SC02", "退役调度器未复活", not revived, "P1",
                   ("复活：%s → %s" % (",".join(x.replace("com.fluxgroup.", "") for x in revived),
                                       RETIRED_SCHEDULERS[revived[0]][:40])) if revived
                   else "无退役件在跑", len(RETIRED_SCHEDULERS)))

    # rc=1 是本仓约定里的"报告型"（发现问题但不是崩），不算红；真异常才红
    bad = ["%s(rc=%s,pid=%s)" % (k.replace("com.fluxgroup.", ""), v["rc"], v["pid"])
           for k, v in loaded.items()
           if v["pid"] is None and v["rc"] not in (0, 1, None)]
    reported = [k.replace("com.fluxgroup.", "") for k, v in loaded.items()
                if v["pid"] is None and v["rc"] == 1]
    out.append(_mk("SC03", "定时器退出码正常", not bad, "P1",
                   ("真异常：%s" % "；".join(bad[:4])) if bad else
                   ("%d 个 rc 正常%s" % (len(loaded),
                                        ("，报告型：" + ",".join(reported[:4])) if reported else "")),
                   len(loaded)))

    # SC04 节拍与排班表一致：表里写 1800s、plist 却是 300s（或反过来）会把让路逻辑全打乱
    lanes = (_j(os.path.join(SOCIAL, "COMPUTE-SCHEDULE.json"), {}) or {}).get("lanes") or []
    mism, checked = [], 0
    for lane in lanes:
        label, every = str(lane.get("timer") or ""), int(lane.get("every_s") or 0)
        if not label.startswith("com.fluxgroup.") or not every:
            continue
        p = os.path.expanduser("~/Library/LaunchAgents/%s.plist" % label)
        if not os.path.exists(p):
            continue
        try:
            d = plistlib.load(open(p, "rb"))
        except Exception:
            continue
        iv = d.get("StartInterval")
        if iv is None:
            continue
        checked += 1
        if int(iv) != every:
            mism.append("%s plist=%ss 表=%ss" % (label.replace("com.fluxgroup.", ""), iv, every))
    out.append(_mk("SC04", "节拍与排班表一致", not mism, "P1",
                   "；".join(mism[:4]) if mism else "%d 个定时器与 COMPUTE-SCHEDULE 一致" % checked,
                   checked))
    return out


def mem_checks():
    """统一内存（CEO 2026-11-21「不触发 swap 的情况下用好用科学 统一内存 gpu cpu」）。

    判据本体在 mem_probe.py（采样 + 真实生成增量），这里只做转写，避免两套阈值。
    曾经的问题：受管 ollama 写着 MAX_LOADED_MODELS=6 / KEEP_ALIVE=10m，
    32GB 统一内存硬塞六个模型必然换页，而审计里没有任何一条会因此变红。
    """
    mp = _import("mem_probe")
    if not mp:
        return [_mk("ME01", "统一内存体检", None, "P1", "mem_probe 导入失败")]
    out = []
    try:
        doc = mp.probe(with_gen=0)          # 静态：两次采样 + 常驻 + 余量（不跑模型）
        for c in doc.get("checks") or []:
            out.append(_mk(c["id"], c["name"], c["ok"], c.get("sev", "P1"), c["detail"]))
    except Exception as e:
        out.append(_mk("ME01", "统一内存体检", None, "P1", "探针异常：%s" % str(e)[:50]))
    # ME04 是卫生项：app 自启的第二个服务端不影响 127.0.0.1 调用，降到 P2，别当红线叫
    for c in out:
        if c["id"] == "ME04":
            c["sev"] = "P2"
    return out


GROUPS = {
    "corpus": corpus_checks,
    "train": train_checks,
    "accounts": account_checks,
    "sends": send_checks,
    "sched": scheduler_checks,
    "mem": mem_checks,
}


# ---------------------------------------------------------------- 汇总与落盘
def run_group(name):
    checks = GROUPS[name]()
    passed = {c["id"]: c["ok"] for c in checks}
    fails = [c for c in checks if c["ok"] is False]
    skips = [c for c in checks if c["ok"] is None]
    doc = {
        "group": name,
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "pass": passed,
        "overall": not fails,
        "n_checks": len(checks),
        "n_fail": len(fails),
        "n_skip": len(skips),
        "checks": checks,
    }
    os.makedirs(STATE, exist_ok=True)
    path = os.path.join(STATE, "GUARD-%s.json" % name.upper())
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return doc


def merge_all(docs):
    """把五组合并成一份 GUARD-ALL.json：职责断言只许指向一个文件。

    为什么要合并（2026-11-21 自己踩的）：B02 的 SD06 在 GUARD-SENDS、AC01 在
    GUARD-ACCOUNTS，同一个职责的断言跨两个文件时，第二个字段读不到 → 静默变 SKIP，
    看起来"没毛病"。合并面让"读不到字段"在任何职责上都只可能是判据真缺。
    """
    merged = {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
              "pass": {}, "checks": [], "groups": {},
              "overall": all(d["overall"] for d in docs)}
    for d in docs:
        merged["pass"].update(d["pass"])
        for c in d["checks"]:
            merged["checks"].append(dict(c, group=d["group"]))
        merged["groups"][d["group"]] = {"overall": d["overall"],
                                        "n_fail": d["n_fail"], "n_skip": d["n_skip"]}
    path = os.path.join(STATE, "GUARD-ALL.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return merged


def one_screen(docs):
    lines = []
    for d in docs:
        mark = "✅" if d["overall"] else "❗"
        lines.append("%s %-8s %d 项：红 %d / 跳过 %d" % (
            mark, d["group"], d["n_checks"], d["n_fail"], d["n_skip"]))
        for c in d["checks"]:
            if c["ok"] is False:
                lines.append("   ❗ %-4s %-24s %s" % (c["id"], c["name"][:24], c["detail"][:88]))
            elif c["ok"] is None:
                lines.append("   ⏭ %-4s %-24s %s" % (c["id"], c["name"][:24], c["detail"][:88]))
    return "\n".join(lines)


# ---------------------------------------------------------------- 自检（负控）
def self_test():
    """负控：把每个判据的输入改坏，必须从 True 翻成 False/None；不许恒真。"""
    from tempfile import mkdtemp
    d = mkdtemp()
    results = {}

    def _flip(name, fn, good, bad):
        try:
            ok_good = bool(fn(good) is True)
            ok_bad = (fn(bad) is not True)
            results[name] = "PASS" if (ok_good and ok_bad) else "FAIL"
        except Exception as e:
            results[name] = "ERR:%s" % str(e)[:40]

    # 1 pass 映射读取（agent_audit 用的那条路径）
    def read_pass(doc, key="CR01"):
        v = (doc or {}).get("pass") or {}
        return True if v.get(key) is True else (False if v.get(key) is False else None)

    _flip("pass_true", read_pass, {"pass": {"CR01": True}}, {"pass": {"CR01": False}})
    _flip("pass_absent_is_skip", lambda x: read_pass(x) is not True, {"pass": {}}, {"pass": {"CR01": True}})

    # 2 SKIP 不许当通过：None 必须既不等于 True，也要被下游显式识别（负控=真值必须被抓）
    def _skip_not_pass(doc):
        return doc.get("ok") is not True

    _flip("skip_not_pass", _skip_not_pass,
          {"ok": None, "detail": "量不到"},
          {"ok": True, "detail": "假装通过"})

    # 3 jsonl 龄期判据（评论出稿那条的骨架）
    def recent_ok(rows, max_h=24):
        oks = [r for r in rows if r.get("ok")]
        if not oks:
            return False
        age = _age_h(oks[-1].get("ts")) or 1e9
        return age <= max_h

    now = datetime.now()
    _flip("jsonl_recent", recent_ok,
          [{"ok": True, "ts": (now - timedelta(hours=1)).isoformat()}],
          [{"ok": True, "ts": (now - timedelta(hours=79)).isoformat()}])

    # 4 跨号同视频判据
    def cross_ok(rows):
        per = {}
        for r in rows:
            per.setdefault(str(r.get("aid")), set()).add(r.get("account"))
        return not any(len(v) > 1 for v in per.values())

    _flip("cross_video", cross_ok,
          [{"aid": 1, "account": "a"}, {"aid": 2, "account": "b"}],
          [{"aid": 1, "account": "a"}, {"aid": 1, "account": "b"}])

    # 5 夜间静默判据
    def night_ok(rows):
        return not any(datetime.fromisoformat(r["ts"]).hour in NIGHT_HOURS for r in rows)

    _flip("night_quiet", night_ok,
          [{"ts": "2026-11-21T22:10:00"}],
          [{"ts": "2026-11-21T03:10:00"}])

    # 6 epoch 判据（1.1/0.49 必须红，3.5 必须绿）
    def epoch_ok(run):
        return 3 <= float(run["iters"]) / float(run["train_rows"]) <= 5

    _flip("epoch_band", epoch_ok,
          {"iters": 3500, "train_rows": 1000},
          {"iters": 500, "train_rows": 1016})

    # 7 语料污染判据（AI 腔率 >5% 必须红）
    tb = _import("train_build")
    if tb:
        rows = ["这个真是绝了", "当年惊艳台湾的歌曲"]
        rate = sum(1 for t in rows if tb.ai_smell(t)) / len(rows)
        results["corpus_smell"] = "PASS" if rate > 0.05 else "FAIL"
    else:
        results["corpus_smell"] = "SKIP"

    # 8 两次自检本身不许静默通过
    flags = [v for v in results.values()]
    ok = all(v == "PASS" for v in flags) and "FAIL" not in flags
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "cases": results},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--group", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    names = list(GROUPS) if a.all else ([a.group] if a.group else [])
    if not names or any(n not in GROUPS for n in names):
        ap.error("用法：--all 或 --group %s" % "|".join(GROUPS))
    docs = [run_group(n) for n in names]
    if len(docs) == len(GROUPS):
        merge_all(docs)
    if a.json:
        print(json.dumps(docs, ensure_ascii=False, indent=1))
    else:
        print(one_screen(docs))
    return 0 if all(d["overall"] for d in docs) else 1


if __name__ == "__main__":
    sys.exit(main())
