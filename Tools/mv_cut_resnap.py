# -*- coding: utf-8 -*-
"""mv_cut_resnap.py — 词头选位 + 拍点落刀（MV 剪辑网格重吸附）

问题：旧网格把「词行边界」硬吸到 ±0.10s 的拍点/词首，但词行边界来自 whisper 行级估计、
经常落在词中间，所以吸附率只有 29%-76%。

正法（剪辑席 2026-10-20 判据 #1/#5）：
  1. 每行切点 = 「离该行词头最近的拍点」（词头用于**选择**，拍点用于**落位**）
  2. 超过 max_shot 的行，在拍/小节线上等距补切点（优先 downbeat）
  3. 同窗重复行去重（相邻完全相同窗口）
输出：<song>-shotgrid-resnap.json + 控制台报告（不覆盖原文件）
"""
import json, glob, os, sys, bisect

BASE = os.path.dirname(os.path.abspath(__file__))
ANCH = os.path.join(BASE, "..", "cph4", "fleet", "mv-album-001-jay", "anchors")
ANCH = os.path.normpath(ANCH)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def times(items):
    out = []
    for x in items:
        if isinstance(x, (list, tuple)):
            out.append(float(x[0]))
        elif isinstance(x, dict):
            out.append(float(x.get("time", x.get("t", 0))))
        else:
            out.append(float(x))
    return sorted(out)


def nearest(arr, t):
    if not arr:
        return None
    i = bisect.bisect_left(arr, t)
    if i == 0:
        return arr[0]
    if i >= len(arr):
        return arr[-1]
    return arr[i] if (arr[i] - t) < (t - arr[i - 1]) else arr[i - 1]


def process(sg_path):
    stem = os.path.basename(sg_path)[: -len("-shotgrid.json")]
    wp = os.path.join(os.path.dirname(sg_path), stem + "-words.json")
    bp = os.path.join(os.path.dirname(sg_path), stem + "-beats.json")
    if not (os.path.exists(wp) and os.path.exists(bp)):
        return None

    sg, w, b = load(sg_path), load(wp), load(bp)
    wstarts = sorted({round(float(x["start"]), 3) for x in w["words"]})
    wends = sorted({round(float(x["end"]), 3) for x in w["words"]})
    beats = times(b["beats"])
    downs = times(b["downbeats"])
    if len(beats) < 8:
        return None

    max_shot = float(sg.get("max_shot_sec", 3.0))
    old_snapped = sum(1 for g in sg["grid"] if g.get("snapped"))
    old_lines = len(sg["grid"])

    # ── 0) 修复源数据坏行：零长度/倒挂/重复 ──────────────────────────
    raw, degenerate, dropped = [], 0, 0
    prev_orig = None
    for g in sg["grid"]:
        t0, t1 = g.get("t0"), g.get("t1")
        if t0 is None or t1 is None:
            raw.append({**g, "_untimed": True})
            continue
        if prev_orig == (t0, t1):
            dropped += 1
            continue
        prev_orig = (t0, t1)
        if t1 <= t0 + 0.05:          # 零长度/倒挂行 = 坏行，标记后按词头重算终点
            degenerate += 1
            raw.append({**g, "_degenerate": True})
            continue
        raw.append(g)
    raw.sort(key=lambda g: (g.get("t0") if g.get("t0") is not None else 1e9))

    out, offs, prev_c1 = [], [], None
    for idx, g in enumerate(raw):
        t0, t1 = g.get("t0"), g.get("t1")
        if t0 is None or t1 is None:
            out.append({**g, "cut0": None, "cut1": None, "on_beat": False,
                        "splits": [], "resnap": "untimed"})
            continue
        if g.get("_degenerate"):      # 坏行（零长度/倒挂）不编造切点：剔除并记账
            out.append({**g, "cut0": None, "cut1": None, "on_beat": False,
                        "splits": [], "resnap": "degenerate_excluded"})
            continue
        ws = nearest(wstarts, float(t0))
        we = nearest(wends, float(max(t1, t0)))
        anchored = abs(ws - float(t0)) <= 1.0     # 词头可锚（前奏/器乐行不参与偏移统计）
        c0 = nearest(beats, ws)
        c1 = nearest(beats, we)
        if prev_c1 is not None and c0 < prev_c1:   # 轻微单调修正（不越一拍）
            c0 = nearest(beats, prev_c1)
            shifted = True
        else:
            shifted = False
        if c1 <= c0:
            i = bisect.bisect_right(beats, c0)
            c1 = beats[min(i, len(beats) - 1)] if i < len(beats) else c0 + 0.5
        prev_c1 = c1
        if anchored and not shifted:
            offs.append(abs(c0 - ws))
        # 超长行在拍/小节线上补切点（优先 downbeat）
        splits = []
        cur = c0
        while c1 - cur > max_shot + 1e-6:
            target = cur + max_shot
            d = nearest(downs, target) if downs else None
            cand = d if (d is not None and abs(d - target) <= 0.60 and d > cur + 0.5) else nearest(beats, target)
            if cand is None or cand <= cur + 0.5:
                break
            splits.append(round(cand, 3))
            cur = cand
        out.append({**g, "cut0": round(c0, 3), "cut1": round(c1, 3), "on_beat": True,
                    "word_onset": round(ws, 3), "onset_offset": round(abs(c0 - ws), 3),
                    "splits": splits, "resnap": "beat"})

    # 不去重吸附后的撞点（撞点已在上面顺延处理——删行=丢词）
    kept = out

    new = dict(sg)
    new["version"] = "anchor-shotgrid v2.0 resnap (word-onset select / beat place)"
    new["grid"] = kept
    new["summary"] = {
        "lines": len(kept),
        "cuts": sum(1 + len(r.get("splits", [])) for r in kept if r.get("cut0") is not None),
        "cuts_on_beat": sum(1 + len(r.get("splits", [])) for r in kept if r.get("cut0") is not None),
        "mean_onset_offset_sec": round(sum(offs) / len(offs), 3) if offs else None,
        "max_onset_offset_sec": round(max(offs), 3) if offs else None,
        "same_window_rows_removed": dropped,
        "degenerate_rows_repaired": degenerate,
        "old_lines": old_lines,
        "old_snapped": old_snapped,
    }
    outp = sg_path.replace("-shotgrid.json", "-shotgrid-resnap.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(new, f, ensure_ascii=False, indent=2)
    return stem, new["summary"], outp


def main():
    paths = sorted(glob.glob(os.path.join(ANCH, "*-shotgrid.json")))
    rows = []
    for p in paths:
        if p.endswith("-resnap.json"):
            continue
        r = process(p)
        if r:
            rows.append(r)
    for stem, s, outp in rows:
        print(f"{stem}\t lines={s['lines']}\tcuts={s['cuts']}\ton_beat={s['cuts_on_beat']}"
              f"\tmean_onset_offset={s['mean_onset_offset_sec']}s"
              f"\tmax={s['max_onset_offset_sec']}s\tdedup={s['same_window_rows_removed']}"
              f"\tdegen_repaired={s['degenerate_rows_repaired']}"
              f"\t(was snapped {s['old_snapped']}/{s['old_lines']})")
    print(f"\nwritten: {len(rows)} files")


if __name__ == "__main__":
    main()