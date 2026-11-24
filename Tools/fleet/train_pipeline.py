#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_pipeline.py — 把"训练完成 → 段评测 → 更新按段车道"接成自动的一拍。

为什么要有它（2026-11-24 实锚）：
训练链其实早就是自动的（`com.fluxgroup.trainloop` 每 300 秒一拍），但**质量评测不在链上**：
最近一次 SEGMENT-EVAL 是 17 小时前的，今天跑完的三轮全靠 val_loss 判定。
而 val_loss 换了数据集就不可比——今天数据集从 2655 条重建到 12876 条，
3.28（旧集 132 条验证）与 3.75（新集 1286 条验证）根本不是一个尺子。
用不可比的数去决定"这轮好不好"，等于自动地做错决定。

本器一拍只做三件事，全部可复算：
  1. 找出"已完成（rc=0）但还没评测过"的 run（台账 NEWS 记已处理，防重复评测）
  2. 对它跑一次段评测（train_eval.py），写进 SEGMENT-EVAL-HISTORY
  3. 用评测事实重算 SEG-POLICY（退步段改走基座），并按退步情况给出建议

用法：
  python3 Tools/fleet/train_pipeline.py --once      # 一拍（launchd 每 15 分钟调）
  python3 Tools/fleet/train_pipeline.py --status
  python3 Tools/fleet/train_pipeline.py --self-test
退出码：0 做了事或无事可做 / 1 有失败（评测失败会记台账，不静默吞掉）
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TRAIN = os.path.join(ROOT, "cph4", "fleet", "social", "train")
RUNS = os.path.join(TRAIN, "RUNS")
SEEN = os.path.join(TRAIN, "PIPELINE-SEEN.json")
LEDGER = os.path.join(TRAIN, "PIPELINE-LEDGER.jsonl")


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _seen():
    try:
        with open(SEEN, encoding="utf-8") as f:
            return set(json.load(f).get("runs") or [])
    except Exception:
        return set()


def _mark_seen(run):
    s = _seen()
    s.add(run)
    os.makedirs(os.path.dirname(SEEN), exist_ok=True)
    with open(SEEN, "w", encoding="utf-8") as f:
        json.dump({"runs": sorted(s)[-200:]}, f, ensure_ascii=False, indent=1)


def _log(rec):
    rec.setdefault("ts", _now())
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def finished_runs():
    """已完成（RUN.json 里 rc==0）的 run，按时间升序。"""
    out = []
    try:
        names = sorted(os.listdir(RUNS))
    except FileNotFoundError:
        return out
    for n in names:
        p = os.path.join(RUNS, n, "RUN.json")
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        if d.get("rc") == 0 and not d.get("plumbing_only"):
            out.append(n)
    return out


def pending(seen=None):
    seen = _seen() if seen is None else seen
    return [r for r in finished_runs() if r not in seen]


def baseline(keep=2):
    """把历史 run 全部标记为已处理，只留最新的 keep 轮待评。

    理由：64 轮历史一次性排队评测要十几个小时，且旧轮的 adapter 早已被覆盖，
    评了也不能用于决策。流水线只该评"从现在起新产生的轮次"。
    """
    runs = finished_runs()
    for r in runs[:-keep] if keep else runs:
        _mark_seen(r)
    print("基线：%d 轮标记已处理，保留最新 %d 轮待评" % (len(runs) - keep, min(keep, len(runs))))
    return 0


VENV = os.path.join(ROOT, ".venv-housing", "bin", "python")


def _py():
    """项目虚拟环境的解释器优先。用系统 python3 会缺依赖，评测直接失败（2026-11-24 实锚）。"""
    return VENV if os.path.exists(VENV) else sys.executable


def best_adapter(run):
    """挑该 run 的适配器：优先 adapter/ 下的聚合文件，否则取最大的 ckpt 编号。"""
    d = os.path.join(RUNS, run, "adapter")
    agg = os.path.join(d, "adapters.safetensors")
    if os.path.exists(agg):
        return d
    cands = []
    try:
        for n in os.listdir(d):
            if n.endswith("_adapters.safetensors"):
                try:
                    cands.append((int(n.split("_")[0]), n))
                except Exception:
                    pass
    except FileNotFoundError:
        return None
    return os.path.join(d, max(cands)[1]) if cands else None


def training_busy():
    """有训练在跑就别评——GPU 抢不过，评测会超时变成假失败。"""
    try:
        out = subprocess.run(["ps", "-ax", "-o", "command"], capture_output=True, text=True, timeout=10)
        return "mlx_lm lora --train" in (out.stdout or "")
    except Exception:
        return False


def evaluate(run, timeout=1800):
    """对某个 run 跑段评测。返回 (ok, 摘要)。"""
    ad = best_adapter(run)
    if not ad:
        return False, "该 run 没有适配器文件"
    cmd = [_py(), "-u", os.path.join(HERE, "train_eval.py"), "--run", run,
           "--adapter", ad, "--per-segment", "--samples", "5"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return False, "评测超时（%ds）" % timeout
    tail = (p.stdout or p.stderr or "").strip().splitlines()[-3:]
    return p.returncode == 0, "\n".join(tail)[-300:]


def refresh_policy():
    """用评测事实重算按段车道策略。"""
    try:
        p = subprocess.run([sys.executable, os.path.join(HERE, "seg_policy.py"), "--write"],
                           capture_output=True, text=True, timeout=120, cwd=ROOT)
        return p.returncode == 0, (p.stdout or "").strip().splitlines()[-1:] or ""
    except Exception as e:
        return False, [str(e)[:80]]


def _lora_present():
    """评测结果里 lora 侧必须有分，否则说明 adapter 没生效——这种"成功"是假绿。"""
    try:
        with open(os.path.join(TRAIN, "SEGMENT-EVAL.json"), encoding="utf-8") as f:
            d = json.load(f)
        return bool(d.get("lora"))
    except Exception:
        return False


def once():
    runs = pending()
    if not runs:
        print("[pipeline] 没有待评测的 run")
        return 0
    if training_busy():
        print("[pipeline] 有训练在跑，评测延后（GPU 抢不过，硬评会假失败）")
        return 0
    run = runs[-1]          # 只评最新一轮，攒着一起评会把 GPU 排队拖长
    print("[pipeline] 评测 run=%s（待评 %d 轮）" % (run, len(runs)))
    ok, tail = evaluate(run)
    if ok and not _lora_present():
        ok, tail = False, "评测只产出基座分（lora 为空），判失败，不标已评"
    _mark_seen(run)
    _log({"run": run, "eval_ok": ok, "tail": tail})
    print("[pipeline] 评测 %s：%s" % ("完成" if ok else "失败", tail.splitlines()[-1] if tail else ""))
    ok2, note = refresh_policy()
    print("[pipeline] 重算按段车道：%s" % ("完成 " + " ".join(note) if ok2 else "失败"))
    return 0 if ok else 1


def status():
    seen = _seen()
    fin = finished_runs()
    pend = [r for r in fin if r not in seen]
    print("已完成 run %d 轮｜已评测 %d 轮｜待评测 %d 轮" % (len(fin), len(seen & set(fin)), len(pend)))
    if pend:
        print("  待评测：" + "、".join(pend[-5:]))
    try:
        with open(os.path.join(TRAIN, "SEGMENT-EVAL.json"), encoding="utf-8") as f:
            ev = json.load(f)
        print("最近一次段评测：%s（adapter=%s）" % (ev.get("ts"), (ev.get("adapter") or "")[-32:]))
    except Exception:
        print("还没有段评测")
    return 0


def self_test():
    """负控：只认 rc=0 且非 plumbing 的 run；已评测的不重复；空目录不崩。"""
    cases = []
    import tempfile
    global RUNS, SEEN
    saved = (RUNS, SEEN)
    with tempfile.TemporaryDirectory() as td:
        RUNS = os.path.join(td, "RUNS")
        SEEN = os.path.join(td, "SEEN.json")
        os.makedirs(os.path.join(RUNS, "a"), exist_ok=True)
        os.makedirs(os.path.join(RUNS, "b"), exist_ok=True)
        os.makedirs(os.path.join(RUNS, "c"), exist_ok=True)
        json.dump({"rc": 0}, open(os.path.join(RUNS, "a", "RUN.json"), "w"))
        json.dump({"rc": 1}, open(os.path.join(RUNS, "b", "RUN.json"), "w"))
        json.dump({"rc": 0, "plumbing_only": True}, open(os.path.join(RUNS, "c", "RUN.json"), "w"))
        cases.append(("只认 rc=0 的 run（rc=1 排除）", finished_runs() == ["a"]))
        cases.append(("plumbing 演练不算真跑", "c" not in finished_runs()))
        cases.append(("没评测过 → 待评", pending(set()) == ["a"]))
        _mark_seen("a")
        cases.append(("评测过 → 不再重复", pending(_seen()) == []))
        # 空目录
        empty = os.path.join(td, "EMPTY")
        os.makedirs(empty, exist_ok=True)
        RUNS = empty
        cases.append(("空目录不崩", finished_runs() == []))
    RUNS, SEEN = saved
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.baseline:
        return baseline()
    if a.status:
        return status()
    return once()


if __name__ == "__main__":
    sys.exit(main())
