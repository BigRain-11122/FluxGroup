# RECEIPT-POOL-0016-night1-latentsync-c2094 — 夜1 LatentSync 口型链正式回执（C2094 补档收口）

- 执行机/窗：bm-c（部署链 C2074-C2083 实绩 + C2094 补档回执与 POOL 闭合）
- 溯源令号：POOL-0016（O-20261015-1655 表演令 + O-20261015-1741 派单令）+ O-20261019-1935 §③（满负荷令·夜窗错峰约束自动失效·立载余项）+ O-20261019-2047 全面开工广播 §2
- **结论：夜1 LatentSync = PASS（v1.5 8GB 档）——三夜链 3/3 全闭合**（夜1 LatentSync + 夜2 LivePortrait L23 + 夜3 MusePose L24 三件全部实绩回执在档）

## 部署链与实测（全部盘面实证·无声称）

1. **部署链五腿全绿**（C2074→C2077→C2079→C2082）：repo 克隆（ByteDance/LatentSync-1.5·gh-proxy 通道）→ deps pip 19/21 --target overlay 零基座污染（insightface fail=NC 红线预期·FaceAlignment 替代 per EL J-30）→ weights dl2 OK 4/4（unet v1.5 **5,072,348,184B** + whisper tiny 75,572,083B + 2DFAN4 96,316,515B + s3fd 89,843,225B·stable_syncnet 1.6GB eval-only 跳过省带宽·verdict=media/latentsync-deploy/weights2_verdict.json）→ patch（tokenizers 0.21.1+future+soundfile 0.14.0+decord ffmpeg shim·六面 IO 冒烟全绿）
2. **trial PASS**（verdict=media/latentsync-deploy/latentsync_trial_verdict.json @16:41:10）：out.mp4 **1,604,658B / 82 帧 / -an 纯画面**（media/latentsync-deploy/trial_c2079/out.mp4）·推理 253s·总 311s·VRAM 起点空闲 10,460MB·**j30_no_insightface=true（零 InsightFace 导入=NC 合规证据）**·82 张脸仿射+还原链净·**82f>16=num_frames 滑窗多窗推理=长片面结构性证明**（长片零 72f 探针需求）
3. **qcboard PASS**（verdict=media/latentsync-deploy/qcboard_verdict.json @17:09:18）：6 IN vs 6 OUT 帧对比板（frames 4/16/28/40/52/70·**latentsync_trial_qcboard_c2082.jpg 554,460B**）——R-stack 卷宗人眼面就绪（导演席可直接复核）

## 档位判读

- 档位=v1.5 8GB 档（16G 卡实测宽裕·18GB v1.6 档未取）·速度=82f/253s≈3.1s/帧（含脸检+仿射+还原全链）·口型贴合证据=qcboard 人眼面
- R-stack（R-20261015-mv-performance-stack）口型行：部署链 verified + trial PASS 在案·「直接可用」终升=导演席过 qcboard 人眼面后落行（证据板在档·非本卡阻塞）
- 银行台账：latentsync-deploy / weights-dl / weights-dl2 / pylibs-patch / trial / qcboard 六单全 done（bm-c-gpu-bank.json 18/18）

## 遗留指针（非本卡阻塞）

- **POOL-0021（Qwen-Image-2.1-Turbo KF 提速试烧）**：本窗已预挂 leg-1 权重下载（银行 p19·qwen21-weights-dl·runner=qwen21_weights_dl_c2094.py）——O-20261019-1935 §③ 序列接续件
- 表演参考片库立项（R-stack 盲区②）= 后续候选 standing

收执：bm-c C2094 EngineTick 窗 2026-10-19 21:5x（本回执=补档性质：trial/qcboard 实绩于 C2082/C2083 完成在盘·正式回执文件与 POOL.json 闭合段本窗补齐上链）
