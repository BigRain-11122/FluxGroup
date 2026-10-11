#!/usr/bin/env python3
# video_qc.py -- AI 视频质量三诊（油腻感 / 镜头抖 / 掉帧闪烁）——量化打分，不靠肉眼
#
# 三个可直接测的代理量（都有明确物理含义）：
#   ① 油腻感 OIL   : 高光占比 + 局部对比度 + 高频能量
#        高光占比高 = 过曝/塑料感；局部对比度低 = 磨皮感；高频能量低 = 过度平滑
#   ② 镜头稳 JITTER: 相邻帧光流的【平滑度】
#        真实镜头运动平滑 -> flow 的二阶差分小；AI 抽帧/跳变 -> 尖刺
#   ③ 掉帧/闪烁 DROP: 帧间差分的异常尖刺率 + 重复帧率
#        掉帧表现为"差分突然很大"或"连续两帧几乎相同"
#
# 用法: python Tools/video_qc.py --video <path> [--maxsec 60] [--fps 8]
import argparse, math, os, sys
import numpy as np

def analyze(path, maxsec=60, fps=8, size=(320, 180)):
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    dur = total / src_fps if src_fps else 0
    step = max(1, int(round(src_fps / fps)))
    n_take = int(min(maxsec, dur) * fps)

    frames = []
    idx = 0; taken = 0
    while taken < n_take:
        ok = cap.grab()
        if not ok:
            break
        if idx % step == 0:
            ok, fr = cap.retrieve()
            if not ok:
                break
            fr = cv2.resize(fr, size, interpolation=cv2.INTER_AREA)
            frames.append(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY))
            taken += 1
        idx += 1
    cap.release()
    if len(frames) < 12:
        return {"error": "frames<12", "n": len(frames)}

    F = np.stack(frames).astype(np.float32)
    n = F.shape[0]

    # 不依赖 OpenCV 的滤波 API（5.x 有变更）：用 numpy 自己算，稳且可复现
    # 拉普拉斯（4 邻域核）：局部对比度
    K = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    from scipy.signal import convolve2d
    lap_sum = 0.0
    grad_sum = 0.0
    tot_sum = 0.0
    for i in range(n):
        lap_sum += float(np.abs(convolve2d(F[i], K, mode="valid")).mean())
        gx, gy = np.gradient(F[i])
        grad_sum += float(np.mean(gx * gx + gy * gy))
        tot_sum += float(np.mean(F[i] * F[i]))
    lap = lap_sum / n
    hf_ratio = grad_sum / (tot_sum + 1e-9)

    # ---- ① 油腻感 ----
    hi = float((F > 235).mean())

    # ---- ② 镜头稳（光流平滑度） ----
    flows = []
    for i in range(1, n):
        fl = cv2.calcOpticalFlowFarneback(F[i-1], F[i], None, 0.5, 3, 15, 3, 5, 1.2, 0)
        flows.append(fl)
    # 每帧的全局平移量与旋转近似（用均值流 + 流场标准差）
    mag = np.array([float(np.mean(np.sqrt((f[...,0]**2 + f[...,1]**2)))) for f in flows])
    sdev = np.array([float(np.std(f[...,0]) + np.std(f[...,1])) for f in flows])
    # 平滑度：mag 的二阶差分绝对值的均值（越小越顺）
    d2 = np.abs(np.diff(mag, 2)) if len(mag) > 2 else np.array([0.0])
    jitter = float(np.mean(d2))
    # 流场散乱度：sdev 均值（越大越像"每帧各动各的"）
    scatter = float(np.mean(sdev))

    # ---- ③ 掉帧/闪烁（帧间差分尖刺 + 重复帧） ----
    d = np.abs(np.diff(F, axis=0)).mean(axis=(1, 2))
    dm = float(np.mean(d)); ds = float(np.std(d)) + 1e-9
    spike_rate = float((d > dm + 2.5 * ds).mean())      # 异常大跳变
    dup_rate = float((d < 0.35).mean())                 # 近乎重复帧
    # 差分抖动：帧间差的"抖"（掉帧会让差分忽大忽小）
    diff_jitter = float(np.mean(np.abs(np.diff(d))))

    return {
        "file": os.path.basename(path),
        "src_fps": round(src_fps, 2), "frames_sampled": n, "duration_s": round(dur, 1),
        "OIL_highlight_ratio": round(hi, 4),
        "OIL_local_contrast": round(float(lap), 2),
        "OIL_hf_ratio": round(hf_ratio, 5),
        "CAM_jitter": round(jitter, 4),
        "CAM_scatter": round(scatter, 3),
        "DROP_spike_rate": round(spike_rate, 4),
        "DROP_dup_rate": round(dup_rate, 4),
        "DROP_diff_jitter": round(diff_jitter, 3),
    }


def verdict(r):
    """阈值（外审设定，可调）：给出可执行的判断与建议"""
    v = []
    if r["OIL_highlight_ratio"] > 0.06:
        v.append(("油腻感", "高光占比 %.1f%% 偏高 -> 降高光/加高光压缩，别用 HDR 拉满" % (r["OIL_highlight_ratio"]*100)))
    if r["OIL_local_contrast"] < 6.0:
        v.append(("油腻感", "局部对比度 %.1f 偏低 -> 过度平滑/磨皮，加微对比(Clarity)与胶片颗粒" % r["OIL_local_contrast"]))
    if r["OIL_hf_ratio"] < 0.02:
        v.append(("油腻感", "高频能量占比 %.4f 偏低 -> 细节被抹平，需加颗粒/锐化" % r["OIL_hf_ratio"]))
    if r["CAM_jitter"] > 0.35:
        v.append(("镜头", "光流二阶差分 %.3f 偏大 -> 镜头运动不顺（AI 帧间不一致），需稳定或重拍" % r["CAM_jitter"]))
    if r["CAM_scatter"] > 2.2:
        v.append(("镜头", "流场散乱度 %.2f 偏高 -> 画面各部分各动各的，典型 AI 伪影" % r["CAM_scatter"]))
    if r["DROP_spike_rate"] > 0.06:
        v.append(("掉帧", "差分尖刺率 %.1f%% -> 有跳变/闪烁，需补帧或去闪烁" % (r["DROP_spike_rate"]*100)))
    if r["DROP_dup_rate"] > 0.12:
        v.append(("掉帧", "重复帧率 %.1f%% -> 有效帧率不足，观感卡顿" % (r["DROP_dup_rate"]*100)))
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--maxsec", type=float, default=60)
    ap.add_argument("--fps", type=float, default=8)
    a = ap.parse_args()
    r = analyze(a.video, a.maxsec, a.fps)
    if not r or "error" in r:
        print("分析失败:", r); return
    print("=== %s ===" % r["file"])
    print("源帧率 %.2f fps | 采样 %d 帧 | 时长 %.1fs" % (r["src_fps"], r["frames_sampled"], r["duration_s"]))
    print("油腻感  : 高光占比 %.2f%% | 局部对比度 %.1f | 高频能量占比 %.5f"
          % (r["OIL_highlight_ratio"]*100, r["OIL_local_contrast"], r["OIL_hf_ratio"]))
    print("镜头    : 光流抖 %.4f | 流场散乱 %.3f" % (r["CAM_jitter"], r["CAM_scatter"]))
    print("掉帧    : 尖刺率 %.2f%% | 重复帧率 %.2f%% | 差分抖动 %.2f"
          % (r["DROP_spike_rate"]*100, r["DROP_dup_rate"]*100, r["DROP_diff_jitter"]))
    v = verdict(r)
    print("\n诊断与建议:")
    if not v:
        print("  三项指标均在阈值内")
    for k, s in v:
        print("  [%s] %s" % (k, s))


if __name__ == "__main__":
    main()
