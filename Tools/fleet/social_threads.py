#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_threads.py — 会话状态机（借 Chatwoot 的会话模型，不引它的代码）。

为什么要有这个：现在整条线是"一条评论 → 一份草稿 → 发或不发"，每条独立处理。
真实客服不是这样的——同一个人可能连问三句、我可能已经回过、也可能拖了两天没回该转人工。
没有会话状态就会犯三种错：对同一个人重复回同一句、把已经聊完的再翻出来、把该人接的
丢给模型。Chatwoot（37k star，核心 MIT）的模型很成熟，直接照抄它的状态与转移：

  open       有新消息，等我方处理
  waiting    我方已回，等对方（超时不动它）
  resolved   处理完（对方再来消息自动重开）
  snoozed    主动延后（到点自动回 open）
  handoff    转人工，模型绝不许再碰

外加两条 Chatwoot 的实务：**SLA**（等我方超时→升级）与 **canned**（标准口径片段，
只作为提示词素材，不直接发——对外发送权在 CEO）。

用法：
  python3 Tools/fleet/social_threads.py --inbound --plat bilibili --conv 388497033:BV1xx --author 某人 --text "求素材"
  python3 Tools/fleet/social_threads.py --outbound --conv ... --text "…" --by auto
  python3 Tools/fleet/social_threads.py --tick            # 结算超时/唤醒 snooze
  python3 Tools/fleet/social_threads.py --due             # 现在该回的清单
  python3 Tools/fleet/social_threads.py --show --conv ...
  python3 Tools/fleet/social_threads.py --self-test
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state", "social-threads.json")
EVENTS = os.path.join(ROOT, "cph4", "fleet", "social", "threads-events.jsonl")
SLA_HOURS = 24          # 等我方超过这个时长 → overdue
SLA_REOPEN = 72         # 转人工后再无动静多久算沉底（只用于报告）
HUMAN = "human"

# 合法转移（Chatwoot 语义 + 我们的 handoff）。表外一律拒绝，不靠调用方自觉。
TRANSITIONS = {
    "open":     {"waiting", "resolved", "snoozed", "handoff"},
    "waiting":  {"open", "resolved", "snoozed", "handoff"},
    "resolved": {"open"},                      # 对方再来消息才重开
    "snoozed":  {"open", "handoff"},
    "handoff":  {"open", "resolved"},          # 人能重新交还机器
}
SLOTS = ("status", "author", "platform", "last_in", "last_out", "last_text",
         "waiting_since", "snooze_until", "human_touched", "n_in", "n_out", "reason")


def _load():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(d):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def _event(row):
    os.makedirs(os.path.dirname(EVENTS), exist_ok=True)
    with open(EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now(ts=None):
    # ts=0 是合法时间戳（自检与回放都用它）；用 or 会把它当假值换成真实时间
    return ts if ts is not None else time.time()


def _blank(platform, author=""):
    return {"status": "open", "author": author, "platform": platform,
            "last_in": None, "last_out": None, "last_text": "", "waiting_since": None,
            "snooze_until": None, "human_touched": False, "n_in": 0, "n_out": 0,
            "reason": ""}


def can(from_status, to_status):
    return to_status in TRANSITIONS.get(from_status, set())


def record_inbound(store, conv, platform, text, author="", ts=None, commit=True):
    """对方来了消息。resolved 自动重开；handoff 保持 handoff（人接手，机器不抢）。"""
    now = _now(ts)
    th = store.get(conv) or _blank(platform, author)
    if th["status"] in ("resolved", "snoozed"):
        th["status"] = "open"
        th["snooze_until"] = None
    th["n_in"] += 1
    th["last_in"] = now
    th["last_text"] = text
    if author:
        th["author"] = author
    if th["status"] not in ("handoff",):
        th["status"] = "open"
    th["waiting_since"] = now
    store[conv] = th
    if commit:
        _save(store)
        _event({"ts": now, "conv": conv, "kind": "in", "text": text, "author": author,
                "status": th["status"]})
    return th


def record_outbound(store, conv, text, by="auto", ts=None, commit=True):
    """我方发出（auto=机器草稿经人确认后发出；human=本人回复）。"""
    now = _now(ts)
    th = store.get(conv)
    if not th:
        return None, "没有会话记录，先记 inbound"
    if th["status"] == "handoff" and by != HUMAN:
        return th, "已转人工：机器不许再发"
    # 人工接手是唯一允许从 handoff 转回对话流程的动作：人回了，机器才能继续跟
    if not can(th["status"], "waiting") and not (th["status"] == "handoff" and by == HUMAN):
        return th, "状态 %s 不允许转 waiting" % th["status"]
    th["status"] = "waiting"
    th["n_out"] += 1
    th["last_out"] = now
    th["waiting_since"] = None
    th["reason"] = "by=%s" % by
    if by == HUMAN:
        th["human_touched"] = True
    store[conv] = th
    if commit:
        _save(store)
        _event({"ts": now, "conv": conv, "kind": "out", "text": text, "by": by,
                "status": th["status"]})
    return th, ""


def handoff(store, conv, reason="", ts=None, commit=True):
    now = _now(ts)
    th = store.get(conv)
    if not th:
        return None, "没有会话记录"
    if not can(th["status"], "handoff"):
        return th, "状态 %s 不能转人工" % th["status"]
    th["status"] = "handoff"
    th["reason"] = reason[:120]
    th["waiting_since"] = None
    store[conv] = th
    if commit:
        _save(store)
        _event({"ts": now, "conv": conv, "kind": "handoff", "reason": reason})
    return th, ""


def snooze(store, conv, hours=6, ts=None, commit=True):
    now = _now(ts)
    th = store.get(conv)
    if not th:
        return None, "没有会话记录"
    if not can(th["status"], "snoozed"):
        return th, "状态 %s 不能 snooze" % th["status"]
    th["status"] = "snoozed"
    th["snooze_until"] = now + hours * 3600
    store[conv] = th
    if commit:
        _save(store)
        _event({"ts": now, "conv": conv, "kind": "snooze", "hours": hours})
    return th, ""


def tick(store, ts=None, commit=True):
    """结算：snooze 到点回 open；等我方超 SLA 标记 overdue（只标不自动发）。"""
    now = _now(ts)
    woke, overdue = [], []
    for conv, th in store.items():
        if th["status"] == "snoozed" and th.get("snooze_until") and now >= th["snooze_until"]:
            th["status"] = "open"
            th["snooze_until"] = None
            woke.append(conv)
        if th["status"] == "open" and th.get("waiting_since") is not None:
            hrs = (now - th["waiting_since"]) / 3600.0
            if hrs >= SLA_HOURS:
                overdue.append((conv, round(hrs, 1)))
    if commit and (woke or overdue):
        _save(store)
        _event({"ts": now, "kind": "tick", "woke": woke,
                "overdue": [c for c, _ in overdue]})
    return {"woke": woke, "overdue": overdue}


def due(store, limit=20, ts=None):
    """现在该回的清单：open 优先，按等我方的时长倒序（最久没回的最急）。"""
    now = _now(ts)
    rows = []
    for conv, th in store.items():
        if th["status"] != "open":
            continue
        ref = th.get("waiting_since")
        if ref is None:
            ref = th.get("last_in")
        if ref is None:
            ref = now
        wait_h = (now - ref) / 3600.0
        rows.append((round(wait_h, 1), conv, th))
    rows.sort(key=lambda x: -x[0])
    return rows[:limit]


def self_test():
    cases = []
    st = {}
    # 1 新会话 = open
    th = record_inbound(st, "c1", "bilibili", "求素材", "甲", ts=1000, commit=False)
    cases.append(("新会话是 open", th["status"] == "open"))
    # 2 回完转 waiting
    th, why = record_outbound(st, "c1", "在置顶", ts=1100, commit=False)
    cases.append(("回完转 waiting", th["status"] == "waiting" and not why))
    # 3 对方再来 = 重开
    th = record_inbound(st, "c1", "bilibili", "没看到", ts=1200, commit=False)
    cases.append(("再来消息重开", th["status"] == "open"))
    # 4 非法转移必须被拒（resolved 不能直接 waiting）
    st2 = {"c9": dict(_blank("bilibili"), status="resolved")}
    _, why = record_outbound(st2, "c9", "x", ts=1300, commit=False)
    cases.append(("resolved→waiting 被拒", bool(why)))
    # 5 handoff 后机器不许发
    st3 = {"c2": dict(_blank("bilibili"), status="open")}
    handoff(st3, "c2", "挑刺", ts=1400, commit=False)
    _, why = record_outbound(st3, "c2", "x", by="auto", ts=1500, commit=False)
    cases.append(("handoff 后机器禁止发送", bool(why)))
    # 6 人可以发（交还机器）
    th, why = record_outbound(st3, "c2", "x", by=HUMAN, ts=1600, commit=False)
    cases.append(("人工可以接手回", th["status"] == "waiting" and not why))
    # 7 SLA：超 24h 标 overdue
    st4 = {}
    record_inbound(st4, "c3", "bilibili", "hi", ts=0, commit=False)
    r = tick(st4, ts=25 * 3600, commit=False)
    cases.append(("超 24h 判 overdue", [c for c, _ in r["overdue"]] == ["c3"]))
    # 8 snooze 到点回 open
    st5 = {}
    record_inbound(st5, "c4", "bilibili", "hi", ts=0, commit=False)
    snooze(st5, "c4", hours=1, ts=0, commit=False)
    r = tick(st5, ts=3601, commit=False)
    cases.append(("snooze 到点醒", st5["c4"]["status"] == "open"))
    # 9 due 按最久没回排序
    st6 = {}
    record_inbound(st6, "old", "bilibili", "a", ts=0, commit=False)
    record_inbound(st6, "new", "bilibili", "b", ts=90000, commit=False)
    d = due(st6, ts=100000)
    cases.append(("due 最久优先", d[0][1] == "old"))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbound", action="store_true")
    ap.add_argument("--outbound", action="store_true")
    ap.add_argument("--tick", action="store_true")
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--handoff", action="store_true")
    ap.add_argument("--snooze", type=float, default=0, help="延后小时数")
    ap.add_argument("--plat", default="bilibili")
    ap.add_argument("--conv", default=None)
    ap.add_argument("--author", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--by", default="auto")
    ap.add_argument("--reason", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    st = _load()
    if a.inbound:
        th = record_inbound(st, a.conv, a.plat, a.text, a.author)
        print("[thread] %s → %s（第 %d 条）" % (a.conv, th["status"], th["n_in"]))
        return 0
    if a.outbound:
        th, why = record_outbound(st, a.conv, a.text, by=a.by)
        print("[thread] %s → %s%s" % (a.conv, (th or {}).get("status"), (" | " + why) if why else ""))
        return 0 if not why else 2
    if a.handoff:
        th, why = handoff(st, a.conv, a.reason)
        print("[thread] %s → %s%s" % (a.conv, (th or {}).get("status"), (" | " + why) if why else ""))
        return 0 if not why else 2
    if a.snooze:
        th, why = snooze(st, a.conv, a.snooze)
        print("[thread] %s 延后 %.1fh" % (a.conv, a.snooze))
        return 0
    if a.tick:
        r = tick(st)
        print("[thread] 唤醒 %d · 超时未回 %d %s"
              % (len(r["woke"]), len(r["overdue"]), r["overdue"][:5]))
        return 0
    if a.due:
        for wait, conv, th in due(st):
            print("  %5.1fh  %-28s %-6s %s" % (wait, conv, th["status"],
                                               (th.get("last_text") or "")[:30]))
        return 0
    if a.show:
        th = st.get(a.conv)
        print(json.dumps(th or {}, ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
