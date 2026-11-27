# -*- coding: utf-8 -*-
"""
房管局每日快照：存量房（二手）+ 商品房（新房）即时成交，按区
来源：苏州市房地产市场和交易管理中心

输出：house/realestate/official-daily.jsonl
      - 一天一行，同日重复运行只保留最后一次采集（值会在盘中增长）
      - 新房页自带官方月度成交套数序列，一并存入 monthly

运行：python Tools/house/snapshot_official.py
"""
import gzip
import json
import os
import re
import urllib.request
from datetime import date, datetime

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
PAGES = {
    'secondhand': 'http://clf.zfcjj.suzhou.gov.cn/xsinfo.aspx',
    'newhome': 'http://spf.zfcjj.suzhou.gov.cn:8089/szfcweb/DataSerach/XSFWINFO.aspx',
}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'house', 'realestate', 'official-daily.jsonl')

DISTRICTS = ['姑苏区', '吴中区', '相城区', '工业园区', '高新区', '吴江区']
# 去标签后单元格之间会留空格，正则必须容忍空白
PAT_DIST = re.compile(
    r'(姑苏区|吴中区|相城区|工业园区|高新区|吴江区)\s*小计\s*(\d+)\s*(\d+\.\d+)\s*'
    r'其中：住宅\s*(\d+)\s*(\d+\.\d+)')
PAT_TOTAL = re.compile(
    r'市区合计\s*总计\s*(\d+)\s*(\d+\.\d+)\s*其中：住宅\s*(\d+)\s*(\d+\.\d+)')
PAT_ASOF = re.compile(r'即时成交信息\s*【?(\d{4}-\d{1,2}-\d{1,2})】?')
PAT_CHART_LABELS = re.compile(r'lineChartData\.labels\s*=\s*(\[[^\]]*\])')
PAT_CHART_DATA = re.compile(r'lineChartData\.datasets\[0\]\.data\s*=\s*(\[[^\]]*\])')


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
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


def flatten(html):
    txt = re.sub(r'<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', txt)


def parse(html):
    txt = flatten(html)
    out = {'districts': {}, 'total': {}}
    for d, n, a, rn, ra in PAT_DIST.findall(txt):
        out['districts'][d] = {'units': int(n), 'area': float(a),
                               'res_units': int(rn), 'res_area': float(ra)}
    m = PAT_TOTAL.search(txt)
    if m:
        out['total'] = {'units': int(m.group(1)), 'area': float(m.group(2)),
                        'res_units': int(m.group(3)), 'res_area': float(m.group(4))}
    a = PAT_ASOF.search(txt)
    if a:
        out['asof'] = a.group(1)
    return out


def parse_monthly(html):
    """新房页内嵌的官方月度成交套数（商品房）。返回 [(yyyy-mm, units), ...]"""
    m1, m2 = PAT_CHART_LABELS.search(html), PAT_CHART_DATA.search(html)
    if not (m1 and m2):
        return []
    labels = json.loads(m1.group(1))
    data = json.loads(m2.group(1))
    out = []
    for lab, val in zip(labels, data):
        lab = str(lab)
        if len(lab) == 6 and lab.isdigit():
            out.append([f'{lab[:4]}-{lab[4:]}', int(val)])
    return out


def load_rows():
    if not os.path.exists(OUT):
        return []
    with open(OUT, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    now = datetime.now()
    row = {'date': str(date.today()), 'ts': now.strftime('%H:%M')}
    htmls = {}
    for k, url in PAGES.items():
        htmls[k] = get(url)
        row[k] = parse(htmls[k])

    # 新房页内嵌的 lineChartData 月度序列已核实为不可用，故不入库：
    # 该页无 canvas 元素（chart 从未渲染），数据来自模板 js，模板自带
    # randomScalingFactor=random()*10000+15000 的示例值，且无标题无单位，
    # 与苏州任何可核对的成交量/均价口径都不吻合。保留解析函数仅供复测。

    # 硬校验：总量解析不到就报错退出，绝不写坏行
    for k, label in (('secondhand', '二手房'), ('newhome', '新房')):
        if not row[k]['total'].get('units'):
            raise SystemExit(f'[FAIL] {label}总量解析失败：{json.dumps(row[k], ensure_ascii=False)[:300]}')
        if len(row[k]['districts']) != len(DISTRICTS):
            raise SystemExit(f'[FAIL] {label}分区解析不全：{list(row[k]["districts"])}')

    rows = [r for r in load_rows() if r.get('date') != row['date']] + [row]
    rows.sort(key=lambda r: r['date'])
    with open(OUT, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    for k, label in (('secondhand', '二手房'), ('newhome', '新房')):
        t = row[k]['total']
        print(f'{row["date"]} {row["ts"]} {label}：{t["units"]} 套 / {t["area"]:.0f} ㎡ '
              f'（住宅 {t["res_units"]} 套 / {t["res_area"]:.0f} ㎡）'
              f'{("  [数据日 " + row[k]["asof"] + "]") if row[k].get("asof") else ""}')
        for d in DISTRICTS:
            v = row[k]['districts'][d]
            print(f'   {d:<6}{v["units"]:>4} 套 {v["area"]:>9.1f} ㎡ '
                  f'住宅 {v["res_units"]:>3} 套  均套 {v["area"]/v["units"]:.0f} ㎡')
    sh, nh = row['secondhand']['total']['units'], row['newhome']['total']['units']
    if nh:
        print(f'\n二手 : 新房 = {sh/nh:.2f} : 1（二手占比 {sh/(sh+nh):.1%}）')

    print('\n各区二手均套面积（住宅）：')
    for d in DISTRICTS:
        v = row['secondhand']['districts'][d]
        if v['res_units']:
            print(f'   {d:<6}{v["res_area"] / v["res_units"]:>6.1f} ㎡')
    print('\n（file 只存官方当日分区成交；成交价/库存/板块口径官方不公开）')

    print(f'\n已写入 {OUT}（累计 {len(rows)} 天）')


if __name__ == '__main__':
    main()
