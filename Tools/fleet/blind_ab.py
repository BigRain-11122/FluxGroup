#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blind_ab.py — 把基座/LoRA 的对拍结果做成"看不见谁是谁"的盲评表。

为什么必须盲：知道哪条是"我们训的"就会下意识给分，那 10pt 门槛就是自己给自己发的。
所以把 A/B 顺序随机洗过再出表，真值另存 KEY.json，判完再对答案。

用法：
  python3 Tools/fleet/blind_ab.py --ab <AB.jsonl>            # 出 BLIND.md + KEY.json
  python3 Tools/fleet/blind_ab.py --ab <AB.jsonl> --score BLIND.md
       # 判完（在 BLIND.md 的"选"列填 A/B/平）后回填，算 LoRA 对基座的胜率差
"""
import argparse
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def load_ab(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("side") in ("base", "lora"):
            rows.append(r)
    return rows


def build(rows, seed, outdir):
    """按题配对：同一题下基座第 i 条 ↔ LoRA 第 i 条，随机左右。"""
    rnd = random.Random(seed)
    by_prompt = {}
    for r in rows:
        by_prompt.setdefault(r["prompt"], {})[r["side"]] = r["outputs"]
    items, key = [], {}
    n = 0
    for prompt, d in by_prompt.items():
        base, lora = d.get("base") or [], d.get("lora") or []
        for i in range(min(len(base), len(lora))):
            n += 1
            left_is_base = rnd.random() < 0.5
            a, b = (base[i], lora[i]) if left_is_base else (lora[i], base[i])
            items.append({"id": "K%02d" % n, "prompt": prompt, "A": a, "B": b})
            key["K%02d" % n] = {"A": "base" if left_is_base else "lora",
                                "B": "lora" if left_is_base else "base"}
    os.makedirs(outdir, exist_ok=True)
    md = os.path.join(outdir, "BLIND.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# 盲评表（A/B 顺序已随机，真值在 KEY.json）\n\n")
        f.write("判据：哪条更像真人在 B 站评论区随手打的？看措辞/长度/标点，不看对错。\n")
        f.write("填法：在「选」列写 A / B / 平（平=两条都不像或一样像）。\n\n")
        f.write("| 编号 | 题 | A | B | 选 |\n|---|---|---|---|---|\n")
        for it in items:
            f.write("| %s | %s | %s | %s |  |\n" % (
                it["id"], it["prompt"][:26].replace("|", "/"),
                it["A"].replace("|", "/")[:40], it["B"].replace("|", "/")[:40]))
    kp = os.path.join(outdir, "KEY.json")
    json.dump(key, open(kp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[blind] %d 组 → %s（真值 %s）" % (len(items), md, kp))
    print("[blind] 判完跑：python3 Tools/fleet/blind_ab.py --ab <同一文件> --score %s" % md)
    return md, kp


def score(md_path, ab_dir):
    key = json.load(open(os.path.join(ab_dir, "KEY.json"), encoding="utf-8"))
    picks = {}
    for line in open(md_path, encoding="utf-8"):
        if not line.startswith("| K"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        picks[cells[0]] = cells[4].upper()
    if not picks:
        print("[blind] 表里没填（「选」列还是空的）")
        return 2
    win = {"lora": 0, "base": 0, "tie": 0}
    for k, v in picks.items():
        truth = key.get(k)
        if not truth:
            continue
        if v in ("A", "B"):
            win[truth[v]] += 1
        elif v in ("平", "TIE", "="):
            win["tie"] += 1
    decided = win["lora"] + win["base"]
    delta = (100.0 * (win["lora"] - win["base"]) / decided) if decided else 0.0
    print("[blind] LoRA %d · 基座 %d · 平 %d → 差 %+.1fpt（线 ≥10pt）"
          % (win["lora"], win["base"], win["tie"], delta))
    out = os.path.join(ab_dir, "BLIND-SCORE.json")
    payload = {"ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
               "lora_wins": win["lora"], "base_wins": win["base"], "ties": win["tie"],
               "delta_pp": round(delta, 1), "n": len(picks)}
    json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 机读正身：human_corpus.py --gate 读这一份。落点固定按仓根算——
    # 原来靠从 ab_dir 往上退三级，ab_dir 在 tmp 里时会算到 /var/folders/qk/out 并崩。
    canon = os.path.join(ROOT, "cph4", "fleet", "out", "account", "blind.json")
    try:
        os.makedirs(os.path.dirname(canon), exist_ok=True)
        json.dump(payload, open(canon, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[blind] → %s（human_corpus.py --gate 读 %s）" % (out, canon))
    except OSError as e:
        print("[blind] → %s（正身写入失败 %s，本次只是一份局部分数）" % (out, str(e)[:60]))
    return 0


def self_test():
    cases = []
    import tempfile
    tmp = tempfile.mkdtemp(prefix="blind-")
    rows = [{"side": "base", "prompt": "q", "outputs": ["b1", "b2"]},
            {"side": "lora", "prompt": "q", "outputs": ["l1", "l2"]}]
    md, kp = build(rows, 7, tmp)
    key = json.load(open(kp, encoding="utf-8"))
    cases.append(("每组一条真值", len(key) == 2))
    cases.append(("A/B 都标了来源", all(v["A"] != v["B"] for v in key.values())))
    # 盲性：表里不能出现 base/lora 字样
    body = open(md, encoding="utf-8").read()
    cases.append(("表中不泄露来源", "lora" not in body and "base" not in body))
    # 判分闭环：全投 LoRA 应得 +100pt，全投平应得 0
    lines = body.splitlines()
    out = []
    for ln in lines:
        if ln.startswith("| K"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            kid = cells[0]
            pick = "A" if key[kid]["A"] == "lora" else "B"
            cells[4] = pick
            out.append("| " + " | ".join(cells) + " |")
        elif ln.startswith("|"):
            out.append(ln)
    open(md, "w", encoding="utf-8").write("\n".join(out) + "\n")
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        score(md, tmp)
    txt = buf.getvalue()
    cases.append(("全投 LoRA 差 +100.0pt", "+100.0pt" in txt))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--ab", default=None)
    ap.add_argument("--score", default=None, help="判完的 BLIND.md 路径（回填算差）")
    ap.add_argument("--seed", type=int, default=20261117)
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.ab:
        print("[blind] 需要 --ab <AB.jsonl>（或用 --self-test）")
        return 2
    ab_dir = os.path.dirname(os.path.abspath(a.ab))
    if a.score:
        return score(a.score, ab_dir)
    build(load_ab(a.ab), a.seed, ab_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
