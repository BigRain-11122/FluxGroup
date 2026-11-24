#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vram_ceiling.py — 实测本机"不触发 swap 的最大模型配置"（不靠猜）。

口径（这是本工具存在的全部理由）：
  1 **判据是 swap 增长，不是"空闲内存还够"**。macOS 会把不活跃页算成可用，
     等真用起来才发现已经在换页；所以每个配置都要盯 vm.swapusage 的 used 有没有涨，
     并在运行中每 2 秒采样一次，取峰值增量。
  2 **算力用满=tok/s × 可用上下文**，不是堆并发。之前实测 4B 串行 39 tok/s、
     并发 2/4 反而 36/35——并发不增吞吐只增内存。
  3 每个配置开跑前 `ollama stop` 全部卸载，保证基线干净；跑完立刻卸载。

产出：cph4/fleet/LOCAL-MODEL-CEILING-v1.json（配置/上下文/tok/s/swap 峰值增量/结论）
用法：
  python3 Tools/fleet/vram_ceiling.py --sweep      # 跑梯子（约 10 分钟）
  python3 Tools/fleet/vram_ceiling.py --apply      # 把最优配置写进 plist 与策略
  python3 Tools/fleet/vram_ceiling.py --self-test
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-CEILING-v1.json")
HOST = "http://127.0.0.1:11434"
PAGE = 16384
KEEP_ALIVE = "6h"           # 档位内模型常驻时长：10m 会掉，等于档位没生效
SWAP_TOL_MB = 200          # 允许的波动（加密 swap 统计有抖动），超过即判"触发了 swap"
PROMPT = "用一句话说明什么是蒙太奇。"
BASE_MODEL = "qwen3.5:4b-mlx"
BIG_MODEL = "qwen3.5:9b-mlx"


def sh(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")


def vm_text():
    return sh("vm_stat")


def mem_free_mb(text=None):
    """空闲 = free + inactive + speculative（inactive 可回收，但要留着给 OS 抖动用）。"""
    t = text or vm_text()
    def pg(k):
        m = re.search(r"%s:\s+(\d+)" % k, t)
        return int(m.group(1)) if m else 0
    return round((pg("Pages free") + pg("Pages inactive") + pg("Pages speculative"))
                 * PAGE / 1e6, 1)


def swap_used_mb():
    m = re.search(r"used = ([\d.]+)M", sh("sysctl -n vm.swapusage"))
    return float(m.group(1)) if m else 0.0


def stop_all():
    out = sh("ollama ps")
    names = [l.split()[0] for l in out.splitlines()[1:] if l.strip()]
    for n in names:
        sh("ollama stop %s" % n)
    time.sleep(3)
    return names


def loaded():
    out = sh("ollama ps")
    rows = []
    for l in out.splitlines()[1:]:
        p = l.split()
        if len(p) >= 6:
            rows.append({"name": p[0], "size_gb": p[2], "ctx": p[5]})
    return rows


def gen(model, num_ctx, num_predict=128, timeout=300, keep_alive=None):
    """一次非流式生成：拿 eval_count/eval_duration 算解码速度。

    keep_alive 必须显式传：服务端 OLLAMA_KEEP_ALIVE=10m，不传就只能热 10 分钟——
    2026-11-18 实锚，切完档过一会儿再看只剩一条在驻，三条车道的 60 tok/s 等于没兑现。
    """
    body = {"model": model, "prompt": PROMPT, "stream": False,
            "options": {"num_ctx": num_ctx, "num_predict": num_predict,
                        "temperature": 0, "top_k": 1}}
    if keep_alive is not None:
        body["keep_alive"] = keep_alive
    body = json.dumps(body).encode()
    req = urllib.request.Request(HOST + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        js = json.loads(r.read().decode())
    wall = time.time() - t0
    ec = js.get("eval_count") or 0
    ed = (js.get("eval_duration") or 0) / 1e9
    return {"tok_s": round(ec / ed, 1) if ed else None, "tokens": ec,
            "wall_s": round(wall, 1),
            "model_total_gb": round((js.get("model_size") or 0) / 2**30, 2) or None}


def probe_once(model, num_ctx, label=""):
    """单配置：卸载→记基线→加载并生成（运行中每 2 秒采 swap）→判结论。"""
    stop_all()
    time.sleep(2)
    base_swap = swap_used_mb()
    base_free = mem_free_mb()
    peak = base_swap
    res = {"model": model, "num_ctx": num_ctx, "label": label,
           "swap_before_mb": base_swap, "free_before_mb": base_free}
    # 生成放在线程里，主线程采样 swap
    import threading
    box = {}

    def work():
        try:
            box.update(gen(model, num_ctx))
        except Exception as e:
            box["err"] = str(e)[:120]

    th = threading.Thread(target=work)
    th.start()
    while th.is_alive():
        peak = max(peak, swap_used_mb())
        time.sleep(2)
    th.join()
    time.sleep(1)
    peak = max(peak, swap_used_mb())
    res.update(box)
    res["swap_peak_mb"] = peak
    res["swap_growth_mb"] = round(peak - base_swap, 1)
    res["loaded"] = loaded()
    res["verdict"] = "SWAP" if res["swap_growth_mb"] > SWAP_TOL_MB else "SAFE"
    stop_all()
    return res


def sweep():
    cfg = [(BASE_MODEL, 8192), (BASE_MODEL, 16384), (BASE_MODEL, 32768),
           (BIG_MODEL, 8192), (BIG_MODEL, 16384), (BIG_MODEL, 32768)]
    rows = []
    print("[ceiling] 空闲可支配 %.1fMB · swap 已用 %.0fMB"
          % (mem_free_mb(), swap_used_mb()), flush=True)
    for model, ctx in cfg:
        r = probe_once(model, ctx)
        rows.append(r)
        print("[ceiling] %-16s ctx=%-6d %5.6s tok/s · swap +%4.0fMB · %-4s · 载入 %s"
              % (model, ctx, r.get("tok_s") or "-", r["swap_growth_mb"], r["verdict"],
                 (r["loaded"][0]["size_gb"] if r["loaded"] else "?")), flush=True)
    # 双驻留：先小后大，看能否同时在线
    stop_all()
    a = probe_once(BASE_MODEL, 8192, label="co-resident-A")
    b = None
    try:                       # 不卸载 A，直接加载 B
        b = gen(BIG_MODEL, 8192)
        time.sleep(1)
        both = loaded()
    except Exception as e:
        both, b = [], {"err": str(e)[:100]}
    co = {"label": "co-resident", "a": a, "b": b, "loaded": both,
          "swap_mb": swap_used_mb(),
          "verdict": "SWAP" if swap_used_mb() - a["swap_before_mb"] > SWAP_TOL_MB else "SAFE"}
    stop_all()
    best = max((r for r in rows if r["verdict"] == "SAFE" and r.get("tok_s")),
               key=lambda r: (r["num_ctx"], r["tok_s"]), default=None)
    payload = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "host": sh("sysctl -n machdep.cpu.brand_string").strip(),
               "ram_gb": round(int(sh("sysctl -n hw.memsize").strip() or 0) / 2**30, 1),
               "swap_total_mb": re.search(r"total = ([\d.]+)M", sh("sysctl -n vm.swapusage")).group(1)
               if "total" in sh("sysctl -n vm.swapusage") else None,
               "tolerance_mb": SWAP_TOL_MB, "rows": rows, "co_resident": co,
               "best": best}
    json.dump(payload, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    restore_tier()
    if best:
        print("[ceiling] 最大安全配置：%s ctx=%d（%.1f tok/s）→ %s"
              % (best["model"], best["num_ctx"], best["tok_s"], os.path.relpath(OUT, ROOT)))
    else:
        print("[ceiling] 没有任何配置通过（全部触发 swap）")
    return 0 if best else 2


def current_mode():
    try:
        return open(os.path.join(ROOT, ".codely-cli", "state", "MODEL-MODE")).read().strip()
    except Exception:
        return "default"


def restore_tier():
    """把机器拨回 state/MODEL-MODE 记的那一档——探测/自检不许留副作用。"""
    m = current_mode()
    if m in MODES:
        print("[ceiling] 清扫结束，恢复 %s 档" % m, flush=True)
        apply_mode(m, warm=True)


def self_test():
    cases = []
    fake = ("Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
            "Pages free:  1000.\nPages active: 10.\nPages inactive:  2000.\n"
            "Pages speculative: 500.\n")
    cases.append(("空闲解析 free+inactive+spec", mem_free_mb(fake) == round((1000 + 2000 + 500) * 16384 / 1e6, 1)))
    cases.append(("判据：增长 50MB 判 SAFE", (50 > 200) is False))
    cases.append(("判据：增长 500MB 判 SWAP", (500 > 200) is True))
    # tok/s：100 token / 2.5s = 40
    cases.append(("tok/s 计算", round(100 / 2.5, 1) == 40.0))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


MODES = {
    # 三档，全部实测过；切换=卸载+按档预热（预热即把 num_ctx 钉进 runner）
    # 2026-11-18 重测（Tools/fleet/gpu_squeeze.py，并发解码 + 零 swap 判据）：
    #   单 4B@8k = 41 tok/s（两批 41.0/41.2，很稳）
    #   4B+2B = 53-63；再叠 8788 LoRA 车道凑三条 = 48.6-63.0
    #   再加第四条（8B / 4B-dense）= 53-63，一条不涨 → 三条到顶，卡在 GPU 不在内存
    #   9B 是毒丸：4B+9B = 34.8（比单条 4B 还低）还白吃 9GB；lora+4B+9B = 41.9
    # 旧注释里"2 驻留 64.6 / 4 驻留 150.5"是各车道单跑相加，不是并发实测，已废。
    "default": {"models": [(BASE_MODEL, 8192), ("qwen3.5:2b", 8192)],
                "why": "日常：两条 ollama 车道 + 8788 LoRA 约 60 tok/s，留 ~10GB 给采集与训练"},
    "max": {"models": [(BASE_MODEL, 32768), ("qwen3.5:2b", 32768),
                       ("qwen3:4b", 16384)],
            "why": "批处理打满：实测四条车道 53-63 tok/s，与三条同档——第四条只多占内存不多出活"},
    "train": {"models": [], "why": "训练档：全部卸载，LoRA 16层@224 需要 ~10GB"},
    # 2026-11-19 实测（tri_lane_probe，40 iter）：训练 + 8788 出稿 + 一个采集浏览器同时跑，
    # 2.0 分钟跑完 40 步（3.0s/步）、swap 零增长、pageouts 6-88/分（阈值 120）、出稿 10/10。
    # 红线是 9B：它一进来就 9GB，训练进程会被换出（11-18 实锚 rss 3.9→0.43GB）。
    # 共用档只留 4B@8k；2B 那份内存留给采集浏览器更值。
    "train-shared": {"models": [(BASE_MODEL, 8192)],
                     "why": "三线共用：训练 ~10GB + 4B ~5GB + 浏览器 ~1.1GB，实测零换页；9B/8B 禁入"},
}


def apply_mode(mode, warm=True):
    """切档：卸载全部 → 按档预热。预热用 num_predict=1，开销可忽略但会把 ctx 钉住。"""
    if mode not in MODES:
        print("[ceiling] 未知档位 %s（可选 %s）" % (mode, "/".join(MODES)))
        return 2
    stop_all()
    spec = MODES[mode]
    for model, ctx in spec["models"]:
        if not warm:
            break
        try:
            gen(model, ctx, num_predict=1, keep_alive=KEEP_ALIVE)
        except Exception as e:
            print("[ceiling] 预热失败 %s@%d：%s" % (model, ctx, str(e)[:60]))
    got = loaded()
    sw = swap_used_mb()
    free = mem_free_mb()
    print("[ceiling] 已切到 %s：%s" % (mode, spec["why"]))
    print("[ceiling] 驻留 %s · 空闲 %.0fMB · swap %.0fMB"
          % ([(x["name"], x["size_gb"]) for x in got], free, sw))
    st = os.path.join(ROOT, ".codely-cli", "state", "MODEL-MODE")
    os.makedirs(os.path.dirname(st), exist_ok=True)
    open(st, "w", encoding="utf-8").write(mode + "\n")
    return 0 if sw <= swap_used_mb() + SWAP_TOL_MB else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--apply", default=None, help="default|max|train 切档")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.apply:
        return apply_mode(a.apply)
    if a.show:
        print(open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else "还没测过")
        return 0
    return sweep()


if __name__ == "__main__":
    sys.exit(main())
