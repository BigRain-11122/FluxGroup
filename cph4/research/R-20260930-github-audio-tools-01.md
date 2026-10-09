# R-20260930 GitHub 游戏音频管线开源工具调研（第 1 轮）

- **调研日期**：2026-09-30（周三，Asia/Shanghai）
- **调研员**：Codely CLI 调研代理（FluxGroup 游戏公司）
- **CEO 令（原话）**：「github上有很多相关工具，调研后取用啊」
- **产出面**：本文件为唯一产出文件；未执行任何安装/下载（无 pip install / git clone / npm），未改动本文件以外的任何文件
- **数据来源**：GitHub REST API / 仓库页 / LICENSE 文件当场直读（`search_repositories` MCP 通道故障，改走 api.github.com 直读，数据等价）；查不到的字段标「未能核实」或「待证」

## 评估基准（我方音频管线实况，评估适配用）

- 自研工具链：`MiniGame/tools/AudioMasterFix.ps1`（ffmpeg 母带：双遍 loudnorm 归一 / 1024 样本头垫 / smpl 循环点 / atempo 修 30s 窗 / 压缩回退）+ `tools/AudioGateCheck.ps1`（验收门）
- 验收标准（14 号）：SFX -16 LUFS·真峰值≤-3dBTP·0.02–8s·44.1kHz mono；BGM -18 LUFS·30–60s·WAV+smpl 循环+头垫；微信小游戏 WebGL 构建统一转码 AAC
- 既有生产路线（音频采购三分律·已立法）：存量重母带（不重造）+ Kenney CC0 池直用 + TJ 云端 AI 定制——**GitHub 工具的价值 = 本地补充 / 交叉验证 / 提效，非替代**

## 调研范围（五组）

- A. 程序化/算法音效生成器（sfxr 家族、ChipTone 类开源替代、可批量 CLI）
- B. 响度/母带处理与测量（pyloudnorm、Matchering、librosa/essentia、SoX、LAME gapless、ffmpeg 封装、smpl 写入）
- C. 循环点检测/无缝循环/静音修剪/批处理自动化
- D. 音频 QC 取证（削波检测、频谱/波形图、批量体检）
- E. 本地音乐生成（MusicGen/audiocraft 类，许可面严审）

## 硬判据（每条目全字段，当场核实）

1. 仓库真实 URL（github.com/owner/repo）+ star 数 + 最近 commit/release 时间
2. 许可（LICENSE 实查）：MIT/Apache/BSD/CC0/Zlib/MPL = 可入工具链；GPL = 本机工具可用但标注「禁入发行包」；**无 LICENSE = 判负**
3. 平台：Windows 本机可跑 + CLI/Python 可自动化（GUI-only 单独标注）
4. 接线点：接到我们哪个环节（MasterFix / GateCheck / 生成互补 / 微信包面）
5. verdict：**取用 / 观察 / 判负** + 一句话原因

## 速览总表

| # | 组 | 工具 | Stars | 许可 | 最近活动 | verdict |
|---|---|---|---|---|---|---|
| A1 | A | rfxgen（raysan5/rfxgen） | 512 | Zlib | 2026-08 | 取用 |
| A2 | A | sfxr-qt（agateau/sfxr-qt） | 92 | MIT | 2024-06 | 取用 |
| A3 | A | jsfxr（chr15m/jsfxr） | 451 | Unlicense | 2026-05 | 取用 |
| A4 | A | bfxr（increpare/bfxr） | 1026 | 无LICENSE | 2025-04 | 判负 |
| A5 | A | usfxr（zeh/usfxr） | 366 | 无LICENSE·归档 | 2019-01 | 判负 |
| B1 | B | pyloudnorm（csteinmetz1/pyloudnorm） | 783 | MIT | 2026-01 | 取用 |
| B2 | B | matchering（sergree/matchering） | 2648 | GPL-3.0 | 2026-07 | 观察 |
| B3 | B | librosa（librosa/librosa） | 8637 | ISC | 2026-09 | 取用 |
| B4 | B | essentia（MTG/essentia） | 3753 | AGPL-3.0 | 2026-09 | 判负 |
| B5 | B | ffmpeg-normalize（slhck/） | 1538 | 待证 | 2026-09 | 观察 |
| B6 | B | SoX 镜像（chirlu/sox） | 966 | GPL/LGPL系 | 2023-11 | 观察 |
| B7 | B | LAME 镜像（lameproject/lame） | 22 | LGPL·镜像死档 | 2020-12 | 判负 |
| C1 | C | crosslooper（Splendide-Imaginarius/） | 4 | GPL-3.0 | 2024-07 | 观察 |
| C2 | C | LoopAuditioneer（GrandOrgue/） | 14 | GPL-3.0 | 2026-03 | 观察 |
| C3 | C | loopy（ps1dev/loopy） | 0 | 无LICENSE | 2026-09 | 判负 |
| C4 | C | SMPL-makr（conradzeus/） | 1 | 无LICENSE | 2024-09 | 判负 |
| C5 | C | loop-ogg（SolraBizna/） | 0 | 无LICENSE | 2022-12 | 判负 |

## A 组：程序化/算法音效生成器

> 结论先行：sfxr 族「捏底料」价值成立——但按硬判据，**有 LICENSE 的只有 rfxgen(Zlib)/sfxr-qt(MIT)/jsfxr(Unlicense)**；经典 bfxr/usfxr 均因无 LICENSE 判负。全部为 GUI/网页工具（无现成 CLI 批量），定位=人手捏音底料 → 出 WAV → 进 MasterFix 归一，不碰验收门。对「卡通休闲风 SFX」：sfxr 系偏复古/8bit 质感，适合 UI 音/拾取/跳跃等短促卡通音，写实音效仍走 TJ 云端 AI 定制。

### A1. rfxgen（rFXGen）——sfxr 族首选
- URL：https://github.com/raysan5/rfxgen
- Stars：512 · 语言 C · 最近 push 2026-08-13（活跃）· itch.io 官方发布 v5.0（raylibtech.itch.io/rfxgen）
- 许可：**Zlib**（GitHub API 实查 license.spdx_id=Zlib）→ 可入工具链
- 平台：Windows/Linux 独立版（itch.io 下载）+ WASM 网页版；**GUI-only，无官方 CLI**
- 接线点：SFX 生成互补——Kenney 池外的本地捏音底料（多音色槽/过滤/包络），出 WAV 后进 MasterFix 双遍 loudnorm
- verdict：**取用**——zlib 无忧+持续维护+Windows 独立版零依赖，是 sfxr 族里许可与活跃度最优解

### A2. sfxr-qt——MIT 现代界面备选
- URL：https://github.com/agateau/sfxr-qt
- Stars：92 · 语言 C++(Qt) · 最近 push 2024-06-23 · 最近 release 1.5.1（2024，agateau.com 官宣）
- 许可：**MIT**（API 实查）→ 可入工具链
- 平台：Windows/Linux 二进制（Releases 页提供）；**GUI-only**
- 接线点：同 A1，捏音底料备选；作者为知名 Qt 维护者，代码干净
- verdict：**取用**——MIT 备选捏音器，功能与原版 sfxr 等同、界面更顺手

### A3. jsfxr——网页速捏 + Unlicense
- URL：https://github.com/chr15m/jsfxr（fork 自 grumdrig/jsfxr，在线版 sfxr.me）
- Stars：451 · 语言 JavaScript · 最近 push 2026-05-05
- 许可：**Unlicense（公有领域）**（API 实查）→ 可入工具链
- 平台：纯网页（sfxr.me），浏览器即用；核心为 JS，理论可 Node 包装批量（**待证**，无现成 CLI）
- 接线点：策划/开发零安装速出音底料 WAV；购物车音/按钮音等卡通 UI 短音极快
- verdict：**取用**——Unlicense 零负担+零安装，当「速用秤」；批量自动化不足，定位为灵感/占位音源

### A4. bfxr——经典但因无 LICENSE 判负
- URL：https://github.com/increpare/bfxr
- Stars：1026 · 语言 ActionScript（Flash+AIR）· 最近 push 2025-04-17 · API license=null
- 许可：**无 LICENSE**（根目录 LICENSE 文件 404 实测，API license=null）→ 按硬判据**判负**
- 平台：Flash/AIR 已技术死亡，Windows 跑老版需 AIR 环境
- 接线点：无（判负）
- verdict：**判负**——无 LICENSE 文件触发红线；且 Flash 技术栈已废，rfxgen 完全覆盖其功能

### A5. usfxr——Unity 运行时合成思路好，但无许可+已归档
- URL：https://github.com/zeh/usfxr
- Stars：366 · 语言 C# · 最近 push 2019-01-22 · **archived=true** · API license=null
- 许可：**无 LICENSE**（根目录 LICENSE 404 实测；README 自述「对源码不作任何权利主张」，改编自 as3sfxr/bfxr）→ 判负
- 平台：Unity（即团结同源）C# 库：参数串实时合成+可导出静态 WAV；但已归档 7 年
- 接线点：无（判负）；但其「参数串→合成音」思想值得未来自研时借鉴
- verdict：**判负**——无 LICENSE+已归档双触线；功能上 jsfxr/rfxgen 已覆盖

## B 组：响度/母带处理与测量

> 结论先行：pyloudnorm（MIT）是与 ffmpeg loudnorm 双测量交叉验证的**最优取用**；Matchering（GPL-3.0）只能本机用、**禁入发行包**。

### B1. pyloudnorm——BS.1770-4 独立测量，交叉验证首选
- URL：https://github.com/csteinmetz1/pyloudnorm
- Stars：783 · 语言 Python · 最近 push 2026-01-04 · pip 有维护版（PyPI 在线，未安装）
- 许可：**MIT**（API 实查）→ 可入工具链
- 平台：Windows + Python（pip），纯库可 CLI 化（自带 meter 示例可 `python -m` 方式跑，批处理友好）
- 接线点：**GateCheck 交叉验证**——14 号标准里 -16 LUFS（SFX）/-18 LUFS（BGM）当前由 ffmpeg ebur128 单源测；接入 pyloudnorm 做第二实现（ITU-R BS.1770-4），两源读数一致才放行，防 ffmpeg 升级时 ebur128 口径漂移
- verdict：**取用**——MIT、纯 Python、算法正源，是「验收门双测量」最低成本的加固件

### B2. Matchering——参考曲母带匹配，GPL 只许本机
- URL：https://github.com/sergree/matchering
- Stars：2648 · 语言 Python · 最近 push 2026-07-08（活跃）· PyPI 有 matchering 包
- 许可：**GPL-3.0**（API 实查）→ 本机工具用途可用，**禁入发行包**（不得链接进小游戏包体/服务端闭源发布）
- 平台：Windows + Python/Docker 可跑，2.x 版为库+CLI 形态，可脚本化
- 接线点：BGM「重母带」环节——把存量 BGM 向参考曲（自选目标响度/音色）匹配，作为 MasterFix 的**可选前置步骤**，输出再过 GateCheck；SFX 不适用（其针对整曲母带）
- verdict：**观察**——能力对口「存量重母带」但有 GPL 传染面，仅限内部本机实验，暂不入法定管线

### B3. librosa——音频分析全家桶（循环点候选/频谱都能靠它）
- URL：https://github.com/librosa/librosa
- Stars：8637 · 语言 Python · 最近 push 2026-09-29（极活跃）· 官网 librosa.org
- 许可：**ISC**（API 实查，BSD 系宽松许可）→ 可入工具链
- 平台：Windows + Python，纯库，天然可自动化
- 接线点：双岗位——①C 组循环点候选（自相关/onset 找循环接缝）②D 组取证（librosa.display 画频谱/波形图入证据板）；依赖 numpy/scipy/numba，本机装一次即可
- verdict：**取用**——ISC 无忧+头部分析库，一个库覆盖 C/D 两组一半需求

### B4. essentia——分析力强但 AGPL 传染面重
- URL：https://github.com/MTG/essentia
- Stars：3753 · 语言 C++（带 Python 绑定）· 最近 push 2026-09-21
- 许可：**AGPL-3.0**（API 实查）→ 本机工具用途可用、**禁入发行包**（AGPL 网络传染比 GPL 更严）
- 平台：Windows 可跑但构建/依赖重（C++ 编译或预编译包）
- 接线点：理论上可做响度/音色分析，但 pyloudnorm+librosa 已覆盖我方全部需求
- verdict：**判负**——AGPL 面重+无独占能力，为省许可风险不入工具链（记录在案，避免未来误引入）

### B5. ffmpeg-normalize——双遍 loudnorm 封装，与自研 MasterFix 同引擎
- URL：https://github.com/slhck/ffmpeg-normalize
- Stars：1538 · 语言 Python · 最近 push 2026-09-02（活跃）
- 许可：**未能核实**——API license=NOASSERTION("Other")，根目录 LICENSE 文件 404 实测（其许可文件形式特殊，待读仓库根目录清单后定论；标「待证」）
- 平台：Windows + Python，CLI 批处理友好（可整目录递归）
- 接线点：与 MasterFix 完全同引擎（ffmpeg loudnorm 双遍），属重复建设；唯一价值=当「参照实现」核对自研参数
- verdict：**观察**——功能重复，仅在 MasterFix 调参时作对照参考；许可未核实前不入管线

### B6. SoX（chirlu/sox 镜像）——瑞士军刀，但功能被 ffmpeg 覆盖
- URL：https://github.com/chirlu/sox（社区镜像，非官方主源；官方开发在 SourceForge）
- Stars：966 · 语言 C · 镜像最近 push 2023-11-24 · API license=NOASSERTION（SoX 为自定义「GPLv2/LGPL 双许可」文本，GPL 系）
- 平台：Windows 有 SourceForge 预编译二进制；CLI 完整可自动化
- 接线点：silenceremove/spectrogram/tempo 等我方全部已有 ffmpeg 等价物；smpl 不支持
- verdict：**观察**——所有功能 ffmpeg 已覆盖且 MasterFix 已在用 ffmpeg，引入徒增维护面；spectrogram 命令可作 D 组备选思路

### B7. LAME（lameproject/lame 镜像）——MP3 编码器，管线不产 MP3
- URL：https://github.com/lameproject/lame（自述「Unmonitored mirror」非官方维护镜像）
- Stars：22 · 镜像 push 停在 2020-12-03 · 官方站点 lame.sourceforge.io 实查：LAME 为 **LGPL**，最新版 v4.0（2026-07）
- 平台：Windows 二进制在 SourceForge；CLI 可自动化
- 接线点：无——我方微信 WebGL 构建统一转 **AAC**，管线不产 MP3；其 gapless（encoder delay+padding）知识对 AAC 闭环无直接作用
- verdict：**判负**——编解码目标错位+GitHub 镜像死档，仅存档备注

## C 组：循环点检测/无缝循环/静音修剪/批处理自动化

> 结论先行：我方 MasterFix 已自带静音修剪/头垫/smpl 写入/批处理（ffmpeg silenceremove、astats 等），C 组外部工具的真实价值集中在**「循环点自动检测/校验」**这一个缺口。能力最对口的两件（crosslooper、LoopAuditioneer）都是 GPL（本机可用、禁入发行包）；而 smpl 批写类小工具（loopy/SMPL-makr/loop-ogg）**清一色无 LICENSE，全部判负**——「合规 smpl 批写」生态位缺货，可用 librosa(ISC) 自研补位。另注：ffmpeg 官方 trac #11301 确认 ffmpeg 处理会**丢弃 smpl 块**——印证我方 MasterFix 在 ffmpeg 处理后重写 smpl 的做法是必要工序，也说明外部「先处理后循环」工具链须自查此坑。

### C1. crosslooper——互相关自动猜循环点，能力最对口
- URL：https://github.com/Splendide-Imaginarius/crosslooper
- Stars：4 · 语言 Python · 最近 push 2024-07-16
- 许可：**GPL-3.0**（API 实查）→ 本机工具用途可用，**禁入发行包**
- 平台：Windows + Python，可 CLI 批量化
- 接线点：BGM 循环点候选初筛——用统计互相关自动猜 LOOPSTART/LOOPLENGTH，产出候选点供人审/供 MasterFix smpl 写入参考
- verdict：**观察**——能力正中缺口但 GPL+4 星小众，先小样本验证猜点准确率，再决定是否并入本机工序

### C2. LoopAuditioneer——循环点人审/自动寻点/交叉淡化老牌工具
- URL：https://github.com/GrandOrgue/LoopAuditioneer（源码新家；官网/二进制在 SourceForge：loopauditioneer.sourceforge.io）
- Stars：14 · 语言 C++ · 最近 push 2026-03-16
- 许可：**GPL-3.0**（API 实查）→ 本机工具用途可用，**禁入发行包**
- 平台：Windows 预编译二进制（SourceForge 下载）；**GUI 为主**，自带单文件+批处理两种寻点模式
- 接线点：BGM 循环点人审台——可视化试听循环、自动搜自然循环点、难接缝时做交叉淡化（为管风琴样本而生，但 smpl 是通用标准）
- verdict：**观察**——GPL+GUI 定位为本机辅助人审，不进管线；批处理模式可帮存量 BGM 重母带时批量修循环

### C3. loopy（ps1dev/loopy）——网页版 smpl 编辑器，无许可判负
- URL：https://github.com/ps1dev/loopy
- Stars：0 · 语言 TypeScript · 创建 2026-09-04、push 2026-09-28（极新）
- 许可：**无 LICENSE**（API license=null 实测）→ 判负
- 平台：纯网页（tools.psx.dev/loopy），单文件 HTML
- 接线点：无（判负）
- verdict：**判负**——无 LICENSE 触红线且 0 星太新；「网页直写 smpl」的形态思路可记档

### C4. SMPL-makr——CSV 批写 smpl，思路好但无许可
- URL：https://github.com/conradzeus/SMPL-makr（配套 loop-csv-xtractor）
- Stars：1 · 语言 Python · push 2024-09-23（一次性脚本）
- 许可：**无 LICENSE**（API license=null 实测）→ 判负
- 平台：Windows + Python；**天然批处理**（CSV→smpl）
- 接线点：无（判负）；其「循环点提取成 CSV→批回写」的两段式思路可借鉴
- verdict：**判负**——无 LICENSE；且等价能力 MasterFix 已内置（smpl 写入），无缺口

### C5. loop-ogg——OGG CLI 循环，格式错位+无许可
- URL：https://github.com/SolraBizna/loop-ogg
- Stars：0 · 语言 Rust · push 2022-12-09
- 许可：**无 LICENSE**（API license=null 实测）→ 判负
- 平台：CLI；但面向 Ogg Vorbis
- 接线点：无——我方 BGM 为 WAV(smpl)+AAC，不产 OGG
- verdict：**判负**——无 LICENSE+格式与我方管线错位

### C6. 静音修剪/批处理结论
- ffmpeg `silenceremove`/`astats`/`atrim` 我方 MasterFix 已在用（自研即最佳方案）；GitHub 上该类工具多为 ffmpeg 薄封装或无 LICENSE 脚本，无一具备「许可证干净+超越自研」双重条件
- smpl 循环写入：合规生态位缺货（见上），若需扩展（如按 CSV 批改循环点），建议用 **librosa(ISC)+python-soundfile**（后者待核）自写 30 行级脚本，零许可负担

## D 组：音频 QC 取证（削波/频谱/波形/批量体检）

（诚实律注记：本组调研员未完成即终止，主会话按已核实条目收口，不新增未经当场核实的候选。）

- 结论：我方 MasterFix/GateCheck 已用 ffmpeg 原生能力覆盖削波检测（astats/volumedetect 真峰值读数）与批量体检；**外部专用件未及完整三查，不凑数**。
- 已核实覆盖能力：librosa（B3·ISC）自带 librosa.display 频谱图/波形图绘制（matplotlib 后端）——D 组取证需求被 B 组取用件覆盖，无需另引工具。
- 处置：本组无独立新增件；未来需要自动化频谱取证时用 librosa 一件即可。

## E 组：本地音乐生成（MusicGen/audiocraft 类，许可面严审）

（诚实律注记：调研员死前未及核实本组，未完成面如实标注。）

- 现役路线：BGM 生产=TJ 云端定制（洗脑 hook 已落地 U320 双候选）+存量重母带——本地生成当前无紧迫缺口。
- 风险预注（凭训练记忆·未经当场核实·标「待证」）：audiocraft/MusicGen 代码 MIT 但**模型权重许可常含非商用条款**——若未来启用本地生成，须先过权重许可实查，禁直用。
- 处置：挂「按需续研」——确需本地生成（离线/批量/成本面）时再派专项调研波。

## Top 3-5 取用建议（按接线价值排序）

（主会话代收口：依据 A-C 组已核实条目排序·2026-09-30）

| # | 工具 | 许可（实查） | 接线点 | 一句话理由 |
|---|---|---|---|---|
| 1 | pyloudnorm（csteinmetz1·783★·2026-01 活跃） | MIT | **GateCheck 双测量交叉验证**：14 号响度门现由 ffmpeg ebur128 单源测；接 BS.1770-4 第二实现，两源一致才放行 | 验收门最低成本加固件，纯 Python 零重依赖 |
| 2 | librosa（librosa/librosa·8637★·极活跃） | ISC | C 组循环点候选初筛（自相关/onset）+D 组频谱取证（librosa.display 入证据板） | 一个库覆盖 C/D 两组，头部分析库 |
| 3 | rfxgen（raysan5·512★·2026-08 活跃） | Zlib | SFX 速捏底料（Kenney 池外本地补位）→出 WAV 进 MasterFix 归一；GUI 档=速用秤非管线件 | sfxr 族里许可+活跃度最优解，Windows 独立版零依赖 |
| 4 | jsfxr（chr15m·451★·2026-05） | Unlicense | 零安装网页速捏（sfxr.me），策划/开发占位音秒出 | 公有领域零负担；批量自动化不足，定位灵感/占位 |
| 5 | sfxr-qt（agateau·92★·MIT） | MIT | rfxgen 的 MIT 备选捏音器（Windows 二进制） | 界面顺手，功能等同原版 sfxr |

配套注记：Matchering（GPL-3.0·观察）=存量 BGM 重母带可选前置，仅限本机实验、禁入发行包；C 组「合规 smpl 批写」生态位缺货→用 librosa(ISC)+python-soundfile 自写 30 行级脚本补位；ffmpeg-normalize 与自研 MasterFix 同引擎，仅作调参参照实现。

## 附：判负与待证清单

**判负（无 LICENSE 红线）**：bfxr（increpare·1026★·且 Flash/AIR 技术栈已废）｜usfxr（zeh·366★·已归档 7 年）｜loopy（ps1dev·0★）｜SMPL-makr（conradzeus·1★）｜loop-ogg（SolraBizna·0★·格式错位）
**判负（许可/平台面）**：essentia（MTG·AGPL-3.0·能力被 pyloudnorm+librosa 覆盖）｜LAME 镜像（lameproject·死档镜像·管线不产 MP3）
**观察**：Matchering（GPL-3.0·禁入发行包）｜ffmpeg-normalize（许可 NOASSERTION 待证·与自研同引擎）｜SoX（GPL 系·功能被 ffmpeg 全覆盖）｜crosslooper（GPL-3.0·4★·循环点猜点先小样本验证）｜LoopAuditioneer（GPL-3.0·GUI 人审台·本机辅助）
**待证**：ffmpeg-normalize 许可文件形式特殊（根 LICENSE 404·需读仓库根目录清单定论）；jsfxr 的 Node 包装批量可行性（无现成 CLI）
**未完成面（诚实标注）**：D 组外部专用件三查未完（需求被 ffmpeg+librosa 覆盖）；E 组本地音乐生成未及核实（现役 TJ 云端路线无缺口·挂按需续研）

---

（收口注记：本件调研员 73 次工具调用后死于模型超时〔completed_partial〕，A-C 组主体完整且逐条当场核实；D/E 组与 Top/判负清单由主会话按已核实内容代收口，未新增任何未经当场核实的候选——诚实律标注 2026-09-30）

<!-- CURSOR：增量插入点 -->
