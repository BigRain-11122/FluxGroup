# R-20260930-audio-sources-01 · 吸嘟嘟可商用音效源采购清单（CC0 优先盘点）

- 调研员：D（集团后台调研）
- 日期：2026-09-30（Asia/Shanghai）
- 任务来源：CEO 令「常见的音效等，可以去合规的网站或者github等地方去下载能商用的，不要都自己弄」
- 游戏档案：吸嘟嘟 · 休闲吸尘玩法 · 治愈系糖瓷卡通 · 全年龄 · 微信小游戏（主包 ≤4MB，音频总预算 ≤2MB）
- 用途：本文档为「可执行采购清单」，主会话按清单采购；本调研只盘点+核验许可，不代下载大包（小样 ≤5MB 单件仅用于核验许可文件真实性）。
- 标注规则：【确认】= 许可原文可由 URL 直引并已核对；【待证】= 需主会话采购时二次核验。

## 0. 结论速览

**一句话**：Kenney.nl 官方 6 包（共 ~4.9MB、482 件 SFX、全 CC0、包内自带 License.txt）一次拿齐 16 槽里的 ~14 槽；金币叮在包内 chips/Digital 系列或 freesound CC0（检索式已过滤好，1,715 件）里挑；Music Jingles 需 15–30 分钟试听标注；**所有源必须过内部 L0 链（-16 LUFS / -3 dBTP / 44.1kHz 单声道）并转码 m4a/aac——微信 iOS 端不支持 ogg（官方格式表实测）**。GitHub 经 12 组检索三看法复核，无可采信镜像仓库，不走 GitHub 渠道。

| 源 | 许可 | 商用 | 署名 | 证据强度 | 吸嘟嘟裁定 |
|---|---|---|---|---|---|
| **Kenney.nl** | CC0 | ✅ | 免 | 三重（页徽标＋og 描述＋包内 License.txt；6 包下载实测） | **主力，一次采购** |
| freesound.org | 逐件（勾 CC0） | ✅（CC0 件） | 免 | 单页徽标（4 件已验） | **单点补缺**（金币等） |
| OpenGameArt | 逐件（勾 CC0） | ✅（CC0 件） | 免 | 页面 `License(s): CC0` 字段（512 包实测） | 复古备选 |
| Pixabay Audio | Pixabay License | ✅ | 免 | 许可摘要页（Wayback 存证） | BGM 备选；禁原样再分发 |
| Mixkit | 分项 Free License | ✅（转述） | 免 | 页面结构已证，**原文待人工抄录** | 备用（先存证再用） |
| Zapsplat | 免费档强制署名 | ✅ | **要署名** | 标准许可原文 | **不采** |
| sonniss GDC | royalty-free | ✅ | 免 | 官方 FAQ 原文 | 7.47GB+/包，与 2MB 预算不符，不采 |
| GitHub 镜像 | 杂 | — | — | 逐仓三看均不全（见第 3 节） | **不作为渠道** |

**预算结论**：16 槽 ≈150KB（含备选）＋ BGM 0.4–0.7MB ≈ **0.9MB ≤ 2MB**，余量充足。

## 1. Kenney.nl 音频包盘点（CC0 主力源）【确认】

**结论：Kenney 为吸嘟嘟首选主力采购源。** 音频类全量 10 包，站点页面全部标注 CC0，包内自带 `License.txt`（本调研下载抽验 6/10 包，逐包确认，zip 直链均实测 HEAD/GET 可达）。CC0 = 无署名、可商用、可修改、可再分发。CC0 Deed 原文直引：*"You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission."*（https://creativecommons.org/publicdomain/zero/1.0/）

**许可证据三重链（全部直引实测）**：
1. 资产页徽标原文：`License Creative Commons CC0`（各包页面 URL 见下表）；
2. 页面 og:description 原文：`Download this package (N assets) for free, CC0 licensed!`（10/10 包均有）；
3. zip 包内 `License.txt` 原文（6 包抽验一致）：
   > `License (Creative Commons Zero, CC0)`　`http://creativecommons.org/publicdomain/zero/1.0/`

### 1.1 逐包盘点（10 包全量）

| 包 | 页面 URL | zip 直链（实测可达） | 页标数 | 实测 SFX 数 | 格式实测（ffprobe） | 时长实测（SFX） | 抽验 |
|---|---|---|---|---|---|---|---|
| UI Audio | https://kenney.nl/assets/ui-audio | https://kenney.nl/media/pages/assets/ui-audio/490d233f68-1677590494/kenney_ui-audio.zip （0.39MB） | 50 | 51（另含 Preview 串烧） | OGG/vorbis 44.1kHz 立体声 | 0.03–0.5s 级 | ✅ |
| Interface Sounds | https://kenney.nl/assets/interface-sounds | https://kenney.nl/media/pages/assets/interface-sounds/fa43c1dd4d-1677589452/kenney_interface-sounds.zip （0.80MB） | 100 | 100 | OGG 44.1kHz：77 单声道 + 23 立体声 | 0.01–1.94s | ✅ |
| Impact Sounds | https://kenney.nl/assets/impact-sounds | https://kenney.nl/media/pages/assets/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip （0.76MB） | 130 | 130 | OGG 44.1kHz 立体声 | 0.11–1.74s | ✅ |
| Casino Audio | https://kenney.nl/assets/casino-audio | https://kenney.nl/media/pages/assets/casino-audio/2472606a04-1721639069/kenney_casino-audio.zip （0.84MB） | 50 | 54（另含 Preview） | OGG 44.1kHz 立体声 | 0.17–1.5s 级 | ✅ |
| Digital Audio | https://kenney.nl/assets/digital-audio | https://kenney.nl/media/pages/assets/digital-audio/216eac4753-1677590265/kenney_digital-audio.zip （0.94MB） | 60 | 62（另含 Preview） | OGG 44.1kHz：47 单声道 + 15 立体声 | 0.31s–数秒 | ✅ |
| Music Jingles | https://kenney.nl/assets/music-jingles | https://kenney.nl/media/pages/assets/music-jingles/f37e530b9e-1677590399/kenney_music-jingles.zip （1.18MB） | 85 | 85（另含 Preview） | OGG 44.1kHz 立体声 | 0.28s–数秒 | ✅ |
| Sci-Fi Sounds | https://kenney.nl/assets/sci-fi-sounds | https://kenney.nl/media/pages/assets/sci-fi-sounds/6b296f9ecf-1677589334/kenney_sci-fi-sounds.zip （5.6MB） | 70 | 未下载（>5MB 小样纪律） | — | — | 页标 CC0，未抽验 |
| RPG Audio | https://kenney.nl/assets/rpg-audio | https://kenney.nl/media/pages/assets/rpg-audio/8e99002d76-1677590336/kenney_rpg-audio.zip （0.92MB） | 50 | 未下载 | — | — | 页标 CC0，未抽验 |
| Voiceover Pack | https://kenney.nl/assets/voiceover-pack | https://kenney.nl/media/pages/assets/voiceover-pack/3f7f168698-1677589897/kenney_voiceover-pack.zip （1.77MB） | 90 | 未下载（吸嘟嘟用不上） | — | — | 页标 CC0，未抽验 |
| Voiceover Pack (Fighter) | https://kenney.nl/assets/voiceover-pack-fighter | https://kenney.nl/media/pages/assets/voiceover-pack-fighter/6ceb77c6f1-1677589837/kenney_voiceover-pack-fighter.zip （1.21MB） | 45 | 未下载 | — | — | 页标 CC0，未抽验 |

> 提示：官方还有一把梭方案「Kenney Game Assets All-in-1」（https://kenney.itch.io/kenney-game-assets ，免费/随意付），一次拿全所有资产+更新，许可同为 CC0。

### 1.2 包内文件清单（实测全量，2026-09-30 版包）

- **UI Audio（51 SFX）**：click1–5、mouseclick1、mouserelease1、rollover1–6、switch1–38 → 纯按钮类短音；switch 系列多达 38 件，是「标签切换」的富矿。
- **Interface Sounds（100 SFX）**：back_001–004、bong_001、click_001–005、close_001–004、confirmation_001–004、drop_001–004、error_001–008、glass_001–006、glitch_001–004、maximize_001–009、minimize_001–009、open_001–004、pluck_001–002、question_001–004、scratch_001–005、scroll_001–005、select_001–008、switch_001–007、tick_001/002/004、toggle_001–004 → **UI 槽位核心包**：确认/错误/弹窗开关/勾选/返回/倒计时嘀嗒全齐。
- **Impact Sounds（130 SFX）**：footstep_（carpet/concrete/grass/snow/wood，各×5）+ impactBell/Glass/Metal/Mining/Plank/Plate/Punch/Soft/Tin/Wood_（heavy/light/medium，各×5）→ 碰撞/物理类；impactPlate、impactTin 可当「宝箱/金币物理叮当」底料；impactSoft 适合吸尘吸入的闷响。
- **Casino Audio（54 SFX）**：card-fan/place/shove/shuffle/slide、cards-pack-open/take-out、chip-lay、chips-collide/handle/stack、dice-grab/shake/throw、die-throw → **注意：现行版已无 coin 音**（旧版 coin1–6 已下架）；chips-collide/chips-stack 是最接近金币叮当的物理声；cards-pack-open 可当「宝箱开启」。
- **Digital Audio（62 SFX）**：highDown、highUp、laser1–9、lowDown、lowRandom、lowThreeTone、pepSound1–5、phaseJump1–5、phaserDown1–3、phaserUp1–7、powerUp1–12、spaceTrash1–5、threeTone1–2、tone1、twoTone1–2、zap1–2、zapThreeToneDown/Up、zapTwoTone×2 → **电子收集音核心**：highUp/threeTone/twoTone/powerUp 系列适合「星星/收集/购买成功」。
- **Music Jingles（85 SFX）**：jingles_NES00–16、jingles_HIT00–16、jingles_PIZZI00–16、jingles_SAX00–16、jingles_STEEL00–16（五组乐器族×17）→ **2026 现行版已按乐器族命名**（旧版 achievement/sad/star 命名已废），需试听挑选；PIZZI（拨弦）组最贴治愈系糖瓷风。

### 1.3 实测注意点（踩坑预警）

1. **Preview.ogg 是全包演示串烧（13–49s），严禁入包**——会吃掉音频预算；
2. 包内存在**超 0dBFS 文件**：tick_001 实测 TruePeak **+0.5 dBFS**、UI Audio Preview +2.1 dBFS → 必须过限幅器；
3. 响度散布大：实测积分响度 **-10.6 ~ -22.0 LUFS** 不等（confirmation_002=-13.3、error_003=-15.9、powerUp3=-14.5、highUp=-10.6、jingles_PIZZI05=-13.4、impactPlate_light_001=-22.0）→ **全部必须过 L0 归一化链**（详见第 5 节）；超短音（<0.05s，如 click_002=0.01s、tick_001=0.02s）EBU 无法积分，按峰值对齐处理；
4. Music Jingles 现行命名不表意，采购后需约 15 分钟试听标注；
5. zip 内 `License.txt` 随包归档到项目 `assets/licenses/`，作为商用证据链留存。

## 2. 其他站点库盘点（freesound / OpenGameArt / Pixabay / Mixkit / Zapsplat / sonniss GDC）

### 2.1 freesound.org —— 逐件多许可，必须勾 CC0【确认】
- 许可模式：每件独立标注（CC0 / CC-BY / CC-BY-NC / CC-BY-NC-ND，另存少量历史 Sampling+）。**商用且免署名 ⇒ 只采 CC0 件**。
- CC0 过滤实测（网页参数法）：搜索 URL 参数 `f=license:"Creative Commons 0"`，示例：
  `https://freesound.org/search/?q=coin&f=license%3A%22Creative%20Commons%200%22` → 实测命中 **1,715 件**。
  （网页 UI 等价操作：结果页 Filters → License → Creative Commons 0；另有官方 API+token 可批量检索下载。）
- 单件许可核验法（实测）：单件页源码含 `license text" href="http://creativecommons.org/publicdomain/zero/1.0/"` 与徽标 `Creative Commons 0`。
- 本调研已单页核验 4 件 CC0 金币/收集音候选：

  | 声音 | 作者 | 单页 URL | 实测参数 |
  |---|---|---|---|
  | Coins35.wav | doudar41 | https://freesound.org/people/doudar41/sounds/573374/ | 0.69s / WAV 44.1kHz·16bit·单声道 / 60.2KB |
  | CoinDrop8.wav | NickMorris | https://freesound.org/people/NickMorris/sounds/184744/ | CC0 徽标已验 |
  | Natural Metal Coin Sound 5.wav | The-Sacha-Rush | https://freesound.org/people/The-Sacha-Rush/sounds/400116/ | CC0 徽标已验 |
  | GAMEMisc_Designed, Coin, Pick-Up…Digital_15 | JW_Audio | https://freesound.org/people/JW_Audio/sounds/830033/ | CC0 徽标已验 |

- 质量参差应对（实操）：①按下载量/评分排序（`&s=score+desc`）；②同槽取 2–3 件 A/B 试听；③**电平问题统一交给 L0 链**——采购只挑音色，不用挑响度；④下载需免费注册。
- **裁定：只作「单点补缺源」**（Kenney 缺什么补什么），不作整包源——逐件人工核验成本高。

### 2.2 OpenGameArt —— 逐件多许可，必须勾 CC0【确认】
- CC0 过滤实测：高级搜索许可参数 `field_art_licenses_tid[]=4`（表单 option `value="4">CC0` 实测抓取），音效类型参数 `field_art_type_tid[]=13`。组合 URL：
  `https://opengameart.org/art-search-advanced?keys=coin&field_art_type_tid%5B%5D=13&field_art_licenses_tid%5B%5D=4` → 实测 **27 件**（过滤生效）。
- 候选包（CC0 实证）：
  - **512 Sound Effects (8-bit style)**（作者 SubspaceAudio；页 https://opengameart.org/content/512-sound-effects-8-bit-style ）：页面许可字段实测 `License(s): CC0`；作者评论原文 *"It's CC0 license so you are free to do what ever you like with these sounds."*；下载件名 `The Essential Retro Video Game Sound Effects Collection [512 sounds].zip`。512 件 8-bit 复古合成音，与「治愈系糖瓷」风格匹配度中，**备选**。
- 风险：OGA 存在 GPL / CC-BY-SA / CC-BY / NC 素材 ⇒ **不带 license=4 参数的检索结果一律不采**。

### 2.3 Pixabay Audio —— Pixabay License，可商用免署名【确认】
- 许可原文（License Summary；原页 https://pixabay.com/service/license-summary/ 有反爬 403，经 2025 年 Wayback 存证抓取）：
  - ✓ *"Use Content for free"*；✓ *"Use Content without having to attribute the author (although giving credit is always appreciated by our community!)"*；✓ *"Modify or adapt Content into new works"*
  - ✕ *"You cannot sell or distribute Content (either in digital or physical form) on a Standalone basis. Standalone means where no creative effort has been applied to the Content and it remains in substantially the same form as it exists on our website."*
- **裁定**：游戏内使用=有创造性加工，**可商用、免署名、可修改** ✅；红线=不得原样再分发、含可识别商标/真人内容禁商用、不得用作商标。页面自述 *"only the full Content License is legally binding"*（全文 https://pixabay.com/service/terms/ ，**采购时人工存证一次**）。定位：**BGM/氛围乐补充源**。

### 2.4 Mixkit —— 分项许可（Sound Effects Free License）【待证】
- 官方许可页 https://mixkit.co/license/ 为分项许可结构（Stock Video / Stock Music / **Sound Effects Free License** / Video Templates / Art），全站素材页挂 `license/#sfxFree` 锚点（页面结构实测存在）；**分项正文为 JS 渲染，本调研抓不到原文**。
- 第三方转述（kripeshadwani.com 2026 年评测）："All sound effects on Mixkit fall under the Sound Effects Free License. You can use them on your personal and commercial projects … videogames …"
- 已知红线（Mixkit License 通例）：免署名、可商用、可入游戏；禁原样再分发/单独售卖、禁 NFT。
- **裁定：备用源**。主会话用浏览器打开 https://mixkit.co/license/ 人工抄录 Sound Effects Free License 原文存证（1 分钟）后方可采；未存证前不采。

### 2.5 Zapsplat —— 免费档强制署名【确认 · 条件禁碰】
- Standard License 原文（https://www.zapsplat.com/license-type/standard-license/）：
  - Basic (Free)：*"You may download and use our sound effects and music tracks in an unlimited number of personal, commercial, and broadcast projects worldwide, in perpetuity, on a non-exclusive basis."* ＋ *"Attribution Required: You must provide clear credit to 'ZapSplat' wherever reasonably possible in your project."*；免费档仅 MP3、限速下载、需注册。
  - Premium：*"Attribution not required for Premium members."*；WAV 可下；订阅期内下载终身可用。
  - 禁止：声音 *"must not constitute the primary value of a product (for example a sound effects app)"*、不得项目外再分发。
- **裁定：不采**。微信小游戏没有署名位；为免署名买 Premium 不值（Kenney/freesound 已覆盖需求）。若未来要采：Premium，或「设置页致谢名单」方案。

### 2.6 sonniss GDC Game Audio Bundles —— royalty-free 商用【确认 · 体积不合适】
- 官方许可原文（https://sonniss.com/gameaudiogdc ）：
  - *"These sound effects are completely royalty-free for any commercial work. No fees, no paperwork. Use them in games you sell, YouTube videos you monetize, or client projects you invoice for."*
  - *"Attribution is always appreciated, but never required."*
  - *"Layer them, stretch them, pitch them, mangle them - make them completely yours."*（可修改）
  - *"Not as standalone files or in sound effect libraries. But you can absolutely sell them as part of your finished game, film, app, or creative project."*（禁原样再分发，可入成品）
  - *"AI/ML training is strictly prohibited under our license."*
- 体积：GDC 2026 包 **7.47GB / 347 个 WAV**（https://gdc.sonniss.com/ ）；GDC 2024 包 27.5GB+；历史包累计 **200GB+**（https://gdc.sonniss.com/gdc-game-audio-bundle/ ）。
- **裁定**：品质顶级但与「总包音频预算 ≤2MB」不匹配（WAV 巨件+筛选成本高）；仅作品质升级素材源，**本轮不采购**。

## 3. GitHub CC0 音频仓库三看清单（star / 最近提交 / 许可证文件）

**检索面**：GitHub Search API，12 组关键词/主题（kenney audio、kenney assets、cc0 sound effects、cc0 sfx、sound effects public domain game、opengameart mirror、freesound cc0、retro game sfx cc0、topic:cc0+audio、topic:cc0+sfx、topic:sound-effects+cc0 等，按 star 降序）。

**结论：无「三证据全达标」的可下载音频资产仓库——GitHub 不作为本轮采购渠道。** Kenney 镜像普遍 0–25 star、停更 3–6 年或仅含个别包；CC0 小仓库 star=0 过不了三看法。**一手源 kenney.nl 的证据链（页面徽标＋og 描述＋包内 License.txt）远强于任何镜像**。逐仓三证据（2026-09-30 实测）：

| 仓库 | star | 最近 push | 许可证文件 | 内容 | 判定 |
|---|---|---|---|---|---|
| Calinou/kenney-ui-audio | 25 | 2020-12-06 | ✅ LICENSE.txt 原文：*"License (Creative Commons Zero, CC0)… You may use these assets in personal and commercial projects. Credit (Kenney or www.kenney.nl) would be nice but is not mandatory."* | 旧版 Kenney UI Audio 的 Godot 封装（click/rollover/mouseclick 等 WAV） | 停更近 6 年＋仅 1 包＋旧版 → **不采**；仅作 Kenney 商用条款的历史佐证 |
| Boyquotes/kenney-rpg-audio-for-godot | 0 | 2023-04-20 | ✅ CC0-1.0 | Kenney RPG Audio 的 Godot 移植 | star=0，三看不过 → 不采 |
| Boyquotes/kenney-digital-audio-for-godot | 0 | 2023-04-20 | ✅ CC0-1.0 | Kenney Digital Audio 的 Godot 移植 | star=0 → 不采 |
| iwenzhou/kenney | 5 | 2016-03-12 | ✅ CC0-1.0 | 2016 年老版 Kenney Asset Pack | 停更 10 年＋陈旧 → 不采 |
| skyzhao1223/free-for-creators | 16 | 2026-09-22 | ✅ CC0-1.0 | 148 项免费素材「许可核验索引」（中英双语，逐项标注商用/署名规则） | 非音频包；**收作参考索引**，非下载源 |
| stargatedaw/stargate-sample-pack | 36 | 2022-12-24 | ❌ NOASSERTION（无标准许可文件） | 公有领域采样包（Stargate DAW 向） | 无许可文件＋风格不符 → 不采 |
| flreey/sfxmint-mcp、sindriax/blip8-sounds、RezaParsian/free-sfx-bgm-pack、sandraschi/sfx-mcp 等 | 0 | 2026-08/09 | CC0 声明（部分有文件） | MCP 工具 / 脚本合成音 | star=0＋非成熟资产库 → 不采 |

> 给 CEO 的一句话：GitHub 上「能直接下载的 CC0 音效」几乎都是 kenney.nl 的二手镜像或零星合成音，三看法一个都不全；直接用第 1 节的 kenney.nl 官方直链——更快、证据更硬。

## 4. 逐槽映射表（核心交付）

**许可证据统一说明**：
- 本表所有 Kenney 文件：包内 `License.txt` 原文 `License (Creative Commons Zero, CC0)`（6 包实测）＋包页徽标 `License Creative Commons CC0`（包页 URL 见 1.1 表）＝ CC0，免署名可商用。
- freesound 候选：单页 CC0 徽标已验（URL 见 2.1）。
- OGA 候选：页面 `License(s): CC0` 字段实测。
- 时长全部为本调研 ffprobe 实测；「入包大小」按转码 AAC 64kbps 单声道 ≈ 8KB/s 估算。

| # | 声音槽 | 主选（库·包·文件名） | 备选 | 实测时长（主选） | 入包大小估算 | 备注 |
|---|---|---|---|---|---|---|
| 1 | 按钮点击 | Kenney·Interface·`click_001` | Interface `click_004`；UI Audio `click1`/`rollover1`（悬停） | 0.10s | ~0.8KB | ⚠️ `click_002/003/005` 实测仅 0.01s，过碎慎选 |
| 2 | 确认 | Kenney·Interface·`confirmation_002` | `confirmation_001`(0.29s)/`003`(0.32s)/`004`(0.49s) | 0.54s（-13.3 LUFS·TP-0.9） | ~4.3KB | 双音「叮咚」语义正 |
| 3 | 取消/返回 | Kenney·Interface·`back_003` | `back_002`/`back_004`（均 0.07s）；`minimize_001`(0.26s) 更轻 | 0.09s | ~0.7KB | 轻短回落感 |
| 4 | 错误/失败提示 | Kenney·Interface·`error_003` | `error_001`(0.16s)/`004`(0.10s)/`008`(0.14s)，8 件可选 | 0.53s（-15.9 LUFS·TP-0.2） | ~4.2KB | 软错误；硬错误用 Digital `zapTwoTone`(1.31s) |
| 5 | 金币叮 | Kenney·Casino·`chips-collide-1`（物理叮当） | A 电子风：Digital `highUp`(0.55s·-10.6 LUFS)/`threeTone1`(0.83s)/`twoTone1`(0.72s)；B freesound CC0 已验：`Coins35`(0.69s·44.1kHz·mono)/`CoinDrop8`/`Natural Metal Coin 5`/`JW_Audio Coin Pick-Up 15` | 0.26s | ~2.1KB | ⚠️ 现行 Casino 包已无 coin 音，chips 系列是最接近的物理声 |
| 6 | 购买成功 | Kenney·Digital·`powerUp3`（+chips-stack 叠层） | `powerUp1`(1.20s)/`powerUp5`(0.44s)/`powerUp12`(0.86s)；Casino `chips-stack-1`(0.29s) | 1.15s（-14.5 LUFS·TP-2.1 达标最好） | ~9.2KB | 上扬+叮当组合 |
| 7 | 宝箱开启 | Kenney·Casino·`cards-pack-open-1`（开包声） | `cards-pack-open-2`(0.73s)；Interface `open_001`(0.15s)/`open_004`(0.32s)；Digital `powerUp12` | 0.94s | ~7.5KB | 「撕开+叮当」两段式，天然贴宝箱 |
| 8 | 星星/收集 | Kenney·Digital·`highUp` | `pepSound1`(0.52s)/`pepSound5`(0.63s)/`threeTone1`；糖瓷玻璃风：Interface `glass_001`(0.28s)/`glass_004`(0.69s) | 0.55s（-10.6 LUFS·TP-0.1） | ~4.4KB | 逐颗星可 pitch 上移 +2 半音递进 |
| 9 | 奖励发放 | Kenney·Music Jingles·`jingles_PIZZI05`（PIZZI 拨弦组试听定稿） | Digital `powerUp` 系列；Casino `chips-stack` 连响 | 0.54s（-13.4 LUFS） | ~4.3KB | 需试听；`jingles_PIZZI00`(0.49s)/`PIZZI03`(1.15s) 备选 |
| 10 | 倒计时嘀 | Kenney·Interface·`tick_004` | `tick_001`/`tick_002`（均 0.02s，⚠️ tick_001 实测 TP+0.5dBFS 必须限幅）；长嘀：Digital `tone1`(0.66s)/`lowThreeTone`(1.02s)；freesound CC0 检索 `clock tick` | 0.05s | ~0.4KB | 超短音按峰值对齐处理 |
| 11 | 胜利 | Kenney·Music Jingles·`jingles_PIZZI01`（试听定稿，PIZZI 组优先） | `jingles_PIZZI03`(1.15s)/`jingles_NES00`(1.76s)/`jingles_HIT00`(0.28s)；Digital `phaserUp1` 组合 | 1.00s | ~8KB | 五组×17 件需试听标注（乐器族命名不表意） |
| 12 | 失败 | Kenney·Digital·`phaserDown1`（下行）＋Music Jingles 低走件试听 | `lowDown`(0.78s)/`highDown`(0.52s)；Interface `error_005–008` | ~0.5–1s | ~6.4KB | 治愈系失败=温和下行音，忌刺耳 |
| 13 | 弹窗开 | Kenney·Interface·`maximize_001` | `maximize_009`(0.22s)/`open_001`(0.15s)/`open_004`(0.32s) | 0.26s | ~2.1KB | 与「确认」区分度足够 |
| 14 | 弹窗关 | Kenney·Interface·`minimize_001` | `minimize_009`(0.22s)/`close_001`(0.15s)/`close_004`(0.32s) | 0.26s | ~2.1KB | — |
| 15 | 标签切换 | Kenney·UI Audio·`switch1` | UI Audio `switch2–38`（38 件富矿：switch15 0.26s/switch30 0.36s）；Interface `switch_001`(0.62s)/`toggle_001`(0.14s)/`toggle_004`(0.07s)；UI Audio `rollover` 系列做悬停 | 0.31s | ~2.5KB | 每个页签可绑不同 switch 编号 |
| 16 | 星星升起 | Kenney·Digital·`phaserUp1`（上行滑音） | `phaserUp3`(0.52s)/`phaseJump1`(0.47s)；Interface `glass_004` 高音区；Music Jingles 上升件 | 0.50s | ~4KB | 结算页星星逐颗升可叠加 pitch 递进 |

**汇总**：16 槽主选合计 ≈ **60KB**；连同备选/变体约 40 件 ≈ **150KB**，占 2MB 预算 <8%。
**玩法专属音**（吸尘嗡鸣、吸入闷响、糖果碰撞）不在本表 16 槽内：闷响可用 Impact `impactSoft_medium_000`(0.12s)/`impactGlass_light_001`(0.21s) 叠层，嗡鸣建议内部合成或 freesound CC0 `vacuum` 检索——采购时另列。

## 5. 下载件技术面预估（格式 / 采样率 / 响度归一化 / L0 门）

### 5.1 源格式实测
- **Kenney 全包**：OGG Vorbis / 44.1kHz（每包另含 1 件 48kHz 文件＝Preview 演示串烧，禁用）；声道混杂：Interface 77% 单声道、Digital 75% 单声道，Impact/Jingles/Casino/UI Audio 以立体声为主。
- **freesound**：WAV 44.1/48kHz 为主（单件页标注采样率/位深/声道，如 Coins35＝44.1kHz·16bit·单声道）。
- **OGA 512 包**：WAV（8-bit 复古合成音）。
- **sonniss**：WAV 48kHz+ 大文件（本轮不采）。

### 5.2 响度/峰值实测（ebur128 抽样 10 件）
- 积分响度散布 **-10.6 ~ -22.0 LUFS**（confirmation_002=-13.3 / error_003=-15.9 / powerUp3=-14.5 / highUp=-10.6 / jingles_PIZZI05=-13.4 / impactPlate_light_001=-22.0）→ 源与源之间差近 12dB，**必须统一归一化**。
- 真峰值：多个贴 0 dBFS（highUp -0.1 / error_003 -0.2）；**`tick_001` 实测 +0.5 dBFS（已超 0dBFS）**；预览串烧最高 +2.1 dBFS → 必须过限幅。
- 超短音（≤0.05s：click_003 0.01s、tick_002 0.02s 等）EBU 积分无效 → 按真峰值对齐处理。
- **结论：100% 要过内部 L0 链**。好处：采购时「源响度参差」这个质量变量被链统一抹平——选料只挑音色，电平交给链。

### 5.3 L0 门与转码管线（SFX -16 LUFS · TP≤-3 dBTP · 44.1kHz 单声道 · 全包音频 ≤2MB）
1. 归一化（本机 ffmpeg 已确认可用；长音建议两遍 loudnorm，短音用增益+限幅）：
   ```
   ffmpeg -i in.ogg -af "highpass=f=60,loudnorm=I=-16:TP=-3:LRA=9:print_format=summary" -ar 44100 -ac 1 -c:a pcm_s16le out.wav
   ```
   （超短音替换为：`-af "volume=XdB,alimiter=limit=0.7079:level=false"` 峰值对齐。）
2. **封装格式（微信小游戏关键结论）**：InnerAudioContext 官方支持格式表（https://mp.weixin.qq.com/debug/minigame/dev/api/InnerAudioContext.html ，实测直引）：

   | 格式 | iOS | Android |
   |---|---|---|
   | m4a | √ | √ |
   | aac | √ | √ |
   | mp3 | √ | √ |
   | wav | √ | √ |
   | **ogg** | **✗** | √ |
   | flac | ✗ | √ |

   ⇒ **Kenney 的 OGG 源不能直接入包（iOS 不支持），必须转码**。目标：**m4a/aac 44.1kHz·单声道·64kbps**（短 UI 音可 48kbps）：
   ```
   ffmpeg -i out.wav -c:a aac -b:a 64k -ar 44100 -ac 1 out.m4a
   ```
3. 预算核算（AAC 64kbps mono ≈ 8KB/s）：16 槽主选 ≈60KB＋备选共 ≈150KB；BGM 30–60s 循环（96kbps 立体声）≈ 0.4–0.7MB → 全部 ≈ **0.9MB ≤ 2MB** ✅。
4. 逐件验收（复测 L0 门）：
   ```
   ffmpeg -i out.m4a -af ebur128=peak=true -f null NUL
   ```
   看 Integrated ≈ -16 LUFS、True Peak ≤ -3 dBTP；不合格回炉。

## 6. 禁碰清单（许可不明或禁商用——逐个点名）

| # | 源 | 许可实情（证据直引） | 裁定 |
|---|---|---|---|
| 1 | **BBC Sound Effects**（sound-effects.bbcrewind.co.uk / bbcsfx.acropolis.org.uk） | BBC 官方：*"These Sound Effects are BBC copyright, but you might be able to use them for personal, educational or research purposes, as detailed in the licence."*（https://www.bbc.co.uk/contact/questions/using-bbc-content/use-sound-effects/ ）；站点首页自述 *"use them in your own personal/educational projects, or licence them for use"* | **禁碰**：免费范围=个人/教育/研究；商用需另购 BBC 授权 |
| 2 | **爱给网 aigei.com** | 其《许可协议》页（https://www.aigei.com/about/license ）自述平台支持**多种许可协议**（CC0/CC-BY/含「不可以商用」的 NC 系等，逐件混杂），站内素材分「免费商用(CC协议)/版权商用(付费)」双轨（配乐 199元/首、音效类同） | **默认禁碰**：逐件核对成本高＋误取 NC 件风险大；除非逐件核验并存证授权页，否则不采 |
| 3 | **freesound 非 CC0 件** | CC-BY-NC / CC-BY-NC-ND（禁商用）、CC-BY（强制署名，微信小游戏无署名位） | **禁碰**：只取 `f=license:"Creative Commons 0"` 过滤结果 |
| 4 | **OpenGameArt GPL / CC-BY-SA 音效** | OGA 高级搜索许可列表含 GPL、CC-BY-SA 等条款 | **禁碰**：闭源游戏内嵌音频不走 GPL/SA；OGA 检索必须带 `field_art_licenses_tid[]=4` |
| 5 | **Zapsplat 免费档** | *"Attribution Required: You must provide clear credit to 'ZapSplat'"*（标准许可原文） | **条件禁碰**：免署名须购 Premium 或接受设置页署名；本轮不采 |
| 6 | **商业游戏/影视/视频里扒的音效** | 无授权=直接侵权 | **绝对禁碰** |
| 7 | **会员制素材站**（千图网/包图网/站长素材类） | 授权范围、可否入游戏包、转售条款均不透明（本调研未取得可靠许可原文） | **禁碰** |
| 8 | 提醒（非禁碰，但属红线）：Pixabay / Mixkit / sonniss / Zapsplat 均有「禁止原样再分发」条款（如 Pixabay *"cannot sell or distribute Content … on a Standalone basis"*） | — | 我们=游戏内创造性使用 ✅；但**不得**把素材包原样挂网盘/商店/资源站二次分发 |

## 7. 采购建议执行序（主会话按此一步执行）

**总方针**：16 槽里 ~14 槽用 Kenney 一次拿全（6 包共 ~4.9MB / 482 件 SFX / 全 CC0，10 分钟）；金币叮备选走 freesound CC0（1,715 件已过滤好检索式）；Music Jingles 需 15–30 分钟试听标注；BGM 视需要走 Pixabay/Mixkit。**所有源一律过 L0 链并转码 m4a/aac（微信 iOS 不支持 ogg）**。全程许可证随包归档。

### Step 1 · 下载 Kenney 6 包（直链均实测可达）
```powershell
$d = "<暂存目录>\kenney-audio"
New-Item -ItemType Directory -Force -Path $d | Out-Null
$packs = @{
 'ui-audio'         = 'https://kenney.nl/media/pages/assets/ui-audio/490d233f68-1677590494/kenney_ui-audio.zip'
 'interface-sounds' = 'https://kenney.nl/media/pages/assets/interface-sounds/fa43c1dd4d-1677589452/kenney_interface-sounds.zip'
 'impact-sounds'    = 'https://kenney.nl/media/pages/assets/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip'
 'casino-audio'     = 'https://kenney.nl/media/pages/assets/casino-audio/2472606a04-1721639069/kenney_casino-audio.zip'
 'digital-audio'    = 'https://kenney.nl/media/pages/assets/digital-audio/216eac4753-1677590265/kenney_digital-audio.zip'
 'music-jingles'    = 'https://kenney.nl/media/pages/assets/music-jingles/f37e530b9e-1677590399/kenney_music-jingles.zip'
}
foreach($k in $packs.Keys){ curl.exe -s -o "$d\kenney_$k.zip" $packs[$k]; Expand-Archive "$d\kenney_$k.zip" "$d\$k" -Force }
Remove-Item "$d\*\Preview.ogg" -ErrorAction SilentlyContinue   # 剔除演示串烧
Copy-Item "$d\*\License.txt" "<项目>\assets\licenses\kenney\"   # 许可证据归档
```
**验收**：每包 `License.txt` 含 `License (Creative Commons Zero, CC0)` → 通过；任何一包没有 → 停止并回报。

### Step 2 · 试听标注（约 30 分钟）
- Interface Sounds 100 件快过打标（文件名即语义）；Music Jingles 85 件（五组×17）挑出：胜利 / 失败 / 奖励发放（**PIZZI 拨弦组最贴治愈系糖瓷风**）；Casino chips 系列定金币主选。

### Step 3 · 按第 4 节槽位表定稿 ~30 件 → 跑 L0 链（命令见 5.3）→ ebur128 复测（-16 LUFS / TP≤-3 dBTP）→ 输出 m4a·44.1kHz·单声道·64kbps。

### Step 4 ·（可选）补缺采购
- 金币叮不满意 → freesound CC0 检索式（已预核验 4 件候选，见 2.1 表）：
  `https://freesound.org/search/?q=coin&f=license%3A%22Creative%20Commons%200%22&s=score+desc`
- 倒计时嘀要更机械 → 同式换关键词 `clock tick`；复古风备选 → OGA：
  `https://opengameart.org/art-search-advanced?keys=countdown&field_art_type_tid%5B%5D=13&field_art_licenses_tid%5B%5D=4`
- freesound/OGA 每采 1 件：单页许可徽标截图/URL 存证后再用。

### Step 5 ·（若需 BGM）Pixabay 音频（许可见 2.3，人工存证一次条款页）或 Mixkit（先人工打开 https://mixkit.co/license/ 抄录分项原文存证）。循环体 30–60s、96kbps ≈ 0.4–0.7MB。

### Step 6 · 合包验收
全部音频 ≤2MB；iOS/Android 真机抽查可播（m4a）；`assets/licenses/` 存：6 份 License.txt ＋ freesound/OGA 单页许可存证 ＋ 采购日期（2026-09-30 后）。

**红线**：不下载任何 BBC / 爱给网 / CC-BY-NC / GPL / CC-BY-SA / Zapsplat 免费档素材（依据见第 6 节）。

---

状态：完成
（2026-09-30 · 调研员D；全部许可证据已实测直引；采购待主会话按第 7 节执行序执行）
