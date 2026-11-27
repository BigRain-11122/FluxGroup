# MV 角色 LoRA 前置门（RUNBOOK v1）

> CEO 令 2026-11-03：**以后 MV 开始前，先把男女主和路人的 LoRA 烧出来；周杰伦的可以一直更新，直到最稳。**
> 工具：`Tools/lora_pipeline.py`（extract / build / train / gate / probe / status）｜台账：`cph4/fleet/mv-lora/LORA-REGISTRY.json`

## 一、工序位置（硬门）

```
定妆照(20-30张)  →  训 LoRA  →  过 gate  →  出关键帧(KF)  →  i2v  →  剪辑
```
LoRA 不过 gate 不许进产线：`python Tools/lora_pipeline.py gate --name <角色> --ref <定妆照目录> --dir <试烧图目录>`
gate 口径＝SFace 余弦相似度 ≥0.40 的产物图占比 ≥80%；阈值与 `Tools/mv_shot_gate.py` 共用一处定义。

## 二、三个角色各自的规矩

- **男主（jman，长期）**：一条跨曲复用。只用人像素材训（官方照/原版 MV 帧）。**AI 生成帧只用于验收，禁止回灌训练**——回灌会把生成的缺陷学进权重。
- **女主（每支单训，换人不换调）**：CEO 令＝每支换人，且换受众记得住、心里有位置的那种。落地＝从年代 DNA 四型池（甜感／清冷／文艺／灵动·正身 `canon/FEMALE-LEAD-ERA-DNA-v1.md`）挑一型，**必须与上一支不同型**；同型内也不复用同一张脸（换种子/换 ID 块）；记忆点每支只押一个（齐刘海／泪痣／笑眼／丸子头），不堆。素材来自本支定妆组图，**不从成片抽**（v721 全片只有 1 帧脸宽达标）。轮换台账＝`LORA-REGISTRY.json → casting_rotation`，开工前先查。
- **路人（长期）**：`crowd2001` 群像 LoRA + 固定 4 个群演身份（extras_a..d），跨曲复用；路人不承担受众认同。

## 三、跑一条新 LoRA

```bash
# 1 素材：从视频/目录抽候选脸（拼板落在 cph4/fleet/queue-receipts/lora-sheet-<name>.jpg）
python Tools/lora_pipeline.py extract --src <视频|目录> --name <角色> --trigger <触发词> \
       --windows 52:56,116:120 --fps 2 --min-face 0.10 [--ref <定妆照>]
# 2 建库：校验 ≥15 张 → 生成 dataset_<name>.toml + train_<name>.bat
python Tools/lora_pipeline.py build --name <角色> --epochs 12
# 3 训练（本机夜窗，工作日 09:00-19:00 让路 CEO 用机）
python Tools/lora_pipeline.py train --name <角色>
# 4 验收
python Tools/lora_pipeline.py gate --name <角色> --ref <定妆照目录> --dir <试烧图目录>
```
先 `probe` 查片：`python Tools/lora_pipeline.py probe --src <视频> --fps 1` → 按身份列出出现帧数与最大脸帧，用来挑定妆帧。

## 四、夜间训练开机前置（缺一即停）

1. `D:\FluxGroup-Offload\15-training\models\krea2\raw\krea2_raw_bf16.safetensors`（24.5GB）
2. `...\text_encoder\qwen3vl_4b_bf16.safetensors`（8.3GB，只影响训练中出样图）
3. VAE `D:\AI\comfyui-krea\...\models\vae\qwen_image_vae.safetensors`
4. ComfyUI 先 `/free` 卸模型，GPU 显存留 ≥11GB

## 五、实测坑（复用前先读）

- **YuNet 会把石刻/浮雕当人脸**（v721 83s 石碑被聚成"一个身份"）→ 素材挑选必须人眼看拼板。
- **probe 的 A 脸（26 帧）是男主**，不是女主；别按"帧数最多"直接认人。
- **素材少就训不出人脸**：15 张只够验通路，20-30 张才定版；同一镜头连抽帧会被 dHash 去重成 1 张，多切时间窗才有量。
- **训练配方**（12GB 已跑通）：`--fp8_base --fp8_scaled --blocks_to_swap 26 --block_swap_h2d_only --block_swap_ring_size 1 --split_attn --gradient_checkpointing --gradient_checkpointing_cpu_offload --sdpa --timestep_sampling krea2_shift --network_dim 32 --network_alpha 32`。
- **LoRA 文件名以盘上为准**：现役是 `jman_v1_rank32.safetensors`；旧文档里的 `jman_v1_640_rank32_final.safetensors` 不存在，接上去 ComfyUI 报 HTTP 400。