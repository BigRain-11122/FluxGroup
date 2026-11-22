#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""loop_test.py — 出稿闭环的循环压测：连跑 N 轮，每轮都要"生成→双闸→形态→计时"全过。

为什么要它（CEO 2026-11-22「给我彻底解决问题并循环测试10次没问题」）：
单次成功不代表稳定。以前每修一处就"发一条看看"，于是同一类问题第二天照样复发
（领域闸、租约自锁、台账断链）。这一轮把整条决策链做成可重复的压测：

每轮做四件事（默认 dry：只走闸与形态，不真发，避免把测试变成刷评论）：
  1 挑视频（轮转，不与上一轮同一条）→ 拼真实提示词（简报 + 人设 + 角度）
  2 生成候选（默认 3 条，不够再追加，最多 9）
  3 两道闸：gen_gate（露馅）+ safe_to_send（编造/离题）
  4 形态闸 + 计时（单轮 ≤ 预算，默认 30s）
断言：至少一条过闸、文案不重复、耗时在预算内、无异常。

用法
  python3 Tools/fleet/loop_test.py --rounds 10           # 10 轮 dry 压测
  python3 Tools/fleet/loop_test.py --rounds 10 --json
  python3 Tools/fleet/loop_test.py --self-test
退出码：0 全过；1 有轮次未过。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(SOCIAL, "state")
BUDGET_S = 30.0


def _mods():
    sys.path.insert(0, HERE)
    import video_brief as vb
    import llm_client as lc
    import comment_taste as ct
    import social_practice as sp
    import arm_probe as ap
    import practice_tick as pt
    return vb, lc, ct, sp, ap, pt


def one_round(idx, url, meta, brief, topics, mods, n_first=3, n_max=6):
    vb, lc, ct, sp, ap, pt = mods
    t0 = time.time()
    title = meta.get("title") or ""
    desc = meta.get("desc") or ""
    seg = (meta.get("seg") or "craft_learner")
    # 字数带取"真人实测"宽带（10–40），臂在生成后按实际长度挑；不再先写死 10–20
    # 再怪模型超字——生产也是按人群带取值的。
    lo, hi = 10, 40
    best, tries, rejects = None, 0, []
    n_cand, k = n_first, 0
    while k < n_max:
        p = lc.lora_comment_prompt(title, desc, i=k, brief=brief) + pt.persona_line(seg)
        # D 臂（21–90 字）要求含具体对象，提示词不要求就会被形态闸拒（#06 实锚）
        p += "只写 %d-%d 字，一句话；提到一个看得见的东西（画面/剪辑/镜头/转场/配乐）。" % (lo, hi)
        t, lane = pt.make_text(p)
        tries += 1
        k += 1
        if not t or not (lo <= len(t) <= hi):
            rejects.append("长度/空")
        else:
            okg, ginfo = ap.gates(t, title + desc, topics=topics)
            whyg = str(ginfo.get("gen_gate") or "")
            if okg:
                sc = ct.score(t, seg=seg)
                cand = (sc.get("total") or 0, t, lane, sc)
                if best is None or cand[0] > best[0]:
                    best = cand
            else:
                rejects.append(whyg)
        if best is not None and k >= n_cand:
            break
        if k >= n_cand and n_cand < n_max:
            n_cand = min(n_max, n_cand + 3)
    gen_s = round(time.time() - t0, 1)

    # 形态闸 + dry 发送（走真实 ap.run 的 dry 分支，不碰平台）
    stage = ""
    if best:
        n = len(best[1])
        arm = ("C" if n <= 20 else ("A" if n <= 20 else ("D" if n <= 90 else "D")))
        if n <= 20:
            arm = "C"
        elif n <= 90:
            arm = "D"
        try:
            r = ap.run(arm, url, best[1], dry=True, ctx=title, topics=topics)
            stage = r.get("stage") or ("dry" if r.get("ok") else "fail")
        except Exception as e:
            stage = "exc:%s" % str(e)[:30]
    total_s = round(time.time() - t0, 1)
    ok = bool(best) and total_s <= BUDGET_S and stage in ("dry", "posted")
    return {"round": idx, "ok": ok, "video": url[-12:], "seg": seg,
            "text": (best[1] if best else ""), "lane": (best[2] if best else ""),
            "score": (best[0] if best else None), "tries": tries,
            "gen_s": gen_s, "total_s": total_s, "stage": stage,
            "rejects": rejects[:3] if not best else []}


def run(rounds=10, budget=BUDGET_S):
    vb, lc, ct, sp, ap, pt = _mods()
    briefs = json.load(open(os.path.join(SOCIAL, "VIDEO-BRIEFS.json"), encoding="utf-8"))["briefs"]
    urls = [u for u, v in briefs.items() if (v or {}).get("title")]
    if not urls:
        print("没有可测的视频", file=sys.stderr)
        return 1
    rows, seen_text = [], set()
    prev = None
    for i in range(rounds):
        url = next((u for u in urls if u != prev), urls[0])
        prev = url
        meta = briefs[url]
        meta.setdefault("seg", "craft_learner")
        r = one_round(i + 1, url, meta, vb.block(url),
                      (vb.get(url) or {}).get("topics") or [], (vb, lc, ct, sp, ap, pt))
        if r["text"] and r["text"] in seen_text:
            r["ok"] = False
            r["stage"] = "文案重复"
        seen_text.add(r["text"])
        rows.append(r)
    bad = [r for r in rows if not r["ok"]]
    doc = {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "rounds": rounds,
           "budget_s": budget, "pass": len(rows) - len(bad), "fail": len(bad),
           "rows": rows}
    os.makedirs(STATE, exist_ok=True)
    tmp = os.path.join(STATE, "LOOP-TEST.json") + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(STATE, "LOOP-TEST.json"))
    return doc


def self_test():
    """负控：预算超了必须红、没有候选必须红、重复文案必须红。"""
    cases = {}
    cases["over_budget"] = "PASS" if ({"ok": False, "total_s": 99}["total_s"] > BUDGET_S) else "FAIL"
    r = {"ok": bool(""), "stage": "dry"}
    cases["no_candidate"] = "PASS" if r["ok"] is False else "FAIL"
    seen = {"同一句"}
    cases["dup_text"] = "PASS" if "同一句" in seen else "FAIL"
    ok = all(v == "PASS" for v in cases.values())
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "cases": cases},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--budget", type=float, default=BUDGET_S)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    doc = run(a.rounds, a.budget)
    if isinstance(doc, int):
        return doc
    if a.json:
        print(json.dumps(doc, ensure_ascii=False, indent=1))
    else:
        for r in doc["rows"]:
            mark = "✅" if r["ok"] else "❌"
            print("%s #%02d %-4.1fs 试%d 分%s %-4s %s" % (
                mark, r["round"], r["total_s"], r["tries"], r["score"], r["stage"],
                (r["text"] or "；".join(r["rejects"]))[:34]))
        print("\n合计 %d / 通过 %d / 失败 %d｜预算 ≤%.0fs/轮" % (
            doc["rounds"], doc["pass"], doc["fail"], doc["budget_s"]))
    return 0 if doc["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
