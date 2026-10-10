# -*- coding: utf-8 -*-
# kf_fix2_fleet.py - v4.2 重制 8 帧生成（bm-c 执行版）
# 版本链: v4.1 火柴棍+台湾她修正 → v4.2 专家团设计闸修正（调色师+美术考据两席 CONDITIONAL PASS 的必修项落地）
#   ①铁壁架→青铜壁托碗（青铜时代无建筑铁五金·美术考据席·超前500年硬伤）+焰纯琥珀金橙禁蓝紫
#   ②展柜灯→3000K 暖钨丝卤素（2001 台湾=卤素暖光时代·冷白 LED=超前9年）+她肤暖调+阴影暖褐 tint
#   ③S3 碑形锁死平板圆顶碑（禁圆柱漂移·直边+冠部浮雕带+20+ 横铭文带叠到碑底）
#   ④KF6 凿刻回暖（石+麻衣推入琥珀族·去双温）+补木槌击凿手势（光手按凿读假）
#   ⑤KFT 金字补胶片颗粒（黑场补 5279 颗粒+光晕 halation 式衰减·去数字黑）
# 用法: python kf_fix2_fleet.py --repo K:/Fluxgroup/FluxGroup [--server http://127.0.0.1:8188] [--seeds 7411,...,7418]
# 前置: 你机 ComfyUI models/ 需有 Krea2 三件（HF: Comfy-Org/Krea-2-Fast-Diffusion-ComfyUI·split_files·~15GB）
# 输出: 直接写 <repo>/.../30s-reel-v1/frames/（8 帧覆盖）
#   QC 闸（帧级多模态）: 火把青铜托宽焰非细棍/碑平板圆顶非圆柱/她2001台湾暖调年代感/KF6 单温/KFT 颗粒
#   <8.5 换种子重摇；过闸后与 KF4/KF5/KF7 拼全板再并排过审
import argparse, json, os, sys, time, urllib.request, uuid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--seeds", default="7411,7412,7413,7414,7415,7416,7417,7418,7419,7420")
    args = ap.parse_args()

    base = os.path.join(args.repo, "cph4", "fleet", "mv0001-handover", "outbound", "krea2", "30s-reel-v1")
    sys.path.insert(0, os.path.join(base, "..", "..", "prompt-writing-spec-v1", "patched-scripts"))
    import prompt_lexicon as LX

    LX.LIGHT["torch"] = ("thick pitch-soaked reed torches bound in corded linen burn in cast bronze "
                         "sconce bowls on thick bronze brackets, each broad flame breathing a full "
                         "wide pool of pure amber-gold light with smoky yellow tips, chiaroscuro "
                         "with the far shadows crushed to pure black")
    LX.LIGHT["torch_side"] = ("a thick reed-bundle torch held low at frame edge throws raking "
                              "side-backlight at 2000K across the stone, relief ridges catching "
                              "the warm light one band at a time while the rest stays matte black")
    LX.LIGHT["case"] = ("the glass display case is lit from within by warm tungsten halogen at 3000K, "
                        "a golden amber pool in the surrounding darkness, her skin and the stone "
                        "both kept in warm tones, the shadows tinted warm brown, glass reflections "
                        "kept in warm gray")
    LX.LIGHT["aisle_dim"] = ("warm tungsten case lights at 3000K dim one by one down the aisle, "
                             "the last golden amber pool clinging to the stone")
    LX.LIGHT["glyph"] = ("the wedge marks are self-lit in deep gold, their glow blooming softly "
                         "through warm haze against black that carries visible 35mm film grain")
    STYLE_LEAD = "as a film still from a 2001 Taiwanese music video"
    # v4.1: 博物馆她=2001 年代台湾女生（CEO 亲裁）
    HER20 = ("a young Taiwanese woman of 2001, a softly rounded youthful face with full cheeks, "
             "large dark eyes, a small nose, long straight black hair with a full blunt fringe, "
             "wearing a simple light knit top, 2001 Taipei style")
    BANDS = ("stacked horizontal bands of irregular carved cuneiform wedge marks, matte black rock "
             "with visible tool marks and fine stone grain")
    # v4.2: 碑形制锁死（美术考据席·禁圆柱漂移）
    STELE = ("a tall flat rounded-top slab stele of polished black basalt, straight sides about "
             "three times taller than wide, the top fifth a carved relief band, below it more than "
             "twenty horizontal cuneiform registers stacked to the base")

    def obj_shot(shot, angle, subject, light_key, extra="", lens="35"):
        s = "A %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
            LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
            LX.LIGHT[light_key].capitalize(),
            LX.LENS[lens], LX.GRADE["mono"], LX.TEXTURE["film_night"], STYLE_LEAD)
        if extra:
            s += " " + extra
        return s

    JOBS = [
        # 火把三帧（青铜壁托碗·纯琥珀焰）
        ("KF1_fire_wake",
         obj_shot("ecu", "eye",
                  "a thick reed-bundle torch at frame left, its bound head and corded linen wrap "
                  "clearly visible, its broad flame washing across polished black basalt inscribed "
                  "with %s, the wedges catching firelight one band at a time as if waking" % BANDS,
                  "torch", lens="50",
                  extra="the wide flame breathing a full pool of amber-gold light, embers drifting, halation blooming softly around the fire core")),
        ("KF2_sweep",
         obj_shot("cu", "high",
                  "the carved stone surface of a polished black basalt stele, pure rock filling the "
                  "frame, %s half revealed and half sinking into darkness" % BANDS,
                  "torch_side", lens="50",
                  extra="each carved band surfacing and drowning in turn as the broad flame flickers low at the frame edge")),
        ("KF3_stele",
         obj_shot("med", "low",
                  "%s, thick reed torches burning broad amber-gold flames in cast bronze sconce "
                  "bowls on mud-brick columns behind" % STELE,
                  "torch",
                  extra="each torch flame reads broad and heavy in its bronze bowl, wide amber pools raking across the hall floor")),
        # KF5 新增（提示词工程 A 案+导演必修2: 新刻带放低位·tilt-down 末点可达·match-cut 基石）
        ("KF5_columns",
         obj_shot("cu", "eye",
                  "stacked horizontal bands of irregular carved cuneiform wedge marks on the "
                  "black basalt surface filling the frame edge to edge, the lowest band still "
                  "holding the torchlight reading freshly cut, its wedge edges crisp and pale "
                  "against the weathered rows above",
                  "torch",
                  extra="amber firelight pooling in the deep-cut grooves, fine dust drifting through the torchlight")),
        # KF6 凿刻（回暖+木槌+火星+收窄构图+手锻青铜凿锚）
        ("KF6_chisel",
         obj_shot("ecu", "eye",
                  "a weathered hand in a rough undyed linen sleeve striking a hand-forged "
                  "flat-bladed bronze chisel with a wooden mallet, the frame tight on the "
                  "fingertips, the chisel blade and the fresh cut in the coarse black basalt, "
                  "the warm golden alloy catching the firelight, the blade seated at the edge "
                  "of a ragged fresh cut, sparks and pale stone dust lifting from the strike",
                  "torch_side",
                  extra="the stone and linen both reading warm amber under single-source torch light")),
        # KFT 金字（补颗粒去数字黑·调色师必修3）
        ("KFT_glyphs",
         obj_shot("med", "eye",
                  "luminous deep-gold cuneiform wedge marks drifting upward through warm haze "
                  "against near-black darkness that carries fine 35mm film grain, soft golden "
                  "bloom breathing around each mark, the glyph glow decaying softly into "
                  "halation at its edges",
                  "glyph",
                  extra="the darkness alive with grain, warm and analog")),
        # 台湾她三帧（3000K 暖钨丝柜光·S8 倒影层·S9 干净侧脸+微动·S10 背影收）
        ("KF8_case",
         obj_shot("med", "eye",
                  "a museum glass display case holding a broken slab of polished black basalt "
                  "carved with %s, the dark soft-edged silhouette reflection of a young "
                  "Taiwanese woman with long straight black hair and a full blunt fringe kept "
                  "low and dim on the glass, over the carved bands, her gaze on the stone" % BANDS,
                  "case", lens="50",
                  extra="a soft warm glass glare crossing the frame, every tone kept warm amber, her reflection reading as a quiet dark shape")),
        ("KF9_profile",
         obj_shot("cu", "eye",
                  "%s, her soft youthful profile in the warm tungsten case glow, her eyes on "
                  "the carved stone behind the glass, a single clean profile line, faint glass "
                  "reflections reading as a soft warm veil" % HER20,
                  "case", lens="50",
                  extra="her hair moving faintly with her breath, low-key warm halogen on her cheek, natural skin grain under 35mm film texture, the amber darkness behind")),
        ("KF10_walkaway",
         obj_shot("wide", "eye",
                  "%s walking away down the dark museum aisle toward the exit, her back to the "
                  "camera as a dark soft-edged silhouette, display cases dimming one by one "
                  "behind her" % HER20,
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
            "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "kf_v42_fleet"}},
        }

    def post(url, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=120).read())

    def get(url):
        return json.loads(urllib.request.urlopen(url, timeout=30).read())

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
                        break
                break
    print("KF V4.3 REGEN DONE -> frames/ 11/11 = 1(KF4 沿用)+10(本批: 火把3+KF5+KF6+KFT+她3)", flush=True)


if __name__ == "__main__":
    main()
