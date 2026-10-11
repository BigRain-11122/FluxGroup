# R-20260930-video-extraction-01 · 2D 活体 C 腿 v3：本地视频模型主径定谳+取帧科学化+图集播放全链实测

日期 2026-09-30 · 沙盒 2dlive-spike\c · 棒 C6（收尾：取帧→图集→Unity 播放→docs）· 主径素材 C3_matrix/m1_512_30_g30

## 一、四组数据与主径定谳（idf=帧对垫白参考图 RMSE·预注册判据=三项须 ≤ 基线）
- 基线 C2_formal_fb（0.9.5-2B@448px·v2 兜底径）：idf first/last/max = 0.0134/0.1553/0.1768 · 漂移离群 [76,77] · 动作峰 cons_max 0.0828
- 13B LTX-0.9.8-13B-distilled@512px·121f·infer 1316.8s：idf 0.0152/0.2201/0.2644 **三项全高于基线**+pop 84/121 帧+f_120 尾帧 Severe 面部熔毁 → **预注册判据未降档，13B≠主径**
- 矩阵 M1 0.9.5-2B@512px/30 步/g3.0·81f：idf **0.0130/0.1239/0.1727 三项全优**（idf_last −20% vs 基线）·离群 []（基线有）·cons_max 0.1223（+48%）→ **主径定谳=M1**；M2(512/40/g3.5) 0.0130/0.1290/0.1801、M3(448/40/g3.5) 0.0139/0.1589/0.1779 均不及 M1
- 云端 Seedance 2.0 mini（5s·720p·同提示词）：identity 零漂·MOTION_READABLE（挥手/跳跃清晰）= 观感上限锚点（C2_cloud_demo.gif·按条计费）

## 二、取帧科学化五律实测（CEO 亲点「避免大幅度跳帧」根治）
- 五律：等间隔（81→24·间距 3.48）+差分平滑（阈 0.08·1 帧替换 f77 0.097→0.0521·0 丢弃）+漂移离群过滤（中位 0.1499·MAD 0.012·限 0.2032·离群 0）+峰值对齐（峰 14/23/41/52/61/73）+循环缝选优（0.1233 无更优·保全长）
- 实证：out\C3_pop_compare.png 原始 7 尖峰跳帧→取帧后宽峰（动作事件型）；如实：动作相位边界相邻差分仍 >0.08（max 0.1408）——根治=削尖峰保动作语义，非零跳变
- 交付：out\C3_demo.gif（24f@512px·1,654,208B·-delay 8）+out\C3_frames_sheet.png（6×4·1,480,590B）；帧表目检 MOTION_READABLE（挥手 ×2 拍+啄鸣+微呼吸·跳未腾空）+如实瑕疵 f_004-005 面部过渡涂抹·f_022-023 眼色金琥珀漂移+头羽模糊

## 三、图集+Unity 播放交付（A5 图集正典·资源账）
- 图集：24 格零重复 2395×2650（格 479×530·12px 透明边）·白底洪泛抠 alpha+脚底锚；**坑1**：c4_atlas.py 脚锚取内容底行均值→撞阴影右叶帧缘碎片（foot_x 499≠真脚心 267→px −184→24/24 格越界叠印）→c6_atlas.py 橙脚质心+钳位修复（anchors 24/24 orange_feet·QC 0/24 越界·多模态四项过）
- 资源账：PNG-32 5,402,844B → PNG-8 量化实测 1,042,615B（19.3%）·ASTC 6x6 预估 900,474B（atlas_bytes/6）·BC7 4bpp 注记 3,173,375B
- Unity 批跑：**坑2**：C3 驱动 GetComponent<SR> 在驱动物体取（SR 在兄弟物体）→MissingComponentException→4 捕获全同 cell 0（1 轮证据 c\tmp\c6_play_fail1）→C6 双脚本显式接线（C6AtlasPlayDriver/Bootstrap·drv.sr=sr）→修复后 exit 0·14s·哨兵 frames=4 playtime=8.00·**drawCalls last=max=2**（单 SpriteRenderer 翻页）；PIL 4×4 交叉矩阵对角 4/4 全优（diag RMSE 10.25-11.82 vs 非对角 40.5-56.0）=逐格播对实证

## 四、本地 vs 云端差距（一行）
云端 C2_cloud_demo.gif 零漂锚点（identity 零漂+动作清晰+无面部抖动）仍是观感上限；本地 M1 主径 idf_last 0.1239+面部 Moderate 抖动（过渡涂抹/眼色漂移）+13B 尾帧崩坏已淘汰——差距=身份稳定性一档，本地优势=离线可复现+图集管线可直供 Unity（drawCalls 2 实测）。

## 五、应用表
| 产出 | 落位 | 用法 |
|---|---|---|
| M1 主径素材 | c\out\C3_matrix\m1_512_30_g30（81f） | 后续本地生成基准参数：512px/30 步/g3.0 |
| 取帧五律工具 | c\scripts\c4_extract.py + extract_report.json | 新视频取帧直接复用（-n 24 可调） |
| 演示 GIF/帧表 | out\C3_demo.gif·out\C3_frames_sheet.png | 对比板/汇报 |
| 图集+map | out\C3_atlas.png·C3_atlas_map.json（Unity 字节直载） | SpriteRenderer 翻页直用；c6_atlas.py 重建 |
| Unity 播放门 | Assets\SpikeScripts\C6Atlas*.cs + c\tmp\c6_run_c3play.ps1 | 批跑出哨兵+drawCalls+捕获，PIL 对角验收 |
| 淘汰证据 | c\out\C3_formal_13b + c5_cmp_13b.png | 13B 复评时对照（勿再走 1316.8s 弯路） |

## 验证声明
本地核验：extract_report.json/eval_report.json 数读、atlas QC（c6_atlas_qc.py 0/24 越界）、Unity 哨兵+日志数读、PIL 对角 4/4、帧表/图集/差分曲线多模态目检三路；未验证项：13B 尾帧 Severe 与 13B infer 1316.8s 承 C5 交接数据未独立复跑（13B 素材在场可复验）。分级源：A=本地实测（脚本+json+哨兵）；B=多模态目检（帧表/图集/pop_compare）；C=前棒交接（C6-任务书所载 13B 数据）。
