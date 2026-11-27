# -*- coding: utf-8 -*-
# wm_diag_r1017.py — 暗水印压缩存活单帧隔离诊断（r1017 全扫 0/235 实锥的病因定位+疗法测试）
# 病因假说：①BGR 三通道全嵌→一半能量在色度→yuv420p 4:2:0 子采样直接抹掉
#           ②x264 量化(含 psy)打掉剩余频域系数
# 疗法候选：A=Y 亮度单通道嵌入（等值三通道嵌入后取均值回写 Y·色度零触碰）
#           B=双嵌强度×2（embed 线性操作·两次叠加=kmeans 分离度翻倍·PSNR 掉 ~6dB）
# 矩阵：{bgr1, bgr2, y1, y2} × {png, crf22_420, crf22_444, crf16_420, crf28_420}
import os, subprocess, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mv_blind_wm_r1017 import embed_frame, extract_frame, wm_bit_len, FF, WM_TEXT

SRC = os.path.join(HERE, "full_mv_v51_proxy.mp4")
IDX = 936
D = os.path.join(HERE, "wm_diag")
os.makedirs(D, exist_ok=True)


def u8(a):
    return a if a.dtype == np.uint8 else np.clip(a, 0, 255).astype(np.uint8)


def load_frame():
    cap = cv2.VideoCapture(SRC)
    cap.set(cv2.CAP_PROP_POS_FRAMES, IDX)
    ok, f = cap.read()
    cap.release()
    assert ok, "load frame failed"
    return f


def y3_of(bgr):
    return cv2.merge([cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)[:, :, 0]] * 3)


def with_y(bgr, emb_y3):
    ycc = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb).copy()
    ycc[:, :, 0] = np.clip(emb_y3.mean(axis=2), 0, 255).astype(np.uint8)
    return cv2.cvtColor(ycc, cv2.COLOR_YCrCb2BGR)


def encode_variants(name, img_bgr):
    png = os.path.join(D, name + ".png")
    cv2.imwrite(png, img_bgr)
    outs = {"png": png}
    for tag, extra in (("crf22_420", ["-crf", "22", "-pix_fmt", "yuv420p"]),
                       ("crf22_444", ["-crf", "22", "-pix_fmt", "yuv444p"]),
                       ("crf16_420", ["-crf", "16", "-pix_fmt", "yuv420p"]),
                       ("crf28_420", ["-crf", "28", "-pix_fmt", "yuv420p"])):
        out = os.path.join(D, "%s_%s.mp4" % (name, tag))
        subprocess.run([FF, "-y", "-i", png, "-c:v", "libx264", "-preset", "veryfast"] + extra + [out],
                       check=True, capture_output=True)
        outs[tag] = out
    return outs


def decode_first(path):
    cap = cv2.VideoCapture(path)
    ok, f = cap.read()
    cap.release()
    assert ok, path
    return f


def psnr(a, b):
    mse = ((a.astype(np.float64) - b.astype(np.float64)) ** 2).mean()
    return 99.0 if mse <= 0 else round(10 * np.log10(255.0 ** 2 / mse), 2)


L = wm_bit_len()
f0 = load_frame()
print("DIAG frame=%d wm_len=%d text=%r" % (IDX, L, WM_TEXT), flush=True)


def try_extract(frame_bgr, ymode):
    probe = y3_of(frame_bgr) if ymode else frame_bgr
    try:
        txt = extract_frame(probe, L)
        return "PASS" if txt == WM_TEXT else "GARBAGE"
    except Exception as e:
        return "ERROR " + str(e)[:36]


def run_row(name, emb_probe_bgr, ymode, out_bgr):
    files = encode_variants(name, out_bgr)
    q = psnr(f0, out_bgr)
    for tag, p in sorted(files.items()):
        frame = cv2.imread(p) if tag == "png" else decode_first(p)
        print("%-5s %-10s %s" % (name, tag, try_extract(frame, ymode)), flush=True)
    print("%-5s PSNR-embed=%.2f dB" % (name, q), flush=True)


# 1) BGR 原生单嵌（现状=已知 crf22_420 失败基线）
run_row("bgr1", None, False, u8(embed_frame(f0)))
# 2) BGR 双嵌（强度x2）
run_row("bgr2", None, False, u8(embed_frame(u8(embed_frame(f0)))))
# 3) Y 单通道单嵌
e = u8(embed_frame(y3_of(f0)))
run_row("y1", None, True, with_y(f0, e))
# 4) Y 单通道双嵌
e = u8(embed_frame(u8(embed_frame(y3_of(f0)))))
run_row("y2", None, True, with_y(f0, e))
print("DIAG-DONE", flush=True)
