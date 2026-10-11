# -*- coding: utf-8 -*-
# kf_fix_trial.py - 火把+女主修正低清试验批（CEO 判负 10-10 11:5x「火把像火柴棍，女主不像那个年代的台湾女生」）
# 修正锚:
#   火把: thin-stick 病→粗束火把（苇捆+麻绳绑扎+宽焰呼吸·物理尺度锚）
#   女主: 西亞直鼻锚→2001 年代台湾女生（圆润脸颊/大眼/小鼻/黑长直发+厚重齐刘海·J1/V3 年代女星型血统）
import json, time, os, urllib.request, uuid, sys

LEX = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\prompt-writing-spec-v1\patched-scripts"
sys.path.insert(0, LEX)
import prompt_lexicon as LX

LX.LIGHT["torch_bundle"] = ("thick pitch-soaked reed torches bound in corded linen burn in iron sconces, "
                           "each broad flame breathing a full wide pool of amber light, "
                           "chiaroscuro with the far shadows crushed to pure black")
LX.LIGHT["case"] = ("the glass display case glows from within at 2900K, a warm amber pool "
                    "in the surrounding darkness, reflections layered on the glass surface")

# 2001 台湾女生 ID（年代女星型血统·背影侧影档）
HER_TW01 = ("a young Taiwanese woman of 2001, a softly rounded youthful face with full cheeks, "
            "large dark eyes, a small nose, long straight black hair with a full blunt fringe, "
            "wearing a simple knit top, 2001 Taipei style")

BANDS = "stacked horizontal bands of irregular carved cuneiform wedge marks"

STYLE_LEAD = "as a film still from a 2001 Taiwanese music video"


def obj_shot(shot, angle, subject, light_key, extra="", lens="35", grade="mono", texture="film_night"):
    s = "A %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
        LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
        LX.LIGHT[light_key].capitalize(),
        LX.LENS[lens], LX.GRADE[grade], LX.TEXTURE[texture], STYLE_LEAD)
    if extra:
        s += " " + extra
    return s


JOBS = [
    # S1 v2: 宽焰束把火光洗过刻痕行
    ("S1_fire_bundle",
     obj_shot("ecu", "eye",
              "a broad torch flame of %s washing across polished black basalt inscribed with %s, "
              "the wedges catching firelight one band at a time as if waking" % (
                  "a thick reed-bundle torch", BANDS),
              "torch_bundle",
              extra="the flame fills the upper frame edge with a wide breathing glow, embers drifting, halation blooming softly around the fire core",
              lens="50")),
    # S3 v2: 铁壁架粗束火把+石碑
    ("S3_stele_bundle",
     obj_shot("med", "low",
              "a tall polished black basalt stele standing upright, a carved relief at the crown above "
              "the stacked bands of cuneiform, thick reed torches burning wide in iron sconces on "
              "mud-brick columns behind",
              "torch_bundle",
              extra="each torch flame reads broad and heavy, wide amber pools raking across the hall floor")),
    # S9 v2: 2001 台湾女生隔玻璃侧影
    ("S9_her_tw01",
     obj_shot("cu", "eye",
              "%s seen through museum glass, her soft youthful profile lit by the warm case glow, "
              "large dark eyes lowered toward the stone, the dark slab of carved black basalt behind "
              "the glass in the same frame" % HER_TW01,
              "case",
              lens="85",
              extra="her full blunt fringe covers her brows, her lowered gaze resting on the carved bands, the glass holding her faint young reflection and the words together")),
    # S8 v2: 2001 台湾女生倒影
    ("S8_her_tw01",
     obj_shot("med", "eye",
              "a museum glass display case holding a broken slab of black basalt etched with %s, and "
              "%s, her dark soft-edged silhouette reflection kept low and dim on the glass, her "
              "reflection overlapping the carved bands" % (BANDS, HER_TW01),
              "case",
              lens="50",
              extra="a soft glass glare crossing over her features, her young reflection reading as a quiet dark shape over the ancient words")),
]

W, H = 672, 384
SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\fix-trial"
os.makedirs(OUT, exist_ok=True)


def graph(prompt_text, seed):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "simple", "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0],
                "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "kf_fix_trial"}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())


def main():
    for i, job in enumerate(JOBS):
        name, p = job
        s = 7200 + i
        hits = LX.lint(p, mode="t2i")
        if hits:
            print("LINT-FAIL", name, hits, flush=True)
    print("=== lint done ===", flush=True)
    for i, job in enumerate(JOBS):
        name, p = job
        s = 7200 + i
        pid = post(SERVER + "/prompt", {"prompt": graph(p, s), "client_id": str(uuid.uuid4())})["prompt_id"]
        t0 = time.time()
        while time.time() - t0 < 600:
            time.sleep(2)
            h = get(SERVER + "/history/" + pid)
            if pid in h:
                for node_id, node_out in h[pid]["outputs"].items():
                    for img in node_out.get("images", []):
                        data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                            "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=60).read()
                        open(os.path.join(OUT, name + ".png"), "wb").write(data)
                        print("SAVED %s (%.0fs)" % (name, time.time() - t0), flush=True)
                        break
                break
    print("FIX TRIAL DONE", flush=True)


if __name__ == "__main__":
    main()
