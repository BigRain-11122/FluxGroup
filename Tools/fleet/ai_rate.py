#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai_rate.py — 量"模型自己有多像 AI"，这是训练好不好的唯一硬指标。

为什么要它：闸的通过率是"我们拦掉了多少"，不是"模型写得多好"。
CEO 2026-11-21「你不是只靠拦着，而是从根本上训练好」——所以这里量的是**闸之前**的
原始输出：命中有没有 AI 腔骨架、字数是不是全挤在一个区间、开头是不是都撞在一起。
这三个数字只有训练能改，改阈值改不动。

用法
  # 量基座
  .venv-housing/bin/python Tools/fleet/ai_rate.py --model base --n 30
  # 量某个适配器（会临时挂上去，跑完切回基座）
  .venv-housing/bin/python Tools/fleet/ai_rate.py --model lora --adapter <RUNS/xxx/ckptNNN> --n 30
  python3 Tools/fleet/ai_rate.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
OUTDIR = os.path.join(SOCIAL, "state")
sys.path.insert(0, HERE)


def opening(t):
    return re.sub(r"[^\u4e00-\u9fff]", "", t or "")[:2]


IMG = re.compile(r"\[[^\[\]]{1,10}\]")


def platform_metrics(texts, seg=""):
    """平台人味：表情码使用率、口癖命中率、字长区间，跟真实语料比。

    2026-11-21 实测基线：真实 B 站评论 20% 带表情（memer 72%/shallow 25%/
    music_seeker 9%），我们生成 0%——这一项不改，写出来的永远是"通用中文"。
    """
    try:
        import platform_voice as pv
        d = json.load(open(pv.OUT, encoding="utf-8"))
        ref = (d.get("segments") or {}).get(seg) or d.get("global") or {}
    except Exception:
        ref = {}
    n = len(texts) or 1
    em = sum(1 for t in texts if IMG.search(t)) / n
    memes = [g for g, _ in (ref.get("meme_top") or [])[:6]]
    mh = sum(1 for t in texts if any(g in t for g in memes)) / n if memes else 0.0
    return {
        "emoji_rate": round(em, 3),
        "emoji_rate_ref": ref.get("emoji_rate"),
        "emoji_gap": (round(em - float(ref.get("emoji_rate") or 0), 3)
                      if ref.get("emoji_rate") is not None else None),
        "meme_hit_rate": round(mh, 3),
        "len_ref": [ref.get("len_p25"), ref.get("len_p50"), ref.get("len_p75")],
    }


def raw_ai_hits(t):
    """闸之前就能看出来的 AI 痕迹（不看分数，只看"这句话本身像不像我们发的"）。"""
    import comment_taste as ct
    hits = []
    for w in ct.AI_SMELL:
        if w in t:
            hits.append(w)
    for w in ct.CLICHE:
        if w in t:
            hits.append(w)
    return hits


def measure(model="base", adapter=None, n=30, per_title=None, seg=""):
    import llm_client as lc
    import comment_taste as ct
    try:
        tv = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        return {"error": "读不到标题池"}
    items = list(tv.items())
    if not items:
        return {"error": "标题池为空"}

    restore = None
    if adapter:
        import adapter_router as ar
        ok, secs, tail = ar._switch(adapter, "度量：挂件判 AI 率")
        if not ok:
            return {"error": "挂适配器失败：%s" % tail}
        restore = ar

    texts, errs = [], 0
    t0 = time.time()
    i = 0
    while len(texts) < n and i < n * 3:
        url, meta = items[i % len(items)]
        title = (meta or {}).get("title") or ""
        p = lc.lora_comment_prompt(title, (meta or {}).get("desc") or "", i=i, seg=seg or None)
        tgt = lc.human_len_target(i) or 15
        p += "只写 %d-%d 字，一句话。" % (max(4, tgt - 2), min(30, tgt + 3))
        r = lc.generate_lora(p, max_tokens=52, temperature=0.85)
        t = (r.get("text") or "").strip() if isinstance(r, dict) else str(r or "")
        if not t:
            errs += 1
        else:
            texts.append(t)
        i += 1
    try:
        if restore:
            restore.restore()
    except Exception:
        pass

    if not texts:
        return {"error": "一条都没生成", "errors": errs}

    hit_rows = [t for t in texts if raw_ai_hits(t)]
    hit_words = Counter(w for t in texts for w in raw_ai_hits(t))
    lens = [len(t) for t in texts]
    opens = Counter(opening(t) for t in texts)
    gate_pass = sum(1 for t in texts if not ct.hard_block(t) and ct.score(t)["verdict"] == "PASS")
    # 原始缺陷率：不只看"像不像 AI"，还看"有没有硬伤"。
    # 2026-11-21 实锚：shallow 旧件吐出 `_formats_`（模板占位符），词表一个都没命中，
    # 只数 AI 腔会把这句算成"干净"——缺陷必须和腔调分开计。
    defs = [(t, ct.hard_block(t)) for t in texts]
    defs = [(t, w) for t, w in defs if w]
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": model, "adapter": adapter or "", "seg": seg,
        "n": len(texts), "call_errors": errs, "seconds": round(time.time() - t0, 1),
        "ai_hit_rate": round(len(hit_rows) / len(texts), 3),
        "ai_hit_words": hit_words.most_common(8),
        "defect_rate": round(len(defs) / len(texts), 3),
        "defect_words": Counter(w for _, w in defs).most_common(6),
        "len_min": min(lens), "len_p50": sorted(lens)[len(lens) // 2], "len_max": max(lens),
        "distinct_lens": len(set(lens)),
        "opening_top": opens.most_common(3),
        "opening_max_share": round(opens.most_common(1)[0][1] / len(texts), 3),
        "gate_pass_rate": round(gate_pass / len(texts), 3),
        **platform_metrics(texts, seg),
        "samples": texts,
    }


def rescore(path):
    """对已存的样本重算指标（不重新生成、不占 GPU）。

    为什么要有这个：判据会变（今天加了缺陷率、内容度），但不能每次都重跑 30 条生成——
    已存样本是最便宜的复算面。这也逼着我们把 samples 全存下来而不是只留 20 条。
    """
    import comment_taste as ct
    d = json.load(open(path, encoding="utf-8"))
    texts = d.get("samples") or []
    if not texts:
        return {"error": "该文件没存样本"}
    lens = [len(t) for t in texts]
    opens = Counter(opening(t) for t in texts)
    hit = sum(1 for t in texts if raw_ai_hits(t))
    defs = [ct.hard_block(t) for t in texts]
    defs = [w for w in defs if w]
    sc = [ct.score(t) for t in texts]
    n = len(texts)
    out = dict(d)
    out.update({
        "ai_hit_rate": round(hit / n, 3),
        "defect_rate": round(len(defs) / n, 3),
        "defect_words": Counter(defs).most_common(6),
        "avg_logic": round(sum(s.get("logic") or 0 for s in sc) / n, 1),
        "avg_human": round(sum(s.get("human") or 0 for s in sc) / n, 1),
        "avg_voice": round(sum(s.get("voice") or 0 for s in sc) / n, 1),
        "avg_total": round(sum(s.get("total") or 0 for s in sc) / n, 1),
        "gate_pass_rate": round(sum(1 for s in sc if s["verdict"] == "PASS") / n, 3),
        "distinct_lens": len(set(lens)),
        "opening_max_share": round(opens.most_common(1)[0][1] / n, 3),
        "rescored_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        **platform_metrics(texts, d.get("seg") or ""),
    })
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def self_test():
    """负控：AI 原句必须被算成命中，真人句必须 0 命中。"""
    bad = raw_ai_hits("教程太干货了，必须三连支持！")
    bad2 = raw_ai_hits("那个转场绝了")
    good = raw_ai_hits("后面那次副歌进来我起鸡皮疙瘩")
    ok = bool(bad) and bool(bad2) and not good and opening("「镜头」很稳") == "镜头"
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "bad": bad, "good": good},
                     ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="base", choices=["base", "lora"])
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seg", default="")
    ap.add_argument("--json-out", default="")
    ap.add_argument("--rescore", default="", help="对已存样本重算指标（不重新生成）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.rescore:
        r = rescore(a.rescore)
        print(json.dumps({k: r.get(k) for k in ("ai_hit_rate", "defect_rate", "avg_logic",
                                                "avg_human", "avg_voice", "avg_total",
                                                "gate_pass_rate", "distinct_lens",
                                                "opening_max_share")}, ensure_ascii=False, indent=1))
        return 0
    res = measure(a.model, a.adapter if a.model == "lora" else None, a.n, seg=a.seg)
    if a.json_out:
        os.makedirs(OUTDIR, exist_ok=True)
        json.dump(res, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
