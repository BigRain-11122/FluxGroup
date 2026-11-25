#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""harvest_generic.py — 通用站点采集器：任意专业站/官网/科学站进同一套语料口径。

为什么要有这个（2026-11-25 CEO：「你采集的不止公众号哦」+「采集也要去 GitHub 找工具」）：
  之前 59 条源里有 21 条 degraded、8 条 dead，原因是我给每个站手写解析器——
  站点一改版就死，死一条少一条。现在正文提取交给成熟的 trafilatura（adbar/trafilatura，
  7.1k★，Apache-2.0 v1.8+），站点发现交给它的 feed / sitemap 两件工具：
    · 有任何 RSS/Atom → find_feed_urls 自动找到，不必知道 feed 地址
    · 没有 RSS 但有 sitemap.xml → sitemap_search 直接给文章 URL 清单
    · 两样都没有 → 只能给具体文章 URL（--url / --seeds）
  这样「换一个站」是给一个域名，不是写一个解析器。

许可纪律：trafilatura 是 Apache-2.0（v1.8.0 之前是 GPLv3+，本机装的是 2.4.0）。
  上游清单在 cph4/fleet/collect/UPSTREAM-HARVEST-v1.json，含拒绝项与理由。

用法：
  harvest_generic.py --probe https://www.pcauto.com.cn/       # 探活：这站怎么采
  harvest_generic.py --feed https://sspai.com/               # 自动找 RSS 并抓正文
  harvest_generic.py --sitemap https://www.miit.gov.cn/      # 走 sitemap 取清单
  harvest_generic.py --url <文章URL>                         # 单篇
  harvest_generic.py --seeds seeds.txt --limit 20            # 一行一个 URL
  harvest_generic.py --self-test
退出码：0 成功 / 2 一篇没抓到 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "collect")
OUT = os.path.join(OUTDIR, "ARTICLES-GENERIC.jsonl")
URLS = os.path.join(OUTDIR, "URLS-GENERIC.jsonl")
MIN_TEXT = 300

try:
    import trafilatura
    from trafilatura import feeds as trfeeds
    from trafilatura import sitemaps as trsitemaps
    HAVE_TRAFILATURA = True
except Exception:                                     # noqa: BLE001
    HAVE_TRAFILATURA = False


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def _append(p, rec):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def uid_of(url):
    """站点级稳定 uid：站点名 + 路径里的数字（无数字则路径哈希）。

    两个坑都在这行里避掉：
      · 不取整串 URL 的数字——域名里的数字（www.d1ev.com 的 1）会被算成文章 id，
        2026-11-25 在 gzh_corpus_expand 里踩过；
      · host 先去掉 www./m./mobile. 前缀再取——否则同一篇的移动版和桌面版是两个 id。
    """
    import hashlib
    u = urlsplit(url or "")
    host = re.sub(r"^(www|m|mobile|wap)\.", "", u.netloc.lower())
    site = re.sub(r"\W", "", host)[:8]
    digits = re.sub(r"\D", "", u.path)
    tail = digits[-10:] if digits else hashlib.sha1(
        (u.path or "").encode("utf-8")).hexdigest()[:10]
    return (site + tail)[:20]


def _meta(html, url):
    m = trafilatura.extract_metadata(html, default_url=url) if HAVE_TRAFILATURA else None
    if m is None:
        return {"title": "", "author": "", "date": "", "sitename": ""}
    return {"title": (getattr(m, "title", "") or "").strip()[:150],
            "author": (getattr(m, "author", "") or "").strip()[:60],
            "date": (getattr(m, "date", "") or "").strip(),
            "sitename": (getattr(m, "sitename", "") or "").strip()[:40]}


def extract_one(url, html=None, delay=0.0):
    """抓一篇 → 统一行。取不到正文就返回 (None, 原因)，不写空壳。"""
    if not HAVE_TRAFILATURA:
        return None, "缺 trafilatura（.venv-housing/bin/python 才有）"
    try:
        if html is None:
            html = trafilatura.fetch_url(url)
            if delay:
                time.sleep(delay)
    except Exception as e:                            # noqa: BLE001
        return None, "%s: %s" % (type(e).__name__, str(e)[:60])
    if not html:
        return None, "取不到页面（超时/403/编码）"
    try:
        text = trafilatura.extract(html, url=url, include_comments=False,
                                   include_tables=False, favor_precision=True) or ""
    except Exception as e:                            # noqa: BLE001
        return None, "解析失败 %s" % type(e).__name__
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(re.sub(r"\s", "", text)) < MIN_TEXT:
        return None, "正文过短（%d 字）" % len(re.sub(r"\s", "", text))
    md = _meta(html, url)
    return {"_uid": uid_of(url), "url": url, "title": md["title"],
            "text": text, "publish_date": md["date"], "author": md["author"],
            "site": md["sitename"] or urlsplit(url).netloc,
            "words": len(re.sub(r"\s", "", text)),
            "source": "generic", "genre": "unspecified",
            "fetched_at": datetime.now().isoformat(timespec="seconds")}, ""


# ---------------- 站点发现 ----------------

def discover_feeds(url, lang="zh"):
    if not HAVE_TRAFILATURA:
        return [], "缺 trafilatura"
    try:
        return trfeeds.find_feed_urls(url, target_lang=lang), ""
    except Exception as e:                            # noqa: BLE001
        return [], "%s: %s" % (type(e).__name__, str(e)[:60])


def discover_sitemap(url, lang="zh"):
    if not HAVE_TRAFILATURA:
        return [], "缺 trafilatura"
    try:
        return trsitemaps.sitemap_search(url, target_lang=lang), ""
    except Exception as e:                            # noqa: BLE001
        return [], "%s: %s" % (type(e).__name__, str(e)[:60])


def _looks_like_feed(text):
    head = (text or "")[:300].lstrip().lower()
    return head.startswith("<?xml") or "<rss" in head or "<feed" in head


def feed_candidates(site, limit=20):
    """站点 → 文章链接清单。

    实测（2026-11-25，少数派）：trafilatura 的 find_feed_urls 有时返回的是
    **文章链接**（/post/118705）而不是 feed 地址。所以不能假定返回值就是 RSS：
    抓下来先看是不是 XML，是就解析条目，不是就直接当文章链接用。
    """
    cands, why = discover_feeds(site)
    if not cands:
        return [], why or "没有可用 feed"
    out, seen = [], set()
    for c in cands:
        if len(out) >= limit:
            break
        try:
            html = trafilatura.fetch_url(c)
        except Exception:                             # noqa: BLE001
            continue
        if not html:
            continue
        if _looks_like_feed(html):
            items, _ = _feed_items_from(html, limit=limit - len(out))
        else:
            items = [c]
        for u in items:
            if u in seen:
                continue
            seen.add(u)
            out.append(u)
            if len(out) >= limit:
                break
    if not out:
        return [], "候选都取不到"
    return out, ""


def probe(url):
    """探活：这个站能用哪种方式采，能采多少。不猜，逐件试并报结果。"""
    out = {"url": url, "feeds": 0, "feed_sample": [], "sitemap_urls": 0,
           "sitemap_sample": [], "article": 0, "why": ""}
    f, e1 = discover_feeds(url)
    out["feeds"], out["feed_sample"] = len(f), f[:3]
    if not f:
        s, e2 = discover_sitemap(url)
        out["sitemap_urls"], out["sitemap_sample"] = len(s), s[:3]
    a, why = extract_one(url)
    out["article"] = a["words"] if a else 0
    out["why"] = why or ""
    out["verdict"] = ("feed" if out["feeds"] else
                      "sitemap" if out["sitemap_urls"] else
                      "article" if out["article"] else "不可采")
    return out


def harvest(urls, limit=20, delay=1.0, verbose=True):
    seen = {r.get("_uid") for r in _rows(OUT)}
    rows, fail = [], []
    for u in urls:
        if len(rows) >= limit:
            break
        uid = uid_of(u)
        if uid in seen:
            continue
        art, why = extract_one(u, delay=delay)
        if art is None:
            fail.append({"url": u, "why": why})
            if verbose:
                print("  跳过 %s → %s" % (u[-42:], why))
            continue
        seen.add(uid)
        rows.append(art)
        if verbose:
            print("  %s → %d 字｜%s" % (u[-42:], art["words"], art["title"][:30]))
    for r in rows:
        _append(OUT, r)
        _append(URLS, {"_uid": r["_uid"], "url": r["url"], "title": r["title"],
                       "site": r["site"], "found_at": r["fetched_at"]})
    return rows, fail


# ---------------- 自检（不联网） ----------------

GOOD_HTML = """<html><head><title>座舱屏幕为什么越做越大</title>
<meta name="author" content="测试作者"><meta property="article:published_time" content="2026-11-10">
</head><body><nav><a href="/">首页</a><a href="/about">关于</a></nav>
<article><h1>座舱屏幕为什么越做越大</h1>
<p>2019 年到 2025 年，主流车型的中控屏尺寸从 8 寸涨到 15 寸，涨幅接近一倍。</p>
<p>原因不全是用户喜欢大屏。座舱里被塞进了导航、音乐、空调、设置四层入口，
每一层都要占位置，屏幕不大就排不开。</p>
<p>但大屏的代价是反光面积变大。实测同一块玻璃，15 寸屏在正午直射下的可读性
比 12 寸低三成，这个数字来自我们自己的三次对比。</p>
<p>第二部分是触控目标尺寸。手指点击的舒适区在 9 毫米以上，而很多车机把设置图标
压到 6 毫米，误触率因此明显上升。这一段也是实测，不是推断。</p>
<p>第三部分是层级。把空调从三级菜单提到一级，用户完成同样操作的耗时从 4.2 秒
降到 1.6 秒，差别比屏幕大小大得多。</p>
<p>所以真正的判断标准不是尺寸，而是常用功能在第几层。三层以内能到，就算合格。</p>
</article><footer>版权所有</footer></body></html>"""

THIN_HTML = """<html><head><title>只有一个标题</title></head><body>
<article><p>太短了。</p></article></body></html>"""

RSS_XML = """<?xml version="1.0"?><rss><channel><title>t</title>
<item><link>https://example.com/a/1001</link><title>稿一</title></item>
<item><link>https://example.com/a/1002</link><title>稿二</title></item>
</channel></rss>"""


def self_test():
    cases = []

    # 1 uid：域名里的数字不许进文章 id（2026-11-25 实锚）
    u1 = uid_of("https://www.d1ev.com/news/shuju/100002")
    u2 = uid_of("https://m.d1ev.com/news/shuju/100002")
    u3 = uid_of("https://www.pcauto.com.cn/news/100002")
    cases.append(("uid 不含域名数字", u1 == "d1evcom100002"))
    cases.append(("同一篇的移动版与桌面版同一个 id（host 前缀已剥）", u1 == u2))
    cases.append(("负控[不同站点同数字] 不许撞 id", u1 != u3))
    cases.append(("uid 稳定可复算", uid_of("https://a.com/x/1") == uid_of("https://a.com/x/1")))
    cases.append(("负控[无数字路径] 用哈希但同 URL 稳定",
                  uid_of("https://a.com/about") == uid_of("https://a.com/about")))

    # 2 正文提取：抓得到真句、丢得掉导航与页脚（需要 trafilatura）
    if HAVE_TRAFILATURA:
        art, why = extract_one("https://example.com/a/1", html=GOOD_HTML)
        cases.append(("正文提取成功", art is not None))
        if art:
            cases.append(("取到关键句", "8 寸涨到 15 寸" in art["text"]))
            cases.append(("标题抽到", "座舱屏幕" in art["title"]))
            cases.append(("日期抽到", art["publish_date"].startswith("2026")))
            cases.append(("导航未混入", "首页" not in art["text"][:40]))
            cases.append(("页脚未混入", "版权所有" not in art["text"]))
            cases.append(("字数按去空白算", art["words"] == len(re.sub(r"\s", "", art["text"]))))
        thin, why2 = extract_one("https://example.com/a/2", html=THIN_HTML)
        cases.append(("负控[正文过短] 不入库", thin is None and "短" in why2))
        empty, why3 = extract_one("https://example.com/a/3", html="")
        cases.append(("负控[空页面] 不入库", empty is None))
    else:
        cases.append(("SKIP 无 trafilatura", True))

    # 3 feed 条目解析（不联网，直接喂 XML）
    items, why = _feed_items_from(RSS_XML)
    cases.append(("feed 解析出 2 条", len(items) == 2))
    cases.append(("feed 条目是文章链接", items[0].endswith("/a/1001")))
    bad, why4 = _feed_items_from("<html><body>不是 feed</body></html>")
    cases.append(("负控[非 feed] 返回空并有原因", bad == [] and why4))

    # 4 站点发现回来的东西可能是 feed，也可能直接是文章链接（实测少数派如此）
    cases.append(("XML 被认成 feed", _looks_like_feed('<?xml version="1.0"?><rss>')))
    cases.append(("HTML 不被认成 feed", not _looks_like_feed("<!DOCTYPE html><html>")))
    cases.append(("负控[空串] 不算 feed", not _looks_like_feed("")))

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def _feed_items_from(xml_text, limit=20):
    """把 feed 解析拆出来，好让自检不联网。"""
    locs = re.findall(r"<link>\s*(?:<!\[CDATA\[)?(https?://[^\]<\s]+)", xml_text or "")
    locs += re.findall(r'<link[^>]+href="(https?://[^"]+)"', xml_text or "")
    seen, out = set(), []
    for u in locs:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= limit:
            break
    if not out:
        return [], "feed 里没解析到条目（可能不是 RSS/被拦）"
    return out, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="只抓这一篇")
    ap.add_argument("--seeds", help="一行一个 URL 的文件")
    ap.add_argument("--feed", help="站点 URL：自动找 RSS 并抓正文")
    ap.add_argument("--sitemap", help="站点 URL：走 sitemap 取文章清单")
    ap.add_argument("--probe", help="探活：这个站能用哪种方式采")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not HAVE_TRAFILATURA:
        print("缺 trafilatura：用 .venv-housing/bin/python 跑", file=sys.stderr)
        return 4
    if a.probe:
        print(json.dumps(probe(a.probe), ensure_ascii=False, indent=1))
        return 0
    if a.url:
        art, why = extract_one(a.url)
        if art is None:
            print("[generic] 失败：%s" % why)
            return 1
        rows, _ = harvest([a.url], limit=1, delay=0, verbose=True)
        print("[generic] %s｜%d 字｜作者 %s｜%s" % (art["title"][:40], art["words"],
                                                  art["author"] or "未知", art["publish_date"]))
        return 0 if rows else 2

    urls, src = [], ""
    if a.seeds:
        urls = [l.strip() for l in open(a.seeds, encoding="utf-8") if l.strip()
                and not l.strip().startswith("#")]
        src = "seeds"
    elif a.feed:
        urls, why = feed_candidates(a.feed, limit=a.limit)
        if not urls:
            print("[generic] 没找到可用 feed：%s" % why, file=sys.stderr)
            return 2
        print("[generic] 站点发现 %d 条候选（feed 或直接文章链接）" % len(urls))
        src = "feed"
    elif a.sitemap:
        urls, why = discover_sitemap(a.sitemap)
        if not urls:
            print("[generic] sitemap 无结果：%s" % why, file=sys.stderr)
            return 2
        print("[generic] sitemap 给出 %d 条候选" % len(urls))
        src = "sitemap"
    else:
        print(__doc__)
        return 0

    rows, fail = harvest(urls, limit=a.limit, delay=a.delay)
    print("\n[generic] 来源 %s｜候选 %d → 入库 %d｜失败 %d"
          % (src, len(urls), len(rows), len(fail)))
    if rows:
        avg = sum(r["words"] for r in rows) / len(rows)
        print("[generic] 平均 %.0f 字 → %s" % (avg, os.path.relpath(OUT, ROOT)))
    return 0 if rows else 2


if __name__ == "__main__":
    sys.exit(main())
