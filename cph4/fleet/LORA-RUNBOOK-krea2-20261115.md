# 男女主 LoRA 运行手册（krea2 · musubi-tuner · bm-c 16G）

> 2026-11-15 建立。目标：给 `media/asset/faces/CH0x` 的训练集产出 krea2 LoRA，用于男女主跨镜一致性（成片级）；零训练路线用已装的 PuLID 做定妆试镜。
> 本机限制：GPU 16G（可用约 13.4G）、RAM 55.9G、Python 3.13。

## 一、现状（已就绪 / 未验）

| 项 | 状态 | 证据 |
|---|---|---|
| 训练框架 | 就绪 | `K:\Fluxgroup\.tools\vendor\musubi-tuner-main`（含 `krea2_train_network.py` / `krea2_cache_latents.py`） |
| 运行环境 | 就绪 | `K:\Fluxgroup\.tools\lora-venv`（Python 3.13 + torch 2.11.0+cu130，实测 `cuda avail True`） |
| 训练数据 | 就绪 | `media/asset/faces/CH01` 起 8 个角色，各 12 张 1024² + 12 条 caption + RIGHTS.json |
| 基座权重 | **格式未验** | `D:\ComfyUI\ComfyUI\models\diffusion_models\krea2_turbo_fp8_scaled.safetensors`（686 张量、`blocks.N` 原生命名、含 386 个 `_scale`）——musubi 要的是原始 DiT 权重，fp8_scaled 能否直吃要在第一步 cache 时验 |
| 文本编码器 | 待定名 | `qwen3vl_4b_fp8_scaled.safetensors`（ComfyUI 里 krea2 用的就是它） |

## 二、四步命令（按序；每步先看 rc 再看产物）

环境变量（每次都带）：

```bat
set PYTHONPATH=K:\Fluxgroup\.tools\vendor\musubi-tuner-main;K:\Fluxgroup\.tools\vendor\musubi-tuner-main\src
set PY=K:\Fluxgroup\.tools\lora-venv\Scripts\python.exe
set MB=K:\Fluxgroup\.tools\vendor\musubi-tuner-main
```

1) 数据集配置（musubi 用 TOML）：把 CH01 的 12 图+12 txt 指成一份 dataset config，`resolution=[1024,1024]`、`batch_size=1`、`enable_bucket=true`。

2) 缓存 VAE latent（验证基座能不能加载）：

```bat
%PY% %MB%\krea2_cache_latents.py --dataset_config <ch01.toml> --vae %DIT_VAE% --dit <krea2 权重> --vae_chunk_size 32
```

3) 缓存文本编码器输出（省显存，必做）：

```bat
%PY% %MB%\krea2_cache_text_encoder_outputs.py --dataset_config <ch01.toml> --text_encoder <qwen3vl 权重>
```

4) 训练（16G 档建议参数）：

```bat
%PY% %MB%\krea2_train_network.py --dataset_config <ch01.toml> ^
  --dit <krea2 权重> --vae <vae> ^
  --network_module networks.lora_krea2 --network_dim 32 --network_alpha 16 ^
  --resolution 1024,1024 --optimizer_type adamw8bit ^
  --learning_rate 1e-4 --max_train_steps 600 --save_every_n_steps 150 ^
  --mixed_precision bf16 --gradient_checkpointing ^
  --sdpa --convrot_int8 --output_dir <lora 输出目录>
```

## 三、判据（不达即停，不许盲跑）

1. 第 2 步 rc=0 且 `*_krea2_1024x1024.npz` 之类缓存文件落在数据集旁 —— 否则先解权重格式问题，不要进训练。
2. 训练中显存峰值 < 15G；RAM < 40G（超了先卸 ComfyUI 模型缓存：`POST /free {"unload_models":true}`）。
3. 出 LoRA 后用同一 seed + 同一提示词在 ComfyUI 跑 3 张对照（无 LoRA / LoRA 0.8 / LoRA 1.0），人眼与相似度双查；对不上的先查 caption 是否混入场景词。
4. 一个角色一轮只调一个变量（rank 或 lr），不许同时改三样。

## 四、已知坑（写死在这里，别再踩）

1. `krea2_train_network.py` 的 import 链会拉 `hv_generate_video` → 必须有 `torchvision`。
2. musubi 的包在 `src/` 下，`PYTHONPATH` 必须同时含仓库根与 `src`，否则 `import musubi_tuner` 失败。
3. `sageattention` 未装（`--sage_attn` 不可用），用 `--sdpa`。
4. 训练期间不要与 ComfyUI 抢卡：先 `POST /free`，或改用 gpu_lease 仲裁。
5. caption 必须剔场景词（`against blurred cityscape` 这类会把背景学进 LoRA）——CH01 现有 caption 已按人物属性写，别再加环境。
