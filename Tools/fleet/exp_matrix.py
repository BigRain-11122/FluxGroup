#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""exp_matrix.py - 无人值守训练的实验矩阵：每次只换一个变量，跑过的不许再跑。

为什么要有它（2026-11-26 排的盘）：
停止"同一批数据+同一个配置反复训"之后，会出现一个新问题——语料不变时 GPU 就没活干。
两种做法都错：
  · 硬训 → 产出同款权重（实锚：music_seeker built 305 三次 KEEP、adapter SHA 完全相同）；
  · 干等 → 违背 CEO「不许摸鱼、利用好算力」。
正解是把"没新语料时干什么"变成**合法对照实验**：每次只动一个变量（步数/层数/评估步距/
序列长度），每个配置只跑一次，跑完入台账。这样每一次 GPU 时间都对应一个**尚不知道答案**
的问题，而不是重复已知结果。

唯一性判据 key = (段, 数据集指纹, 变体 id)。数据集变了就重新开放一轮——
因为同一组配置换一批语料，本来就是新的一课。

不做的事：不决定"哪一段先训"（那是 train_forever 的 pick），不判 KEEP/REJECT。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 基线（train_forever 现行默认）。变体一律相对基线**只改一个键**，自检守这条。
BASE = {"iters": 400, "num_layers": 16, "steps_per_eval": 50,
        "max_seq_length": None, "learning_rate": None, "batch_size": None}

VARIANTS = [
    {"id": "v0-base", "overrides": {},
     "why": "基线：验证当前配方在这批数据上的基准表现"},
    {"id": "v1-iters450", "overrides": {"iters": 450},
     "why": "多训 50 步：看是否还在涨（判断有没有欠训）"},
    {"id": "v2-layers8", "overrides": {"num_layers": 8},
     "why": "只训 8 层：降容量看是否过拟合（少层常常更稳）"},
    {"id": "v3-seval25", "overrides": {"steps_per_eval": 25},
     "why": "评估步距减半：让『最低 val 那一步』选得更准"},
    # 2026-11-27 扩容：CPU/GPU 有空就多问几个"还不知道答案"的问题，
    # 而不是把同一批数据跑完 4 轮就停。新增两个都只动一个变量。
    {"id": "v4-lr5e6", "overrides": {"learning_rate": 5e-6},
     "why": "学习率减半：看之前的负分是不是过冲（过拟合常见成因）"},
    {"id": "v5-iters300", "overrides": {"iters": 300},
     "why": "少训 100 步：判断 400 步是否已经训过头（对照 v1 的 +50 步）"},
]

MAX_VARIANTS = 6          # 一批数据最多跑几个变体，防止无限烧


def variant_map():
    return {v["id"]: v for v in VARIANTS}


def effective(vid):
    """变体 → 真正的训练参数（基线 + 覆盖）。未知变体返回 None，不许凭空生成。"""
    v = variant_map().get(vid)
    if not v:
        return None
    out = dict(BASE)
    out.update(v.get("overrides") or {})
    out["variant"] = vid
    out["why"] = v.get("why")
    return out


def key(seg, fp, vid):
    return "%s|%s|%s" % (seg, fp or "-", vid)


def done_keys(ledger_rows):
    """台账里已经跑过的 (段|数据集指纹|变体)。缺 fp 的老记录不算——
    它们无法证明"这批数据跑过这个配置"，宁可重跑一次也不许把未知当已知。"""
    out = set()
    for r in ledger_rows:
        seg, fp, vid = r.get("seg"), r.get("fp"), r.get("variant")
        if seg and fp and vid:
            out.add(key(seg, fp, vid))
    return out


def next_variant(seg, fp, ledger_rows, max_variants=None):
    """该段在这批数据上下一个该跑的变体。全部跑过返回 None（=没有新问题可问）。"""
    cap = MAX_VARIANTS if max_variants is None else int(max_variants)
    done = done_keys(ledger_rows)
    n_run = sum(1 for r in ledger_rows
                if r.get("seg") == seg and r.get("fp") == fp and r.get("variant"))
    pending = [v for v in VARIANTS if key(seg, fp, v["id"]) not in done]
    if not pending:
        return None, "这批数据的变体已全部跑过，等新语料"
    if n_run >= cap:
        return None, "这批数据已跑满 %d 个变体（不许无限烧）" % cap
    return pending[0]["id"], pending[0].get("why") or ""


def report(ledger_rows, segs):
    done = done_keys(ledger_rows)
    lines = []
    for seg in segs:
        row = []
        for v in VARIANTS:
            mark = "x" if any(k.startswith("%s|" % seg) and k.endswith("|" + v["id"])
                              for k in done) else " "
            row.append("%s:%s" % (v["id"], mark))
        lines.append({"seg": seg, "matrix": row})
    return lines


def self_test():
    cases = []
    # 1 一变量原则：除 v0 外，每个变体相对 BASE 只改一个键
    ok_single = True
    for v in VARIANTS[1:]:
        diff = [k for k in set(list(BASE.keys()) + list(v["overrides"].keys()))
                if BASE.get(k) != v["overrides"].get(k, BASE.get(k))]
        if len([k for k in v["overrides"] if BASE.get(k) != v["overrides"][k]]) != 1:
            ok_single = False
    cases.append(("每个变体相对基线只改一个变量", ok_single))
    # 2 未知变体不许凭空生成
    cases.append(("未知变体返回 None", effective("v9-nope") is None))
    # 3 跑过的必须跳过
    rows = [{"seg": "s", "fp": "fp1", "variant": "v0-base"}]
    vid, _ = next_variant("s", "fp1", rows)
    cases.append(("跑过的变体必须跳过", vid != "v0-base" and vid is not None))
    # 4 全跑过返回 None（不许硬造新问题）
    rows_all = [{"seg": "s", "fp": "fp1", "variant": v["id"]} for v in VARIANTS]
    vid2, why2 = next_variant("s", "fp1", rows_all)
    cases.append(("全部跑过 → 不给活干", vid2 is None and "等新语料" in why2))
    # 5 数据集变了要重新开放
    vid3, _ = next_variant("s", "fp2", rows_all)
    cases.append(("数据集指纹变了 → 重新开放变体", vid3 == "v0-base"))
    # 6 跑满上限即收手（防无限烧）。用 max_variants=2 才能在"还有待跑变体"时触发上限，
    #   否则 4 个变体恰好等于上限，"全跑过"这条先命中——那样上限就永远测不到。
    rows_cap = [{"seg": "s", "fp": "fp1", "variant": "v0-base"},
                {"seg": "s", "fp": "fp1", "variant": "v1-iters450"}]
    vid4, why4 = next_variant("s", "fp1", rows_cap, max_variants=2)
    cases.append(("跑满上限即收手（防无限烧）", vid4 is None and "跑满" in why4))
    # 7 老记录缺 fp 不算已跑（不拿未知当已知）
    rows_old = [{"seg": "s", "variant": "v0-base"}]
    vid5, _ = next_variant("s", "fp9", rows_old)
    cases.append(("缺指纹的老记录不算已跑", vid5 == "v0-base"))
    # 8 effective 必须带上基线值
    e = effective("v1-iters450")
    cases.append(("effective 合并基线（没覆盖的键保留默认）",
                  e and e["iters"] == 450 and e["num_layers"] == 16))
    ok = sum(1 for _, v in cases if v)
    for name, v in cases:
        print("  [%s] %s" % ("PASS" if v else "FAIL", name))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger")
    ap.add_argument("--segs", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    rows = []
    if a.ledger and os.path.exists(a.ledger):
        for ln in open(a.ledger, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if ln:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    continue
    segs = [s for s in (a.segs or "").split(",") if s] or \
        sorted({r.get("seg") for r in rows if r.get("seg")})
    print("变体矩阵（x=已在这批数据上跑过；空=还没问过）：")
    for r in report(rows, segs):
        print("  %-14s %s" % (r["seg"], "  ".join(r["matrix"])))
    print("\n变体说明：")
    for v in VARIANTS:
        print("  %-12s %s" % (v["id"], v["why"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
