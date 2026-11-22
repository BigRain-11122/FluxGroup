#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quality_agent.py — 养号线的常驻质量智能体（自己判断下一步干什么）。

CEO 2026-11-22「你既然每次都知道下一步要干什么，就派个智能体持续干下去」。
所以这里不是一个"跑一堆检查"的脚本，而是一个**决策循环**：
  SENSE  → 读质量饼图、档位、池子、样本量、闸通过率
  DECIDE → 按优先级挑一件最该做的事（规则写死，可复算，不靠我现场拍）
  ACT    → 只做"确定性、可逆、不对外"的动作（扩池/补样本/参数在括号内微调）
  RECORD → 每步落账 before/after，写进 state/QUALITY-AGENT.jsonl
  REPORT → 生成一屏 cph4/fleet/social/QUALITY-BOARD.md

边界（写在这里，也是硬约束）：
- 不发帖、不改判据阈值、不改代码：发帖归 practice_tick，改阈值与改代码归主控/CEO。
- 动作必须在"括号内"：扩池有上限、补采有限速、样本量有目标值。
- 任何一步做不了就写清楚原因，不假装做过（宁可空转一轮也不造假活）。

用法：
  python3 Tools/fleet/quality_agent.py --once        # 跑一轮（launchd 用这个）
  python3 Tools/fleet/quality_agent.py --once --dry  # 只看它打算做什么
  python3 Tools/fleet/quality_agent.py --board       # 只重写一屏
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
AGENT_LOG = os.path.join(STATE, "QUALITY-AGENT.jsonl")
AGENT_STATE = os.path.join(STATE, "QUALITY-AGENT.json")
BOARD = os.path.join(SOCIAL, "QUALITY-BOARD.md")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
HOT = os.path.join(SOCIAL, "corpus", "hot", "HOT-COMMENTS.jsonl")

# 括号（动作边界）：改这些数要有依据，不许为"看起来在干活"而放宽
POOL_TARGET = 2000          # 内容池目标条数
HOT_TARGET = 300            # 高赞样本目标条数
MINE_COOLDOWN_MIN = 45      # 两次补采的最小间隔（接口会 412）
EXPAND_ADD = 400            # 单次扩池最多加多少条
DUP_LINE = 0.10             # 撞模板率上限
LEN_LINE = 0.80             # 长度带命中率下限
CONC_LINE = 0.60            # 具体性下限
SHARE_LINE = 0.50           # 单一原型最大占比
MIN_N = 8                   # 质量样本最少条数


def _now():
    return datetime.now()


def _load(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d if d is not None else {}


def _log(rec):
    rec.setdefault("ts", _now().isoformat(timespec="seconds"))
    try:
        with open(AGENT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _run(args, timeout=900):
    """跑一个子工具，返回 (rc, 末行输出)。子工具自己会落账，这里只收结论。"""
    try:
        r = subprocess.run([sys.executable, "-u"] + args, cwd=ROOT,
                           capture_output=True, text=True, timeout=timeout)
        tail = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        return r.returncode, (tail[-1][:160] if tail else "")
    except subprocess.TimeoutExpired:
        return 124, "超时"
    except Exception as e:
        return 1, "%s: %s" % (type(e).__name__, str(e)[:100])


# ---------------- SENSE ----------------
def sense():
    s = {"ts": _now().isoformat(timespec="seconds")}
    # 质量
    try:
        import reply_quality as rq
        q = rq.evaluate(n=30, since="2026-11-22T18:05") or {}
    except Exception as e:
        q = {"error": str(e)[:80]}
    s["quality"] = {k: q.get(k) for k in ("n", "median", "concrete_rate", "dup_rate",
                                          "len_ok_rate", "ai_smell_rate", "max_share",
                                          "unique_arch", "ok")}
    s["quality"]["archetypes"] = q.get("archetypes")
    s["quality"]["interaction"] = q.get("interaction")
    # 档位与配额
    pol = _load(os.path.join(SOCIAL, "FREQ-POLICY.json"), {})
    s["policy"] = {k: pol.get(k) for k in ("level", "max_per_day", "min_gap_min")}
    s["ramp"] = _load(os.path.join(STATE, "RAMP.json"), {})
    # 池子与样本
    try:
        s["pool"] = len([1 for v in (_load(TITLES, {}) or {}).values() if (v or {}).get("title")])
    except Exception:
        s["pool"] = 0
    try:
        s["hot"] = sum(1 for line in open(HOT, encoding="utf-8") if line.strip())
    except Exception:
        s["hot"] = 0
    try:
        import freq_policy as fp
        s["supply_cap"] = fp.supply_cap()
    except Exception:
        s["supply_cap"] = None
    # 上次补采时间（限流保护）
    st = _load(AGENT_STATE, {})
    s["last_mine"] = st.get("last_mine")
    return s


# ---------------- DECIDE ----------------
def decide(s):
    """按优先级返回 (动作, 理由)。规则顺序＝这边出问题最伤质量的顺序。"""
    q = s.get("quality") or {}
    n = int(q.get("n") or 0)
    dup = float(q.get("dup_rate") or 0)
    lenok = float(q.get("len_ok_rate") or 0)
    conc = float(q.get("concrete_rate") or 0)
    share = float(q.get("max_share") or 0)
    ai = float(q.get("ai_smell_rate") or 0)

    if q.get("error"):
        return "diag", "质量评估出错：%s" % q["error"]
    if n >= MIN_N:
        if ai > 0:
            return "diag", "AI 腔仍有 %.0f%% 漏过闸（该修闸，不归我改）" % (100 * ai)
        if dup > DUP_LINE:
            return "diag", "撞模板 %.0f%% > %.0f%%（要列出重复开头，交主控改选片/提示词）" % (
                100 * dup, 100 * DUP_LINE)
        if lenok < LEN_LINE:
            return "diag", "长度带命中 %.0f%% < %.0f%%（字数带可能又被打架）" % (100 * lenok, 100 * LEN_LINE)
        if conc < CONC_LINE:
            return "diag", "具体性 %.0f%% < %.0f%%（稿子在说空话）" % (100 * conc, 100 * CONC_LINE)
        if share > SHARE_LINE:
            return "rebalance", "单一原型 %.0f%% > %.0f%%（一天一个腔）" % (100 * share, 100 * SHARE_LINE)

    if s.get("pool", 0) < POOL_TARGET:
        return "expand", "内容池 %d < 目标 %d（池子是频率与多样性的共同上限）" % (
            s.get("pool", 0), POOL_TARGET)

    # 补采高赞样本：限流保护 + 目标量
    last = s.get("last_mine")
    ok_gap = True
    if last:
        try:
            ok_gap = (_now() - datetime.fromisoformat(last)) > timedelta(minutes=MINE_COOLDOWN_MIN)
        except Exception:
            ok_gap = True
    if s.get("hot", 0) < HOT_TARGET and ok_gap:
        return "mine", "高赞样本 %d < 目标 %d，且距上次 %.0f 分钟已过冷却" % (
            s.get("hot", 0), HOT_TARGET, MINE_COOLDOWN_MIN)

    if n < MIN_N:
        return "wait", "新话术下的质量样本只有 %d 条（需 ≥%d），先让出稿跑起来" % (n, MIN_N)
    return "idle", "各项达线（质量中位 %.0f、具体 %.0f%%、撞模板 %.0f%%）" % (
        float(q.get("median") or 0), 100 * conc, 100 * dup)


# ---------------- ACT ----------------
def act(action, why, dry=False):
    out = {"action": action, "why": why, "did": "", "rc": None}
    if action == "diag":
        # 只做诊断取证：把最低分那条与重复开头列出来，交主控改（不改代码/阈值）
        try:
            import reply_quality as rq
            agg = rq.evaluate(n=30, since="2026-11-22T18:05") or {}
            items = sorted((agg.get("items") or []), key=lambda i: i.get("score") or 0)[:3]
            out["did"] = "列出最低分 %d 条" % len(items)
            out["worst"] = [{"text": i.get("text"), "score": i.get("score")} for i in items]
        except Exception as e:
            out["did"] = "诊断失败：%s" % str(e)[:80]
        return out
    if action == "rebalance":
        # 把今天用得最多的原型计数抬高，下一轮自然轮到别的（只动计数，不动内容）
        try:
            p = os.path.join(STATE, "VOICE-USAGE.json")
            d = _load(p, {}) or {}
            day = _now().strftime("%Y-%m-%d")
            cur = d.get(day) or {}
            if cur:
                top = max(cur.items(), key=lambda kv: kv[1])[0]
                cur[top] = int(cur[top]) + 3
                d[day] = cur
                json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                out["did"] = "把最扎堆原型 %s 计数 +3，下一批会轮换" % top
            else:
                out["did"] = "今天还没有原型计数，跳过"
        except Exception as e:
            out["did"] = "重平衡失败：%s" % str(e)[:80]
        return out
    if action == "expand":
        if dry:
            out["did"] = "（dry）将扩池 %d 条" % EXPAND_ADD
            return out
        rc, tail = _run([os.path.join(HERE, "pool_expand.py"), "--limit", str(EXPAND_ADD)], timeout=1200)
        out["rc"], out["did"] = rc, tail
        return out
    if action == "mine":
        if dry:
            out["did"] = "（dry）将补采高赞样本"
            return out
        rc, tail = _run([os.path.join(HERE, "voice_mine.py"), "--videos", "60",
                         "--min-like", "10", "--pages", "2"], timeout=1500)
        out["rc"], out["did"] = rc, tail
        st = _load(AGENT_STATE, {}) or {}
        st["last_mine"] = _now().isoformat(timespec="seconds")
        json.dump(st, open(AGENT_STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return out
    if action in ("wait", "idle"):
        out["did"] = "按规则不动手"
        return out
    out["did"] = "未知动作"
    return out


# ---------------- REPORT ----------------
def board(s, out):
    q = s.get("quality") or {}
    it = q.get("interaction") or {}
    lines = [
        "# 养号线 质量一屏（自动，%s）" % _now().strftime("%Y-%m-%d %H:%M"),
        "",
        "- 档位 L%s ｜ 每日 %s 条 ｜ 间隔 ≥%s 分钟 ｜ 供给上限 %s" % (
            s.get("policy", {}).get("level"), s.get("policy", {}).get("max_per_day"),
            s.get("policy", {}).get("min_gap_min"), s.get("supply_cap")),
        "- 质量（新话术生效后 %d 条）：中位 %s ｜ 具体 %s%% ｜ 撞模板 %s%% ｜ 长度带 %s%% ｜ AI 腔 %s%%" % (
            q.get("n") or 0, q.get("median"), _pct(q.get("concrete_rate")),
            _pct(q.get("dup_rate")), _pct(q.get("len_ok_rate")), _pct(q.get("ai_smell_rate"))),
        "- 原型分布 %s（最扎堆 %s%%，%s 类）" % (
            q.get("archetypes"), _pct(q.get("max_share")), q.get("unique_arch")),
        "- 互动弱信号：%s 条已回验，点赞中位 %s，被赞 %s" % (
            it.get("n"), it.get("median_likes"),
            ("%s%%" % _pct(it.get("any_liked_rate"))) if it.get("any_liked_rate") is not None else "—"),
        "- 池子 %d ｜ 高赞样本 %d" % (s.get("pool", 0), s.get("hot", 0)),
        "",
        "## 本轮决策",
        "- 动作 `%s`：%s" % (out.get("action"), out.get("why")),
        "- 结果：%s" % (out.get("did") or "—"),
    ]
    for w in (out.get("worst") or []):
        lines.append("  - 最低分 %s：%s" % (w.get("score"), w.get("text")))
    try:
        open(BOARD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    except Exception:
        pass
    return BOARD


def _pct(x):
    try:
        return "%d" % round(100 * float(x))
    except Exception:
        return "—"


def once(dry=False):
    s = sense()
    action, why = decide(s)
    out = act(action, why, dry=dry)
    _log({"sense": {"n": s.get("quality", {}).get("n"), "median": s.get("quality", {}).get("median"),
                    "dup": s.get("quality", {}).get("dup_rate"), "pool": s.get("pool"),
                    "hot": s.get("hot")}, "decision": action, "why": why,
          "did": out.get("did"), "rc": out.get("rc")})
    board(s, out)
    print("[agent] 动作=%s ｜ %s ｜ %s" % (action, why, out.get("did")))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--board", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    if a.board:
        s = sense()
        board(s, {"action": "-", "why": "只重写一屏", "did": ""})
        print("[agent] 一屏已更新：%s" % BOARD)
        return 0
    return once(dry=a.dry)


if __name__ == "__main__":
    sys.exit(main())
