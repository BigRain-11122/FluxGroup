#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""segment_personas.py - 按段把"人群习惯"从真实语料里量出来（不是形容词）。

CEO 2026-11-19「我要求的就是你分足够多的人群画像和习惯等，能应对自如」。

为什么要这个：AUDIENCE-SEGMENTS-v1.json 里的 lang（长度带/语气/emoji 上限）是**手写**的，
而生成侧用的是全局统一字数带——等于对所有人说同一种话。这里做两件事：

  1 MEASURE  每段从 QUALITY-PASS 语料里量出真实习惯：中位长度、P90、问句率、
             emoji 密度、感叹号率、口语助词种类、样本数。
  2 CALIBRATE 把量出来的分布与规格里的 lang.len 对比，冲突就报（不改规格，报事实）：
             规格说 memer 8-20 字而实测中位 31 字，那不是模型问题，是尺子问题。

输出：
  cph4/fleet/social/SEGMENT-PERSONAS-v1.json   机读（生成侧取参数的唯一来源）
  cph4/fleet/social/SEGMENT-PERSONAS.md        人读（一屏扫完）

自检（负控，不通过就不许上线）：
  - 样本 < MIN_N 的段必须标 insufficient，且不许被生成侧当可用参数
  - 人为把某段样本换成超长句，median 必须跟着变（量的是分布不是常量）
  - 规格 len 与实测 P10-P90 区间不重叠时必须报 mismatch（否则等于没校准）
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
CORPUS = os.path.join(SOCIAL, "corpus", "human", "QUALITY-PASS.jsonl")
SPEC = os.path.join(SOCIAL, "AUDIENCE-SEGMENTS-v1.json")
OUT_JSON = os.path.join(SOCIAL, "SEGMENT-PERSONAS-v1.json")
OUT_MD = os.path.join(SOCIAL, "SEGMENT-PERSONAS.md")

MIN_N = 60          # 少于这个数就不给参数（用 30 条估分布＝用噪声当习惯）
ORAL = set("吧啊呀呢嘛啦咩咯诶嗷嗯哦哈嘿")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]|\\[[^\\]]{1,6}\\]")
Q = re.compile(r"[?？]|(吗|呢|怎么|如何|哪|啥|求|有没有)")

sys.path.insert(0, HERE)


def pct(xs, p):
    if not xs:
        return 0
    s = sorted(xs)
    k = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return s[k]


def habits(rows):
    """一群真实评论的"习惯"长什么样——全部可复算，不含任何形容词。"""
    n = len(rows)
    if not n:
        return {"n": 0, "insufficient": True}
    lens = [len(r["text"]) for r in rows]
    return {
        "n": n,
        "insufficient": n < MIN_N,
        "len_median": pct(lens, 50),
        "len_p10": pct(lens, 10),
        "len_p90": pct(lens, 90),
        "question_rate": round(sum(1 for r in rows if Q.search(r["text"])) / n, 3),
        "emoji_rate": round(sum(1 for r in rows if EMOJI.search(r["text"])) / n, 3),
        "exclaim_rate": round(sum(1 for r in rows if "！" in r["text"] or "!" in r["text"]) / n, 3),
        "oral_rate": round(sum(1 for r in rows if any(c in ORAL for c in r["text"])) / n, 3),
        "samples": [r["text"][:40] for r in rows[:3]],
    }

def measure(rows, spec):
    """按段归并，返回 {seg: habits}。generic 单列——它不进任何人群段。

    额外算 in_band：实测样本落在"规格字数带"内的比例——校准判据要用它，
    只比区间是否重叠会把"12-30 的规格遇上 9-63 的实测"判成对齐。
    """
    segs = spec.get("segments") or []
    bands = {s["id"]: ((s.get("lang") or {}).get("len") or [0, 10 ** 6]) for s in segs}
    buckets = {s["id"]: [] for s in segs}
    buckets.setdefault("generic", [])
    for r in rows:
        t = r.get("text") or ""
        if len(t) < 8:
            continue
        seg = classify_cached(t)
        buckets.setdefault(seg, []).append(r)
    out = {}
    for k, v in buckets.items():
        h = habits(v)
        if v and not h.get("insufficient"):
            lo, hi = bands.get(k) or [0, 10 ** 6]
            h["in_band"] = round(sum(1 for r in v if lo <= len(r["text"]) <= hi) / len(v), 3)
        out[k] = h
    return out


_SPEC = None


def classify_cached(t):
    global _SPEC
    if _SPEC is None:
        import segments as sg
        _SPEC = sg.load_spec()
    import segments as sg
    return sg.classify(t, _SPEC)["primary"]


def calibrate(personas, spec, rows_by_seg=None, cover_min=0.60):
    """实测 vs 规格：报"规格带子能不能代表这一群人"，不自动改规格。

    2026-11-19 初版只判"区间是否重叠"——12-30 的规格遇上 9-63 的实测当然重叠，
    于是每段都判"对齐"，等于没有校准。现改为两条硬判据：
      ①**覆盖率**：实测样本落在规格带内的比例 >= cover_min；
      ②**中位在带内**：规格带不包含真实中位，就是尺子错了（不是模型错）。
    """
    out = {}
    for s in (spec.get("segments") or []):
        sid = s["id"]
        p = personas.get(sid) or {}
        lo, hi = (s.get("lang") or {}).get("len") or [0, 0]
        if p.get("insufficient"):
            continue
        cov = p.get("in_band", 0.0)
        med = p.get("len_median") or 0
        ok_cov = cov >= cover_min
        ok_med = lo <= med <= hi
        out[sid] = {
            "spec_len": [lo, hi],
            "measured_len_median": med,
            "measured_p10_p90": [p.get("len_p10"), p.get("len_p90")],
            "in_band_rate": round(cov, 3),
            "verdict": "对齐" if (ok_cov and ok_med) else
                       ("不一致：规格 [%d,%d] 只覆盖实测 %.0f%%（中位 %d）"
                        % (lo, hi, 100 * cov, med)),
        }
    return out


def build():
    rows = []
    for line in open(CORPUS, encoding="utf-8"):
        if line.strip():
            rows.append(json.loads(line))
    spec = json.load(open(SPEC, encoding="utf-8"))
    personas = measure(rows, spec)
    cal = calibrate(personas, spec)
    doc = {"version": "SEGMENT-PERSONAS-v1", "corpus": os.path.relpath(CORPUS, ROOT),
           "corpus_n": len(rows), "min_n": MIN_N, "segments": {}, "calibration": cal}
    for s in (spec.get("segments") or []):
        sid = s["id"]
        p = dict(personas.get(sid) or {})
        p["name"] = s.get("name")
        p["risk"] = s.get("risk")
        # 生成侧参数：规格给语义（tone/address/do/dont），实测给硬数字（带子）
        p["gen"] = {
            "len": [p.get("len_p10") or 0, p.get("len_p90") or 0] if not p.get("insufficient")
                   else (s.get("lang") or {}).get("len"),
            "tone": (s.get("lang") or {}).get("tone"),
            "address": (s.get("lang") or {}).get("address"),
            "emoji_max": 1 if p.get("emoji_rate", 0) >= 0.15 else 0,
            "slang": (s.get("lang") or {}).get("slang"),
            "source": "measured" if not p.get("insufficient") else "spec-fallback",
        }
        p["do"] = s.get("do")
        p["dont"] = s.get("dont")
        doc["segments"][sid] = p
    # generic 不进选段，但要在屏上看见它的体重
    doc["generic"] = personas.get("generic")
    json.dump(doc, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return doc


def render(doc):
    segs = doc["segments"]
    order = sorted(segs.items(), key=lambda kv: -(kv[1].get("n") or 0))
    L = ["# 人群画像与习惯（实测，%d 条过闸语料）" % doc["corpus_n"], "",
         "- 段数 %d ｜ 可用（n≥%d）%d 个 ｜ 语料不足 %d 个 ｜ generic 体量 %d 条（%.0f%%）"
         % (len(segs), doc["min_n"],
            sum(1 for _, p in order if not p.get("insufficient")),
            sum(1 for _, p in order if p.get("insufficient")),
            (doc.get("generic") or {}).get("n") or 0,
            100.0 * ((doc.get("generic") or {}).get("n") or 0) / max(1, doc["corpus_n"])),
         "",
         "| 段 | 名称 | 样本 | 中位字 | P10–P90 | 问句率 | emoji | 感叹 | 口语 | 生成带 | 依据 |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for sid, p in order:
        if p.get("insufficient"):
            L.append("| %s | %s | %d | — | — | — | — | — | — | %s | 语料不足 |"
                     % (sid, p.get("name") or "", p.get("n") or 0,
                        (p.get("gen") or {}).get("len")))
            continue
        L.append("| %s | %s | %d | %d | %d–%d | %.0f%% | %.0f%% | %.0f%% | %.0f%% | %d–%d | %s |"
                 % (sid, p.get("name") or "", p["n"], p["len_median"], p["len_p10"], p["len_p90"],
                    100 * p["question_rate"], 100 * p["emoji_rate"], 100 * p["exclaim_rate"],
                    100 * p["oral_rate"], p["gen"]["len"][0], p["gen"]["len"][1],
                    p["gen"]["source"]))
    bad = [(k, v["verdict"]) for k, v in (doc.get("calibration") or {}).items()
           if v["verdict"] != "对齐"]
    L += ["", "## 规格与实测不一致（尺子问题，不是模型问题）", ""]
    if bad:
        for k, v in bad:
            L.append("- **%s**：%s" % (k, v))
    else:
        L.append("- 全部对齐")
    L += ["", "## 典型样本（每段 3 条，取自真实过闸语料）", ""]
    for sid, p in order[:6]:
        if p.get("insufficient"):
            continue
        L.append("**%s**：%s" % (sid, " ／ ".join(p.get("samples") or [])))
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return OUT_MD


def self_test():
    ok, bad = [], []

    def chk(name, cond):
        (ok if cond else bad).append(name)

    # 1 分布是真的被量出来的（换成长句，中位必须涨）
    a = habits([{"text": "短句"}, {"text": "也很短"}])
    b = habits([{"text": "这是一句明显更长的评论内容用来验证中位数会跟着变"}, {"text": "也是一句同样很长的评论内容"}])
    chk("中位数随内容变化", b["len_median"] > a["len_median"] + 10)
    # 2 样本不足必须标 insufficient（30 条不许当习惯）
    c = habits([{"text": "随便一句够长的评论内容"} for _ in range(MIN_N - 1)])
    chk("样本不足标 insufficient", c["insufficient"] is True)
    d = habits([{"text": "随便一句够长的评论内容"} for _ in range(MIN_N)])
    chk("样本足够不误标", d["insufficient"] is False)
    # 3 规格与实测不重叠必须报不一致
    spec = {"segments": [{"id": "x", "lang": {"len": [5, 10]}}]}
    # 覆盖不足必须报不一致（规格 5-10 字，实测全在 30-50）
    cal = calibrate({"x": {"insufficient": False, "len_p10": 30, "len_p90": 50,
                            "len_median": 40, "in_band": 0.0}}, spec)
    chk("覆盖不足报不一致", cal["x"]["verdict"] != "对齐")
    # 负控：中位落在带内且覆盖达标才算对齐
    cal2 = calibrate({"x": {"insufficient": False, "len_p10": 6, "len_p90": 9,
                            "len_median": 8, "in_band": 0.95}}, spec)
    chk("中位在带内且覆盖达标=对齐", cal2["x"]["verdict"] == "对齐")
    # 负控：中位在带外即使覆盖有部分也必须报不一致
    cal3 = calibrate({"x": {"insufficient": False, "len_p10": 6, "len_p90": 40,
                            "len_median": 25, "in_band": 0.7}}, spec)
    chk("中位在带外报不一致", cal3["x"]["verdict"] != "对齐")
    # 4 问句率/emoji 是可复算的
    e = habits([{"text": "这个怎么做的？"}, {"text": "好耶[笑哭]"}] * 40)
    chk("问句率可复算", abs(e["question_rate"] - 0.5) < 0.05)
    chk("emoji 可复算", abs(e["emoji_rate"] - 0.5) < 0.05)

    for n in ok:
        print("  PASS", n)
    for n in bad:
        print("  FAIL", n)
    print("[personas] self-test %d/%d" % (len(ok), len(ok) + len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    doc = build()
    print("[personas] 写出 %s" % os.path.relpath(OUT_JSON, ROOT))
    print("[personas] 一屏 %s" % os.path.relpath(render(doc), ROOT))
