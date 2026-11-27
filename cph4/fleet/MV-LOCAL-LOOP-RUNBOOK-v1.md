# MV 本地闭环运行手册 v1（bm-c · 2026-11-20）

> **位次：本件是操作速查，不是新法。** 工艺正典仍是 `mv0001-handover/canon/PRODUCTION.md` /
> `AI-EDITING-SPEC-v1.md` / `PERFORMANCE-SPEC-v1.md` 与 `mv-album-001-jay/prompt-writing-spec-v1/`；
> 烧片闸仍是 `PREFLIGHT-GATE-v1.md`（本件的 `drama_kf_batch` 走同一道闸，profile="drama"）；
> 装配质检仍是 `drama_assemble.py` / `drama_quality_gate.py` / `subs_qc.py`。
> 本件只把「在哪台机器上、用什么路径、按什么命令、多快」写清楚，供换班/换机时照抄——
> **它不改变任何工艺判据**（CEO 2026-11-21：之前的规则工作流不要推翻，能用就用）。
>
> 目的：一台机器、零云端，从剧本到成片全链自己跑。
> 全部命令均在本机实测过；未实测的项显式标注「未验」。
> 适用：MV / 漫剧 / 短剧共用同一骨架（D3 关键帧 → D4 i2v → D6 配音 → D7 装配 → D8 闸）。

---

## 〇、硬件与守卫

| 项 | 值 |
|---|---|
| GPU | RTX 3070 16GB（实测 free 16.0GB / 燃烧窗 ~15.3GB 峰值） |
| ComfyUI | `http://127.0.0.1:8188`（`D:\ComfyUI\ComfyUI`，`python_embeded`） |
| 熔断法 | 烧卡前 `POST /free {"unload_models":true,"free_memory":true}`；LLM 与烧卡**不同时占卡** |

**判例**：ComfyUI 空闲时会把 12GB 模型留在显存里 → ollama 请求会**挂到超时**（本窗实测 4B 模型
120 秒无响应）。要跑 LLM 先 `/free`；要烧卡先让 LLM 退出。这不是故障，是显存只有 16GB。

---

## 一、环境清单（本机实况）

| 组件 | 路径 | 状态 |
|---|---|---|
| 出图/出片 | `D:\ComfyUI\ComfyUI` | 在役 |
| 视频模型 | `models\diffusion_models\`：`minimax_h3_*_int4/int8`、`Wan2.2-TI2V-5B-Q4` | 在盘 |
| 图像模型 | `krea2_turbo_fp8_scaled`(12.2G)、`animagine-xl-4.0`、`DreamShaperXL_Lightning`、`qwen_image_2512_fp8`(+2步 LoRA) | 在盘 |
| 文本编码器 | `qwen3vl_32b_minimax_h3_nvfp4_awq`(H3 用)、`qwen3vl_4b_fp8_scaled`(krea2 用) | 在盘 |
| 角色 LoRA | `jman_v1_640_rank32_final`、`jman_lora_v2` | 在盘 |
| 字体 | `K:\Fluxgroup\.tools\fonts\NotoSansCuneiform-Regular.ttf`（OFL） | 在盘 |
| 本地大模型 | `C:\Users\Dasheng\AppData\Local\Programs\Ollama\ollama.exe serve`；`OLLAMA_HOST=127.0.0.1:11434` | 在役 |
| 模型清单 | `qwen3.5:4b-q4_K_M`（快）、`qwen3.5:9b-q4_K_M`、`qwen3-vl:2b`（看图）、`qwen3.8:27b`、`glm-4.7-flash:30b`、`qwen3.6-coder:35b` | 6 个 |
| 中文配音 | `K:\Fluxgroup\.tools\tts-venv\Scripts\piper.exe` + `piper-voices\zh_CN-huayan-medium.onnx` | 在役 |
| 字幕/ASR | `faster-whisper`（python 包）+ `media\voicebank-models\faster-whisper-small` | 在役 |
| 装配 | `ffmpeg`（PATH）+ `Tools/fleet/drama_assemble.py` | 在役 |
| 质检 | `Tools/fleet/drama_quality_gate.py`（七条）、`Tools/fleet/subs_qc.py`（字幕八条） | 在役 |

---

## 二、启动/收工（照抄）

```powershell
# LLM 起
Start-Process 'C:\Users\Dasheng\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve' -WindowStyle Hidden
# 烧卡前释放显存
python -c "import json,urllib.request;urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8188/free',data=json.dumps({'unload_models':True,'free_memory':True}).encode(),headers={'Content-Type':'application/json'}),timeout=30).read()"
```

---

## 三、全链命令（按站）

### D3 关键帧（MV 用 krea2／漫剧用 animagine）

```powershell
# MV：krea2 仿真人（bm-c 必须显式指 fp8 权重，默认名是 bm-a 的 int8 档）
python Tools\mv_kf_batch.py --prompts <prompts.json> --out <dir> `
  --unet krea2_turbo_fp8_scaled.safetensors --clip qwen3vl_4b_fp8_scaled.safetensors `
  --width 1344 --height 768 --steps 8
# prompts.json 契约：[{id, prompt, scene, light, shot, angle, grade, texture}]
# ⚠ mv_kf_batch 的 preflight_gate 用 MV 专用词表（grade∈tw2001/mono/bluefire/nost），
#   漫剧/短剧勿用此脚本，用下面的 drama_kf_batch。

# 漫剧：剧本 → prompt 表 → 面板
python Tools\fleet\drama_kf_plan.py --eps <N|N-M|all>
python Tools\fleet\drama_kf_batch.py --ep <N> --ckpt animagine-xl-4.0.safetensors --width 832 --height 1472
```

### D4 i2v

```powershell
python cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py --repo K:\Fluxgroup\FluxGroup `
  --lane bmc --manifest <manifest.json> --out <dir> `
  --wf cph4/fleet/mv-album-001-jay/local-i2v/wf_h3_i2v_480p_int4.json --timeout 4200
# manifest 契约：{wave,total,total_win_s,units:[{id,frame,src_s,win_s,width,height,i2v_prompt,...}]}
# 低清验证律：先 480P（864×480）过，再 768P 正片；单镜 ≤10s（16G 卡实测墙）
```

### D5 口型（LatentSync）

未接 MV 链路（本机在册但未接入自动命令）——**未验**。

### D6 配音（漫剧/短剧）

```powershell
$env:PYTHONUTF8='1'
& 'K:\Fluxgroup\.tools\tts-venv\Scripts\piper.exe' `
  --model 'K:\Fluxgroup\.tools\piper-voices\zh_CN-huayan-medium.onnx' `
  --output_file out.wav --input_file text.txt
python Tools\fleet\drama_av_manifest.py --ep <N> --mix    # 按时间线混成单轨 + 出字幕
```

### D7 装配

```powershell
$env:ASSEMBLE_ENCODER='libx264'     # Windows 无 videotoolbox
python Tools\fleet\drama_assemble.py --manifest <asm.json> --out <mp4> --qa <qa.json>
```
> Windows 坑（已修，见 `Tools/fleet/drama_assemble.py` L~218）：`ass=...:fontsdir=C:/...` 不加引号会报
> `No option name near '/Windows/Fonts'`。修法=选项值单引号包裹。

### D8 质检

```powershell
python Tools\fleet\drama_quality_gate.py --in <mp4>
python Tools\fleet\subs_qc.py <srt>                      # 字幕八条
```

### 一条命令跑一集（漫剧）

```powershell
python Tools\fleet\drama_ep_chain.py --ep <N> --stages plan,kf,i2v-plan
```

---

## 四、本窗实测基线（拿这些数当参照）

| 动作 | 实测 |
|---|---|
| 漫剧 KF（animagine 832×1472 / 28 步） | **20 秒/张** |
| H3 i2v 480P 3s（73 帧） | **135–150 秒/镜** |
| H3 i2v 480P 4s（107 帧） | **165 秒/镜** |
| piper 中文单句 | < 3 秒 |
| 装配（15s / 1080×1920 / libx264） | 约 20–30 秒 |
| 一集 21 镜（KF+i2v+装配+闸） | **约 1.5 小时** |
| v731 石碑镜（纹理→KF→i2v） | 3 分钟（不含 KF 合成） |

---

## 五、纪律（违反会返工）

1. **低清验证律**：新配方先 480P，过了才 768P。
2. **重烧先归档**：`kf/*.png`、`i2v/*.mp4` 有 SKIP 判据，旧件不归档=命令秒过零产出。
3. **单镜 ≤10s**：超了必炸（16G 卡）+ 必须拆镜（MV 里 10 秒不切本就不合理）。
4. **先验输入再领 GPU 租约**：必败任务不许碰租约（会毒化 2 小时）。
5. **同 checkpoint 连烧**：禁逐镜重载模型。
6. **呈审前过闸**：机器闸红的东西不给 CEO 看。

---

## 六、未接通项（诚实清单）

| 项 | 状态 |
|---|---|
| D5 口型接 MV 链 | 未接（LatentSync 在册未接线） |
| 4K 超分 / 隐形水印 | 工具在 bm-a 侧（`mv_videoseal_wm` 等），本机无 |
| 60fps 插帧母版 | `minterpolate` 方案在 bm-a；本机未接 |
| 云端 | 按 CEO 令：仅辅助，不参与默认链 |

—— bm-c · 2026-11-20

---

## 七、本机环境基线（2026-11-21 重启后实测）

| 项 | 值 |
|---|---|
| GPU | RTX 3070 **16384 MiB**（16GB）· 驱动 621.24 · 重启后空载 2960MiB |
| ComfyUI | **v0.46.0**，`torch 2.11.0+cu130`，`cuda_avail True` |
| 自定义节点 18 个 | H3 全家（CAB-Sampler / Director / Fused-Kernels / Long-Sequence / Low-Memory-Sage2 / Optimization-Suite / Spectrum）· **H3E_IndexTTS2.5** · Krea2T-Enhancer · PuLID · LivePortraitKJ · KJNodes · GGUF · VideoHelperSuite · controlnet_aux · DD-Translation · Manager |
| 模型 | diffusion：H3 int4/int8、Wan2.2-TI2V-5B-Q4、krea2_fp8、qwen_image 2.1/2512、animagine-xl-4.0、DreamShaperXL；LoRA：jman_v1_640 / jman_v2 / H3 turbo-4step / qwen 2step |
| 配音 | piper `zh_CN-huayan-medium`（本地单音色·默认）；**edge-tts 多音色可用**（Yunxi 男 / Xiaoxiao 女 / Yunjian 旁白，1.5–2.3s/句·云端辅助通道） |
| IndexTTS2.5 | 节点已装、**权重未下**（`models/tts` 空）→ 本地多角色音色仍缺 |
| 技能 | 本机 `~/.codely-cli/skills` 已装 MV/漫剧整车：tw-mv-director(更新) · drama-director · bigstream-expert-panel · mv-casting · mv-colorist · mv-edit-rhythm · mv-intent-to-prompt · mv-lighting · mv-performance · mv-props-era · art-critique · gate-rigor · content-recon · agent-librarian |

> 更新纪律（承 11-15 判例）：**ComfyUI-Manager 不要点"更新全部"**——它会连带换 torch，
> 曾把 `2.11.0+cu130` 换成 `2.15.0+cpu`，启动即 `Torch not compiled with CUDA enabled`。
> 升级前先看 `requirements.txt` 里有没有 torch / torchvision 行。

> **2026-11-21 新增判例（krea2 必读）**：krea2_turbo_fp8(12.24GB) + qwen3vl_4b_fp8(4.88GB) ≈ 17.1GB 权重 > 16GB 显存，
> 默认模式跑到第 3 帧会让 **ComfyUI 进程直接消失**（ConnectionResetError 10054）。
> 正法：起服加 --lowvram + 步数 6——实测稳定且更快（22s/帧 vs 60s/帧）。
