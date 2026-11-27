#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""网易新闻跟帖采集：中文互联网最老练的"抖机灵 + 短评论"语料。

为什么加这条（CEO 2026-11-26「扩大语料采集范围，优质渠道」）：
按"短、具体、有情绪、不总结"这条标准逐个实测，Steam（302→首页）、NGA（403）、
豆瓣小组（403）、虎扑移动端（壳页 8KB）都不通；**网易新闻跟帖是唯一打通且质量高的**。

实测样本（2026-11-26）：
  「咱文科毕业的看这篇直点头。当年全家让我考编，说那才叫体面，结果体面是给别人看的，
    累是自己扛的。」
  「最强的实习律师：张伟」
前者是带具体经历的长评论，后者是短梗——正是我们要补的两类。

两个必须记住的实现细节：
1. **接口返回是转义 JSON**（`\\x7B\\x22...`），直接 json.loads 会炸。要先
   `unicode_escape` 再按 latin-1 回解，才能把中文拿回来。
2. **不硬闯**：本文件只做通了的那个源。Steam/NGA/贴吧/微博被挡就记在矩阵里，不绕。

用法：
  python3 Tools/fleet/news_comments.py --self-test
  python3 Tools/fleet/news_comments.py --channels 3 --per-doc 3 --dry
  python3 Tools/fleet/news_comments.py --channels 6
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

from music_comments import write_rows, clean_and_filter, existing_hashes  # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PRODUCT = "a2869674571f77b5a0867c3d71db5856"
CHANNELS = [
    "https://news.163.com/",
    "https://tech.163.com/",
    "https://sports.163.com/",
    "https://ent.163.com/",
    "https://money.163.com/",
    "https://auto.163.com/",
]
CMT = ("https://comment.api.163.com/api/v1/products/%s/threads/%s/comments/newList"
       "?offset=%d&limit=%d&showLevelThreshold=72&headLimit=1&tailLimit=2&ibc=newspc")
GAP = 1.0


def _get(url, timeout=20, retries=2):
    last = None
    for _ in range(max(1, retries)):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Referer": "https://news.163.com/"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(GAP * 2)
    raise last


def decode_escaped(raw):
    """网易跟帖返回的是 `\\x7B\\x22...` 形式的转义 JSON，必须两步才能还原中文。"""
    s = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
    try:
        step = s.encode("utf-8").decode("unicode_escape")
        return step.encode("latin-1", "backslashreplace").decode("utf-8", "replace")
    except Exception:
        return s


def parse_comments(raw):
    """→ [{"text","likes"}]。字段是 comments 字典（按 id 索引），不是数组。"""
    try:
        d = json.loads(decode_escaped(raw))
    except Exception:
        return []
    out = []
    for _k, v in (d.get("comments") or {}).items():
        t = re.sub(r"\s+", " ", (v.get("content") or "")).strip()
        if t:
            out.append({"text": t, "likes": int(v.get("vote") or 0)})
    return out


def parse_docids(html):
    """从频道页取 docid（16 位大写字数字），保持出现顺序并去重。"""
    s = html.decode("utf-8", "replace") if isinstance(html, (bytes, bytearray)) else str(html)
    out, seen = [], set()
    for m in re.findall(r"/article/([A-Z0-9]{16})\.html", s):
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def collect(channels=3, per_doc=2, dry=False):
    errs, items = [], []
    docids = []
    for url in CHANNELS[:max(1, channels)]:
        try:
            docids += parse_docids(_get(url))
        except Exception as e:
            errs.append("%s 取不到：%s" % (url, type(e).__name__))
        time.sleep(GAP + random.uniform(0, 0.5))
    seen, uniq = set(), []
    for d in docids:
        if d not in seen:
            seen.add(d)
            uniq.append(d)

    have = None if dry else existing_hashes()
    total_new = 0
    for doc in uniq:
        batch = []
        for pg in range(max(1, per_doc)):
            try:
                batch += parse_comments(_get(CMT % (PRODUCT, doc, pg * 20, 20)))
            except Exception:
                break
            time.sleep(GAP + random.uniform(0, 0.5))
        if not batch:
            continue
        kept = clean_and_filter([{"text": x["text"], "likes": x["likes"],
                                  "song": doc, "platform": "netease_news"}
                                 for x in batch])
        for x in kept:
            x["seg_hint"] = "memer"     # 跟帖以短梗与抖机灵为主，归到 memer 段
        n, _r = write_rows(kept, dry=dry, have=have)
        total_new += n
    return {"docs": len(uniq), "new": total_new, "errs": errs[:5], "dry": dry}


def self_test():
    cases = []
    esc = r'\x7B\x22comments\x22\x3A\x7B\x221\x22\x3A\x7B\x22content\x22\x3A\x22\xE6\x9C\x80\xE5\xBC\xBA\x22\x2C\x22vote\x22\x3A7\x7D\x7D\x7D'
    got = parse_comments(esc.encode())
    cases.append(("转义 JSON 能解出中文", got and got[0]["text"] == "最强"))
    cases.append(("点赞数解析", got and got[0]["likes"] == 7))
    cases.append(("坏 JSON 返回空不造假", parse_comments(b"<html>") == []))
    html = b'<a href="/article/LBKRB9KU000181IU.html">a</a><a href="/article/LBKRB9KU000181IU.html">b</a><a href="/article/LB2OCU6S000181IU.html">c</a>'
    ids = parse_docids(html)
    cases.append(("docid 去重保序", ids == ["LBKRB9KU000181IU", "LB2OCU6S000181IU"]))
    cases.append(("无 docid 返回空", parse_docids(b"<html></html>") == []))
    ok = 0
    for name, val in cases:
        print("  [%s] %s" % ("PASS" if val else "FAIL", name))
        ok += 1 if val else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", type=int, default=3)
    ap.add_argument("--per-doc", type=int, default=2, help="每篇翻页数（20 条/页）")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    out = collect(channels=a.channels, per_doc=a.per_doc, dry=a.dry)
    print("[news] 文章 %d 篇 → 新入库 %d 条%s"
          % (out["docs"], out["new"], "（dry，未写）" if out["dry"] else ""))
    for e in out["errs"]:
        print("  ! %s" % e)
    return 0 if (out["new"] or out["dry"]) else 3


if __name__ == "__main__":
    sys.exit(main())
