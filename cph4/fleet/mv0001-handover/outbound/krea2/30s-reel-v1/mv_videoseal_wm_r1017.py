# -*- coding: utf-8 -*-
# mv_videoseal_wm_r1017.py — MV 全片隐形水印工具 v2（VideoSeal·Meta MIT·2025）
# CEO 令 2026-10-17 11:0x「MV记得给我打上暗水印...内容是 大喵没鱼吃，不要影响画面...去github看看研究下」
# 调研判决链（2026-10-17 r1017 实证·负结果全留档）：
#   ①guofei9987/blind_watermark（DWT-DCT-SVD）→ png 冒烟过但 x264 全灭（crf16/444/双嵌/Y通道 20 组矩阵
#     全 GARBAGE·kmeans 提取对视频压缩天生脆弱）→ 弃（wm_diag_r1017.py 诊断矩阵留档）
#   ②RivaGAN（DAI-Lab）→ 无预训练权重须自训 GAN·Python3.7 古栈；tucaodashen 产线版=ONNX 随 GUI 工程自带 → 弃
#   ③**VideoSeal（facebookresearch/videoseal·Meta·MIT）→ 定谳选用**：pip 可装 v1.0.1·预训练权重自动下载·
#     256bit·is_video=True 时序一致嵌入·lowres_attenuation JND 感知衰减·逐帧软预测全片均值解码·
#     抗 H.264 重压缩=训练目标（Meta 平台级 provenance 实战）
# 方案：16 帧分块全片逐帧嵌入（每帧都带印——任何 ≥16 帧盗版片段可解码）·消息=「大喵没鱼吃」utf-8
#   120bit 装 256bit 槽（余位填零）·cv2 解码→RGB→GPU 嵌入→管道回编码（单代）·音频流直拷零损。
# 用法（comfyui python·torch 2.14+cu130 在位）：
#   PY = C:\Users\sjs20\comfyui-krea\ComfyUI_windows_portable\python_embeded\python.exe
#   冒烟: & $PY mv_videoseal_wm_r1017.py smoke   <in.mp4> [nframes=48] [crf=22]
#   嵌入: & $PY mv_videoseal_wm_r1017.py embed   <in.mp4> <out.mp4> [crf=22] [preset=veryfast]
#   提取: & $PY mv_videoseal_wm_r1017.py extract <in.mp4>
#   压测: & $PY mv_videoseal_wm_r1017.py stress  <wm.mp4>          # 平台重压两级+提取
#   画质: & $PY mv_videoseal_wm_r1017.py psnr   <orig.mp4> <wm.mp4>
#   目检: & $PY mv_videoseal_wm_r1017.py board   <orig.mp4> <wm.mp4> <帧号,帧号,帧号>
import os
import subprocess
import sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import cv2
import torch
import types
sys.modules.setdefault("decord", types.ModuleType("decord"))   # decord 无 cp313 轮子·官方 README 注 inference 可缺
import videoseal

FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
WM_TEXT = "大喵没鱼吃"
MSG_BITS = np.unpackbits(np.frombuffer(WM_TEXT.encode("utf-8"), dtype=np.uint8))   # 120bit
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL = None


def load_model():
    global MODEL
    if MODEL is None:
        site_root = os.path.dirname(os.path.dirname(videoseal.__file__))  # pip 包 CWD 坑：cards_dir=相对路径 'videoseal/cards'
        prev = os.getcwd()                                                # → 须在 site-packages 根运行才能找到模型卡
        os.chdir(site_root)
        try:
            MODEL = videoseal.load("videoseal")
        finally:
            os.chdir(prev)
        MODEL.eval()
        MODEL.to(DEVICE)
        try:
            MODEL.compile()
        except Exception as e:
            print("compile-skip: %s" % str(e)[:80], flush=True)
        print("MODEL loaded on %s" % DEVICE, flush=True)
    return MODEL


def our_msgs(model):
    n = int(model.get_random_msg().shape[1])
    m = torch.zeros((1, n), dtype=torch.float32, device=DEVICE)
    m[0, :MSG_BITS.size] = torch.from_numpy(MSG_BITS).float()
    return m


def bgr2rgb(a):
    return np.ascontiguousarray(a[..., ::-1])


def embed_clip(model, clip_bgr, msgs):
    t = torch.tensor(bgr2rgb(clip_bgr), dtype=torch.float32, device=DEVICE).permute(0, 3, 1, 2) / 255.0
    with torch.no_grad():
        out = model.embed(t, msgs=msgs, is_video=True, lowres_attenuation=True)
    w = (out["imgs_w"].clamp(0, 1) * 255.0).byte().permute(0, 2, 3, 1).cpu().numpy()
    return bgr2rgb(w)


def detect_clip(model, clip_bgr):
    t = torch.tensor(bgr2rgb(clip_bgr), dtype=torch.float32, device=DEVICE).permute(0, 3, 1, 2) / 255.0
    with torch.no_grad():
        out = model.detect(t, is_video=True)
    return out["preds"][:, 1:].detach().cpu()      # (T, nbits) 软预测


def decode_soft(soft, tag=""):
    """soft=(N_frames, nbits) 软预测均值→硬比特→utf-8 文本。返回 (文本, 前120bit 准确率, 在场位)."""
    mean = soft.mean(dim=0)
    hard = (mean > 0).float()
    acc = (hard[:MSG_BITS.size] == torch.from_numpy(MSG_BITS).float()).float().mean().item()
    raw = hard[:MSG_BITS.size].cpu().numpy().astype(np.uint8)
    packed = np.packbits(raw).tobytes()
    txt = packed.decode("utf-8", errors="replace")
    print("DECODE%s bit-acc=%.1f%% text=%r" % (tag, acc * 100, txt), flush=True)
    return txt, acc


def open_pipe(in_mp4, out_mp4, crf, preset, w, h, fps):
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (w, h),
           "-r", "%.3f" % fps, "-i", "-", "-i", in_mp4, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-c:a", "copy", "-movflags", "+faststart", out_mp4]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def do_embed(in_mp4, out_mp4, crf, preset, nframes=None):
    model = load_model()
    msgs = our_msgs(model)
    cap = cv2.VideoCapture(in_mp4)
    w, h, fps = int(cap.get(3)), int(cap.get(4)), float(cap.get(5) or 24)
    proc = open_pipe(in_mp4, out_mp4, crf, preset, w, h, fps)
    chunk, count, total, t0 = [], 0, 0, __import__("time").time()

    def flush():
        nonlocal count
        if chunk:
            emb = embed_clip(model, np.stack(chunk), msgs)
            for fr in emb:
                proc.stdin.write(fr.tobytes())
            chunk.clear()
            count = 0

    while nframes is None or total < nframes:
        ok, fr = cap.read()
        if not ok:
            break
        chunk.append(fr)
        count += 1
        total += 1
        if count == 16:
            flush()
    flush()
    proc.stdin.close()
    proc.wait()
    cap.release()
    assert proc.returncode == 0, "ffmpeg failed"
    print("EMBED-OK frames=%d (%.0fs) crf=%d -> %s" % (total, __import__("time").time() - t0, crf, out_mp4), flush=True)


def do_extract(in_mp4, nframes=None, tag=""):
    model = load_model()
    cap = cv2.VideoCapture(in_mp4)
    soft, total = [], 0
    while nframes is None or total < nframes:
        ok, fr = cap.read()
        if not ok:
            break
        chunk = [fr]
        for _ in range(15):
            ok2, fr2 = cap.read()
            if not ok2:
                break
            chunk.append(fr2)
            total += 1
        total += 1
        soft.append(detect_clip(model, np.stack(chunk)))
    cap.release()
    return decode_soft(torch.cat(soft, dim=0), tag=tag)


def do_stress(wm_mp4):
    d = os.path.dirname(os.path.abspath(wm_mp4))
    s1 = os.path.join(d, "wm_stress_960_crf23.mp4")
    s2 = os.path.join(d, "wm_stress_960_crf28.mp4")
    for tag, crf, outp in (("L1-crf23", 23, s1), ("L2-crf28", 28, s2)):
        subprocess.run([FF, "-y", "-i", wm_mp4, "-vf", "scale=960:540", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
                        "-c:a", "copy", outp], check=True)
        print("== stress %s ==" % tag, flush=True)
        do_extract(outp, tag="-" + tag)


def frame_at(idx, path):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, fr = cap.read()
    cap.release()
    assert ok, "read %d failed" % idx
    return fr


def do_psnr(orig, marked):
    import random
    random.seed(3)
    vals = []
    for idx in [x * 400 for x in range(1, 14)]:
        f1 = frame_at(idx, orig).astype(np.float64)
        f2 = frame_at(idx, marked).astype(np.float64)
        mse = ((f1 - f2) ** 2).mean()
        vals.append(round(10 * np.log10(255.0 ** 2 / mse), 2) if mse > 0 else 99.0)
    print("PSNR frames=[%s] min=%.2f avg=%.2f" % (", ".join(str(v) for v in vals), min(vals), sum(vals) / len(vals)), flush=True)


def do_board(orig, marked, frames):
    idxs = [int(x) for x in frames.split(",")]
    rows = []
    for idx in idxs:
        f1, f2 = frame_at(idx, orig), frame_at(idx, marked)
        diff = np.clip(np.abs(f1.astype(np.int16) - f2.astype(np.int16)) * 24, 0, 255).astype(np.uint8)
        rows.append(np.hstack([f1, f2, diff]))
    outp = os.path.join(os.path.dirname(os.path.abspath(marked)), "WM-VIS-BOARD-VS.jpg")
    cv2.imwrite(outp, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("BOARD frames=%s -> %s" % (idxs, outp), flush=True)


def do_smoke(in_mp4, nframes, crf):
    model = load_model()
    msgs = our_msgs(model)
    print("SMOKE nbits=%d msg=%r (%dbit)" % (msgs.shape[1], WM_TEXT, MSG_BITS.size), flush=True)
    cap = cv2.VideoCapture(in_mp4)
    w, h, fps = int(cap.get(3)), int(cap.get(4)), float(cap.get(5) or 24)
    frames = []
    while len(frames) < nframes:
        ok, fr = cap.read()
        if not ok:
            break
        frames.append(fr)
    cap.release()
    emb = embed_clip(model, np.stack(frames), msgs)
    mse = ((emb.astype(np.float64) - np.stack(frames).astype(np.float64)) ** 2).mean()
    psnr = 10 * np.log10(255.0 ** 2 / mse) if mse > 0 else 99.0
    print("SMOKE embed-PSNR=%.2f dB" % psnr, flush=True)
    # A) 内存回环
    soft = detect_clip(model, emb)
    txt, acc = decode_soft(soft, tag="-mem")
    # B) crf22 编码回环
    out = os.path.join(os.path.dirname(os.path.abspath(in_mp4)), "wm_smoke_vs.mp4")
    proc = open_pipe(in_mp4, out, crf, "veryfast", w, h, fps)
    for fr in emb:
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    proc.wait()
    assert proc.returncode == 0
    do_extract(out, nframes=len(emb), tag="-crf%d" % crf)
    # C) crf28 重压
    s2 = out.replace(".mp4", "_crf28.mp4")
    subprocess.run([FF, "-y", "-i", out, "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                    "-pix_fmt", "yuv420p", "-an", s2], check=True)
    do_extract(s2, nframes=len(emb), tag="-crf28")
    print("SMOKE-DONE", flush=True)


def main():
    assert len(sys.argv) >= 3, "usage: mv_videoseal_wm_r1017.py <smoke|embed|extract|stress|psnr|board> ..."
    mode = sys.argv[1]
    if mode == "smoke":
        do_smoke(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 48,
                 int(sys.argv[4]) if len(sys.argv) > 4 else 22)
    elif mode == "embed":
        do_embed(sys.argv[2], sys.argv[3],
                 int(sys.argv[4]) if len(sys.argv) > 4 else 22,
                 sys.argv[5] if len(sys.argv) > 5 else "veryfast")
    elif mode == "extract":
        do_extract(sys.argv[2])
    elif mode == "stress":
        do_stress(sys.argv[2])
    elif mode == "psnr":
        do_psnr(sys.argv[2], sys.argv[3])
    elif mode == "board":
        do_board(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit("unknown mode " + mode)


if __name__ == "__main__":
    main()
