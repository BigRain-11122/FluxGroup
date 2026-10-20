# -*- coding: utf-8 -*-
# 星晴-shots-v2.py - 《星晴》全曲帧级分镜表 v2.2（深研喂入·词级卡点·变速设计·选角案）
# v2.1=设计闸判决机械补丁（PANEL-WAVE1/2-VERDICT-20261011·改窗/改词/改挂·不动立意不动结构）
# v2.2=复审残余清零（PANEL-REGATE-V3 §五 7 项一行级）：GRADE 2001→2000 本地覆写/XQ13 手持/XQ31-33 星点措辞链/XQ33 现画线句洗净/hair 长度词对齐
# v2.3=CEO 道具令（2026-10-11 22:3x「把关键帧里面的电动车换成自行车…不要出现这么掉氛围的东西」）：SCOOTER 常量退役→BICYCLE（2000 台式校园单车·钢架+后座铁架+车铃）/头灯系改小电池灯/6 帧同种子重摇（XQ02/05/07/10/13/26）
# v2.4=CEO 服装师令（2026-10-12 00:0x「服装师也要介入…要符合那个年代的流行！」）：XQ02 骑行抵达镜加 2000 街头配饰层（腰间系格纹衬衫+银细链·白T牛仔基底保留）·同种子重摇
# v2.5=XQ26 构图锁（10-12 晨检回炉件·多模态帧检：双人共骑被画成两车+亮脸违剪影）——kf/i2v 双词面加「side-saddle on rear rack + arms around waist + dark silhouettes」正向锁定·同种子重摇帧+重烧
# v2.6=五席修词批（四闸预检 8 项+视觉评审 15 回炉件）：双载锁位 XQ03/04/06/09/11+XQ07 帧补人+星线族 holding steady XQ19/21/31/32/33+细节锁 XQ14/17/23/24/25+XQ30 牵手（帧重做）+发夹 XQ01/12
# v2.7=XQ26 三烧剪影锚：night_ride 光块（二烧构图修复但亮脸复发——faces in shadow 入光块+subject 减负防超词限）
# v2.8=XQ26 四烧=导演席构图定谳：改背跟视角 seen from behind（三烧 faces in shadow 仍被 Krea2 暖肤惯性打穿——**正面脸剪影=该模型不可达判例**·搂腰背影=剪影结构性免疫+拥抱读感更佳=设计内升华）
# v2.9=XQ26 五烧：XQ_HER_BACK 背影专用块（四烧实证=背影位仍被 XQ_HER 脸部词诱导出回眸亮脸——**背影镜必须去脸部词**·身份标记=发型+发卡+服装）+night_ride 沉影措辞
# v2.10=held12 QC 回炉 2 格修词：XQ09 悬垂分词归位（her hand reaching——旧句 reaching 落最近主语=男主伸手）+XQ27 视线离轴（画内无他时 turning back toward him=模型读成看镜头·改 over her shoulder toward the road behind）
# v2.11=XQ27 三烧回归仰脸夜版本体（二烧瞳孔仍居中——**Krea2 转身先验=看镜头**·仰脸向花=结构性离轴·NOTE 本义「她仰脸夜版」=XQ11 夜变体）
# v2.12=XQ27 四烧=eyes closed 结构锁（三连看镜头定谳：单人脸+暖光=Krea2 瞳孔居中先验不可改——闭眼=XQ11 同曲过审先例·**单人脸暖光镜一律给眼睛明确状态**：闭眼/望具体目标物）
# v2.13=XQ27 五烧=止损定谳（四连看镜头含 eyes closed 失效）——**单人脸+暖光构图=看镜头先验不可破**·弃人脸变体回归 NOTE 本义「路旁花影」：花主体+她发肩软边入画（XQ26 同款去脸部词根治）
# 权威=星晴-剧本-v3.md（创作核心）+ mv0002-星晴-立意案-v1 + RESEARCH-mv-craft-80s-90s-00s（§二/三/四/六 星晴行）
# 词级锚点=anchors/星晴.txt（whisper 2026-10-10 实测·尾词 248.76）·film=song 对齐·0-259.40（ffprobe 判决一实证·尾窗定格延展收尾奏）
# 长期律：匀速判负（逐镜变速）/做旧克制（5246 纯日戏·5279 黄昏蓝调+夜·台式奶黑 telecine）/禁看镜头/物质转场（天光暗/路灯亮/云影压路/星点亮）
#   叠化全片仅一处=星线成形（XF_T1=XQ18a→XQ18b 1.5s·光丝连续生长）/音轨=画面+原曲/AIGC 开门帧标识/神似不形似
# 发布话术红线：禁称邝盛执导星晴（原版导演=黄中平·三源）；禁称复刻原版名场面（骑行/牵手/星空=词面意象视觉化）
# 词曲双权：发布物料必挂『词曲著作权/录音制作者权授权中』注记（承 INDEX 五）
# 选角律=CASTING-LAW.md：本曲女主=独立面孔（XQ_HER 正典块·候选卡 KF 批另出供 CEO 点选）
# 卡点律：乐句切=默认（词窗行首）·数步段=一步一剪（XQ17a-d 阶梯渐快·同种子同帧装配切分）·数星段=一星一连线（XQ18a 散星→XQ18b 成丝）
# jman LoRA 挂载=mv_full_kf_r2.py L88 范式·strength 0.6-0.8 先网格（判决二可7）
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
import prompt_lexicon as LX

# ---- 光照块扩展（本曲世界：黄昏街角→日光公路→金色坡→蓝调时刻→自然夜）----
LX.LIGHT["street_dusk"] = ("blue-hour dusk at 8000K over a 2000 Taipei street corner, low-pressure sodium "
                           "streetlamp pools at 2200K laying deep orange over ink-blue asphalt, aged "
                           "hand-painted signboards and old neon tubes just waking")
LX.LIGHT["day_road"] = ("soft bright late-afternoon daylight at 5200K over a mountain highway, the asphalt pale, the far ridge haze warm")
LX.LIGHT["sunset_rake"] = ("golden-hour sun at 2900K raking low across a grass slope, long warm shadows, a single small flare where the sun clips the ridge")
LX.LIGHT["dusk_blue"] = ("deep blue-hour ambience at 8000K with the first tungsten road lamp at 2800K waking on the mountain road, a warm band still holding at the horizon")
LX.LIGHT["night_road"] = ("ink-blue natural night over the mountain road, a small bicycle battery lamp pool at 3000K carrying ahead, distant sodium village lights, the sky deep blue-black")
# XQ26 三烧剪影锚（二烧构图修复但亮脸复发=灯池照亮面部——剪影语义入光块·对冲 GRADE 尾 warm skin tones 惯性）
LX.LIGHT["night_ride"] = ("ink-blue night over the mountain road, the small battery lamp's warm pool held low on the asphalt, the two riders sinking into shadow against far sodium lights, only their outlines catching the far glow, deep blue-black sky")
LX.LIGHT["star_field"] = ("an ink-blue natural night sky crowded with warm gold stars over a dark grass slope, a denser band of faint starlight across the middle of the sky, one warm flashlight pool low in frame")
LX.LIGHT["star_field_pure"] = ("an ink-blue natural night sky crowded with warm gold stars, a denser band of faint starlight across the middle, the dark grass a low rim at the frame bottom")
LX.LIGHT["lamp_grass"] = ("one warm flashlight beam at 2800K lying low across night grass, silvergrass heads catching the rim, the slope beyond sinking into blue-black darkness")
LX.LIGHT["streetlamp_pool"] = ("one streetlamp pool at 2800K lying on the road center line, the white line bright inside the warm circle, the asphalt fading to blue-black beyond")

# macroslide 去污（判决二可1）：扩无 cuneiform 的 slide 变体，XQ14 运镜改挂
LX.CAM_MOVE["slide"] = "the camera slides laterally with small amplitude at slow speed in shallow focus"

STYLE_LEAD = "as a film still from a 2000 Taiwanese music video"

# 残余⑤（复审 v2.2）：专辑年代=2000——GRADE 本地覆写统一（共享词表 tw2001 块=mv0001 范特西 2001 在飞正身·不动）
GRADE_2000 = LX.GRADE["tw2001"].replace("2001 telecine", "2000 telecine")

# ---- 人物正典块 ----
# jman 触发词前置（判决一选1）：全部含 HIM 镜自动继承；KF 工单挂 jman_v1_640_rank32_final.safetensors（L88 范式）
HIM = ("jman, " + LX.ID_M_2001_BONE + ", in a plain white short-sleeve shirt, dark denim jeans and worn canvas shoes")
# 星晴女主·候选A（默认·受众洞察卡锚=2000「甜美邻家」时代审美：鹅蛋脸/杏眼/中长黑直发斜刘海/彩色发夹/素色棉背心+低腰牛仔）
XQ_HER = ("a 20-year-old Taipei girl of the year 2000 with a soft oval face, gentle almond eyes, a small "
          "rounded nose, medium-length straight black hair with a soft side fringe pinned by a small colored "
          "hair clip, in a plain knit tank top, low-rise jeans and canvas shoes")
BICYCLE = ("an old 2000 Taipei campus bicycle with a rear rack and a chrome bell, its paint dull from use")
# 双人近身镜词面预算位（lint ≤200）：全量常量挤爆时用短形（年代锚「old 2000 Taipei campus bicycle」保留·车铃细节让位脸级 ID 块）
BICYCLE_SHORT = "the old 2000 Taipei campus bicycle"
# 剪影/背影镜专用女主块（XQ26 四烧判例：XQ_HER 脸部词在背影视角=回眸亮脸诱导——背影镜只留发型+发卡+服装身份标记·零脸部词）
XQ_HER_BACK = "a girl with medium-length straight black hair and a small colored hair clip, in a plain knit tank top and low-rise jeans"
KITE = ("a simple diamond paper kite in faded warm colors, a wooden cross spar and a long pale string wound on a bamboo spool")

def kf(shot, angle, subject, light, lens="35", tex="film_day", extra=""):
    s = "A %s of %s, %s. %s. Shot on %s, %s, %s, %s." % (
        LX.SHOT_SIZE[shot], subject, LX.CAM_ANGLE[angle],
        LX.LIGHT[light].capitalize(), LX.LENS[lens],
        GRADE_2000, LX.TEXTURE[tex], STYLE_LEAD)
    return s + (" " + extra if extra else "")

I2V_TAIL = ("Warm 2000 Taiwanese telecine grade, warm skin tones, milky lifted blacks. "
            "Visible 35mm film grain. Restrained continuous motion, camera and subject motion only.")

def i2v(size_angle, motion, content):
    return ("Single continuous take at 24fps, 16:9. %s; %s. %s. " % (size_angle, motion, content)) + I2V_TAIL

CM = LX.CAM_MOVE

# XF_T1=唯一叠化：XQ18a→XQ18b 1.5s（星晴全片仅此一处·判决二可4 KF 双帧叠化交付·i2v 禁现画线）
XF_T1 = {"from": "XQ18a", "to": "XQ18b", "dissolve_s": 1.1}

# 数步段共用源帧（一步一剪·同种子同帧·装配切分·判决二工3）
_XQ17_KF = kf("cu", "high", "two pairs of feet stepping together along the road center line under one streetlamp, his canvas shoe and her canvas shoe landing just past the white line, asphalt grain in the warm pool", "streetlamp_pool", lens="50", tex="film_night")
_XQ17_I2V = i2v("A close-up from a high angle", CM["track"], "Two pairs of shoes stepping together in easy rhythm along a white road line under a streetlamp, the warm pool bright on the asphalt, each pair of steps landing just past the line in time")

# ================= 新产镜头（38 镜）=================
# (id, t0, t1, speed, note, kf_prompt, i2v_prompt)
NEW = [
    # ---- 前奏 0-30（她等→他来→双载出城）----
    ("XQ01", 0.00, 5.20, 0.90, "黄昏街角她靠墙等（蓝调×钠灯开场）",
     kf("med", "eye", "a 2000 Taipei street corner at dusk, %s waiting leaning against a tiled shopfront wall, her canvas bag on one shoulder, her breath visible in the cooling air" % XQ_HER, "street_dusk", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "A Taipei street corner at dusk, a girl in a plain knit tank top leaning against a shopfront wall under a sodium streetlamp, her medium-length straight black hair with a soft side fringe and a small colored hair clip moved by a light breeze, shop lights waking one by one along the street")),
    ("XQ02", 5.20, 9.80, 1.00, "他骑单车来",
     kf("med", "eye", "%s arriving on %s, a plaid flannel shirt tied around his waist, a thin silver chain catching the streetlamp, slowing to a stop at the curb, one small ring of the chrome bell" % (HIM, BICYCLE), "street_dusk", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "A young man on an old black campus bicycle rolling to the curb at dusk, a plaid flannel shirt tied around his waist, a thin silver chain catching the sodium orange, a distant, soft-focus girl waiting at the wall behind him")),
    ("XQ03", 9.80, 14.50, 0.95, "她上后座",
     kf("cu", "eye", "%s stepping to %s and settling onto its rear rack seat behind %s on the saddle, her hand on his shoulder" % (XQ_HER, BICYCLE_SHORT, HIM), "street_dusk", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A girl in a knit tank top settling onto the rear rack of a parked old campus bicycle at dusk, the boy seated on the saddle in front of her, her hand resting on his shoulder as she settles in, sodium light warm on her sleeve")),
    ("XQ04", 14.50, 20.50, 1.08, "双载穿过黄昏街景（街灯次亮）",
     kf("mw", "eye", "%s and %s riding double on the old campus bicycle through the dusk street, her arms around his waist, shopfront lights waking" % (HIM, XQ_HER), "street_dusk", lens="35", tex="film_night"),
     i2v("A medium-wide shot at eye level", CM["track"], "An old campus bicycle with two riders passing through a Taipei street at dusk, the girl seated on the rear rack behind the boy with her arms around his waist, her medium-length straight black hair with a soft side fringe lifting in the moving air, shop lights passing in warm layers on both sides")),
    ("XQ05", 20.50, 30.00, 1.05, "出城上郊山公路（城灯留在身后·片头车辆记忆）",
     kf("ext", "high", "two distant figures small on %s climbing the mountain highway out of the city, the Taipei basin haze sinking behind, the road pale ahead" % BICYCLE, "dusk_blue", lens="24", tex="film_night", extra="an old sedan passing in the opposite lane"),
     i2v("An extreme wide establishing shot from a high angle", CM["pullout"], "An old bicycle with two riders small on a mountain highway climbing away from the city, the pedals turning slowly, the basin lights falling behind, the road curving up toward the ridge in the last light, a single old sedan passing in the opposite lane")),

    # ---- 主歌1 30-51.8（趁风/蓝天边/云掉落/捏成形状/一口一口吃掉忧愁·词窗重切=判决一 TOP3）----
    ("XQ06", 30.00, 33.16, 1.10, "乘着风=车侧跟拍·风灌衣袖",
     kf("med", "eye", "%s pedaling %s with %s side-saddle on its rear rack, her arms around his waist, wind lifting her soft side fringe, the ridge haze bright" % (HIM, BICYCLE_SHORT, XQ_HER), "day_road", lens="35"),
     i2v("A medium shot at eye level", CM["track"], "An old campus bicycle with two riders rolling along a mountain highway in late daylight, the girl seated on the rear rack behind the boy, the pedals turning steadily, the wind pressing the girl's knit tank top flat and streaming her side-fringed hair, the road unrolling beside them")),
    ("XQ07", 33.16, 38.52, 0.92, "蓝天边=天大远景车小",
     kf("ext", "eye", "the sky taking most of the frame, a thin ridge line and %s with its two riders tiny on the road below, the blue afternoon haze deep" % BICYCLE, "day_road", lens="24"),
     i2v("An extreme wide establishing shot at eye level", CM["tiltup"], "A wide sky over a thin mountain ridge, an old bicycle with its two riders tiny on the pale road below, the camera easing up until the sky fills the frame, afternoon haze drifting")),
    ("XQ08", 38.52, 43.86, 1.00, "一片云掉落=云影压过公路",
     kf("med", "high", "a large soft cloud shadow sliding across the highway asphalt, the road grain deepening as the shadow passes over it", "day_road", lens="35"),
     i2v("A medium shot from a high angle", CM["static"], "The pale asphalt of a mountain highway as a large soft cloud shadow slides across it edge to edge, the road brightening and dimming as the cloud passes")),
    ("XQ09", 43.86, 47.00, 0.88, "捏成你的形状=她对云伸手",
     kf("med", "eye", "%s on the rear rack seat of %s behind the boy pedaling ahead of her, her hand reaching up toward the far sky, a tall cloud standing over the ridge like a quiet figure, her fingers open" % (XQ_HER, BICYCLE), "day_road", lens="50"),
     i2v("A medium shot at eye level", CM["pushin"], "A girl on the rear rack of a moving old campus bicycle, the boy pedaling in front of her, her hand reaching slowly up toward a tall cloud over the ridge, her fingers spreading against the sky, the cloud holding its shape")),
    ("XQ09b", 47.00, 51.80, 0.92, "一口一口吃掉忧愁=风把路边蒲公英逐颗吃走（判决一 TOP3 补镜）",
     kf("cu", "high", "wind lifting dandelion seeds one by one off the roadside grass, each small white head breaking free and drifting away over the road", "day_road", lens="85"),
     i2v("A close-up from a high angle", CM["static"], "Dandelion seed heads breaking free of the roadside grass one by one, each white head lifting and drifting away over the warm road, the bare stems left behind")),

    # ---- 主歌1b 54.28-73.4（载着阳光/晴天/蝴蝶/因你而香）----
    ("XQ10", 54.28, 59.68, 1.02, "载着阳光=车影拉长在夕照",
     kf("wide", "low", "two distant figures riding double on %s with their long shadows stretched far down the road by the low sun, the asphalt warm and bright" % BICYCLE, "sunset_rake", lens="35"),
     i2v("A wide shot from a low angle", CM["static"], "An old bicycle carrying its two riders steadily down a sunlit mountain road, their long shadows reaching the whole way, the low sun warm across the asphalt, the shadows breathing with the road surface")),
    ("XQ11", 59.68, 64.62, 0.90, "都是晴天=她仰脸",
     kf("hs", "eye", "%s on the rear rack seat of %s, the boy pedaling ahead of her, her face tipped up into the late sun, eyes closed, the warm light on her skin, a small smile settling" % (XQ_HER, BICYCLE), "sunset_rake", lens="85"),
     i2v("A head-and-shoulders framing at eye level", CM["pushin"], "A girl on the rear rack of a moving bicycle, the boy pedaling in front of her, her face tipped up into the warm low sun, eyes closed, sun freckles bright, her breath slow and easy as the ride hums on")),
    ("XQ12", 64.62, 70.08, 1.15, "蝴蝶自在飞=她追蝶（草地停车点）",
     kf("med", "eye", "%s running a few light steps across the grass slope after a white butterfly drifting ahead of her, silvergrass heads bowing in her wake" % XQ_HER, "sunset_rake", lens="35"),
     i2v("A medium shot at eye level", CM["stead"], "A girl in a knit tank top stepping quickly across a golden grass slope after a white butterfly, silvergrass heads swaying around her, her straight hair swinging with each step, a small colored hair clip holding her side fringe")),
    ("XQ13", 70.08, 73.42, 0.85, "因你而香=他看她（注视链·逆光·手持生活流=残余③）",
     kf("cu", "eye", "%s standing beside the parked old bicycle, one hand resting on its saddle, watching a distant girl figure chase a white butterfly across the slope, the low sun behind her, his quiet attention carried in his stillness" % HIM, "sunset_rake", lens="50"),
     i2v("A close-up at eye level", CM["hand"], "A young man beside a parked old bicycle watching a girl chase a butterfly across a golden slope, the low sun flaring gently behind her, his stillness holding the whole frame")),

    # ---- 主歌2 73.42-101.36（夕阳飞翔/迎着风/手牵手数步·一步一剪）----
    ("XQ14", 73.42, 78.82, 1.00, "让夕阳飞翔=风筝线轴特写",
     kf("cu", "high", "hands paying out %s, the string unspooling through fingers, pale string dust lifting in the golden light" % KITE, "sunset_rake", lens="50"),
     i2v("A close-up from a high angle", CM["slide"], "Hands unwinding string from a bamboo spool for a diamond paper kite, the pale line running out whole and taut through steady fingers, golden light on the paper")),
    ("XQ15", 78.82, 86.82, 0.95, "风筝上天（摇起）",
     kf("wide", "low", "%s rising above the grass slope into the golden sky, its string taut from a low hand hold, the sun behind the paper" % KITE, "sunset_rake", lens="35"),
     i2v("A wide shot from a low angle", CM["tiltup"], "A diamond paper kite climbing away from a golden grass slope, the camera easing up to follow it into the warm sky, the string singing taut")),
    ("XQ16", 86.82, 95.58, 0.90, "并肩坐·线在两人之间（蓝调时刻转场）",
     kf("med", "eye", "%s and %s sitting side by side on the grass slope, the kite string passing between them, the first road lamp waking warm down the highway" % (HIM, XQ_HER), "dusk_blue", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "A young man and a girl sitting side by side on a grass slope at blue hour, a kite string running up between them out of frame, the first road lamp waking warm down the highway")),
    # 数步段拆分（判决二工3）：一步一剪·阶梯渐快·同种子同帧·装配切分
    ("XQ17a", 95.58, 97.04, 1.00, "手牵手一步两步三步四步=白线并走·一步一剪①（同种子同帧·装配切分）", _XQ17_KF, _XQ17_I2V),
    ("XQ17b", 97.04, 98.50, 1.06, "手牵手一步两步三步四步=白线并走·一步一剪②（阶梯渐快）", _XQ17_KF, _XQ17_I2V),
    ("XQ17c", 98.50, 99.93, 1.12, "手牵手一步两步三步四步=白线并走·一步一剪③（阶梯渐快）", _XQ17_KF, _XQ17_I2V),
    ("XQ17d", 99.93, 101.36, 1.18, "手牵手一步两步三步四步=白线并走·一步一剪④（阶梯渐快）", _XQ17_KF, _XQ17_I2V),

    # ---- 副歌1 101.36-140.76（数星连线=XQ18a 散星→XQ18b 成丝·XF_T1 唯一叠化/背对背/远星/它一定实现）----
    ("XQ18a", 101.36, 103.90, 1.00, "看星星一颗两颗三颗四颗=散星逐颗亮（数星段·一星一连线·无丝版=叠化源帧A）",
     kf("wide", "low", "the night sky above the dark slope, scattered warm gold stars, their places steady, a faint denser band across the middle of the sky", "star_field", lens="24", tex="film_night"),
     i2v("A wide shot from a low angle", CM["tiltup"], "Warm gold stars lighting one after another, each star holding its place with a slow twinkle")),
    ("XQ18b", 103.90, 106.64, 1.00, "连成线=光丝连星（成丝版=叠化源帧B·XF_T1 落点）",
     kf("wide", "low", "the same night sky, a crooked line of five warm gold stars now linked by fine pale threads of light, the threads thin and steady", "star_field", lens="24", tex="film_night"),
     i2v("A wide shot from a low angle", CM["static"], "The linked stars holding their threads steady, each star holding its place with a slow twinkle")),
    ("XQ19", 106.64, 110.94, 0.88, "背对背默默许下心愿（缓升）",
     kf("mw", "eye", "%s and %s sitting back to back on the night grass, silhouettes against the faint starlight" % (HIM, XQ_HER), "star_field_pure", lens="35", tex="film_night"),
     i2v("A medium-wide shot at eye level", CM["craneup"], "Two silhouettes sitting back to back on night grass under a sky of warm gold stars holding their places, the camera easing up and away from them, the night wind moving her hair strands")),
    ("XQ20", 111.84, 116.74, 0.85, "看远方的星=远星特写呼吸",
     kf("cu", "eye", "a single distant star steady in the ink-blue field, its warm point breathing with the fine grain of the night air around it", "star_field", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A single warm gold star holding steady in the ink-blue night, its point breathing softly, the fine starfield drifting almost imperceptibly around it")),
    ("XQ21", 122.98, 128.20, 0.92, "重复句=星线五点成形·第六星初醒（判决二工4）",
     kf("wide", "low", "the crooked line of five warm stars holding its threads, a sixth star beginning to wake at the line's end", "star_field", lens="24", tex="film_night"),
     i2v("A wide shot from a low angle", CM["pullout"], "A completed line of five warm gold stars linked by pale threads holding steady across the night sky, a sixth star waking brighter at the line's end as the camera eases back until the whole line reads end to end above the dark slope")),
    ("XQ22", 138.63, 140.76, 0.95, "它一定实现=指尖沿光丝划到头",
     kf("cu", "eye", "%s with her arm raised, one fingertip tracing slowly along the faint thread of the star line above her, her face following the star path" % XQ_HER, "star_field_pure", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A girl on night grass with her arm raised, her fingertip moving slowly along the faint gold thread already in the sky, the thread holding steady, her face catching the star line's warm glow as she follows it to the end")),

    # ---- 间奏 140.76-162.82（风筝线仍牵着）----
    ("XQ23", 140.76, 148.00, 1.00, "风筝线在夜里仍牵着",
     kf("cu", "eye", "the kite string running up out of frame into the dark, one hand holding the spool low, the line's faint silver catching starlight", "lamp_grass", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["tiltup"], "A pale kite string running up from a steady hand into the night sky, the camera following the line up out of frame, the line's faint silver catching starlight, the spool turning a slow notch, the fingers clear")),
    ("XQ24", 148.00, 155.00, 0.95, "夜风·线微颤",
     kf("cu", "eye", "the kite line trembling in a night gust, the grass heads bowing in the same wind, one streetlamp far down the road breathing warm", "lamp_grass", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A kite line trembling in a night gust while silvergrass heads bow around it in the same wind, the distant streetlamp a small steady point of warm orange far down the road")),
    ("XQ25", 155.00, 162.82, 0.90, "两人回头望城里灯=俯拍人物致敬（受众卡①·判决一受1）",
     kf("med", "top", "two distant figures standing on the dark mountain road seen from directly above, turned toward the far city lights, the road a pale thread beside them", "night_road", lens="35", tex="film_night"),
     i2v("A medium shot", CM["static"], "A top-down view of only two figures standing close on an empty dark road, the far city a scatter of soft unreadable light points beyond the ridge, the night wind moving their clothes")),

    # ---- 主歌重演 162.82-195.70（夜色变体：骑行/她仰脸/风筝更高）----
    ("XQ26", 162.82, 172.38, 1.06, "夜骑=载着你仿佛载着阳光（夜版）",
     kf("med", "eye", "%s pedaling %s seen from behind, %s seated side-saddle on its rear rack, her arms around his waist, her head bowed toward his back" % (HIM, BICYCLE_SHORT, XQ_HER_BACK), "night_ride", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "An old bicycle carrying two down a night mountain road seen from behind, the girl seated on the rear rack leaning with the curves, both riders dark silhouettes, the small lamp's thin warm beam touching the asphalt ahead, far sodium lights sliding past")),
    ("XQ27", 173.48, 181.44, 1.00, "路旁花影夜版（花主体+她发肩软边·人脸变体四翻车判例弃用=单人脸暖光构图看镜头先验不可破）",
     kf("cu", "eye", "white roadside flowers catching the small bicycle lamp glow, her shoulder and the soft edge of her hair entering the frame beside them, the night road dark beyond", "night_road", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "White flowers swaying in the warm glow of a small bicycle lamp, her hair edge and shoulder soft at the frame edge, the night road breathing dark beyond")),
    ("XQ28", 182.54, 192.80, 0.90, "风筝更高=夕飞夜版（逆着星）",
     kf("wide", "eye", "%s high in the dark sky above the slope, its paper dim against the stars, the string running down to a small hand at the frame edge" % KITE, "star_field", lens="35", tex="film_night"),
     i2v("A wide shot at eye level", CM["tiltup"], "A diamond kite small and dark high in a starfield night, its pale string running down out of frame, the stars steady behind it as the paper sways")),
    ("XQ29", 195.70, 202.62, 0.92, "迎着风=夜路并肩走",
     kf("med", "eye", "%s and %s walking side by side along the night highway shoulder, their hands nearly joined, the warm road lamp ahead of them" % (HIM, XQ_HER), "night_road", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["stead"], "A young man and a girl walking side by side along a night road toward a warm streetlamp, their hands nearly joined between them, the night wind moving their clothes")),

    # ---- 副歌2 203.68-259.40（夜版·更亮·尾窗延至片长）----
    ("XQ30", 203.68, 209.36, 0.94, "手牵手夜版=白线并走（路灯池）",
     kf("wide", "high", "two distant figures small on the road walking the white center line from lamp pool to lamp pool, their joined hands between them, their shadows paired and re-paired", "night_road", lens="35", tex="film_night"),
     i2v("A wide shot from a high angle", CM["track"], "Two figures small on a night road walking the white center line from one streetlamp pool to the next, their joined hands between them, their paired shadows stretching and turning as they pass each lamp")),
    ("XQ31", 209.36, 214.68, 0.98, "连线第二次=更亮",
     kf("wide", "low", "the star line lighting brighter this time, its five linked threads a warmer gold, a sixth star awake at the line's end, the whole sky a deep ink-blue drum", "star_field", lens="24", tex="film_night"),
     i2v("A wide shot from a low angle", CM["pushin"], "The star line over the dark slope holding brighter, its five warm gold threads steady and whole end to end, a sixth star awake at the line's end, the camera easing toward it")),
    ("XQ32", 236.26, 241.38, 0.92, "星线全貌映着两个剪影",
     kf("ext", "eye", "the full star line arched above the slope, and small below it the two silhouettes standing close, their heads tipped back", "star_field_pure", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot at eye level", CM["cranedn"], "A complete line of linked stars arched above a dark slope, its threads even and steady as the only light in the sky, two tiny silhouettes below with their heads tipped back, the camera easing down toward them")),
    ("XQ33", 241.38, 259.40, 0.96, "第六星光丝落定+定格延窗收尾奏（装配=剪辑席微呼吸案：冻结+极慢推 13s 累计缩 3-4%·fade 251s 起 8s 渐黑·源 5s·i2v 禁现画线=残余④）",
     kf("med", "eye", "the sixth star of the line joined by one last thread of pale gold light, the line complete end to end, and below in the dark the two silhouettes hand in hand, the grass heads still", "star_field_pure", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "The completed star line resting still and whole end to end, its threads quiet, the newest thread of pale gold light settled between the last two stars, and below in the dark two silhouettes standing hand in hand, everything settling to stillness")),
]

# ---- 重演律复用（副歌2 三轮词循环·已产素材回归）+ 漏窗补齐（判决二工1·≤3s=前镜定格延展/>3s=邻镜双挂）----
REUSE = [
    ("XQ09b", 51.80, 54.28, 1.00, "定格延展补窗"),
    ("XQ19", 110.94, 111.84, 1.00, "定格延展补窗"),
    ("XQ20", 116.74, 117.60, 1.00, "定格延展补窗"),
    ("XQ17", 117.60, 122.98, 0.98, "手牵手 pass2=XQ17 回归"),
    ("XQ19", 128.20, 132.82, 0.90, "背对背 pass2=XQ19 回归"),
    ("XQ21", 132.82, 133.31, 1.00, "定格延展补窗"),
    ("XQ20", 133.31, 138.00, 0.80, "看远方的星 pass2=XQ20 回归"),
    ("XQ20", 138.00, 138.63, 1.00, "定格延展补窗"),
    ("XQ26", 172.38, 173.48, 1.00, "定格延展补窗"),
    ("XQ27", 181.44, 182.54, 1.00, "定格延展补窗"),
    ("XQ26", 192.80, 195.70, 0.90, "双挂补窗（XQ26 前半）"),
    ("XQ29", 202.62, 203.68, 1.00, "定格延展补窗"),
    ("XQ19", 214.68, 219.16, 0.87, "背对背 重演"),
    ("XQ20", 219.16, 219.82, 1.00, "定格延展补窗"),
    ("XQ20", 219.82, 224.50, 0.90, "看远方的星 重演"),
    ("XQ19", 224.50, 225.42, 1.00, "定格延展补窗"),
    ("XQ17", 225.42, 230.94, 0.96, "手牵手 pass3=XQ17 回归"),
    ("XQ31", 230.94, 236.26, 0.94, "看星星 pass3=XQ31 回归"),
]

FILM_END = 259.40  # ffprobe 片长实测（判决一 TOP1·XQ33 定格延窗对齐）

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
    "law_notes": "每曲独立面孔（禁跨 MV 复用·与可爱女人 KN_HER 不同块）；AI 参照生成·真照不入管线；落定后 ID 块逐字复用；定脸后即跑以图搜人反向测试留档（合规席·XQ_HER 落定候选+jman 成帧后必跑·LOOKBOARD 附件留证）",
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
    md = ("# 《星晴》分镜表 v2.13（帧级·深研喂入·设计闸判决落地版·CEO 道具令+服装师令+五席修词执法）\n\n"
          "> 权威=星晴-剧本-v3.md（v1.1 修订同步）+立意案 v1+RESEARCH-mv-craft §六星晴行+RESEARCH-星晴-受众洞察-v1.md；词级锚点=anchors/星晴.txt（尾词 248.76）·片长 259.40（ffprobe 判决一实证）\n"
          "> **导演事实纠偏（受众卡①）**：原版星晴 MV 导演=黄中平（三源一致·非邝盛）——镜头权威=黄中平「弱剧情/极简/定格/色彩烘托」+年代共同语法\n"
          "> 发布话术红线：禁称邝盛执导星晴（原版导演=黄中平·三源）；禁称复刻原版名场面（骑行/牵手/星空=词面意象视觉化）\n"
          "> 词曲双权：发布物料必挂『词曲著作权/录音制作者权授权中』注记（承 INDEX 五）\n"
          "> jman LoRA 挂载=mv_full_kf_r2.py L88 范式（jman_v1_640_rank32_final.safetensors）·strength 0.6-0.8 先网格（判决二可7）·含 HIM 镜自动继承触发词\n"
          "> XF_T1=唯一叠化：XQ18a→XQ18b 1.5s（星晴全片仅此一处·星线成形=KF 双帧叠化交付·i2v 禁现画线）\n"
          "> 长期律：逐镜变速/5246 纯日戏·5279 黄昏蓝调+夜（XQ01-05/16 补档·判决二年1）/台式奶黑/物质转场/禁看镜头/音轨=画面+原曲/AIGC 标识\n"
          "> **CEO 道具令（10-11 22:3x）**：载具全量=2000 台式校园单车（旧钢架+后座铁架+车铃·夜戏小电池灯）——机车/电动车=年代错位判负；道具席+导演席帧级 QC 必含时代错位道具扫描位\n"
          "> 状态机读正身=本 py 文件（md=衍生物）；自检=lint（t2i/video 双模式）+WINDOW GAPS（0→259.40 无 >0.5s 空档）+时长断言（源长=窗长/速度 ≤15s·定格延窗镜只验源 5s）\n\n"
          "## 女主选角案（CASTING-LAW 必携件）\n\n- 受众：%s\n- 默认候选：%s\n- 候选池：%s\n- 法条：%s\n\n## 镜头表（%d 新镜）\n\n%s\n"
          % (CASTING_XQ["audience"], CASTING_XQ["default_A"],
             "；".join(CASTING_XQ["candidates"]), CASTING_XQ["law_notes"], len(NEW), _md()))
    out = os.path.join(_HERE, "星晴-SHOTLIST-v2.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("md written:", out)
