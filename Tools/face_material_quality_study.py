# -*- coding: utf-8 -*-
"""素材质量 → LoRA 效果 的相关性分析。

数据来源（两边都是实测，不是估计）：
  效果侧 = 2026-11-17 跑出的跨镜 SFace 中位（同提示词只换场景、LoRA 1.0 自己担脸）
  素材侧 = 各条 LoRA 的训练集逐图特征（人脸像素、清晰度、人脸占比、分辨率、数量、多样性）

目的：回答"什么素材拉回来训练最高效、质量最高"，给采集端定优先级。
"""
import json
import os
import sys

import cv2
import numpy as np

TOOLS = r"C:\Users\sjs20\Desktop\FluxGroup\Tools"
sys.path.insert(0, TOOLS)
import face_lora_prep as GATE  # noqa: E402

TRAIN = r"D:\FluxGroup-Offload\15-training\dataset"
IMG = (".jpg", ".jpeg", ".png", ".webp")

# 2026-11-17 accept 实测（跨镜相似度中位 / 与素材相似度 / 建成张数）
SCORES = {
    "her_mv0001": (0.539, 0.658),
    "T02": (0.572, 0.662),
    "T03": (0.310, 0.489),
    "T04": (0.460, 0.559),
    "T05": (0.541, 0.657),
    "T06": (0.567, 0.684),
    "T07": (0.362, 0.563),
    "T08": (0.451, 0.590),
}


def analyze(name):
    d = os.path.join(TRAIN, name)
    if not os.path.isdir(d):
        return None
    rows = []
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(IMG):
            continue
        p = os.path.join(d, fn)
        img = cv2.imread(p)
        if img is None:
            continue
        h, w = img.shape[:2]
        faces = GATE.detect_faces(img)
        if not faces:
            continue
        f = faces[0]
        fw, fh = f[2], f[3]
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 人脸框可能贴边/越界，切片后为空会让 cv2.Laplacian 直接抛断言
        x0, y0 = max(0, int(f[0])), max(0, int(f[1]))
        x1, y1 = min(w, int(f[0] + fw)), min(h, int(f[1] + fh))
        patch = g[y0:y1, x0:x1]
        rows.append({
            "face_px": min(fw, fh),
            "face_ratio": (fw * fh) / float(w * h),
            "lap": GATE.laplacian_var(patch) if patch.size else 0.0,
            "px": min(w, h),
            "aspect": w / float(h),
            "bright": float(g.mean()),
        })
    if not rows:
        return None
    A = {k: np.array([r[k] for r in rows], dtype=np.float32) for k in rows[0]}
    # 多样性：尺寸/宽高比/亮度三维各自的离散度（越大＝角度/构图/光位越丰富）
    div = float(np.mean([A["px"].std() / max(A["px"].mean(), 1),
                         A["aspect"].std() / max(A["aspect"].mean(), 1e-6),
                         A["bright"].std() / max(A["bright"].mean(), 1e-6)]))
    return {
        "n": len(rows),
        "face_px_med": float(np.median(A["face_px"])),
        "face_px_min": float(A["face_px"].min()),
        "pass_320": float((A["face_px"] >= 320).mean()),
        "face_ratio_med": float(np.median(A["face_ratio"])),
        "lap_med": float(np.median(A["lap"])),
        "lap_ok": float((A["lap"] >= 60).mean()),
        "px_med": float(np.median(A["px"])),
        "diversity": div,
    }


def main():
    print("%-11s %5s %7s %7s %7s %7s %7s %7s  %s" % (
        "LORA", "n", "facePx", "≥320%", "faceR", "lap", "lapOK%", "divers", "跨镜分"))
    print("-" * 92)
    data = []
    for name in SCORES:
        s = analyze(name)
        if not s:
            print("%-11s  (无数据集)" % name)
            continue
        cross, refsim = SCORES[name]
        data.append((name, s, cross))
        print("%-11s %5d %7.0f %6.0f%% %7.3f %7.1f %6.0f%% %7.2f  %.3f"
              % (name, s["n"], s["face_px_med"], 100 * s["pass_320"], s["face_ratio_med"],
                 s["lap_med"], 100 * s["lap_ok"], s["diversity"], cross))

    # 与跨镜分的秩相关（样本少，用 Spearman 更稳）
    if len(data) >= 5:
        print("\n特征 vs 跨镜分（Spearman 秩相关，n=%d）：" % len(data))
        import itertools

        def rank(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            r = [0] * len(v)
            for pos, i in enumerate(order):
                r[i] = pos
            return np.array(r, dtype=np.float32)

        y = rank([c for _, _, c in data])
        for key in ("n", "face_px_med", "pass_320", "face_ratio_med", "lap_med", "lap_ok", "diversity"):
            x = rank([s[key] for _, s, _ in data])
            if x.std() == 0:
                print("  %-14s 无变异" % key)
                continue
            rho = float(np.corrcoef(x, y)[0, 1])
            flag = "强" if abs(rho) >= 0.7 else ("中" if abs(rho) >= 0.4 else "弱")
            print("  %-14s rho=%+.2f  (%s)" % (key, rho, flag))


if __name__ == "__main__":
    main()
