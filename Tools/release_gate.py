# -*- coding: utf-8 -*-
"""release_gate.py —— 成片出品闸（PIPELINE-MODULE-REVIEW-v1 §9 四项硬指标）

用法：
    python release_gate.py <video> [--planned N]

输出：四项实测 + PASS/FAIL。任何一项 FAIL → 不得签 PASS、不得发布。
"""
import argparse, subprocess, sys
import numpy as np

W, H, FPS = 240, 136, 24.0


def probe_meta(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_frames,width,height,r_frame_rate",
                        "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1",
                        path], capture_output=True, text=True, errors="replace")
    d = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def detect_cuts(path, threshold=27.0):
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
    except Exception as e:
        return None, "scenedetect 不可用: %s" % e
    v = open_video(path)
    sm = SceneManager()
    sm.add_detector(ContentDetector(threshold=threshold, min_scene_len=6))
    sm.detect_scenes(v, show_progress=False)
    sc = sm.get_scene_list()
    cuts = [float(s.seconds) for s, _ in sc][1:]
    return cuts, None


def frame_diffs(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf",
                          "scale=%d:%d,format=gray" % (W, H), "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, bufsize=10**8)
    fs = W * H
    diffs, prev = [], None
    while True:
        b = p.stdout.read(fs)
        if len(b) < fs:
            break
        a = np.frombuffer(b, dtype=np.uint8).astype(np.int16)
        if prev is not None:
            diffs.append(float(np.abs(a - prev).mean()))
        prev = a
    p.stdout.close(); p.wait()
    return np.array(diffs)


def islands(d):
    spikes = []
    for k in range(len(d)):
        lo, hi = max(0, k - 6), min(len(d), k + 7)
        loc = np.median(np.r_[d[lo:k], d[k + 1:hi]]) if hi - lo > 2 else 1.0
        if d[k] > max(loc * 3.0, 8.0):
            spikes.append(k + 1)
    out = []
    i = 0
    while i < len(spikes) - 1:
        if spikes[i + 1] - spikes[i] <= 3:
            out.append((spikes[i], spikes[i + 1]))
            i += 2
        else:
            i += 1
    return out, spikes


def loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
                        "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    I = lra = tp = None
    for line in r.stderr.splitlines():
        s = line.strip()
        if s.startswith("I:") and "LUFS" in s:
            I = float(s.split()[1])
        elif s.startswith("LRA:") and "LU" in s:
            lra = float(s.split()[1])
        elif "Peak:" in s and "dBFS" in s:
            try:
                tp = float(s.split()[-2])
            except Exception:
                pass
    return I, lra, tp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--planned", type=int, default=None, help="计划镜头数; 缺省则跳过第1项")
    ap.add_argument("--plan-cuts", default=None, help="计划切点 json（含 cuts 数组）")
    ap.add_argument("--max-delta", type=int, default=5)
    ap.add_argument("--tol", type=float, default=0.35, help="切点匹配容差(秒)")
    ap.add_argument("--max-unplanned", type=int, default=5, help="允许的非计划突变数")
    a = ap.parse_args()

    fails = []
    meta = probe_meta(a.video)
    print("== 成片出品闸 ==")
    print("文件:", a.video)
    print("帧数 %s | %sx%s | %s fps | 时长 %ss" % (
        meta.get("nb_frames"), meta.get("width"), meta.get("height"),
        meta.get("r_frame_rate"), round(float(meta.get("duration", 0)), 2)))

    cuts, err = detect_cuts(a.video)
    if err:
        fails.append("①切点检测失败 " + err)
        print("① 计划vs检测: 检测不可用")
    else:
        n = len(cuts) + 1
        plan = None
        if a.plan_cuts:
            try:
                import json
                plan = json.load(open(a.plan_cuts, encoding="utf-8"))["cuts"]
            except Exception as e:
                print("① 计划切点表读取失败:", e)
        if plan:
            # 判据口径：只统计"硬跳"(帧差突跳)，不把叠化/渐变算成突变
            _d = frame_diffs(a.video)
            _, _sp = islands(_d)
            _spike_t = [s / FPS for s in _sp]
            unplanned = [t for t in _spike_t if not any(abs(t - p) <= a.tol for p in plan)]
            print("   ①口径：帧差突跳 %d 处，其中非计划 %d 处" % (len(_spike_t), len(unplanned)))
            ok = len(unplanned) <= a.max_unplanned
            print("① 计划切点 %d | 检测切点 %d | **非计划突变 %d** (门线 ≤%d) → %s" %
                  (len(plan), len(cuts), len(unplanned), a.max_unplanned, "PASS" if ok else "FAIL"))
            if not ok:
                fails.append("①非计划突变 %d 处（%s）" % (
                    len(unplanned), ", ".join("%.2f" % x for x in unplanned[:12])))
        elif a.planned:
            delta = n - a.planned
            ok = abs(delta) <= a.max_delta
            print("① 计划镜数 %d | 检测镜数 %d | 差 %+d (门线 ±%d) → %s" %
                  (a.planned, n, delta, a.max_delta, "PASS" if ok else "FAIL"))
            if not ok:
                fails.append("①非计划突变超限 %+d" % delta)
        else:
            print("① 检测镜数 %d（未给计划表，跳过比对）" % n)

    d = frame_diffs(a.video)
    isl, spikes = islands(d)
    print("② 微叠化孤岛 %d 处 | 帧间突跳 %d 处" % (len(isl), len(spikes)))
    if isl:
        fails.append("②微叠化孤岛 %d 处" % len(isl))
        for s, e in isl[:8]:
            print("   孤岛 t=%.2f-%.2f (帧 %d-%d)" % (s / FPS, e / FPS, s, e - 1))

    I, lra, tp = loudness(a.video)
    ok_loud = (I is not None and -15.0 <= I <= -13.0)
    ok_tp = (tp is not None and tp <= -1.0)
    print("③ 响度 I=%s LUFS (门线 -14±1) | LRA=%s | 真峰值 %s dBFS (门线 ≤-1.0) → %s" %
          (I, lra, tp, "PASS" if (ok_loud and ok_tp) else "FAIL"))
    if not ok_loud:
        fails.append("③响度超窗 I=%s" % I)
    if not ok_tp:
        fails.append("③真峰值超限 %s" % tp)

    print("④ 逐切点 strip+波形：需人工/子代理按切点 ±1.5s 目检（本闸只出清单）")
    print("   切点清单:", ", ".join("%.2f" % c for c in (cuts or [])[:60]))

    print()
    if fails:
        print("VERDICT: FAIL —— " + "；".join(fails))
        sys.exit(1)
    print("VERDICT: PASS（第④项仍需人工目检确认）")


if __name__ == "__main__":
    main()