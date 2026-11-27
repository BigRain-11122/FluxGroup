# R-20261016-8g-draft-ecosystem — 8G 草稿/轻量生态（CEO 令 2026-10-16 分层分配·波3）
> 溯源：CEO 令 2026-10-16「务必去github上好好调研和看最新的，8G显存虽然少，但适合轻量业务或者草稿，不要一票否定」·消费方=委员会 C-20261016-01 bm-d 六卡机分层分配定谳案·判据=Q1 GitHub 生态盘点/Q2 草稿车道判定/Q3 sm_61 特判
> 验证声明：实读 20 次（帽 22：网页抓取 9·搜索 9·GitHub 工具 2）·成源 23 条（A=11/B=1/C=8/M=3·其中 NVIDIA RN/NVIDIA dev blog/pytorch issues/OneDiff wiki 共 4 条 A 为官方页搜索摘要直引，余 A 全文本会话直读）·失败面：deepbeepbeep/Wan2GP 404（仓已迁 deepbeepmeep/WanGP）；GitHub search_repositories 解析失败×1；GitHub search_code 解析失败×1（降级 raw 源码直读命中）；ggml 根 CMake 无 arch 行（改读 src/ggml-cuda 子文件命中）·改判指令来源=CEO 令 2026-10-16「8G 勿一票否定」
## 一、GitHub 8G 低显存生态盘点（Q1）
- a) ComfyUI 生态：city96/ComfyUI-GGUF 4.2k★·Apache-2.0·193 commits·活跃 [A：仓页直读]——原文"DiT models…seem less affected by quantization…much lower bits per weight…on low-end GPUs"+T5 量化"further VRAM savings"；预置 flux1/SD3.5 GGUF，Wan GGUF 同机制加载 [A]
- b) 视频低显存：deepbeepmeep/WanGP 10.5k★·1854 commits·极活跃（v18.10=2026-10-15）[A：仓页直读]——原文"run select models with as little as 6 GB of VRAM"／"Older Nvidia GPU support: use GTX 10XX, RTX 20XX, and newer cards"／Docker GPU 表"Supported GPUs: …GTX 10XX, Tesla V100, A100…"／专设"MANUAL INSTALLATION: (FOR GTX 10XX)"=torch 2.7.1+cu128·Python 3.10.9／"SageAttention 2 requires an Ampere-or-newer GPU; GTX 10XX should use SDPA"／CUDA13 升级注明"FOR NON GTX10XX USERS"／v17.17"only 5-6GB of VRAM to gen 15 seconds of H3 video at 480p"。Lightricks/LTX-Video 11.1k★·Apache-2.0·活跃 [A]——2B distilled="light VRAM usage"；社区 LTX-VideoQ8"720x480x121 in under a minute on RTX 4060 (8GB VRAM)"（Q8/FP8 内核限 Ada）；Wan 1.3B GGUF 档 4-6GB [C：willitrunai]·"8GB VRAM entry point" [C：canirun]
- c) SD 优化仓：OneDiff（siliconflow/onediff）官方 wiki 原文"supports acceleration for Compute capability >= 8.0"→P104 与 V100 双判负 [A：官方 wiki]；SD1.5 低显存实证：GTX 1070 8GB fp16 占用~3.7GB [C：localmodel.run]·512² 批 3 约 30s [C：Reddit]；SDXL/Flux 低显存主轮=ComfyUI-GGUF（见 a）
- d) llama.cpp/Pascal：主线 ggml/src/ggml-cuda/CMakeLists.txt 源码直读——CUDA<13 默认 arch 含"50-virtual 61-virtual 70-virtual"（原文注"61 == Pascal, __dp4a instruction"）；CUDA≥13 默认剔除 50/61/70 [A：raw 源码直读]；ik_llama.cpp 3.3k★·MIT·5068 commits·活跃至 2026 [A]——原文"fully functional and performant…CUDA (Turing or newer, but…recent progress on bringing Pascal and Volta up to speed)"→对 Pascal=追赶态、主线仍是首选；社区速度锚：GTX 1060 6G 7B Q4_0=27.79 t/s [C：bestllmfor]·双 P104 跑 32B Q4 仅 2.5-3 t/s（模型超显存 offload 拖累·"CUDA 数量太少"）[C：知乎]；P104+Ollama 本地部署有中文全流程实证 [C：CSDN]
- e) faster-whisper：SYSTRAN 25.9k★·MIT·活跃（v1.1.0 基准）[A：仓页直读]——GPU 栈原文"cuBLAS for CUDA 12 + cuDNN 9"（README 未列算力下限）；8G 档基准（RTX 3070 Ti 8GB）：13min 音频 large-v2 fp16 1m03s/4.5GB·int8 59s/2.9GB·batched int8 16s [A：README]；whisper.cpp=同 ggml-CUDA 栈，sm_61 态随 d) 联动 [A-推理]
## 二、草稿车道判定矩阵（Q2·四态+速度预估）
| 车道 | 判定 | P104 速度预估 | 卡点 | 证据级 |
|---|---|---|---|---|
| a) MV 关键帧 672×384 试构图（对位正片=Krea2 fp8@1344×768 跑 bm-c 3070 16G） | 草稿档适合 | SD1.5≈10-15s/图（672×384 像素量≈512²）；SDXL Q4 GGUF 慢一档·推测 40-80s | fp16 算术 1:64 慢路径→fp16 存储+fp32 计算；注意力走 SDPA | C+推测 |
| b) 480P i2v 视频草稿（对位 bm-b 3070 8G INT4 实证） | 待证：限 Wan 1.3B 档可试·5B/14B 档判负边缘→V100 兜底 | 无 Pascal 一手锚；对位：4060 8G Q8 480P<1min [A]·14B 低显存 offload≈15min/段（更强卡）[C：civitai]→P104 1.3B 480P 5s 片推测 5-15min | bf16 默认权重须转 fp16/fp32（显存×2）+Sage2/Triton 判负+GGUF dequant 慢 | C/推测 |
| c) SD1.5 512² 透明底占位图批产（现役=ComfyUI 本地线平移） | 正档适合（P104 最稳车道） | ≈10-15s/图 [C]→夜间批产约 250-350 图/时/卡（推测） | 基本无·老卡 SD1.5 成熟生态 | C+现役同栈 |
| d) qwen 4B/8B Q4 常驻（B站自动回复/初筛/校对） | 正档适合 | 1060 锚 27.79 t/s(7B Q4_0) [C]→P104 推测 8B Q4≈30-45 t/s·4B Q4≈60-90 t/s（前提全入显存） | llama.cpp 须 CUDA12.x 自编（默认含 sm_61 [A]）；模型超 8G 即落 2.5-3 t/s 深渊 [C：知乎] | A/C+推测 |
| e) Real-ESRGAN/像素级上采样草稿档 | 草稿档适合 | "Even a GTX 1060 works" [C：insiderllm]→512→2048 推测 10-30s/图 | 基本无·CNN fp32 可跑·ncnn/Vulkan 另有旁路 | C+推测 |
## 三、sm_61 特判与兜底清单（Q3）
- 底座三律：①CUDA 12.x 保留 sm_61；CUDA 13.0 已移除 Maxwell/Pascal/Volta 离线编译与库支持 [A：NVIDIA 13.0.1 RN+dev blog 摘要·llama.cpp CMake 行为独立佐证]；②PyTorch 官方帖（2025-07-14 直读）：cu128/129 自 2.8 删 Maxwell/Pascal（Volta 重入）、2.11 起 cu128 删 Volta、cu126 轮至 2.14 止——官方帖 2026-09-04 标题" CUDA 12.6 wheels will no longer be published from PyTorch 2.15 (drops Maxwell / Pascal / Volta)" [A]；③llama.cpp 主线 CUDA<13 默认含 61-virtual（P104 LLM/STT 底座成立）[A：源码]
- P104 硬判负清单：OneDiff（CC≥8.0）[A]｜SageAttention 2/flash-attn 类加速（Ampere+；GTX 10XX 官方退路=SDPA）[A：WanGP 引文]｜Triton/torch.compile GPU 加速（WanGP Triton 表仅 RTX 20XX+）[A→推理]｜PyTorch cu128/129/130 轮与 2.15 起全线官方轮 [A]｜CUDA 13 工具链 [A]｜bf16 权重栈直跑 [推理]｜fp16 算术 1:64（sm_61 通病·GP100 除外）[M：NVIDIA Prog Guide 指针·本会话未直读]
- V100 单卡兜底清单（sm_70·16G·fp16 TC·无 bf16）：480P 视频草稿（WanGP 官方 GPU 表含 Tesla V100 [A]）｜SDXL/1344×768 试构图直跑｜faster-whisper large-v3（fp16 TC·3070Ti 锚外推≈3-6× 实时·推测）｜LLM 14B-32B Q4 常驻｜基线同锁 CUDA12.x+torch cu126≤2.14（2.11 起 cu128 亦无 Volta [A]）；OneDiff/Sage2 于 V100 同判负 [A]
## 四、结论面（P104 草稿层定位建议）
1. CEO 改判成立：「8G 勿一票否定」获 GitHub 一手证据支持——P104(Pascal sm_61) 在 2026 生态有官方级支持面（WanGP 明列 GTX 10XX、llama.cpp 默认 arch 含 sm_61、faster-whisper CUDA12 栈、Real-ESRGAN 老卡可用），定档「轻量常驻+平面草稿」层；但不可拿 bm-b 3070(Ampere) 实证冒充 Pascal 判定，视频车道仍以 V100 兜底为正解。
2. 三卡分工建议：1×qwen 4B/8B Q4 常驻（B站自动回复/初筛/校对·推测 30-90 t/s）+1×SD1.5 512² 占位图夜间批产+1×STT/上采样/试构图杂务池；480P i2v 归 V100 16G（fp16 TC+容量），P104 仅限 Wan 1.3B 档试验性承接。
3. 软件基线锁死（P104/V100 同律）：CUDA 12.x（禁 13）+PyTorch cu126 ≤2.14（2.15 起停发须锁旧版）+llama.cpp 主线自编；WanGP 走官方 GTX 10XX 路径（torch 2.7.1+cu128 test 轮）。
4. 风险与校准：P104=矿卡（PCIe 电气弱+CUDA 核少·知乎实测泼冷水 2.5-3 t/s@32B）→上机先跑 llama-bench/sweep-bench 校准，一切预估取保守下限；32B 级禁上 P104。
## 五、结论应用表
| 结论 | 落点 | 状态 |
|---|---|---|
| P104 判「轻量常驻+平面草稿」档·四车道可用（LLM 常驻/SD1.5 批产/上采样/STT），非一票否决对象 | 决策呈报 C-20261016-01 | 接线中 |
| 480P 视频草稿：P104 限 Wan 1.3B 档待证·5B/14B 归 V100 兜底（WanGP GPU 表含 V100/GTX10XX） | 决策呈报 C-20261016-01 | 待证 |
| 软件基线锁 CUDA12.x+torch cu126≤2.14+llama.cpp 自编（P104/V100 同律·2.15 起停发） | 决策呈报 C-20261016-01 | 已闭环 |
| OneDiff(CC≥8.0)/Sage2(Ampere+)/Triton=P104 与 V100 双判负清单 | 决策呈报 C-20261016-01 | 接线中 |
- 更新记录：T0 骨架落盘 → T1 Q1a/Q1b 部分 → T2 Q1b/e 收口 → T3 Q1c/d+Q3+Q2 主体 → T4 终稿 35 行（Q2 b/e 收口+结论面+应用表）
- 防线二：两承重主张（WanGP"Older Nvidia GPU support: use GTX 10XX"、llama.cpp 默认 arch 含 61-virtual）均为本会话仓页/raw 源码全文直读非摘要传话；NVIDIA CUDA13 移除面为搜索摘要直引（另有 llama.cpp CMake 源码行为独立佐证），建议验收方按 P-65 复抽 NVIDIA 13.0.1 RN 一条
