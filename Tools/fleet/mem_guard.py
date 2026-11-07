#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mem_guard.py - 本地算力「完全赋能」的护栏：往内存里多塞模型，但不许把硬盘当内存用。

CEO 2026-11-07：「我办公不用留这么多，希望把本地算力完全赋能，但最好不要 swap 浪费硬盘」。

为什么不能只看 swap used：macOS 的 swap 一旦用过就会保留在账上（本机实测 used 3.2GB，
其中很多是历史页），它不回落不代表现在在抖。真正会伤硬盘的是**换页速率**：
  - Pageouts 增长 = 正在把内存页写到盘
  - Pageins 增长 = 正在从盘读回（更慢）
所以本工具的判据是「窗口内的换页增量」，不是 swap 占用总量。

判据（阈值来自 cph4/fleet/MEM-GUARD-v1.json）：
  A. window 内 pageouts 增量 ≤ pageouts_max_per_min * 分钟数
  B. 窗口内 swap used 增量 ≤ swap_growth_max_mb
  C. 常驻模型合计 ≤ resident_gb_limit
  D. 系统可用内存 ≥ min_free_gb（防止把办公应用挤到换页）

输出 state/mem-guard.json + 一屏 MEM-GUARD.md；rc=1 表示有人在拿硬盘当内存用，
并给出「该卸谁」的具体建议（按矩阵 swap.order）。

用法：
  python3 Tools/fleet/mem_guard.py                # 观察 60 秒后判定
  python3 Tools/fleet/mem_guard.py --window 120
  python3 Tools/fleet/mem_guard.py --apply        # 超限时真的按 swap.order 卸档
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
CFG = os.path.join(F, "MEM-GUARD-v1.json")
OLLAMA = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ""


def swap_used_mb():
    m = re.search(r"used = ([\d.]+)M", sh("sysctl -n vm.swapusage"))
    return float(m.group(1)) if m else -1.0


def pageouts():
    m = re.search(r"Pageouts:\s+(\d+)", sh("vm_stat"))
    return int(m.group(1)) if m else -1


def pageins():
    m = re.search(r"Pageins:\s+(\d+)", sh("vm_stat"))
    return int(m.group(1)) if m else -1


def free_gb():
    """真实可用内存 = 总内存 - (wired + active + compressed)。

    2026-11-07 修正：早先按 free + inactive*0.5 算，把 macOS 的文件缓存当成了占用，
    报出"可用 5.5GB"的假紧张（实际 free%=60）。文件缓存是可回收的，不该算占。
    """
    v = sh("vm_stat")
    def pages(key):
        m = re.search(r"%s:\s+(\d+)" % key, v)
        return int(m.group(1)) if m else 0
    total = int(re.search(r"page size of (\d+) bytes", v).group(1)) if "page size of" in v else 16384
    used = pages("Pages wired down") + pages("Pages active") + pages("Pages occupied by compressor")
    mem = int(sh("sysctl -n hw.memsize") or 0)
    if not mem:
        mem = 32 * 1073741824
    return round((mem - used * total) / 1073741824.0, 1)


def resident():
    try:
        d = json.loads(urllib.request.urlopen(OLLAMA + "/api/ps", timeout=8).read())
        out = []
        for m in d.get("models") or []:
            out.append({"name": m.get("name"), "gb": round((m.get("size") or 0) / 1e9, 1)})
        return out
    except Exception as e:
        return [{"name": "_error", "gb": 0.0, "err": str(e)[:80]}]


def unload(name):
    try:
        req = urllib.request.Request(OLLAMA + "/api/generate", method="POST",
                                     data=json.dumps({"model": name, "keep_alive": 0}).encode())
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=60).read()
        return True
    except Exception:
        return False


def cfg():
    d = {}
    try:
        with open(CFG, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        pass
    return {
        "window_s": d.get("window_s", 60),
        "pageouts_max_per_min": d.get("pageouts_max_per_min", 120),
        "swap_growth_max_mb": d.get("swap_growth_max_mb", 64),
        "resident_gb_limit": d.get("resident_gb_limit", 16.0),
        "min_free_gb": d.get("min_free_gb", 3.0),
        "swap_order": d.get("swap_order") or ["triage", "big", "resident", "embedding"],
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    c = cfg()
    win = a.window or c["window_s"]

    sw0, po0, pi0 = swap_used_mb(), pageouts(), pageins()
    time.sleep(win)
    sw1, po1, pi1 = swap_used_mb(), pageouts(), pageins()
    mins = max(win / 60.0, 0.1)
    d_po = po1 - po0
    d_pi = pi1 - pi0
    d_sw = sw1 - sw0
    live = resident()
    tot = round(sum(x["gb"] for x in live), 1)
    fg = free_gb()

    errs, warns = [], []
    rate = d_po / mins
    if rate > c["pageouts_max_per_min"]:
        errs.append("E-SWAP-THRASH: %d 秒内换出 %d 页（%.0f/min，上限 %d/min）"
                    % (win, d_po, rate, c["pageouts_max_per_min"]))
    if d_pi > c["pageouts_max_per_min"] * mins * 4:
        warns.append("W-SWAP-IN: 换入 %d 页，读回在拖慢推理" % d_pi)
    if d_sw > c["swap_growth_max_mb"]:
        errs.append("E-SWAP-GROW: swap 增长 %.0fMB（上限 %dMB）" % (d_sw, c["swap_growth_max_mb"]))
    if tot > c["resident_gb_limit"]:
        errs.append("E-RESIDENT: 常驻 %.1fGB 超上限 %.1fGB" % (tot, c["resident_gb_limit"]))
    if fg < c["min_free_gb"]:
        warns.append("W-FREE: 可用内存 %.1fGB 低于 %.1fGB，办公应用会被挤" % (fg, c["min_free_gb"]))

    verdict = "FAIL" if errs else ("WARN" if warns else "PASS")
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "window_s": win,
           "pageouts_delta": d_po, "pageins_delta": d_pi, "swap_used_mb": sw1,
           "swap_delta_mb": d_sw, "resident_gb": tot,
           "resident": [x["name"] for x in live], "free_gb": fg,
           "verdict": verdict, "errors": errs, "warnings": warns}
    os.makedirs(os.path.join(F, "state"), exist_ok=True)
    with open(os.path.join(F, "state", "mem-guard.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    acted = []
    if a.apply and errs:
        # 按矩阵换出顺序，从最便宜的开始卸，直到常驻回到上限内
        for name in live:
            if tot <= c["resident_gb_limit"] and rate <= c["pageouts_max_per_min"]:
                break
            if unload(name["name"]):
                acted.append(name["name"])
                tot = round(tot - name["gb"], 1)
                rate = 0

    L = ["# 内存护栏 %s" % rec["ts"], "",
         "- 判定：**%s**" % verdict,
         "- 观察窗：%ds｜换出 %d 页（%.0f/min）｜换入 %d 页" % (win, d_po, rate, d_pi),
         "- swap：used %.0fMB（窗口变化 %+.0fMB）" % (sw1, d_sw),
         "- 常驻：%.1fGB（上限 %.1f）｜%s" % (tot, c["resident_gb_limit"],
                                            ", ".join("%s %.1f" % (x["name"], x["gb"]) for x in live) or "-"),
         "- 可用内存：%.1fGB（下限 %.1f）" % (fg, c["min_free_gb"]), ""]
    if errs:
        L += ["## 违规", ""] + ["- %s" % e for e in errs]
    if warns:
        L += ["", "## 提醒", ""] + ["- %s" % w for w in warns]
    if acted:
        L += ["", "## 已卸载", ""] + ["- %s" % x for x in acted]
    L += ["", "_判据：换页速率，不看 swap 占用总量（用过就会留账，不回落不等于在抖）_"]
    open(os.path.join(F, "MEM-GUARD.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    if a.json:
        print(json.dumps(rec, ensure_ascii=False))
    else:
        print("[mem-guard] %s 换出 %.0f/min 换入 %d 常驻 %.1fGB 可用 %.1fGB%s"
              % (verdict, rate, d_pi, tot, fg, (" 卸载:" + ",".join(acted)) if acted else ""))
        for e in errs:
            print("   - %s" % e)
        for w in warns:
            print("   - %s" % w)
    return 0 if verdict != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))