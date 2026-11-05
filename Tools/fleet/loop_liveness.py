#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""loop_liveness.py - 闭环存活检查器（CEO 2026-11-06 令「要有自我更新迭代的能力，闭环的能力，
不再只是空转规则口嗨」）。

宣言的机制 ≠ 活着的机制。本工具把每个已宣布的机制变成持续验证的事实：
静态探针（代码在库）+ 工件探针（正身存在）+ 规则探针（WORK-RULES 行在册）→ 一份
LOOP-HEALTH 回执（rc=0 全活 / rc=1 有 BROKEN）。BROKEN 项在回执里逐条点名——回执走
agent 的 own-delta 自动上链=全队可见，谁冲掉了机制当场现形。

首跑实锚（2026-11-06）：本工具开发当晚就抓到两起真回归——
  1) need-work 机制被昨夜 self_dispatch 重写整段删除（宣布过+主控备单制建立在它之上）；
  2) OS 闸拦截后直接 return True=投毒派单吞死车道（z01 试点在队列躺死数小时）。

用法（在任一节点克隆根跑，只读不改库）：
  python Tools/fleet/loop_liveness.py --node <bm-x> [--root <repo>]
rc: 0=全部机制存活；1=存在 BROKEN（回执里逐条列出与证据）。
"""
import argparse
import json
import os
import subprocess
import time


def _read_origin(root, path):
    r = subprocess.run(["git", "-C", root, "show", "origin/main:" + path],
                       capture_output=True, timeout=90)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def _git_exists(root, path):
    r = subprocess.run(["git", "-C", root, "cat-file", "-e", "origin/main:" + path],
                       capture_output=True, timeout=60)
    return r.returncode == 0


PROBES = [
    {"loop": "need-work 机制（没活喊话）", "kind": "code",
     "file": "Tools/fleet/lane_agent.py",
     "require_all": ["def _need_work_flag", "_need_work_flag(root, node, True",
                     "_need_work_flag(root, node, False"],
     "why": "CEO 11-04 令「没活就赶紧找主控要」；主控备单制按此旗标 P0 响应",
     "regression": "2026-11-06 实锚：被 self_dispatch 整段重写冲掉，宣布过的机制无人验证存活"},
    {"loop": "OS 投毒不吞车道", "kind": "code",
     "file": "Tools/fleet/lane_agent.py",
     "require_all": ["after OS-MISMATCH, no eligible fallback"],
     "why": "本机跑不了的派单不许饿死申报池（11-06 实锚：DOCS 卡占死 bm-b 车道数小时、z01 躺死）"},
    {"loop": "回执自动上链 v3（--sparse -f）", "kind": "code",
     "file": "Tools/fleet/agent.py",
     "require_all": ["--sparse", '"-f"', "own deltas"],
     "why": "ff-only 拉取带脏工作树成功=自有面永不提交（60+ 回执滞留一整天实锚）",
     "regression": "v1 撞中文八进制、v2 撞稀疏锥外+ignore——v3 后由本工具盯防再退化"},
    {"loop": "五道机器闸（OS/输入/二进制）", "kind": "code",
     "file": "Tools/fleet/fleet_lane.py",
     "require_all": ["def infer_node_os", "def implicit_inputs", "def requires_bin_ok"],
     "why": "11-03 假失败三根因的根治件"},
    {"loop": "钉机执法（hard_nodes）", "kind": "code",
     "file": "Tools/fleet/lane_agent.py",
     "require_all": ["hard_nodes"],
     "why": "11-03 偷卡案根治件（--node bm-c 在 bm-b 跑完实锚）"},
    {"loop": "pins-alive 守卫（读不到主控状态≠全员失联）", "kind": "code",
     "file": "Tools/fleet/lane_agent.py",
     "require_all": ["if not lanes:", "return False"] if False else
                    ["_pins_stale"],
     "why": "稀疏克隆偷卡案根治件"},
    {"loop": "DE-AI-SPEC 出厂总闸", "kind": "artifact",
     "file": "cph4/fleet/quality/DE-AI-SPEC-v1.md",
     "why": "CEO 根本要求令正身（高质量+去AI感 28 条）"},
    {"loop": "互通索引（cross-talk）", "kind": "artifact",
     "file": "cph4/fleet/CROSS-TALK-INDEX.json",
     "why": "CEO 11-05 互通令正身"},
    {"loop": "总账正身", "kind": "artifact",
     "file": "cph4/fleet/BACKLOG-LEDGER-20261103.md",
     "why": "三天复盘与执法台账"},
    {"loop": "主控备单制（R-NEEDWORK）", "kind": "workrules",
     "id": "R-NEEDWORK-20261104-001",
     "why": "主控侧「早早备好工单」执行行"},
    {"loop": "主控日扫互通（R-CROSSTALK-SWEEP）", "kind": "workrules",
     "id": "R-CROSSTALK-SWEEP-20261105-001",
     "why": "主控侧分诊腿（help→派单/judgment→广播/blocker→核销）"},
    {"loop": "回执卫生基线表", "kind": "artifact",
     "file": "cph4/fleet/receipt-attrib-20261103.json",
     "why": "全量回执体检基座（缺 rc=0/缺 class=1）"},
]


def run_probes(root):
    results, broken = [], []
    cache = {}
    for p in PROBES:
        ok, evidence = False, ""
        if p["kind"] == "code":
            if p["file"] not in cache:
                cache[p["file"]] = _read_origin(root, p["file"]) or ""
            text = cache[p["file"]]
            missing = [s for s in p["require_all"] if s not in text]
            ok = not missing
            evidence = ("all markers present" if ok else
                        "MISSING in %s: %s" % (p["file"], missing))
        elif p["kind"] == "artifact":
            ok = _git_exists(root, p["file"])
            evidence = "on origin" if ok else "ABSENT on origin: %s" % p["file"]
        elif p["kind"] == "workrules":
            wr = cache.get("WORK-RULES") or _read_origin(root, "cph4/fleet/WORK-RULES.jsonl") or ""
            cache["WORK-RULES"] = wr
            ok = p["id"] in wr
            evidence = "row in WORK-RULES" if ok else "ROW GONE from WORK-RULES: %s" % p["id"]
        r = {"loop": p["loop"], "alive": ok, "evidence": evidence, "why": p.get("why", "")}
        if p.get("regression"):
            r["known_regression"] = p["regression"]
        results.append(r)
        if not ok:
            broken.append(r)
    return results, broken


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    root = a.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    results, broken = run_probes(root)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "node": a.node,
           "verdict": "ALIVE" if not broken else "BROKEN",
           "alive": len(results) - len(broken), "total": len(results),
           "broken": [b["loop"] for b in broken], "probes": results,
           "note": "闭环检查器：宣言的机制必须持续验证存活；BROKEN 项逐条点名于 probes"}
    out = a.out or os.path.join(root, "cph4", "fleet", "queue-receipts",
                                "loop-liveness-%s-%s.json" % (a.node, time.strftime("%Y%m%d")))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("LOOP-LIVENESS %s %s: %d/%d alive" % (a.node, rec["verdict"],
                                                rec["alive"], rec["total"]))
    for b in broken:
        print("  BROKEN %s :: %s" % (b["loop"], b["evidence"]))
    return 1 if broken else 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))