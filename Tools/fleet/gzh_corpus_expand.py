#!/usr/bin/env python3
"""语料扩采：从静态可读的垂类媒体（目前是盖世汽车）按作者抓正文。

为什么选盖世而不是继续磨公众号：
  公众号原文的「发现」通道全封（搜狗/百度/必应验证码，新榜/清博登录墙），
  而盖世汽车是**纯静态**——首页 26 个作者入口、每个作者页 30 篇、文章页有
  `<div id="ArticleContent">` 正文容器，全程不需要登录（2026-11-25 实测）。

诚实的代价：盖世是汽车供应链/行业媒体（B2B），文风偏行业通稿，
**不等于消费向公众号文笔**。所以：
  · 它的稿子标 `source=gasgoo`、`genre=industry`，训练时可单独排除；
  · 主要用途是「多作者 + 形态基线 + 行业事实素材」，不是学文笔。

用法：
  gzh_corpus_expand.py --authors 5 --per-author 6        # 抓 5 个作者各 6 篇
  gzh_corpus_expand.py --authors 26 --per-author 30 --all  # 全量（约 780 篇）
  gzh_corpus_expand.py --self-test
退出码：0 成功 / 2 部分失败 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
OUT = os.path.join(GZH, "ARTICLES-GASGOO.jsonl")
URLS = os.path.join(GZH, "URLS.jsonl")
HOME = "https://auto.gasgoo.com/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
MIN_TEXT = 300        # 少于这么多字判为没抓到正文


def get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


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


def extract_article(html):
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
    return {"title": title, "text": body, "date": date}


def crawl(n_authors=5, per_author=6, delay=1.0, verbose=True):
    """抓取主流程。返回 (rows, stats)。失败不抛，计入 stats。"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    seen_uids = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            try:
                seen_uids.add(json.loads(line).get("_uid"))
            except Exception:  # noqa: BLE001
                pass

    stats = {"authors_ok": 0, "authors_fail": 0, "articles_tried": 0,
             "articles_ok": 0, "too_short": 0}
    rows = []
    try:
        home = get(HOME)
    except Exception as e:  # noqa: BLE001
        print(f"首页取不到：{type(e).__name__}", file=sys.stderr)
        return [], stats
    aids = authors_from(home)[:n_authors]
    if verbose:
        print(f"首页发现作者 {len(authors_from(home))} 个，本轮取前 {len(aids)} 个")

    for aid in aids:
        try:
            apage = get(f"https://auto.gasgoo.com/user/{aid}")
            stats["authors_ok"] += 1
        except Exception:  # noqa: BLE001
            stats["authors_fail"] += 1
            continue
        arts = articles_from_author(apage)[:per_author]
        if verbose:
            print(f"  作者 {aid}: {len(articles_from_author(apage))} 篇，本轮取 {len(arts)}")
        for a in arts:
            url = "https://auto.gasgoo.com" + a["path"]
            uid = re.sub(r"\W", "", a["path"])[-16:]
            if uid in seen_uids:
                continue
            stats["articles_tried"] += 1
            try:
                art = extract_article(get(url))
            except Exception:  # noqa: BLE001
                continue
            if len(art["text"]) < MIN_TEXT:
                stats["too_short"] += 1
                continue
            seen_uids.add(uid)
            stats["articles_ok"] += 1
            rows.append({"_uid": uid, "url": url, "title": art["title"][:150],
                         "text": art["text"], "publish_date": art["date"],
                         "words": len(re.sub(r"\s", "", art["text"])),
                         "author_id": aid, "source": "gasgoo", "mirror": True,
                         "genre": "industry",
                         "fetched_at": datetime.now().isoformat(timespec="seconds")})
            time.sleep(delay)
        time.sleep(delay)

    if rows:
        with open(OUT, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(URLS, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps({"_uid": r["_uid"], "url": r["url"],
                                    "title": r["title"], "source": "gasgoo",
                                    "mirror": True, "author_id": r["author_id"],
                                    "found_at": r["fetched_at"]}, ensure_ascii=False) + "\n")
    return rows, stats


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


def self_test():
    fails = []
    aids = authors_from(HOME_HTML)
    if aids != ["10195079", "10759615"]:
        fails.append(f"作者去重失败：{aids}")

    arts = articles_from_author(AUTHOR_HTML)
    if len(arts) != 2:
        fails.append(f"文章去重失败（#nav/#SOHUCS 应合并）：{len(arts)}")

    art = extract_article(ARTICLE_HTML)
    if "富士康" not in art["title"]:
        fails.append("标题抽取失败")
    if "72.4 亿日元" not in art["text"]:
        fails.append("正文未取到关键句")
    if "广告位" in art["text"] or "评论不该被吃进来" in art["text"]:
        fails.append("正文越界吃进了页脚/评论")
    if art["date"] != "2026-11-18":
        fails.append(f"日期抽取失败：{art['date']}")

    # 负控：没有正文容器时必须返回空而不是乱抓
    bad = extract_article("<html><body><p>随便一段话随便一段话随便一段话</p></body></html>")
    if bad["text"]:
        fails.append("负控[无容器] 仍抽出了正文")

    # 负控：作者页没有文章链接时返回空
    if articles_from_author("<html></html>"):
        fails.append("负控[空作者页] 未返回空")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 6/6  (作者去重/文章去重/标题/正文/不越界/日期 + 2 负控)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--authors", type=int, default=5)
    ap.add_argument("--per-author", type=int, default=6)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    rows, st = crawl(a.authors, a.per_author, a.delay)
    print(f"\n作者 {st['authors_ok']} 成功 / {st['authors_fail']} 失败")
    print(f"文章 试 {st['articles_tried']} → 成功 {st['articles_ok']} "
          f"/ 正文过短丢弃 {st['too_short']}")
    print(f"落盘 {OUT}（累计 {len(rows)} 篇新增）")
    if st["articles_ok"]:
        avg = sum(r["words"] for r in rows) / len(rows)
        print(f"平均正文 {avg:.0f} 字（判据：>300 才算抓到）")
    return 0 if st["articles_ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
