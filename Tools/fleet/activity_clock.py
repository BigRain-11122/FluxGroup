#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""activity_clock.py — 用真实评论时间戳算出"这个平台的人什么时候活跃"。

CEO 2026-11-21「你的频率太低了，要符合一个 B 站 UP 主的操作习惯」。
拍脑袋定"10/12/16/21 点"没有依据，而且均匀发稿本身就像机器人。真实依据一直在:
B 站每条评论带 ctime，匿名接口就能取（`x/v2/reply?type=1&oid=<aid>`），
多采样几个视频的评论，就能得到一份小时分布——这是**人群几点在说话**，
不是我们几点想发。

产出 cph4/fleet/social/ACTIVITY-CLOCK.json：
  hours: {0..23: 占比}，peak: 前 5 个高峰小时，windows: 建议场次（连续段合并）
  per_hour_index: 以均值为 1 的强度指数（用来定每场动作量）
  samples: 采了多少条评论、多少个视频

用法
  python3 Tools/fleet/activity_clock.py --videos 12 --pages 5
  python3 Tools/fleet/activity_clock.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
OUT = os.path.join(SOCIAL, "ACTIVITY-CLOCK.json")
API = "https://api.bilibili.com/x/v2/reply"
VIEW = "https://api.bilibili.com/x/web-interface/view"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Referer": "https://www.bilibili.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def aid_of(bvid):
    d = _get(VIEW + "?" + urllib.parse.urlencode({"bvid": bvid}))
    if d.get("code") != 0:
        return None
    return (d.get("data") or {}).get("aid")


def comments_ctime(aid, pages=5, ps=20):
    out = []
    for pn in range(1, pages + 1):
        q = urllib.parse.urlencode({"type": 1, "oid": aid, "pn": pn, "sort": 2, "ps": ps})
        try:
            d = _get(API + "?" + q)
        except Exception:
            break
        if d.get("code") != 0:
            break
        rs = (d.get("data") or {}).get("replies") or []
        if not rs:
            break
        out.extend(int(r.get("ctime") or 0) for r in rs)
        time.sleep(0.5)
    return [t for t in out if t > 0]


def build_clock(ctimes):
    """小时分布 → 占比 + 高峰 + 建议窗口（连续段）。"""
    h = Counter()
    for t in ctimes:
        h[datetime.fromtimestamp(t).hour] += 1
    n = sum(h.values()) or 1
    share = {i: round(h.get(i, 0) / n, 4) for i in range(24)}
    mean = 1 / 24
    index = {i: round(share[i] / mean, 2) for i in range(24)}
    # 高峰：占比 ≥ 均值 1.15 倍的小时
    peak = sorted([i for i in range(24) if index[i] >= 1.15], key=lambda i: -share[i])
    # 窗口：把高峰小时连成段（跨 0 点也算连续）
    hours = [i for i in range(24) if index[i] >= 1.0]
    windows, cur = [], []
    for i in range(24):
        if i in hours:
            cur.append(i)
        else:
            if cur:
                windows.append(cur)
                cur = []
    if cur:
        windows.append(cur)
    # 头尾相接（例如 23 与 0）合并
    if len(windows) > 1 and windows[0][0] == 0 and windows[-1][-1] == 23:
        windows[0] = windows[-1] + windows[0]
        windows.pop()
    return {"hours": share, "index": index,
            "peak_hours": peak[:6], "windows": windows,
            "n": n}


def load():
    try:
        return json.load(open(OUT, encoding="utf-8"))
    except Exception:
        return {}


def index_now(now=None):
    """当前小时的活跃指数（1.0 = 平台均值）。读不到时钟就返回 1.0（不阻断）。"""
    d = load()
    idx = (d.get("index") or {})
    if not idx:
        return 1.0
    return float(idx.get(str((now or datetime.now()).hour), 1.0))


def session_plan(now=None, persona=None):
    """一次会话该开多久、做多少动作——按当前小时的真实活跃度缩放。

    2026-11-21 CEO「频率太低，要符合 UP 主操作习惯」：均匀地每几小时来一场、
    每场固定做几件事，是机器的节奏。真人的节奏是**晚上重、白天轻、深夜没有**：
    峰值 22 点 2.6 倍、凌晨 1–5 点接近 0。所以时长与动作量都乘以当前小时的指数。
    """
    i = index_now(now)
    per = persona or {}
    caps = per.get("caps") or {}
    hour = (now or datetime.now()).hour
    # 深夜（1–6 点）一律不发：实测这几个小时的真实评论占比接近 0，
    # 这个点还在互动就是"不是人"。指数阈值 0.7 用来挡住其它冷门小时。
    if hour in (1, 2, 3, 4, 5, 6) or i < 0.7:
        return {"open": False, "why": "本小时活跃指数 %.2f（真人这个点在睡）" % i}
    base_min = 18 if i >= 1.6 else (12 if i >= 1.0 else 8)
    minutes = int(round(base_min * min(2.0, i)))
    def _scale(n, lo=1):
        return max(lo, int(round(n * min(1.8, i))))
    return {"open": True, "minutes": minutes, "index": round(i, 2),
            "comment": _scale(int(caps.get("comment") or 8) / 4, 1),
            "danmaku": _scale(int(caps.get("danmaku") or 20) / 3, 1),
            "like": _scale(int(caps.get("like") or 50) / 3, 2)}


def run(videos=12, pages=5):
    try:
        tv = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        tv = {}
    urls = [u for u, v in tv.items() if (v or {}).get("title")]
    if not urls:
        return {"error": "标题池为空"}
    # 均匀取样，避免只盯头部视频
    step = max(1, len(urls) // max(1, videos))
    picked = urls[::step][:videos]
    ctimes, used, failed = [], 0, 0
    for u in picked:
        bv = ""
        for part in (u or "").split("/"):
            if part.startswith("BV"):
                bv = part
        if not bv:
            failed += 1
            continue
        aid = aid_of(bv)
        if not aid:
            failed += 1
            continue
        got = comments_ctime(aid, pages)
        if got:
            ctimes.extend(got)
            used += 1
        else:
            failed += 1
        time.sleep(0.6)
    if not ctimes:
        return {"error": "一条时间戳都没采到"}
    clock = build_clock(ctimes)
    clock.update({"version": "v1-20261121", "videos_used": used, "videos_failed": failed,
                  "source": "x/v2/reply ctime（匿名）", "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
    json.dump(clock, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"videos_used": used, "videos_failed": failed, "comments": len(ctimes),
            "peak_hours": clock["peak_hours"],
            "windows": clock["windows"],
            "top3_share": round(sum(clock["hours"][i] for i in clock["peak_hours"][:3]), 3),
            "out": os.path.relpath(OUT, ROOT)}


def self_test():
    """负控：8 小时集中的样本，高峰必须落在 8 点而不是均匀分布。"""
    base = datetime(2026, 11, 20, 8, 0).timestamp()
    ts = [base + i * 60 for i in range(50)] + [base + 12 * 3600]
    c = build_clock(ts)
    ok = c["peak_hours"][0] == 8 and c["hours"][8] > 0.9
    print(json.dumps({"self_test": "PASS" if ok else "FAIL",
                      "peak": c["peak_hours"][:2], "h8": c["hours"][8]}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", type=int, default=12)
    ap.add_argument("--pages", type=int, default=5)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    print(json.dumps(run(a.videos, a.pages), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
