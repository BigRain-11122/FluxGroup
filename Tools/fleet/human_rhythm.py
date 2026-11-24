#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""human_rhythm.py - 把"人的操作习惯"写成可复算的模型（零 LLM，纯分布）。

CEO 2026-11-18「你要真正的模拟人类的操作习惯和回复习惯」。

现在的问题不是文案，是**行为轨迹**：我们原来的动作是"开浏览器 → 发一条 → 关掉"，
间隔均匀抖动 20-45 秒，回复在读到评论后 20 秒内就出现。真人不是这样：

  1 有作息：白天零散、晚饭后到睡前是高峰、深夜偶尔刷一下
  2 有会话：一次进来先刷若干条（只看不互动），再挑 0-2 条动手，然后离开
  3 有延迟：看到评论到回出来，多数在半小时到几小时，不是秒回
  4 有选择：绝大多数评论不回——全回才是最像机器人的行为
  5 有停留：读评论要花时间，页面要滚动，不是"打开接口就发"

这个模块只输出**分布与判决**，不发请求、不碰浏览器，所以能被自检与回归。
接进发帖流程见 social_comment（dwell/scroll）与 social_24x7（REPLY 阶段）。

用法：
  python3 Tools/fleet/human_rhythm.py --self-test
  python3 Tools/fleet/human_rhythm.py --now          # 现在该不该醒着/能做什么
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from datetime import datetime, timedelta

# ---- 作息：每小时"在线权重"（0-1）。依据是普通人刷 B 站的时段分布，
#      刻意做成双峰（午休 + 晚间）+ 深夜尾，而不是全天均一。
HOUR_WEIGHT = [
    0.25, 0.15, 0.08, 0.05, 0.05, 0.08, 0.15, 0.30,   # 00-07
    0.45, 0.55, 0.60, 0.60, 0.65, 0.55, 0.50, 0.50,   # 08-15
    0.55, 0.60, 0.65, 0.80, 0.90, 0.95, 0.90, 0.70,   # 16-23
]

# 会话长度（分钟）：对数正态，中位约 8 分钟，长尾到 40 分钟
SESSION_MEDIAN_MIN = 8.0
SESSION_SIGMA = 0.6


def awake(ts=None, rng=None):
    """现在是否"在线"。用权重做概率判定，不硬切时间窗——真人不会整点上下线。"""
    rng = rng or random
    ts = ts or datetime.now()
    w = HOUR_WEIGHT[ts.hour]
    return rng.random() < w


def session_plan(rng=None):
    """一次会话的计划：看多少条、动手几条、总共待多久。

    真人特征：看得多、动手少；动手数为 0 的会话占相当比例。
    """
    rng = rng or random
    dwell_min = min(45.0, max(2.0, rng.lognormvariate(math.log(SESSION_MEDIAN_MIN), SESSION_SIGMA)))
    passive = max(1, int(rng.gauss(6, 2.5)))          # 只浏览/滑动的条数
    r = rng.random()
    social = 0 if r < 0.45 else (1 if r < 0.85 else 2)  # 45% 的会话一条不动手
    return {"dwell_min": round(dwell_min, 1), "passive": passive, "social": social}


def reply_delay_s(now=None, rng=None):
    """从"看到评论"到"回出来"的延迟：对数正态，中位约 40 分钟，尾部到十几小时。

    秒回是最像机器的信号之一（我们原来 20 秒内就回）。夜里看到的评论，
    通常要等到下次醒来才回，所以再把延迟推到下一个在线时刻。
    """
    rng = rng or random
    now = now or datetime.now()
    med = 40 * 60
    d = rng.lognormvariate(math.log(med), 0.9)
    d = min(d, 14 * 3600)
    due = now + timedelta(seconds=d)
    # 落到深夜就顺延到早上（人不会凌晨三点回评论）
    while not (9 <= due.hour <= 23) or due.hour == 9 and due.minute < 30:
        due += timedelta(minutes=30)
        if (due - now).total_seconds() > 20 * 3600:
            break
    return int((due - now).total_seconds())


def should_reply(comment, rng=None):
    """该不该回这条。全回=机器人；按"有信息量/有钩子/有分歧"提高概率，
    纯灌水与注销号直接跳过。返回 (bool, 理由)。
    """
    rng = rng or random
    t = (comment or "").strip()
    if not t:
        return False, "空"
    if len(t) < 4:
        return False, "太短（无信息）"
    if any(g in t for g in ("账号已注销", "已注销")):
        return False, "注销号"
    p = 0.12                                   # 基础回复率：绝大多数不回
    if "?" in t or "？" in t:
        p += 0.35                              # 提问更可能被回
    if len(t) >= 15:
        p += 0.15                              # 有内容的更可能被回
    if any(w in t for w in ("求", "怎么", "为什么", "能不能", "有没有")):
        p += 0.15
    if any(w in t for w in ("傻", "垃圾", "骗", "别吹")):
        p -= 0.05                              # 挑衅类冷处理
    p = max(0.02, min(0.75, p))
    return rng.random() < p, "p=%.2f" % p


def dwell_before_post_s(rng=None):
    """读评论到动手之间的"阅读时间"：20-120 秒，模拟滚动与阅读。"""
    rng = rng or random
    return int(rng.uniform(20, 120))


def self_test():
    """分布要能被反向验证：不能靠"看起来像"。"""
    import statistics
    rng = random.Random(42)
    cases = []
    # 1 作息：22 点命中率应显著高于 4 点
    n = 4000
    late = sum(1 for _ in range(n) if awake(datetime(2026, 11, 18, 22), rng))
    dawn = sum(1 for _ in range(n) if awake(datetime(2026, 11, 18, 4), rng))
    cases.append(("22 点比 4 点活跃得多", late > dawn * 2))
    # 2 会话：45% 左右不动手
    plans = [session_plan(rng) for _ in range(2000)]
    idle = sum(1 for p in plans if p["social"] == 0) / len(plans)
    cases.append(("无互动会话占比 35-55%%（实测 %.0f%%）" % (100 * idle), 0.35 <= idle <= 0.55))
    # 3 回复延迟：中位应在 20-90 分钟之间，且不应有秒回
    ds = [reply_delay_s(datetime(2026, 11, 18, 20, 0), rng) for _ in range(2000)]
    med = statistics.median(ds)
    cases.append(("延迟中位 20-90 分钟（实测 %.0f 分）" % (med / 60), 20 * 60 <= med <= 90 * 60))
    cases.append(("几乎没有秒回（<60s 占比 %.1f%%）" % (100 * sum(1 for d in ds if d < 60) / len(ds)),
                  sum(1 for d in ds if d < 60) / len(ds) < 0.02))
    # 4 选择性：普通夸奖的回复率应低于提问
    rng2 = random.Random(7)
    plain = sum(1 for _ in range(2000) if should_reply("这个视频不错", rng2)[0]) / 2000
    ask = sum(1 for _ in range(2000) if should_reply("UP主这个转场怎么做的？", rng2)[0]) / 2000
    cases.append(("提问比夸奖更容易被回（%.0f%% vs %.0f%%）" % (100 * ask, 100 * plain), ask > plain + 0.2))
    cases.append(("注销号一律不回", not should_reply("账号已注销", rng2)[0]))
    # 5 停留时间在 20-120 秒
    d = [dwell_before_post_s(rng) for _ in range(500)]
    cases.append(("阅读停留 20-120 秒", min(d) >= 20 and max(d) <= 120))

    ok = 0
    for n_, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n_))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--now", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.now:
        now = datetime.now()
        print("现在 %s（权重 %.2f）→ 醒着：%s" % (now.strftime("%H:%M"), HOUR_WEIGHT[now.hour],
                                            "是" if awake(now, random.Random(1)) else "否"))
        print("会话计划示例：%s" % session_plan(random.Random(2)))
        print("回复延迟示例：%d 分钟" % (reply_delay_s(now, random.Random(3)) / 60))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
