# OH-20261011-bigstream.md — BigStream OSS 收获台账·窗 6

> 窗：2026-10-11 21:40 → 2026-10-14 21:40（窗 6 切片 1 = R2045·09:5x 日窗领·w5 切片 1 下窗指针「候选=PoC 判负→面 moot 归档/PoC 过+CEO 定夺→试跑窗起跑/或如实零发现」兑现——PoC 已过 + D-20261009-05 公众号三路自决=默认不接已裁 → RSS 公众号面 moot 归档；本窗取「或如实零发现」路径变体 = 现产线真实缺口面扫描 4 刀）
> 实体：BigStream（bm-a OSLoop R2045 切片 1）
> 时点闸注记：起跑 09:5x ≥ 开窗 10-11 21:40 ✓（w5 时点闸纪律承继）。

## 切片 1（R2045·2026-10-12 09:5x 起跑 → 窗内交付）— ASR 幻觉抑制 / 数字读法两缺口面扫描：stable-ts 死档 reject + cn2an 留观 parked + VAD 姿态确认（零采用·判负留痕）

### 实搜面（4 刀实录·GitHub API 匿名 4 次 + 本地栈实探零 API）

1. **直采刀 A**（`repos/jianfch/stable-ts`·2026-10-12 09:5x 实读）：**MIT**·2,282★·push 2026-05-30·**archived=True（死档档案化）**·desc「Transcription, forced alignment, and audio indexing with OpenAI's Whisper」=whisper 词级对齐/幻觉抑制 canonical 候选正身。
2. **搜索刀 B**（`search/repositories?q=whisper+hallucination`·total=71·top5 全读）：meizhong986/WhisperJAV（**MIT**·2,322★·push 2026-10-09 当日·Qwen3-ASR+TEN-VAD+本地 LLM 组合=**VAD=幻觉抑制主流路线佐证**·域=JAV 字幕生成错位不采）+DSP-AGH/ICASSP2025_Whisper_Hallucination（MIT·14★·ICASSP 2025 论文 CSV 数据件非工具）+faborsky/whisper-cz-en（MIT·12★·捷克语域错位）+薄档 2 件。
3. **直采/搜索刀 C**（首刀 `q=chinese+numbers+convert+speech`→**total=0 如实记·换刀** `q=cn2an`→total=8）：**Ailln/cn2an**——MIT·768★·push 2026-04-23 活档·非 archived·desc「快速转化中文数字和阿拉伯数字（分数、日期、温度等）」=中文数字规范化 canonical。（首查直采 `AidenLiu1994/cn2an` 404=owner 猜错·搜索刀正法定位，如实记。）
4. **搜索刀 D**（`search/repositories?q=chinese+text+normalization+tts`·total=4 全读）：F31/textnorm（Apache-2.0·**0★ 薄档**）+soon14/TTS_text_norm（无 license 禁入·2020 死档）+terrense/TTS-sambert_hifiGAN（2★）+clear2x/tts-chef（MIT·0★·「AI Agent Skills for TTS Text Preprocessing」=**技能类→姊妹线只供源**）——**无 robust 候选**。
5. **本地栈实探**（零 API）：`src/render/whisper_to_srt.py:269` 实读=**vad_filter=True 已在 R169 QC recipe（medium-int8+beam5+noctx）在役**——尾部静音幻觉抑制面已自持；rg SubMaker/WordBoundary 全仓零命中=cue 时序由逐拍合成时长构造精确（词级边界面无消费者=SubMaker 姊妹面 moot）。

### 判据预注册（评估前先立·≤3 问·R1021 同式）

- **D1（stable-ts）**：外件工位实存？→ **不实存**：vad_filter 在 recipe + SC-005 系五件（10-11 正典 --asr-diff 读数）零尾部静音幻觉旗 = 现时零已旗痛点（R1827 tech#12 excluded 族「尾部静音幻觉=VAD/归一化面」承载注 → 本地实探证实承载已在役）。
- **D1（cn2an）**：工位实存？→ **条件式未来位**：拍稿数字位 = TTS 自然读（「432→四三二=TTS 逐位读」在案为确定性口径非缺陷·数字形差分离=ASR-QC 记账面已处置）；唯 M6 真人校准线 / E4 听感 / CEO 直评若旗数字读法 → 工位现。
- **D4（stable-ts）**：archived 死档（wewe-rss 同判族）。

### 五门评估（候选 A：jianfch/stable-ts·whisper 对齐/幻觉抑制位）

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | 无现时工位（vad_filter 在役+近期 QC 读数零幻觉旗） | **FAIL** |
| ②反重复 | faster-whisper 1.2.1 在装（word_timestamps+vad_filter 已消费）=recipe 覆盖幻觉抑制面 | **FAIL** |
| ③许可 | MIT | PASS |
| ④健康 | **archived 死档**（push 2026-05-30·档案化=维护终止） | **FAIL** |
| ⑤成本 | 整库后端换装（transcribe 面重集成）=重成本对零已旗收益 | **FAIL** |

→ **reject**。重开条件（串联）：尾部静音幻觉族复发 ≥2 件/窗（post-vad QC 读数）→ 先评估活档 license 洁净替代（WhisperJAV 组合=配方参考位非采用位）；**stable-ts 死档永不为候选**。

### 五门评估（候选 B：Ailln/cn2an·拍稿数字读法规范化位）

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | 条件式未来位：M6 真人校准线 / E4 / CEO 数字读法旗 ≥2 件才现 | 条件 FAIL（现时） |
| ②反重复 | 无在册数字规范化器（拍稿数字手写位） | PASS |
| ③许可 | MIT | PASS |
| ④健康 | 768★·push 2026-04-23 活档·非 archived | PASS |
| ⑤成本 | pip 纯 Python 轻量·试点成本可承 | PASS |

→ **parked（留观）**。重开条件：数字读法被旗（M6 真人校准线 / E4 听感 / CEO 直评）≥2 件 → 拍稿预处理 A/B 试点（判据=数字读音自然度真人盲评 + 卡片锚 verbatim 零损 + 字幕轨=edge-tts 直出零损兜底不变）。

### 收益透镜（P-20260926-08 承 P-20261004-02 接线·3 型标注）

- **stable-ts**：N/A（reject·零收益路径）。
- **cn2an**：**省工时·条件式**（触发后=拍稿数字规范化一步自动化）→ 不升权（条件未至）；非纯玩具（canonical 数字转化件）如实记。
- **VAD 姿态确认**（WhisperJAV TEN-VAD 佐证）：**零成本正身收益**=现 R169 QC recipe 主流性背书·零动作。
- 省 token 型 N/A（采集/评估面零推理）·纯玩具类降权不适用面如实记。

### 结论：**reject ×1 + parked ×1 + 姿态确认 ×1——窗 6 首切片零采用（判负留痕合法·P-2026-09-28-02）**

- 稳定幻觉抑制面=自持正身（vad_filter 在 recipe·主流佐证在档）；stable-ts 死档=永不为候选位。
- cn2an 留观位入档（重开条件上表）。
- 姊妹线咬合：**模型类零发现**（P-17/P-19 零触发零拉取）；**技能类** tts-chef（thin）→P-20260926-01 技能律只供源不双建。

### 采用 → 落点（工作流变更 0 条·结论应用表）

1. 零工作流变更（两候选=reject/parked·现产线零动作）；
2. 落点=本台账全档（重开条件双条=未来 QC/M6 读数窗消费面）。

### 结论应用表

| 结论 | 应用面 | 承接 |
|---|---|---|
| reject：stable-ts（archived 死档） | 禁入候选池永久位；幻觉抑制重开条件=族复发 ≥2 件/窗（post-vad QC 读数） | 本台账 + SC 系 QC 读数位（现有 face 承载·零新队行=反膨胀） |
| parked：cn2an 数字读法规范化 | 重开条件=M6/E4/CEO 数字读法旗 ≥2 件 → 拍稿 A/B 试点 | 本台账 + M6 真人校准线注记位 |
| 姿态确认：vad_filter 主流性 | 现 R169 QC recipe 维持·零变更 | 本台账 |

### 三律自检：①真实缺口锚=SC-005 系 QC 读数面+R1827 tech#12 excluded 族 VAD 承载注 ✓ ②判据先行（D1/D4 预注册）✓ ③落点强制=本台账+下窗指针 ✓

### 下窗指针（窗 6 余切片 ≤10-14 21:40 随窗领）

候选面预判：①M5 解锁类维持 gated 不评估 ②audio 线 SC-005-07 收官观察位族（tech#116/#117/#118）消费轮若现真缺口 → 即时切片 ③或如实零发现。≤3 刀照守。
---

## 切片 2（R2053·2026-10-12 13:5x 领做 — audio QC ASR 中文后端替代候选扫描：FunASR/SenseVoice 双 MIT 活档 → conditional-parked〔B 臂 A/B 试点预注册·SC-005-07 QC 腿触发〕）

### 实搜面（3 刀实录：GitHub API 直采 2 刀 + 本司在案证据 1 刀零 API）

- 刀 1 直采 modelscope/FunASR：**MIT·20,653★/2,076 forks/push 2026-10-10（2 日内）·非 archived**——desc=ASR 训练/推理/流式/VAD/标点/说话人分离全管线+OpenAI 兼容/MCP serving（whisper 系外中文主战栈正主）。
- 刀 2 直采 FunAudioLLM/SenseVoice：**MIT·9,495★/837 forks/push 2026-09-30（12 日内）·非 archived**——SenseVoiceSmall=中/粤/英/日/韩 ASR+语种识别+情绪识别+音频事件检测（阿里 FunAudioLLM 官方仓）。
- 刀 3 本司在案证据（零 API）：SC-005 系字位带 01=13.8/02=15.0/03=14.6/04=14.2/05=16.0（峰）/06=11.8（系最优）——whisper-medium-int8 中文同音/专名漂移族三现（编年史→编年时 ×3·硅基→归基 ×2·户籍锚卡→户籍毛卡）+繁体漂移带 R2003 A/B 判负（--no-context 下 initial_prompt 只条件首解码窗·尾部漂移结构性不可达）+tech#97/#102 双阈值全建于此噪声面+tech#108 --asr-diff=测量器在役；发布面零损（字幕轨=edge-tts 直出）=QC-only 缺口锚；系列首季收官/二季 SC-005-07 在飞=换基线天然窗口（二季新带=可比性成本最小化）。

### 判据预注册（测前预立 ≤3 问）

1. B 臂 A/B 四轴读数（SC-005-07 同一音频双后端）：字位 % 对比（whisper 基线带 vs 候选）/硬事实链存活（信条句+口令族 verbatim 净度）/繁体带（close 段五连繁体复现否）/运行时（CPU 面）。
2. 采用闸：字位降 ≥30% 且硬事实链零回归 → 候选转 QC 主后端（whisper 降级对照）；不达 → 判负留痕（R2003 同式）。
3. 依赖闸：funasr pip 面与 ComfyUI/便携 env 零冲突探针先行（隔离 venv/--no-deps 二选一）·模型件 ~1-2GB 落盘+CPU 推理优先（12GB 卡 pause 窗零 VRAM 争用）。

### 五门评估（候选 A：modelscope/FunASR〔paraformer-zh 中文 ASR 位〕+候选 B：FunAudioLLM/SenseVoice〔SenseVoiceSmall 位〕·共判共落）

- D1 契合门：**PASS（QC-only 工位实锚）**——ASR 终轨 QC 面=每件音频跑（SC-005 系 6 件+F-180 在飞）；专名同音漂移直接咬硬事实链核验（QC 核心使命面）；中文主战后端直击 whisper 中文弱面；二季换基线窗在位。
- D2 反重复门：**PASS（换轮非重建）**——现役 whisper 本身即外轮；本司自建面（tech#108 测量器/tech#97 阈值/em 归一）全保留复用；候选=同一 QC 面更优测量轮非重复造轮。
- D3 许可门：**PASS（repo 双 MIT·注记）**——仓库级 MIT 双证；模型权重 license（ModelScope 卡面 paraformer-zh/SenseVoiceSmall）=集成时二验位（QC 内用零再分发=低风险面先行）。
- D4 健康门：**PASS**——20.6k★/9.5k★ 双活档·push 2 日/12 日内·非 archived。
- D5 成本门：**trial PASS / adoption gated**——B 臂 A/B=一次性成本（模型下载+CPU 推理单件）；全采换后端=带重整注（二季新带=时点已对）+VRAM 零争用。

### 收益透镜（P-2026-09-26-08 + P-20261004-02 透镜·2 条备注）

- 直接收益面=QC 判读减负：R1996 形差剔除 90 sites 全轮段级 adjudication+R2003 繁体带法证两轮=噪声税实锚；后端换净=该税面收缩（tech#97 触发频率趋零化路径）。
- 姊妹线咬合：模型类**首次正发现登记**（P-17/P-19 模型类零拉取先例承继=本切片仅登记不拉取·采不采=A/B 读数后定）；技能类零发现。

### 结论：**conditional-parked ×2（B 臂 A/B 试点预注册·触发件=SC-005-07 F-180 QC 腿）——切片 2 零直接采用·判据已立**

### 采用 → 落点（工作流变更 0 条·结论应用表）

### 结论应用表

| 结论 | 应用面 | 承接 |
|---|---|---|
| conditional-parked：FunASR paraformer-zh / SenseVoice-small（QC ASR 中文替代候选） | B 臂 A/B 试点=SC-005-07 QC 腿四轴读数（字位/硬事实链/繁体带/运行时）·采用闸=字位降 ≥30% 且硬事实链零回归 | tech 队新种子（A/B 试点行）+SC-005-07 消费轮（F-180 QC 腿） |
| 依赖闸先行探针 | funasr pip 隔离探针（venv/--no-deps）·CPU 推理位·模型件 license 二验 | 同上种子内子步 |

### 三律自检：①真实缺口锚=SC-005 系字位带+专名族三现（技术件在案）✓ ②判据先行=四轴 A/B+采用闸预注册 ✓ ③落点强制=tech 队种子+本表双落 ✓

### 下窗指针（窗 6 余切片 ≤10-14 21:40 随窗领）

候选面预判：①A/B 试点若先行兑现→读数件即时切片；②或如实零发现。≤3 刀照守。
