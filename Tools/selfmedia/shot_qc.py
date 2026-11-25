#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shot_qc.py — 块面级 + 组装级双闸质检（CEO 2026-11-25「每个环节每个块面都要严格检查，组装起来更要」）。

两个视图，一个工具：
  --mode block     逐块面严格检查（时长/欠曝/过曝/冻结/重复帧/清晰度/色温/构图重心/黑边）
  --mode assembly  组装级检查（相邻块边界跳变/越轴嫌疑/音画/总账/字幕）
  --mode all       两者都跑（默认）

块面清单来源优先级：
  1) --edl <json>：{"fps":24,"blocks":[{"i":1,"t0":0,"t1":3.4,"desc":"...","src":"..."}]}
  2) --segments <sec,sec,...>：手工切点
  3) 自动切点（帧差阈值）

判据集中在本文件顶部的 THRESH，改动即全局生效；不达标打印 FAIL 行并让退出码非 0。

用法：
  python Tools/selfmedia/shot_qc.py --film X.mp4 --edl edl.json --out <dir> [--strict]
Exit: 0 全 PASS；1 有 WARN/FAIL；2 输入缺失
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = "ffmpeg"
FP = "ffprobe"

# ---------------- 判据（每条都对应一个 CEO 会骂的具体现象） ----------------
THRESH = {
    # 块面
    "dark_yavg": 12.0,          # YAVG<12 记欠曝帧
    "dark_ratio_fail": 0.20,    # 欠曝帧占比 >20% = FAIL（有设计内黑场的块请用 edl 的 allow_dark）
    "hot_yavg": 235.0,          # YAVG>235 记过曝帧
    "hot_ratio_fail": 0.15,
    "freeze_diff": 0.35,        # 相邻帧灰度差 <0.35 记冻结
    "freeze_frames_fail": 12,   # 连续 >=12 帧冻结 = FAIL（按检测 fps 计）
    "dup_ratio_fail": 0.05,     # 像素级近似重复帧占比 >5% = FAIL
    "dur_tol": 0.10,            # 实测块时长 vs EDL 目标 >0.10s = FAIL
    "sharp_ratio_fail": 0.40,   # 本块清晰度 < 全片中位 * 0.40 = FAIL（画质断档）
    "bar_ratio_fail": 0.06,     # 单边黑边宽度占该轴 >6% = FAIL（变形/填充错误）
    # 组装
    "b_yavg_jump": 26.0,        # 相邻块 YAVG 跳变（硬切允许，但 >26 需确认是不是闪曝/黑场衔接）
    "b_rb_jump": 22.0,          # 相邻块 R-B 跳变（色温断档）
    "b_cx_jump": 0.34,          # 构图重心 x 跳变（归一化）
    "b_diff_spike": 46.0,       # 边界帧差尖峰（>46=硬切带爆点，需人眼确认）
    "lufs_target": -14.0,
    "lufs_tol": 1.0,
    "tp_max": -1.0,
}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def probe(p):
    r = sh([FP, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", p])
    d = json.loads(r.stdout or "{}")
    fmt = d.get("format", {})
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    num, den = (v.get("r_frame_rate") or "24/1").split("/")
    return {
        "dur": float(fmt.get("duration") or 0),
        "size": int(fmt.get("size") or 0),
        "w": v.get("width"), "h": v.get("height"),
        "fps": float(num) / float(den or 1),
        "vcodec": v.get("codec_name"), "pix": v.get("pix_fmt"),
        "audio": None if not a else {
            "codec": a.get("codec_name"), "sr": a.get("sample_rate"),
            "ch": a.get("channels"), "dur": a.get("duration"),
        },
    }


def read_frames(p, w, h, fps=None, strict=False):
    """流式读缩略 RGB 帧，返回 (n, h, w, 3) uint8。strict=原生帧率。"""
    vf = "scale=%d:%d:flags=area,format=rgb24" % (w, h)
    if not strict and fps:
        vf = "fps=%s,%s" % (fps, vf)
    cmd = [FF, "-v", "error", "-i", p, "-an", "-vf", vf, "-f", "rawvideo", "-"]
    per = w * h * 3
    buf = bytearray()
    n = 0
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as pr:
        while True:
            chunk = pr.stdout.read(per * 24)
            if not chunk:
                break
            buf.extend(chunk)
            n += len(chunk) // per
    usable = (len(buf) // per) * per
    a = np.frombuffer(bytes(buf[:usable]), dtype=np.uint8)
    return a.reshape(-1, h, w, 3)


def frame_metrics(frames, fps_used):
    """逐帧指标。frames:(n,h,w,3)"""
    n, h, w, _ = frames.shape
    f = frames.astype(np.float32)
    gray = (0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2])
    yavg = gray.reshape(n, -1).mean(1)
    rb = (f[..., 0] - f[..., 2]).reshape(n, -1).mean(1)
    # 清晰度：拉普拉斯能量（水平方向近似）
    lap = (((gray[:, :, 1:-1] * 4 - gray[:, :, :-2] - gray[:, :, 2:]) / 255.0) ** 2).reshape(n, -1).mean(1) * 1000
    # 帧间差
    d = np.abs(np.diff(gray, axis=0)).reshape(max(n - 1, 1), -1).mean(1) if n > 1 else np.array([0.0])
    # 构图重心：亮度平方加权，归一化到 0..1
    wgt = (gray ** 2).reshape(n, -1)
    tot = wgt.sum(1) + 1e-6
    ys, xs = np.mgrid[0:h, 0:w]
    cx = (wgt * xs.reshape(1, -1)).sum(1) / tot / max(w - 1, 1)
    cy = (wgt * ys.reshape(1, -1)).sum(1) / tot / max(h - 1, 1)
    # 重复帧：与前一帧的全图平均绝对差 < 0.20 视为近似重复
    if n > 1:
        mad = np.abs(np.diff(frames.astype(np.int16), axis=0)).reshape(n - 1, -1).mean(1)
    else:
        mad = np.array([999.0])
    return {
        "n": n, "fps_used": fps_used,
        "yavg": yavg, "rb": rb, "lap": lap, "diff": d,
        "cx": cx, "cy": cy, "mad": mad, "gray": gray,
    }


def black_bars(frames):
    """判四条黑边。真黑边=整列/整行几乎全黑：用 99 分位仍 <24 判「该列没有亮点」。
    只看均值会被死黑体系误报（暗场景大面积 <16 但仍有火光/高光），99 分位能区分。
    返回 (left,right,top,bottom) 占比例。"""
    n, h, w = frames.shape[0], frames.shape[1], frames.shape[2]
    g = (0.299 * frames[..., 0] + 0.587 * frames[..., 1] + 0.114 * frames[..., 2]).astype(np.float32)
    col_q99 = np.percentile(g, 99, axis=(0, 1))   # (w,) 时间+纵向合并后的 99 分位
    row_q99 = np.percentile(g, 99, axis=(0, 2))   # (h,)
    edge = 24.0

    left = 0
    for x in range(w):
        if col_q99[x] < edge:
            left += 1
        else:
            break
    right = 0
    for x in range(w - 1, -1, -1):
        if col_q99[x] < edge:
            right += 1
        else:
            break
    top = 0
    for y in range(h):
        if row_q99[y] < edge:
            top += 1
        else:
            break
    bottom = 0
    for y in range(h - 1, -1, -1):
        if row_q99[y] < edge:
            bottom += 1
        else:
            break
    return left / w, right / w, top / h, bottom / h


def auto_cuts(frames, fps_used):
    m = frame_metrics(frames, fps_used)
    d = m["diff"]
    thr = max(12.0, float(np.percentile(d, 96)) if d.size else 12.0)
    cuts, last = [], 0.0
    for i in range(len(d)):
        t = (i + 1) / fps_used
        if d[i] > thr and t - last >= 0.6:
            cuts.append(round(t, 3))
            last = t
    return cuts


def analyze_block(frames, fps_used, target_dur, desc, allow_dark=False, allow_freeze=False,
                  allow_static=False):
    m = frame_metrics(frames, fps_used)
    n = m["n"]
    dur = n / fps_used
    dark_ratio = float((m["yavg"] < THRESH["dark_yavg"]).mean()) if n else 0.0
    hot_ratio = float((m["yavg"] > THRESH["hot_yavg"]).mean()) if n else 0.0
    dup_ratio = float((m["mad"] < 0.20).mean()) if m["mad"].size else 0.0
    # 最长冻结
    freeze_max = run = 0
    for v in m["diff"]:
        if v < THRESH["freeze_diff"]:
            run += 1
            freeze_max = max(freeze_max, run)
        else:
            run = 0
    bars = black_bars(frames) if n else (0, 0, 0, 0)
    res = {
        "desc": desc, "dur": round(dur, 3), "target": target_dur,
        "n": n,
        "yavg": round(float(m["yavg"].mean()), 2),
        "yavg_min": round(float(m["yavg"].min()), 2) if n else None,
        "dark_ratio": round(dark_ratio, 3),
        "hot_ratio": round(hot_ratio, 3),
        "freeze_max": freeze_max,
        "dup_ratio": round(dup_ratio, 3),
        "motion": round(float(m["diff"].mean()), 3) if m["diff"].size else 0.0,
        "sharp": round(float(m["lap"].mean()), 2),
        "rb": round(float(m["rb"].mean()), 2),
        "cx": round(float(m["cx"].mean()), 3),
        "cy": round(float(m["cy"].mean()), 3),
        "bars": [round(x, 4) for x in bars],
        "notes": [],
        "flags": [],
    }
    # 黑边：只有「对侧对称」才是真 letterbox/pillarbox 缺陷；
    # 死黑体系里单侧大片纯黑是构图（火光只照一侧），不能判负。
    l, r, t, b = bars
    if l > THRESH["bar_ratio_fail"] and r > THRESH["bar_ratio_fail"] and abs(l - r) < 0.03:
        res["flags"].append("BARS 左右对称 %.0f%%/%.0f%%" % (l * 100, r * 100))
    elif t > THRESH["bar_ratio_fail"] and b > THRESH["bar_ratio_fail"] and abs(t - b) < 0.03:
        res["flags"].append("BARS 上下对称 %.0f%%/%.0f%%" % (t * 100, b * 100))
    elif max(bars) > 0.10:
        res["notes"].append("单侧暗区 %.0f%%（构图，非黑边）" % (max(bars) * 100))
    if target_dur and abs(dur - target_dur) > THRESH["dur_tol"]:
        res["flags"].append("DUR %.2f≠%.2f" % (dur, target_dur))
    if dark_ratio > THRESH["dark_ratio_fail"] and not allow_dark:
        res["flags"].append("DARK %.0f%%" % (dark_ratio * 100))
    if hot_ratio > THRESH["hot_ratio_fail"]:
        res["flags"].append("HOT %.0f%%" % (hot_ratio * 100))
    if freeze_max >= THRESH["freeze_frames_fail"] and not allow_freeze:
        res["flags"].append("FREEZE %d帧" % freeze_max)
    if dup_ratio > THRESH["dup_ratio_fail"] and not allow_static:
        res["flags"].append("DUP %.0f%%" % (dup_ratio * 100))
    return res


def assembly_checks(blocks, film_dur, pl):
    """相邻块边界 + 总账。"""
    issues = []
    pairs = []
    for a, b in zip(blocks, blocks[1:]):
        dy = b["yavg"] - a["yavg"]
        drb = b["rb"] - a["rb"]
        dcx = b["cx"] - a["cx"]
        dcy = b["cy"] - a["cy"]
        p = {
            "at": round(a["t1"], 3), "from": a["desc"], "to": b["desc"],
            "d_yavg": round(dy, 2), "d_rb": round(drb, 2),
            "d_cx": round(dcx, 3), "d_cy": round(dcy, 3),
            "notes": [],
        }
        if abs(drb) > THRESH["b_rb_jump"]:
            p["notes"].append("色温断档")
        if abs(dcx) > THRESH["b_cx_jump"]:
            p["notes"].append("构图重心大跳（可能越轴/景别突变）")
        if abs(dy) > THRESH["b_yavg_jump"]:
            p["notes"].append("亮度大跳（确认非闪曝）")
        # 越轴嫌疑：两镜都有明确主体重心，且 x 分居中轴两侧
        if abs(a["cx"] - 0.5) > 0.12 and abs(b["cx"] - 0.5) > 0.12 and (a["cx"] - 0.5) * (b["cx"] - 0.5) < 0:
            p["notes"].append("越轴嫌疑（主体左右对调）")
        pairs.append(p)
        if p["notes"]:
            issues.append(p)
    total = round(sum(b["dur"] for b in blocks), 3)
    checks = {
        "sum_blocks": total,
        "film_dur": round(film_dur, 3),
        "sum_delta": round(total - film_dur, 3),
        "pairs": pairs,
        "pair_issues": issues,
    }
    if abs(total - film_dur) > 0.25:
        checks.setdefault("global_flags", []).append(
            "总账不平：Σ块 %.2f vs 成片 %.2f" % (total, film_dur))
    return checks


def audio_checks(p):
    r = sh([FF, "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"])
    s = r.stderr
    out = {}
    m = re.findall(r"(?m)^\s*I:\s+(-?[\d.]+) LUFS", s)
    if m:
        out["lufs"] = float(m[-1])
    m = re.findall(r"(?m)^\s*Peak:\s+(-?[\d.]+) dBFS", s)
    if m:
        out["true_peak"] = float(m[-1])
    m = re.findall(r"(?m)^\s*LRA:\s+(-?[\d.]+) LU", s)
    if m:
        out["lra"] = float(m[-1])
    flags = []
    if "lufs" in out and abs(out["lufs"] - THRESH["lufs_target"]) > THRESH["lufs_tol"]:
        flags.append("响度偏离 %.1f LUFS" % out["lufs"])
    if "true_peak" in out and out["true_peak"] > THRESH["tp_max"]:
        flags.append("真峰削波 %.1f dBTP" % out["true_peak"])
    out["flags"] = flags
    return out


def subtitle_checks(frames, fps_used):
    """底部 18% 区域：高亮像素占比在片中出现过（用于确认字卡/标识在位）。"""
    n, h, w, _ = frames.shape
    band = frames[:, int(h * 0.82):, :, :].astype(np.float32)
    bright = (band.mean(3) > 200).mean(axis=(1, 2))
    frac = float((bright > 0.004).mean())
    return {"bottom_bright_frame_ratio": round(frac, 3), "max": round(float(bright.max()), 4)}


def build_contact(frames, fps_used, t0, t1, out_png, ff=FF):
    """取块内首/中/末三帧拼一条（1x3），供人眼与多模态席位看。"""
    idx = [0, frames.shape[0] // 2, frames.shape[0] - 1]
    h, w = frames.shape[1:3]
    strip = np.concatenate([frames[i] for i in idx], axis=1)
    raw = os.path.join(os.path.dirname(out_png), "_tmp_strip.raw")
    strip.astype(np.uint8).tofile(raw)
    r = subprocess.run([ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", "%dx%d" % (w * 3, h), "-i", raw,
                        "-frames:v", "1", out_png], capture_output=True)
    try:
        os.remove(raw)
    except OSError:
        pass
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True)
    ap.add_argument("--edl", default="")
    ap.add_argument("--segments", default="")   # "3.4,6.0,9.2,..." 内部切点
    ap.add_argument("--out", default="")
    ap.add_argument("--mode", default="all", choices=["block", "assembly", "all"])
    ap.add_argument("--fps", type=float, default=12.0, help="块面统计抽样帧率")
    ap.add_argument("--strict", action="store_true", help="按原生帧率统计（更慢更严）")
    a = ap.parse_args()
    if not os.path.exists(a.film):
        print("FATAL film not found:", a.film)
        return 2

    info = probe(a.film)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                "cph4", "fleet", "selfmedia", "qc",
                                os.path.splitext(os.path.basename(a.film))[0])
    out = os.path.abspath(out)
    os.makedirs(os.path.join(out, "blocks"), exist_ok=True)

    # ---- 块面清单 ----
    fps_used = info["fps"] if a.strict else a.fps
    W, H = 160, max(2, int(round(160 * info["h"] / info["w"])))
    frames = read_frames(a.film, W, H, fps=a.fps, strict=a.strict)
    if frames.size == 0:
        print("FATAL no frames decoded")
        return 2

    edl_blocks = None
    if a.edl and os.path.exists(a.edl):
        edl = json.load(open(a.edl, encoding="utf-8"))
        edl_blocks = edl.get("blocks") or []
        if edl.get("fps"):
            fps_used = float(edl["fps"]) if a.strict else a.fps
    bounds = []
    if edl_blocks:
        bounds = [(float(b["t0"]), float(b["t1"]), b.get("desc", ""),
                   bool(b.get("allow_dark")), bool(b.get("allow_freeze")),
                   bool(b.get("allow_static"))) for b in edl_blocks]
    else:
        cuts = ([float(x) for x in a.segments.split(",") if x.strip()]
                if a.segments else auto_cuts(frames, fps_used))
        edges = [0.0] + cuts + [info["dur"]]
        bounds = [(edges[i], edges[i + 1], "seg%d" % (i + 1), False, False, False)
                  for i in range(len(edges) - 1)]

    # ---- 逐块 ----
    blocks = []
    for k, (t0, t1, desc, allow_dark, allow_freeze, allow_static) in enumerate(bounds, 1):
        i0 = max(0, int(round(t0 * fps_used)))
        i1 = min(frames.shape[0], int(round(t1 * fps_used)))
        if i1 - i0 < 2:
            continue
        sub = frames[i0:i1]
        r = analyze_block(sub, fps_used, round(t1 - t0, 3), desc, allow_dark, allow_freeze,
                          allow_static)
        r.update({"i": k, "t0": round(t0, 3), "t1": round(t1, 3)})
        blocks.append(r)
        if a.mode in ("block", "all"):
            build_contact(sub, fps_used, t0, t1,
                          os.path.join(out, "blocks", "b%02d_%.2f-%.2f.jpg" % (k, t0, t1)))

    # 清晰度断档：只能与「同亮度档」比。Laplacian 是绝对能量，暗镜头天然低，
    # 拿全片中位比会把所有死黑体系镜头判成「糊」（v13b 浮雕 81.6 vs 片中位 250 即此误报）。
    if blocks:
        def band(y):
            return 0 if y < 20 else (1 if y < 35 else 2)
        for k in (0, 1, 2):
            grp = [b for b in blocks if band(b["yavg"]) == k]
            if len(grp) < 2:
                continue
            med = float(np.median([b["sharp"] for b in grp]))
            for b in grp:
                if med > 0 and b["sharp"] < med * THRESH["sharp_ratio_fail"]:
                    b["flags"].append("SHARP 断档 %.1f (YAVG档%d中位 %.1f)" % (b["sharp"], k, med))

    report = {"film": a.film, "probe": info, "fps_used": fps_used,
              "mode": a.mode, "blocks": blocks}
    if a.mode in ("assembly", "all"):
        report["assembly"] = assembly_checks(blocks, info["dur"], info)
        report["audio"] = audio_checks(a.film)
        report["subtitle"] = subtitle_checks(frames, fps_used)

    json.dump(report, open(os.path.join(out, "QC-REPORT.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ---- 人读报告 ----
    L = ["# 块面/组装质检报告", "", "片源：`%s`" % a.film, "",
         "| 项 | 值 |", "|---|---|",
         "| 分辨率 | %s×%s |" % (info["w"], info["h"]),
         "| 时长 | %.3f s |" % info["dur"],
         "| 帧率 | %.3f |" % info["fps"],
         "| 块数 | %d |" % len(blocks),
         "| 统计帧率 | %s |" % ("原生" if a.strict else "%.0f fps" % a.fps), ""]

    if a.mode in ("block", "all"):
        L += ["## 逐块面", "",
              "| # | 区间 | 描述 | 时长 | YAVG | 暗% | 冻结 | 重复% | 运动 | 清晰 | R-B | 重心x | 判定 |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for b in blocks:
            if b["flags"]:
                verdict = "FAIL " + " / ".join(b["flags"])
            elif b.get("notes"):
                verdict = "NOTE " + " / ".join(b["notes"])
            else:
                verdict = "PASS"
            L.append("| %d | %.2f–%.2f | %s | %.2f | %.1f | %.0f%% | %d | %.1f%% | %.2f | %.1f | %.1f | %.2f | %s |"
                     % (b["i"], b["t0"], b["t1"], b["desc"], b["dur"], b["yavg"],
                        b["dark_ratio"] * 100, b["freeze_max"], b["dup_ratio"] * 100,
                        b["motion"], b["sharp"], b["rb"], b["cx"], verdict))
        L.append("")
        L.append("块面接触条（首/中/末帧）：`blocks/`")
        L.append("")

    if a.mode in ("assembly", "all"):
        asm = report["assembly"]
        L += ["## 组装级", "",
              "| 项 | 值 |", "|---|---|",
              "| Σ块时长 | %.3f s |" % asm["sum_blocks"],
              "| 成片时长 | %.3f s |" % asm["film_dur"],
              "| 差值 | %+.3f s |" % asm["sum_delta"], ""]
        if asm.get("global_flags"):
            for g in asm["global_flags"]:
                L.append("- **FAIL** %s" % g)
            L.append("")
        L += ["### 边界对（%d 个）" % len(asm["pairs"]), "",
              "| 切点 | 从 | 到 | ΔY | Δ(R-B) | Δ重心x | 备注 |", "|---|---|---|---|---|---|---|"]
        for p in asm["pairs"]:
            L.append("| %.2f | %s | %s | %+.1f | %+.1f | %+.3f | %s |"
                     % (p["at"], p["from"], p["to"], p["d_yavg"], p["d_rb"], p["d_cx"],
                        " / ".join(p["notes"]) if p["notes"] else "ok"))
        L.append("")
        au = report["audio"]
        L += ["### 音频", "", "`%s`" % json.dumps(au, ensure_ascii=False)]
        if au.get("flags"):
            L.append("")
            for f in au["flags"]:
                L.append("- **FAIL** %s" % f)
        L.append("")
        sb = report["subtitle"]
        L += ["### 字卡/底部信息位", "",
              "- 底部 18%% 区域出现高亮文字帧占比：%.1f%%（max %.3f）"
              % (sb["bottom_bright_frame_ratio"] * 100, sb["max"]), ""]

    fails = sum(len(b["flags"]) for b in blocks)
    if a.mode in ("assembly", "all"):
        fails += len(report["assembly"].get("global_flags", []))
        fails += len(report["assembly"].get("pair_issues", []))
        fails += len(report["audio"].get("flags", []))
    L += ["## 结论", "", "共 **%d** 项告警/失败。" % fails]

    open(os.path.join(out, "QC-REPORT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("QC -> %s" % out)
    print("  块数 %d  告警 %d" % (len(blocks), fails))
    for b in blocks:
        if b["flags"]:
            print("  FAIL b%02d %.2f-%.2f %s :: %s"
                  % (b["i"], b["t0"], b["t1"], b["desc"], " / ".join(b["flags"])))
    if a.mode in ("assembly", "all"):
        for p in report["assembly"].get("pair_issues", []):
            print("  PAIR @%.2f %s -> %s :: %s" % (p["at"], p["from"], p["to"], " / ".join(p["notes"])))
        for f in report["audio"].get("flags", []):
            print("  AUDIO ::", f)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
