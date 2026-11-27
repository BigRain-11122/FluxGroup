# -*- coding: utf-8 -*-
"""黑色幽默 D2 v2.0 生成器（合规版）：按 CEO 律生成分镜表 + KF 提示词，并自检预算。

硬约束（来自 MV-CEO-REQUIREMENTS-v1.md）：
  主歌 2-3s/镜 · 副歌踩点 ~2s/镜 · 前奏留长 · 尾慢收
  空镜 ≤20% · 主体 ≥50% · 人脸近特 ≥25%
  WARDROBE：2000 台式明星衣橱（禁素T路人感）
  表演：写动作不写情绪
"""
import json
import os

ROOT = r'K:\Fluxgroup\FluxGroup'
BASE = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay')
MD = os.path.join(BASE, '黑色幽默-D2-SHOTLIST-v2.md')
PROMPTS = os.path.join(BASE, 'plan', 'hei-kf-prompts-v2.json')

# ---- WARDROBE（WARDROBE-LAW 2000 台式·反韩化）----
LOOK_A = ("a washed indigo denim jacket over a white graphic tee, loose straight charcoal trousers, "
          "a thin silver chain at the collar, a braided leather bracelet on the wrist")
MAN = "an unnamed young Taiwanese man around 25, short black hair, %s" % LOOK_A

STYLE = ("as a film still from a 2000 Taiwanese music video, 35mm film grain, low-key interior lighting, "
         "cold blue-black shadow with a single warm tungsten desk lamp at 2200K as the only warm source, "
         "rain-streaked window with distant neon as the only colour, restrained practical bloom, "
         "black lifted slightly with the toe intact, clean unlettered surfaces")

# ---- 段与镜长（CEO 10-19 节奏律）----
# (段名, t0, t1, 镜数, 类型池)  类型: F=人脸近特 P=人物主体(med/hs) E=空镜
PLAN = [
    ("前奏", 0.0, 17.2, 3, "E"),
    ("主歌1", 17.2, 41.9, 10, "FPPEPFPPEP"),
    ("主歌2", 44.7, 73.5, 11, "PFEPPFEPPFE"),
    ("副歌1", 75.9, 101.8, 13, "FPFPEFPFPFEPF"),
    ("副歌2", 107.9, 130.0, 11, "PFPFPEFPFPF"),
    ("间奏", 130.0, 164.9, 7, "EEPFEPE"),
    ("主歌3", 164.9, 180.9, 6, "PFEPPF"),
    ("副歌3", 184.2, 207.1, 11, "FPFPFPEFPFP"),
    ("副歌4", 213.2, 237.2, 12, "PFPFPFPEFPFP"),
    ("尾", 255.7, 283.13, 5, "EPEEP"),
]

# 人物面内容池（写动作·不写情绪）
FACE_CONTENT = [
    "his eyes lifting from the keys to the rain window, the jaw staying set",
    "one slow blink while his throat moves once, swallowing",
    "his gaze dropping to his own hand on the keys, holding there",
    "his head turning a few degrees toward the empty chair, then stopping",
    "a breath leaving through the nose, the shoulders settling a fraction",
    "his eyes closing for two seconds, the mouth staying closed",
]
BODY_CONTENT = [
    "he sits on the piano bench and starts a phrase, then stops with the hand still on the key",
    "he stands and walks two steps to the window, one hand resting on the frame",
    "he sets the cassette recorder down and presses rewind, watching the reels turn",
    "he leans against the piano with both hands behind him on the lid",
    "he turns the desk lamp a few degrees so the light moves across the keys",
    "he picks up a photograph face down and sets it back the same way",
    "he sits back down, aligning the bench with his knee before sitting",
]
EMPTY_CONTENT = [
    "the empty piano bench, dust turning slowly in the lamp light",
    "the rain running down the glass, a neon sign breathing behind it",
    "the stopped clock on the wall, its hands frozen",
    "a peeled edge of wallpaper lifting away from the wall",
    "the cassette tape reels turning inside the dark recorder",
    "the lamp cord and its shadow across the wooden floor",
    "the room with one fewer object than before, same camera position",
]

SHOT_MAP = {"F": ("cu", "eye"), "P": ("med", "eye"), "E": ("wide", "eye")}
MOVE_CYCLE = ["static", "pushin", "static", "pullout", "static", "pan"]


def build():
    rows = []
    idx = 0
    for seg, t0, t1, n, kinds in PLAN:
        span = (t1 - t0) / float(n)
        for k in range(n):
            kind = kinds[k % len(kinds)]
            idx += 1
            sid = "H%03d" % idx
            shot, angle = SHOT_MAP[kind]
            if kind == "F":
                detail = "close-up of %s, %s" % (MAN, FACE_CONTENT[idx % len(FACE_CONTENT)])
            elif kind == "P":
                detail = "medium shot of %s as %s" % (MAN, BODY_CONTENT[idx % len(BODY_CONTENT)])
            else:
                detail = EMPTY_CONTENT[idx % len(EMPTY_CONTENT)]
            prompt = "A %s: %s. %s." % (
                {"cu": "close-up", "med": "medium shot", "wide": "wide shot"}[shot], detail, STYLE)
            rows.append({
                "id": sid, "seg": seg, "t0": round(t0 + k * span, 2), "t1": round(t0 + (k + 1) * span, 2),
                "dur": round(span, 2), "kind": kind, "shot": shot, "angle": angle,
                "move": MOVE_CYCLE[idx % len(MOVE_CYCLE)],
                "scene": "piano_room", "light": "night", "grade": "tw2001", "texture": "film_night",
                "prompt": prompt, "seed": 20261122 + idx,
            })
    return rows


def budget(rows):
    n = float(len(rows))
    e = sum(1 for r in rows if r["kind"] == "E")
    f = sum(1 for r in rows if r["kind"] == "F")
    p = sum(1 for r in rows if r["kind"] == "P")
    return {"n": len(rows), "empty_pct": round(e / n * 100, 1), "face_pct": round(f / n * 100, 1),
            "body_pct": round(p / n * 100, 1)}


def rebalance(rows):
    """按预算确定性校正镜型：空镜超→改主体；主体不足→近特改主体。

    只改"这一类镜头怎么拍"，不改时间轴（窗长/时长严格守恒）。
    """
    n = len(rows)
    def cnt(k):
        return sum(1 for r in rows if r["kind"] == k)

    # 空镜压到 ≤18%
    i = 0
    while cnt("E") > int(n * 0.18) and i < n:
        if rows[i]["kind"] == "E":
            rows[i]["kind"] = "P"
        i += 1
    # 主体补到 ≥52%（近特富余时）
    i = 0
    while cnt("P") < int(n * 0.52) and i < n:
        if rows[i]["kind"] == "F" and cnt("F") > int(n * 0.27):
            rows[i]["kind"] = "P"
        i += 1
    # 回填镜头语汇（类型变了要同步景别/内容）
    for j, r in enumerate(rows):
        k = r["kind"]
        shot, angle = SHOT_MAP[k]
        r["shot"], r["angle"] = shot, angle
        if k == "F":
            detail = "close-up of %s, %s" % (MAN, FACE_CONTENT[j % len(FACE_CONTENT)])
        elif k == "P":
            detail = "medium shot of %s as %s" % (MAN, BODY_CONTENT[j % len(BODY_CONTENT)])
        else:
            detail = EMPTY_CONTENT[j % len(EMPTY_CONTENT)]
        r["prompt"] = "A %s: %s. %s." % (
            {"cu": "close-up", "med": "medium shot", "wide": "wide shot"}[shot], detail, STYLE)
    return rows


def main():
    rows = rebalance(build())
    b = budget(rows)
    print("shots=%d  empty=%.1f%% (≤20)  face=%.1f%% (≥25)  body=%.1f%% (≥50)" % (
        b["n"], b["empty_pct"], b["face_pct"], b["body_pct"]))
    ok = b["empty_pct"] <= 20 and b["face_pct"] >= 25 and b["body_pct"] >= 50
    print("BUDGET", "PASS" if ok else "FAIL")

    json.dump(rows, open(PROMPTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print("prompts ->", PROMPTS)

    # 分镜表 md
    lines = ["# 《黑色幽默》分镜表 v2.0（合规版·283.13s·%d 镜）" % b["n"], "",
             "> 依据 `MV-CEO-REQUIREMENTS-v1.md`；v1 因空镜 62%/镜长 11.8s/服装素T 被判不合规（见 AUDIT 件）。",
             "> 人物面预算：主体 %.1f%%（≥50）· 人脸近特 %.1f%%（≥25）· 空镜 %.1f%%（≤20）" % (
                 b["body_pct"], b["face_pct"], b["empty_pct"]), "",
             "## 七轴指纹卡（GRADE-LAW §四·覆写 7/7 轴）", "",
             "| 轴 | 本曲取值 | 与专辑底差异 |", "|---|---|---|",
             "| 叙事结构 | 单场景实时独白 | 多数曲多场景/闪回 → 覆写 |",
             "| 影像质感 | 冷蓝黑剧场感·单一实光源 | 覆写 |",
             "| 色彩体系 | 蓝黑 + 唯一暖点 2200K 台灯 | 覆写（星晴金蓝/可爱女人银蓝） |",
             "| 运镜 | 固定为主 + 副歌微推 | 覆写 |",
             "| 剪辑 | 主歌 2.5s / 副歌 2.0s 踩点 | 覆写 |",
             "| 表演 | 内收·几乎不落泪 | 覆写 |",
             "| 场景世界 | 雨夜室内（全专唯一纯内景） | 覆写 |", "",
             "## 造型案（WARDROBE-LAW）", "",
             "男主 = 水洗靛蓝牛仔外套 + 白色图案 T + 宽松炭灰直筒裤 + 细银链 + 皮绳手环（2000 台式正身·反韩化）。",
             "女主 = **零出镜**（只以空椅/反面照片存在）——零出镜设计案：受众预期由「原版钢琴房独角戏记忆」承载，不引入新面孔。", "",
             "## 镜头表", "", "| 镜 | 段 | 窗口(s) | 长 | 类型 | 景别 | 内容 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %.1f–%.1f | %.1fs | %s | %s | %s |" % (
            r["id"], r["seg"], r["t0"], r["t1"], r["dur"],
            {"F": "人脸近特", "P": "主体", "E": "空镜"}[r["kind"]], r["shot"],
            r["prompt"].split(". ")[0][:56]))
    open(MD, 'w', encoding='utf-8').write("\n".join(lines) + "\n")
    print("shotlist ->", MD)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
