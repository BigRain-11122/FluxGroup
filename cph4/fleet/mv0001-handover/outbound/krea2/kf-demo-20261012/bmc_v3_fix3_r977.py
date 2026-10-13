# -*- coding: utf-8 -*-
# bmc_v3_fix3_r977.py -- V3 修复第三轮 (QC-r977 判负四帧定向手术)
# QC-r977 verdict: SIL1 石色暖褐错 / SIL2 泥板刻痕不可辨 / SIL4 anime 断裂 2.0 一票否决 /
#   SING3b 表演 cue 未中 (头未抬唇未开)。本批 = 原基座 + v2 补丁累积 + v3 手术增量 + 换 seed。
# 手术律: 零否定词 (prompt-writing-spec v1 正面描述律) · 单句散文 · subject 加权前置。
# SING1_v2 8.0 / SIL3_v2 7.5 = 锁定候选不入本批 (勿过迭代)。
# 血统: bmc_v3_fix_r977.py verbatim 范式 (nf helpers + kf_graph 1344x768 jman0.6 + 幂等 skip)。
import os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as nf

BMC = os.path.join(HERE, "bmc")
SERVER = "http://127.0.0.1:8188"
NEWKF_PACK = os.path.join(HERE, "V3-NEWKF-PACK-v1.md")

# (输出镜位id, 基座镜位id, seed, v2_patches, v3_patches) -- v2 补丁全量继承 (单命中断言)
JOBS = [
    ("SIL1_stele_backlit_v3", "SIL1_stele_backlit", 9015,
     [("a towering black basalt stele in a torch-lit Babylonian chamber",
       "a towering monolith of deep black basalt — dense dark volcanic stone reading almost pure black — in a torch-lit Babylonian chamber"),
      ("Iron torches burn low in wall sconces flanking the stele, their flames the only light sources,",
       "Two heavy iron wall-sconce torches flank the stele, each a plain iron bracket holding one slim flame that rises straight upward on a smooth continuous base with a soft orange core, the left flame slightly taller than the right, and these flames are the only light sources,"),
      ("while the stele's carved face glows faint amber",
       "while the stele's carved rows of cuneiform wedges glow faint amber in sharp legible relief, each incised stroke throwing its own small shadow"),
      ("Camera: static medium-wide shot at chest height, 35mm lens, the figure weighted low in the frame.",
       "Camera: static medium-wide shot at chest height, 35mm lens with a shallow cinematic focus plane held on the figure, the chamber walls falling softly out of focus, the figure weighted low in the frame.")],
     [("while the stele's carved rows of cuneiform wedges glow faint amber in sharp legible relief, each incised stroke throwing its own small shadow",
       "while the stele's flat uncarved stone stays deep near-black volcanic basalt reading almost pure black even where the torchlight grazes it, only the carved rows of cuneiform wedges glowing faint amber in sharp legible relief, each incised stroke throwing its own small shadow"),
      ("the left flame slightly taller than the right, and these flames are the only light sources,",
       "the left flame slightly taller than the right, both flames kept small and low so their glow reaches the carved rows yet leaves the stone mass itself in darkness,")]),

    ("SIL2_ots_crowd_v3", "SIL2_ots_crowd", 9016,
     [("her calm face turned three-quarter toward a small carved stone tablet cradled in her hands, her eyes lowered onto the carved words while the crowd moves around her",
       "her calm face turned three-quarter downward toward a small dark clay tablet cradled in both hands, its surface densely carved with rows of varied cuneiform wedges — nail-heads, hooks and tails in many different shapes — incised deep so every stroke throws a tiny shadow downward into its own hollow, her eyes resting fully on those carved words, her gaze holding the tablet alone while the crowd moves around her")],
     [("her calm face turned three-quarter downward toward a small dark clay tablet cradled in both hands,",
       "her calm face turned three-quarter downward toward a dark clay tablet held up at her chest in the near foreground of the frame, the tablet large and close enough that its carved face reads clearly, cradled in both hands,"),
      ("her eyes resting fully on those carved words, her gaze holding the tablet alone while the crowd moves around her",
       "a warm shaft of market torchlight falling across the tablet's carved face so every wedge reads in sharp relief, her eyes resting fully on those carved words, her gaze holding the tablet alone while the crowd moves around her")]),

    ("SIL4_crowd_edge_v3", "SIL4_crowd_edge", 9017,
     [("a white-haired old man and a small child",
       "a white-haired old man and a small child, both reading as real photographic human silhouettes with natural proportions"),
      ("Lighting: the case's cool spotlight cone as the single main light,",
       "Lighting: the case's cool spotlight cone as the single main light, the cone falling off softly at its edges with a faint drift of dust in the beam,"),
      ("Style: shot on Kodak Vision 5279 35mm film in 2001, telecine transfer, amber over crushed black, fine organic grain, authentic 2001 Taiwanese music video cinematography.",
       "Style: shot on Kodak Vision 5279 35mm film in 2001, telecine transfer, continuous photographic tonality rendered as live-action cinema, amber over crushed black, fine organic grain across the whole frame, soft halation around the case lamp, authentic 2001 Taiwanese music video cinematography.")],
     [("In a dim museum hall at night two visitors stand in silhouette before the glowing display case",
       "A live-action 35mm film still photographed inside a dim museum hall at night: two real visitors stand in silhouette before the glowing display case"),
      ("a white-haired old man and a small child, both reading as real photographic human silhouettes with natural proportions",
       "a white-haired old man and a small child, both actual people of true adult and child body proportions, their faces kept as soft unlit shadows,")]),

    ("SING3b_morning_song_open_v3", "SING3_morning_song", 9016,
     [("singing the last note under his breath with his head easing from slightly lifted down toward the page: his jaw and throat easing downward as the note settles",
       "singing a soft open note with his head tilted gently upward toward the window: his lips parted in a relaxed oval, his jaw and throat opening lightly toward the light, a quiet breath of song rising")],
     [("a fountain pen resting loose in his hand above a page of crossed-out lyrics",
       "his fountain pen set down on a page of crossed-out lyrics, both his hands resting open and still on the desk edge,"),
      ("Camera: static close-up in profile at eye level, 50mm lens, shallow focus on the profile edge.",
       "Camera: static close-up in profile at eye level, 50mm lens, shallow focus held sharp on his lifted chin, his parted lips and the open line of his throat.")]),
]


def io_read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def parse_newkf():
    t = io_read(NEWKF_PACK)
    out = {}
    for m in re.finditer(r"### (SIL[1-4]_\w+|SING[1-3]_\w+)（[^\n]*）\n\n(.*?)(?=\n\n### |\n\n## )",
                        t, re.S):
        out[m.group(1)] = m.group(2).strip()
    assert len(out) == 7, "NEWKF pack parse got %d sections" % len(out)
    return out


def build_fix_prompt(base, patch_sets, mid):
    prose = base
    for patches in patch_sets:
        for old, new in patches:
            assert prose.count(old) == 1, "[%s] patch anchor not single-hit: %r (count=%d)" % (
                mid, old[:60], prose.count(old))
            prose = prose.replace(old, new)
    return prose


def kf_graph_fix(prompt_text, seed, prefix):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"lora_name": "jman_v1_rank32.safetensors", "strength_model": 0.6, "model": ["10", 0]}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "simple", "denoise": 1.0, "model": ["15", 0], "positive": ["6", 0],
                "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }


def burn_one(out_id, prose, seed):
    dst = os.path.join(BMC, "%s_s%d_hd.png" % (out_id, seed))
    if os.path.isfile(dst) and os.path.getsize(dst) > 500000:
        nf.log("[fix3 %s s%d] SKIP (exists %dKB)" % (out_id, seed, os.path.getsize(dst) // 1024))
        return dst
    pid = nf.http_json(SERVER + "/prompt", {"prompt": kf_graph_fix(prose, seed, "bmc_v3kf_fix3"),
                                            "client_id": "bmc-v3kf-fix3-r977"})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(5)
        h = nf.http_json(SERVER + "/history/" + pid, timeout=30)
        if pid not in h:
            continue
        for nid, out in h[pid]["outputs"].items():
            for img in out.get("images", []):
                data = urllib.request.urlopen("%s/view?filename=%s&subfolder=%s&type=%s" % (
                    SERVER, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                    timeout=180).read()
                open(dst, "wb").write(data)
                nf.log("[fix3 %s s%d] SAVED %dKB (%.0fs)" % (out_id, seed, len(data) // 1024, time.time() - t0))
                return dst
            break
        break
    nf.log("[fix3 %s s%d] FAIL after %.0fs" % (out_id, seed, time.time() - t0))
    return None


def build_board(saved):
    from PIL import Image, ImageDraw
    tw, th = 480, 274
    cells = [(j[0], j[2]) for j in JOBS]
    rows = [cells[:2], cells[2:]]
    board = Image.new("RGB", (2 * tw + 3 * 8, 2 * th + 3 * 16 + 8), (12, 12, 12))
    d = ImageDraw.Draw(board)
    for r, row in enumerate(rows):
        for c, (mid, sd) in enumerate(row):
            d.text((8 + c * (tw + 8), r * (th + 16) + 2), "%s s%d" % (mid, sd), fill=(220, 200, 150))
            p = saved.get((mid, sd))
            if p:
                board.paste(Image.open(p).resize((tw, th)), (8 + c * (tw + 8), r * (th + 16) + 16))
    dst = os.path.join(BMC, "V3-FIX3-BOARD-r977_q88.jpg")
    q = 88
    while True:
        board.save(dst, "JPEG", quality=q)
        if os.path.getsize(dst) <= 1000000 or q <= 55:
            break
        q -= 6
    nf.log("FIX3 BOARD SAVED %s (%dKB q%d, imgs=%d/4)" % (
        dst, os.path.getsize(dst) // 1024, q, len(saved)))


def main():
    nf.log("=== V3 FIX3 r977 start: 4 surgical reshakes (QC-r977 verdicts) ===")
    base = parse_newkf()
    saved = {}
    for out_id, src_id, sd, v2p, v3p in JOBS:
        prose = build_fix_prompt(base[src_id], [v2p, v3p], out_id)
        p = burn_one(out_id, prose, sd)
        if p:
            saved[(out_id, sd)] = p
    build_board(saved)
    nf.log("V3 FIX3 r977 COMPLETE: %d/4" % len(saved))
    if len(saved) < 4:
        sys.exit(1)


if __name__ == "__main__":
    main()
