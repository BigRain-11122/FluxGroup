#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""platform_tone.py — 量出每个平台的"调性指纹"，让提示词按平台分别对版。

CEO 2026-11-23：「还是要符合各个平台用户群的调性，他们都不一样的，你好好调研或者去拉数据」。

为什么要有这个工具：调性不能靠形容词（"小红书更活泼"是废话），要能算出来。
每个平台给一组可复算的数：字数中位、短句率、标点率、表情率、语气词率、
第一人称率、句式分布、高频词，再配 8 条真实样本做 few-shot。

用法：
  platform_tone.py --platform bilibili --src corpus/human/own_collected.jsonl
  platform_tone.py --platform gzh --src gzh/ARTICLES.jsonl --field content
  platform_tone.py --all                      # 跑已配置的全部平台并出对比表
  platform_tone.py --self-test                # 负控：造两份调性迥异的样本必须被区分开

产出：cph4/fleet/social/PLATFORM-TONE-v1.json（机读）+ 控制台对比表
Exit: 0 正常；1 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
OUT = os.path.join(SOCIAL, "PLATFORM-TONE-v1.json")

# 每平台的数据源与字段（没有数据源就写 None，绝不假装有）
SOURCES = {
    "bilibili": {"path": os.path.join(SOCIAL, "corpus", "human", "own_collected.jsonl"),
                 "field": "text"},
    "gzh": {"path": os.path.join(SOCIAL, "gzh", "ARTICLES.jsonl"), "field": "text"},
    "xiaohongshu": {"path": os.path.join(SOCIAL, "raw", "xiaohongshu.comment.jsonl"),
                    "field": "text"},
    "zhihu": {"path": os.path.join(SOCIAL, "raw", "zhihu.comment.jsonl"), "field": "text"},
    "douyin": {"path": os.path.join(SOCIAL, "raw", "douyin.comment.jsonl"), "field": "text"},
}

EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")     # 真表情
EMOJI_CODE = re.compile(r"\[[^\]]{1,10}\]")                     # [doge] 这类代码表情
ORAL = ("啊", "吧", "呢", "嘛", "哈", "哦", "呀", "啦", "唉", "诶", "哎", "唔", "嗯")
HEDGE = ("感觉", "觉得", "好像", "可能", "其实", "有点", "挺", "太", "真的", "估计")
FIRST = ("我", "俺", "咱")
SELF_KNOCK = ("我不会", "我不配", "菜", "渣", "翻车", "不懂", "看不懂", "没看懂")


def norm(t):
    return re.sub(r"\s+", " ", (t or "").strip())


def metrics(texts):
    """把一组文本压成可复算的调性指标。全部用占比/中位数，不用形容词。"""
    ts = [norm(t) for t in texts if norm(t)]
    if not ts:
        return None
    n = len(ts)
    lens = [len(t) for t in ts]

    def rate(pred):
        return round(100.0 * sum(1 for t in ts if pred(t)) / n, 1)

    # 句末标点：真人评论常常没有（B 站 78% 不写句号）
    no_end = rate(lambda t: not re.search(r"[。！？!?…~～]$", t))
    q = rate(lambda t: bool(re.search(r"[？?]", t)))
    ex = rate(lambda t: bool(re.search(r"[！!]", t)))
    emoji = rate(lambda t: bool(EMOJI.search(t)))
    code = rate(lambda t: bool(EMOJI_CODE.search(t)))
    oral = rate(lambda t: any(w in t for w in ORAL))
    hedge = rate(lambda t: any(w in t for w in HEDGE))
    first = rate(lambda t: any(w in t for w in FIRST))
    knock = rate(lambda t: any(w in t for w in SELF_KNOCK))
    short = rate(lambda t: len(t) <= 10)

    # 高频词（2 字以上、出现≥3 次），按出现文本数排，避免长文刷榜
    df = {}
    for t in ts:
        for w in set(re.findall(r"[\u4e00-\u9fa5]{2,4}", t)):
            df[w] = df.get(w, 0) + 1
    top = [w for w, c in sorted(df.items(), key=lambda kv: -kv[1]) if c >= 3][:12]

    # 样本：取长度接近中位的 8 条（最能代表平台语体，不用最长的）
    med = statistics.median(lens)
    pool = sorted(ts, key=lambda t: abs(len(t) - med))
    samples = pool[:8]

    return {"n": n, "len_mean": round(statistics.mean(lens), 1), "len_median": med,
            "short_rate": short, "no_end_punct_rate": no_end,
            "question_rate": q, "exclaim_rate": ex,
            "emoji_rate": emoji, "emoji_code_rate": code,
            "oral_particle_rate": oral, "hedge_rate": hedge,
            "first_person_rate": first, "self_knock_rate": knock,
            "top_words": top, "samples": samples}


def load(path, field):
    rows = []
    if not path or not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            v = d.get(field) or ""
            if isinstance(v, str) and v:
                rows.append(v)
    return rows


def run_one(platform):
    cfg = SOURCES.get(platform) or {}
    texts = load(cfg.get("path"), cfg.get("field", "text"))
    if not texts:
        return {"platform": platform, "status": "NO-DATA",
                "note": "无语料（需采集：%s）" % (cfg.get("path") or "未配置")}
    m = metrics(texts)
    return dict(platform=platform, status="OK", src=os.path.relpath(cfg["path"], ROOT), **m)


def self_test():
    cases = []
    short_party = ["好家伙[doge]", "绝了", "哈哈哈哈哈", "xsl", "我裂开了"] * 4
    long_prose = ["这个问题需要从产业结构的角度来分析，首先要看上游供给。",
                  "我们认为，长期来看这一趋势不会改变，但短期存在波动。"] * 4
    a, b = metrics(short_party), metrics(long_prose)
    cases.append(("中位长度能分开两种语体", a["len_median"] < b["len_median"]))
    cases.append(("表情率能分开", a["emoji_code_rate"] > b["emoji_code_rate"]))
    cases.append(("无句末标点率能分开", a["no_end_punct_rate"] > b["no_end_punct_rate"]))
    cases.append(("空输入返回 None", metrics([]) is None and metrics(["", " "]) is None))
    bad = [n for n, ok in cases if not ok]
    for n, ok in cases:
        print("  %s %s" % ("PASS" if ok else "FAIL", n))
    print("[self-test] %d/%d %s" % (len(cases) - len(bad), len(cases), "PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


def show(rows):
    print("%-12s %6s %7s %7s %7s %7s %7s %7s" % (
        "平台", "n", "中位字", "短句%", "无句号%", "表情%", "语气词%", "第一人称%"))
    for r in rows:
        if r.get("status") != "OK":
            print("%-12s  %s" % (r["platform"], r.get("note")))
            continue
        print("%-12s %6d %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f" % (
            r["platform"], r["n"], r["len_median"], r["short_rate"],
            r["no_end_punct_rate"], r["emoji_rate"] + r["emoji_code_rate"],
            r["oral_particle_rate"], r["first_person_rate"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", choices=sorted(SOURCES))
    ap.add_argument("--src")
    ap.add_argument("--field", default="text")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    rows = []
    if a.platform:
        if a.src:
            SOURCES[a.platform] = {"path": a.src, "field": a.field}
        rows.append(run_one(a.platform))
    elif a.all:
        rows = [run_one(p) for p in SOURCES]
    else:
        ap.error("要么 --platform，要么 --all")

    show(rows)
    data = {}
    if os.path.exists(OUT):
        try:
            data = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            data = {}
    data.setdefault("platforms", {})
    for r in rows:
        data["platforms"][r["platform"]] = r
    data["_why"] = ("各平台调性指纹：全部是可复算的占比/中位数，不是形容词。"
                    "CEO 2026-11-23「各个平台用户群的调性都不一样」")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("\n写入 %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
