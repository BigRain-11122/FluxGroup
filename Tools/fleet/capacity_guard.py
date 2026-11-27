#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capacity_guard.py - 本机（bm-m）开工前的能力闸，按实测量出来。

CEO 2026-11-05：「不换页、不过热，好好测这个度」「自己本机的也是（要调度好）」。
实测包络（cph4/fleet/MAC-CAPACITY-SURFACE-v1.json）：
  - CPU 拐点 8 并发，第 9/10 路只多 3.6%
  - 新增不可压缩负载上限约 8GB，超过先压缩后换页
  - 视觉模型与生成模型必须互斥（GPU 同一刻只给一个）

用法（供 lane_agent 在跑 GPU 卡前调用）：
  from capacity_guard import before_gpu
  ok, why = before_gpu(need_gb=10)
  python3 Tools/fleet/capacity_guard.py --need-gb 10   # 命令行自检
Exit: 0 可以开；1 不该开（附原因）
"""
import json
import os
import subprocess
import sys
import urllib.request

SWAP_GROWTH_LIMIT_MB = 64     # 采样两点的增量上限（存量不算，增量才算压力）
SWAP_SAMPLE_S = 5
MAX_NEW_INCOMPRESSIBLE_GB = 8.0   # 实测：视觉模型驻留时的新增上限（仅作参考）
RESERVE_GB = 4.0                   # 留给系统与 CEO 办公应用的底线
VISION_MODELS = ("qwen3.5", "mlx")
KEEP_RESIDENT = ()  # 2026-11-09 交换紧张：向量改为按需加载，用完即卸


def swap_mb():
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                             text=True, timeout=5).stdout
        return float(out.split("used =")[1].split("M")[0].strip())
    except Exception:
        return -1.0


def vm_avail_gb():
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return -1.0
    p = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.rsplit(":", 1)
            v = v.strip().replace(".", "")
            if v.isdigit():
                p[k.strip()] = int(v)
    return (p.get("Pages free", 0) + p.get("Pages inactive", 0)
            + p.get("Pages purgeable", 0)) * 16384 / 1e9


def resident():
    try:
        d = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/ps",
                                              timeout=5).read())
        return [(m.get("name", ""), m.get("size", 0) / 1e9) for m in d.get("models", [])]
    except Exception:
        return []


def unload(name):
    body = json.dumps({"model": name, "keep_alive": 0}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=30)
        return True
    except Exception:
        return False


def before_gpu(need_gb=10.0):
    """返回 (ok, why)。会把不该驻留的模型退掉再判。"""
    # 存量的 swap 不算红灯（macOS 懒回收，实测长期停在 2.9GB）；
    # 真正的信号是「它还在涨」——所以取两点差。
    sw0 = swap_mb()
    import time as _t
    _t.sleep(SWAP_SAMPLE_S)
    sw1 = swap_mb()
    growth = sw1 - sw0
    if growth > SWAP_GROWTH_LIMIT_MB:
        return False, ("SWAP-GROWING：%.0fMB -> %.0fMB（+%.0fMB），正在换页，不开新槽"
                       % (sw0, sw1, growth))
    sw = sw1
    evicted = []
    for name, gb in resident():
        if any(k in name for k in KEEP_RESIDENT):
            continue
        if any(k in name for k in VISION_MODELS):
            if unload(name):
                evicted.append("%s(%.1fG)" % (name, gb))
    avail = vm_avail_gb()
    # 退掉之后重新量
    if evicted:
        import time
        time.sleep(3)
        avail = vm_avail_gb()
        sw = swap_mb()
    # 上限不该写死 8G：那是在"视觉模型还占着"时测出的；退掉之后可用内存会变大。
    # 正解=可用内存减去给系统/CEO 应用的保留量。
    head = max(0.0, avail - RESERVE_GB)
    if need_gb > head:
        return False, ("HEADROOM：需要 %.0fG，可给 %.1fG（可用 %.1fG - 保留 %.0fG，swap %.0fMB）"
                       % (need_gb, head, avail, RESERVE_GB, sw))
    return True, "OK 可用 %.1fG swap %.0fMB 已退 %s" % (avail, sw, ",".join(evicted) or "无")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--need-gb", type=float, default=0)
    ap.add_argument("--gpu", action="store_true")
    a = ap.parse_args(argv)
    if a.gpu or a.need_gb:
        ok, why = before_gpu(a.need_gb)
    else:
        ok, why = True, "swap %.0fMB（只看增量，见 before_gpu）" % swap_mb()
    print("[guard]", "PASS" if ok else "BLOCK", why)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())