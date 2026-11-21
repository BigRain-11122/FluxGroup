#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfgen.py — 自举造集：让模型自己写一批，只把**过得了闸**的那些留下当训练数据。

为什么这样做（CEO 2026-11-21「你不是只靠拦着，而是从根本上训练好」）：
  闸只能一条条拒，模型的先验不会因此改变。反过来，把模型已经写对的句子捡出来
  继续训练它（rejection sampling / STaR 那一套），等于用同一把尺子做数据增广，
  模型的先验才会往"能过闸的那一支"移动。mlx_lm 没有 DPO，这就是本地可行的根治法。

三条硬规矩，防止"自己教自己越教越歪"：
  1 只收 PASS：硬拒为空 + 品味分过线 + 字数在带内 + 不抄样句，一条都不放宽；
  2 角度轮换：每条候选换一个说话角度（画面/感受/挑刺/短评/回忆/细节/接话/带表情），
     否则 8 条全是同一个开头，等于把模板教得更牢；
  3 开头配额：同一开头（前两字）不超过总产出的 3%，撞了就丢——这条比"多要几条"重要。

用法：
  .venv-housing/bin/python Tools/fleet/selfgen.py --titles 43 --per 8 --seg craft_learner
  .venv-housing/bin/python Tools/fleet/selfgen.py --dry --limit 3     # 只看不写
  python3 Tools/fleet/selfgen.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
OUTDIR = os.path.join(SOCIAL, "corpus", "human")
sys.path.insert(0, HERE)

LO, HI = 10, 20          # 生产字数带（arm A/B/C 都是 10-20，与 practice_tick 一致）


def h_of(t):
    return hashlib.md5((t or "").encode()).hexdigest()[:16]


def opening(t):
    import re
    return re.sub(r"[^\u4e00-\u9fff]", "", t or "")[:2]


def gate(t):
    """一条候选能不能进训练集。返回 ("PASS", "") 或 (原因, 细节)。"""
    import comment_taste as ct
    if not t:
        return "空", ""
    if not (LO <= len(t) <= HI):
        return "字数", str(len(t))
    hb = ct.hard_block(t)
    if hb:
        return "硬拒", hb
    if ct.awkward_particles(t):
        return "语气词错位", ""
    s = ct.score(t)
    if s["verdict"] != "PASS":
        return "品味分", "%s/%s" % (s["verdict"], s["total"])
    return "PASS", ""


def sample_one(title, desc, k, seg, temperature=0.85):
    import llm_client as lc
    p = lc.lora_comment_prompt(title, desc, i=k, seg=seg or None)
    p += "只写 %d-%d 字，一句话。" % (LO, HI)
    r = lc.generate_lora(p, max_tokens=48, temperature=temperature)
    if isinstance(r, dict):
        if not r.get("ok"):
            return "", r.get("why") or "生成失败"
        return (r.get("text") or "").strip(), ""
    return str(r or "").strip(), ""


def run(titles_limit=0, per=8, seg="", dry=False, temperature=0.85, out_name=""):
    # 一块 GPU 一把租约（2026-11-21）：与训练/嵌入互斥，拿不到就让路，不抢。
    try:
        import gpu_lease as _gl
        got, why = _gl.acquire("selfgen", ttl_s=3 * 3600)
    except Exception as _e:
        got, why = True, "租约不可用：%s" % str(_e)[:40]
    if not got:
        return {"skipped": why}
    try:
        return _run(titles_limit, per, seg, dry, temperature, out_name)
    finally:
        try:
            _gl.release("selfgen")
        except Exception:
            pass


def _run(titles_limit=0, per=8, seg="", dry=False, temperature=0.85, out_name=""):
    import segments as sg
    spec = sg.load_spec() if not seg else None
    try:
        tv = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        return {"error": "读不到 %s" % TITLES}
    items = list(tv.items())
    if titles_limit:
        items = items[:titles_limit]

    seen = set()
    avoid = set()
    base = os.path.join(OUTDIR, out_name or ("selfgen-%s.jsonl" % (seg or "all")))
    if os.path.exists(base):
        for line in open(base, encoding="utf-8"):
            if line.strip():
                seen.add(json.loads(line).get("h"))
    # 亲笔样句绝不进自举集：那几句是他本人说的，抄进训练集等于让模型背他的原话
    try:
        few = json.load(open(os.path.join(SOCIAL, "HUMAN-PERSONA-v1.json"),
                             encoding="utf-8")).get("fewshot") or []
        avoid = {"".join(x.split()) for x in few}
    except Exception:
        pass

    stats = Counter()
    kept = []
    cap_hit = set()
    t0 = time.time()
    for url, meta in items:
        title = (meta or {}).get("title") or ""
        desc = (meta or {}).get("desc") or ""
        if not title:
            continue
        for k in range(per):
            t, why = sample_one(title, desc, k, seg, temperature)
            if why:
                stats["调用失败"] += 1
                continue
            verdict, detail = gate(t)
            if verdict != "PASS":
                stats[verdict + ("：" + detail.split("：")[0] if detail else "")] += 1
                continue
            key = "".join(t.split())
            if key in seen or key in avoid:
                stats["重复/抄样句"] += 1
                continue
            if opening(t) in cap_hit:
                stats["开头撞车"] += 1
                continue
            seen.add(key)
            segv = seg or (sg.classify(t, spec)["primary"] if spec else "generic")
            import train_build as tb
            kept.append({"h": h_of(t), "text": t, "src": "selfgen",
                         "license": "自举生成（过当前全部闸）", "use": "train",
                         "kind": tb._kind(t), "seg": segv, "thread": url,
                         "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
            stats["PASS"] += 1
        # 每个标题处理完再定开头配额：同一开头（前两字）不超过 3%，至少留 2 条
        if kept:
            cap = max(2, int(len(kept) * 0.03))
            cnt = Counter(opening(r["text"]) for r in kept)
            cap_hit = {o for o, c in cnt.items() if c >= cap}

    if not dry and kept:
        os.makedirs(OUTDIR, exist_ok=True)
        before = 0
        if os.path.exists(base):
            before = sum(1 for _ in open(base, encoding="utf-8"))
        with open(base, "a", encoding="utf-8") as f:
            for r in kept:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        added = len(kept)
    else:
        base, before, added = base, 0, 0
    return {"titles": len(items), "per": per, "kept": len(kept), "added": added,
            "file": os.path.relpath(base, ROOT), "before": before,
            "seconds": round(time.time() - t0, 1),
            "reasons": stats.most_common(10)}


def self_test():
    """负控：闸必须能拒 AI 腔、放真人句；开头配额函数不能把 2 字当 0 字。"""
    bad = ["教程太干货了，必须三连支持！", "那个转场绝了，氛围感拿捏得死死的",
           "这个电影真的很不错我觉得还行吧"]
    # 用"像人但不在亲笔样句里"的句子：样句本身会被抄样句闸拦，那是正确行为不是误杀。
    # 注意 9 字的真人句会被字数带拒——这正是"带子比真人窄"的实锚，记在报告里。
    good = ["索爱那广告放到现在看还是有点好笑", "后面那次副歌进来我起鸡皮疙瘩"]
    ok_bad = all(gate(t)[0] != "PASS" for t in bad)
    ok_good = all(gate(t)[0] == "PASS" for t in good)
    ok_open = opening("「镜头」很稳") == "镜头" and len(opening("abc")) == 0
    ok = ok_bad and ok_good and ok_open
    print(json.dumps({"self_test": "PASS" if ok else "FAIL",
                      "拒掉坏句": ok_bad, "放行真人句": ok_good, "开头解析": ok_open},
                     ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", type=int, default=0, help="取标题池前 N 条（0=全部）")
    ap.add_argument("--per", type=int, default=8, help="每个标题采几条")
    ap.add_argument("--seg", default="", help="目标人群段；不传=自动分类")
    ap.add_argument("--temperature", type=float, default=0.85)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--out-name", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    print(json.dumps(run(a.titles, a.per, a.seg, a.dry, a.temperature, a.out_name),
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
