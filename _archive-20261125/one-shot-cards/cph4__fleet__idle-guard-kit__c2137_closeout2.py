# -*- coding: utf-8 -*-
# c2137_closeout2.py -- snapshot doc + kanban row for round C2137 (rerun after the .format brace bug).
import io
import os

ROOT = r"K:\Fluxgroup\MiniGame"
KANBAN = os.path.join(ROOT, "Design", "configs", "GLOBAL", "\u6863\u6848", "\u673a\u961f\u534f\u4f5c\u770b\u677f.md")
SNAPDOC = os.path.join(ROOT, "\u81ea\u52a8\u5316\u5feb\u7167-c.md")
SNAP = "tick-20261020-0945@c2137-casting-full"

snap = u"""# \u81ea\u52a8\u5316\u5feb\u7167-c\uff08C \u673a\uff09\u00b7vC2137\u00b72026-10-20 09:45\u00b7\u661f\u6674\u5973\u4e3b\u5b9a\u8138\u6b63\u6863 12 \u683c\u5206\u8f6e\u5728\u71c3

- **\u68c0\u6d4b\u65f6\u95f4**\uff1a2026-10-20 09:28 \u2192 09:45\uff08tick = """ + SNAP + u""" \u00b7 normal_iteration \u00b7 batchmode \u65e0 \u00b7 MCP \u65e0 \u00b7 GPU \u6709\uff09
- **Step0**\uff1apreflight \u5168 PASS\u3001FLAG \u96f6\uff08INBOX / CEO-DESK / WAVE-PENDING / REDLINE / ORPHAN \u5168\u7a7a\uff09\uff1bINFO = RAM 9.4% < 40% \u2192 NOT-GREEN-IDLE \u00b7 GPU free 14.3G verdict=GPU_DRAFT_OK
- **\u8fd0\u884c\u6a21\u5f0f**\uff1anormal_iteration\uff0810 \u5206\u949f\u65cf\uff09

## \u672c\u8f6e\u5b9e\u7269\uff08\u53ef\u6253\u5f00\uff09

- **\u5b9a\u8138\u6b63\u6863\u6d77\u9009\u5728\u71c3** = `media/MV/mv0001/xingqing/xq-casting-c2136-full/`\uff081344\u00d7768 PNG\uff0c\u9996\u5e27 `CAST_A_ponytail_dusk_s583046.png` \u5df2\u843d\u76d8\uff09
- **\u5b9e\u65f6\u8fdb\u5ea6** = `xq_casting_c2136_full_progress.json`\uff08\u9010\u683c ok/file/seed\uff0c\u53ef\u590d\u73b0\uff09
- **\u65e5\u5fd7** = `media/MV/mv0001/logs/xq_casting_c2136.out.log` \u4e0e `.err.log`
- **\u6536\u5272\u89e6\u53d1\u5668** = `.codely-cli/engine-tick/wave-harvest-pending.json`\uff08\u4e0b\u8f6e GateSitter \u5fc5\u5f00\u6536\u5272\u8f6e\uff09

## \u8f66\u9053\u5757

| \u8f66\u9053 | \u72b6\u6001 |
|---|---|
| M1 dev-tick | \u672c\u73ed\uff08C2137\uff09 |
| M2 \u96f7\u8fbe | \u4e0a\u6b21 09:52\uff0810-20\uff09 |
| M4 \u653f\u7b56 | \u65e0\u65b0\u4ef6 |
| M5 \u5ba1\u8ba1 | \u4e0a\u6b21 10-20 \u65e9\u73ed |
| M6 \u7acb\u9879 | \u65e0\u65b0\u4ef6 |

## \u5f00\u53d1\u5757\uff08WIP\uff09

- \u672c\u673a owned \u4e3b\u7ebf = **\u661f\u6674 MV\uff08mv-album-001-jay\uff09**\uff1aA \u5305 33 \u5355\u5143\u5df2\u88c5\u914d + \u54cd\u5ea6\u6bcd\u7248 + origin \u590d\u6838\u95ed\u73af\uff1bB \u5305 6 \u5e27\u5361\u5b9a\u8138 \u2192 \u672c\u8f6e\u6b63\u6863\u5168\u5c3a\u5bf8\u6d77\u9009\u5728\u71c3\u3002
- \u5176\u4f59\u6b3e\uff08G22/G25/G03/G06\u2026\uff09= \u89c2\u5bdf\u4f4d\uff0c\u672c\u8f6e\u96f6\u52a8\u4f5c\u3002

## \u8d44\u4ea7\u53f0\u8d26

| \u57df | \u6001 | \u8bf4\u660e |
|---|---|---|
| \u7b56\u5212 | B | \u661f\u6674 39 \u5e27\u4e2d A33 \u5168\u843d\u5730\uff0cB6 \u5019\u5b9a\u8138 |
| \u4ee3\u7801 | B | \u65e0 blocked\uff1bA \u5305\u88c5\u914d\u7d22\u5f15 v2 \u4e0e\u6837\u7247 v2 \u5747\u8fc7\u95f8 |
| QA | B | \u9009\u89d2\u4e09\u95e8\u7981\u5168\u8fc7\uff08v2 8.0\uff09\uff1b\u6b63\u6863\u95f8 CASTING-FULL-END \u5f85\u6536\u5272\u8f6e\u5224 |
| \u7f8e\u672f | B | \u672c\u6279\u6b63\u6863 12 \u683c\u5728\u71c3\uff1bB \u5305 6 \u5e27\u672a\u4ea7 |
| \u97f3\u9891 | A | \u672c\u66f2 259.4s \u6bcd\u5e26\u5728\u76d8\uff1b\u6837\u7247\u5df2\u8fc7 loudnorm |

## \u8d28\u91cf\u5757

- \u95f8 = \u5f00\u5de5\u524d\u53e3\u4ee4\u7a7a\u961f\u63a2\u9488 PASS\uff08queue empty 0/0\uff09\u00b7 \u63d0\u793a\u8bcd lint \u96f6\u547d\u4e2d 12/12 \u00b7 \u79cd\u5b50\u552f\u4e00 12/12
- \u81ea\u6293\u7f3a\u9677 0\uff08\u672c\u73ed\u672a\u8dd1\u5b8c\uff0c\u4e0d\u58f0\u79f0\u6210\u54c1\uff09
- \u9057\u7559\uff1aB \u578b\u591c\u683c\u5218\u6d77\u3001\u591c\u683c\u9ad8\u5149\u8f7b\u5fae\u8721\u9762 \u2192 \u5728\u672c\u6ce2\u6837\u5f20\u91cc\u4e00\u5e76\u91cd\u770b

## \u95ee\u9898\u6e05\u5355

- **(\u9ec4)** B \u5305 6 \u5e27\uff08S1-08 / S3-17 / S3-21 / S5-31 + B \u8865 2\uff09\u5019\u5b9a\u8138\u62cd\u677f \u2192 \u6b63\u6863\u5c31\u4f4d\u540e\u5f53\u8f6e\u9009\u578b
- **(\u84dd)** \u673a\u5668\u95e8\uff1a\u65e0

## \u989d\u5ea6\u4e0e\u5de5\u5177

- GPU\uff1aComfyUI 0.36.0 \u5728\u73ed\uff0cKrea2 turbo fp8 + qwen3vl 4b + qwen_image_vae\uff0c\u672c\u8f6e 12 \u683c\u5206\u8f6e\u5728\u71c3
- \u4e91\u7aef token\uff1a\u672c\u8f6e\u96f6\u6d88\u8017\uff08\u5168\u672c\u5730\uff09
- \u5907\u8d27\u6c60\uff1abm-c-gpu-bank jobs=45 \u00b7 pending=0 \u00b7 claimed=1\uff08`casting-ab-full-c2136`\uff0cpid 52820\uff09

## \u4e0b\u8f6e\u9009\u7ebf

1. \u6536\u5272\u672c\u6ce2\uff1a12/12 \u9f50 \u2192 \u8d34\u5168\u5c3a\u5bf8\u63a5\u89e6\u677f\uff08`xq-CASTING-BOARD-c2136-full.jpg`\uff09+ CASTING-FULL-END \u95f8\u5224 \u2192 \u5bfc\u6f14\u5e2d\u9501 ID \u5757
2. \u9501\u4f4f ID \u5757 \u2192 \u91cd\u6447 `KF-PACK-B` 6 \u5e27\uff08S1-08 / S3-17 / S3-21 / S5-31 + B \u8865 2\uff09
3. A+B \u5408\u88c5\u8986\u76d6\u5168\u66f2\uff08\u73b0 A \u5305 196.14s / \u8868 238s / \u66f2 259.4s\uff09
4. \u5386\u53f2\u5feb\u7167\uff08vC1998\u2013vC2136\uff09\u5728 git \u91cc\u53ef\u6eaf\uff0c\u672c\u6587\u4ef6\u81ea vC2137 \u8d77\u53ea\u7559\u5f53\u524d\u6001
"""
t = SNAPDOC + ".tmp"
io.open(t, "w", encoding="utf-8", newline="").write(snap)
os.replace(t, SNAPDOC)
print("SNAP-OK", SNAP, len(snap))

k = io.open(KANBAN, encoding="utf-8").read()
kn = (u"| C | 2026-10-20 | **C2137 \u661f\u6674\u5973\u4e3b\u5b9a\u8138\u6b63\u6863 12 \u683c\u5206\u8f6e\u5728\u71c3**"
      u"\uff0809:28-09:45 tick\u00b7\u53f7\u6c60 C2137@09:30:38\uff09\uff1a"
      u"**\u6b63\u5728\u5e72**=`casting-ab-full-c2136` \u6b63\u6863\u6d77\u9009\uff08A/B \u578b \u00d7 \u9ec4\u660f/\u591c \u00d7 3 \u79cd\u5b50\uff0c1344\u00d7768\uff0cpid 52820\uff09\uff1b"
      u"**\u6700\u8fd1\u4ea4\u4ed8**=\u9996\u5e27 `CAST_A_ponytail_dusk_s583046.png` \u5df2\u843d\u76d8 + \u5b9e\u65f6\u8fdb\u5ea6 json\uff1b"
      u"**\u4e0b\u4e00\u6b65**=\u6536\u5272\u8f6e\uff08wave-harvest-pending \u5df2\u843d\uff09\u8d34\u5168\u5c3a\u5bf8\u63a5\u89e6\u677f\u2192\u9501 ID \u5757\u2192`KF-PACK-B` 6 \u5e27\uff1b"
      u"**\u81ea\u6291**=\u672c\u73ed\u672a\u58f0\u79f0\u6210\u54c1\uff0c\u6536\u5272\u95f8 CASTING-FULL-END \u7559\u4e0b\u8f6e\u5224 |\n")
idx = k.find(u"| C | ")
if idx < 0:
    raise SystemExit("KANBAN-C-ROW-SEARCH-FAIL")
k2 = k[:idx] + kn + k[idx:]
tmpk = KANBAN + ".tmp"
io.open(tmpk, "w", encoding="utf-8", newline="").write(k2)
os.replace(tmpk, KANBAN)
print("KANBAN-OK delta=%d" % (len(k2) - len(k)))