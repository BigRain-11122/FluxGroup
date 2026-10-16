# R-20261016-drama-sfx-tts-deploy-01 — 漫剧音效/BGM 音源清单 + IndexTTS-2 bm-b（RTX 3070 8G·Windows）落地 runbook

> 溯源：AI 漫剧部门工具研究 round-2·只补 round-1 未盖双缺口（令：音源清单 + TTS 落地）。
> **查重边界**：round-1 两件已覆盖面本件不重研、只引用——①`R-20261015-drama-oss-stack-01.md`（中文 TTS 选型已定：IndexTTS-2=主力 24.5k★·bilibili 许可；口型/i2v/角色一致性/装配 15 仓五门全量在册）；②`R-20261015-drama-industry-01.md`（行业面：六道工序 SOP/分账/合规拼图）。本件 Part A=音源（round-1 未涉）·Part B=IndexTTS-2 落地 runbook（round-1 只到选型未到部署）。
> 验证声明：Part A=search_audio_lib MCP 共 15 轮免费搜索（**零下载·零积分消耗**·每类 1-2 轮定向+复查，未做目录穷举）；Part B=上游 index-tts/index-tts 仓库 main 分支源码逐件直读（README.md / pyproject.toml / webui.py / indextts/infer_v2_5.py / indextts/utils/model_download.py / LICENSE·raw.githubusercontent + cdn.jsdelivr.net 双道抓取）+ ModelScope API / hf-mirror API 实抓 JSON（权重体量）。本机实查（2026-10-16·glob `**/index-tts*`、`**/webui.py`、`**/drama-tools/**` 扫 C:\Fluxgroup 与 E:\Fluxgroup 全盘）：**drama-tools/repos/ 目录不存在=克隆批未执行**——B 部分基于上游源码实读并如实标注，runbook 第 1 步即克隆补齐。
> 消费方：bm-b 循环班（download_audio_lib 取用批 + IndexTTS-2 落地执行）·drama-dept-v1 DRAMA-PRODUCTION-SYSTEM D5 配音站 · 席位⑫（合规自审）。

---

# Part A · 漫剧音效/BGM 音源下载候选清单

## A.0 池卡实读与「喂」法定位（POOL-0018/0019）

**池卡实读**（源：`C:\Fluxgroup\FluxGroup\cph4\fleet\dispatcher\POOL.json` L212-243·bmb-work-registry.json W009 关联行）：
- **POOL-0018** = whisperX 词锚批：41 曲词级时间戳 → `anchors/<曲>-words.json`·lane=@bm-b cpu-audio-anchors（24/7·与 GPU 零抢）·输入=**bm-a 盘 `cph4/fleet/mv-album-001-jay/audio/` 320k mp3**（Taildrop 拉取·audio-inbox 候场·音源待达态）。
- **POOL-0019** = allin1 结构锚批：41 曲 BPM/beats/downbeats/段落标签 → `anchors/<曲>-structure.json`·与 0018 同批音源共用。
- **判读**：两卡的「音源」= 自有 41 曲 MV 曲目（bm-a 待推送），**不是**本清单对象；锚批处理的是「歌曲」→ 产剪辑锚点。
- **本清单定位**：漫剧线 D5 配音合成工序的**环境/音效/BGM 三层铺底音源**（行业 SOP R-20261015-drama-industry-01 §三工序⑤「配音合成=对白+环境+音效+口型」中的环境与音效两料）——与双锚批同属 bm-b CPU 音频面姊妹件（锚批=内容/节奏轴分析，本清单=成片合成铺底料）。取用经济性同律：search 免费 → 候选清单（本件）→ 实际下载那一步才计积分（每组首下计费·重复免费）。

## A.1 八类 12 组「下载候选清单」（正选·供 download_audio_lib 一步取用）

> 时长 150s 长垫虽 is_loop=false，漫剧单集 60-90s 可直铺全场；标 ✓loop 组为无缝循环底噪，可任意拉长。zip 体量为全组体积。

| # | 类别 | 组名（主题） | audio_id | 时长 | loop | clips/格式 | zip | 漫剧用途 |
|---|---|---|---|---|---|---|---|---|
| 1 | 雨夜氛围·小雨 | Light Rain | `6ad0e778ff9a710affee21a7` | 150s | ✗ | 1·wav | 25.3MB | 静谧雨夜戏底噪（思念/独白场景） |
| 2 | 雨夜氛围·室内 | Heavy Rain From Inside | `6ad0e775ff9a710affee21a1` | 150s | ✗ | 1·wav | 25.3MB | 室内戏窗外暴雨（音色隔窗闷感） |
| 3 | 雷声 | Heavy Rain Thunder & Lightning | `6ad0e78dff9a710affee21cd` | 150s | ✗ | 1·wav | 25.3MB | 暴雨雷电高潮戏/转场惊变 |
| 4 | 城市夜环境 | AMBIENCE_City_Street_Calm_Day | `6ad0e87cff9a710affee23a3` | 12.1s | ✓ | 1·wav | 2.0MB | 城市街道循环底噪（夜感=后期 EQ 压暗，见 A.5 缺口注） |
| 5 | 人群嘈杂·大厅 | AMBIENCE_Public_Hall_Chatter | `6ad0e87dff9a710affee23a9` | 17.5s 总 | ✓ | 2·wav | 2.9MB | 群戏/大厅人群交谈循环垫 |
| 6 | 人群嘈杂·餐厅 | AMBIENCE_Restaurant_Chatter | `6ad0e87eff9a710affee23ab` | 3.8s | ✓ | 1·wav | 0.6MB | 餐馆/酒楼内景人群（国风漫剧常用） |
| 7 | 心跳·全变体包 | Heartbeat_Pulse | `6ad0e986ff9a710affee2c91` | 18.2s 总 | ✓ | 14·wav | 1.6MB | 紧张/悬疑打底：9 常规+5 loop 变体一包打尽（性价比最高） |
| 8 | 心跳·紧张长段 | SFX_HeartBeatPulsingTensionLong | `6ad0fe02ff9a710affeeb3a9` | 13.1s | ✗ | 1·wav | 2.4MB | 单段连续紧张心跳床（前 3 秒钩子/悬念卡点用） |
| 9 | 脚步·水泥行走 | FOOTSTEP_Concrete_Walk | `6ad0e977ff9a710affee2c51` | 6.8s 总 | ✗ | 19·wav | 0.6MB | 城市行走逐镜配步（19 变体防重复感） |
| 10 | 脚步·草地奔跑 | FOOTSTEP_Grass_Run | `6ad0e97aff9a710affee2c5d` | 18.5s 总 | ✗ | 51·wav | 1.7MB | 追逐/逃亡戏（最大变体包·山野场景） |
| 11 | 车门·开 | CAR_Door_Open | `6ad0ea69ff9a710affee3535` | 3.5s 总 | ✗ | 3·wav | 0.3MB | 上车戏（3 变体） |
| 12 | 车门·关 | CAR_Door_Close | `6ad0ea68ff9a710affee3533` | 1.3s 总 | ✗ | 2·wav | 0.1MB | 下车/离场戏（与 #11 成对取用） |

**BGM 正选 1 组**（第 13 位·复古类库内无正主，见 A.5）：

| # | 类别 | 组名 | audio_id | 时长 | loop | clips | zip | 用途 |
|---|---|---|---|---|---|---|---|---|
| 13 | BGM·影视氛围 | Nordic Title | `6ad10ad4ff9a710affeeff4f` | 124.3s | ✓ | 1·wav | 20.9MB | 片头/氛围垫乐（无缝循环·单集 60-90s 直用） |

**合计：13 组（八类全覆盖·含 BGM 1 组）·zip 总量 ≈107MB·audio_id 已验唯一**。取用命令样例：`download_audio_lib audio_id="6ad0e986ff9a710affee2c91"`（本任务未执行任何下载）。

## A.2 备查组（不入正选·按需加取）

| 组名 | audio_id | 时长/loop | 说明 |
|---|---|---|---|
| Heavy Rain & Thunder Urban | `6ad0e789ff9a710affee21cb` | 150s ✗ | 城市雨雷变体（与 #3 互补带城市场景感） |
| MUSIC_EFFECT_Solo_EPiano_Negative | `6ad0e9d4ff9a710affee2f6d` | 48.3s 总·16 clips | 复古电钢 stinger 包（转场情绪小句·库内最接近「复古质感」件） |
| FOOTSTEPS_Asphalt_Trainers_Walk_Slow_x | `6ad0e96fff9a710affee2c17` | 5.0s ✓loop | 沥青路慢走循环（夜巷尾随戏备用） |
| AMBIENCE_Parking_Garage_Car_Boot_Sale | `6ad0e87dff9a710affee23a7` | 20.4s 总·3 clips ✓ | 旧货市集人群（市集/庙会场景备用） |

## A.3 预听直链（TOS 签名短链·**1h 有效**·过期后按 audio_id 免费重搜即得）

- 直链内嵌 VolcEngine 临时签名 AK，2026-10-16 01:48 已全部过期作废；按仓库安全律不入库——预听按 A.2 表 audio_id 免费重搜即得。


## A.4 短剧向免版权 BGM 外站盘点（三查=许可/国内可达性/活跃度·2026-10-16 本网实测）

| 站点 | 许可（查） | 国内可达性（查） | 结论 |
|---|---|---|---|
| **Pixabay Music** | Pixabay Content License：**商用免费·免署名**；禁原样转售/单独分发当素材卖（条款摘要页 /service/license-summary/ 本次抓取被重定向至曲库页=细节待二次核，取用前逐曲看 LICENSE 标） | ✅ 实测可达（本网直抓成功） | **主选**：29 万+曲·实测页面含 suspense/horror/cinematic/phonk/old-school/synthwave 检索面=短剧张力+复古向最对口 |
| **incompetech**（Kevin MacLeod 影视配乐老牌） | CC-BY 4.0：免费商用·**需署名**（知识基线·本次抓到的是站点公告非条款页·逐曲核） | ✅ 实测可达（2026-08 仍在更博=活跃） | 备选：影视情绪曲海。**注意其 2026-04-02 公告：Spotify/YouTube Content ID 存在误标案例**——平台发布遇 claim 按授权方（Frequency）申诉流程走 |
| **Bensound** | 免费档需署名（Bensound License·每曲带 LICENSE 链）·Pro 付费免署名（档位页本次未展开=待核） | ✅ 实测可达（2012-2026 活跃） | 备选：检索面实测含 Suspense/Dramatic/Music for Film/Trailer Music + SFX 区 |
| **FreePD** | 公版（CC0） | ✅ 可达但**已关站** | ❌ **判负**：首页公告「2008-2025·permanently closed·服务已永久下线」——**公有领域免署名攻略失效，从候选除名**（负面结论入库：网上旧攻略引用 FreePD 的一律作废） |
| **Musopen**（公版古典·年代戏 BGM 正源） | 公版古典乐/录音（免费+会员双轨） | ❌ 实测 403 Forbidden | 可达性判差：如需公版古典（民国/年代戏配乐）走代理，或改 Pixabay classical 检索面 |

- **GitHub 侧判负**：无「高星免版权 BGM 曲库仓」——BGM 资产主体在站不在仓（与 round-1「漫画分镜无成熟开源件=自建」同构）；GitHub 只贡献工具面（MoneyPrinterTurbo/moviepy 已在 round-1 §一.5 盖章，本件不重研）。
- 国内站提醒：爱给网等「会员免商用」模式权利链不清（知识基线·常识判断）——正式商发剧不采，平台备案审核过权源时免麻烦。

## A.5 库内缺口判负（如实记·搜索零命中实证）

1. **无「夜晚」专属城市环境组**：`夜晚 night 环境音` 检索 100 命中无一含夜标注——城市夜环境以 #4 街道循环底噪（日景采样）+后期 EQ 压暗/加蝉虫替代；后续可补搜 frog/crickets（虫鸣）组。
2. **无真「复古 BGM」组**：music 事件 `复古`/`复古 怀旧`/`vintage 爵士 慢`/`BGM 循环` 四连零命中；music 长曲实有=Nordic 系 4 支（Title/Grand/Ambient/Frozen 2'36"）+Deep_In_Space+Cave 系（氛围向）+MUSIC_EFFECT 钢琴/电钢 stinger 包——复古（80s/港风/爵士）缺口走 A.4 外站（Pixabay old-school/synthwave 检索面）。
3. **horror 事件内无心跳**：`心跳`（horror）零命中；心跳实际索引在 other/horror 混布（无事件检索 21 命中定位到 A.1 #7/#8）——后续按 event 检索注意。

---

# Part B · IndexTTS-2 在 bm-b（RTX 3070 8G·Windows）落地 runbook

## B.0 状态声明（本地仓库核查·如实记）

- 令文指定实读路径 `C:\Fluxgroup\FluxGroup\media\drama-tools\repos\index-tts\`：**全盘核查不存在**（`media/` 下仅 `drama-pilot-out/`；`**/index-tts*`、`**/webui.py`、`**/drama-tools/**` 在 C:\ 与 E:\ 两盘均零命中）——round-1 §四建议克隆清单 15 仓克隆批**未执行**（W009 报告亦未生成·bmb-work-registry W009 仍 open）。
- 本 runbook 改基**上游 main 分支源码逐件实读**（见溯源声明六件），源码态=IndexTTS-2.5 发布后主线（pyproject version 2.0.0·README News 2026/08/10 2.5 发布行）；克隆步骤列为 runbook 第 1 步，克隆后源码与本文引码如有 drift 以仓库为准。
- 官方唯一渠道警示（README CAUTION 原文）：仅 `github.com/index-tts/index-tts` 为官方仓，他站非官方（round-1 已录原 bilibili 组织迁移，取件认准 index-tts org）。

## B.1 版本与 Python/依赖要求（pyproject.toml 实读）

- **版本**：`indextts` 2.0.0·主力 **IndexTTS-2.5**（README 默认·2026/08/10 发布·推理比 2 更快+zh/en/ja/es/ar 五语+语速 duration_factor 0.5-2.0×+拼音/CMU/假名注音）；IndexTTS-2 为兼容备选（`--version 2`）。
- **Python**：`requires-python = ">=3.10,<3.12"`——**uv 自动安装并管理项目 Python**（README：「automatically creates a `.venv` project directory and installs the correct versions of Python and all required dependencies」），**项目内独立 .venv=天然满足「独立 venv·勿用 comfy 的 python_embeded」**；README IMPORTANT 原文：跑 uv 命令**勿手动激活任何其他环境**（防依赖冲突）。
- **核心依赖**（dependencies 节摘）：`torch==2.8.*` + `torchaudio==2.8.*`（Linux/Windows 走 `pytorch-cuda` index **cu128**，pyproject `[[tool.uv.index]] url="https://download.pytorch.org/whl/cu128"`）、`transformers==4.52.1`、`modelscope==1.27.0`、`librosa==0.10.2.post1`、`numpy==2.2.6`、`numba==0.63.0`、`openai-whisper`、`jieba/cn2an/g2p-en`、`ffmpeg-python==0.2.0`、`omegaconf/einops/safetensors/sentencepiece/tokenizers==0.21.0`；**文本正则化 Windows 用 `wetext>=0.0.9`**（Linux 才用 WeTextProcessing——pyproject 平台标记 `sys_platform != 'linux'`）。
- **extras**：`webui = ["gradio==5.45.0"]`；`deepspeed = ["deepspeed==0.17.1"]`（**Windows 难装，跳过**——README IMPORTANT 原文「Windows: DeepSpeed may be difficult to install. You can skip it by removing the --all-extras flag」）；`accel = ["flash-attn==2.8.3.post1", "triton-windows==3.1.0.post17; sys_platform=='win32'"]`（可选加速）；`torch_compile`（triton-windows 同源·可选）。
- **CLI 入口**（pyproject `[project.scripts]`）：`indextts = "indextts.cli:main"`、`indextts2 = "indextts.cli_v2:main"`（uv tool install 后可用）；旧 `infer_cli.py` 已随 v1.5 时代归档（README Legacy 节指向 `archive/README_INDEXTTS_1_5.md`），main 现役脚本入口=`indextts/infer_v2_5.py`（见 B.4）。
- CUDA 报错排障（README IMPORTANT 原文）：装期遇 CUDA error→确认系统 **CUDA Toolkit 12.8+**（仅 deepspeed/flash-attn 编译路径需要；最小路径 torch cu128 轮子自带运行时，免装 Toolkit）。

## B.2 安装步骤（uv 路线·README Getting Started 直译+bm-b 本地化）

```bash
# 1) 克隆（bm-b 本地化路径：drama-tools/repos/ 目录树自建）
git clone https://github.com/index-tts/index-tts.git C:\Fluxgroup\FluxGroup\media\drama-tools\repos\index-tts
cd C:\Fluxgroup\FluxGroup\media\drama-tools\repos\index-tts
#    （GitHub 慢道备选：ghproxy 类镜像前缀拉取；LFS 已不需要——README：示例音频首次启动按需下载，Git LFS no longer required）

# 2) 装 uv（任一可用 python 即可，uv 自管项目 Python）
pip install -U uv

# 3) 依赖（Windows：只加 webui extra，勿用 --all-extras=跳过 deepspeed）
uv sync --extra webui
#    国内慢道二选一（README 原文）：
uv sync --extra webui --default-index "https://mirrors.aliyun.com/pypi/simple"
uv sync --extra webui --default-index "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
#    → 自动生成仓库内 .venv（独立环境·与 comfy python_embeded 零接触）
```

## B.3 权重下载（ModelScope 优先）与体量（ModelScope API + hf-mirror API 实抓·2026-10-16）

**下载命令**（README §3 原文·ModelScope 优先=本网实测 huggingface.org 直连不通、modelscope.cn 通）：

```bash
uv tool install modelscope-hub
modelscope download --model IndexTeam/IndexTTS-2.5 --local_dir checkpoints
#  IndexTTS-2 备选：modelscope download --model IndexTeam/IndexTTS-2 --local_dir checkpoints_2
#  HF 备道：uv tool install "huggingface-hub" && （$env:HF_ENDPOINT="https://hf-mirror.com"）hf download IndexTeam/IndexTTS-2.5 --local-dir=checkpoints
```

**体量实抓**（IndexTeam/IndexTTS-2.5 仓库文件表）：

| 文件 | 字节 | 体量 | 用途 |
|---|---|---|---|
| gpt.pth | 3,259,599,833 | ≈3.04 GiB | GPT 主干（0.8B 参数） |
| codec.pth | 607,290,935 | ≈579 MiB | 语义 codec |
| s2mel.pth | 414,908,601 | ≈396 MiB | s2mel 声码链 |
| multilingual_zh_ja_yue_char_del.tiktoken | 907,395 | ≈0.87 MiB | 多语 tokenizer |
| wav2vec2bert_stats.pt + feat1/2 + config.yaml | <1 MiB | 微 | 统计/配置 |
| **核心运行权重小计** | | **≈4.02 GiB** | webui 启动校验五件套=webui.py REQUIRED_FILES["2.5"] 全列 |
| qwen0.6bemo4-merge/model.safetensors | 1,192,135,096 | ≈1.11 GiB | QwenEmotion 文本→情感向量（0.6B） |
| **仓库总量**（API usedStorage） | 5,485,798,498 | **≈5.11 GiB** | 全仓拉取口径 |

**辅助模型**（首次启动 `ensure_models_available()` 自动下到 `checkpoints/hf_cache/`·`model_download.py` 实读：`need_proxy()` 网络探测**自动切 ModelScope**，ModelScope 失败兜底 `hf-mirror.com`——源码内置国内可达路径，bm-b 免手工干预）：

| 辅模 | 源（ModelScope 映射·源码 HF_TO_MODELSCOPE_REPO_MAP） | 实抓体量 |
|---|---|---|
| w2v-bert-2.0（语义特征） | facebook/w2v-bert-2.0 → `AI-ModelScope/w2v-bert-2.0`（全仓 snapshot） | model.safetensors 2.16 GiB + conformer_shaw.pt 2.17 GiB ≈ **4.65 GiB** |
| BigVGAN 声码器 | nvidia/bigvgan_v2_22khz_80band_256x（仅 config.json+bigvgan_generator.pt 两文件） | ≈**428 MiB** |
| MaskGCT semantic codec | amphion/MaskGCT（semantic_codec/model.safetensors 单文件） | 待首跑实测（估 0.1-0.3 GiB） |
| CAMPPlus 说话人特征 | funasr/campplus → `iic/speech_campplus_sv_zh-cn_16k-common` | 待首跑实测（估 ~30 MiB） |

**磁盘预算**：权重 5.11 + 辅模 ≈5.3 + .venv(torch cu128 系) ≈6 + 余量 → **预留 ≥20 GiB**。

## B.4 推理入口实码（三通道）

**① WebUI**（`webui.py` 实读·argparse 全参）：
```powershell
uv run webui.py            # IndexTTS-2.5 默认；http://127.0.0.1:7860（--port 7860 --host 0.0.0.0 默认）
# 全参：--verbose --port 7860 --host 0.0.0.0 --model_dir ./checkpoints --version {2.5|2}
#       --fp16 --deepspeed --cuda_kernel --accel --torch_compile --qwen_emo --gui_seg_tokens 120 --share
# v2：uv run webui.py --version 2 --model_dir ./checkpoints_2
```
启动自动链（源码）：缺件自检 REQUIRED_FILES→`snapshot_download(MODEL_REPO[version])` 自动补权重→`ensure_config_available()` 下 config.yaml→`ensure_examples_available()` 下示例音频——**首启即自动完成 B.3 辅模全下载**。

**② CLI 脚本**（`indextts/infer_v2_5.py` `__main__` 实读·README Python API 节同源）：
```powershell
$env:PYTHONPATH="."
uv run indextts/infer_v2_5.py --cfg_path checkpoints/config.yaml --model_dir checkpoints --prompt_wav examples/voice_01.wav --text "台词" --lang ZH --output gen.wav
# argparse：--cfg_path / --model_dir / --prompt_wav / --text / --lang(ZH) / --output(gen.wav) / --text_normalization
```
⚠ **8G 卡注意（源码实读）**：该脚本硬编码 `IndexTTS2(..., use_bf16=True, use_qwen_emo=True)`——qwen_emo=True 会加载 1.11 GiB 情感模型，8G 显存见 B.5；OOM 时改走 ① 或 ③。

**③ Python API**（README 原文·漫剧批量产线正道）：
```python
from indextts.infer_v2_5 import IndexTTS2
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", use_bf16=True, use_qwen_emo=False)
tts.infer(spk_audio_prompt="prompts/角色A.wav", text="台词", lang="ZH", output_path="d5/wav/ep01_a001.wav",
          emo_vector=[0, 0.8, 0, 0, 0, 0, 0, 0], use_random=False, verbose=True)  # 8 维情感向量
```
- 情感向量序（infer_v2_5.py `normalize_emo_vec` 注释原文）：`[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`（喜/怒/哀/惧/厌恶/低落/惊喜/平静）；内置偏置 `[0.9375, 0.875, 1.0, 1.0, 0.9375, 0.9375, 0.6875, 0.5625]`、总和>0.8 自动缩放——webui 滑条同源。
- 情感控制四式：参考音频同情绪（mode0）/情感参考音频（mode1·emo_alpha 0.65 默认）/情感向量（mode2）/情感描述文本（mode3·**需 use_qwen_emo=True**·8G 默认不可用）。
- 语速：`duration_factor=0.5-2.0`（>1 变慢·<1 加快·2.5 专属）；注音：`他在银<行|XING2>里…`（pinyin.vocab 全表）。
- 参考音频自动截 15s、重采样 22.05k/16k；推理结束打印 RTF（源码 print 行）。

## B.5 显存档位配置（8G 卡可行路径·源码实锁）

- **webui.py 自动档**：`LOW_VRAM_THRESHOLD_GB = 10.0` → `detect_vram_gb()` 实测 3070 8G <10G → `LOW_VRAM=True` → ① `HALF_PRECISION` 自动开：2.5 走 `use_bf16 = HALF_PRECISION and torch.cuda.is_bf16_supported()`——**3070（Ampere）支持 bf16**（不支持时源码自动回落全精度并打印）；② `LOAD_QWEN_EMO = qwen_emo or not LOW_VRAM` → **QwenEmotion 默认跳过**（省 1.11 GiB；情感文本 mode3 不可用，强行开启加 `--qwen_emo`，8G 勿开）。
- **infer_v2_5.py 自动档**：`__init__` 内同阈值 `<10.0` → `self.low_vram=True`（源码打印「Low-VRAM mode enabled…long text will be split into chunks」）→ `infer()` 遇 `len(text)>40` 自动按标点切 ≤40 字/段逐段生成、200ms 静音间隔拼接——**峰值显存不随文本长度涨**。
- **显存构成估算**（按实抓权重量级推算·待首跑实测验证）：bf16 GPT ≈1.6G + w2v-bert fp32 ≈2.3G（源码不降精度加载）+ codec ≈0.6G + s2mel ≈0.4G + BigVGAN fp32 ≈0.45G + CAMPPlus 微 ≈ **权重底 ≈5.4G**+上下文/激活 ≈6.5-7G 峰 → **8G 可跑（webui 默认档）**；+QwenEmo fp16 +1.2G ≈ 8.2G → 越线，故 CLI 脚本（硬编码 qwen=True）在长文本时有 OOM 风险，8G 批量产线走 ③ 自写 API 关 qwen_emo。
- **速度基准**（README 实测表）：RTX 4090·2.5 bf16·kv_cache=True·RTF=0.2065（≈5× 实时）——3070 推算 RTF ≈0.4-0.7（**待 bm-b 实测**）；漫剧单集台词 30-60s→单集配音生成 <1 分钟级，30 集日更无压力。
- **webui 高级参数默认**（源码）：do_sample=True·top_p 0.8·top_k 30·temperature 0.8·num_beams 3·repetition_penalty 10.0·max_mel_tokens 1500·分句 token 120（建议 80-200·源码 info 原文）。

## B.6 bm-b 10 步落地清单（RTX 3070 8G·Windows·PowerShell）

1. **盘检**：目标盘预留 ≥20 GiB；`nvidia-smi` 驱动就绪（CUDA 12.8 兼容驱动版）；ffmpeg PATH 缺则临时补（W009 自检记录：`MiniGame\Tools\ffmpeg` 在盘）。
2. **克隆仓库**：`git clone https://github.com/index-tts/index-tts.git C:\Fluxgroup\FluxGroup\media\drama-tools\repos\index-tts`（目录树自建；GitHub 慢道走镜像前缀）——同时补齐 round-1 克隆清单 15 仓欠账的第一仓。
3. **装 uv**：`pip install -U uv`（系统任一 Python 即可，项目 Python 由 uv 自管 3.10-3.11 档）。
4. **依赖**：仓库根 `uv sync --extra webui`（**勿 `--all-extras`**=Windows 跳 deepspeed；慢道加 `--default-index https://mirrors.aliyun.com/pypi/simple`）→ 项目内独立 `.venv`（与 comfy python_embeded 零接触）。
5. **下权重（ModelScope 优先）**：`uv tool install modelscope-hub` → `modelscope download --model IndexTeam/IndexTTS-2.5 --local_dir checkpoints`（5.11 GiB·本网实测 ModelScope 直达）。
6. **GPU 自检**：`uv run tools/gpu_check.py`（应识别 3070/CUDA·README §4 原命令）。
7. **首启 WebUI**：`uv run webui.py` → `http://127.0.0.1:7860`；首启自动补辅模至 `checkpoints/hf_cache/`（w2v-bert 4.65 GiB+BigVGAN 428 MiB+MaskGCT codec+CAMPPlus；源码 need_proxy 自动走 ModelScope）——**首启窗即辅模下载窗，一次性等完**。
8. **8G 档位确认**：控制台应见「Low-VRAM mode enabled (8.0 GB < 10 GB)」行+bf16 生效打印；**不加** `--qwen_emo`/`--fp16`（2.5 用 bf16 自动）；长台词确认自动分句打印。
9. **批量产线**：③ Python API 写 `drama_voicegen.py`（use_qwen_emo=False·emo_vector 控情感·duration_factor 控语速）逐集批量；CLI ② `infer_v2_5.py` 单发验证可（硬编码 qwen=True·长文 OOM 则回退 API）。
10. **验收+登记**：出三件套=①60-90s 集台词样带（单 RTF 行留档）②三情感向量对照（喜/哀/惧各一）③拼音注音一例；License 红线登记 B.7 入装配线合规自审。**执行窗纪律**（W009 §二同律）：GPU 生成让路 MV 全速令、首烧候 MV 波次间隙错峰；POOL-0020 烧机通过前保守期不并跑重 GPU 批（TTS 属轻 GPU 档·影响面小）。

## B.7 License 红线（LICENSE 原文直读·bilibili Model Use License Agreement）

- **商用门槛（§2.2）**：上月**月活 >1 亿** 或 上年**年营收 >10 亿元人民币**（任一触发）→ 须另行书面授权；**未触发=本协议直接商用**——本队规模远低于双门槛，**漫剧配音商用无障碍**（与 round-1 红线 2 同源·本件核到原文数字：MAU 100 million / revenue RMB 1 billion）。
- **模型改进禁令（§3.4 c 原文）**："You may not Use the bilibili indextts2 or any Derivative Work to improve any AI model, except for the bilibili indextts2 itself, its Derivative Works, or non-commercial AI models." → **红线：禁止用其权重/输出训练或改进其他商业 AI 模型**；例外=改进 indextts2 自身/其衍生/非商业模型（即微调 indextts2 做角色音色=允许·属 Derivative Work）。**角色音色固化线继续走 GPT-SoVITS（MIT·round-1 正位）不碰此限**。
- **随附义务（§3.4 a/b）**：分发 Derivative Work 须在发布页/文档附免责声明（原文模板在条款内）；每份拷贝保留版权声明+本协议副本。
- **内容合规（§4.1 c/d）**：模型与产出不得违反使用地法律（生成内容红线与 16 号令 AIGC 标识/备案合规叠加——见 R-20261015-drama-industry-01 §六）。
- **高风险场景禁用（§4.2）**：医疗诊断/自动驾驶/军事/关键基础设施/大规模生物识别监控/自动决策——漫剧线不涉。
- **其他**：§5.3 对 bilibili 发起知产诉讼=许可自动终止；§6 中国法+上海仲裁；**§9 中英文本冲突以中文版为准**（商用争议前以中文版精读为准）；商务合作 indexspeech@bilibili.com。

---

## 结论应用表（research-protocol 强制）

| 结论 | 落点 | 消费方 |
|---|---|---|
| Part A 13 组下载候选清单（八类音效+1 BGM·≈107MB·audio_id 齐） | download_audio_lib 取用批 + DRAMA-PRODUCTION-SYSTEM D5 音源库建库 | bm-b 循环班 · drama 会话 |
| POOL-0018/0019 池卡判读（锚批输入=41 曲自有曲目·待 bm-a Taildrop 推送；本清单=漫剧 D5 铺底料姊妹件） | 双锚批承接序（audio-inbox 到达链） | bm-b 循环班 |
| FreePD 已关站判负+incompetech Content ID 误标风险 | 音源 SOP 免署名清单除名 + 平台发布 claim 申诉预案 | 席位⑫ |
| 库内两缺口（无夜专属城市环境/无真复古 BGM）+外站主选 Pixabay | D5 音源库补采序 | drama 会话 |
| **repos/ 克隆批未执行**（全盘零命中实证） | 克隆欠账台账（round-1 §四 15 仓·首仓=index-tts） | bm-b 会话 · W009 |
| IndexTTS-2.5 8G 档源码实锁（<10G 自动 bf16+跳 QwenEmo+长文自动分句；CLI 脚本硬编码 qwen=True 有 OOM 风险→批量走 API） | bm-b 落地 10 步 + D6 配音站执行正身 | bm-b · 席位⑧ |
| 权重体量表（核心 4.02 GiB+qwen 1.11 GiB+辅模 ≈5.3 GiB·盘预算 ≥20 GiB） | bm-b 盘位规划 | bm-b |
| bilibili 许可红线原文核（MAU>1 亿/年收>10 亿需另行授权；禁改进其他商业模型·中文版为准） | CHARTER §三 skill 律 + 装配线合规自审（与 round-1 红线 2 合并正身） | 席位⑫ |
