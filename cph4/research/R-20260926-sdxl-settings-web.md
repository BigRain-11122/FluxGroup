# R-20260926-sdxl-settings-web — SDXL 本地设置/模型/参数外部调研（web 检索·硅基城市城市级宽幅道）
> 溯源：CEO 令「研究 sdxl 本地大模型各种设置、模型、参数等技巧，测出适合生产硅基城市的高效高质稳定输出」·消费方=FluxVerse 美术产线（MiniGame C 6/6 实证配方→城市级宽幅扩展）·判据预注册=Q1 参数正典/Q2 模型生态/Q3 效率路径
> 验证声明：2026-09-26 执行·网页读取 20 次（16 成读+2 abort+1 hf-mirror 重定向实测+1 DDG 验证码拦截）·成源 26 条（A=6：SDXL 论文 abs/全文·HF base/refiner/Lightning/Turbo 卡·Hyper-SD arXiv 2404.13686；B=4：ComfyUI 官方示例直读+docs.comfy.org·blog.comfy.org×2 快照指针；C=16：社区教程/Reddit/HF 讨论）·另 6 项标 M·失败面见第五节末

## 一、SDXL 参数正典（Q1）
- CFG：社区正典 SDXL **5-8**、SD1.5 为 7-11 → SDXL 相对天然低 2-3 档（C·apatero "SDXL works best at 5-8"；C·note.com/artificialguy 同区间）·论文对比样品即 cfg 8.0（A·arXiv 2307.01952 "cfg-scale 8.0"）→ 现配 cfg 6.0 落在正典区间·**确认（C 多源+论文旁证）**
- sampler/steps：**DPM++ 2M Karras·20-30 步**为 2025-2026 社区验证主流（C·note.com "DPM++ 2M Karras, 20-30 steps, CFG Scale 7-8"；C·artificialguy/digitalgamerhub 同款）→ dpmpp_2m+karras 仍是首选、28 步在区间·**确认（C 多源）**；>30 步边际收益线无外部数字源·🟡待证
- 分辨率 bucket：论文 Appendix I 官方全表——多宽比微调「pixel count as close to 1024² as possible…multiples of 64」（A）·**宽幅 1344×768（1.75:1）与 1536×640（2.4:1）均为官方训练 bucket**（A）·ComfyUI 官方示例点名「896x1152 or 1536x640 are good resolutions」（B·官方示例页直读）→ 16:9 主力 1344×768（较真 16:9 偏差 1.6%）、超宽 1536×640·**确认（A/B 双源）**；总像素勿超 1,048,576（C·reddit sdxl_resolution_cheat_sheet）
- size conditioning：c_size=(h_orig,w_orig)+c_crop=(top,left) 经 Fourier 嵌入并入时间步嵌入，推断时 crop 设 (0,0)（A·论文 §2.2/§2.3）→ 宽幅必须走 CLIPTextEncodeSDXL 注入 target_size·**确认（A 官方机制原文）**
- base+refiner：论文用户研究 refiner 胜率 48.44% vs base 36.93%（A·§2.5·2023 口径）；官方接法 80/20（n_steps=40·high_noise_frac=0.8·A·HF base 卡）·但 2025-2026 社区主流弃用（C·r/comfyui 民调 "majority do not use a refiner"；C·r/SD "hit or miss"）→ 判：不引入·**🟡（弃用=C 源共识，无 B 级定论）**

## 二、模型生态候选（Q2）
- 像素 LoRA 王座：HF 上**无取代 nerijs/pixel-art-xl 的新王**——pixel-art-xl（2023-07-31 v1.0·HF 在库·163MB safetensors）（C·civarchive/aimodels.fyi）仍是被引正典；触发词非必需（"without requiring style prompts or trigger keywords"·C·aimodels.fyi）→ 与集团句首 "pixel art" 触发法相容·**确认（消极结论）**·许可未直读→许可待证（集团已产线在用，沿用既有合规判定）
- 对位候选：artificialguybr/PixelArtRedmond（HF 在库·"crisp retro" 偏复古向·C）；ntc-ai/SDXL-LoRA-slider.pixel-art（HF·滑条式·C）；civitai 独占「V2 HD Pixelized Art」（"blocky, early 90's…to Pixelated PSP"·正中 HD 像素化需求）与「Pixo」（Illustrious 底模·非 SDXL）→ **civitai 本网络不可达+许可不明→不入推荐位**·仅记侦察名单
- 赛博城市 LoRA：HF 在库四候选 mnemic/CyberpunkWorldXL-SDXL-LoRA（搜索快照示 License: gpl-3.0）/jbilcke-hf/sdxl-cyberpunk-2077/issaccyj/lora-sdxl-cyberpunk/BRUHCUH/sdxl-cyberpunk-lora——**质量零实证+三许可待证·全 M·不入推荐位**；另：论文 Fig.6 官方样品即长距黄昏城市景（"Epic long distance cityscape…at sunset"·A）→ base 对黄昏城市景有原生能力
- 通用 checkpoint 2026 共识（C）：写实王者 Juggernaut XL Ragnarok「most versatile photorealism checkpoint」+RealVisXL V5（皮肤/低光/电影感）（C·insiderllm/promptzone）·DreamShaper XL 全用途（C）·RunDiffusion/Juggernaut-XL HF 在库（搜索实证）·许可待证；写实 checkpoint×像素 LoRA 叠加适配度无外部源·🟡；换底=LoRA 配方整体重过 6/6 闸（集团法）
- hf-mirror 实测：hf-mirror.com 模型卡页对 huggingface.co **308 永久重定向**→镜像口径=文件下载端点（HF_ENDPOINT 法）；「HF 在库」即「hf-mirror 下载可得」·huggingface.co 卡页本环境可直读（stabilityai/ByteDance 均成读）·civitai 全域不可达未采

## 三、效率路径（Q3）
- **集团判例验证：「Lightning 交付禁用」获 A 级原文旁证→维持**——官方卡「Use LoRA only if you are using non-SDXL base models. Otherwise use our full checkpoint for better quality」+「1-step…only experimental and the quality is much less stable」+必配 Euler+sgm_uniform·CFG=0（A·HF ByteDance/SDXL-Lightning 卡）→ 像素 LoRA 叠加与其设计用法冲突·**确认**
- Hyper-SD（ByteDance·NeurIPS 2024·arXiv 2404.13686·A）：轨迹分段一致性蒸馏·1-8 步；项目页自比其他 LoRA 加速法（hyper-sd.github.io·C 快照，无量化数字）·社区口碑 1 步「spectacular…very close quality to base sdxl」但 2/4 步分歧（"I prefer sdxl lightning 4 step over 2 and 4 step hyper sdxl"·C·HF discussion/31）→ 侦察道候选·步数×CFG 组合需本机实测·**🟡待证**
- Lightning vs Hyper-SD 汇判（C·aimodels.fyi）：步数专用全 UNet 版 Lightning 质量可胜 LoRA 版·Hyper-SD 一份 LoRA 多步数更灵活 → 两者均只配**侦察道**·交付道维持全步数·**确认（C 共识与集团判例一致）**
- SDXL Turbo：官方卡「generated images are of a fixed resolution (512x512 pix)」+「does not make use of guidance_scale or negative_prompt…guidance_scale=0.0」（A）→ 512 原生+无 CFG+无负面词·宽幅交付道不适用·**负判·确认（A）**
- 12GB 提速正路：①steps 50→20-28+DPM++ 2M Karras（C·digitalgamerhub）②SDPA 注意力后端+fp16（C 同源）③madebyollin/sdxl-vae-fp16-fix 防宽幅 VAE 黑图（C·digitalgamerhub/HF 卡佐证）④VAEDecodeTiled「tiled approach to handle large images efficiently」（B·docs.comfy.org 快照）⑤ComfyUI 2026 新优化 NVFP4/Async Offload/Pinned Memory（B·blog.comfy.org 2026-01 快照）+Dynamic VRAM（B·同站 2026-03 快照）→ fp8 对 SDXL 质量影响无强源·🟡待证

## 四、硅基城市适配建议
- 宽幅定档：城市级 16:9 主力 **1344×768**·超宽横幅 **1536×640**（均官方 bucket·A/B 双源）·生成走 CLIPTextEncodeSDXL 注入 target_size·crop=(0,0)·总像素锁 ~1MP；如需像素级精确 16:9 由 1344×768 裁切收边（推测·待证）；64 倍数幅与像素网格后处理天然对齐（推测·适配推断）
- 配方沿用判定：base+pixel-art-xl@0.8+cfg 6.0+dpmpp_2m/karras+28 步全部落在正典区间（一节）→ 城市级道**不换底·不加 refiner·不走蒸馏**；扩展只做三件事：宽幅 bucket 化+黄昏城市语汇词表+像素后处理网格按新幅重标定（后处理为集团 6/6 自有实证法·非本调研域）
- 城市场景风格：无 HF 实证 LoRA 王者（二节）→ 先以「cyberpunk city skyline, neon signs, dusk/night」自然语汇跑 base 小样（论文 Fig.6 原生城市景旁证·A）；风格强度不足再批侦察轮（HF 四候选+两 checkpoint A/B）
- 提速现实线：量产道 steps 28→20-24 本机 A/B（采样算力按步数线性·28→20 约 -29%·算术推算非源）；侦察道才用 Hyper-SD/Lightning 4-8 步预览（判例维持）
- 闸门不变：一切候选/参数变更入产线前过集团 6/6 资产单元闸·判据不变

## 五、结论应用表（落点四选一：①任务单转办 ②法/文档修改指针 ③决策呈报 ④判负留痕）

| 结论 | 落点 | 状态 |
|---|---|---|
| 宽幅 bucket=1344×768/1536×640+target_size 注入（A/B 双源） | ①任务单转办：产线任务单加「宽幅分辨率规范」条目 | 待接线 |
| 现配方全落正典区间→城市级道沿用·不换底不加 refiner | ②法/文档修改指针：产线配方文档补正典区间与本文出处 | 已闭环 |
| Lightning 交付禁用判例获 A 级原文旁证→维持 | ④判负留痕：判例补 HF Lightning 卡「non-SDXL base models」条款指针 | 已闭环 |
| SDXL Turbo 512 原生+CFG0→宽幅负判出局 | ④判负留痕 | 已闭环 |
| Hyper-SD 4-8 步侦察道（步数×CFG 网格小样实测） | ①任务单转办：侦察道实测任务单 | 待办 |
| 赛博城市 LoRA 四 HF 候选全 M·无王者·仅侦察名单 | ③决策呈报：是否批侦察小样轮预算（四候选×1 轮） | 待 CEO |
| 换底 Juggernaut/RealVisXL 收益无外部证+在库未核全 | ④判负留痕：本轮不换底；如换需整体重过 6/6 闸 | 已闭环 |
| steps>30 边际线·fp8 质量影响·Hyper-SD CFG 均无源 | ①任务单转办：并入侦察道本机 A/B 实测 | 待办 |

- 失败面（如实）：①nerijs/pixel-art-xl 官方卡 2 次 abort+hf-mirror 308→许可未直读（集团已产线在用·沿用既有判定）②RealVisXL_V5/DreamShaper-XL 的 HF 在库性因 DDG 验证码拦截未核③Hyper-SD 各步数推荐 CFG 无原文数字④>30 步边际收益无源⑤非 bucket 分辨率伪影形态无强源⑥civitai 全域不可达→「V2 HD Pixelized Art」等候选无法验质验许可
- 更新记录：T0 骨架落盘（早落盘律）→ T1 Q1（8 读）→ T2 Q2（4 读）→ T3 Q3+hf-mirror 实测（8 读）→ 终稿 48 行·预算 20/20 用尽
- 防线二（集团抽验位）：承重主张①「1344×768/1536×640 为官方训练 bucket」直读 arxiv.org/abs/2307.01952（Appendix I）；承重主张②「Lightning 卡 LoRA 用法限制条款」直读 huggingface.co/ByteDance/SDXL-Lightning
