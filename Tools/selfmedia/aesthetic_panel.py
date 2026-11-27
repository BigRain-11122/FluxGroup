#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aesthetic_panel.py — MV 美学专家席：机检先行 + 逐席证据包 + 记分卡。

为什么（CEO 2026-11-25「不仅要工具，还要美学技能和专家」）：
  专家评审以前靠会话临时写提示词，判据散落、每次不一样。这个工具把
  ① 席位判据（cph4/agents/seats/mv-aesthetic-seats.json）
  ② 机器可测的那一半（镜长/切点/黑帧/冻结/清晰度断层/音频）
  ③ 逐席证据包（每席只拿到自己该看的数字与图）
  固化成一次可复跑的动作：`python Tools/selfmedia/aesthetic_panel.py --film X.mp4`
产物落 <out>/ ：EVIDENCE.md（机检）+ seats/*.md（逐席提示词）+ SCORECARD.md（待填）

用法：
  --film <mp4>  --out <dir>  [--seats director,editor,...] [--edl <EDIT-PLAN.json>]
  [--audio]
Exit: 0 正常；2 输入缺失
"""
import argparse
import json
import os
import subprocess
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEATS = os.path.join(ROOT, "cph4", "agents", "seats", "mv-aesthetic-seats.json")
FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FP = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"


def probe(p):
    o = subprocess.run([FP, "-v", "error", "-show_entries",
                        "stream=nb_read_frames,width,height,r_frame_rate:format=duration",
                        "-of", "json", p], capture_output=True, text=True).stdout
    d = json.loads(o)
    st = (d.get("streams") or [{}])[0]
    return {"dur": float(d["format"]["duration"]),
            "w": st.get("width"), "h": st.get("height"),
            "fps": st.get("r_frame_rate")}


def per_frame_stats(p, work):
    """逐帧亮度/清晰度（抽样 4fps 省时），用于黑帧/冻结/断层。"""
    raw = os.path.join(work, "_frames.raw")
    subprocess.run([FF, "-y", "-i", p, "-vf", "fps=4,scale=320:-2,format=gray",
                    "-c:v", "rawvideo", "-f", "rawvideo", raw], capture_output=True)
    import numpy as np
    a = np.fromfile(raw, dtype=np.uint8)
    for h in range(120, 400, 2):
        if a.size % (320 * h) == 0 and 200 * (320 * h) <= a.size <= 200000 * (320 * h):
            pass
    # 由宽度 320 反推高度：找能被整除且比例接近 16:9 的高度
    per = None
    for h in range(100, 500):
        if a.size % (320 * h) == 0:
            cand = 320 * h
            if 400 * cand <= a.size <= 3000 * cand:
                per = cand
                break
    if not per:
        return None
    n = a.size // per
    f = a[:n * per].reshape(n, per).astype("float32")
    luma = f.mean(axis=1)
    lap = (((f[:, 1:-1] * 4 - f[:, :-2] - f[:, 2:]) / 255.0) ** 2).mean(axis=1) * 1000
    d = np.abs(np.diff(f, axis=0)).mean(axis=1)
    return luma, lap, d, 4.0


def audio_stats(p):
    r = subprocess.run([FF, "-hide_banner", "-i", p, "-af", "ebur128=peak=true",
                        "-f", "null", "NUL"], capture_output=True, text=True, errors="replace")
    s = r.stderr
    import re
    out = {}
    m = re.findall(r"(?m)^\s*I:\s+(-?[\d.]+) LUFS", s)
    if m:
        out["lufs"] = float(m[-1])
    m = re.findall(r"(?m)^\s*Peak:\s+(-?[\d.]+) dBFS", s)
    if m:
        out["true_peak"] = float(m[-1])
    return out


def detect_cuts(p, work, fps=24.0):
    """按帧差找切点（每帧），返回切点时间列表。"""
    raw = os.path.join(work, "_cut.raw")
    subprocess.run([FF, "-y", "-i", p, "-vf", "scale=256:-2,format=gray",
                    "-c:v", "rawvideo", "-f", "rawvideo", raw], capture_output=True)
    import numpy as np
    a = np.fromfile(raw, dtype=np.uint8)
    per = None
    for h in range(100, 500):
        if a.size % (256 * h) == 0:
            cand = 256 * h
            if 400 * cand <= a.size <= 20000 * cand:
                per = cand
                break
    n = a.size // per
    f = a[:n * per].reshape(n, per).astype("float32")
    d = np.abs(np.diff(f, axis=0)).mean(axis=1)
    raw = [i / fps for i in range(1, len(d)) if d[i] > 12]
    # 合并碎镜：相邻切点间隔 <0.6s 视为假切（推近/淡入淡出/闪帧）
    cuts = []
    last = 0.0
    for c in raw:
        if c - last >= 0.6:
            cuts.append(round(c, 3))
            last = c
    return cuts, fps


def build(outdir, film, seats, edl=None, do_audio=True):
    os.makedirs(outdir, exist_ok=True)
    work = os.path.join(outdir, "_work")
    os.makedirs(work, exist_ok=True)
    reg = json.load(open(SEATS, encoding="utf-8"))
    by_id = {s["id"]: s for s in reg["seats"]}
    want = [s.strip() for s in seats.split(",")] if seats else list(by_id)

    info = probe(film)
    L = []
    L.append("# 机检证据（aesthetic_panel 自动生成）")
    L.append("")
    L.append("片源：`%s`" % film)
    L.append("")
    L.append("| 项 | 值 |")
    L.append("|---|---|")
    L.append("| 分辨率 | %s×%s |" % (info["w"], info["h"]))
    L.append("| 时长 | %.2f s |" % info["dur"])
    L.append("| 帧率 | %s |" % info["fps"])

    # 切点与镜长
    try:
        cuts, fps = detect_cuts(film, work)
        bounds = [0.0] + cuts + [info["dur"]]
        lens = [round(bounds[i + 1] - bounds[i], 3) for i in range(len(bounds) - 1)]
        import statistics
        L.append("| 切点数 | %d |" % len(cuts))
        L.append("| 镜数 | %d |" % len(lens))
        L.append("| 镜长 均值/中位/最短/最长 | %.2f / %.2f / %.2f / %.2f s |"
                 % (statistics.mean(lens), statistics.median(lens), min(lens), max(lens)))
        L.append("| 镜长方差 | %.3f |" % statistics.pvariance(lens))
        third = max(1, len(lens) // 3)
        head = statistics.mean(lens[:third])
        mid = statistics.mean(lens[third:2 * third])
        tail = statistics.mean(lens[2 * third:])
        L.append("| 首/中/末三段均长 | %.2f / %.2f / %.2f s（末段应小于中段） |" % (head, mid, tail))
        # 同人连镜（若给了 EDL 才能判角色）
        if edl and os.path.exists(edl):
            plan = json.load(open(edl, encoding="utf-8")).get("plan", [])
            run = 1
            runs = []
            for i in range(1, len(plan)):
                if plan[i].get("id") == plan[i - 1].get("id"):
                    run += 1
                else:
                    if run >= 3:
                        runs.append((plan[i - run]["t0"], plan[i - 1]["t1"], plan[i - 1].get("id"), run))
                    run = 1
            if run >= 3:
                runs.append((plan[-run]["t0"], plan[-1]["t1"], plan[-1].get("id"), run))
            L.append("| 同镜号连用>=3 段 | %d %s |" % (len(runs), runs[:3] if runs else ""))
    except Exception as e:
        L.append("| 切点分析 | 失败 %s |" % e)

    # 亮度/冻结
    try:
        st = per_frame_stats(film, work)
        if st:
            luma, lap, d, srate = st
            import numpy as np
            L.append("| YAVG 均值/最小 | %.1f / %.1f |" % (luma.mean(), luma.min()))
            L.append("| 欠曝帧(<12) | %d |" % int((luma < 12).sum()))
            frozen = 0
            run = 0
            for v in d:
                if v < 0.35:
                    run += 1
                else:
                    frozen = max(frozen, run)
                    run = 0
            L.append("| 最长冻结(帧@4fps) | %d |" % frozen)
            L.append("| 清晰度 lap 均值/最小/最大 | %.1f / %.1f / %.1f |"
                     % (lap.mean(), lap.min(), lap.max()))
    except Exception as e:
        L.append("| 逐帧统计 | 失败 %s |" % e)

    if do_audio:
        try:
            a = audio_stats(film)
            L.append("| 音频 | %s |" % (json.dumps(a, ensure_ascii=False)))
        except Exception as e:
            L.append("| 音频 | 失败 %s |" % e)

    open(os.path.join(outdir, "EVIDENCE.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    # 长片分段（多模态一次吃不下 200s+；每段 <=78s，按段送审）
    segdir = os.path.join(outdir, "segments")
    segments = []
    if info["dur"] > 90:
        os.makedirs(segdir, exist_ok=True)
        n = int(-(-info["dur"] // 78))
        for k in range(n):
            a = k * 78.0
            b = min(info["dur"], a + 78.0)
            if b - a < 2.0:
                break
            sp = os.path.join(segdir, "seg%02d_%03.0f-%03.0f.mp4" % (k + 1, a, b))
            subprocess.run([FF, "-y", "-ss", "%.2f" % a, "-t", "%.2f" % (b - a),
                            "-i", film, "-vf", "scale=720:-2",
                            "-c:v", "libx264", "-crf", "33", "-preset", "veryfast",
                            "-an", sp], capture_output=True)
            segments.append({"k": k + 1, "t0": round(a, 2), "t1": round(b, 2),
                             "path": os.path.relpath(sp, outdir)})
        with open(os.path.join(outdir, "SEGMENTS.json"), "w", encoding="utf-8") as f:
            json.dump(segments, f, ensure_ascii=False, indent=1)
        with open(os.path.join(outdir, "EVIDENCE.md"), "a", encoding="utf-8") as f:
            f.write("\n## 分段（多模态一次吃不下长片，按段送审）\n\n")
            for sg in segments:
                f.write("- seg%02d：%0.1f–%0.1f s → `%s`\n" % (sg["k"], sg["t0"], sg["t1"], sg["path"]))

    # 逐席提示词
    sdir = os.path.join(outdir, "seats")
    os.makedirs(sdir, exist_ok=True)
    for sid in want:
        s = by_id.get(sid)
        if not s:
            continue
        P = []
        P.append("# 席位提示词 · %s（%s）" % (s["name"], sid))
        P.append("")
        P.append("**视角**：%s" % s["lens"])
        P.append("")
        P.append("## 判据（逐条打分，0-10，必须给时间码）")
        for i, r in enumerate(s["rubric"], 1):
            P.append("%d. %s" % (i, r))
        P.append("")
        if s.get("dialogue"):
            P.append("**本轮要辩的点**：%s" % s["dialogue"])
            P.append("")
        P.append("## 机检证据（先看数字，再看画面）")
        P.append("同目录 `../EVIDENCE.md`；长片已切段见 `../segments/`（每段 <=78s，逐段送审再汇总）。")
        P.append("")
        P.append("## 输出格式")
        P.append("每条：`判据N: 分数 · 理由(时间码)`；末尾 `TOP3 必改` + `seat_verdict = PASS / CONDITIONAL / FAIL`。")
        open(os.path.join(sdir, sid + ".md"), "w", encoding="utf-8").write("\n".join(P) + "\n")

    # 记分卡
    K = ["# 评审记分卡", "", "| 席位 | 判定 | 关键扣分项 | 修复归属 |", "|---|---|---|---|"]
    for sid in want:
        s = by_id.get(sid)
        if s:
            K.append("| %s（%s） | （待填） | | |" % (s["name"], sid))
    open(os.path.join(outdir, "SCORECARD.md"), "w", encoding="utf-8").write("\n".join(K) + "\n")

    print("PANEL ready -> %s" % outdir)
    print("  EVIDENCE.md / seats×%d / SCORECARD.md" % len(want))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--seats", default="")
    ap.add_argument("--edl", default="")
    ap.add_argument("--no-audio", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.film):
        print("FATAL film not found:", a.film)
        return 2
    out = a.out or os.path.join(ROOT, "cph4", "fleet", "selfmedia", "panel",
                                os.path.splitext(os.path.basename(a.film))[0])
    return build(out, a.film, a.seats, a.edl, not a.no_audio)


if __name__ == "__main__":
    sys.exit(main())
