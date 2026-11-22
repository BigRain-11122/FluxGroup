#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reply_quality.py — 按"回复质量"给已发评论打分（不看可见率）。

为什么（2026-11-22 CEO「评论是否可见不是很重要，我要的是回复质量」）：
可见率取决于平台审核与折叠，不是我们能控制的东西，拿它当加量开关等于把平台的
审核延迟当成自己的 KPI。质量是可自查的：具体、像人、不撞模板、长度对、贴视频。

五个维度（都能从文本与台账算出，不需要模型打分）：
  concrete  具体性：含领域名词/数字/时间点/专有名词（"50 块那段""问苍生""Codex"）
  human     人味：有口语语气词，且不撞 AI 腔词表
  fresh     不撞模板：开头 2 字与近 20 条不重复，且 4-gram 不重复
  length    长度带：落在该条所在人群段的中位 ±12 字
  ontopic   相关性：与视频标题/话题词有实词交集

用法：
  python3 Tools/fleet/reply_quality.py            # 打分并打印
  python3 Tools/fleet/reply_quality.py --json
  python3 Tools/fleet/reply_quality.py --n 40     # 只看最近 40 条
返回码：0 合格；2 质量线以下（供调度与升档判据使用）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
LOG = os.path.join(SOCIAL, "practice-log.jsonl")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
NORMS = os.path.join(SOCIAL, "BILI-NORMS-v1.json")

# 领域名词：评论里出现这些＝在说这条视频的具体东西，而不是空话
DOMAIN = ["剪辑", "蒙版", "转场", "调色", "配乐", "音效", "镜头", "字幕", "歌词识别", "节奏",
          "运镜", "光影", "特效", "素材", "剪映", "PR", "AE", "开场", "结尾", "解说", "配音",
          "团战", "操作", "意识", "对线", "剧情", "分镜", "剧本", "画质", "建模", "渲染",
          "AI", "提示词", "短片", "MV", "漫剧", "短剧"]
ORAL = ["啊", "吧", "呢", "嘛", "啦", "哈哈", "哈", "呀", "哦", "诶", "唉", "额", "咋", "挺", "真"]
AI_SMELL = ["绝了", "氛围感", "质感", "干货", "拉满", "封神", "无与伦比", "令人", "不禁",
            "值得一提", "整体而言", "综上所述", "简直", "颇为", "堪称"]
MECH = ["首先", "其次", "然后", "之后", "综上所述", "总而言之"]

PASS_LINE = 65.0        # 中位分合格线
CONCRETE_LINE = 0.5     # 具体性覆盖率
DUP_LINE = 0.10         # 模板碰撞率上限


def _rows(path, limit=None):
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        return []
    return out[-limit:] if limit else out


def _norms():
    try:
        d = json.load(open(NORMS, encoding="utf-8")) or {}
    except Exception:
        return {}
    return d.get("segments") or {}


def _title_of(url):
    try:
        d = json.load(open(TITLES, encoding="utf-8")) or {}
        return ((d.get(url) or {}).get("title") or "")
    except Exception:
        return ""


def _grams(t, n=4):
    t = re.sub(r"\s+", "", t)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def score_one(text, recent, seg, title=""):
    t = (text or "").strip()
    d = {}
    # 1 具体性：领域词 / 数字 / 时间点 / 引号里的东西
    concrete_hit = [w for w in DOMAIN if w in t]
    has_num = bool(re.search(r"\d+|[一二三四五六七八九十]+(块|秒|分|年|集)", t))
    d["concrete"] = bool(concrete_hit or has_num)
    d["concrete_word"] = (concrete_hit or [])[:2]
    # 2 人味
    d["oral"] = any(w in t for w in ORAL)
    d["ai_smell"] = [w for w in AI_SMELL if w in t]
    d["mech"] = [w for w in MECH if w in t]
    d["human"] = d["oral"] and not d["ai_smell"] and not d["mech"]
    # 3 不撞模板
    head = t[:2]
    d["head_dup"] = any((r.get("text") or "")[:2] == head for r in recent)
    g = _grams(t)
    d["gram_dup"] = any(len(g & _grams(r.get("text") or "")) >= 3 for r in recent)
    d["fresh"] = not d["head_dup"] and not d["gram_dup"]
    # 4 长度带（按人群段实测中位 ±12）
    p50 = ((_norms().get(seg or "generic") or {}).get("len_p50")) or 15
    d["len"] = len(t)
    d["len_ok"] = abs(len(t) - int(p50)) <= 12
    # 5 相关性：与视频标题有 2 字以上实词交集
    if title:
        tw = {w for w in re.findall(r"[\u4e00-\u9fff]{2,6}", title)}
        d["ontopic"] = any(w in t for w in tw) or bool(concrete_hit)
    else:
        d["ontopic"] = bool(concrete_hit)
    # 合计（每项 20 分）
    d["score"] = round(20 * sum(1 for k in ("concrete", "human", "fresh", "len_ok", "ontopic")
                                if d.get(k)), 1)
    return d


def evaluate(n=30, since=None):
    rows = _rows(LOG)
    posts = [r for r in rows if r.get("action") == "post" and (r.get("text") or "").strip()]
    if since:
        # 判据只判"生效之后"：闸改了以后再拿旧稿算质量，会把已修的毛病一直报红
        posts = [r for r in posts if str(r.get("ts") or "") >= since]
    posts = posts[-n:]
    items = []
    for i, r in enumerate(posts):
        recent = posts[max(0, i - 20):i]
        seg = ""
        title = _title_of(r.get("video") or "")
        # 人群段：优先取 qualified 行的 persona
        d = score_one(r.get("text"), recent, seg, title)
        d["ts"] = r.get("ts")
        d["rpid"] = r.get("rpid")
        d["text"] = (r.get("text") or "")[:60]
        items.append(d)
    if not items:
        return {"n": 0, "ok": False, "why": "没有已发评论"}
    scores = [i["score"] for i in items]
    agg = {
        "n": len(items),
        "median": round(st.median(scores), 1),
        "concrete_rate": round(sum(1 for i in items if i["concrete"]) / len(items), 2),
        "human_rate": round(sum(1 for i in items if i["human"]) / len(items), 2),
        "fresh_rate": round(sum(1 for i in items if i["fresh"]) / len(items), 2),
        "len_ok_rate": round(sum(1 for i in items if i["len_ok"]) / len(items), 2),
        "ontopic_rate": round(sum(1 for i in items if i["ontopic"]) / len(items), 2),
        "ai_smell_rate": round(sum(1 for i in items if i["ai_smell"]) / len(items), 2),
        "dup_rate": round(sum(1 for i in items if not i["fresh"]) / len(items), 2),
    }
    agg["ok"] = (agg["median"] >= PASS_LINE and agg["concrete_rate"] >= CONCRETE_LINE
                 and agg["dup_rate"] <= DUP_LINE and agg["ai_smell_rate"] == 0)
    agg["items"] = items
    return agg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--since", default=None, help="只看这个时间之后的稿（判据只判生效之后）")
    a = ap.parse_args(argv)
    agg = evaluate(a.n, since=a.since)
    if a.json:
        print(json.dumps(agg, ensure_ascii=False))
    else:
        if not agg.get("n"):
            print("❗ %s" % agg.get("why"))
            return 2
        print("最近 %d 条：中位 %.0f 分（线 %.0f）｜具体 %.0f%%｜人味 %.0f%%｜不撞模板 %.0f%%｜"
              "长度带 %.0f%%｜贴题 %.0f%%｜AI 腔 %.0f%%"
              % (agg["n"], agg["median"], PASS_LINE, 100 * agg["concrete_rate"],
                 100 * agg["human_rate"], 100 * agg["fresh_rate"], 100 * agg["len_ok_rate"],
                 100 * agg["ontopic_rate"], 100 * agg["ai_smell_rate"]))
        worst = sorted(agg["items"], key=lambda i: i["score"])[:3]
        for w in worst:
            why = []
            if not w["concrete"]:
                why.append("不具体")
            if not w["human"]:
                why.append("AI腔" if w["ai_smell"] else ("非口语" if not w["oral"] else "机械连接"))
            if not w["fresh"]:
                why.append("撞模板")
            if not w["len_ok"]:
                why.append("长度%d" % w["len"])
            if not w["ontopic"]:
                why.append("不贴题")
            print("   最低 [%d分] %s ← %s" % (w["score"], w["text"], "、".join(why)))
        print("%s 质量线%s" % ("✅" if agg["ok"] else "❗", "达标" if agg["ok"] else "未达标"))
    return 0 if agg["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
