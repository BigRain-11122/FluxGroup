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


def fetch_image(server, hist, pid, target):
    """把 ComfyUI 输出目录里的成品取回本地。之前只记 prompt_id 不落盘，
    卡上要的 <ID>/<view>.png 实际并不存在。"""
    import urllib.parse
    node_out = (hist.get(pid) or {}).get("outputs") or {}
    for v in node_out.values():
        for im in v.get("images") or []:
            q = urllib.parse.urlencode({"filename": im.get("filename", ""),
                                        "subfolder": im.get("subfolder", ""),
                                        "type": im.get("type", "output")})
            try:
                with urllib.request.urlopen(server + "/view?" + q, timeout=120) as resp:
                    data = resp.read()
            except Exception:
                continue
            if len(data) > 1024:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(data)
                return True
    return False


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


def graph_ckpt(pos, neg, seed, m, w, h):
    """整包 checkpoint 路线（只有 CheckpointLoaderSimple 的机器用这条）。"""
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": m["ckpt"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4", 1]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": int(m.get("steps", 24)), "cfg": float(m.get("cfg", 5.0)),
            "sampler_name": m.get("sampler", "euler"), "scheduler": m.get("scheduler", "normal"),
            "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "char"}},
    }


def _names(info, node, field):
    try:
        req = info[node]["input"]["required"][field][0]
        return [x for x in req if isinstance(x, str)]
    except Exception:
        return []


def probe(server):
    """问机器自己有哪些模型，而不是猜。返回可直接落盘的配置。"""
    info = http_json(server + "/object_info", timeout=25)
    ckpts = _names(info, "CheckpointLoaderSimple", "ckpt_name")
    unets = _names(info, "UNETLoader", "unet_name")
    clips = _names(info, "CLIPLoader", "clip_name")
    vaes = _names(info, "VAELoader", "vae_name")

    def pref(lst, keys):
        for k in keys:
            for x in lst:
                if k in x.lower():
                    return x
        return lst[0] if lst else None

    cfg = {"probed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "available": {"ckpt": len(ckpts), "unet": len(unets), "clip": len(clips), "vae": len(vaes)}}
    # 人像优先：显式写优先序，别只看第一个
    # CLIPLoader 的 type 是枚举，写死非法值会让 /prompt 直接 400；按 UNET 家族推导再校验。
    clip_types = _names(info, "CLIPLoader", "type")
    family = [("krea2", "krea2"), ("qwen", "qwen_image"), ("minimax", "minimax"),
              ("flux", "flux"), ("sd3", "sd3"), ("hidream", "hidream"),
              ("chroma", "chroma"), ("omnigen", "omnigen2"), ("lumina", "lumina2"),
              ("pixart", "pixart"), ("cosmos", "cosmos")]
    wants = ["sdxl", "real", "photo", "jugg", "krea", "qwen"]
    # 有 checkpoint 就优先走它：CLIP/VAE 由 checkpoint 自带，不可能错配；
    # unet 路线需要人工确认配套文本编码器，探针无法验证，容易到 KSampler 才炸。
    if not ckpts and unets and clips:
        unet = pref(unets, wants)
        ctype = "stable_diffusion"
        for k, v in family:
            if k in (unet or "").lower():
                ctype = v
                break
        if ctype in clip_types:
            cfg.update({"route": "unet", "unet": unet, "clip": pref(clips, wants),
                        "vae": pref(vaes, ["sdxl", "vae"]), "clip_type": ctype,
                        "steps": 8, "cfg": 1.0, "sampler": "euler", "scheduler": "simple"})
    if not cfg.get("route") and ckpts:
        # 没有能自洽的 unet/clip 组合时退回 checkpoint：clippy 由 checkpoint 自带，无需猜 type。
        good = [c for c in ckpts if c.lower().endswith((".safetensors", ".ckpt"))] or ckpts
        ckpt = pref(good, ["sdxl", "real", "photo", "jugg", "xl"])
        light = "lightning" in (ckpt or "").lower() or "turbo" in (ckpt or "").lower()
        cfg.update({"route": "ckpt", "ckpt": ckpt,
                    "steps": 8 if light else 26, "cfg": 2.0 if light else 5.0,
                    "sampler": "euler" if light else "dpmpp_2m",
                    "scheduler": "normal" if light else "karras"})
    if not cfg.get("route"):
        cfg["route"] = None
    return cfg


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
    ap.add_argument("--probe-only", action="store_true",
                    help="只问机器有哪些模型并写配置，不出图")
    ap.add_argument("--receipt", default="",
                    help="回执落点（默认 cph4/fleet/queue-receipts/char-gen-<node>-<YYYYMMDD>.json）")
    a = ap.parse_args(argv)
    stamp = time.strftime("%Y%m%d")
    outrec = a.receipt or os.path.join(RECEIPTS, "char-gen-%s-%s.json" % (a.node, stamp))
    if a.receipt and not os.path.isabs(outrec):
        outrec = os.path.join(ROOT, outrec)
    os.makedirs(os.path.dirname(outrec), exist_ok=True)

    conf_path = os.path.join(CONF, "comfy-%s.json" % a.node)
    mk = None
    if os.path.exists(conf_path):
        mk = json.load(open(conf_path, encoding="utf-8"))
    try:
        if a.probe_only or not mk:
            mk = probe(a.server)
            with open(conf_path, "w", encoding="utf-8") as f:
                json.dump(mk, f, ensure_ascii=False, indent=1)
            print("[char_gen] probed -> %s | route=%s" % (os.path.relpath(conf_path, ROOT), mk.get("route")))
        if a.probe_only:
            if not mk.get("route"):
                return blocked(
                    "本机 ComfyUI 没有任何可用 checkpoint/unet",
                    ["装一个能出人像的模型（SDXL 系）再跑；不要用 KF 专用模型硬顶人像"],
                    outrec)
            # 2026-11-11：探针成功路径原本只写 conf、不写 --receipt，卡片 rc=0 却被判
            # E-ARTIFACT（deliverable_exists=false）——成功被记成失败，卡会反复重派。
            rec = {"probe_only": True, "node": a.node, "server": a.server, "rc": 0,
                   "outcome": "OK", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "conf": os.path.relpath(conf_path, ROOT),
                   "route": mk.get("route"), "ckpt": mk.get("ckpt"),
                   "available": mk.get("available")}
            json.dump(rec, open(outrec, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("[char_gen] receipt -> %s" % os.path.relpath(outrec, ROOT))
            return 0
    except Exception as e:
        return blocked("ComfyUI 不可达或 /object_info 失败：%s" % a.server,
                       ["在 %s 上启动 ComfyUI 并确认 8188 可连（%s）" % (a.node, e)], outrec)
    if not mk.get("route"):
        return blocked("模型配置为空", ["跑 --probe-only 看机器上有哪些模型"], outrec)

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
                # 2026-11-04: an already-produced view IS the deliverable (saved on disk).
                # Counting it as made keeps "made>0" honest when a rerun finds the batch done;
                # reporting made=[] made the card FAIL forever while all images sat on disk.
                made.append({"character": cid, "view": view, "prompt_id": "skip-existing",
                             "file": os.path.relpath(fp, ROOT), "saved": True})
                continue
            _g = graph_ckpt if mk.get("route") == "ckpt" else graph
            payload = {"prompt": _g(pr["positive"], pr["negative"], seed, mk, a.width, a.height),
                       "client_id": str(uuid.uuid4())}
            try:
                r = http_json(a.server + "/prompt", payload, timeout=60)
                pid = r.get("prompt_id")
                for i in range(180):
                    time.sleep(2)
                    h = http_json(a.server + "/history/" + str(pid), timeout=15)
                    if h and pid in h:
                        break
                    # stdout 就是执行器的进度信号：静默等待会被 closer 判 30min STALL 并杀线
                    if i and i % 15 == 0:
                        print("WAIT pid=%s elapsed=%ds" % (pid, (i + 1) * 2), flush=True)
                if not (h and pid in h):
                    print("TIMEOUT pid=%s after 360s (comfy history empty)" % pid, flush=True)
                saved = fetch_image(a.server, h, pid, fp)
                made.append({"character": cid, "view": view, "prompt_id": pid,
                             "file": os.path.relpath(fp, ROOT) if saved else "",
                             "saved": saved})
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