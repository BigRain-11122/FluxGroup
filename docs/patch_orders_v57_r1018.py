# -*- coding: utf-8 -*-
# patch_orders_v57_r1018.py — orders.md 尾部补记本窗 CEO 两令（V5.7 署名字卡三连令+逐镜终审高清成品令）
# 幂等：已存在即跳过（多窗共享仓安全设计）
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\sjs20\Desktop\FluxGroup\docs\orders.md"
raw = open(P, "rb").read()
bom = raw[:3] == b"\xef\xbb\xbf"
s = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")

MARK = "V5.7 署名字卡三连令"
if MARK in s:
    print("SKIP: rows already present")
    sys.exit(0)
if not s.endswith("\n"):
    s += "\n"

ROWS = [
"| 2026-10-18 13:3x | CEO 令（三连）：①「片名加专辑和词曲署名」（专辑《范特西》·作词：方文山·作曲：周杰伦）②「标注二创定位，避免侵权」（二创：大喵没鱼吃）③「撤掉爱在西元前上方看不懂的楔形符号」（**V5.7 署名字卡三连令**） | **executed（当窗）**：make_title_card_v57_r1018.py 出图=三行署名字卡（主标「愛在西元前」140px 鎏金=画宽 57% 居中·「二创：大喵没鱼吃」50px 亮金·「专辑《范特西》·作词：方文山·作曲：周杰伦」36px 角标金·楔形带彻底移除）+全分辨率叠底验收 PASS（三行逐字转录完整·层次协调·零楔形残留）+V5.7 装配全绿（build_full_mv_v57.py·v56 段件缓存 REUSE 全命中·唯一改=title_card_v57.png·终长 234.25 精确·ASSERT-OK·full_mv_v57.mp4）+成片 5.60s 字卡帧终渲复验 PASS | executed（V5.7 基线出炉·候逐镜终审+高清成品链） [via bm-a 导演席] |\n",
"| 2026-10-18 13:5x | CEO 令（原话）：「基本定稿，逐镜逐帧专家团过问题快速修复给我高清成品」（**逐镜终审+快速修复+高清成品交付令**·V5.7 署名版为基线） | **executing（当窗全链推进）**：①逐镜专家团四波子代理在飞（W1=0-47.5/W2=47.5-110.52/W3=110.52-187.26/W4=187.26-234.25·V5.6 成片基线上跑=内容与 V5.7 除字卡窗外一致·一票否决四查〔年代穿帮三面/文字硬伤/人物一致性/技术硬伤〕+小板串行+指控量化复核防假警报纪律）②本地量化扫描完成=4fps 全片 luma/重复帧（无过曝帧·死黑全落 fade/灯灭/夜戏设计窗·60 条 aHash 冻结旗经 11 条长跑像素级三勘全判 ALIVE=哈希碰撞假阳性·量化面零阻断）③回执后=问题清单严重度分级→快速修复（已过项零改·真缺陷才修·punch-in/delogo/换源工艺在案）④交付链=VideoSeal 暗水印 embed（消息「大喵没鱼吃」120bit·四闸验证：extract 100%+stress crf23/28+psnr+目检板）→N1 音频 TP≤-1.0 复测→KFT 封面帧→DIRECTOR-REVIEW 终版→成片直呈 CEO | executing（四波在飞·回执随到随修） [via bm-a 导演席] |\n",
]
s += "".join(ROWS)
open(P, "wb").write((("\ufeff" if bom else "") + s).encode("utf-8"))
print("orders.md +2 rows appended (bom=%s)" % bom)
