# KF 生图产线工作流档案（2026-11-15 升级批定稿）

## 档位矩阵（v0.45.0 + torch 2.11.0+cu130 实测验证）

| 档位 | 工作流 | 参数 | 实测 | 质检 |
|---|---|---|---|---|
| 速度档（量产） | wf_dreamshaper_xl_lightning_8steps.json | DreamShaperXL_Lightning 8步 cfg2.0 euler/normal | 9-17s/张 @1-3.5MP | 量产级 |
| 质量档（关键帧） | wf_qwen_image_2512_2steps.json | Qwen-Image-2512 fp8 + Wuli 2steps LoRA + AuraFlow shift=3 + 2步 cfg1.0 | 70s 含19GB冷加载；热跑约10-20s | 8.8/10 A级 |
| 质量备档 | wf_qwen_image_21_turbo_4steps.json | Qwen-Image-2.1 turbo int8 + turbo LoRA 4步 cfg1.0 | 70s 含冷加载 | 8.5/10 |

## Qwen 系官方参数（2512 官方模板背书）
- 负条件：ConditioningZeroOut（turbo 配方）
- 采样：euler / simple，cfg=1.0
- 比例（官方七档）：1328x1328 / 1664x928 / 928x1664 / 1472x1104 / 1104x1472 / 1584x1056 / 1056x1584
- VAE：qwen_image_vae.safetensors（2512 与 2.0/2.1 通用，本地在盘）
- TE：2512 用 qwen_2.5_vl_7b_fp8_scaled；2.1 用 qwen3vl_8b_w4a8（type=qwen_image 均可加载）

## i2v 产线（维持现役配方）
- H3 int4/int8 + turbo 4step：已是上游最新代，参数维持
- H3-Fused-Kernels 插件 A/B 实测：提速仅 3.4%（169s vs 175s）+ 帧差 2.22 超感知阈值 → 判负不入主链
- 四 H3 优化插件定性为备用工具箱（长镜 >10s 困境时试 Long-Sequence/Sage2）

## 权重清单（2512 批新增 30GB，modelscope 国内 CDN 拉取）
- diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors 19.03GB
- text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors 8.74GB
- loras/Wuli-Qwen-Image-2512-Turbo-LoRA-2steps-V1.0-bf16.safetensors 2.2GB
