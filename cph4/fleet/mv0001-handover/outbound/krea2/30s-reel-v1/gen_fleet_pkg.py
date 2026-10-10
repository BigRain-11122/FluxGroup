# -*- coding: utf-8 -*-
# gen_fleet_pkg.py - 生成机队本地 H3 i2v 派单包（CEO 令 2026-10-10「让机队其他机器本地跑视频」）
# 产物: ①h3_i2v_local_768p_v4.json(bm-c 768P t2v→i2v 补丁版·含 LoadImage16+first_frame)
#       ②local_h3_i2va_v4.json(11 镜清单: frame/prompt(I2VA 三字段)/seed/规格)
# 全部提示词过 prompt_lexicon lint 三名单·音轨禁令合规(纯画面+提示词删氛围声)
import json, os, sys

LEX = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\prompt-writing-spec-v1\patched-scripts"
sys.path.insert(0, LEX)
import prompt_lexicon as LX

OUT_CANON = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
WF_SRC = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\h3-local-test\h3_t2v_local_768p_bmc.json"

# 词表扩展（与关键帧批同源·v4.1 火把道具律=粗束苇把宽焰）
LX.LIGHT["torch"] = ("thick pitch-soaked reed torches bound in corded linen burn in iron sconces, "
                     "each broad flame breathing a full wide pool of amber light, "
                     "chiaroscuro with the far shadows crushed to pure black")
LX.LIGHT["torch_side"] = ("a thick reed-bundle torch held low at frame edge throws raking "
                          "side-backlight at 2000K across the stone, relief ridges catching "
                          "the light one band at a time while the rest stays matte black")
LX.LIGHT["case"] = ("the glass display case glows from within at 2900K, a warm amber pool "
                    "in the surrounding darkness, reflections layered on the glass surface")
LX.LIGHT["aisle_dim"] = ("warm case lights at 2900K dim one by one down the aisle, "
                         "the last amber pool clinging to the stone")
LX.LIGHT["glyph"] = ("the wedge marks are self-lit in deep gold, their light blooming softly "
                     "through warm haze against pure black")

# v4.1: 博物馆她=2001 年代台湾女生（CEO 亲裁 10-10）
HER20 = ("a young Taiwanese woman of 2001, a softly rounded youthful face with full cheeks, "
         "large dark eyes, a small nose, long straight black hair with a full blunt fringe, "
         "wearing a simple knit top, 2001 Taipei style")

ALIGN = ("For the target video, at 0.00 seconds into the target video, "
         "<Picture 1> (from [Shot 1]) is fully referenced.")


def i2va(shot, angle, move, action, scene, light, seed):
    desc = ("%s, %s. %s. %s. %s, %s." % (LX.SHOT_SIZE[shot], LX.CAM_ANGLE[angle],
             move, action, scene, LX.LIGHT[light].capitalize()))
    desc += (" %s, %s. Character identity, clothing, colors, key objects and spatial "
             "relationships remain consistent." % (LX.GRADE["mono"], LX.TEXTURE["film_night"]))
    s = (ALIGN + " integrated_multimodal_description: " + desc
         + " overall_soundscape: silence, the music video song is laid in post."
         + " non_diegetic_music: N/A (song laid in post)"
         + " About 5.0 seconds, 16:9 aspect.")
    hits = LX.lint(s, mode="video")
    if hits:
        raise SystemExit("LINT FAIL: %s" % hits)
    return s


SHOTS = [
    ("S1_fire_wake", "KF1_fire_wake", "ecu", "eye",
     "the camera holds a perfectly static shot",
     "a broad torch flame of a thick reed-bundle torch washes across polished black basalt "
     "inscribed with stacked bands of carved cuneiform wedges, the wide flame breathing as each "
     "band catches firelight in turn, fine dust drifting through the amber glow, soft halation "
     "blooming around the broad fire core",
     "in the deep darkness of an ancient Babylonian hall", "torch", 7801),
    ("S2_sweep", "KF2_sweep", "cu", "high",
     "the camera tracks laterally with small amplitude at slow speed",
     "the raking light of a thick reed-bundle torch slides across the stacked carved bands of a "
     "polished black basalt stele face, pure rock surface filling the frame, each band surfacing "
     "into light and drowning back into blackness as the broad flame flickers at the frame edge",
     "inside the torchlit Babylonian hall", "torch_side", 7802),
    ("S3_stele", "KF3_stele", "med", "low",
     "the camera pushes in with medium amplitude at slow speed",
     "a tall polished black basalt stele stands upright in the torchlit hall, carved relief at "
     "its crown above stacked cuneiform bands, thick reed torches burning broad amber flames in "
     "iron sconces, mud-brick columns dissolving into darkness as the stele grows larger in "
     "frame with quiet authority",
     "in the vast Babylonian hall", "torch", 7803),
    ("S4_crown", "KF4_crown", "cu", "low",
     "the camera holds a perfectly static shot",
     "amber firelight crawls slowly across the carved crown relief of the black basalt stele: "
     "a standing bearded king raising his hand before a seated god extending a rod and ring, "
     "their carved forms surfacing from near-black stone, soft halation around the torch glow",
     "at the crown of the stele in the torchlit hall", "torch", 7804),
    ("S5_columns", "KF5_columns", "cu", "eye",
     "the camera tilts down with medium amplitude at moderate speed",
     "the view slides steadily down stacked horizontal bands of carved cuneiform wedge marks "
     "filling the black basalt face edge to edge, amber firelight pooling in the deep-cut "
     "grooves, fine dust drifting through the torchlight, the tilt settling at its end on one "
     "band of freshly cut wedges, crisp and new against the weathered rows",
     "across the law-text face of the stele", "torch", 7805),
    ("S6_chisel", "KF6_chisel", "ecu", "eye",
     "the camera holds locked-off and still",
     "a weathered hand in a rough undyed linen sleeve drives a bronze chisel into coarse black "
     "basalt, the tip biting into a ragged fresh cut early in the take, pale stone dust and "
     "coarse chips lifting from the strike, firelight raking across the struck face",
     "at the stone face in the torchlit scriptorium", "torch_side", 7806),
    ("S7_hall", "KF7_hall", "ext", "eye",
     "the camera pulls out and cranes up with steady amplitude at moderate speed",
     "the black basalt stele shrinks at the center of the vast Babylonian hall as the camera "
     "rises and retreats, torch pools receding, a hard light shaft of drifting dust above it, "
     "darkness swallowing the space around it",
     "in the vast mud-brick hall", "godray", 7807),
    ("T_glyphs", "KFT_glyphs", "med", "eye",
     "the camera holds a perfectly static shot",
     "carved cuneiform wedge marks lift gently off a pure black background, becoming luminous "
     "deep-gold marks drifting slowly upward through warm haze, soft golden bloom breathing "
     "around each mark",
     "in deep darkness between two worlds", "glyph", 7808),
    ("S8_case", "KF8_case", "med", "eye",
     "the camera pushes in with small amplitude at moderate speed",
     "a museum glass display case lit from within by warm amber light holds a broken slab of "
     "black basalt carved with cuneiform bands, the dark soft-edged silhouette reflection of "
     "%s overlapping the carved words, the warm pool breathing around the stone" % HER20,
     "in the quiet dark museum archive", "case", 7809),
    ("S9_profile", "KF9_profile", "cu", "eye",
     "the camera holds a perfectly static shot",
     "seen through museum glass, the soft youthful profile of %s lit by the warm case glow, "
     "her large dark eyes lowered toward the stone, her full blunt fringe covering her brows, "
     "the faint amber reflection breathing on the glass surface" % HER20,
     "at the glass display case in the dark museum", "case", 7810),
    ("S10_walkaway", "KF10_walkaway", "wide", "eye",
     "the camera pulls out slowly with small amplitude",
     "%s walks away down the dark museum aisle toward the exit, her back to the camera as a "
     "dark silhouette, warm case lights dimming one by one behind her, the last amber pool "
     "clinging to a broken black stone slab" % HER20,
     "in the long dark museum aisle", "aisle_dim", 7811),
]


def main():
    # 1) I2VA 清单
    manifest = []
    for tag, frame, shot, angle, move, action, scene, light, seed in SHOTS:
        manifest.append({
            "tag": tag, "frame": "frames/%s.png" % frame, "seed": seed,
            "prompt": i2va(shot, angle, move, action, scene, light, seed),
            "length": 124, "width": 1344, "height": 768,
        })
    mf_path = os.path.join(OUT_CANON, "local_h3_i2va_v4.json")
    json.dump(manifest, open(mf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("manifest:", mf_path, len(manifest), "shots, lint all green")

    # 2) i2v 工作流（bm-c 768P t2v 补丁: +LoadImage16 → node6 first_frame）
    wf = json.load(open(WF_SRC, "r", encoding="utf-8"))
    assert wf["6"]["class_type"] == "MiniMaxH3ImageToVideo"
    wf["6"]["inputs"]["first_frame"] = ["16", 0]
    wf["16"] = {"class_type": "LoadImage", "inputs": {"image": "PLACEHOLDER.png"}}
    wf["15"]["inputs"]["filename_prefix"] = "mv30s_v4_fleet"
    wf_path = os.path.join(OUT_CANON, "h3_i2v_local_768p_v4.json")
    json.dump(wf, open(wf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("workflow:", wf_path)


if __name__ == "__main__":
    main()
