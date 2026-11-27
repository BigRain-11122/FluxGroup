#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mem_gate.py - what a 32GB unified-memory Mac may actually load, measured not guessed.

Unified memory is one pool: the CEO's apps (Doubao/Feishu/Claude/Safari/Tuanjie) are part of
the same 32GB the model would take. So the budget is not "how big is the model" but
"how much is left after the human".

  available = free + inactive + speculative + purgeable   (macOS reclaimables)
  reserve   = 6GB   (apps + kernel + compressor headroom; swap was already 5GB at 0GB free)
  model_max = clamp(available - reserve, 0, 12GB)

Verdicts:
  OK      model_max >= requested footprint
  DOWNGRADE  fits a smaller tier (4B) but not the requested one
  WAIT    below even the resident tier -> do not load anything now

Usage: python3 Tools/fleet/mem_gate.py [--need-gb 22] [--json]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time

# CEO 2026-11-02: 这台机器主要就是赋能 AI，轻度办公 → 办公预留从 6GB 降到 4GB，
# 单模型上限提到 14GB（仍然受换页规则约束）。
RESERVE_GB = 4.0
CAP_GB = 14.0          # AI-first box: a 9-14B judge seat must be able to fit
RESIDENT_GB = 3.3      # qwen3:4b-instruct @8k, measured
# CEO 2026-11-01: 不要频繁触发硬盘交换，合理使用 MacBook 的算力. Swap already in use means
# the box is under pressure BEFORE the model loads; counting only "free" RAM would invite
# a load that thrashes. Every GB of live swap is subtracted from what a model may claim.
SWAP_SOFT_GB = 1.0     # 仅在没有 paging 基线时作保守参考
SWAP_HARD_GB = 2.0     # 同上；绝对值只是残留量，不是"正在换页"的证据
# 真正的红线=换页速率（页/秒）。实测基线：系统空闲 60 秒 Δswapins=8、Δswapouts=0，
# 即 0.1 页/秒量级；真的在 thrash 时是几百页/秒。取 5 / 50 两档留足余量。
SWAP_RATE_SOFT = 5.0
SWAP_RATE_HARD = 50.0
SWAP_STATE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), ".codely-cli", "state", "mem-swap-state.json")


def available_gb() -> float:
    vm = subprocess.check_output(["vm_stat"], text=True)
    page = 16384
    vals = {}
    for ln in vm.splitlines():
        if "page size of" in ln:
            page = int(ln.split("page size of")[1].split()[0])
        if ":" in ln:
            k, v = ln.split(":", 1)
            try:
                vals[k.strip()] = int(v.strip().rstrip("."))
            except ValueError:
                pass
    return round(sum(vals.get(k, 0) for k in
                     ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable"))
                 * page / 1e9, 1)


def swap_used_gb() -> float:
    out = subprocess.check_output(["sysctl", "-n", "vm.swapusage"], text=True)
    m = re.search(r"used = ([\d.]+)M", out)
    return round(float(m.group(1)) / 1024, 1) if m else -1.0


def _counters():
    """返回 (swap_used_gb, swapouts, swapins)。

    `vm.swapusage` 的 used 是**累计占用**，macOS 不会主动退还给系统——
    所以拿它的绝对值当"正在换页"是错的：机器闲着一整天，这个数也纹丝不动。
    判"有没有在换页"只能看 Swapouts/Swapins 的**增量速率**（2026-11-27 实测：
    2.6GB 残留、60 秒内 Δswapouts=0、Δswapins=8，完全没在换）。
    """
    used = swap_used_gb()
    vs = subprocess.check_output(["vm_stat"], text=True)

    def g(k):
        m = re.search(k + r":\s+(\d+)", vs)
        return int(m.group(1)) if m else 0
    return used, g("Swapouts"), g("Swapins")


def swap_rate(state_path=None, min_window_s=15):
    """paging 速率（页/秒）。返回 (rate, delta_used_gb, window_s)；无基线时 rate=None。

    速率才是 CEO 那条红线的正身："跑活期间不许涨"。残留多少不重要，
    重要的是这一段时间里内核有没有往磁盘搬页。
    """
    p = state_path or SWAP_STATE
    now = time.time()
    used, so, si = _counters()
    prev = None
    try:
        prev = json.load(open(p, encoding="utf-8"))
    except Exception:
        prev = None
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump({"ts": now, "used_gb": used, "swapouts": so, "swapins": si},
                  open(p, "w", encoding="utf-8"))
    except Exception:
        pass
    if not prev:
        return None, 0.0, 0.0
    dt = now - float(prev.get("ts") or 0)
    if dt < min_window_s:
        # 窗口太短，速率没有统计意义，别用噪声当判据
        return None, round(used - float(prev.get("used_gb") or 0), 2), round(dt, 1)
    d_out = so - int(prev.get("swapouts") or 0)
    d_in = si - int(prev.get("swapins") or 0)
    rate = max(0, d_out + d_in) / dt
    return round(rate, 2), round(used - float(prev.get("used_gb") or 0), 2), round(dt, 1)


def decide(need_gb: float, state_path=None) -> dict:
    avail = available_gb()
    swap = swap_used_gb()
    rate, d_used, win = swap_rate(state_path=state_path)
    model_max = max(0.0, min(CAP_GB, avail - RESERVE_GB))
    note = ""
    # 判据按"正在换页的速率"分级，不看历史残留量。
    if rate is not None and rate >= SWAP_RATE_HARD:
        model_max = min(model_max, RESIDENT_GB)
        note = "正在换页（%.1f 页/秒，近 %.0fs）→ 不许超过驻留席位" % (rate, win)
    elif rate is not None and rate >= SWAP_RATE_SOFT:
        model_max = min(model_max, max(RESIDENT_GB, model_max - 2.0))
        note = "轻微换页（%.1f 页/秒，近 %.0fs）→ 预算减 2GB" % (rate, win)
    else:
        # 2026-11-27 实测把「残留量是过期判据」这个假设打翻了：
        # 空闲时 swap 速率确实是 0.0 页/秒（60 秒 Δswapouts=0），但真加载 9B 的
        # 那 39 秒里 swap +2100MB、swapouts +135432 页（≈529MB 写盘、约 3500 页/秒）。
        # 也就是说"加载瞬间的换页"是**采样前看不见**的，拿空闲速率当放行依据会直接踩雷。
        # 所以残留量这一条必须保留为硬约束：32GB 上 2GB 以上的残留在本机等同于
        # "压缩器已经吃了 7GB，再来 9GB 一定换页"。
        if swap >= SWAP_HARD_GB:
            model_max = min(model_max, RESIDENT_GB)
            note = "swap 残留 %.1fGB（实测 9B 在此状态下加载会 +135k 换出）→ 封顶驻留席位" % swap
        elif swap >= SWAP_SOFT_GB:
            model_max = max(0.0, model_max - (swap - SWAP_SOFT_GB))
            note = "swap 残留 %.1fGB → 从预算里扣掉" % swap
        elif rate is None:
            note = "无 paging 基线（首次调用），按可用内存判"
    if need_gb >= model_max:
        verdict = "OK" if need_gb <= model_max else (
            "DOWNGRADE" if model_max >= RESIDENT_GB else "WAIT")
    else:
        verdict = "OK"
    return {"available_gb": avail, "reserve_gb": RESERVE_GB, "cap_gb": CAP_GB,
            "model_max_gb": round(model_max, 1), "need_gb": need_gb,
            "swap_used_gb": swap, "swap_rate": rate, "swap_delta_gb": d_used,
            "window_s": win, "verdict": verdict, "note": note}


def self_test() -> int:
    """判据自检：用注入的采样，不依赖真机当时的负载。

    负控的意义：同一个"2.6GB 残留"在两种情况下必须给出不同结论——
    没在换页时不许禁大模型（否则 9B 被一条过期判据永久锁死），
    真在换页时必须降到驻留席位。
    """
    import tempfile
    cases = []
    d = tempfile.mkdtemp(prefix="mg-")
    st = os.path.join(d, "s.json")

    def mkfile(ts_back, used, d_out, d_in, real=None):
        """基线必须建立在**真实计数器**上，否则算出来的增量毫无意义（自检第一版就栽在这）。"""
        ru, rout, rin = real or _counters()
        json.dump({"ts": time.time() - ts_back, "used_gb": used,
                   "swapouts": rout - d_out, "swapins": rin - d_in},
                  open(st, "w", encoding="utf-8"))

    # 1 残留 2.6GB 但窗口内零换页 → 速率≈0，不许因此禁 9B
    mkfile(60, 2.6, 0, 0)
    rate, _, win = swap_rate(state_path=st, min_window_s=15)
    cases.append(("残留 swap 但零换页 → rate≈0", rate is not None and rate < 1))
    # 2 真在换页 → rate 高
    mkfile(60, 2.6, 6000, 0)
    rate2, _, _ = swap_rate(state_path=st, min_window_s=15)
    cases.append(("60 秒 6000 次换出 → rate≈100", rate2 is not None and rate2 >= 50))
    # 3 窗口过短 → 不判（不许拿噪声当判据）
    mkfile(3, 2.6, 0, 0)
    rate3, _, _ = swap_rate(state_path=st, min_window_s=15)
    cases.append(("窗口 3 秒 → 返回 None（窗口太短不判）", rate3 is None))
    # 4 无基线 → None
    try:
        os.remove(st)
    except Exception:
        pass
    rate4, _, _ = swap_rate(state_path=st, min_window_s=15)
    cases.append(("无基线 → None", rate4 is None))
    n = sum(1 for _, v in cases if v)
    for name, v in cases:
        print("  [%s] %s" % ("PASS" if v else "FAIL", name))
    print("[mem-gate] %d/%d %s" % (n, len(cases), "PASS" if n == len(cases) else "FAIL"))
    return 0 if n == len(cases) else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    need = 22.0
    if "--need-gb" in sys.argv:
        need = float(sys.argv[sys.argv.index("--need-gb") + 1])
    d = decide(need)
    if "--json" in sys.argv:
        print(json.dumps(d, ensure_ascii=False))
    else:
        print("[mem] avail=%.1fGB max_model=%.1fGB need=%.1fGB swap=%.1fGB rate=%s -> %s%s"
              % (d["available_gb"], d["model_max_gb"], d["need_gb"], d["swap_used_gb"],
                 d.get("swap_rate"), d["verdict"],
                 (" | " + d["note"]) if d.get("note") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())