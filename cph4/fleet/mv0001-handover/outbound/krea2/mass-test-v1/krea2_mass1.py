# -*- coding: utf-8 -*-
# krea2_mass1.py - mass prompt test: 5 hero scenes x3 seeds + 8 scene variants + 8 quality probes
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\mass1"
os.makedirs(OUT, exist_ok=True)

NO_TEXT = "Absolutely no readable modern text, no typography, no letters, no logos, no watermark, pure imagery only."
B = ("cinematic film still from a 2001 music video, warm amber monochrome color grading with deep shadows, "
     "single motivated torch light, subtle 35mm film grain, ancient Babylonian Mesopotamian world, solemn and mysterious mood. " + NO_TEXT)

HERO_CARVE = ("Extreme close-up macro shot: a scribe's weathered hand pressing a triangular-cut reed stylus into a wet clay tablet, "
              "fresh wedge-shaped cuneiform strokes forming in neat rows on the clay surface, coarse clay texture with fingerprints, "
              "razor-thin depth of field focused on the freshly carved wedge, warm torch key light from the right side, "
              "floating dust motes in the light beam, ancient Babylonian night. " + B)
HERO_GODDESS = ("A woman in a flowing white gown fading into existence within dying torchlight inside an ancient Babylonian temple corridor, "
                "her backlit silhouette half-materialized like light made flesh, soft halation bloom around the light, embers drifting, "
                "volumetric incense smoke, symmetrical columns receding into darkness, 85mm full shot, soft focus. " + B)
HERO_LIBRARY = ("An ancient Babylonian library archive at night, an elderly scribe with grey beard and wrapped headcloth writing at a wooden desk "
                "lit by two clay oil lamps with open flames, arched shelves of clay tablets receding into darkness behind him, and faintly superimposed "
                "like an in-camera double exposure the translucent profile of a young modern man gazing over the scribe's shoulder from two thousand "
                "years away, deep chiaroscuro, shallow depth of field. " + B)
HERO_CASE = ("A museum archive aisle at night, a glowing glass display case holding a carved cuneiform stone stele, a girl's silhouette standing at "
             "the glass with her faint reflection beside the stele, a young man watching her from behind over her shoulder with longing, rim light "
             "spilling from the case, shelf rows creating parallax, the cool glass-blue light of the case as the only cold accent in the warm amber "
             "scene, 50mm medium close-up, shallow depth of field. " + B)
HERO_GLASS = ("A museum display glass where a modern young woman's face is reflected while an ancient Babylonian cuneiform carving shows through the "
              "glass behind her, two eras in one frame as in-camera double exposure, her fingertips hovering near the glass, a cyan glass sheen as the "
              "only cold accent in the warm amber grade, soft halation, 50mm medium close-up. " + B)

JOBS = []
# Layer A: 5 hero scenes x 3 seeds (consistency test)
for i, s in enumerate([7001, 7002, 7003]):
    JOBS.append(("A_carve_s%d" % i, HERO_CARVE, s))
for i, s in enumerate([7101, 7102, 7103]):
    JOBS.append(("A_goddess_s%d" % i, HERO_GODDESS, s))
for i, s in enumerate([7201, 7202, 7203]):
    JOBS.append(("A_library_s%d" % i, HERO_LIBRARY, s))
for i, s in enumerate([7301, 7302, 7303]):
    JOBS.append(("A_case_s%d" % i, HERO_CASE, s))
for i, s in enumerate([7401, 7402, 7403]):
    JOBS.append(("A_glass_s%d" % i, HERO_GLASS, s))
# Layer B: 8 scene variants / coverage
JOBS.append(("B_s1_study", "An ancient study at night, a lone scribe silhouette writing at a wooden desk, single clay oil lamp with open flame as the only light, "
             "top light cone on the open clay tablet, low-key chiaroscuro, 35mm medium shot, deep shadows swallowing the room. " + B, 7501))
JOBS.append(("B_s3_temple", "A vast Babylonian temple interior, a priestess silhouette standing still in thick incense smoke, symmetrical columns, "
             "shafts of light falling through the smoke from a high opening, relief-carved walls, 24mm wide shot, deep space. " + B, 7502))
JOBS.append(("B_s5_strata", "A desert strata cross-section with a buried clay tablet among layered sediment, an Assyrian relief band running through the strata, "
             "golden-hour side light raking the texture, 35mm wide, deep focus, drifting sand particles. " + B, 7503))
JOBS.append(("B_s6_unearth", "A dark chamber lit by a single torch, a clay tablet half-uncovered in sand, an archaeologist's brush revealing carved cuneiform signs, "
             "hard key light from upper left, deep shadows, 50mm medium shot, volumetric glow. " + B, 7504))
JOBS.append(("B_s7_magnifier", "A modern desk at night, a magnifying glass over an old photograph of a cuneiform tablet, and faintly double-exposed over it "
             "an ancient hand carving the same tablet, tungsten lamp pool of light, 85mm close-up, the sharpest frame of the film. " + B, 7505))
JOBS.append(("B_s4_carve_medium", "A young scribe hunched at work in a stone chamber, torch on the wall, rows of finished clay tablets stacked beside him, "
             "he presses a reed stylus into a wet tablet, deep concentration, 35mm medium shot. " + B, 7506))
JOBS.append(("B_s8_glass_reflect", "A museum display glass at night where a woman's modern reflection and the ancient cuneiform carving behind the glass are equally "
             "visible, strong glass surface with faint fingerprints and a cyan sheen as the only cold accent, warm amber grade, 50mm close-up. " + B, 7507))
JOBS.append(("B_s9_dyinglamp", "The ancient study at night again, the clay oil lamp dying down to a last ember, a closed-eye profile of the scribe in the afterglow, "
             "darkness closing in, closing vignette, 35mm medium shot, black-gold ember palette. " + B, 7508))
# Layer C: 8 quality probes (in-world)
JOBS.append(("C_p1_eyes", "Extreme close-up of a young woman's eyes in dying torchlight, warm amber light catching skin texture and fine pores, "
             "long eyelashes, reflection of a small flame in the iris, 100mm macro, razor-thin depth of field. " + B, 7601))
JOBS.append(("C_p2_hands", "Two weathered ancient hands holding a wet clay tablet with rows of crisp wedge-shaped cuneiform, visible knuckle wrinkles and "
             "calluses, warm torch light raking across, 85mm close-up. " + B, 7602))
JOBS.append(("C_p3_claymacro", "Macro shot of a wet clay surface, fresh glistening wedge-shaped cuneiform strokes in neat rows, the tip of a reed stylus "
             "entering the frame corner, torch light from the left, 100mm macro. " + B, 7603))
JOBS.append(("C_p4_crowd", "A vast Babylonian temple hall filled with rows of scribes working at clay desks, dozens of small oil lamps, shafts of torch smoke "
             "through the hall, wide establishing shot, deep focus. " + B, 7604))
JOBS.append(("C_p5_rainglass", "Night rain running down a museum glass case, water droplets refracting warm lamp light into bokeh, the dim shape of a cuneiform "
             "stele inside, cool blue night tones against warm interior glow, 50mm close-up. " + B, 7605))
JOBS.append(("C_p6_embers", "Close-up of embers and sparks drifting upward through dark air, warm orange bokeh circles, deep black background, "
             "high-speed photographic feel. " + B, 7606))
JOBS.append(("C_p7_ruins", "Wide shot of desert ruins at golden hour, a half-buried Assyrian relief wall catching raking light, wind-blown sand drifting, "
             "heat haze on the horizon, 24mm wide. " + B, 7607))
JOBS.append(("C_p8_silhouette", "Full-body silhouette of a man holding a raised torch in a dark stone corridor, volumetric dust in the torch beam, "
             "strong rim light, 35mm wide shot, minimal composition. " + B, 7608))

W, H = 1344, 768

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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "krea2_mass1"}},
    }

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())

def run_one(name, prompt_text, seed):
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 1200:
        time.sleep(3)
        h = get(SERVER + "/history/" + pid)
        if pid in h:
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=60).read()
                    fn = os.path.join(OUT, name + ".png")
                    open(fn, "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0))
                    return
    print("TIMEOUT " + name)

def main():
    for name, p, s in JOBS:
        run_one(name, p, s)
    print("MASS1 DONE %d images" % len(JOBS))

main()
