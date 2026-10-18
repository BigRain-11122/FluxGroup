# -*- coding: utf-8 -*-
# patch_orders_v58_r1018.py — orders.md 尾部补记 CEO MV 版权令（14:32）+执行回执
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\sjs20\Desktop\FluxGroup\docs\orders.md"
raw = open(P, "rb").read()
bom = raw[:3] == b"\xef\xbb\xbf"
s = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")

MARK = "V5.8 credits 四件套"
if MARK in s:
    print("SKIP: row already present")
    sys.exit(0)
if not s.endswith("\n"):
    s += "\n"

ROWS = [
"| 2026-10-18 14:32 | CEO 令（原话·发自 metis 会话）：「片名要加上专辑名和作词作曲，导演，大喵没鱼吃是二创。避免侵权。」（**MV 片名 credits 四件套令**·BigStream 长期硬门） | **executed（当窗收口）**：解读=片名卡必带=专辑名+作词+作曲+**导演**（credits 四件套）+二创显式署名。执行链：①V5.7 三行卡→**V5.8 四行卡**（make_title_card_v58_r1018.py：主标「愛在西元前」140px 鎏金+「二创：大喵没鱼吃」50px 亮金+「专辑《范特西》·作词：方文山·作曲：周杰伦」36px+**「导演：大喵没鱼吃」36px 新增行**·衬底随块加高·边距律全过）②叠底预验收 PASS（四行逐字完整）+成片 5.60s 终渲复验③build_full_mv_v58.py（v56 缓存 REUSE 全命中·唯一改=字卡·终长 234.25 精确·ASSERT-OK·full_mv_v58.mp4）④N1 音频闸 PASS（TP +0.2→-1.6 dBTP）⑤VideoSeal embed full_mv_v58_wmvs.mp4 四闸复验中；RETRO P6 升 credits 四件套标准（全曲适用） | executed（V5.8 交付链收口中） [via bm-a 导演席] |\n",
]
s += "".join(ROWS)
open(P, "wb").write((("\ufeff" if bom else "") + s).encode("utf-8"))
print("orders.md +1 row appended (bom=%s)" % bom)
