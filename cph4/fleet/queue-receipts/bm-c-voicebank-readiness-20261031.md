# bm-c 音色库 CPU 腿就绪度（2026-10-31 00:1x，承 CEO 令「CPU 算力机队都不要浪费，去训练音色库」）

## 结论一句话

bm-c 的 CPU 语料腿**依赖已装好、工具跑得通**，但**两件输入不在本机**：BV 任务清单（机队派发面）和 ASR 模型权重（网络当前不可达）。所以现在能做的只有等这两件到货，而不是空转。

## 已就位（本机实测）

| 项 | 状态 |
|---|---|
| `Tools/voicebank/vb_worker.py --help` | 可运行（args: --voice/--bvids/--bvids-file/--minutes/--jobs/--out/--raw-only） |
| bilibili-api-python | 已装，import 正常 |
| noisereduce | 已装，import 正常（mild spectral-gate 去噪） |
| faster-whisper | 已装，import 正常 |
| ffmpeg | `C:\Program Files\ffmpeg\bin\ffmpeg.exe` |
| CPU 空闲 | 24 核级，当前负载 18–27%，可承接 --jobs 6–8 |

## 两件缺口（都不是本机能自己解决的）

1. **BV 分配清单**：`vb_worker` 的设计是「每机下载自己的分片视频、自建语料」，但派给 bm-c 的 BV 号还没有任何来源。仓内无 `jobs_<voice>.txt`，也没有 speaker→BV 映射。已按 CEO 令走令总线（`OB-20261031-001653-926`）指派：bm-b 先出 v01-v03 样板并公布 BV 清单，bm-c 领 v04/v05。
2. **ASR 权重**：`vb_build.py` 硬依赖 `faster_whisper.WhisperModel(VB_ASR)`，默认 `E:\Fluxgroup\.codely-cli\models\faster-whisper-small` —— 本机无 E 盘。试图从 hf-mirror 拉 `Systran/faster-whisper-small`，**直连超时、代理 7897 未启动**（实测两条都失败），ModelScope 同样不可达。网络恢复后一条命令即可补齐：
   `HF_ENDPOINT=https://hf-mirror.com python -m faster_whisper` 或直接把 bm-b 的模型目录拷来（约 500MB）。

## 结构性事实（免得后面重复踩）

- **GPT-SoVITS 本机没有**，全机队唯一安装点是 bm-b 的 `C:\Fluxgroup\FluxGroup\media\drama-tools\GPT-SoVITS`（`vb_build.py` 的默认 `VB_GPT_ROOT` 就指向那里）。也就是说 **SoVITS 训练只能在 bm-b 跑**，bm-c 能做的是语料 shard + 质检；除非把最小可跑集（源码 + pretrained v2Pro，约 2–3GB）分发过来。
- 机队没有大文件通道（FleetLink `/sync` 只带 ≤256KB 仓内件，SMB/WinRM 关闭），所以「分片自建」是唯一可行形态，别设计跨机搬音频。
- bm-b 当前 CPU 53%（短剧 TTS `Q-TTS-1202` 在跑），它自己也在满负荷，音色库排产要排在 TTS 之后或分时。

## 建议下一步（等主控/CEO 一句话）

1. bm-b 公布 BV 清单 → bm-c 立刻跑 `vb_worker --voice v04 --bvids-file jobs_v04.txt --minutes 20 --jobs 6`，产出 shard + list.txt。
2. 网络恢复后本机补 ASR 模型 → 把 shard 转成 SoVITS 可训语料（转写+切分+list.txt），交给 bm-b 训练，或装最小可跑集在 bm-c 本地训。