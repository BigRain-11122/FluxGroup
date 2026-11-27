# -*- coding: utf-8 -*-
"""mv_anomaly_map.py —— 把成片的硬跳/孤岛/重复帧定位到镜头与帧号（只读诊断）

输出：每条异常的 时间/帧号/帧差值/所属镜号/与最近计划切点的偏差，
      以及逐镜帧差基线，便于判断是"素材内部抖动"还是"多切了一刀"。
"""
import json, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release_gate as RG

FPS = 24.0
VIDEO = sys.argv[1] if len(sys.argv) > 1 else \
    r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\full_mv_v601.mp4"
PLAN = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\plan-cuts-mv0001-v5.json"
OUT = r"D:\FleetWorker\review\mv-anomaly-map.json"

plan = json.load(open(PLAN, encoding="utf-8"))["cuts"]
d = RG.frame_diffs(VIDEO)
isl, spikes = RG.islands(d)

# 报告固定写 UTF-8 文本（PowerShell 的 > 会把 stdout 转成 UTF-16）
class _Tee:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.f = open(path, "w", encoding="utf-8")

    def write(self, s):
        self.f.write(s)

    def flush(self):
        self.f.flush()


TXT = OUT.replace(".json", ".txt")
_tee = _Tee(TXT)
_pr = print


def print(*a, **k):
    s = " ".join(str(x) for x in a)
    _tee.write(s + "\n")
    try:
        _pr(*a, **k)
    except Exception:
        pass
n = len(d) + 1
dur = n / FPS

bounds = [0.0] + list(plan) + [dur]
shot_of = lambda t: max(0, min(len(bounds) - 2, int(np.searchsorted(bounds, t, "right") - 1)))
shot_len = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]


def nearest_plan(t):
    if not plan:
        return None, None
    diffs = [(abs(t - p), p) for p in plan]
    return min(diffs)[0], min(diffs)[1]


def spike_rows():
    rows = []
    for s in spikes:
        t = s / FPS
        delta, p = nearest_plan(t)
        k = shot_of(t)
        # 局部基线（前后 12 帧中位数），用于判断超出多少倍
        lo, hi = max(0, s - 13), min(len(d), s + 12)
        base = float(np.median(np.r_[d[lo:s], d[s + 1:hi]])) if hi - lo > 2 else 0.0
        rows.append({"frame": s, "t": round(t, 3), "diff": round(float(d[s - 1]), 2),
                     "base": round(base, 2), "ratio": round(float(d[s - 1]) / base, 1) if base else None,
                     "shot": k + 1, "shot_start": round(bounds[k], 2),
                     "shot_len": round(shot_len[k], 2),
                     "plan_delta": round(delta, 3) if delta is not None else None,
                     "planned": delta is not None and delta <= 0.35})
    return rows


def island_rows():
    rows = []
    for s, e in isl:
        t0, t1 = s / FPS, e / FPS
        k = shot_of(t0)
        seg = d[max(0, s - 1):e]
        rows.append({"frame_start": s, "frame_end": e, "t_start": round(t0, 3),
                     "t_end": round(t1, 3), "len_frames": e - s + 1,
                     "diffs": [round(float(x), 2) for x in seg],
                     "shot": k + 1, "shot_start": round(bounds[k], 2),
                     "plan_delta": round(min(abs(t0 - p) for p in plan), 3) if plan else None})
    return rows


def dup_rows():
    rows = []
    run = []
    for k in range(len(d)):
        if d[k] < 0.35:
            run.append(k + 1)
        else:
            if run:
                rows.append({"frames": run, "t": round(run[0] / FPS, 3),
                             "len": len(run), "shot": shot_of(run[0] / FPS) + 1})
                run = []
    if run:
        rows.append({"frames": run, "t": round(run[0] / FPS, 3), "len": len(run),
                     "shot": shot_of(run[0] / FPS) + 1})
    return rows


sp = spike_rows()
unplanned = [r for r in sp if not r["planned"]]

print("=== 异常定位 ===")
print("总帧 %d / %.3fs / 计划切点 %d / 镜数 %d" % (n, dur, len(plan), len(shot_len)))
print("\n-- 非计划硬跳 %d 处 --" % len(unplanned))
print("%8s %7s %6s %5s %6s %5s %8s %8s" % ("帧", "时间", "帧差", "基线", "倍率", "镜号", "镜起点", "偏计划"))
for r in unplanned:
    print("%8d %7.3f %6.2f %5.2f %6s %5d %8.2f %8.3f" % (
        r["frame"], r["t"], r["diff"], r["base"], r["ratio"], r["shot"],
        r["shot_start"], r["plan_delta"]))

print("\n-- 计划内突跳 %d 处（供对照，不算缺陷） --" % (len(sp) - len(unplanned)))
for r in sp:
    if r["planned"]:
        print("  帧%6d t=%7.3f 镜%3d diff=%.1f" % (r["frame"], r["t"], r["shot"], r["diff"]))

isl_rows = island_rows()
print("\n-- 微叠化孤岛 %d 处 --" % len(isl_rows))
for r in isl_rows:
    print("  帧%6d-%6d t=%7.3f-%7.3f 长%d帧 镜%3d 距计划%.2fs diffs=%s" % (
        r["frame_start"], r["frame_end"], r["t_start"], r["t_end"],
        r["len_frames"], r["shot"], r["plan_delta"], r["diffs"]))

print("\n-- 重复帧(相邻帧差<0.35) %d 段 --" % len(dup_rows()))
for r in dup_rows():
    print("  帧%s t=%.3f 长%d 镜%d" % (r["frames"][:6], r["t"], r["len"], r["shot"]))

lens = np.array(shot_len)
print("\n-- 节奏 --")
print("镜长 σ=%.3f 均值=%.2f 中位=%.2f" % (lens.std(), lens.mean(), np.median(lens)))
for name, a, b, want in [("副歌A", 77.3, 108.2, "<=1.5"), ("副歌B", 141.8, 171.7, "<=1.5"),
                         ("桥段", 172.5, 187.3, ">=4.5")]:
    v = [shot_len[i] for i in range(len(shot_len)) if a <= bounds[i] < b]
    print("%s %d 镜 均长 %.2fs (%s)" % (name, len(v), (sum(v) / len(v)) if v else 0, want))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"video": VIDEO, "frames": n, "duration": round(dur, 3),
           "unplanned_spikes": unplanned, "planned_spikes": [r for r in sp if r["planned"]],
           "islands": isl_rows, "dup_runs": dup_rows(),
           "shot_lengths": [round(x, 3) for x in shot_len]},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已存", OUT)