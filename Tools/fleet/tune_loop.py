#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tune_loop.py - 参数调优闭环：单源参数 + 扫参 + 边际判定 + 落账。

CEO 2026-11-18「你要不断调优」。调优不是"我觉得该放宽"，而是三件事：
  1 参数只有一份（TUNE-PARAMS.json），工具都读它，改一处生效
  2 每次只用**已有真实数据**扫参，报出"这个值会让多少条通过、代价是什么"
  3 只有提升超过边际（默认 5%）才改；改了就落账，写清依据与样本量

当前可扫的参数（都能离线算，不占 GPU）：
  maxlen        评论长度上限（social_comment_gen.MAXLEN）
  min_human     训练集入集的人味门槛（train_build --min-human）
  hard_keep     过闸但偏硬的保留率（预留给后续 A/B）

用法：
  python3 Tools/fleet/tune_loop.py --self-test
  python3 Tools/fleet/tune_loop.py --sweep            # 只报不改
  python3 Tools/fleet/tune_loop.py --sweep --apply    # 过边际才写回参数单源
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
PARAMS = os.path.join(SOCIAL, "TUNE-PARAMS.json")
LEDGER = os.path.join(SOCIAL, "TUNE-LEDGER.jsonl")
PASS_F = os.path.join(SOCIAL, "corpus", "human", "QUALITY-PASS.jsonl")
HOT_F = os.path.join(SOCIAL, "corpus", "human", "study_hot.jsonl")
QUEUE = os.path.join(SOCIAL, "comment-queue.jsonl")

sys.path.insert(0, HERE)

DEFAULTS = {
    "maxlen": {"value": 90, "why": "语料 P95=86，取 90", "sweep": [45, 60, 75, 90, 120]},
    "min_human": {"value": 8, "why": "只收有人味的行，实测产出最像人", "sweep": [0, 4, 8]},
}
MARGIN = 0.05          # 提升不到 5% 不动，避免噪声驱动的来回抖
# 只有"提高通过率不伤质量"的参数才允许自动改。
# min_human 不能：把它降到 0，通过率 354→1152（3 倍），但那正是我们判为"没人味"的行——
# 拿通过率当目标就是放水。它必须有下游评测（E2E/评测分）证据才能动。
APPLY_SAFE = {"maxlen"}


def load_params():
    p = {}
    try:
        p = json.load(open(PARAMS, encoding="utf-8"))
    except Exception:
        p = {}
    out = {}
    for k, d in DEFAULTS.items():
        cur = (p.get(k) or {})
        out[k] = {"value": cur.get("value", d["value"]),
                  "why": cur.get("why", d["why"]),
                  "sweep": d["sweep"]}
    out["_updated"] = p.get("_updated", "")
    return out


def save_params(p):
    import datetime
    # 保留本器不管的参数（eval_n / kind_share 由 social_loop 读写）：
    # 整份覆写会把别人的参数抹掉，属"同一事实两处写"的典型事故。
    try:
        keep = json.load(open(PARAMS, encoding="utf-8"))
    except Exception:
        keep = {}
    out = {k: v for k, v in keep.items() if k not in DEFAULTS and not k.startswith("_")}
    out.update({k: {"value": v["value"], "why": v["why"]}
                for k, v in p.items() if not k.startswith("_")})
    out["_updated"] = datetime.datetime.now().isoformat(timespec="seconds")
    json.dump(out, open(PARAMS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def load_jsonl(p, limit=None):
    """均匀取样，不取文件头。

    2026-11-18 实锚：直接取前 1200 行扫 min_human，结果 0 条通过——
    因为高人情味的行分布在文件后段，头部几乎都是低分。取样错位会让结论反过来。
    """
    rows = []
    try:
        for line in open(p, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    except FileNotFoundError:
        return []
    if limit and len(rows) > limit:
        step = len(rows) / float(limit)
        rows = [rows[int(i * step)] for i in range(limit)]
    return rows


def samples(limit=1500):
    """调优样本：真实语料（可信型）+ 高赞评论（共鸣型）+ 现役队列。"""
    rows = []
    for r in load_jsonl(PASS_F, limit):
        rows.append({"text": r.get("text") or "", "src": "own"})
    for r in load_jsonl(HOT_F, limit // 2):
        rows.append({"text": r.get("text") or "", "src": "hot"})
    for r in load_jsonl(QUEUE):
        rows.append({"text": r.get("text") or "", "src": "queue"})
    return [r for r in rows if r["text"]]


def gate_with(rows, maxlen, min_human=None):
    """在给定参数下算通过率。min_human 只作用于训练型语料（own）。"""
    import comment_taste as ct
    ok = 0
    for r in rows:
        t = r["text"]
        if len(t) < 6 or len(t) > maxlen:
            continue
        if r["src"] == "own" and min_human is not None:
            # human_feel 返回 int（不是 dict）。2026-11-18 踩过：写成 ["total"] 会抛
            # TypeError 被 except 吞掉 → 全量 0，还以为"没人味"。
            try:
                if int(ct.human_feel(t)) < min_human:
                    continue
            except Exception:
                continue
        if ct.score(t)["verdict"] == "PASS":
            ok += 1
    return ok


def sweep(rows):
    p = load_params()
    base_len = p["maxlen"]["value"]
    base_h = p["min_human"]["value"]
    base = gate_with(rows, base_len, base_h)
    n = len(rows) or 1
    print("[tune] 样本 %d 条｜当前 maxlen=%d min_human=%d → 通过 %d（%.1f%%）"
          % (n, base_len, base_h, base, 100.0 * base / n))
    print("\n[scan] maxlen（min_human 固定 %d）" % base_h)
    best_len, best_len_v = base_len, base
    for v in p["maxlen"]["sweep"]:
        c = gate_with(rows, v, base_h)
        mark = "←当前" if v == base_len else ""
        print("   maxlen=%-4d 通过 %4d（%.1f%%）%s" % (v, c, 100.0 * c / n, mark))
        if c > best_len_v:
            best_len, best_len_v = v, c
    print("\n[scan] min_human（maxlen 固定 %d，仅可信型语料）" % base_len)
    own = [r for r in rows if r["src"] == "own"]
    no = len(own) or 1
    base_h_v = gate_with(own, base_len, base_h)
    best_h, best_h_v = base_h, base_h_v
    for v in p["min_human"]["sweep"]:
        c = gate_with(own, base_len, v)
        mark = "←当前" if v == base_h else ""
        print("   min_human=%-2d 通过 %4d / %d（%.1f%%）%s" % (v, c, no, 100.0 * c / no, mark))
        if c > best_h_v:
            best_h, best_h_v = v, c

    prop = []
    if base and best_len_v > base * (1 + MARGIN):
        prop.append(("maxlen", best_len,
                     "通过率 %.1f%% → %.1f%%（+%.0f%%）"
                     % (100.0 * base / n, 100.0 * best_len_v / n,
                        100.0 * (best_len_v - base) / max(base, 1))))
    if base_h_v and best_h_v > base_h_v * (1 + MARGIN):
        if "min_human" in APPLY_SAFE:
            prop.append(("min_human", best_h,
                         "可信型通过 %d → %d" % (base_h_v, best_h_v)))
        else:
            print("   ⚠ min_human=%d 能让通过数 %d→%d，但通过率不是质量：需下游评测才可改"
                  % (best_h, base_h_v, best_h_v))
    return prop, {"n": n, "base_pass": base, "base_rate": round(100.0 * base / n, 1),
                  "maxlen_scan": {str(v): gate_with(rows, v, base_h)
                                  for v in p["maxlen"]["sweep"]},
                  "min_human_scan": {str(v): gate_with(own, base_len, v)
                                     for v in p["min_human"]["sweep"]}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=1200)
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.sweep:
        ap.print_help()
        return 0

    rows = samples(a.limit)
    if not rows:
        print("[tune] 没有样本，先跑语料清洗")
        return 2
    prop, stat = sweep(rows)
    import datetime
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
           "stat": stat, "proposals": [{"param": k, "value": v, "why": w} for k, v, w in prop]}
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if not prop:
        print("\n[tune] 无参数越过边际（%.0f%%），保持现状" % (MARGIN * 100))
        return 0
    print("\n[tune] 建议改：")
    for k, v, w in prop:
        print("   %s → %s（%s）" % (k, v, w))
    if a.apply:
        p = load_params()
        for k, v, w in prop:
            p[k]["value"] = v
            p[k]["why"] = w + "（tune_loop 自动）"
        save_params(p)
        print("[tune] 已写回 %s" % os.path.relpath(PARAMS, ROOT))
    else:
        print("[tune] 未改（加 --apply 生效）")
    return 0


def self_test():
    """判据要能红：造两组样例，一组该提 maxlen、一组不该动。"""
    import tempfile
    long_ok = [{"text": "这段剪辑的节奏真的稳，转场也顺手，学到了不少细节，感谢分享经验" * 2,
                "src": "own"} for _ in range(6)]
    short_ok = [{"text": "这段剪辑节奏真稳", "src": "own"} for _ in range(6)]
    # 长句在 maxlen=45 下全被截掉、在 120 下能过 → 应建议提高
    c45 = gate_with(long_ok, 45)
    c120 = gate_with(long_ok, 120)
    cases = [
        ("长句在窄上限下被拦", c45 <= c120),
        ("短句不受上限影响", gate_with(short_ok, 45) == gate_with(short_ok, 120)),
        ("参数单源可读写", isinstance(load_params(), dict)
         and all("value" in v for k, v in load_params().items() if not k.startswith("_"))),
        ("边际阈值存在", 0 < MARGIN < 1),
    ]
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
