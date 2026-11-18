# -*- coding: utf-8 -*-
"""
地产公众号检索（走搜狗微信搜索，服务端渲染，可解析）。

用法：
    python Tools/house/wechat_search.py "苏州 贝壳 成交 真实成交价"
    python Tools/house/wechat_search.py --pages 3 --since 2026-10-01 "苏州二手房 成交"
    python Tools/house/wechat_search.py --fetch 3 "小春哥南京苏州二手房"

--pages N      抓前 N 页（每页 10 条），默认 2
--since DATE   只要该日期之后的文章（按公众号发布时间，不是抓取时间）
--fetch N      按时间倒序抓前 N 篇正文，存 house/realestate/wechat/

注意：
- tsn 参数（时间范围）会触发空页，不用；改用翻页 + 本地按日期过滤。
- 搜狗高频访问会出验证码；本工具每页间隔 2 秒，单次最多 3 页。
"""
import argparse
import html as htmlmod
import http.cookiejar
import os
import re
import time
import urllib.parse
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')

# 搜狗 /link 跳转依赖搜索页种下的 cookie（SUID/SNUID），必须全程共用
JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))
SOGOU = 'https://weixin.sogou.com/weixin'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTDIR = os.path.join(ROOT, 'house', 'realestate', 'wechat')

TIER1 = ('克而瑞', '中指研究院', '中指院', '易居', '贝壳研究院', '丁祖昱',
         '中国城市中心', '国家统计局')
TIER2 = ('苏州楼市', '狂楼', '直击苏州楼市', '苏州房观', '深度苏州',
         '苏州房地产', '楼市参考', '米宅', '小春哥')


def fetch(url, referer=None, timeout=25):
    hdr = {'User-Agent': UA,
           'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
           'Accept-Language': 'zh-CN,zh;q=0.9'}
    if referer:
        hdr['Referer'] = referer
    req = urllib.request.Request(url, headers=hdr)
    with OPENER.open(req, timeout=timeout) as r:
        raw, st, final = r.read(), r.status, r.geturl()
    if raw[:2] == b'\x1f\x8b':
        import gzip
        raw = gzip.decompress(raw)
    for enc in ('utf-8', 'gb18030'):
        try:
            return st, raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return st, raw.decode('utf-8', 'ignore')


def strip_tags(h):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S | re.I)
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def tier_of(account):
    for k in TIER1:
        if k.lower() in account.lower():
            return 'T1机构'
    for k in TIER2:
        if k in account:
            return 'T2本地'
    return '其他'


def parse_page(page):
    items = []
    for block in re.split(r'<li id="sogou_vr_', page)[1:]:
        m = re.search(r'<h3>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        href = htmlmod.unescape(m.group(1))
        title = htmlmod.unescape(strip_tags(m.group(2)))
        acc = re.search(r'class="all-time-y2"[^>]*>(.*?)</span>', block, re.S)
        acc = htmlmod.unescape(strip_tags(acc.group(1))) if acc else ''
        ts = re.search(r"timeConvert\('(\d{10})'\)", block)
        date = time.strftime('%Y-%m-%d', time.localtime(int(ts.group(1)))) if ts else ''
        snip = re.search(r'class="txt-info"[^>]*>(.*?)</p>', block, re.S)
        snip = htmlmod.unescape(strip_tags(snip.group(1))) if snip else ''
        url = href if href.startswith('http') else 'https://weixin.sogou.com' + href
        # 搜狗把查询串里的空格原样带出来，会造出非法 URL
        url = re.sub(r'[\r\n\t]', '', url).replace(' ', '%20')
        items.append({'title': title, 'account': acc, 'date': date,
                      'url': url, 'snippet': snip})
    return items


def search(keyword, pages=2):
    out, seen = [], set()
    for p in range(1, pages + 1):
        q = urllib.parse.quote(keyword)
        url = f'{SOGOU}?type=2&query={q}&ie=utf8&page={p}'
        st, page = fetch(url, referer=SOGOU)
        if '请输入验证码' in page or 'antispider' in page:
            print(f'[warn] 第 {p} 页触发验证码，停止翻页')
            break
        got = parse_page(page)
        for it in got:
            key = (it['title'], it['account'])
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        if p < pages:
            time.sleep(2.0)
    return out


def article_text(html):
    m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*(?:<script|<div\s+class="rich_media_tool)',
                  html, re.S)
    body = m.group(1) if m else html
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'</(p|div|section|h\d|li|tr|td)>', '\n', body)
    body = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', body, flags=re.S | re.I)
    body = re.sub(r'<[^>]+>', '', body)
    body = htmlmod.unescape(body)
    lines = [l.strip() for l in body.splitlines()]
    return '\n'.join(l for l in lines if l)


def resolve_sogou_link(html):
    """搜狗 /link 返回的是 JS 跳转页，真链接由 url += '...' 逐段拼接。"""
    parts = re.findall(r"url \+= '([^']*)'", html)
    if not parts:
        return None
    return ''.join(parts).replace('@', '').strip()


def save_article(item):
    os.makedirs(OUTDIR, exist_ok=True)
    try:
        st, h = fetch(item['url'], referer=SOGOU)
    except Exception as e:
        print(f'   [fetch-err] {type(e).__name__}: {str(e)[:70]}')
        return None
    if 'js_content' not in h:
        real = resolve_sogou_link(h)
        if not real:
            t = re.search(r'<title>(.*?)</title>', h, re.S)
            t = re.sub(r'\s+', '', t.group(1))[:40] if t else '(无标题)'
            print(f'   [no-article] {len(h)} 字节，标题={t!r}，且无跳转串')
            return None
        try:
            st, h = fetch(real, referer=SOGOU)
        except Exception as e:
            print(f'   [fetch-err2] {type(e).__name__}: {str(e)[:70]}')
            return None
    if 'js_content' not in h:
        print(f'   [no-article] 跳到微信后仍无正文（{len(h)} 字节）')
        return None
    body = article_text(h)
    if len(body) < 200:
        print(f'   [too-short] 正文仅 {len(body)} 字，跳过')
        return None
    slug = re.sub(r'[^\w\u4e00-\u9fa5]+', '-', item['account'])[:14]
    slug2 = re.sub(r'[^\w\u4e00-\u9fa5]+', '-', item['title'])[:38].strip('-')
    path = os.path.join(OUTDIR, f"{item['date'] or 'na'}-{slug}-{slug2}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# {item['title']}\n\n")
        f.write(f"- 公众号：{item['account']}\n- 发布：{item['date']}\n")
        f.write(f"- 索引链接：{item['url'][:160]}\n\n---\n\n{body}\n")
    print(f'   [saved] {os.path.basename(path)}  {len(body)} 字')
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('keyword')
    ap.add_argument('--pages', type=int, default=2)
    ap.add_argument('--since', default='')
    ap.add_argument('--fetch', type=int, default=0)
    ap.add_argument('--save', action='store_true',
                    help='把结果追加到 house/realestate/wechat-index.jsonl（按 标题+号 去重）')
    args = ap.parse_args()

    items = search(args.keyword, args.pages)
    if args.since:
        items = [i for i in items if i['date'] >= args.since]
    items.sort(key=lambda i: i['date'], reverse=True)
    if not items:
        print('没有符合条件的结果')
        return
    print(f'关键词「{args.keyword}」命中 {len(items)} 条（按时间倒序）：\n')
    for i, it in enumerate(items, 1):
        print(f"{i:>2}. [{tier_of(it['account'])}] {it['date']}  {it['account']}")
        print(f"    {it['title'][:76]}")
        if it['snippet']:
            print(f"    {it['snippet'][:140]}")
    if args.save:
        import json
        os.makedirs(OUTDIR, exist_ok=True)
        path = os.path.join(ROOT, 'house', 'realestate', 'wechat-index.jsonl')
        old = []
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                old = [json.loads(l) for l in f if l.strip()]
        keys = {(r.get('title'), r.get('account')) for r in old}
        added = 0
        for it in items:
            if (it['title'], it['account']) in keys:
                continue
            rec = dict(it)
            rec['tier'] = tier_of(it['account'])
            rec['keyword'] = args.keyword
            rec['harvested'] = time.strftime('%Y-%m-%d %H:%M')
            old.append(rec)
            keys.add((it['title'], it['account']))
            added += 1
        with open(path, 'w', encoding='utf-8') as f:
            for r in old:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(f'\n[a-save] 新增 {added} 条 → {path}（累计 {len(old)} 条）')
    if args.fetch:
        print(f'\n抓取前 {args.fetch} 篇：')
        for it in items[:args.fetch]:
            save_article(it)
            time.sleep(2.5)


if __name__ == '__main__':
    main()
