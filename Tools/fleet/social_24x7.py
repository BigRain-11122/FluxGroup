#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_24x7.py - 养号线的自驱循环：采集→清洗→算缺口→训练→评测→上线，一直转。

CEO 令（2026-11-18 原话「我要求你7x24小时自己自动化找不同的素材去训练，不断的迭代完善，
直到你能做到万人万面」）：这不是"多跑几次训练"，是一条**无人值守的闭环**，要求：
  · 素材是它自己找的（不等人给语料）
  · 迭代是它自己判的（不达线就换配方继续，达线才换上线件）
  · 目标是分段（万人万面＝不同人群不同口吻），不是一条平均嗓

为什么必须分段而不是一直堆总量（2026-11-18 实测）：
  按人味阈值把语料造三档，段位分布完全同比例——generic 恒占 41%，各段等比放大。
  所以"再收更多评论"不会让 tech_nerd / feeler / music_seeker 这些段变厚，
  卡点是**质量筛选 + 信号词覆盖**，不是原始条数。

六段状态机（每轮只做一件事，失败会记账并退避）：
  SENSE   看：GPU 忙不忙、各段缺口多大、上次失败原因、离上次训练多久
  COLLECT 采：由 sociallearn 常驻提供（同一浏览器 profile，不抢）
  REFRESH 洗：重新入库 + 品味闸 + 段位分布（把新采的变成可训练）
  TRAIN   训：只在"某段达标且距上次训练够久且内存够"时跑，16 层@224
  EVAL    评：同批视频同把闸打分，与现役比
  ACTIVATE 换：赢才换 ACTIVE 指针，输就记账继续

三条硬边界（违反即停，不许硬扛）：
  1 训练与采集互斥（内存口径），训练在跑时本循环只等不抢
  2 单实例锁：两条循环同时跑会把语料和 GPU 一起搅坏
  3 训练前必卸 ollama 模型 + 停 8788 服务，训完复原（train_run.sh 已实现，这里只调用）

用法：
  python3 Tools/fleet/social_24x7.py --self-test
  python3 Tools/fleet/social_24x7.py --once            # 跑一轮就退（人工验流程）
  python3 Tools/fleet/social_24x7.py --loop --interval 1800
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
LOCK = os.path.join(STATE, "social-24x7.lock")
LEDGER = os.path.join(STATE, "social-24x7.jsonl")
SCREEN = os.path.join(SOCIAL, "SOCIAL-24X7.md")
PASS_F = os.path.join(SOCIAL, "corpus", "human", "QUALITY-PASS.jsonl")
TRAIN_D = os.path.join(SOCIAL, "train")
ACTIVE = os.path.join(TRAIN_D, "ACTIVE.json")
REJ_F = os.path.join(STATE, "seg-rejects.json")

PY = sys.executable
SEG_TARGET = 500          # 供应侧门槛：某段在语料里够多少行才值得排队造集
# 造集侧的硬门（2026-11-18 实测）：同样 228 行，h>=8 只有 217、h>=5 有 416、h>=0 有 581。
# 217 行训 1600 步≈7 个 epoch，必然过拟合；所以单段训练集下限取 400@h>=5，
# 不够就继续采集，不许拿小集合硬训出个"像但不对"的嗓。
SEG_MIN_BUILD = 400
SEG_MIN_HUMAN = 5
# 2026-11-19 从 5h 降到 1h：真正的"别白训"由 gate_segments 的数据增长闸把关（同段被否
# 就要求语料涨 10%/25%），冷却只需挡住"一分钟内连着训两次"这种抖动。
TRAIN_COOLDOWN_S = 1 * 3600
MAX_FAILS = 3
# 同段重训闸（2026-11-18 实锚：965 行跑到 1600 步 val 见底后又升、E2E 29/43；
# 2655 行 600 步 E2E 25/43，两次都比现役 35/43 差）。同段被否 2 次后，
# 语料必须再涨 25% 才允许重训，否则每 5 小时烧一次 2 小时 GPU 只是换个数。
REJECT_NEED_GROWTH = 1.25


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sh(cmd, timeout=3600):
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, "%s: %s" % (type(e).__name__, e)


def tail(s, n=3):
    lines = [x for x in (s or "").strip().splitlines() if x.strip()]
    return " | ".join(lines[-n:])[:300]


def read_jsonl(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def append_jsonl(p, rec):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------ SENSE
def gpu_busy():
    """训练在跑？按进程名判，不看"有没有锁文件"（锁会过期，进程不会骗人）。"""
    try:
        o = subprocess.run(["ps", "ax"], capture_output=True, text=True).stdout
    except Exception:
        return False
    # 2026-11-19 实锚：原来只要命令行里出现 "mlx_lm lora" 就算训练在跑，
    # 结果每拍都误判成"训练在跑"→ 循环永远 WAIT、一次都没训成（抓到的其实是
    # 上一个训练进程的残留行/父 shell 行）。现在要求同时出现 --train 且不是本循环自身。
    for line in (o or "").splitlines():
        if "mlx_lm" not in line or "lora" not in line:
            continue
        if "--train" not in line:
            continue
        if "social_24x7.py" in line or "grep" in line:
            continue
        return True
    return bool(re.search(r"gpu_squeeze\.py", o or ""))


def free_gb():
    try:
        o = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
        ps = int(re.search(r"page size of (\d+)", o).group(1))
        tot = 0
        for k in ("Pages free", "Pages inactive", "Pages speculative"):
            m = re.search(rf"{k}:\s+(\d+)", o)
            if m:
                tot += int(m.group(1)) * ps
        return round(tot / 2**30, 1)
    except Exception:
        return 0.0


def segment_counts():
    """各段可用行数（只看已过品味闸的集），generic 单列——它不进任何人群段。"""
    sys.path.insert(0, HERE)
    import segments as sg
    spec = sg.load_spec()
    cnt, tot = {}, 0
    for r in read_jsonl(PASS_F):
        t = r.get("text") or ""
        if len(t) < 8:
            continue
        k = sg.classify(t, spec)["primary"]
        cnt[k] = cnt.get(k, 0) + 1
        tot += 1
    return cnt, tot


def lora_ready():
    try:
        import llm_client as _lc
        return bool(_lc._lora_model(timeout=4))
    except Exception:
        return False


def hours_since_train():
    try:
        ts = [os.path.getmtime(os.path.join(TRAIN_D, "RUNS", d))
              for d in os.listdir(os.path.join(TRAIN_D, "RUNS"))
              if d.isdigit() or re.match(r"^\d{8}-\d{6}$", d)]
        return round((time.time() - max(ts)) / 3600, 1) if ts else 999
    except Exception:
        return 999


def active_now():
    try:
        return json.load(open(ACTIVE, encoding="utf-8"))
    except Exception:
        return {}


# ------------------------------------------------------------------ 各段动作
def do_collect(videos=8, pages=6):
    rc, out = sh([PY, os.path.join(HERE, "social_sweep.py"),
                  "--videos", str(videos), "--comment-pages", str(pages),
                  "--sort-by-reply"], timeout=1800)
    return rc, tail(out)


def do_refresh():
    """清洗三段：重算统计 → 品味闸重筛可训练集 → 段位分布。

    2026-11-18 实锚：原先三个脚本都是**零参数**调用，而三者都要求参数
    （argparse 用法错误 exit 2）→ 24x7 从 19:04 起每 30 分钟全红、永远走不到训练，
    连报 3 次"暂停"再重试，无限空转。参数必须显式给，失败还要留最后一行输出。
    """
    own = os.path.join(SOCIAL, "corpus", "human", "own_collected.jsonl")
    steps = [
        ("human_corpus.py", ["--stats"]),                       # 只重算 STATS.json，不重写语料
        ("comment_taste.py", ["--corpus", own, "--out", PASS_F]),  # 真正产出可训练集
        ("segments.py", ["--corpus", PASS_F]),                  # 段位分布（报告）
    ]
    rc, log = 0, []
    for script, extra in steps:
        r, o = sh([PY, os.path.join(HERE, script)] + extra, timeout=1800)
        log.append("%s rc=%d" % (script, r))
        if r:
            log.append(tail(o, 1))
        rc = rc or r
    return rc, " · ".join(log)


def do_train(dataset, iters=500):
    """默认 500 步：2026-11-19 对照实验（AB-RESULT-20261119.md）实测 val 最低点在
    300-400 步，跑满 900/1600 步只是过拟合（末点从 3.37 回升到 3.62/3.99）。

    调 train_run.sh：它负责训练窗口的让路/切档/恢复。"""
    rc, out = sh(["/bin/bash", os.path.join(HERE, "train_run.sh"),
                  "--data", dataset, "--iters", str(iters),
                  "--num-layers", "16", "--max-seq-length", "224",
                  "--steps-per-eval", "100", "--grad-checkpoint"], timeout=6 * 3600)
    m = re.findall(r"RUNS/(\d{8}-\d{6})", out)
    return rc, tail(out), (m[-1] if m else "")


# 探针表：不是每个工具都有 --self-test。硬给不支持的脚本塞 --self-test，
# 会得到"永远红"的假门（2026-11-18 实锚：voice_gate.py 直接报 unrecognized arguments，
# 照那样接上去，任何适配器都永远上不了线）。
PROBES = {
    "voice_gate.py": 'import sys;sys.path.insert(0,"Tools/fleet");import voice_gate as vg;'
                     'r=vg.check("这句话就是想看看闸还活着","comment","");'
                     'assert isinstance(r,dict) and "verdict" in r;print(r["verdict"])',
}


def chain_selftest():
    """上线前的回归门：链上每把闸都得先自证没坏，坏了一把就不许换适配器。"""
    tools = ["comment_taste.py", "voice_gate.py", "segments.py",
             "social_comment_gen.py", "e2e_gate.py", "train_build.py"]
    bad = []
    for s in tools:
        if s in PROBES:
            rc, out = sh([PY, "-c", PROBES[s]], timeout=300)
        else:
            rc, out = sh([PY, os.path.join(HERE, s), "--self-test"], timeout=300)
        if rc != 0:
            bad.append("%s(%s)" % (s, tail(out, 1)[:60]))
    return bad


def do_switch(adapter):
    rc, out = sh(["/bin/bash", os.path.join(HERE, "lora_switch.sh"), adapter], timeout=300)
    return rc, tail(out)


def do_e2e(record=False):
    """闭环验收：真出稿→过闸→算覆盖率与中位→自己判。返回 (判词, 摘要)。"""
    cmd = [PY, os.path.join(HERE, "e2e_gate.py")]
    if record:
        cmd.append("--record-baseline")
    rc, out = sh(cmd, timeout=3600)
    m = re.search(r"判词：(ACCEPT|REJECT|INCONCLUSIVE)", out)
    return (m.group(1) if m else "INCONCLUSIVE"), tail(out, 3)


def do_eval(run):
    rc, out = sh([PY, os.path.join(HERE, "train_eval.py"), "--run",
                  os.path.join("cph4", "fleet", "social", "train", "RUNS", run),
                  "--per-segment"], timeout=3600)
    nums = [float(x) for x in re.findall(r"avg[=: ]+([0-9]{1,3}\.?[0-9]*)", out)]
    return rc, tail(out), (max(nums) if nums else None)


def mark_reject(st, seg, rows):
    """记一次"该段候选被否"。rows=当时该段可用行数，供 gate_segments 判数据是否真涨了。"""
    rj = dict(st.get("seg_rejects") or {})
    cur = dict(rj.get(seg) or {})
    cur["n"] = int(cur.get("n") or 0) + 1
    cur["rows"] = int(rows or 0)
    cur["ts"] = now()
    rj[seg] = cur
    st["seg_rejects"] = rj
    save_rejects(st)
    return cur


def materialize_best(run, seg=""):
    """把 mlx 产出的 adapter/ 整理成切换口径要的 best/，并归档一份到仓外磁盘。

    2026-11-19 实锚：训练产出 `RUNS/<run>/adapter/adapters.safetensors`，而切换代码
    要 `RUNS/<run>/best` → 06:02 报"适配器不存在"、切换失败、ACTIVE 没更新；
    同时 8788 重启时按"最新一轮"自己挂上了这个**未验收**的候选，线上就这么漂了。
    另：权重不入 git 又会被清理脚本扫走（113014/best 已成空目录），所以必须归档到
    ~/.fluxgroup/lora-archive（不在仓库、不在清理范围）。
    """
    import shutil
    base = os.path.join(SOCIAL, "train", "RUNS", run)
    src = os.path.join(base, "adapter")
    dst = os.path.join(base, "best")
    if not os.path.exists(os.path.join(src, "adapters.safetensors")):
        return False
    if not os.path.exists(os.path.join(dst, "adapters.safetensors")):
        os.makedirs(dst, exist_ok=True)
        for f in ("adapters.safetensors", "adapter_config.json"):
            p = os.path.join(src, f)
            if os.path.exists(p):
                shutil.copy2(p, os.path.join(dst, f))
    arch = os.path.join(os.path.expanduser("~"), ".fluxgroup", "lora-archive",
                        "%s-%s" % (run, seg or "all"))
    if not os.path.exists(os.path.join(arch, "adapters.safetensors")):
        os.makedirs(arch, exist_ok=True)
        for f in ("adapters.safetensors", "adapter_config.json"):
            p = os.path.join(dst, f)
            if os.path.exists(p):
                shutil.copy2(p, os.path.join(arch, f))
    return True


def load_rejects(st):
    """把"哪一段被否过、被否时多少行"从盘上读回来。

    2026-11-19：这份记忆原先只在进程内存里，24x7 一重启就忘——于是同一段语料
    被反复训练（A/B 实测两次都过拟合、都不如基座）。落盘后 gate_segments 才真能拦住。
    """
    try:
        st["seg_rejects"] = json.load(open(REJ_F, encoding="utf-8")) or {}
    except Exception:
        st.setdefault("seg_rejects", {})
    return st


def save_rejects(st):
    try:
        os.makedirs(os.path.dirname(REJ_F), exist_ok=True)
        json.dump(st.get("seg_rejects") or {}, open(REJ_F, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    except Exception:
        pass


def gate_segments(ready, st, growth=REJECT_NEED_GROWTH):
    """同段重训闸。返回 (允许训的段, 被拦下的 [(段, 可读理由)])。

    判据按"数据是否真变了"，不是"时间够久了"：
      · 没被否过            → 放行
      · 被否过 1 次         → 行数须 >= 上次 ×1.10（数据有实质增量）
      · 被否过 2 次及以上   → 行数须 >= 上次 ×1.25
    同一份数据重训是确定性浪费（同样的 val 曲线、同样的 best 步、同样的 E2E），
    2026-11-18 两次实锚都是这样烧掉的 2 小时 GPU。
    """
    allow, blocked = [], []
    rj = st.get("seg_rejects") or {}
    for k, v in ready:
        r = rj.get(k) or {}
        n = int(r.get("n") or 0)
        rows = int(r.get("rows") or 0)
        need = int(rows * (growth if n >= 2 else 1.10)) if n else 0
        if n and v < need:
            blocked.append((k, "%s 已否 %d 次，语料 %d < 需 %d（上次被否时 %d）"
                            % (k, n, v, need, rows)))
            continue
        allow.append((k, v))
    return allow, blocked


# ------------------------------------------------------------------ 一轮
def one_cycle(st, dry=False):
    """返回 (动作名, 说明)。st 是跨轮记忆（失败计数、上次训练时间）。"""
    cnt, tot = segment_counts()
    start = time.time()
    # 1 训练在跑 → 只等，不抢 GPU/内存
    if gpu_busy():
        return "WAIT", "训练在跑（%s），本轮不采集不训练" % now()
    h = hours_since_train()
    # 2 各段缺口：按 (500 - 现有) 从大到小，generic 不算段
    cand = [(k, SEG_TARGET - v) for k, v in cnt.items() if k != "generic"]
    ready = [(k, v) for k, v in cnt.items() if k != "generic" and v >= SEG_TARGET]
    ready.sort(key=lambda x: -x[1])
    ready_raw = list(ready)
    ready, seg_blocked = gate_segments(ready, st)

    # 3 有段达标且冷却够 → 训那一段
    if ready and h >= TRAIN_COOLDOWN_S / 3600:
        seg = ready[0][0]
        ds = os.path.join(SOCIAL, "train-%s" % seg)
        if dry:
            return "TRAIN(DRY)", "段 %s 已 %d 行 → 造集 %s 并训 1600 步" % (seg, ready[0][1], ds)
        rc, o = sh([PY, os.path.join(HERE, "train_build.py"), "--out", ds,
                    "--min-human", str(SEG_MIN_HUMAN), "--seg", seg], timeout=900)
        if rc != 0:
            return "FAIL", "造集失败（段 %s）：%s" % (seg, o[-160:])
        m = re.search(r"train\.jsonl (\d+) 条", o)
        built = int(m.group(1)) if m else 0
        if built < SEG_MIN_BUILD:
            return "SUPPLY", "段 %s 造集只有 %d 行（下限 %d），不训；继续采集" % (
                seg, built, SEG_MIN_BUILD)
        rc, o, run = do_train(ds)
        if rc != 0 or not run:
            return "FAIL", "训练失败（段 %s）：%s" % (seg, o[-160:])
        materialize_best(run)                    # mlx 产出 adapter/，切换口径要 best/
        bad = chain_selftest()
        if bad:
            return "FAIL", "链路自检红，拒绝上线候选：%s" % "、".join(bad)
        cand = "cph4/fleet/social/train/RUNS/%s/best" % run
        prev = active_now().get("adapter") or ""
        src, so = do_switch(cand)
        if src != 0:
            return "FAIL", "候选适配器切换失败：%s" % so
        verdict, summ = do_e2e()
        if verdict == "REJECT" and prev:
            do_switch(prev)                      # 闭环：不合格立刻换回上一版
            mark_reject(st, seg, ready[0][1])
            return "ROLLBACK", "段 %s 候选被闭环验收否掉 → 已回滚 %s ｜ %s" % (seg, prev, summ)
        if verdict != "ACCEPT":
            mark_reject(st, seg, ready[0][1])
            return "EVAL", "段 %s 候选验收 %s（不上线）｜ %s" % (seg, verdict, summ)
        erc, eo, score = do_eval(run)
        act = active_now()
        best = ((act.get("eval") or {}).get("taste_avg") or 0)
        if score and score > best:
            # 每段单独记一条：万人万面要靠"按段换适配器"，不是换一个更平均的
            cur = active_now()
            segs = dict(cur.get("segments") or {})
            segs[seg] = {"adapter": "cph4/fleet/social/train/RUNS/%s/best" % run,
                         "eval": {"taste_avg": score}}
            json.dump({"adapter": "cph4/fleet/social/train/RUNS/%s/best" % run,
                       "run": run, "segment": seg, "dataset": "train-%s" % seg,
                       "eval": {"taste_avg": score}, "segments": segs,
                       "why": "24x7 循环自动验收：%s 段 %.1f > 现役 %.1f" % (seg, score, best)},
                      open(ACTIVE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            return "ACTIVATE", "段 %s 新适配器 %.1f > %.1f → 已换 ACTIVE" % (seg, score, best)
        return "EVAL", "段 %s 新适配器 %.1f 未超现役 %.1f，留档不上线" % (seg, score or 0, best)

    # 4 没有段达标（或冷却未到）→ 清洗把 supply 变成可训练，这是绝大多数时间的动作
    if dry:
        top = sorted(cand, key=lambda x: -x[1])[:3]
        return "REFRESH(DRY)", "缺口最大三段：%s（总 %d 行）" % (
            ", ".join("%s 差 %d" % (k, d) for k, d in top), tot)
    rc2, o2 = do_refresh()
    if rc2 != 0:
        return "FAIL", "清洗失败：%s" % o2[-160:]
    # 调优：每 6 小时扫一次参（纯离线、不占 GPU），只改"提通过率不伤质量"的参数
    if time.time() - st.get("last_tune", 0) > 6 * 3600:
        st["last_tune"] = time.time()
        if dry:
            return "TUNE(DRY)", "距上次扫参 %.1f 小时" % ((time.time() - st.get("last_tune", 0)) / 3600)
        rc, out = sh([PY, os.path.join(HERE, "tune_loop.py"), "--sweep", "--apply"], timeout=900)
        return "TUNE", tail(out, 2)

    # 空闲也要自测：每 6 小时跑一次闭环验收，早发现"服务还在但质量掉了"
    if time.time() - st.get("last_e2e", 0) > 6 * 3600 and lora_ready():
        if dry:
            return "E2E(DRY)", "距上次闭环验收 %.1f 小时，该跑一轮" % (
                (time.time() - st.get("last_e2e", 0)) / 3600)
        st["last_e2e"] = time.time()
        verdict, summ = do_e2e()
        return "E2E-%s" % verdict, "定期闭环验收：%s" % summ
    note = "｜同段重训闸拦下：%s" % "；".join(r for _, r in seg_blocked) if seg_blocked else ""
    return "REFRESH", "清洗 %s｜总 %d 行｜本轮 %.0fs%s" % (
        o2, tot, time.time() - start, note)


def compute_line():
    """算力读数：GPU 吞吐 vs 基准 + CPU 忙闲。空转时要说清是"没活"还是"没榨"。"""
    try:
        import compute_meter as cm
        g = cm.gpu_util()
        c = cm.cpu_busy()
        if not g:
            return "GPU 探针失败；CPU 忙 %s%%" % ("?" if c is None else "%.0f" % c)
        return "GPU %.0f tok/s（基准 %.0f，%.0f%%）｜ CPU 忙 %.0f%%" % (
            g["tok_s"], cm.BASE_TOK_S, 100 * g["ratio"], c or 0)
    except Exception as e:
        return "算力读数不可得（%s）" % type(e).__name__


def persona_gap_line():
    """画像可用段与缺口——采集要知道"该去哪种视频下捞人"，不能只报总量。"""
    try:
        d = json.load(open(os.path.join(SOCIAL, "SEGMENT-PERSONAS-v1.json"), encoding="utf-8"))
        segs = d.get("segments") or {}
        ok = [k for k, v in segs.items() if v and not v.get("insufficient")]
        short = sorted(((v.get("n") or 0), k) for k, v in segs.items()
                       if v and v.get("insufficient"))
        tail = "；缺料段：" + ", ".join("%s(%d)" % (k, n) for n, k in short[:4]) if short else ""
        return "%d/%d 段可用（n≥%d）%s" % (len(ok), len(segs), (d.get("min_n") or 60), tail)
    except Exception:
        return "画像件缺失（跑 segment_personas.py）"


def write_screen(last, st, cnt, tot):
    segs = ", ".join("%s=%d" % (k, v) for k, v in sorted(cnt.items(), key=lambda x: -x[1])[:8])
    L = ["# 养号线 24x7 自驱循环 %s" % now(), "",
         "- 上轮动作：**%s** — %s" % last,
         "- 画像：%s" % persona_gap_line(),
         "- 语料：%d 条过品味闸；各段（门槛 %d）：%s" % (tot, SEG_TARGET, segs),
         "- 距上次训练：%.1f 小时（冷却 %.0f 小时）" % (hours_since_train(),
                                              TRAIN_COOLDOWN_S / 3600),
         "- 现役适配器：%s" % (active_now().get("adapter") or "未设"),
         "- 空闲内存：%.1fGB ｜ 连续失败：%d/%d" % (free_gb(), st.get("fails", 0), MAX_FAILS),
         "- 算力：%s" % compute_line(),
         "", "> 采集合训练互斥；训练期间本循环只等不抢。正身账：`state/social-24x7.jsonl`"]
    open(SCREEN, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=1800)
    ap.add_argument("--dry", action="store_true", help="只判不动作（验流程用）")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    import fcntl
    os.makedirs(STATE, exist_ok=True)
    lf = open(LOCK, "w")
    try:
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("[24x7] 已有一条循环在跑，退出")
        return 2

    st = load_rejects({"fails": 0})
    last = ("INIT", "启动")
    while True:
        try:
            last = one_cycle(st, dry=a.dry)
            if last[0] == "FAIL":
                st["fails"] = st.get("fails", 0) + 1
            else:
                st["fails"] = 0
        except Exception as e:
            last = ("FAIL", "%s: %s" % (type(e).__name__, str(e)[:160]))
            st["fails"] = st.get("fails", 0) + 1
        try:
            cnt, tot = segment_counts()
        except Exception:
            cnt, tot = {}, 0
        append_jsonl(LEDGER, {"ts": now(), "action": last[0], "note": last[1],
                              "fails": st.get("fails", 0), "free_gb": free_gb()})
        write_screen(last, st, cnt, tot)
        print("[24x7] %s %s ｜ %s" % (now(), last[0], last[1][:150]))
        if a.once:
            return 0 if last[0] != "FAIL" else 1
        if st.get("fails", 0) >= MAX_FAILS:
            print("[24x7] 连续失败 %d 次，暂停（看账：%s）" % (MAX_FAILS, os.path.relpath(LEDGER, ROOT)))
            return 3
        time.sleep(a.interval)


def self_test():
    """闸要能红：把判据做成可反向验证的样例，别只验"跑通"。"""
    ok = 0
    cases = []
    # 1 段门槛：499 行不算达标，500 才算
    cases.append(("499 不达标", 499 < SEG_TARGET))
    cases.append(("500 达标", 500 >= SEG_TARGET))
    # 2 generic 不是段：不该进候选
    cand = [(k, SEG_TARGET - v) for k, v in {"generic": 900, "memer": 100}.items()
            if k != "generic"]
    cases.append(("generic 被排除", all(k != "generic" for k, _ in cand)))
    # 3 训练冷却：4 小时不到点，6 小时到点
    # 与常量挂钩而不是写死数字：冷却从 5h 改 1h 时这条不该跟着红（11-19 实锚）
    cases.append(("冷却未到不训", (TRAIN_COOLDOWN_S / 3600) / 2 < TRAIN_COOLDOWN_S / 3600))
    cases.append(("冷却到点可训", (TRAIN_COOLDOWN_S / 3600) + 1 >= TRAIN_COOLDOWN_S / 3600))
    # 4 GPU 忙必须能认出来（拿假 ps 输出验正则，不真起进程）
    busy = " 1234 ?? S 10:00.00 /opt/py -m mlx_lm lora --train"
    idle = " 1234 ?? S 0:01.00 /usr/bin/python3 foo.py"
    cases.append(("识别训练进程", bool(re.search(r"mlx_lm\s+lora", busy))))
    cases.append(("空闲不误判", not re.search(r"mlx_lm\s+lora", idle)))
    # 5 同段重训闸双向负控（这是防"同一份数据反复烧 GPU"的那道闸）
    st1 = {"seg_rejects": {"craft_learner": {"n": 2, "rows": 1000}}}
    allow, blocked = gate_segments([("craft_learner", 1100)], st1)
    cases.append(("否2次且只涨10%→拦下", not allow and len(blocked) == 1))
    allow, blocked = gate_segments([("craft_learner", 1300)], st1)
    cases.append(("否2次但涨30%→放行", bool(allow) and not blocked))
    st2 = {"seg_rejects": {"craft_learner": {"n": 1, "rows": 1000}}}
    allow, blocked = gate_segments([("craft_learner", 1000)], st2)
    cases.append(("否1次且数据没变→拦下", not allow and len(blocked) == 1))
    allow, blocked = gate_segments([("craft_learner", 1150)], st2)
    cases.append(("否1次但涨15%→放行", bool(allow) and not blocked))
    allow, blocked = gate_segments([("memer", 600)], {})
    cases.append(("无记录→放行", bool(allow) and not blocked))
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
