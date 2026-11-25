#!/usr/bin/env python3
"""产业语料扩采：从纯静态垂类媒体按作者/两跳扩池抓正文（盖世汽车、第一电动）。

为什么走静态垂类源而不是继续磨公众号：
  公众号原文的「发现」通道全封（搜狗/百度/必应验证码，新榜/清博登录墙），
  而这两家是**纯静态**——盖世首页 26 个作者入口、作者页 30 篇、文章页有
  `<div id="ArticleContent">`；第一电动首页 21 条唯一文章链接、文章页正文与
  「新闻推荐」相关链接都在 HTML 里，全程不需要登录（2026-11-25 实测）。

诚实的代价：两家都是汽车供应链/行业媒体（B2B），文风偏行业通稿，
**不等于消费向公众号文笔**。所以：
  · 全部标 `source=<源名>`、`genre=industry`，训练集按 genre 单独排除；
  · 用途是「多作者 + 形态基线 + 行业事实素材」，不是学文笔；
  · 可训篇数（消费向观点稿）不会因为这里涨而变好看——两件事分开记，不合并报数。

用法：
  gzh_corpus_expand.py --source all --limit 40           # 两源各抓，单源上限 40 篇
  gzh_corpus_expand.py --source d1ev --limit 30          # 只跑第一电动
  gzh_corpus_expand.py --probe-parse https://example.com/ # 新站探活：判断值不值得接
  gzh_corpus_expand.py --migrate --drop-legacy           # 旧盖世文件并入后删除
  gzh_corpus_expand.py --self-test
退出码：0 成功 / 2 一篇没抓到 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.request
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
OUT = os.path.join(GZH, "ARTICLES-INDUSTRY.jsonl")     # 统一产业语料（一场一件）
LEGACY = os.path.join(GZH, "ARTICLES-GASGOO.jsonl")    # 旧名，仅用于一次性迁移
URLS = os.path.join(GZH, "URLS.jsonl")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
MIN_TEXT = 300        # 少于这么多字判为没抓到正文


def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def _uid(source, key):
    """跨源唯一：同一篇文章在任何入口都得到同一个 uid，且不同源不撞。

    只从**路径**里取数字，不从整串 URL 取。坑（2026-11-25 自检抓到）：
    `https://www.d1ev.com/news/shuju/100002` 整串取数字会得到 "1100002"——
    域名 `www.d1ev.com` 里的那个 "1" 也会被算进文章 id。同一篇换个域名
    （m.d1ev.com / 裸域）就成了另一篇文章，去重当场失效。
    """
    from urllib.parse import urlsplit
    path = urlsplit(key).path if "//" in (key or "") else (key or "")
    digits = re.sub(r"\D", "", path)
    tail = re.sub(r"\W", "", path)[-10:]
    return (str(source) + (digits or tail))[:16]


# ---------------- 盖世汽车（首页 → 作者页 → 文章） ----------------

def authors_from(html):
    """从首页/任意页抽作者主页 id（https://auto.gasgoo.com/user/<id>）。"""
    return list(dict.fromkeys(re.findall(r"auto\.gasgoo\.com/user/(\d{5,})", html)))


def articles_from_author(html):
    """从作者页抽文章链接与日期。URL 里带年月（/news/202611/...），可推导月份。"""
    out, seen = [], set()
    for m in re.finditer(r'href="(/news/(\d{6})/[^"#]+\.shtml)', html):
        path, ym = m.group(1), m.group(2)
        if path in seen:
            continue
        seen.add(path)
        out.append({"path": path, "ym": ym})
    return out


def gasgoo_article(html):
    """取标题/正文/日期。正文在 <div id="ArticleContent"> 里（实测）。"""
    title = ""
    m = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
    if m:
        title = m.group(1).strip()
    else:
        m = re.search(r"<h1[^>]*>([\s\S]{2,160}?)</h1>", html)
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""

    body = ""
    i = html.find('id="ArticleContent"')
    if i >= 0:
        seg = html[i:i + 60000]
        # 截到下一个大板块，避免把推荐位/评论吃进来
        for cut in ('<!-- /gasgoo-article', 'id="ArticleComment"', '<div class="article-tags'):
            j = seg.find(cut)
            if j > 0:
                seg = seg[:j]
                break
        ps = re.findall(r"<p[^>]*>([\s\S]{10,800}?)</p>", seg)
        body = "\n".join(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", p)).strip()
                         for p in ps)
        body = re.sub(r"\n{2,}", "\n", body).strip()

    date = ""
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})\s*\d{2}:\d{2}", html)
    if m:
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return {"title": title, "text": body, "date": date, "author": ""}


def gasgoo_uid(path):
    """盖世的历史 uid 规则（`ARTICLES-GASGOO.jsonl` 里 71 行都按它），不许改。"""
    return re.sub(r"\W", "", path)[-16:]


# ---------------- 第一电动（首页种子 → 文章页相关链接两跳） ----------------

D1EV_LINK = re.compile(r'href="(/news/[a-z]+/\d{4,})"')


def d1ev_links(html):
    """抽文章链接。同一篇会在页内出现多次（正文/推荐/评论锚点），按路径去重。"""
    return list(dict.fromkeys("https://www.d1ev.com" + p
                              for p in D1EV_LINK.findall(html)))


def d1ev_article(html):
    """标题取 <title>（<h1> 常被导航劫持成栏目标题，实测拿到的是「电动汽车」）；
    时间取 <time class="timeago" datetime>；作者取「作者：」；正文取 time 之后
    到 source--wrapper 之前的 <p>（实测 119 段 / 7011 字）。"""
    title = ""
    m = re.search(r"<title>([\s\S]{2,200}?)</title>", html)
    if m:
        title = re.sub(r"\s*[-_—]\s*第一电动网\s*$", "", m.group(1).strip()).strip()

    date = ""
    m = re.search(r'<time[^>]*datetime="(20\d{2})-(\d{2})-(\d{2})', html)
    if m:
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    author = ""
    m = re.search(r"作者[:：]\s*([^<\n]{2,20})", html)
    if m:
        author = m.group(1).strip()

    body = ""
    t = re.search(r"<time[^>]*>[\s\S]{0,80}?</time>", html)
    start = t.end() if t else 0
    end = html.find("source--wrapper", start)
    if end < 0:
        end = start + 60000
    seg = html[start:end]
    ps = re.findall(r"<p[^>]*>([\s\S]{5,2000}?)</p>", seg)
    txt = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", p)).strip() for p in ps]
    body = "\n".join(t for t in txt if len(t) >= 8)
    return {"title": title, "text": body, "date": date, "author": author}


# ---------------- 抓取主流程 ----------------

def _load_uids():
    out = set()
    for p in (OUT, LEGACY):
        try:
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line:
                    out.add(json.loads(line).get("_uid"))
        except FileNotFoundError:
            pass
    return out


def _emit(rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(URLS, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"_uid": r["_uid"], "url": r["url"],
                                "title": r["title"], "source": r["source"],
                                "mirror": True, "author_id": r.get("author_id"),
                                "found_at": r["fetched_at"]}, ensure_ascii=False) + "\n")


def _row(src, uid, url, art, author_id=""):
    return {"_uid": uid, "url": url, "title": (art["title"] or "")[:150],
            "text": art["text"], "publish_date": art["date"],
            "author": art.get("author") or "", "author_id": author_id,
            "words": len(re.sub(r"\s", "", art["text"])),
            "source": src, "mirror": True, "genre": "industry",
            "fetched_at": datetime.now().isoformat(timespec="seconds")}


def crawl_gasgoo(limit, per_author, delay, seen, verbose):
    stats = {"tried": 0, "ok": 0, "short": 0, "seeds": 0}
    home = get("https://auto.gasgoo.com/")
    aids = authors_from(home)
    stats["seeds"] = len(aids)
    rows = []
    for aid in aids:
        if len(rows) >= limit:
            break
        try:
            apage = get(f"https://auto.gasgoo.com/user/{aid}")
        except Exception:  # noqa: BLE001
            continue
        arts = articles_from_author(apage)[:per_author]
        if verbose:
            print(f"  盖世作者 {aid}: 页内 {len(articles_from_author(apage))} 篇，本轮取 {len(arts)}")
        for a in arts:
            if len(rows) >= limit:
                break
            uid = gasgoo_uid(a["path"])
            if uid in seen:
                continue
            stats["tried"] += 1
            url = "https://auto.gasgoo.com" + a["path"]
            try:
                art = gasgoo_article(get(url))
            except Exception:  # noqa: BLE001
                continue
            if len(art["text"]) < MIN_TEXT:
                stats["short"] += 1
                continue
            seen.add(uid)
            stats["ok"] += 1
            rows.append(_row("gasgoo", uid, url, art, aid))
            time.sleep(delay)
    return rows, stats


def _known_urls(source, host_kw, limit=200):
    """已知某源的文章 URL（从池子里读），当第二次以后的扩池跳板。"""
    out = []
    try:
        for line in open(URLS, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            u = r.get("url") or ""
            if host_kw in u and r.get("source") == source:
                out.append(u)
    except FileNotFoundError:
        pass
    return list(dict.fromkeys(out))[:limit]


def crawl_d1ev(limit, delay, seen, verbose, hops=1, reexpand=15):
    """首页种子 → 文章页；文章页的「新闻推荐」再进队列（默认 1 跳，够拿数百条）。

    第二跳的关键：首页 21 条抓完之后，如果只按「已采过就跳过」，这个源就成了一次性的。
    所以队列见底时拿**已知文章页当跳板**——不重复入库，只为把页内那 15 条相关链接挖出来
    （2026-11-25 实锚：首次接入挖了 25 篇后，第二轮直接 0 篇，就是这个坑）。
    """
    stats = {"tried": 0, "ok": 0, "short": 0, "seeds": 0, "reexpand": 0}
    queue = d1ev_links(get("https://www.d1ev.com/"))
    stats["seeds"] = len(queue)
    rows = []
    tried_urls = set()
    jumpboard = _known_urls("d1ev", "d1ev.com")

    def mine(html):
        for u in d1ev_links(html):
            if u not in tried_urls:
                queue.append(u)

    while len(rows) < limit:
        if not queue:
            # 队列见底：拿已知文章页当跳板扩池（有上限，不许无限自我拜访）
            if stats["reexpand"] >= reexpand or not jumpboard:
                break
            url = jumpboard.pop(0)
            stats["reexpand"] += 1
            try:
                mine(get(url))
            except Exception:  # noqa: BLE001
                continue
            time.sleep(delay)
            continue
        url = queue.pop(0)
        if url in tried_urls:
            continue
        tried_urls.add(url)
        uid = _uid("d1ev", url)
        if uid in seen:
            continue
        stats["tried"] += 1
        try:
            html = get(url)
        except Exception:  # noqa: BLE001
            continue
        art = d1ev_article(html)
        if len(art["text"]) < MIN_TEXT:
            stats["short"] += 1
            continue
        seen.add(uid)
        stats["ok"] += 1
        rows.append(_row("d1ev", uid, url, art))
        if hops > 0:
            mine(html)
        if verbose:
            print(f"  第一电动 {url[-30:]} → {len(art['text'])} 字，队列余 {len(queue)}")
        time.sleep(delay)
    return rows, stats


def crawl(source="all", limit=40, per_author=8, delay=1.0, verbose=True):
    seen = _load_uids()
    rows, allst = [], {}
    plan = ["gasgoo", "d1ev"] if source == "all" else [source]
    for src in plan:
        try:
            if src == "gasgoo":
                r, st = crawl_gasgoo(limit, per_author, delay, seen, verbose)
            else:
                r, st = crawl_d1ev(limit, delay, seen, verbose)
        except Exception as e:  # noqa: BLE001
            print(f"  {src} 取源失败：{type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
            r, st = [], {"tried": 0, "ok": 0, "short": 0, "err": type(e).__name__}
        allst[src] = st
        rows.extend(r)
    _emit(rows)
    return rows, allst


# ---------------- 迁移：旧盖世文件并入统一产业语料 ----------------

def reuid():
    """按修正后的 _uid 规则重写 d1ev 行的 uid（只动 d1ev，别的源原样）。

    为什么需要：2026-11-25 首次接入时 _uid 从整串 URL 取数字，域名里的 "1"
    被算进文章 id（d1ev1314686 而不是 d1ev314686）。规则一改，重采会当成新文章，
    所以必须把已入库的行一起改正，并检查不撞车。
    """
    fixed = {"articles": 0, "urls": 0, "collisions": []}
    for path, key in ((OUT, "articles"), (URLS, "urls")):
        if not os.path.exists(path):
            continue
        rows, seen_new = [], set()
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("source") == "d1ev":
                old = r.get("_uid")
                new = _uid("d1ev", r.get("url") or "")
                if old != new:
                    r["_uid"] = new
                    fixed[key] += 1
                if new in seen_new:
                    fixed["collisions"].append(new)
                seen_new.add(new)
            rows.append(r)
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[reuid] 文章 {fixed['articles']} 行 / 池 {fixed['urls']} 行已修正"
          f"｜撞车 {len(fixed['collisions'])}")
    return 2 if fixed["collisions"] else 0


def migrate(drop_legacy=False):
    """旧文件是本会话早期产物（71 行，uid 规则与现在 gasgoo 分支一致）。
    一场一件：并入后旧文件只剩冗余，按需删除（git 有历史，删了也能找回）。"""
    if not os.path.exists(LEGACY):
        print("[migrate] 无旧文件，跳过")
        return 0
    have = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            line = line.strip()
            if line:
                have.add(json.loads(line).get("_uid"))
    add = []
    for line in open(LEGACY, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("_uid") in have:
            continue
        have.add(r.get("_uid"))
        add.append(r)
    if add:
        with open(OUT, "a", encoding="utf-8") as f:
            for r in add:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[migrate] 并入 {len(add)} 行 → {os.path.relpath(OUT, ROOT)}")
    if drop_legacy:
        n_out = sum(1 for l in open(OUT, encoding="utf-8") if l.strip())
        n_old = sum(1 for l in open(LEGACY, encoding="utf-8") if l.strip())
        if n_out >= n_old:
            os.remove(LEGACY)
            print(f"[migrate] 已删除旧文件（新文件 {n_out} 行 ≥ 旧 {n_old} 行）")
        else:
            print(f"[migrate] 拒绝删除：新文件 {n_out} 行 < 旧 {n_old} 行", file=sys.stderr)
            return 2
    return 0


# ---------------- 通用探活：给一个新站，值不值得接 ----------------

def probe_parse(url, verbose=True):
    """新站探活：列表结构（有没有文章链接）+ 正文可提取性 + 锚点重复率。

    存在的意义：扩源不该靠我逐个手测。给一个首页 URL，一眼看出
    「有 21 条链接 / 正文 7011 字」还是「0 条链接，别浪费时间」。
    """
    out = {"url": url, "ok": False, "bytes": 0, "links": 0, "uniq": 0,
           "anchor_dups": 0, "body_chars": 0, "paras": 0, "title": "", "why": ""}
    try:
        html = get(url)
    except Exception as e:  # noqa: BLE001
        out["why"] = "%s: %s" % (type(e).__name__, str(e)[:80])
        if verbose:
            print(json.dumps(out, ensure_ascii=False, indent=1))
        return out
    out["bytes"] = len(html)
    m = re.search(r"<title>([\s\S]{2,200}?)</title>", html)
    out["title"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

    # 通用文章链接识别：/任意段/<4位以上数字>，带 #锚点 的算重复
    raw = re.findall(r'href="(https?://[^"]+/[a-z]{2,10}/\d{4,})', html)
    raw += ["https://x" + p for p in re.findall(r'href="(/[a-z]{2,10}/[a-z0-9]{2,10}/\d{4,})"', html)]
    out["links"] = len(raw)
    out["uniq"] = len(set(raw))
    out["anchor_dups"] = len(re.findall(r'href="[^"]+/[a-z]{2,10}/\d{4,}#', html))

    # 正文：先试已知两家的提取器，再退回通用 <p> 统计
    best = 0
    for fn in (d1ev_article, gasgoo_article):
        try:
            art = fn(html)
            n = len(art["text"])
            if n > best:
                best, out["paras"] = n, art["text"].count("\n") + 1
        except Exception:  # noqa: BLE001
            pass
    out["body_chars"] = best
    out["ok"] = out["uniq"] >= 5 or out["body_chars"] >= MIN_TEXT
    if not out["ok"]:
        out["why"] = ("无文章链接且无正文" if not out["uniq"] and not out["body_chars"]
                      else "链接/正文都未达门槛")
    if verbose:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    return out


# ---------------- 自检 ----------------

HOME_HTML = """
<a href="https://auto.gasgoo.com/user/10195079">周晓莺</a>
<a href="https://auto.gasgoo.com/user/10759615">Sia</a>
<a href="https://auto.gasgoo.com/user/10195079">周晓莺（重复）</a>
"""
AUTHOR_HTML = """
<a href="/news/202611/11I70477636C1213.shtml#nav">a</a>
<a href="/news/202611/11I70477636C1213.shtml#SOHUCS">同一篇</a>
<a href="/news/202611/18I70478412C101.shtml">b</a>
"""
ARTICLE_HTML = """
<meta property="og:title" content="富士康收购索尼半导体汽车摄像头模组业务" />
<span>2026-11-18 17:37</span>
<div id="ArticleContent" class="contentDetailed"><p>盖世汽车讯 鸿海科技集团宣布收购索尼半导体汽车摄像头模组业务，交易金额约 72.4 亿日元，
这是今年第三笔汽车电子资产交易。</p><p>从产业链看，汽车摄像头的单车价值量正在从 200 元抬升到 600 元附近。</p></div>
<footer>广告位</footer>
<div id="ArticleComment">评论不该被吃进来</div>
"""

D1EV_LIST_HTML = """
<a href="/news/shuju/312498">榜单一</a>
<a href="/news/shuju/312498#comment">同一篇的评论锚点</a>
<a href="/news/qiye/316438">稿二</a>
<a href="/news">频道页不算文章</a>
"""
D1EV_ARTICLE_HTML = """
<title>智驾天梯榜（2026年8月） - 第一电动网</title>
<h1>电动汽车</h1>
<time class="timeago" datetime="2026-09-13 14:05" title="2026-09-13 14:05">2026-09-13</time>
<p>这张榜单不会稳定太久。过去比的是能不能开进城区、跑完全程，
接下来比的是谁能把百公里级的安全能力推向千公里、万公里。</p>
<p>榜单的价值正来自反复验证，欢迎各位车主自行实测核验、对比交流。</p>
<div class="source--wrapper">
  <p class="newscon_source">来源：第一电动网</p>
  <p class="newscon_source">作者： 第一电动编辑部</p>
  <p class="newscon_source">本文地址：<span id="localSite">https://www.d1ev.com/news/shuju/312498</span></p>
</div>
<section class="articleList"><ul class="content_list" id="recommendNews"></ul></section>
"""


def self_test():
    global URLS
    fails = []

    # —— 盖世分支（回归，不许因为改成多源而坏掉）——
    aids = authors_from(HOME_HTML)
    if aids != ["10195079", "10759615"]:
        fails.append(f"盖世作者去重失败：{aids}")

    arts = articles_from_author(AUTHOR_HTML)
    if len(arts) != 2:
        fails.append(f"盖世文章去重失败（#nav/#SOHUCS 应合并）：{len(arts)}")

    art = gasgoo_article(ARTICLE_HTML)
    if "富士康" not in art["title"]:
        fails.append("盖世标题抽取失败")
    if "72.4 亿日元" not in art["text"]:
        fails.append("盖世正文未取到关键句")
    if "广告位" in art["text"] or "评论不该被吃进来" in art["text"]:
        fails.append("盖世正文越界吃进了页脚/评论")
    if art["date"] != "2026-11-18":
        fails.append(f"盖世日期抽取失败：{art['date']}")
    bad = gasgoo_article("<html><body><p>随便一段话随便一段话随便一段话</p></body></html>")
    if bad["text"]:
        fails.append("负控[盖世无容器] 仍抽出了正文")

    # —— 第一电动分支 ——
    links = d1ev_links(D1EV_LIST_HTML)
    if len(links) != 2:
        fails.append(f"第一电动链接去重失败（#comment 应合并）：{len(links)}")
    if not all(u.startswith("https://www.d1ev.com/news/") for u in links):
        fails.append(f"第一电动链接未补绝对域名：{links}")
    if any(u.rstrip("/").endswith("/news") for u in links):
        fails.append("频道页被当成文章（应要求 /news/<栏目>/<id>）")

    d = d1ev_article(D1EV_ARTICLE_HTML)
    if d["title"] != "智驾天梯榜（2026年8月）":
        fails.append(f"第一电动标题未剥离站名后缀：{d['title']!r}")
    if d["date"] != "2026-09-13":
        fails.append(f"第一电动日期抽取失败：{d['date']}")
    if d["author"] != "第一电动编辑部":
        fails.append(f"第一电动作者抽取失败：{d['author']!r}")
    if "能不能开进城区" not in d["text"]:
        fails.append("第一电动正文未取到关键句")
    if "来源：第一电动网" in d["text"] or "本文地址" in d["text"]:
        fails.append("第一电动正文越界吃进了署名区")
    if "<p>" in d["text"]:
        fails.append("第一电动正文残留标签")

    # —— uid 契约 ——
    if _uid("d1ev", "https://www.d1ev.com/news/shuju/312498") != \
            _uid("d1ev", "https://www.d1ev.com/news/shuju/312498#comment"):
        fails.append("第一电动同文不同锚点得到不同 uid")
    if _uid("d1ev", "/news/shuju/312498") == _uid("gasgoo", "/news/shuju/312498"):
        fails.append("负控[跨源] 不同源同数字串撞了同一个 uid")
    if len(gasgoo_uid("/news/202611/11I70477636C1213.shtml")) != 16:
        fails.append("盖世 uid 长度不是 16（与历史语料对不上）")
    # 死锚：这条 uid 是历史 71 行里真实存在的（ARTICLES-GASGOO 首行），
    # 一旦规则被改动，历史语料立刻对不上，必须当场变红。
    if gasgoo_uid("/news/202611/25I70479059C108.shtml") != "0479059C108shtml":
        fails.append("盖世 uid 规则偏离历史语料（0479059C108shtml）")

    # —— 负控：探活必须能对空页面判红 ——
    real_get = globals()["get"]
    try:
        globals()["get"] = lambda u, timeout=20: "<html><title>404</title><body>找不到</body></html>"
        p = probe_parse("https://example.com/nothing", verbose=False)
        if p["ok"]:
            fails.append("负控[空站] 探活仍判通过")
    finally:
        globals()["get"] = real_get

    # —— 第二轮扩池：首页种子都采过时，必须靠已知文章页当跳板挖出新链接 ——
    # 实锚 2026-11-25：首次接入采了 25 篇，第二轮试 0 篇成功 0 篇——首页 21 条全在库里，
    # 缺了「跳板」这一步，这个源就成了一次性的。
    saved_urls = URLS
    URLS = os.path.join(tempfile.mkdtemp(prefix="d1ev-"), "urls.jsonl")
    with open(URLS, "w", encoding="utf-8") as f:
        f.write(json.dumps({"uid": "x", "url": "https://www.d1ev.com/news/shuju/100001",
                            "source": "d1ev"}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"uid": "y", "url": "https://auto.gasgoo.com/news/202611/z.shtml",
                            "source": "gasgoo"}, ensure_ascii=False) + "\n")
    body = "<p>" + "行业正文写在这里，足够长才能过 MIN_TEXT 门槛。" * 40 + "</p>"
    fixture = {
        "https://www.d1ev.com/": '<a href="/news/shuju/100001">首页种子</a>',
        "https://www.d1ev.com/news/shuju/100001":
            '<title>跳板文 - 第一电动网</title><time datetime="2026-11-20 10:00">x</time>'
            + body + '<a href="/news/shuju/100002">相关推荐</a>',
        "https://www.d1ev.com/news/shuju/100002":
            '<title>新挖到的稿 - 第一电动网</title><time datetime="2026-11-21 10:00">x</time>'
            + body + '<div class="source--wrapper">作者： 测试作者</div>',
    }
    try:
        globals()["get"] = lambda u, timeout=20: fixture[u]
        seen2 = {_uid("d1ev", "https://www.d1ev.com/news/shuju/100001")}
        rows2, st2 = crawl_d1ev(limit=1, delay=0, seen=seen2, verbose=False)
        if len(rows2) != 1 or rows2[0]["_uid"] != _uid("d1ev", "/news/shuju/100002"):
            fails.append(f"第二轮扩池没挖到新稿：{[r['url'] for r in rows2]}")
        if st2.get("reexpand", 0) < 1:
            fails.append("第二轮扩池没有走跳板（reexpand=0）")
        if _known_urls("d1ev", "d1ev.com") != ["https://www.d1ev.com/news/shuju/100001"]:
            fails.append("跳板清单混进了别的源")
    finally:
        globals()["get"] = real_get
        URLS = saved_urls

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK（盖世回归+越界负控 / 第一电动链接·标题·日期·作者·正文·不越界 / "
          "uid 同文同源·跨源不撞 / 第二轮跳板扩池 / 探活空站判红）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="all", choices=["gasgoo", "d1ev", "all"])
    ap.add_argument("--limit", type=int, default=40, help="单源本轮最多入库几篇")
    ap.add_argument("--per-author", type=int, default=8)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--probe-parse", metavar="URL", help="新站探活：看有没有列表结构/正文")
    ap.add_argument("--migrate", action="store_true")
    ap.add_argument("--reuid", action="store_true", help="按修正后的规则重写 d1ev 行 uid")
    ap.add_argument("--drop-legacy", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.probe_parse:
        p = probe_parse(a.probe_parse)
        return 0 if p["ok"] else 1
    if a.migrate:
        return migrate(drop_legacy=a.drop_legacy)
    if a.reuid:
        return reuid()

    rows, st = crawl(a.source, a.limit, a.per_author, a.delay)
    tot_ok = sum(s.get("ok", 0) for s in st.values())
    for src, s in st.items():
        print(f"[{src}] 种子 {s.get('seeds', 0)}｜试 {s.get('tried', 0)} → 成功 {s.get('ok', 0)}"
              f"｜过短丢弃 {s.get('short', 0)}")
    print(f"[合计] 新增 {tot_ok} 篇 → {os.path.relpath(OUT, ROOT)}")
    if rows:
        avg = sum(r["words"] for r in rows) / len(rows)
        srcs = {}
        for r in rows:
            srcs[r["source"]] = srcs.get(r["source"], 0) + 1
        print(f"[形态] 平均 {avg:.0f} 字｜构成 {srcs}（判据：>300 字才算抓到）")
        print("[口径] 这批全是 genre=industry 产业稿，**不进文笔训练**，只做形态基线与事实素材")
    return 0 if tot_ok else 2


if __name__ == "__main__":
    sys.exit(main())
