# -*- coding: utf-8 -*-
# cloud_dispatch_v4.py (准备件·由会话内 file_upload+generate_video 执行·本文件=提示词正典)
# 云端 MiniMax-H3 i2v 运镜三维提示词（与 30s-立意案-v4-定稿 镜头表逐条对位）
# 全部正向措辞·单镜单运镜·lint 三名单已过

STYLE_TAIL = ("Warm amber monochrome grade with deep crushed shadows, visible 35mm film grain. "
              "Restrained continuous motion, camera and subject motion only.")

CLOUD_PROMPTS = {
    # S1 4.0s 静态·火苗呼吸唤醒刻痕
    "KF1_fire_wake": ("Single continuous take at 24fps, 16:9. An extreme close-up at eye level; "
        "the camera holds a perfectly static shot. A torch flame edge brushes across polished black "
        "basalt inscribed with stacked bands of carved cuneiform wedges; the flame breathes gently, "
        "fine dust drifting through the amber glow, each carved band catching firelight in turn, "
        "soft halation blooming around the flame core. ") + STYLE_TAIL,
    # S2 4.0s 横移·火把侧逆光扫碑面
    "KF2_sweep": ("Single continuous take at 24fps, 16:9. A close-up at eye level; the camera tracks "
        "laterally with small amplitude at slow speed. The carved face of a black basalt stele passes "
        "across frame, a torch held low at the frame edge throwing raking amber side-light, each carved "
        "band of cuneiform surfacing into light and drowning back into blackness as the light moves. ") + STYLE_TAIL,
    # S3 3.5s 推近·石碑全貌权威
    "KF3_stele": ("Single continuous take at 24fps, 16:9. A medium shot from a low angle; the camera "
        "pushes in with medium amplitude at slow speed. A tall polished black basalt stele standing "
        "upright in a vast Babylonian hall, carved relief at its crown above stacked bands of cuneiform, "
        "wall torches burning amber in pools around it, mud-brick columns dissolving into darkness; "
        "the stele grows larger in frame with quiet authority, torch flames flickering. ") + STYLE_TAIL,
    # S4 2.1s 静态·碑顶浮雕二神·火光爬行
    "KF4_crown": ("Single continuous take at 24fps, 16:9. A close-up from a low angle; the camera holds "
        "a perfectly static shot. The carved crown relief of a black basalt stele: a standing bearded "
        "king raising his hand before a seated god extending a rod and ring; amber firelight crawls "
        "slowly across the two carved figures, their forms surfacing from the black stone, soft halation "
        "around the torch glow. ") + STYLE_TAIL,
    # S5 3.6s 下摇·法典铭文带层逐层读
    "KF5_columns": ("Single continuous take at 24fps, 16:9. A close-up at eye level; the camera tilts "
        "down with medium amplitude at moderate speed. Stacked horizontal bands of carved cuneiform "
        "wedge marks fill the black basalt face edge to edge; the view slides steadily down band after "
        "band of the carved code, amber firelight pooling in the deep-cut grooves, fine dust drifting "
        "through the torchlight. ") + STYLE_TAIL,
    # S6 2.2s 锁定·铜凿咬石（动作在前段）
    "KF6_chisel": ("Single continuous take at 24fps, 16:9. An extreme close-up at eye level; the camera "
        "holds locked-off and still. A weathered hand in a rough undyed linen sleeve drives a bronze "
        "chisel into polished black basalt; the chisel bites and strikes early in the take, fresh wedge "
        "marks forming under the tip, fine black stone chips lifting from the cut, firelight raking "
        "across the struck surface, the flame flickering at frame edge. ") + STYLE_TAIL,
    # S7 2.3s 拉远+升·时间吞没
    "KF7_hall": ("Single continuous take at 24fps, 16:9. An extreme wide shot at eye level; the camera "
        "pulls out and cranes up with steady amplitude at moderate speed. The black basalt stele stands "
        "small at the center of a vast Babylonian hall of mud-brick columns, torch pools on the floor, "
        "a single hard light shaft above full of drifting dust; as the camera rises and retreats the "
        "stele shrinks and darkness swallows the space around it. ") + STYLE_TAIL,
    # T 1.0s 金字显形上升（叠化转场件）
    "KFT_glyphs": ("Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera holds "
        "a perfectly static shot. Carved cuneiform wedge marks lift gently off a pure black background, "
        "becoming luminous deep-gold marks drifting slowly upward through warm haze, soft golden bloom "
        "breathing around each mark. ") + STYLE_TAIL,
    # S8 2.0s 缓推·玻璃柜+她的倒影叠字
    "KF8_case": ("Single continuous take at 24fps, 16:9. A medium shot at eye level; the camera pushes "
        "in with small amplitude at moderate speed. A museum glass display case lit from within by a warm "
        "amber interior light holds a broken slab of black basalt etched with stacked cuneiform bands; the "
        "dark soft-edged silhouette of a young woman with long black center-parted hair is reflected on "
        "the glass, her reflection overlapping the carved words, the warm pool breathing around the stone. ") + STYLE_TAIL,
    # S9 3.0s 静态凝视·她的侧影（镜头=他的注视）
    "KF9_profile": ("Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds "
        "a perfectly static shot. Seen through museum glass: the dark side profile of a young woman "
        "with long black center-parted hair, softly lit by the warm case glow, her lowered gaze resting "
        "on a broken black basalt slab carved with cuneiform bands behind the glass; a strand of her hair "
        "moves almost imperceptibly, the faint amber reflection breathing on the glass surface. ") + STYLE_TAIL,
    # S10 2.3s 拉远·走远灯熄字存
    "KF10_walkaway": ("Single continuous take at 24fps, 16:9. A wide shot at eye level; the camera pulls "
        "out slowly with small amplitude. A young woman with long black center-parted hair walks away "
        "down a dark museum aisle toward the exit, her back to the camera as a dark silhouette; warm case "
        "lights dim one by one behind her, the last amber pool clinging to a broken black stone slab, its "
        "carved bands still holding the light as the darkness rises. ") + STYLE_TAIL,
}

# 目标时长（剪辑裁切·生成统一 5s）
TRIM = {
    "KF1_fire_wake": 4.0, "KF2_sweep": 4.0, "KF3_stele": 3.5, "KF4_crown": 2.1,
    "KF5_columns": 3.6, "KF6_chisel": 2.2, "KF7_hall": 2.3, "KFT_glyphs": 1.0,
    "KF8_case": 2.0, "KF9_profile": 3.0, "KF10_walkaway": 2.3,
}

if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\prompt-writing-spec-v1\patched-scripts")
    import prompt_lexicon as LX
    ok = True
    for k, v in CLOUD_PROMPTS.items():
        hits = LX.lint(v, mode="video")
        print(("PASS" if not hits else "FAIL"), k, hits if hits else "")
        ok = ok and not hits
    print("ALL OK" if ok else "HAS FAILURES")
