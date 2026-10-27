# -*- coding: utf-8 -*-
# 龙卷风-shots-v2.py - 《龙卷风》全曲帧级分镜表 v2.0（A 批起草·词级卡点·双速对撞）
# 权威=龙卷风-剧本-v2.md（含 v2.1/v2.2/v2.3 打磨批）+ 剧本-v3 增量；词级锚点=anchors/龙卷风-shotgrid-resnap.json
#   （v2.0 resnap：word-onset select / beat place·bpm_median 72.3·snap_tol 0.10s·max_shot 3.0s·38 词行）
# 片长=250.36s（ffprobe 实测·尾窗对齐歌长）；窗=词行 cut0/cut1 原值，未焊接段走 REUSE 定格延展补窗
# 长期律：匀速判负（现实线 0.82-0.95 慢稳 / 闪回线 1.10-1.25 burst·双速对撞）/做旧克制（全专最冷色：现实青灰·闪回铅蓝黑）
#   禁看镜头（她=只闪回·越往后越侧越背）/物质转场/音轨=画面+原曲零 AI 音轨/AIGC 显著标识
#   一歌一律=全专最冷色；闪回里她=唯一暖点（2200K 残烛级）
# 剧情记忆钉：相框浅方形（时间负片·场0 埋/场5 显/场7 收）+ 停摆的钟（场7 扶正上弦）+ 两把椅子只拖一把
# 发布话术红线：禁称复刻邝盛版分镜·周杰伦/徐若瑄真名禁入提示词与物料；词曲双权注记随物料
# 选角律=CASTING-LAW：本曲女主=陈怡蓉系清纯初恋脸（只活闪回·独立 ID 块·神似不形似·真照不入管线）
# jman LoRA 挂载：mv_full_kf_r2.py L88 范式 · strength 0.6（影射档·本曲剧本硬约束）
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
import prompt_lexicon as LX

# ---- 光照块扩展（本曲世界：灰晨房间→青灰台灯孤岛→铅蓝风暴→她的暖残光→白昼正白→浅方形侧照）----
LX.LIGHT["room_grey"] = ("flat grey morning light through a rain-washed window at 6200K, low saturation, the corners of the room falling into cool shadow")
LX.LIGHT["room_lamp"] = ("one old table lamp burning a small pool of teal-grey light at 3000K in a dark corner of the room, the surrounding furniture nearly black")
LX.LIGHT["storm_lead"] = ("a street under lead-blue storm cloud at 5600K, rain slanting through the air, brief white lightning light on the wet asphalt")
LX.LIGHT["her_warm"] = ("a warm residual light at 2200K held on her face inside the cold storm, like a candle's last reach")
LX.LIGHT["day_white"] = ("clean white daylight at 5600K pouring through an opened curtain, fine dust suspended in the beam")
LX.LIGHT["patch_light"] = ("raking white daylight across one wall, the paint two stops paler in a tall rectangle where a wooden frame once hung")
LX.LIGHT["window_rain"] = ("rain streaming down an old aluminium window pane, the grey street dissolving behind the glass")

STYLE_LEAD = "as a film still from a 2000 Taiwanese music video"

# 专辑年代=2000（共享词表 tw2001 块=mv0001 范特西 2001 在飞正身·不动·本地覆写）
GRADE_2000_BASE = LX.GRADE["tw2001"].replace("2001 telecine", "2000 telecine")
# L2 F-13 option A: night frames must not carry a baked warm skin tone
# (QC §10 v1.10); the KF tail now matches the cold i2v tail.
GRADE_2000_COLD = ("2000 telecine grade, cold neutral skin left unlit, black point "
                   "lifted to 10-14 code with the toe intact, restrained practical "
                   "bloom, slight color bleed")
GRADE_2000 = GRADE_2000_COLD

# ---- 人物正典块 ----
HIM = ("jman, " + LX.ID_M_2001_BONE + ", in a charcoal grey wool crewneck sweater, loose dark trousers, "
       "bare feet on the wooden floor")
# 本曲女主=陈怡蓉系清纯初恋脸（只闪回·词面零真名·与星晴/可爱女人不同 ID 块·禁跨曲复用）
HER = ("a 24-year-old Taiwanese woman with a clear oval face and calm almond eyes, long straight black hair "
       "tied loosely back, in a soft knitted scarf and a plain cream knit top")


def kf(shot, angle, subject, light, lens="35", tex="film_day", extra=""):
    art = "An" if LX.SHOT_SIZE[shot][:1].lower() in "aeiou" else "A"
    s = "%s %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
        art, LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
        LX.LIGHT[light].capitalize(), LX.LENS[lens],
        GRADE_2000, LX.TEXTURE[tex], STYLE_LEAD)
    return s + (" " + extra if extra else "")


# 继承缺陷修正（W2 i2v 包 2026-10-20 17:47 回执）：禁 warm skin tones 隐形补光 / 禁 milky lifted blacks
I2V_TAIL = ("Cold 2000 Taiwanese telecine grade, skin tones kept natural and unlit, black point lifted to "
            "10-14 code with shadow crush intact. Visible 35mm film grain. Restrained continuous motion, "
            "camera and subject motion only.")


def i2v(size_angle, motion, content):
    return ("Single continuous take at 24fps, 16:9. %s; %s. %s. " % (size_angle, motion, content)) + I2V_TAIL


CM = LX.CAM_MOVE

# ================= 新产镜头（29 镜·A 批）=================
# (id, t0, t1, speed, note, kf_prompt, i2v_prompt)
NEW = [
    # ---- 场 0 前奏 0-30.02「风暴已过」（现实线·灰晨·缓推）----
    ("T01", 0.00, 10.00, 0.88, "狼藉空房间一帧缓推（倒下的相框/歪的钟/碎玻璃）",
     kf("wide", "high", "a wrecked 2000 Taipei apartment room in flat grey morning light, an overturned wooden picture frame lying face-down on the floor, a stopped mechanical wall clock hanging crooked, its hands stopped at ten past four, splinters of window glass along the sill, dust hanging in the air", "room_grey", lens="24", tex="film_day"),
     i2v("A wide shot from a high angle", CM["pushin"], "A wrecked apartment room in grey morning light, an overturned wooden frame face-down on the floor, a crooked mechanical clock stopped, glass splinters along the sill, the camera easing forward through the still dust")),
    ("T02", 10.00, 18.00, 0.90, "墙上浅方形一瞥（相框原位日晒色差·首刷几乎看不见）",
     kf("med", "eye", "one wall of the wrecked room seen at a glancing angle, the paint two stops paler in a tall rectangle where a wooden frame hung for years, everything around it in cool shadow", "room_grey", lens="50", tex="film_day"),
     i2v("A medium shot at eye level", CM["stead"], "A wall of a wrecked room at a glancing angle, a tall paler rectangle of paint where a frame once hung, the camera holding steady as the grey light shifts slowly across the wall")),
    ("T03", 18.00, 30.02, 0.85, "他背窗而坐（背影剪影①·灰晨光·全片最慢点之一）",
     kf("wide", "eye", "%s. Sitting on the floor at the centre of the wrecked room with his back to a rain-washed window, a low-contrast silhouette against the grey glass, the room wrecked around him" % HIM, "room_grey", lens="35", tex="film_day"),
     i2v("A wide shot at eye level", CM["static"], "A young man sitting on the floor at the centre of a wrecked room, his back to a rain-washed window, the grey glass holding him as a low-contrast silhouette, the room still around him")),

    # ---- 场 1 A 段 30.02-64.19「收拾+第一组闪回」----
    ("T04", 30.02, 33.35, 1.00, "拿起相框擦灰（拇指停在她的脸那格）",
     kf("cu", "high", "his hands lifting the overturned wooden frame off the floor and wiping the glass with a cloth, turning the frame face-up in his hands, one thumb coming to rest on the corner where her face is", "room_grey", lens="50", tex="film_day"),
     i2v("A close-up from a high angle", CM["static"], "Hands lifting an overturned wooden picture frame and wiping the glass in slow passes, the thumb stopping at one corner of the photograph, the cloth pausing there")),
    ("T05", 33.35, 36.69, 1.05, "闪回1=她在铅蓝风暴里回头（暖残光·唯一暖点首现）",
     kf("cu", "eye", "%s. Turning her head inside a lead-blue storm light, her loose black hair lifting at the side of her face, one warm band of light laid across her cheek" % HER, "her_warm", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A young woman turning her head inside a lead-blue storm light, her loose black hair lifting, one warm band of light crossing her cheek, the cold blue holding everything else")),
    ("T06", 37.52, 40.02, 1.00, "空掉的半张床（关系的物质残留）",
     kf("med", "high", "the empty half of an old wooden bed in the grey room, the sheet still holding the shallow shape of someone who left long ago, the other half turned down", "room_grey", lens="35", tex="film_day"),
     i2v("A medium shot from a high angle", CM["pushin"], "The empty half of an old wooden bed in a grey room, the sheet holding a shallow dent, the camera easing toward it until the dent fills the frame")),
    ("T07", 40.85, 46.69, 0.95, "闪回2=她替他拂掉肩上的灰（他站着不动）",
     kf("med", "eye", "%s. Reaching up to brush ash from his shoulder in the storm light, %s. Standing still under her hand" % (HER, HIM), "her_warm", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["stead"], "A young woman reaching up to brush ash off a young man's shoulder in storm light, his body still under her hand, the small motion the only movement in the frame")),
    ("T08", 46.69, 52.48, 1.20, "闪回3=黑云降落+两人被风拖走（词面超现实镜·物理轨迹真实）",
     kf("ext", "low", "a low black cloud rolling down over the rooftops of a 2000 Taipei street, dust and litter lifted and driven sideways, two small figures far below leaning against the wind", "storm_lead", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot from a low angle", CM["track"], "A low black cloud rolling down over the rooftops of a Taipei street, litter driven sideways through the air, two small figures below leaning hard into the wind as the camera tracks with the gust")),
    ("T09", 52.48, 64.19, 0.90, "拖椅子归位·两把椅子只拖一把（空的那把不动）",
     kf("med", "eye", "%s. Sliding one wooden chair back under the table, the second chair beside it left standing exactly where it was, untouched, the room half tidied around him" % HIM, "room_lamp", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["stead"], "A young man sliding one wooden chair back under a table, the second chair left standing where it drifted, his movement slow and deliberate in the teal-grey lamplight")),

    # ---- 场 2 副歌1 67.52-96.69「风暴闪回全面爆发」（快切·双速对撞）----
    ("T10", 67.52, 73.36, 1.25, "暴雨斜打窄街（水从雨棚成片泻下）",
     kf("med", "eye", "rain striking a narrow 2000 Taipei street almost horizontally, water sheeting off a corrugated awning, a folded umbrella jammed against a wall", "storm_lead", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["panr"], "Rain striking a narrow street almost horizontally, water sheeting off a corrugated awning in one continuous sheet, the camera panning across the flooded kerb")),
    ("T11", 73.36, 80.86, 1.10, "伞骨外翻+她隔着被风灌满的街（唯一暖点·L1 可读锚）",
     kf("wide", "eye", "an umbrella turned inside out at the near kerb in the wind, and across the flooded street %s. Standing still under the rain, the only warm light left in the frame" % HER, "storm_lead", lens="35", tex="film_night"),
     i2v("A wide shot at eye level", CM["static"], "An umbrella turned inside out at the near kerb, and across a flooded street a young woman standing still under the rain, her warm light the only warmth in the cold blue frame")),
    ("T12", 80.86, 86.69, 1.10, "暴风圈来不及逃=牵手奔跑剪影（背影剪影②）",
     kf("wide", "low", "young trees bowed flat by the wind along the street, two silhouettes running hand in hand through the rain between them", "storm_lead", lens="35", tex="film_night"),
     i2v("A wide shot from a low angle", CM["track"], "Young trees bowed flat by the wind along a street, two silhouettes running hand in hand through the rain between them, the camera tracking alongside their run")),
    ("T13", 86.69, 94.19, 1.15, "他抓她手腕抓得太紧（腕上勒痕一帧·失控外化）",
     kf("ecu", "eye", "his hand closed hard around her wrist in the rain, her skin pale between his fingers, a red pressure line across her wrist", "storm_lead", lens="85", tex="film_night"),
     i2v("An extreme close-up at eye level", CM["static"], "A hand closed hard around a wrist in the rain, the skin pale and pressed between the fingers, the grip staying tight a beat too long")),

    # ---- 场 2v2.3 静一拍插入（打磨批 #7：快切段插单硬光低位特写）----
    ("T14", 94.19, 100.03, 0.85, "静一拍=他抬眼缓推（风暴里唯一清醒的一秒·单硬光低位）",
     kf("cu", "low", "%s. Lifting his eyes in the storm light, the background falling to full black behind him, one hard light low on his face" % HIM, "storm_lead", lens="85", tex="film_night"),
     i2v("A close-up from a low angle", CM["pushin"], "A young man lifting his eyes inside storm light, everything behind him fallen to black, one hard light low on his face, the camera pushing in slowly")),

    # ---- 场 3 C 段 100.03-117.53「叙事轴心·后知后觉=停手」----
    ("T15", 100.03, 107.53, 0.84, "收拾的手越来越慢（每个「不觉得」=一拍放慢）",
     kf("cu", "top", "his hands moving over a small pile of objects on the floor, the motion slowing, one hand lowering a ceramic cup and stopping", "room_grey", lens="50", tex="film_day"),
     i2v("A close-up from a top angle", CM["static"], "Hands moving over a small pile of objects on a floor, the motion slowing with each pass, one hand lowering a ceramic cup and coming to rest")),
    ("T16", 107.53, 113.36, 0.82, "放下手里的东西→手空了才停（v2.1 打磨 #4 动作因果先于情绪）",
     kf("cu", "eye", "his hand laying the wooden frame face-down on the table, the fingers letting go one by one, the hand then resting open and empty", "room_grey", lens="50", tex="film_day"),
     i2v("A close-up at eye level", CM["pushin"], "A hand laying a wooden picture frame face-down on a table, the fingers releasing one by one, the hand then resting open and empty on the wood")),
    ("T17", 113.36, 117.53, 0.88, "同构图房间半净（停手时刻·与开场同机位）",
     kf("wide", "eye", "%s. Sitting on the floor at the centre of the room with his back to the window, the room around him half tidied, a tall pale rectangle of paint on the wall just visible in the grey light" % HIM, "room_grey", lens="35", tex="film_day"),
     i2v("A wide shot at eye level", CM["static"], "A young man sitting on the floor at the centre of a half-tidied room, his back to the window, the pale rectangle on the wall just readable, the frame held still")),

    # ---- 场 4 副歌2 120.85-146.70「重演+完成度递增」----
    ("T18", 120.85, 126.69, 1.10, "闪回重演=同一动作更短更淡（回忆在褪色）",
     kf("med", "eye", "%s. Brushing ash from his shoulder in the storm light, the light around them a stop dimmer, the gesture held a beat less" % HER, "her_warm", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["stead"], "The same gesture of brushing ash from a shoulder in storm light, everything a stop dimmer, the movement shorter and softer than before")),
    ("T19", 126.69, 134.20, 0.95, "她的暖残光逐次减一档+越往后越侧越背（v2.1 #5 记忆被转过去）",
     kf("cu", "eye", "%s half turned away inside the storm, the warm light on her cheek already a stop cooler, her face turned away from the lens" % HER, "her_warm", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A young woman half turned away inside storm light, the warmth on her cheek a stop cooler, her face staying turned as the frame holds")),
    ("T20", 134.20, 143.36, 0.90, "房间越来越空净+空相框在桌上（完成度递增）",
     kf("wide", "high", "the room almost cleared, the floor swept, the frame lying face-down on the table, the photograph already slipped out beside it, a tall pale rectangle of paint catching the grey light", "room_grey", lens="24", tex="film_day"),
     i2v("A wide shot from a high angle", CM["cranedn"], "An almost cleared room, the floor swept bare, one empty wooden frame face-down on the table, the camera easing down toward the pale rectangle on the wall")),

    # ---- 场 5 尾奏1 146.70-174.20「光进·浅方形显形」----
    ("T21", 146.70, 151.70, 0.86, "演唱锚①=钢琴旁侧影（零脸·2.5s 实拍位 5s 源）",
     kf("med", "eye", "%s at an old upright piano in profile, only his shoulder and the line of his jaw in frame, the head cut off by the top edge of the frame, his face entirely out of view, his hands resting lightly on the keys, the keys still level, the varnish dull and worn" % HIM, "room_lamp", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["stead"], "A young man at an old upright piano in profile, only his shoulder and jawline in frame, his hands resting lightly on the keys, the keys still level, the dull varnish catching a thin light")),
    ("T22", 151.70, 164.00, 0.84, "拉开窗帘=日光第一次入房（手臂全程匀速不停顿·接受态）",
     kf("wide", "eye", "%s. Drawing the heavy curtains open with one steady arm, grey-white daylight breaking into the room and laying a long bright path across the bare floor" % HIM, "day_white", lens="35", tex="film_day"),
     i2v("A wide shot at eye level", CM["static"], "A young man drawing heavy curtains open with one steady arm, grey-white daylight breaking into the room and laying a long bright path across the bare floor")),
    ("T23", 164.00, 174.20, 0.85, "浅方形显形+抬手停半空（v2.2 给观众的手指·唯一指路）",
     kf("med", "eye", "the wall in raking white daylight, the paint two stops paler in a tall rectangle where a wooden frame hung, his raised palm stopping in the air a hand-span clear of the wall, the palm held clear of the paint, open air visible between hand and wall, the fingers curled just short of contact", "patch_light", lens="50", tex="film_day"),
     i2v("A medium shot at eye level", CM["static"], "A wall in raking white daylight with a tall paler rectangle of paint, a raised palm stopping in the air a hand-span clear of it, the fingers curled just short of contact, the hand held still")),

    # ---- 场 6 尾段副歌 174.20-200.88「最后一次回望」----
    ("T24", 174.20, 185.87, 0.90, "演唱锚②=窗前背影哼尾段（最静处理·反向于副歌1）",
     kf("med", "eye", "%s. Standing at the opened window with his back to the room, his shoulders level, the white daylight clean on the window frame around him" % HIM, "day_white", lens="50", tex="film_day"),
     i2v("A medium shot at eye level", CM["static"], "A young man standing at an opened window with his back to the room, his shoulders level, white daylight clean on the frame around him, the room behind him still")),
    ("T25", 185.87, 193.00, 0.88, "她最后回望的半张脸（白光收走前一秒·记忆被转过去）",
     kf("cu", "eye", "%s turned back for one last look inside a blown-out white light, only the near half of her face still readable, her mouth moving once in silence" % HER, "day_white", lens="85", tex="film_day"),
     i2v("A close-up at eye level", CM["static"], "A young woman turned back for one last look inside a blown-out white light, only the near half of her face readable, her mouth moving once in silence")),

    # ---- 场 7 Outro 200.88-250.36「你-渐弱蒙太奇→推窗→回望浅方形」----
    ("T26", 200.88, 212.00, 0.92, "「你」渐弱蒙太奇1（她走远·边缘开始发白）",
     kf("med", "eye", "%s. Standing far down the rain-washed street, already pale at the edges of the frame, the street greys washing over her silhouette" % HER, "storm_lead", lens="85", tex="film_night"),
     i2v("A medium shot at eye level", CM["pullout"], "A young woman standing far down a rain-washed street, her edges already pale, the camera easing back as the grey street washes over her outline")),
    ("T27", 212.00, 224.00, 0.90, "「你」渐弱蒙太奇2（只剩轮廓·街已溶解）",
     kf("wide", "eye", "a pale street emptied of detail, only the faint outline of a figure left standing in the white haze, the kerb and wall nearly dissolved", "day_white", lens="35", tex="mist"),
     i2v("A wide shot at eye level", CM["static"], "A pale street emptied of detail, only the faint outline of a figure standing in white haze, the kerb and wall dissolving as the light swells")),
    ("T28", 224.00, 237.00, 0.88, "推窗全开（接受·光进满屋）",
     kf("wide", "eye", "%s. Pressing the old aluminium window fully open with both hands, the white light pouring over the sill and across the floor, the room behind him bright and bare" % HIM, "day_white", lens="35", tex="film_day"),
     i2v("A wide shot at eye level", CM["pushin"], "A young man pressing an old aluminium window fully open with both hands, white light pouring over the sill and across the bare floor, the room behind him bright")),
    ("T29", 237.00, 250.36, 0.90, "回望墙上浅方形一拍→满屋白光收黑（v2.1 #1 钟并肩物证·尾窗对齐歌长）",
     kf("med", "eye", "%s. Pausing in the bright doorway to look back across the empty room at a tall pale rectangle of paint on the wall, his hands loose at his sides, the stopped clock now standing level on the shelf, its hands still at ten past four, the white light swelling behind him" % HIM, "patch_light", lens="50", tex="film_day"),
     i2v("A medium shot at eye level", CM["static"], "A young man pausing in a bright doorway to look back across an empty room at a pale rectangle on the wall, his hands loose, the white light swelling until only the wall remains")),
]

# ---- 词行缝补窗（词行间空白·定格延展保窗零空档）----
REUSE = [
    ("T05", 36.69, 37.52, 1.00, "定格延展补窗"),
    ("T06", 40.02, 40.85, 1.00, "定格延展补窗"),
    ("T09", 64.19, 67.52, 1.00, "定格延展补窗（副歌进前空拍）"),
    ("T17", 117.53, 120.85, 1.00, "定格延展补窗（C 段→副歌2 间奏）"),
    ("T20", 143.36, 146.70, 1.00, "定格延展补窗"),
    ("T25", 193.00, 200.88, 1.00, "定格延展补窗（尾段副歌收）"),
]

FILM_END = 250.36  # ffprobe 歌长实测（shotgrid inputs.duration_sec）

# ---- 女主选角案（CASTING-LAW 必携件）----
CASTING_LJF = {
    "track": "龙卷风（mv-jay-09·W2 首曲）",
    "audience": "原版受众预期=陈怡蓉系初代杰女郎（清纯初恋脸/气质优雅/受众零性感向期待）——只存在于闪回里",
    "default_A": "HER=独立选角块（陈怡蓉系清纯初恋脸·神似不形似·真照不入管线·词面零真名·与星晴/可爱女人禁跨曲复用）",
    "candidates": [
        "A=陈怡蓉系清纯初恋脸（默认·HER 块）",
        "B=新铸「素净邻家系」块（B 位换铸·同一 ID 块禁挂两曲池）",
        "C=受众卡校正后另铸（每曲独立面孔律）",
    ],
    "law_notes": "只活闪回·现实线零她=空房间的重量；越往后越侧越背（记忆被转过去不是被剪掉）；定脸后跑以图搜人反向测试留档。",
}


def _md():
    rows = ["| 镜 | 窗口(s) | 速 | 内容 |", "|---|---|---|---|"]
    rows += ["| %s | %.2f-%.2f | %.2f | %s |" % (s[0], s[1], s[2], s[3], s[4]) for s in NEW]
    rows += ["", "**词行缝补窗（定格延展）**", "", "| 复用镜 | 窗口(s) | 速 | 说明 |", "|---|---|---|---|"]
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
    dur_bad, freeze_n = 0, 0
    for s in NEW:
        w = s[2] - s[1]
        if "定格延窗" in s[4]:
            freeze_n += 1
            src = 5.0
        else:
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
    print("SELF-CHECK GREEN: lint_bad=0 | WINDOW GAPS=0 (0.00-%.2f 无空档无叠窗) | 时长断言 %d 镜全过"
          % (FILM_END, len(NEW)))
    md = ("# 《龙卷风》分镜表 v2.0（帧级·A 批起草·双速对撞·词级卡点）\n\n"
          "> 权威=龙卷风-剧本-v2.md（含 v2.1/v2.2/v2.3 打磨批）+剧本-v3；词级锚点=anchors/龙卷风-shotgrid-resnap.json（word-onset/beat place·bpm 72.3·38 词行）\n"
          "> 片长 250.36s=ffprobe 实测·尾窗对齐歌长；窗=词行 cut0/cut1 原值·词行缝以 REUSE 定格延展补窗（零空档零叠窗）\n"
          "> 发布话术红线：禁称复刻邝盛版分镜·周杰伦/徐若瑄真名禁入提示词与物料；词曲双权注记随物料\n"
          "> 一歌一律=全专最冷色（现实青灰 / 闪回铅蓝黑·她=唯一暖点 2200K）；双速对撞=现实 0.82-0.95 慢稳 / 闪回 1.10-1.25 burst\n"
          "> 状态机读正身=本 py 文件（md=衍生物）；自检=lint（t2i/video 双模式）+WINDOW GAPS（0→250.36）+时长断言（源长=窗长/速度 ≤15s）\n\n"
          "## 女主选角案（CASTING-LAW 必携件）\n\n- 受众：%s\n- 默认候选：%s\n- 候选池：%s\n- 法条：%s\n\n## 镜头表（%d 新镜）\n\n%s\n"
          % (CASTING_LJF["audience"], CASTING_LJF["default_A"],
             "；".join(CASTING_LJF["candidates"]), CASTING_LJF["law_notes"], len(NEW), _md()))
    out = os.path.join(_HERE, "龙卷风-SHOTLIST-v4.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("md written:", out)