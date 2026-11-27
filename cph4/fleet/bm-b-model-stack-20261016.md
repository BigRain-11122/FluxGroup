# bm-b 8G 模型栈落地回执：MiniMax-H3 量化视频 + Z-Image/Qwen 生图三栈（2026-10-16 01:3x · bm-b 会话）

- 依据：CEO 令「去 github 找 8G 显存能跑的 minimax 量化和生图模型，要最新的好的高赞的」+「你自己决策 别问我 科学调研 理性决策」。
- 研究结论（GitHub/HF/ModelScope 当日实抓，代理报告已复核）：①**MiniMax 生图模型不开源**（官方 37 仓实证：H3 视频/Music3/M2 系 LLM，无生图仓，生图纯 API）；②MiniMax-H3 视频量化生态完整且**本机已在役**（53/53 animatic 批=H3 int4 480P 实证）；③8G 生图落双栈：Z-Image-Turbo（Tongyi-MAI **12,094★**·Artificial Analysis 开源第一）+ Qwen-Image-2.1（QwenLM **8,407★**·7B·原生 2K/RGBA/10 图编辑）；④MiniMax LLM（M2.5/M3）量化存在但 20GB+，8G+16G 内存机不可行；⑤FLUX.2-klein-4B（Apache 备胎）记档未拉。

## 三栈冒烟实证（多模态像素级验收全 PASS）

| 栈 | 量化档（磁盘） | 冒烟参数 | 实测 | 验收 |
|---|---|---|---|---|
| Z-Image-Turbo t2i | int8_convrot DiT 5.91G + fp8_mixed TE 5.37G + VAE 0.32G | 1024²·8步·cfg1·res_multistep/simple·shift3·CLIP type=lumina2 | **20s**·556KB | PASS 贴纸基准样张级（零崩坏/风格三要素全中） |
| MiniMax-H3 i2v | int4 DiT 15.7G + nvfp4 TE 14.6G + fp16 视频 VAE（原有在盘）+ 新增 int8 VAE 2.68G + fp32 音频 VAE 0.58G | 864×480·124帧·4step turbo（既有 wf_h3_i2v_480p_int4.json 原样复用） | **150s**·606KB | PASS animatic 基准级（镜头/动态/量化伪影全过） |
| Qwen-Image-2.1 t2i | turbo int8 DiT 6.92G + w4a8 TE 6.02G + VAE 0.64G + turbo LoRA 0.87G | 1024²·8步·cfg1·euler/simple·QwenImage21Cache(auto)·TextEncodeQwenImage21 | **20s**·1611KB | PASS 8G 回归基准级（建筑几何/植被/小型生物三类高频崩坏全过，int8 无可感知劣化） |

- 落点：产物=Tools\comfy\smoke-out\{smoke_z_image.png, smoke_qwen21.png, smoke_h3_i2v.mp4}；工作流=smoke_wf_z_image.json / smoke_wf_qwen21.json（参数已固化可复现）；驱动=smoke_models.py / smoke_q.py；窗口=smoke_window.ps1 / qwen_window.ps1（自含闸门+自动复役 flash）。

## 架构与安装事实

1. **双盘架构**：生产 0.36 便携版（8198·animatic 产线）**未动**；新增 v0.40.0 并行便携版（Tools\v040_stage\ComfyUI_windows_portable·8199·Qwen-2.1 专属节点 TextEncodeQwenImage21/QwenImage21Cache 需 ≥0.38）。
2. **权重零拷贝**：v040 通过 extra_model_paths.yaml 共享 0.36 的 models 树（本夜新增 ~40G 权重单份存放）。
3. 下载通道：ModelScope resolve 直链 + gh-proxy（v0.40 包 1.9G）。磁盘 C: 余 428.5G。

## 许可红线（商用必读）

- Z-Image-Turbo = **Apache-2.0** ✓ 可商用。
- **Qwen-Image-2.1 = qwen-research（非 Apache！研究代理的 Apache 说法有误）**——游戏素材商用前必读 LICENSE 全文。
- MiniMax-H3 = MiniMax Community License（地域限制+商用门槛，MV 商用发布前过法务）。

## 坑录五条（今夜实弹，全已根治）

1. **共享日志锁**：`curl 2>>$log` 重定向在 curl 存活期长持句柄→并发后台任务对该日志全部写入失败、静默假死（TE 任务 5 连重试全 IOException 实锤）——并发任务必须各用独立日志文件。
2. **ModelScope 并发连接零速挂起**：3 路并发中 2 路连上但 0 字节挂死（--retry/--connect-timeout 均不覆盖「已连接零流量」）——大文件下载必带 `--speed-limit 10240 --speed-time 30` 断流守卫+外层循环重试。
3. **后台任务 exit 0 ≠ 成功**：下载脚本 GIVE-UP 分支也 exit 0——成败以日志 OK 行+实际文件尺寸为准，禁信退出码。
4. **闸门取整坑**：尺寸阈值用 MB 单位又 `Round(,2)` 取整→2KB 小文件门槛永远 0.00<0.001 不过（窗卡 16 分钟实锤）——闸门比较用原始字节值，勿先取整。
5. **杀进程自匹配**：按命令行子串匹配杀 powershell 会吃到自己的执行壳（rc=255 半途死实锤）——精杀一律按 PID。

## 观察备忘与后续可选件

- 哨兵 01:1x 起 state=PROBE_ERR（pyCpu=-1/pool=unknown，非本会话引入；ollama=OK·无 IDLE/CRIT flag·无实害）——候下次会话排查。
- H3 新增 10 运镜 embedding 已入 models\embeddings（bullet_time/four_seasons/truman_show 等，drama 线可用）。
- 可选件记档未拉：H3 Fun ControlNet Union int8 4.3G（控镜）、ref2va 角色锁、Qwen PE 提示词增强器 t2i/i2i 各 6.4G、Qwen 平版 int8 DiT（25 步质量档）、Z-Image fp4_mixed TE（更低显存档）、GGUF 全家（ComfyUI-GGUF 节点未装）。
- 8G 产线能力面更新：**生图 20s/张·双栈**（Z-Image 量产主力/Qwen 2K+RGBA+编辑特化）+ **H3 i2v 150s/5s 片**（480P animatic）——车道派工可即取用。
