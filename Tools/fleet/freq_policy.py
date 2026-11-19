#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""freq_policy.py - 发帖频率的放行/收回判据（用可见率说话，不靠感觉）。

CEO 2026-11-18「你科学判断 是否可以合理增加频率」。

判据链：
  1 只认**公开可见**：`code=0 发送成功`不算数。2026-11-17/18 实锚——4 次提交里 3 次
    公开不可见，其中昨天那条 24 小时后仍不可见，说明"待审核"实际等于没发出去。
  2 样本门槛：<6 条不下结论（现在的 4 条只够判"不许加"，不够判"可以加"）。
  3 阶梯上行：可见率够才升一档，升档靠证据，降档靠红线（连续 2 条不可见立即回退）。
  4 不允许"为了多发文而放宽判据"——可见率是唯一的准入指标。

用法：
  python3 Tools/fleet/freq_policy.py --show          # 现在的档位与依据
  python3 Tools/fleet/freq_policy.py --recompute     # 用台账重算并写回
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
POLICY = os.path.join(SOCIAL, "FREQ-POLICY.json")
LEDGERS = [os.path.join(SOCIAL, "practice-log.jsonl"),
           os.path.join(SOCIAL, "comments-sent.jsonl")]

# 阶梯：(档位, 每日上限, 最小间隔分钟, 升到此档所需样本, 所需可见率)
# 2026-11-19 CEO「不至于，我说了模拟人类操作习惯就好，不要这么保守」。
# 原表 2/3/4/6 条/日是把"人类节律"做成了硬配额：实测一个活跃用户在同一晚
# 56 分钟里发 10 条完全正常（17:35-18:31），且真实可见率 67%——限额才是那个假的约束。
# 改为"人类量级"：单日上限按活跃用户给足，间隔与活跃时段交给 human_rhythm 决定。
LADDER = [
    (0, 8, 15, 0, 0.0),        # 试用档：一天 8 条、最短 15 分钟
    (1, 12, 12, 6, 0.60),
    (2, 18, 8, 15, 0.70),
    (3, 25, 5, 25, 0.80),
]
ROLLBACK_VISIBLE = 0.45        # 近 5 条可见率低于此即降档（含假红教训：只算有结论的行）
CONSEC_INVISIBLE = 2           # 连续不可见即降档


def load_rows():
    out = []
    for p in LEDGERS:
        try:
            for line in open(p, encoding="utf-8"):
                if line.strip():
                    out.append(json.loads(line))
        except FileNotFoundError:
            pass
    return out


def attempts(rows):
    """只统计"真发出去并回验过"的条目（有 visible 字段）。"""
    a = []
    for r in rows:
        if r.get("action") in ("verify", "post") and "visible" in r:
            a.append(r)
        elif r.get("ok") is True and "visible" in r:
            a.append(r)
    a.sort(key=lambda r: str(r.get("ts", "")))
    return a


def summarize(a):
    n = len(a)
    vis = sum(1 for r in a if r.get("visible"))
    rate = (vis / n) if n else 0.0
    last5 = a[-5:]
    rate5 = (sum(1 for r in last5 if r.get("visible")) / len(last5)) if last5 else 0.0
    consec = 0
    for r in reversed(a):
        if r.get("visible"):
            break
        consec += 1
    return {"n": n, "visible": vis, "rate": round(rate, 3),
            "rate_last5": round(rate5, 3), "consec_invisible": consec}


def decide(stats, cur_stage=0):
    """返回 (档位, 每日上限, 间隔, 理由)。先判回退，再判升档。"""
    if stats["n"] == 0:
        return 0, 2, 90, "无样本：按试用档"
    if stats["consec_invisible"] >= CONSEC_INVISIBLE:
        new = max(0, cur_stage - 1)
        return (LADDER[new][1],) + (LADDER[new][2],) + (
            "连续 %d 条不可见 → 降到档 %d" % (stats["consec_invisible"], new),)
    if stats["n"] >= 5 and stats["rate_last5"] < ROLLBACK_VISIBLE:
        new = max(0, cur_stage - 1)
        return (LADDER[new][1], LADDER[new][2],
                "近 5 条可见率 %.0f%% < %.0f%% → 降到档 %d"
                % (100 * stats["rate_last5"], 100 * ROLLBACK_VISIBLE, new))
    best = LADDER[0]
    for stage, per, gap, need_n, need_rate in LADDER:
        if stats["n"] >= need_n and stats["rate"] >= need_rate and stage <= cur_stage + 1:
            best = (stage, per, gap, need_n, need_rate)
    stage, per, gap, need_n, need_rate = best
    if stage == cur_stage:
        why = ("可见率 %.0f%%（%d/%d 条）未达升档条件（需 %d 条且 ≥%.0f%%）→ 维持档 %d"
               % (100 * stats["rate"], stats["visible"], stats["n"],
                  next((n for s, _, _, n, _ in LADDER if s == cur_stage + 1), 999),
                  100 * next((r for s, _, _, _, r in LADDER if s == cur_stage + 1), 1.0),
                  stage))
    else:
        why = ("可见率 %.0f%%（%d/%d）达到档 %d 要求 → 升档"
               % (100 * stats["rate"], stats["visible"], stats["n"], stage))
    return per, gap, why


def load_policy():
    try:
        return json.load(open(POLICY, encoding="utf-8"))
    except Exception:
        return {"stage": 0, "max_per_day": 2, "min_gap_min": 90, "why": "初始"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--recompute", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    rows = load_rows()
    at = attempts(rows)
    st = summarize(at)
    cur = load_policy()
    per, gap, why = decide(st, int(cur.get("stage", 0)))
    stage = max(0, min(3, [s for s, p, g, _, _ in LADDER if p == per and g == gap][0]))
    if a.show or not a.recompute:
        print("[freq] 已回验动作 %d 条：可见 %d（%.0f%%）｜近5条可见率 %.0f%% ｜连续不可见 %d"
              % (st["n"], st["visible"], 100 * st["rate"],
                 100 * st["rate_last5"], st["consec_invisible"]))
        print("[freq] 当前档位 %s → 判定：每日 %d 条、间隔 ≥%d 分钟" % (cur.get("stage"), per, gap))
        print("[freq] 依据：%s" % why)
        if st["n"] < 6:
            print("[freq] 样本不足（<6），不允许升档；先按「短句/不同视频」做对照实验")
        return 0
    rec = {"stage": stage, "max_per_day": per, "min_gap_min": gap, "why": why,
           "evidence": st, "ts": __import__("datetime").datetime.now().isoformat(timespec="seconds")}
    json.dump(rec, open(POLICY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[freq] 已写回 %s：每日 %d 条 / 间隔 %d 分钟（%s）"
          % (os.path.relpath(POLICY, ROOT), per, gap, why))
    return 0


def self_test():
    """判据必须能红：三种台账必须给出三种不同结论。"""
    def mk(flags):
        return [{"ts": "2026-11-18T1%d:00:00" % i, "visible": f} for i, f in enumerate(flags)]
    cases = []
    # 连续两条不可见 → 必须降档
    s = summarize(mk([True, True, False, False]))
    per, gap, why = decide(s, 1)
    cases.append(("连续不可见可触发降档", "降到档" in why or per <= LADDER[1][1]))
    # 高可见率但样本不足 → 不许升
    s2 = summarize(mk([True, True, True]))
    per2, _, why2 = decide(s2, 0)
    cases.append(("样本<6 不升档", per2 <= LADDER[0][1]))
    # 6 条全可见 → 应允许升到档 1
    s3 = summarize(mk([True] * 6))
    per3, _, why3 = decide(s3, 0)
    cases.append(("6 条全可见可升档", per3 >= LADDER[1][1]))
    # 近 5 条可见率低 → 回退
    s4 = summarize(mk([True, True, True, False, False, False, False]))
    per4, _, why4 = decide(s4, 2)
    cases.append(("近5条低可见率回退", per4 <= LADDER[1][1]))
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
