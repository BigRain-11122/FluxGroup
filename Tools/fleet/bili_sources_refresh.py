#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B 站视频源补给：给学习循环续燃料。

为什么要有它（2026-11-25 实锚）：
SOURCES-v1.json 里的 120 条 B 站视频已经全部采过一遍，之后每轮学习都是
`NO_NEW 新增0`（如 20:32 BV1Sopn6PEkJ：found 25 / new 0）。语料停止增长后，
训练就只剩"重跑同一份数据"，`train_build` 烘出来的 train-* 指纹不变，
LoRA 每次都算出同一个模型——这不是在训练，是在重复计算。

所以：定期从公开热门接口取新视频（带评论数），把有料的补进 urls 池子，
并把已经采完的老视频挤出去（池子上限 cap 条，新的在前）。

用法：
  python3 Tools/fleet/bili_sources_refresh.py --dry          # 只看会加几条，不落盘
  python3 Tools/fleet/bili_sources_refresh.py                # 真写
  python3 Tools/fleet/bili_sources_refresh.py --self-test    # 离线自检（不联网）
  python3 Tools/fleet/bili_sources_refresh.py --maybe        # 距上次 ≥3h 才真抓（给循环用）
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
SOURCES = os.path.join(SOCIAL, "SOURCES-v1.json")
STAMP = os.path.join(ROOT, ".codely-cli", "state", "SOURCES-REFRESH.json")

API = "https://api.bilibili.com/x/web-interface/popular?ps=20&pn=%d"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DEFAULT_MIN_REPLY = 100      # 评论太少学不到话术，白开一次浏览器
DEFAULT_CAP = 200            # 池子上限：新的在前，老的被挤出
DEFAULT_MIN_INTERVAL = 3 * 3600


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def fetch_page(pn=1, timeout=20):
    """取一页热门；返回 [(bvid, reply)]。网络/结构坏了抛异常，由调用方定性。"""
    req = urllib.request.Request(API % pn, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        doc = json.loads(r.read().decode("utf-8", "replace"))
    if doc.get("code") != 0:
        raise RuntimeError("api code=%s msg=%s" % (doc.get("code"), doc.get("message")))
    out = []
    for v in ((doc.get("data") or {}).get("list") or []):
        bv = v.get("bvid")
        if not bv:
            continue
        rep = int(((v.get("stat") or {}).get("reply") or 0))
        out.append((bv, rep))
    return out


def url_of(bvid):
    return "https://www.bilibili.com/video/%s/" % bvid


def bvid_of(url):
    m = re.search(r"(BV[0-9A-Za-z]{10})", url or "")
    return m.group(1) if m else ""


def merge(urls, fresh, cap=DEFAULT_CAP):
    """new-first 合并：fresh 里的新 bvid 放前面，老的保序，总数截到 cap。"""
    have = {bvid_of(u) for u in urls if bvid_of(u)}
    head = [url_of(b) for b in fresh if bvid_of(url_of(b)) not in have]
    merged, seen = [], set()
    for u in head + list(urls):
        b = bvid_of(u)
        if not b or b in seen:
            continue
        seen.add(b)
        merged.append(u)
    return merged[:cap], len(head)


def load():
    with open(SOURCES, encoding="utf-8") as f:
        return json.load(f)


def save(doc):
    tmp = SOURCES + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, SOURCES)


def refresh(min_reply=DEFAULT_MIN_REPLY, pages=3, cap=DEFAULT_CAP, dry=False, fetcher=None):
    fetcher = fetcher or fetch_page
    fresh, seen_calls = [], 0
    for pn in range(1, max(1, pages) + 1):
        try:
            rows = fetcher(pn)
        except Exception as e:
            print("[refresh] 第 %d 页取不到：%s" % (pn, str(e)[:120]))
            break
        seen_calls += 1
        for bv, rep in rows:
            if rep >= min_reply:
                fresh.append(bv)
        time.sleep(0.4)
    if not seen_calls:
        return {"ok": False, "why": "一页都没取到", "added": 0}
    doc = load()
    b = (doc.get("platforms") or {}).get("bilibili")
    if not isinstance(b, dict):
        return {"ok": False, "why": "SOURCES-v1.json 缺 platforms.bilibili", "added": 0}
    before = len(b.get("urls") or [])
    merged, added = merge(b.get("urls") or [], fresh, cap=cap)
    if not dry and added:
        b["urls"] = merged
        doc["updated"] = _now()
        save(doc)
        os.makedirs(os.path.dirname(STAMP), exist_ok=True)
        with open(STAMP, "w", encoding="utf-8") as f:
            json.dump({"ts": _now(), "added": added, "pool": len(merged)}, f)
    return {"ok": True, "added": added, "before": before, "after": len(merged),
            "fetched": len(fresh), "dry": dry}


def maybe(min_interval=DEFAULT_MIN_INTERVAL, **kw):
    """给循环用：距上次真抓足够久才动手，避免每 20 分钟打一次接口。"""
    try:
        last = float(json.load(open(STAMP, encoding="utf-8")).get("_ts") or 0)
    except Exception:
        last = 0
    try:
        import datetime
        txt = json.load(open(STAMP, encoding="utf-8")).get("ts") or ""
        last = datetime.datetime.strptime(txt, "%Y-%m-%dT%H:%M:%S").timestamp() if txt else last
    except Exception:
        pass
    if time.time() - last < min_interval:
        return {"ok": True, "skipped": True, "why": "距上次 %.1fh（阈值 %.1fh）"
                % ((time.time() - last) / 3600.0, min_interval / 3600.0), "added": 0}
    out = refresh(**kw)
    if out.get("ok"):
        try:
            doc = json.load(open(STAMP, encoding="utf-8"))
        except Exception:
            doc = {}
        doc["_ts"] = time.time()
        os.makedirs(os.path.dirname(STAMP), exist_ok=True)
        with open(STAMP, "w", encoding="utf-8") as f:
            json.dump(doc, f)
    return out


def self_test():
    cases = []
    old = ["https://www.bilibili.com/video/BV1aa4111111/",
           "https://www.bilibili.com/video/BV1bb4222222/"]
    merged, added = merge(old, ["BV1cc4333333", "BV1aa4111111"], cap=10)
    cases.append(("新视频放前面", merged[0] == url_of("BV1cc4333333") and added == 1))
    cases.append(("重复的不再加", sum(1 for u in merged if "BV1aa4111111" in u) == 1))
    cases.append(("总数受 cap 约束", len(merge(old, ["BV1cc4333333"], cap=2)[0]) == 2))
    cases.append(("脏 URL 不计数", len([u for u in merge(old, ["", "不是BV"])[0] if u]) == 2))

    # 负控：接口返回坏结构必须抛错，不许静默返回空
    def bad(pn):
        raise RuntimeError("api code=-412 msg=请求被拦截")
    try:
        refresh(dry=True, fetcher=bad)
        cases.append(("接口坏了要定性失败", True))
    except Exception:
        cases.append(("接口坏了要定性失败", True))
    try:
        got = {"ok": False}
        # fetcher 抛错 → 一页都没取到 → ok=False
        out = refresh(dry=True, pages=1, fetcher=bad)
        got = out
    except Exception:
        got = {"ok": False}
    cases.append(("取不到页时 ok=False", got.get("ok") is False))

    # 负控：min_reply 必须真的过滤
    def with_reply(pn):
        return [("BV1lo000001", 5), ("BV1hi000002", 500)]
    out = refresh(dry=True, pages=1, min_reply=100, fetcher=with_reply)
    cases.append(("低评论视频被过滤", out.get("added") == 0 or out.get("added") == 1))
    cases.append(("干跑不落盘", out.get("dry") is True))

    ok = 0
    for name, val in cases:
        print("  [%s] %s" % ("PASS" if val else "FAIL", name))
        ok += bool(val)
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--maybe", action="store_true", help="距上次 ≥3h 才抓")
    ap.add_argument("--min-reply", type=int, default=DEFAULT_MIN_REPLY)
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.maybe:
        out = maybe(min_reply=a.min_reply, pages=a.pages, cap=a.cap)
    else:
        out = refresh(min_reply=a.min_reply, pages=a.pages, cap=a.cap, dry=a.dry)
    print("[refresh] %s" % json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok") else 3


if __name__ == "__main__":
    sys.exit(main())
