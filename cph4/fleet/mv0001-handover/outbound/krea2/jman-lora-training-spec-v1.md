# jman LoRA 训练规格 v1（O-20261009-2330）

> CEO 令：「本地好好去训练一个周杰伦的lora，让以后能固定好角色」+「训练素材要找好的，不要乱七八糟的都来！」+「只要周杰伦年轻时候的」
> 执行机：bm-a（RTX 4070 SUPER 12GB · 内存 94GB）· 执行窗：2026-10-10 00:1x 起

## 1. 路线定谳（深研结论）

- **训练器 = musubi-tuner**（kohya-ss 官方，`krea2_train_network.py` Krea2 原生支持）。
  - ai-toolkit 在 12GB 上必 OOM（多位实测，学习环环崩）→ 弃。
  - 官方推荐工作流 = **RAW 底模训练 → Turbo 推理**（蒸馏权重训不了，LoRA 跨 RAW/Turbo 通用是官方背书路线）。
- **权重三件**（全部 sha256 校验 MATCH）：
  - DiT：`Comfy-Org/Krea-2` → `krea2_raw_bf16.safetensors` 26.28GB（未门禁仓直连）
  - 文本编码器：同仓 `qwen3vl_4b_bf16.safetensors` 8.88GB
  - VAE：本地复用 `qwen_image_vae.safetensors`（与 Qwen-Image 同 VAE）
- **12GB 实跑配方**（4070 12GB 博主验证 + 官方文档）：
  `--fp8_base --fp8_scaled`（两件必须同给）+ `--blocks_to_swap 26`（28 块上限 26）+ `--block_swap_h2d_only --block_swap_ring_size 1 --split_attn` + `--gradient_checkpointing --gradient_checkpointing_cpu_offload` + `--sdpa` + adamw8bit lr 1e-4 + `--network_dim 32 --network_alpha 32`（模型作者推荐默认）+ `--timestep_sampling krea2_shift`（变分辨率桶训练对齐推理 schedule）。
- 显存腾挪：ComfyUI `/free` 卸载 + MiniGameOllama 双任务 disable + 停 llama-server（训完按序恢复）。

## 2. 数据集（质量门执行实录）

- **CEO 质量令执行**：原版 MV 119 帧三轮多模态 QC（糊/闭眼/字幕压脸/背影/空镜/多人全弃）→ 24 张；官方照 12 张入筛、多轮 QC 后弃 5（重复红帽特写 4 + 字幕暗帧 1）→ **终版 32 张**。
- 三时期覆盖：2001 原版 MV 帧（范特西时期·主）+ 八度空间 2002 官方照 bd_1-4 + 叶惠美 2003 yhm_3 + 范特西海报 web_9/ceoref/refmain9。
- 裁切：字幕带裁 0.885 / 特写保全帧+TELEA 修复式擦字幕 / 小脸按人脸框扩裁（2.6-1.2 阶梯）/ 官方照 logo 水印区裁除。
- **判例**：选择性亮度蒙版 inpaint 会误伤下巴高光成涂抹 → 大区域全蒙版也留痕 → 与下巴重叠的文字**裁不掉就弃图**（web_1/bd_5/refclose1/web_5 四张全弃=宁缺毋滥）；poster 标题字散布多块，单框假设不可靠。
- 打标：trigger=`jman` + 逐张英文描述（姿态/光线/年代/景别），无艺人名字符串；`num_repeats=8` → 32×8=256/epoch。

## 3. 训练配置

- `dataset_jman_v1.toml`：resolution [512,512] + enable_bucket + bucket_no_upscale=false + batch 1
- 16 epochs（≈4096 步）· 每 2 epoch 存档（8 档）· seed 42 · 输出 `outputs/jman_v1/jman_v1_rank32`
- 预缓存：latents（全 32 入桶 ✓）+ qwen3vl 多层 hidden states（TE 缓存后训练环不载 TE）

## 4. 验收与接入

- 训后把 LoRA 拷入 ComfyUI `models/loras/`，产线 turbo 工作流加 `LoraLoaderModelOnly`（strength 0.6-1.0 扫档）。
- 验证网格：4 正典场景 × strength {0, 0.8, 1.0} × 固定 seed → LOOKBOARD 呈 CEO 定版。
- **发布安全三件不变**：AIGC 显著标识 + 文案永不提「神似 XXX」+ 反向测试留档（正典触发词=jman 中性词，提示词面零真名）。
- 门检：CEO 眼感定版（「像不像」类目标以 CEO 眼为最终门，自检分仅参考）。

## 5. 复用速记（下次角色 LoRA 直接套）

下载链=HF 直连 Comfy-Org 未门禁仓；装配=uv sync --extra cu128；数据集 QC=拼板多模态分拣+bbox 定位+裁切；训练=本规格 12GB 配方；TELEA 修复只用于小字幕、宁可弃图不硬修。
