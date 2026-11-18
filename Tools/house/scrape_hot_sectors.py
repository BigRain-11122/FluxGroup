# -*- coding: utf-8 -*-
"""
热门板块库存体检：在售套数 + 参考均价 + 房源陈旧率
陈旧率 = 标注"1年前发布"及更早的房源占比（越大=越卖不动）
输出：house/realestate/hot-sectors-20261116.csv
"""
import csv
import gzip
import re
import time
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')

SECTORS = [
    ('湖东', '园区', 'a0277', 'b04000'), ('玲珑', '园区', 'a0277', 'b04001'),
    ('双湖', '园区', 'a0277', 'b04002'), ('独墅湖', '园区', 'a0277', 'b010778'),
    ('斜塘', '园区', 'a0277', 'b04005'), ('青剑湖', '园区', 'a0277', 'b013075'),
    ('狮山', '高新', 'a0278', 'b04008'), ('科技城', '高新', 'a0278', 'b013065'),
    ('平江', '姑苏', 'a013102', 'b04014'), ('双塔', '姑苏', 'a013102', 'b04020'),
    ('沧浪', '姑苏', 'a013102', 'b04023'), ('金阊', '姑苏', 'a013102', 'b04028'),
    ('郭巷', '吴中', 'a0283', 'b04037'), ('城南', '吴中', 'a0283', 'b04034'),
    ('太湖新城', '吴中', 'a0283', 'b024391'),
    ('高铁新城', '相城', 'a0288', 'b014314'), ('元和', '相城', 'a0288', 'b015761'),
]

PAT_PRICE = re.compile(r'参考均价\s*([0-9]{3,6})\s*元')
PAT_COUNT = re.compile(r'共(?:找到)?\s*([0-9][0-9,]{1,7})\s*套')


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Referer': 'https://suzhou.esf.fang.com/',
                                               'Accept-Language': 'zh-CN,zh;q=0.9'})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    for enc in ('utf-8', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode('utf-8', 'ignore')


def main():
    rows = []
    print(f'{"板块":<8}{"区":<5}{"均价":>7}{"在售":>7}{"陈旧率":>8}{"样本":>6}')
    for name, dist, a, b in SECTORS:
        url = f'https://suzhou.esf.fang.com/house/{a}-{b}/'
        try:
            h = get(url)
            p = PAT_PRICE.search(h)
            c = PAT_COUNT.search(h)
            # 只统计房源卡片区域
            body = h.split('房源', 1)[-1]
            stale = len(re.findall(r'1年前发布|2年前发布|3年前发布|4年前发布', body))
            fresh = len(re.findall(r'新上|今日发布|昨天发布|\d+天前发布|\d+个月前发布', body))
            total = stale + fresh
            rate = stale / total if total else None
            rows.append({
                'sector': name, 'district': dist,
                'price': p.group(1) if p else '',
                'listings': c.group(1).replace(',', '') if c else '',
                'stale_rate': round(rate, 3) if rate is not None else '',
                'sample': total,
            })
            print(f'{name:<8}{dist:<5}{(p.group(1) if p else "N/A"):>7}'
                  f'{(c.group(1) if c else "N/A"):>7}'
                  f'{(f"{rate:.0%}" if rate is not None else "N/A"):>8}{total:>6}')
        except Exception as e:
            rows.append({'sector': name, 'district': dist, 'price': '', 'listings': '',
                         'stale_rate': '', 'sample': 0})
            print(f'{name:<8}{dist:<5}ERR {type(e).__name__}')
        time.sleep(1.0)

    import os
    from datetime import date
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    path = os.environ.get('HS_OUT') or os.path.join(
        root, 'house', 'realestate', f'hot-sectors-{date.today():%Y%m%d}.csv')

    # 限流时抓回来的是空值——绝不能用空值覆盖已有数据（历史的"整份覆盖"污染坑）
    prev = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                prev[r.get('sector', '')] = r

    kept = 0
    for r in rows:
        old = prev.get(r['sector'])
        if not old:
            continue
        for k in ('price', 'listings', 'stale_rate', 'sample'):
            if not r.get(k) and old.get(k):
                r[k] = old[k]
                kept += 1
    if kept:
        print(f'[merge] 从旧文件补回 {kept} 个空字段（本次多半被限流）')

    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['sector', 'district', 'price', 'listings',
                                          'stale_rate', 'sample'])
        w.writeheader()
        w.writerows(rows)
    filled = sum(1 for r in rows if r.get('price'))
    print(f'→ {path}（{filled}/{len(rows)} 个板块有价）')


if __name__ == '__main__':
    main()
