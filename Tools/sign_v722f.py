# -*- coding: utf-8 -*-
"""Append the V7.22f (title card) sign-off note to the existing review."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "cph4", "fleet", "mv0001-handover", "canon",
                 "DIRECTOR-REVIEW-V722E-PASS-20261105.md")

ADD = """

---

## 六、V7.22f 补签（2026-11-05 22:0x）· 片名卡

CEO 令：片名（=歌曲名）与作词作者要设计、排版与位置要好看。

- 新增：**竖排宋体片名卡**，右侧暗部，暖纸白，双层柔投影，竖细线分隔，词曲演唱右对齐贴线。
- 时长：0.45s 淡入 → 2.62s 起淡出 → 3.37s 结束，**只活在第一个镜头内**（首版跨镜压到女主，已否）。
- 帧数不变（14064），交付闸复跑 **PASS**：dup 0 / static 0 / seams 0 / freezes 3（均 <0.25s）。
- 成片：`outbound/krea2/30s-reel-v1/full_mv_v722f_60fps_1080p.mp4`（282MB）
- 设计留档：`canon/TITLE-DESIGN-v3-20261105.md`
"""
with io.open(p, "a", encoding="utf-8") as fh:
    fh.write(ADD)
print("appended v722f sign-off")