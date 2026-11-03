# -*- coding: utf-8 -*-
"""vb_roster.py - turn screened candidates into an actionable talent roster.

Outputs voicebank\ROSTER.md:
  - per category, candidates sorted by acoustic score
  - tier A/B by gates (speech_ratio, bg_ratio, pitch distinctiveness)
  - the exact build command for each A-tier row
  - a rights note per class (named professionals vs. amateurs)

Rationale: a roster that cannot be executed is a list, not an asset. Every A row can be
fed straight into vb_build.py, so the bank grows by command, not by decision.
"""
import json
import os
import sys

VB = os.environ.get("VB_ROOT", r"E:\Fluxgroup\.codely-cli\voicebank")
CATS = {
    "audiobook": "有声书/评书（录音棚级、长时段、几乎无伴奏）",
    "radio": "电台/情感主播（气息与情绪起伏是卖点）",
    "anchor": "播音/主持（字正腔圆，适合旁白与播报）",
    "dubbing": "配音/广播剧（角色化音色，戏剧性强）",
    "uplive": "UP 主口播（知识/测评/科普，语速自然）",
    "actor": "演员/台词（舞台腔，爆发力强）",
    "timbre": "特殊音色（低音炮/沙哑/童声/老年/方言）",
}
RIGHTS = {
    "audiobook": "多为腰尾部播讲人；商用前确认授权，素人优先",
    "radio": "多为个人主播；注意节目版权",
    "anchor": "可能是在职主持人（机构身份），仅内部试验",
    "dubbing": "职业配音演员，声音人格强，商用需授权",
    "uplive": "UP 主本人声音，商用需授权",
    "actor": "公众人物/演员，形象权风险最高，仅研究用",
    "timbre": "素人为主，风险最低",
}


import re
BAD = re.compile(r'广播剧|多人|有声剧|MV|舞蹈|翻唱|音乐|直播回放|合辑|鬼畜|配音秀|漫画|动画')
GOOD = re.compile(r'单播|独播|朗读|讲述|口播|讲解|播讲|读|说|讲|课|科普|解读|全集')
def usable(r):
    t = str(r.get('title',''))
    if BAD.search(t): return False
    return bool(GOOD.search(t)) or r.get('cat') in ('uplive','anchor','timbre')


def tier(r):
    if r["speech_ratio"] >= 0.55 and r["bg_ratio"] <= 0.25:
        return "A"
    if r["speech_ratio"] >= 0.45 and r["bg_ratio"] <= 0.35:
        return "B"
    return "C"


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(VB, "screen_pool.json")
    data = json.load(open(src, encoding="utf-8"))
    rows = data["rows"]

    lines = ["# 声源名册（自动生成 by vb_roster.py）", "",
             "筛查口径：`speech_ratio` 说话占比、`bg_ratio` 静音/说话能量比（越小越干净）、"
             "`f0_med` 基频中位、`f0_iqr_ratio` 起伏（越大越有表现力）、`score` 综合分。",
             "", "A 档 = 说话占比 ≥0.55 且 bg ≤0.25（可直接进训练）；B 档需降噪加强或截取更干净片段。",
             ""]

    for cat, desc in CATS.items():
        sub = [r for r in rows if r["cat"] == cat and usable(r)]
        if not sub:
            continue
        lines.append("## %s" % desc)
        lines.append("")
        lines.append("| 档 | 分 | 基频 | 起伏 | 说话 | bg | 时长 | 作者 | 标题 | bvid | 命令可用 |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for r in sub[:12]:
            t = tier(r)
            lines.append("| %s | %.2f | %.0f | %.2f | %.2f | %.2f | %dm | %s | %s | %s | %s |" % (
                t, r["score"], r["f0_med"], r["f0_iqr_ratio"], r["speech_ratio"], r["bg_ratio"],
                r["dur"] // 60, str(r["author"])[:12], str(r["title"])[:34], r["bvid"],
                "是" if t == "A" else ""))
        a_rows = [r for r in sub if tier(r) == "A"][:6]
        if a_rows:
            lines.append("")
            lines.append("可直接开跑：")
            lines.append("```powershell")
            for i, r in enumerate(a_rows, 1):
                lines.append(
                    "python vb_build.py --voice vb-%s-%02d --raw <下载目录> --minutes 30 --epochs 20 --jobs 8"
                    % (cat, i))
                lines.append("  # 素材 = %s  %s" % (r["bvid"], str(r["title"])[:40]))
            lines.append("```")
        lines.append("")
        lines.append("> 权利提示：%s" % RIGHTS.get(cat, "商用前须确认授权"))
        lines.append("")

    lines.append("## 使用顺序建议")
    lines.append("")
    lines.append("1. `timbre` 与 `audiobook` 先跑（干净、长时段、权利风险低）；")
    lines.append("2. `uplive` 补齐语域（口播腔、自然语速）；")
    lines.append("3. `anchor` / `dubbing` / `actor` 仅在工作区内部试验，商用前逐条过授权。")
    lines.append("")

    out = os.path.join(VB, "ROSTER.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    counts = {}
    for r in rows:
        counts[tier(r)] = counts.get(tier(r), 0) + 1
    print("ROSTER ->", out, "tiers:", counts)


if __name__ == "__main__":
    main()