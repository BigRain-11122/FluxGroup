# -*- coding: utf-8 -*-
# kf_v4_fix.py - 关键帧重摇批（专家评审点名4帧·字面歧义与材质锚修正）
# 病灶: KF2 "carved face at eye level" 被字面读成脸 → 改"surface/high angle"; KF6 规则齿槽读作金属 → ragged/coarse 锚;
#       KF4 浮雕读浅色石膏 → near-black matte 锚; KF8 倒影五官过清(背影侧影律边缘) → dark soft-edged + glare crossing
import json, time, os, urllib.request, uuid, sys

LEX = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\prompt-writing-spec-v1\patched-scripts"
sys.path.insert(0, LEX)
import prompt_lexicon as LX

LX.LIGHT["torch"] = ("wall torches burn at 2000K, their amber pools the only light, "
                     "chiaroscuro with the far shadows crushed to pure black")
LX.LIGHT["torch_side"] = ("a torch held low at frame edge throws raking side-backlight at 2000K "
                          "across the stone, relief ridges catching the light one band at a time "
                          "while the rest stays matte black")
LX.LIGHT["case"] = ("the glass display case glows from within at 2900K, a warm amber pool "
                    "in the surrounding darkness, reflections layered on the glass surface")
STYLE_LEAD = "as a film still from a 2001 Taiwanese music video"


def obj_shot(shot, angle, subject, light_key, extra="", lens="35", grade="mono", texture="film_night"):
    s = "A %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
        LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
        LX.LIGHT[light_key].capitalize(),
        LX.LENS[lens], LX.GRADE[grade], LX.TEXTURE[texture], STYLE_LEAD)
    if extra:
        s += " " + extra
    return s


HER_SIL = ("a young woman with long black center-parted hair, her dark soft-edged silhouette "
           "reflection kept low and dim on the glass")

BANDS = ("stacked horizontal bands of irregular carved cuneiform wedge marks, matte black rock "
         "with visible tool marks and fine stone grain")

JOBS = [
    ("KF2_sweep",
     obj_shot("cu", "high",
              "the carved stone surface of a polished black basalt stele, pure rock filling the frame, %s "
              "half revealed and half sinking into darkness" % BANDS,
              "torch_side",
              lens="50",
              extra="each carved band surfacing and drowning in turn, restrained matte highlights, the rock coarse-grained and ancient"),
     7401),
    ("KF4_crown",
     obj_shot("cu", "low",
              "the crown relief of a black basalt stele carved near-black in the amber light: a standing "
              "bearded king raising his hand before a seated god extending a rod and ring, the stone "
              "reading matte and deep",
              "torch",
              lens="85",
              extra="firelight crawling over the two carved figures, their forms surfacing from near-black stone, restrained amber highlights on the edges"),
     7402),
    ("KF6_chisel",
     obj_shot("ecu", "eye",
              "a weathered hand in a rough undyed linen sleeve driving a bronze chisel into a coarse "
              "black basalt block, the chisel tip wedged into a ragged fresh cut, pale stone dust and "
              "coarse chips lifting from the strike",
              "torch_side",
              extra="the surrounding rock surface uneven and rough-grained with older hand-struck marks, firelight raking across the struck face"),
     7403),
    ("KF8_case",
     obj_shot("med", "eye",
              "a museum glass display case holding a broken slab of polished black basalt etched with "
              "%s, and %s, her dim reflection overlapping the carved bands" % (BANDS, HER_SIL),
              "case",
              lens="50",
              extra="a soft glass glare crossing over her features, her reflection reading as a quiet dark shape over the ancient words"),
     7404),
]

W, H = 1344, 768
SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\kf-v4"


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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "mv30s_kf4fix"}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())


def run_one(name, prompt_text, seed):
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(3)
        h = get(SERVER + "/history/" + pid)
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR %s" % name, flush=True); return
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=60).read()
                    open(os.path.join(OUT, name + ".png"), "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0), flush=True)
                    return
    print("TIMEOUT " + name, flush=True)


def main():
    for name, p, s in JOBS:
        hits = LX.lint(p, mode="t2i")
        if hits:
            print("LINT-FAIL %s %s" % (name, hits), flush=True); continue
        print("PASS %s" % name, flush=True)
    for name, p, s in JOBS:
        run_one(name, p, s)
    print("FIX DONE %d" % len(JOBS), flush=True)


if __name__ == "__main__":
    main()
