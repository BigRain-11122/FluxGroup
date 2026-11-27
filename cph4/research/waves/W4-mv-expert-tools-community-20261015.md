# W4：MV 产线开源工具+中文社群提示词资产+QC 筛查面（R-20261015）｜在档关系：whisper 词锚（lyric_calibration.py 自研）、ffmpeg 装配链、q88 抽帧 QC 板、B站评论自动回复线（Nemo2011/bilibili-api 在用）均=在档基线不入表，本表只报增量
> 溯源：CEO 直令 2026-10-15「去找 MV 方方面面的专家 agent/skill/提示词/灯光/服装/导演等（github/开源社区）」·消费方=BigStream MV 产线（周杰伦 41 曲重制；ffmpeg+whisper 词锚装配@bm-a 本机、i2v 烧制@bm-c）13 席专家评审团·判据预注册：①剪辑/词锚/音乐/字幕工具②中文社群提示词库③视频 QC 工具④采用判定

## ① 在档关系与范围
- 波次范围：剪辑装配/词对齐/音乐分析/字幕件；节拍与 BGM 结构切分；视频质量 QC/崩坏筛查；GitHub 中文社群提示词资产（即梦/Seedance/HunyuanVideo/Kling）；MV 生成管线类项目。不碰：多智能体框架、SKILL.md 生态、灯光/服装/调色知识库（他波在档）。
- 三查方法：星/许可/活跃=api.github.com 官方 API 直读（A 级）；README 内容真实度=raw.githubusercontent 直读（A 级）；数据日期 2026-10-15；安装可行性未实装=下轮。

## ② 主表（仓/星/许可/最近推送/功能一句话/席位映射）
| 仓 | 星 | 许可 | 推送 | 功能一句话 | 席 |
|---|---|---|---|---|---|
| WyattBlue/auto-editor | 5,522 | Unlicense | 2026-10-14 | 自动化粗剪 CLI（自述 Effort free video editing；静音/运动剪除细节 M 级待复核） | ⑦ |
| SYSTRAN/faster-whisper | 25,863 | MIT | 2026-10-13 | whisper 的 CTranslate2 重实现：推理提速+词级时间戳 | ⑦/词锚 |
| m-bain/whisperX | 24,553 | BSD-2 | 2026-09-26 | 词级时间戳 ASR+说话人分离 | ⑦/词锚 |
| jianfch/stable-ts | 2,282 | MIT | 2026-05-30·已归档 | whisper 词级对齐——上游停更 | ⑦ |
| librosa/librosa | 8,681 | ISC | 2026-10-06 | 节拍/onset/tempo 音乐分析库 | ⑦ |
| mir-aidj/all-in-one | 860 | MIT | 2024-05-09 | allin1：BPM/节拍/强拍/功能分段边界+标签(intro/verse/chorus…)（README 直验·PyPI） | ⑦ |
| facebookresearch/demucs | 10,382 | MIT | 2024-04-24·已归档 | 人声/伴奏源分离（代码成熟） | ⑦/词锚 |
| CPJKU/madmom | 1,726 | Other(非标) | 2026-03-20 | DBN 节拍/强拍跟踪——许可非标需法务 | ⑦ |
| smacke/ffsubsync | 7,900 | MIT | 2026-07-24 | 音频指纹自动字幕同步 | ⑨/⑦ |
| Zulko/moviepy | 14,986 | MIT | 2026-08-26 | Python 化 ffmpeg 剪辑编排 | ⑦ |
| harry0703/MoneyPrinterTurbo | 131,068 | MIT | 2026-10-15 | 一键短视频全链自动化（TTS/字幕/ffmpeg 合成） | ⑦ |
| Vchitect/VBench | 1,822 | Apache-2.0 | 2026-08-21 | 生视频多维自动评估套件（CVPR24 Highlight） | ⑩/视频闸 |
| linzhiqiu/t2v_metrics | 603 | Apache-2.0 | 2026-06-05 | VQAScore：文-视频提示对齐评分 | ⑥/⑩/视频闸 |
| Emily2040/seedance-2.0 | 7,690 | MIT | 2026-10-03 | Seedance 2.0 Skill OS：镜头表→提示词→续拍/重拍协议（中英多语·README 直验） | ⑥/③/① |
| Tencent-Hunyuan/HunyuanVideo | 12,622 | NOASSERTION | 2026-10-08 | 官方 Prompt Rewrite：Normal/Master 双模提示词改写经验+改写权重（README 直验） | ⑥ |
| songguoxs/awesome-video-prompts | 588 | 无(未标) | 2025-10-18 | veo3/veo3.1/kling/hailuo 视频提示词合集 | ⑥ |
| beshuaxian/higgsfield-seedance2-jineng | 968 | 无(未标) | 2026-04-09 | 中文：Seedance 2.0×Higgsfield 15 个 prompt skill | ⑥ |
| cclank/lanshu-awesome-ai-video-kit | 421 | MIT | 2026-10-07 | 中文：企业 AI 视频工具包 411 prompt/15 模型 | ⑥/⑬ |
| BaYue-SYJ/shuixian-prompts | 402 | NOASSERTION | 2026-09-21 | 5,000+ 中文 AI 绘画提示词库（分镜图向） | ⑥/④ |

## ③ 增量评述
- 词锚生态（判据①）：whisperX=lyric_calibration.py 的词锚精度升级路径、faster-whisper=同链提速件；stable-ts 已归档判负；demucs 人声分离反哺词锚 STT 准确率（MIT 停更但成熟）。
- 节奏/结构（判据①②）：allin1 一件出 BPM/节拍/强拍/主副歌标签——41 曲批量「结构锚」与词锚构成双轴剪辑锚=剪辑节奏师最大增量；librosa 补细锚；madmom 非标许可仅借鉴；ASS 卡拉OK 字幕可由词锚自研生成交在档 ffmpeg 链烧制（方案属推测）。
- QC 面（判据③）：VBench+t2v_metrics/VQAScore 可把 q88 抽帧人工板升级为半自动视频闸；专用「AI 视频崩坏检测 agent」成熟开源件未寻得（⬜）。
- 中文社群（判据②）：Seedance 向最成熟=seedance-2.0 Skill OS（MIT·中文文档；「一镜一动作+镜尾锁线重申光/人/位」=i2v 跨镜连续性实弹经验）；Kling 向=awesome-video-prompts（无许可仅借鉴）；即梦专项提示词仓在榜未寻得（⬜；仅见 jimeng-free-api-all 625⭐ GPL-3.0 反代轮子=法务判负）。附带 A 级线索：smixs/visual-skills 516⭐ CC-BY-4.0（AI film director skills）、myccarl/ai-shortVideo-pipeline 738⭐ MIT、Dooy/chatgpt-web-midjourney-proxy 6,796⭐ MIT（kling/seedance 代理 UI）。
- MV 管线（判据⑤）：GitHub 榜未见成熟「文生 MV/歌词驱动」开源管线（⬜）——41 曲继续走自研链；MoneyPrinterTurbo「文案→TTS→字幕→素材→合成」编排可借鉴；wzk1015/video-bgm-generation 328⭐ MIT（ACM MM21 配乐生成研究件）可作音乐向参考。

## ④ 应用表（资产→席位→判定→理由）
| 资产 | 席位 | 判定 | 理由 |
|---|---|---|---|
| allin1(+librosa) | ⑦剪辑节奏师 | 直接采用 | MIT；PyPI allin1；41 曲批量出主副歌/节拍锚与词锚双轴对齐；上游低频维护可接受 |
| seedance-2.0 Skill OS | ⑥提示词工程(辅③①) | 直接采用 | MIT；Seedance 提示词范式+续拍/重拍协议+中文文档，直喂 bm-c i2v |
| whisperX+faster-whisper | ⑦/词锚校准 | 适配 | BSD-2/MIT；A/B 校验精度与速度后再切换 lyric_calibration 底座 |
| auto-editor | ⑦剪辑节奏师 | 适配 | Unlicense；素材粗剪自动化；静音/运动阈值实装复核 |
| demucs | ⑦/词锚 | 适配 | MIT(已归档)；人声分离→词锚 STT 提准；接受停更风险 |
| ffsubsync | ⑨文字设计/⑦ | 适配 | MIT；LRC/字幕同步自动化 |
| VBench | ⑩VFX 总监/视频闸 | 适配 | Apache-2.0；多维评分作闸需先标定阈值、bm-c 部署 |
| t2v_metrics(VQAscore) | ⑥/⑩/视频闸 | 适配 | Apache-2.0；提示-成片对齐分=每批烧制轻量闸 |
| HYV Prompt Rewrite | ⑥提示词工程 | 仅借鉴 | 仓为自定义社区许可且模型重——只采鉴 Normal/Master 改写经验 |
| awesome-video-prompts·higgsfield-seedance2-jineng | ⑥提示词工程 | 仅借鉴 | 均无许可标记；kling/veo3/Seedance 提示词语料参考 |
| lanshu-awesome-ai-video-kit | ⑥/⑬平台运营 | 直接采用 | MIT；中文 411 prompt 工具包贴合运营语境 |
| stable-ts·madmom·jimeng-free-api-all | ⑦/⑫法务 | 判负/仅借鉴 | stable-ts 上游 archived；madmom 许可非标；jimeng 反代 GPL-3.0+逆向=法务判负 |

## ⑤ TOP-3 采用建议+验证声明
1. **allin1**：41 曲批量跑结构分析→「结构锚 JSON」与 whisper 词锚双轴对齐，剪辑节奏师每曲省手工分段（下轮实装 3 曲样例验证）。
2. **seedance-2.0 Skill OS**：装进 ⑥席弹药位——「一镜一动作+镜尾锁线」续拍协议直对治 i2v 跨镜连续性崩坏；MIT 可改可内化。
3. **whisperX+faster-whisper**：bm-a 词锚链升级组合（对齐精度+推理速度），A/B 通过后切换。
- 验证声明：读数 19/20——外部读取 19 次调用（含 1 次批查 3 条 API 检索、1 次双仓 README 批读）；成源 18 条全 A 级（api.github.com/raw.githubusercontent 官方端点），另 1 次噪声未成源；关键结论双 A 源=API 元数据+README 直读（allin1 功能、seedance-2.0 内容真实度、HYV Prompt Rewrite）；M 级记忆处已行内标注、列入下轮实装复核。
- 失败面：search_repositories 工具 7 次解析故障（改走 api.github.com 通道后全通）；即梦搜索响应超限 1 次（shell 本地解析重查成功）；mir-aidy 404 仓名纠错 1 次；可灵中文搜索分词噪声；⬜ 崩坏检测 agent、⬜ 文生 MV 管线、⬜ 即梦提示词专项仓——三项未寻得留待下波或防线二。
- 更新记录：T0 骨架落盘→T1 词锚/剪辑件→T2 QC+社群+MV 管线→T3 README 双验→终稿 60 行；下次到期=实装验证（pip allin1/whisperx 跑 3 曲样例）+防线二抽验。
