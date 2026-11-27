# OH-20261002-bigstream.md — BigStream OSS 收获台账·窗 3

> 窗：2026-10-02 21:40 → 2026-10-05 21:40（窗 3 切片 1 = 开窗即领·R1020 下步指针①兑现·R762 下窗指针「ASS/libass 逐行居中=R9 遗留候选位可评估」承接）
> 实体：BigStream（bm-a OSLoop R1021 切片 1）

## 切片 1（R1021·2026-10-02 21:4x）— ASS/libass 逐行居中渲染路径：R9 遗留候选位迁移预评（#70 窗 3·判负留痕）

### 实搜面（3 处实录）

1. **GitHub API 直采**（A 级·`api.github.com/repos/libass/libass`·2026-10-02 21:4x 实读）：description="libass is a portable subtitle renderer for the ASS/SSA (Advanced Substation Alpha/Substation Alpha) subtitle format."·license spdx_id=**ISC**·stars=**1,181**·forks=248·open_issues=170·pushed_at=**2026-09-17T15:22:52Z**（15 日内）·archived=false·language=C——R459 窗 1 读数（1.2k★/249 fork）同源续证·健康态维持。
2. **GitHub API 直采**（A 级·`api.github.com/repos/tkarabela/pysubs2`·同窗实读）：description="A Python library for editing subtitle files"·license spdx_id=**MIT**·stars=**442**·forks=57·open_issues=17·pushed_at=**2026-09-27T19:08:28Z**（5 日内）·archived=false·language=Python——SRT→ASS 桥正主（R458 五门评估 parked 登记承继）·活跃续证。
3. **本司在案证据**（跨仓只读）：①**R9 设计先例**（OS 循环第 9 轮·R-A 渲染器交付轮·`src/render/render_card_video.py`）=drawtext **块居中+行内左对齐**双律=L-卡系列模板正典（QUOTE-v2 参数 verbatim 复用 ×51 件 DAILY 系·零新模板律）；E4 参考仪对位观感注记双档明示「中段左对齐块=系列模板设计一致面〔R9 drawtext 块居中行内左对齐先例·观感面非缺陷〕」（review-20261002-mcdaily-v27/v28.md 在案）=**评审席正面定性·非旗**。②在役机检资产=em 预算机核（`_em_cost`·梯档律 R293/R301-313）+VERT 垂直栈预算律（R381）+fc_args 传输门控（capabilities v1.27）——全部在 drawtext 字体度量坐标系内校准；本地 ffmpeg 9.0.1 `-filters` 实测含 ass/subtitles 双滤镜（R459 实测原文「using the libass library」=内置在役栈零新依赖）。③**零旗历史**：E8/E4/CEO 目检/帧验三律从未旗「行内左对齐/逐行居中」面——R459 parked 重开条件「字幕逐行对齐被旗→ASS/libass 迁移预评」自 09-27 立档以来**零触发**。

### 判据预注册（评估前先立·≤3 问·R644/R762 同式）

- **D1 契合门**：逐行居中工位实存？→ **不实存**。R9 块居中行内左对齐=系列模板正典（零新模板律 ×51 verbatim 复用·visual-spec v1.2 §5.5 系列模板统一律同源面）；E4「观感面非缺陷」双档正面定性；零旗历史（R459 重开条件从未触发）。「替谁省什么」一句话=无工位可答——逐行居中不是缺口而是**设计选择**。
- **D2 反重复门**：在役 drawtext 栈已覆盖卡面/字幕渲染工位；ASS/libass 迁移=同工位换轨非新增；且 em 机核/VERT 断言/梯档律整套机检资产锚定 drawtext 字体度量坐标系——libass 自行排版（含自动折行/对齐）=机核断言坐标系失效面（迁移=机检资产整套重写）。
- **D3 adopt 线**：D1 无工位 → adopt 不可达（无 A/B 面需要·与 R644/R762「无实测=adopt 不可达」同型更前置：无工位=无需实测）。
- 三态线：D1 无工位 → **reject**（判负留痕合法·P-2026-09-28-02·R432 零采用诚实收口先例）。

### 五门评估

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | 逐行居中工位不实存：R9 块居中行内左对齐=系列模板正典（×51 复用）；E4「观感面非缺陷」双档正面定性；E8/CEO/帧验零旗历史（R459 重开条件零触发） | **FAIL** |
| ②反重复 | drawtext 在役覆盖工位（R-A 引擎+em 机核+VERT 断言+fc_args 门控）；迁移=同工位换轨且整套机检资产坐标系失效需重写；51 件存量同源面破坏（§5.5 系列模板统一律） | **FAIL** |
| ③许可 | libass ISC + pysubs2 MIT（GitHub API 实读 2026-10-02）=直用合法（无工位故 moot） | PASS |
| ④健康 | libass 1,181★/fork 248/push 09-17（15 日内）非 archived；pysubs2 442★/fork 57/push 09-27（5 日内）非 archived=双活（R458/R459 读数同源续证） | PASS |
| ⑤成本/安全 | 本地渲染零 API token（ass 滤镜 ffmpeg 内置零新依赖）；无外发数据；但迁移成本=em 梯档/VERT/机核整套重写+51 件存量同源破坏=高成本零已旗收益 | **FAIL** |

### 结论：**reject（无工位·判负留痕合法）——R9 遗留候选位收口为「设计正典确认」**

- R762 下窗指针点名评估的「ASS/libass 逐行居中」候选，预评毕定谳：**逐行居中非缺口而是设计选择**——R9 块居中行内左对齐经 51 件量产+E4 正面定性双档+零旗历史三方实证为正典设计；R459 parked 态的「字幕逐行对齐被旗」重开条件维持（零触发在案）。
- **重开条件（触发律·任一即启迁移预评腿）**：
  - 触发 A：E4/E8/CEO 目检或帧验三律旗「行内左对齐/逐行居中」面——**连续 ≥2 件**同位旗或 CEO 直评；
  - 触发 B：系列模板改版窗（visual-spec §5.5 修订令）开窗 → 同窗评估排版轴（含逐行居中变体 A/B 样片呈 CEO 目检·L-卡 模板变更须 CEO 过目惯例）。
- **迁移预评腿判据（触发后执行·Bonsai 波范式）**：pysubs2 SRT→ASS 桥 PoC + ffmpeg ass 滤镜渲染 A/B 对照（同稿双样片·块居中行内左对齐 vs 逐行居中）+ em 机核移植评估（libass 排版坐标系下梯档/VERT 断言重写量清单）→ 呈 CEO 目检定夺（模板面=CEO 决策面·visual-spec §5.5 惯例）。

### 采用 → 落点（工作流变更 0 条·reject 态）

1. 零工作流变更（R9 设计维持正典·51 件存量同源面零动）；
2. 落点=本台账全档（判据预注册+重开条件+迁移预评腿判据=后续轮执法面）+R459 parked 行重开条件细化注记（由「被旗→迁移预评」细化为触发 A/B 双律+预评腿判据）。

### 结论应用表

| 结论 | 应用面 | 承接 |
|---|---|---|
| reject（无工位·设计正典确认） | L-卡/字幕渲染轴收口：逐行居中=设计选择非缺口·R762 指针评估毕 | 本台账 + R459 parked 行注记 |
| 重开条件（触发 A/B） | 连续 2 件同位旗 或 CEO 直评 或 §5.5 修订窗 → 迁移预评腿 | 本切片 D3 判据 |
| 迁移预评腿判据 | pysubs2 桥 PoC + ass 滤镜 A/B 双样片 + em 机核移植评估 → CEO 目检 | Bonsai 波范式 |

### 姊妹线咬合

- 模型类零发现=P-17 适配矩阵/P-19 管线无触发零拉取维持；
- AI 会话技能类零发现=P-20260926-01 技能律只供源维持；
- pysubs2 供源登记承继（R458 五门评估 parked·重开条件=字幕逐行对齐被旗——本切片 A/B 触发律与其同源联动）。

### 下窗指针

- 窗 3 剩余切片（10-05 21:40 前开·续写本文件·每窗 ≥1 切片义务已满）：候选 ≥1 项（本地提效类优先·ASR 双轨已齐〔whisper.cpp 环境轴+SenseVoice zh 质量轴〕+字幕渲染轴已收口〔本切片〕→下一切片候选面=渲染工程基建/字体栈/包装工具类·≤3 刀·或如实零发现）；EAGLE-3/BitNet=CPH4 侧份额知悉不动作维持。

— R1021 bm-a OSLoop·切片 1 毕

## 切片 2（R1033·2026-10-03 01:0x）— 字体栈：fontTools 字形覆盖预检门 **ADOPT（已落地）**（#70 窗 3·R1032 指针「OSS w3 slice 2」兑现）

### 实搜面（3 处实录）

1. **GitHub API 直采**（A 级·`api.github.com/repos/fonttools/fonttools`·2026-10-03 实读）：license spdx_id=**MIT**·stars=**5,272**·forks=545·open_issues=398·pushed_at=**2026-10-02T12:43:29Z**（1 日内）·archived=false·language=Python——canonical 字体库顶配活跃；本机 fontTools **4.65.0 已在装零拉取**（transitive 依赖实证 `import fontTools` 直读）。
2. **GitHub API 搜索两刀**（A 级·`search/repositories`）：`font+glyph+coverage+check`（4 命中全读=jettbrains/-L- GPL-3.0 死件无关/blueset/font-coverage **无 license=禁入产品链**〔R458 no-license 先例〕·pdf-font-inspector MIT 0★ PDF 面错位/grokify/fontscan MIT 0★ Go 栈错位）+`subtitle+missing+glyph+tofu`（**0 命中=刀面空如实记**）→ **无契合专建工具**（0★/无 license/栈错位三态全灭）。
3. **本司在案证据全量机核**（`.c3-tmp/r1033_glyph_audit.txt`+`r1033_glyph_lines.py` 精扫·2026-10-03）：
   - **渲染行语料 160 件 cards-style json（cards[].lines+aigc_notice）1470 unique chars：缺字 1 例实锤**=`data/sources/bs005/cards-v1-matched.json` card4「重后端 **✂** · 成本为零」（U+2702 不在 msyh cmap）——**bs-005-v1 渲染件 R192 已烧 tofu 入帧**（后随 D-BS-08 弃件处置、未发布零外泄=无公开缺陷，但**当轮无任何门拦住**：em 机核只测宽度、抽帧验图查语义不查字形渲染）；
   - L-卡 poster 面 257 件（cards.json lines+aigc）+ 全部 .srt 字幕面：**0 缺字**（85+ 成品零 tofu 实证）；
   - U+2194（↔）9 件/U+2713（✓）2 件=**仅 meta 散文位从未入渲染行**（in-LINES hits=NONE 机核）；
   - **源面潜在危险**=日报热榜（REACT 热点标题 verbatim 律唯一不可控上帧文本面）已机核实锤含 msyh 缺字 emoji：⚡ U+26A1/🤔 U+1F914/U+FE0F 落 2026-09-29 日报→若 M0 择优选中即烧 tofu（现行防线=M2 验图事后抓=烧一次渲再返工）；
   - 字体实况=渲染双路（PIL poster/ffmpeg drawtext）同源 `msyh.ttc`+`msyhbd.ttc`（face 0·cmap 29905/29888 codepoints）。

### 判据预注册（评估前先立·≤3 问·切片 1 同式）

- **D1 契合门**：渲染前字形覆盖预检工位实存？→ **实存（实锤+潜在双锚）**：✂ 实锤=1 例已烧帧未被任何门拦（弃件未发布=无外泄但防线缺口实证）+emoji 潜在=REACT verbatim 可选池实锤含缺字位。「替谁省什么」一句话=烧渲前拦住缺字，省一次「渲染→M2 抓→返工」循环，且把「verbatim 律×emoji 政策」冲突浮面到选材时点而非渲染后。
- **D2 反重复门**：在役栈无覆盖检位（em 机核管宽度/VERT 管垂直/验图查语义——**均不问字形存在性**=三件同盲区）+实搜无契合专建件（0★/无 license/Go 栈错位）→ fontTools 库级采=正解非重复造轮。
- **D3 adopt 线**：additive 门+3 测试+真数据冒烟+阴性对照四证可达=**adopt 本轮落地**。
- 三态线：D1 实存 → **adopt**。

### 五门评估

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | 渲染前覆盖检工位实存：✂ 实锤 1 例烧帧未拦（bs-005-v1 card4·R192·弃件未发布）+REACT 可选池 emoji 潜在（⚡/🤔 09-29 日报实锤）；唯一不可控上帧文本面=热点标题 verbatim 律 | **PASS** |
| ②反重复 | 在役三机检（em/VERT/验图）均不问字形存在性=同盲区；实搜无契合专建件；fontTools=库级采零重复造轮 | **PASS** |
| ③许可 | fontTools **MIT**（API 实读 2026-10-03）；无 license 候选（blueset/font-coverage）已按 R458 先例排除 | PASS |
| ④健康 | 5,272★/fork 545/push 2026-10-02（1 日内）/非 archived=顶配活跃；本地 4.65.0 已在装 | PASS |
| ⑤成本/安全 | 零拉取（已在装）·零 API token·纯本地 cmap 读·60 行 additive 门+3 测试；**零迁移**（drawtext 坐标系零动·51 件存量同源面零破坏=R1021 libass reject 的成本面对照）；fail-open 仅限依赖缺失/字体不可读（main 的 font-exists 前置+M2 验图双兜底在案） | **PASS** |

### 结论：**ADOPT（本切片已落地）**——render_card_video.py `load_cards` 字形覆盖门（M2 装载位 fail-fast）

- 实现：`_glyph_cmap()`（face-0 best-cmap 读·absent/unreadable→None）+`_check_glyph_coverage()`（lines[0]→h1_font、lines[1:]+aigc_notice→font.file 按渲染分工精确对位〔build_render_plan L254 口径〕·缺字→`ValueError: glyph coverage FAIL`+U+XXXX 清单·ASCII 消息）+`load_cards` 尾调用=poster/视频双路单入口全覆盖；
- 诚实边界（fail-open 面如实注）：fontTools 缺失=stderr WARN 跳过；fake 字体路径（单测夹具态）自跳过=main L593 真渲染前 font-exists 拒绝兜底；**字幕 .srt 面不入门**（历史 0 缺字+TTS 直出受控文本=证据面 YAGNI·首个 srt 缺字现=扩门触发条件）；
- 验证四证：**306 全回归绿**（+3 新测：真 msyh 常用字过门/🤔 U+1F914 注入 RAISE/fake 路径自跳过）+真数据冒烟（最新成品 DAILY v61 cards.json 全链 load_cards 过门）+阴性对照（同件注入 U+1F914 即 RAISE）+bs005 ✂ 复盘（该件若走新门=card4 拦截实证）。

### 采用 → 落点（工作流变更 1 条·adopt 态）

1. **M2 渲染链装载位新增字形覆盖机检门**（`src/render/render_card_video.py` load_cards 内·烧渲前 fail-fast·L-卡 poster+视频 cards 双路全盖）；测试锁=`tests/test_render_card.py` TestLoadCards 3 新测。

### 结论应用表

| 结论 | 应用面 | 承接 |
|---|---|---|
| adopt：字形覆盖门入 M2 装载位 | L-卡/视频渲染链防 tofu：✂ 实锤类+emoji 潜在类双面拦截·烧渲前非渲染后 | 本切片+306 回归绿 |
| emoji×verbatim 政策触发条件 | 门 RAISE 即浮面「热点标题 verbatim 律 vs 缺字 emoji」政策取舍（回避/脱敏/换候选）——**留待首个真实命中轮定夺，不预立律**（禁无锚立法） | 首命中轮 M0 择优面 |
| srt 面扩门条件 | 字幕轨首现缺字=扩门触发（历史 0 缺字·受控文本面） | 后续轮 |

### 姊妹线咬合

- 模型类零发现=P-17 适配矩阵/P-19 管线无触发零拉取维持；
- AI 会话技能类零发现=P-20260926-01 技能律只供源维持；
- EAGLE-3/BitNet=CPH4 侧份额知悉不动作维持（切片 1 同判）。

### 下窗指针

- 窗 3 剩余切片（10-05 21:40 前开·续写本文件）：候选面=渲染工程基建/包装工具类剩余面（**faststart 包装位已核毕=双渲染器在役零缺口**·R1033 核）·或如实零发现；≤3 刀照守。

— R1033 bm-a OSLoop·切片 2 毕

## 切片 3（R1034·2026-10-03 01:2x）— 渲染工程基建/包装工具类剩余面三刀收口：零采用（#70 窗 3·R1033 下窗指针「候选面=渲染工程基建/包装工具类剩余面·或如实零发现」兑现·判负留痕）

### 实搜面（3 处实录·≤3 刀照守）

1. **GitHub API 搜索刀 1**（A 级·`search/repositories?q=ffmpeg+filtergraph+python`·2026-10-03 01:2x 实读·total_count=2 全读）：SuperSonicHub1/comply（**Unlicense**·1★·push 2023-12-17·Python·"A Python DSL for creating more friendly FFmpeg filtergraphs"=停滞玩具级）+imbcmdth/ffrwd-cli（Apache-2.0·0★·push 2026-10-01·Python·Wasm+SQL 滤镜配方注册表=**栈错位**——本司滤镜=原生 drawtext/drawgrid/drawbox 非该域）→ **filtergraph 构建面零契合**：本司 filtergraph=build_render_plan 机器生成单一真相（R447 edit_craft 七参同源接线）+% 转义 expansion=none 回归锁（R186/R188 五处烧帧教训防复发）+fc_args 长图传输门控（capabilities v1.27）+306 测试绿——「替谁省什么」无工位可答（手写复杂度痛点不存在=机器生成件）。
2. **GitHub API 搜索刀 2**（A 级·`search/repositories?q=mp4+faststart`·同窗实读·total_count=31·top6 全读）：ypresto/qtfaststart-java（MIT·76★·push 2018-06·Java）+kanongil/node-faststart（**无 license=禁入**〔R458 先例〕·17★·2015·JS）+messer/php-qtfaststart（**无 license**·9★·2013·C/PHP 扩展）+kevincharm/moov-faststart（Apache-2.0·8★·2019·TS）+reklatsmasters/mp4-moov-move（**无 license**·7★·2016·JS）+ExReanimator/video-faststarter（**无 license+archived=true**·5★·2011·Ruby）→ **包装/封轴零缺口**：top 命中全=qt-faststart 他栈移植件（2011-2019 全停滞·半数无 license·1 件 archived）；本司 faststart=双渲染器原生在役（`src/render/edit_craft.py:571`+`src/render/render_card_video.py:729` `-movflags +faststart`·R1033 包装位核毕续证·本轮 grep 实锚）——移植件类=对在役 ffmpeg 原生功能的他栈重实现=契合门无工位+反重复门 FAIL。
3. **GitHub API 搜索刀 3+候选尽调**（A 级·`search/repositories?q=video+quality+control+artifact+analysis`·total_count=1=justindutcher/computer-forensics **无 license** 取证面错位如实记）→ 视频 QC 面唯一可信候选=**bavc/qctools** 直采（390★/fork 45/push 2026-07-06T09:17:56Z·非 archived·C++·desc="Quality Control Tools for Video Preservation"）+License.html 直读定谳（API license=NOASSERTION→原文="QCTools is licensed under a **GPLv3** License" verbatim·r1034_qctools_license.txt 留档）→ 五门评估见下=**reject**。

### 判据预注册（评估前先立·≤3 问·切片 1/2 同式）

- **D1 契合门**：信号级 QC 工位实存？→ **不实存**。本司成品=自渲染件（编码参数已知自控：yuv420p/AAC/faststart·非外部摄入数字化档案）；在役质量门=S2 三门（ai_feel 拍稿↔SRT/platform_spec 画幅时长窗/edit_craft 层 1.8）+帧验采样三律（拍头/段中尾/回环边界）+E4/E8/CEO 目检多席——fleet 202 件成品档**零编码伪影旗历史**；qctools 目标域=数字化档案保存 QC（preservation telemetry）≠AIGC 短视频管线。「替谁省什么」一句话=无工位可答。
- **D2 反重复门**：发布前拦截职能已由 S2+帧验+多席评审覆盖；信号遥测位零需求（D1 级联 moot）。
- **D3 adopt 线**：D1 无工位 → adopt 不可达（R1021 切片 1 同型更前置）。
- 三态线：D1 无工位 → **reject**（判负留痕合法·P-2026-09-28-02）。

### 五门评估（bavc/qctools）

| 门 | 读数 | 判定 |
|---|---|---|
| ①契合 | 无工位：自渲染件参数自控+S2 三门+帧验三律在役零伪影旗；qctools 域=档案保存 QC 错位 | **FAIL** |
| ②反重复 | 发布前质量门已覆盖（S2+帧验+多席）；信号遥测位零需求（D1 级联） | **FAIL** |
| ③许可 | **GPLv3**（License.html verbatim 直读 2026-10-03·API NOASSERTION→人工定谳）→ **禁入产品交付链登记**〔R458 GPL-3.0 先例同律〕 | **FAIL** |
| ④健康 | 390★/fork 45/push 2026-07-06（~3 个月）/非 archived/C++=活档如实记 | PASS |
| ⑤成本/安全 | Qt GUI 桌面重集成+GPL 登记禁=高成本零已旗收益 | **FAIL** |

### 结论：**reject（无工位+GPLv3 双 FAIL·判负留痕合法）——渲染工程基建/包装工具类剩余面三刀收口=零采用（如实零发现）**

- 窗 3 指针候选面三刀全读：filtergraph 构建面=机器生成单一真相在役零痛点·包装/封轴=faststart 双渲染器原生在役零缺口·视频 QC=唯一可信候选 GPLv3 禁入+无工位 → **零采用诚实收口**（R432/R1021 reject 先例续证）。
- **重开条件（触发律·任一即启重评腿）**：
  - 触发 A：M5 上线后平台转码拒绝/技术 QC 旗连续 ≥2 件 → 先评估 **license 洁净替代**（GPL 排除面维持——ffprobe 信号统计自研扩展优先·Bonsai 波范式·qctools 仅对照参考不入链）；
  - 触发 B：外部摄入素材（实录批扩容）进入深处理链 → 摄入面 QC 预评腿（域对位再判）。

### 采用 → 落点（工作流变更 0 条·reject 态）

1. 零工作流变更（S2+帧验+faststart 在役面零动）；
2. 落点=本台账全档（三刀读数+重开条件=后续轮执法面）。

### 结论应用表

| 结论 | 应用面 | 承接 |
|---|---|---|
| reject：filtergraph DSL 面 | 机器生成 filtergraph 单一真相维持（build_render_plan+回归锁+fc_args） | 本台账刀 1 |
| reject：qt-faststart 移植件 | faststart 原生在役维持（双渲染器 L571/L729） | 本台账刀 2+R1033 核毕 |
| reject：qctools（GPLv3+无工位） | 发布前 QC=S2 三门+帧验三律维持；重开条件 A/B 在档 | 本台账刀 3 |

### 姊妹线咬合

- 模型类零发现=P-17 适配矩阵/P-19 管线无触发零拉取维持；
- AI 会话技能类零发现=P-20260926-01 技能律只供源维持；
- EAGLE-3/BitNet=CPH4 侧份额知悉不动作维持（切片 1/2 同判）。

### 三律自检

礼貌节流 3 刀（搜索三刀·qctools 直采+License 直读=刀 3 候选尽调内含·窗口内 API 调用 ≤6 次）✓；落点强制=结论应用表 3 行在件 ✓；判据预注册先立后评 ✓。

### 下窗指针

- 窗 3 义务已满（切片 1-3·10-05 21:40 前剩余轮次可续但候选面已收窄=如实零发现合法）；**窗 4=10-05 21:40 开**：候选面=音频轴工具（响度/EBU R128 类——当前 D-BS-02 禁烧 BGM+edge-tts 单声源同构=响度恒定零旗·预判无工位）/发布链平台 API 客户端类（M5 账号物理件 blocked-on-CEO 前不评估）/或如实零发现；≤3 刀照守。

— R1034 bm-a OSLoop·切片 3 毕
