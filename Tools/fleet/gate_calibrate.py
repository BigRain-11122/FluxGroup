#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""出稿闸标定：用真实评论现场生成，量每个环节的淘汰率和重叠度分布。

为什么要有它（2026-11-26）：
reply-log 里 91% 都是「闸拒或无稿」一句笼统话；拆开之后发现主因是"跑题"
判据用固定阈值 2 个二元组，把短评上的正常改写全杀了。凭感觉调阈值不算证据，
所以这里按真实评论批量生成，逐环节统计：长度 / 闸 / AI 腔 / 编造 / 跑题，
并把"除跑题外全过"的那些回复的共享二元组数打出来——阈值该定多少看这张分布。

用法：
  python3 Tools/fleet/gate_calibrate.py --n 20          # 真实生成并统计
  python3 Tools/fleet/gate_calibrate.py --self-test     # 离线自检（注入生成器）
"""
import argparse
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
sys.path.insert(0, HERE)

CORPUS = os.path.join(SOCIAL, "corpus", "bilibili.jsonl")


def _bg(s):
    s = re.sub(r"[^\u4e00-\u9fff]", "", s or "")
    return {s[i:i + 2] for i in range(max(0, len(s) - 1))}


def _need(n_bg, cap=2):
    """口径：短中评只要有 1 个共享二元组，长评（≥12 个二元组 ≈14 字）要 2 个。

    为什么不是按比例：按 1/4 缩放时，9 字评论（8 个二元组）就要 2 个，
    等于要求 25% 重叠——自然改写做不到。1 个共享二元组是"别自说自话"的地板；
    长评里单个二元组太容易撞（"好听""真的"），所以长评抬到 2。
    """
    return min(int(cap), 2) if n_bg >= 12 else 1


def load_comments(path=CORPUS, n=20, minlen=4, maxlen=40, seed=7):
    """取真实评论：太短的抽不出语义、太长的模板化，两头都裁掉。"""
    pool = []
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            t = (r.get("text") or "").strip()
            if minlen <= len(t) <= maxlen and not re.search(r"https?://", t):
                pool.append(t)
    except FileNotFoundError:
        return []
    random.Random(seed).shuffle(pool)
    out, seen = [], set()
    for t in pool:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= n:
            break
    return out


def calibrate(comments, gen, gate=None, deai=None, fab=None, verbose=True):
    """逐条生成并分环节判定。gen(comment) -> 文本；其余判定器可注入（自检用）。"""
    import reply_tick as rt
    gate = gate or (lambda t: rt.__dict__["_reply_text"].__globals__ and True)
    stat = {"n": 0, "llm_fail": 0, "empty": 0, "len_bad": 0, "gate": 0,
            "deai": 0, "fab": 0, "ontopic": 0, "pass": 0}
    shares = []
    rows = []
    for c in comments:
        stat["n"] += 1
        try:
            t = gen(c)
        except Exception as e:
            stat["llm_fail"] += 1
            rows.append((c, "", "LLM异常 %s" % type(e).__name__, None))
            continue
        t = (t or "").strip().strip("“”\"'").split("\n")[0].strip()
        if not t:
            stat["empty"] += 1
            rows.append((c, "", "空文本", None))
            continue
        if not (8 <= len(t) <= 30):
            stat["len_bad"] += 1
            rows.append((c, t, "长度 %d" % len(t), None))
            continue
        try:
            import social_comment_gen as cg
            ok, why, _ = cg.gate(t, face="reply", taste_gate=False)
        except Exception as e:
            ok, why = False, "gate异常 %s" % type(e).__name__
        if not ok:
            stat["gate"] += 1
            rows.append((c, t, "闸拒：%s" % str(why)[:30], None))
            continue
        try:
            import deai_check as dz
            if dz.check(t)["verdict"] != "clean":
                stat["deai"] += 1
                rows.append((c, t, "AI 腔", None))
                continue
        except Exception:
            pass
        if rt._fabricates(t, c):
            stat["fab"] += 1
            rows.append((c, t, "编造/承诺", None))
            continue
        a, b = _bg(t), _bg(c)
        share = len(a & b)
        need = _need(len(b))
        shares.append((len(b), share, need))
        if share < need:
            stat["ontopic"] += 1
            rows.append((c, t, "跑题（共享 %d / 需 %d）" % (share, need), (len(b), share, need)))
            continue
        stat["pass"] += 1
        rows.append((c, t, "通过（共享 %d / 需 %d）" % (share, need), (len(b), share, need)))
    if verbose:
        for c, t, why, _x in rows:
            print("评论：%s\n回复：%s\n  → %s\n" % (c[:32], (t or "（空）")[:32], why))
        n = max(1, stat["n"])
        print("合计 %d 条：" % stat["n"])
        for k, label in (("pass", "通过"), ("ontopic", "跑题"), ("gate", "闸拒"),
                         ("deai", "AI 腔"), ("fab", "编造"), ("len_bad", "长度不合"),
                         ("empty", "空文本"), ("llm_fail", "模型不可用")):
            print("  %-6s %3d  %5.1f%%" % (label, stat[k], 100.0 * stat[k] / n))
        if shares:
            dist = {}
            for _nb, share, _nd in shares:   # 别用 _need：会遮蔽模块级函数
                dist[share] = dist.get(share, 0) + 1
            print("  走到跑题判定的 %d 条，共享二元组分布：%s" % (len(shares), dict(sorted(dist.items()))))
            print("  建议：共享 0 必拒；共享 1 在短评上应放行（当前 %d 条因此通过）"
                  % sum(1 for _nb, s, _nd2 in shares if s == 1 and _nd2 == 1))
    return stat, shares, rows


def self_test():
    cases = []
    import reply_tick as rt
    cases.append(("短评需 1", _need(len(_bg("这歌真好听"))) == 1))
    cases.append(("中评需 1", _need(len(_bg("这首歌真的挺好听的啊"))) == 1))
    cases.append(("临界（12 个二元组）需 2", _need(12) == 2))
    cases.append(("长评需 2", _need(len(_bg("当年这首确实被严重低估了现在听还是很顶"))) == 2))

    # 负控：模型不可用时必须记成 llm_fail，不许算成"跑题"
    def boom(_c):
        raise RuntimeError("8788 down")
    stat, _s, _r = calibrate(["这歌真好听"] * 3, boom, verbose=False)
    cases.append(("生成失败记 llm_fail", stat["llm_fail"] == 3 and stat["ontopic"] == 0))
    # 负控：空文本必须单独计，不许混进跑题
    stat2, _s2, _r2 = calibrate(["这歌真好听"] * 2, lambda _c: "", verbose=False)
    cases.append(("空文本单独计", stat2["empty"] == 2 and stat2["ontopic"] == 0))
    # 正控：完全无关的回复必须判跑题
    stat3, _s3, _r3 = calibrate(["这歌真好听"], lambda _c: "今天股市又跌了心情很差", verbose=False)
    cases.append(("无关回复判跑题或前序环节拦下",
                  stat3["ontopic"] + stat3["gate"] + stat3["deai"] + stat3["fab"] >= 1))
    ok = 0
    for name, val in cases:
        print("  [%s] %s" % ("PASS" if val else "FAIL", name))
        ok += 1 if val else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    cs = load_comments(n=a.n, seed=a.seed)
    if not cs:
        print("取不到真实评论（%s），换语料或先跑采集" % CORPUS)
        return 3
    import llm_client as lc
    import reply_tick as rt

    def gen(c):
        r = lc.generate_lora(rt._FEW + rt._RULE + "观众：%s\nUP：" % c[:60],
                             max_tokens=48, temperature=0.75)
        if not r.get("ok", True):
            raise RuntimeError(str(r.get("why"))[:60])
        return r.get("text") or ""

    stat, shares, _rows = calibrate(cs, gen)
    return 0 if stat["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
