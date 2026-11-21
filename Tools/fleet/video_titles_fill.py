#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""video_titles_fill.py — 给只有 URL 没有标题的视频补标题与简介（走公网 view 接口）。

为什么需要（2026-11-21 面清单 F01）：可用视频源 106 条，其中 **65 条只有 URL**。
没有标题 → 自举时只能编题、内容简报缺一半 → 评论没法"看着片子说"。
标题其实公网就有（`x/web-interface/view?bvid=…`，不需要登录、不需要浏览器），
以前没补是因为采集侧只存了 thread URL。

做法：读 VIDEO-BRIEFS.json 里 has_title=false 的 URL → 调 view 接口 → 写回
VIDEO-TITLES.json（title/desc/bvid/dur）。限速 0.7s，失败重试一次，全程落计数。

用法
  python3 Tools/fleet/video_titles_fill.py            # 补缺
  python3 Tools/fleet/video_titles_fill.py --limit 5  # 先试 5 条
  python3 Tools/fleet/video_titles_fill.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
BRIEFS = os.path.join(SOCIAL, "VIDEO-BRIEFS.json")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
API = "https://api.bilibili.com/x/web-interface/view"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def bvid_of(url):
    m = re.search(r"(BV[0-9A-Za-z]{10})", url or "")
    return m.group(1) if m else ""


def fetch(bvid, timeout=12):
    q = urllib.parse.urlencode({"bvid": bvid})
    req = urllib.request.Request(API + "?" + q, headers={"User-Agent": UA,
                                                        "Referer": "https://www.bilibili.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode() or "{}")
    if d.get("code") != 0:
        return None
    v = d.get("data") or {}
    return {"title": (v.get("title") or "").strip(),
            "desc": (v.get("desc") or "").strip(),
            "bvid": bvid,
            "dur": v.get("duration")}


def run(limit=0, sleep_s=0.7):
    try:
        briefs = (json.load(open(BRIEFS, encoding="utf-8")).get("briefs") or {})
    except Exception:
        return {"error": "先跑 video_brief.py --build"}
    try:
        titles = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        titles = {}
    todo = [u for u, b in briefs.items() if not b.get("has_title") or not (b.get("title") or "")]
    todo = [u for u in todo if u not in titles or not (titles[u] or {}).get("title")]
    if limit:
        todo = todo[:limit]
    ok = fail = 0
    fails = []
    for u in todo:
        bv = bvid_of(u)
        if not bv:
            fail += 1
            fails.append((u, "无 bvid"))
            continue
        got = None
        for attempt in range(2):
            try:
                got = fetch(bv)
                break
            except urllib.error.HTTPError as e:
                if e.code in (412, 429):
                    time.sleep(3 + attempt * 3)      # 被限流就等，不硬撞
                    continue
                fails.append((u, "http %d" % e.code))
                break
            except Exception as e:
                fails.append((u, "%s" % type(e).__name__))
                break
        if got and got.get("title"):
            titles[u] = dict(titles.get(u) or {}, **{k: v for k, v in got.items() if v})
            ok += 1
        else:
            fail += 1
        time.sleep(sleep_s)
    if ok:
        json.dump(titles, open(TITLES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"todo": len(todo), "ok": ok, "fail": fail,
            "titles_total": len(titles),
            "with_title": sum(1 for v in titles.values() if (v or {}).get("title")),
            "fails": fails[:5]}


def self_test():
    """负控：URL 里必须能取到 bvid；取不到要判失败而不是猜。"""
    ok1 = bvid_of("https://www.bilibili.com/video/BV18a4y1g7xc/") == "BV18a4y1g7xc"
    ok2 = bvid_of("https://example.com/x") == ""
    ok3 = bvid_of("") == ""
    ok = ok1 and ok2 and ok3
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "正常URL": ok1,
                      "无bvid": ok2 and ok3}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.7)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    print(json.dumps(run(a.limit, a.sleep), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
