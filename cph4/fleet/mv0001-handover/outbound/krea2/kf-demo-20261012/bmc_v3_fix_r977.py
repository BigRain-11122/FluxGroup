# -*- coding: utf-8 -*-
# bmc_v3_fix_r977.py -- O-20261013 ORD 21:2x/21:5x @bm-c V3 修复批 (白名单 v1.4 修复单)
# 导演席帧审定谳: SIL1 spec收紧重烧 / SIL2 泥板补刻+视线落点 / SIL3 碑面压暗 /
#   SIL4 风格断裂整帧重烧(胶片实拍锚全套·同 seed s9013) / SING1 焰基+纯侧影 /
#   SING3b_morning_song_open 补烧 (SING3 保留晨写铺垫镜·同机位同灯同 seed s9012)
# 血统: bmc_v3_fullres_r972.py verbatim 范式 (nf helpers + kf_graph 1344x768 jman0.6)
#   · 幂等 skip-if-exists · 串行 FIFO · patch 全部 single-hit assert (词源审计律)
# i2v 点火 = 白名单 v1.4 全签后 (本批只烧帧·零视频·音轨禁令照旧)
import os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as nf  # __main__ guard in place

BMC = os.path.join(HERE, "bmc")
SERVER = "http://127.0.0.1:8188"
NEWKF_PACK = os.path.join(HERE, "V3-NEWKF-PACK-v1.md")

# 修复批 6 帧 (导演席 21:2x 修单 + 21:5x 五席汇总 SIL1 spec 收紧 + 白名单 v1.4 §二)
# 命名律: _v2 后缀不覆盖正档原帧 (史保) · SING3b = 新镜位
JOBS = [
    # (输出镜位id, 基座镜位id, seed, patches[(old, new), ...])
    ("SIL1_stele_backlit_v2", "SIL1_stele_backlit", 9011, [
        ("a towering black basalt stele in a torch-lit Babylonian chamber",
         "a towering monolith of deep black basalt — dense dark volcanic stone reading almost pure black — in a torch-lit Babylonian chamber"),
        ("Iron torches burn low in wall sconces flanking the stele, their flames the only light sources,",
         "Two heavy iron wall-sconce torches flank the stele, each a plain iron bracket holding one slim flame that rises straight upward on a smooth continuous base with a soft orange core, the left flame slightly taller than the right, and these flames are the only light sources,"),
        ("while the stele's carved face glows faint amber",
         "while the stele's carved rows of cuneiform wedges glow faint amber in sharp legible relief, each incised stroke throwing its own small shadow"),
        ("Camera: static medium-wide shot at chest height, 35mm lens, the figure weighted low in the frame.",
         "Camera: static medium-wide shot at chest height, 35mm lens with a shallow cinematic focus plane held on the figure, the chamber walls falling softly out of focus, the figure weighted low in the frame."),
    ]),
    ("SIL2_ots_crowd_v2", "SIL2_ots_crowd", 9013, [
        ("her calm face turned three-quarter toward a small carved stone tablet cradled in her hands, her eyes lowered onto the carved words while the crowd moves around her",
         "her calm face turned three-quarter downward toward a small dark clay tablet cradled in both hands, its surface densely carved with rows of varied cuneiform wedges — nail-heads, hooks and tails in many different shapes — incised deep so every stroke throws a tiny shadow downward into its own hollow, her eyes resting fully on those carved words, her gaze holding the tablet alone while the crowd moves around her"),
    ]),
    ("SIL3_case_rim_v2", "SIL3_case_rim", 9013, [
        ("standing close before the glass case where a black basalt stele glows faint amber",
         "standing close before the glass case where a black basalt stele rests in near-black darkness, its stone face dark and dense with only the carved band holding the faintest amber glow, the stone's weathered pale rim narrowing to a hairline along its edges"),
        ("on the glass surface floats the faint reflection of a young West Asian woman with long dark center-parted hair, her soft face in three-quarter view",
         "on the glass surface floats a very faint reflection of a young West Asian woman with long dark center-parted hair, her soft face barely brighter than the dark glass, in three-quarter view"),
    ]),
    ("SIL4_crowd_edge_v2", "SIL4_crowd_edge", 9013, [
        ("a white-haired old man and a small child",
         "a white-haired old man and a small child, both reading as real photographic human silhouettes with natural proportions"),
        ("Lighting: the case's cool spotlight cone as the single main light,",
         "Lighting: the case's cool spotlight cone as the single main light, the cone falling off softly at its edges with a faint drift of dust in the beam,"),
        ("Style: shot on Kodak Vision 5279 35mm film in 2001, telecine transfer, amber over crushed black, fine organic grain, authentic 2001 Taiwanese music video cinematography.",
         "Style: shot on Kodak Vision 5279 35mm film in 2001, telecine transfer, continuous photographic tonality rendered as live-action cinema, amber over crushed black, fine organic grain across the whole frame, soft halation around the case lamp, authentic 2001 Taiwanese music video cinematography."),
    ]),
    ("SING1_torch_song_v2", "SING1_torch_song", 9013, [
        ("iron torches burning behind him on both sides, a small clay oil lamp at the stele's base",
         "two iron sconce torches burning steadily behind him on both sides, each flame rooted tight to its wick on a smooth continuous base and rising as a single unbroken plume, a small clay oil lamp at the stele's base"),
        ("a hard golden rim tracing his profile edge and the tilt of his head, halation blooming large around the two torch flames",
         "his whole face held in pure black silhouette with the front of his face kept fully dark, a hard golden rim tracing only his profile edge and the tilt of his head, halation blooming large around the two torch flames"),
    ]),
    ("SING3b_morning_song_open", "SING3_morning_song", 9012, [
        ("singing the last note under his breath with his head easing from slightly lifted down toward the page: his jaw and throat easing downward as the note settles",
         "singing a soft open note with his head tilted gently upward toward the window: his lips parted in a relaxed oval, his jaw and throat opening lightly toward the light, a quiet breath of song rising"),
    ]),
]


def parse_newkf():
    t = io_read(NEWKF_PACK)
    out = {}
    for m in re.finditer(r"### (SIL[1-4]_\w+|SING[1-3]_\w+)（[^\n]*）\n\n(.*?)(?=\n\n### |\n\n## )",
                        t, re.S):
        out[m.group(1)] = m.group(2).strip()
    assert len(out) == 7, "NEWKF pack parse got %d sections" % len(out)
    return out


def io_read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def build_fix_prompt(base, patches, mid):
    prose = base
    for old, new in patches:
        assert prose.count(old) == 1, "[%s] patch anchor not single-hit: %r (count=%d)" % (
            mid, old[:60], prose.count(old))
        prose = prose.replace(old, new)
    return prose


def kf_graph_fix(prompt_text, seed, prefix):
    # bmc_v3_fullres_r972.kf_graph_hd verbatim (1344x768 正档 · jman 0.6)
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
        nf.log("[fix %s s%d] SKIP (exists %dKB)" % (out_id, seed, os.path.getsize(dst) // 1024))
        return dst
    pid = nf.http_json(SERVER + "/prompt", {"prompt": kf_graph_fix(prose, seed, "bmc_v3kf_fix"),
                                            "client_id": "bmc-v3kf-fix-r977"})["prompt_id"]
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
                nf.log("[fix %s s%d] SAVED %dKB (%.0fs)" % (out_id, seed, len(data) // 1024, time.time() - t0))
                return dst
            break
        break
    nf.log("[fix %s s%d] FAIL after %.0fs" % (out_id, seed, time.time() - t0))
    return None


def build_board(saved):
    from PIL import Image, ImageDraw
    tw, th = 480, 274
    cells = [(j[0], j[2]) for j in JOBS]
    rows = [cells[:3], cells[3:]]
    board = Image.new("RGB", (3 * tw + 4 * 8, 2 * th + 3 * 16 + 8), (12, 12, 12))
    d = ImageDraw.Draw(board)
    for r, row in enumerate(rows):
        for c, (mid, sd) in enumerate(row):
            d.text((8 + c * (tw + 8), r * (th + 16) + 2), "%s s%d" % (mid, sd), fill=(220, 200, 150))
            p = saved.get((mid, sd))
            if p:
                board.paste(Image.open(p).resize((tw, th)), (8 + c * (tw + 8), r * (th + 16) + 16))
    dst = os.path.join(BMC, "V3-FIX-BOARD-r977_q88.jpg")
    q = 88
    while True:
        board.save(dst, "JPEG", quality=q)
        if os.path.getsize(dst) <= 1000000 or q <= 55:
            break
        q -= 6
    nf.log("FIX BOARD SAVED %s (%dKB q%d, imgs=%d/6)" % (
        dst, os.path.getsize(dst) // 1024, q, len(saved)))


def main():
    nf.log("=== V3 FIX r977 start: 6 fix frames @1344x768 jman0.6 (whitelist v1.4 修单) ===")
    base = parse_newkf()
    saved = {}
    for out_id, src_id, sd, patches in JOBS:
        prose = build_fix_prompt(base[src_id], patches, out_id)
        p = burn_one(out_id, prose, sd)
        if p:
            saved[(out_id, sd)] = p
    build_board(saved)
    nf.log("V3 FIX r977 COMPLETE: %d/6 fix frames" % len(saved))
    if len(saved) < 6:
        sys.exit(1)


if __name__ == "__main__":
    main()
