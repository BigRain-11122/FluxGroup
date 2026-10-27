# -*- coding: utf-8 -*-
# V5-REDO-PACK-r1054.py — 《爱在西元前》V5 修片重烧提示词包（bm-c r1054）
# 正身链: V5-REBURN-SPEC-20261016.md（导演席签发·verdict 依据=DIRECTOR-REVIEW-V4）逐镜转译
# 铁律: ID 块逐字复用（JAY-REDO-PACK-v1 正身）·零否定词（反韩=正向骨相锚挤位）·三段式表演（预备→发力→余势）
#       眼先于手·生命脉冲律·HOLD 槽律收尾=I2V_TAIL·「发光」一律 lit/self-lit
# 女主锚=ID_F_2001（spec §三: N02/R02 族基准·厚齐刘海至眉线+黑长直发过胸+奶白针织衫）·剪影/倒影级
# KF: Krea2 turbo 8步 1344x768·男镜挂 jman_v1_rank32@0.80·女主/物件镜零 LoRA（女脸被男 LoRA 污染=违例）
# i2v: INT8 768P 5s 124帧 24fps·音轨禁令（工作流无 audio 链）·trial 镜先 480P INT4 2 条验证构图/坐姿（总则⑥）

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
HER_2001 = ("a young Taiwanese woman of 2001, a softly rounded youthful face with full cheeks, large dark eyes, "
            "a small nose, long straight black hair falling past her chest with a full blunt fringe to her brow "
            "line, wearing a loose oatmeal chunky-knit wool sweater with a soft round neckline")
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
TORCH_RIM = ("A thick reed-bundle torch wedged in a cast bronze sconce bowl behind his shoulder throws a warm rim "
             "of side-backlight at 2000K along his fringe, his jaw and the chisel edge, fine organic grain in the "
             "glow, the rest of the stone staying matte black.")
TORCH_LOW = ("A thick reed-bundle torch burning thin and low in its bronze bowl at the frame edge throws raking "
             "warm light at 2000K across the stone, the glow failing softly into warm film-base brown darkness.")
TORCH_STELE = ("A thick reed-bundle torch wedged in a cast bronze sconce bowl at the frame edge throws raking warm "
               "light at 2000K across the stone, the carved bands catching the glow row by row while the rest "
               "stays matte black.")
UNSEEN_TORCH = ("Unseen torchlight from beyond the frame edge throws raking side-backlight at 2000K across the "
                "stone, the pale cut edges catching the warm light one sign at a time while the rest stays matte "
                "black.")

# SHOTS: (id, 窗口, 装配速度, KF提示词(None=复用既有帧), i2v提示词, trial, jman, KF复用路径)
SHOTS = [
("INT1_desk_breath_v5", "0.00-3.50", "0.85",
 "A close-up at eye level of %s seated upright facing the wooden study desk straight on, his shoulders squared "
 "to the desk edge, both forearms resting on the desk edge, a fresh cuneiform rubbing paper lying flat directly "
 "in front of him, a fountain pen tip hovering above the page, his heavy-lidded drowsy gaze on the marks. %s %s"
 % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame "
 "while his chest rises and falls in one visible breath with the pen tip hovering over the paper, then the pen "
 "lands the first slow stroke with the elbow carrying the shoulder in one line, the pen stopping and his eyes "
 "lifting toward the rubbing beyond the frame edge, his brow lifting a fraction. %s" % I2V_TAIL,
 True, True, None),

("INT2_paper_v5", "3.50-7.50", "0.92",
 "A medium shot at eye level of %s at his night desk as a draft through the window gap lifts one corner of the "
 "cuneiform rubbing paper off the desk, his hand reaching across to press the paper flat, the lamp warm on his "
 "face and a thin band of cooler window light resting at the frame edge, fine dust adrift in the lit air. %s %s"
 % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera holds a locked-off tripod frame "
 "while the paper corner flutters once in the draft, his palm root pressing it flat to the desk, then his "
 "fingertips smoothing the paper in one slow pass, his head dipping a moment. %s" % I2V_TAIL,
 True, True, None),

("INT3_photo_stare_v5", "7.50-11.50", "0.90",
 "A close-up at eye level of %s holding a legible cuneiform rubbing sheet in both hands before his chest, the "
 "sheet tilted a little toward his face, every wedge stroke clear and readable on the fibrous paper texture, "
 "his heavy-lidded gaze resting on the carved marks, his face turned in clear three-quarter toward the camera. "
 "%s %s" % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame "
 "while the rubbing sheet settles still in his hands, his thumb riding one slow pass across the pressed marks, "
 "his gaze traveling along the sign row, his lip line easing open a fraction. %s" % I2V_TAIL,
 True, True, None),

("INT4_rubbing_v5", "11.50-14.60", "0.95",
 "A close-up at eye level over the desk of %s bowed over the notebook writing one continuous line, his wrist "
 "carrying the pen, the cassette stack and the tea mug at the desk edge, his face in soft three-quarter beyond, "
 "his eyes on the page. %s %s" % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame "
 "while the pen hovers above the page, then writes one continuous slow line with the wrist carrying the motion, "
 "the pen lifting clear of the paper and his gaze resting on the written line. %s" % I2V_TAIL,
 True, True, None),

("INT5_head_bow_v5", "14.60-17.50", "0.88",
 "A close-up at eye level of %s sitting upright at the desk with his eyes on the page, his back straight, the "
 "lamp glow warming a fraction as if a first ember of firelight waking at the amber base of the frame. %s %s"
 % (HIM_MODERN, LAMP, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame "
 "while his back stays straight and his gaze holds the page, his shoulder blades settling and his head bowing "
 "slowly in a tired arc that keeps the spine lifted, then his eyes closing one slow beat and opening again. %s"
 % I2V_TAIL,
 True, True, None),

("B01_weary_v5", "172.50-177.00", "0.85",
 "A close-to-medium shot at eye level of %s slumped onto his low wooden stool before the unfinished row, his "
 "back caved into a tired curve, one elbow braced on his knee with his head hanging, the mallet and chisel "
 "resting at his foot, his heavy-lidded eyes low. %s %s" % (HIM_SCRIBE, TORCH_LOW, STYLE),
 "Single continuous take at 24fps, 16:9. A close-to-medium shot at eye level; the camera holds a locked-off "
 "tripod frame while his shoulders sink and sink again, his elbow sliding onto his knee to prop his forehead, "
 "then one long exhale leaving him as the thin flame eases lower with the breath. %s" % I2V_TAIL,
 True, True, None),

("C01_carver_face_v5", "77.34-80.18", "0.90",
 "A close-up at eye level of %s in profile at his work, a half-cut row of large fresh wedges before him, his "
 "heavy-lidded eyes fixed on the half-cut sign with the weight of long work held in his shoulders, his closed "
 "lips still. %s %s" % (HIM_SCRIBE, TORCH_RIM, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame "
 "while his gaze rests on the half-cut wedge before his hand moves, his wrist lifting and driving the chisel "
 "one clean strike into the stone, the chisel stopping, his breath easing out, the flame flickering once on "
 "his lashes, his closed lips holding still. %s" % I2V_TAIL,
 False, True, None),

("D01_carver_words_v5", "141.76-144.56", "0.90",
 "A close-up over the shoulder at eye level of %s at his work, the half-finished fresh row of large wedges "
 "before him and his weathered hand resting still on the chisel at the row's end, his profile at the frame "
 "edge, warm raking torchlight on the linen sleeve and the fringe. %s %s" % (HIM_SCRIBE, TORCH_RIM, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up over the shoulder at eye level; the camera holds a "
 "locked-off tripod frame while the chisel rests at the row's end, his fingertip riding one slow pass across "
 "the fresh-cut marks, his gaze traveling the row out past the frame edge. %s" % I2V_TAIL,
 False, True, None),

("D03b_direct_gaze_v5", "150.54-152.14", "0.90",
 "A close-up at eye level of %s pausing at his work, his chisel down at his side, lifting his eyes straight "
 "ahead toward something far beyond the frame edge, his drowsy gaze steady and clear. %s %s"
 % (HIM_SCRIBE, TORCH_RIM, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame "
 "while the last of the strike settles out of his shoulders, his eyes lifting straight ahead, his brow lifting "
 "a fraction, his breath visible once, the flame breathing once. %s" % I2V_TAIL,
 False, True, None),

("E01c_first_line_v5", "191.60-193.12", "0.90",
 "A close-up at eye level of %s with his bronze chisel tip seated at the next uncut mark in the black basalt, "
 "his heavy-lidded eyes on the point, the fresh row behind the tip, warm raking torchlight on his hand and the "
 "wedge-cut band. %s %s" % (HIM_SCRIBE, TORCH_STELE, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame "
 "while the chisel tip hovers and seats at the mark, one clean strike landing the cut, the fine stone chips "
 "jumping and hanging in the torchlight. %s" % I2V_TAIL,
 False, True, None),

("E03_gaze_meet_v5", "197.52-200.80", "0.85",
 "A close-up at eye level of dark glass carrying two silhouettes held apart by the pane: in the foreground the "
 "warm-lit profile silhouette of %s in her oatmeal chunky-knit sweater with her long straight black hair and "
 "full blunt fringe, and beyond the glass the firelit silhouette of %s in his rough linen robe, the torch glow "
 "edging his shoulder and fringe, two shapes at either rim of one dark pane. The glass carries a faint warm "
 "tungsten sheen at 3000K from the case within and a low torch glow at 2000K beyond it, the rest warm film-base "
 "brown fading to black. %s" % (HER_2001, HIM_SCRIBE, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a locked-off tripod frame "
 "while the two silhouettes each ease a fraction toward the other across the glass, the light breathing once, "
 "the two shapes holding together in the frame. %s" % I2V_TAIL,
 False, False, None),

("R06_museum_verse_v5", "131.72-138.56", "0.75",
 "A medium shot at eye level of the carved cuneiform registers inside the glass display case laid out like lines "
 "of verse in the warm light, and at the glass edge the faint reflection of %s resting quiet at the pane, her "
 "eyes on the carved rows. %s %s" % (HER_2001, CASE_NIGHT, STYLE),
 "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera eases back with small amplitude "
 "at slow speed while her reflected gaze rests on the verse rows, her lashes dipping once, her shoulder line "
 "rising and falling in one slow breath, the reflection breathing with her. %s" % I2V_TAIL,
 False, False, None),

("E04_replay_faces_v5", "212.66-219.84", "0.72",
 "A medium shot at eye level of the carved stone slab centered in warm blackness with its wedge marks self-lit "
 "in deep gold blooming through warm haze, and over the surface two profiles in slow exchange: the modern "
 "profile of %s in her oatmeal knit sweater, and the ancient profile of a Babylonian woman in a white robe with "
 "a coiled-snake armband, one silhouette easing into the other through the gold haze. The wedge marks are "
 "self-lit in deep gold, their glow blooming softly through warm haze against black that carries visible 35mm "
 "film grain. %s" % (HER_2001, STYLE),
 "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera holds locked-off while the "
 "modern young woman's profile with her long straight hair and full blunt fringe dissolves slowly into the "
 "outline of a Babylonian woman in a white robe with a coiled-snake armband, one shape easing into the other, "
 "the gold haze deepening and thinning with the slow breath of the light. %s" % I2V_TAIL,
 False, False, None),

("C04_words_alive_v5", "87.74-91.06", "0.88",
 "A close-up at eye level of one low register of large crisp fresh-cut cuneiform wedge marks across black "
 "basalt, every sign a tight cluster of clean triangular heads and tapering tails, the raw cut edges pale and "
 "fresh as new carving, the row filling the frame like a line of new words in still warm light. %s %s"
 % (UNSEEN_TORCH, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a near-static frame with "
 "only the warm light breathing slowly across the fresh-cut strokes, fine dust motes drifting through the "
 "amber air. %s" % I2V_TAIL,
 False, False, None),

("D05_words_warm_v5", "155.40-159.66", "0.87",
 "A close-up at eye level of the complete horizontal registers of large crisp cuneiform wedges inside the glass "
 "display case, the rows laid out like finished lines of verse, every stroke open in the warm case light. %s %s"
 % (CASE_NIGHT, STYLE),
 "Single continuous take at 24fps, 16:9. A close-up at eye level; the camera pushes in with small amplitude at "
 "very slow speed toward the carved rows, the case light breathing once over the strokes, fine dust motes "
 "drifting in the amber pool. %s" % I2V_TAIL,
 False, False, None),

("SIL1_babylon_v5", "29.00-30.80", "1.00",
 "A medium shot at eye level of a dome-topped black basalt stele carved with stacked bands of cuneiform wedge "
 "marks, the carved bands edged with simple Babylonian city-gate motifs of eight-point stars and flat carved "
 "rosettes, the firelight washing over one carved band. %s %s" % (TORCH_STELE, STYLE),
 "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera holds a locked-off tripod "
 "frame while the torchlight washes slowly across the carved band, the warm patches drifting over the "
 "cuneiform rows. %s" % I2V_TAIL,
 False, False, None),

("SIL4_crowd_edge_v5", "207.00-208.80", "1.00",
 None,
 "Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera holds a locked-off tripod "
 "frame while the warm light flows slowly over the crowd edge at the case, her silhouette standing still at "
 "the rim of the light with her long straight hair and full blunt fringe edged warm. %s" % I2V_TAIL,
 False, False,
 r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\SIL4_crowd_edge_v2_s9013_hd.png"),
]

SEEDS = {  # 9900 段新种子系（避撞 9500/9600/9800 老批）
    "INT1_desk_breath_v5": (9901, 9902), "INT2_paper_v5": (9903, 9904),
    "INT3_photo_stare_v5": (9905, 9906), "INT4_rubbing_v5": (9907, 9908),
    "INT5_head_bow_v5": (9909, 9910), "B01_weary_v5": (9911, 9912),
    "C01_carver_face_v5": (9913,), "D01_carver_words_v5": (9914,),
    "D03b_direct_gaze_v5": (9915,), "E01c_first_line_v5": (9916,),
    "E03_gaze_meet_v5": (9917,), "R06_museum_verse_v5": (9918,),
    "E04_replay_faces_v5": (9919,), "C04_words_alive_v5": (9920,),
    "D05_words_warm_v5": (9921,), "SIL1_babylon_v5": (9922,),
    "SIL4_crowd_edge_v5": (9923,),  # 既有 KF 复用·seed=i2v noise_seed
}

if __name__ == "__main__":
    import re
    BAD = re.compile(r"\b(no|not|never|without|don't|doesn't|nope)\b", re.I)
    VAGUE = re.compile(r"\b(glowing|beautiful|stunning|dramatic|iconic|aesthetic)\b", re.I)
    ok = True
    for s in SHOTS:
        sid, win, spd, kf, iv, trial, jman, reuse = s
        for label, p in (("kf", kf), ("i2v", iv)):
            if p is None:
                continue
            for rx, tag in ((BAD, "NEG"), (VAGUE, "VAGUE")):
                hits = rx.findall(p)
                if hits:
                    ok = False
                    print("LINT-FAIL", sid, label, tag, hits)
        assert sid in SEEDS, "SEED-MISSING %s" % sid
        if reuse is None:
            assert kf, "KF-MISSING %s" % sid
    print("V5-REDO-PACK shots=%d lint=%s" % (len(SHOTS), "OK" if ok else "FAIL"))
