#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""社区短评采集：豆瓣读书（已验证可用）。

为什么补这条（CEO 2026-11-26「去找其他的平台语料投喂训练，要高质量的，打开思路」）：
养号要的是"像人说话"，所以只收**评论区短回复**，不收长文章。按这个标准筛过一圈实测：

| 平台 | 结果 | 说明 |
|---|---|---|
| 豆瓣·读书短评 | ✅ 可用 | 质量最高：「看四十四次日落的小王子，他有多么难过」 |
| 豆瓣·电影短评 | ❌ 302/反爬 | 加 Referer 仍返回 3KB 提示页 |
| 百度贴吧 | ❌ 403 | 列表页直接挡 |
| 微博 | ❌ 302 | 需登录态 cookie |
| 小红书 / 抖音 | ❌ 强签名 | 不碰 |
| 虎扑 | ⚠️ 200 但前端渲染 | 静态 HTML 里没有帖子正文，需另想办法 |

所以先只把**通了且质量最高**的那条做成能力，剩下的按"能通再上"排队，不做无用功。

豆瓣读书 Top250 可以自动发现（每页 25 本，10 页共 250 本），
每本短评页 20 条 → 理论池 5000 条。这是目前找到的最好的中文短评语料。

用法：
  python3 Tools/fleet/forum_comments.py --self-test
  python3 Tools/fleet/forum_comments.py --douban-books --pages 2 --books 10   # 小批验证
  python3 Tools/fleet/forum_comments.py --douban-books --pages 10            # 全量 250 本
  python3 Tools/fleet/forum_comments.py --douban-books --dry                 # 只看量不落盘
"""
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
sys.path.insert(0, HERE)

from music_comments import (quality_ok, write_rows, _h, clean_and_filter)  # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TOP_URL = "https://book.douban.com/top250?start=%d"
CMT_URL = "https://book.douban.com/subject/%s/comments/?start=%d"
STATE = os.path.join(ROOT, ".codely-cli", "state", "FORUM-PROGRESS.json")
# 豆瓣对高频很敏感：1.2s + 抖动。宁可慢，不要被封。
GAP = 1.2


def _get(url, referer="https://book.douban.com/", timeout=25, retries=2):
    last = None
    for _ in range(max(1, retries)):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if getattr(r, "status", 200) != 200:
                    raise RuntimeError("http %s" % r.status)
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(GAP * 2)
    raise last


def parse_top_books(html):
    """从 Top250 列表页取 subject id（保持页面顺序，去重）。"""
    ids, seen = [], set()
    for m in re.findall(r"subject/(\d+)/", html or ""):
        if m not in seen:
            seen.add(m)
            ids.append(m)
    return ids


def parse_short_comments(html):
    """短评正文在 <span class="short">；去掉内嵌标签与多余空白。"""
    out = []
    for raw in re.findall(r'<span class="short">(.*?)</span>', html or "", re.S):
        t = re.sub(r"<[^>]+>", "", raw)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append(t)
    return out


def douban_books(pages=10, books=0, per_book=2, dry=False):
    """Top250 → 每本采 per_book 页短评（20 条/页）。books>0 时限量（便于小批验证）。"""
    got_ids, errs = [], []
    for p in range(max(1, pages)):
        try:
            got_ids += parse_top_books(_get(TOP_URL % (p * 25)))
        except Exception as e:
            errs.append("Top250 第 %d 页失败：%s" % (p, type(e).__name__))
            break
        time.sleep(GAP + random.uniform(0, 0.5))
    seen, uniq = set(), []
    for i in got_ids:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    if books:
        uniq = uniq[:books]

    items = []
    for bid in uniq:
        for pg in range(max(1, per_book)):
            try:
                html = _get(CMT_URL % (bid, pg * 20))
            except Exception as e:
                errs.append("书目 %s 第 %d 页：%s" % (bid, pg, type(e).__name__))
                break
            for t in parse_short_comments(html):
                items.append({"text": t, "likes": 0, "song": bid,
                              "platform": "douban_book"})
            time.sleep(GAP + random.uniform(0, 0.6))
    kept = [x for x in clean_and_filter(items) if quality_ok(x["text"])]
    # 豆瓣短评进 critic 段：有观点、有判断，正好补现在只有 157 行的 critic
    for x in kept:
        x["seg_hint"] = "critic"
    n, _rows = write_rows(kept, dry=dry)
    return {"books": len(uniq), "raw": len(items), "kept": len(kept), "new": n,
            "errs": errs[:5], "dry": dry}


def self_test():
    cases = []
    top = '<a href="https://book.douban.com/subject/1084336/">小王子</a>' \
          '<a href="https://book.douban.com/subject/1007305/">红楼梦</a>' \
          '<a href="https://book.douban.com/subject/1084336/">重复</a>'
    ids = parse_top_books(top)
    cases.append(("Top250 解析去重保序", ids == ["1084336", "1007305"]))

    cmt = ('<span class="short">看四十四次日落的小王子，他有多么难过。</span>'
           '<span class="short">  <b>加粗</b> 多余  空白 </span>')
    got = parse_short_comments(cmt)
    cases.append(("短评解析去标签", got and got[0].startswith("看四十四次日落")))
    cases.append(("多余空白被压平", got[1] == "加粗 多余 空白"))

    # 负控：页面没有短评时必须返回空，不许造
    cases.append(("空页面不造假", parse_short_comments("<html></html>") == []))
    # 负控：挡板页（3KB 提示页）也必须是空
    cases.append(("反爬提示页返回空", parse_short_comments("<p>请求异常</p>") == []))
    ok = 0
    for name, val in cases:
        print("  [%s] %s" % ("PASS" if val else "FAIL", name))
        ok += 1 if val else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--douban-books", action="store_true")
    ap.add_argument("--pages", type=int, default=10, help="Top250 列表页数（每页 25 本）")
    ap.add_argument("--books", type=int, default=0, help="最多采几本（0=全部）")
    ap.add_argument("--per-book", type=int, default=2, help="每本采几页短评（20 条/页）")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.douban_books:
        print("[forum] 目前只实现 --douban-books（其余平台实测被挡，见文件头）")
        return 2
    out = douban_books(pages=a.pages, books=a.books, per_book=a.per_book, dry=a.dry)
    print("[forum] 书 %d 本 → 抓 %d 条 → 清洗后 %d → 新入库 %d%s"
          % (out["books"], out["raw"], out["kept"], out["new"],
             "（dry，未写）" if out["dry"] else ""))
    for e in out["errs"]:
        print("  ! %s" % e)
    return 0 if (out["new"] or out["dry"]) else 3


if __name__ == "__main__":
    sys.exit(main())
