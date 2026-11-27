# 本地 TTS 环境现状与处置（2026-11-23 · 音色席）

## 一、已经做成的

| 件 | 状态 |
|---|---|
| GPT-SoVITS 源码 | ✅ `K:\Fluxgroup\.tools\GPT-SoVITS-main`（gh-proxy 直下 6.6MB·348 文件） |
| 预训练权重布局 | ✅ 按代码期望摆好 `GPT_SoVITS/pretrained_models/`（hubert/roberta/s1bert/s2G2333k/v2Pro 全部硬链） |
| 语料分片 v06 | ✅ **14.88 分钟 / 235 段 / f0=169.6Hz（男声）**·过 8 分钟门槛 |
| 语料分片 v04 | ✅ 另一条（含 59.9 分钟单人长段） |
| 文字处理依赖 | ✅ pypinyin/cn2an/jieba/LangSegment/g2p_en/wordsegment/ffmpeg-python/x-transformers/einx/vocos/torchdiffeq |

## 二、卡点（必须隔离环境，不能再往系统 Python 里装）

装 `x-transformers/einx/vocos/torchdiffeq` 时，pip 把**系统 Python 的 torch 顶到了 2.15.0+cpu**，
导致 `torchvision 0.23`（需要 torch 2.8）循环导入失败。

**影响评估（已实测）**：
| 面 | 状态 |
|---|---|
| 音色库产线（faster-whisper / librosa / noisereduce） | ✅ 正常 |
| ComfyUI（独立 `python_embeded`，torch 2.11+cu130 / CUDA True） | ✅ 完全未受影响 |
| GPT-SoVITS TTS 推理 | ❌ 卡在 torchvision 循环导入 |

**结论：生产没坏，只是 TTS 这条路要独立环境。**

## 三、正法（下一步执行）

建**专用 venv**（效仿 sd-scripts 的既有做法）：

```powershell
python -m venv K:\Fluxgroup\.tools\gsv-venv
K:\Fluxgroup\.tools\gsv-venv\Scripts\pip install torch==2.8.0 torchaudio==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
K:\Fluxgroup\.tools\gsv-venv\Scripts\pip install -r K:\Fluxgroup\.tools\GPT-SoVITS-main\requirements.txt
```

> 铁律（本次再次实证）：**永远不要把 TTS/训练类依赖装进 ComfyUI 或系统 Python**。
> 每加一类模型栈 = 一个独立 venv。11-15 那次 ComfyUI 被 Manager 换 torch 掉 CUDA，与本次同族。

## 四、对《一碗面》的影响（不阻塞）

- EP01 先用 **piper / edge-tts 占位音色**跑通全流程（分镜→KF→i2v→装配→闸）
- 声线定版等专用 venv 就绪后，用 v06 语料训出「陈砚」的声线，再重配 EP01 对白
- **自建语料这条路本身合规**（不克隆任何真人演播者），这正是我们换掉有声书方案的原因

—— 音色席 · bm-c · 2026-11-23
