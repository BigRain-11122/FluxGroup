# -*- coding: utf-8 -*-
# kf_style_probe.py - 低清快速风格/提示词框架试验批（CEO 令 10-10 11:5x「本机也可以跑一些关键帧图，
# 不用高清的，快速跑去试风格和提示词框架什么的！让我多看多评估」）
# 设计: 3 个风格敏感镜(S1 火光唤醒/S3 石碑全貌/S8 玻璃柜+她的倒影) × 4 档调色/质感框架 = 12 张
# 分辨率 672×384(半幅=快)·8 步·每张 ~8-12s·总 ~3 分钟
import json, time, os, urllib.request, uuid, sys

LEX = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\prompt-writing-spec-v1\patched-scripts"
sys.path.insert(0, LEX)
import prompt_lexicon as LX

LX.LIGHT["torch"] = ("wall torches burn at 2000K, their amber pools the only light, "
                     "chiaroscuro with the far shadows crushed to pure black")
LX.LIGHT["case"] = ("the glass display case glows from within at 2900K, a warm amber pool "
                    "in the surrounding darkness, reflections layered on the glass surface")
LX.LIGHT["torch_lowkey"] = ("a single distant torch at 2000K hangs in the black, a minimal warm pool, "
                            "over eighty percent of the frame held in pure shadow")
LX.LIGHT["case_coldmilk"] = ("the glass display case is lit by cool archival fluorescents at 4300K mixed "
                             "with a faint warm spill, pale milky highlights on the glass")

# 四档风格框架（同一镜头·调色/光路/质感全换·全正向·lint 过）
GRADES = {
    "A_mono":   ("mono", "film_night", "torch",       "STYLE-A 琥珀单色·火把深黑·5279 颗粒（现正典）"),
    "B_tw2001": ("tw2001", "film_night", "torch",    "STYLE-B 2001 电视卡带感·乳白浮黑·高光晕开"),
    "C_lowkey": ("mono", "mist", "torch_lowkey",      "STYLE-C 极简单光源·8 成纯黑·雾面晕光"),
    "D_doc":    ("nost", "film_night", "case_coldmilk", "STYLE-D 档案纪实感·冷荧光+暖漏光·褪色调"),
}
# S8 档案馆镜的 D 档用冷柜光；古巴比伦镜的 D 档也用冷光做对照——按镜位换光
SCENES = {
    "S1": ("ecu", "eye",
           "a torch flame edge brushing across polished black basalt inscribed with stacked bands of "
           "carved cuneiform wedges, the wedges catching firelight one band at a time as if waking"),
    "S3": ("med", "low",
           "a tall polished black basalt stele standing upright, a carved relief at the crown above "
           "stacked bands of cuneiform, mud-brick columns dissolving into darkness behind"),
    "S8": ("med", "eye",
           "a museum glass display case holding a broken slab of black basalt etched with cuneiform "
           "bands, the dark soft-edged silhouette reflection of a young woman with long black "
           "center-parted hair overlapping the carved words"),
}
# S8 镜专属光映射（D 档冷光用 case_coldmilk，其余用暖柜光）
S8_LIGHT = {"A_mono": "case", "B_tw2001": "case", "C_lowkey": "case", "D_doc": "case_coldmilk"}

W, H = 672, 384
SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\style-probe"
os.makedirs(OUT, exist_ok=True)

JOBS = []
for sc_name, (shot, angle, subject) in SCENES.items():
    for g_name, (grade, texture, light, label) in GRADES.items():
        real_light = S8_LIGHT[g_name] if sc_name == "S8" and g_name != "C_lowkey" else (S8_LIGHT.get(g_name, light) if sc_name == "S8" else light)
        prompt = ("A %s of %s, %s. %s. Shot on %s, %s, %s, "
                  "as a film still from a 2001 Taiwanese music video." % (
            LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
            LX.LIGHT[real_light].capitalize(), LX.LENS["35"], LX.GRADE[grade], LX.TEXTURE[texture]))
        JOBS.append(("%s_%s" % (sc_name, g_name), prompt, 7000 + len(JOBS)))


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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "kf_style_probe"}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())


def main():
    bad = 0
    for name, p, s in JOBS:
        hits = LX.lint(p, mode="t2i")
        if hits:
            print("LINT-FAIL %s %s" % (name, hits), flush=True)
            bad += 1
    print("=== lint done bad=%d, generating %d ===" % (bad, len(JOBS) - bad), flush=True)
    t00 = time.time()
    for name, p, s in JOBS:
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
    print("STYLE PROBE DONE %d in %.0fs" % (len(JOBS), time.time() - t00), flush=True)


if __name__ == "__main__":
    main()
