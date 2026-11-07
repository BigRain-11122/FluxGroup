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

# 车道可接受的 needs 集合：从 fleet_lane.LANES 自动取（别在这里抄一份——
# 抄一份的结果就是两处各自漂移，之前 MODEL-POLICY 两份各写一个现役就是同一个坑）
def _lane_caps():
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import fleet_lane as fl
        return {n: set(v.get('needs') or []) for n, v in fl.LANES.items()}
    except Exception:
        return {}


LANE_CAPS = _lane_caps()
LANE_NEEDS = set().union(*LANE_CAPS.values()) if LANE_CAPS else {'cpu', 'gpu'}
VOLUME_RE = re.compile(r'^/Volumes/([^/]+)/')


def unmounted_volume(path):
    """路径在 /Volumes/<卷>/ 下而该卷当前没挂载 → 返回卷名，否则 None。"""
    m = VOLUME_RE.match(str(path or '').replace('\\', '/'))
    if not m:
        return None
    return None if os.path.isdir('/Volumes/%s' % m.group(1)) else m.group(1)


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


def cmd_outs(cmd):
    """cmd 里所有 `--out`（链式命令常有多个：中间件 + 最终产物）。"""
    return [norm(m.group(1)) for m in re.finditer(
        r'--out\s+("[^"]+"|\'[^\']+\'|\S+)', cmd or '')]


def cmd_out(cmd):
    outs = cmd_outs(cmd)
    return outs[0] if outs else None


def _tool_literals(cmd, root):
    """取 cmd 里那个工具源码中的 .md/.csv 字符串字面量（含模板）。"""
    m = re.search(r'([\w./\\-]+\.py)', cmd or '')
    if not m:
        return []
    path = os.path.join(root, m.group(1).replace('\\', '/'))
    try:
        src = open(path, encoding='utf-8', errors='replace').read(400000)
    except Exception:
        return []
    return re.findall(r'''["']([^"'\n]{2,120}\.(?:md|csv))["']''', src)


def name_is_derived(cmd, deliverable, root):
    """没写 --out 但工具按模板拼文件名（如 'triage-%s-%s.md'）时，也算它产得出交付物。

    否则契约检查会把能正常跑的真卡判成 SPEC-IMPOSSIBLE——假红和假绿一样伤信任。
    """
    base = os.path.basename(norm(deliverable))
    if not base:
        return False
    for lit in _tool_literals(cmd, root):
        parts = re.split(r'(%s|%d|\{[^}]*\}|\*)', lit)
        pat = ''.join('.*' if re.fullmatch(r'%s|%d|\{[^}]*\}|\*', p) else re.escape(p)
                      for p in parts)
        if re.fullmatch(pat, base, re.I):
            return True
    return False


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
            outs = cmd_outs(r.get('cmd'))
            o = outs[0] if outs else None
            d = norm(r.get('deliverable'))
            # R1（链式命令允许多个 --out：中间件 + 最终产物，交付物命中任一个即可）
            if outs and d and d not in outs and not r.get('deliverable_note'):
                v.append({'rule': 'OUT-MISMATCH', 'src': src, 'id': rid,
                          'cmd_out': o, 'deliverable': d,
                          'why': 'cmd 产出的路径与卡的 deliverable 不同 ⇒ 永远 FAIL 重试'})
                continue
            # R2
            if d.lower().endswith(('.md', '.csv')) and not o and \
                    any(w in (r.get('accept') or '') for w in HUMAN_WORDS) and \
                    not name_is_derived(r.get('cmd'), d, root) and \
                    'cph4/fleet/queue-receipts/' not in d:
                # queue-receipts 下的交付物按约定就是执行机写的回执（如 line_triage 按
                # 行名拼文件名），accept 里出现"写明"只是在描述回执内容，不是要人判。
                # 实测假红：两张子仓体检卡因 accept 含"写明"被连续 3 轮判不可满足。
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
                # 不 continue：一张卡常常同时犯多条（非法 needs + 钉错机器 + 输入在未挂载卷），
                # 只报第一条会让人修完一层又发现一层。
            # R5 NODE-CAP-MISMATCH（2026-11-07 实锚）：needs="gpu-vision" 且钉在 bm-m——
            # 那台机只有 cpu。合法 needs + 错误的机器，同样是"队列有活、永远不派"。
            for n in (r.get('hard_nodes') or r.get('nodes') or []):
                caps = LANE_CAPS.get(n)
                if caps is not None and nd not in caps:
                    v.append({'rule': 'NODE-CAP-MISMATCH', 'src': src, 'id': rid,
                              'needs': nd, 'node': n, 'node_caps': sorted(caps),
                              'why': '钉在 %s 但它没有 %s 能力 ⇒ 该卡永远不派' % (n, nd)})
                    break
            # R6 DEAD-INPUT（2026-11-07 实锚）：输入在未挂载的移动硬盘上，卡却挂着 OPEN，
            # 看起来是"供给"，实际谁都跑不了；应当标 BLOCKED 并写清等什么。
            for p in [r.get('deliverable')] + list(r.get('requires') or []):
                vol = unmounted_volume(p)
                if vol:
                    v.append({'rule': 'DEAD-INPUT', 'src': src, 'id': rid,
                              'volume': vol, 'path': str(p)[:80],
                              'why': '输入/产物在未挂载的卷 %s 上 ⇒ 应标 BLOCKED 而不是 OPEN' % vol})
                    break
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