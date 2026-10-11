# -*- coding: utf-8 -*-
# kf_v1_rebuild_bmc.py - meme V1《慢慢踩》五帧重产（bm-c 接管·2 轮兜底执法·O-20261011-1436 §2）
# 依据=PREPRO-V1.md v3.3 CERTIFIED §五帧规格（KF-P v2/KF-N v2 现实锚 2026 + S1/S3/S4 已过闸件重产）
# 律=J-M17 现代现实感锚/J-M1 品牌安全正面锚（plain blank 面板）/J-M18 提示词预检（LX.lint 全绿才点火）/J-M5 帧内动效锚预埋
# 输出: <repo>/media/meme-daily-v1/v1-zunjie-brake/frames/{KF_P,KF_N,S1,S3,S4}.png（768×1344 竖屏）
# 用法: python kf_v1_rebuild_bmc.py --repo K:/Fluxgroup/FluxGroup [--seeds 9101,9102,9103,9104,9105]
import argparse, json, os, sys, time, urllib.request, uuid

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--seeds", default="9101,9106,9107,9108,9109")
    ap.add_argument("--only", default="", help="逗号分隔仅重摇的帧名（空=全跑）")
    a = ap.parse_args()

    base = os.path.join(a.repo, "cph4", "fleet", "mv0001-handover", "outbound", "krea2", "prompt-writing-spec-v1", "patched-scripts")
    sys.path.insert(0, base)
    import prompt_lexicon as LX

    out_dir = os.path.join(a.repo, "media", "meme-daily-v1", "v1-zunjie-brake", "frames")
    os.makedirs(out_dir, exist_ok=True)

    JOBS = [
        ("KF_P",  # 拍1 发布会（2026 现实锚·大屏生成期留白·字后期合成）
         "A wide shot of a vast modern car launch keynote stage seen from the dark auditorium floor, at eye level. "
         "A giant ultra-dense LED wall fills the whole background, showing a smooth warm golden gradient field, its "
         "surface clean and unbroken. A matte black minimal stage holds a central low circular turntable, and on it "
         "a car fully covered by a smooth silk cloth, the covered mass reading clearly as a parked car. A lone "
         "speaker stands as a small back-lit silhouette far below the wall scale, one hand raised mid-sentence. Cool "
         "white digital spotlights cut thin light shafts through controlled haze, dark tiered audience rows soft out "
         "of focus in the foreground. Shot on 24mm lens, modern launch-film look, warm screen glow over deep blacks, fine grain."),
        ("KF_N",  # 拍5 深夜智能工厂（QC r1 修：看板留白防伪文字·AGV 真实尺寸·桌面真生活感）
         "A medium-wide shot of a bright white smart-factory night-shift floor, at eye level. Polished white epoxy "
         "flooring with crisp yellow safety lanes, a conveyor line carrying a plain unbranded bare car body shell "
         "with smooth blank panels, white robotic arms arranged around it mid-assembly, an AGV tug cart of "
         "realistic industrial size parked on the lane. An overhead electronic board shows a plain soft amber glow "
         "field, its surface smooth and unbroken, the only warm point in the frame, under dimmed cool-white LED "
         "high-bay lights. In the foreground right a lone engineer sits at a modern control console seen from "
         "behind in silhouette, a dented thermos and scattered papers on the desk. Glass-walled corridor and white "
         "ceiling trusses behind. Shot on 35mm lens, modern industrial documentary look, pressed low-saturation "
         "cool grade with one warm amber point, fine grain."),
        ("S1",  # 拍4 豪车广告（QC r1 修：无签名贯通简灯带·特征空白尾板）
         "A medium shot from a low rear three-quarter angle of a large unbranded black luxury MPV speeding along "
         "an elevated city highway at night. Its rear carries a smooth featureless tail panel with two simple slim "
         "horizontal red light bars, clean unmarked body panels, wet asphalt mirroring warm sodium streetlight "
         "pools, the city haze soft behind. Shot on 35mm lens, luxury car commercial look, deep warm blacks with "
         "blooming taillight highlights, fine grain."),
        ("S3",  # 拍3a 断裂微距（QC r1 修：粗糙撕裂断口+踏板语境·去装饰纹）
         "An extreme close-up of a steel brake pedal arm freshly snapped in two, the fracture face reading as "
         "rough torn metal with a coarse granular break surface and a thin bent lip where the steel stretched "
         "before giving way, fine metal dust lifted around the break, the rubber-tipped pedal pad just entering "
         "the frame edge. Warm hard side light over a deep dark workshop background, the steel surface plainly "
         "machined with honest wear scratches. Shot on a macro lens, industrial test documentary look, fine grain."),
        ("S4",  # 拍2+拍3b 测试场三台车（QC r1 修：侧profile 视角避开头尾签名·角度差破克隆）
         "A wide shot of three identical unbranded black MPVs parked in a staggered line on an empty "
         "proving-ground test track at warm dusk, seen in side profile, each car turned at a slightly different "
         "angle, their side panels smooth, featureless and clean. Orange traffic cones and a small test-equipment "
         "cart stand beside them, fine dust in the low warm light, long soft shadows on pale asphalt. Shot on "
         "35mm lens, documentary test-film look, warm dusk grade, fine grain."),
    ]

    seeds = [int(x) for x in a.seeds.split(",")]
    only = set(x.strip() for x in a.only.split(",") if x.strip())

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
            "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "meme_v1_kf"}},
        }

    def post(url, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=120).read())

    def get(url):
        return json.loads(urllib.request.urlopen(url, timeout=30).read())

    done = []
    for (name, p), seed in zip(JOBS, seeds):
        if only and name not in only:
            done.append(name)
            continue
        hits = LX.lint(p, mode="t2i")           # J-M18 预检：不过禁点火
        if hits:
            print("LINT-FAIL", name, hits, flush=True)
            sys.exit(2)
        pid = post(a.server + "/prompt", {"prompt": graph(p, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
        print("[%s] submitted seed=%d" % (name, seed), flush=True)
        t0 = time.time()
        while time.time() - t0 < 1800:
            time.sleep(3)
            h = get(a.server + "/history/" + pid)
            if pid in h:
                for nid, out in h[pid]["outputs"].items():
                    for img in out.get("images", []):
                        data = urllib.request.urlopen(
                            "%s/view?filename=%s&subfolder=%s&type=%s" % (
                                a.server, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                            timeout=60).read()
                        open(os.path.join(out_dir, name + ".png"), "wb").write(data)
                        print("[%s] SAVED %s.png (%.0fs)" % (name, name, time.time() - t0), flush=True)
                        done.append(name)
                        break
                break
    missing = [n for n, _ in JOBS if n not in done]
    if missing:
        print("MEME KF INCOMPLETE, missing: %s" % ",".join(missing), flush=True)
        sys.exit(1)
    print("MEME KF DONE -> %s (5 frames, 768x1344)" % out_dir, flush=True)

if __name__ == "__main__":
    main()
