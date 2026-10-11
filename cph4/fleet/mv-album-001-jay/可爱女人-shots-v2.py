# -*- coding: utf-8 -*-
# 可爱女人-shots-v2.py - 《可爱女人》全曲帧级分镜表 v2（深研喂入·词级卡点·变速设计·选角案）
# 权威=可爱女人-剧本-v1.md（创作核心：纸飞机投掷-归返弧）+ RESEARCH-mv-craft-80s-90s-00s（§一/三/六 可爱女人行）
# 词级锚点=anchors/可爱女人.txt（whisper 2026-10-10 实测·词行至 236.30）·film=song 对齐·0-247
# 长期律：匀速判负（掷出快/穿云极缓·逐镜变速）/做旧克制（5246黄昏段·5279夜段·台式奶黑）/禁看镜头（她=远景/剪影/灯窗）
#   物质转场（云层吞机/星尘化开/灯如星互映）/叠化全片仅一处=机影融进银河/AIGC 开门帧标识/定格收口（80s 惯用件·RESEARCH §三）
# 选角律=CASTING-LAW.md：本曲女主=徐若瑄型（受众预期锚=原版徐若瑄亲演·神似不形似·真照不入管线）——与星晴 XQ_HER 不同块
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "mv0001-handover", "outbound", "krea2",
                                "prompt-writing-spec-v1", "patched-scripts"))
import prompt_lexicon as LX

# ---- 光照块扩展（本曲世界：黄昏天台→城市灯碗→云海月晕→银河→她的天台）----
LX.LIGHT["roof_dusk"] = ("blue-hour dusk at 8000K over a 2000 Taipei rooftop, sodium haze rising from the streets, a water tower standing black against the sky glow")
LX.LIGHT["city_bowl"] = ("the night city bowl of Taipei seen from high above, warm sodium scatter across ink-blue darkness, shop signs and apartment windows a slow drift of small lights")
LX.LIGHT["cloud_moon"] = ("silver-blue moonlight at 4400K over an endless cloud deck, the cloud tops carrying a faint warm rim from the city glow far below, the moon ringed by a soft halo")
LX.LIGHT["galaxy_gold"] = ("a broad band of warm gold star dust arched across an ink-blue night sky, fine stars seeded through the dark, the grain of the night air thick and soft")
LX.LIGHT["warm_window"] = ("one small rooftop window lit warm at 2800K in the blue darkness, its light laying a short amber path across the roof ledge")
LX.LIGHT["streak"] = ("dusk sky ambience with a faint warm shimmer trailing behind a small paper plane, the city lights below catching the paper")

STYLE_LEAD = "as a film still from a 2000 Taiwanese music video"

# ---- 人物正典块 ----
HIM = (LX.ID_M_2001_BONE + ", in a plain grey cotton t-shirt and dark straight trousers")
# 可爱女人女主=徐若瑄型（词表年代女星型块·受众预期锚=原版亲演·全片远景/剪影/灯窗呈现）
KN_HER = (LX.ID_F_VVR + ", in a simple light cotton sundress")
PLANE = ("a plain white paper plane folded from a single sheet of notebook paper, its creases crisp, "
         "one wing slightly buckled from an earlier flight")
HER_PLANE = "a small paper plane folded from cream paper with one wing tip dipped in red"

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
    # ---- 前奏 0-30.14（天台叠机→掷出）----
    ("KN01", 0.00, 6.50, 0.90, "他叠机（手部特写）",
     kf("cu", "high", "hands folding %s on a rooftop ledge, the creases pressed flat one by one, the dusk city soft below" % PLANE, "roof_dusk", lens="50"),
     i2v("A close-up from a high angle", CM["macroslide"] if "macroslide" in LX.CAM_MOVE else CM["static"],
         "Hands folding a white paper plane on a rooftop ledge at dusk, each crease pressed flat in turn, the paper catching the last light")),
    ("KN02", 6.50, 13.00, 0.95, "天台全景（水塔/晾衣绳·城在脚下）",
     kf("med", "eye", "%s standing on a 2000 Taipei rooftop among strung clotheslines and a black water tower, the dusk city soft below the parapet" % HIM, "roof_dusk", lens="35"),
     i2v("A medium shot at eye level", CM["static"], "A young man in a grey t-shirt standing on a Taipei rooftop at dusk among strung clotheslines and a water tower, the whole city bowl dim and warm below the parapet")),
    ("KN03", 13.00, 22.00, 1.00, "他持机立于边缘（城为底）",
     kf("cu", "eye", "%s at the parapet edge holding %s back by its tail, his eyes on the sky above the city, the wind in his fringe" % (HIM, PLANE), "roof_dusk", lens="50"),
     i2v("A close-up at eye level", CM["pushin"], "A young man at a rooftop parapet holding a white paper plane back by its tail, the dusk city far below, his fringe moved by the rising wind")),
    ("KN04", 22.00, 30.14, 1.20, "掷出（burst 快）",
     kf("cu", "eye", "the throw: %s just released from a follow-through hand, the rooftop ledge and water tower streaking past below" % PLANE, "roof_dusk", lens="50"),
     i2v("A close-up at eye level", CM["track"], "A white paper plane flashing up off a rooftop into the dusk sky, the hand still open in its follow-through, the water tower sliding past below")),

    # ---- 主歌 30.14-55.66（直升机/升空/她的灯窗/让我碰到你）----
    ("KN05", 30.14, 37.22, 1.05, "想要有直升机=纸机与夜航直升机同框",
     kf("med", "eye", "%s gliding high over the city lights with a night helicopter holding far off in the same frame, its searchlight a soft cone" % PLANE, "city_bowl", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "A white paper plane gliding above a night city while a helicopter holds far off in the same sky, its running lights blinking slow, the paper banking gently")),
    ("KN06", 37.22, 43.64, 1.00, "掠过屋顶升空（蓝渐深）",
     kf("med", "eye", "%s rising past the last rooftops of the city edge into deepening blue air, the streets falling away beneath it" % PLANE, "roof_dusk", lens="50"),
     i2v("A medium shot at eye level", CM["tiltup"], "A paper plane climbing past dark rooftops into deep blue air, the camera easing up with it as the street lights sink below the frame")),
    ("KN07", 43.64, 50.48, 0.95, "每天每天想着你=返程俯瞰城（她的天台亮一盏灯）",
     kf("ext", "high", "%s small and high above the whole city bowl, and far below one single rooftop window warm-lit among the sodium scatter" % PLANE, "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot from a high angle", CM["static"], "A paper plane tiny above the whole night city bowl, and far below one single rooftop window burning warm among the scatter of sodium lights")),
    ("KN08", 50.48, 55.66, 0.90, "她的灯窗（让我碰到你·许愿锚）",
     kf("cu", "eye", "a rooftop window lit warm with a slim girl silhouette pausing inside the light, a red-tipped paper plane resting on the ledge outside", "warm_window", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A warm rooftop window with a slim girl silhouette pausing inside the light, a red-tipped paper plane resting on the ledge, the window breathing softly as the figure stands still")),

    # ---- 副歌1 56.94-85.82（他仰脸+四种飞姿·卡「可爱女人」拍点）----
    ("KN09", 56.94, 60.76, 0.85, "漂亮得让我面红=他天台仰脸",
     kf("hs", "eye", "%s on the rooftop with his face tipped up to the first stars, the dusk leaving a warm flush on his cheeks, the plane gone from his hand" % HIM, "roof_dusk", lens="85"),
     i2v("A head-and-shoulders framing at eye level", CM["pushin"], "A young man on a night rooftop with his face tipped up to the first stars, a warm flush on his cheeks, his eyes following something high above")),
    ("KN10", 60.76, 64.30, 1.10, "飞姿1=宽弧回旋",
     kf("med", "eye", "%s carving a wide slow arc over the city lights, its wings catching a streetlamp flare" % PLANE, "city_bowl", lens="35", tex="film_night"),
     i2v("A medium shot at eye level", CM["panr"], "A paper plane carving a wide slow arc above night city lights, its white wings flashing as they cross a streetlamp flare, the skyline wheeling past")),
    ("KN11", 64.30, 67.98, 1.00, "飞姿2=迎面直飞（翼尖弹）",
     kf("cu", "eye", "%s nose-on to the camera, its wings flexing once as it climbs, the city lights soft circles behind" % PLANE, "city_bowl", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A paper plane flying nose-on toward the camera, its wings flexing once as it climbs, the night city reduced to soft circles of light behind it")),
    ("KN12", 67.98, 73.26, 1.15, "飞姿3=穿过两楼灯阵之间",
     kf("med", "eye", "%s threading between two apartment towers whose windows are strung with warm lights, the gaps closing around its path" % PLANE, "city_bowl", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "A paper plane threading between two lit apartment towers, warm windows sliding past on both sides close to its wingtips, the gap opening again beyond")),
    ("KN13", 73.26, 78.50, 0.95, "飞姿4=全城灯碗上的小点",
     kf("ext", "eye", "%s a single pale point high above the whole lit bowl of the city, the streets a warm drift far below" % PLANE, "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot at eye level", CM["static"], "A paper plane a single pale point high over the whole lit bowl of a night city, the streets a slow warm drift far below, the sky holding it still")),
    ("KN14", 78.50, 85.82, 1.00, "收拍=暖微光尾迹",
     kf("cu", "eye", "%s trailing a faint warm shimmer through the dark, its paper edge lit from the city below" % PLANE, "streak", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["track"], "A paper plane trailing a faint warm shimmer through the night, its white edge lit softly from the city below as it holds a steady line")),

    # ---- Bridge 89.36-141.34（穿云/月晕/银河全景/融化=主呼吸段）----
    ("KN15", 89.36, 99.00, 0.88, "穿云（雾流过翼）",
     kf("med", "eye", "%s punching up through a moving cloud layer, thin mist streaming off its wings, the grey breaking into blue above" % PLANE, "cloud_moon", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["tiltup"], "A paper plane punching up through a moving cloud layer, thin mist streaming off its wings, the grey breaking into blue as it breaks through")),
    ("KN16", 99.00, 109.00, 0.84, "云海月晕（极缓长镜）",
     kf("wide", "eye", "an endless moonlit cloud deck under a haloed moon, %s small above the white sea, the city gone far below" % PLANE, "cloud_moon", lens="35", tex="film_night"),
     i2v("A wide shot at eye level", CM["pullout"], "An endless cloud deck under a haloed moon, a small paper plane holding still above the white sea, the camera easing back until the moon halo fills the sky")),
    ("KN17", 109.00, 117.46, 0.82, "银河全景（主呼吸镜1·星尘缓旋）",
     kf("ext", "eye", "the whole arc of a warm gold star band across the ink-blue night, the cloud deck a dark rim below, star dust thick along the middle of the sky", "galaxy_gold", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot at eye level", CM["pushin"], "The whole arc of a warm gold star band arched across an ink-blue night, the star dust wheeling almost imperceptibly, the cloud deck a dark rim below the frame")),
    ("KN18", 117.46, 126.52, 0.86, "银河近景（主呼吸镜2）",
     kf("cu", "eye", "the star dust itself close: countless fine warm points and pale currents drifting through deep blue-black, the grain of the night soft and thick", "galaxy_gold", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["macroslide"] if "macroslide" in LX.CAM_MOVE else CM["static"], "The star dust of the galaxy band in close detail, fine warm points and pale currents drifting through deep blue-black, everything moving at the slowest breath")),
    ("KN19", 126.52, 134.26, 0.88, "纸机漂进星流（纸面染金）",
     kf("med", "eye", "%s drifting into the gold star stream, its white paper warming gold at the edges, the stars thickening around it" % PLANE, "galaxy_gold", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["track"], "A paper plane drifting up into a stream of warm gold stars, its white paper warming to gold at the edges as the star field thickens around it")),
    ("KN20", 134.26, 141.34, 0.90, "融化在银河里（叠化源帧）",
     kf("cu", "eye", "%s dissolving softly into the star stream, its silhouette thinning into light, the fold lines of the paper becoming threads of star dust" % PLANE, "galaxy_gold", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A paper plane dissolving softly into a stream of warm gold stars, its silhouette thinning into light until only the fold lines remain as threads of star dust")),

    # ---- 间奏 141.34-171.34（她在城市另一头）----
    ("KN21", 141.34, 155.00, 0.90, "她的天台·红尾纸机停在檐上",
     kf("cu", "eye", "%s resting on a rooftop ledge beside a warm-lit window, the red wing tip turned toward the light" % HER_PLANE, "warm_window", lens="50", tex="film_night"),
     i2v("A close-up at eye level", CM["pushin"], "A cream paper plane with a red wing tip resting on a rooftop ledge beside a warm-lit window, the red tip catching the light as the window breathes")),
    ("KN22", 155.00, 171.34, 0.95, "两天台隔城相望（双线交叉锚帧）",
     kf("ext", "high", "two rooftops facing each other across the night city bowl, one small warm light on each, the streets a soft warm drift between them", "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot from a high angle", CM["static"], "Two rooftops facing each other across a night city bowl, a single warm light on each roof, the streets a soft drift between them holding both still")),

    # ---- 慢段 171.34-183.28（小小的爱=一俯一仰）----
    ("KN23", 171.34, 174.46, 0.85, "他的天台（俯望城）",
     kf("wide", "high", "%s sitting on the rooftop edge with his elbows on his knees, looking across the whole night city, the water tower behind him" % HIM, "city_bowl", lens="35", tex="film_night"),
     i2v("A wide shot from a high angle", CM["cranedn"], "A young man sitting on a rooftop edge above the night city, elbows on knees, the whole bowl of lights below him, the camera easing down behind his stillness")),
    ("KN24", 174.46, 177.88, 0.85, "她的天台（仰·灯下细影）",
     kf("wide", "eye", "a far rooftop where a slim girl stands in the warm window light, %s held to her chest, her face turned up to the stars" % HER_PLANE, "warm_window", lens="85", tex="film_night"),
     i2v("A wide shot at eye level", CM["static"], "A slim girl standing in the warm light of a far rooftop window holding a red-tipped paper plane to her chest, her face turned up to the stars")),
    ("KN25", 177.88, 183.28, 1.00, "两灯之间的城（全力包含你）",
     kf("ext", "eye", "the whole night city between the two rooftops, two faint warm lights aligned across the frame, the streets carrying the drift of sodium", "city_bowl", lens="24", tex="film_night"),
     i2v("An extreme wide establishing shot at eye level", CM["static"], "A night city seen between two far warm lights aligned across the frame, the streets drifting below, the two lights holding their distance")),

    # ---- 副歌2 184.60-218.18（重演律：四种飞姿回归=REUSE·见 REUSE 表；新镜=他夜脸）----
    ("KN26", 184.60, 188.28, 0.87, "他夜脸（副歌2 起拍）",
     kf("hs", "eye", "%s on the rooftop in full night now, his face tipped up, the star band faint above the city glow" % HIM, "city_bowl", lens="85", tex="film_night"),
     i2v("A head-and-shoulders framing at eye level", CM["static"], "A young man on a night rooftop with his face tipped up to a faint band of stars above the city glow, his stillness holding the whole sky")),
    # ---- 副歌2 尾+尾奏 218.18-247（呼应/她答/相遇/归返定格）----
    ("KN27", 218.18, 227.28, 1.00, "呼应镜=纸机与直升机高处再同框",
     kf("med", "eye", "%s and the night helicopter sharing the high sky again, both small and steady, the city a faint glow under them" % PLANE, "city_bowl", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["static"], "A paper plane and a distant helicopter sharing the high night sky, both small and steady over the faint city glow, their lights keeping their distance")),
    ("KN28", 227.28, 236.30, 1.02, "她的红尾机从她的天台升空（她的回答）",
     kf("med", "eye", "%s lifting off from her rooftop window light, the warm square falling away below it as it climbs" % HER_PLANE, "warm_window", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["tiltup"], "A cream paper plane with a red wing tip lifting off from a warm rooftop window, the square of light falling away below it as it climbs into the night")),
    ("KN29", 236.30, 240.50, 0.95, "让我碰到你=双机航线交错而过（定格源）",
     kf("cu", "eye", "the white plane and the red-tipped plane crossing paths high above the city, their wingtips a hand-span apart, the streets far below", "city_bowl", lens="85", tex="film_night"),
     i2v("A close-up at eye level", CM["static"], "A white paper plane and a red-tipped paper plane crossing paths high above a night city, their wingtips a hand-span apart, both holding their line as they pass")),
    ("KN30", 240.50, 247.00, 0.96, "她的机落回他的天台·双机并排定格（定格收口）",
     kf("med", "eye", "%s settling onto the rooftop ledge beside %s, two planes side by side in the window light, the city dim beyond" % (HER_PLANE, PLANE), "warm_window", lens="50", tex="film_night"),
     i2v("A medium shot at eye level", CM["pushin"], "A red-tipped paper plane settling onto a rooftop ledge beside a white one, the two planes coming to rest side by side in the warm window light, everything settling to stillness")),
]

# ---- 重演律复用（副歌2 四种飞姿回归·已产素材重挂）----
REUSE = [
    ("KN10", 188.28, 195.60, 1.05, "飞姿1 回归（更亮夜空）"),
    ("KN11", 195.60, 202.48, 1.02, "飞姿2 回归"),
    ("KN12", 202.48, 209.70, 1.10, "飞姿3 回归（更紧）"),
    ("KN13", 209.70, 218.18, 0.95, "飞姿4 回归"),
]

# ---- 女主选角案（CASTING-LAW 必携件）----
CASTING_KN = {
    "track": "可爱女人（mv-jay-02·P1 主打曲）",
    "audience": "原版受众预期=徐若瑄亲演（A 级底座锚）——徐若瑄型年代脸型族（甜/空气感/长直发铁刘海）；受众洞察卡 RESEARCH-可爱女人-受众洞察-v1.md 喂入后校正",
    "default_A": "KN_HER=词表 ID_F_VVR 块（徐若瑄型·2001 年代质感·神似不形似·真照不入管线）",
    "candidates": [
        "A=徐若瑄型（默认·词表 ID_F_VVR 块·甜系空气感）",
        "B=甜系苹果肌（词表 ID_F_JOLIN 块·备选）",
        "C=新铸「空气感初恋系」块（待受众卡校正后铸）",
    ],
    "law_notes": "每曲独立面孔（与星晴 XQ_HER 不同块·禁跨曲复用）；全片她=远景/剪影/灯窗呈现（禁看镜头·距离语言）；落定后 ID 块逐字复用",
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
    md = ("# 《可爱女人》分镜表 v2（帧级·深研喂入）\n\n"
          "> 权威=可爱女人-剧本-v1.md（投掷-归返弧）+RESEARCH-mv-craft §一/三/六；词级锚点=anchors/可爱女人.txt（词行至 236.30·尾窗延至 247 定格收）\n"
          "> 长期律：逐镜变速（掷 1.2 burst/穿云 0.84-0.9 极缓）/5246 黄昏段 5279 夜段/台式奶黑/她=远景剪影灯窗/叠化仅机影融银河一处/定格收口/AIGC 标识\n"
          "> 状态机读正身=本 py 文件（md=衍生物）；KF 批挂 bm-c（空镜+物件帧先行）·i2v 云端波待 CEO 过目 LOOKBOARD\n\n"
          "## 女主选角案（CASTING-LAW 必携件）\n\n- 受众：%s\n- 默认候选：%s\n- 候选池：%s\n- 法条：%s\n\n## 镜头表（%d 新镜）\n\n%s\n"
          % (CASTING_KN["audience"], CASTING_KN["default_A"],
             "；".join(CASTING_KN["candidates"]), CASTING_KN["law_notes"], len(NEW), _md()))
    out = os.path.join(_HERE, "可爱女人-SHOTLIST-v2.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("md written:", out)
