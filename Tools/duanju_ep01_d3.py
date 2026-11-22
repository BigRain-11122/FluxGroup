# -*- coding: utf-8 -*-
"""《商路》EP01 分镜表 + KF 提示词生成（AI 真人短剧·仿真人）

硬约束：
  · 竖屏 9:16 · 1080×1920 目标（KF 出 832×1472，装配放大）
  · 人物面预算：主体 ≥50% / 人脸近特 ≥25% / 空镜 ≤20%
  · 写实纪录感：手持、现场光、禁美颜、禁电影感打光
  · 年代：2000 年前后中国内地大学食堂（不锈钢餐台/搪瓷碗/蓝布围裙/白瓷砖墙）
"""
import json
import os

ROOT = r'K:\Fluxgroup\FluxGroup'
BASE = os.path.join(ROOT, 'cph4', 'fleet', 'duanju-dept-v1', 'duanju-002-shanglu')
OUT_MD = os.path.join(BASE, 'D3-EP01-分镜表-v1.md')
OUT_JSON = os.path.join(BASE, 'plan', 'ep01-kf-prompts.json')

STYLE = ("documentary realism, handheld camera, available interior light from canteen windows, "
         "raw unretouched skin with visible pores and slight shine, "
         "year 2000 mainland China university canteen, stainless steel counter, enamel bowls, "
         "white tile walls, clean unlettered surfaces, 35mm film colour, slight grain")

HOU = ("a 28-year-old Chinese man from Sichuan, short unpromoted hair, broad shoulders, "
       "large work-worn hands, plain light-blue button shirt with rolled sleeves, dark trousers")
MA = ("a 38-year-old Chinese man, short slicked hair, dark blazer over a polo shirt, "
      "thin gold watch, permanent half smile")

# (kind, 景别, 内容)
SHOTS = [
    ("E", "ecu", "an extreme close-up of a flour-dusted hand slapping a worn notebook onto a greasy steel canteen table"),
    ("P", "wide", "%s standing at the end of a long queue, bowl in hand, looking down at it" % HOU),
    ("F", "cu", "close-up of %s, his eyes lifting from the bowl toward the serving window" % HOU),
    ("P", "med", "a canteen server behind the counter ladling noodles, shaking the ladle three times before it lands"),
    ("F", "cu", "close-up of %s asking a question, mouth barely open, jaw steady" % HOU),
    ("F", "cu", "close-up of %s smiling with his eyes only, mouth held flat" % MA),
    ("P", "med", "%s and %s facing each other beside the kitchen doorway, stainless counter between them" % (HOU, MA)),
    ("F", "cu", "close-up of %s speaking one short sentence, chin slightly raised" % HOU),
    ("E", "cu", "close-up of the notebook open on the table, columns of handwritten numbers in blue ink"),
    ("P", "med", "%s turning toward the queue, one hand holding the notebook open" % HOU),
    ("P", "wide", "the queue of students seen from behind, all heads turning toward the counter"),
    ("P", "med", "%s standing still among the turning students, notebook in hand" % HOU),
    ("F", "cu", "close-up of %s with the smile gone from his eyes, mouth held flat" % MA),
    ("P", "med", "%s clapping twice, slowly, elbows loose" % MA),
    ("F", "cu", "close-up of %s leaning in close, speaking low" % MA),
    ("F", "cu", "close-up of %s listening with a still face, eyes fixed on the other man" % HOU),
    ("P", "wide", "the canteen doorway at dusk, %s standing alone with the notebook in his hand" % HOU),
    ("F", "cu", "close-up of %s writing two characters on the last page of the notebook" % HOU),
    ("P", "med", "%s walking out through the doorway, back to camera" % HOU),
    ("E", "wide", "the empty canteen tables at dusk, steam still rising from a bowl left behind"),
    ("P", "med", "%s standing under the doorway light, closing the notebook against his chest" % HOU),
    ("P", "med", "%s reaching across the counter to take an enamel bowl, forearm flexing" % HOU),
    ("P", "med", "%s stepping back half a pace, both hands going into his blazer pockets" % MA),
]


def main():
    rows, idx = [], 0
    for kind, shot, detail in SHOTS:
        idx += 1
        sid = "S%02d" % idx
        subj = HOU if "you" not in detail else HOU
        prompt = "A %s: %s. %s." % (
            {"ecu": "extreme close-up", "cu": "close-up", "med": "medium shot", "wide": "wide shot"}[shot],
            detail, STYLE)
        rows.append({
            "id": sid, "prompt": prompt,
            "scene": "drama_interior", "light": "day" if idx <= 14 else "dusk",
            "shot": shot, "angle": "eye", "move": "handheld",
            "grade": "tw2001", "texture": "film_day",
            "kind": kind, "seed": 20261123 + idx,
        })

    n = float(len(rows))
    e = sum(1 for r in rows if r["kind"] == "E")
    f = sum(1 for r in rows if r["kind"] == "F")
    p = sum(1 for r in rows if r["kind"] == "P")
    ep, fp, pp = e / n * 100, f / n * 100, p / n * 100
    ok = ep <= 20 and fp >= 25 and pp >= 50
    print("EP01 shots=%d empty=%.1f%% (≤20) face=%.1f%% (≥25) body=%.1f%% (≥50) -> %s"
          % (n, ep, fp, pp, "PASS" if ok else "FAIL"))

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(rows, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    lines = ["# 《商路》EP01 分镜表 v1（%d 镜·竖屏 9:16）" % len(rows), "",
             "> 人物面预算：主体 %.1f%%（≥50）· 人脸近特 %.1f%%（≥25）· 空镜 %.1f%%（≤20）→ **%s**"
             % (pp, fp, ep, "PASS" if ok else "FAIL"), "",
             "| 镜 | 类型 | 景别 | 内容 |", "|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s |" % (
            r["id"], {"F": "人脸近特", "P": "主体", "E": "空镜"}[r["kind"]], r["shot"],
            r["prompt"].split(". ")[0][:60]))
    open(OUT_MD, 'w', encoding='utf-8').write("\n".join(lines) + "\n")
    print("shotlist ->", OUT_MD)
    print("prompts  ->", OUT_JSON)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
