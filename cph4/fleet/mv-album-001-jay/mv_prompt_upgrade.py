# -*- coding: utf-8 -*-
"""mv_prompt_upgrade.py — MV 提示词升级器（2026-10-20）

把本周调研结论落成可调用件，不覆盖旧词库：
  1. LIGHT7  七槽光句（源→尺寸→距离→方向→质感→光比→K），补上旧五槽缺的尺寸/距离
  2. FOCUS   景深/焦点术语（旧词库缺整层）
  3. PERF    表演微动作（配合 mv-performance：意图+时序）
  4. h3_i2v  H3 方括号相机命令 + 单主动作（官方唯一有语法保证的运镜通道）
  5. lint_density  术语密度/反例词机检
"""
# ---------- 1. 七槽光句（W2 可爱女人的光锚） ----------
LIGHT7 = {
    "roof_dusk": "one open sky source, no fixture: blue-hour daylight at 8000K falling from a wide 180-degree sky "
                 "behind and above him, the near side of his face two stops under; sodium haze from the street below "
                 "2400K rimming the parapet; soft, low contrast, ratio about 2:1",
    "roof_night": "two sources only: the city glow rising from below the parapet (a broad 2000-2400K sodium wash, "
                  "bounce-level, no fixture) and a small 2800K window behind him at frame left; his face lit only by "
                  "the rising bounce, harsh-cut shadow under the jaw, ratio about 4:1",
    "city_bowl": "no fixtures: a whole city of sodium and incandescent points at 2200-2900K scattered below, the sky "
                 "above falling to ink blue; light comes from every direction at once, lowest contrast, ratio about 3:1",
    "city_moon": "one moon source, a 4400K silver-blue haze from above and behind the city, the street lights cool "
                 "and fine below, the paper's top surface catching the moon while its underside stays dark; ratio 8:1",
    "cloud_moon": "one moon source at 4400K from high rear-left, cloud tops carrying a pale silver edge and the troughs "
                  "falling two stops under; no other fixture; very soft, ratio 3:1",
    "galaxy_gold": "no fixture: a broad gold star-dust band arching overhead, its light diffuse and warm 3000K, the "
                   "ground falling to near black; ratio 16:1",
    "warm_window": "one practical only: a single 40cm paper-shaded bulb behind the window glass at 2800K, two metres "
                   "from her, its pool laying across the sill and falling off hard within a metre; the room beyond "
                   "two stops under; ratio 4:1",
    "streak": "one faint moving source: a warm 2800K shimmer trailing the paper plane, no fixture, the rest of the "
              "frame at bounce level; ratio 6:1",
}

# ---------- 2. 景深与焦点 ----------
FOCUS = {
    "shallow": "shallow depth of field, the background falling into soft bokeh",
    "deep": "deep focus, both the near hands and the far wall resolved",
    "rack": "the sharpest point passing from {a} to {b}",
    "fore": "an out-of-focus foreground element at frame left",
    "breath": "focus breathing slightly as he leans in",
    "split": "split diopter, the near hand and the far window both sharp",
}

# ---------- 3. 表演微动作 ----------
PERF = {
    "hold_blink": "eyelid held shut for eight frames, then released",
    "eyes_first": "eyes reach the target two frames before the head turns",
    "swallow": "one slow swallow, throat moving once",
    "breath_held": "breath held, ribs still, released after the sound",
    "finger_hover": "fingertip hovering a breath above the surface without touching",
    "weight_forward": "weight pressing forward onto the front of the foot, heels staying planted",
    "shoulders_settle": "shoulders dropping before they release",
    "fingers_open": "fingers staying open after the release",
    "mid_expression": "caught mid-expression, the smile not yet reaching the mouth",
    "asymmetry": "one brow a breath higher than the other",
    "settle_back": "then easing back to stillness",
    "hands_busy": "his hands keep working while his face does not change",
}

# ---------- 4. H3 方括号运镜 ----------
H3_CAM = {
    "push": "[Push in]", "pull": "[Pull out]", "pan_l": "[Pan left]", "pan_r": "[Pan right]",
    "tilt_u": "[Tilt up]", "tilt_d": "[Tilt down]", "truck_l": "[Truck left]", "truck_r": "[Truck right]",
    "ped_u": "[Pedestal up]", "ped_d": "[Pedestal down]", "track": "[Tracking shot]",
    "shake": "[Shake]", "static": "[Static shot]",
}


def h3_i2v(size_angle, cam_actions, content, keep, tail=None):
    """H3 单镜：单主动作 + 方括号相机命令（可串联两段：先动后静）。"""
    cam = ", ".join(H3_CAM[c] for c in cam_actions)
    body = f"{size_angle}, {cam}. {content}"
    tail = tail or ("Every motion eases in and settles out, in the quiet camera language of a "
                    "2000 Taiwanese music video. Preserve film grain and the original color palette.")
    return f"{body} {keep} {tail}"


# ---------- 5. 术语密度闸 ----------
POSITIVE_TERMS = set(LIGHT7) | set(FOCUS) | set(PERF) | {
    "extreme close-up", "close-up", "medium shot", "wide shot", "establishing shot",
    "eye-level", "low angle", "high angle", "over-the-shoulder",
    "rack focus", "shallow depth of field", "deep focus",
    "key light", "rim light", "practical", "halation", "falloff", "ratio",
    "35mm", "grain", "telecine", "halation bloom",
}
BANNED = {
    "cinematic", "dramatic", "moody", "epic", "beautiful", "stunning",
    "emotional", "atmospheric", "vibes", "alive", "natural", "realistic feel",
    "high quality", "masterpiece", "8k", "ultra detailed",
}


def lint_density(prompt, shot_kind="face"):
    low = prompt.lower()
    hits = sorted(t for t in POSITIVE_TERMS if t in low)
    bad = sorted(t for t in BANNED if t in low)
    need = {"face": ("perf", "light"), "empty": ("material", "light"), "action": ("chain",)}.get(shot_kind, ())
    problems = []
    if len(hits) < 3:
        problems.append(f"term_density={len(hits)} <3")
    if bad:
        problems.append("banned=" + ",".join(bad))
    return {"terms": len(hits), "hits": hits, "banned": bad, "problems": problems}


if __name__ == "__main__":
    demo = h3_i2v(
        "A close-up at eye level, camera outside the window",
        ["static"],
        "Inside a warm rooftop window she pauses with her hand on the sill; " + PERF["eyes_first"] + "; "
        + PERF["settle_back"] + ".",
        "A red-tipped paper plane rests on the ledge outside. " + LIGHT7["warm_window"] + ".",
    )
    print(demo)
    print(lint_density(demo, "face"))