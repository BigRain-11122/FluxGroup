# -*- coding: utf-8 -*-
# gen_fleet_pkg.py - 生成机队本地 H3 i2v 派单包（六席专家评审团必修全落地·v4.3 终版）
# 版本链: v4.1 火柴棍/台湾她 → v4.2 青铜壁托/暖柜光/碑形锁 → v4.3 六席必修:
#   调色师: 暖律锁死/KF6 回暖/KFT 颗粒/剪辑链 grain 站
#   美术考据: 青铜壁托碗(杀铁器年代硬伤)/3000K 暖钨丝柜光/平板圆顶碑形锁/焰禁蓝紫
#   摄影指导: S8 回滚剪影倒影(禁直视镜头)/S5 落点 early/S7 单轴 crane-up/S10 settle hold/finishing
#   受众: S9 叠字不叠脸(干净侧脸+后期字层)/S6 火星替手收窄构图/S2 斜推/S7 异步火焰
#   导演: T 桥 1.4s 压"你在橱窗前"整句/S8 落光连续性/S5→S6 帧级 match 机制/S9 微动律/数字收口
#   提示词工程: face/text 病灶簇清除/scriptorium 弃用/KF6 hand-forged 凿锚/S4 静态动词/S8 倒影剥五官
import json, os, sys

LEX = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\prompt-writing-spec-v1\patched-scripts"
sys.path.insert(0, LEX)
import prompt_lexicon as LX

OUT_CANON = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
WF_SRC = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\h3-local-test\h3_t2v_local_768p_bmc.json"

LX.LIGHT["torch"] = ("thick pitch-soaked reed torches bound in corded linen burn in cast bronze "
                     "sconce bowls on thick bronze brackets, each broad flame breathing a full "
                     "wide pool of pure amber-gold light with smoky yellow tips, chiaroscuro "
                     "with the far shadows crushed to pure black")
LX.LIGHT["torch_side"] = ("a thick reed-bundle torch held low at frame edge throws raking "
                          "side-backlight at 2000K across the stone, relief ridges catching "
                          "the warm light one band at a time while the rest stays matte black")
LX.LIGHT["case"] = ("the glass display case is lit from within by warm tungsten halogen at 3000K, "
                    "a golden amber pool in the surrounding darkness, skin and stone kept in "
                    "warm tones, shadows tinted warm brown")
LX.LIGHT["aisle_dim"] = ("warm tungsten case lights at 3000K dim one by one down the aisle, "
                         "the last golden amber pool clinging to the stone")
LX.LIGHT["glyph"] = ("the wedge marks are self-lit in deep gold, their glow blooming softly "
                     "through warm haze against black that carries visible 35mm film grain")

HER20 = ("a young Taiwanese woman of 2001, a softly rounded youthful face with full cheeks, "
         "large dark eyes, a small nose, long straight black hair with a full blunt fringe, "
         "wearing a simple oatmeal knit top, 2001 Taipei style")

ALIGN = ("For the target video, at 0.00 seconds into the target video, "
         "<Picture 1> (from [Shot 1]) is fully referenced.")

_ART = {"ecu": "An", "ext": "An"}


def i2va(shot, angle, move, action, scene, light, seed):
    art = _ART.get(LX.SHOT_SIZE[shot].split()[0], "A")
    cap = lambda s: s[0].upper() + s[1:]
    desc = ("%s %s, %s. %s. %s. %s, %s." % (art, LX.SHOT_SIZE[shot], LX.CAM_ANGLE[angle],
             cap(move), cap(action), cap(scene), LX.LIGHT[light].capitalize()))
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
     "a broad torch flame of a thick reed-bundle torch in its cast bronze sconce bowl washes "
     "across polished black basalt inscribed with stacked bands of carved cuneiform wedges, "
     "the wide pure amber-gold flame breathing as each band catches firelight in turn, fine "
     "dust drifting through the glow, soft halation blooming around the broad fire core",
     "in the deep darkness of an ancient Babylonian hall", "torch", 7801),
    ("S2_sweep", "KF2_sweep", "cu", "high",
     "the camera glides diagonally with small amplitude at slow speed",
     "the raking light of a thick reed-bundle torch slides across the stacked carved bands on "
     "the polished black front of the basalt stele, pure rock filling the frame, each band "
     "surfacing into light and drowning back into blackness as the broad flame flickers at "
     "the frame edge",
     "inside the torchlit Babylonian hall", "torch_side", 7802),
    ("S3_stele", "KF3_stele", "med", "low",
     "the camera pushes in with medium amplitude at slow speed",
     "a tall flat rounded-top slab stele of polished black basalt, straight sides three times "
     "taller than wide, its top fifth a carved relief band above twenty cuneiform registers, "
     "thick reed torches burning broad amber-gold flames in "
     "cast bronze sconce bowls on mud-brick columns, the hall dissolving into darkness as "
     "the stele grows larger in frame",
     "in the vast Babylonian hall", "torch", 7803),
    ("S4_crown", "KF4_crown", "cu", "low",
     "the camera holds a perfectly static shot",
     "amber firelight crawls slowly across the carved crown relief of the black basalt stele: "
     "a standing bearded king with his hand raised before a seated god holding out a rod and "
     "ring, their carved forms surfacing from near-black stone, soft halation around the "
     "torch glow",
     "at the crown of the stele in the torchlit hall", "torch", 7804),
    ("S5_columns", "KF5_columns", "cu", "eye",
     "the camera tilts down with medium amplitude at moderate speed",
     "the view slides steadily down stacked horizontal bands of carved cuneiform wedge marks "
     "on the black basalt surface edge to edge, amber firelight pooling in the deep-cut "
     "grooves, fine dust drifting through the torchlight, the tilt settling early on the "
     "lowest lit band of freshly cut wedges, crisp against the weathered rows above, then "
     "holding",
     "across the carved law bands of the stele", "torch", 7805),
    ("S6_chisel", "KF6_chisel", "ecu", "eye",
     "the camera holds locked-off and still",
     "a weathered hand in a rough undyed linen sleeve strikes a hand-forged flat-bladed "
     "bronze chisel with a wooden mallet, the warm golden alloy catching the firelight, the "
     "blade seated at the edge of a ragged fresh cut in coarse black basalt, the blow "
     "landing early with pale stone dust and sparks lifting, the "
     "stone and linen both reading warm amber",
     "at the fresh carving on the black basalt stele in the torchlit Babylonian hall",
     "torch_side", 7806),
    ("S7_hall", "KF7_hall", "ext", "eye",
     "the camera cranes up with large amplitude at slow speed",
     "the black basalt stele shrinks at the center of the vast Babylonian hall as the camera "
     "rises, each bronze brazier flame at a different burning stage and flickering "
     "asynchronously, torch pools receding, a hard light shaft of drifting dust above it, "
     "darkness swallowing the space around it",
     "in the vast mud-brick hall", "godray", 7807),
    ("T_glyphs", "KFT_glyphs", "med", "eye",
     "the camera holds a perfectly static shot",
     "luminous deep-gold cuneiform wedge marks drift slowly upward through warm haze "
     "against near-black darkness that carries fine 35mm film grain, soft golden bloom "
     "breathing around each mark",
     "in deep darkness between two worlds", "glyph", 7808),
    ("S8_case", "KF8_case", "med", "eye",
     "the camera pushes in with small amplitude at moderate speed",
     "a museum glass display case holds a broken slab of black basalt carved with cuneiform "
     "bands, the warm glow settling into a steady pool, the dark soft-edged silhouette "
     "reflection of a young Taiwanese woman with long straight black hair and a full blunt "
     "fringe kept low and dim on the glass, over the carved bands, her gaze on the stone",
     "in the dark museum archive", "case", 7809),
    ("S9_profile", "KF9_profile", "cu", "eye",
     "the camera holds locked-off and still while she breathes",
     "through museum glass, the youthful profile of %s in the warm case glow, "
     "her eyes on the stone, her hair moving faintly with her "
     "breath, faint glass reflections a warm veil" % HER20,
     "at the glass case in the dark museum", "case", 7810),
    ("S10_walkaway", "KF10_walkaway", "wide", "eye",
     "the camera pulls out slowly, decelerating into a locked-off hold",
     "%s walks away down the dark museum aisle toward the exit, her back to the camera as a "
     "dark soft-edged silhouette, warm case lights dimming one by one behind her, the last "
     "amber pool clinging to a broken black stone slab" % HER20,
     "in the long dark museum aisle", "aisle_dim", 7811),
]


def main():
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

    wf = json.load(open(WF_SRC, "r", encoding="utf-8"))
    wf["6"]["inputs"]["first_frame"] = ["16", 0]
    wf["16"] = {"class_type": "LoadImage", "inputs": {"image": "PLACEHOLDER.png"}}
    wf["15"]["inputs"]["filename_prefix"] = "mv30s_v4_fleet"
    wf_path = os.path.join(OUT_CANON, "h3_i2v_local_768p_v4.json")
    json.dump(wf, open(wf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("workflow:", wf_path)


if __name__ == "__main__":
    main()
