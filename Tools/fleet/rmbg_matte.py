# -*- coding: utf-8 -*-
"""用本机 BRIA RMBG-1.4 权重给图片抠出透明底（离线，无需登录）。

ComfyUI 的 BRIA 节点需要登录，但 models/rmbg 下的权重是完整可用的，
直接用 ComfyUI 自带的 torch 环境加载即可。GPU 被 ComfyUI 占满时可 --cpu。

用法（必须用 ComfyUI 的 python，项目 python 没有 torch）：
  D:\\ComfyUI\\python_embeded\\python.exe Tools/fleet/rmbg_matte.py 图1.png 图2.png
  ... --cpu --out-dir media/asset/props
输出：同目录同名加 -alpha 后缀的 PNG；已存在的跳过（--force 重做）。
"""
import argparse
import os
import sys

RMBG_DIR = r"D:\ComfyUI\ComfyUI\models\rmbg"
WEIGHT = os.path.join(RMBG_DIR, "model.safetensors")


def load_model(device):
    import torch
    sys.path.insert(0, os.path.dirname(RMBG_DIR))
    from rmbg.briarmbg import BriaRMBG
    from rmbg.MyConfig import RMBGConfig
    model = BriaRMBG(RMBGConfig())
    from safetensors.torch import load_file
    state = load_file(WEIGHT)
    model.load_state_dict(state, strict=False)
    model.to(device).eval()
    return model


def keep_main_object(mask):
    """只留最大连通域并填掉内部空洞。

    RMBG 偶尔会把一块背景光斑判成主体（实测怀表左上方留了半块霓虹），
    这类碎块和主体不相连，取最大连通域就能去掉；内部空洞则是模型在
    物体亮部挖的洞，填掉可避免成品出现透空斑。
    """
    import numpy as np
    from scipy import ndimage
    m = mask >= 128
    if not m.any():
        return mask
    lbl, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, lbl, range(1, n + 1))
        m = lbl == (int(np.argmax(sizes)) + 1)
    m = ndimage.binary_fill_holes(m)
    # 物体内部一律不透明，只有边缘保留模型的软过渡；否则深色玻璃面会透出背景色。
    interior = ndimage.binary_erosion(m, iterations=2)
    alpha = np.where(m, mask, 0).astype(np.uint8)
    alpha[interior] = 255
    return alpha


def run(model, path, device):
    import numpy as np
    import torch
    import torch.nn.functional as F
    from PIL import Image
    orig = Image.open(path).convert("RGB")
    w, h = orig.size
    im = torch.tensor(np.array(orig), dtype=torch.float32).permute(2, 0, 1)
    im = F.interpolate(torch.unsqueeze(im, 0), size=(1024, 1024), mode="bilinear")
    im = (im / 255.0 - 0.5) / 1.0
    with torch.no_grad():
        out = model(im.to(device))
    if isinstance(out, (list, tuple)):
        while isinstance(out, (list, tuple)):
            out = out[0]
    out = out.squeeze()
    out = F.interpolate(out.view(1, 1, *out.shape[-2:]), size=(h, w), mode="bilinear")[0, 0]
    lo, hi = torch.min(out), torch.max(out)
    out = (out - lo) / (hi - lo + 1e-6)
    mask = (out.squeeze().cpu().numpy() * 255).astype(np.uint8)
    mask = keep_main_object(mask)
    rgba = orig.convert("RGBA")
    rgba.putalpha(Image.fromarray(mask))
    return rgba


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--suffix", default="-alpha")
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.exists(WEIGHT):
        print("[rmbg] 缺少权重:", WEIGHT)
        return 3
    import torch
    device = "cpu" if a.cpu or not torch.cuda.is_available() else "cuda:0"
    model = load_model(device)
    print("[rmbg] device", device)
    fails = 0
    for f in a.files:
        stem, _ = os.path.splitext(os.path.basename(f))
        out_dir = a.out_dir or os.path.dirname(f) or "."
        os.makedirs(out_dir, exist_ok=True)
        dst = os.path.join(out_dir, stem + a.suffix + ".png")
        if os.path.exists(dst) and not a.force:
            print("[rmbg] skip", dst)
            continue
        try:
            run(model, f, device).save(dst)
            print("[rmbg]", f, "->", dst)
        except Exception as e:
            fails += 1
            print("[rmbg] FAIL", f, str(e)[:160])
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))