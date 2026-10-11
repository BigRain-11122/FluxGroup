# -*- coding: utf-8 -*-
# 星晴-shots-v2.py - 《星晴》全曲帧级分镜表 v2（深研喂入·词级卡点·变速设计·选角案）
# 权威=星晴-剧本-v1.md（创作核心）+ mv0002-星晴-立意案-v1 + RESEARCH-mv-craft-80s-90s-00s（§二/三/四/六 星晴行）
# 词级锚点=anchors/星晴.txt（whisper 2026-10-10 实测·尾词 248.76）·film=song 对齐·0-248.76
# 长期律：匀速判负（逐镜变速）/做旧克制（5246 日·5279 夜·台式奶黑 telecine）/禁看镜头/物质转场（天光暗/路灯亮/云影压路/星点亮）
#   叠化全片仅一处=星线成形（光丝连续生长）/音轨=画面+原曲/AIGC 开门帧标识/神似不形似
# 选角律=CASTING-LAW.md：本曲女主=独立面孔（XQ_HER 正典块·候选卡 KF 批另出供 CEO 点选）
# 卡点律：乐句切=默认（词窗行首）·数步段=一步一剪·数星段=一星一连线（立意案「数=剪辑本体」）
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
import prompt_lexicon as LX

# ---- 光照块扩展（本曲世界：黄昏街角→日光公路→金色坡→蓝调时刻→自然夜）----
LX.LIGHT["street_dusk"] = ("blue-hour dusk at 8000K over a 2000 Taipei street corner, low-pressure sodium streetlamp pools at 2200K laying deep orange over ink-blue asphalt, the shop signs just waking")
LX.LIGHT["day_road"] = ("soft bright late-afternoon daylight at 5200K over a mountain highway, the asphalt pale, the far ridge haze warm")
LX.LIGHT["sunset_rake"] = ("golden-hour sun at 2900K raking low across a grass slope, long warm shadows, a single small flare where the sun clips the ridge")
LX.LIGHT["dusk_blue"] = ("deep blue-hour ambience at 8000K with the first tungsten road lamp at 2800K waking on the mountain road, a warm band still holding at the horizon")
LX.LIGHT["night_road"] = ("ink-blue natural night over the mountain road, a single scooter headlight pool at 3000K carrying ahead, distant sodium village lights, the sky deep blue-black")
LX.LIGHT["star_field"] = ("an ink-blue natural night sky crowded with warm gold stars over a dark grass slope, a denser band of faint starlight across the middle of the sky, one warm flashlight pool low in frame")
LX.LIGHT["lamp_grass"] = ("one warm flashlight beam at 2800K lying low across night grass, silvergrass heads catching the rim, the slope beyond sinking into blue-black darkness")

STYLE_LEAD = "as a film still from a 2000 Taiwanese music video"

# ---- 人物正典块 ----
HIM = (LX.ID_M_2001_BONE + ", in a plain white short-sleeve shirt, dark denim jeans and worn canvas shoes")
# 星晴女主·候选A（默认·受众洞察卡锚=2000「甜美邻家」时代审美：鹅蛋脸/杏眼/中长黑直发斜刘海/彩色发夹/素色棉背心+低腰牛仔）
XQ_HER = ("a 20-year-old Taipei girl of the year 2000 with a soft oval face, gentle almond eyes, a small "
          "rounded nose, medium-length straight black hair with a soft side fringe pinned by a small colored "
          "hair clip, in a plain knit tank top, low-rise jeans and canvas shoes")
SCOOTER = ("an old 2000 Taipei scooter with a round headlight and chrome mirror, its paint dull from years of city rain")
KITE = ("a simple diamond paper kite in faded warm colors, a wooden cross spar and a long pale string wound on a bamboo spool")

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
    # ---- 前奏 0-30（她等→他来→双载出城）----
    ("XQ01", 0.00, 5.20, 0.90, "黄昏街角她靠墙等（蓝调×钠灯开场）",
     kf("med", "eye", "a 2000 Taipei street corner at dusk, %s waiting leaning against a tiled shopfront wall, her canvas bag on one shoulder, her breath visible in the cooling air" % XQ_HER, "street_dusk", lens="35", tex="film_day"),
     i2v("A medium shot at eye level", CM["static"], "A Taipei street corner at dusk, a girl in a pale-yellow blouse leaning against a shopfront wall under a sodium streetlamp, her ponytail moved by a light breeze, shop lights waking one by one along the street")),
    ("XQ02", 5.20, 9.80, 1.00, "他骑机车来",
     kf("med", "eye", "%s arriving on %s, slowing to a stop at the curb, his headlight washing the pavement" % (HIM, SCOOTER), "street_dusk", lens="50"),
     i2v("A medium shot at eye level", CM["track"], "A young man on a 2000 Taipei scooter rolling to the curb at dusk, the round headlight steady, his plain white shirt catching the sodium orange, the girl waiting at the wall behind him")),
    ("XQ03", 9.80, 14.50, 0.95, "她上后座",
     kf("cu", "eye", "%s stepping to the scooter and settling onto the back seat, one hand on his shoulder, the streetlamp orange on her sleeves" % XQ_HER, "street_dusk", lens="50"),
     i2v("A close-up at eye level", CM["static"], "A girl in a knit tank top stepping onto the back of a parked scooter at dusk, her hand resting on the rider's shoulder as she settles in, sodium light warm on her sleeve")),
    ("XQ04", 14.50, 20.50, 1.08, "双载穿过黄昏街景（街灯次亮）",
     kf("mw", "eye", "%s riding double on %s through a dusk Taipei street, her arms around his waist, shopfront lights waking along both sides" % (HIM, SCOOTER), "street_dusk", lens="35"),
     i2v("A medium-wide shot at eye level", CM["track"], "A scooter carrying two riding through a Taipei street at dusk, the girl's ponytail and loose hair strands lifting in the moving air, shop lights passing in warm layers on both sides")),
    ("XQ05", 20.50, 30.00, 1.05, "出城上郊山公路（城灯留在身后）",
     kf("ext", "high", "%s small on %s climbing the mountain highway out of the city, the Taipei basin haze sinking behind, the road pale ahead" % (HIM, SCOOTER), "dusk_blue", lens="24"),
     i2v("An extreme wide establishing shot from a high angle", CM["pullout"], "A scooter with two riders small on a mountain highway climbing away from the city, the basin lights falling behind, the road curving up toward the ridge in the last light")),

    # ---- 主歌1 30-51.8（趁风/蓝天边/云掉落/捏成形状）----
    ("XQ06", 30.00, 37.74, 1.10, "乘着风=车侧跟拍·风灌衣袖",
     kf("med", "eye", "%s riding double on %s along the mountain highway, wind pressing her blouse flat and freeing strands of her ponytail, the ridge haze bright" % (HIM, SCOOTER), "day_road", lens="35"),
     i2v("A medium shot at eye level", CM["track"], "A scooter riding along a mountain highway in late daylight, the wind pressing the girl's knit tank top flat and streaming her side-fringed hair, the road unrolling fast beside them")),
    ("XQ07", 37.74, 43.22, 0.92, "蓝天边=天大远景车小",
     kf("ext", "eye", "the sky taking most of the frame, a thin ridge line and %s tiny on the road below, the blue afternoon haze deep" % SCOOTER, "day_road", lens="24"),
     i2v("An extreme wide establishing shot at eye level", CM["tiltup"], "A wide sky over a thin mountain ridge, a scooter tiny on the pale road below, the camera easing up until the sky fills the frame, afternoon haze drifting")),
    ("XQ08", 43.22, 46.50, 1.00, "一片云掉落=云影压过公路",
     kf("med", "high", "a large soft cloud shadow sliding across the highway asphalt, the road grain deepening as the shadow passes over it", "day_road", lens="35"),
     i2v("A medium shot from a high angle", CM["static"], "The pale asphalt of a mountain highway as a large soft cloud shadow slides across it edge to edge, the road brightening and dimming as the cloud passes")),
    ("XQ09", 46.50, 51.80, 0.88, "捏成你的形状=她对云伸手",
     kf("med", "eye", "%s on the scooter back seat reaching one hand up toward the far sky, a tall cloud standing over the ridge like a quiet figure, her fingers open" % XQ_HER, "day_road", lens="50"),
     i2v("A medium shot at eye level", CM["pushin"], "A girl on the back of a moving scooter reaching one hand slowly up toward a tall cloud over the ridge, her fingers spreading against the sky, the cloud holding its shape")),

    # ---- 主歌1b 54.28-73.4（载着阳光/晴天/蝴蝶/因你而香）----
    ("XQ10", 54.28, 59.68, 1.02, "载着阳光=车影拉长在夕照",
     kf("wide", "low", "%s riding double with their long shadows stretched far down the road by the low sun, the asphalt warm and bright" % SCOOTER, "sunset_rake", lens="35"),
     i2v("A wide shot from a low angle", CM["static"], "A scooter with two riders and their long shadows reaching down a sunlit mountain road, the low sun warm across the asphalt, the shadows breathing with the road surface")),
    ("XQ11", 59.68, 64.62, 0.90, "都是晴天=她仰脸",
     kf("hs", "eye", "%s on the back seat with her face tipped up into the late sun, eyes closed, the warm light on her skin, a small smile settling" % XQ_HER, "sunset_rake", lens="85"),
     i2v("A head-and-shoulders framing at eye level", CM["pushin"], "A girl on a scooter back seat with her face tipped up into the warm low sun, eyes closed, sun freckles bright, her breath slow and easy as the ride hums on")),
    ("XQ12", 64.62, 70.08, 1.15, "蝴蝶自在飞=她追蝶（草地停车点）",
     kf("med", "eye", "%s running a few light steps across the grass slope after a white butterfly drifting ahead of her, silvergrass heads bowing in her wake" % XQ_HER, "sunset_rake", lens="35"),
     i2v("A medium shot at eye level", CM["stead"], "A girl in a knit tank top stepping quickly across a golden grass slope after a white butterfly, silvergrass heads swaying around her, her straight hair swinging with each step")),
    ("XQ13", 70.08, 73.42, 0.85, "因你而香=他看她（注视链·逆光）",
     kf("cu", "eye", "%s standing by the parked scooter watching her across the slope, the low sun behind her, his quiet attention carried in his stillness" % HIM, "sunset_rake", lens="50"),
     i2v("A close-up at eye level", CM["static"], "A young man by a parked scooter watching a girl chase a butterfly across a golden slope, the low sun flaring gently behind her, his stillness holding the whole frame")),

    # ---- 主歌2 73.42-101.36（夕阳飞翔/迎着风/手牵手数步）----
    ("XQ14", 73.42, 78.82, 1.00, "让夕阳飞翔=风筝线轴特写",
     kf("cu", "high", "hands paying out %s, the string unspooling through fingers, pale string dust lifting in the golden light" % KITE, "sunset_rake", lens="50"),
     i2v("A close-up from a high angle", CM["macroslide"] if "macroslide" in LX.CAM_MOVE else CM["static"], "Hands unwinding string from a bamboo spool for a diamond paper kite, the pale line running out fast through the fingers, golden light on the paper")),
    ("XQ15", 78.82, 86.82, 0.95, "风筝上天（摇起）",
     kf("wide", "low", "%s rising above the grass slope into the golden sky, its string taut from a low hand hold, the sun behind the paper" % KITE, "sunset_rake", lens="35"),
     i2v("A wide shot from a low angle", CM["tiltup"], "A diamond paper kite climbing away from a golden grass slope, the camera easing up to follow it into the warm sky, the string singing taut")),
    ("XQ16", 86.82, 95.58, 0.90, "并肩坐·线在两人之间（蓝调时刻转场）",
     kf("med", "eye", "%s and %s sitting side by side on the grass slope, the kite string passing between them, the first road lamp waking warm down the highway" % (HIM, XQ_HER), "dusk_blue", lens="35"),
     i2v("A medium shot at eye level", CM["static"], "A young man and a girl sitting side by side on a grass slope at blue hour, a kite string running up between them out of frame, the first road lamp waking warm down the highway")),
    ("XQ17", 95.58, 101.36, 1.00, "手牵手一步两步三步四步=白线并走（步点卡词·夜初）",
     kf("cu", "high", "two pairs of feet stepping together along the road center line under one streetlamp, his canvas shoe and her canvas shoe landing just past the white line, asphalt grain in the warm pool", "lamp_grass", lens="50", tex="film_night"),
     i2v("A close-up from a high angle", CM["track"], "Two pairs of shoes stepping in easy rhythm along a white road line under a streetlamp, the warm pool bright on the asphalt, each step landing just past the line")),

    # ---- 副歌1 101.36-140.76（数星连线/背对背/远星/它一定实现）----
    ("XQ18", 101.36, 106.64, 1.00, "看星星一颗两颗三颗四颗连成线=星点亮起+光丝连星（招牌镜）",
     kf("wide", "low", "the night sky above the dark slope, scattered warm gold stars and fine pale threads of light beginning to link a few of them into a crooked line, the grass a black rim at the frame bottom", "star_field", lens="24", tex="film_night"),
     i2v("A wide shot from a low angle", CM["tiltup"], "A night sky over a dark slope where warm gold stars light one after another and fine pale threads of light draw slowly between them, linking star to star into one crooked line")),
    ("XQ19", 106.64, 110.94, 0.88, "背对背默默许下心愿（缓升）",
     kf("mw", "eye", "%s and %s sitting back to back on the night grass, silhouettes against the faint starlight" % (HIM, XQ_HER), "star_field", lens="35", tex="film_night"),
     i2v("A medium-wide shot at eye level", CM["craneup"], "Two silhouettes sitting back to back on night grass under a sky of warm gold stars, the camera easing up and away from them, the night wind moving her hair strands")),
    ("XQ20", 111.84, 116.74, 0.85, "看远方的星=远星特写呼吸",
     kf("cu", "eye", "a single distant star steady in the ink-blue field, its warm point breathing with the fine grain of the night air around it", "star_field", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A single warm gold star holding steady in the ink-blue night, its point breathing softly, the fine starfield drifting almost imperceptibly around it")),
    ("XQ21", 122.98, 128.20, 0.92, "重复句=星线已成形全貌",
     kf("wide", "low", "the crooked star line now complete and quietly lit across the middle of the sky, five warm points held by pale threads, the slope dark below", "star_field", lens="24", tex="film_night"),
     i2v("A wide shot from a low angle", CM["pullout"], "A completed line of five warm gold stars linked by pale threads across the night sky, the camera easing back until the whole line reads end to end above the dark slope")),
    ("XQ22", 138.63, 140.76, 0.95, "它一定实现=指尖沿光丝划到头",
     kf("cu", "eye", "%s with her arm raised, one fingertip tracing slowly along the faint thread of the star line above her, her face following the star path" % XQ_HER, "star_field", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A girl on night grass with her arm raised, her fingertip moving slowly along an invisible line of stars above her, her face tilting as she follows it to the end")),

    # ---- 间奏 140.76-162.82（风筝线仍牵着）----
    ("XQ23", 140.76, 148.00, 1.00, "风筝线在夜里仍牵着",
     kf("cu", "eye", "the kite string running up out of frame into the dark, one hand holding the spool low, the line's faint silver catching starlight", "lamp_grass", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["tiltup"], "A pale kite string running up from a hand into the night sky, the line's faint silver catching starlight as it rises out of frame, the spool turning a slow notch")),
    ("XQ24", 148.00, 155.00, 0.95, "夜风·线微颤",
     kf("cu", "eye", "the kite line trembling in a night gust, the grass heads bowing in the same wind, one streetlamp far down the road breathing warm", "lamp_grass", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A kite line trembling in a night gust while silvergrass heads bow around it in the same wind, a distant streetlamp breathing warm orange down the road")),
    ("XQ25", 155.00, 162.82, 0.90, "两人回头望城里灯（人潮对比）",
     kf("med", "eye", "%s and %s standing turned toward the far city, the Taipei basin a low warm scatter of lights under the star line" % (HIM, XQ_HER), "night_road", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "Two figures from behind standing on a dark mountain road looking toward a far city, the basin lights a warm scatter below the stars, their stillness carrying the distance")),

    # ---- 主歌重演 162.82-195.70（夜色变体：骑行/她仰脸/风筝更高）----
    ("XQ26", 162.82, 172.38, 1.06, "夜骑=载着你仿佛载着阳光（夜版）",
     kf("med", "eye", "%s riding double on %s into the night road, the headlight cone carrying ahead, village sodium lights strung far down the valley" % (HIM, SCOOTER), "night_road", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "A scooter with two riders running a night mountain road, the headlight cone sweeping the asphalt, the girl's silhouette leaning gently with the curves, far sodium lights sliding past")),
    ("XQ27", 173.48, 181.44, 1.00, "她仰脸夜版=路旁花影（她转身笑）",
     kf("hs", "eye", "%s stopped beside the road in the headlight glow, turning back toward him with a smile, white roadside flowers catching the light around her" % XQ_HER, "night_road", lens="50", tex="film_night"),
     i2v("A head-and-shoulders framing at eye level", CM["static"], "A girl beside a night road in a warm headlight glow, white flowers catching the light around her as she turns back with a slow smile")),
    ("XQ28", 182.54, 192.80, 0.90, "风筝更高=夕飞夜版（逆着星）",
     kf("wide", "eye", "%s high in the dark sky above the slope, its paper dim against the stars, the string running down to a small hand at the frame edge" % KITE, "star_field", lens="35", tex="film_night"),
     i2v("A wide shot at eye level", CM["tiltup"], "A diamond kite small and dark high in a starfield night, its pale string running down out of frame, the stars steady behind it as the paper sways")),
    ("XQ29", 195.70, 202.62, 0.92, "迎着风=夜路并肩走",
     kf("med", "eye", "%s and %s walking side by side along the night highway shoulder, their hands nearly joined, the warm road lamp ahead of them" % (HIM, XQ_HER), "night_road", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["stead"], "A young man and a girl walking side by side along a night road toward a warm streetlamp, their hands nearly joined between them, the night wind moving their clothes")),

    # ---- 副歌2 203.68-248.76（夜版·更亮）----
    ("XQ30", 203.68, 209.36, 0.92, "手牵手夜版=白线并走（路灯池）",
     kf("wide", "high", "the two of them small on the road walking the white center line from lamp pool to lamp pool, their shadows paired and re-paired", "night_road", lens="35", tex="film_night"),
     i2v("A wide shot from a high angle", CM["track"], "Two figures small on a night road walking the white center line from one streetlamp pool to the next, their paired shadows stretching and turning as they pass each lamp")),
    ("XQ31", 209.36, 214.68, 0.98, "连线第二次=更亮",
     kf("wide", "low", "the star line lighting brighter this time, its threads a warmer gold, six points now holding the line, the whole sky a deep ink-blue drum", "star_field", lens="24", tex="film_night"),
     i2v("A wide shot from a low angle", CM["pushin"], "The star line over the dark slope brightening link by link, its pale threads warming to gold, the whole line steadying as the camera eases toward it")),
    ("XQ32", 236.26, 241.38, 0.92, "星线全貌映着两个剪影",
     kf("ext", "eye", "the full star line arched above the slope, and small below it the two silhouettes standing close, their heads tipped back", "star_field", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot at eye level", CM["cranedn"], "A complete line of linked stars arched above a dark slope, two tiny silhouettes below with their heads tipped back, the camera easing down toward them")),
    ("XQ33", 241.38, 248.76, 0.96, "这一定实现=最后一连+两剪影牵手定格（定格收）",
     kf("med", "eye", "the two brightest stars of the line completing one last link, and below in the dark the two silhouettes hand in hand, the grass heads still", "star_field", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "The last thread of light completing its link between the two brightest stars, and below in the dark two silhouettes standing hand in hand, everything settling to stillness")),
]

# ---- 重演律复用（副歌2 三轮词循环·已产素材回归）----
REUSE = [
    ("XQ17", 117.60, 122.98, 0.98, "手牵手 pass2=XQ17 回归"),
    ("XQ19", 128.20, 132.82, 0.90, "背对背 pass2=XQ19 回归"),
    ("XQ20", 133.31, 138.00, 0.85, "看远方的星 pass2=XQ20 回归"),
    ("XQ17", 225.42, 230.94, 0.96, "手牵手 pass3=XQ17 回归"),
    ("XQ19", 214.68, 219.16, 0.87, "背对背 夜版重演"),
    ("XQ20", 219.82, 224.50, 0.85, "看远方的星 夜版重演"),
    ("XQ31", 230.94, 236.26, 0.94, "看星星 pass3=XQ31 回归"),
]

# ---- 女主选角案（CASTING-LAW 必携件）----
CASTING_XQ = {
    "track": "星晴（mv-jay-01·P1 首发曲）",
    "audience": "星晴受众=跨代大众青春恋曲（80后+00后大合唱·嘉年华常设）——预期=2000「甜美邻家」时代审美（受众洞察卡锚：鹅蛋脸/杏眼/中长黑直发斜刘海/彩色发夹/素色棉背心+低腰牛仔·甜而不艳·禁性感化禁BE）",
    "default_A": "XQ_HER（上述正典块·受众卡脸型族锚直译）",
    "candidates": [
        "A=甜美邻家系（默认块·斜刘海/杏眼/彩色发夹·受众卡锚）",
        "B=甜系苹果肌（词表 ID_F_JOLIN 块·备选）",
        "C=清雅文静系（词表 ID_F_HOU 块·备选）",
    ],
    "law_notes": "每曲独立面孔（禁跨 MV 复用·与可爱女人 KN_HER 不同块）；AI 参照生成·真照不入管线；落定后 ID 块逐字复用",
}

def _md():
    rows = ["| 镜 | 窗口(s) | 速 | 内容 |", "|---|---|---|---|"]
    rows += ["| %s | %.2f-%.2f | %.2f | %s |" % (s[0], s[1], s[2], s[3], s[4]) for s in NEW]
    rows += ["", "**重演律复用**", "", "| 复用镜 | 窗口(s) | 速 | 说明 |", "|---|---|---|---|"]
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
    print("shots NEW=%d REUSE=%d lint_bad=%d" % (len(NEW), len(REUSE), bad))
    md = ("# 《星晴》分镜表 v2（帧级·深研喂入）\n\n"
          "> 权威=星晴-剧本-v1.md+立意案 v1+RESEARCH-mv-craft §六星晴行+RESEARCH-星晴-受众洞察-v1.md；词级锚点=anchors/星晴.txt（尾词 248.76）\n"
          "> **导演事实纠偏（受众卡①）**：原版星晴 MV 导演=黄中平（三源一致·非邝盛）——镜头权威=黄中平「弱剧情/极简/定格/色彩烘托」+年代共同语法；发布话术禁称「邝盛执导星晴」、禁称「复刻原版名场面」（骑行/牵手/星空=词面意象·非已证实 MV 镜头·改编话术只称「词面世界视觉化」）\n"
          "> 长期律：逐镜变速/5246日5279夜/台式奶黑/物质转场/叠化仅星线一处/禁看镜头/音轨=画面+原曲/AIGC 标识\n"
          "> 状态机读正身=本 py 文件（md=衍生物）；KF 批挂 bm-c（候选卡+空镜先行）·i2v 云端波待 CEO 过目 LOOKBOARD\n\n"
          "## 女主选角案（CASTING-LAW 必携件）\n\n- 受众：%s\n- 默认候选：%s\n- 候选池：%s\n- 法条：%s\n\n## 镜头表（%d 新镜）\n\n%s\n"
          % (CASTING_XQ["audience"], CASTING_XQ["default_A"],
             "；".join(CASTING_XQ["candidates"]), CASTING_XQ["law_notes"], len(NEW), _md()))
    out = os.path.join(_HERE, "星晴-SHOTLIST-v2.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("md written:", out)
