#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""account_plan.py — 开号清单与平台轮转登记的对账器。

存在理由：开号清单（ACCOUNT-OPENING-v1.json）和轮转登记（res_alloc.PLATFORMS）
是两份事实。任一方改了另一方忘了改，就会出现两种事故：
  ① 号还没开，轮转却给它排了班 → 每天空跑一次浏览器，日志里看起来"在采集"；
  ② 号开了，轮转还是 0 权重 → 永远不排班，等于白开。
本器只做一件事：把两份对起来，不一致就红。

判据（三个方向都要对）：
  A. 开号清单里每个 id 必须在轮转登记里存在
  B. state=need-account / need-login 的平台，轮转权重必须 0（没号就不许排班）
  C. 轮转登记里 state 属于 live/read/building 的平台，清单里必须列（有号的必须进清单）

用法：
  python3 Tools/fleet/account_plan.py --check
  python3 Tools/fleet/account_plan.py --status
  python3 Tools/fleet/account_plan.py --self-test
退出码：0 一致 / 1 有漂移 / 2 文件读不到
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PLAN = os.path.join(ROOT, "cph4", "fleet", "social", "ACCOUNT-OPENING-v1.json")

LIVE_STATES = ("live", "read", "building")   # 有号的或已验可读的
READ_OK = "ok"
READ_BLOCKED = ("need-login", "untested")     # 读都读不到 → 不许排班
READ_PENDING = ("need-login",)               # 需要登录后才能读


def _reg():
    sys.path.insert(0, HERE)
    import res_alloc
    return {p["id"]: p for p in res_alloc.PLATFORMS}


def _plan(path=None):
    with open(path or PLAN, encoding="utf-8") as f:
        d = json.load(f)
    return {p["id"]: p for p in d.get("platforms") or []}


def check(plan=None, reg=None):
    """对账。返回 (ok, 问题列表, 明细行)。

    三个方向：
      A. id 必须两边都有（同一个平台两套名字＝排班与清单各说各话）
      B. read=ok 必须有权重；read 在 need-login/untested 必须权重 0（读都读不到就别排班）
      C. 轮转里 state=live/read/building 的平台必须出现在清单
    注意 publish 不参与权重判定——匿名可读 ≠ 能发；能发要账号，进 publish 那一列单独管。
    """
    plan = plan if plan is not None else _plan()
    reg = reg if reg is not None else _reg()
    bad, rows = [], []

    for pid, p in plan.items():
        if pid not in reg:
            bad.append("A: 清单有 %s，轮转登记没有（开了号也不会进班）" % pid)
            continue
        r = reg[pid]
        w = int(r.get("weight") or 0)
        rd = p.get("read")
        if rd == READ_OK and w <= 0:
            bad.append("B: %s 读取已验（read=ok），但轮转权重 0（永远不排班）" % pid)
        if rd in READ_BLOCKED and w > 0:
            bad.append("B: %s read=%s（读不到），却有权重 %d（会空跑）" % (pid, rd, w))
        rows.append("%-16s read=%-11s publish=%-12s 轮转=%-12s 权重=%-2d %s"
                    % (pid, rd, p.get("publish"), r.get("state"), w, (r.get("note") or "")[:22]))

    for pid, r in reg.items():
        if r.get("state") in LIVE_STATES and pid not in plan:
            bad.append("C: 轮转里 %s 是 %s（有号的），清单里没列" % (pid, r.get("state")))

    return (not bad), bad, rows


def status():
    ok, bad, rows = check()
    print("开号清单 ↔ 轮转登记 对账  %s" % ("一致" if ok else "有漂移"))
    for r in rows:
        print("  " + r)
    for b in bad:
        print("  ✗ " + b)
    return 0 if ok else 1


def self_test():
    """负控：造三种漂移必须各自判红；正常数据必须判绿。"""
    cases = []
    plan = {"a": {"id": "a", "read": "ok", "publish": "ok"},
            "b": {"id": "b", "read": "need-login", "publish": "need-account"}}
    reg = {"a": {"id": "a", "state": "live", "weight": 5},
           "b": {"id": "b", "state": "need-login", "weight": 0}}
    cases.append(("正常：读得到就排班、读不到不排 → 绿", check(plan, reg)[0] is True))

    reg1 = {"a": {"id": "a", "state": "live", "weight": 5},
            "b": {"id": "b", "state": "need-login", "weight": 3}}
    cases.append(("负控1 读不到却排班 → 红",
                  any(x.startswith("B:") for x in check(plan, reg1)[1])))

    reg2 = {"a": {"id": "a", "state": "live", "weight": 0},
            "b": {"id": "b", "state": "need-login", "weight": 0}}
    cases.append(("负控2 读得到却不排班 → 红",
                  any(x.startswith("B:") for x in check(plan, reg2)[1])))

    reg3 = reg
    plan3 = {"a": {"id": "a", "read": "ok", "publish": "ok"},
             "ghost": {"id": "ghost", "read": "ok", "publish": "need-account"}}
    cases.append(("负控3 清单里有、登记里没有 → 红",
                  any(x.startswith("A:") for x in check(plan3, reg3)[1])))

    # 负控5：能发不能混进权重判据——publish=need-account 但 read=ok 必须判绿
    plan5 = {"a": {"id": "a", "read": "ok", "publish": "need-account"}}
    reg5 = {"a": {"id": "a", "state": "read", "weight": 2}}
    cases.append(("负控5 能读不能发 → 仍应排班（绿）", check(plan5, reg5)[0] is True))

    reg4 = dict(reg, c={"id": "c", "state": "live", "weight": 2})
    cases.append(("负控4 有号却没列清单 → 红",
                  any(x.startswith("C:") for x in check(plan, reg4)[1])))

    # 真数据也必须能跑（不能只在假数据上绿）
    try:
        ok, bad, _ = check()
        cases.append(("真数据可读并对账", isinstance(ok, bool)))
    except Exception:
        cases.append(("真数据可读并对账", False))

    n = sum(1 for _, v in cases if v)
    for name, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", name))
    print("[self-test] %d/%d %s" % (n, len(cases), "PASS" if n == len(cases) else "FAIL"))
    return 0 if n == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return status()


if __name__ == "__main__":
    sys.exit(main())
