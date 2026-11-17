#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_pipe.py — 训练工作流总入口：门槛 → 造集 → 训练 → 按质量选点 → 出盲评表。

为什么要有总入口：这条线现在有 6 个工具（build/lora/eval/sample/blind/gate），
每次手敲一条条命令，就会漏环——今天已经漏过三次（忘了重启常驻进程、忘了补标题、
忘了按质量选点直接用最后一个 checkpoint）。社区口径也是一致的：**先有评测闭环再训**。

每一环都有硬门，任何一门不过就直接停，不许"先训了再说"：
  门1 语料量 + 红线召回（human_corpus --gate rc=0）
  门2 训练集规模 ≥ --min-rows（默认 500；太少训出来只会抄碎片）
  门3 质量选点：最好 checkpoint 必须超过基座，否则不推荐、不出盲评表
用法：
  python3 Tools/fleet/train_pipe.py                     # 全流程
  python3 Tools/fleet/train_pipe.py --build-only        # 只造集（不占内存）
  python3 Tools/fleet/train_pipe.py --iters 300 --danmaku-max 0.1
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TRAIN = os.path.join(ROOT, "cph4", "fleet", "social", "train")
PY = sys.executable


def run(argv, title, capture=False):
    print("\n=== %s ===\n$ %s" % (title, " ".join(argv[1:])), flush=True)
    if capture:
        r = subprocess.run(argv, text=True, capture_output=True)
        sys.stdout.write(r.stdout or "")
        if r.returncode != 0:
            sys.stderr.write(r.stderr or "")
        return r.returncode, (r.stdout or "")
    return subprocess.run(argv).returncode, ""


def gate2_ok(rows, min_rows):
    """门2：训练集规模。太少只会抄碎片——这条判据必须能被单独测。"""
    return rows >= min_rows


def gate3_ok(eval_json):
    """门3：最优 checkpoint 必须超过基座，否则不采用。"""
    if not eval_json:
        return False
    best = eval_json.get("best")
    if not best or best == "base":
        return False
    b = (eval_json.get("results") or eval_json).get(best) or {}
    base = (eval_json.get("results") or eval_json).get("base") or {}
    try:
        return float(b.get("avg", 0)) > float(base.get("avg", 0))
    except Exception:
        return False


def self_test():
    cases = []
    cases.append(("门2：达标放行", gate2_ok(2383, 500)))
    cases.append(("门2：不足拦住", not gate2_ok(120, 500)))
    cases.append(("门3：超过基座放行",
                  gate3_ok({"best": "iter100",
                            "iter100": {"avg": 70}, "base": {"avg": 54}})))
    cases.append(("门3：没超过拦住",
                  not gate3_ok({"best": "iter100",
                                "iter100": {"avg": 50}, "base": {"avg": 54}})))
    cases.append(("门3：选到 base 拦住", not gate3_ok({"best": "base", "base": {"avg": 9}})))
    cases.append(("门3：空结果拦住", not gate3_ok(None)))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def latest_run():
    d = os.path.join(TRAIN, "RUNS")
    if not os.path.isdir(d):
        return None
    runs = sorted(x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x)))
    return runs[-1] if runs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--iters", type=int, default=500)
    ap.add_argument("--num-layers", type=int, default=-1, help="-1=全部层（不留余量）")
    ap.add_argument("--max-seq-length", type=int, default=256)
    ap.add_argument("--danmaku-max", type=float, default=0.1)
    ap.add_argument("--min-rows", type=int, default=500)
    ap.add_argument("--samples", type=int, default=3, help="盲评每题生成几条")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--skip-train", action="store_true", help="复用最近一次 run，只做选点+对拍")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    log = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "steps": []}

    # 门1：开训门槛
    rc, out = run([PY, os.path.join(HERE, "human_corpus.py"), "--gate"], "门1 开训门槛", capture=True)
    log["steps"].append({"step": "gate", "rc": rc})
    if rc != 0:
        print("\n[pipe] 门1 未过：语料量或红线不达标，停止。")
        return 2

    # 造集
    rc, out = run([PY, os.path.join(HERE, "train_build.py"),
                   "--danmaku-max", str(a.danmaku_max)], "造集（品味闸+去重+单源上限）", capture=True)
    log["steps"].append({"step": "build", "rc": rc})
    if rc != 0:
        print("\n[pipe] 造集失败，停止。")
        return 2
    rows = 0
    try:
        rows = json.load(open(os.path.join(TRAIN, "STATS.json"), encoding="utf-8"))["train"]
    except Exception:
        pass
    # 门2：训练集规模
    if not gate2_ok(rows, a.min_rows):
        print("\n[pipe] 门2 未过：训练集 %d 条 < %d。样本太少只会抄碎片，先补语料。" % (rows, a.min_rows))
        return 2
    print("\n[pipe] 门2 通过：训练集 %d 条" % rows)

    if a.build_only:
        print("[pipe] --build-only：停在这里（不占统一内存）")
        return 0

    # 训练
    run_ts = None
    if not a.skip_train:
        rc, _ = run([PY, os.path.join(HERE, "train_lora.py"), "--iters", str(a.iters),
                     "--num-layers", str(a.num_layers),
                     "--max-seq-length", str(a.max_seq_length)], "训练")
        log["steps"].append({"step": "train", "rc": rc})
        if rc != 0:
            print("\n[pipe] 训练失败，停止。")
            return 1
        run_ts = latest_run()
    else:
        run_ts = latest_run()
    if not run_ts:
        print("[pipe] 找不到任何 run 目录")
        return 2

    # 门3：按质量选点
    rc, _ = run([PY, os.path.join(HERE, "train_eval.py"), "--run", run_ts,
                 "--samples", "2"], "门3 按质量选 checkpoint")
    log["steps"].append({"step": "eval", "rc": rc, "run": run_ts})
    ev = os.path.join(TRAIN, "RUNS", run_ts, "EVAL.json")
    best = None
    if os.path.exists(ev):
        e = json.load(open(ev, encoding="utf-8"))
        best = e.get("best")
        print("\n[pipe] %s" % e.get("verdict"))
        if not gate3_ok(e):
            print("[pipe] 门3 未过：没有 checkpoint 超过基座，不出盲评表、不采用。")
            log["verdict"] = "REJECTED_BY_EVAL"
            json.dump(log, open(os.path.join(TRAIN, "RUNS", run_ts, "PIPELINE.json"), "w",
                                encoding="utf-8"), ensure_ascii=False, indent=1)
            return 2

    # 对拍 + 盲评表（用最终权重；选点结论已在 EVAL.json 里）
    adir = os.path.join(TRAIN, "RUNS", run_ts, "adapter")
    rc, _ = run([PY, os.path.join(HERE, "train_sample.py"), "--adapter", adir,
                 "--n", str(a.samples)], "基座 vs LoRA 对拍")
    if rc == 0:
        run([PY, os.path.join(HERE, "blind_ab.py"),
             "--ab", os.path.join(TRAIN, "RUNS", run_ts, "AB.jsonl")], "盲评表")
    log["verdict"] = "PENDING_HUMAN_BLIND"
    json.dump(log, open(os.path.join(TRAIN, "RUNS", run_ts, "PIPELINE.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n[pipe] 全流程完成。待办：人判 %s"
          % os.path.join("cph4/fleet/social/train/RUNS", run_ts, "BLIND.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
