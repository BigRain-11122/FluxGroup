#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""银行自动补料：把"能机器验的体检活"按机器能力写进 work-bank，让空闲机永远有活。

为什么要有这件（2026-11-03 实测）：workgen 的规则是"每台在线机保底 3 张"，
但 work-bank 五个文件全是 0 项 → 队列没料 → 机器空转。此前靠人手工往 bank 塞，
人一停就断粮。补料的正确来源不是"编活"，是**用现成的闸/体检工具生成兜底卡**：
产物落 cph4/fleet/queue-receipts/（受 git 管），有 accept，可机器复核。

约束：
  - 只补"只读/体检"类活，不补生产活（生产由工序表 line_plan 负责，重复补会双重派卡）
  - 幂等：同 id 已在队列/积压则不补；产物已在盘则不补
  - 每台机最多补到 FLOOR 张，不灌水

用法：
  python3 Tools/fleet/bank_autofill.py --root . [--dry-run]
"""

import argparse
import json
import os
import sys
import time

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLOOR = 3
BANK_DIR = os.path.join("cph4", "fleet", "work-bank")
Q = os.path.join("cph4", "fleet", "PRODUCTION-QUEUE.jsonl")
B = os.path.join("cph4", "fleet", "PRODUCTION-BACKLOG.jsonl")
RECEIPTS = os.path.join("cph4", "fleet", "queue-receipts")

# 体检活目录：key=tool 路径，value=(标题, 参数模板, 产物名, accept)
# 全部只读或只写 queue-receipts；needs=cpu 表示不占 GPU、不加载大模型。
CHECKS = {
    "receipt": ("回执卫生体检（rc 缺失/error_class 缺失出表）",
                ["Tools/fleet/receipt_attrib.py", "--out", "cph4/fleet/queue-receipts/receipt-attrib-{date}.json"],
                "receipt-attrib-{date}.json",
                "verdict 字段在盘；GAPS 时列出缺 rc 与缺 error_class 的张数"),
    "skills": ("技能库质检出表（A/B 分级+死指针）",
               ["Tools/fleet/skill_check.py"],
               "state/skills-check.json",
               "state/skills-check.json 的 ts 为当日；A/B 计数变化写明"),
    "canon": ("五线认知基座一致性（工序段 id 与表同源）",
              ["Tools/fleet/line_canon.py", "--all"],
              None,
              "rc∈{0,2}；rc=2 时列出不一致的线段"),
    "dupes": ("重复派单向量重扫",
              ["Tools/fleet/semantic_dupes.py", "--json", "cph4/fleet/queue-receipts/dupes-scan-{date}.json"],
              "dupes-scan-{date}.json",
              "输出重复对清单；与前次相比新增对数量写明"),
    "asset": ("资产训练环境体检（能不能烧）",
              ["Tools/fleet/asset_env_check.py", "--json", "cph4/fleet/queue-receipts/asset-env-{date}.json"],
              "asset-env-{date}.json",
              "routes_ok 非空；缺什么写明"),
}

# 机器能力 → 能跑的体检活（bm-d 未入网不列）
NODE_CHECKS = {
    "bm-m": ["receipt", "skills", "dupes"],
    "bm-a": ["canon", "receipt", "skills"],
    "bm-b": ["asset", "receipt"],
    "bm-c": ["asset", "dupes"],
}


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def held(root, node):
    rows = read_jsonl(os.path.join(root, Q)) + read_jsonl(os.path.join(root, B))
    ids = set()
    for r in rows:
        if r.get("state") in ("OPEN", "RUNNING", "READY"):
            if node in (r.get("nodes") or []) or r.get("owner") == node:
                ids.add(r.get("id"))
    return ids


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    root = a.root
    date = time.strftime("%Y%m%d")
    added, skipped = [], 0
    for node, keys in NODE_CHECKS.items():
        lf = os.path.join(root, "cph4", "fleet", "lanes", "%s.json" % node)
        if not os.path.exists(lf):
            continue
        held_ids = held(root, node)
        need = FLOOR - len(held_ids)
        if need <= 0:
            continue
        bankp = os.path.join(root, BANK_DIR, "%s-cpu-bank.json" % node)
        bank = {}
        if os.path.exists(bankp):
            try:
                bank = json.load(open(bankp, encoding="utf-8"))
            except Exception:
                bank = {}
        jobs = bank.setdefault("jobs", [])
        # 银行里的"尸体"：产物已在盘却仍标 pending 的条目会虚占保底名额，
        # 使 need<=0 而机器实际无活可跑（2026-11-03 实测 bm-m held=1、pending 却满）。
        # 这里先把它们销账，再算缺口。
        for j in jobs:
            dp = j.get("deliverable") or ""
            if j.get("status") == "pending" and dp and os.path.exists(
                    dp if os.path.isabs(dp) else os.path.join(root, dp)):
                j["status"] = "done"
        pending = [j for j in jobs if j.get("status") == "pending"]
        need -= len(pending)
        if need <= 0:
            continue
        for key in keys:
            if need <= 0:
                break
            title, cmd, deliv, accept = CHECKS[key]
            cid = "CHK-%s-%s" % (key.upper(), date)
            if cid in held_ids or any(j.get("id") == cid for j in jobs):
                skipped += 1
                continue
            dpath = None
            if deliv:
                dpath = os.path.join("cph4", "fleet", deliv.format(date=date))
                if os.path.exists(os.path.join(root, dpath)):
                    skipped += 1
                    continue
            jobs.append({
                "id": cid,
                "title": "%s（%s 兜底体检）" % (title, node),
                "cmd": "python3 " + " ".join(x.format(date=date) for x in cmd),
                "deliverable": dpath or "",
                "accept": accept,
                "needs": "cpu", "prio": "P2", "day_ok": True,
                "status": "pending", "est_gb": 0,
                "why": "bank_autofill: 空闲机兜底体检活，产物落 queue-receipts",
            })
            added.append("%s -> %s" % (cid, node))
            need -= 1
        if not a.dry_run:
            os.makedirs(os.path.dirname(bankp), exist_ok=True)
            with open(bankp, "w", encoding="utf-8") as f:
                json.dump(bank, f, ensure_ascii=False, indent=1)
    print("bank_autofill added=%d skipped=%d%s" % (len(added), skipped, " (dry-run)" if a.dry_run else ""))
    for x in added:
        print("  + " + x)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))