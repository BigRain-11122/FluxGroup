# -*- coding: utf-8 -*-
# kfpb_i2v_manifest_c2146.py - author the KF-PACK-B i2v manifests (C2146)
# Emits two manifests next to the album i2v runner:
#   run-bmc-packB-i2v.json        production 768P, one entry per approved B frame
#   run-bmc-packB-verify480.json  the 480P verification slice (3 shots) fired first
# Every unit is validated before the files are written: the first frame must exist
# on disk at production size, the prompt must sit inside the word band, carry a
# camera-dimension clause, and stay free of negation / audio / emotion-label words.
import io, json, os, re, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "local-i2v")
KF_DIR = "media/MV/mv0001/xingqing"

WORLD = ("Taiwan countryside around the Taitung-Danshui hills, 2000 era, "
         "faded single centre line road, golden grass fields, a small tin-and-brick farmhouse")

UNITS = [
    {
        "id": "XQ_B-S3-17", "shot": "S3-17", "track": "XQ",
        "win_s": 6.4, "speed": 0.95, "src_s": 6.74, "policy_band": "5s", "light": "dusk",
        "frame": KF_DIR + "/xq-kf-s317-feet-c2145/KFPB_MP_S3-17_feet_s266291.png",
        "lyric_anchor": "手牽手 一步兩步三步四步 望著天 (95.58-101.36)",
        "prompt": ("Locked-off low close-up on two pairs of feet. Two pairs of feet step along the faded "
                   "white centre line in a counting rhythm, four shoes landing one after another, dusk dust "
                   "lifting at each contact, the white paint bright underfoot. The camera stays still on the "
                   "ground and lets the stepping carry the frame. Preserve the 35mm film grain and the warm "
                   "dusk telecine palette."),
        "note": "Numbers-metre beat: the counting rhythm IS the shot, so the frame holds and the feet do the moving. Anchor = SHOTLIST v3 S3-17, frame = the C2145 re-roll that replaced the failed full-body two-shot.",
    },
    {
        "id": "XQ_B-S1-08", "shot": "S1-08", "track": "XQ",
        "win_s": 6.0, "speed": 1.05, "src_s": 5.71, "policy_band": "5s", "light": "noon",
        "frame": KF_DIR + "/xq-kf-packb-mainpass-c2144/KFPB_MP_S1-08_hands_s726816.png",
        "lyric_anchor": "一片雲 掉落在我面前 (38.52-43.22)",
        "prompt": ("Tight side close-up held on a steady frame. Her hands grip the bicycle handlebar, the "
                   "knuckles flexing once as the front wheel finds a rut, the loose school shirt billowing and "
                   "snapping in the warm wind, grass blades streaking past at the frame edge. Her face sits "
                   "outside the crop. The camera holds with a very small drift at a slightly quickened pace. "
                   "Preserve the 35mm film grain and the warm 2001 telecine palette."),
        "note": "Wind-through-fabric beat under the falling-cloud lyric. Handlebar is the true contact point per the Chinese shot cell (the English cell was corrected in C2145).",
    },
    {
        "id": "XQ_B-S3-21", "shot": "S3-21", "track": "XQ",
        "win_s": 8.76, "speed": 0.95, "src_s": 9.22, "policy_band": "8-15s", "light": "dusk",
        "frame": KF_DIR + "/xq-kf-packb-mainpass-c2144/KFPB_MP_S3-21_lookup_s129686.png",
        "lyric_anchor": "看遠方的星 如果聽得見 (133.31-138.00)",
        "prompt": ("Steady medium close-up. She lowers her head for a half beat, the corner of her mouth "
                   "lifting first, then she raises her eyes to him and holds them there. Warm dusk backlight "
                   "rims her hair and the edge of her cheek, the near eye catching one small highlight. The "
                   "camera holds with a very small drift, letting the half-beat land. Preserve the 35mm film "
                   "grain and the 2001 telecine palette."),
        "note": "Look-up beat played as observable sequence (mouth corner first, then eyes) instead of an emotion word. Long window so the half beat is not rushed.",
    },
    {
        "id": "XQ_B-S5-31", "shot": "S5-31", "track": "XQ",
        "win_s": 10.0, "speed": 0.88, "src_s": 11.36, "policy_band": "8-15s", "light": "night",
        "frame": KF_DIR + "/xq-kf-packb-mainpass-c2144/KFPB_MP_S5-31_twoshot_s323825.png",
        "lyric_anchor": "看星星 一顆兩顆三顆四顆 連成線 (209.36-214.68)",
        "prompt": ("Steady close two-shot under the night sky. The two of them turn to face each other, her "
                   "hand finding his, the thumbs pressing once before both hold, the shoulders settling a "
                   "notch. Cool starlight falls on warm skin while a faint lamp edge warms the near cheek. The "
                   "camera holds with a small drift, letting the pair breathe in one slow take. Preserve the "
                   "35mm film grain and the 2001 telecine palette."),
        "note": "Line-closing hand hold (the motif that opened at S0-03). Longest B window; slowest speed so the hand contact reads before the cut to the final sky card.",
    },
    {
        "id": "XQ_B-EX1", "shot": "B-EX1", "track": "XQ",
        "win_s": 3.0, "speed": 1.0, "src_s": 3.0, "policy_band": "5s", "light": "dusk",
        "inset_into": "S3-21", "frame": KF_DIR + "/xq-kf-packb-mainpass-c2144/KFPB_MP_B-EX1_spool_s143992.png",
        "lyric_anchor": "看遠方的星 如果聽得見 (133.31-138.00)",
        "prompt": ("Locked-off medium close-up. Her fingertips hover a half beat above the wooden kite spool, "
                   "then take the line and wind it two slow turns against the pull of the wind, her gaze fixed "
                   "past the frame edge. Dusk backlight rims her forearm and the taut line. The camera stays "
                   "still and lets the winding carry the movement. Preserve the 35mm film grain and the warm "
                   "dusk telecine palette."),
        "note": "Insert, not a standalone window: at assembly it takes 3.0s out of the hosting S3-21 window (133.6-136.6s), matching the listening line. Shotlist places both B extras inside chorus 1.",
    },
    {
        "id": "XQ_B-EX2", "shot": "B-EX2", "track": "XQ",
        "win_s": 3.0, "speed": 1.0, "src_s": 3.0, "policy_band": "5s", "light": "dusk",
        "inset_into": "S3-20", "frame": KF_DIR + "/xq-kf-packb-mainpass-c2144/KFPB_MP_B-EX2_occl_s204921.png",
        "lyric_anchor": "背對背 默默許下心願 (128.20-132.82)",
        "prompt": ("Locked-off close-up at shoulder height. She stands with her back to the lens and folds her "
                   "arm across, her fingers hooking the hem of his jacket so the fabric creases over her wrist. "
                   "His eyes lower toward her hand, then lift to her face, both heads at the same height. The "
                   "camera stays still and holds the two of them. Preserve the 35mm film grain and the 2001 "
                   "telecine palette."),
        "note": "Insert into S3-20 at assembly (129.0-132.0s) on the wish line. The occluded-hand anchor is the one that finally rendered after two failed hand close-ups.",
    },
]

VERIFY = [
    {"id": "XQ_VERIFY-S3-17", "src_unit": "XQ_B-S3-17", "why": "pack B close-up: counting feet, dense motion"},
    {"id": "XQ_VERIFY-S5-31", "src_unit": "XQ_B-S5-31", "why": "two-shot: face identity across a hand hold"},
    {"id": "XQ_VERIFY-S2-10", "src_unit": "XQ_A-S2-10", "why": "landscape: grass field holds under a slow drift"},
]

A_UNITS = [
    {
        "id": "XQ_A-S2-10", "shot": "S2-10", "track": "XQ",
        "win_s": 8.0, "speed": 1.0, "src_s": 8.0, "policy_band": "8-15s", "light": "noon",
        "frame": KF_DIR + "/abatch/S2-10_s20072.png",
        "lyric_anchor": "在著你彷彿在這陽光 (54.28-59.68)",
        "prompt": ("Wide landscape under high noon sun. The golden grass field runs to the horizon on both "
                   "sides of a faint white path, the stalks bending as a slow breeze crosses the field in one "
                   "visible wave from the near edge to the far edge. The camera holds with a very small drift "
                   "and lets the field breathe. Preserve the 35mm film grain and the 2001 telecine palette."),
        "note": "Verification-only landscape. Not part of the B production wave; the A-pack already has its own manifest.",
    },
]

NEG = re.compile(r"\b(no|not|never|without|avoid|none|nothing)\b", re.I)
AUDIO = re.compile(r"\b(sound|audio|music|ambient|song|singing|voice)\b", re.I)
EMO = re.compile(r"\b(happy|sad|joy|joyful|shy|nervous|angry|loving|sorrow|excited)\b", re.I)


def check_prompt(p):
    words = len(p.split())
    problems = []
    if not (40 <= words <= 90):
        problems.append("word band %d outside 40-90" % words)
    if "camera" not in p.lower():
        problems.append("missing camera-dimension clause")
    for rx, tag in ((NEG, "negation"), (AUDIO, "audio"), (EMO, "emotion label")):
        m = rx.search(p)
        if m:
            problems.append("%s word: %s" % (tag, m.group(0)))
    return words, problems


def build(units, wave, policy, gate):
    out, total_win = [], 0.0
    for u in units:
        fp = os.path.join(REPO, u["frame"].replace("/", os.sep))
        if not os.path.isfile(fp):
            raise SystemExit("MISSING FRAME %s" % fp)
        size = os.path.getsize(fp)
        if size < 500000:
            raise SystemExit("FRAME TOO SMALL %s (%d)" % (fp, size))
        words, problems = check_prompt(u["prompt"])
        if problems:
            raise SystemExit("PROMPT %s: %s" % (u["id"], "; ".join(problems)))
        item = dict(u)
        item["prompt"] = "%s. %s LIT_BY_%s. %s" % (
            WORLD, u["prompt"], u["light"].upper(), u.get("closing", "35mm film grain, telecine texture, 2001 Taiwan music video look"))
        item.pop("closing", None)
        item["i2v_prompt"] = item.pop("prompt")
        item["frame_bytes"] = size
        item["prompt_words"] = words
        total_win += float(u["win_s"])
        out.append(item)
    doc = {"policy": policy, "gate": gate, "wave": wave, "total": len(out),
           "total_win_s": round(total_win, 2), "units": out}
    return doc


def main():
    b_doc = build(
        UNITS, "packB-i2v",
        "KF-PACK-B (6 approved frames, verdict xq-KFPB-MAINPASS-VERDICT-c2144.md) burned as i2v for the A+B assembly. Production size 1344x768 int8, 768P only after the 480P verification slice passes.",
        "verdict c2144 section 5 no.2 (i2v may fire only after the coverage board exists: xq-KF-COVERAGE-c2145.json) + SHOTLIST v3 camera cues + CEO audio ban (pure picture, no native audio)")

    v_units = []
    pool = {u["id"]: u for u in UNITS + A_UNITS}
    for v in VERIFY:
        base = dict(pool[v["src_unit"]])
        base["id"] = v["id"]
        base["verify_of"] = v["src_unit"]
        base["verify_why"] = v["why"]
        v_units.append(base)
    v_doc = build(
        v_units, "packB-verify480",
        "480P verification slice per the efficiency law: three representative shots (close-up / two-shot / landscape) burned at 672x384 int4 and read for motion and identity drift BEFORE any 768P production wave.",
        "same gate as packB-i2v; clips land in their own out dir so a verification file can never be mistaken for a production clip")

    for name, doc in (("run-bmc-packB-i2v.json", b_doc), ("run-bmc-packB-verify480.json", v_doc)):
        p = os.path.join(PKG, name)
        data = json.dumps(doc, ensure_ascii=False, indent=1)
        json.loads(data)  # pre-write gate: never leave a half-valid manifest
        io.open(p, "w", encoding="utf-8", newline="\n").write(data + "\n")
        print("WROTE %s units=%d win=%.2fs bytes=%d" % (name, doc["total"], doc["total_win_s"], len(data)))

    print("MANIFEST-END ok=2")


if __name__ == "__main__":
    main()