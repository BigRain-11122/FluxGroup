# -*- coding: utf-8 -*-
# 可爱女人-shots-v2.py - 《可爱女人》全曲帧级分镜表 v2.1（深研喂入·词级卡点·变速设计·选角案）
# v2.1=设计闸判决机械补丁（PANEL-WAVE1/2-VERDICT-20261011·改窗/改词/改挂·不动立意不动结构）
# 权威=可爱女人-剧本-v1.md（创作核心：纸飞机投掷-归返弧）+ RESEARCH-mv-craft-80s-90s-00s（§一/三/六 可爱女人行）
# 词级锚点=anchors/可爱女人.txt（whisper 2026-10-10 实测·词行至 236.30）·film=song 对齐·0-239.03（ffprobe 判决一实证·尾窗对齐歌长）
# 长期律：匀速判负（掷出快/穿云极缓·逐镜变速）/做旧克制（5279 黄昏蓝调+夜段·台式奶黑）/禁看镜头（她=远景/剪影/灯窗·KN24 灯窗内初见=唯一露脸）
#   物质转场（云层吞机/星尘化开/灯如星互映）/叠化全片仅一处=机影融进银河（XF_T2=KN20 内 1-2s=24-48 帧）/AIGC 开门帧标识/定格收口（80s 惯用件·RESEARCH §三）
# 发布话术红线：禁称复刻邝盛版分镜·徐若瑄/周杰伦真名禁入提示词与物料
# 词曲双权：发布物料必挂『词曲著作权/录音制作者权授权中』注记（承 INDEX 五）
# 选角律=CASTING-LAW.md：本曲女主=徐若瑄型（受众预期锚=原版徐若瑄亲演·神似不形似·真照不入管线·词面零真名）——与星晴 XQ_HER 不同块
# jman LoRA 挂载=mv_full_kf_r2.py L88 范式·strength 0.6-0.8 先网格（判决二可7）
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
import prompt_lexicon as LX

# ---- 光照块扩展（本曲世界：黄昏天台→城市灯碗→云海月晕→银河→夜天台→她的天台）----
LX.LIGHT["roof_dusk"] = ("blue-hour dusk at 8000K over a 2000 Taipei rooftop, sodium haze rising from the streets, a water tower standing black against the sky glow")
LX.LIGHT["roof_night"] = ("a night rooftop with the city glow rising from below the parapet, the first stars faint above the haze")
LX.LIGHT["city_bowl"] = ("the night city bowl of Taipei seen from high above, warm sodium scatter across ink-blue darkness, shop signs and apartment windows a slow drift of small lights")
LX.LIGHT["cloud_moon"] = ("silver-blue moonlight at 4400K over an endless cloud deck, the cloud tops carrying a faint warm rim from the city glow far below, the moon ringed by a soft halo")
LX.LIGHT["galaxy_gold"] = ("a broad band of warm gold star dust arched across an ink-blue night sky, fine stars seeded through the dark, the grain of the night air thick and soft")
LX.LIGHT["warm_window"] = ("one small rooftop window lit warm at 2800K in the blue darkness, its light laying a short amber path across the roof ledge")
LX.LIGHT["streak"] = ("night air ambience with a faint warm shimmer trailing behind a small paper plane, the city lights below catching the paper")

# macroslide 去污（判决二可1）：扩无 cuneiform 的 slide 变体，KN01/KN18 运镜改挂
LX.CAM_MOVE["slide"] = "the camera slides laterally with small amplitude at slow speed in shallow focus"

STYLE_LEAD = "as a film still from a 2000 Taiwanese music video"

# ---- 人物正典块 ----
# jman 触发词前置（判决一选1）：全部含 HIM 镜自动继承；KF 工单挂 jman_v1_640_rank32_final.safetensors（L88 范式）
HIM = ("jman, " + LX.ID_M_2001_BONE + ", in a plain grey cotton t-shirt and dark straight trousers")
# 可爱女人女主=徐若瑄型 2000 版块（判决一合3+判决二年3：删职业/年份统一 2000·词面零真名·KN24 灯窗内初见=唯一露脸）
KN_HER = ("a 20-year-old Taiwanese girl of the year 2000, a softly sweet oval face with full rounded cheeks, "
          "large bright dark double-lidded eyes with gentle innocent warmth, a small straight nose, soft "
          "medium-full rosy lips, long straight black hair with a solid blunt full fringe, in a simple light "
          "cotton sundress")
PLANE = ("a plain white paper plane folded from a single sheet of notebook paper, its creases crisp, "
         "one wing slightly buckled from an earlier flight")
HER_PLANE = "a small paper plane folded from cream paper with one wing tip dipped in red"

# XF_T2=唯一叠化：机影融进银河（KN20 内·1-2s=24-48 帧·可爱女人全片仅此一处·承 RESEARCH §三）
XF_T2 = {"shot": "KN20", "dissolve_s": 1.5}

def kf(shot, angle, subject, light, lens="35", tex="film_day", extra=""):
    s = "A %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
        LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
        LX.LIGHT[light].capitalize(), LX.LENS[lens],
        LX.GRADE["tw2001"], LX.TEXTURE[tex], STYLE_LEAD)
    return s + (" " + extra if extra else "")

I2V_TAIL = ("Warm 2000 Taiwanese telecine grade, warm skin tones, milky lifted blacks. "
            "Visible 35mm film grain. Restrained continuous motion, camera and subject motion only.")

def i2v(size_angle, motion, content):
    return ("Single continuous take at 24fps, 16:9. %s; %s. %s. " % (size_angle, motion, content)) + I2V_TAIL

CM = LX.CAM_MOVE

# ================= 新产镜头（30 镜）=================
# (id, t0, t1, speed, note, kf_prompt, i2v_prompt)
NEW = [
    # ---- 前奏 0-30.14（天台叠机→掷出·黄昏蓝调段=5279 补档·判决二年1）----
    ("KN01", 0.00, 6.50, 0.90, "他叠机（手部特写）",
     kf("cu", "high", "hands folding %s on a rooftop ledge, the creases pressed flat one by one, the dusk city soft below" % PLANE, "roof_dusk", lens="50", tex="film_night"),
     i2v("A close-up from a high angle", CM["slide"],
         "Hands folding a white paper plane on a rooftop ledge at dusk, each crease pressed flat in turn, the paper catching the last light")),
    ("KN02", 6.50, 13.00, 0.95, "天台全景（水塔/晾衣绳·城在脚下）",
     kf("med", "eye", "%s standing on a 2000 Taipei rooftop among strung clotheslines and a black water tower, the dusk city soft below the parapet" % HIM, "roof_dusk", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "A young man in a grey t-shirt standing on a Taipei rooftop at dusk among strung clotheslines and a water tower, the whole city bowl dim and warm below the parapet")),
    ("KN03", 13.00, 22.00, 1.00, "他持机立于边缘（城为底）",
     kf("cu", "eye", "%s at the parapet edge holding %s back by its tail, his eyes on the sky above the city, the wind in his fringe" % (HIM, PLANE), "roof_dusk", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A young man at a rooftop parapet holding a white paper plane back by its tail, the dusk city far below, his fringe moved by the rising wind")),
    ("KN04", 22.00, 30.14, 1.20, "掷出（burst 快）",
     kf("cu", "eye", "the throw: %s just released from a follow-through hand, the rooftop ledge and water tower streaking past below" % PLANE, "roof_dusk", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["track"], "A white paper plane flashing up off a rooftop into the dusk sky, the hand still open in its follow-through, the water tower sliding past below")),

    # ---- 主歌 30.14-55.66（直升机/升空/她的灯窗/让我碰到你）----
    ("KN05", 30.14, 37.22, 1.05, "想要有直升机=纸机与夜航直升机同框",
     kf("med", "eye", "%s gliding high over the city lights with a night helicopter holding far off in the same frame, its searchlight a soft cone" % PLANE, "city_bowl", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "A white paper plane gliding above a night city while a helicopter holds far off in the same sky, its running lights blinking slow, the paper banking gently")),
    ("KN06", 37.22, 43.64, 1.00, "掠过屋顶升空（蓝渐深）",
     kf("med", "eye", "%s rising past the last rooftops of the city edge into deepening blue air, the streets falling away beneath it" % PLANE, "roof_dusk", lens="50"),
     i2v("A medium shot at eye level", CM["tiltup"], "A paper plane climbing past dark rooftops into deep blue air, the camera easing up with it as the street lights sink below the frame")),
    ("KN07", 43.64, 50.48, 0.95, "每天每天想着你=升空寻望俯瞰城（她的天台亮一盏灯·判决一立3）",
     kf("ext", "high", "%s small and high above the whole city bowl, and far below one single rooftop window warm-lit among the sodium scatter" % PLANE, "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot from a high angle", CM["static"], "A paper plane tiny above the whole night city bowl, and far below one single rooftop window burning warm among the scatter of sodium lights")),
    ("KN08", 50.48, 55.66, 0.90, "她的灯窗（让我碰到你·许愿锚）",
     kf("cu", "eye", "a rooftop window lit warm with a slim girl silhouette pausing inside the light, a red-tipped paper plane resting on the ledge outside", "warm_window", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A warm rooftop window with a slim girl silhouette pausing inside the light, a red-tipped paper plane resting on the ledge, the window breathing softly as the figure stands still")),

    # ---- 副歌1 56.94-85.82（他仰脸+四种飞姿·hook 行首对齐=判决二配3）----
    ("KN09", 56.94, 59.14, 0.85, "漂亮得让我面红=他天台仰脸（夜天台·判决二年2）",
     kf("hs", "eye", "%s on the rooftop with his face tipped up to the first stars, a warm flush on his cheeks, the plane gone from his hand" % HIM, "roof_night", lens="85", tex="film_night"),
     i2v("A head-and-shoulders framing at eye level", CM["pushin"], "A young man on a night rooftop with his face tipped up to the first stars, a warm flush on his cheeks, his eyes following something high above")),
    ("KN10", 59.14, 62.66, 1.10, "飞姿1=宽弧回旋（卡「可爱女人」hook 行首）",
     kf("med", "eye", "%s carving a wide slow arc over the city lights, its wings catching a streetlamp flare" % PLANE, "city_bowl", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["panr"], "A paper plane carving a wide slow arc above night city lights, its white wings flashing as they cross a streetlamp flare, the skyline wheeling past")),
    ("KN11", 62.66, 66.26, 1.00, "飞姿2=迎面直飞（翼尖弹·hook 行首）",
     kf("cu", "eye", "%s nose-on to the camera, its wings flexing once as it climbs, the city lights soft circles behind" % PLANE, "city_bowl", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A paper plane flying nose-on toward the camera, its wings flexing once as it climbs, the night city reduced to soft circles of light behind it")),
    ("KN12", 66.26, 69.80, 1.15, "飞姿3=穿过两楼灯阵之间（hook 行首）",
     kf("med", "eye", "%s threading between two apartment towers whose windows are strung with warm lights, the gaps closing around its path" % PLANE, "city_bowl", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "A paper plane threading between two lit apartment towers, warm windows sliding past on both sides close to its wingtips, the gap opening again beyond")),
    ("KN13", 69.80, 78.50, 0.95, "飞姿4=全城灯碗上的小点（四连 hook 收口）",
     kf("ext", "eye", "%s a single pale point high above the whole lit bowl of the city, the streets a warm drift far below" % PLANE, "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot at eye level", CM["static"], "A paper plane a single pale point high over the whole lit bowl of a night city, the streets a slow warm drift far below, the sky holding it still")),
    ("KN14", 78.50, 85.82, 1.00, "收拍=暖微光尾迹（夜空语义对齐·判决二年2）",
     kf("cu", "eye", "%s trailing a faint warm shimmer through the dark, its paper edge lit from the city below" % PLANE, "streak", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["track"], "A paper plane trailing a faint warm shimmer through the night, its white edge lit softly from the city below as it holds a steady line")),

    # ---- Bridge 89.36-141.34（穿云/月晕/银河全景/融化=主呼吸段·D 段重排=判决一立2）----
    ("KN15", 89.36, 99.00, 0.88, "穿云（雾流过翼）",
     kf("med", "eye", "%s punching up through a moving cloud layer, thin mist streaming off its wings, the grey breaking into blue above" % PLANE, "cloud_moon", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["tiltup"], "A paper plane punching up through a moving cloud layer, thin mist streaming off its wings, the grey breaking into blue as it breaks through")),
    ("KN16", 99.00, 109.00, 0.84, "云海月晕（极缓长镜）",
     kf("wide", "eye", "an endless moonlit cloud deck under a haloed moon, %s small above the white sea, the city gone far below" % PLANE, "cloud_moon", lens="35", tex="film_night"),
     i2v("A wide shot at eye level", CM["pullout"], "An endless cloud deck under a haloed moon, a small paper plane holding still above the white sea, the camera easing back until the moon halo fills the sky")),
    ("KN17", 109.00, 117.46, 0.82, "银河全景（主呼吸镜1·星尘缓旋·伪影锚=判决二可5）",
     kf("ext", "eye", "the whole arc of a warm gold star band across the ink-blue night, the cloud deck a dark rim below, star dust thick along the middle of the sky", "galaxy_gold", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot at eye level", CM["pushin"], "The whole arc of a warm gold star band arched across an ink-blue night, the star dust wheeling almost imperceptibly, the cloud deck a dark rim below the frame, soft round points, the dust cloudlike")),
    ("KN18", 117.46, 126.52, 0.86, "银河近景（主呼吸镜2·伪影锚=判决二可5）",
     kf("cu", "eye", "the star dust itself close: countless fine warm points and pale currents drifting through deep blue-black, the grain of the night soft and thick", "galaxy_gold", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["slide"], "The star dust of the galaxy band in close detail, fine warm points and pale currents drifting through deep blue-black, everything moving at the slowest breath, soft round points, the dust cloudlike")),
    ("KN19", 126.52, 131.18, 0.88, "纸机漂进星流（纸面染金）",
     kf("med", "eye", "%s drifting into the gold star stream, its white paper warming gold at the edges, the stars thickening around it" % PLANE, "galaxy_gold", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "A paper plane drifting up into a stream of warm gold stars, its white paper warming to gold at the edges as the star field thickens around it")),
    ("KN20", 131.18, 134.92, 0.88, "融化在银河里（XF_T2 唯一叠化源帧）",
     kf("cu", "eye", "%s dissolving softly into the star stream, its silhouette thinning into light, the fold lines of the paper becoming threads of star dust" % PLANE, "galaxy_gold", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A paper plane dissolving softly into a stream of warm gold stars, its silhouette thinning into light until only the fold lines remain as threads of star dust")),
    ("KN20b", 134.92, 138.38, 0.90, "感谢地心引力=星尘逆引力折拢成纸机下坠（归返因果补·判决一立2）",
     kf("med", "eye", "the warm gold star dust gathering back inward against its own drift, folding itself into the small sharp shape of a paper plane high above the far city lights, the shape tipping into a slow dive toward the streets", "galaxy_gold", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "The star dust drawing together into a paper plane shape, the shape leaning into a slow dive toward the city far below")),
    ("KN21", 141.34, 155.00, 0.92, "她的天台·红尾纸机停在檐上（13.66s 窗·15s 政策内单挂·判决二配1）",
     kf("cu", "eye", "%s resting on a rooftop ledge beside a warm-lit window, the red wing tip turned toward the light" % HER_PLANE, "warm_window", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A cream paper plane with a red wing tip resting on a rooftop ledge beside a warm-lit window, the red tip catching the light as the window breathes")),

    # ---- 间奏 155.00-171.34（两天台隔城相望·KN22 拆两端=判决二配1）----
    ("KN22a", 155.00, 163.20, 0.95, "两天台隔城相望·她的天台端（双线交叉锚帧A）",
     kf("ext", "high", "a far rooftop alone on one side of the night city bowl, one small warm window light burning on its ledge, the streets a soft warm drift running away toward the far side of the city", "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot from a high angle", CM["static"], "A single far rooftop with one small warm light burning on its ledge, the streets a soft warm drift running away from it toward the far side of the night city, the frame holding still")),
    ("KN22b", 163.20, 171.34, 0.95, "两天台隔城相望·他的天台端（双线交叉锚帧B）",
     kf("ext", "high", "a rooftop on the near side of the night city bowl, the black water tower and strung clotheslines dark against the sky glow, the whole bowl of lights spread below the parapet", "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot from a high angle", CM["static"], "A rooftop with a black water tower and strung clotheslines against the night sky glow, the whole bowl of city lights spread below the parapet, the frame holding still")),

    # ---- 慢段 171.34-183.28（小小的爱=一俯一仰·KN24 升 med 露脸投递=判决一受2 选A）----
    ("KN23", 171.34, 174.46, 0.84, "他的天台（俯望城）",
     kf("wide", "high", "%s sitting on the rooftop edge with his elbows on his knees, looking across the whole night city, the water tower behind him" % HIM, "city_bowl", lens="35", tex="film_night"),
     i2v("A wide shot from a high angle", CM["cranedn"], "A young man sitting on a rooftop edge above the night city, elbows on knees, the whole bowl of lights below him, the camera easing down behind his stillness")),
    ("KN24", 174.46, 177.88, 0.87, "她的天台（仰·灯窗内初见=升 med 露脸投递·选A）",
     kf("med", "eye", "the warm rooftop window from across the gap, %s inside the light, her long straight hair and gentle bright eyes visible for the first time, %s held to her chest" % (KN_HER, HER_PLANE), "warm_window", lens="85", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "A girl inside a warm rooftop window holding a red-tipped paper plane to her chest, her eyes lifting slowly toward the stars, the window light breathing")),
    ("KN25", 177.88, 183.28, 1.00, "两灯之间的城（全力包含你）",
     kf("ext", "eye", "the whole night city between the two rooftops, two faint warm lights aligned across the frame, the streets carrying the drift of sodium", "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot at eye level", CM["static"], "A night city seen between two far warm lights aligned across the frame, the streets drifting below, the two lights holding their distance")),

    # ---- 尾奏 218.18-239.03（她答/相遇/归返定格收·判决一受3+配2·尾窗对齐歌长）----
    ("KN28", 218.18, 227.28, 1.02, "她的红尾机从她的天台升空（她的回答·15s 政策内 10s 源）",
     kf("med", "eye", "%s lifting off from her rooftop window light, the warm square falling away below it as it climbs" % HER_PLANE, "warm_window", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["tiltup"], "A cream paper plane with a red wing tip lifting off from a warm rooftop window, the square of light falling away below it as it climbs into the night")),
    ("KN29", 227.28, 234.42, 0.95, "让我碰到你=双机航线交错而过（卡「可爱女人」hook 串·定格源）",
     kf("cu", "eye", "the white plane and the red-tipped plane crossing paths high above the city, their wingtips a hand-span apart, the streets far below", "city_bowl", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A white paper plane and a red-tipped paper plane crossing paths high above a night city, their wingtips a hand-span apart, both holding their line as they pass")),
    ("KN30", 234.42, 239.03, 0.96, "落回天台双机并排定格收（239.03=歌长·定格收口）",
     kf("med", "eye", "%s settling onto the rooftop ledge beside %s, two planes side by side in the window light, the city dim beyond" % (HER_PLANE, PLANE), "warm_window", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["pushin"], "A red-tipped paper plane settling onto a rooftop ledge beside a white one, the two planes coming to rest side by side in the warm window light, everything settling to stillness")),
]

# ---- 重演律复用（副歌2 重排=判决一受3+配2）+ 漏窗补齐（判决二工1·≤3s=前镜定格延展/>3s=邻镜双挂）----
REUSE = [
    ("KN08", 55.66, 56.94, 1.00, "定格延展补窗"),
    ("KN05", 85.82, 89.36, 0.95, "双挂补窗（KN05 后半）"),
    ("KN20b", 138.38, 141.34, 1.00, "定格延展补窗（讓我懂了你窗·前镜尾帧冻结）"),
    ("KN25", 183.28, 184.60, 1.00, "定格延展补窗"),
    ("KN09", 184.60, 188.28, 0.87, "他夜脸（副歌2 起拍）=KN09 夜脸重演"),
    ("KN10", 188.28, 195.60, 1.06, "飞姿1 回归"),
    ("KN11", 195.60, 202.48, 1.03, "飞姿2 回归"),
    ("KN12", 202.48, 204.42, 1.08, "飞姿3 回归（hook 行首）"),
    ("KN12", 204.42, 209.70, 1.04, "飞姿3 回归·双挂"),
    ("KN05", 209.70, 214.84, 0.98, "直升机呼应回归=KN05 重演"),
    ("KN13", 214.84, 218.18, 0.92, "飞姿4 回归"),
]

FILM_END = 239.03  # ffprobe 歌长实测（判决一 TOP1·KN30 定格收口对齐）

# ---- 女主选角案（CASTING-LAW 必携件）----
CASTING_KN = {
    "track": "可爱女人（mv-jay-02·P1 主打曲）",
    "audience": "原版受众预期=徐若瑄亲演（A 级底座锚）——徐若瑄型年代脸型族（甜/空气感/长直发铁刘海）；受众洞察卡 RESEARCH-可爱女人-受众洞察-v1.md 喂入后校正",
    "default_A": "KN_HER=独立选角块（2000 年版·徐若瑄型年代脸型族·词面零真名·神似不形似·真照不入管线·KN24 灯窗内初见=唯一露脸）",
    "candidates": [
        "A=徐若瑄型（默认·KN_HER 2000 版块·甜系空气感·长直发铁刘海）",
        "B=新铸「空气感初恋系」块（B 位换铸·判决一选2 去撞·同一 ID 块禁挂两曲池）",
        "C=待受众卡校正后再铸第三系（每曲独立面孔律·禁挂他曲词表 ID 块）",
    ],
    "law_notes": "每曲独立面孔（与星晴 XQ_HER 不同块·禁跨曲复用）；她=远景/剪影/灯窗呈现+KN24 灯窗内初见一次（禁看镜头·距离语言）；定脸后即跑以图搜人反向测试留档（合规席·KN24 升 med 露脸后必跑）；落定后 ID 块逐字复用",
}

def _md():
    rows = ["| 镜 | 窗口(s) | 速 | 内容 |", "|---|---|---|---|"]
    rows += ["| %s | %.2f-%.2f | %.2f | %s |" % (s[0], s[1], s[2], s[3], s[4]) for s in NEW]
    rows += ["", "**重演律复用+漏窗补齐**", "", "| 复用镜 | 窗口(s) | 速 | 说明 |", "|---|---|---|---|"]
    rows += ["| %s | %.2f-%.2f | %.2f | %s |" % (r[0], r[1], r[2], r[3], r[4]) for r in REUSE]
    return "\n".join(rows)

if __name__ == "__main__":
    bad = 0
    for s in NEW:
        for p, mode in ((s[5], "t2i"), (s[6], "video")):
            hits = LX.lint(p, mode=mode)
            if hits:
                bad += 1
                print("[%s][%s] LINT HITS %s: %s" % (s[0], mode, hits, p[:90]))
    # ---- 时长断言（判决二配1）：源长=窗长/速度 ≤15s；note 含「定格延窗」豁免=只验源 5s ----
    dur_bad, freeze_n = 0, 0
    for s in NEW:
        w = s[2] - s[1]
        if "定格延窗" in s[4]:
            freeze_n += 1
            src = 5.0  # 定格延窗镜=源 5s+装配 tpad 冻结延窗
        else:
            src = w / s[3]
        if src > 15.0:
            dur_bad += 1
            print("DUR-FAIL %s: win %.2fs / speed %.2f = src %.2fs > 15s" % (s[0], w, s[3], src))
    # ---- 窗口断言（判决二工1）：NEW+REUSE 合并 0→FILM_END 无 >0.5s 空档（容差 0.05s）·禁叠窗 ----
    allw = sorted([(r[1], r[2], r[0]) for r in NEW] + [(r[1], r[2], r[0]) for r in REUSE])
    gap_bad = 0
    if abs(allw[0][0]) > 0.05:
        gap_bad += 1
        print("WINDOW HEAD: starts at %.2f (expect 0.00)" % allw[0][0])
    if abs(allw[-1][1] - FILM_END) > 0.05:
        gap_bad += 1
        print("WINDOW TAIL: ends at %.2f (expect %.2f)" % (allw[-1][1], FILM_END))
    gaps = [(a[2], b[2], round(b[0] - a[1], 2)) for a, b in zip(allw, allw[1:]) if b[0] - a[1] > 0.55]
    ovlp = [(a[2], b[2], round(b[0] - a[1], 2)) for a, b in zip(allw, allw[1:]) if b[0] - a[1] < -0.05]
    if gaps:
        gap_bad += len(gaps)
        print("WINDOW GAPS (>0.5s):", gaps[:6])
    if ovlp:
        gap_bad += len(ovlp)
        print("WINDOW OVERLAPS:", ovlp[:6])
    print("shots NEW=%d REUSE=%d lint_bad=%d | dur_checked=%d freeze_exempt=%d dur_bad=%d | window_gap_bad=%d gaps>0.5s=%d overlaps=%d"
          % (len(NEW), len(REUSE), bad, len(NEW), freeze_n, dur_bad, gap_bad, len(gaps), len(ovlp)))
    assert bad == 0, "LINT FAILED (lint_bad=%d)" % bad
    assert dur_bad == 0, "DURATION ASSERT FAILED (%d)" % dur_bad
    assert gap_bad == 0, "WINDOW GAPS ASSERT FAILED (%d)" % gap_bad
    print("SELF-CHECK GREEN: lint_bad=0 | WINDOW GAPS=0 (0.00-%.2f 无空档无叠窗) | 时长断言 %d 镜全过（定格延窗豁免 %d 镜·源 5s）"
          % (FILM_END, len(NEW), freeze_n))
    md = ("# 《可爱女人》分镜表 v2.1（帧级·深研喂入·设计闸判决落地版）\n\n"
          "> 权威=可爱女人-剧本-v1.md（投掷-归返弧·v1.1 修订同步）+RESEARCH-mv-craft §一/三/六；词级锚点=anchors/可爱女人.txt（词行至 236.30）·片长 239.03=ffprobe 判决一实证·尾窗对齐歌长\n"
          "> 发布话术红线：禁称复刻邝盛版分镜·徐若瑄/周杰伦真名禁入提示词与物料\n"
          "> 词曲双权：发布物料必挂『词曲著作权/录音制作者权授权中』注记（承 INDEX 五）\n"
          "> jman LoRA 挂载=mv_full_kf_r2.py L88 范式（jman_v1_640_rank32_final.safetensors）·strength 0.6-0.8 先网格（判决二可7）·含 HIM 镜自动继承触发词\n"
          "> XF_T2=唯一叠化：机影融进银河（KN20 内 1-2s=24-48 帧·可爱女人全片仅此一处）\n"
          "> 长期律：逐镜变速（掷 1.2 burst/穿云 0.84-0.9 极缓）/做旧克制：黄昏蓝调+夜段=5279（KN01-04 补档·判决二年1）·纯日戏 5246/台式奶黑/她=远景剪影灯窗（KN24 灯窗内初见=唯一露脸）/物质转场/定格收口/AIGC 标识\n"
          "> 状态机读正身=本 py 文件（md=衍生物）；自检=lint（t2i/video 双模式）+WINDOW GAPS（0→239.03 无 >0.5s 空档）+时长断言（源长=窗长/速度 ≤15s·定格延窗镜只验源 5s）\n\n"
          "## 女主选角案（CASTING-LAW 必携件）\n\n- 受众：%s\n- 默认候选：%s\n- 候选池：%s\n- 法条：%s\n\n## 镜头表（%d 新镜）\n\n%s\n"
          % (CASTING_KN["audience"], CASTING_KN["default_A"],
             "；".join(CASTING_KN["candidates"]), CASTING_KN["law_notes"], len(NEW), _md()))
    out = os.path.join(_HERE, "可爱女人-SHOTLIST-v2.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("md written:", out)
