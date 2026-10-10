# -*- coding: utf-8 -*-
# kf_vertical_fleet.py - 抖音竖版双镜重做帧生成（平台席变体方案·bm-c 执行版）
# 用法: python kf_vertical_fleet.py --repo K:/Fluxgroup/FluxGroup [--server http://127.0.0.1:8188] [--seeds 7431,7432]
# 输出: <repo>/.../30s-reel-v1/frames/KF4_v.png + KFT_v.png（768×1344·9:16）
# 依据: 平台运营席横竖版决策——S1/S4/T 三镜中心裁报废·其中 S4/T 必须重做（金字=标志语言糊不得）；
#   其余 9 镜由 bm-a 静态取景裁切（ffmpeg·CPU）。QC=六检同主批（楔形检/浮雕检照常）。
import argparse, json, os, sys, time, urllib.request, uuid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--seeds", default="7431,7432")
    args = ap.parse_args()

    base = os.path.join(args.repo, "cph4", "fleet", "mv0001-handover", "outbound", "krea2", "30s-reel-v1")
    sys.path.insert(0, os.path.join(base, "..", "..", "prompt-writing-spec-v1", "patched-scripts"))
    import prompt_lexicon as LX

    LX.LIGHT["torch"] = ("thick pitch-soaked reed torches bound in corded linen burn in cast bronze "
                         "sconce bowls on thick bronze brackets, each broad flame breathing a full "
                         "wide pool of pure amber-gold light with smoky yellow tips, chiaroscuro "
                         "with the far shadows crushed to pure black")
    LX.LIGHT["glyph"] = ("the wedge marks are self-lit in deep gold, their glow blooming softly "
                         "through warm haze against black that carries visible 35mm film grain")
    STYLE_LEAD = "as a film still from a 2001 Taiwanese music video"

    def obj_shot(shot, angle, subject, light_key, extra="", lens="35"):
        s = "A %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
            LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
            LX.LIGHT[light_key].capitalize(),
            LX.LENS[lens], LX.GRADE["mono"], LX.TEXTURE["film_night"], STYLE_LEAD)
        if extra:
            s += " " + extra
        return s

    JOBS = [
        # S4 竖版：王神对置上下排布进竖画幅（服装席浮雕正解锚全量保留）
        ("KF4_v",
         obj_shot("cu", "low",
                  "the carved crown relief band of the black basalt stele filling a tall vertical "
                  "frame: a standing bearded king in a long fringed robe and a rolled-brim cap, "
                  "his hand raised in salute toward a seated god wearing a horned tiara and a "
                  "heavy flounced robe with one shoulder bared, the god holding out a rod and a "
                  "ring, the two figures arranged one above the other in the tall frame",
                  "torch",
                  extra="their carved forms surfacing from near-black stone, the god's rod and the "
                        "ring reading as two separate objects")),
        # T 竖版：金字短列=天然竖构图（文字席成簇锚全量保留）
        ("KFT_v",
         obj_shot("med", "eye",
                  "a tall column of luminous deep-gold cuneiform signs drifting upward through "
                  "warm haze, each sign a tight cluster of wedges with triangular heads and long "
                  "tapering tails, soft golden bloom breathing around each sign, the glyph glow "
                  "decaying softly into halation at its edges",
                  "glyph",
                  extra="the darkness alive with grain, warm and analog")),
    ]
    seeds = [int(x) for x in args.seeds.split(",")]
    out_dir = os.path.join(base, "frames")
    os.makedirs(out_dir, exist_ok=True)

    def graph(prompt_text, seed):
        return {
            "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
            "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
            "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
            "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 1344, "batch_size": 1}},
            "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                    "scheduler": "simple", "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0],
                    "negative": ["13", 0], "latent_image": ["5", 0]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
            "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "kf_v44_vertical"}},
        }

    def post(url, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=120).read())

    def get(url):
        return json.loads(urllib.request.urlopen(url, timeout=30).read())

    done = []
    for (name, p), seed in zip(JOBS, seeds):
        hits = LX.lint(p, mode="t2i")
        if hits:
            print("LINT-FAIL", name, hits, flush=True)
            continue
        pid = post(args.server + "/prompt", {"prompt": graph(p, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
        print("[%s] submitted seed=%d" % (name, seed), flush=True)
        t0 = time.time()
        while time.time() - t0 < 1800:
            time.sleep(3)
            h = get(args.server + "/history/" + pid)
            if pid in h:
                for nid, out in h[pid]["outputs"].items():
                    for img in out.get("images", []):
                        data = urllib.request.urlopen(
                            "%s/view?filename=%s&subfolder=%s&type=%s" % (
                                args.server, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                            timeout=60).read()
                        open(os.path.join(out_dir, name + ".png"), "wb").write(data)
                        print("[%s] SAVED frames/%s.png (%.0fs)" % (name, name, time.time() - t0), flush=True)
                        done.append(name)
                        break
                break
    missing = [n for n, _ in JOBS if n not in done]
    if missing:
        print("KF VERTICAL INCOMPLETE, missing: %s" % ",".join(missing), flush=True)
        sys.exit(1)
    print("KF VERTICAL DONE -> frames/KF4_v.png + KFT_v.png (768x1344)", flush=True)


if __name__ == "__main__":
    main()
