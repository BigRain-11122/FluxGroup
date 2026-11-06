# 工具逐个实测板（2026-11-06）

判据统一：可安装 / 可跑通 / 有本仓真实数据 / 给出可用或不可用的明确结论。跑不通也记，写成「不可用+原因」。

## 一、结果总表

| # | 项 | 星 | 结果 | 数字 | 结论 |
|---|---|---|---|---|---|
| 1 | ffmpeg freezedetect/blackdetect/ebur128 | 内置 | ✅ | v722g 5 定格 / v723 2 定格；黑帧 0；真峰值 +2.3 dBFS | **可用，应进闸** |
| 2 | PySceneDetect | 5,394 | ✅ | v722g 74 切点/75 镜、v723 72 镜、均镜长 3.26s、仅 1 镜 <0.5s | **可用** |
| 3 | ffmpeg libvmaf | 5,582 | ✅ | 同段 60s，CRF28 对 CRF16：mean 91.50 / min 79.16 / harmonic 91.45 | **可用**；min 79 说明有单帧劣化点 |
| 4 | PySceneDetect → cut index | — | ✅ | 72 镜 CSV 落盘；转 .otio 后回读 72 clips、总时长 234.4s 与成片一致 | **可用，闭环成立** |
| 5 | faster-whisper | 26,523 | ⚠️ 部分可用 | small/int8，60s 音频 3.7-11s 转写；**VAD 开启时 0 段（歌唱被当噪声）**；关 VAD 出 19 段 | 用于「已知歌词的强制对齐」可用，**纯 ASR 认歌词不可信** |
| 6 | leanctx | 320 | ✅ 装成 / ❌ 不单测 | 其源码自述 `Lingua` = LLMLingua-2 封装、`Verbatim` 才是代码默认 | **与 LLMLingua-2 同源，中文继承同一缺陷**，不重复测 |
| 7 | sdl-mcp | 497 | ⏸ 未测 | npm 包名待确认 | 待下一轮 |
| 8 | OpenTimelineIO | 2,059 | ✅ | 0.18.1（3.12 venv，必须 `--only-binary`，源码编译会超时） | **可用** |
| 9 | hikyuu | 3,688 | 进行中 | C++ 扩展编译 | 待回 |
| 10 | apkscan | 311 | ⛔ 阻塞 | 全仓 **0 个 APK 样本** | 需先有样本，否则无法测 |
| 11 | just | 36,587 | ⏸ 不测 | 无 cargo/scoop，winget 需装系统件 | 已有 dispatcher，价值低，暂缓 |
| 12 | splitrail | 228 | ⏸ 不测 | 无 npm 包，需下二进制 | 暂缓 |
| 13 | mem0 | 68,507 | ⛔ 不引 | 需 LLM API + 与文件+git 记忆制冲突 | 结论已定 |
| 14 | LatentSync | 6,255 | ⛔ 转派 | 需 GPU | 本机让路态，转 bm-c |
| 15 | Context-Gateway | 647 | ⛔ 阻塞 | 需 Go 工具链（本机无） | 待装 Go 或转执行机 |
| 16 | claude-slim | 44 | ⛔ 不适用 | 面向 `.claude` 配置面，我们走 `.codely-cli` | 不兼容 |
| 17 | repomix / LLMLingua / contextshield | — | ✅ | 见 TOKEN-OPT-TOOLBOX §四·五 | 已定选型 |

## 二、本轮新得的可用件（3 个）

1. **剪映索引闭环**：`PySceneDetect → CSV → OTIO`，实测 72 镜、总时长 234.4s 与成片逐秒吻合。这是补 D5 缺口的现成路径。
2. **VMAF 压片质检**：本机 ffmpeg 自带 libvmaf，60s 段 28 秒算完，能给压片定「不低于 93」的硬线。
3. **ffmpeg 三件（定格/黑帧/响度）**：零安装、秒级，已在我们成片上抓到真问题。

## 三、踩到的坑（复用）

1. `libvmaf=log_path=` 里写 Windows 反斜杠路径会静默不出 json → 一律用正斜杠或相对路径。
2. faster-whisper 与 av 19 不兼容（`metadata_errors` 参数不存在）→ 降 `av==13.1.0` 即通。
3. OpenTimelineIO 在 py3.14 无轮子、py3.12 源码编译超时 → `pip install --only-binary :all:` 秒装 0.18.1。
4. faster-whisper 的 VAD 会把「唱歌」判成噪声 → 转 0 段；测歌声必须 `vad_filter=False`。
5. Speaches/ASR 在歌声上准确率明显不足（"用借金蚊子割下的永远"这类无意义句），字幕线正解是「已知歌词 + 强制对齐」。

## 四、待办（下一轮）
- hikyuu 回执后补测（若装不上，改用轻量回测库对照口径）
- apkscan：先让 recon 线提供一个 APK 样本
- sdl-mcp：确认 npm 包名后测「检索 vs 直读」的 token 成本
- Context-Gateway：装 Go 后或转执行机测