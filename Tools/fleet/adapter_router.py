#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adapter_router.py — 按人群段切 LoRA 适配器，用完切回。

问题：五个段件（tech_nerd/peer_pro/music_seeker/craft_learner/memer）都判为有效、
都归档了，但线上一直跑基座——**训出来的权重一次没用过**，这是最大的算力浪费。

为什么必须"切"而不是"并发挂"：8788 一次只加载一个适配器；再开一个进程就是
再吃 2.9GB，而本机 GPU 只有一个（2026-11-20 实测：训练中生成从 25.7 掉到 2.1 tok/s）。
所以正确形态是**按需切换**：写一条评论前切到该段的件，写完切回基座。

代价：每次切换要重启 8788 并等它就绪（实测约 20–30 秒）。会话里一条评论本来就要
停留 25–110 秒，切换时间被这段时间吸收，不额外占用算力。

用法：
  python3 Tools/fleet/adapter_router.py --list
  python3 Tools/fleet/adapter_router.py --ensure peer_pro
  python3 Tools/fleet/adapter_router.py --restore
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TRAIN = os.path.join(ROOT, "cph4", "fleet", "social", "train")
LEDGER = os.path.join(TRAIN, "TRAIN-LOOP-LEDGER.jsonl")
ACTIVE = os.path.join(TRAIN, "ACTIVE.json")
SWITCH = os.path.join(HERE, "lora_switch.sh")
STATE = os.path.join(ROOT, ".codely-cli", "state")
LOG = os.path.join(STATE, "adapter-router.jsonl")


MIN_DEPLOY_N = 30       # 上线门槛：判决样本量低于这个数，一律不采（宁可用基座）


def pick_best(rows, exists=None):
    """从台账行里挑每段最优件：**按增益取最大，不是取最后一次 KEEP**。

    2026-11-20 实锚：peer_pro 先后两件都判 KEEP（87.3 与 73.6），
    旧的"后写覆盖"会让差件静默顶掉好件——重训一次就等于降级，且不报错。
    n<10 的结论是抽样运气（见 topics/training-verdict-noise-and-power.md），一律不收。
    """
    exists = exists or (lambda p: os.path.exists(p))
    best = {}
    # 高功率的否必须能推翻低功率的"留"：2026-11-20 实测 craft_learner 的 n=10 KEEP
    # 在 n=30 重验下是 -3.2 分。只看 KEEP，那条已被推翻的件会永远当最优。
    rejected = {}
    for r in rows:
        if r.get("verdict") == "REJECT" and r.get("adapter"):
            rejected[r["adapter"]] = max(rejected.get(r["adapter"], 0),
                                         int(r.get("eval_n") or 0))
    for r in rows:
        if r.get("verdict") != "KEEP" or not r.get("adapter"):
            continue
        n = int(r.get("eval_n") or 0)
        # 2026-11-27：门槛 10 → 30。实锚：shallow 今天全被否、只能退回 11-21 那个
        # "n=10、+21.1 分"的旧件上线；而同一段 memer 的 n=10 KEEP(+9.7) 在 n=30 下是 -4.4。
        # n<30 的判决是抽样运气，不许拿它决定线上挂哪个模型——宁可挂基座。
        if n < MIN_DEPLOY_N:
            continue
        if rejected.get(r["adapter"], 0) >= n:
            continue
        if not exists(os.path.join(ROOT, r["adapter"], "adapters.safetensors")):
            continue
        gain = round(float(r.get("lora_avg") or 0) - float(r.get("base_avg") or 0), 1)
        cur = best.get(r["seg"])
        if cur is None or gain > cur["gain"] or (gain == cur["gain"] and n > cur["n"]):
            best[r["seg"]] = {"adapter": r["adapter"], "gain": gain, "n": n}
    return best


def best_adapters():
    """每个段当前最优的适配器（判据见 pick_best）。"""
    rows = []
    try:
        for line in open(LEDGER, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return pick_best(rows)


def current():
    try:
        d = json.load(open(ACTIVE, encoding="utf-8"))
    except Exception:
        d = {}
    return d.get("adapter") if d.get("mode") != "base" else None


def _switch(target, why, timeout=180):
    t0 = time.time()
    p = subprocess.run(["/bin/bash", SWITCH, target, why], cwd=ROOT,
                       capture_output=True, text=True, timeout=timeout)
    secs = round(time.time() - t0, 1)
    ok = p.returncode == 0
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "target": target,
           "ok": ok, "secs": secs, "why": why,
           "tail": ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-1][:120]
           if ((p.stdout or "") + (p.stderr or "")).strip() else ""}
    os.makedirs(STATE, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return ok, secs, rec["tail"]


def ensure(seg, timeout=180):
    """切到该段最优件。返回 (是否已就位, 说明, 切换耗时秒)。"""
    allb = best_adapters()
    best = allb.get(seg)
    if not best and allb.get("__all__"):
        # 该段没练出专属件：退到全量件（比基座强，且是同一套语料风格）
        best = dict(allb["__all__"], fallback=True)
    if not best:
        return False, "该段没有可用件（用基座）", 0.0
    if current() == best["adapter"]:
        return True, "已在位", 0.0
    ok, secs, tail = _switch(best["adapter"],
                             "段 %s 出稿：%+0.1f 分（n=%s）%s" % (
                                 seg, best["gain"], best["n"],
                                 "·全量件兜底" if best.get("fallback") else ""),
                             timeout=timeout)
    return ok, ("%s（%s）" % (tail, best["adapter"]) if ok else "切换失败：" + tail), secs


def restore(timeout=180):
    """切回基座：别把段件留在线上影响别的消费者。"""
    if current() is None:
        return True, "已是基座", 0.0
    ok, secs, tail = _switch("base", "出稿完成，切回基座", timeout=timeout)
    return ok, tail, secs


def heal_stale(max_age_min=10):
    """兜底：切换后进程被杀，段件会留在线上影响所有消费者。

    判据：日志里最后一次动作是"切到段件"、且超过 max_age_min 没有切回 → 主动切回基座。
    只在 practice_tick 这类高频进程里调用，所以最多十分钟就会自我恢复。
    """
    cur = current()
    if not cur:
        return False, "已是基座"
    try:
        lines = [json.loads(x) for x in open(LOG, encoding="utf-8") if x.strip()]
    except Exception:
        lines = []
    if not lines:
        return False, "无切换记录"
    last = lines[-1]
    if last.get("target") == "base":
        return False, "最后一步已是切回"
    try:
        ts = time.mktime(time.strptime(last["ts"], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return False, "时间读不出"
    if time.time() - ts < max_age_min * 60:
        return False, "切换不到 %d 分钟，可能仍在用" % max_age_min
    ok, note, secs = _switch("base", "兜底切回：段件留在线上超过 %d 分钟" % max_age_min)
    return ok, note


def self_test():
    cases = []
    b = best_adapters()
    cases.append(("能从台账读出至少一个段件", isinstance(b, dict) and len(b) >= 1))
    cases.append(("读出的件文件真实存在",
                  all(os.path.exists(os.path.join(ROOT, v["adapter"], "adapters.safetensors"))
                      for v in b.values()) if b else False))
    cases.append(("增益字段是数字", all(isinstance(v["gain"], float) for v in b.values()) if b else False))

    # 负控：合成的台账行，不碰真实文件与真实台账
    fake = [
        {"seg": "X", "verdict": "KEEP", "adapter": "a", "lora_avg": 87.3, "base_avg": 47.6, "eval_n": 30},
        {"seg": "X", "verdict": "KEEP", "adapter": "b", "lora_avg": 73.6, "base_avg": 53.0, "eval_n": 30},
        {"seg": "Y", "verdict": "KEEP", "adapter": "c", "lora_avg": 99.0, "base_avg": 10.0, "eval_n": 10},
        {"seg": "Z", "verdict": "REJECT", "adapter": "d", "lora_avg": 99.0, "base_avg": 10.0, "eval_n": 20},
    ]
    picked = pick_best(fake, exists=lambda p: True)
    cases.append(("后写的差件不能顶掉好件（应取 +39.7 的 a）",
                  (picked.get("X") or {}).get("adapter") == "a"))
    cases.append(("n<30 的 KEEP 一律不采（10 也不行）", "Y" not in picked))
    cases.append(("REJECT 不采", "Z" not in picked))

    # 负控：同件先 n=10 KEEP、后 n=30 REJECT —— 必须被推翻，不许继续当最优
    fake2 = [
        {"seg": "W", "verdict": "KEEP", "adapter": "k", "lora_avg": 70.0, "base_avg": 50.0, "eval_n": 30},
        {"seg": "W", "verdict": "REJECT", "adapter": "k", "lora_avg": 46.8, "base_avg": 50.0, "eval_n": 30},
    ]
    picked2 = pick_best(fake2, exists=lambda p: True)
    cases.append(("高功率 REJECT 推翻低功率 KEEP", "W" not in picked2))
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--ensure", default=None)
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.list:
        print(json.dumps(best_adapters(), ensure_ascii=False, indent=1))
        print("当前线上:", current() or "base")
        return 0
    if a.ensure:
        ok, note, secs = ensure(a.ensure)
        print("[router] %s → %s%s" % (a.ensure, "就位" if ok else "未就位", note))
        return 0 if ok else 1
    if a.restore:
        ok, note, secs = restore()
        print("[router] 切回基座 %s（%s）" % ("完成" if ok else "失败", note))
        return 0 if ok else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
