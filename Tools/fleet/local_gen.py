#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_gen.py - 本机 M1 Pro 本地出图（无云端额度限制）。

为什么（2026-11-05 CEO「特地买的 M1 Pro 大内存版本，好好思考利用到位」）：
  这台机 32GB 统一内存 + 16 核 GPU，跑 SDXL-Turbo 只需 ~8-10GB，
  生成的瓶颈是显存/带宽而不是额度——正好补上云端「每日 100 次」的天花板。
  产物一律落移动盘，机队可直接自取（asset_pull）。

用法：
  python3 Tools/fleet/local_gen.py --batch cph4/fleet/state/gen-batch.json
  python3 Tools/fleet/local_gen.py --prompt "..." --out /Volumes/.../x.png [--n 2]
Exit: 0 成功；1 部分失败；2 权重缺失
"""
import argparse
import json
import os
import sys
import time

MODEL = "stabilityai/sdxl-turbo"
def _default_out():
    v = os.environ.get("FLUX_VAULT")
    if v:
        return os.path.join(v, "incoming", "generated")
    cfg = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "cph4", "fleet", "ASSET-VAULT.json")
    try:
        import json as _json
        with open(cfg, encoding="utf-8") as f:
            return os.path.join(_json.load(f)["vault"]["path"], "incoming", "generated")
    except Exception:
        return os.path.join(os.path.expanduser("~"), "FluxAssets", "incoming", "generated")


DEFAULT_OUT = _default_out()


def load_pipe():
    import torch
    from diffusers import AutoPipelineForText2Image
    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL, torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
    pipe = pipe.to("mps")
    pipe.set_progress_bar_config(disable=True)
    return pipe


def gen(pipe, prompt, out_path, steps=2, size=1024, seed=0):
    import torch
    g = torch.Generator("mps").manual_seed(int(seed) or int(time.time()) & 0xFFFF)
    img = pipe(prompt=prompt, num_inference_steps=steps, guidance_scale=0.0,
               width=size, height=size, generator=g).images[0]
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    img.save(out_path)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--out")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--batch")
    a = ap.parse_args(argv)

    cache = os.path.expanduser("~/.cache/huggingface/hub/models--stabilityai--sdxl-turbo")
    if not os.path.isdir(cache):
        print("[gen] 权重未下载（%s 不存在）；先跑 snapshot_download（rc=2）" % cache)
        return 2

    jobs = []
    if a.batch:
        spec = json.load(open(a.batch, encoding="utf-8"))
        for it in spec.get("items", []):
            jobs.append({"prompt": it["prompt"], "out": it["out"],
                         "n": int(it.get("n", 1)), "steps": int(it.get("steps", a.steps)),
                         "size": int(it.get("size", a.size))})
    elif a.prompt and a.out:
        jobs = [{"prompt": a.prompt, "out": a.out, "n": a.n,
                 "steps": a.steps, "size": a.size}]
    else:
        print("[gen] 需要 --batch 或 --prompt + --out")
        return 2

    t0 = time.time()
    pipe = load_pipe()
    t_load = time.time() - t0
    made, failed = [], []
    for j in jobs:
        base, ext = os.path.splitext(j["out"])
        for i in range(j["n"]):
            dst = j["out"] if j["n"] == 1 else "%s-%02d%s" % (base, i + 1, ext)
            t = time.time()
            try:
                gen(pipe, j["prompt"], dst, j["steps"], j["size"], seed=i + 1)
                made.append({"file": dst, "sec": round(time.time() - t, 1),
                             "steps": j["steps"], "size": j["size"]})
                print("[gen] OK %s %.1fs" % (os.path.basename(dst), time.time() - t))
            except Exception as e:
                failed.append({"file": dst, "why": str(e)[:120]})
                print("[gen] FAIL %s %s" % (os.path.basename(dst), str(e)[:80]))
    total = time.time() - t0
    print("[gen] 完成 %d 张，失败 %d，加载 %.1fs，总计 %.1fs（%.1fs/张）"
          % (len(made), len(failed), t_load, total,
             (total - t_load) / max(1, len(made))))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())