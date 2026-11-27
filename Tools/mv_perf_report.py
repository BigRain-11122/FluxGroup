# -*- coding: utf-8 -*-
"""mv_perf_report.py - 把 MV 渲染的耗时记账汇成一页，供"优化到底有没有用"取证。

为什么（2026-11-03）：装了加速库/改了步数之后，判断只能靠"感觉变快了"——这不成立。
每次渲染必须留下 steps/sec/尺寸/字节（mv_kf_batch.py 已写 <out>/_perf.jsonl），
本工具只做汇总与对比，不调模型、不改产线参数。

用法：
  python Tools/mv_perf_report.py                 # 扫 media/ 下所有 _perf.jsonl
  python Tools/mv_perf_report.py --root D:\\FluxGroup\\media
  python Tools/mv_perf_report.py --json cph4/fleet/queue-receipts/mv-perf-<date>.json

口径：
  按 (tag, steps, unet) 分组，报 n / 中位秒数 / 中位出图字节；
  中位数而不是均值——单次受 GPU 状态影响大，均值会被一次卡顿带跑偏。
"""
import argparse
import glob
import json
import os
import statistics
import sys
import time


def _root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_rows(media_root):
    rows = []
    for p in glob.glob(os.path.join(media_root, "**", "_perf.jsonl"), recursive=True):
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    r["_src"] = p
                    rows.append(r)
        except OSError:
            continue
    return rows


def summarize(rows):
    groups = {}
    for r in rows:
        key = (r.get("tag") or "", r.get("steps"), r.get("unet") or "")
        groups.setdefault(key, []).append(r)
    out = []
    for (tag, steps, unet), rs in sorted(groups.items(), key=lambda kv: (kv[0][2], kv[0][1] or 0)):
        secs = [x["sec"] for x in rs if isinstance(x.get("sec"), (int, float))]
        sizes = [x["bytes"] for x in rs if isinstance(x.get("bytes"), int) and x["bytes"]]
        out.append({
            "tag": tag, "steps": steps, "unet": os.path.basename(unet),
            "n": len(rs),
            "median_sec": round(statistics.median(secs), 1) if secs else None,
            "median_mb": round(statistics.median(sizes) / 1e6, 2) if sizes else None,
            "first_ts": min((x.get("ts") or "") for x in rs),
            "last_ts": max((x.get("ts") or "") for x in rs),
        })
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    root = _root()
    # media 在工作树里是 junction，dirname(root) 会落到桌面而不是仓库；
    # 默认优先真身目录，其次才是仓库内的 media/。
    candidates = [a.root, r"D:\FluxGroup\media", os.path.join(root, "media")]
    media = next((c for c in candidates if c and os.path.isdir(c)), os.path.join(root, "media"))
    rows = load_rows(media)
    groups = summarize(rows)
    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "media_root": media,
              "rows": len(rows), "groups": groups}
    print("rows=%d groups=%d media=%s" % (len(rows), len(groups), media))
    for g in groups:
        print("  steps=%s tag=%-4s n=%-3d median=%ss %sMB %s"
              % (g["steps"], g["tag"] or "-", g["n"], g["median_sec"],
                 g["median_mb"], g["unet"]))
    if not rows:
        # 空账不是错误，但必须说清楚"账本为空"，否则会被当成"已优化且很快"
        print("NOTE: 没有 _perf.jsonl —— 说明还没用带记账的批跑过，不能据此判断任何性能")
    if a.json:
        p = a.json if os.path.isabs(a.json) else os.path.join(root, a.json)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print("wrote %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))