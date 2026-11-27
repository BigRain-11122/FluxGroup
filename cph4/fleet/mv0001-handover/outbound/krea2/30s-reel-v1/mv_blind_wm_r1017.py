# -*- coding: utf-8 -*-
# mv_blind_wm_r1017.py — MV 全片隐形盲水印工具（CEO 令 2026-10-17 11:0x）
# 原话：「MV记得给我打上暗水印 要很小很不明显，但是又能防别人盗版，按水印的内容是 大喵没鱼吃
#        ，不要影响画面，具体怎么弄，你去github看看，研究下」
# 调研结论（2026-10-17 11:1x·GitHub 实查）：
#   主算法=guofei9987/blind_watermark（MIT·14.8k★·DWT-DCT-SVD·盲提取无须原图·
#     抗旋转/裁剪/遮罩/缩放/椒盐/亮度·中文文本支持实证'开源万岁！'·pip blind-watermark）
#   视频落地正法参照=tucaodashen/invisible_video_watermark（其 TEXT_GOUFEI 算法即本库逐帧嵌入·
#     本体为 GUI 框架不引入，管线自建）
# 方案：每 STRIDE 帧嵌一枚密码保护文本水印「大喵没鱼吃」（5 CJK=160bit·kmeans 盲提取）——
#   任何 ≥STRIDE 帧的盗版片段必含标记帧；cv2 逐帧管线（解码→内存嵌入→管道回编码）单代编码、
#   音频流直拷零损；提取端按 stride 扫帧+kmeans 提取+全片投票（盗版取证只需任一标记帧）。
# 用法（comfyui python 运行·库已装）：
#   PY = C:\Users\sjs20\comfyui-krea\ComfyUI_windows_portable\python_embeded\python.exe
#   冒烟:   & $PY mv_blind_wm_r1017.py roundtrip <in.mp4>
#   嵌入:   & $PY mv_blind_wm_r1017.py embed   <in.mp4> <out.mp4> [stride=24] [crf=22] [preset=veryfast]
#   提取:   & $PY mv_blind_wm_r1017.py extract <in.mp4> [stride=24]
#   压测:   & $PY mv_blind_wm_r1017.py stress  <wm.mp4> [stride=24]     # 平台重压两级模拟后提取
#   画质:   & $PY mv_blind_wm_r1017.py psnr   <orig.mp4> <wm.mp4> [stride=24]
#   目检板: & $PY mv_blind_wm_r1017.py board   <orig.mp4> <wm.mp4> [stride=24] [n=3]
import contextlib
import io
import os
import subprocess
import sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2
import numpy as np
from blind_watermark import WaterMark

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
WM_TEXT = "大喵没鱼吃"
P_IMG, P_WM = 20261017, 1110          # 提取密钥（组内私仓正身·泄露即换钥重发）
STRIDE_DEF = 24                       # 每 24 帧（1 秒@24fps）一枚


def quiet_bwm(processes=1):
    with contextlib.redirect_stdout(io.StringIO()):
        return WaterMark(password_wm=P_WM, password_img=P_IMG, processes=processes)


def wm_bit_len():
    bwm = quiet_bwm()
    bwm.read_wm(WM_TEXT, mode="str")
    return bwm.wm_size


def embed_frame(frame):
    bwm = quiet_bwm(processes=1)
    bwm.read_wm(WM_TEXT, mode="str")
    bwm.read_img(img=frame)
    return bwm.embed()


def extract_frame(frame, wm_len):
    bwm = quiet_bwm(processes=1)
    return bwm.extract(embed_img=frame, wm_shape=wm_len, mode="str")


def cap_info(path):
    cap = cv2.VideoCapture(path)
    info = dict(w=int(cap.get(3)), h=int(cap.get(4)), fps=float(cap.get(5) or 24), n=int(cap.get(7)))
    cap.release()
    return info


def do_embed(in_mp4, out_mp4, stride, crf, preset):
    cap = cv2.VideoCapture(in_mp4)
    w, h, fps = int(cap.get(3)), int(cap.get(4)), float(cap.get(5) or 24)
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (w, h),
           "-r", "%.3f" % fps, "-i", "-", "-i", in_mp4, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-c:a", "copy", "-movflags", "+faststart", out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    i = marked = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % stride == 0:
            frame = embed_frame(frame)
            if frame.dtype != np.uint8:            # bwm embed() 返 float 深度（cv2 警告实证）——管道前必转 uint8
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            marked += 1
        proc.stdin.write(frame.tobytes())
        i += 1
    proc.stdin.close()
    proc.wait()
    cap.release()
    assert proc.returncode == 0, "ffmpeg encode failed"
    print("EMBED-OK frames=%d marked=%d stride=%d wm=%dB -> %s" % (i, marked, stride, len(WM_TEXT.encode("utf-8")), out_mp4), flush=True)


def do_extract(in_mp4, stride, tag=""):
    wm_len = wm_bit_len()
    cap = cv2.VideoCapture(in_mp4)
    i = votes = hits = 0
    from collections import Counter
    cnt = Counter()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % stride == 0:
            try:
                txt = extract_frame(frame, wm_len)
            except Exception as e:
                txt = "<extract-error: %s>" % str(e)[:60]
            votes += 1
            cnt[txt] += 1
            if txt == WM_TEXT:
                hits += 1
        i += 1
    cap.release()
    top, top_n = (cnt.most_common(1)[0] if cnt else ("<none>", 0))
    print("EXTRACT%s frames=%d scanned=%d exact-hits=%d rate=%.1f%%" % (tag, i, votes, hits, 100.0 * hits / votes if votes else 0), flush=True)
    print("EXTRACT%s top-vote=%r x%d  all=%s" % (tag, top, top_n, dict(cnt)), flush=True)
    return hits, votes


def do_stress(wm_mp4, stride):
    d = os.path.dirname(os.path.abspath(wm_mp4))
    s1 = os.path.join(d, "wm_stress_960_crf23.mp4")
    s2 = os.path.join(d, "wm_stress_960_crf28.mp4")
    subprocess.run([FF, "-y", "-i", wm_mp4, "-vf", "scale=960:540", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "copy", s1], check=True)
    subprocess.run([FF, "-y", "-i", wm_mp4, "-vf", "scale=960:540", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p", "-c:a", "copy", s2], check=True)
    print("== stress L1: 960x540 crf23 (平台常规重压模拟)", flush=True)
    do_extract(s1, stride, tag="-L1")
    print("== stress L2: 960x540 crf28 (恶劣重压模拟)", flush=True)
    do_extract(s2, stride, tag="-L2")


def frame_at(cap_map, idx, path):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, fr = cap.read()
    cap.release()
    assert ok, "read frame %d failed" % idx
    return fr


def do_psnr(orig, marked, stride):
    a, b = cap_info(orig), cap_info(matched := marked)
    assert a["w"] == b["w"] and a["h"] == b["h"], "size mismatch"
    import random
    random.seed(1)
    idxs = [i * stride for i in range(0, 8)] + [random.randrange(stride, a["n"] - 1, stride) for _ in range(7)]
    vals = []
    for idx in idxs:
        f1 = frame_at(None, idx, orig).astype(np.float64)
        f2 = frame_at(None, idx, marked).astype(np.float64)
        mse = ((f1 - f2) ** 2).mean()
        vals.append(10 * np.log10(255.0 ** 2 / mse) if mse > 0 else 99.0)
    vals = [round(v, 2) for v in vals]
    print("PSNR-marked frames=%s  min=%.2f avg=%.2f" % (vals, min(vals), sum(vals) / len(vals)), flush=True)
    print("PSNR-VERDICT %s" % ("PASS(>38dB 不可辨)" if min(vals) > 38 else "CHECK(<38dB 需复检)"), flush=True)


def do_board(orig, marked, stride, n=3, frames=None):
    a = cap_info(orig)
    if frames:
        idxs = sorted(int(x) for x in frames.split(","))
    else:
        import random
        random.seed(7)
        idxs = sorted(random.sample(range(stride, a["n"] - 1, stride), n))
    rows = []
    for idx in idxs:
        f1 = frame_at(None, idx, orig)
        f2 = frame_at(None, idx, marked)
        diff = np.clip(np.abs(f1.astype(np.int16) - f2.astype(np.int16)) * 24, 0, 255).astype(np.uint8)
        rows.append(np.hstack([f1, f2, diff]))
    board = np.vstack(rows)
    outp = os.path.join(os.path.dirname(os.path.abspath(marked)),
                        "WM-VIS-BOARD2.jpg" if frames else "WM-VIS-BOARD.jpg")
    cv2.imwrite(outp, board, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("BOARD frames=%s -> %s (每行=原图|水印帧|24x放大差)" % (idxs, outp), flush=True)


def do_roundtrip(in_mp4):
    cap = cv2.VideoCapture(in_mp4)
    ok, frame = cap.read()
    cap.release()
    assert ok, "no frame"
    wm_len = wm_bit_len()
    print("SMOKE wm_bit_len=%d text=%r" % (wm_len, WM_TEXT), flush=True)
    emb = embed_frame(frame)
    if emb.dtype != np.uint8:
        emb = np.clip(emb, 0, 255).astype(np.uint8)
    mse = ((emb.astype(np.float64) - frame.astype(np.float64)) ** 2).mean()
    psnr = 10 * np.log10(255.0 ** 2 / mse) if mse > 0 else 99.0
    txt = extract_frame(emb, wm_len)
    print("SMOKE embed-PSNR=%.2f dB  extract=%r  %s" % (psnr, txt, "PASS" if txt == WM_TEXT else "FAIL"), flush=True)
    # PNG 往返（模拟中间存储）
    cv2.imwrite("smoke_frm.png", emb)
    back = cv2.imread("smoke_frm.png")
    txt2 = extract_frame(back, wm_len)
    print("SMOKE png-roundtrip extract=%r  %s" % (txt2, "PASS" if txt2 == WM_TEXT else "FAIL"), flush=True)
    return 0 if (txt == WM_TEXT and txt2 == WM_TEXT) else 1


def main():
    assert len(sys.argv) >= 3, "usage: mv_blind_wm_r1017.py <roundtrip|embed|extract|stress|psnr|board> ..."
    mode = sys.argv[1]
    if mode == "roundtrip":
        raise SystemExit(do_roundtrip(sys.argv[2]))
    if mode == "embed":
        stride = int(sys.argv[4]) if len(sys.argv) > 4 else STRIDE_DEF
        crf = int(sys.argv[5]) if len(sys.argv) > 5 else 22
        preset = sys.argv[6] if len(sys.argv) > 6 else "veryfast"
        do_embed(sys.argv[2], sys.argv[3], stride, crf, preset)
        return
    if mode == "extract":
        stride = int(sys.argv[3]) if len(sys.argv) > 3 else STRIDE_DEF
        hits, votes = do_extract(sys.argv[2], stride)
        raise SystemExit(0 if hits == votes and votes > 0 else 1)
    if mode == "stress":
        stride = int(sys.argv[3]) if len(sys.argv) > 3 else STRIDE_DEF
        do_stress(sys.argv[2], stride)
        return
    if mode == "psnr":
        stride = int(sys.argv[4]) if len(sys.argv) > 4 else STRIDE_DEF
        do_psnr(sys.argv[2], sys.argv[3], stride)
        return
    if mode == "board":
        arg4 = sys.argv[4] if len(sys.argv) > 4 else str(STRIDE_DEF)
        frames = arg4 if "," in arg4 else None
        stride = STRIDE_DEF if frames else int(arg4)
        do_board(sys.argv[2], sys.argv[3], stride, n=int(sys.argv[5]) if len(sys.argv) > 5 else 3, frames=frames)
        return
    raise SystemExit("unknown mode " + mode)


if __name__ == "__main__":
    main()
