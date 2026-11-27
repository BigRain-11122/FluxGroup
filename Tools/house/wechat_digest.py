# -*- coding: utf-8 -*-
"""把 wechat-index.jsonl 导出成可读摘要（落盘 UTF-8，避开控制台编码）"""
import argparse
import json
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IDX = os.path.join(ROOT, 'house', 'realestate', 'wechat-index.jsonl')
OUT = os.path.join(ROOT, 'house', 'realestate', 'logs', 'wechat-digest.md')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--since', default='2026-10-15')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()

    rows = []
    with open(IDX, encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get('date', '') >= args.since:
                rows.append(r)

    rows.sort(key=lambda r: (r.get('date', ''), r.get('account', '')), reverse=True)
    by_acc = defaultdict(list)
    for r in rows:
        by_acc[r.get('account', '?')].append(r)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(f'# 公众号摘要导出（{args.since} 起，{len(rows)} 条）\n\n')
        f.write(f'公众号数：{len(by_acc)}\n\n')
        for acc, items in sorted(by_acc.items(), key=lambda kv: -len(kv[1])):
            f.write(f'## {acc}（{len(items)} 条）\n')
            for it in items:
                f.write(f"- {it.get('date','')} [{it.get('tier','')}] {it.get('title','')}\n")
                if it.get('snippet'):
                    f.write(f"  > {it['snippet']}\n")
            f.write('\n')
    print(f'written {len(rows)} rows from {len(by_acc)} accounts -> {args.out}')


if __name__ == '__main__':
    main()
