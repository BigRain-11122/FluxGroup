# OH-20260929-bigstream.md — BigStream OSS 收获台账·窗 2

> 窗：2026-09-29 21:40 → 2026-10-02 21:40（**先行开窗**：#87 whisper.cpp 接线单先行轮领做·backlog R633 排板/P-20260928-08 转办「接线单认领轮先行〔切片内判据预注册〕」；窗 2 剩余切片 09-29 21:40 后续写本文件·一窗一文件律）
> 实体：BigStream（bm-a OSLoop R644 切片 1）

## 切片 1（R644·2026-09-29 02:2x）— #87 whisper.cpp 字幕转写接线单（P-20260928-08·五门评估+判据预注册+结论三态）

### 实搜面（2 处实录）

1. **GitHub API 直采**（A 级·`api.github.com/repos/ggerganov/whisper.cpp`·2026-09-29 02:1x 实读）：full_name=**ggml-org/whisper.cpp**（原 ggerganov 已转入 ggml-org 组织·API 301 语义下 canonical 名）·description="Port of OpenAI's Whisper model in C/C++"·license spdx_id=**MIT**·stars=**53,990**·forks=6,200·open_issues=347·pushed_at=**2026-09-24T08:29:15Z**（5 日内活跃）·archived=false·language=C++·topics 含 speech-recognition/speech-to-text/whisper。
2. **集团能力注册表+本司在役栈**（跨仓只读）：`cph4/README.md` L58 ASR 位实况=「qwen2.5:7b 现役·14b/bge-m3/**whisper 随消费线**」（=P-20260928-08 转办行「注册表『随消费线』规划位激活·缺口依据=模型矩阵 §二 有 TTS 无 STT」原文实证）；本司消费线在役=faster-whisper 1.2.1（m2-local-stack L15·R169 QC recipe=medium-int8+beam5+noctx·CER 5.53% 实测锚·六案在役 R169/R174/R180/R187/R638/R639）。

### 判据预注册（评估前先立·R630 判据先立 ≤3 问先例）

- **D1 契合门**：S2 席 ASR 事实词核验工位实存？→ 工位实存（六案在役）。「替谁省什么」一句话=**S2 席 ASR 环境阻塞时（HF hub 挂起型）提供零 HF hub 依赖备轨**。
- **D2 反重复门**：在役 faster-whisper R169 QC recipe 对照下 whisper.cpp 是否纯重复？→ 非纯重复但增量面=**环境韧性非质量**（同源 OpenAI Whisper 权重=质量同源；增量=①ggml 模型文件本地直载零 HF hub 依赖=R638 挂起坑〔360MB WS 停 20min·杀进程+HF_HUB_OFFLINE=1 重飞才通〕天然根除②单二进制零 Python/PyTorch 栈依赖）。
- **D3 adopt 线**：同片 A/B 实测 CER ≤5.53% 且耗时 ≤21s（R169 QC recipe 读数）且环境依赖轻量化实证——**无实测=adopt 不可达**（无实测证据不轻换产线·科学判断）。
- 三态线：D1 过+D2 增量明确+D3 无实测 → **parked**；D1 无工位或 D2 纯重复 → reject。

### 五门评估

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | 字幕转写工位实存（S2 席·集团注册表「随消费线」规划位激活=接线单法源） | PASS |
| ②反重复 | 在役 faster-whisper 已覆盖工位；增量=HF hub 离线根除+零 Python 栈（R638 实证坑）；质量同源（同 OpenAI Whisper 权重） | PASS（增量注记） |
| ③许可 | MIT（GitHub API spdx_id 实读·2026-09-29）=直用 | PASS |
| ④健康 | 53,990★·fork 6,200·push 2026-09-24（5 日内）·非 archived·ggml-org 组织（llama.cpp 同组织） | PASS |
| ⑤成本/安全 | 本地推理零 API token；ggml medium ~1.5GB 与在役模型缓存 1.53GB 同量级；**模型类发现只登记不拉取**（P-17 矩阵+试验走 Bonsai 波范式 R635 先例·禁自行占显存）；无外发数据面 | PASS（登记级） |

### 结论：**parked**（备选轨登记+重开条件·判负留痕合法 P-2026-09-28-02）

- 在役 faster-whisper R169 QC recipe=12 处实验调优锚定（CER 5.53% 字位级实测）；换轨须 D3 A/B 实测证据——本轮接线单预算内无真部署实测（Bonsai 波范式=真下载+真编译+真跑·四件套回执，超轮预算，不造速记断言）。
- **重开条件（触发律）**：S2 ASR 面再遇 HF hub 型环境阻塞且 HF_HUB_OFFLINE=1 缓解失效 → 启动 A/B 实测腿（标准片=BS-002 v2 终轨 58.02s·判据=CER ≤5.53% 且耗时 ≤21s）→ 过线即 adopt 换轨。
- **HF_HUB_OFFLINE 坑律入单**（R643 尾针兑现）：faster-whisper 模型载入前置 HF hub 在线 etag 检查=网络挂起型阻塞（R638 根因）；whisper.cpp ggml 路径天然无此坑——两条都已正典化（见落点）。

### 采用 → 落点（工作流变更 2 条·防摆设五律）

1. `src/render/whisper_to_srt.py` docstring 增 HF_HUB_OFFLINE=1 产线默认环境位建议行（R638 根因修正典化·#85 收官后利益回避解除）。
2. `docs/m2-local-stack.md` STT 节增 whisper.cpp 备选轨登记行+变更记录行（重开条件入册·Bonsai 波范式注记）。

### 结论应用表

| 结论 | 应用面 | 承接 |
|---|---|---|
| parked 登记 | S2 席 ASR 备选轨（环境韧性位） | m2-local-stack STT 节 + 本台账 |
| HF_HUB_OFFLINE 坑律 | whisper_to_srt.py 文档行+产线环境位建议 | R638 根因·R643 尾针 |
| 重开条件 | HF hub 型阻塞再发且缓解失效 → A/B 实测腿（CER ≤5.53%·耗时 ≤21s·BS-002 v2 片） | 本切片 D3 判据 |

### 下窗指针

- #70 窗 2 剩余切片（09-29 21:40 后开·续写本文件）：候选 ≥1 项（本地提效类优先）+实搜面 ≥2 处；EAGLE-3/BitNet=CPH4 dogfood 侧份额非本司转办（L160 注记）·知悉不动作。

— R644 bm-a OSLoop·切片 1 毕
