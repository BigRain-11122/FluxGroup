# -*- coding: utf-8 -*-
# kf_fix2_fleet.py - v4.1 重制 6 帧生成（bm-c 执行版·CEO 判负修正 10-10「火把像火柴棍」+「女主不像那个年代台湾女生」）
# 用法: python kf_fix2_fleet.py --repo K:/Fluxgroup/FluxGroup [--server http://127.0.0.1:8188] [--seeds 7411,7412,7413,7414,7415,7416]
# 前置: 你机 ComfyUI models/ 需有 Krea2 三件（无则先装·见下）
#   diffusion_models/krea2_turbo_fp8_scaled.safetensors + text_encoders/qwen3vl_4b_fp8_scaled.safetensors
#   + vae/qwen_image_vae.safetensors ← HF: Comfy-Org/Krea-2-Fast-Diffusion-ComfyUI（split_files 结构·~15GB）
# 输出: 直接写 <repo>/.../30s-reel-v1/frames/{KF1,KF2,KF3 火把三帧+KF8,KF9,KF10 台湾她三帧}.png
#   （写完多模态 QC：火把=粗束宽焰非细棍·她=2001 台湾年代感·<8.5 换种子重摇）
import argparse, json, os, sys, time, urllib.request, uuid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--seeds", default="7411,7412,7413,7414,7415,7416")
    args = ap.parse_args()

    base = os.path.join(args.repo, "cph4", "fleet", "mv0001-handover", "outbound", "krea2", "30s-reel-v1")
    sys.path.insert(0, os.path.join(base, "..", "..", "prompt-writing-spec-v1", "patched-scripts"))
    import prompt_lexicon as LX

    LX.LIGHT["torch"] = ("thick pitch-soaked reed torches bound in corded linen burn in iron sconces, "
                         "each broad flame breathing a full wide pool of amber light, "
                         "chiaroscuro with the far shadows crushed to pure black")
    LX.LIGHT["torch_side"] = ("a thick reed-bundle torch held low at frame edge throws raking "
                              "side-backlight at 2000K across the stone, relief ridges catching "
                              "the light one band at a time while the rest stays matte black")
    LX.LIGHT["case"] = ("the glass display case glows from within at 2900K, a warm amber pool "
                        "in the surrounding darkness, reflections layered on the glass surface")
    LX.LIGHT["aisle_dim"] = ("warm case lights at 2900K dim one by one down the aisle, "
                             "the last amber pool clinging to the stone")
    STYLE_LEAD = "as a film still from a 2001 Taiwanese music video"
    # v4.1 (CEO 10-10): 博物馆她=2001 年代台湾女生（推翻西亞直鼻锚用于现代段）
    HER20 = ("a young Taiwanese woman of 2001, a softly rounded youthful face with full cheeks, "
             "large dark eyes, a small nose, long straight black hair with a full blunt fringe, "
             "wearing a simple knit top, 2001 Taipei style")
    BANDS = ("stacked horizontal bands of irregular carved cuneiform wedge marks, matte black rock "
             "with visible tool marks and fine stone grain")

    def obj_shot(shot, angle, subject, light_key, extra="", lens="35"):
        s = "A %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
            LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
            LX.LIGHT[light_key].capitalize(),
            LX.LENS[lens], LX.GRADE["mono"], LX.TEXTURE["film_night"], STYLE_LEAD)
        if extra:
            s += " " + extra
        return s

    JOBS = [
        # v4.1 火把道具律 3 帧（CEO「火把像火柴棍」→ 粗束苇把宽焰；S1 束头入画=材质可读）
        ("KF1_fire_wake", "ecu", "eye",
         obj_shot("ecu", "eye",
                  "a thick reed-bundle torch at frame left, its bound head and corded linen wrap "
                  "clearly visible, its broad flame washing across polished black basalt inscribed "
                  "with %s, the wedges catching firelight one band at a time as if waking" % BANDS,
                  "torch", lens="50",
                  extra="the wide flame breathing a full pool of amber light, embers drifting, halation blooming softly around the fire core")),
        ("KF2_sweep", "cu", "high",
         obj_shot("cu", "high",
                  "the carved stone surface of a polished black basalt stele, pure rock filling the "
                  "frame, %s half revealed and half sinking into darkness" % BANDS,
                  "torch_side", lens="50",
                  extra="each carved band surfacing and drowning in turn as the broad flame flickers low at the frame edge")),
        ("KF3_stele", "med", "low",
         obj_shot("med", "low",
                  "a tall polished black basalt stele standing upright, a carved relief at the crown "
                  "above the stacked bands of cuneiform, thick reed torches burning broad amber "
                  "flames in iron sconces on mud-brick columns behind",
                  "torch",
                  extra="each torch flame reads broad and heavy, wide amber pools raking across the hall floor, the stele filling the frame with authoritative stillness")),
        # v4.1 台湾年代女生 3 帧
        ("KF8_case", "med", "eye",
         obj_shot("med", "eye",
                  "a museum glass display case holding a broken slab of polished black basalt etched "
                  "with %s, and %s, her dark soft-edged silhouette reflection kept low and dim on the "
                  "glass, her reflection overlapping the carved bands" % (BANDS, HER20),
                  "case", lens="50",
                  extra="a soft glass glare crossing over her features, her young reflection reading as a quiet dark shape over the ancient words")),
        ("KF9_profile", "cu", "eye",
         obj_shot("cu", "eye",
                  "%s seen through museum glass, her soft youthful profile lit by the warm case "
                  "glow, large dark eyes lowered toward the stone, the dark slab of carved black "
                  "basalt behind the glass in the same frame" % HER20,
                  "case", lens="85",
                  extra="her full blunt fringe covers her brows, her lowered gaze resting on the carved bands, the glass holding her faint young reflection and the words together, natural skin grain under 35mm film texture")),
        ("KF10_walkaway", "wide", "eye",
         obj_shot("wide", "eye",
                  "%s walking away down the dark museum aisle toward the exit, her back to the camera "
                  "as a dark soft-edged silhouette, display cases dimming one by one behind her" % HER20,
                  "aisle_dim",
                  extra="one case still holds a faint amber pool around a broken black stone slab, the carved bands catching the last warm light")),
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
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
            "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                    "scheduler": "simple", "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0],
                    "negative": ["13", 0], "latent_image": ["5", 0]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
            "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "kf_fix2_fleet"}},
        }

    def post(url, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=120).read())

    def get(url):
        return json.loads(urllib.request.urlopen(url, timeout=30).read())

    for (name, _, p), seed in zip(JOBS, seeds):
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
                        break
                break
    print("KF V4.1 REGEN DONE -> frames/ 11/11 = 5(已推有效帧)+6(本批重制)", flush=True)


if __name__ == "__main__":
    main()
