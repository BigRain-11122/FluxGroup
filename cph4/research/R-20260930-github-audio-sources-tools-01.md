# R-20260930-github-audio-sources-tools-01 · GitHub 音频相关工具调研（取用清单）

- 调研员：E（集团后台调研）
- 日期：2026-09-30（星期三，Asia/Shanghai）
- 任务来源：CEO 令（原话）「github上有很多相关工具，调研后取用啊」
- 纪律：只调研、只写本产出文件；禁止安装/下载任何工具或音频；一切当场核实（GitHub API 实查 star/最近提交/LICENSE 文件），查不到写「未能核实」，禁止凭记忆编造；每积累 3 个候选先落盘、持续增量更新。

## 背景对齐（两份前置文件）

1. **前批判复核对象**：R-20260930-audio-sources-01 第 3 节结论「GitHub 经 12 组检索三看法复核，无可采信镜像仓库，不走 GitHub 渠道」。本次独立重查，重点找该结论的**遗漏面**——前批判只查了「Kenney 镜像 + CC0 音效资产」，未系统排查：①含音频文件的原创 CC0/MIT/CC-BY 资产仓库（非镜像）；②Freesound API 客户端工具链；③AIGC 音频合规工具（隐式标识/元数据写入/水印/防剥离校验）。
2. **合规义务基线**（R-20260930-audio-compliance-01）：《人工智能生成合成内容标识办法》（2025-09-01 已生效）下我方作为「用户/内容使用者」三义务——①提审主动声明（第十条）；②不剥离服务方写入的元数据隐式标识（第五条、第十条第二款）；③需自行补写隐式标识的情形（第九条承接）。工具判定规则：无 LICENSE=判负；GPL=本机可用+禁入发行包；MIT/Apache/BSD/CC0=可入；CC-BY=可入需署名。

## 调研范围（三组）

- **A 组**：GitHub 上托管的、实际含音频文件的可商用资产仓库（CC0/MIT/CC-BY 可商用），给许可证据链 + 内容规模估计
- **B 组**：CC0 音源平台的现成工具链——Freesound API 客户端 / 批量检索下载 / 按许可过滤（找可直接用的客户端工具，非教程）
- **C 组（重点）**：AIGC 音频合规工具——音频隐式标识与元数据写入、标识防剥离校验、音频水印（AudioSeal 类）

## 硬标准（每条目必填）

仓库真实 URL + star 数 + 最近维护时间 + LICENSE 实查（MIT/Apache/BSD/CC0=可入；GPL=本机用途+标注禁入发行包；无 LICENSE=判负）+ 平台（Windows/CLI/Python 可自动化）+ 接线点（直用台账/合规 manifest/AIGC 标识链）+ verdict（取用/观察/判负）+ 一句话原因。

## 0. 结论速览

**一句话**：CEO 令方向正确——GitHub 的价值不在「音源仓库」而在「工具」。A 组（音频资产仓库）经独立重查**维持前判**（GitHub 无合格件，资产走 kenney.nl 一手源）；B 组与 C 组合计挖出 **6 个「取用」级现成工具**，其中 C 组（AIGC 合规工具链）是本次最高价值发现：《标识办法》三义务全部有现成执行载体（C2PA 官方件写隐式标识+核验、exiftool 元数据 dump、AudioSeal/Perth 鲁棒水印），全部当天可接线。

- **A 组**：`q=cc0 sound effects` 全部 12 命中 star≤1、无标准 LICENSE 文件；`topic:game-audio` 头部全是引擎工具；OGA 名件无 GitHub 镜像 → **前批判成立，资产采购不走 GitHub**。
- **B 组**：**MTG/freesound-python（MIT 原文已核，官方出品，star 157）** 取用——freesound CC0 批量检索下载的唯一稳健件；MCP 封装 sfx-mcp 观察。
- **C 组**：**c2pa-python / c2patool（Apache-2.0，Adobe 主导官方件，Windows 预编译实测在 Releases）**＋ **exiftool（GPL 本机用，star 5108）** ＋ **AudioSeal（MIT，Meta，star 791）/ Perth（MIT 原文已核，star 536，本月活跃）**——三义务工具链齐活；另发现 23k star 级**标识剥离工具生态**（威胁情报：元数据是软标识，必须「元数据+水印+显式提示」三层叠加）。
- **风险注记**：GB 45438-2025 量化字段未能直引（前批判已声明），C2PA manifest 与国标三要素的字段映射落地时做一次对照表；GPL 件（exiftool/mutagen/audiowmark）一律「本机 CLI 用、禁入发行包」。

---

## A. GitHub 可商用音频资产仓库（复核前批判「无合格件」）

> 检索面（2026-09-30 GitHub API 实测）：`q=cc0+sound+effects`（12 命中）、`q=512+sound+effects`（0 命中）、`q=subspaceaudio+sound`（0 命中）、`q=topic:game-audio`（162 命中，按 star 降序取前 15）、`q=opengameart`（105 命中，按 star 降序取前 10）。

### A0. 复核结论（对照前批判）

1. **前批判结论在「资产面」成立**：`q=cc0 sound effects` 全部 12 个命中仓库 star≤1、多为 2026 年新建的 MCP/小包；`topic:game-audio` 的头部仓库（Godot-Mixing-Desk 672★、bevy_kira_audio 473★、wwise-godot-integration 446★）**全部是音频引擎/中间件代码，无一是音频资产仓库**；`q=opengameart` 头部无音效镜像（最高分是像素搜索/贴图数据集）。OGA 名件「512 Sound Effects (8-bit style)」与「SubspaceAudio」在 GitHub **零命中**（无官方镜像）。
2. **一个补充发现（前批判未覆盖）**：GitHub 上 CC0 声明的小音效库确实存在若干新件（如 blip8-sounds 181 件、sfxmint 4,600+ 件索引），但**全部卡在「无标准 LICENSE 文件」或「star=0」上，按硬标准无一入格**。判负理由逐条列于 A1。
3. **对吸嘟嘟的资产面裁定**：维持前判——**采购音频资产不走 GitHub 渠道，走 kenney.nl/freesound/OGA 一手源**；GitHub 的价值在 B 组（工具链）和 C 组（合规工具），这正是 CEO「GitHub 有很多相关工具」的正确打开面。

### A1. 最接近「合格」的候选（逐个否决/观察）

| 条目 | 实测数据 | 核查与裁定 |
|---|---|---|
| **sindriax/blip8-sounds** | https://github.com/sindriax/blip8-sounds · star **0** · push 2026-08-20 · license：**NOASSERTION**（无标准许可文件；README/topics 自述 CC0、public-domain）· 181 件 Python 脚本合成 chiptune | 描述原文："181 CC0 chiptune sound effects for games, generated from one Python script. No samples, no recordings. Commercial use, no attribution required." **verdict：判负**——star=0 且无标准 LICENSE 文件（按合规基线无 LICENSE=一律不用）；MIT 基线可破例的唯一情形是「标准许可文件在场」，本案不满足 |
| **flreey/sfxmint-mcp** | https://github.com/flreey/sfxmint-mcp · star **0** · push 2026-09-26（活跃） · license：**CC0-1.0**（API 检测，repo 有标准许可文件） · 描述："Free CC0 sound effects MCP server… search 4,600+ sounds. Permanent hotlinkable MP3/WAV, no API key." | **verdict：观察**——许可文件本身合规（CC0-1.0），但 ① star=0 ② 音源托管在 sfxmint.com 外部服务，逐件许可真实性未核（「自称 CC0」的平台需抽验单件许可标注）③ MCP 形态需 Codely/Claude 接入。若未来接 MCP 采购链，先抽验其平台上 5–10 件的单件许可标注再定 |
| **Daarko/sparkstream-sounds** | https://github.com/Daarko/sparkstream-sounds · star **0** · push 2026-07-02 · license：**无（null）** · 描述："Curated CC0 sound library for SparkStream (521 free, commercial-safe sound effects)" | **verdict：判负**——无 LICENSE 文件；「commercial-safe」仅是 README 自述，无许可文本载体 |
| **novincode/atomcut-library** | https://github.com/novincode/atomcut-library · star **0** · push 2026-09-17 · license：**无（null）** · 描述："The CC0 content behind AtomCut's Library — 700 public-domain sound effects" | **verdict：判负**——同上，无 LICENSE 文件，声明的公共领域无证据载体 |
| **smartpage/strongerfx-mcp** | https://github.com/smartpage/strongerfx-mcp · star **0** · push 2026-09-15 · license：**NOASSERTION** · 描述："254 CC0 sound effects with searchable metadata, local MCP server and Apify delivery actor" | **verdict：判负**——无标准许可文件 |
| **RezaParsian/free-sfx-bgm-pack** | https://github.com/RezaParsian/free-sfx-bgm-pack · star **0** · push 2026-09-15 · license：**NOASSERTION** · 31 SFX + 8 BGM 代码合成件 | **verdict：判负**——同上（前批判已列名，本次复核确认） |
| **sandraschi/sfx-mcp** | https://github.com/sandraschi/sfx-mcp · star **1** · push 2026-09-14 · license：**MIT** · 描述："Sound Effects MCP server — FreeSound API wrapper. CC0 SFX search, download, tag, local cache." | **verdict：观察（归入 B 组）**——MIT 合规、正对「Freesound CC0 过滤检索下载」场景，但 star=1、2026-07 新建；作为 freesound-python 的 MCP 封装备选记录，非首选 |
| Calinou/kenney-ui-audio 等 Kenney 镜像 | 前批判已逐仓三看（Calinou 25★ 停更 6 年、Boyquotes 0★、iwenzhou 5★ 停更 10 年），本次经 `q=cc0 sound effects`/`topic:game-audio` 复核未见新的高 star Kenney 音频镜像 | **verdict：维持前判不采**——镜像证据链弱于 kenney.nl 一手源 |

> A 组否决共性一句话：**GitHub 上「能直接下载的 CC0 音频」要么是 kenney.nl 的二手镜像，要么是 star=0、无标准 LICENSE 文件的自述 CC0 小仓库——许可证据链全部弱于一手源。**

---

## B. CC0 音源平台工具链（Freesound API 客户端 / 批量检索下载 / 许可过滤）

> 检索面（2026-09-30 实测）：`q=freesound`（536 命中，按 star 降序取前 10）＋ `q=cc0 sound effects` 中交叉发现的 MCP 件。

### B1. 候选清单

| 条目 | 实测数据 | 核查与裁定 |
|---|---|---|
| **MTG/freesound-python** | https://github.com/MTG/freesound-python · star **157** · 最近 push **2025-12-23**（updated 2026-09-15） · license：**MIT**（**LICENSE 原文实查**：repo 内 `COPYING.txt` 首行 "The MIT License (MIT)"，版权行 "Copyright (c) 2013-2014 Universitat Pompeu Fabra"） · Python | 描述："python client for the freesound API"。**MTG = Music Technology Group（UPF，巴塞罗那庞培法布拉大学）＝ freesound.org 的运营方**，即官方客户端。**批量能力实查**：repo 根目录自带 `examples.py`（官方示例演示 `search(query=…, filter=…, sort=…)` 过滤检索机制，filter 语法如 `tag:tenuto duration:[1.0 TO 15.0]`）与 `download_bookmarks_example.py`（书签批量下载示例）。许可过滤沿用 freesound 官方 filter 语法 `filter='license:"Creative Commons 0"'`（与 audio-sources-01 已实测的网页端 `f=` 参数同源；examples.py 未直接演示 license 字段，落地首次调用时验证一次即可）。平台：Python 3，API key 自动化。**接线点**：按 CC0 过滤检索 → 批量下载 → API 响应自带的来源 URL/作者/许可三字段直接喂台账。**verdict：取用**——B 组唯一官方出品 + MIT（原文已核）+ 维护中，freesound CC0 采购链首选 |
| **MTG/freesound** | https://github.com/MTG/freesound · star **384** · push 2026-09-28 · license：**AGPL-3.0** · Python | 描述："The Freesound website"——freesound.org 站点本身的源码，**不是客户端工具**。**verdict：判负**——AGPL 传染性许可 + 非工具（对我方用途无用） |
| **g-roma/freesound.js** | https://github.com/g-roma/freesound.js · star **62** · push 2026-08-13 · license：**无（null）** · JavaScript | 描述："javascript client for the freesound.org API"。**verdict：判负**——无 LICENSE 文件=默认保留所有权利（合规基线红线）；且 JS 客户端对我方 Windows/Python 管线无增益 |
| **futurice/freesound-android** | https://github.com/futurice/freesound-android · star **86** · push **2021-11-19**（停更 ~5 年） · license：**Apache-2.0** · Java | 非官方 Android 浏览客户端。**verdict：判负**——用途不符（手机端 app ≠ 采购管线工具）＋停更 |
| **sandraschi/sfx-mcp** | https://github.com/sandraschi/sfx-mcp · star **1** · push 2026-09-14 · license：**MIT** · Python | 见 A1 表。**verdict：观察**——Freesound API 的 MCP 封装（CC0 过滤/下载/本地缓存 5 操作），star=1 太新；若主会话走 Codely MCP 采购可试，稳健路线仍走 freesound-python |
| **numberoverzero/oga** | https://github.com/numberoverzero/oga · star **3** · push 2026-03-21 · **archived=true** · license：**MIT** · Python | 描述："A simple tool to search and download assets from OpenGameArt.org"。**verdict：判负**——官方已归档（archived=true 无维护）＋ star=3；OGA 检索继续用网页高级搜索（audio-sources-01 已给参数）即可 |
| **emnh/PixelArtSearch** | https://github.com/emnh/PixelArtSearch · star **93** · push 2023-07-24 · license：**无（null）** · Python | OGA 像素画搜索引擎（在线 ogasearch），非音频。**verdict：判负**——无 LICENSE + 非音频用途 |

### B2. B 组小结

- **可直接用的现成客户端=MTG/freesound-python（取用）**；MCP 封装 sfx-mcp 为观察备选。
- freesound-python 的许可过滤检索能力经 API 官方支持（`filter=license:"Creative Commons 0"`），与 audio-sources-01 第 2.1 节网页参数法一致——工具与既有采购方案无缝衔接。
- OGA 侧无合格 CLI 工具（唯一件已归档）→ OGA 维持网页逐件采购。

---

## C. AIGC 音频合规工具（隐式标识 / 元数据写入 / 水印 / 防剥离校验）

> 对应我方三义务：①入包前**自行补写隐式标识**（元数据：生成合成内容属性 + 服务提供者名称/编码 + 内容编号，对应《标识办法》第五条与 GB 45438-2025）；②**不剥离**上游服务方已写入的元数据（第十条第二款）；③校验环节证明标识在位。以下数据均为 2026-09-30 GitHub API 实测（star 数、pushed_at、license 由 GitHub API 返回）。

### C1. 音频水印（AI 生成件防剥离/溯源用）

| 条目 | 实测数据 | 核查 |
|---|---|---|
| **facebookresearch/audioseal** | https://github.com/facebookresearch/audioseal · star **791** · 最近 push **2026-05-19**（updated 2026-09-29） · license：**MIT（LICENSE 原文实查：首行 "MIT License"，版权行 "Copyright (c) Meta Platforms, Inc. and affiliates."）** · 语言 Python | 描述："Localized watermarking for AI-generated speech audios, with SOTA on robustness and very fast detector"（本地化音频水印 + SOTA 检测器，Meta 官方）。平台：Python/torch，CLI 可自动化。**verdict：取用**——MIT + 水印生成与鲁棒检测一体，正对「AI 音频入包前打标、入包后校验」两个接线点 |
| **resemble-ai/Perth** | https://github.com/resemble-ai/Perth · star **536** · 最近 push **2026-09-02**（活跃维护中） · license：**MIT（LICENSE 原文实查：版权行 "Copyright (c) 2025 Resemble AI"）** · 语言 Python | 描述："Open Audio Watermarking Tool"（Resemble AI 公司官方开源，该公司主营 AI 语音合成）。平台：Python，pip 可装。**verdict：取用（观察备用）**——活跃度最高（本月有 push）的 MIT 音频水印件，可与 AudioSeal 二选一或组合 |
| **swesterfeld/audiowmark** | https://github.com/swesterfeld/audiowmark · star **595** · 最近 push **2026-09-23**（活跃） · license：**GPL-3.0**（API 检测） · 语言 C++ | 描述："Audio Watermarking"（经典 FFT 域水印 CLI）。平台：C++ CLI（Windows 无官方预编译，需自行编译）。**verdict：观察（GPL）**——本机 CLI 用途可行，但 GPL **禁入发行包/禁止代码链接**；且该件是「水印」不是「元数据标识」，与 GB 45438 的隐式标识规范非同构 |
| **wavmark/wavmark** | https://github.com/wavmark/wavmark · star **321** · 最近 push **2024-01-07**（停更 ~2.7 年） · license：**MIT**（API 检测） · 语言 Python | 描述："AI-based Audio Watermarking Tool"（ICASSP 2023 论文官方件）。**verdict：观察**——MIT 可入，但停更近 3 年、无 issue 响应保障，被 AudioSeal/Perth 覆盖 |
| **facebookresearch/content-seal** | https://github.com/facebookresearch/content-seal · star **243** · 最近 push **2026-07-08** · license：**MIT**（API 检测） · 语言 HTML（研究框架+文档站） | 描述："invisible, robust watermarking across all modalities audio, image, video, and text… spans the entire generative lifecycle"（全模态水印框架，2025-12 新发布）。**verdict：观察**——方向最正（覆盖生成全生命周期 provenance），但太新（star<300、工具化程度待验），列为 AudioSeal 的未来升级路线 |
| **LSXPrime/SoundFlow** | https://github.com/LSXPrime/SoundFlow · star **516** · 最近 push **2026-05-11** · license：**MIT**（API 检测） · 语言 C#/.NET 8+ | 描述：.NET 音频引擎，含 "security suite for AES-256 encryption, acoustic fingerprinting, and watermarking"。**verdict：观察**——对单一音频标识任务过重（整是 DAW 级引擎），仅当吸嘟嘟走 .NET 工具链时再评估 |
| **zy445566/node-digital-watermarking** | https://github.com/zy445566/node-digital-watermarking · star **343** · 最近 push **2026-08-11** · license：**MIT**（API 检测） · 语言 JavaScript | 描述：通用数字水印（图像为主，音频支持存疑）。**verdict：判负**——与音频标识链匹配度低，README 自述以图像 LSB 为核心 |
| **ktekeli/audio-steganography-algorithms** | https://github.com/ktekeli/audio-steganography-algorithms · star **286** · 最近 push **2023-11-07** · license：**MIT**（API 检测） · 语言 **MATLAB** | 描述：音频隐写/水印算法库。**verdict：判负**——MATLAB 平台不可自动化入我方管线（硬标准平台项不过） |
| **Jpinsoft/DeepSound** | https://github.com/Jpinsoft/DeepSound · star **338** · 最近 push **2026-09-15** · license：**无 LICENSE 文件**（API 返回 license:null） · C#/WPF GUI | 描述：音频隐写 freeware（WAV/FLAC 藏数据）。**verdict：判负**——无 LICENSE=按合规基线一律判负（freeware ≠ 可商用许可），且 GUI 不利自动化 |

### C2. 元数据隐式标识写入/核验（对应《标识办法》第五条 + GB 45438-2025）

| 条目 | 实测数据 | 核查与裁定 |
|---|---|---|
| **contentauth/c2patool** | https://github.com/contentauth/c2patool · star **137** · 最近 push **2026-09-29**（当日仍在提交） · license：**Apache-2.0**（API 检测） · Rust CLI | 描述："Command line tool for displaying and adding C2PA manifests"。**contentauth = Content Authenticity Initiative 官方组织（Adobe 主导）**。C2PA = 内容凭证标准，把「生成来源/动作/签署者」清单签入媒体文件元数据（manifest），与《标识办法》隐式标识的「内容属性+服务提供者编码+内容编号」三要素高度同构。**接线点**：AI 音频入包前 `c2patool add` 写入含「AI 生成」训练/生成动作声明的 manifest；核验环节 `c2patool inspect` 读回——一步覆盖「自行补写隐式标识」与「防剥离校验」两义务。**平台实测**：v0.28.1（2026-09-28 发布）Releases 含 `v0.28.1-x86_64-pc-windows-msvc.zip` **Windows 预编译二进制**（另有 darwin/linux）。**verdict：取用**——官方出品、Apache-2.0、维护活跃（最新版发布于调研日前 2 天）、Windows 开箱可用 |
| **contentauth/c2pa-python** | https://github.com/contentauth/c2pa-python · star **105** · push **2026-09-29** · license：**Apache-2.0**（API 检测） · Python（pip 包） | 描述："Python binding for c2pa-rs library"。同一能力的 Python 绑定，适合嵌入采购/入包管线脚本。**verdict：取用**——与 c2patool 二选一或组合（Python 管线选它，纯 CLI 选 c2patool） |
| **contentauth/c2pa-rs** | https://github.com/contentauth/c2pa-rs · star **424** · push **2026-09-29** · license：**双许可，repo 内 LICENSE-APACHE 与 LICENSE-MIT 两个文件在场（实查文件列表确认；API 因此返回 NOASSERTION）** · Rust SDK | 描述："Rust SDK for the core C2PA specification"。上两件的底层引擎，含 `make_release.ps1`/`setup-rust-openssl.ps1`（Windows PowerShell 支持脚本在场）。**verdict：观察（取用的依赖项）**——除非自研 Rust 工具，一般直接用 c2patool/c2pa-python 即可，无需直接动 SDK |
| **exiftool/exiftool** | https://github.com/exiftool/exiftool · star **5108** · push 2026-05-27 · license：**GPL-3.0**（API 检测；官网 exiftool.org，Perl） | 描述："ExifTool meta information reader/writer"——媒体元数据读写的业界基线工具（XMP/ID3/MP4 容器全支持）。**接线点**：①入包前对每件音频 dump 全量元数据（`-a -G1 -s`）核验「上游标识是否在场/被剥离」；②用 `-XMP:xxx<=` 写自定义字段补隐式标识（GB 45438 元数据字段的兜底写法）；③台账「元数据快照」列的直接证据来源。**verdict：取用（本机用途）**——GPL **禁入发行包/禁止代码链接**，仅作独立 CLI 调用（CLI 进程调用不构成衍生作品），在台账注明 GPL 属性 |
| **quodlibet/mutagen** | https://github.com/quodlibet/mutagen · star **1964** · push 2026-08-20 · license：**GPL-2.0**（API 检测） · Python 库 | 描述："Python module for handling audio metadata"（ID3/MP4/FLAC/OGG/Opus/APEv2 全格式标签读写）。**verdict：取用（本机用途）**——仅限内部脚本 import（内部使用不分发即不触发 GPL 义务）；**红线：不得 import 进游戏/发行代码**；与 exiftool 功能重叠时优先 exiftool（CLI 隔离更干净） |
| c2pa-org/specifications | https://github.com/c2pa-org/specifications · star **210** · push 2026-09-16 · license：**CC-BY-4.0**（API 检测） · 规范文档 | C2PA 规范正文。**verdict：观察（参考资料）**——落地时核对 GB 45438-2025 与 C2PA 字段映射，属文档不是工具 |

### C3. 威胁情报：标识剥离工具生态（非取用件，列此证明「防剥离」是真实威胁面）

| 条目 | 实测数据 | 说明 |
|---|---|---|
| guillaumemeyer/watermarks-remover | https://github.com/guillaumemeyer/watermarks-remover · star **23095**（！2026-08 新建即爆红） · push 2026-09-28 · MIT · Python | 描述："A privacy-first app that strips AI watermarks from content you own." **剥离类工具已有 23k star 级生态** |
| wiltodelta/remove-ai-watermarks | https://github.com/wiltodelta/remove-ai-watermarks · star **5718** · push 2026-09-30（当日） · Apache-2.0 · Python 库+CLI | 描述原文："Remove visible and invisible AI watermarks and provenance metadata from images and video… **SynthID, C2PA, EXIF, IPTC, XMP**"——**C2PA/EXIF/XMP 元数据均在其剥离清单内** |
| mertizci/noai-watermark | https://github.com/mertizci/noai-watermark · star **193** · push 2026-09-16 · MIT · Python CLI | 同类（SynthID/StableSignature/TreeRing 图像水印剥离） |

> **C3 对吸嘟嘟的三条操作结论**：
> 1. **元数据隐式标识是「软标识」**——成熟工具一键剥离（连 C2PA、SynthID 都被点名支持），《标识办法》第五条「鼓励数字水印」的双轨设计是必要的：**我方 AI 件 = 元数据标识（合规基线）+ AudioSeal/Perth 类鲁棒水印（增强层）+ 游戏内显式提示（硬义务）**，三层叠加。
> 2. **我方红线**：任何管线环节禁止引入上述剥离工具（自用「清洗」也不行——《标识办法》第十条第二款明令「不得恶意删除、篡改、伪造、隐匿标识」；服务方写入的元数据必须原样保留过审）。
> 3. **核验视角**：`exiftool` dump + `c2patool inspect` + AudioSeal 检测器三件组合，即「防剥离校验」闭环——入包前全部读回一遍，结果进台账。

### C4. C 组小结

- **可直接落地的组合拳（全部实查许可）**：`c2pa-python`/`c2patool`（Apache-2.0，写隐式标识+核验）＋ `exiftool`（GPL 本机用，元数据 dump/兜底写入）＋ `audioseal`（MIT，鲁棒水印+检测）或 `Perth`（MIT，活跃度更高）。
- **判负/观察件**：GPL 的 audiowmark（本机可 CLI 用但非必需）、停更的 wavmark、平台不符的 MATLAB 件、无 LICENSE 的 DeepSound、过重的 SoundFlow。
- **风险注记**：GB 45438-2025 的元数据字段格式以标准正文为准（前批判已声明未能直引量化条款）——C2PA manifest 与国标字段并非逐字对应，落地时需做一次字段映射表（元数据写「生成合成内容属性+服务提供者名称或编码+内容编号」三要素），c2patool/exiftool 都是执行载体，不是标准本身。

---

## Top 取用建议（按接线价值排序）

> 排序依据＝「对 compliance-01 合规义务的覆盖 × 对 audio-sources-01 采购链的增益 × 许可/维护实测强度」。

| # | 工具 | 许可（实查） | 接线点 | 一句话理由 |
|---|---|---|---|---|
| 1 | **contentauth/c2pa-python**（或同门 CLI **c2patool**） | Apache-2.0 · star 105/137 · push 2026-09-29 · Windows 预编译实测 | **AIGC 标识链（核心）**：AI 音频入包前写含生成动作声明的 C2PA manifest（对应义务③「自行补写隐式标识」）；`inspect` 读回核验（对应义务②防剥离校验）；台账「AI 元数据标识确认」字段由它产出 | 把 compliance-01 A3/A5 两条人工动作变成一行命令；官方（Adobe/CAI）+ 当周仍在发版 + Windows 开箱即用，全 C 组无出其右 |
| 2 | **exiftool/exiftool** | GPL-3.0（**本机 CLI 用，禁入发行包/禁止代码链接**） · star 5108 · push 2026-05-27 | **合规 manifest + 标识链（核验）**：入包前逐件 dump 全量元数据，核验上游服务方标识在场未剥离；台账存元数据快照；GB 45438 字段的兜底写入（XMP） | 元数据核验的行业基线（20 年事实标准），GPL 红线用「独立进程调用」隔离即可，零成本接入 |
| 3 | **facebookresearch/audioseal** | **MIT（LICENSE 原文实查："Copyright (c) Meta Platforms, Inc. and affiliates."）** · star 791 · push 2026-05-19 | **AIGC 标识链（增强层）**：对 AI 生成音频打不可感知鲁棒水印，检测器校验标识存活——对应《标识办法》第五条「鼓励数字水印」+ C3 威胁面（元数据可被剥离，水印是第二道保险） | Meta 官方、水印+检测一体、MIT 无接入顾虑；音效/BGM 均适用 |
| 4 | **MTG/freesound-python** | **MIT（COPYING.txt 原文实查："Copyright (c) 2013-2014 Universitat Pompeu Fabra"）** · star 157 · push 2025-12-23 | **采购链**：CC0 过滤批量检索 + 批量下载（官方批量示例在场）→ API 响应自带来源/作者/许可三字段直喂台账——audio-sources-01 第 7 节 Step 4「补缺采购」的自动化载体 | freesound.org 运营方官方出品，与已验证的网页端 `license:"Creative Commons 0"` 过滤同源，逐件人工核验成本从「逐件」降为「首次调用验证一次」 |
| 5 | **resemble-ai/Perth** | **MIT（LICENSE 原文实查："Copyright (c) 2025 Resemble AI"）** · star 536 · push 2026-09-02（活跃） | AudioSeal 的**平行备份**：同为 MIT 音频水印，Resemble AI（AI 语音厂商）官方维护 | 与 AudioSeal 二选一或互为备份，谁先跑通用谁；活跃度（本月 push）优于 AudioSeal |
| 6 | **quodlibet/mutagen** | GPL-2.0（**仅内部脚本 import，禁止进发行代码**） · star 1964 · push 2026-08-20 | 管线脚本内读写 ID3/MP4/FLAC/OGG 标签 | exiftool 的 Python 内嵌替代品，仅当脚本需要库级操作时用；CLI 隔离场景下优先 exiftool |
| 7 | 观察：facebookresearch/content-seal（MIT · 243★ · 全模态水印框架）、sandraschi/sfx-mcp（MIT · Freesound MCP 封装）、flreey/sfxmint-mcp（CC0-1.0 · 4,600 件 CC0 音库 MCP，音源平台许可真实性未抽验） | — | 未来升级路线 | 全部 star<300 或 star=1，先记录不接入 |

**接线总图**（采购→入包→提审三段）：

```
采购段（下载件）：freesound-python(CC0过滤批量下载) → kenney.nl 官方包（前批判清单）
入包段（AI 件）：audioseal/Perth 打水印 → c2pa-python 写隐式标识 manifest → exiftool dump 核验快照
                （下载件）：exiftool dump 核验上游标识在场（AI 下载件）→ LICENSE 归档（前批判四件套）
提审段：台账一行一音频（元数据快照列=exiftool 产出；AI 标识列=c2patool inspect 产出）→ 5 分钟出示能力
```

**给 CEO 的一句话**：GitHub 上「能商用的音频文件」没有合格件（一手源还是 kenney.nl/freesound），但「让音频合规的工具」全是硬货——C2PA 官方件+exiftool+AudioSeal 三件套把《标识办法》三义务变成三条命令，freesound-python 把 CC0 补缺采购自动化；以上 6 件全部许可实查通过，可按 Top 表直接取用。

---

状态：完成
（2026-09-30 · 调研员E；三组检索面全部 GitHub API 当场实测，取用级候选 LICENSE 原文全部直引；未安装/下载任何工具或音频，未改动本文件以外任何文件）
