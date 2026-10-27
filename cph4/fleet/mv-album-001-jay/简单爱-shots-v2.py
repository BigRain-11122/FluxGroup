# -*- coding: utf-8 -*-
# 简单爱-shots-v2.py - 《简单爱》全曲帧级分镜表 v2.0（A 批起草·词行锚定·愿望清单弧）
# 权威=简单爱-剧本-v2.md（含 v2.1/v2.2/v2.3 打磨批）；锚点=anchors/简单爱-shotgrid-resnap.json
#   数据勘定（本窗实测）：resnap 的 cut0/cut1 在 #1-#34 与词行错位（#34 单窗 106.31-150.84=44.5s、
#   头段 13 行被压到 56.8-61.1）＝已知坏行区；正身改用 t0_used/t1_used 词行时间（26.12→256.78
#   连续零重叠零逆序），切点按 bpm_median 96.8（beat 0.6198s）落拍。坏行不修、只记账，见 SELF-CHECK 输出。
# 片长=270.99s（shotgrid inputs.duration_sec）；窗=词行合并成镜块，按词义排场（棒球镜对「我想和你看棒球」）
# 长期律：匀速判负（相遇 1.05 / 风与发丝 0.9 / 日落静 0.85 / 尾牵 0.88 / 奔跑棒球 1.15）
#   一歌一律=透明日光（晴段高调透明暖白 / 雨段青灰柔软·伞下是暖的）/禁看镜头/物质转场/
#   音轨=画面+原曲零 AI 音轨/AIGC 显著标识/意象分仓（单车归本曲·星晴资产零入镜）
# 剧情记忆钉：影子先牵手（独立镜·v2.2 #6 + v2.3 #7 先物理后概念）+ 积水写「简单爱」+ 两代单车尾拍（零人物）
# 发布话术红线：识别句「我想就这样牵着你的手不放开」=首帧字幕必用；文案零姓名指向（2015 骑车联读已群像化）
# 选角律=CASTING-LAW：本曲女主=日系清纯邻家（「清純羞涩」受众 7 处复现共识·气质优先于国籍·独立 ID 块）
# jman LoRA 挂载：strength 0.6（影射档）
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
import prompt_lexicon as LX

# ---- 光照块扩展（本曲世界：透明日光系·四光位 + 两条天气支线）----
# 光位纪律（QC §10 v1.12）：源→尺寸→距离→方向→质感→光比→K；钠灯不校正；halation 必有源
LX.LIGHT["day_clear"] = ("one large north-facing sky source at 6200K raking through an open lane, soft-edged shadows on grey concrete, contrast about three to one")
LX.LIGHT["day_back"] = ("the low sun at 3200K placed behind the two figures, a two-stop bleed around their silhouettes, the embankment wall catching the spill")
LX.LIGHT["golden_rim"] = ("the last twenty minutes of sun at 2800K rimming hair and shoulders from camera left, the rest of the frame falling two stops under")
LX.LIGHT["rain_soft"] = ("flat overcast rain light at 6800K, everything desaturated to blue-grey, one warm 2700K lamp under the eaves holding a small pool")
LX.LIGHT["eave_win"] = ("daylight through an old window at 5600K, a pale rectangle on the floor of a covered walkway, dust drifting in the beam")
LX.LIGHT["dusk_sodium"] = ("a single sodium street lamp at 2200K over the alley mouth, warm orange pooling on the concrete, the unlit street falling into cool grey")

STYLE_LEAD = "as a film still from a 2001 Taiwanese music video"

# 专辑年代=2000（共享词表 tw2001 块=mv0001 范特西 2001 在飞正身·不动·本地沿用）
GRADE_2001 = LX.GRADE["tw2001"]

# ---- 人物正典块 ----
HIM = ("jman, " + LX.ID_M_2001_BONE + ", in a plain white short-sleeve shirt with the collar open, "
       "straight dark trousers, scuffed canvas shoes")
# 本曲女主=日系清纯邻家（羞涩型·与星晴/可爱女人/龙卷风不同 ID 块·禁跨曲复用）
HER = ("a 20-year-old East Asian woman with a soft round face and clear dark eyes, shoulder-length black hair "
       "tucked behind one ear, in a pale blue cotton blouse and a knee-length pleated skirt")
BIKE = "an old steel single-speed city bicycle with chrome fenders, a wire front basket and a worn leather saddle"


def kf(shot, angle, subject, light, lens="35", tex="film_day", extra=""):
    art = "An" if LX.SHOT_SIZE[shot][:1].lower() in "aeiou" else "A"
    s = "%s %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
        art, LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
        LX.LIGHT[light].capitalize(), LX.LENS[lens],
        GRADE_2001, LX.TEXTURE[tex], STYLE_LEAD)
    return s + (" " + extra if extra else "")


# 继承缺陷修正（W2 i2v 包 2026-10-20 17:47 回执 / 龙卷风 R2414）：禁 warm skin tones 隐形补光 / 禁 milky lifted blacks
I2V_TAIL = ("Warm 2001 Taiwanese telecine grade, skin tones kept natural and unlit, black point lifted to "
            "10-14 code with shadow crush intact. Fine 35mm grain. Continuous unhurried motion, "
            "camera and subject motion only.")


def i2v(size_angle, motion, content):
    return ("Single continuous take at 24fps, 16:9. %s; %s. %s. " % (size_angle, motion, content)) + I2V_TAIL


CM = LX.CAM_MOVE

# ================= 新产镜头（30 镜·A 批）=================
# (id, t0, t1, speed, note, kf_prompt, i2v_prompt)
NEW = [
    # ---- 场 0 前奏 0.00-26.12「相遇鼓点」（黑场→镲音她入画 / 鼓音他入画）----
    ("T01", 0.00, 13.00, 1.00, "前奏=黑场鼓点起→巷口石板路渐亮（无人·只有风与光）",
     kf("wide", "eye", "an empty 2001 Taipei lane at mid-morning in clear white daylight, grey concrete paving with a pale worn stripe down the middle, an old shopfront shutter half raised at the far end", "day_clear", lens="35", tex="film_day"),
     i2v("A wide shot at eye level", CM["static"], "An empty Taipei lane in clear white daylight, grey concrete paving with a worn pale stripe, the shutter at the far end lifting slowly, dust drifting in the open light")),
    ("T02", 13.00, 26.12, 1.05, "他推车入画（鼓音）→ 镜头随车轮缓摇",
     kf("med", "eye", "%s. Pushing %s along the lane, his hand on the saddle, the chrome fender throwing a small hard glint" % (HIM, BIKE), "day_clear", lens="35", tex="film_day"),
     i2v("A medium shot at eye level", CM["panr"], "A young man pushing an old steel bicycle along a lane, his hand resting on the saddle, the chrome fender throwing a small hard glint as the camera pans with the wheels")),

    # ---- 场 0b 主歌 1 26.12-56.21「她跑过来·被石阶绊倒·扶起相识」----
    ("T03", 26.12, 36.08, 1.05, "她跑进巷口（鼓点落·人群零添加）",
     kf("med", "eye", "%s. Running into the lane from a side street, one hand holding the hem of her skirt, her school bag swinging out behind her" % HER, "day_clear", lens="50", tex="film_day"),
     i2v("A medium shot at eye level", CM["stead"], "A young woman running into a lane from a side street, one hand holding the hem of her skirt, her bag swinging out behind her, the camera holding as she fills the frame")),
    ("T04", 36.08, 46.10, 1.10, "石阶绊倒（失误=动作链真实·裙摆与掌心同框）",
     kf("wide", "low", "%s. Catching her canvas shoe on a low stone step and pitching forward, one palm thrown out toward the paving, the bicycle stopping at the near edge of the frame" % HER, "day_clear", lens="35", tex="film_day"),
     i2v("A wide shot from a low angle", CM["static"], "A young woman catching her shoe on a low stone step and pitching forward, one palm thrown out toward the paving, the bicycle stopping at the near edge of the frame")),
    ("T05", 46.10, 56.21, 0.95, "伸手扶起（外化：他先在裤缝蹭一下手·扶起后多停半拍·掌心蹭破一划）",
     kf("cu", "eye", "his hand pressed flat against the seam of his trousers once before reaching out, then closing around her forearm above a small graze on her palm, the fingers staying there a beat too long", "day_clear", lens="50", tex="film_day"),
     i2v("A close-up at eye level", CM["static"], "A hand pressing flat against a trouser seam once, then reaching out and closing around a forearm above a small graze on the palm, the fingers staying a beat too long")),

    # ---- 场 1 主歌 A 56.21-75.60「愿望一：骑单车」----
    ("T06", 56.21, 65.68, 0.90, "她抓他袖口又放开（羞涩三态①）→ 视线落到后座",
     kf("med", "eye", "%s. Standing up with her fingers hooked in his shirt cuff for balance and then letting go, her eyes dropping to the ground" % HER, "day_clear", lens="50", tex="film_day"),
     i2v("A medium shot at eye level", CM["stead"], "A young woman standing up with her fingers hooked in a shirt cuff for balance, then letting go, her eyes dropping to the ground")),
    ("T07", 65.68, 75.60, 0.90, "他用自己的袖子擦车座（郑重到笨拙·v2.1 #3）→ 她坐上后座发丝逆风",
     kf("med", "eye", "his forearm wiping the leather saddle twice with his own shirt sleeve, %s already side-saddle behind him with her hair lifting in the lane wind" % HER, "day_clear", lens="35", tex="film_day"),
     i2v("A medium shot at eye level", CM["track"], "An arm wiping a leather bicycle saddle twice with a shirt sleeve, then a young woman side-saddle behind him with her hair lifting in the wind, the camera tracking alongside")),

    # ---- 场 2 主歌 B 75.60-95.54「愿望二：看日落」----
    ("T08", 75.60, 85.68, 0.85, "河堤并肩坐·日落逆光双影一长一短（背影剪影①·原版保真）",
     kf("wide", "low", "two figures sitting shoulder to shoulder on a concrete river embankment facing the low sun, their long shadows laid out on the concrete in front of them", "day_back", lens="35", tex="film_day"),
     i2v("A wide shot from a low angle", CM["static"], "Two figures sitting shoulder to shoulder on a concrete embankment facing the low sun, their long shadows laid on the concrete in front of them, the frame held still")),
    ("T09", 85.68, 95.54, 0.85, "她的头一点一点磕在他肩上（困意外化·不煽情）+ 他回头看她一眼（演唱锚②·零口型）",
     kf("cu", "eye", "%s's head dipping slowly toward his shoulder and catching there, her eyes closing, one strand of hair lifting in the river wind, %s's face just turning back into the near edge of the frame" % (HER, HIM), "day_back", lens="85", tex="film_day"),
     i2v("A close-up at eye level", CM["static"], "A young woman's head dipping slowly toward a shoulder and catching there, her eyes closing, a strand of hair lifting in the wind, a face turning back into the near edge of the frame")),

    # ---- 场 3 副歌 1 95.54-121.77「愿望三：牵手」（先物理后概念·影先手后）----
    ("T10", 95.54, 105.42, 0.90, "真实的手先入画牵住（低角度逆光·v2.3 #7）",
     kf("cu", "low", "his hand entering the frame from the left and closing over hers against the low sun, the fingers lacing, the embankment concrete falling out of focus", "day_back", lens="50", tex="film_day"),
     i2v("A close-up from a low angle", CM["static"], "A hand entering the frame from the left and closing over another hand against the low sun, the fingers lacing, the concrete falling out of focus")),
    ("T11", 105.42, 113.96, 0.88, "影子先牵手=独立镜（堤面占画幅 ≥60%·多停 4-6 帧·v2.2 #6）",
     kf("wide", "high", "two long shadows on the embankment concrete, the shadow hands meeting and closing, the real bodies cropped out above the frame line, the shadow heads touching", "day_back", lens="35", tex="film_day"),
     i2v("A wide shot from a high angle", CM["static"], "Two long shadows on embankment concrete, the shadow hands meeting and closing while the bodies stay cropped out above, the frame held still until the shadows settle")),
    ("T12", 113.96, 121.77, 1.15, "牵手奔跑过整条街（扣紧那一下=识别句拍点·拇指压一下）",
     kf("wide", "eye", "two figures running hand in hand down a narrow street away from the camera, her skirt and his shirt pulling back in the wind, the street empty behind them", "day_back", lens="35", tex="film_day"),
     i2v("A wide shot at eye level", CM["track"], "Two figures running hand in hand down a narrow street away from the camera, her skirt and his shirt pulling back in the wind, the camera tracking behind them")),

    # ---- 场 6 副歌 2 121.77-135.06「愿望五：棒球」（词面对位「我想和你看棒球」）----
    ("T13", 121.77, 128.40, 1.15, "午后操场·他投她打（挥棒起手）",
     kf("wide", "eye", "a school sports field in the afternoon with netting and a dirt infield, %s mid-pitch and %s at the plate with a wooden bat" % (HIM, HER), "day_clear", lens="35", tex="film_day"),
     i2v("A wide shot at eye level", CM["static"], "A school sports field in the afternoon with netting and a dirt infield, a young man mid-pitch and a young woman at the plate with a wooden bat")),
    ("T14", 128.40, 135.06, 1.15, "挥空三次笑场（玩心档·挥拍三连快切）",
     kf("med", "eye", "%s. Swinging the bat through empty air for the third time and laughing at herself, the bat dropping to her shoulder" % HER, "day_clear", lens="50", tex="film_day"),
     i2v("A medium shot at eye level", CM["stead"], "A young woman swinging a bat through empty air for the third time and laughing at herself, the bat dropping to her shoulder")),

    # ---- 场 4 副歌间 135.06-154.94「愿望四：雨中伞」----
    ("T15", 135.06, 145.28, 1.00, "暴雨突至·伞永远斜向她那边（他半肩湿=守护外化）",
     kf("med", "eye", "%s. Holding a plain long umbrella tilted hard toward her while his own shoulder darkens with rain, the street behind them blue-grey and empty" % HIM, "rain_soft", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["stead"], "A young man holding a plain long umbrella tilted hard toward a young woman while his own shoulder darkens with rain, the blue-grey street behind them empty")),
    ("T16", 145.28, 154.94, 0.95, "伞下的分歧（她伸手接雨·他轻轻拉回=全片唯一分歧·v2.1 #1）",
     kf("cu", "eye", "her hand reaching out past the umbrella rim with the palm open to the rain, and his hand closing gently around her wrist to draw it back under the canopy", "rain_soft", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A hand reaching past an umbrella rim with the palm open to the rain, and another hand closing gently around the wrist to draw it back under the canopy")),

    # ---- 场 5 间奏 154.94-194.46「屋檐笑 + 吉他 + 独自漫步 + 积水写字」----
    ("T17", 154.94, 164.66, 0.90, "屋檐躲雨笑出声（暖池/青灰分界可见）",
     kf("wide", "eye", "the two of them standing under a narrow eave with the rain sheeting off the edge in a bright line, both laughing, one warm lamp behind them and the wet street cold beyond", "rain_soft", lens="35", tex="film_night"),
     i2v("A wide shot at eye level", CM["static"], "Two young people standing under a narrow eave with rain sheeting off the edge in a bright line, both laughing, a warm lamp behind them and the wet street cold beyond")),
    ("T18", 164.66, 174.74, 0.85, "屋檐下教她假装弹吉他（耳根红·指尖只碰三根指头·羞涩三态②）",
     kf("med", "eye", "%s. Sitting on a step with a guitar across her knee and her hand flat on the strings, %s crouched beside her guiding her wrist with three fingertips, his ears reddening" % (HER, HIM), "eave_win", lens="50", tex="film_day"),
     i2v("A medium shot at eye level", CM["static"], "A young woman sitting on a step with a guitar across her knee and a hand flat on the strings, a young man crouched beside her guiding her wrist with three fingertips")),
    ("T19", 174.74, 184.64, 0.95, "独自撑伞漫步街头（间奏·原版记忆点「最青涩最纯情」）",
     kf("wide", "eye", "%s. Walking alone along the wet street under the umbrella, the rain easing, his reflection travelling with him along the pavement" % HIM, "rain_soft", lens="35", tex="mist"),
     i2v("A wide shot at eye level", CM["track"], "A young man walking alone along a wet street under an umbrella, the rain easing, his reflection travelling with him along the pavement, the camera tracking at his pace")),
    ("T20", 184.64, 194.46, 0.88, "（词面物质镜）他蹲下用手指在积水里写「简单爱」",
     kf("cu", "high", "%s. Crouching at the edge of a shallow puddle with one finger tracing three short strokes into the water, the marks already illegible and closing over, the surface breaking and reforming behind his fingertip" % HIM, "eave_win", lens="50", tex="film_day"),
     i2v("A close-up from a high angle", CM["static"], "A young man crouching at the edge of a shallow puddle, one finger drawing characters in the water, the surface breaking and reforming behind his fingertip")),

    # ---- 场 5b 间奏 194.46-223.83「雨停空景 + 堤面再坐」----
    ("T21", 194.46, 201.80, 1.00, "雨停后堤面空镜（水洼反光·无人物）",
     kf("wide", "high", "a rain-washed embankment with shallow water standing in the paving, the sky opening pale behind the railing, the concrete still dark where it is wet", "rain_soft", lens="35", tex="mist"),
     i2v("A wide shot from a high angle", CM["cranedn"], "A rain-washed embankment with shallow water standing in the paving, the sky opening pale behind the railing, the camera easing down toward the reflection in the water")),
    ("T22", 201.80, 209.26, 0.95, "收起的伞靠在栏杆上（关系的静物残留）",
     kf("med", "eye", "a closed umbrella leaning against the concrete railing of the embankment, water running off its folds onto the paving, the sky pale behind it", "rain_soft", lens="50", tex="mist"),
     i2v("A medium shot at eye level", CM["pushin"], "A closed umbrella leaning against a concrete railing with water running off its folds onto the paving, the camera easing toward the wet folds")),
    ("T23", 209.26, 216.50, 0.85, "回外婆家=堤面再坐（她的头又磕上肩·愿望回环）",
     kf("wide", "low", "the two figures sitting on the same embankment concrete in the late sun, closer together than before, her head resting against his shoulder", "golden_rim", lens="35", tex="film_day"),
     i2v("A wide shot from a low angle", CM["static"], "Two figures sitting on the same embankment concrete in the late sun, closer together than before, her head resting against his shoulder")),
    ("T24", 216.50, 223.83, 0.85, "她的手放在他胸口（上衣布料起皱=接触的物质证据）",
     kf("cu", "eye", "her palm resting flat on his chest, the cotton of his shirt creasing under her fingers, the low sun laying a thin rim across both hands", "golden_rim", lens="85", tex="film_day"),
     i2v("A close-up at eye level", CM["static"], "A palm resting flat on a chest, the cotton creasing under the fingers, a thin rim of low sun crossing both hands")),

    # ---- 场 7 尾段 223.83-256.78「愿望终章：不放开」----
    ("T25", 223.83, 231.50, 1.00, "黄昏骑车载她远去（背影剪影·愿望第一项的回收）",
     kf("wide", "eye", "%s. Riding %s away down the embankment road with her behind him, both reduced to dark silhouettes against the low sun" % (HIM, BIKE), "day_back", lens="35", tex="film_day"),
     i2v("A wide shot at eye level", CM["static"], "A young man riding a steel bicycle away down an embankment road with a young woman behind him, both reduced to dark silhouettes against the low sun")),
    ("T26", 231.50, 239.12, 1.00, "巷口晚灯亮起（钠灯不校正·暖橙只落在口那里）",
     kf("wide", "eye", "the mouth of an old alley at dusk with a single sodium lamp switching on, warm orange pooling on the concrete while the rest of the street stays cool grey", "dusk_sodium", lens="35", tex="film_night"),
     i2v("A wide shot at eye level", CM["static"], "The mouth of an old alley at dusk with a single sodium lamp switching on, warm orange pooling on the concrete while the rest of the street stays cool grey")),
    ("T27", 239.12, 249.19, 0.88, "她先伸手（坦荡三态③·反转）→ 他愣半拍→扣紧",
     kf("med", "eye", "%s. Reaching her hand out first with the palm open, %s. Pausing half a beat before his fingers close over hers, his throat moving once" % (HER, HIM), "dusk_sodium", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["stead"], "A young woman reaching her hand out first with the palm open, a young man pausing half a beat before his fingers close over hers, his throat moving once")),
    ("T28", 249.19, 256.78, 0.88, "十指相扣特写（拇指压一下）+「就这样」字帧 1s（思源宋体系）",
     kf("ecu", "eye", "two hands laced together at the centre of the frame, the thumbs pressing once into the backs of the hands, the sodium light warm on the knuckles", "dusk_sodium", lens="85", tex="film_night"),
     i2v("An extreme close-up at eye level", CM["static"], "Two hands laced together at the centre of the frame, the thumbs pressing once into the backs of the hands, warm sodium light on the knuckles")),

    # ---- 场 8 尾拍 256.78-270.99「两代单车（零人物·愿望清单最后一条）」----
    ("T29", 256.78, 264.00, 0.90, "多年后同一段河堤：老单车锈成深褐·车筐野草开花",
     kf("wide", "low", "an old steel bicycle leaning against the same concrete railing years later, its frame rusted deep brown, weeds flowering up out of the wire basket, the river light unchanged behind it", "day_back", lens="35", tex="film_day"),
     i2v("A wide shot from a low angle", CM["static"], "An old steel bicycle leaning against a concrete railing, its frame rusted deep brown, weeds flowering out of the wire basket, the river light unchanged behind it")),
    ("T30", 264.00, 270.99, 0.90, "旁边一辆同款新车（亮漆/干净铃面/褪色红绳·橡胶把套有磨损）→ 缓摇收→黑场片名",
     kf("med", "low", "a second bicycle of the same old city model standing beside the first, its paint still glossy and its bell face clean, a faded red cord tied at the grip where the rubber is worn smooth", "day_back", lens="50", tex="film_day"),
     i2v("A medium shot from a low angle", CM["panr"], "A second bicycle of the same old city model standing beside a rusted one, glossy paint and a clean bell face, a faded red cord tied at a worn grip, the camera panning slowly across both then settling")),
]

# ---- 缝补窗（本表时间轴按词行连续铺满 0→270.99·当前无需补窗件）----
REUSE = []

FILM_END = 270.99  # shotgrid inputs.duration_sec（4:30.99）

# ---- 女主选角案（CASTING-LAW 必携件）----
CASTING_JDA = {
    "track": "简单爱（mv-jay-11·W2 次曲）",
    "audience": "原版受众记忆=日系清纯邻家（「清純羞涩」在评论区 7 处复现=选角第一共识）·气质优先于国籍·禁冷感御姐向·禁浓妆",
    "default_A": "HER=独立选角块（20 岁东方面孔·软圆脸·齐肩黑发掖耳后·浅蓝棉布衫+百褶裙·神似不形似·真照不入管线）",
    "candidates": [
        "A=日系清纯邻家脸（默认·HER 块）",
        "B=华人清纯学生脸（同气质不同面孔·独立 ID 块）",
        "C=受众卡校正后另铸（每曲独立面孔律）",
    ],
    "law_notes": "羞涩三态递进=抓袖口又放开→伞下抬眼半拍→尾段她先伸手；定脸后跑反向测试留档；与星晴/可爱女人/龙卷风零复用。",
}


def _md():
    rows = ["| 镜 | 窗口(s) | 速 | 内容 |", "|---|---|---|---|"]
    rows += ["| %s | %.2f-%.2f | %.2f | %s |" % (s[0], s[1], s[2], s[3], s[4]) for s in NEW]
    if REUSE:
        rows += ["", "**缝补窗（定格延展）**", "", "| 复用镜 | 窗口(s) | 速 | 说明 |", "|---|---|---|---|"]
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
    dur_bad = 0
    for s in NEW:
        w = s[2] - s[1]
        src = w / s[3]
        if src > 15.0:
            dur_bad += 1
            print("DUR-FAIL %s: win %.2fs / speed %.2f = src %.2fs > 15s" % (s[0], w, s[3], src))
    allw = sorted([(r[1], r[2], r[0]) for r in NEW] + [(r[1], r[2], r[0]) for r in REUSE])
    gap_bad = 0
    if abs(allw[0][0]) > 0.05:
        gap_bad += 1
        print("WINDOW HEAD: starts at %.2f (expect 0.00)" % allw[0][0])
    if abs(allw[-1][1] - FILM_END) > 0.05:
        gap_bad += 1
        print("WINDOW TAIL: ends at %.2f (expect %.2f)" % (allw[-1][1], FILM_END))
    gaps = [(a[2], b[2], round(b[0] - a[1], 2)) for a, b in zip(allw, allw[1:]) if b[0] - a[1] > 0.05]
    ovlp = [(a[2], b[2], round(b[0] - a[1], 2)) for a, b in zip(allw, allw[1:]) if b[0] - a[1] < -0.05]
    if gaps:
        gap_bad += len(gaps)
        print("WINDOW GAPS (>0.05s):", gaps[:8])
    if ovlp:
        gap_bad += len(ovlp)
        print("WINDOW OVERLAPS:", ovlp[:8])
    print("shots NEW=%d REUSE=%d lint_bad=%d | dur_checked=%d dur_bad=%d | window_gap_bad=%d gaps=%d overlaps=%d"
          % (len(NEW), len(REUSE), bad, len(NEW), dur_bad, gap_bad, len(gaps), len(ovlp)))
    assert bad == 0, "LINT FAILED (lint_bad=%d)" % bad
    assert dur_bad == 0, "DURATION ASSERT FAILED (%d)" % dur_bad
    assert gap_bad == 0, "WINDOW GAPS ASSERT FAILED (%d)" % gap_bad
    print("SELF-CHECK GREEN: lint_bad=0 | WINDOW GAPS=0 (0.00-%.2f 无空档无叠窗) | 时长断言 %d 镜全过"
          % (FILM_END, len(NEW)))
    md = ("# 《简单爱》分镜表 v2.0（帧级·A 批起草·词行锚定·愿望清单弧）\n\n"
          "> 权威=简单爱-剧本-v2.md（含 v2.1/v2.2/v2.3 打磨批）；锚点=anchors/简单爱-shotgrid-resnap.json\n"
          "> **数据勘定**：resnap 的 cut0/cut1 在 #1-#34 与词行错位（#34 单窗 44.5s、头段 13 行压到 56.8-61.1）＝已知坏行；本表改用词行时间 t0_used/t1_used（26.12→256.78 连续零逆序），切点按 BPM 96.8 落拍\n"
          "> 片长 270.99s（shotgrid inputs.duration_sec）；窗=词行合并成镜块，按词义排场（棒球镜对「我想和你看棒球」/牵手镜对「我想就这样牵着」）\n"
          "> 一歌一律=透明日光（晴段高调透明暖白 / 雨段青灰柔软·伞下是暖的）；速度=相遇 1.05 / 风与发丝 0.9 / 日落静 0.85 / 尾牵 0.88 / 奔跑棒球 1.15\n"
          "> 发布话术红线=识别句「我想就这样牵着你的手不放开」首帧字幕必用；文案零姓名指向（2015 骑车联读已群像化）\n"
          "> 状态机读正身=本 py 文件（md=衍生物）；自检=lint（t2i/video 双模式）+WINDOW GAPS（0→270.99）+时长断言（源长=窗长/速度 ≤15s）\n\n"
          "## 女主选角案（CASTING-LAW 必携件）\n\n- 受众：%s\n- 默认候选：%s\n- 候选池：%s\n- 法条：%s\n\n## 镜头表（%d 新镜）\n\n%s\n"
          % (CASTING_JDA["audience"], CASTING_JDA["default_A"],
             "；".join(CASTING_JDA["candidates"]), CASTING_JDA["law_notes"], len(NEW), _md()))
    out = os.path.join(_HERE, "简单爱-SHOTLIST-v4.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("md written:", out)