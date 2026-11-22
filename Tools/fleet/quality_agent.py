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
HOT_TARGET = 1200           # 高赞样本目标条数（2026-11-22 并发补采后 11 秒入 949 条，目标上调）
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
    # 整面体检（12 个面，可复算）：一屏要能回答"这一线还有几个面是红的"
    try:
        import surface_audit as sa
        s["surface"] = sa.audit()
    except Exception as e:
        s["surface"] = {"red": None, "skip": None, "checks": [],
                        "error": str(e)[:60]}
    # 本地模型评审（规则算数、模型判"像不像人"）；训练独占时排队，不硬打
    try:
        import local_review as lr
        s["review"] = lr.run(n=3)
    except Exception as e:
        s["review"] = {"why": "评审调用失败：%s" % str(e)[:60]}
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
        "- 本地模型评审：%s" % _review_line(s.get("review") or {}),
        "- 互动弱信号：%s 条已回验，点赞中位 %s，被赞 %s" % (
            it.get("n"), it.get("median_likes"),
            ("%s%%" % _pct(it.get("any_liked_rate"))) if it.get("any_liked_rate") is not None else "—"),
        "- 池子 %d ｜ 高赞样本 %d ｜ 12 面：红 %s / 待判 %s" % (
            s.get("pool", 0), s.get("hot", 0),
            (s.get("surface") or {}).get("red"), (s.get("surface") or {}).get("skip")),
        "- 红面：%s" % ("、".join("%s %s" % (c["id"], c["name"])
                                 for c in ((s.get("surface") or {}).get("checks") or [])
                                 if c.get("ok") is False) or "无"),
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


def _review_line(rv):
    if rv.get("n"):
        return "评 %d 条，人味中位 %s，原型 %s%s" % (
            rv.get("n"), rv.get("human_median"), rv.get("archetypes"),
            ("；问题：" + "、".join(rv.get("issues") or [])[:60]) if rv.get("issues") else "")
    return rv.get("why") or "无"


def _pct(x):
    try:
        return "%d" % round(100 * float(x))
    except Exception:
        return "—"


# ---------------- 任务台账（自驱的核心：有活自己扛） ----------------
BACKLOG = os.path.join(STATE, "QUALITY-BACKLOG.json")
ESCALATE = os.path.join(STATE, "ESCALATIONS.md")
MAX_ATTEMPTS = 3

# 每个任务由谁负责：agent 能自己闭环的归 agent，要动代码/阈值的归 human
ITEMS = {
    "Q-POOL":   {"title": "内容池扩到目标", "owner": "agent", "priority": 5},
    "Q-HOT":    {"title": "补采高赞样本", "owner": "agent", "priority": 6},
    "Q-DIV":    {"title": "原型分布别扎堆", "owner": "agent", "priority": 4},
    "Q-DUP":    {"title": "撞模板率压到 10% 以下", "owner": "human", "priority": 2},
    "Q-LEN":    {"title": "长度带命中率回到 80%", "owner": "human", "priority": 3},
    "Q-AI":     {"title": "AI 腔必须为 0（闸漏了）", "owner": "human", "priority": 1},
    "S8-SPEED": {"title": "出稿节拍压到 30s 内", "owner": "human", "priority": 1},
    "S7-GATE":  {"title": "闸负控有红，定位失效断言", "owner": "human", "priority": 1},
    "S9-ACCT":  {"title": "跨号隔离/重复评论收口", "owner": "human", "priority": 1},
    "Q-WAIT":   {"title": "等新稿样本攒够（≥8）", "owner": "agent", "priority": 9},
}


def _backlog():
    d = _load(BACKLOG, {}) or {}
    return d.get("items") or {}


def _save_backlog(items):
    json.dump({"ts": _now().isoformat(timespec="seconds"), "items": items},
              open(BACKLOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def sync_backlog(s):
    """把"当前事实"同步成任务：新问题立卡，已消失的自动关掉（不留假活）。"""
    q = s.get("quality") or {}
    n = int(q.get("n") or 0)
    items = _backlog()
    want = {}
    if s.get("pool", 0) < POOL_TARGET:
        want["Q-POOL"] = "池 %d < 目标 %d" % (s.get("pool", 0), POOL_TARGET)
    if s.get("hot", 0) < HOT_TARGET:
        want["Q-HOT"] = "高赞样本 %d < 目标 %d" % (s.get("hot", 0), HOT_TARGET)
    if n >= MIN_N:
        if float(q.get("max_share") or 0) > SHARE_LINE:
            want["Q-DIV"] = "单一原型 %.0f%% > %.0f%%" % (100 * float(q.get("max_share") or 0), 100 * SHARE_LINE)
        if float(q.get("dup_rate") or 0) > DUP_LINE:
            want["Q-DUP"] = "撞模板 %.0f%% > %.0f%%" % (100 * float(q.get("dup_rate") or 0), 100 * DUP_LINE)
        if float(q.get("len_ok_rate") or 0) < LEN_LINE:
            want["Q-LEN"] = "长度带命中 %.0f%% < %.0f%%" % (100 * float(q.get("len_ok_rate") or 0), 100 * LEN_LINE)
        if float(q.get("ai_smell_rate") or 0) > 0:
            want["Q-AI"] = "AI 腔 %.0f%%（必须 0）" % (100 * float(q.get("ai_smell_rate") or 0))
    if n < MIN_N:
        want["Q-WAIT"] = "新话术下样本 %d 条（需 ≥%d）" % (n, MIN_N)
    for c in ((s.get("surface") or {}).get("checks") or []):
        if c.get("ok") is not False:
            continue
        if c.get("id") == "S8":
            want["S8-SPEED"] = c.get("detail") or ""
        elif c.get("id") == "S7":
            want["S7-GATE"] = c.get("detail") or ""
        elif c.get("id") == "S9":
            want["S9-ACCT"] = c.get("detail") or ""
    # 新问题立卡 / 已有问题刷新理由 / 问题消失则关闭
    now = _now().isoformat(timespec="seconds")
    for k, why in want.items():
        if k in items and items[k].get("status") in ("open", "doing", "blocked", "waiting"):
            items[k]["why"] = why
            items[k]["updated"] = now
            continue
        meta = ITEMS.get(k) or {"title": k, "owner": "human", "priority": 5}
        items[k] = {"id": k, "title": meta["title"], "owner": meta["owner"],
                    "priority": meta["priority"], "why": why, "attempts": 0,
                    "status": "open", "created": now, "updated": now}
    for k, v in list(items.items()):
        if k not in want and v.get("status") in ("open", "doing"):
            v["status"] = "done"
            v["updated"] = now
            v["closed_why"] = "问题已消失（事实不再触发这个任务）"
    _save_backlog(items)
    escalations(items)
    return items


def pick_item(items):
    """先干自己能闭环的，干不了的去把证据备齐（这同样是自驱，不是等）。"""
    openc = [v for v in items.values() if v.get("status") in ("open", "doing")]
    # human 型任务取过一次证就转 waiting：不再反复摘同一张卡（实测曾空转 174 次）
    for v in list(openc):
        if v.get("owner") == "human" and int(v.get("attempts") or 0) >= 1:
            v["status"] = "waiting"
            openc.remove(v)
    if not openc:
        return None
    # 排法：①human 型且还没取过证的先做一次（取证便宜，且能让主控一小时内有卡片可执行）
    # ②agent 能自己闭环的 ③其余 human 型（等主控处置，不重复打扰）
    def _k(v):
        human_first = 0 if (v.get("owner") == "human" and int(v.get("attempts") or 0) == 0) else (
            1 if v.get("owner") == "agent" else 2)
        return (human_first, int(v.get("priority") or 9), str(v.get("created") or ""))
    openc.sort(key=_k)
    return openc[0]


def act_item(item, s, dry=False):
    """按任务 id 动手；human 型任务只做取证（把结论备成一分钟可执行的卡片）。"""
    iid = item.get("id")
    out = {"action": iid, "why": item.get("why"), "did": ""}
    if iid == "Q-POOL":
        if dry:
            out["did"] = "（dry）扩池 %d" % EXPAND_ADD
            return out
        rc, tail = _run([os.path.join(HERE, "pool_expand.py"), "--limit", str(EXPAND_ADD)], timeout=1200)
        out["rc"], out["did"] = rc, tail
        return out
    if iid == "Q-HOT":
        if dry:
            out["did"] = "（dry）补采高赞样本"
            return out
        rc, tail = _run([os.path.join(HERE, "voice_mine.py"), "--videos", "60",
                         "--min-likes" if False else "--min-like", "10", "--pages", "2"], timeout=1500)
        out["rc"], out["did"] = rc, tail
        st = _load(AGENT_STATE, {}) or {}
        st["last_mine"] = _now().isoformat(timespec="seconds")
        json.dump(st, open(AGENT_STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return out
    if iid == "Q-DIV":
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
                out["did"] = "最扎堆原型 %s 计数 +3" % top
            else:
                out["did"] = "今天还没有原型计数"
        except Exception as e:
            out["did"] = "重平衡失败：%s" % str(e)[:70]
        return out
    if iid == "S8-SPEED":
        # 取证：把"慢在生成还是慢在发帖排队"分开算清楚
        rows = [r for r in _load_log() if r.get("action") == "timing"][-10:]
        gen = sorted(float(r.get("gen_s") or 0) for r in rows)
        post = sorted(float(r.get("post_s") or 0) for r in rows if r.get("post_s") is not None)
        tot = sorted(float(r.get("total_s") or 0) for r in rows)
        med = lambda a: (a[len(a) // 2] if a else None)
        out["did"] = "取证：total 中位 %s、gen 中位 %s、post 中位 %s（n=%d）%s" % (
            med(tot), med(gen), med(post), len(rows),
            "；历史行无 post_s 字段，等新样本才能拆分" if not post else "")
        out["evidence"] = {"total_med": med(tot), "gen_med": med(gen), "post_med": med(post)}
        return out
    if iid == "S7-GATE":
        # 证据要从真正的产物读（GATE-RESULT.json 的 overall/pos/neg），
        # 不是跑 guard 自己的 self-test——那是另一套东西，会得出"全绿"的错觉。
        try:
            d = _load(os.path.join(SOCIAL, "state", "GATE-RESULT.json"), {})
            bad = (d.get("pos_fail_samples") or []) + (d.get("neg_leak_samples") or [])
            out["did"] = "闸回归 overall=%s 正例 %s/%s 负例拦 %s/%s" % (
                d.get("overall"), d.get("pos_pass"), d.get("pos_n"),
                d.get("neg_blocked"), d.get("neg_n"))
            out["detail"] = bad[:3] or ["（无漏/误样本，红在别处）"]
        except Exception as e:
            out["did"] = "读闸结果失败：%s" % str(e)[:60]
        return out
    if iid == "S9-ACCT":
        rc, t = _run([os.path.join(HERE, "social_guard.py"), "--group", "accounts"], timeout=300)
        det = []
        try:
            for line in open(os.path.join(SOCIAL, "state", "GUARD-ACCOUNTS.json"), encoding="utf-8"):
                pass
            d = _load(os.path.join(SOCIAL, "state", "GUARD-ACCOUNTS.json"), {})
            det = ["%s %s" % (c.get("id"), (c.get("detail") or "")[:80])
                   for c in (d.get("checks") or []) if c.get("ok") is False][:4]
        except Exception:
            pass
        out["rc"], out["did"], out["detail"] = rc, "账号安全：%d 项红" % len(det), det
        return out
    if iid == "Q-WAIT":
        out["did"] = "等出稿，不动手（样本不足时不折腾模型）"
        return out
    out["did"] = "未实现的动作"
    return out


def _load_log():
    out = []
    try:
        for line in open(os.path.join(SOCIAL, "practice-log.jsonl"), encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def verify_item(item, s, out):
    """做完必须自验：事实没变就不许标完成（否则又是假绿）。"""
    iid = item.get("id")
    if iid == "Q-POOL":
        return (s.get("pool", 0) >= POOL_TARGET, "池 %d / 目标 %d" % (s.get("pool", 0), POOL_TARGET))
    if iid == "Q-HOT":
        return (s.get("hot", 0) >= HOT_TARGET, "样本 %d / 目标 %d" % (s.get("hot", 0), HOT_TARGET))
    if iid == "Q-DIV":
        q = s.get("quality") or {}
        if int(q.get("n") or 0) < MIN_N:
            return None, "样本不足，无法验证"
        return (float(q.get("max_share") or 0) <= SHARE_LINE, "最扎堆 %.0f%%" % (100 * float(q.get("max_share") or 0)))
    if iid in ("S8-SPEED", "S7-GATE", "S9-ACCT"):
        # human 型任务：本轮只取证，不算闭环；证据必须写清楚，否则卡片没用
        det = out.get("detail") or []
        ev = out.get("did") or ""
        if det:
            ev += "；" + " | ".join(str(x) for x in det[:3])
        return None, ev[:300]
    if iid == "Q-WAIT":
        q = s.get("quality") or {}
        return (int(q.get("n") or 0) >= MIN_N, "样本 %d" % int(q.get("n") or 0))
    return None, "无自动验证"


def escalations(items):
    """把所有 human 型/反复失败的任务写成一屏，供人一分钟内决断。"""
    lines = ["# 待主控处置（自动生成 %s）" % _now().strftime("%Y-%m-%d %H:%M"), ""]
    rows = [v for v in items.values() if v.get("status") in ("open", "blocked") and v.get("owner") == "human"]
    rows.sort(key=lambda v: int(v.get("priority") or 9))
    if not rows:
        lines.append("无。")
    for v in rows:
        lines.append("## %s %s（尝试 %d 次）" % (v["id"], v["title"], int(v.get("attempts") or 0)))
        lines.append("- 现象：%s" % (v.get("why") or "—"))
        if v.get("evidence"):
            lines.append("- 证据：%s" % v["evidence"])
        if v.get("status") == "blocked":
            lines.append("- 状态：已重试 %d 次未果，**需要主控改结构**" % MAX_ATTEMPTS)
    try:
        open(ESCALATE, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    except Exception:
        pass


LOCK = os.path.join(STATE, "QUALITY-AGENT.lock")


def _take_lock():
    """单实例：扩池一轮要 8–10 分钟，launchd 与手工调用可能撞车，
    两个进程同时写 VIDEO-TITLES 会互相覆盖（2026-11-22 实测过同类事故）。"""
    try:
        if os.path.exists(LOCK):
            pid = int((open(LOCK).read() or "0").strip() or 0)
            if pid and pid != os.getpid():
                os.kill(pid, 0)
                return False
    except Exception:
        pass
    try:
        open(LOCK, "w").write(str(os.getpid()))
    except Exception:
        pass
    return True


def _drop_lock():
    try:
        if (open(LOCK).read() or "").strip() == str(os.getpid()):
            os.remove(LOCK)
    except Exception:
        pass


def once(dry=False):
    s = sense()
    items = sync_backlog(s)
    item = pick_item(items)
    if not item:
        board(s, {"action": "idle", "why": "没有未闭环任务（事实全绿）", "did": "空转一轮"})
        _log({"ts": _now().isoformat(timespec="seconds"), "decision": "idle",
              "why": "没有未闭环任务", "did": ""})
        print("[agent] 空闲：所有任务已闭环")
        return 0
    item["status"] = "doing"
    item["attempts"] = int(item.get("attempts") or 0) + 1
    out = act_item(item, s, dry=dry)
    if not dry:
        s2 = sense()          # 动作后重测
        ok, detail = verify_item(item, s2, out)
        out["verify"] = detail
        if ok is True:
            item["status"] = "done"
            item["closed_why"] = detail
        elif ok is False:
            # Q-WAIT 是"等条件"不是"做没做成"：条件不满足不该被判死
            if item.get("id") == "Q-WAIT":
                item["status"] = "waiting"
            elif item["attempts"] >= MAX_ATTEMPTS:
                item["status"] = "blocked"
            else:
                item["status"] = "open"
        else:
            # 无法自动验证（human 型/样本不足）：保持 open，等下一次或交主控
            item["status"] = "open"
        item["updated"] = _now().isoformat(timespec="seconds")
        item["evidence"] = detail
        _save_backlog(items)
        escalations(items)
        s = s2
    _log({"sense": {"n": (s.get("quality") or {}).get("n"),
                    "median": (s.get("quality") or {}).get("median"),
                    "pool": s.get("pool"), "hot": s.get("hot")},
          "decision": item.get("id"), "why": item.get("why"),
          "did": out.get("did"), "verify": out.get("verify"),
          "status": item.get("status"), "attempts": item.get("attempts")})
    board(s, out)
    print("[agent] 任务=%s（%s，第 %d 次）｜ %s ｜ 验证：%s" % (
        item.get("id"), item.get("owner"), item.get("attempts"),
        out.get("did"), out.get("verify") or "—"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--board", action="store_true")
    ap.add_argument("--backlog", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    if a.backlog:
        s = sense()
        items = sync_backlog(s)
        for v in sorted(items.values(), key=lambda x: (x.get("status"), int(x.get("priority") or 9))):
            print("%-9s %-6s %-7s 尝试%d  %s ← %s" % (
                v["id"], v.get("status"), v.get("owner"), int(v.get("attempts") or 0),
                v.get("title"), (v.get("why") or "")[:48]))
        return 0
    if a.board:
        s = sense()
        board(s, {"action": "-", "why": "只重写一屏", "did": ""})
        print("[agent] 一屏已更新：%s" % BOARD)
        return 0
    if not _take_lock():
        print("[agent] 已有实例在跑（扩池/补采可能正在进行），本轮让路")
        return 0
    try:
        return once(dry=a.dry)
    finally:
        _drop_lock()


if __name__ == "__main__":
    sys.exit(main())
