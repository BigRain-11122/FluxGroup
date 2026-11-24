#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e2e_gate.py - 闭环验收：拿固定题集跑一遍真实产线，自己判"能上"还是"该回滚"。

为什么要有它（CEO 2026-11-18 原话「自己要去循环测试，闭环测试，自己去判断」）：
训练脚本只会算一个 taste 分，那不等于产线能用。真验收必须跑**整条链**：
同一批视频 → 真出稿 → 过同一把闸 → 算覆盖率与中位分 → 和写死的门槛比。

三条口径（不许临场改）：
  1 题集固定：视频 key 列表落盘（EVAL-VIDEOS.json），每轮都用同一批，换批次就没法比。
  2 门槛写死：覆盖率 ≥40/43 且 品味中位 ≥80（正身 ACCEPTANCE-TRAIN.md）。
  3 判词三态：ACCEPT / REJECT（并给出回滚指令）/ INCONCLUSIVE（题集不全或服务不可用）。

失败归因（用于"下一步试什么"，这是自我迭代的判断依据）：
  太长 / RISKY / 照抄语料 / 语感闸BLOCK / 红线  各自计数，占比最高者决定下一个配方。

用法：
  python3 Tools/fleet/e2e_gate.py --self-test
  python3 Tools/fleet/e2e_gate.py --videos 43            # 真跑一轮
  python3 Tools/fleet/e2e_gate.py --record-baseline      # 把当前结果记为基线
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
SET_F = os.path.join(SOCIAL, "EVAL-VIDEOS.json")
BASE_F = os.path.join(SOCIAL, "E2E-BASELINE.json")
OUT_F = os.path.join(ROOT, ".codely-cli", "state", "e2e-gate.json")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")

sys.path.insert(0, HERE)
import comment_taste as ct          # noqa: E402
import llm_client as lc            # noqa: E402
import social_comment_gen as cg   # noqa: E402

# 门槛写死（改这里必须同时改 ACCEPTANCE-TRAIN.md，并在提交里写依据）
MIN_COVERAGE = 40          # 43 条视频里至少 40 条能出稿
MIN_MEDIAN = 80
N_VIDEOS = 43
LANES = ("lora", "4b", "2b")


def load_set():
    """固定题集：只有第一次生成，之后一律复用（换了题集，历史分数就不可比）。"""
    d = None
    try:
        d = json.load(open(SET_F, encoding="utf-8"))
    except Exception:
        pass
    if d and d.get("videos"):
        return d
    try:
        vids = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        return {"videos": [], "created": None}
    v = [{"key": k, "title": (m or {}).get("title") or "", "desc": (m or {}).get("desc") or ""}
         for k, m in vids.items() if (m or {}).get("title")][:N_VIDEOS]
    d = {"created": datetime.now().isoformat(timespec="seconds"), "videos": v}
    json.dump(d, open(SET_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return d


def lora_up():
    try:
        lc._lora_model(timeout=5)
        return True
    except Exception:
        return False


def run_e2e(videos, corpus_texts=None):
    """按产线同样的方式出稿并过闸，返回逐视频结果。"""
    corpus = corpus_texts if corpus_texts is not None else cg.corpus_texts()
    taken, per_video = [], []
    t0 = time.time()
    for n, v in enumerate(videos):
        ctx = (v["title"] or "")[:40]
        got = {}

        def work(lane):
            got[lane] = cg.gen_one(lane, v["title"], v.get("desc") or "", n)

        th = [threading.Thread(target=work, args=(x,)) for x in LANES]
        [t.start() for t in th]
        [t.join() for t in th]

        best, fails = None, []
        for lane in LANES:
            r = got.get(lane) or {}
            if not r.get("ok"):
                fails.append("lane_fail")
                continue
            ok, why, s = cg.gate(r["text"], ctx=ctx, taken=taken, corpus=corpus)
            if ok:
                if best is None or (s or {}).get("total", 0) > best[1]:
                    best = (r["text"], (s or {}).get("total", 0), lane)
            else:
                fails.append(why)
        if best:
            taken.append(best[0])
        per_video.append({"video": v["key"], "title": ctx, "ok": bool(best),
                          "score": best[1] if best else None,
                          "lane": best[2] if best else None, "fails": fails})
        print("  [%d/%d] %s → %s" % (n + 1, len(videos), ctx[:22],
                                     "%.0f(%s)" % (best[1], best[2]) if best else "无"))
    ok_rows = [x for x in per_video if x["ok"]]
    scores = [x["score"] for x in ok_rows if x["score"]]
    return {"ts": datetime.now().isoformat(timespec="seconds"),
            "n_videos": len(videos), "coverage": len(ok_rows),
            "median": statistics.median(scores) if scores else 0,
            "min": min(scores) if scores else 0, "max": max(scores) if scores else 0,
            "secs": round(time.time() - t0, 1), "per_video": per_video}


def diagnose(res):
    """把失败原因归类，给出"下一步该试什么"——这是自我判断的部分，不是给人看的。"""
    # 归因键必须与 social_comment_gen.gate 的真实前缀一致，否则全判成 0（实锚：首跑全 0）
    bucket = {"品味闸": 0, "太长": 0, "太短": 0, "感叹号": 0, "踩红线": 0,
              "点名他人": 0, "指控": 0, "Markdown": 0, "与本视频领域无关": 0,
              "与本批重复": 0, "照抄语料": 0, "语感闸": 0, "lane_fail": 0}
    for x in res["per_video"]:
        if x["ok"]:
            continue
        for w in x["fails"]:
            for k in bucket:
                if w.startswith(k):
                    bucket[k] += 1
    total = sum(bucket.values()) or 1
    top = max(bucket.items(), key=lambda kv: kv[1])
    advice = {
        "品味闸": "五维闸没过（多为字数带/结构不合）：先看该段语料够不够，别调温度硬凑",
        "与本视频领域无关": "指令没把标题里的信息用起来：提示词缺上下文，不是模型不会写",
        "太短": "输出被截断：检查 max_tokens 与模板字数带",
        "点名他人": "生成时点名了真实账号：红线，回查 few-shot 是否混入 @",
        "指控": "出现盗/抄/无耻类词：链路红线，必须在生成侧拦",
        "太长": "收紧指令字数（8-35 已写死）或把 max_tokens 降到 48；先查模板是否被改回旧版",
        "照抄语料": "提高本批去重阈值 k（8→10）或减少 few-shot 条数",
        "语感闸": "查是否把 viewer 稿子拿 reply 口径量了（两套尺子不许混）",
        "红线": "命中导流/身份词：查 few-shot 里是否混入这类样本",
        "lane_fail": "8788 或 ollama 车道不可用：先看服务与内存，不要急着改模型",
    }
    return {"counts": bucket, "top": top[0], "top_share": round(100.0 * top[1] / total),
            "advice": advice.get(top[0], "")}


def judge(res, base=None):
    """三态判词 + 回滚指令。判据写死，不看"感觉变好了"。"""
    cov, med = res["coverage"], res["median"] or 0
    reasons = []
    if res["n_videos"] < N_VIDEOS:
        return "INCONCLUSIVE", ["题集只有 %d/%d 条，比分不可比" % (res["n_videos"], N_VIDEOS)]
    if cov < MIN_COVERAGE:
        reasons.append("覆盖率 %d/%d < %d" % (cov, N_VIDEOS, MIN_COVERAGE))
    if med < MIN_MEDIAN:
        reasons.append("品味中位 %.0f < %d" % (med, MIN_MEDIAN))
    if reasons:
        return "REJECT", reasons
    if base:
        if cov < base.get("coverage", 0):
            reasons.append("覆盖率低于基线 %d" % base.get("coverage", 0))
        if med < base.get("median", 0) - 2:
            reasons.append("中位低于基线 %.0f（容差 2 分）" % base.get("median", 0))
        if reasons:
            return "REJECT", reasons
    return "ACCEPT", []


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--videos", type=int, default=N_VIDEOS)
    ap.add_argument("--record-baseline", action="store_true")
    ap.add_argument("--no-lora", action="store_true", help="不查 8788（只跑 ollama 两车道）")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    s = load_set()
    videos = s["videos"][:a.videos]
    if not videos:
        print("[e2e] 没有题集（%s）——先跑一次采集把 VIDEO-TITLES.json 生出来" % SET_F)
        return 2
    if not a.no_lora and not lora_up():
        print("[e2e] 8788 不可用：先启动 com.fluxgroup.mlxlora（训练期间它会被停下）")
        return 2
    res = run_e2e(videos)
    dia = diagnose(res)
    base = None
    try:
        base = json.load(open(BASE_F, encoding="utf-8"))
    except Exception:
        pass
    verdict, why = judge(res, base)
    act = {}
    try:
        act = json.load(open(os.path.join(SOCIAL, "train", "ACTIVE.json"), encoding="utf-8"))
    except Exception:
        pass
    rec = {"ts": res["ts"], "verdict": verdict, "why": why,
           "coverage": res["coverage"], "n_videos": res["n_videos"],
           "median": res["median"], "min": res["min"], "max": res["max"],
           "secs": res["secs"], "diagnosis": dia, "adapter": act.get("adapter"),
           "baseline": base, "per_video": res["per_video"]}
    os.makedirs(os.path.dirname(OUT_F), exist_ok=True)
    json.dump(rec, open(OUT_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n[e2e] 覆盖率 %d/%d ｜ 品味中位 %.0f（%d–%d）｜ 用时 %.0fs"
          % (res["coverage"], res["n_videos"], res["median"], res["min"], res["max"], res["secs"]))
    print("[e2e] 判词：%s%s" % (verdict, ("——" + "；".join(why)) if why else ""))
    print("[e2e] 失败归因：%s（主因 %s %.0f%%）→ %s"
          % (dia["counts"], dia["top"], dia["top_share"], dia["advice"]))
    if verdict == "REJECT":
        print("[e2e] 回滚命令：python3 Tools/fleet/lora_switch.sh <上一版 ACTIVE 的 adapter>")
    if a.record_baseline and verdict == "ACCEPT":
        json.dump({"ts": rec["ts"], "coverage": res["coverage"], "median": res["median"],
                   "adapter": act.get("adapter")},
                  open(BASE_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[e2e] 已记为基线 → %s" % os.path.relpath(BASE_F, ROOT))
    return 0 if verdict == "ACCEPT" else 1


def self_test():
    """判词必须能红：造三组样例，ACCEPT / REJECT / 回滚都要能触发。"""
    ok = {"coverage": 41, "median": 82, "n_videos": 43}
    low_cov = {"coverage": 30, "median": 90, "n_videos": 43}
    low_med = {"coverage": 42, "median": 70, "n_videos": 43}
    partial = {"coverage": 43, "median": 95, "n_videos": 20}
    cases = [
        ("达标应 ACCEPT", judge(ok, None)[0] == "ACCEPT"),
        ("覆盖率不足应 REJECT", judge(low_cov, None)[0] == "REJECT"),
        ("中位不足应 REJECT", judge(low_med, None)[0] == "REJECT"),
        ("题集不全应 INCONCLUSIVE", judge(partial, None)[0] == "INCONCLUSIVE"),
        ("低于基线应 REJECT", judge(ok, {"coverage": 42, "median": 80})[0] == "REJECT"),
        ("容差内应 ACCEPT", judge(ok, {"coverage": 41, "median": 83})[0] == "ACCEPT"),
    ]
    # 归因：三条"太长"必须判出主因是太长
    res = {"per_video": [{"ok": False, "fails": ["太长(70>48)"]},
                         {"ok": False, "fails": ["太长(66>48)"]},
                         {"ok": False, "fails": ["品味闸 RISKY(40)"]}]}
    d = diagnose(res)
    cases.append(("归因取最大项", d["top"] == "太长" and d["counts"]["太长"] == 2))
    n_ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        n_ok += 1 if c else 0
    print("[self-test] %d/%d" % (n_ok, len(cases)))
    return 0 if n_ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
