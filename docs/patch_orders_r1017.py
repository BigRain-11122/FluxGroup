# -*- coding: utf-8 -*-
# patch_orders_r1017.py — orders.md 尾部补记本窗四条 CEO 令（治理在册·P0 律）
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\sjs20\Desktop\FluxGroup\docs\orders.md"
raw = open(P, "rb").read()
bom = raw[:3] == b"\xef\xbb\xbf"
s = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
if not s.endswith("\n"):
    s += "\n"

ROWS = [
"| 2026-10-17 21:1x | CEO 令（原话六连·终审反馈）：①「镜头间的衔接还是有问题，导演和剪辑师去看看，其他都通过了」+「字幕要干净点，纯白色，不要黑边，间距，字体大小等考究，马上改好给我」②「爱在西元前的片头歌曲名好好设计，还有大喵没鱼吃也好好设计，在画面里要美观，AIGC 标识去掉，并注明欢迎转载，请注明出处」③「主要是镜头间的转场，硬切很难受 有跳帧，剪辑去调研看如何美化」④「女孩的镜头还是有穿帮和 AI 鬼影鬼畜，导演负责啊！」⑤「还乱入了动画镜头，导演你在干嘛？？？」（**MV V5.4 终审六连整改令**·呈看物=full_mv_v53.mp4） | **executed（当窗-夜窗三连收口）**：①转场=47 裸切量化+Top-16 判读→4 内点 XF（44/126.32/152/191.60）+b33 由 D08 换源自愈（dLuma 53.3→17.6）+其余 11 处定谳双光系骨架保硬切；②字幕纯白化 52px 零描边零 blur+Sp1.2（ASS 55 事件时间轴原样）；③歌名卡+大喵没鱼吃重设计（鎏金渐变+楔形符号带+落款式·验收 8.5 分）；④AIGC 三处删+片尾「欢迎转载请注明出处」声明层；⑤女主镜=E04 定罪慢放插值三重放大→0.85 提速+定格+bloom（N03/R03 复现检验推翻 V53 定罪=双双 C 干净）；⑥D08 换 cloudv2 archived 源（CG 纹理叠加+画廊乱入定罪清除）；取证全链 commit 68516f8+cd909b4 | executed（DIRECTOR-REVIEW-V5.4-PASS 签发 [via bm-a 导演席]） |\n",
"| 2026-10-17 23:0x | CEO 令（原话）：「我提的爱在西元前的问题 赶紧全部改好，严格审核后给我终片！！！」（**终片冲刺令**） | **executed（当窗）**：V5.4→V5.4.1（E04 提速+bloom）→V5.4.2（转场顶级升格）三轮重建全断言绿；严格审核=终验板三专项 PASS+转场四组判读 9/10·8/10·9/10+CHK-T3 16/16 全 PASS（子代理三层补证：ASS 规格级+全分辨率渲染级+亮背景反证级——字幕黑边彻底清除三重证据闭环）；终片=full_mv_v54.mp4（234.25s 精确·DIRECTOR-REVIEW-V5.4-PASS-20261017.md 签发呈 CEO） | executed（终片已呈·候 CEO 审片） [via bm-a 导演席] |\n",
"| 2026-10-17 23:2x | CEO 令（原话）：「剪辑的技巧很多，剪辑师和导演一起共同研究，尤其是转场，务必做到MV最顶级的」（**转场顶级令·剪辑师+导演共研**） | **executed（当窗 V5.4.2）**：转场设计正身重读（R-20261017-mv-fx-transitions-01 八语言族+era 禁用名单）→三升格：①44.00 fadeblack 违 era 禁用名单自纠→hblur 过门（光融进寂静·9/10）；②126.32 叠化+fx_leak 漏光伴切（地下金线光从土层渗出·8/10）；③191.60 叠化+fx_echo2=E01b 末帧跨千年残像叠印（「同一块碑跨千年」第二签名时刻·9/10）；正典三基线零回归；转场语言族现役 9 族 | executed（V542-TRANSITION-AUDIT 四组全 PASS·已并入终片） [via bm-a 导演席] |\n",
"| 2026-10-17 23:xx | CEO 令（原话）：「按最新的进度更新一遍所有项目的游戏软著材料，要精读和审查到位」（**软著材料全量刷新二批·精读审查令**·承 10-13 一批） | **executed（当窗收口）**：①生成器 32 款全量复跑——A 机 14 款源程序按最新代码重出（P08 +403 行：VideoRig 采集+Explore 探索+PuppetMicroMotion 多帧变体+T019 情感镜头·G09 +25 行）；②精读审查四项行数漂移修正（FluxVerse 8300→8377/P01 9500→9570/P08 7558→7961 双处）+P08 微动系统升格；③审计器 audit_copyright_r1017.py 立法首跑：32 款三件套零缺件·名称零违例·行数零漂移（复跑 ISSUES=0）；④报审提交区四款（P08/P01/FluxVerse/G09）12 件换新；⑤README 台账二批批记录+32 款行数回写；commit 99c7919；⑥**@bm-b/@bm-c 派单**：B 机 10 款（G04/G05/G07/G08/G13/G14/G20/G26/G23/G28）+C 机 8 款（G02/G09Y/G10/G12/G03/G06/G17/G18）各 owner 机窗口跑一遍 `python 软著申请材料/generate_copyright.py`（机队生成律·本机源程序=10-15 bm-c 批已产·10-17 后工程若有新提交须再复跑·材料随 git 归拢权威位） | executed（A 机面全绿·B/C 机复跑派单在行） [via bm-a] |\n",
]
s += "".join(ROWS)
open(P, "wb").write((("\ufeff" if bom else "") + s).encode("utf-8"))
print("orders.md +4 rows appended (bom=%s)" % bom)
