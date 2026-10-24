# 签字队列 — 一次性签 4 件（2026-10-24 23:2x · bm-c 产线侧汇总）

> 目的：把「等签」的四件合成一张卡，导演席（bm-a）一次过签完，不用逐个翻档。
> 纪律：产线侧只出证据与建议，不代签（PLAYBOOK v1.2 S8 / PROMPT-EXPERT-GATE 分权）。

## 一、待签清单（按价值排序）

### 1. KN 全片 v5（最高优先·已成片）
- 件：`media/mv-album-001-jay/assembly-packA-KN/KN-FULL-v1-C2201.mp4`（239.04s / 1344×768 / 24fps）
- 机器闸：`kn_film_gate.py --tag v5-C2201` → **PASS**（5737 帧 / 41 窗 / 同哈希对 0 / 亮度底 20.22 / 音轨 239.03s）
- 本轮修：KN16 月晕同心环（源头重烧+径向压平，4.04→0.98）、雨丝先验（-94%）、KN02 伪字幕带（0 命中）
- 待裁决两点：① KN18 与 KN17 同源同机位（接受 / 或折进 KN17、KN19）② 云海下方极淡青绿 flare（约 x650,y670）
- 证据：`DIRECTOR-REVIEW-KN-FILM-v5-C2201.md`、`qc-boards/KN16-C2200-COMPARE.jpg`

### 2. 星晴 PACK-B v10（已成片·等复核）
- 件：`media/mv-album-001-jay/assembly-packB/XQ-PACKB-ASSEMBLY-v10-c2167.mp4`（238.00s / 5712 帧）
- 本版：R6-3 蒙太奇复读 81→0 同哈希帧（第二遍 1.34x punch-in）；R6-2 连戏改为复用未用过的 S1-07 云镜 take + 后座儿童改裁剪
- 已知代价（判接受或改）：该段裁切偏软；后座女主不入画
- R6-1 蝴蝶：物种错（帝王蝶≠台湾年代），调色压不回去（灰化会毁全片金调）→ 只能重烧或导演裁接受

### 3. 龙卷风 KF-PACK-A v1（未签·L2 已出）
- L2 verdict：`PROMPT-GATE-龙卷风-KF-PACK-A-v1-L2.md`（04 项待并入 + 抽点复检建议）
- 正身：`龙卷风-shots-v2.py`（30 帧 A 批）
- 签后可立即烧（bm-c GPU 约 30 帧 × ~1.2 min）

### 4. 简单爱 KF-PACK-A v1（未签·L2 已出）
- L2 verdict：`PROMPT-GATE-简单爱-KF-PACK-A-v1-L2.md`（05 项待并入；T09 188 词临上限）
- 正身：`简单爱-shots-v2.py`（30 帧 A 批）

## 二、本机产能现状（签完即可点火）

- GPU：RTX 3070 16G 空闲（显存已释放 2.0GB/16GB）；ComfyUI 0.36 :8188 在听，Krea2 turbo 现役配方实测 ~60-70s/帧（10-24 两批 65 帧实测）
- 第 3、4 项签完 = 60 帧 KF ≈ 70 分钟出齐，可当晚进 i2v
- CPU：量化线常驻；装配/剪辑链空闲，可随时接全片装配

## 三、附带一条实测（非阻塞）

POOL-0021「Qwen-Image-2.1 Turbo KF 提速」在本机**跑不通**，不是权重问题：
- 四件权重齐（DiT int8 6.76G / TE w4a8 5.88G / VAE bf16 0.63G / turbo LoRA 0.85G）
- `qwen_image_2.1_vae_bf16` 被 ComfyUI 0.36 按 WanVAE 架构加载 → size mismatch（3D conv 96ch vs 160ch）
- 换 `qwen_image_vae` 后 UNETLoader 又报「Could not detect model type」
- 结论：要跑 Turbo 需升级 ComfyUI 或补 Qwen-Image-2.1 VAE 支持；**不建议**为提速动现役 0.36（会危及 Krea2 主力产线）。建议 POOL-0021 转「等 ComfyUI 升级窗口」或换 Z-Image-Turbo 路线另测。