#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""card_contract_check.py — queue-card contract lint (machine-judged).

Why: 2026-11-04 01:0x-01:4x bm-a 实测事故 —— 卡 biggame-playable-2026-11-03 的 cmd 是
`game_pack_scan.py --out ...-r2.json`，而它的 deliverable 写成 `game-playable-...md`。
cmd 永远产不出 deliverable ⇒ 每 ~5 分钟被 backlog_fill 重发一次 ⇒ 40 分钟 6 轮
"job(...): artifact" 提交 + 一次未完成 rebase + 队列冲突标记落地。

所以"cmd 的产物"和"卡的交付物"必须是同一个路径，这条能机判，就不该靠人看。

Rules
  R1 OUT-MISMATCH   cmd 里有 `--out <p>` 时，<p> 必须等于 deliverable（规范化后）。
                    例外：卡上写 `deliverable_note`（说明为何不同，如"cmd 出中间件，
                    交付物由下一段合成"）。
  R2 SPEC-IMPOSSIBLE 卡上 deliverable 是 .md/.csv 但没有 cmd 写它的路径，且 accept 要求
                    人裁判定（含"写明/判定/选/评分/评审"等词）→ 提示：人决件不该入机器队列。
  R3 LEDGER-LAG     OPEN 卡的 deliverable 已存在且内容是真交付（非 BLOCKED/SKIPPED/GAPS）
                    → 应 close（台账滞后）。

Usage:
  python Tools/fleet/card_contract_check.py [--root DIR] [--json OUT]

Exit: 0 = clean; 1 = violations found; 2 = usage/IO error.
"""
import argparse
import json
import os
import re
import sys

QUEUE = os.path.join('cph4', 'fleet', 'PRODUCTION-QUEUE.jsonl')
BACKLOG = os.path.join('cph4', 'fleet', 'PRODUCTION-BACKLOG.jsonl')

HUMAN_WORDS = ('写明', '判定', '选款', '选出', '评分', '评审', '签名', '评价')
NOT_DELIVERED = ('BLOCKED', 'SKIPPED', 'GAPS', 'FAIL', 'ERROR')

# 车道可接受的 needs 集合（取自 fleet_lane.LANES 的并集；写卡的人不能随手发明新值）
LANE_NEEDS = {'cpu', 'gpu'}


def norm(p):
    return (p or '').strip().strip('"\'').replace('\\', '/').lstrip('./')


def load_jsonl(path):
    rows, bad = [], 0
    if not os.path.exists(path):
        return rows, bad
    for line in open(path, encoding='utf-8-sig', errors='replace'):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            bad += 1
    return rows, bad


def cmd_out(cmd):
    m = re.search(r'--out\s+("[^"]+"|\'[^\']+\'|\S+)', cmd or '')
    return norm(m.group(1)) if m else None


def deliverable_is_real(path):
    """存在 && 内容不是拒绝回执。解析不了就当缺席（不让坏文件假绿）。"""
    if not path or not os.path.exists(path):
        return False
    if path.lower().endswith(('.md', '.txt', '.csv')):
        head = open(path, encoding='utf-8', errors='replace').read(600)
        return not any(k in head.upper() for k in ('BLOCKED', 'SKIPPED', 'GAPS'))
    if path.lower().endswith('.json'):
        try:
            d = json.load(open(path, encoding='utf-8-sig'))
        except Exception:
            return False
        if not isinstance(d, dict):
            return True
        for k in ('verdict', 'status', 'state', 'outcome'):
            v = str(d.get(k) or '').upper()
            if any(v.startswith(x) for x in NOT_DELIVERED):
                return False
        return True
    return True


def check(root):
    v = []
    bad_lines = {}
    for src, rel in (('BACKLOG', BACKLOG), ('QUEUE', QUEUE)):
        rows, bad = load_jsonl(os.path.join(root, rel))
        if bad:
            bad_lines[rel] = bad
        for r in rows:
            rid = r.get('id') or '?'
            st = r.get('state')
            if src == 'BACKLOG' and st not in (None, 'READY'):
                continue
            if src == 'QUEUE' and st not in ('OPEN', 'RUNNING'):
                continue
            o = cmd_out(r.get('cmd'))
            d = norm(r.get('deliverable'))
            # R1
            if o and d and o != d and not r.get('deliverable_note'):
                v.append({'rule': 'OUT-MISMATCH', 'src': src, 'id': rid,
                          'cmd_out': o, 'deliverable': d,
                          'why': 'cmd 产出的路径与卡的 deliverable 不同 ⇒ 永远 FAIL 重试'})
                continue
            # R2
            if d.lower().endswith(('.md', '.csv')) and not o and \
                    any(w in (r.get('accept') or '') for w in HUMAN_WORDS):
                v.append({'rule': 'SPEC-IMPOSSIBLE', 'src': src, 'id': rid,
                          'deliverable': d,
                          'why': '交付物需人裁判定而 cmd 不产出它 ⇒ 机器队列不可满足'})
                continue
            # R3
            if src == 'QUEUE' and st == 'OPEN' and deliverable_is_real(os.path.join(root, d)):
                v.append({'rule': 'LEDGER-LAG', 'src': src, 'id': rid,
                          'deliverable': d,
                          'why': '交付物已在盘且是真交付，卡仍 OPEN'})
                continue
            # R4 NEEDS-INVISIBLE（2026-11-07 实锚）：needs 写成 "net" 的卡对派单器永久不可见
            # ——write_lane_files 只认 needs ∈ 车道 allowed(needs)，不在集合里的卡既不进 lane
            # 也不报警，症状是"队列有活、机器空闲"。非法 needs 必须在投卡时就被拦下。
            nd = r.get('needs') or 'cpu'
            if nd not in LANE_NEEDS:
                v.append({'rule': 'NEEDS-INVISIBLE', 'src': src, 'id': rid,
                          'needs': nd, 'allowed': sorted(LANE_NEEDS),
                          'why': 'needs 不在车道可接受集合内 ⇒ 该卡永远不会被派出去'})
    return v, bad_lines


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--json')
    a = ap.parse_args(argv[1:])
    root = os.path.abspath(a.root)
    v, bad = check(root)
    if bad:
        print('WARN unparsable lines: %s' % bad)
    if not v:
        print('CARD-CONTRACT PASS (0 violations)')
        return 0
    print('CARD-CONTRACT VIOLATIONS: %d' % len(v))
    for x in v:
        print('  [%s] %-10s %-40s %s' % (x['rule'], x['src'], x['id'], x['why']))
    if a.json:
        json.dump({'violations': v, 'bad_lines': bad}, open(a.json, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))