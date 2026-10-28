# -*- coding: utf-8 -*-
# anchor_shotgrid.py — POOL-0018/0019 消费面：词面行窗口 × 鼓点网格 → 镜头网格（advisory）
#
# 输入: anchors/<曲>-beats.json      madmom beats [[t,pos]] + downbeats [t] + duration_sec
#       anchors/<曲>-calibrated.json 官方词面行 + 行级时间窗 [{t0,t1,text,approx}]
# 输出: anchors/<曲>-shotgrid.json   每行一镜候选：词窗 + 鼓点吸附后窗口 + 长镜建议切点
#       产物旁立 <曲>-shotgrid.md    人眼可读表（1 行 1 镜）
#
# 规则（对齐 CEO 10-19 22:17 V5.11 收口批规格与 QC §22）:
#   - 吸附容差 0.10s：|边界-最近beat| <= 0.10 才吸附，否则保留词窗（>0.10s 词窗优先保留）
#   - 镜长上限 3.0s（主歌 2-3s 上限）：超限行按 beat 网格取近似等分点作为建议切点，
#     切点必落在 beat 上（副歌踩鼓点），不足 2 个候选 beat 时如实留 1 镜并标注
#   - 纯 advisory：不判定、不改词窗、不宣称成片；下游剪辑席自行采纳
# 幂等: 只读输入 + 确定性输出（无墙钟字段、无随机），重跑字节恒等
# selftest: python anchor_shotgrid.py --selftest   (离线合成夹具，零文件依赖)
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ANC = os.path.join(BASE, "anchors")
SONGS = [
    "可爱女人",
    "安静",
    "开不了口",
    "星晴",
    "晴天",
    "简单爱",
    "龙卷风",
    "伊斯坦堡",
    "印第安老斑鸠",
    "反方向的钟",
    "娘子",
    "完美主义",
    "斗牛",
    "黑色幽默",
    "三年二班",
    "上海一九四三",
    "东风破",
    "以父之名",
    "你听得到",
    "分裂",
    "半兽人",
    "半岛铁盒",
    "双刀",
    "双截棍",
    "同一种调调",
    "回到过去",
    "她的睫毛",
    "威廉古堡",
    "对不起",
    "忍者",
    "懦夫",
    "暗号",
    "最后的战役",
    "梯田",
    "火车叨位去",
    "爱在西元前",
    "爱情悬崖",
    "爷爷泡的茶",
    "爸,我回来了",
    "米兰的小铁匠",
    "龙拳",
    # 全专 41 首看板（2026-10-29 事件班：beats 已 41/41，ready 面按 calibrated 实产计）
]
SNAP_TOL = 0.10          # 秒
MAX_SHOT = 3.0           # 秒（主歌镜长上限）
MIN_SHOT = 1.0           # 秒（建议切点最小间隔）
VERSION = "anchor-shotgrid v1.0 (r1070 bm-b)"


def snap(t, beats, tol=SNAP_TOL):
    """返回 (吸附后时间, 是否吸附, 吸附偏差)。beats 已升序。"""
    if not beats:
        return t, False, None
    lo, hi = 0, len(beats) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if beats[mid] < t:
            lo = mid + 1
        else:
            hi = mid
    best = beats[lo]
    if lo > 0 and abs(beats[lo - 1] - t) < abs(best - t):
        best = beats[lo - 1]
    d = t - best
    if abs(d) <= tol:
        return best, True, d
    return t, False, d


def split_points(t0, t1, beats):
    """超长行的建议切点：落在 beat 上、近似等分、间隔 >= MIN_SHOT。"""
    dur = t1 - t0
    if dur <= MAX_SHOT:
        return []
    n = int(dur // MAX_SHOT) + 1
    inner = [b for b in beats if t0 + MIN_SHOT <= b <= t1 - MIN_SHOT]
    if len(inner) < n - 1:
        return []
    pts = []
    for k in range(1, n):
        target = t0 + dur * k / n
        cand = min(inner, key=lambda b: abs(b - target))
        if all(abs(cand - p) >= MIN_SHOT for p in pts) and abs(cand - t0) >= MIN_SHOT and abs(t1 - cand) >= MIN_SHOT:
            pts.append(round(cand, 3))
    return sorted(pts)


def build(song, beats_doc, cal_rows):
    beats = [round(float(b[0]), 3) for b in beats_doc["beats"]]
    down = [round(float(x), 3) for x in beats_doc.get("downbeats") or []]
    if len(beats) >= 2:
        gaps = sorted(beats[i + 1] - beats[i] for i in range(len(beats) - 1))
        bpm = round(60.0 / gaps[len(gaps) // 2], 1) if gaps[len(gaps) // 2] > 0 else None
    else:
        bpm = None

    grid, snaps, missed = [], 0, 0
    for i, r in enumerate(cal_rows):
        t0, t1 = r.get("t0"), r.get("t1")
        if t0 is None:
            grid.append({"i": i, "text": r.get("text"), "t0": None, "t1": None,
                         "t0_used": None, "t1_used": None, "snapped": False,
                         "approx": True, "splits": []})
            continue
        s0, ok0, d0 = snap(float(t0), beats)
        s1, ok1, d1 = snap(float(t1), beats) if t1 is not None else (t0, False, None)
        if ok0 or ok1:
            snaps += 1
        else:
            missed += 1
        if s1 <= s0:  # 防守：吸附后不得反转
            s0, s1 = float(t0), float(t1 if t1 is not None else t0 + MAX_SHOT)
        grid.append({
            "i": i,
            "text": r.get("text"),
            "t0": round(float(t0), 3),
            "t1": round(float(t1), 3) if t1 is not None else None,
            "t0_used": round(s0, 3),
            "t1_used": round(s1, 3),
            "snapped": bool(ok0 or ok1),
            "snap_deltas": [round(d0, 3) if d0 is not None else None,
                            round(d1, 3) if d1 is not None else None],
            "approx": bool(r.get("approx")),
            "splits": split_points(s0, s1, beats),
        })

    return {
        "song": song,
        "version": VERSION,
        "inputs": {"beats_sha_face": beats_doc.get("n_beats"),
                   "n_beats": len(beats), "n_downbeats": len(down),
                   "duration_sec": beats_doc.get("duration_sec")},
        "bpm_median": bpm,
        "snap_tol_sec": SNAP_TOL,
        "max_shot_sec": MAX_SHOT,
        "grid": grid,
        "summary": {
            "lines": len(grid),
            "lines_untimed": sum(1 for g in grid if g["t0"] is None),
            "lines_snapped": snaps,
            "lines_unsnapped": missed,
            "lines_need_split": sum(1 for g in grid if g["splits"]),
            "total_splits": sum(len(g["splits"]) for g in grid),
        },
        "advisory": True,
    }


def emit_md(doc):
    L = ["# %s 镜头网格（advisory·%s）" % (doc["song"], doc["version"]), "",
         "- BPM(median)=%s  镜数=%d  吸附=%d  超 3s 需切=%d（建议切点合计 %d）"
         % (doc["bpm_median"], doc["summary"]["lines"], doc["summary"]["lines_snapped"],
            doc["summary"]["lines_need_split"], doc["summary"]["total_splits"]),
         "", "| # | t0 | t1 | 吸附窗 | 切点 | 词 |", "|---|---|---|---|---|---|"]
    for g in doc["grid"]:
        if g["t0"] is None:
            L.append("| %d | - | - | - | - | %s |" % (g["i"], g["text"]))
            continue
        L.append("| %d | %.2f | %.2f | %.2f-%.2f%s | %s | %s |" % (
            g["i"], g["t0"], g["t1"], g["t0_used"], g["t1_used"],
            " (snap)" if g["snapped"] else "",
            ",".join("%.2f" % x for x in g["splits"]) or "-", g["text"]))
    L += ["", "> advisory：吸附容差 %.2fs、镜长上限 %.1fs 为建议值；采纳与否则归剪辑席。"
          % (SNAP_TOL, MAX_SHOT), ""]
    return "\n".join(L)


def selftest():
    beats_doc = {"beats": [[0.5, 1], [1.0, 2], [1.5, 3], [2.0, 4], [2.5, 1], [3.0, 2],
                           [3.5, 3], [4.0, 4], [4.5, 1], [5.0, 2], [5.5, 3], [6.0, 4],
                           [6.5, 1], [7.0, 2]],
                 "downbeats": [0.5, 2.0, 4.0, 6.0], "n_beats": 14, "n_downbeats": 4,
                 "duration_sec": 7.2}
    cal = [{"t0": 0.52, "t1": 1.48, "text": "A", "approx": False},     # 双边界吸附
           {"t0": 2.30, "t1": 3.35, "text": "B", "approx": False},     # 2.30 不吸附(0.30>0.10)
           {"t0": None, "t1": None, "text": "C", "approx": True},      # 未定时
           {"t0": 3.50, "t1": 7.00, "text": "D", "approx": False}]     # 3.5s 超限需切
    doc = build("TEST", beats_doc, cal)
    assert doc["bpm_median"] == 120.0, doc["bpm_median"]
    g = doc["grid"]
    assert g[0]["snapped"] and abs(g[0]["t0_used"] - 0.5) < 1e-9 and abs(g[0]["t1_used"] - 1.5) < 1e-9
    assert not g[1]["snapped"] and abs(g[1]["t0_used"] - 2.30) < 1e-9
    assert g[2]["t0"] is None and g[2]["splits"] == []
    assert g[3]["splits"], g[3]
    assert all(p in [b[0] for b in beats_doc["beats"]] for p in g[3]["splits"])
    assert doc["summary"]["lines_untimed"] == 1
    # 幂等：同输入两次构建字节恒等
    a = json.dumps(build("TEST", beats_doc, cal), ensure_ascii=False, sort_keys=True)
    b = json.dumps(build("TEST", beats_doc, cal), ensure_ascii=False, sort_keys=True)
    assert a == b
    print("selftest: 7/7 PASS")
    return 0


def matrix():
    """POOL-0018/0019 就绪矩阵：words/beats/calibrated/shotgrid 四件在位性（幂等，无墙钟）。"""
    rows = []
    for s in SONGS:
        r = {"song": s}
        for kind, suffix in (("words", "-words.json"), ("beats", "-beats.json"),
                             ("calibrated", "-calibrated.json"), ("shotgrid", "-shotgrid.json")):
            p = os.path.join(ANC, s + suffix)
            r[kind] = os.path.getsize(p) if os.path.exists(p) else 0
        r["ready"] = all(r[k] > 0 for k in ("words", "beats", "calibrated", "shotgrid"))
        rows.append(r)
    doc = {"stage": "POOL-0018(words)+POOL-0019(beats) first-batch-7 readiness",
           "version": VERSION,
           "machine": "bm-b", "rows": rows,
           "ready_count": sum(1 for r in rows if r["ready"]),
           "total": len(rows),
           "note": "audio supply = 7/7 staged; remaining 34 album tracks have no source audio on this node"}
    out = os.path.join(BASE, "POOL-0018-0019-anchor-matrix.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("MATRIX ready=%d/%d -> %s" % (doc["ready_count"], doc["total"], os.path.basename(out)))
    for r in rows:
        print("  %s words=%d beats=%d cal=%d grid=%d %s"
              % (ascii(r["song"]), r["words"], r["beats"], r["calibrated"], r["shotgrid"],
                 "READY" if r["ready"] else "GAP"))
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--matrix" in argv:
        return matrix()
    only = [a for a in argv[1:] if not a.startswith("-")]
    targets = [s for s in SONGS if not only or s in only]
    done, miss = 0, []
    for s in targets:
        bp = os.path.join(ANC, s + "-beats.json")
        cp = os.path.join(ANC, s + "-calibrated.json")
        if not (os.path.exists(bp) and os.path.exists(cp)):
            miss.append({"song": s, "beats": os.path.exists(bp), "calibrated": os.path.exists(cp)})
            continue
        doc = build(s, json.load(open(bp, encoding="utf-8")),
                    json.load(open(cp, encoding="utf-8")))
        with open(os.path.join(ANC, s + "-shotgrid.json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        with open(os.path.join(ANC, s + "-shotgrid.md"), "w", encoding="utf-8") as f:
            f.write(emit_md(doc))
        done += 1
        print("SHOTGRID %s lines=%d snapped=%d split=%d bpm=%s"
              % (ascii(s), doc["summary"]["lines"], doc["summary"]["lines_snapped"],
                 doc["summary"]["lines_need_split"], doc["bpm_median"]))
    print(json.dumps({"built": done, "missing": miss}, ensure_ascii=False))
    return 0 if done else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))