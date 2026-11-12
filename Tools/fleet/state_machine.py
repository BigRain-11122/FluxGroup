#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_machine.py - 卡状态机的唯一权威（读 `cph4/fleet/STATE-MACHINE-v1.json`）。

2026-11-12 立。此前两套终态定义并存：
  station_shards.TERMINAL    = (DONE, CANCELLED, ARCHIVED, FAILED)
  station_drive.DONE_STATES  = (DONE, CANCELLED, SHELVED)
ARCHIVED 与 SHELVED 的行为正好相反；而 FAILED/BLOCKED/REVISE/PENDING_* 等 8 种
状态既不被执行、也不被重建 —— 卡进了就出不来（评审团判"返工"的卡直接躺死）。

本模块只做三件事：判定合法迁移、给出可去状态、把"哪些算终态/可执行"从一处派生。
代码里不许再各写一份状态清单（gate-rigor 第 4 问：唯一判据）。

用法：
  python3 Tools/fleet/state_machine.py                 # 打印状态机
  python3 Tools/fleet/state_machine.py --check <文件>  # 审计一份 jsonl 分片的非法迁移
  python3 Tools/fleet/state_machine.py --self-test
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "STATE-MACHINE-v1.json")

_CACHE = {}


def spec():
    if "v" not in _CACHE:
        with open(SPEC, encoding="utf-8-sig") as f:
            _CACHE["v"] = json.load(f)
    return _CACHE["v"]


def states():
    return spec()["states"]


def kind(state):
    return (states().get(state) or {}).get("kind")


def by_kind(*kinds):
    return tuple(s for s, v in states().items() if v.get("kind") in kinds)


def terminal():
    """终态：不再执行、不再重建。"""
    return by_kind("terminal")


def live():
    """可执行状态（自驱只领 OPEN，但 live 表示"这张卡还在链路里等着跑"）。"""
    return by_kind("live")


def closed():
    """"这件事已经结束"的集合：终态 + 人工停放。

    对应旧 station_drive.DONE_STATES（DONE/CANCELLED/SHELVED）的语义升级：
    停放件也不再重建，否则会被反复派同一张卡。
    """
    return by_kind("terminal", "parked")


def rebuildable():
    """"这张卡不再挡重建"的集合（supply 用它算 open_keys）。

    与 closed() 不同：BLOCKED 属 parked 但**挡重建**（缺输入的卡每轮重建会刷屏）。
    2026-11-12 首版取值与原 station_drive.DONE_STATES 完全一致，保证只做单一权威、
    不改行为；批次4 再让 FAILED/REVISE 可重建（带 attempt+1 与退避）。
    """
    return tuple(s for s, v in states().items() if v.get("rebuild"))


def can_transition(old, new, strict=True):
    """返回 (ok, why)。strict=False 时未知状态按放行处理（只用于读历史数据）。"""
    st = states()
    if old == new:
        return True, "同状态（幂等写入，允许）"
    if old not in st:
        return (False, "未知旧状态：%s" % old) if strict else (True, "未知旧状态，放行")
    if new not in st:
        return (False, "未知新状态：%s" % new) if strict else (True, "未知新状态，放行")
    allowed = st[old].get("can_go") or []
    if new in allowed:
        return True, "%s -> %s（%s）" % (old, new, (st[old].get("who") or {}).get(new, "见状态机"))
    return False, "%s 不允许直接到 %s（允许：%s）" % (old, new, ", ".join(allowed) or "无（终态）")


def next_states(state):
    return list((states().get(state) or {}).get("can_go") or [])


def self_test():
    """期望值独立写死：不拿本文件自身结果当答案（改状态机必须同时改这里）。"""
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    chk("12 种状态齐全", len(states()) == 12, sorted(states()))
    chk("终态 = DONE/CANCELLED/ARCHIVED", set(terminal()) == {"DONE", "CANCELLED", "ARCHIVED"}, terminal())
    chk("closed = 终态 + BLOCKED/SHELVED",
        set(closed()) == {"DONE", "CANCELLED", "ARCHIVED", "BLOCKED", "SHELVED"}, closed())
    chk("live 含 OPEN/RUNNING/FAILED", {"OPEN", "RUNNING", "FAILED"} <= set(live()), live())

    # 正例
    chk("OPEN -> RUNNING 合法", can_transition("OPEN", "RUNNING")[0])
    chk("RUNNING -> DONE 合法", can_transition("RUNNING", "DONE")[0])
    chk("RUNNING -> REVISE 合法（评审团返工）", can_transition("RUNNING", "REVISE")[0])
    chk("REVISE -> OPEN 合法（带退避重排）", can_transition("REVISE", "OPEN")[0])
    chk("FAILED -> OPEN 合法（重试路径）", can_transition("FAILED", "OPEN")[0])

    # 负控：这四条是以前真发生过的死卡/回跳
    chk("负控：DONE -> RUNNING 必须拒绝（终态回跳）", not can_transition("DONE", "RUNNING")[0])
    chk("负控：ARCHIVED -> OPEN 必须拒绝（归档只读）", not can_transition("ARCHIVED", "OPEN")[0])
    chk("负控：OPEN -> DONE 必须拒绝（没跑就完成）", not can_transition("OPEN", "DONE")[0])
    chk("负控：RUNNING -> SHELVED 必须拒绝（运行中不许停放）", not can_transition("RUNNING", "SHELVED")[0])

    # 每个非终态都必须有出路，否则就是死卡
    dead = [s for s, v in states().items() if v.get("kind") != "terminal" and not v.get("can_go")]
    chk("非终态都有出路（无死卡）", not dead, dead)

    # 未知状态
    chk("负控：未知状态在严格模式下拒绝", not can_transition("WAT", "OPEN")[0])
    chk("宽松模式放行未知状态（只读历史用）", can_transition("WAT", "OPEN", strict=False)[0])
    print("[state_machine] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def check_file(path):
    """审计一份分片：同一个 id 出现多次时，检查相邻状态迁移是否合法。"""
    last = {}
    bad = []
    n = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            n += 1
            cid = str(r.get("id") or "")
            st = str(r.get("state") or "")
            if cid in last and last[cid] != st:
                okk, why = can_transition(last[cid], st, strict=False)
                if not okk:
                    bad.append({"line": i, "id": cid, "why": why})
            last[cid] = st
    return {"rows": n, "illegal": bad[:20], "count": len(bad)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", metavar="JSONL", help="审计分片里的非法状态迁移")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.check:
        r = check_file(a.check)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=1))
        else:
            print("%s：%d 行，非法迁移 %d 条" % (a.check, r["rows"], r["count"]))
            for b in r["illegal"]:
                print("  行 %d %s：%s" % (b["line"], b["id"], b["why"]))
        return 1 if r["count"] else 0
    if a.json:
        print(json.dumps(spec(), ensure_ascii=False, indent=1))
    else:
        print("%-15s %-9s %s" % ("状态", "类别", "可去"))
        for s, v in states().items():
            print("%-15s %-9s %s" % (s, v.get("kind"), ", ".join(v.get("can_go") or []) or "—"))
        print("\n终态：%s" % ", ".join(terminal()))
        print("已结束（终态+停放）：%s" % ", ".join(closed()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
