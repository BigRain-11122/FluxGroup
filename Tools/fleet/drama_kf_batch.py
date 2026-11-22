#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_kf_batch.py — 漫剧/短剧关键帧（D3）本地批量烧制器。

为什么单写一个而不是复用 mv_kf_batch.py（2026-11-20）：
  mv_kf_batch 的 preflight_gate 词表是 MV 专用（grade ∈ tw2001/mono/bluefire/nost，
  texture ∈ film_night/...），漫剧/短剧的画风轴完全不同；硬接等于把 MV 判据套在漫剧上，
  闸会一直红、或者逼人改 MV 词表。档位=补缺口，不动 MV 链。

链：drama_kf_plan.py（剧本→prompt 表）→ 本文件（prompt 表→PNG）
铁律（全部来自 60 集量产线判例）：
  - SKIP 断点续跑：目标 PNG 存在且 >10KB 即跳过（重烧前必须先归档旧帧）
  - 种子由 plan 给定，确定性可复刻
  - 同 checkpoint 批一次加载跑完（队列驻留律）
  - 落盘一律 .tmp → os.replace，禁止半文件假成功

用法：
  python Tools/fleet/drama_kf_batch.py --prompts cph4/fleet/out/drama/EP001/kf_prompts.json \
         --out cph4/fleet/out/drama/EP001/kf
  python Tools/fleet/drama_kf_batch.py --ep 1 --limit 4        # 冒烟
  [--ckpt animagine-xl-4.0.safetensors] [--width 832] [--height 1472]
  [--steps 28] [--cfg 6.0] [--clip-skip 2] [--server http://127.0.0.1:8188]
  [--only EP001_05,EP001_07] [--timeout 600]
Exit: 0 = 全部成图（含跳过）；1 = 有失败；2 = 输入/服务器不可用
"""
import argparse
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "Tools"))
import preflight_gate as G  # noqa: E402  与 MV 同一道闸，profile="drama" 换词表

MIN_BYTES = 10 * 1024


def http(url, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def wait_server(server, budget=300):
    t0 = time.time()
    while True:
        try:
            http(server + "/system_stats", timeout=6)
            return True
        except Exception:
            if time.time() - t0 > budget:
                return False
            time.sleep(3)


def build_wf(row, a):
    clip_skip = a.clip_skip
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "seed": int(row["seed"]), "steps": a.steps, "cfg": a.cfg,
            "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0,
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0]}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": a.ckpt}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {
            "width": a.width, "height": a.height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": row["prompt"], "clip": ["12", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": row.get("negative") or "", "clip": ["12", 0]}},
        "12": {"class_type": "CLIPSetLastLayer", "inputs": {"stop_at_clip_layer": -int(clip_skip), "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": row["id"]}},
    }


def run_one(row, a):
    wf = build_wf(row, a)
    pid = json.loads(http(a.server + "/prompt", data=json.dumps(
        {"prompt": wf, "client_id": "drama-kf-%d" % int(time.time() * 1000)}).encode()))["prompt_id"]
    t0 = time.time()
    while True:
        time.sleep(2)
        if time.time() - t0 > a.timeout:
            return None, None, "TIMEOUT"
        h = json.loads(http(a.server + "/history/" + pid))
        if pid in h:
            break
    entry = h[pid]
    if entry.get("status", {}).get("status_str") == "error":
        return None, None, "GEN_ERROR " + json.dumps(entry.get("status", {}))[:400]
    meta = None
    for node_out in entry.get("outputs", {}).values():
        for im in node_out.get("images", []):
            meta = im
            break
        if meta:
            break
    if not meta:
        return None, None, "NO_IMAGE"
    qs = "filename=%s&subfolder=%s&type=%s" % (
        urllib.request.quote(meta["filename"]),
        urllib.request.quote(meta.get("subfolder", "")),
        urllib.request.quote(meta.get("type", "output")))
    raw = http(a.server + "/view?" + qs, timeout=300)
    return raw, round(time.time() - t0, 1), None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default="")
    ap.add_argument("--ep", type=int, default=0)
    ap.add_argument("--out", default="")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--ckpt", default="animagine-xl-4.0.safetensors")
    ap.add_argument("--width", type=int, default=832)
    ap.add_argument("--height", type=int, default=1472)
    ap.add_argument("--steps", type=int, default=28)
    ap.add_argument("--cfg", type=float, default=6.0)
    ap.add_argument("--clip-skip", type=int, default=2)
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--receipt", default="")
    a = ap.parse_args(argv)

    if not a.prompts and a.ep:
        base = os.path.join(ROOT, "cph4", "fleet", "out", "drama", "EP%03d" % a.ep)
        a.prompts = os.path.join(base, "kf_prompts.json")
        a.out = a.out or os.path.join(base, "kf")
    if not a.prompts or not os.path.isfile(a.prompts):
        print("BATCH ABORT prompts missing: %s" % a.prompts)
        return 2
    try:
        rows = json.load(open(a.prompts, encoding="utf-8"))
    except Exception as e:
        print("BATCH ABORT prompts unreadable: %s" % type(e).__name__)
        return 2
    if a.only:
        want = set(x.strip() for x in a.only.split(",") if x.strip())
        rows = [r for r in rows if r["id"] in want]
    if a.limit:
        rows = rows[:a.limit]
    if not rows:
        print("BATCH ABORT empty selection")
        return 2

    a.out = a.out or os.path.join(os.path.dirname(a.prompts), "kf")
    os.makedirs(a.out, exist_ok=True)

    if not wait_server(a.server):
        print("BATCH ABORT server down: %s" % a.server)
        return 2

    made = skipped = 0
    fails = []
    gated = 0
    t0 = time.time()
    for i, row in enumerate(rows, 1):
        dst = os.path.join(a.out, row["id"] + ".png")
        if os.path.isfile(dst) and os.path.getsize(dst) > MIN_BYTES:
            skipped += 1
            continue
        # 预检闸（PREFLIGHT-GATE-v1 §三：绕过＝违规）。本批是文生图 KF，无源帧，
        # 与 mv_kf_batch 同口径：kf_verified=True + 显式记录豁免理由。
        gate_fails = G.guard(
            row["id"], row.get("prompt", ""),
            {k: row.get(k) for k in ("shot", "angle", "move", "grade", "texture", "scene", "light")},
            kf_verified=True,
            kf_note="text-to-image KF：无源帧可核（同 mv_kf_batch 口径）",
            profile="drama")
        if gate_fails:
            gated += 1
            fails.append({"id": row["id"], "err": "GATE", "why": gate_fails})
            print("[%d/%d] GATE-FAIL %s :: %s" % (i, len(rows), row["id"], " ; ".join(gate_fails)[:220]),
                  flush=True)
            continue
        raw, sec, err = run_one(row, a)
        if err or not raw:
            fails.append({"id": row["id"], "err": err})
            print("[%d/%d] FAIL %s :: %s" % (i, len(rows), row["id"], err), flush=True)
            continue
        tmp = dst + ".tmp"
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, dst)
        made += 1
        print("[%d/%d] GEN %s %.1fs %dB %.0fs-elapsed" % (
            i, len(rows), row["id"], sec, len(raw), time.time() - t0), flush=True)

    receipt = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "prompts": os.path.relpath(a.prompts, ROOT).replace("\\", "/"),
        "out": os.path.relpath(a.out, ROOT).replace("\\", "/"),
        "ckpt": a.ckpt, "w": a.width, "h": a.height, "steps": a.steps, "cfg": a.cfg,
        "total": len(rows), "made": made, "skipped": skipped, "failed": len(fails),
        "gate_failed": gated, "fails": fails[:20], "elapsed_s": round(time.time() - t0, 1),
    }
    rp = a.receipt or os.path.join(os.path.dirname(a.out), "kf-receipt.json")
    json.dump(receipt, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("BATCH DONE made=%d skipped=%d gate_failed=%d failed=%d receipt=%s" % (
        made, skipped, gated, len(fails), os.path.relpath(rp, ROOT)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
