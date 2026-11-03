#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""角色包出图执行器：按 PROMPTS.json 在**本机** ComfyUI 上出 6 视角图。

设计要点（2026-11-03）：
  1. 只在 127.0.0.1 上跑——ComfyUI 不外绑，所以这张卡必须落在有 ComfyUI 的那台机上
     （mem: 2026-10-23「你不能远程调度」，8188 从外部永远测不通）。
  2. 不知道模型就**不猜**：模型名从 `asset-lib-v1/comfy-<node>.json` 读，
     文件不存在或模型缺失 → 写 BLOCKED 回执 (rc=3, E-BLOCKED-INPUT) 并列出缺什么。
  3. 产物落 media/asset/characters/<ID>/<view>.png；回执落 cph4/fleet/queue-receipts/。

用法（在目标机上）：
  python Tools/fleet/char_gen.py --node bm-c [--only CH03] [--limit 6] [--server http://127.0.0.1:8188]
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHARS = os.path.join(ROOT, "media", "asset", "characters")
CONF = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")


def http_json(url, payload=None, timeout=30):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
    return json.loads(body) if body.strip().startswith(("{", "[")) else body


def graph(pos, neg, seed, m, w, h):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": m["unet"], "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": m["clip"], "type": m.get("clip_type", "sdxl")}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": m["vae"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["11", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["11", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": int(m.get("steps", 8)), "cfg": float(m.get("cfg", 1.0)),
            "sampler_name": m.get("sampler", "euler"), "scheduler": m.get("scheduler", "simple"),
            "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "char"}},
    }


def blocked(why, gaps, outpath):
    rec = {"rc": 3, "verdict": "BLOCKED", "status": "BLOCKED", "error_class": "E-BLOCKED-INPUT",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "why": why, "gaps": gaps,
           "tool": "char_gen"}
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("[char_gen] BLOCKED:", why)
    for g in gaps:
        print("   -", g)
    return 3


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default="bm-c")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    a = ap.parse_args(argv)
    stamp = time.strftime("%Y%m%d")
    outrec = os.path.join(RECEIPTS, "char-gen-%s-%s.json" % (a.node, stamp))

    conf_path = os.path.join(CONF, "comfy-%s.json" % a.node)
    if not os.path.exists(conf_path):
        return blocked("缺模型配置：%s" % os.path.relpath(conf_path, ROOT),
                       ["写一份 comfy-%s.json（unet/clip/vae/steps/cfg），不要靠猜模型名" % a.node],
                       outrec)
    m = json.load(open(conf_path, encoding="utf-8"))
    try:
        http_json(a.server + "/system_stats", timeout=8)
    except Exception as e:
        return blocked("ComfyUI 不可达：%s" % a.server,
                       ["在 %s 上启动 ComfyUI 并确认 8188 可连（%s）" % (a.node, e)], outrec)

    items = []
    for cid in sorted(os.listdir(CHARS)):
        d = os.path.join(CHARS, cid)
        p = os.path.join(d, "PROMPTS.json")
        if not os.path.isfile(p) or (a.only and cid != a.only):
            continue
        items.append((cid, d, json.load(open(p, encoding="utf-8"))))
    if not items:
        return blocked("没有 PROMPTS.json", ["先跑 Tools/fleet/char_plan.py 生成提示词包"], outrec)

    made, failed = [], []
    budget = a.limit or 10 ** 9
    for cid, d, pack in items:
        seed = int(pack["consistency"]["seed"])
        for view, pr in pack["views"].items():
            if budget <= 0:
                break
            fp = os.path.join(d, "%s.png" % view)
            if os.path.exists(fp) and os.path.getsize(fp) > 20000:
                continue
            payload = {"prompt": graph(pr["positive"], pr["negative"], seed, m, a.width, a.height),
                       "client_id": str(uuid.uuid4())}
            try:
                r = http_json(a.server + "/prompt", payload, timeout=60)
                pid = r.get("prompt_id")
                for _ in range(180):
                    time.sleep(2)
                    h = http_json(a.server + "/history/" + str(pid), timeout=15)
                    if h and pid in h:
                        break
                made.append({"character": cid, "view": view, "prompt_id": pid})
                budget -= 1
            except Exception as e:
                failed.append({"character": cid, "view": view, "error": str(e)[:160]})
                budget -= 1
    rec = {"rc": 0 if not failed else 1, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "node": a.node, "made": made, "failed": failed,
           "note": "图落 ComfyUI 输出目录后需回拷到 media/asset/characters/<ID>/<view>.png，"
                   "下一步由 asset_dataset_audit 判准入"}
    os.makedirs(RECEIPTS, exist_ok=True)
    with open(outrec, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("char_gen: made=%d failed=%d -> %s" % (len(made), len(failed), os.path.relpath(outrec, ROOT)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))