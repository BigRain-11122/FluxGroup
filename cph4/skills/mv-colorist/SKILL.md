---
name: mv-colorist
description: MV 调色席技能（2000 telecine 底 × ffmpeg 实参）。Use when building or auditing a grade chain — black lift vs curves, skin turning uniformly red, whole-frame blue cast at night, grain/vignette/halation ordering. 含本机实测带位与暗角标定，防止把 PI 系暗角当轻档。正身=research/SEAT-colorist-20261020.md
---

# MV 调色席（mv-colorist）

## 一句话
先把量测做出来，再挂风格。**没数的调色=凭感觉。**

## 实测标定（ffmpeg 9.0.1·本机复算）
- `colorbalance` 带位：**mid = 灰阶 32-104（峰 64）／high = 96-255**；`rm=1` 时 128 灰 dR=0 → **中调调不到肤色**，暖推肤色用 `rh/bh`。
- 暗角：`0.30 → -16.9%｜0.40 → -27.3%｜0.50 → -39.8%｜PI/5 → -55.5%｜PI/4.6 → -63.9%`。**PI 系两档禁用**（历史缺陷：装配链长期用 PI/5 却文档写"轻档"）。
- 黑位：`eq=brightness` 抬黑会灰；`lift 0.010` 仅 2.5 code 不可见 → 用 curves 黑点 `0/0.045`（≈11 code）。
- 颗粒两法：直加 `noise` 必须放 curves **之前**；softlight 颗粒放之后（放反=全带数字噪声）。

## 硬判据
- 黑位 p1=10-14 code；高光 p99=247-251、clip=0。
- 三带非肤色 R−B：shadow +24~32／mid +110~130／high +20~35。
- 肤色：颊部 R−B +55~+85、R>G>B、跨镜 ΔE2000<2。
- 颗粒中调 σ1.5-3.0、黑位 σ<1.0；暗角角部 -12~-20%。
- 铁序：归一→分带/曲线→halation→颗粒→暗角→输出；颗粒后禁锐化。
- 每段只动明度/饱和 ±10%，不换色相家族；同段一档，禁逐镜各调。

## 流程
1. 归一校白（`colortemperature` + `normalize`，低反差雾镜先限幅）。
2. 抽 3 帧量三带与黑位。
3. 落分带参数（肤色镜走保护档：rm/bm 减半）。
4. halation（闸 0.62）、颗粒、暗角。
5. 盲评与姊妹曲并排能分开。

## 禁用
水洗滤镜｜现代 LUT 满强度｜逐镜各调｜整体蓝罩／整体红脸｜`eq=brightness` 抬黑｜PI 系暗角当轻档｜颗粒后锐化｜闪白帧挂 halation。

## 来源分级
A=本机 ffmpeg 实测、原版 9 锚帧直测、KODAK VISION 500T 数据表；B=张明珠访谈（台湾 MV 是 telecine 主线）、spectral_film_lut 114★MIT（只出 LUT）；C=morphic/infinitecreation 教程类。