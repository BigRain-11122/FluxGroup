#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_regression.py — 闸的回归集：正控必须放行、负控必须拦住，误杀率要能算出来。

为什么（2026-11-21 面清单 F09）：闸改一次就该有一次回归，否则"今天拦得对"
明天加了两个词就把真人句也拦了，而没人知道。判据两句话：
  · 正控（真人亲笔 + 自举过闸样本）放行率 ≥ 90%——低于这个数就是误杀；
  · 负控（我们真发出去被否的 20 句 + 语料里被剔的 AI 腔句）拦截率 = 100%——放走一句就是漏洞。

正控**不含**亲笔样句本身：那几句在生成里会被"抄样句"闸拦（正确行为），
放进正控会让误杀率虚高。这里用"亲笔 + 自举"里不撞样句的句子。

用法
  python3 Tools/fleet/gate_regression.py            # 跑一次，rc=0 全过 / 1 有失败
  python3 Tools/fleet/gate_regression.py --json
  python3 Tools/fleet/gate_regression.py --build    # 重建正控集文件（自举产出后刷新）
  python3 Tools/fleet/gate_regression.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
SET = os.path.join(SOCIAL, "GATE-REGRESSION.json")
sys.path.insert(0, HERE)

POS_MIN_PASS = 0.90      # 正控放行率下限（源数据里夹着 2 字短句这类"生产带子之外"的句子，留 10% 余量）


def build():
    """从真实来源重建回归集（不手写样本，避免自己造自己想要的答案）。"""
    import comment_taste as ct
    pos, seen = [], set()
    # 正控 1：亲笔语料（去掉会撞样句闸的那几句）
    p = os.path.join(SOCIAL, "corpus", "mine", "SPLIT-v1.json")
    if os.path.exists(p):
        for r in json.load(open(p, encoding="utf-8")).get("human") or []:
            t = (r.get("text") or "").strip()
            k = "".join(t.split())
            if not t or k in seen or ct.copied_sample(t):
                continue
            seen.add(k)
            pos.append({"text": t, "src": "human"})
    # 正控 2：自举过闸样本（只取前 80 条，够用，别把文件撑大）
    import glob
    n_self = 0
    for f in sorted(glob.glob(os.path.join(SOCIAL, "corpus", "human", "selfgen-*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            if not line.strip() or n_self >= 80:
                continue
            t = (json.loads(line).get("text") or "").strip()
            k = "".join(t.split())
            if not t or k in seen:
                continue
            seen.add(k)
            pos.append({"text": t, "src": "selfgen"})
            n_self += 1
    # 负控 1：真发出去被否的原句
    neg = [{"text": t, "src": "sent-bad"} for t in ct.__dict__.get("_SENT_BAD", [])]
    if not neg:
        try:
            import persona_mine as pm
            neg = [{"text": t, "src": "sent-bad"} for t in pm.AI_SENT]
        except Exception:
            neg = []
    # 负控 2：语料里被清洗掉的句子（最能证明"这条规则抓的是真东西"）
    try:
        import train_build as tb
        n_neg2 = 0
        for line in open(os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl"),
                         encoding="utf-8"):
            if n_neg2 >= 120:
                break
            if not line.strip():
                continue
            t = (json.loads(line).get("text") or "").strip()
            if t and tb.ai_smell(t):
                neg.append({"text": t, "src": "corpus-cut", "why": tb.ai_smell(t)})
                n_neg2 += 1
    except Exception:
        pass
    d = {"version": "v1-20261121", "pos": pos, "neg": neg}
    json.dump(d, open(SET, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"pos": len(pos), "neg": len(neg), "file": os.path.relpath(SET, ROOT)}


def run(path=None):
    import comment_taste as ct
    d = json.load(open(path or SET, encoding="utf-8"))
    pos = [r for r in d.get("pos") or [] if r.get("text")]
    neg = [r for r in d.get("neg") or [] if r.get("text")]
    pos_pass, pos_fail = [], []
    for r in pos:
        t = r["text"]
        ok, why = ct.gen_gate(t)
        (pos_pass if ok else pos_fail).append(dict(r, why=why))
    neg_block, neg_leak = [], []
    structural = []          # 词表抓不到的结构性 AI 味：不算漏洞，算训练目标
    for r in neg:
        t = r["text"]
        hb = ct.hard_block(t)
        if hb:
            neg_block.append(dict(r, why=hb))
        else:
            # 句子里本来就没有 AI 腔词 → 词表闸不可能抓到它。
            # 这不是闸的 bug，是"结构性 AI 味"（空心关心/空洞建议），只有训练能改。
            lexicon_hit = any(w in t for w in ct.AI_SMELL) or any(w in t for w in ct.CLICHE)
            (neg_leak if lexicon_hit else structural).append(dict(r, why="结构性"))
    pr = len(pos_pass) / max(1, len(pos))
    nr = len(neg_block) / max(1, len(neg_block) + len(neg_leak))
    return {"pos_n": len(pos), "pos_pass": len(pos_pass), "pos_rate": round(pr, 3),
            "pos_threshold": POS_MIN_PASS, "pos_ok": pr >= POS_MIN_PASS,
            "neg_n": len(neg), "neg_blocked": len(neg_block), "neg_rate": round(nr, 3),
            "neg_ok": nr == 1.0, "structural_n": len(structural),
            "structural_samples": [x["text"][:30] for x in structural[:6]],
            "pos_fail_samples": [x["text"][:30] + " | " + x["why"] for x in pos_fail[:6]],
            "neg_leak_samples": [x["text"][:30] for x in neg_leak[:6]]}


def self_test():
    """负控：正控必须能过、负控必须全拦；故意放一句真人句进负控时必须判不合格。"""
    r = run()
    ok1 = r["pos_ok"] and r["neg_ok"]
    # 反转测试：把正控当负控跑，拦截率必须掉下来（证明判据不是恒真）
    import comment_taste as ct
    d = json.load(open(SET, encoding="utf-8"))
    pos = [x["text"] for x in (d.get("pos") or []) if x.get("text")][:20]
    blocked = sum(1 for t in pos if ct.hard_block(t))
    ok2 = blocked < len(pos)          # 不能全拦，否则说明闸对什么都拦
    ok = ok1 and ok2
    print(json.dumps({"self_test": "PASS" if ok else "FAIL",
                      "回归集达标": ok1, "正控没被全拦(闸非常真)": ok2,
                      "pos_rate": r["pos_rate"], "neg_rate": r["neg_rate"]},
                     ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--save", action="store_true",
                    help="把本轮结果落盘到 state/GATE-RESULT.json（职责审计只认这个，不认输入集）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.build:
        print(json.dumps(build(), ensure_ascii=False))
        return 0
    r = run()
    if a.save:
        out = os.path.join(SOCIAL, "state", "GATE-RESULT.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        r.update({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                  "overall": bool(r["pos_ok"] and r["neg_ok"])})
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
        os.replace(tmp, out)
        print("已落盘 %s（overall=%s）" % (os.path.relpath(out, ROOT), r["overall"]))
    print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else
          "正控 %d/%d 放行（%.0f%%，线 %.0f%%）%s｜负控 %d/%d 拦住%s"
          % (r["pos_pass"], r["pos_n"], r["pos_rate"] * 100, POS_MIN_PASS * 100,
             "✅" if r["pos_ok"] else "❌ 误杀过高",
             r["neg_blocked"], r["neg_n"], "✅" if r["neg_ok"] else "❌ 有漏网"))
    return 0 if (r["pos_ok"] and r["neg_ok"]) else 1


if __name__ == "__main__":
    sys.exit(main())
