# -*- coding: utf-8 -*-
"""preflight_gate.py — 烧片前机械闸（见 prompt-writing-spec-v1/PREFLIGHT-GATE-v1.md）

用法：
    import preflight_gate as G
    fails = G.guard(shot_id="S9_profile", prompt_text=P, tokens=CFG, kf_verified=True)
    if fails: raise SystemExit(fails)

任一 fail → 不得提交 ComfyUI。绕过即违规。
"""
import re

NEG_TOKENS = ("no ", "not ", "never ", "without", "avoid", "don't", "doesn't", "won't", "non-")

VALID = {
    "shot": {"ecu", "cu", "hs", "med", "mw", "wide", "ext"},
    "angle": {"eye", "low", "high", "top", "ots", "dutch"},
    "move": {"static", "pushin", "pullout", "pan", "tilt", "track", "handheld"},
    "grade": {"tw2001", "mono", "bluefire", "nost"},
    "texture": {"film_night", "film_day", "mist", "soft"},
}

# 场景词 → 会把该场景带偏的冲突词
SCENE_CONFLICT = {
    "museum": ("torchlit", "torch", "temple", "mud-brick", "babylonian hall", "godray", "fire pit"),
    "hall": ("glass case", "museum aisle", "display case"),
    "classroom": ("torch", "temple", "museum"),
    "rooftop": ("torch", "temple", "museum"),
}

# 黑名单：命中 = 禁止再烧，只能换方案
BLOCKED = {
    ("S9_profile", "reflected_face"): (
        "2026-10-21 实测 4 条 take 全部复现（原 KF×2 / 清洗 KF×2 含去玻璃语义版）；"
        "同构图换种子无效。出路=换镜或换构图。"),
    ("S8_case", "reflected_face"): "观察项：与 S9 同源展柜构图，若 S9 换掉可保留观察。",
}

# 同一镜同一缺陷连烧 2 条仍复现 → 自动 BLOCK 的计数台账
BURN_LEDGER = {}


def check_blocked(shot_id, defect=None):
    fails = []
    for (sid, d), why in BLOCKED.items():
        if sid != shot_id:
            continue
        if defect is None or defect == d:
            fails.append("BLOCKED %s/%s :: %s" % (sid, d, why))
    if shot_id in BURN_LEDGER and BURN_LEDGER[shot_id] >= 2:
        fails.append("BURN-LIMIT %s 已连烧 %d 条，转方案讨论" % (shot_id, BURN_LEDGER[shot_id]))
    return fails


def guard(shot_id, prompt_text, tokens, kf_verified=False, kf_note="", defect=None, kinds=None):
    fails = []
    low = prompt_text.lower()

    # ① 首帧
    if not kf_verified:
        fails.append("①首帧未 sign-off（须放大核过本镜缺陷后才置 True）")
    elif not kf_note.strip():
        fails.append("①首帧 sign-off 缺核验记录（kf_note 不得为空）")

    # ② token
    for k in ("shot", "angle", "move", "grade", "texture"):
        v = tokens.get(k)
        if v not in VALID[k]:
            fails.append("②token 非法 %s=%s 不在 %s" % (k, v, sorted(VALID[k])))
    for k in ("scene", "light"):
        if not tokens.get(k):
            fails.append("②缺 %s" % k)

    # ③ 零否定
    hit = [w for w in NEG_TOKENS if w in low]
    if hit:
        fails.append("③否定句命中 %s（否定词会诱发目标出现）" % hit)

    # ④ 场景锚
    scene = tokens.get("scene", "")
    bad = [w for w in SCENE_CONFLICT.get(scene, ()) if w in low]
    if bad:
        fails.append("④场景锚冲突 scene=%s 却出现 %s" % (scene, bad))

    # ⑤ 正向必备锚（FRAME-GATE-v1 §六）——由调用方用 kinds 显式声明；未声明时不猜
    kinds = set(kinds or [])
    def need(cond, phrase_list, msg):
        if cond and not any(p in low for p in phrase_list):
            fails.append("⑤缺正向锚：" + msg)

    need("inscription" in kinds,
         ("cuneiform", "carved marks", "wedge"), "含刻痕/泥板的镜必须写 cuneiform / carved marks")
    need("glass" in kinds,
         ("the glass carries only", "sheen of the room light", "glass surface shows only"),
         "含玻璃/展柜的镜必须正向限定玻璃上只有光/刻痕")
    need("sing" in kinds, ("lips",), "唱歌镜必须写 lips")
    need("sing" in kinds,
         ("opening and closing", "shaping each word", "shape each word"),
         "唱歌镜必须写口部开合/咬字")
    need("carve" in kinds,
         ("stay fixed", "remains identical", "stays fixed"),
         "刻写镜必须写明刻痕成形后保持稳定")

    # 黑名单
    fails += check_blocked(shot_id, defect)
    return fails


def note_burn(shot_id):
    """每次提交成功后调用一次，累计同一镜的重烧次数。"""
    BURN_LEDGER[shot_id] = BURN_LEDGER.get(shot_id, 0) + 1
    return BURN_LEDGER[shot_id]