# PROMPT-GATE-V53R-CLOUD-2shot-r1017 · 独立提示词专家审 verdict

- gate id=PROMPT-GATE-V53R-CLOUD-2shot-r1017 · 被审包=canon/V53R-CLOUD-2shot-r1017.md 4 条（KF-D04/KF-SIL1 修帧 + I2V-D04/I2V-SIL1）
- 审席=独立提示词专家席〔PROMPT-EXPERT-GATE v1 第 2 层·禁自审自签〕
- 成文注记：审席三度阵亡（2 原跑+1 续跑·分析毕落盘前墙钟耗尽族）——**本 verdict=审席分析回收+主窗代笔成文**（判例=发现清单回收+主窗接管），审席语义结论忠实转录；两处坐标疑点经导演席按帧析实测值核正（见 §核正）。
- 前置：第 1 层 lint 机核已过 4/4 零命中（KF-D04 98 词/KF-SIL1 69/I2V-D04 70/I2V-SIL1 56·runner=lint_v53r_cloud_r1017.py）

## 一 逐条 verdict 表

| 条目 | 扫描简记（审席语义面） | verdict | FIX |
|---|---|---|---|
| KF-D04 | B4 一句直接改动+保持项 ✓（禁过程叙述/禁重述整幅·「render the surface beneath as a plain worn wooden table」=板面铺满全帧的必然改写项·非越界加戏）；C4 形制锚到部件 ✓（wet clay tablet+incised cuneiform rows/reed stylus+full pale handle/V-groove 级）；C1 双真值源消解 ✓（damp sheen 显式绑右上灯轴·keep raking light axis/amber palette 光色不改物色式）；D 面可信静止态 ✓（笔尖触板+手姿保持=i2v 起帧可用）；G1/G3 年代媒介锚 ✓；edit_region 覆盖度：受光可读子区（x≥430px=0.320）⊂ region（x≥360px=0.268）✓·手 bbox（0.577-1.0）⊂ region ✓·刷具虚影 ⊂ ✓·避灯焰（region 顶 y=60px=焰界）✓；风险=区内大手笔重绘手部保真（包 §五已载·逐指核 QC+缩区两遍法回退梯在场） | **PASS** | — |
| KF-SIL1 | B4 ✓（一句替换+同格同深同风格约束+全保持项）；C4 ✓（eight-pointed star votive glyph+single-line V-groove·与邻符同 size）；C1 ✓（upper-left edges 绑同火把光+grooves 同深影）；D 面静止可信 ✓；edit_region 覆盖/溢出：左界 494px vs 左邻蝶形符右缘 488px=**6px 净距不入界 ✓**（帧析原文实证）；右界 586px vs 人物发丝剪影 590px=**4px 净距不重叠 ✓**（帧析「间隙 4-6px」=region 与剪影间净距·非心形与剪影间距）；残留风险=4px 重绘渗色带（watchpoint·QC 帧检剪影背线完整兜底） | **PASS** | — |
| I2V-D04 | v2 五律全过：①零文化锚·保留句官方口径 ✓②只写接下来（描字+尘+影=延伸非重述）✓③≥2 层（腕动/尘升/影摆）✓④五槽序 ✓⑤一镜一动作·70 词·零否定 ✓；D1=修帧后首帧自然延伸（笔尖触板→描字）✓；E3 尘绑灯束可见动因 ✓；E5 lamp flare holds steady=锁其余微动源 ✓；H3 零音轨 ✓；I1/I2 零冲突 ✓；幅度上限参数（腕摆±10-15°/行程 80-150px）与帧析活动空间实读一致 ✓ | **PASS** | — |
| I2V-SIL1 | 五律全过：①保留句 ✓②火焰 flicker/halo swelling/ash drift=帧内火把锚的延伸非重述 ✓③双火把 flicker+ash=两层 ✓④五槽 ✓⑤56 词零否定 ✓；D1=双火把在帧（焰心 x≈0.18/0.81）→flicker=自然延伸 ✓；E3 halo 绑火焰 ✓；E5 静止符号锁死（symbols hold their grooves）+微动源=火焰 ✓；F1 符带刻符保持 ✓；H3 ✓ | **PASS** | — |

## 二 核正记（导演席·审席两处坐标疑点复核）

审席在途分析曾按「心形右缘 0.425+4-6px 间隙」重推导剪影位（≈0.428-0.4295）并据此外推 region 右界 0.436 溢出剪影 ~9-10px——**该推导与帧析实测值冲突，判误推**：帧析正身（V53R-CLOUD-2shot §一定位实读）明载左邻蝶形符右缘 px≈488·剪影轮廓 px≈590·region=px(494,220,92,82)——按实测：左净距 494−488=6px ✓；右净距 590−586=4px ✓。帧析「间隙仅 ≈4-6px ⚠️」语义=region 界与剪影间的渗色预警（非重叠宣告）·其「叠加保护遮罩」建议与 edit_mode=local 单选约束（region/mask 互斥）不相容·已按 region-only 模式+QC 帧检兜底收案。

## 三 病灶行汇总（watchpoints·非 FIX）

1. KF-D04 区外残留板面纹理：受光可读子区全覆 ✓·区外（顶带 y<60 焰区/底带 y>580 暗衰减带/左缘暗带）低可读性——QC 帧级扫查「无编绳/无竹条可读」全帧核·若出可读残留→region 扩界重试（扩至 [0.0, 0.078, 1.0, 0.755] 级·代价=重绘面增大）。
2. KF-SIL1 4px 渗色带：QC 核剪影背线完整+邻蝶形符零形变；渗色实发→缩 region 右界至 0.430（px 577·心形右缘 571 内 6px/剪影 590 外 13px）重试〔原 §五 fallback 值 0.370 系乱码·已在包正身勘误〕。
3. KF-D04 手部保真=本包最大重绘风险位（审席与包 §五 双确认）：QC 逐指核（五指/红甲/袖口）·不过即同参数重试或缩 region 两遍法（先板后笔）。

## 四 总结

- 计数：**PASS 4 / FIX 0 / REJECT 0**
- 审席语义面结论：四条全过（两修帧条 B4/C4/C1/D/G 全绿·region 覆盖经实测值核正为安全；两 i2v 条五律全过）。
- 复发升格建议：edit_region 溢出预警若在 QC 实证复发（渗色伤剪影/邻符）→ 升格为 lint 位（region-vs-bbox 净距机核·<3px 即 fail）。
- 候导演席注意点：①烧后 QC 双帧级（D04 手部逐指+区外板面·SIL1 剪影背线+邻符）②C01 人脸镜仍候 bm-c（本包不含）③装配重建候三镜齐。

## 五 导演席签发（第 3 层）

- **签发=PASS**（审席 4 PASS 转录核正无误·watchpoints 移交 QC 帧检清单执行）——**D04/SIL1 云道修帧即行点火**（generate_image edit_mode=local ×2·region 照包 §一·prompt 照包 §一/§二 gated 文本逐字）。
- 包正身 §五 勘误同步执行：fallback 值 0.370→0.430（乱码修正）。
- 签发人=bm-a 导演席 · 2026-10-17 21:2x
