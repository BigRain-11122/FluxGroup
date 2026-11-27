# -*- coding: utf-8 -*-
"""deai_metrics.py — 去 AI 感七项机检（DE-AI-PLAYBOOK-v1 §四）。

为什么有它：AI 感不是玄学，是四层物理偏差（高频缺失/光学不成立/噪声谱不对/统计过完美）。
本脚本只量「能机器量的那部分」，判不了的明确标人判，不假装机判过了。

七项指标：
  M1 noise_sigma   高通残差中位绝对偏差（传感器噪声底）
  M2 hf_ratio      高频（>0.35 cyc/px）能量占比（微纹理量）
  M3 spec_slope    径向功率谱 log-log 斜率（自然像 ≈ -2）
  M4 nyquist_peak  0.42-0.50 环 / 0.20-0.30 环 能量比（重采样棋盘伪影）
  M5 chroma_noise  色度高通 / 亮度高通（CFA 与色噪）
  M6 lap_var       拉普拉斯方差（整体锐度）
  M7 clip_ratio    高光/死黑裁剪占比

阈值不拍脑袋：先 --calibrate 用真实照片集出基线（均值/标准差），偏离 ≥2σ 才判 SUSPECT。

用法：
  python Tools/deai_metrics.py calibrate <real_dir> --out baseline.json
  python Tools/deai_metrics.py check <file|dir> [--baseline baseline.json] [--json out.json]
  python Tools/deai_metrics.py selftest
退出码：0 PASS / 1 有 SUSPECT / 2 输入错误 / 3 依赖缺失
"""
import argparse
import json
import os
import sys

try:
    import cv2
    import numpy as np
except ImportError:
    print("[BLOCKED] 需要 opencv-python 与 numpy", file=sys.stderr)
    raise SystemExit(3)

SIZE = 1024
IMG = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
VID = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
Z = 2.0

# AI 方向：-1=偏低像 AI，+1=偏高像 AI，0=双向都算异常
DIRECTION = {
    "noise_sigma": -1,
    "hf_ratio": -1,
    "spec_slope": 0,
    "nyquist_peak": 1,
    "chroma_noise": -1,
    "lap_var": 0,
    "clip_ratio": 1,
}
LABEL = {
    "noise_sigma": "M1 噪声底",
    "hf_ratio": "M2 高频占比",
    "spec_slope": "M3 谱斜率",
    "nyquist_peak": "M4 奈奎斯特峰",
    "chroma_noise": "M5 色噪比",
    "lap_var": "M6 锐度",
    "clip_ratio": "M7 裁剪占比",
}


def load_square(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    if min(h, w) < SIZE:
        s = SIZE / float(min(h, w))
        img = cv2.resize(img, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_CUBIC)
    h, w = img.shape[:2]
    y0, x0 = (h - SIZE) // 2, (w - SIZE) // 2
    return img[y0:y0 + SIZE, x0:x0 + SIZE]


def _hp(x):
    f = x.astype(np.float32)
    return f - cv2.medianBlur(x, 3).astype(np.float32)


def noise_sigma(gray):
    # 用均值而非中位：studio 白底/大平场会把中位压成 0，指标就废了
    return float(np.abs(_hp(gray)).mean())


def radial(gray):
    g = gray.astype(np.float32) / 255.0
    g = g - g.mean()
    win = np.hanning(g.shape[0])[:, None] * np.hanning(g.shape[1])[None, :]
    F = np.abs(np.fft.fft2(g * win)) ** 2
    F = np.fft.fftshift(F)
    h, w = F.shape
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((y - cy) ** 2 + (x - cx) ** 2) / (min(h, w) / 2.0)
    return r, F


def spectrum_stats(gray):
    r, F = radial(gray)
    tot = float(F[(r > 0.02) & (r < 0.5)].sum()) or 1e-9
    hf = float(F[r > 0.35].sum()) / tot
    nyq = float(F[(r >= 0.42) & (r <= 0.5)].mean()) / (float(F[(r >= 0.20) & (r <= 0.30)].mean()) or 1e-9)

    rs, ps = [], []
    for lo in np.arange(0.05, 0.45, 0.05):
        m = (r >= lo) & (r < lo + 0.05)
        if m.sum() == 0:
            continue
        v = float(F[m].mean())
        if v <= 0:
            continue
        rs.append(np.log(lo + 0.025))
        ps.append(np.log(v))
    slope = float(np.polyfit(rs, ps, 1)[0]) if len(rs) >= 3 else float("nan")
    return hf, nyq, slope


def metrics(path, square=None):
    img = square if square is not None else load_square(path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hf, nyq, slope = spectrum_stats(gray)

    ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb).astype(np.float32)
    yh = _hp(ycc[:, :, 0].astype(np.uint8))
    ch = 0.5 * (np.abs(_hp(ycc[:, :, 1].astype(np.uint8))).mean() +
                np.abs(_hp(ycc[:, :, 2].astype(np.uint8))).mean())
    cn = float(ch / (np.abs(yh).mean() or 1e-9))

    n = gray.size
    clip = float(((gray >= 250).sum() + (gray <= 5).sum()) / float(n))
    return {
        "noise_sigma": round(noise_sigma(gray), 4),
        "hf_ratio": round(hf, 6),
        "spec_slope": round(slope, 4),
        "nyquist_peak": round(nyq, 4),
        "chroma_noise": round(cn, 4),
        "lap_var": round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 2),
        "clip_ratio": round(clip, 5),
    }


def frames_from_video(path, n=6):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    out = []
    for i in range(n):
        idx = int((i + 0.5) * total / n) if total else i
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = cap.read()
        if not ok:
            continue
        h, w = fr.shape[:2]
        if min(h, w) < SIZE:
            s = SIZE / float(min(h, w))
            fr = cv2.resize(fr, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC)
        h, w = fr.shape[:2]
        out.append(fr[(h - SIZE) // 2:(h - SIZE) // 2 + SIZE, (w - SIZE) // 2:(w - SIZE) // 2 + SIZE])
    cap.release()
    return out


def measure_one(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in VID:
        frs = frames_from_video(path)
        if not frs:
            return None
        rows = [metrics(path, f) for f in frs]
        rows = [r for r in rows if r]
        return {k: round(float(np.mean([r[k] for r in rows])), 5) for k in rows[0]} if rows else None
    return metrics(path)


def iter_files(target):
    if os.path.isdir(target):
        for base, _, files in os.walk(target):
            for fn in files:
                if os.path.splitext(fn)[1].lower() in (IMG | VID):
                    yield os.path.join(base, fn)
    else:
        yield target


def calibrate(real_dir, out):
    keys = list(DIRECTION)
    vals = {k: [] for k in keys}
    n = 0
    for p in iter_files(real_dir):
        m = measure_one(p)
        if not m:
            continue
        n += 1
        for k in keys:
            if isinstance(m.get(k), (int, float)) and m[k] == m[k]:
                vals[k].append(m[k])
    if n < 8:
        print(f"[FAIL] 真实样本仅 {n} 张，基线不可信（需 ≥8，建议 ≥30）", file=sys.stderr)
        return 2
    base = {"n": n, "dir": os.path.abspath(real_dir), "metrics": {}}
    for k in keys:
        arr = np.asarray(vals[k], dtype=np.float64)
        base["metrics"][k] = {"mean": round(float(arr.mean()), 6),
                              "std": round(float(arr.std() or 1e-9), 6)}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
    print(f"基线 → {out}（n={n}）")
    for k in keys:
        print(f"  {LABEL[k]:<14} mean={base['metrics'][k]['mean']:<10} std={base['metrics'][k]['std']}")
    return 0


def judge(m, base):
    rows, suspect = [], []
    for k, d in DIRECTION.items():
        if k not in m or k not in base["metrics"]:
            continue
        mean, std = base["metrics"][k]["mean"], base["metrics"][k]["std"]
        z = (m[k] - mean) / std
        bad = abs(z) >= Z if d == 0 else (z <= -Z if d < 0 else z >= Z)
        if bad:
            suspect.append(k)
        rows.append({"metric": k, "value": m[k], "z": round(z, 2), "bad": bad})
    return rows, suspect


def cmd_check(target, baseline, out_json):
    base = None
    if baseline and os.path.isfile(baseline):
        with open(baseline, encoding="utf-8") as f:
            base = json.load(f)
    results = []
    worst = 0
    for p in iter_files(target):
        m = measure_one(p)
        if not m:
            print(f"[skip] {p}")
            continue
        if base:
            rows, suspect = judge(m, base)
        else:
            rows, suspect = [], []
        results.append({"file": p, "metrics": m, "rows": rows, "suspect": suspect})
        tag = "PASS" if (not base or not suspect) else "SUSPECT"
        n_bad = len(suspect)
        worst = max(worst, n_bad)
        print(f"{tag:<8} {os.path.basename(p)}  bad={n_bad} "
              f"noise={m['noise_sigma']} hf={m['hf_ratio']} slope={m['spec_slope']} "
              f"nyq={m['nyquist_peak']} chroma={m['chroma_noise']} lap={m['lap_var']}")
        for r in rows:
            if r["bad"]:
                print(f"         └ {LABEL[r['metric']]} z={r['z']}")
    if not base:
        print("\n[note] 未提供基线：只报数不判。先 calibrate 真实照片集。")
    else:
        print(f"\n人判仍需: 皮肤蜡质 / 过对称 / 眼神光 / 手指 / 调色艳俗（本脚本不判）")
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({"baseline": baseline, "items": results}, f, ensure_ascii=False, indent=1)
        print(f"报告 → {out_json}")
    return 0 if (not base or worst == 0) else 1


def selftest():
    """正例（有纹理有噪声）与反例（过度平滑）必须分开——分不开=闸是假闸。"""
    rng = np.random.default_rng(7)
    base = np.zeros((SIZE, SIZE, 3), np.uint8)
    base[:] = (120, 140, 160)
    tex = base.copy()
    blob = rng.normal(0, 18, (SIZE, SIZE, 1)).repeat(3, axis=2)
    tex = np.clip(tex.astype(np.float32) + blob, 0, 255).astype(np.uint8)
    tex = cv2.GaussianBlur(tex, (3, 3), 0)
    smooth = cv2.GaussianBlur(base, (31, 31), 0)

    mt = metrics("synthetic_real", tex)
    ms = metrics("synthetic_ai", smooth)
    fails = []
    if not mt["noise_sigma"] > ms["noise_sigma"] * 2:
        fails.append(f"M1 未分离（real {mt['noise_sigma']} vs smooth {ms['noise_sigma']}）")
    if not mt["hf_ratio"] > ms["hf_ratio"] * 2:
        fails.append(f"M2 未分离（real {mt['hf_ratio']} vs smooth {ms['hf_ratio']}）")
    # 加颗粒后必须回升（后期链是否真的在补 L3）
    grained = np.clip(tex.astype(np.float32) + rng.normal(0, 10, tex.shape), 0, 255).astype(np.uint8)
    mg = metrics("synthetic_grained", grained)
    if not mg["noise_sigma"] > mt["noise_sigma"]:
        fails.append("加颗粒后 M1 未上升——颗粒注入无效")

    for f in fails:
        print(f"[FAIL] {f}")
    if fails:
        return 1
    print(f"[PASS] M1 real={mt['noise_sigma']} smooth={ms['noise_sigma']} grain={mg['noise_sigma']} | "
          f"M2 real={mt['hf_ratio']} smooth={ms['hf_ratio']} | slope={mt['spec_slope']}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="去 AI 感七项机检")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("calibrate"); s.add_argument("real_dir"); s.add_argument("--out", required=True)

    s = sub.add_parser("check"); s.add_argument("target")
    s.add_argument("--baseline"); s.add_argument("--json")

    sub.add_parser("selftest")
    a = ap.parse_args(argv)

    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "calibrate":
        return calibrate(a.real_dir, a.out)
    return cmd_check(a.target, a.baseline, a.json)


if __name__ == "__main__":
    sys.exit(main())
