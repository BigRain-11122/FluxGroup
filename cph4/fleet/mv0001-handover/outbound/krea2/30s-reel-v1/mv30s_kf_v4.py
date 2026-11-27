# -*- coding: utf-8 -*-
# mv30s_kf_v4.py - 30s重制 v4 关键帧批（本地 Krea 2 t2i）
# 依据: 30s-立意案-v4-定稿（两路一手深研+whisper实测锚点并入后）
# 机制: prompt_lexicon 词表+官方顺序单段散文+lint 三名单（对象镜头走本脚本 obj_shot 组装）
# CEO 硬律: 黑色玄武岩·背影侧影·全片琥珀单色统一调·运镜=i2v提示词内调度·关键帧到位过五维检
import json, time, os, urllib.request, uuid, sys

LEX = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\prompt-writing-spec-v1\patched-scripts"
sys.path.insert(0, LEX)
import prompt_lexicon as LX

# 扩充词表（消费侧扩展·不改正典文件）
LX.LIGHT["torch"] = ("wall torches burn at 2000K, their amber pools the only light, "
                     "chiaroscuro with the far shadows crushed to pure black")
LX.LIGHT["torch_side"] = ("a torch held low at frame edge throws raking side-backlight at 2000K "
                          "across the stone face, relief ridges catching the light one band at a time "
                          "while the rest sinks into pure black")
LX.LIGHT["case"] = ("the glass display case glows from within at 2900K, a warm amber pool "
                    "in the surrounding darkness, reflections layered on the glass surface")
LX.LIGHT["aisle_dim"] = ("warm case lights at 2900K dim one by one down the aisle, "
                         "the last amber pool clinging to the stone")
LX.LIGHT["glyph"] = ("the wedge marks are self-lit in deep gold, their light blooming softly "
                     "through warm haze against pure black")

# ---- 西亞面孔女主（CEO 22:2x 定谳·背影侧影档·不露正脸） ----
HER_SIL = ("a young woman with long black center-parted hair and a fine straight-nosed "
           "profile line, seen only as a dark soft-edged silhouette")
HER_PROF = ("her dark side profile softly lit by the warm case glow, long black "
            "center-parted hair, deep-set eyes lowered toward the stone, seen through glass")

STYLE_LEAD = "as a film still from a 2001 Taiwanese music video"


def obj_shot(shot, angle, subject, light_key, extra="", lens="35", grade="mono", texture="film_night"):
    """对象镜头组装（官方顺序变体·无人物）：主体+材质→光→镜头风格收尾。全部正向措辞。"""
    s = "A %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
        LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
        LX.LIGHT[light_key].capitalize(),
        LX.LENS[lens], LX.GRADE[grade], LX.TEXTURE[texture], STYLE_LEAD)
    if extra:
        s += " " + extra
    return s


BASALT = "polished black basalt"
BANDS = "stacked horizontal bands of irregular carved cuneiform wedge marks running tight across the face"

JOBS = [
    # S1 火光唤醒刻痕（macro·「字是活过的痕迹」）
    ("KF1_fire_wake",
     obj_shot("ecu", "eye",
              "a torch flame edge brushing across %s inscribed with %s, the wedges "
              "catching firelight one band at a time as if waking" % (BASALT, BANDS),
              "torch",
              extra="a shallow fire-breathing flicker on the stone surface, blackness swallowing everything beyond the flame",
              lens="50")),
    # S2 火把侧逆光扫碑面（浮雕半明半暗·逐行显出）
    ("KF2_sweep",
     obj_shot("cu", "eye",
              "the carved face of %s, %s half revealed and half sinking into darkness" % (BASALT, BANDS),
              "torch_side",
              lens="50",
              extra="the light rakes across relief ridges, each carved band surfacing and drowning in turn")),
    # S3 完整石碑全貌（火把大厅·权威）
    ("KF3_stele",
     obj_shot("med", "low",
              "a tall black basalt stele standing upright, a carved relief at the crown above "
              "the stacked bands of cuneiform continuing down the whole face",
              "torch",
              extra="the stele fills the frame with authoritative stillness, mud-brick columns dissolving into darkness behind")),
    # S4 碑顶浮雕特写（立姿王者向端坐神祇·授律）
    ("KF4_crown",
     obj_shot("cu", "low",
              "the carved crown relief of the stele showing a standing bearded king raising his hand "
              "before a seated god who extends a rod and ring",
              "torch",
              lens="85",
              extra="firelight crawling over the two carved figures, their forms surfacing from black stone")),
    # S5 法典铭文带层（楔形字横带叠满·tilt-down 起点）
    ("KF5_columns",
     obj_shot("cu", "eye",
              "%s filling the frame edge to edge, each band of %s dense and regular" % (BASALT, BANDS),
              "torch",
              lens="50",
              extra="the wedge marks sharp and deep-cut, amber firelight pooling in the carved grooves")),
    # S6 铜凿咬石（ECU·「刻」是动作·麻衣袖·火光侧照）
    ("KF6_chisel",
     obj_shot("ecu", "eye",
              "a weathered hand driving a bronze chisel into %s, fresh wedge marks forming under "
              "the tip, fine black stone chips lifting from the cut" % BASALT,
              "torch_side",
              extra="the hand wears a rough undyed linen sleeve, firelight raking across the struck surface")),
    # S7 大厅拉远起点（碑立于大厅·光柱尘埃·黑暗吞边）
    ("KF7_hall",
     obj_shot("ext", "eye",
              "the black basalt stele standing small at the center of a vast Babylonian "
              "hall of mud-brick columns, torch pools on the floor, a single hard light "
              "shaft above it full of drifting dust",
              "godray",
              lens="24",
              extra="darkness pressing in from all edges, the hall swallowing itself in shadow")),
    # T 金字显形（转场资产·原版标志语言）
    ("KFT_glyphs",
     obj_shot("med", "eye",
              "carved cuneiform wedge marks lifting gently off a black background, the wedges "
              "becoming luminous deep-gold marks drifting upward in warm haze",
              "glyph",
              extra="soft golden bloom around each mark, the darkness breathing behind them")),
    # S8 玻璃柜+她的倒影（「你在橱窗前」·注视链种子）
    ("KF8_case",
     obj_shot("med", "eye",
              "a museum glass display case holding a broken slab of %s etched with %s, "
              "and %s reflected on the glass surface, her reflection overlapping the carved bands" % (BASALT, BANDS, HER_SIL),
              "case",
              lens="50",
              extra="her reflection reads as a quiet dark ghost over the ancient words, warm glow pooling around the stone")),
    # S9 隔玻璃侧影（「我却在旁静静欣赏你」·镜头=他的注视）
    ("KF9_profile",
     obj_shot("cu", "eye",
              "%s, the dark slab of carved black basalt behind the glass in the same frame" % HER_PROF,
              "case",
              lens="85",
              extra="her lowered gaze rests on the carved bands, the glass holding her faint reflection and the words together")),
    # S10 走远+灯熄+字存（「灯灭了字还亮」·背影收）
    ("KF10_walkaway",
     obj_shot("wide", "eye",
              "a young woman with long black center-parted hair walking away down the dark museum "
              "aisle toward the exit, her back to the camera as a dark soft-edged silhouette, "
              "display cases dimming one by one behind her",
              "aisle_dim",
              lens="35",
              extra="one case still holds a faint amber pool around a broken black stone slab, the carved bands catching the last warm light")),
]

W, H = 1344, 768
SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\kf-v4"
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "mv30s_kf4"}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())


def run_one(name, prompt_text, seed):
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(3)
        h = get(SERVER + "/history/" + pid)
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR %s" % name, flush=True); return
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=60).read()
                    fn = os.path.join(OUT, name + ".png")
                    open(fn, "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0), flush=True)
                    return
    print("TIMEOUT " + name, flush=True)


def main():
    seeds = iter(range(7301, 7301 + len(JOBS) * 4, 4))  # 预留重摇位
    ok = True
    for name, p in JOBS:
        hits = LX.lint(p, mode="t2i")
        if hits:
            print("LINT-FAIL %s: %s" % (name, hits), flush=True)
            ok = False
    if not ok:
        print("=== lint failed, abort ===", flush=True)
        return
    print("=== lint all pass (%d jobs), generating ===" % len(JOBS), flush=True)
    for name, p in JOBS:
        run_one(name, p, next(seeds))
    print("KF-V4 DONE %d" % len(JOBS), flush=True)


if __name__ == "__main__":
    main()
