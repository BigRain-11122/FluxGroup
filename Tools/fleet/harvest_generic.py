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
  harvest_generic.py --list    https://www.stats.gov.cn/sj/zxfb/  # 列表页抽链接
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


BAD_TITLE = re.compile(r"\b(var|let|const|function|document)\b|\w+\s*=\s*['\"]|</?\w+")
SITE_TAIL = re.compile(r"\s*[-_—|｜]\s*(中华人民共和国)?[\u4e00-\u9fa5]{0,12}"
                       r"(统计局|政府|工信部|信息网|官网|网站|网)\s*$")


def _clean_title(title, html):
    """标题清洗。两个坑都是实测踩的：

      1. 页面把标题写在 JS 里（`var title1 = '2026年11月中旬...'`），元数据抽取
         直接把它当标题，入库后标题列就是一段代码 → 出现 JS 关键字就换来源；
      2. 标题常带站名尾巴（`... - 国家统计局`）→ 统一按分隔符剥掉。
    """
    t = (title or "").strip()
    if not (t and not BAD_TITLE.search(t) and len(t) <= 120):
        m = re.search(r"<title[^>]*>([\s\S]{2,300}?)</title>", html or "", re.I)
        t = ""
        if m:
            cand = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
            if cand and not BAD_TITLE.search(cand):
                t = cand
    t = SITE_TAIL.sub("", t).strip()
    return t[:150]


def _meta(html, url):
    m = trafilatura.extract_metadata(html, default_url=url) if HAVE_TRAFILATURA else None
    if m is None:
        return {"title": _clean_title("", html), "author": "", "date": "", "sitename": ""}
    return {"title": _clean_title(getattr(m, "title", ""), html),
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
    """sitemap 清单。max_sitemaps 必须给上限：默认 10000 会让一个大站
    探活挂好几分钟（2026-11-25 实测：跑着跑着就不动了，9/29 卡住）。"""
    if not HAVE_TRAFILATURA:
        return [], "缺 trafilatura"
    try:
        return trsitemaps.sitemap_search(url, target_lang=lang, max_sitemaps=40), ""
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


ASSET_EXT = (".css", ".js", ".json", ".jpg", ".jpeg", ".png", ".gif", ".svg",
             ".ico", ".webp", ".woff", ".woff2", ".ttf", ".mp4", ".mp3", ".zip")


def page_links(html, page_url, limit=200):
    """列表页 → 文章链接。官方/专业站绝大多数是列表页而不是 RSS。

    判据两条：
      1. 路径里带 4 位以上数字（`/202611/t20261120_123.html`、
         `/news/shuju/312498` 都符合）。首页导航、栏目页、关于我们都不带长数字，
         所以这条比"猜 class 名"稳得多——class 名一改版就全错。
      2. **排除静态资源**。坑（2026-11-25 实测）：`gtj2023_base.css` 里的 2023
         正好是 4 位数字，被当成文章链接，一次抓了 9 条 CSS 全失败。
    """
    from urllib.parse import urljoin
    out, seen = [], set()
    for m in re.finditer(r'href="([^"#]+)"', html or ""):
        raw = m.group(1).strip()
        if raw.startswith(("javascript:", "mailto:", "tel:")):
            continue
        u = urljoin(page_url, raw)
        if not u.startswith("http"):
            continue
        path = urlsplit(u).path
        if path.lower().endswith(ASSET_EXT):
            continue
        if not re.search(r"\d{4,}", path):
            continue
        if re.search(r"/(index|default)\.(html?|shtml?)$", path, re.I):
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= limit:
            break
    return out


def probe(url):
    """探活：这个站能用哪种方式采，能采多少。不猜，逐件试并报结果。

    五种判定，顺序就是优先级：
      feed    → 有 RSS/Atom，直接 --feed
      sitemap → 有 sitemap，走 --sitemap 拿清单
      list    → 列表页（官方站最常见），走 --list
      article → 页面本身就是一篇文章，走 --url
      不可采  → 首页是 JS 壳，三条路都不通

    「list」这一档是 2026-11-25 补的：在此之前统计局这类列表页会被判成
    「article」（trafilatura 抽到了首页自己那段文字），是假阳性。
    """
    out = {"url": url, "feeds": 0, "feed_sample": [], "sitemap_urls": 0,
           "sitemap_sample": [], "list_links": 0, "list_sample": [],
           "article": 0, "why": ""}
    f, e1 = discover_feeds(url)
    out["feeds"], out["feed_sample"] = len(f), f[:3]
    if not f:
        s, e2 = discover_sitemap(url)
        out["sitemap_urls"], out["sitemap_sample"] = len(s), s[:3]
    if not f and not out["sitemap_urls"]:
        try:
            html = trafilatura.fetch_url(url)
        except Exception:                             # noqa: BLE001
            html = ""
        links = page_links(html, url) if html else []
        out["list_links"], out["list_sample"] = len(links), links[:3]
    a, why = extract_one(url)
    out["article"] = a["words"] if a else 0
    out["why"] = why or ""
    out["verdict"] = ("feed" if out["feeds"] else
                      "sitemap" if out["sitemap_urls"] else
                      "list" if out["list_links"] >= 5 else
                      "article" if out["article"] and not out["list_links"] else
                      "不可采")
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

    # 5 列表页识别（官方站最常见；2026-11-25 统计局被误判成 article 才补的）
    LIST_HTML = """<html><body>
    <a href="/202611/t20261120_1901234.html">十一月数据发布</a>
    <a href="/202611/t20261118_1901199.html">十月工业增加值</a>
    <a href="https://www.stats.gov.cn/sj/zxfb/202610/t20261020_1900001.html">九月数据</a>
    <a href="/index.html">首页（不该算文章）</a>
    <a href="/about">关于我们（无长数字）</a>
    <a href="javascript:void(0)">JS 链接</a>
    </body></html>"""
    links = page_links(LIST_HTML, "https://www.stats.gov.cn/sj/zxfb/")
    cases.append(("列表页抽出 3 条文章链接", len(links) == 3))
    cases.append(("相对链接补成绝对链接", links[0].startswith("https://www.stats.gov.cn/202611/")))
    cases.append(("负控[首页 index] 不算文章", not any("index.html" in x for x in links)))
    cases.append(("负控[无长数字的导航页] 不算文章", not any(x.endswith("/about") for x in links)))
    cases.append(("负控[空 HTML] 返回空", page_links("", "https://a.com/") == []))
    cases.append(("负控[纯导航页] 0 条（不许瞎凑）",
                  page_links('<a href="/news">新闻</a><a href="/about">关于</a>',
                             "https://a.com/") == []))
    cases.append(("负控[CSS 链里带年份] 不算文章（实锚 gtj2023_base.css）",
                  page_links('<a href="/images/gtj2023_base.css">x</a>',
                             "https://www.stats.gov.cn/") == []))

    # 6 标题清洗：页面把标题写在 JS 里时不许把代码当标题
    js_html = ("<html><head><title>2026年11月中旬流通领域重要生产资料价格</title></head>"
               "<body>x</body></html>")
    cases.append(("负控[JS 变量不作标题] 回退到 <title>",
                  _clean_title("var title1 = '2026年11月'", js_html)
                  == "2026年11月中旬流通领域重要生产资料价格"))
    cases.append(("正常标题原样保留", _clean_title("座舱屏幕越做越大", js_html) == "座舱屏幕越做越大"))
    cases.append(("站名尾巴被去掉",
                  _clean_title("2026年10月份数据 - 国家统计局", "<title>2026年10月份数据</title>")
                  .endswith("数据")))
    cases.append(("负控[取不到任何标题] 返回空而不是代码",
                  _clean_title("var a = 'x'", "<html></html>") == ""))

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


def probe_isolated(url, timeout=75):
    """在子进程里探活，带硬超时。

    为什么必须隔离（2026-11-25 实测两次踩）：trafilatura 的 sitemap / fetch
    没有可以传进去的整体超时，某个大站能把整轮探活挂住——一次挂到第 10 个源
    就不动了，而且已经探完的结论全丢。子进程 + 硬超时 = 最多浪费这一条。
    """
    import subprocess
    try:
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--probe", url],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"verdict": "超时", "why": "%d 秒没回来" % timeout}
    raw = (p.stdout or "").strip()
    i = raw.find("{")
    if i < 0:
        return {"verdict": "崩溃", "why": (p.stderr or "")[-120:]}
    try:
        return json.loads(raw[i:])
    except ValueError:
        return {"verdict": "崩溃", "why": "输出不是 JSON"}


def apply_verdicts(path=None, verdicts_path=None):
    """把探活结论回写源册。规则写死，不凭感觉改：

      feed/list/sitemap → status=ok，并记 harvest.via，下次直接按这条通道采
      不可采           → status 保持/降为 degraded（真有证据才升 ok，不粉饰）
      超时             → 状态不动，只记 via=timeout（没测出来不等于不能用）
    """
    path = path or os.path.join(ROOT, "cph4", "fleet", "social", "gzh",
                                "SOURCES-REGISTRY-v1.json")
    verdicts_path = verdicts_path or os.path.join(OUTDIR, "SOURCE-VERDICTS.json")
    try:
        reg = json.load(open(path, encoding="utf-8"))
        vd = json.load(open(verdicts_path, encoding="utf-8"))
    except FileNotFoundError as e:
        print("[apply] 缺文件：%s" % e, file=sys.stderr)
        return 2
    vs = vd.get("verdicts") or {}
    ts = vd.get("_ts") or datetime.now().isoformat(timespec="seconds")
    changed = {"ok": 0, "degraded": 0, "unchanged": 0}
    for x in reg.get("sources") or []:
        name = x.get("name") or ""
        v = vs.get(name)
        if not v:
            changed["unchanged"] += 1
            continue
        before = x.get("status")
        via = v.get("verdict")
        x["harvest"] = {"via": via if via in ("feed", "list", "sitemap") else
                        ("none" if via == "不可采" else "timeout"),
                        "probed": ts, "was": before,
                        "feeds": v.get("feeds", 0), "list_links": v.get("list_links", 0),
                        "article": v.get("article", 0)}
        if via in ("feed", "list", "sitemap"):
            x["status"] = "ok"
        elif via == "不可采":
            if before != "dead":
                x["status"] = "degraded"
        else:
            x["status"] = before
        if x["status"] != before:
            changed["ok" if x["status"] == "ok" else "degraded"] += 1
        else:
            changed["unchanged"] += 1
    reg["updated"] = ts[:10]
    json.dump(reg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import collections
    print("[apply] 源册已回写：升为 ok %d 条 / 降级 %d 条 / 不变 %d 条"
          % (changed["ok"], changed["degraded"], changed["unchanged"]))
    print("[apply] 现在状态分布：%s"
          % dict(collections.Counter(x.get("status") for x in reg["sources"])))
    print("[apply] 按通道分布：%s"
          % dict(collections.Counter((x.get("harvest") or {}).get("via", "-")
                                     for x in reg["sources"])))
    return 0


def probe_registry(path=None, only_bad=True, max_n=40):
    """把源册里「说不清能不能采」的源逐个探活，落成 verdict 台账。

    为什么值得跑：源册里 30 ok / 21 degraded / 8 dead 是**当时的印象**，不是测出来的。
    探活把它们换成四档实测结论，顺手告出该走哪条通道（feed/list/sitemap/不可采）。
    """
    path = path or os.path.join(ROOT, "cph4", "fleet", "social", "gzh",
                               "SOURCES-REGISTRY-v1.json")
    try:
        reg = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return {}
    srcs = reg.get("sources") or []
    if only_bad:
        srcs = [x for x in srcs if x.get("status") in ("degraded", "dead")]
    out = {}
    dst = os.path.join(OUTDIR, "SOURCE-VERDICTS.json")
    os.makedirs(OUTDIR, exist_ok=True)

    def dump():
        """逐条落盘：29 个源要跑很久，中途被超时打断也要保住已测结论。"""
        json.dump({"_ts": datetime.now().isoformat(timespec="seconds"),
                   "registry": os.path.relpath(path, ROOT), "verdicts": out},
                  open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    for x in srcs[:max_n]:
        url = x.get("url") or ""
        if not url.startswith("http"):
            out[x.get("name") or "?"] = {"verdict": "无 URL", "tier": x.get("tier")}
            dump()
            continue
        p = probe_isolated(url, timeout=75)
        out[x.get("name") or url] = {"url": url, "tier": x.get("tier"),
                                     "was": x.get("status"),
                                     "verdict": p.get("verdict", "超时/崩溃"),
                                     "feeds": p.get("feeds", 0),
                                     "list_links": p.get("list_links", 0),
                                     "article": p.get("article", 0),
                                     "why": p.get("why", "")}
        print("  %-18s %-8s → %-9s（feed %d / list %d / 正文 %d）"
              % (str(x.get("name"))[:18], x.get("status"),
                 out[x.get("name") or url]["verdict"],
                 out[x.get("name") or url]["feeds"],
                 out[x.get("name") or url]["list_links"],
                 out[x.get("name") or url]["article"]), flush=True)
        dump()
    print("[probe-registry] %d 条 → %s" % (len(out), os.path.relpath(dst, ROOT)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="只抓这一篇")
    ap.add_argument("--seeds", help="一行一个 URL 的文件")
    ap.add_argument("--feed", help="站点 URL：自动找 RSS 并抓正文")
    ap.add_argument("--list", help="列表页 URL：从列表里抽文章链接再逐篇抓")
    ap.add_argument("--sitemap", help="站点 URL：走 sitemap 取文章清单")
    ap.add_argument("--probe", help="探活：这个站能用哪种方式采")
    ap.add_argument("--probe-registry", action="store_true",
                    help="把源册里 degraded/dead 的源逐个探活，落 SOURCE-VERDICTS.json")
    ap.add_argument("--registry-all", action="store_true", help="配合 --probe-registry：连 ok 的源也探")
    ap.add_argument("--apply-verdicts", action="store_true",
                    help="把 SOURCE-VERDICTS.json 的实测结论回写进源册")
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
    if a.probe_registry:
        res = probe_registry(only_bad=not a.registry_all)
        return 0 if res else 2
    if a.apply_verdicts:
        return apply_verdicts()
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
    elif a.list:
        try:
            html = trafilatura.fetch_url(a.list)
        except Exception as e:                        # noqa: BLE001
            print("[generic] 列表页取不到：%s" % e, file=sys.stderr)
            return 2
        if not html:
            print("[generic] 列表页取不到（超时/403）", file=sys.stderr)
            return 2
        urls = page_links(html, a.list, limit=max(a.limit * 3, 30))
        if not urls:
            print("[generic] 列表页里没找到文章链接", file=sys.stderr)
            return 2
        print("[generic] 列表页给出 %d 条候选" % len(urls))
        src = "list"
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
