#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_expand.py — 用「相关视频」接口扩内容池（高频的前提是池子够大）。

为什么要它（2026-11-22 实锚）：频率上限不是政策给的，是**内容池**给的。
池内 108 条 + 「同视频 7 天 ≤1 条评论」= 全账号每天最多 15 条、每号 7.7 条；
再往上加配额只会变成同一条视频反复评论（AC05 已抓到 3 次重复），那才是机器味。

入口选择：走 api.bilibili.com/x/web-interface/archive/related（公开、无需登录、
不占浏览器 profile），一次拿 40 条相关视频；按人设话题词 + 播放量带 + 时长带过滤，
只收"中腰部"（太凉的没人看、太爆的评论沉底，都不适合养号）。

用法：
  python3 Tools/fleet/pool_expand.py --dry-run          # 只看能扩多少
  python3 Tools/fleet/pool_expand.py --limit 200        # 真写回 VIDEO-TITLES
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
PERSONAS = os.path.join(SOCIAL, "ACCOUNT-PERSONAS.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
REL = "https://api.bilibili.com/x/web-interface/archive/related?bvid=%s"

VIEW_MIN, VIEW_MAX = 50_000, 5_000_000     # 中腰部：有人看，评论不沉底
DUR_MIN, DUR_MAX = 120, 1800              # 2–30 分钟


def _get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Referer": "https://www.bilibili.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def topics():
    d = json.load(open(PERSONAS, encoding="utf-8")) or {}
    out = set()
    for k, v in d.items():
        if isinstance(v, dict):
            for t in (v.get("topics") or []):
                if t:
                    out.add(str(t))
    return sorted(out)


def _related(bv, tries=2):
    """取一条视频的相关列表；412/超时就退避重试一次。并发下这条要幂等且不抛。"""
    for i in range(max(1, tries)):
        try:
            j = _get(REL % urllib.parse.quote(bv))
            if j.get("code") in (0, None):
                return bv, (j.get("data") or [])
        except Exception:
            pass
        time.sleep(2 + 2 * i)
    return bv, []


def expand(limit=200, dry=False, sleep_s=0.0, workers=10):
    vids = json.load(open(TITLES, encoding="utf-8")) or {}
    have = set((v or {}).get("bvid") for v in vids.values() if v)
    words = topics()
    print("[pool] 现有 %d 条；话题词 %d 个：%s" % (len(vids), len(words), ",".join(words[:8])))

    cands = {}
    # 并发取相关列表：实测单条 121ms、10 并发全成功、0.29s 拿 16 条；
    # 串行 + sleep 0.35s 时 808 条要 6 分钟，并行后 30–60 秒（10 核 8 性能核）。
    bvs = [(u, (v or {}).get("bvid")) for u, v in vids.items() if (v or {}).get("bvid")]
    got = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for bv, data in ex.map(lambda kv: _related(kv[1]), bvs):
            got[bv] = data
    for i, (u, bv) in enumerate(bvs):
        for x in (got.get(bv) or []):
            nb = x.get("bvid")
            st = x.get("stat") or {}
            view = st.get("view") or 0
            dur = x.get("duration") or 0
            title = (x.get("title") or "").strip()
            if not nb or nb in have or nb in cands or not title:
                continue
            if not (VIEW_MIN <= view <= VIEW_MAX) or not (DUR_MIN <= dur <= DUR_MAX):
                continue
            hits = sum(1 for w in words if w and w in title)
            if not hits:
                continue
            cands[nb] = {"title": title, "bvid": nb, "desc": (x.get("desc") or "")[:400],
                         "dur": dur, "_view": view, "_hits": hits}
        if i and i % 100 == 0:
            print("[pool] 已扫 %d/%d 源，新候选 %d" % (i, len(bvs), len(cands)))
        if sleep_s:
            time.sleep(sleep_s)

    ranked = sorted(cands.values(), key=lambda c: (-c["_hits"], -c["_view"]))[:limit]
    print("[pool] 候选 %d 条，取 %d 条（按话题命中数、播放量排序）" % (len(cands), len(ranked)))
    if dry:
        for c in ranked[:5]:
            print("   + %s %s（播放 %d，命中 %d）" % (c["bvid"], c["title"][:26], c["_view"], c["_hits"]))
        return 0, len(vids), len(ranked)

    for c in ranked:
        url = "https://www.bilibili.com/video/%s/" % c["bvid"]
        vids[url] = {"title": c["title"], "bvid": c["bvid"], "desc": c["desc"], "dur": c["dur"]}
    json.dump(vids, open(TITLES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[pool] 写回后 %d 条（+%d）" % (len(vids), len(ranked)))
    return 1, len(vids), len(ranked)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=10, help="并发取相关列表的线程数")
    a = ap.parse_args(argv)
    rc, total, added = expand(a.limit, dry=a.dry_run, workers=a.workers)
    # 池子变化直接决定媒体量：按 7 天不重复规则报一下可持续上限
    print("[pool] 按「同视频 7 天 ≤1 条」：全账号 %.1f 条/天，每号（2 号）%.1f 条/天"
          % (total / 7.0, total / 7.0 / 2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
