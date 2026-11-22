#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""freq_policy.py - 发帖频率的放行/收回判据（用可见率说话，不靠感觉）。

CEO 2026-11-18「你科学判断 是否可以合理增加频率」／2026-11-22「额度不要这么严厉，
我说了像个平台的常用用户行为」。

判据链（v2，两件事分开）：
  · **人类量级**：一天 10–20 条、间隔 6–25 分钟，按日期种子每天不同（不是固定数）。
    活跃时段交给 activity_clock / social_session，不在这里做硬配额。
  · **只被真失败叫停**：连续 2 次"平台拒绝/风控/登录失效"才收手；可见率只记录、不判决
    （CEO 2026-11-20 明确："评论在不在显示不重要，按规则好好评论"）。

旧版判据链（留档）：
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

# 人类量级（不再用"可见率换配额"的阶梯——那是把平台的审核延迟当成自己的 KPI）。
# 每日上限与间隔都取区间、按日期种子决定：同一个号每天不一样，才不像脚本。
PER_DAY = (10, 20)
GAP_MIN = (6, 25)
# 只有这两类信号允许叫停（真失败，不是"看不见"）：
CONSEC_REAL_FAIL = 2


def _rng_for_today():
    import random as _r
    from datetime import datetime as _dt
    return _r.Random(int(_dt.now().strftime("%Y%m%d")))


def human_band():
    """今天的"人类量级"上限与最小间隔（同日稳定、跨日变化）。"""
    r = _rng_for_today()
    return r.randint(*PER_DAY), r.randint(*GAP_MIN)


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
    real = 0
    for r in reversed(a):
        why = str(r.get("why") or "")
        if r.get("visible") is False and any(k in why for k in ("风控", "登录", "拒绝", "captcha")):
            real += 1
        else:
            break
    return {"n": n, "visible": vis, "rate": round(rate, 3), "consec_real_fail": real,
            "rate_last5": round(rate5, 3), "consec_invisible": consec}


def decide(stats, cur_stage=0):
    """返回 (每日上限, 最小间隔分钟, 理由)。只被真失败叫停，可见率只记录。"""
    per, gap = human_band()
    real = int(stats.get("consec_real_fail") or 0)
    if real >= CONSEC_REAL_FAIL:
        return 2, 60, ("连续 %d 次真发送失败（平台拒绝/风控/登录失效）→ 收手观察；"
                       "可见率 %.0f%% 仅记录不判决" % (real, 100 * stats.get("rate", 0)))
    return per, gap, ("人类量级：今天 %d 条、最短 %d 分钟（可见率 %.0f%% 仅记录，不换配额）"
                      % (per, gap, 100 * stats.get("rate", 0)))


def load_policy():
    """读策略；没有文件或字段缺就用今天的人类带（不再回落到 2 条/90 分钟）。"""
    per, gap = human_band()
    base = {"stage": 0, "max_per_day": per, "min_gap_min": gap, "why": "人类量级（默认）"}
    try:
        d = json.load(open(POLICY, encoding="utf-8")) or {}
        base.update({k: v for k, v in d.items() if v is not None})
    except Exception:
        pass
    return base


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
    stage = 0
    if a.show or not a.recompute:
        print("[freq] 已回验动作 %d 条：可见 %d（%.0f%%）｜近5条可见率 %.0f%% ｜连续不可见 %d"
              % (st["n"], st["visible"], 100 * st["rate"],
                 100 * st["rate_last5"], st["consec_invisible"]))
        print("[freq] 判定：每日 %d 条、间隔 ≥%d 分钟" % (per, gap))
        print("[freq] 依据：%s" % why)
        return 0
    rec = {"stage": stage, "max_per_day": per, "min_gap_min": gap, "why": why,
           "evidence": st, "ts": __import__("datetime").datetime.now().isoformat(timespec="seconds")}
    json.dump(rec, open(POLICY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[freq] 已写回 %s：每日 %d 条 / 间隔 %d 分钟（%s）"
          % (os.path.relpath(POLICY, ROOT), per, gap, why))
    return 0


def self_test():
    """v2 判据必须能红：人类量级在天内稳定、跨日可变；只有真失败才收手。"""
    def mk(flags, why=""):
        return [{"ts": "2026-11-22T1%d:00:00" % i, "visible": f, "why": why}
                for i, f in enumerate(flags)]
    cases = []
    per1, gap1 = human_band()
    per2, gap2 = human_band()
    cases.append(("同日稳定", (per1, gap1) == (per2, gap2)))
    cases.append(("人类量级≥10 条", per1 >= 10))
    cases.append(("间隔≤25 分钟", gap1 <= 25))
    # 可见率低但无真失败 → 配额不降（可见率只记录）
    s = summarize(mk([False] * 8))
    per3, gap3, why3 = decide(s, 0)
    cases.append(("可见率低不降配额", per3 == per1 and "仅记录" in why3))
    # 连续真失败 → 收手
    s2 = summarize(mk([False, False], why="风控拒绝"))
    per4, gap4, why4 = decide(s2, 0)
    cases.append(("连续真失败收手", per4 <= 2 and gap4 >= 30))
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
