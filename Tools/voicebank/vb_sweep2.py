# -*- coding: utf-8 -*-
"""vb_sweep2.py - category sweep for the talent roster (voice actors, hosts, narrators...).

Six source classes, each with the keyword shapes that actually surface them on Bilibili.
Rows carry a category tag so the roster can be grouped and compared class by class.
"""
import json
import sys

from bilibili_api import search, sync

CATS = {
    "audiobook": ["有声小说 单播", "官场小说 有声", "悬疑推理 有声书", "历史 有声书 全集"],
    "radio": ["深夜电台", "情感电台 主播", "睡前电台 女声", "夜话 电台"],
    "anchor": ["播音主持 练习", "新闻播报 练习", "婚礼主持 现场", "播音腔 展示"],
    "dubbing": ["配音 展示", "声优 配音集", "广播剧 配音", "配音演员 作品"],
    "uplive": ["科技测评 口播", "历史 讲述 口播", "财经 解读 口播", "普法 口播", "汽车 测评 口播"],
    "actor": ["演员 台词 功底", "话剧 台词", "老戏骨 台词", "朗诵 名篇"],
    "timbre": ["低音炮 声音", "沙哑 嗓音 说话", "童声 配音", "老年 嗓音 讲述", "方言 播音"],
}
OUT = sys.argv[1] if len(sys.argv) > 1 else r"E:\Fluxgroup\.codely-cli\voicebank\sweep_pool.json"
MIN_SEC, MAX_SEC, MIN_PLAY = 480, 7200, 8000


def secs(d):
    try:
        parts = [int(x) for x in str(d).split(":")]
    except Exception:
        return 0
    s = 0
    for p in parts:
        s = s * 60 + p
    return s


rows, seen = {}, set()
for cat, kws in CATS.items():
    for kw in kws:
        for page in (1, 2):
            try:
                r = sync(search.search_by_type(kw, search_type=search.SearchObjectType.VIDEO,
                                               page=page))
            except Exception as e:
                print("kw=%s p%d ERR %r" % (kw, page, e))
                break
            res = (r or {}).get("result") or []
            if not res:
                break
            new = 0
            for v in res:
                bv = v.get("bvid")
                d, play = secs(v.get("duration")), int(v.get("play") or 0)
                if not bv or bv in seen or not (MIN_SEC <= d <= MAX_SEC) or play < MIN_PLAY:
                    continue
                seen.add(bv)
                new += 1
                rows[bv] = {
                    "bvid": bv, "mid": v.get("mid"), "author": v.get("author"),
                    "title": (v.get("title") or "").replace('<em class="keyword">', "").replace("</em>", ""),
                    "dur": d, "play": play, "cat": cat, "kw": kw,
                }
            print("%-9s %-16s p%d +%d total=%d" % (cat, kw, page, new, len(rows)), flush=True)

json.dump({"count": len(rows), "rows": list(rows.values())},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL", len(rows), "->", OUT)