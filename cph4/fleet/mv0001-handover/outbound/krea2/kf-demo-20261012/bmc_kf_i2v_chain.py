# -*- coding: utf-8 -*-
# bmc_kf_i2v_chain.py - @bm-c kf-demo 链（O-20261012-2020 五帧 KF 批 seed 9011 + O-20261012-2025 白名单 i2v 正片波 A）
# 正身源=同目录 PROMPTS-v2.md（KF 五帧）+ FRAME-GATE-WHITELIST-v1.md（i2v 七帧+CDN 直链）——运行时解析零转抄。
# 硬律：纯画面无音轨（768P 工作流已剥 audio 链）·prompt_optimizer 无关（本地直连）·FIFO 共服不动他窗队列项。
import json, os, re, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
BMC = os.path.join(HERE, "bmc")
FRAMES_DIR = os.path.join(BMC, "i2v_frames")
I2V_OUT = os.path.join(BMC, "i2v")
os.makedirs(BMC, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(I2V_OUT, exist_ok=True)
SERVER = "http://127.0.0.1:8188"
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
WF_768P = os.path.join(REPO_ROOT, "cph4", "fleet", "mv0001-handover", "outbound",
                       "krea2", "30s-reel-v1", "h3_i2v_local_768p_v4.json")


def http_json(url, payload=None, timeout=30):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_prompts_v2():
    t = open(os.path.join(HERE, "PROMPTS-v2.md"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^## (KF[1-5]) ·.*?\n\n(.*?)(?=\n\n## |\n\n---)", t, re.S | re.M):
        out[m.group(1)] = m.group(2).strip()
    assert len(out) == 5, "PROMPTS-v2 parse got %d sections" % len(out)
    return out


def parse_whitelist():
    t = open(os.path.join(HERE, "FRAME-GATE-WHITELIST-v1.md"), encoding="utf-8").read()
    pm = {}
    for m in re.finditer(r"^(\d)\. \*\*([A-Za-z0-9_v]+)\*\*：(.+)$", t, re.M):
        pm[m.group(1)] = m.group(3).strip()
    urls = {}
    for m in re.finditer(r"^(\d)\. (\S+) → (\S+\.png)$", t, re.M):
        urls[m.group(1)] = (m.group(2), m.group(3))
    assert len(pm) == 7 and len(urls) == 7, "whitelist parse %d/%d" % (len(pm), len(urls))
    return pm, urls


def kf_graph(prompt_text, seed):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"lora_name": "jman_v1_rank32.safetensors", "strength_model": 0.8, "model": ["10", 0]}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "simple", "denoise": 1.0, "model": ["15", 0], "positive": ["6", 0],
                "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "bmc_kf_demo"}},
    }


def phase1_kf_batch():
    prompts = parse_prompts_v2()
    http_json(SERVER + "/system_stats")
    ok = []
    for name in ("KF1", "KF2", "KF3", "KF4", "KF5"):
        dst = os.path.join(BMC, name + "_s9011.png")
        if os.path.isfile(dst) and os.path.getsize(dst) > 100000:
            print("KF SKIP %s (exists)" % name, flush=True)
            ok.append(dst)
            continue
        pid = http_json(SERVER + "/prompt", {"prompt": kf_graph(prompts[name], 9011),
                                            "client_id": "bmc-kf-demo"})["prompt_id"]
        t0 = time.time()
        got = False
        while time.time() - t0 < 900:
            time.sleep(3)
            h = http_json(SERVER + "/history/" + pid, timeout=30)
            if pid in h:
                for nid, out in h[pid]["outputs"].items():
                    for img in out.get("images", []):
                        data = urllib.request.urlopen("%s/view?filename=%s&subfolder=%s&type=%s" % (
                            SERVER, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                            timeout=120).read()
                        open(dst, "wb").write(data)
                        got = True
                        break
                break
        print("KF %s -> %s %s (%.0fs)" % (name, os.path.basename(dst), "SAVED" if got else "FAIL", time.time() - t0), flush=True)
        if got:
            ok.append(dst)
    # q88 lookboard (<=1MB) for the FRAME-GATE machine check + director morning review
    if ok:
        try:
            from PIL import Image
            ims = [Image.open(p) for p in ok]
            w = min(i.width for i in ims); scale = 480 / max(i.height for i in ims)
            tw = [i.resize((int(i.width * scale), 480)) for i in ims]
            board = Image.new("RGB", (sum(t.width for t in tw) + 8 * (len(tw) + 1), 500), (12, 12, 12))
            x = 8
            for t in tw:
                board.paste(t, (x, 10)); x += t.width + 8
            dst = os.path.join(BMC, "BMC-KF-DEMO-BOARD_q88.jpg")
            q = 88
            while True:
                board.save(dst, "JPEG", quality=q)
                if os.path.getsize(dst) <= 1000000 or q <= 60:
                    break
                q -= 6
            print("BOARD SAVED %s (%dKB q%d)" % (dst, os.path.getsize(dst) // 1024, q), flush=True)
        except Exception as e:
            print("BOARD FAIL (non-blocking): %r" % e, flush=True)
    return len(ok)


def upload_image(path):
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----i2v" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)


def phase2_i2v_wave_a():
    prompts, urls = parse_whitelist()
    http_json(SERVER + "/system_stats")
    wf = json.load(open(WF_768P, encoding="utf-8"))
    ok = []
    for i in sorted(urls):
        tag, url = urls[i]
        dst_frame = os.path.join(FRAMES_DIR, tag + ".png")
        if not (os.path.isfile(dst_frame) and os.path.getsize(dst_frame) > 100000):
            print("[%s] downloading frame..." % tag, flush=True)
            data = urllib.request.urlopen(url, timeout=120).read()
            open(dst_frame, "wb").write(data)
        clip = os.path.join(I2V_OUT, tag + ".mp4")
        if os.path.isfile(clip) and os.path.getsize(clip) > 500000:
            print("I2V SKIP %s (exists)" % tag, flush=True)
            ok.append(clip)
            continue
        img = upload_image(dst_frame)
        w = json.loads(json.dumps(wf))
        w["16"]["inputs"]["image"] = img
        n6 = w["6"]["inputs"]
        n6["prompt"] = prompts[i]
        n6["length"] = 124
        n6["width"] = 1344
        n6["height"] = 768
        w["10"]["inputs"]["noise_seed"] = 9021 + int(i)
        pid = http_json(SERVER + "/prompt", {"prompt": w, "client_id": "bmc-i2v-waveA"})["prompt_id"]
        print("[%s] SUBMITTED frame=%s seed=%d" % (tag, img, 9021 + int(i)), flush=True)
        t0 = time.time()
        got = False
        while time.time() - t0 < 3000:
            time.sleep(15)
            try:
                hist = http_json(SERVER + "/history/" + pid, timeout=20)
            except Exception:
                continue
            e = hist.get(pid)
            if e is None:
                print("[%s] %4ds running..." % (tag, time.time() - t0), flush=True)
                continue
            if e.get("status", {}).get("status_str") == "error":
                print("[%s] ERROR %s" % (tag, json.dumps(e["status"].get("messages", []))[:300]), flush=True)
                break
            for nid, out in e["outputs"].items():
                vids = out.get("gifs", []) or out.get("videos", []) or out.get("images", [])
                for vid in vids:
                    u = "%s/view?filename=%s&subfolder=%s&type=%s" % (
                        SERVER, vid["filename"], vid.get("subfolder", ""), vid.get("type", "output"))
                    data = urllib.request.urlopen(u, timeout=300).read()
                    open(clip, "wb").write(data)
                    got = True
                    break
                if got:
                    break
            break
        print("[%s] %s (%.0fs)" % (tag, "SAVED " + os.path.basename(clip) if got else "FAIL", time.time() - t0), flush=True)
        if got:
            ok.append(clip)
    print("I2V WAVE A DONE ok=%d/%d out=%s" % (len(ok), len(urls), I2V_OUT), flush=True)
    return len(ok)


if __name__ == "__main__":
    print("=== PHASE 1: KF demo batch (5 frames, jman LoRA 0.8, seed 9011) ===", flush=True)
    n1 = phase1_kf_batch()
    print("KF BATCH DONE ok=%d/5" % n1, flush=True)
    print("=== PHASE 2: i2v wave A (7 clips, INT8 768P, length 124) ===", flush=True)
    n2 = phase2_i2v_wave_a()
    print("CHAIN COMPLETE kf=%d/5 i2v=%d/7" % (n1, n2), flush=True)
