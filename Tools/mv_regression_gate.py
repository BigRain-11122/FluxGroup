#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_regression_gate.py — 跑 REGRESSION-LEDGER，防止"修好的能力被下一次重建洗掉"。

为什么：MV-DEFINITION-OF-DONE-v1 §八 在 2026-11-05 就要求建回归台账，20 天没建。
后果实证（2026-11-25 复盘）：
  · v7 修好的音轨真峰（-1.1 dBTP）在 v13 用 -c:a copy 又回到 +2.1 dBTP
  · 重排脚本 setpts 系数写反 → 30s 变 22.33s，但没人发现，因为没人跑"帧数断言"
  · v13 三版切点全是 v5 旧结构，因为没人跑"剪辑表对账"

用法：
  # 重建/重剪之前：跑上一版的台账，全绿才开工
  python Tools/mv_regression_gate.py --film prev.mp4 --edl EDL.json --expect-frames 720

  # 出片之前：跑新版的台账
  python Tools/mv_regression_gate.py --film new.mp4 --edl EDL.json --expect-frames 720 --json out.json

  # 只跑某些条目
  python Tools/mv_regression_gate.py --film X.mp4 --only R-01,R-07

Exit 0 = 全绿；1 = 有条目 FAIL；2 = 输入缺失。
manual 条目统一记 SKIP（不计 FAIL，但会列出来提示人工跑）。
"""
import argparse
import json
import os
import re
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "Tools", "selfmedia"))

import numpy as np                     # noqa: E402
import shot_qc as SQ                   # noqa: E402  复用块面判据，避免两套阈值

FF = "ffmpeg"
FP = "ffprobe"
DEFAULT_LEDGER = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "REGRESSION-LEDGER.json")

# 素材根候选（跨机路径按尾部重锚，判例：offnode 不算缺口）
POOL_ROOTS = [
    os.path.join(REPO, "media", "mv0001-handover"),
    os.path.join(REPO, "media", "mv-album-001-jay"),
    os.path.join(REPO, "cph4", "fleet", "mv0001-handover"),
    os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "pool"),
]


def probe(p):
    return SQ.probe(p)


def find_asset(src):
    """把 EDL 里的 src 解析到本机；找不到返回 None（不判负）。"""
    if not src:
        return None
    s = src.replace("\\", "/")
    if os.path.isabs(s) and os.path.exists(s):
        return s
    for root in POOL_ROOTS:
        cand = os.path.join(root, s)
        if os.path.exists(cand):
            return cand
    # 按尾部两段重锚
    parts = [x for x in s.split("/") if x and x not in (".", "..")]
    if len(parts) >= 2:
        tail = os.path.join(*parts[-2:])
        for root in POOL_ROOTS:
            for dirpath, _dirs, files in os.walk(root):
                if os.path.basename(tail) in files:
                    cand = os.path.join(dirpath, os.path.basename(tail))
                    if os.path.exists(cand):
                        return cand
    return None


# ---------------- 各 assert_kind 的实现 ----------------
def a_true_peak(film, edl, opts, ent):
    au = SQ.audio_checks(film)
    p = ent.get("params", {})
    fails = []
    lufs = au.get("lufs")
    tp = au.get("true_peak")
    if tp is not None and tp > p.get("max_dbtp", -1.0):
        fails.append("true_peak %.1f dBTP > %.1f" % (tp, p.get("max_dbtp", -1.0)))
    if lufs is not None and abs(lufs - p.get("lufs_target", -14.0)) > p.get("lufs_tol", 1.5):
        fails.append("lufs %.1f 偏离 %.1f" % (lufs, p.get("lufs_target", -14.0)))
    return fails, {"lufs": lufs, "true_peak": tp, "lra": au.get("lra")}


def a_duration_frames(film, edl, opts, ent):
    info = probe(film)
    fails, obs = [], {"dur": round(info["dur"], 3)}
    tol = ent.get("params", {}).get("dur_tol_s", 0.05)
    exp = opts.expect_frames
    if exp:
        r = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-count_frames",
                            "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", film],
                           capture_output=True, text=True)
        try:
            n = int((r.stdout or "0").strip().split(",")[0])
        except Exception:
            n = -1
        obs["frames"] = n
        if n != exp:
            fails.append("帧数 %s ≠ 期望 %d" % (n, exp))
    if edl:
        d = json.load(open(edl, encoding="utf-8"))
        bt = d.get("blocks") or []
        if bt:
            target = float(bt[-1]["t1"])
            obs["edl_end"] = round(target, 3)
            if abs(info["dur"] - target) > tol:
                fails.append("时长 %.3f ≠ 剪辑表 %.3f" % (info["dur"], target))
    return fails, obs


def a_dup_freeze(film, edl, opts, ent):
    """重复/冻结。EDL 标了 allow_static 的块（PNG loop + 呼吸亮度）必须豁免，
    否则每一版都会被静态图判负 —— 这正是 R-03 第一次跑就误报 0.84% 的原因。"""
    p = ent.get("params", {})
    info = probe(film)
    W, H = 160, max(2, int(round(160 * info["h"] / info["w"])))
    fps = 12.0
    fr = SQ.read_frames(film, W, H, fps=fps)
    if fr.size == 0:
        return ["无法解码"], {}
    m = SQ.frame_metrics(fr, fps)
    skip = []
    if edl and os.path.exists(edl):
        d = json.load(open(edl, encoding="utf-8"))
        skip = [(float(b["t0"]), float(b["t1"])) for b in d.get("blocks", [])
                if b.get("allow_static")]

    def in_skip(t, margin=0.15):
        return any(a - margin <= t <= b + margin for a, b in skip)

    # mad[i] 对应第 i+1 帧与第 i 帧之差
    keep = np.array([not in_skip((i + 1) / fps) for i in range(len(m["mad"]))], dtype=bool)
    mad = m["mad"][keep] if keep.size else m["mad"]
    dif = m["diff"][keep] if keep.size else m["diff"]
    dup = float((mad < 0.20).mean()) if mad.size else 0.0
    fmax = run = 0
    for v in dif:
        if v < p.get("freeze_diff", 0.35):
            run += 1
            fmax = max(fmax, run)
        else:
            run = 0
    fails = []
    if dup > p.get("max_dup_ratio", 0.0) + 1e-9:
        fails.append("重复帧 %.2f%% > %.2f%%" % (dup * 100, p.get("max_dup_ratio", 0.0) * 100))
    if fmax > p.get("max_freeze_frames", 0):
        fails.append("最长冻结 %d 帧(12fps) > %d" % (fmax, p.get("max_freeze_frames", 0)))
    return fails, {"dup_ratio": round(dup, 4), "freeze_max": fmax,
                   "static_windows": len(skip)}


def a_era_color(film, edl, opts, ent):
    if not edl:
        return ["缺 EDL，无法分段判时代"], {}
    d = json.load(open(edl, encoding="utf-8"))
    blocks = d.get("blocks") or []
    eras = [(b.get("era"), float(b["t0"]), float(b["t1"])) for b in blocks]
    if not any(e for e, _a, _b in eras):
        return None, {"reason": "EDL 未标 era，本项降级为人工"}
    p = ent.get("params", {})
    info = probe(film)
    W, H = 160, max(2, int(round(160 * info["h"] / info["w"])))
    fps = 8.0
    fr = SQ.read_frames(film, W, H, fps=fps)
    m = SQ.frame_metrics(fr, fps)
    fails, obs = [], {}
    for era, t0, t1 in eras:
        if not era:
            continue
        i0, i1 = int(t0 * fps), min(len(m["rb"]), int(t1 * fps))
        if i1 - i0 < 2:
            continue
        rb = float(m["rb"][i0:i1].mean())
        obs[era] = round(rb, 2)
        if era == "modern" and rb > p.get("modern_max_rb", 5.0):
            fails.append("现代段 R-B %.1f > %.1f" % (rb, p.get("modern_max_rb", 5.0)))
        if era == "ancient" and rb < p.get("ancient_min_rb", 15.0):
            fails.append("古代段 R-B %.1f < %.1f" % (rb, p.get("ancient_min_rb", 15.0)))
    return fails, obs


def a_text_card(film, edl, opts, ent):
    info = probe(film)
    W, H = 160, max(2, int(round(160 * info["h"] / info["w"])))
    fr = SQ.read_frames(film, W, H, fps=8)
    sb = SQ.subtitle_checks(fr, 8)
    p = ent.get("params", {})
    ratio = sb["bottom_bright_frame_ratio"]
    fails = []
    if ratio < p.get("min_bottom_bright_ratio", 0.02):
        fails.append("底部高亮占比 %.1f%% 过低（字卡可能缺失）" % (ratio * 100))
    return fails, sb


def a_cut_edl_match(film, edl, opts, ent):
    if not edl:
        return ["缺 EDL，无法对账"], {}
    d = json.load(open(edl, encoding="utf-8"))
    blocks = d.get("blocks") or []
    want = [float(b["t1"]) for b in blocks[:-1]]
    if not want:
        return ["EDL 无内部切点"], {}
    info = probe(film)
    W, H = 160, max(2, int(round(160 * info["h"] / info["w"])))
    fps = 12.0
    fr = SQ.read_frames(film, W, H, fps=fps)     # 与 auto_cuts 的时间轴必须同一抽样率
    got = SQ.auto_cuts(fr, fps)
    tol = ent.get("params", {}).get("tolerance_s", 0.12)
    hit = sum(1 for w in want if any(abs(g - w) <= tol for g in got))
    ratio = hit / float(len(want))
    min_ratio = ent.get("params", {}).get("min_match_ratio", 0.8)
    fails = []
    if ratio < min_ratio:
        fails.append("切点吻合 %d/%d=%.0f%% < %.0f%%（成片与剪辑表不是同一版）"
                     % (hit, len(want), ratio * 100, min_ratio * 100))
    return fails, {"want": want, "detected": got, "matched": hit,
                   "total": len(want), "ratio": round(ratio, 3)}


def a_asset_pool(film, edl, opts, ent):
    if not edl:
        return ["缺 EDL，无法审素材"], {}
    d = json.load(open(edl, encoding="utf-8"))
    blocks = d.get("blocks") or []
    p = ent.get("params", {})
    pats = [x.lower() for x in p.get("banned_name_patterns", ["fail", "broken", "test"])]
    fails, obs = [], {"checked": 0, "missing": 0, "banned": [], "lowres": []}
    for b in blocks:
        src = b.get("src")
        if not src:
            continue
        obs["checked"] += 1
        low = src.lower()
        base = os.path.basename(low)
        # 名字闸：fail1 / _fail / broken / test 一律不得入剪
        if any(x in base for x in pats):
            fails.append("禁用件入剪：%s（块 %s）" % (src, b.get("i")))
            obs["banned"].append(src)
        path = find_asset(src)
        if not path:
            obs["missing"] += 1
            continue
        try:
            pi = probe(path)
        except Exception:
            continue
        short = min(pi["w"] or 0, pi["h"] or 0)
        if short and short < p.get("min_short_side", 768):
            obs["lowres"].append("%s=%dx%d" % (os.path.basename(path), pi["w"], pi["h"]))
    return fails, obs


def a_block_sharp(film, edl, opts, ent):
    """复用 shot_qc 的分亮度档判据；不给 EDL 时按整片自动切点。"""
    rep = _run_shot_qc(film, edl, mode="block")
    fails = []
    for b in rep["blocks"]:
        for f in b["flags"]:
            if f.startswith("SHARP"):
                fails.append("块 %s(%.2f-%.2f) %s" % (b["i"], b["t0"], b["t1"], f))
    return fails, {"blocks": len(rep["blocks"]), "fail_blocks": len(fails)}


def a_block_bars(film, edl, opts, ent):
    rep = _run_shot_qc(film, edl, mode="block")
    fails = []
    for b in rep["blocks"]:
        for f in b["flags"]:
            if f.startswith("BARS"):
                fails.append("块 %s(%.2f-%.2f) %s" % (b["i"], b["t0"], b["t1"], f))
    return fails, {"blocks": len(rep["blocks"]), "fail_blocks": len(fails)}


def a_lb_density(film, edl, opts, ent):
    rep = _run_shot_qc(film, edl, mode="block")
    lens = [b["dur"] for b in rep["blocks"]]
    if len(lens) < 6:
        return ["块数不足 6，无法判首中末"], {"lens": lens}
    k = len(lens) // 3
    head, mid, tail = (sum(lens[:k]) / k, sum(lens[k:2 * k]) / k,
                       sum(lens[2 * k:]) / max(1, len(lens[2 * k:])))
    obs = {"head": round(head, 2), "mid": round(mid, 2), "tail": round(tail, 2)}
    fails = []
    if ent.get("params", {}).get("tail_must_be_less_than_mid", True):
        if tail >= mid + ent.get("params", {}).get("tolerance_s", 0.15):
            fails.append("末段均长 %.2f ≥ 中段 %.2f（结尾反而变松）" % (tail, mid))
    return fails, obs


def a_av_sync(film, edl, opts, ent):
    r = subprocess.run([FP, "-v", "error", "-print_format", "json",
                        "-show_format", "-show_streams", film],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), {})
    if not a:
        return ["无音频流"], {}
    vd = float(v.get("duration") or 0)
    ad = float(a.get("duration") or 0)
    dlt = abs(vd - ad)
    fails = []
    if dlt > ent.get("params", {}).get("max_delta_s", 0.05):
        fails.append("音画时长差 %.3fs > %.2fs" % (dlt, ent.get("params", {}).get("max_delta_s", 0.05)))
    return fails, {"v_dur": round(vd, 3), "a_dur": round(ad, 3), "delta": round(dlt, 3)}


def a_manual(film, edl, opts, ent):
    return None, {"manual_cmd": ent.get("manual_cmd", "")}


KINDS = {
    "true_peak": a_true_peak,
    "duration_frames": a_duration_frames,
    "dup_freeze": a_dup_freeze,
    "era_color": a_era_color,
    "text_card": a_text_card,
    "cut_edl_match": a_cut_edl_match,
    "asset_pool": a_asset_pool,
    "block_sharp": a_block_sharp,
    "block_bars": a_block_bars,
    "lb_density": a_lb_density,
    "av_sync": a_av_sync,
    "manual": a_manual,
}

_QC_CACHE = {}


def _run_shot_qc(film, edl, mode="block"):
    key = (film, edl, mode)
    if key in _QC_CACHE:
        return _QC_CACHE[key]
    import tempfile
    out = tempfile.mkdtemp(prefix="rtgate_")
    args = ["--film", film, "--out", out, "--mode", mode, "--fps", "8"]
    if edl:
        args += ["--edl", edl]
    old = sys.argv
    try:
        sys.argv = ["shot_qc.py"] + args
        SQ.main()
    finally:
        sys.argv = old
    rep = json.load(open(os.path.join(out, "QC-REPORT.json"), encoding="utf-8"))
    _QC_CACHE[key] = rep
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True)
    ap.add_argument("--edl", default="")
    ap.add_argument("--expect-frames", type=int, default=0)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--only", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    if not os.path.exists(a.film):
        print("FATAL film not found:", a.film)
        return 2
    if not os.path.exists(a.ledger):
        print("FATAL ledger not found:", a.ledger)
        return 2

    led = json.load(open(a.ledger, encoding="utf-8"))
    only = set(x.strip() for x in a.only.split(",") if x.strip())
    rows, fails_total, skips = [], 0, 0

    for ent in led.get("entries", []):
        eid = ent["id"]
        if only and eid not in only:
            continue
        kind = ent.get("assert_kind", "manual")
        fn = KINDS.get(kind)
        if not fn:
            rows.append((eid, ent["name"], "SKIP", "未实现的 assert_kind=%s" % kind, {}))
            skips += 1
            continue
        try:
            fails, obs = fn(a.film, a.edl, a, ent)
        except Exception as e:
            rows.append((eid, ent["name"], "ERROR", "%s: %s" % (type(e).__name__, e), {}))
            fails_total += 1
            continue
        if fails is None:
            rows.append((eid, ent["name"], "SKIP", "人工项：" + ent.get("manual_cmd", ""), obs))
            skips += 1
            continue
        st = "PASS" if not fails else "FAIL"
        if fails:
            fails_total += 1
        rows.append((eid, ent["name"], st, "; ".join(fails) or "ok", obs))

    print("=" * 78)
    print("REGRESSION GATE  %s" % os.path.basename(a.film))
    print("=" * 78)
    for eid, name, st, detail, obs in rows:
        print("%-6s %-24s %-5s %s" % (eid, name, st, detail[:110]))
    verdict = "PASS" if fails_total == 0 else "FAIL"
    print("-" * 78)
    print("VERDICT=%s   FAIL=%d SKIP=%d  (共 %d 条)" % (verdict, fails_total, skips, len(rows)))

    rep = {"film": a.film, "edl": a.edl, "ledger": a.ledger,
           "verdict": verdict, "fail": fails_total, "skip": skips,
           "rows": [{"id": e, "name": n, "status": s, "detail": d, "obs": o}
                    for e, n, s, d, o in rows]}
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".", exist_ok=True)
        json.dump(rep, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("receipt ->", a.json)
    return 0 if fails_total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
