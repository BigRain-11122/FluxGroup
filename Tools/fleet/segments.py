#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""segments.py — 人群细分识别器（确定性，零 LLM）。

为什么要有它：回复要"迎合不同人群的口味"，前提是先认出对面是谁。同一句话对不同人是
不同的正确答案——对零基础新手讲原理=没帮上，对同行讲基础概念=冒犯，对索取型画饼=招骂。
所以段位必须是可复算的判据，而不是生成时让模型自己猜。

口径（与 AUDIENCE-SEGMENTS-v1.json 对齐）：
  - 多段命中报 primary + secondary；primary = 命中信号数最多、同分按文件顺序。
  - 无信号 = generic（不猜）。硬套比不套更假。
  - 输出带 matched 信号，可审计、可回归。

用法：
  python3 Tools/fleet/segments.py --text "零基础，求教程"          # 判一条
  python3 Tools/fleet/segments.py --corpus <jsonl>               # 语料段位分布
  python3 Tools/fleet/segments.py --self-test                    # 判据自检
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "social", "AUDIENCE-SEGMENTS-v1.json")


def load_spec(path=SPEC):
    return json.load(open(path, encoding="utf-8"))


def classify(text, spec=None):
    """返回 {primary, secondary, matched, lang, risk, n_hits}。"""
    spec = spec or load_spec()
    t = (text or "").lower()
    hits = []
    for seg in spec["segments"]:
        m = [w for w in seg["signals"] if w.lower() in t]
        if m:
            hits.append((len(m), seg, m))
    if not hits:
        g = spec["generic"]
        return {"primary": "generic", "secondary": [], "matched": [],
                "lang": g["lang"], "risk": "低", "n_hits": 0}
    # 命中数优先；同分保持文件顺序（稳定、可回归）
    hits.sort(key=lambda x: -x[0])
    primary = hits[0][1]
    secondary = [h[1]["id"] for h in hits[1:]]
    return {"primary": primary["id"], "secondary": secondary,
            "matched": hits[0][2], "lang": primary["lang"],
            "risk": primary.get("risk", "低"), "n_hits": hits[0][0]}


def style_block(seg, spec=None):
    """给生成用的段位指令（判据式，不含例句——写例句模型会照抄）。"""
    spec = spec or load_spec()
    row = next((s for s in spec["segments"] if s["id"] == seg), None)
    if not row:
        g = spec["generic"]
        return "未识别人群：用平实口吻，%d-%d 字，不用梗。" % tuple(g["lang"]["len"])
    l = row["lang"]
    return ("对方属于「%s」：%d-%d 字，%s，称呼=%s，emoji≤%d，%s。该做：%s；不该做：%s"
            % (row["name"], l["len"][0], l["len"][1], l["tone"], l["address"], l["emoji_max"],
               "可用网络梗" if l["slang"] else "不用网络梗",
               "、".join(row["do"]), "、".join(row["dont"])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--corpus")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    spec = load_spec()

    if a.self_test:
        cases = [
            ("零基础新手，不知道从哪里开始，求教程", "beginner"),
            ("学生党宿舍里剪的，暑假作业做完了", "student"),
            ("做后期的，甲方爸爸又改需求了", "peer_pro"),
            ("这段的码率和宽容度多少，用的什么头", "tech_nerd"),
            ("看哭了，想起我高中暗恋的那个女生", "feeler"),
            ("要素察觉，笑死，狗头保命", "memer"),
            ("求工作流，求素材，已三连", "requester"),
            ("节奏太乱了，有点糊，看不下去", "critic"),
            ("前排打卡，支持一下", "shallow"),
            ("带娃没时间剪，哄睡以后才能摸电脑", "family"),
            ("這個剪輯覺得很好看，畫面很穩", "traditional"),
            ("今天天气不错", "generic"),
        ]
        ok = 0
        for text, want in cases:
            got = classify(text, spec)["primary"]
            if got == want:
                ok += 1
            else:
                print("  FAIL %-24s 期望 %-10s 得到 %s" % (text[:24], want, got))
        # 判据强度负控：把某段的 signals 全删，必须落回 generic
        broken = json.loads(json.dumps(spec))
        for s in broken["segments"]:
            if s["id"] == "student":
                s["signals"] = []
        got = classify("学生党宿舍里剪的", broken)["primary"]
        ok += 1 if got != "student" else 0
        print("[self-test] %d/%d %s" % (ok, len(cases) + 1, "PASS" if ok == len(cases) + 1 else "FAIL"))
        return 0 if ok == len(cases) + 1 else 1

    if a.text:
        r = classify(a.text, spec)
        if a.json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            print("[seg] %s（命中 %d：%s）次选=%s 风险=%s"
                  % (r["primary"], r["n_hits"], "/".join(r["matched"]) or "-",
                     ",".join(r["secondary"]) or "-", r["risk"]))
            print("[seg] %s" % style_block(r["primary"], spec))
        return 0

    if a.corpus:
        rows = [json.loads(l) for l in open(a.corpus, encoding="utf-8") if l.strip()]
        dist, risk = {}, {}
        for r in rows:
            s = classify(r.get("text"), spec)
            dist[s["primary"]] = dist.get(s["primary"], 0) + 1
            if s["risk"].startswith("高"):
                risk["high"] = risk.get("high", 0) + 1
        total = len(rows) or 1
        print("[seg] 语料 %d 条，段位分布：" % len(rows))
        for k, v in sorted(dist.items(), key=lambda kv: -kv[1]):
            print("  %-12s %5d  %4.1f%%" % (k, v, v * 100.0 / total))
        if dist.get("generic"):
            print("  未识别占比 %.1f%%——太高说明信号词没覆盖真实说法，要补 signals" %
                  (dist["generic"] * 100.0 / total))
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
