# -*- coding: utf-8 -*-
# kf_fix2_fleet.py - v4.3.1 重制 10 帧生成（bm-c 执行版）
# 版本链: v4.1 火柴棍+台湾她修正 → v4.2 设计闸修正 → v4.3 六席 27 修项 → v4.3.1 第二波七席修项：
#   ①她的服装块三要素补齐（服装席 P0：S10 全身背影镜头下装零锚=修身韩系直通；宽松粗针织+低腰微喇牛仔+帆布鞋+斜背包）
#   ②KF6 三席合修（VFX：槌凿分离两件物+余震收尾；文字席：凿尖坐楔形字半笔；服装席：硬挺粗织亚麻版型）
#   ③KFT 金字成簇锚（文字席：纯三角无尾读作播放键；短列+三角头+长拖尾+成簇）
#   ④KF4 加回重制批（服装席：神像泛化——角冠+荷叶袍+裸肩丢失+rod/ring 融成单杖）
#   ⑤KF1 焰收画内留天头+焰根纯琥珀（VFX 席：焰尖出画必撕裂+蓝白焰根违零冷色律）
#   ⑥KF2 光源画外 implied（VFX 席 B 案：帧内无火把锚=视频凭空造火高危；观众零损失）
#   ⑦KF5 新刻带对比锚（文字席：短·疏·大楔新带 vs 密排旧带=match-cut 基石+S5→S6 并排比对）
#   ⑧BANDS 形态学正锚（文字席：三角压痕头+拖尾+成簇+带间刻线；同批 KF1 证明模型能力够缺的是锚）
#   ⑨交付卫生（文字席 P2-5：失败显式退出+帧齐断言；旧版静默跳过+计数矛盾根除）
# 用法: python kf_fix2_fleet.py --repo K:/Fluxgroup/FluxGroup [--server http://127.0.0.1:8188] [--seeds 7411,...,7420]
# 前置: 你机 ComfyUI models/ 需有 Krea2 三件（HF: Comfy-Org/Krea-2-Fast-Diffusion-ComfyUI·split_files·~15GB）
# 输出: 直接写 <repo>/.../30s-reel-v1/frames/（10 帧覆盖+KF7 沿用=11/11）
#   QC 闸（帧级多模态·六检·<8.5 换种子重摇）:
#     1 火把青铜托宽焰非细棍+焰根纯琥珀零蓝白
#     2 碑平板圆顶非圆柱+黑玄武岩非棕石灰岩
#     3 她 2001 台湾暖调年代感+宽松廓形（非修身韩系）
#     4 楔形文字检（正检=三角压痕头+拖尾·横行成带·带间细刻线·2-6 画成簇；三杀=随机划痕冒充/拉丁字母式排布/等宽机刻槽）
#     5 KF6 槌凿分离两件物+凿尖坐半笔楔形字
#     6 KFT 颗粒+金字成簇成字（非孤立三角）
import argparse, json, os, sys, time, urllib.request, uuid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--seeds", default="7411,7412,7413,7414,7415,7416,7417,7418,7419,7420")
    args = ap.parse_args()

    base = os.path.join(args.repo, "cph4", "fleet", "mv0001-handover", "outbound", "krea2", "30s-reel-v1")
    sys.path.insert(0, os.path.join(base, "..", "prompt-writing-spec-v1", "patched-scripts"))
    import prompt_lexicon as LX

    LX.LIGHT["torch"] = ("thick pitch-soaked reed torches bound in corded linen burn in cast bronze "
                         "sconce bowls on thick bronze brackets, each broad flame breathing a full "
                         "wide pool of pure amber-gold light with smoky yellow tips, chiaroscuro "
                         "with the far shadows crushed to pure black")
    LX.LIGHT["torch_side"] = ("a thick reed-bundle torch wedged in a cast bronze sconce bowl at the "
                              "lower frame edge throws raking side-backlight at 2000K across the "
                              "stone, wedge-cut grooves catching the warm light one band at a time "
                              "while the rest stays matte black")
    LX.LIGHT["torch_off"] = ("unseen torchlight from beyond the frame edge throws raking "
                             "side-backlight at 2000K across the stone, wedge-cut grooves catching "
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
    # v4.3.1: 她的服装块三要素（材质+版型+色名·服装席统一块·S9/S10 逐字复用）
    HER20 = ("a young Taiwanese woman of 2001, a softly rounded youthful face with full cheeks, "
             "large dark eyes, a small nose, long straight black hair with a full blunt fringe, "
             "wearing a loose oatmeal chunky-knit wool sweater with a soft round neckline and long "
             "sleeves reaching past her wrists, relaxed low-rise bootcut dark denim jeans, flat "
             "canvas shoes and a simple shoulder bag, un-fitted relaxed 2001 Taipei street style")
    BANDS = ("stacked horizontal bands of hand-cut cuneiform wedge marks, each sign a tight cluster "
             "of wedge strokes with clean triangular heads and tapering tails, thin ruled lines "
             "between rows, matte black rock with visible tool marks and fine stone grain")
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
        # 火把三帧（青铜壁托碗·纯琥珀焰·焰收画内）
        ("KF1_fire_wake",
         obj_shot("ecu", "eye",
                  "a thick reed-bundle torch at frame left, its bound head and corded linen wrap "
                  "clearly visible, its broad flame washing across polished black basalt inscribed "
                  "with %s, the carved bands breathing in the flickering firelight" % BANDS,
                  "torch", lens="50",
                  extra="the whole flame held inside the frame with clear headroom above the flame "
                        "tip, the flame base a solid amber-gold, embers drifting, halation blooming "
                        "softly around the fire core")),
        ("KF2_sweep",
         obj_shot("cu", "high",
                  "the carved stone surface of a polished black basalt stele, pure rock filling the "
                  "frame, %s half revealed and half sinking into darkness" % BANDS,
                  "torch_off", lens="50",
                  extra="each carved band surfacing and drowning in turn as the unseen torchlight "
                        "drifts slowly across the stone")),
        ("KF3_stele",
         obj_shot("med", "low",
                  "%s, thick reed torches burning broad amber-gold flames in cast bronze sconce "
                  "bowls on mud-brick columns behind" % STELE,
                  "torch",
                  extra="each torch flame reads broad and heavy in its bronze bowl, wide amber pools raking across the hall floor")),
        # KF4 冠部浮雕（服装席：神像衣冠还原+rod/ring 两件物·旧帧神像泛化判废）
        ("KF4_crown",
         obj_shot("cu", "low",
                  "the carved crown relief band of the black basalt stele: a standing bearded king "
                  "in a long fringed robe and a rolled-brim cap, his hand raised in salute before "
                  "a seated god wearing a horned tiara and a heavy flounced robe with one shoulder "
                  "bared, the god holding out a rod and a ring",
                  "torch",
                  extra="their carved forms surfacing from near-black stone, the god's rod and the "
                        "ring reading as two separate objects")),
        # KF5 新刻带（提示词工程+导演+文字席：短·疏·大楔新带低位·match-cut 基石）
        ("KF5_columns",
         obj_shot("cu", "eye",
                  "stacked horizontal bands of irregular carved cuneiform wedge marks on the "
                  "black basalt surface filling the frame edge to edge, the lowest band a short "
                  "sparse row of large fresh wedges, crisp pale triangular heads against the dense "
                  "weathered rows above",
                  "torch",
                  extra="amber firelight pooling in the deep-cut grooves, fine dust drifting through the torchlight")),
        # KF6 凿刻（VFX+文字+服装三席合修：槌凿分离+半笔楔形字+硬挺亚麻版型）
        ("KF6_chisel",
         obj_shot("ecu", "eye",
                  "a weathered hand in a loose sleeve of coarse stiff-woven undyed linen, the raw "
                  "frayed edge hanging in heavy unshaped folds, his bare forearm plain, gripping a "
                  "hand-forged flat-bladed bronze chisel with a wooden mallet raised clear of the "
                  "blade as two separate tools, the blade seated at the head of a half-cut "
                  "cuneiform wedge in a short fresh row of large pale wedges, crisp against the "
                  "coarse black basalt, pale stone dust lifting from the groove",
                  "torch_side",
                  extra="the stone and linen both reading warm amber under single-source torch "
                        "light, ample clear space above the raised mallet head, the bronze reading "
                        "hand-forged with hammer marks")),
        # KFT 金字（文字席：短列+三角头+长拖尾+成簇；调色席：颗粒去数字黑）
        ("KFT_glyphs",
         obj_shot("med", "eye",
                  "a short column of luminous deep-gold cuneiform signs drifting upward through "
                  "warm haze, each sign a tight cluster of wedges with triangular heads and long "
                  "tapering tails, soft golden bloom breathing around each sign, the glyph glow "
                  "decaying softly into halation at its edges",
                  "glyph",
                  extra="the darkness alive with grain, warm and analog")),
        # 台湾她三帧（3000K 暖钨丝柜光·S8 倒影剥衣子集·S9 干净侧脸+微动·S10 背影收）
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
                  extra="her profile holding perfectly steady with only her fringe stirring "
                        "faintly with her breath, low-key warm halogen on her cheek, natural "
                        "skin grain under 35mm film texture, the amber darkness behind")),
        ("KF10_walkaway",
         obj_shot("wide", "eye",
                  "%s walking away down the dark museum aisle toward the exit, her back to the "
                  "camera as a dark soft-edged silhouette, both feet clearly mid-stride small in "
                  "the wide frame, the nearest case light dimming then the one beyond it behind "
                  "her" % HER20,
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
        print("KF V4.3.1 REGEN INCOMPLETE, missing: %s" % ",".join(missing), flush=True)
        sys.exit(1)
    print("KF V4.3.1 REGEN DONE -> frames/ 11/11 = 1(KF7 沿用)+10(本批: 火把3+KF4+KF5+KF6+KFT+她3)", flush=True)


if __name__ == "__main__":
    main()
