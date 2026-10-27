# 机位档案 · bm-b（BIGMONEY）

- 采集时间：2026-10-27 00:2x（实测，工具 `Tools/model_slot_bench.py` → `bench-bm-b.json`）
- 维护：bm-b 执行；机位档案随硬件/模型变化更新，**不许凭印象改**

## 一、硬件

| 项 | 值 |
|---|---|
| 主机名 | BIGMONEY（机位 bm-b） |
| CPU | AMD Ryzen 7 3800X（8 核 / 16 线程） |
| RAM | 24.0 GB |
| GPU | RTX 3070 **8 GB**·驱动 617.42·功耗墙 239.8 / 240 W（已拉满） |
| 磁盘 | C: 可用 348.6 GB·E: 可用 177.4 GB |

## 二、显存实况（关键底数）

| 状态 | 实测显存 |
|---|---|
| 空载（Ollama 全卸，仅桌面） | **665 MB** |
| 7B 常驻（qwen2.5:7b-instruct, 4096 ctx） | 5,384 MB |
| 14B 常驻（bili-reply-14b） | 7,856 MB |

→ **8 GB 卡的真实可用预算 ≈ 7.4 GB**（8.2 − 0.7 桌面）。**没有"桌面吃掉 4GB"这回事**（本窗初测误判已自纠：那是模型自身的驻留）。

## 三、模型实测（同一 prompt·num_ctx 2048·num_predict 64）

| 模型 | 首载 | 生成速率 | 驻留显存 | 结论 |
|---|---|---|---|---|
| qwen3.8:4b | 9.7 s | **77.0 tok/s** | 4,947 MB | 最快，但 4B 容量偏小 |
| qwen2.5:7b-instruct | 8.3 s | **59.6 tok/s** | 5,890 MB | **本机质量/速度最优解** |
| bili-reply-v38（7B 定制） | 10.6 s | 24.2 tok/s | 采样异常（1,284 MB） | 待复测；定制语气提示词 |
| bili-reply-14b（14B Q4） | 13.9 s | **4.4 tok/s** | 7,856 MB | 仅离线批量可用，禁常驻 |

## 四、槽位（谁用图卡、谁让路）

| Profile | 内容 | 显存 | 适用 |
|---|---|---|---|
| `text-fast`（默认常驻） | qwen3.8:4b·keep_alive 30m | 4.9 GB | 哨兵/工作轮/循环班（**消费方硬编码 4B，槽位须与之对齐**） |
| `text-standard` | qwen2.5:7b-instruct·keep_alive 20m | 5.9 GB | 需要更好语感的交互（回复候选初筛） |
| `text-quality` | bili-reply-14b·keep_alive 10m | 7.9 GB | 离线批量（慢但稳），**独占** |
| `image` | 卸全部文本 → ComfyUI | 需 ≥6.5 GB 空闲 | KF/素材烧制 |
| `audio` | 卸全部文本 → IndexTTS / GPT-SoVITS | 需 ≥4.5 GB 空闲 | 配音/声线 |
| `idle` | 全卸 | 0.65 GB | 让路 CEO 用机/保底 |

**为什么默认是 4B 而不是 7B**：`bmb-sentinel.ps1` 与 `bmb-work-runner.ps1` 把 `qwen3.8:4b` 写死为 keep_alive=-1 的常驻件（09-xx 起的设计）。7B 虽语感更好，但 +1GB 显存、−18% 速度，在 8G 卡上会挤掉图像车道的余量。**任务负载优先于纸面最优**——所以 7B 降为按需档 `text-standard`，不与常驻槽抢位。（实测佐证：切 7B 后哨兵下一拍即 `REPINNED` 拉回 4B，双模型共存会超卡）。

切换：`python Tools/model_slot.py --profile <name>`（带 VRAM 闸，超预算直接 REFUSE）；查状态 `--status`。

## 五、任务→槽位映射（工作流侧）

| 任务 | 槽位 | 理由 |
|---|---|---|
| 量化循环班（BM IterationLoop） | text-fast（4B） | 每分钟级交互，需低延迟且与哨兵同槽 |
| 哨兵/自驱工件 | text-fast（4B） | 消费方硬编码 4B，禁改槽 |
| B 站回复候选（离线批） | text-quality（14B） | 4.4 tok/s 可接受，质量优先 |
| 漫剧 KF 烧制 / MV KF | image | 与文本互斥 |
| 漫剧配音 / 声线微调 | audio | 与文本互斥 |
| CEO 用机（「我要工作」） | idle + 释放阀 | 让路律 |

## 六、迭代机制

- 每周一 09:07（S4U 任务 `FluxGroup-ModelSlotBench`）复测四模型 → 覆盖 `bench-bm-b.json`，速率变化 >20% 或新模型入册时更新本档案。
- 新模型入册标准：在**本机**实测速率 + 驻留显存 + 一个真实任务 A/B（不是看排行榜）。
- 与提示词方法论联动：槽位决定 `num_ctx`（2048/4096），prompt 预算按槽位上限算（见 PROMPT-ASSET-METHODOLOGY §一）。