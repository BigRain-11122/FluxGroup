# 男女主 LoRA 运行手册（krea2 · musubi-tuner · bm-c 16G）

> 2026-11-15 建立，同日按实测重写。目标：产出 krea2 LoRA 用于男女主/资产角色跨镜一致性。
> 本机：GPU 16G（krea2 烧片时可用约 12~13G）、RAM 55.9G、Python 3.13。
> **动手前先读 §四 的三条硬结论**，那三条是这一版重写的全部原因。

## 一、现状（逐项有证据）

| 项 | 状态 | 证据 |
|---|---|---|
| 训练框架 | 就绪 | `.tools/vendor/musubi-tuner-main`，含 `krea2_train_network.py` / `krea2_cache_latents.py` / `krea2_cache_text_encoder_outputs.py`；`python -m musubi_tuner.krea2_train_network --help` 在本机 lora-venv 下干净退出 |
| 运行环境 | 就绪 | `.tools/lora-venv`（Python 3.13 + torch 2.11.0+cu130，`cuda avail True`；safetensors/accelerate/transformers 5.17/diffusers 0.40 均在） |
| 基座 DiT | **下载中→已改口径** | `K:\Fluxgroup\.tools\models\krea2\krea2_raw_bf16.safetensors`（24.48GB，来自 **Comfy-Org/Krea-2 未 gated 镜像**） |
| 文本编码器 | 同上 | `K:\Fluxgroup\.tools\models\krea2\qwen3vl_4b_bf16.safetensors`（8.27GB，同仓） |
| VAE | 就绪 | `D:\ComfyUI\ComfyUI\models\vae\qwen_image_vae.safetensors` |
| 数据集体检工具 | 就绪 | `Tools/smoke/qc_lora_dataset.py`（重复度/caption 场景词/触发词三闸） |
| 设定图纸生成器 | 就绪 | `Tools/smoke/gen_cast_sheet.py`（krea2 turbo 多视角直出，GPU 空闲时跑） |
| 三步驱动 | 就绪 | `Tools/smoke/run_krea2_lora.py`（cache → te → train，日志落盘） |

## 二、权重口径（这一节是最容易白跑一天的地方）

1. **官方仓库 `krea/Krea-2-Raw` / `krea/Krea-2-Turbo` 是 gated**：hf-mirror 直连返回 403
   （`"gated":"auto"`，无 token 拿不到）。不要在这两个仓库上反复试。
2. **改用 `Comfy-Org/Krea-2`（未 gated）**，同仓就有全套单文件：
   - `diffusion_models/krea2_raw_bf16.safetensors`（24.48GB，**训练用 RAW**）
   - `diffusion_models/krea2_turbo_bf16.safetensors`（24.48GB，推理/训练中出样）
   - `text_encoders/qwen3vl_4b_bf16.safetensors`（8.27GB）
   - `vae/qwen_image_vae.safetensors`（已有）
3. **ComfyUI 用的 `*_fp8_scaled` 不能直接训练**：实测该文件 686 张量里含 **386 个
   `*.weight_scale`**、权重 dtype 为 `F8_E4M3`；musubi 的 `--fp8_base --fp8_scaled` 是
   在**内存里**把 bf16 权重动态量化（`load_safetensors_with_lora_and_fp8`），
   不是读取 ComfyUI 的量化产物，`strict=True` 加载会因多出的 scale 键直接失败。
4. 下载法：hf-mirror 单连接约 0.7MB/s，分段并行（`K:\Fluxgroup\.tools\dl\seg_dl.py`，
   32MB 一段 × 8~16 线程）可到 2~3MB/s，断线重跑即续（按段文件大小判定）。
   **拼接阶段踩过的坑**：`seg_dl.py` 一开始把被 worker `pop` 空的 segment 列表拿去拼，
   结果拼出 0 字节文件、校验报 `file too short`——分段其实完好，用
   `K:\Fluxgroup\.tools\dl\join_parts.py --parts <out.parts> --out <out>` 几秒就能救回，
   不要重下 8GB。本机 TE（8.27GB/265 段）就是这么救回来的，`safetensors` 实际读取 713 个
   bf16 张量正常。

## 三、命令（全部是本机验证过的形态）

环境：

```bat
set PY=K:\Fluxgroup\.tools\lora-venv\Scripts\python.exe
set SRC=K:\Fluxgroup\.tools\vendor\musubi-tuner-main\src
set PYTHONPATH=%SRC%
```

三步（也可直接用驱动脚本 `Tools/smoke/run_krea2_lora.py`，它把这些都封好了）：

```bat
:: 1) 缓存 VAE latent（这一步同时验证 bf16 DiT 能被加载）
%PY% -m musubi_tuner.krea2_cache_latents --dataset_config <toml> --vae <qwen_image_vae> --batch_size 1 --skip_existing

:: 2) 缓存文本编码器输出（训练本身要用，省显存）
%PY% -m musubi_tuner.krea2_cache_text_encoder_outputs --dataset_config <toml> --text_encoder <qwen3vl_4b_bf16> --batch_size 1 --skip_existing

:: 3) 训练（16G 卡口径）
%PY% -m musubi_tuner.krea2_train_network ^
  --dit <krea2_raw_bf16> --vae <qwen_image_vae> --dataset_config <toml> ^
  --sdpa --mixed_precision bf16 ^
  --timestep_sampling krea2_shift --weighting_scheme none ^
  --optimizer_type AdamW --learning_rate 1e-4 --gradient_checkpointing ^
  --max_data_loader_n_workers 2 --persistent_data_loader_workers ^
  --network_module networks.lora_krea2 --network_dim 32 --network_alpha 32 ^
  --max_train_epochs 10 --save_every_n_epochs 2 --seed 42 ^
  --output_dir <lora 输出目录> --output_name <名字> ^
  --fp8_base --fp8_scaled --blocks_to_swap 26
```

- `--fp8_base` 必须与 `--fp8_scaled` 同用（只用前者会被训练器拒绝：会把 norm 也转 fp8 把模型搞坏）。
- `--blocks_to_swap` 上限 26（28 个主 block 留 2 个常驻）；fp8 下每块约 0.45GB 走 CPU。
- `--timestep_sampling krea2_shift` 是本仓已有选项（`trainer_base.py` 里 97/658 行），
  它按分辨率自动复现 K2 推理时的 time-shift；固定档写法是 `--timestep_sampling shift` +
  `--discrete_flow_shift 2.5`（1024² 的对应值）。
- 本机没有 `adamw8bit`（未装 bitsandbytes），用 `--optimizer_type AdamW`。

## 四、三条硬结论（今天用实测换来的，别再踩）

1. **权重只能从 Comfy-Org 镜像拿 bf16**：官方仓 gated；ComfyUI 的 fp8_scaled 不能训（§二）。
2. **训练集必须先过体检闸**：`mv0002-cast-work/lora-dataset` 两组各 16 张实测重复对
   88%~100%（dHash 中位数 9/256）——是同一张正面像的近重复，训出来只会正面像过拟合。
   证据与处置见 `cph4/fleet/mv0001-handover/DATASET-AUDIT-20261115.md`。
3. **成片关键帧不适合当训练集**：38 张 XQ 关键帧只有 7 张检出人脸。要多样性就用
   `gen_cast_sheet.py` 按设定图纸直出多视角，再用 `qc_identity_cluster.py` 剔离群脸。

## 五、验收判据（不达即停）

1. 第 1 步 rc=0，且数据集旁出现 `*_krea2_*.npz` 缓存——失败先解权重/显存，不进训练。
2. 训练中显存峰值 <15G、系统 RAM <45G（超了先 `POST /free {"unload_models":true}` 卸 ComfyUI 缓存）。
3. 出 LoRA 后同 seed 三档对照（无 LoRA / 0.8 / 1.0）在 ComfyUI 出图，人眼 + 相似度双查；
   崩了先查 caption 是否有场景词、数据集是否又混进近重复。
4. 一轮只改一个变量（rank、lr、epochs 三选一）。

## 六、已知坑

1. musubi 的包在 `src/` 下，`PYTHONPATH` 指 `...\musubi-tuner-main\src` 即可（指到仓库根不够）。
2. `--sage_attn` 不可用（未装 sageattention），用 `--sdpa`；`--convrot_int8` 需要 triton-windows，
   且与 `--turbo_dit` 互斥，本机先走 fp8 路线。
3. 训练与 ComfyUI 抢卡：训练前先 `POST /free`，或直接用 GPU 期的单车道纪律（同一时段只跑一件 GPU 活）。
4. `krea2_cache_latents` **没有 `--dit` 参数**（旧版手册写错了），只要 `--vae` + `--dataset_config`。
5. 会话一断 GPU 长跑就死：训练必须用 `pythonw`/隐藏进程承接并写日志（本仓纪律 D-12 只禁自启任务，不禁人工常驻进程）。
6. **`--device cpu` 走不通**：2026-11-15 实测 `krea2_cache_latents --device cpu` 停在
   `Encoding dataset [0]` + `0it [00:00, ?it/s]`，进程 CPU 占用 0%、两分钟无产物（Windows 下
   DataLoader/编码器没起来）。缓存与训练一律走 GPU；想「不占卡先验一遍」这条路不通。
7. **ComfyUI 的 VAE 能直接用**：`qwen_image_vae.safetensors` 加载时自动
   `Converted ComfyUI AutoencoderKL state dict keys to official format`，`<All keys matched successfully>`。
   推论：同仓（Comfy-Org）出的 bf16 DiT / TE 也应能直接吃，只是**量化档（fp8_scaled/int8_convrot）不行**。
