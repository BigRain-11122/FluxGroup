# OH-20261005-bigstream.md — BigStream OSS 收获台账·窗 4

> 窗：2026-10-05 21:40 → 2026-10-08 21:40（窗 4 切片 1 = 开窗即领·R1034 下窗指针「音频轴工具·预判无工位 / 发布链平台 API 类 M5 前不评估 / 或如实零发现」兑现·**P-2026-10-04-02 收益透镜接线窗 4 首用**〔每契合件五门评估增写预期收益形态 3 型标注+可变现升权·纯玩具类降权〕）
> 实体：BigStream（bm-a OSLoop R1409 切片 1）
> **时点闸操作红注记**：三刀起跑 21:33-21:39 早于本窗开窗时点 21:40 约 7 分钟（探针基线 21:32 判定后预算内顺跑未守时点闸）；交付 commit 落窗内 21:40+，每窗 ≥1 切片义务达成不受影响；执法注记=切片起跑时刻须 ≥ 开窗时点（R1021 开窗即领 21:5x 口径·下窗照守）。

## 切片 1（R1409·2026-10-05 21:3x 起跑 → 21:4x 窗内交付）— 音频响度面收口 + ASR 热词面正发现：双 reject + 既有依赖未用特性回流提案（#70 窗 4·判负留痕+提案回流双产出）

### 实搜面（3 处实录·≤3 刀照守）

1. **GitHub API 搜索刀 1**（A 级·`search/repositories?q=ffmpeg+loudnorm+python`·2026-10-05 21:4x 实读·total_count=6 全读）：trsdn/autocut（**MIT**·3★·push 2026-08-27·静音剪重切工具=**杀真实感域·w1 mortemtrimmer 同判**）+urscaviezel/Loudnorm-PRO（**GPL-3.0=禁入产品交付链**〔R458/R1034 先例〕·1★）+torkian/acx-rms-fix（MIT·1★·ACX 有声书平台拒收修复器=**平台域错位**·本司无此合规面）+dllmr/Levelator（**无 license=禁入**）+MatchingMole/MasteringMythBuster（**GPL-3.0 禁入**·0★）+QarabaiErooom/YOUTUBE-MP3（MIT·0★·yt-dl 包装器域错位）→ **响度面搜索零契合**（半数 GPL/无 license 禁入·余域错位/薄档）。
2. **GitHub API 直采 + 搜索刀 2**（A 级）：`csteinmetz1/pyloudnorm` 直采=license **MIT**·**783★**/fork 61·push **2026-01-04**（~9 个月·低频维护档如实记）·非 archived·desc="Flexible audio loudness meter in Python with implementation of ITU-R BS.1770-4 loudness algorithm"；`search/repositories?q=whisper+hotwords`（total_count=12·top6 全读）=masoumehhsn/VoiceRecognizer（**无 license 禁入**·11★·C++·whisper.cpp 热词唤醒）+qinyu765/xiluolin（MIT·4★·Rust 实时听写）+dn0sh/audio-video-transcriber-faster-whisper（MIT·2★·俄语转写）+**yaniv-golan/asr-bias-builder**（MIT·**1★**·"Build ASR bias artifacts from PDF/PPTX decks — generates **Whisper hotword prompts** and Google Speech-to-Text phr[ases]"）+**lukadoncic12/voice-hotwords-local**（MIT·**0★**·项目感知 whisper 听写+隔离热词）+zak1201/hermes-local-voice（MIT·0★·Shell）→ 热词生态位实存但**双外件全薄档**（1★/0★）+域=实时听写/演示文稿偏置工件。
3. **本地栈实探**（零 API·`r1409_oss_blades.py` 实跑）：**faster-whisper 1.2.1 已装**（S2 席 ASR 终轨在役栈·R169 QC recipe=medium-int8+beam5+noctx）·`transcribe` 签名 **`hotwords` 参数在位**+**`initial_prompt` 参数在位**（`inspect.signature` 实证 True/True）——**双参数从未启用**（R169 recipe=noctx口径·历轮 ASR 终轨零调用）=**既有依赖未用特性**；ffmpeg 9.0.1 `-filters` 实测 **loudnorm 滤镜内置在役**（present=True）。

### 判据预注册（评估前先立·≤3 问·R1021/R1033/R1034 同式）

- **D1 契合门（响度面）**：响度测量/归一工位实存？→ **不实存**（R1034 预判兑现）：edge-tts 单声源确定性输出（同稿复跑时长逐毫秒一致=R189 实证）+BGM-A 纯净（D-BS-02 禁烧）+S2 三门/帧验三律/E8/E4/CEO 目检历**零响度旗**。「替谁省什么」一句话=无工位可答。
- **D2 反重复门（响度面）**：ffmpeg loudnorm 滤镜内置在役（本地实探）=测量/归一双位已有轮子。
- **D1 契合门（热词外件）**：外件工位实存？→ **不实存**：双外件域=实时听写/Google STT 偏置工件 ≠ 本司批处理 QC 终轨域；且本司缺口可由**既有依赖参数**直接解（见 B'）。
- **D2 反重复门（热词外件）**：faster-whisper 1.2.1 双参数在位（本地实探）→ 外件零增量。
- **B' 正发现（既有依赖未用特性）**：**非新件不入五门**（oss-harvest 三律：模型/库/件三分类·B'=既有轮子未用面）→ 落点强制=**回流提案面 P-3**（queue §D·司内提案面·跨仓写禁令不直写集团台账）。
- 三态线：响度面 D1 无工位 → **reject**；热词外件 D1 域错位+D4 薄档 → **reject**；B' → **提案回流**。

### 五门评估（候选 A：pyloudnorm）

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | 无工位（R1034 预判兑现）：edge-tts 单声源确定性+BGM-A 纯净+S2/帧验/E8/CEO 历零响度旗；搜索面 6 命中半数禁入余域错位=刀面零契合续证 | **FAIL** |
| ②反重复 | ffmpeg 9.0.1 loudnorm 滤镜内置在役（本地 -filters 实探 present=True）=测量/归一双位已有轮子 | **FAIL** |
| ③许可 | MIT（API 实读 2026-10-05） | PASS |
| ④健康 | 783★/fork 61·push 2026-01-04（~9 个月·低频维护档如实记）·非 archived | PASS |
| ⑤成本/安全 | 纯本地测量库零 API；但 D1 级联=零已旗收益无成本正当性 | **FAIL** |

### 五门评估（候选 B：asr-bias-builder + voice-hotwords-local 热词外件对）

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | 域错位：双外件=实时听写/演示文稿偏置工件（whisper.cpp 唤醒/Google STT phrase）≠ 本司批处理 QC 终轨域（faster-whisper CT2 medium-int8+beam5）；本司缺口=既有依赖参数可解 | **FAIL** |
| ②反重复 | faster-whisper 1.2.1 transcribe 签名 hotwords/initial_prompt 双参数在位（本地 inspect 实证）=外件零增量 | **FAIL** |
| ③许可 | 双 MIT（API 实读） | PASS |
| ④健康 | 1★/0★ 薄档（thin-repo）·push 2026-01/2026-08 | **FAIL** |
| ⑤成本/安全 | 新增依赖零收益（参数级方案在位） | **FAIL** |

### 收益透镜（P-2026-10-04-02 接线·窗 4 首用·3 型标注=省 token/省工时/直接营收）

- **pyloudnorm**：预期收益形态=**省工时·条件式**（M5 上线后平台响度拒收返工场景）→ **不升权**（现时收益 0·条件未至）；**非纯玩具**（ITU-R BS.1770-4 严肃算法库）如实记·降权不适用。
- **热词外件对**：预期收益形态=**省工时**（S2 席 QC 复核轮次）→ 外件零增量=**不升权**；薄档如实记。
- **B' 提案回流（initial_prompt 专名预载）**：预期收益形态=**省工时**（S2 席 ASR 专名复核面·真旗链在案=历轮 M6「真人校准线」注记系列）→ **微升权入提案面**（升权理由=真旗链+零新依赖+零 token 成本；非直接营收型如实注）；可变现口径=QC 门保真度提升。
- **零 token 型注记**：三候选全本地栈相关·省 token 型收益 N/A 如实记（本司推理面零云维持）。

### 结论：**reject ×2（判负留痕合法·P-2026-09-28-02）+ B' 正发现回流提案面 P-3**

- 音频响度面收口：R1034 预判（"响度恒定零旗·预判无工位"）**兑现**——edge-tts 同构+loudnorm 内置双已有轮子+零响度旗历史三方实证；搜索面 6 命中半数 GPL/无 license 禁入+域错位=刀面零契合。
- ASR 热词外装面收口：生态位实存（asr-bias-builder 印证 whisper hotword prompt 方法论）但外件全薄档+域错位；**正发现=既有依赖未用特性**（faster-whisper 1.2.1 hotwords/initial_prompt 双参数从未启用）→ **提案面 P-3 回流**（docs/self-improvement-queue.md §D）。
- **重开条件（响度面触发律）**：M5 上线后平台响度拒收/投诉 ≥2 件 → 先评估 **ffmpeg loudnorm 两遍法自研**（零新依赖·Bonsai 波范式）·pyloudnorm 仅测量对照位不入链。
- **B' 试点判据（P-3 行承载·≤3 问·窗 ≤2 周=下 1-2 件 ASR 终轨）**：①专名首提退化位点数 A/B 降幅 ≥50%？②prompt 文本泄漏进转写新增幻觉位=0？③全字位同音噪声率不升？——**诚实 caveat**：faster-whisper 官方注记 hotwords 仅 large-v3-turbo 系生效（训练数据口径·须 A/B 实测定谳非断言）→ medium-int8 走 **initial_prompt 路径**；字幕轨=edge-tts 直出=发布面零损不变（QC-only 改动零发布面风险）。

### 采用 → 落点（工作流变更 0 条·提案面 1 条）

1. 零工作流变更（S2 QC recipe 维持 R169 口径·P-3 试点未开窗）；
2. 落点=**P-3 提案行**（docs/self-improvement-queue.md §D·司内提案面正典位·落点强制律）+本台账全档（判据+重开条件+试点判据=后续轮执法面）。

### 结论应用表

| 结论 | 应用面 | 承接 |
|---|---|---|
| reject：pyloudnorm（无工位+反重复双 FAIL） | 音频响度面收口：edge-tts 同构+loudnorm 内置=双已有轮子维持；重开条件=M5 后平台响度投诉 ≥2 | 本台账 |
| reject：热词外件对（薄档+域错位+参数在位） | ASR 热词外装面收口：方法论印证留存（whisper hotword prompt 路线成立） | 本台账 |
| B' 回流提案 P-3 | S2 ASR QC 专名热词预载 A/B 试点（initial_prompt 路径·medium-int8）·判据三问+诚实 caveat | queue §D P-3 行 |

### 姊妹线咬合

- 模型类零新断言=P-17 适配矩阵/P-19 管线无触发**零拉取维持**（B'=既有依赖参数·零新模型）；
- AI 会话技能类零发现=P-20260926-01 技能律只供源维持；
- 发布链平台 API 客户端类=**M5 账号物理件 blocked-on-CEO 前不评估维持**（R1034 指针照守）。

### 三律自检

礼貌节流 3 刀（搜索两刀+直采一刀+本地实探零 API·窗口内 API 调用 4 次 ≤6 帽）✓；落点强制=结论应用表 3 行+P-3 提案行在盘 ✓；判据预注册先立后评 ✓。

### 下窗指针

- 窗 4 剩余切片（**10-08 21:40 前续写本文件**·每窗 ≥1 切片义务已满）：候选面=发布链平台 API 类维持 M5-gated 不评估/音频轴已收口/渲染工程基建类 w3 已三刀收口/**或如实零发现**（诚实预判=三面全收口后剩余面薄）；≤3 刀照守。

— R1409 bm-a OSLoop·切片 1 毕

## 切片 2（R1411·2026-10-05 22:1x 起跑 → 22:2x 窗内交付）— 剩余面诚实收口：zh 纠错面+ASR 度量面双 reject + w2 parked 双轨维持（#70 窗 4·下窗指针「候选面已收窄或如实零发现」兑现·窗 4 全窗收口）

### 实搜面（3 处实录·≤3 刀照守·本切片 API 2 次→窗计 6/6 帽尽）

1. **GitHub 搜索刀 1（zh 文本纠错面）**（A 级·`search/repositories?q=chinese+text+correction+python`·2026-10-05 22:1x 实读·total_count=1 全读）：Ahmedhass6140/open-dictate（MIT·**0★**·macOS MLX Whisper 本地听写+自定义词表纠正=**域错位薄档**）→ 面级命中薄；**诚实注**=canonical 候选 shibing624/pycorrector 因其 description 为中文（「pycorrector: 中文文本纠错工具…」）未入英文自由文本查询命中=查询面盲位如实记；窗 API 6/6 帽尽不加第三刀——**面级判决不依赖候选身份**（见判据预注册 D1 设计级），pycorrector 的 D3/D4 门未跑=非必要（D1 闭面后 moot）；若未来该面出现真工位（现设计下不可达），新窗新刀重评。
2. **GitHub 搜索刀 2（ASR 度量对齐库面）**（A 级·`search/repositories?q=jiwer`·total_count=25·top6 全读）：**jitsi/jiwer**（**Apache-2.0**·**933★**·push 2026-09-03 活档·非 archived·"Evaluate your speech-to-text system with similarity measures such as WER"=canonical 度量库）+maximnara/jiwer（MIT·17★·**AngularJs 图片查看器=同名异物域错位**）+lixuanqun/asr-eval（MIT·**2★ 薄档**·中文 ASR 评测工具箱 micro-CER 对比 FunASR/Whisper——同域邻档）+comparison-moonshine-vs-faster-whisper-tiny-en（**无 license 禁入**·4★·Jupyter 对照实验非库）+余 Bangla 域错位两件。
3. **本地实探（w2 parked 双轨重开条件复查·零 API）**：pinned medium 模型在盘 4 件（`data/assets/models/faster-whisper-medium`）+R1410 P-3 A/B 四转写全走 HF_HUB_OFFLINE=1 零 hub 接触（state log R1410 实录）+log 尾零「HF hub 型阻塞」字样=**whisper.cpp 环境轴重开条件（hub 阻塞再发且缓解失效）未触发**；SenseVoice 触发 A 线（字位 diff ≥40% 连发 ≥2 件）：P-3 读数 BS-003 A=0.1275/B=0.1176、BS-004 A=0.3112/B=0.0918——A 轨峰 31.12% **单件且 <40%**、现役 recipe（B=initial_prompt 预载·R1410 adopt）9.18%-11.76% 全带内零连发；触发 B 线（同音人工裁定 >0.5 轮预算连续 ≥2 件）：log 尾零「瓶颈」旗=未触发。

### 判据预注册（评估前先立·≤3 问·r1411_oss_blades.py 头注预注册=起跑前落盘·R644/R762/R1021 同式）

- **D1 契合门（zh 纠错面·面级）**：自动纠错工位实存？→ **设计级不实存**：S2 asr-check 转写=QC 仪器（测「ASR 听到什么」·噪声级如实入账喂 M6 真人校准线=诚实律设计面），自动纠正会**伪造 QC 信号本身**；成品字幕轨=edge-tts 直出（发布面零损不经过 ASR）=纠错零发布面；唯一可行动子面（专名首提退化）已由 R1410 adopted initial_prompt 预载在**源头**闭（P-3 三问全过）。「替谁省什么」一句话=无工位可答（工位在现 QC 设计下不可达）。
- **D2 反重复门（ASR 度量面）**：在役 in-house asr-diff/r1410_p3_ab.py 字位率+专名位点双口径已量测（R1410 四转写 A/B 实证·判据③全字位噪声率即用此工具判 PASS）→ 标准化 WER/CER 库零增量。
- **D1 契合门（ASR 度量面）**：S2 QC 度量工位在役但**零旗**（历轮零「缺标准化 CER/WER」旗·字位噪声率口径已在 R169 recipe+P-3 判据双锚定）。
- 三态线：zh 纠错面 D1 设计级无工位 → **reject（面级）**；jiwer D1 无旗+D2 纯重复 → **reject**；parked 双轨触发皆未启 → **维持 parked**。

### 五门评估（候选：jitsi/jiwer）

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | S2 QC 度量工位在役零旗：字位噪声率/专名位点/事实词存活三口径 in-house 已锚定（R169 recipe 12 处调优+P-3 判据③实测）；无任何「缺标准化 WER/CER 对齐」历史旗 | **FAIL** |
| ②反重复 | in-house asr-diff/r1410_p3_ab.py 在役实证（R1410 四转写 A/B·A 复跑与归档逐字一致 ratio 1.0000=度量确定性同证）；jiwer 增量=alignment ops（sub/del/ins 分解）——本司口径无需该分解面 | **FAIL** |
| ③许可 | Apache-2.0（API 实读 2026-10-05） | PASS |
| ④健康 | 933★·push 2026-09-03（月内活档）·非 archived·jitsi 组织 | PASS |
| ⑤成本/安全 | 纯本地度量库零 API；但 D1/D2 双 FAIL 级联=零收益无成本正当性 | **FAIL** |

（同族邻档 asr-eval：MIT 但 2★ 薄档 D4 FAIL·同域 in-house 覆盖 → reject 同判·不另立表。）

### 收益透镜（P-20261004-02 接线·3 型标注=省 token/省工时/直接营收）

- **jiwer**：预期收益形态=**省工时**（S2 QC 度量自动化假设位）→ in-house 双 FAIL=**不升权**；非纯玩具（jitsi 在役严肃库）如实记·降权不适用。
- **zh 纠错面**：预期收益形态=**N/A**（设计级无工位·QC 诚实律禁自动纠正=工位不可达）→ 不升权不降权（非候选件·面级闭）。
- **asr-eval**：预期收益形态=省工时 → 薄档+零增量=**不升权**。
- **零 token 型注记**：三面全本地栈相关·推理面零云维持=省 token 型 N/A 如实记。

### 结论：**reject ×2（面级 1+候选级 1·判负留痕合法 P-2026-09-28-02）+ parked 维持 ×2 —— 窗 4 剩余切片收口=零采用（如实零发现）·窗 4 全窗闭环**

- zh 纠错面收口：D1 设计级判决（QC 仪器原始性=诚实律设计面+发布面零损+可行动子面已在源头闭）——**该面在现行 QC 设计下永久闭**，重开条件=QC 设计变更（如 M6 真人校准线工具化立制）须 CEO 令或立法窗授权，非 OSS 面事件。
- ASR 度量库面收口：jiwer 健康 canonical 但 in-house 度量双口径在役+零旗=反重复主导 reject（非候选缺陷·D3/D4 全 PASS 如实记）。
- w2 parked 双轨维持：whisper.cpp 环境轴（pinned 模型在盘+HF_HUB_OFFLINE=1 缓解在役零阻塞再发）+SenseVoice zh 轴（触发 A 峰 31.12% 单件 <40%·现役 recipe 带内·触发 B 零瓶颈）——**双触发皆未启=parked 维持·重开条件原文照守**。
- 窗 4 全窗账：切片 1（reject ×2 + B' 正发现→P-3 提案回流）+切片 2（本切片）→ **窗 4 净采用=1 件（B'→P-3→R1410 initial_prompt QC leg 已落地）+reject 4 面+parked 维持 2 轨**。

### 采用 → 落点（工作流变更 0 条·reject/parked 态）

1. 零工作流变更（现役 QC recipe=R169 口径+R1410 initial_prompt leg 维持不动）；
2. 落点=本台账全档（面级闭面判据+parked 双轨复查读数+窗 4 全窗账=后续轮执法面）。

### 结论应用表

| 结论 | 应用面 | 承接 |
|---|---|---|
| reject：zh 纠错面（设计级无工位） | S2 QC 仪器原始性维持：噪声如实入账喂 M6 真人校准线；重开条件=QC 设计变更须 CEO 令/立法窗 | 本台账 |
| reject：jiwer（无旗+反重复双 FAIL） | ASR 度量面收口：in-house asr-diff 双口径维持（字位率+专名位点） | 本台账 |
| parked 维持 ×2（whisper.cpp 环境轴/SenseVoice zh 轴） | w2 重开条件原文照守·触发未启实证（pinned 在盘+零 hub 阻塞/A 峰 31.12% 单件带外缘内+零瓶颈） | m2-local-stack STT 节 + 本台账 |

### 姊妹线咬合

- 模型类零新断言=P-17 适配矩阵/P-19 管线无触发**零拉取维持**（jiwer=库非模型·纠错面零候选身份依赖）；
- AI 会话技能类零发现=P-20260926-01 技能律只供源维持；
- 发布链平台 API 类=**M5 账号物理件 blocked-on-CEO 前不评估维持**（R1034 指针照守）。

### 三律自检

礼貌节流：本切片 2 刀（搜索两刀）+本地实探零 API·窗计 6/6 帽 ✓；落点强制=结论应用表 3 行 ✓；判据预注册先立后评（脚本头注=起跑前落盘）✓；候选未读位诚实注（pycorrector 查询盲位·D1 面级判决候选无关）✓。

### 下窗指针

- **窗 5（2026-10-08 21:40 → 10-11 21:40·OH-20261008-bigstream.md 新文件=一窗一文件律）**：候选面诚实预判=**全产线面已收口**（音频轴 w4 闭/渲染基建 w3 闭/字幕排版 w3 闭/ASR 双轨 parked+度量闭/纠错面设计级闭/发布链 M5-gated）——窗 5 首切片=①M5 账号物理件若到位→发布链 API 类面解冻评估·②或新旗驱面（产线新旗先立项再采）·③或如实零发现（近零发现诚实预判维持）；≤3 刀照守。

— R1411 bm-a OSLoop·切片 2 毕
