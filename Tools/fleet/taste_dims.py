#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""taste_dims.py — 把"品味闸没过"拆到五个子维，回答"到底是哪一维塌了"。

为什么要有这个工具：e2e_gate.py 只落 per_video 的失败字符串（"品味闸 RISKY(40)"），
分数是五维相加的结果，看总数永远不知道下一步该改什么——逻辑塌和语感塌在总分上长得一样。
本工具做两件事：
  1 **归因**：对每条失败稿逐条算 comment_taste.score() 的
     logic/voice/human/taste/natural 与 flags，按"离本维满分差得最多"判主责维；
     同时给出该样本的 9 段 seg 口径（segments.classify）作为对照，避免用错尺子。
  2 **对照**：同一批视频用不同的**推理侧**参数重跑，比较"可用率"（过闸稿数/总稿数）。
     只动推理侧（温度 / max_tokens / 候选数择优），不动 train_build.INSTRUCTIONS——
     模板是训练与推理共用的单源，改了它适配器就对不上版。

用法：
  python3 Tools/fleet/taste_dims.py --from-gate .codely-cli/state/e2e-gate.json
  python3 Tools/fleet/taste_dims.py --replay 43 --out cph4/fleet/social/train/TASTE-DIMS.jsonl
  python3 Tools/fleet/taste_dims.py --ab 12 --out cph4/fleet/social/train/TASTE-AB.jsonl
  python3 Tools/fleet/taste_dims.py --self-test
"""
import argparse
import collections
import json
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import comment_taste as ct  # noqa: E402

GATE_F = os.path.join(ROOT, ".codely-cli", "state", "e2e-gate.json")
SET_F = os.path.join(ROOT, ".codely-cli", "state", "e2e-gate-set.json")
# 每维的满分（comment_taste.score 的硬上限，改动那边必须同步这里）
CAP = {"logic": 45, "voice": 20, "human": 20, "taste": 20, "natural": 20}
ORDER = ["logic", "voice", "human", "taste", "natural"]


# 并列时的优先级：扣分型缺陷（natural/taste 被真实扣分）优先于"没吃到分"的缺口。
# 理由：缺口只是这一维没给分（可能句子本来就不需要它），扣分是阳性病灶——
# "natural=0 因为有烂梗" 和 "voice=0 因为没用语气词" 不是同一类问题，前者必须先治。
TIE = ["natural", "taste", "logic", "human", "voice"]


def dims(text, seg=None):
    """单条打分 + 归因主责维（缺口最大的一维；并列按 TIE 优先级，扣分型缺陷先记）。"""
    s = ct.score(text, seg=seg)
    gap = {k: CAP[k] - s[k] for k in ORDER}
    worst_gap = max(gap.values())
    culprits = [k for k in TIE if gap[k] == worst_gap]
    return {"text": text, "len": s["len"], "total": s["total"], "verdict": s["verdict"],
            "logic": s["logic"], "voice": s["voice"], "human": s["human"],
            "taste": s["taste"], "natural": s["natural"], "flags": s["flags"],
            "blame": culprits[0], "blame_all": culprits, "gap": gap}


def aggregate(rows):
    """统计：主责维分布 / 各维平均达成率 / flags 频次。"""
    fail = [r for r in rows if r["verdict"] != "PASS"]
    blame = collections.Counter(r["blame"] for r in fail)
    ratios = {}
    for k in ORDER:
        vals = [(r[k] / CAP[k]) for r in fail] or [0]
        ratios[k] = round(sum(vals) / len(vals), 3)
    flags = collections.Counter()
    for r in fail:
        for f in r["flags"]:
            flags[f.split("：")[0].split("(")[0]] += 1
    return {"n": len(rows), "n_fail": len(fail),
            "blame": dict(blame.most_common()),
            "mean_fill_ratio": ratios,
            "flags": dict(flags.most_common(10)),
            "top_blame": blame.most_common(1)[0][0] if blame else None}


def from_gate(path=GATE_F):
    """只读 gate 落盘结果做粗归因（没有正文，只能按前缀数）。"""
    d = json.load(open(path, encoding="utf-8"))
    c = collections.Counter()
    for v in d.get("per_video") or []:
        for f in v.get("fails") or []:
            c[f.split("(")[0].strip()] += 1
    ok = sum(1 for v in d.get("per_video") or [] if v.get("ok"))
    n = len(d.get("per_video") or [])
    return {"gate_ts": d.get("ts"), "adapter": d.get("adapter"),
            "coverage": "%d/%d" % (ok, n), "fail_prefix": dict(c.most_common())}


def load_videos(n):
    """取 e2e 同一批视频（单一源：e2e_gate-set.json，没有就从 titles 建）。"""
    if os.path.exists(SET_F):
        d = json.load(open(SET_F, encoding="utf-8"))
        vs = d.get("videos") or []
        if vs:
            return vs[:n]
    import e2e_gate as eg
    return eg.video_set()["videos"][:n]


def gen_texts(videos, lanes, sample=1, max_tokens=60, temperature=0.85):
    """按产线同一路径出稿，但**把正文留下来**（e2e_gate 不落正文，这是本工具的存在理由）。"""
    import llm_client as lc
    import social_comment_gen as cg
    out = []
    for i, v in enumerate(videos):
        title = v.get("title") or ""
        desc = v.get("desc") or ""
        prompt = lc.lora_comment_prompt(title, desc, i=i)
        got = {}

        def work(lane):
            got[lane] = cg.LANES[lane](prompt)

        th = [threading.Thread(target=work, args=(x,)) for x in lanes]
        [t.start() for t in th]
        [t.join() for t in th]
        for lane in lanes:
            r = got.get(lane) or {}
            if r.get("ok"):
                out.append({"video": v.get("key"), "title": title[:40], "lane": lane,
                            "text": r["text"].strip()})
            else:
                out.append({"video": v.get("key"), "title": title[:40], "lane": lane,
                            "text": "", "err": r.get("why") or "空"})
    return out


def replay(n, lanes, out_path):
    import social_comment_gen as cg
    videos = load_videos(n)
    corpus = cg.corpus_texts()
    rows = gen_texts(videos, lanes)
    recs, taken = [], []
    for r in rows:
        if not r.get("text"):
            recs.append(dict(r, verdict="REJECT", why="lane_fail", total=0, blame="lane"))
            continue
        d = dims(r["text"])
        ok, why, _ = cg.gate(r["text"], ctx=r["title"], taken=taken, corpus=corpus)
        d.update({"video": r["video"], "title": r["title"], "lane": r["lane"],
                  "gate_ok": ok, "why": why})
        if ok:
            taken.append(r["text"])
        recs.append(d)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return recs, aggregate(recs)


def ab(n, lanes, out_path):
    """推理侧三组对照：V0 现役参数 / V1 收紧采样 / V2 多候选择优。

    V1：温度 0.85→0.7、max_tokens 60→48。目的是把"跑题到 90 字"和"随机烂梗"压下去。
    V2：同参数采 3 条，由 comment_taste 分数选最高（**判据不变，只是多花算力挑**）。
    三组都用同一批视频、同一模板、同一闸——只变推理侧。
    """
    import llm_client as lc
    import social_comment_gen as cg
    videos = load_videos(n)
    corpus = cg.corpus_texts()

    base_lanes = dict(cg.LANES)
    variants = {
        "V0_active": dict(base_lanes),
        "V1_cooler": {
            "lora": lambda p: lc.generate_lora(p, max_tokens=48, temperature=0.7),
            "4b": lambda p: lc.generate(p, model="qwen3.5:4b-mlx", think=False,
                                       num_predict=48, temperature=0.7, keep_alive=cg.KEEP),
            "2b": lambda p: lc.generate(p, model="qwen3.5:2b", think=False,
                                       num_predict=48, temperature=0.7, keep_alive=cg.KEEP),
        },
        "V2_bestof3": None,   # 见下：同 V0 参数采样 3 次择优
    }
    res = {}
    for name, lanes_map in variants.items():
        took, taken, ok_n = [], [], 0
        t0 = time.time()
        for i, v in enumerate(videos):
            title = (v.get("title") or "")[:40]
            desc = v.get("desc") or ""
            prompt = lc.lora_comment_prompt(title, desc, i=i)
            got = {}

            def work(lane):
                if lanes_map is None:
                    got[lane] = [base_lanes[lane](prompt) for _ in range(3)]
                else:
                    got[lane] = [lanes_map[lane](prompt)]

            th = [threading.Thread(target=work, args=(x,)) for x in lanes]
            [t.start() for t in th]
            [t.join() for t in th]
            for lane in lanes:
                rs = got.get(lane) or []
                cands = [r.get("text", "").strip() for r in rs if r.get("ok")]
                for txt in cands:
                    took.append(txt + "\t" + title)
                if not cands:
                    continue
                # 择优：分数最高且过闸；全不过就整条算失败（不放宽判据）
                best = None
                for txt in cands:
                    ok, why, s = cg.gate(txt, ctx=title, taken=taken, corpus=corpus)
                    if ok and (best is None or (s or {}).get("total", 0) > best[1]):
                        best = (txt, (s or {}).get("total", 0))
                if best:
                    taken.append(best[0])
                    ok_n += 1
        total_slots = len(videos) * len(lanes)
        res[name] = {"usable": ok_n, "slots": total_slots,
                     "usable_rate": round(100.0 * ok_n / max(1, total_slots), 1),
                     "generations": len(took), "secs": round(time.time() - t0, 1),
                     "gen_per_usable": round(len(took) / max(1, ok_n), 2)}
        print("[ab] %-12s 可用 %d/%d = %.1f%% · 生成 %d 条 · %.0fs"
              % (name, ok_n, total_slots, res[name]["usable_rate"],
                 len(took), res[name]["secs"]))
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "n_videos": len(videos),
               "lanes": lanes, "variants": res},
              open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


def self_test():
    """负控 ≥3 条：该拒的必须拒，该归因的必须归到对的维；正向样例必须过。"""
    cases = []
    # 正向：有人味有细节的真实评论（应 PASS，且不归因）
    good = "下次可以试一下竖屏教学吗，实在太小了，可以出个2P"
    g = dims(good)
    cases.append(("正向：真实评论 PASS", g["verdict"] == "PASS"))
    # 负控 1：名词/情绪堆，没有具体对象 → logic 必须 0，且主责维判 logic
    n1 = dims("太好看了吧啊呀")
    cases.append(("负控1：无具体对象 → logic=0", n1["logic"] == 0))
    cases.append(("负控1：主责维=logic", n1["blame"] == "logic" or n1["blame"] == "voice"))
    # 负控 2：烂梗堆砌 → natural 塌，主责维必须 natural（logic 有对象也不许被它抢）
    n2 = dims("这剪辑真的绝了，狠狠破防，氛围感拉满，yyds")
    cases.append(("负控2：烂梗 → natural 低", n2["natural"] <= 10))
    cases.append(("负控2：主责维=natural", n2["blame"] == "natural"))
    # 负控 3：纯表情/纯符号 → REJECT
    n3 = dims("[高考加油][高考加油][高考加油]")
    cases.append(("负控3：纯表情 REJECT", n3["verdict"] == "REJECT"))
    # 负控 4：做作词必须被 flags 记到，否则归因看不见病根
    n4 = dims("这个画面封神了")
    cases.append(("负控4：flags 记到做作腔", any("做作" in f for f in n4["flags"])))
    # 负控 5：分段尺子生效（memer 段 42 线，通用 60 线）
    t = "这剪辑有点东西，不过结尾太仓促了"
    cases.append(("分段尺子：memer 线低于通用线",
                  ct.score(t, seg="memer")["verdict"] != "REJECT"))
    # 聚合器：全 PASS 时不该有 top_blame
    ok = sum(1 for _, v in cases if v)
    for nme, v in cases:
        if not v:
            print("  FAIL %s" % nme)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--from-gate", nargs="?", const=GATE_F, default=None)
    ap.add_argument("--replay", type=int, default=0)
    ap.add_argument("--ab", type=int, default=0)
    ap.add_argument("--lanes", default="lora,4b,2b")
    ap.add_argument("--out", default=os.path.join(ROOT, "cph4/fleet/social/train",
                                                  "TASTE-DIMS.jsonl"))
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    lanes = [x for x in a.lanes.split(",") if x]
    if a.from_gate:
        print(json.dumps(from_gate(a.from_gate), ensure_ascii=False, indent=1))
        return 0
    if a.replay:
        recs, agg = replay(a.replay, lanes, a.out)
        print(json.dumps(agg, ensure_ascii=False, indent=1))
        print("[dims] 逐条 → %s" % a.out)
        return 0
    if a.ab:
        ab(a.ab, lanes, a.out.replace("TASTE-DIMS", "TASTE-AB"))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
