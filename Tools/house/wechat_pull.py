# -*- coding: utf-8 -*-
"""
批量拉取公众号：数据/研究号 + 苏州本地房产号。
走 wechat_search 的检索与索引写入，额外做两件事：
  1. 每条结果只打印「带数字」的摘要行，便于快速抠硬数据
  2. 全部落 wechat-index.jsonl（按 标题+公众号 去重）

用法：python Tools/house/wechat_pull.py [--pages 2] [--since 2026-10-20] [--queries 银行]
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import wechat_search as ws

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

DEFAULT_QUERIES = [
    '苏州 二手房 成交 11月 网签',
    '苏州 商品住宅 库存 去化周期',
    '苏州 二手房 均价 11月',
    '克而瑞 苏州 市场月报',
    '中指研究院 苏州 房价',
    '贝壳研究院 二手房 数据',
    '苏州 板块 成交 元和 相城',
    '苏州 房价 走势 2026 11月',
]

NUM_RE = re.compile(r'\d')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', type=int, default=1)
    ap.add_argument('--since', default='2026-10-15')
    ap.add_argument('--sleep', type=float, default=5.0)
    ap.add_argument('--queries', default='')
    args = ap.parse_args()

    queries = [q.strip() for q in args.queries.split('|') if q.strip()] or DEFAULT_QUERIES
    index_path = os.path.join(ws.ROOT, 'house', 'realestate', 'wechat-index.jsonl')
    old = []
    if os.path.exists(index_path):
        with open(index_path, encoding='utf-8') as f:
            old = [json.loads(l) for l in f if l.strip()]
    seen = {(r.get('title'), r.get('account')) for r in old}
    added = 0

    for q in queries:
        try:
            items = ws.search(q, args.pages)
        except Exception as e:
            print(f'\n=== 「{q}」 ERR {type(e).__name__}: {str(e)[:60]}')
            time.sleep(args.sleep * 2)
            continue
        items = [i for i in items if not args.since or i['date'] >= args.since]
        items.sort(key=lambda i: i['date'], reverse=True)
        print(f'\n=== 「{q}」 {len(items)} 条')
        for it in items:
            mark = 'NEW' if (it['title'], it['account']) not in seen else '   '
            tier = ws.tier_of(it['account'])
            snip = it['snippet']
            has_num = bool(NUM_RE.search(snip))
            print(f'{mark} [{tier}] {it["date"]} {it["account"][:14]} | {it["title"][:44]}')
            if has_num:
                print(f'      {snip[:150]}')
            if mark == 'NEW':
                rec = dict(it)
                rec['tier'] = tier
                rec['keyword'] = q
                rec['harvested'] = time.strftime('%Y-%m-%d %H:%M')
                old.append(rec)
                seen.add((it['title'], it['account']))
                added += 1
        time.sleep(args.sleep)

    with open(index_path, 'w', encoding='utf-8') as f:
        for r in old:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'\n[索引] 新增 {added} 条，累计 {len(old)} 条 → {index_path}')


if __name__ == '__main__':
    main()
