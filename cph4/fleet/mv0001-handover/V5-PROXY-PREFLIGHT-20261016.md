# V5-PROXY-PREFLIGHT — 2026-10-16（管线预检实录·bm-a）

> 性质：**管线预检**，非 V5 正身 PROXY-PASS。本跑全部源=legacy/fallback——17 镜 V5REDO（@bm-c 夜窗连烧·交付哨死线 23:30）到货前，**不得据此发 PROXY-PASS**。
> 制=PLAYBOOK v1.2 代理/PROXY-PASS 双闸 + V5-TYPOGRAPHY-SPEC（CHK-T 字幕三查）+ V5-REBURN-SPEC（17 镜重烧单）。

## 一、20:59 实跑（DRYRUN=0 · PROXY 模式 · 全 legacy 源）

- final_len computed = **234.25**（target 234.25 · 精确命中）
- 九点 xfade offset 全落词锚：38.81 / 40.20 / 47.49 / 80.18 / 102.83 / 110.47 / 131.68 / 187.24 / 219.83（逐点断言通过）
- loudnorm 两遍 pass1 实测：I=-10.10 TP=+0.90 LRA=5.60
- 单链断言全过（ASSERT-OK：len / sil4 / xf-math / loudnorm / encode）
- PAD-WARN 1 处：E04_replay_faces tpad=1.20s（尾延落 fade 渐隐内 · 块尾延律执行态）
- 产物：`outbound/krea2/30s-reel-v1/full_mv_v5_proxy.mp4`（PROXY 代理剪 · legacy 源混剪 · **禁外发**）

## 二、CHK-T1 字层探针帧多模态验字 — **3/3 PASS**（21:2x · bm-a）

探针帧 = `media/MV/mv0001/kf-demo-20261012/segments/_cut/v5/chk_t/`（装配器自动抽出）

| 帧 | 期望 | 判读 | verdict |
|---|---|---|---|
| title_mid(5.80s) | 歌名卡「爱在西元前」 | 5 字全清 · 宋体衬线 · 深金+光晕+软投影 · 零 tofu 零截断 · 未压主体 | **PASS** |
| s9_mid(43.92s) | 金句「我却在旁静静欣赏你」 | 9 字全清 · 零 tofu 零截断 · 左侧暗带在位（3-4% 宽）；轻擦人物额头/发际 · 未压五官 | **PASS**（选位挂账①） |
| aigc_1s(1.00s) | AIGC 合规标识 | 「AI 生成内容」完整 · 右下角 · 零 tofu 零截断；对比度偏弱（弱水印感） | **PASS**（显著性挂账②） |

**判定：V4「金句层全系未渲染」PTS 病根在 V5 实跑合成流中终验治愈**（单帧 PNG→-loop 1→setpts 窗起平移 三层修复链 · 实跑成片多模态实证）。

## 三、挂账项（17 件到货后消化）

1. s9 金句选位轻擦额头——按实帧复核（TYPOGRAPHY-SPEC §五：INT2 s9904 / S9 实帧定 --x --y 重生成）
2. AIGC 标识对比度偏弱——终版微调不透明度（AIGC 标识办法「显著标识」合规判据）
3. 歌名卡金色饱和度在压缩下略发灰——终版观察项

## 四、正式链（17 件到货后 · 未变）

QC 拼板六检 + E03/E04 女主锚比对板（ID_F_2001 基准）→ `build_full_mv_v5.py`（DRYRUN=0 · V5REDO 源优先）→ PROXY 540p → 导演 PROXY-PASS → 768P 终版 → CHK-E1~E7 + CHK-T → DIRECTOR-REVIEW-V5-PASS → 呈 CEO

—— bm-a · 2026-10-16 21:2x
