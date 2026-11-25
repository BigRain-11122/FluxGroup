# -*- coding: utf-8 -*-
"""C2120: append the sec-8 execution receipt block to xq-AB-DIRECTOR-RATIFY-r1017.md."""
import os

P = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\xq-AB-DIRECTOR-RATIFY-r1017.md"
BLOCK = """
## 十一 C2120 终检移交清单执行回执（bm-c 机·2026-10-20 05:2x·§八逐项）

> 全部为盘面实测/机械探针，未改任何原档像素；证据件路径均相对于 `media/MV/mv0001/xingqing/`。

| §八项 | 状态 | 实测结论 | 证据件 |
|---|---|---|---|
| 1 六格 ESRGAN 线补修+4K 复核 | **条件②闭合·条件①待修** | 颗粒端点 A/B 已出（0.05 vs 0.10），多模态读 **0.10 更近 2000 年代胶片**（暗部 0.05 略偏数字底）→ 六格已按 **grain 0.10** 干净重烧（3840×2194·15.1–15.8MB·s20193/s20202 与 A/B 端点件字节恒等=确定性）；4K 监看：star_retention 1.27–3.50（无暗弱小星流失）·corner_dark 0.995–0.9998 六格一致。**条件①（细线幻觉/点阵残留局部修补）仍未做**：定位探针在 4K 件上每格报 130–357 个孤立高频斑，与刚加的胶片颗粒同谱混叠、地址不可信（已知局限，勿直接照坐标修补） | `xq-S527-GRAIN-AB-BOARD-c2120.jpg`·`xq-S527-4K-GRAIN010-RECEIPT-c2120.json`·`xq-S527-4K-GRAIN010-BOARD-c2120.jpg`·`xq-S527-4K-GRAIN010-MONITOR-c2121.json`·`xq-S527-ARTIFACT-LOCATE-c2121.json` |
| 2a S0-04 风筝线/草尖振铃 | **闭合（风筝线）·草尖留 1:1 复看** | 细亮结构旁 2px 高通振幅中位：风筝线 4.23/4.45、草尖 4.30/6.23（灰阶，≤6=不可见振铃）；风筝线全净。s20039 草尖带 p90 23.05/40%>8 为刃状草叶真实高频结构（非周期晕），非振铃 → 出 1:1 板交导演眼判 | `xq-S08-PROBE2-c2120.json`·`xq-S08-KITE-1TO1-c2120.jpg`·`xq-S08-GRASS-1TO1-c2120.jpg` |
| 2b S0-04/05 膝点连续性（高光 knee 波形） | **闭合·四格单调无断阶** | 顶部 5% 亮度曲线 0.1% 步长最大跳变：2.03/1.93/7.44/3.84 灰阶（knee_ratio 5.77/5.60/5.33/2.59）；clip_frac(≥250)=0 四格一致 → 无硬截断台阶，S0-05 两格的 7.4/3.8 由车铃镜面高光连通所致、非曲线断裂 | `xq-S08-PROBE-c2120.json` |
| 3 S4-23 s20160 手持物 100% 定谳 | **闭合·支撑 CD/MD 读法** | 物件裁切框 229×119px@(611,407) 内 **≥210 亮像素占比 0.0000、最大自发光斑 0px** → 无大亮屏（智能手机负向特征缺失），与外框形制并读 = 2000 年代随身听级；1:1×3 板交导演 | `xq-S08-PROBE-c2120.json`·`xq-S08-S423-HANDHELD-1TO1-c2120.jpg` |
| 4 S2-14 s20105 亮度拉伸复检 | **闭合·第三影维持证伪** | 暗块 (0–33%×30–79%) 拉伸至全幅后：梯度方向分布熵 4.901/5.17 bit（近满=纹理方向弥散、无连贯轮廓）·拉伸后高频能量 3.87·**无头肩级孤立闭合亮块**；置信 85%→**93%** | `xq-S08-PROBE-c2120.json`·`xq-S08-S214-STRETCH-c2120.jpg` |
| 5 S2-13 s21026 旋转对齐残差差分 | **机械面未决·眼判板已出** | 轮廓相似拟合最佳 IoU 0.779（rot 148°, sc 1.30, 面积比 1.086=近等标度）；落在 0.75–0.90 中间带=**大体相似成立、翼缘细节有别**，判「刚性克隆」或「自然变化」均不成立 → 不自行改判，出 1:1×3 双蝶板交导演定谳（原降级附条件状态维持） | `xq-S08-PROBE2-c2120.json`·`xq-S08-S213-BUTTERFLY-1TO1-c2120.jpg` |
| 6 版本管理勘误（S7R 板面列举 s7rA/B 口径 + ORGINAL 拼写） | **未做·已预挂** | 需重出 S7R 板族标注体系（A/B/C 三列 → s7rA/s7rB 对齐回执口径）+ 修 `xq-AB-S7R-COMPARE-S5-26-r1058.jpg` 的「ORGINAL」字样；本班时间盒已尽，预挂为后继件 | — |

**下轮建议**：① §八-6 标注 conform（零 GPU·纯板面重出）；② §八-1 条件①细线幻觉修补必须先取得可信地址（建议在**未加颗粒的 ESRGAN 上采件**上定位，勿在 grain 件上找）；③ §八-5 双蝶待导演一句话定谳后回写本节。
"""

with open(P, "rb") as f:
    raw = f.read()
eol = b"\r\n" if b"\r\n" in raw[-400:] else b"\n"
add = BLOCK.replace("\n", eol.decode()).encode("utf-8")
if not raw.endswith(b"\n"):
    raw += eol
with open(P, "wb") as f:
    f.write(raw + add)
print("APPENDED bytes=%d total=%d" % (len(add), os.path.getsize(P)))