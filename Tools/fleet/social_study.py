#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_study.py - 学别人的爆款：日榜 top 视频 + 高赞评论 + 200 个不同 UP 名册。

CEO 2026-11-18「你要去排名前200的不同up和每天爆火的top20视频等去看去学习」。

为什么这件事比自采更有价值：
  · 我们自己的语料只有"什么人写了什么"，没有"哪句真的被看见"。
  · B站评论接口支持按热度排序（sort=1），**点赞数就是真人投票**——这是现成的、
    比我们自造的品味闸更硬的地面真值。高赞评论该进训练集，冷笑话该被降权。
  · 日榜 top20 决定"现在什么话题会爆"，UP 名册决定"该向谁学口吻"。

产出（都在 cph4/fleet/social/study/）：
  ranking-YYYYMMDD.jsonl   日榜视频（vid/up/aid/view/like）
  hot-comments.jsonl       高赞评论（text/likes/up/video/seg 待标注）
  UP-ROSTER.json           累计的不同 UP 名册（目标 200，跨天累积去重）
  STUDY-REPORT.md          一屏结论：长度/问句/emoji/点赞分布 + 高频短语

用法：
  .venv-housing/bin/python Tools/fleet/social_study.py --top 20        # 日榜 top20 + 评论
  .venv-housing/bin/python Tools/fleet/social_study.py --top 20 --report
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import random
import re
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STUDY = os.path.join(ROOT, "cph4", "fleet", "social", "study")
ROSTER = os.path.join(STUDY, "UP-ROSTER.json")
HOT = os.path.join(STUDY, "hot-comments.jsonl")
REPORT = os.path.join(STUDY, "STUDY-REPORT.md")

sys.path.insert(0, HERE)

UP_TARGET = 200


def _jitter(a=1.2, b=2.8):
    time.sleep(random.uniform(a, b))


class Bili:
    """一个浏览器上下文跑完整批，避免反复起停与 profile 抢锁。"""

    def __init__(self):
        from playwright.sync_api import sync_playwright
        import social_comment as sc
        self._p = sync_playwright().start()
        self.ctx = sc._launch(self._p)
        self.pg = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        self.pg.goto("https://www.bilibili.com/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

    def get(self, url):
        raw = self.pg.evaluate("""async(u)=>{const r=await fetch(u,{credentials:'include'});
            return await r.text();}""", url)
        return json.loads(raw)

    def close(self):
        try:
            self.ctx.close()
        except Exception:
            pass
        try:
            self._p.stop()
        except Exception:
            pass


def fetch_ranking(b, want=20, rid=0):
    """rid=0 全站；分区榜（音乐3/科技188/影视181/动画1…）能捞到完全不同的人群，
    这是在一天内把 UP 名册从 100 推到 200 的唯一稳妥办法（日榜全站一天只有 100 条）。"""
    d = b.get("https://api.bilibili.com/x/web-interface/ranking/v2?rid=%d&type=all" % rid)
    lst = (d.get("data") or {}).get("list") or []
    out = []
    for v in lst[:want]:
        owner = v.get("owner") or {}
        st = v.get("stat") or {}
        out.append({"aid": v.get("aid"), "bvid": v.get("bvid"),
                    "title": (v.get("title") or "")[:60],
                    "up": owner.get("name"), "up_mid": owner.get("mid"),
                    "view": st.get("view"), "like": st.get("like"),
                    "reply": st.get("reply"), "tname": v.get("tname")})
    return out


def fetch_hot_comments(b, aid, pages=1, per=20):
    """按热度排序取评论：点赞数就是真人投票。"""
    out = []
    for pn in range(1, pages + 1):
        d = b.get("https://api.bilibili.com/x/v2/reply?type=1&oid=%s&pn=%d&ps=%d&sort=1"
                  % (aid, pn, per))
        reps = (d.get("data") or {}).get("replies") or []
        for r in reps:
            txt = re.sub(r"\s+", " ", (r.get("content") or {}).get("message") or "").strip()
            if not txt:
                continue
            out.append({"text": txt, "likes": r.get("like") or 0,
                        "author": ((r.get("member") or {}).get("uname") or ""),
                        "rpid": r.get("rpid"), "aid": aid})
        _jitter()
    return out


def load_jsonl(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def append_jsonl(p, rows):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def update_roster(videos):
    r = {"ups": [], "updated": ""}
    try:
        r = json.load(open(ROSTER, encoding="utf-8"))
    except Exception:
        pass
    seen = {u["name"] for u in r.get("ups") or []}
    add = 0
    for v in videos:
        n = v.get("up")
        if n and n not in seen:
            r.setdefault("ups", []).append({"name": n, "mid": v.get("up_mid"),
                                            "first_seen": datetime.now().strftime("%Y-%m-%d"),
                                            "from": v.get("title", "")[:30]})
            seen.add(n)
            add += 1
    r["updated"] = datetime.now().isoformat(timespec="seconds")
    r["count"] = len(r.get("ups") or [])
    os.makedirs(STUDY, exist_ok=True)
    json.dump(r, open(ROSTER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return r["count"], add


def analyse(hot):
    if not hot:
        return {}
    lens = sorted(len(h["text"]) for h in hot)
    likes = sorted(h["likes"] for h in hot)
    q = sum(1 for h in hot if "?" in h["text"] or "？" in h["text"]) / len(hot)
    emo = sum(1 for h in hot if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", h["text"])) / len(hot)
    ex = sum(1 for h in hot if "!" in h["text"] or "！" in h["text"]) / len(hot)
    words = collections.Counter()
    for h in hot:
        s = re.sub(r"[^\u4e00-\u9fff]", " ", h["text"])
        for n in (3, 4):
            for i in range(len(s) - n + 1):
                w = s[i:i + n]
                if " " not in w:
                    words[w] += 1
    top = [(w, c) for w, c in words.most_common(120) if c >= 3][:18]
    return {"n": len(hot),
            "len_median": lens[len(lens) // 2], "len_p90": lens[int(len(lens) * 0.9)],
            "likes_median": likes[len(likes) // 2], "likes_max": likes[-1],
            "ask_rate": round(q, 2), "emoji_rate": round(emo, 2), "exclaim_rate": round(ex, 2),
            "top_phrases": top}


def write_report(meta, stats, roster_n):
    L = ["# 爆款学习报告 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), "",
         "- 日榜取样：%s 条视频｜UP 名册累计：**%d**/%d"
         % (meta.get("videos"), roster_n, UP_TARGET),
         "- 高赞评论：%s 条（按点赞排序取）" % stats.get("n"),
         "", "## 高赞评论的形状（真人投票选出来的）", "",
         "| 指标 | 值 | 读法 |", "|---|---|---|",
         "| 长度中位 | %s 字 | 与我们训练集 27 字对照 |" % stats.get("len_median"),
         "| 长度 P90 | %s 字 | 长评论仍能高赞说明不是越短越好 |" % stats.get("len_p90"),
         "| 点赞中位 | %s | 高赞门槛 |" % stats.get("likes_median"),
         "| 点赞最高 | %s | 天花板 |" % stats.get("likes_max"),
         "| 带问句 | %.0f%% | 提问是高赞高发形态 |" % (100 * stats.get("ask_rate", 0)),
         "| 带 emoji | %.0f%% | 表情是不是必需 |" % (100 * stats.get("emoji_rate", 0)),
         "| 带感叹号 | %.0f%% | 情绪浓度 |" % (100 * stats.get("exclaim_rate", 0)),
         "", "## 高频短语（高赞评论里反复出现的说法）", "",
         " · ".join("%s(%d)" % (w, c) for w, c in (stats.get("top_phrases") or [])) or "（样本不足）",
         "", "> 机读：`study/hot-comments.jsonl`、`study/UP-ROSTER.json`"]
    os.makedirs(STUDY, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20, help="日榜取前几条视频")
    ap.add_argument("--pages", type=int, default=1, help="每个视频取几页评论（20/页）")
    ap.add_argument("--rid", type=int, default=0, help="榜单分区：0 全站/3 音乐/188 科技/181 影视/1 动画")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    b = Bili()
    try:
        vids = fetch_ranking(b, a.top, a.rid)
        print("[study] 日榜取到 %d 条视频" % len(vids))
        day = datetime.now().strftime("%Y%m%d")
        append_jsonl(os.path.join(STUDY, "ranking-%s.jsonl" % day), vids)
        hot = []
        for i, v in enumerate(vids, 1):
            if not v.get("aid"):
                continue
            cs = fetch_hot_comments(b, v["aid"], pages=a.pages)
            for c in cs:
                c["up"] = v.get("up")
                c["video"] = v.get("title")
                c["ts"] = datetime.now().isoformat(timespec="seconds")
            hot += cs
            if i % 5 == 0 or i == len(vids):
                print("  [%d/%d] 累计高赞评论 %d 条" % (i, len(vids), len(hot)), flush=True)
        append_jsonl(HOT, hot)
        roster_n, add = update_roster(vids)
        stats = analyse(hot)
        write_report({"videos": len(vids)}, stats, roster_n)
        print("[study] 高赞评论 %d 条｜UP 名册 %d（本次新增 %d）" % (len(hot), roster_n, add))
        print("[study] 长度中位 %s 字｜点赞中位 %s｜问句率 %.0f%%｜emoji %.0f%%"
              % (stats.get("len_median"), stats.get("likes_median"),
                 100 * stats.get("ask_rate", 0), 100 * stats.get("emoji_rate", 0)))
        return 0
    finally:
        b.close()


def self_test():
    """判据要能红：分析函数在造好的样例上必须给出确定结论。"""
    hot = [{"text": "这段剪辑的节奏太舒服了？", "likes": 100},
           {"text": "求教程", "likes": 5},
           {"text": "笑死我了😂这个转场", "likes": 50}]
    s = analyse(hot)
    cases = [
        ("样本数正确", s["n"] == 3),
        ("点赞最高取到 100", s["likes_max"] == 100),
        ("问句率 1/3", abs(s["ask_rate"] - 1 / 3) < 0.01),
        ("emoji 率 1/3", abs(s["emoji_rate"] - 1 / 3) < 0.01),
        ("长度中位是 9（3/9/12 的中位）", s["len_median"] == 9),
    ]
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
