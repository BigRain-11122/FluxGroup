#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_profile.py - 按平台读评论、出风格画像（喂给模型当约束，而不是拍脑袋写提示词）。

CEO 2026-11-17「你主要是看数据，训练每个平台的用户的评论特点，风格等等」。
所以要的不是"回复机器人"，是**可复算的平台风格档案**：每个平台的观众怎么说话、
说什么、多长、带不带 emoji、爱不爱问、爱不爱催、爱不爱怼。全部规则算，不交给模型
（4B 算术实测会错；画像必须可复算才能被信任）。

Input  : 任意 jsonl（inbox.jsonl / raw/<platform>.<behavior>.jsonl / drafts.jsonl）
         每行至少要有文本字段：comment / text，平台字段：platform（可缺，缺=unknown）
Output : cph4/fleet/social/STYLE-PROFILE-v1.json  机读（drafts 会读它定风格参数）
         cph4/fleet/social/STYLE-REPORT.md        人读一屏

Usage:
  python3 Tools/fleet/social_profile.py cph4/fleet/social/inbox.jsonl
  python3 Tools/fleet/social_profile.py --raw-dir cph4/fleet/social/raw
  python3 Tools/fleet/social_profile.py --self-test
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
OUT_JSON = os.path.join(SOCIAL, "STYLE-PROFILE-v1.json")
OUT_MD = os.path.join(SOCIAL, "STYLE-REPORT.md")

EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
ASK = re.compile(r"(吗|呢|\?|？|求|请问|怎么|什么|哪|多少|能不能|有没有|如何)")
URGE = re.compile(r"(什么时候|多久|还更|不更|催更|快点|更新|下一|后面|蹲)")
PRAISE = re.compile(r"(好听|好看|好美|太强|牛|厉害|绝了|顶|爱了|喜欢|牛啊|帅|美)")
NEG = re.compile(r"(难看|垃圾|浪费|退|取关|别更|拉黑|恶心|烂|劝退|一般般|不行)")
LAUGH = re.compile(r"(哈哈|233|hhh|笑死|草|乐|绷不住|救命)")
NETWORD = re.compile(r"(yyds|awsl|xswl|绝绝子|栓Q|emo|破防|真香|爷青回|YYDS|泪目|离谱)")
EXCLAIM = re.compile(r"[!！]")
MENTION = re.compile(r"@[\w\u4e00-\u9fa5]+")
MONEY = re.compile(r"(\d+\s*[元块]|多少钱|价格|付费|买)")
STOP = set("的了是我你他她它我们你们这那个一不在有和就把被让给说得地很都也还就又才而要会能可对与及或者吧啊呢吗呀哈哦嗯咯嘛")


def _txt(r):
    return str(r.get("comment") or r.get("text") or "").strip()


def _tokenize(text):
    """不做分词依赖：中文按 2-3 字滑窗，英文/数字按词。够画像用，且零依赖。"""
    toks = re.findall(r"[A-Za-z]{2,}|\d+", text)
    han = re.findall(r"[\u4e00-\u9fa5]+", text)
    for seg in han:
        for n in (2, 3):
            for i in range(len(seg) - n + 1):
                g = seg[i:i + n]
                if not (set(g) & STOP) or len(g) == 3:
                    toks.append(g)
    return toks


def profile(rows):
    """返回 {platform: 画像} + overall。"""
    buckets = {}
    for r in rows:
        t = _txt(r)
        if not t:
            continue
        p = str(r.get("platform") or "unknown")
        buckets.setdefault(p, []).append(t)

    def one(texts):
        n = len(texts)
        lens = [len(t) for t in texts]
        cnt = Counter()
        cnt["emoji"] = sum(1 for t in texts if EMOJI.search(t))
        cnt["ask"] = sum(1 for t in texts if ASK.search(t))
        cnt["urge"] = sum(1 for t in texts if URGE.search(t))
        cnt["praise"] = sum(1 for t in texts if PRAISE.search(t))
        cnt["neg"] = sum(1 for t in texts if NEG.search(t))
        cnt["laugh"] = sum(1 for t in texts if LAUGH.search(t))
        cnt["netword"] = sum(1 for t in texts if NETWORD.search(t))
        cnt["exclaim"] = sum(1 for t in texts if EXCLAIM.search(t))
        cnt["mention"] = sum(1 for t in texts if MENTION.search(t))
        cnt["money"] = sum(1 for t in texts if MONEY.search(t))
        tok = Counter()
        for t in texts:
            tok.update(_tokenize(t))
        rate = {k: round(v / max(n, 1), 3) for k, v in cnt.items()}
        p50 = int(statistics.median(lens)) if lens else 0
        p90 = int(sorted(lens)[int(0.9 * (n - 1))]) if lens else 0
        # 回复建议（派生参数，drafts 直接读）
        return {
            "n": n,
            "len_mean": round(sum(lens) / max(n, 1), 1),
            "len_p50": p50, "len_p90": p90,
            "rates": rate,
            "top_terms": tok.most_common(12),
            "advice": {
                "reply_len_target": max(6, min(24, int(p50 * 0.8) or 10)),
                "emoji_budget": 0 if rate["emoji"] < 0.05 else (1 if rate["emoji"] < 0.2 else 2),
                "allow_question": rate["ask"] < 0.25,
                "tone": ("热闹/敢玩梗" if rate["laugh"] + rate["netword"] > 0.25 else
                         ("克制/少语气词" if rate["laugh"] + rate["netword"] < 0.08 else "中性")),
            },
        }

    out = {p: one(v) for p, v in buckets.items()}
    allrows = [t for v in buckets.values() for t in v]
    if allrows:
        out["_overall"] = one(allrows)
    return out


def load_rows(paths=None, raw_dir=None):
    rows = []
    files = list(paths or [])
    if raw_dir:
        files += sorted(glob.glob(os.path.join(raw_dir, "*.jsonl")))
    for f in files:
        if not os.path.exists(f):
            continue
        # 文件名 <platform>.<behavior>.jsonl 时，platform 从文件名补
        base = os.path.basename(f)
        fplat = base.split(".")[0] if base.count(".") >= 2 else None
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if not r.get("platform") and fplat and fplat not in ("inbox", "drafts"):
                r["platform"] = fplat
            rows.append(r)
    return rows


def render_md(prof):
    lines = ["# 平台评论风格画像 %s" % os.path.basename(OUT_JSON), ""]
    order = [k for k in prof if k != "_overall"] + (["_overall"] if "_overall" in prof else [])
    for p in order:
        d = prof[p]
        r = d["rates"]
        lines += ["## %s（%d 条）" % (p, d["n"]),
                  "- 长度：均值 %.1f 字 / 中位 %d / P90 %d" % (d["len_mean"], d["len_p50"], d["len_p90"]),
                  "- 特征：问句 %.0f%% · 催更 %.0f%% · 夸赞 %.0f%% · 负面 %.0f%% · 笑 %.0f%% · 网络词 %.0f%% · emoji %.0f%% · 感叹号 %.0f%%"
                  % (r["ask"] * 100, r["urge"] * 100, r["praise"] * 100, r["neg"] * 100,
                     r["laugh"] * 100, r["netword"] * 100, r["emoji"] * 100, r["exclaim"] * 100),
                  "- 高频词：" + "、".join("%s(%d)" % (w, c) for w, c in d["top_terms"][:10]),
                  "- 回复建议：目标 %d 字 · emoji 上限 %d · 允许反问 %s · 语气 %s"
                  % (d["advice"]["reply_len_target"], d["advice"]["emoji_budget"],
                     "是" if d["advice"]["allow_question"] else "否", d["advice"]["tone"]),
                  ""]
    return "\n".join(lines) + "\n"


def self_test():
    cases = []
    rows = [
        {"platform": "bilibili", "comment": "这段剪辑太顺了哈哈哈哈"},
        {"platform": "bilibili", "comment": "求bgm名字！！"},
        {"platform": "bilibili", "comment": "什么时候更新啊，蹲一个"},
        {"platform": "bilibili", "comment": "yyds 绝了"},
        {"platform": "douyin", "comment": "多少钱一条 报价"},
        {"platform": "douyin", "comment": "难看死了 取关"},
        {"platform": "xiaohongshu", "comment": "姐妹这个色号好好看🥹"},
    ]
    p = profile(rows)
    b, d = p["bilibili"], p["douyin"]
    cases.append(("平台分桶正确", b["n"] == 4 and d["n"] == 2))
    cases.append(("B站问句率应高", b["rates"]["ask"] >= 0.5))
    cases.append(("B站有笑/梗", b["rates"]["laugh"] + b["rates"]["netword"] > 0))
    cases.append(("抖音识别报价/负面", d["rates"]["money"] > 0 and d["rates"]["neg"] > 0))
    cases.append(("小红书 emoji 被识别", p["xiaohongshu"]["rates"]["emoji"] == 1.0))
    cases.append(("回复长度建议在 6-24", 6 <= b["advice"]["reply_len_target"] <= 24))
    cases.append(("总体段存在", "_overall" in p and p["_overall"]["n"] == 7))
    # 空输入不许炸
    cases.append(("空输入返回空画像", profile([]) == {}))
    # 文件名补平台
    rows2 = load_rows([os.path.join(SOCIAL, "nonexist.jsonl")])
    cases.append(("缺文件不炸", rows2 == []))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--raw-dir", default=None)
    ap.add_argument("--out-json", default=OUT_JSON)
    ap.add_argument("--out-md", default=OUT_MD)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    rows = load_rows(a.files, a.raw_dir)
    if not rows:
        print("[profile] 没有可分析的评论（给 jsonl 或 --raw-dir）")
        return 2
    prof = profile(rows)
    json.dump(prof, open(a.out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(a.out_md, "w", encoding="utf-8").write(render_md(prof))
    for p, d in prof.items():
        print("[profile] %-14s n=%-4d 中位%2d字 问%.0f%% 催%.0f%% 负%.0f%% → %s"
              % (p, d["n"], d["len_p50"], d["rates"]["ask"] * 100, d["rates"]["urge"] * 100,
                 d["rates"]["neg"] * 100, d["advice"]["tone"]))
    print("[profile] -> %s / %s" % (a.out_json, a.out_md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
