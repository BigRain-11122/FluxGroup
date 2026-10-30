#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_ai_business.py - turn bm-m's local model into a business producer.

Why: the control plane was only scheduling; the local model wrote generic summaries
(2026-10-30 review of brain-*.md: stale citations, no usable business content). Business
value needs declared jobs with real sources, a fixed output shape, and a gate that rejects
invented facts - not a daily essay.

Model policy (measured 2026-10-30, LLM-BENCH-20261030.json):
  fast  = qwen3:4b-instruct   3.3GB / 41.6 tok/s  -> judgement, triage, short copy
  deep  = qwen3.5:35b-a3b    22.0GB / 29-40 tok/s -> the deliverable itself
Deep loads on demand (keep_alive 5m) and is unloaded when the batch ends, so a 32GB Mac
never carries 22GB just in case.

Gate (any failure = rejected, no file):
  * every cited filename must literally exist in the excerpt set (anti-hallucination);
  * banned marketing/compliance words must be absent;
  * required section headers must be present;
  * length must be inside bounds.

Usage:
  python3 Tools/fleet/local_ai_business.py --list
  python3 Tools/fleet/local_ai_business.py --job mv-promo --deep
  python3 Tools/fleet/local_ai_business.py --due-only          # called by the pulse
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
END = "http://127.0.0.1:11434/api/generate"
MODELS = {"fast": "qwen3:4b-instruct", "deep": "qwen3.5:35b-a3b"}
BANNED = ["绝对", "顶级", "永久", "稳赚", "包过", "全球最强", "全网第一", "销量第一", "官方认证", "零风险"]

# Each job = a real business deliverable the group currently needs, with its sources.
JOBS = {
    "mv-promo": {
        "line": "bigstream-mv",
        "tier": "deep",
        "sources": [
            "cph4/fleet/mv0001-handover/D1-NARRATIVE-MAP-V5-20261016.md",
            "cph4/fleet/mv0001-handover/canon/V717-RECEIPT-20261027.md",
            "cph4/fleet/mv0001-handover/canon/DIRECTOR-REVIEW-V717-REVISE-20261030.md",
        ],
        "task": ("为《爱在西元前》AI MV 出一份可直接拿去发布的物料包，读者是 B 站/抖音的普通观众。"
                 "必须包含四块：`## 标题`（5 条，每条 <=20 字，不同角度：故事/年代/情绪/悬念/歌名梗）、"
                 "`## 简介`（<=120 字，第一句说清这是什么作品、讲什么故事；**不要提 AI 制作**，"
                 "是否勾选平台 AI 声明由 CEO 发布时决定）、"
                 "`## 标签`（12 个，用空格分隔，不要 #，只用观众真会搜的词：歌手/歌名/题材/情绪/形式，"
                 "不要评论性词汇如「叙事结构」「视觉艺术」）、"
                 "`## 置顶评论`（<=60 字，问观众一个问题以引导评论）。"
                 "只用给定素材里出现的事实（年代、叙事、制作方式）；不确定的不要写。"),
        "must": ["## 标题", "## 简介", "## 标签", "## 置顶评论"],
        "chars": (120, 2200),
    },
    "duanju-ep1": {
        "line": "bigstream-duanju",
        "tier": "deep",
        "sources": ["cph4/fleet/duanju-dept-v1/duanju-001-shimiaorensheng"],
        "task": ("给短剧《十秒人生》EP001 出一份配音执行单：逐段列出「段落 / 情绪 / 语速 / 停顿 / 备注」，"
                 "读者是录音席。只用素材里已有的剧情与角色，不要新造人物或台词。"
                 "末尾用 `## 风险` 列 2 条可能翻车的点（每条一句话）。"),
        "must": ["## 风险"],
        "chars": (200, 2500),
    },
    "mv-publish-checklist": {
        "line": "bigstream-mv",
        "tier": "fast",
        "sources": [
            "cph4/fleet/mv0001-handover/canon/DIRECTOR-REVIEW-V717-REVISE-20261030.md",
            "cph4/fleet/queue-receipts/biz-mv-promo-20261031.md",
        ],
        "task": ("给《爱在西元前》MV 出一份「发布前检查单」，读者是 CEO 本人，他要在 5 分钟内判断能不能发。"
                 "必须包含：`## 能发吗`（一句话结论，只依据素材里已完成的项，未完成的一律不算）、"
                 "`## 机器已过`（逐条列素材里明确通过的判据）、"
                 "`## 还差什么`（逐条列素材里明确未完成/待定的项，每条标注谁负责：导演席/剪辑席/CEO）、"
                 "`## 发布时要做`（平台侧动作，例如声明位勾选这类，由 CEO 决定，不要替他决定）。"
                 "只用给定素材里出现的事实，没写的不要假设已经完成。"),
        "must": ["## 能发吗", "## 机器已过", "## 还差什么", "## 发布时要做"],
        "chars": (150, 2000),
    },
    "car-gaming": {
        "line": "car-gaming",
        "tier": "fast",
        "sources": [
            "cph4/fleet/car-gaming-v1/CAR-GAMING-STRATEGY-20261024.md",
            "cph4/fleet/car-gaming-v1/CAR-GAMING-CHARTER-20261024.md",
        ],
        "task": ("用 3 句话写「吸嘟嘟家庭版」对一家车厂 HMI 负责人的价值主张：第一句是什么场景，"
                 "第二句为什么是我们的机制，第三句能替车厂带来什么可验证的结果。"
                 "再列 3 个对方最可能追问的问题（每行一条）。不要用形容词堆砌。"),
        "must": [],
        "chars": (120, 1200),
    },
}


def _read_text(path, limit):
    full = os.path.join(ROOT, path)
    if os.path.isdir(full):
        parts = []
        for f in sorted(os.listdir(full)):
            if f.endswith(".md") and len(parts) < 3:
                parts.append(_read_text(os.path.join(path, f), limit // 3))
        return "\n".join(parts)
    try:
        with open(full, encoding="utf-8-sig") as f:
            return f.read()[:limit]
    except Exception:
        return ""


def excerpts(job):
    per = 3500 if job["tier"] == "deep" else 2000
    chunks = []
    for s in job["sources"]:
        body = _read_text(s, per)
        if body:
            chunks.append("### %s\n%s" % (s, body))
    return "\n\n".join(chunks)


def call(model, prompt, num_ctx=8192, keep_alive="5m", timeout=900):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "think": False, "keep_alive": keep_alive,
                       "options": {"num_ctx": num_ctx, "temperature": 0.4}}).encode()
    req = urllib.request.Request(END, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    return (d.get("response") or "").strip(), round(time.time() - t0, 1)


def unload(model):
    try:
        body = json.dumps({"model": model, "keep_alive": 0}).encode()
        urllib.request.urlopen(urllib.request.Request(
            END, data=body, headers={"Content-Type": "application/json"}), timeout=30).read()
    except Exception:
        pass


def gate(text, job, ex):
    problems = []
    allowed = set(re.findall(r"[A-Za-z0-9_./-]+\.(?:md|json|py|txt)", ex))
    cited = set(re.findall(r"`?([A-Za-z0-9_./-]+\.(?:md|json|py|txt))`?", text))
    ghost = sorted(c for c in cited
                   if not any(c == a or c in a or a.endswith(c) for a in allowed))
    if ghost:
        problems.append("invented-file:" + ",".join(ghost[:3]))
    hit = [w for w in BANNED if w in text]
    if hit:
        problems.append("banned-word:" + ",".join(hit))
    for h in job["must"]:
        if h not in text:
            problems.append("missing-section:" + h)
    # Soft gate: process/policy names are the easiest thing for a small model to invent.
    # Not a hard reject (the sentence may still be useful) but the CEO must see it flagged.
    invented = [t for t in ("流程", "制度", "规范", "协议", "白皮书") if t in text and t not in ex]
    if invented:
        problems.append("soft-needs-review:" + ",".join(invented))
    lo, hi = job["chars"]
    if not (lo <= len(text) <= hi):
        problems.append("length:%d not in %d-%d" % (len(text), lo, hi))
    return problems


def run(job_id, tier_override=None, dry=False):
    job = JOBS[job_id]
    tier = tier_override or job["tier"]
    if tier == "deep":
        # CEO 2026-10-31: 这台机器只做调度/监督/常驻轻量模型，不干重度生产。
        # A 22GB generation is production, not control. Route it, do not run it.
        row = {"job": job_id, "line": job["line"], "tier": tier, "state": "ROUTED",
               "ts": datetime.now().isoformat(timespec="seconds"),
               "why": "bm-m 只做调度/监督/轻量模型；deep 档交机队（bm-a 夜窗 / bm-d）"}
        route = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "ROUTED-WORK.jsonl")
        os.makedirs(os.path.dirname(route), exist_ok=True)
        with open(route, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return dict(row, problems=[])
    model = MODELS[tier]
    ex = excerpts(job)
    if not ex:
        return {"job": job_id, "state": "NO-SOURCE", "problems": ["no excerpt"]}
    prompt = ("你是 FluxGroup 的本地业务生产席。只依据下面给出的仓库素材写作，"
              "严禁编造素材里没有的数字、人名、文件名、平台规则；素材不足就少写，不要凑。\n"
              "任务：%s\n\n=== 仓库素材 ===\n%s" % (job["task"], ex))
    if dry:
        return {"job": job_id, "tier": tier, "model": model, "prompt_chars": len(prompt)}
    text, sec = call(model, prompt)
    problems = gate(text, job, ex)
    hard = [p for p in problems if not p.startswith("soft-")]
    soft = [p for p in problems if p.startswith("soft-")]
    out = {"job": job_id, "line": job["line"], "tier": tier, "model": model,
           "sec": sec, "chars": len(text), "problems": problems}
    if hard:
        out["state"] = "REJECTED"
        return out
    if soft:
        text += "\n\n> ⚠️ 需人工复核：文中出现素材未给出的流程/制度词（%s），不要直接当结论用。\n" \
                % "、".join(p.split(":")[1] for p in soft)
    day = datetime.now().strftime("%Y%m%d")
    base = os.path.join(OUT_DIR, "biz-%s-%s" % (job_id, day))
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(text + "\n\n---\n*本地业务生产席 bm-m · %s · %ss · 依据仓库素材，非云端*\n"
                % (model, sec))
    out.update(state="DONE", path=base + ".md")
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(dict(out, ts=datetime.now().isoformat(timespec="seconds"),
                       sources=job["sources"]), f, ensure_ascii=False, indent=1)
    return out


def due(job_id):
    day = datetime.now().strftime("%Y%m%d")
    p = os.path.join(OUT_DIR, "biz-%s-%s.json" % (job_id, day))
    if not os.path.exists(p):
        return True
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("state") != "DONE"
    except Exception:
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--job")
    ap.add_argument("--tier", choices=["fast", "deep"])
    ap.add_argument("--due-only", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    if a.list:
        for k, v in JOBS.items():
            print("%-12s tier=%-4s line=%-16s sources=%d" % (k, v["tier"], v["line"], len(v["sources"])))
        return 0

    jobs = [a.job] if a.job else list(JOBS)
    if a.due_only:
        jobs = [j for j in jobs if due(j)]
    if not jobs:
        print("[biz] nothing due")
        return 0

    deep_used = False
    rc = 0
    for j in jobs:
        r = run(j, a.tier, a.dry)
        deep_used = deep_used or (r.get("tier") == "deep" and not a.dry)
        print("[biz] %-12s %-8s %-18s %ss %s" % (
            r.get("job"), r.get("state", "PLAN"), r.get("model", ""), r.get("sec", "-"),
            (",".join(r.get("problems") or []) or r.get("path", ""))[:100]))
        if r.get("state") not in ("DONE", "PLAN"):
            rc = 1
    if deep_used:
        unload(MODELS["deep"])   # give the 22GB back the moment the batch is over
    return rc


if __name__ == "__main__":
    sys.exit(main())