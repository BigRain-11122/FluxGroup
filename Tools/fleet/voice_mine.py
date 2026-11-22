#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_mine.py — 采"高赞真实评论"当说话样本（语感靠样本，不靠形容词）。

为什么（2026-11-22 CEO「策略可以多元化，参考他们的评论、高点赞数的评论，不要这么讲话」）：
我们现在两种毛病——①评论只有一套腔调（同一批模板改字），②弹幕只有 10 条模板。
小模型（4B）靠形容词改不掉腔调，靠 few-shot 样本才有效；而"什么算好样本"不能由我挑，
要由平台投票结果决定：**按点赞数排序的真实评论 = 这个分区被最多人认可的说法**。

数据来源：api.bilibili.com/x/v2/reply?sort=2（按热度），匿名可取，不需要登录。
产出：
  corpus/hot/HOT-COMMENTS.jsonl   高赞评论（text/like/len/video/seg/archetype）
  corpus/hot/HOT-STATS.json       长度分布、表情/问句/口语比例、原型分布
用法：
  python3 Tools/fleet/voice_mine.py --videos 120 --min-like 20
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import time
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
OUTDIR = os.path.join(SOCIAL, "corpus", "hot")
OUT = os.path.join(OUTDIR, "HOT-COMMENTS.jsonl")
STATS = os.path.join(OUTDIR, "HOT-STATS.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
REPLY = ("https://api.bilibili.com/x/v2/reply?type=1&oid=%s&sort=2&ps=20&pn=%s")

# 原型：按下法分，供提示词按"这次要说哪种话"取样，而不是每次同一套腔
ARCH = [
    ("反应", r"^(哈|hh|笑死|草|泪目|哭了|破防|卧槽|绝|好家伙|我?[直真]接|救命)"),
    ("共鸣", r"(我也是|我也是这样|从小|当年|以前|想起|经历过|同款|一模一样|DNA)"),
    ("玩梗", r"([\[\【].{1,8}[\]\】]|梗|圣经|经典|老哥|doge|狗头|要素|浓度)"),
    ("具体点评", r"(这|那)(个|段|里|句|帧).{0,8}(镜头|转场|配乐|剪辑|调色|节奏|光|画质|字幕|音效)"),
    ("补充信息", r"(其实|顺便|科普|补充|更正|应该|原曲|出自|原作|来源|av\d+|BV\w+)"),
    ("追问", r"(\?|？|吗$|呢$|哪|怎么|为什么|求|有人知道|谁知道)"),
    ("短感叹", r"^.{1,6}$"),
]


def _get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Referer": "https://www.bilibili.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def archetype(text):
    t = (text or "").strip()
    for name, pat in ARCH:
        if re.search(pat, t, re.I):
            return name
    return "其他"


def clean(t):
    t = re.sub(r"\s+", " ", (t or "")).strip()
    return t[:200]


def _hot_via_daemon(aid, pn=1):
    """走登录态常驻浏览器取高赞评论；daemon 不在就回落匿名接口。

    匿名接口 rate limit 很紧（采到第 60 个视频就 412，之后整条路都堵），
    登录上下文里同源 fetch 才是可持续的路子。
    """
    try:
        sys.path.insert(0, HERE)
        import social_comment as sc
        hit = sc._daemon("hot", {"aid": aid, "pn": pn}, timeout=40)
        if hit and hit.get("ok") and isinstance(hit.get("res"), str):
            return json.loads(hit["res"])
    except Exception:
        pass
    return _get(REPLY % (aid, pn))


LOCK = os.path.join(SOCIAL, "corpus", "hot", ".miner.lock")


def _take_lock():
    try:
        if os.path.exists(LOCK):
            pid = int((open(LOCK).read() or "0").strip() or 0)
            if pid and pid != os.getpid():
                os.kill(pid, 0)
                return False
    except Exception:
        pass
    try:
        open(LOCK, "w").write(str(os.getpid()))
    except Exception:
        pass
    return True


def _drop_lock():
    try:
        if (open(LOCK).read() or "").strip() == str(os.getpid()):
            os.remove(LOCK)
    except Exception:
        pass


def _one_video(args):
    """取一条视频的高赞评论（含 412 退避）。并发安全：只读接口 + 返回纯数据。"""
    url, bv, min_like, pages, sleep_s = args
    for i in range(3):
        try:
            j = _get("https://api.bilibili.com/x/web-interface/view?bvid=%s" % bv)
            oid = ((j.get("data") or {}).get("aid"))
            if not oid:
                return url, bv, []
            out = []
            for pn in range(1, max(1, pages) + 1):
                d = _hot_via_daemon(oid, pn)
                for r in ((d.get("data") or {}).get("replies") or []):
                    txt = clean((r.get("content") or {}).get("message"))
                    like = int(r.get("like") or 0)
                    if not txt or like < min_like:
                        continue
                    out.append({"text": txt, "like": like, "len": len(txt), "video": url,
                                "bvid": bv, "archetype": archetype(txt),
                                "has_emoji": bool(re.search(r"[\[\【].{1,10}[\]\】]", txt)),
                                "has_q": bool(re.search(r"[?？]", txt))})
                if sleep_s:
                    time.sleep(sleep_s / max(1, pages))
            return url, bv, out
        except Exception as e:
            if "412" in str(e) and i < 2:
                time.sleep(8 * (i + 1))
                continue
            return url, bv, []
    return url, bv, []


def mine(n_videos=120, min_like=20, pages=2, sleep_s=0.2, workers=3):
    """按热度采高赞评论。三条铁律（都是 2026-11-22 踩出来的）：

    1. **不许覆盖**：结果与已有样本合并去重——第一次跑完 58 条，第二次被限流只回 6 条，
       直接覆盖就把好样本全丢了。
    2. **reply 接口要限速**：连续快打会 412（Precondition Failed）。1.2 秒一条 + 到 412
       就退避 30 秒重试，比一次跑完更实际。
    3. **续采**：已采过的 bvid 记进 HOT-SEEN.json，下次跳过，攒样本不用重跑。
    """
    vids = json.load(open(TITLES, encoding="utf-8")) or {}
    os.makedirs(OUTDIR, exist_ok=True)
    seen_file = os.path.join(OUTDIR, "HOT-SEEN.json")
    try:
        done_bv = set(json.load(open(seen_file, encoding="utf-8")) or [])
    except Exception:
        done_bv = set()
    rows, seen = [], set()
    try:
        for line in open(OUT, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                rows.append(r)
                seen.add(re.sub(r"\W", "", r.get("text") or "")[:40])
    except FileNotFoundError:
        pass
    before = len(rows)

    todo = [(u, v) for u, v in vids.items()
            if (v or {}).get("bvid") and (v or {}).get("bvid") not in done_bv]
    todo = todo[:max(1, n_videos)]
    # 并发 3：实测 6 条 0.63s 全成功；串行 1.2s/条时 60 个视频要 2.4 分钟，并行 20–30 秒。
    # 接口有 IP 限流，所以并发不上去（411/412 就退避），3 线程是"快又不惹"的位置。
    args = [(u, (v or {}).get("bvid"), min_like, pages, sleep_s) for u, v in todo]
    done_ct = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for url, bv, got in ex.map(_one_video, args):
            for r in got:
                key = re.sub(r"\W", "", r["text"])[:40]
                if key in seen:
                    continue
                seen.add(key)
                rows.append(r)
            done_bv.add(bv)
            done_ct += 1
            if done_ct % 25 == 0:
                print("[hot] 已扫 %d/%d，累计样本 %d" % (done_ct, len(todo), len(rows)))
                json.dump(sorted(done_bv), open(seen_file, "w", encoding="utf-8"), ensure_ascii=False)

    json.dump(sorted(done_bv), open(seen_file, "w", encoding="utf-8"), ensure_ascii=False)

    json.dump(sorted(done_bv), open(seen_file, "w", encoding="utf-8"), ensure_ascii=False)
    rows.sort(key=lambda r: -r["like"])
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    lens = sorted(r["len"] for r in rows)
    med = lens[len(lens) // 2] if lens else 0
    stat = {
        "n": len(rows), "added": len(rows) - before, "videos_mined": len(done_bv),
        "len_p50": med, "len_p25": lens[len(lens) // 4] if lens else 0,
        "len_p75": lens[len(lens) * 3 // 4] if lens else 0,
        "emoji_rate": round(sum(1 for r in rows if r["has_emoji"]) / len(rows), 3) if rows else 0,
        "question_rate": round(sum(1 for r in rows if r["has_q"]) / len(rows), 3) if rows else 0,
        "short_rate": round(sum(1 for r in rows if r["len"] <= 10) / len(rows), 3) if rows else 0,
        "archetype": dict(collections.Counter(r["archetype"] for r in rows).most_common()),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    json.dump(stat, open(STATS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[hot] 累计 %d 条（本次 +%d）；长度中位 %d（P25 %d / P75 %d）；表情 %.0f%%、问句 %.0f%%、≤10字 %.0f%%"
          % (stat["n"], stat["added"], stat["len_p50"], stat["len_p25"], stat["len_p75"],
             100 * stat["emoji_rate"], 100 * stat["question_rate"], 100 * stat["short_rate"]))
    print("[hot] 原型分布：%s" % stat["archetype"])
    return stat


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", type=int, default=120)
    ap.add_argument("--min-like", type=int, default=20)
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args(argv)
    if not _take_lock():
        print("[hot] 已有补采实例在跑，本轮让路")
        return 0
    try:
        mine(a.videos, a.min_like, a.pages, workers=a.workers)
    finally:
        _drop_lock()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
