#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mlx_bench.py - 本地视觉推理对照：ollama(服务化) vs mlx-vlm(直调 MLX)。

为什么（CEO：本地模型都要针对 MLX 优化）：
  ollama 走的是服务化路径（HTTP + 自己的调度 + 可能的排队），
  mlx-vlm 直接吃 MLX 图，理论上省掉服务层与格式转换。
  但"理论上"不算数，必须同一张图同一提示词实测。

用法：
  python3 Tools/fleet/mlx_bench.py --img <图片> [--runs 2]
Exit: 0 测完；2 环境不满足
"""
import argparse
import base64
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.request

MLX_MODEL = os.environ.get("MLX_VL_MODEL") or "/Users/junsheng.sun/models/mlx-qwen25vl-3b-4bit"
OLLAMA_MODEL = os.environ.get("CAPTION_MODEL") or "qwen3.5:4b-mlx"
PROMPT = ("Describe this image as a Stable Diffusion LoRA training caption of an object or scene. "
          "State at least four concrete visible attributes: what the object is, its material, "
          "colour, shape, surface condition, how it is arranged, and the background. "
          "One sentence, under 40 words, English. "
          "Never hedge: do not write 'appears to be', 'looks like', 'seems' or 'possibly'. "
          "Do not guess brands, do not name people, do not add style words.")


def ollama_once(img):
    b = base64.b64encode(open(img, "rb").read()).decode()
    body = {"model": OLLAMA_MODEL, "prompt": PROMPT, "images": [b], "stream": False,
            "think": False, "keep_alive": "10m",
            "options": {"temperature": 0.2, "num_predict": 90}}
    t0 = time.time()
    r = urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:11434/api/generate", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}), timeout=300)
    d = json.loads(r.read())
    return round(time.time() - t0, 2), (d.get("response") or "").strip(), d.get("eval_count")


def mlx_once(img):
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config
    t0 = time.time()
    if not hasattr(mlx_once, "_pipe"):
        model, processor = load(MLX_MODEL)
        cfg = load_config(MLX_MODEL)
        mlx_once._pipe = (model, processor, cfg)
    model, processor, cfg = mlx_once._pipe
    t1 = time.time()
    formatted = apply_chat_template(processor, cfg, PROMPT, num_images=1)
    out = generate(model, processor, formatted, [img], max_tokens=90, verbose=False)
    text = out.text if hasattr(out, "text") else str(out)
    total = round(time.time() - t0, 2)
    if not hasattr(mlx_once, "_load_s"):
        mlx_once._load_s = round(t1 - t0, 2)
    return total, text.strip(), None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--runs", type=int, default=2)
    a = ap.parse_args(argv)
    if not os.path.isfile(a.img):
        print("[bench] 图片不存在")
        return 2
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "img": a.img, "runs": a.runs}
    for name, fn in (("ollama", ollama_once), ("mlx-vlm", mlx_once)):
        times, sample = [], ""
        try:
            # 预热一次并丢弃：首调用含模型加载，混进中位数会把"加载慢"记成"推理慢"
            try:
                fn(a.img)
            except Exception as _e:
                print("[bench] %-8s 预热失败 %s" % (name, str(_e)[:80]))
            for i in range(a.runs):
                t, text, _ = fn(a.img)
                times.append(t)
                sample = text
                print("[bench] %-8s 第%d次 %.2fs  %s" % (name, i + 1, t, text[:70]))
        except Exception as e:
            print("[bench] %-8s 失败：%s" % (name, str(e)[:120]))
            out[name] = {"error": str(e)[:200]}
            continue
        out[name] = {"times": times, "median_s": round(statistics.median(times), 2),
                     "sample": sample[:200]}
    if "ollama" in out and "mlx-vlm" in out and "median_s" in out.get("mlx-vlm", {}):
        gain = out["ollama"]["median_s"] / out["mlx-vlm"]["median_s"]
        out["speedup_mlx"] = round(gain, 2)
        print("[bench] mlx-vlm 相对 ollama 提速 %.2fx（中位 %.2fs vs %.2fs）"
              % (gain, out["mlx-vlm"]["median_s"], out["ollama"]["median_s"]))
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                     "cph4", "fleet", "state", "mlx-bench.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())