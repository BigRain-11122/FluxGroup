# -*- coding: utf-8 -*-
# JAY-REDO-PACK-v1.py — O-20261015-1035 CEO 令「男主还是要像周杰伦！包括神态和发型」涉改镜重做件
# 导演席签发 2026-10-15 10:5x · 执行=@bm-c（生成视觉车道）
#
# 病根（JAY-BEFORE-BOARD.jpg 18 格取证定谳）：男主可见脸镜头=「泛AI帅哥」只有发型在演周杰伦——
#   本批 KF 全部未挂 jman LoRA 或强度不足；剪影/背影镜=身份零信息。CEO 裁决=撤剪影方案·改回像周杰伦。
#
# ══ KF 铁律（全部镜头）══
#   Krea2 turbo 8步 1344x768 + LoraLoaderModelOnly(jman_v1_rank32, strength=0.80)  ← 本批核心修复
#   正脸/3/4 镜必挂 JAY_BONE 反韩骨相锚 v2（KF1v2 s9015 实证 8.5 过正脸关的同一配方）
#   ID 块 HIM_MODERN / HIM_SCRIBE 逐字复用·禁改写（文本身份漂移=违例）
#   零否定词（反韩=正向骨相锚挤位·禁 NOT/no/without）；「发光」一律写 lit/self-lit
#   生命脉冲律：静镜必带 one slow blink / breath；唱镜必挂唱腔神态（chin tucked, eyes narrowed to slits, mouth open mid-line）
#   HOLD 槽律收尾：lighting wardrobe hair and set stay unchanged for the whole shot
#
# ══ i2v（全部镜头）══
#   INT8 768P · 5s 档 · 24fps · 单镜单运镜 · first_frame=对应 KF · 音轨禁令剥 audio 链
#   输出名=REDO 下同正典名（装配器 find_src 按名收片·零改表）
#
# ══ 交付 ══
#   bmc/i2v/jayredo/<正典名>.mp4（15 件）+ jayredo_qc_sheet.jpg 拼板 + git push + poke bm-a
#   先 KF 全烧 → LOOKBOARD 上链 → poke bm-a 导演席过目 → 过线件才进 i2v（批前抽检律·KF 便宜 i2v 贵）
#   次级校验件 C01/B01/D01：现有帧与 SING1/SING2 新标准比对，达标免重烧，不达标按本包重摇

JAY_BONE = ("heavy-lidded puffy monolid single-lidded eyes with heavy upper lids, small narrow drowsy eyes, "
            "a thick lower lip, a wide flat rounded jaw with a blunt round chin, softly rounded cheeks, "
            "natural unretouched skin with visible pores, a calm deadpan drowsy expression")
JAY_HAIR_2001 = ("thick black hair in a full blunt fringe lying flat over his eyebrows, "
                 "a slightly overgrown soft mop cut in the 2001 Taipei album-cover style")
JAY_HAIR_SCRIBE = ("thick black hair in a heavy straight fringe pressed flat over his brows, slightly tousled from work")
HIM_MODERN = ("a 20-year-old Taipei student of 2001 with %s, %s, wearing a loose plain white T-shirt under an open "
              "charcoal-grey cotton jacket, relaxed straight-leg dark denim jeans and worn flat canvas shoes"
              % (JAY_BONE, JAY_HAIR_2001))
HIM_SCRIBE = ("a 20-year-old Babylonian scribe with %s, %s, wearing a rough hand-woven undyed linen tunic with a "
              "simple rope belt" % (JAY_BONE, JAY_HAIR_SCRIBE))
STYLE = ("Shot on Kodak Vision 5279 35mm film in 2001, telecine transfer, amber monochrome grade with deep crushed "
         "shadows, fine organic grain, as a film still from a 2001 Taiwanese music video.")
I2V_TAIL = ("Warm amber monochrome grade with deep crushed shadows, visible 35mm film grain, highlights blooming "
            "softly. Every motion eases in and settles out, in the quiet camera language of a 2001 Taiwanese music "
            "video. Lighting wardrobe hair and set stay unchanged for the whole shot.")
LAMP = ("A single warm tungsten desk lamp at 2400K lights his face from the left, the small student room beyond "
        "kept in warm film-base brown fading to black, cassette tapes and a tea mug at the desk edge, fine dust "
        "adrift in the lit air.")
CASE_NIGHT = ("The glass display case is lit from within by warm tungsten halogen at 3000K, a golden amber pool in "
              "the surrounding darkness of the closed museum hall, the long aisle floor catching a faint amber "
              "sheen, everything else warm film-base brown fading to black.")

# ── SHOTS: (正典名, 窗口/速度备注, KF 提示词, i2v 提示词) ──
SHOTS = [
# ══ 一、2001 台北夜·书桌线（INT 系·前奏 0-17.5）══
("INT1_desk_breath.mp4", "窗0.00-3.50 @0.85x",
 "A medium shot at eye level of %s seated slumped forward on his forearms at a wooden study desk at night, his "
 "head lifted a little in three-quarter view toward the warm lamp, eyes drifting to slits in a drowsy deadpan, a "
 "fountain pen and loose sheets of handwriting before him. %s %s" % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera holds a locked-off tripod frame "
 "while his chest rises and falls in one slow breath, his head easing a fraction lower and lifting again, his "
 "eyelids sinking and steadying in one slow blink. %s" % I2V_TAIL),

("INT3_photo_stare.mp4", "窗7.50-11.50 @0.90x",
 "A medium close-up at eye level of %s at his night desk holding a small black-and-white photograph in both hands, "
 "his face turned in clear three-quarter toward the camera, his heavy-lidded gaze resting on the photograph, lips "
 "relaxed in a deadpan, one thumb at the photo edge. %s %s" % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A medium close-up at eye level; the camera holds a locked-off tripod "
 "frame while his thumb smooths one slow pass along the photograph edge, his drowsy gaze holding the photo through "
 "one slow blink. %s" % I2V_TAIL),

("INT4_rubbing_glow.mp4", "窗11.50-14.60 @0.95x",
 "A close-up at eye level over the desk of %s pressing the side of a graphite stick flat across paper laid on a "
 "small carved stone slab, the wedge marks surfacing through the paper as clean amber-tinted strokes under his "
 "hand, his face in soft three-quarter beyond, eyes on the strokes. %s %s" % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame while "
 "the graphite stick sweeps one slow pass across the paper, the carved strokes surfacing stroke by stroke under "
 "his hand, his gaze following the pass. %s" % I2V_TAIL),

("INT5_head_bow.mp4", "窗14.60-17.50 @0.88x",
 "A medium close-up at eye level of %s with his head bowed low over the notebook, fringe hanging over his brows, "
 "the pen moving across the page, his drowsy face partly shadowed and still readable in three-quarter, breath "
 "settled. %s %s" % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A medium close-up at eye level; the camera holds a locked-off tripod frame "
 "while the pen crosses two slow lines, his breath slow and even, the lamp filament breathing its glow. %s" % I2V_TAIL),

("E01c_first_line.mp4", "窗191.60-193.12 @0.90x",
 "A close-up at eye level of %s with his pen touching the first word onto a fresh page, chin tucked, his "
 "heavy-lidded eyes on the line in a drowsy focus, the fresh ink wet under the lamp. %s %s" % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame while "
 "the pen lands the first slow strokes, his eyes holding the line, one slow blink. %s" % I2V_TAIL),

("SING3b_morning_song_open_v4_s9019.mp4", "插入@197.0s·1.8s窗·2.0s 档",
 "A medium close-up at eye level of %s at his desk in the first pale morning light, his head beginning to sink "
 "toward the manuscript pages, mouth open mid-line in a quiet sung note, chin tucked, eyes narrowed to slits, the "
 "desk lamp still warm beside the pale window. A single warm tungsten desk lamp at 2400K from the left and a thin "
 "band of first pale dawn light at the window edge, the room beyond warm film-base brown. %s" % (HIM_MODERN, STYLE),
 "Single continuous take at 24fps, 16:9. A medium close-up at eye level; the camera holds a locked-off tripod frame "
 "while his head sinks slowly toward the pages as the long note breathes out, one slow blink, the pen resting, the "
 "dawn band softening at the window. %s" % I2V_TAIL),

# ══ 二、博物馆夜·访客线（SIL 系+D03b+E03·2001 现代装）══
("D03b_direct_gaze.mp4", "窗150.54-152.14 @0.90x（SIL3 咬窗后实取 150.54-152.00）",
 "A close-up at eye level of %s standing before the lit display case in the closed museum hall at night, turned "
 "back over his shoulder toward the camera in three-quarter, his calm heavy-lidded gaze lifting and holding beyond "
 "the frame edge, the case glow lighting his face warm amber. %s %s" % (HIM_MODERN, CASE_NIGHT, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame while "
 "his head settles a fraction and his drowsy gaze holds steady, one slow blink, the case glow breathing around him. "
 "%s" % I2V_TAIL),

("SIL1_stele_backlit_v4b_s9021.mp4", "插入@29.0s·1.8s窗",
 "A medium shot at eye level of %s standing close before the glass display case at night, seen in three-quarter "
 "from just behind his left shoulder, his face readable in the warm case glow, fringe over his brows, his drowsy "
 "gaze resting on the carved band inside the case, a tall black basalt stele lit amber behind the glass. %s %s"
 % (HIM_MODERN, CASE_NIGHT, STYLE),
 "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera holds a locked-off tripod frame "
 "while his faint reflection rests on the glass, his gaze traveling one carved row, one slow blink, the case light "
 "breathing. %s" % I2V_TAIL),

("SIL2_ots_crowd_v4_s9018.mp4", "插入@44.0s·1.8s窗",
 "A medium shot over his shoulder of %s standing still before the lit case among slow blurred visitors drifting "
 "past in the foreground, his calm face lit warm in three-quarter, his heavy-lidded eyes on the stone. %s %s"
 % (HIM_MODERN, CASE_NIGHT, STYLE),
 "Single continuous take at 24fps, 16:9. A medium shot over his shoulder; the camera holds a locked-off tripod "
 "frame while one blurred visitor wipes across the near frame and clears, his gaze holding the stone through one "
 "slow blink. %s" % I2V_TAIL),

("SIL3_case_rim_v2_s9013.mp4", "插入@152.0s·1.6s窗",
 "A close-up at eye level of %s at the rim of the lit case, the warm tungsten rim light tracing his fringe and the "
 "line of his jaw in three-quarter, his heavy-lidded eyes resting on the low register, the carved words softly "
 "doubled in the glass before him. %s %s" % (HIM_MODERN, CASE_NIGHT, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame while "
 "his eyes travel one register, the rim light steady, his breath slow. %s" % I2V_TAIL),

("E03_gaze_meet.mp4", "窗197.52-200.80 @0.85x",
 "A close-up at eye level of the dark museum glass carrying her warm-lit profile in the foreground reflection, and "
 "beyond the glass the face of %s surfaced in the amber light in three-quarter, his drowsy heavy-lidded gaze "
 "finding hers across the glass, two edges of one reflection. %s %s" % (HIM_MODERN, CASE_NIGHT, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame while "
 "the two reflections drift a fraction toward each other and hold together as the light settles. %s" % I2V_TAIL),

# ══ 三、演唱锚（巴比伦厅·古装置装·原唱 MV 打法=杰伦出镜唱）══
("SING1_torch_song_v2_s9013.mp4", "插入@78.0s·2.5s窗",
 "A medium close-up at eye level of %s standing before the tall stele in the Babylonian hall, chin tucked, eyes "
 "narrowed to slits, mouth open mid-line singing, one hand loose at his side, a reed-bundle torch burning warm "
 "amber in its bronze sconce behind his shoulder, his fringe over his brows, his face lit by the flame in "
 "three-quarter. A thick reed-bundle torch in a cast bronze sconce bowl throws raking warm light at 2000K across "
 "him and the carved stone, the hall beyond warm film-base brown fading to black. %s" % (HIM_SCRIBE, STYLE),
 "Single continuous take at 24fps, 16:9. A medium close-up at eye level; the camera holds a locked-off tripod frame "
 "while the torch flame swells softly behind him as the long note holds, his chest rising, his eyes steady in "
 "slits, the line easing out and his mouth closing. %s" % I2V_TAIL),

("SING2_firepit_song_s9014.mp4", "插入@180.0s·2.0s窗",
 "A medium close-up at eye level of %s seated cross-legged at a low fire pit, his face turned into the ember glow "
 "in three-quarter, chin tucked, eyes narrowed to slits, mouth open on the closing note, the small flame "
 "breathing warm amber from below, his linen tunic and fringe lit warm. A low reed-bundle fire in a shallow clay "
 "pit breathes warm amber light up across him, the plain beyond warm film-base brown fading to black. %s"
 % (HIM_SCRIBE, STYLE),
 "Single continuous take at 24fps, 16:9. A medium close-up at eye level; the camera holds a locked-off tripod frame "
 "while the embers breathe, his shoulders easing slowly downward as the note breathes out, his eyes holding slits. "
 "%s" % I2V_TAIL),

# ══ 四、古代刻字者·门框线（B02 由黑影升格可辨认）══
("B02_far_home.mp4", "窗177.00-181.50 @0.90x",
 "A wide shot at eye level of %s standing in a mud-brick doorway seen from inside the room in three-quarter back "
 "angle, his heavy fringe and shoulder line readable against the low warm amber horizon, distant fires small on "
 "the dark sleeping plain, his face partly turned into the doorway shadow and still readable, his drowsy gaze out "
 "at the land. A dark alluvial plain at night under a low warm amber sky glow at the horizon, faint torch pools in "
 "the far distance, warm film-base brown darkness. %s" % (HIM_SCRIBE, STYLE),
 "Single continuous take at 24fps, 16:9. A wide shot at eye level; the camera eases back from the doorway on a slow "
 "floor dolly, holding him framed in the black rectangle of the doorway while the night air moves his fringe, one "
 "slow blink. %s" % I2V_TAIL),

# ══ 五、次级校验件（现有帧达标免重烧·不达标按同配方重摇）══
("C01_carver_face.mp4", "窗77.34-80.18·校验",
 "校验参照：现帧为 jman 0.8 旧批·与 SING1 新标准同框比对——脸型宽钝/眯眼钝感/厚下唇/发压眉四点达标即保留；"
 "不达标重摇：A close-up at eye level of %s in profile at his work, a half-cut row of large fresh wedges before "
 "him, his heavy-lidded eyes lifting toward something beyond the frame edge, warm raking torchlight on the linen "
 "weave and the fringe over his brows. %s" % (HIM_SCRIBE, STYLE),
 "校验件·重摇时同原 i2v（locked frame·his eyes lift and hold·torch breathing）"),
("B01_weary.mp4", "窗172.50-177.00·校验",
 "校验参照同上；不达标重摇：A close-up at eye level of %s sunk onto his stool before the unfinished row, the "
 "mallet and chisel down at his side, his heavy-lidded eyes low, the torch burning thin. %s" % (HIM_SCRIBE, STYLE),
 "校验件·重摇时同原 i2v（locked frame·shoulders settle lower breath by breath·flame thinning）"),
("D01_carver_words.mp4", "窗141.76-144.56·校验",
 "校验参照同上（OTS 侧影边缘发帘+侧脸）；不达标重摇：A close-up over the shoulder of %s at his work, the "
 "half-finished fresh row of large wedges before him and his weathered hand resting on the chisel, his profile at "
 "the frame edge, warm raking torchlight on the linen sleeve. %s" % (HIM_SCRIBE, STYLE),
 "校验件·重摇时同原 i2v（locked frame·hand seats the chisel and stills）"),
]

if __name__ == "__main__":
    import re
    BAD = re.compile(r"\b(no|not|never|without|don't|doesn't|nope)\b", re.I)
    ok = True
    for name, w, kf, iv in SHOTS:
        for label, p in (("kf", kf), ("i2v", iv)):
            if p.startswith("校验"):
                continue
            hits = BAD.findall(p)
            if hits:
                ok = False
                print("LINT-FAIL", name, label, hits)
    print("JAY-REDO-PACK SHOTS=%d LINT=%s" % (len(SHOTS), "OK" if ok else "FAIL"))
