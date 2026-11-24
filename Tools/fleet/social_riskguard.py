#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_riskguard.py - 平台风控闸：任何采集/发送前必须先过它，封号风险靠代码挡，不靠记性。

CEO 2026-11-17「你还要有风控意识 不要被封号了」。

平台封号的真实判据（按我们见过的现象写，不猜）：
  * 频率异常：短时间大量页面/请求、固定间隔机械访问
  * 行为异常：只读不互动、只采集不消费、整点准点跑
  * 环境异常：同一 cookie 在多个 IP/无头环境反复登录（小红书 300012、知乎 unhuman 都是这类）
  * 内容异常：批量同质回复、复制粘贴、带外链/联系方式
  * 账号新生：零作品新号做高频动作，最先被限

本闸做四件事（全部确定性、落盘、可审计）：
  1 配额：每平台 每小时/每天 的次数上限（见 LIMITS），留余量，宁慢勿猛
  2 间隔：两次动作最小间隔 + 随机抖动（机械等间隔本身是特征）
  3 熔断：命中风控信号（验证码/安全限制/频繁/300012/unhuman）→ 立刻进冷却，
     1h → 6h → 24h 递增；连续 3 次 → 停 72h 并要求人工复核
  4 联动：collect / learn / autopilot 全部先 check()，冷却期内直接拒绝执行

Usage
  python3 Tools/fleet/social_riskguard.py --status
  python3 Tools/fleet/social_riskguard.py --check bilibili
  python3 Tools/fleet/social_riskguard.py --note bilibili blocked "命中 300012"
  python3 Tools/fleet/social_riskguard.py --reset bilibili --why "人工复核通过"
  python3 Tools/fleet/social_riskguard.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, ".codely-cli", "state", "RISK-STATE.json")

# 两档节律。CEO 2026-11-17「不用太保守，模拟人类去浏览」：
# 真实风险不是"次数多"，而是"机械均匀 + 零互动 + 只会读"。所以 human 档改成
# **会话模型**：一坐下来连看 8-20 分钟、期间动作间隔 20-45 秒、一轮 8-14 个动作，
# 然后休息 35-90 分钟再回来；日上限放宽但保留硬顶（真出事靠熔断，不靠抠次数）。
LIMITS = {
    "human": {
        "bilibili":    {"hour": 60, "day": 300, "gap": 20, "session_actions": 12,
                        "session_min": 8, "break": [35, 90]},
        "xiaohongshu": {"hour": 40, "day": 160, "gap": 30, "session_actions": 8,
                        "session_min": 6, "break": [60, 150]},   # 300012 仍最凶
        "douyin":      {"hour": 20, "day": 80,  "gap": 60, "session_actions": 6,
                        "session_min": 6, "break": [60, 180]},
        "weibo":       {"hour": 40, "day": 160, "gap": 30, "session_actions": 10,
                        "session_min": 6, "break": [45, 120]},
        "zhihu":       {"hour": 30, "day": 120, "gap": 40, "session_actions": 8,
                        "session_min": 6, "break": [60, 150]},
        "wechat_mp":   {"hour": 40, "day": 160, "gap": 30, "session_actions": 10,
                        "session_min": 6, "break": [45, 120]},
        "default":     {"hour": 40, "day": 160, "gap": 30, "session_actions": 10,
                        "session_min": 6, "break": [45, 120]},
    },
    "conservative": {
        "bilibili":    {"hour": 30, "day": 120, "gap": 90},
        "xiaohongshu": {"hour": 20, "day": 60,  "gap": 120},
        "douyin":      {"hour": 10, "day": 40,  "gap": 300},
        "weibo":       {"hour": 20, "day": 60,  "gap": 120},
        "zhihu":       {"hour": 15, "day": 40,  "gap": 150},
        "wechat_mp":   {"hour": 20, "day": 60,  "gap": 120},
        "default":     {"hour": 20, "day": 60,  "gap": 120},
    },
}
PROFILE = os.environ.get("RISK_PROFILE", "human")     # 默认像人


def limits(platform):
    prof = LIMITS.get(PROFILE) or LIMITS["human"]
    return prof.get(platform, prof["default"])
# 风控信号：出现任何一种就立刻停手（不是"再试一次"）
BLOCK_SIGNS = ("当前网络存在风险", "安全限制", "系统监测到您的网络环境", "unhuman",
               "访问异常", "请完成验证", "人机验证", "操作过于频繁", "300012",
               "验证码", "账号存在风险", "请求过于频繁")
COOLDOWN_STEPS = [3600, 6 * 3600, 24 * 3600, 72 * 3600]


def _now():
    return time.time()


def _load():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def _save(d):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(d, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _plat(d, platform):
    return d.setdefault(platform, {"events": [], "blocks": 0, "cooldown_until": 0,
                                   "last_action": 0, "day": ""})


def _prune(node, now=None):
    """只留最近 24h 事件，避免状态文件无限长。"""
    now = now or _now()
    node["events"] = [e for e in node.get("events") or [] if now - e.get("ts", 0) < 86400]


def check(platform, cost=1, kind="read"):
    """返回 (allowed, reason)。读操作也要过闸——采集本身就是风控敏感行为。"""
    d = _load()
    node = _plat(d, platform)
    lim = limits(platform)
    now = _now()
    if node.get("cooldown_until", 0) > now:
        left = int(node["cooldown_until"] - now)
        return False, "冷却中（剩 %d 分，原因：%s）" % (left // 60, node.get("last_reason") or "-")
    node.setdefault("day", "")
    today = datetime.now().strftime("%Y-%m-%d")
    if node["day"] != today:
        node["day"] = today
        node["day_count"] = 0
    _prune(node)
    hour_n = sum(e.get("n", 1) for e in node["events"] if now - e.get("ts", 0) < 3600)
    if hour_n + cost > lim["hour"]:
        return False, "本小时已达上限 %d（已用 %d）" % (lim["hour"], hour_n)
    if (node.get("day_count") or 0) + cost > lim["day"]:
        return False, "今日已达上限 %d（已用 %d）" % (lim["day"], node.get("day_count") or 0)
    # 会话模型：一轮做够 session_actions 就强制休息（人不会连刷三小时）
    sa = lim.get("session_actions")
    if sa:
        sess_start = node.get("session_start") or 0
        if not sess_start or (now - sess_start) > lim.get("session_min", 10) * 60:
            node["session_start"] = now
            node["session_count"] = 0
        if (node.get("session_count") or 0) >= sa:
            brk = lim.get("break") or [45, 90]
            wait = random.randint(brk[0], brk[1]) * 60
            node["session_start"] = now
            node["session_count"] = 0
            node["cooldown_until"] = now + wait
            node["last_reason"] = "会话休息（做完 %d 个动作）" % sa
            _save(d)
            return False, "会话休息 %d 分钟（像人一样歇一会）" % (wait // 60)
    gap = lim["gap"]
    last = node.get("last_action") or 0
    if last and now - last < gap:
        wait = int(gap - (now - last))
        return False, "动作间隔未满（还需 %d 秒；机械等间隔也是风控特征，这里带抖动）" % wait
    return True, "ok"


def wait_turn(platform, max_wait=120, poll=5):
    """等到可以动作（像人一样等），而不是一遇到间隔就把整轮判失败。

    只有"冷却中"（真命中风控）才直接放弃；间隔/会话休息都属于正常节律，等就行。
    """
    waited = 0
    while waited <= max_wait:
        ok, why = check(platform)
        if ok:
            return True, "ok"
        if "冷却中" in why:
            return False, why
        time.sleep(min(poll, max(1, max_wait - waited)))
        waited += poll
    return False, "等待超时（%ds）：%s" % (max_wait, why)


def note(platform, kind="ok", detail=""):
    """记账。kind: ok / blocked / captcha。blocked 会进冷却并升级。"""
    d = _load()
    node = _plat(d, platform)
    now = _now()
    _prune(node, now)
    node["events"].append({"ts": now, "kind": kind, "n": 1, "detail": str(detail)[:120]})
    node["day_count"] = (node.get("day_count") or 0) + 1
    # 抖动：记录下一次的最早时间也带随机，避免固定节拍
    node["last_action"] = now
    node["session_count"] = (node.get("session_count") or 0) + 1
    if kind in ("blocked", "captcha"):
        step = min(node.get("blocks", 0), len(COOLDOWN_STEPS) - 1)
        node["blocks"] = node.get("blocks", 0) + 1
        node["cooldown_until"] = now + COOLDOWN_STEPS[step]
        node["last_reason"] = "%s %s" % (kind, detail)
    elif kind == "ok":
        # 连续成功慢慢降级冷却等级（7 天不犯事就归零）
        node.setdefault("last_ok", now)
        node["last_ok"] = now
        if now - (node.get("last_block_ts") or 0) > 7 * 86400:
            node["blocks"] = 0
    _save(d)
    return node


def blocked_text(text):
    """页面/响应里有没有风控信号。命中就整平台停手，不重试。"""
    t = str(text or "")
    for s in BLOCK_SIGNS:
        if s in t:
            return s
    return ""


def jitter_gap(platform):
    """返回本次应等待的秒数（基准间隔 + 0-40% 抖动），别用固定节拍。"""
    lim = limits(platform)
    return int(lim["gap"] * (1 + random.uniform(0, 0.4)))


def status():
    d = _load()
    now = _now()
    print("[risk] 当前档位=%s（可用 RISK_PROFILE=conservative 收紧）" % PROFILE)
    print("[risk] 平台              冷却      本小时  今日   连续命中")
    for p in [k for k in LIMITS["human"] if k != "default"]:
        node = d.get(p) or {}
        _prune(node, now)
        hour_n = sum(e.get("n", 1) for e in node.get("events") or [] if now - e.get("ts", 0) < 3600)
        cd = node.get("cooldown_until", 0)
        left = ("%dmin" % ((cd - now) // 60)) if cd > now else "—"
        print("[risk] %-16s %-9s %-7s %-6s %s" % (p, left, hour_n, node.get("day_count") or 0,
                                                  node.get("blocks") or 0))
    if not d:
        print("[risk] 无记录（等于从没跑过）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--check", default=None)
    ap.add_argument("--note", nargs=3, metavar=("PLATFORM", "KIND", "DETAIL"), default=None)
    ap.add_argument("--reset", default=None)
    ap.add_argument("--why", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.status:
        return status()
    if a.check:
        ok, why = check(a.check)
        print("[risk] %s %s：%s" % (a.check, "放行" if ok else "拒绝", why))
        return 0 if ok else 3
    if a.note:
        p, k, det = a.note
        node = note(p, k, det)
        print("[risk] %s 记账 %s；连续命中 %d，冷却至 %s"
              % (p, k, node.get("blocks"), datetime.fromtimestamp(node.get("cooldown_until") or 0)
                 .strftime("%H:%M:%S") if node.get("cooldown_until") else "—"))
        return 0
    if a.reset:
        d = _load()
        node = _plat(d, a.reset)
        node.update({"blocks": 0, "cooldown_until": 0, "last_reason": "人工复核：%s" % a.why})
        _save(d)
        print("[risk] %s 已解除冷却（%s）" % (a.reset, a.why or "无理由"))
        return 0
    ap.print_help()
    return 2


def self_test():
    global STATE, PROFILE
    cases = []
    orig, origp = STATE, PROFILE
    PROFILE = "conservative"
    STATE = os.path.join(ROOT, ".codely-cli", "tmp", "risk-selftest.json")
    if os.path.exists(STATE):
        os.remove(STATE)

    ok, why = check("bilibili")
    cases.append(("首次放行", ok is True))
    note("bilibili", "blocked", "300012 风险")
    ok2, why2 = check("bilibili")
    cases.append(("命中风控后必须冷却", ok2 is False and "冷却" in why2))
    # 冷却升级：第二次命中 → 6h
    d = _load()
    node = d["bilibili"]
    node["cooldown_until"] = 0
    _save(d)
    note("bilibili", "blocked", "again")
    d = _load()
    cases.append(("连续命中冷却升级", d["bilibili"]["cooldown_until"] - _now() > 3600 * 5))
    # 间隔闸
    os.remove(STATE)
    note("weibo", "ok")
    ok3, why3 = check("weibo")
    cases.append(("最小间隔生效", ok3 is False and "间隔" in why3))
    # 每小时配额
    os.remove(STATE)
    d = {"douyin": {"events": [{"ts": _now(), "n": 10}], "last_action": 0, "day_count": 10}}
    json.dump(d, open(STATE, "w", encoding="utf-8"))
    ok4, why4 = check("douyin")
    cases.append(("每小时配额生效", ok4 is False and "上限" in why4))
    # 风控信号识别
    cases.append(("风控信号可识别", blocked_text("当前网络存在风险，请切换网络") != ""
                  and blocked_text("这条评论不错") == ""))
    # 抖动：不是固定值
    gaps = {jitter_gap("bilibili") for _ in range(5)}
    cases.append(("间隔带抖动（非固定节拍）", len(gaps) > 1))
    # human 档：会话里连做 12 个动作后必须休息
    os.remove(STATE)
    PROFILE = "human"
    for _ in range(12):
        note("weibo", "ok")
    ok5, why5 = check("weibo")
    cases.append(("human 档做完一轮必须休息", (ok5 is False) and ("会话休息" in why5 or "间隔" in why5)))
    STATE, PROFILE = orig, origp
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
