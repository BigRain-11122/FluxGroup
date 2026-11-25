# -*- coding: utf-8 -*-
"""C2120: append the C machine row to the fleet collaboration board."""
import os
import time

P = r"K:\Fluxgroup\MiniGame\Design\configs\GLOBAL\档案\机队协作看板.md"
now = time.strftime("%Y-%m-%d %H:%M")
ROW = ("| C | 2026-10-20 | **C2120 六格 4K 颗粒端点定谳 + r1017 §八终检四项闭环**（04:31-04:4x·占号 C2120）"
       " | 实物=①六格 4K 按 **grain 0.10** 干净重烧 6×3840×2194（15.1-15.8MB·单帧 8.1-10.1s·s20193/s20202 与 A/B 端点件"
       "字节恒等=确定性）+ 对比板 xq-S527-4K-GRAIN010-BOARD-c2120.jpg 473,453B + 回执 JSON；②颗粒 A/B 证据板"
       " xq-S527-GRAIN-AB-BOARD-c2120.jpg 223,408B（多模态读 0.10 更近 2000s 胶片）；③§八证据板五张（风筝线/草尖 1:1、"
       "s20160 手持物 1:1×3、s20105 拉伸、s21026 双蝶 1:1×3）+ 实测 JSON 两份；④4K 监看板 120,229B（star_retention "
       "1.27-3.50 无暗星流失·corner_dark 0.995-0.9998） "
       "| 判定=§八-2a 风筝线振铃 halo_p50 4.23/4.45 灰阶=净（闭合）·草尖 4.30/6.23 系刃状草叶真实高频（留眼判）；"
       "§八-2b 高光 knee 最大跳变 2.03/1.93/7.44/3.84 灰阶·clip_frac 0=无硬台阶（闭合）；§八-3 s20160 手持物 ≥210 亮像素"
       "占比 0.0000/最大自发光斑 0px=无大亮屏（CD/MD 读法获支撑·闭合）；§八-4 s20105 暗块拉伸后梯度方向熵 4.901/5.17 bit"
       "·无头肩闭合亮块（第三影证伪 85%→93%·闭合）；§八-5 双蝶轮廓拟合 IoU 0.779(rot148°/sc1.30/面积比1.086)=中间带"
       "不自裁→交导演；§八-1 条件①细线修补定位在 grain 件上被颗粒同谱混叠、地址不可信（如实记档）；§八-6 S7R 标注 conform 顺延 "
       "| 下一步=★§八-6 S7R 标注 conform（A/B/C→s7rA/s7rB + ORGINAL 拼写·零 GPU）·§八-1 条件① 先在无颗粒 ESRGAN 采件上定位细线伪影"
       "·§八-5 双蝶候导演一句话定谳回写；银行 28 done/1 pending（后继 s527-grain-007-vs-010 已预挂，脚本试跑通过） |")

with open(P, "rb") as f:
    raw = f.read()
eol = b"\r\n" if b"\r\n" in raw[-800:] else b"\n"
if not raw.endswith(b"\n"):
    raw += eol
with open(P, "wb") as f:
    f.write(raw + ROW.replace("\n", eol.decode()).encode("utf-8"))
print("BOARD-END row appended bytes=%d total=%d ts=%s" % (len(ROW.encode()), os.path.getsize(P), now))