# OH-20261017-bigstream — OSS 收获轮切片（BigStream 实体·窗 8）

- **窗**：2026-10-17 21:40 → 2026-10-20 21:40（切片 1=2026-10-19 09:5x 交付·窗 7 下窗指针③「whisperX 词锚候选」兑现）
- **实搜面**：GitHub API 匿名 search 3 刀 sort=stars top 全读（①`whisperx` total=1424 ②`whisper word timestamps` total=127 ③`lyrics forced alignment` total=20）+源码/元数据直读 4 率（whisperX alignment.py 两验：`def align(transcript: Iterable[SingleSegment], ...)` 签名+`"zh": "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"` 对齐模型行；python-lyrics-transcriber README+repo 元数据=archived 判定）。**死面如实记**：`lyrics forced alignment` 刀 total=20 全薄档（<60★：AGPL/GPL 染疫 2+无 license 2+微星 1）=歌词对齐专用直接可用件零健康档——已知词面对齐能力由通用件 whisperX 承载（通用件非死面·下窗不重跑此刀）。
- **候选**（名称·源URL·许可·契合点）：
  - **m-bain/whisperX**（https://github.com/m-bain/whisperX · BSD-2-Clause · 24,656★ · push 2026-10-18 当日活档）——VAD 分段+wav2vec2 CTC 强制对齐=词级时间戳；zh 对齐模型一等公民（DEFAULT_ALIGN_MODELS_HF 源码实读）；`align()` 收 transcript 段文本=**官方歌词可作已知词面喂入**（词面校准正身路径·非 whisper 直出依赖）。
  - linto-ai/whisper-timestamped（https://github.com/linto-ai/whisper-timestamped · AGPL-3.0 · 2,855★ · 2026-09 活）——词级+置信度备选；AGPL 染疫=禁入交付链。
  - nomadkaraoke/python-lyrics-transcriber（https://github.com/nomadkaraoke/python-lyrics-transcriber · MIT · 94★ · **archived 2026-01 deprecated**）——「Whisper 转写+官方词源（Genius/Spotify/Musixmatch/LRCLib）+纠错算法→词级同步 ASS/LRC」=用例正中同型件（范式佐证）；死档不采·后继 karaoke-gen=web 平台栈不合本地律。
  - Kdroidwin/CTCLRC（https://github.com/Kdroidwin/CTCLRC · AGPL-3.0 · 12★ · 2026-09 活）——CTC+官方歌词→LRC（Windows GUI）；AGPL 染疫=只学不搬（已知词面 CTC 路径第二佐证）。
- **五门评估**（主候选=m-bain/whisperX）：
  1. **契合门 PASS**——替谁省什么：MV 41 曲词级卡点批锚点精度（CEO 剪辑六令「whisper 词级重核」+2026-10-13 判例=本机 whisper 锚点 txt 误听严重·词面正身一律用官方歌词·whisper 仅作行级时序参考）——whisperX 已知词面 CTC 强制对齐=「官方歌词引导重对齐批」正身工具位；省=人工校听返工+错词卡点位返烧。
  2. **反重复门 PASS**——三面实测：cph4/README.md 注册表 whisperX/forced-align 零在册（grep 实录）；本司栈=faster-whisper 1.2.1 在役（无已知词面对齐能力·只信 ASR 直出）+whisper.cpp/SenseVoice parked（环境/zh 质量轴·非对齐轴）+stable-ts w6 已 reject（archived 死档）——零双建零双购。
  3. **许可门 PASS**——BSD-2-Clause（API license 字段源页级读）=交付链直用合规；zh 对齐模型=HF 公开权重 wav2vec2-large-xlsr-53-chinese-zh-cn（内部产线用）；AGPL 姊妹件全隔离在评估面未入链。
  4. **健康门 PASS**——24,656★+push 2026-10-18（当日活）+MIT docker 包装生态件在场（jim60105/docker-whisperX 458★·按需部署位）=维护与部署双健康。
  5. **成本/安全门 PASS**——本地离线（模型一次性下载后 HF_HUB_OFFLINE 律同栈在役）·CPU 可跑（wav2vec2 xlsr-53 对齐档·显存包络低于 faster-whisper large int8 2926MB 在役基准）·零 API token·零外发数据（本地音频本地对齐）。
- **采用→落点**（五门全过=候选采用·试点判据窗先立）：①司内 state/queue/tech.md 种子落位=「词面校准批工具位=whisperX 首选」（试点判据=1 曲 A/B：官方歌词引导重对齐 vs 旧 whisper 直出·词面 CER+词级卡点位对拍双读数）②消费面=MV 词面校准批（bm-a MV 会话域 lane·本循环零接触 R1745 承继——本切片只供源+评估不代跑）③cph4/README.md 注册表加行=采用 lane 批开工时随批落（跨仓写禁令·本循环单文件例外仅限本台账件·悬空发现零）。
- **parked+理由**：whisper-timestamped（AGPL 染疫·只学词级置信度思路零搬运）；python-lyrics-transcriber（archived 死档·三段链范式佐证位）；karaoke-gen（平台栈+web 面不合本地律）；CTCLRC（AGPL+GUI 形态·只学不搬）；arkhe-lyric-lock（3★ 微星·「vocal stem CTC 对齐+自评分」思路留档）；docker-whisperX（本机非 docker 车道·按需再评）。
- **本地提效注记**（P-2026-09-28-08）：whisperX=本地提效类候选（离线 CPU 可跑·省人工校听）——本窗本地提效 ≥1 义务满。
- **三律自检**：①业务契合=MV 词级卡点批真缺口实锚（CEO 六令+误听判例双源）②不重复造轮子=注册表/自栈/stable-ts 三面零重③科学使用=五门全过+试点判据窗先立（CER A/B 对拍）才入链。
- **结论应用表**：

| 发现 | 评估结论 | 应用/落点 |
|---|---|---|
| m-bain/whisperX（BSD-2·24.7k★·push 当日） | 五门全过=候选采用（试点窗待跑） | tech 队种子「词面校准批工具位」+MV 词面校准批开工 A/B 试点→注册表行 |
| linto-ai/whisper-timestamped（AGPL·2.9k★） | 染疫律 reject 入链 | 词级置信度思路留档·零搬运 |
| python-lyrics-transcriber（MIT·archived） | 健康门 reject·范式佐证 | 「转写+官方词源+纠错」三段链范式入批设计参照 |
| CTCLRC（AGPL·12★） | 染疫律 reject 入链 | 已知词面 CTC 路径第二佐证·零搬运 |
| 死面：lyrics forced alignment 专用薄档 | 换刀不重跑·通用件承载 | 零动作 |

- **姊妹线咬合注记**：模型类（wav2vec2 zh 对齐模型）=P-17 适配矩阵包络注（CPU 档 <3GB·包络内）·P-19 管线位=词面校准批 lane 排期禁自行拉模型占显存；AI 会话技能类零发现；美术资产类零发现。
- **送达注**：本切片由 BigStream OS 循环 R2378 交付·BigStream 仓 commit 消息含 P-2026-09-26-08+R2378+下一动作（P-51 双载体）；集团仓 git 面零接触（单文件落盘即值守轮可扫）。
- **下窗指针**：①词面校准批试点判据窗回执（1 曲 CER A/B 对拍读数）→注册表行+拍稿/卡点链消费注归位；②vocal stem 前置分离候选（对齐精度增益面·Demucs/uvr 系下窗细评）；③编年史批七史源面随批领（10-19 日闭窗后开）。
