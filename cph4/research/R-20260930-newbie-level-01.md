# R-20260930 吸嘟嘟新手关（关 1「家·晨光房间」）吸引力改造方案

- 调研员：FluxGroup 关卡体验调研员（Codely 派遣）
- 日期：2026-09-30（Asia/Shanghai）
- 触发：CEO 判语（原话）——「新手关卡做的很不吸引人」
- 对象：吸嘟嘟（微信小游戏·吸取制休闲清洁玩法·治愈系卡通）首章首关 = 关 1「家·晨光房间」（章 1 覆盖关 1-5，出处：`Assets\_Project\Levels\ChapterLore.cs` ChapterNames[0]）
- 纪律声明：代码面全部实读；外部范式每条给来源，查不到写「未能核实」。本文件为唯一产出，任务中途被杀时以已落盘章节为准。

## 撰写进度（任务已完成·本节为执行记录）

- [x] 骨架建立
- [x] ①现况审计（关 1 配置实读+截图证据+吸引力缺口清单 G1-G12）
- [x] ②头部首关范式 P1-P12（外部对标·逐条带来源）
- [x] ③改造提案 T1-T15（五组分类+机器可验判据）
- [x] ④优先级 P0/P1/P2+执行顺序+未能核实项披露

---

## ① 现况审计

### 1.1 关 1 配置实读（代码面，逐条带出处）

| 项 | 值 | 出处 |
|---|---|---|
| 关卡定位 | 新手关 = 新 id1 = 样例 L1（教学首关），章 1「家 · 晨光房间」覆盖关 1-5 | `Levels/ContentCatalog.cs` CurriculumOldId 表（新 id1 = 样例 L1）；`Levels/ChapterLore.cs` ChapterNames[0] |
| 标题 | 「早安，你的房间」 | `Levels/LevelCatalog.cs` BuildL1() |
| 时限 / 目标 | 45s / 全清（goalClearedCount=-1），dust 100% | `Levels/LevelCatalog.cs` BuildL1()：`timeLimitSec=45f, goalClearedCount=-1` |
| 实体构成 | 16 只 dust 收成 3 个密集簇 + 1 只签名袜（sock）注入 = 全清 17 件 | BuildL1() 16 条 spawn；`ContentCatalog.ApplySignatureInjections`：`levels[0].spawns.Add(sock, x=5.8, y=-1.2, scale=0.95)` |
| 三簇语义 | A 簇 6 只=「清晨床边的浮尘团」（左下床脚）；B 簇 5 只=最密主角簇（贴嘟嘟出生点=首按即大团吸入）；C 簇 5 只=「飘窗边的晨光尘」（三簇最高） | BuildL1() 内逐条注释与坐标 |
| 理论最优 / 余量 | ≈16s / ≈29s（压力比 ~2.8，注释自称「首关爽感优先」；45s=≥1.8× 不可失败契约） | BuildL1() 注释「四难度数据」；`ContentCatalog.SampleOptimalSec = {16f,…}` |
| 难度单价 | dust 0.8s/只 ｜ fur 2.0s/只 ｜ debris 3.0s/只 ｜ 簇间跳转 1.5s/跳 | `ContentCatalog.cs` 类头注释「难度模型」 |
| 签名袜行为 | 「床底失踪的另一只袜子（逃跑+藏匿）」——吸场靠近小步窜逃，逃跑力随进度平方衰减，按住必得（治愈红线） | `ContentCatalog.ApplySignatureInjections` 关1 注释；`Gameplay/SignatureTargets.cs` SockTarget（fleeFactor 0.85、maxSpeed 6.5） |
| 签名袜反馈三件套 | 专属音（sfx_sig_sock 真声优先/合成回退）+ 薄荷色粒子 + 嘟嘟三拍反应（惊呆 0.35s→鼓腮 0.25s→狂喜 0.9s） | `Audio/SfxFlow.cs` SignatureClipFor；`SuctionTarget.BurstTint`/`OnCapturedFeedback`；`ActorDudu.SignatureReactionSeq` |
| 吸力场手感 | 半径 2.2、强度 12、跟手 lerp 0.35、最近 3 件并行捕获上限 | `Gameplay/SuctionFieldConfig.cs` 默认值 |
| dust 手感 | mass 0.15 / 阈值 0.15 / maxSpeed 15——「贴手即死、连续成串」 | `Gameplay/DustTarget.cs` |
| 星沙经济 | 每捕获 dust +1、签名 +5；关 1 满收 ≈ 21 星沙；失败也照收（治愈红线） | `Game/MetaFlow.cs` BaseSandPerCapture/SignatureSandPerCapture |
| 大招充能线 | 嚏风暴=捕 12 件充满（半径 ×2.5 持续 2s）；伙伴技=捕 15 件充满 | `Gameplay/SneezeSystem.cs` NeededCaptures=12；`Core/Companions/CompanionProgress.cs` ChargeNeeded=15 |

### 1.2 新手引导流实读（代码面）

现役新手流 = 「菜单直进 + 关内两条一次性文案教学」，无预览、无演出、无宽限：

1. **启动**：Bootstrap.AfterSceneLoad 自装配（零场景依赖）；首屏=健康忠告屏（ScreenRouter Boot 态），菜单背景板从 Boot 起即垫底给「第一章房间温暖底色」。出处：`Game/Bootstrap.cs` EnsureInfra/ApplyBackdrop(1)。
2. **菜单→进关**：菜单主 CTA「开吸！」→ `ContinueRequested` → 组合根按 `MaxLevelReached`（新档=0）直取 `ContentCatalog.All()[0]` → `LevelRunner.StartLevel`。**无选关、无关卡预告卡、无「本关目标」预读**。出处：`Game/Bootstrap.cs` OnContinueRequested；`UI/MainMenuScreen.cs` OnStartClicked。
3. **进关瞬间**：`LevelStarted` 发布 → `SpawnAll` 全量瞬刷 + `LevelTimer` **立刻开跑计时**（无 3-2-1、无首按宽限）。出处：`Levels/LevelRunner.cs` StartLevel；`Levels/LevelTimer.cs` OnLevelStarted。
4. **到站横幅**：章名「家 · 晨光房间」顶部横幅 1.5s（滑入 0.35s+停留 0.8s+滑出 0.35s）；**同章内不重播**（`title == _lastShown` 即跳过——关 2-5 玩家再看不到任何章节宣告）。出处：`UI/ArrivalBanner.cs`。
5. **教学层（W17-NEWBIE-FLOW）**：仅两条一次性提示——①「按住屏幕」72px 大字+「嘟嘟跟着你的指尖，吸！」+涟漪脉冲，进关 1.7s 后淡入（与横幅错拍），按住 ≥0.15s 或首捕即退场，落档 `vh.tut.press`；②「嘟嘟满啦——按下去！」2s toast，首次满能时出现，落档 `vh.tut.sneeze`。**全层 raycastTarget=false 不吞按压**。出处：`UI/TutorialHint.cs`。
6. **战斗 HUD**：顶部暖色倒计时 80px（最后 10s 脉冲 ±5%）+ 关卡标题 + 「已清 n/17」计数（每次捕获弹跳 1.30 峰+星星贝塞尔飞入计数器）+ 嚏钮 + 左下角道具/伙伴钮（库存 0 隐藏）。出处：`UI/InGameHud.cs`。
7. **结算**：`GoalTracker` 达标 → `LevelCompleted` → 灰幕揭开（RevealVeil 0.8s 淡出+暖白金泛光）→ 胜利短句+章界铃（章末关）→ ResultScreen。失败不揭幕（房间保持灰蒙）。出处：`Levels/GoalTracker.cs`；`Game/RevealVeil.cs`。

**捕获正反馈链（现役已具备）**：12 粒子爆（U320 由 8 加码）+ 捕获波纹 0.3s + 「啵」缩没曲线 + HUD 计数弹跳 + 星星飞计数器 + 嘟嘟咀嚼拍（连击 ≥3 加码）+ 连击音高阶梯 + 待机呼吸/出生弹入/被吸鼓胀微颤/拖尾 90ms + 涡流星沙 + 围观者 Happy 小跳（creature_home 五情绪）。出处：`Gameplay/CaptureBurst.cs`、`SuctionTarget.cs`、`InGameHud.cs`（W20-D/U305）、`ActorDudu.cs`（W19-JUICE）、`SuctionTrail`/`SuctionField.TickVortex`、`ChapterOnlooker.cs`。

### 1.3 截图证据（uishots-u315 四幕多模态实读）

审计对象：`gaming\MiniGame\Design\evidence\uishots-u315\`（01-notice / 02-menu / 03-level-start / 04-level-live，及 -gui 版）。

**先说定性**：该组截图为 U315「引擎真身首验板」时代产物，其中「空战场」「首屏无字」两点根因已被 U316 修复（`UI/MainMenuScreen.cs` 注释原话：「原挂屏根=永驻全屏不透明层：Boot 态盖死健康忠告屏+吞射线…局内盖死整个战场（S3『空战场』真相」）。因此截图=CEO 差评现场还原，**结构性观察仍有效，但「战场全空」不能当作现况指控**——现况以代码实读为准。

- **01-notice（首屏）**：水彩云+星星美术在位，但**无 logo、无按钮、无健康忠告文字**——首屏零信息量、无交互锚点，被动等待。多模态判读：「用户打开后无法确认『我进对游戏了吗』，前 3-5 秒流失风险高」。
- **02-menu（菜单）**：层级清晰、主 CTA「开吸！」金色橙红大胶囊+呼吸动画在位；副标语「一指吸走所有烦恼」、时段问候「早安，今天的烦恼已经摆好，就等你来吸了」、每日副题齐全。**问题：满屏零数值**（星沙 0、今日任务 0/3、宝箱 0/5）——首日玩家第一眼看到的是「空荡荡的成就位」，无任何即时奖励钩子；「同吸/嘟崽」对新手指代不透明。
- **03-level-start（关 1 开局 ~3s，计时已扣到 42 秒）**：HUD 齐（42 秒/早安，你的房间/已清 0/17）；「按住屏幕」大字教学在位。**三个异常**：①「嘟嘟满啦——按下去！」toast 在 0/17 时已出现（时机错位——按现役代码该 toast 只能在捕获 12 件后触发，此帧系 U315 时序残留）；②战场无可见灰尘/角色（U316 已修的盖屏 bug 现场证据）；③教学阅读期内计时已在扣秒。
- **04-level-live（关 1 进行中，40 秒、已清 4-7/17、伙伴 4-7/15「金漩涡」）**：HUD 完整可读；**玩法层全空、房间=抽象奶油卡纸、无家具可辨、无灰蒙蒙「脏」感**。多模态判读原话：「清洁游戏最强的吸引钩子是『看见剩下的脏东西→想吸掉』…屏幕没有可玩对象，动力归零」「更像一张早安问候卡，而不是一个正在进行中的清扫关卡」；底部棕条生硬、无暂停键。

### 1.4 吸引力缺口清单（逐条带出处）

| # | 缺口 | 证据出处 |
|---|---|---|
| G1 | **无首分钟钩子的「零秒可玩」设计**：菜单→关硬切，无目标预告、无「为什么吸」的动机铺陈；进关 0-1.7s 内玩家无任何指引（教学 1.7s 才淡入），且计时从 0 秒即扣 | `MainMenuScreen.OnStartClicked`→`Bootstrap.OnContinueRequested`（无中间层）；`TutorialHint.StartDelaySeconds=1.7`；`LevelTimer.OnLevelStarted` 立即开跑 |
| G2 | **开场零演出**：17 件实体同帧瞬刷（仅 0.35s 出生弹入），无登场编排、无镜头运动、无「脏房间」的整体展陈；「打扫前」状态从未被刻意展示 | `LevelRunner.SpawnAll` 全量同步生成；`SuctionTarget.SpawnPopDur=0.35s` |
| G3 | **教学=纯文案**：「按住屏幕」是文字+涟漪，无实体演示（嘟嘟不会自己走过去吸一只做示范）、无强制首按引导（玩家不按也会一直悬着） | `TutorialHint.cs` 全文（仅 Text+ripple） |
| G4 | **两个大招在关 1 形同虚设**：嚏需捕 12/17（71%）、伙伴需捕 15/17（88%）——新手首关几乎体验不到「满能→释放」的核心爽点循环；且嚏教学 toast 在捕 12 件后才出现，与 30s 首爽点（第一按大团吸入）之间无任何中间奖励节拍 | `SneezeSystem.NeededCaptures=12`；`CompanionProgress.ChargeNeeded=15`；关 1 总目标 17 |
| G5 | **「找袜子」招牌梗缺引导时刻**：签名袜在 (5.8,-1.2) 藏匿位，无发现提示、无特写、无「找到另一只袜子！」的叙事时刻；新手很可能全程没意识到这关有彩蛋 | `ContentCatalog.ApplySignatureInjections` 关1 注释「逃跑+藏匿——全民找袜子梗」；全工程检索无 sock 发现提示类代码 |
| G6 | **「脏→净」对比不强烈**：灰幕仅 alpha 0.20（注释自称「克制」），截图判读「灰蒙蒙的脏感完全不存在」；过关揭幕虽有，但「打扫前」的脏感铺垫太弱，前后对比打折 | `RevealVeil.VeilAlpha=0.20f`；截图 04 判读 |
| G7 | **场景 dressing 抽象**：scene_room 为 768² 整图大场景，实体簇的语义坐标（床边/飘窗）在画面上无对应家具锚点可辨识（截图判读无床无窗）；「晨光房间」叙事全靠文字 | `Game/ChapterArt.cs` SceneNames[0]="scene_room"（768² 一张图）；截图 03/04 判读「无家具」 |
| G8 | **正反馈密度无节拍设计**：捕获反馈是「每件等幅」的（16 只 dust 同一粒子同一音量），无连击里程碑、无「清完一簇」的簇级庆祝、无进度阶段演出（25%/50%/75% 无任何差异时刻）；唯一簇级爽点=首按大团，之后 15 件是平铺直叙 | `CaptureBurst.Emit`（每次捕获恒定 12 粒子）；`InGameHud.RefreshProgress`（纯数字） |
| G9 | **结算缺「哇」点**：过关=灰幕揭开+胜利短句+ResultScreen（数字结算），无星级演出/无房间焕新对照镜头/无「下一关预告」钩子（章内过关 NextChapterTitle 为空——衔接句只在章末） | `GoalTracker` LevelCompleted 事件；`ChapterLore.GetNextChapterTitle`（id<5 或非章末返回 ""） |
| G10 | **菜单首日零激励**：新档打开菜单=星沙 0/任务 0/3/宝箱 0/5，无新手礼包、无「首通送」的入局奖励（章首通赠=沙漏+磁力道具挂在**章末关 id%5==0**，即新手要打完 5 关才第一次见道具） | 截图 02 判读；`MetaFlow.OnLevelCompleted`（章首通赠条件 `e.LevelId % 5 == 0`） |
| G11 | **计时即压力**：教学未完成也在扣秒；L1 虽 45s 足够，但「倒数开始」本身就是焦虑源，与「按下就有好事发生」的零压力首关叙事相悖 | `LevelTimer`；`TutorialHint` 与计时无联动 |
| G12 | **截图暴露的打磨毛刺**（部分 U316 已修）：首屏无字（已修）、战场盖死（已修）、底部棕条生硬、无暂停键、伙伴图标紫 vs 名字「金漩涡」金的颜色错位、「n/15」与「n / 17」计数格式不一 | 截图 03/04 判读；`MainMenuScreen`/`SuctionField` U316 修复注释 |

**小结（审计结论）**：吸嘟嘟的**反馈原子件质量并不差**（捕获粒子/波纹/弹跳/飞星/咀嚼/围观者/音效链完整且多处注明 juice 加码史），CEO「不吸引人」的病根不在缺 juice 原料，而在**首分钟编排**：钩子缺位（G1/G2/G5/G9）、节拍缺位（G4/G8/G11）、新手指代与激励缺位（G3/G10），以及首关「脏乱感→清洁欲」的核心动机链太弱（G6/G7）。

## ② 头部首关范式（外部对标·双源验证）

> 来源缩写：〔DoF〕Deconstructor of Fun《Royal Match – The New King from Turkey?》(deconstructoroffun.com, 2021)；〔Gamigion/Playliner〕《Royal Match Level Design Insights》前 100 关数据拆解（gamigion.com）；〔HS-Playliner〕《Homescapes Level Design Insights》前 100 关拆解（Anton Slashcev/Playliner by SensorTower，LinkedIn）；〔Naavik〕《The Royal Blueprint: Easy to Copy… Or Not?》(naavik.co)；〔GamesNest〕《Royal Match: What Actually Matters in Your First Hour》(gamesnest.org)；〔CC-Wiki〕Candy Crush Saga Wiki「Sugar Crush」条目（candycrush.fandom.com）；〔GS-Strategy〕《Why Is Austin Watching You During Gardenscapes Levels?》(gardenscapesstrategy.com)；〔Playio〕《Onboarding Decides Your D1》2026 留存基准（blog.playio.co）；〔微信指南〕微信小游戏官方设计指南（developers.weixin.qq.com/minigame/design）；〔掘金-闪学it〕《微信小游戏开发实战》开发者实践帖（juejin.cn）。

**P1｜首 35 关「结构性必胜」——难度线远远后置**
机制：头部三消前 35 关不设失败尖峰，玩家在「学习期」几乎不可能输，把第一次真实挫折推迟到习惯养成之后。数字判据：Royal Match 前 100 关 Normal 层平均 ≈1.2 次尝试/关，首个 hard 关在 Lv 39、首个 super-hard 在 Lv 59；Homescapes Normal 层 1.1-1.4 次尝试，首个 hard 关在 Lv 37。（Gamigion/Playliner；HS-Playliner）
对照吸嘟嘟：L1 压力比 ~2.8（45s vs 最优 16s）+ W7-PLAYFIX「前五关 ≥1.8× 不可失败」——难度面上已达标，**吸引力问题不在难度而在反馈编排**（呼应 ① 小结）。

**P2｜快、短、流畅——动画时长即手感**
机制：Royal Match 被评为「最快的 switcher 之一」：道具/障碍/掉落动画刻意做短，碎屑「恰好满足感又不至于淹没棋盘」；并**删除了关卡重试之间的加载、删除了开局目标横幅（goal swipe）**以压缩单次尝试总时长；Royal Kingdom V2 又进一步加快级联速度并缩短关卡间流程，后回流进 Royal Match。数字判据：单次重试流程零加载、零非必要过场；级联动画时长以「玩家永远不用等」为准。（DoF；Naavik）
对照吸嘟嘟：有入场短句/到站横幅/结算屏等过场环节——首关重开路径上的非必要停留需按此范式重审。

**P3｜教学=边玩边学的强制首动，不是文字**
机制：Royal Match 首关以指针手型强制完成第一次匹配，即时触发级联+庆祝——玩家「第一次操作」即「第一次爽」；微信官方设计指南明文：「游戏教程应该让玩家边玩边学，不要用大量的文本来描述游戏规则」。Candy Crush 用递进赞叹词（Sweet→Tasty→Delicious→Divine）把教学期变成奖励期——每一步操作都有语音级表扬。数字判据：教学期每一次玩家动作 ≤1s 内必有视/听反馈；教程文字量趋近于零（微信指南；CC-Wiki）。

**P4｜过关庆祝仪式化（Sugar Crush 律）**
机制：Candy Crush 每关达成目标后必触发「Sugar Crush!」语音+大字+剩余步数换分庆祝——过关不是静默跳结算，而是一个有名字、有声音、有额外收益的仪式。数字判据：每次过关 = 1 个命名仪式时刻 + 剩余资源变现（CC-Wiki：sugar crush = "a reward and a way to get extra points for every move you have remaining"）。
对照吸嘟嘟：有揭幕+胜利短句但无命名仪式、无剩余时间变现——45s 关剩 20s 与剩 2s 过关体验完全相同。

**P5｜角色反应即反馈（Austin 在看你）**
机制：Playrix Scapes 系把管家 Austin 放进关卡场景，对玩家每一步操作做出表情/动作反应，设计心理学上把「系统反馈」翻译成「人物情感」——玩家打扫时有人捧场。数字判据：关键玩家动作（大消除/濒败/过关）均有角色情绪帧响应。（GS-Strategy；Austin 角色设定见 Homescapes/Gardenscapes Fandom）
对照吸嘟嘟：已有 ChapterOnlooker 五情绪+嘟嘟咀嚼拍/签名三拍反应——**此范式吸嘟嘟已具备**，缺的是把它接进首关教学编排（教学时不演示、不捧场）。

**P6｜小局快循环——「3 秒上手、30 秒一局」**
机制：微信小游戏生态的开发者共识与官方「即点即玩」价值主张：3 秒上手（不用教程，点一下就知道怎么玩）、30 秒一局（失败不心疼，重开零成本）；Royal Match 同款逻辑（删重试加载）。数字判据：从点开小游戏到第一次可玩交互 ≤3-5s；单局 ≤60s；重开 ≤1 次点击、零加载。（掘金-闪学it；DoF；微信指南「即点即玩」）

**P7｜meta 奖励前置——首小时就要「看得见的变漂亮」**
机制：Royal Match「front-loads its decoration loop because it feels rewarding」（把装修循环前置因为它是即时可感的奖励）；Homescapes 新房间在 **Lv 1、2、3、4** 连续解锁——第一分钟就开始「改造世界」；Gardenscapes 的核心动机=把荒废花园「restore to its former glory」——before/after 反差即钩子。数字判据：新场景/新可见变化在前 4 关内至少出现 1 次；装修选项 2-3 个/次（轻决策）。（GamesNest；HS-Playliner；Playrix 官方游戏介绍）
对照吸嘟嘟：章 1 五关同一房间、同一背景板（ChapterArt 章级单图）——前 5 关画面零变化，仅文字换皮（「上午·沙发缝隙」等标题），无「房间逐渐变亮/变美」的进程可视。

**P8｜新机制=「教学板→小考→尖峰」三段律**
机制：头部关卡节奏统一为「新机制投放 → 2-3 个教学板 → 难度尖峰 →（后期）超级尖峰」，即 learn→test→celebrate 循环；Homescapes 新障碍落位 Lv 8/18/22、新元素 Lv 6/12、道具 Lv 7/14/19——首个新内容在 5-8 关内必到。数字判据：每个新机制配 2-3 个专用教学关；前 10 关内至少引入 1 个新元素+1 个新道具。（Gamigion/Playliner；HS-Playliner）
对照吸嘟嘟：关 1 纯 dust、关 3 才见 fur（老 id5「毛球初见面」落位新 id3）、关 2 巨毛球签名件实为「按住不放」预教——节奏面上接近此范式，但**无道具先例**（章首通赠道具挂关 5 结算后才到手，见 G10）。

**P9｜「游戏站在你这边」——慷慨感设计**
机制：Royal Match 被评「feels like it's been designed with players in mind…it wants you to win」「leans heavily on the side of the player」：道具慷慨、不强制用道具、智能道具转向、邮箱够量即关闭并提示——细节处处的「为你好」。数字判据：教学期资源给足（RM 道具威力按清除格数计为同类最大）；系统状态变化主动告知玩家（DoF）。
对照吸嘟嘟：治愈系文案基调已对齐此范式，但首关「系统为你做了什么」几乎不可见（无免费道具演示、无提示性辅助）。

**P10｜before/after 还原爽点=清洁品类核心多巴胺**
机制：Gardenscapes/Homescapes 的 meta=修复前后的可见反差；吸嘟嘟自家代码注释亦自认此范式（`RevealVeil.cs`：「PowerWash 式多巴胺，主流用户即懂」）。判据：过关瞬间必须有肉眼可辨的「变干净/变亮」前后对照，且「脏」的铺垫要足够强——反差越大爽感越大（Playrix 官方介绍 + 本项目代码注释互证）。
对照吸嘟嘟：灰幕 0.20 alpha 自称克制，截图判读「灰蒙蒙的脏感完全不存在」——反差的前半段缺位。

**P11｜留存诊断基准（给改造效果定标尺）**
机制：2026 移动游戏留存基准——行业中位 D1 ≈26%；「good」=D1/D7/D30 35/15/5；头部四分位 40/20/10；头部三消可高达 47/24/13。**低 D1 = 首会话问题**：诊断三个指标=FTUE 完成率、首会话时长、教学流失点。数字判据：新手改造的验收口径应取「关 1 完播率、首会话时长、教学流失点」三项埋点对照（Playio，单源但为 2026 年度基准数据）。

**P12｜复活/中断回归要有「准备时间」**
机制：微信官方设计指南明文：「闯关型游戏复活体验——玩家选择复活后应给予其充分准备时间及操作预判提醒」。数字判据：复活后 ≥1-2s 的重整窗（画面提示+可预判状态），而非即时恢复战斗。（微信指南）
对照吸嘟嘟：复活=+10s 直接回 Playing（`Bootstrap.OnReviveRequested`），无重整提示窗——好在 L1 不可失败，此项主要影响后续关。



## ③ 改造提案（15 条·按五组分类）

> 每条=具体改动+落点（文件/系统）+机器可验判据+预期效果。约束提醒：`ContentCatalog` 有「种子+规格表+域常量」可复现契约——样例关 BuildL1 为手写坐标、签名注入不消费 rng 流，改关 1 数据不破契约（`ContentCatalog.cs` 类头注释）；U315 时代「空战场」类 UI 盖屏 bug 已在 U316 修复，本节不重复立项。验收埋点面：`Game/TelemetryRelay.cs`（W10-GROWTH 全事件中继）+ `Tests/Editor/NewbieFlowCapture.cs`（新手流捕获测试既有面）。

### 甲、首分钟钩子（First-Minute Hook）

**T1｜「脏房亮相」开场演出**（对应 G1/G2 ← P3/P10）
- 改动：`LevelStarted` 后不再同帧瞬刷——17 件实体按「离嘟嘟出生点由近及远」错峰弹入（每件延迟 0-0.4s，复用既有出生弹入曲线），同时嘟嘟做一个 0.6s 的「环顾→瞪大眼」开场拍；到站横幅与弹入并行。演出期冻结计时（接 T2）。
- 落点：新 `LevelIntroSequencer`（Levels 模块，订阅 `LevelStarted`，驱动 `SuctionTarget` 出生延迟）或最小改法——`LevelRunner.SpawnAll` 内按 `Vector2.Distance(出生点, spawn)` 排序写入每件延迟字段；嘟嘟开场拍走 `ActorDudu` 反应协程同款模式。
- 机器可验判据：①PlayGate 断言 `LevelStarted` 后 0.6s 内 `ObjectRegistry` 中 17 件全部 active；②每件实际可见延迟与设计表误差 ≤1 帧；③演出总时长 ≤0.8s（不吞首按——教学 1.7s 淡入照旧先行可见）。
- 预期效果：首帧即见「乱」——清洁欲在 0.8s 内被点燃；对照 P11 指标看「首按延迟」埋点下降。

**T2｜计时器「首按启动」**（对应 G1/G11 ← P6/P9）
- 改动：关 1-5（引导段，`CurriculumOldId` 位 1-10 的 B4(R) 契约关）计时从玩家第一次按住才开始走；到站横幅+教学阅读期零压力。首按后计时正常。
- 落点：`Levels/LevelTimer.cs` 增 `WaitForFirstPress` 位（`LevelStarted` 只挂秒表臂不挂倒计时臂；`SuctionField` 首次 `_pressed=true` 时发 `FirstPressStarted` 事件，`LevelTimer` 收到后再挂 `_counting`）。关卡范围判定复用 `LevelRunner.CurrentLevelData.id ≤ 10`。
- 机器可验判据：①`TestLevelTimerRearm` 扩一测：关 1 不按压静置 10s → `Remaining==45.0f` 恒定；②首按后 `Remaining` 开始递减；③关 11+ 行为不变（回归）。
- 预期效果：消灭「读教学也在扣秒」的隐性焦虑，与「按下就有好事发生」的首关自述（`LevelCatalog.BuildL1` 注释）对齐。

**T3｜教学落位最爽点+首按全屋回应**（对应 G3 ← P3）
- 改动：①教学涟漪从屏幕中央（`AnchorCenter(0,-240)`）改到 B 簇簇心 (1.5,-2.9) 的屏幕投影位——教玩家的第一按按在「最密的一团」上；②首按达成（≥0.15s）的瞬间发 `FirstPressCelebrated`：全场 dust 向场心轻探 0.3u 的视觉涌动（纯 transform，0.3s 回弹）+嘟嘟鼓腮——「全屋回应你的第一下」。
- 落点：`UI/TutorialHint.cs`（涟漪锚点改 `FlyToTarget.WorldToCanvas` 同款投影）；首按涌动走新 `SuctionField` 冷路径广播 + `SuctionTarget` 一次性视觉偏移（不进 ApplySuction 主路径、零判定耦合）。
- 机器可验判据：①PlayMode 断言教学涟漪屏幕坐标与 B 簇投影坐标距离 ≤100px；②首按 0.3s 内可录得全场非零位移帧（SweepCapture 截帧比对）；③不吞按压红线维持（全层 raycastTarget=false 回归）。
- 预期效果：教学与爽点合一——第一按即大团吸入+全屋涌动双爽点，首分钟钩子完成度从「半成立」到成立（截图 03 判读原文：钩子被空场/错位削弱）。

### 乙、场景视觉铺陈（Dressing）

**T4｜灰幕章 1 档加强（0.20→0.34）**（对应 G6 ← P10）
- 改动：`VeilAlpha` 从全局常量 0.20 改为按章取值表：章 1-2 用 0.34、章 3-6 用 0.26、章 7+ 维持 0.20——「越前面的章，脏得越可见」，过关揭幕反差最大化。揭幕时长/泛光不动。
- 落点：`Game/RevealVeil.cs`（`ChapterArt.ChapterOf(levelId)` 现成纯函数可直接用；`LevelStarted` 事件已带 LevelId）。
- 机器可验判据：①PlayGate 截帧采样（SweepCapture）：关 1 蒙纱态画面平均饱和度较揭幕态低 ≥15%；②单元断言章 1 取 0.34f、章 7 取 0.20f；③HUD 文字可读性回归（AddLegibilityShadow 已有，验对比度不降级）。
- 预期效果：before/after 反差成立——「打扫完房间亮起来」的还原爽点有前半段铺垫（P10 双源验证的核心律）。

**T5｜簇-家具对位审计+「乱感」散落物补强**（对应 G7 ← P7 场景叙事）
- 改动：①对位审计——scene_room 实读有床（左上）、深窗台飘窗（顶部不可玩区）、圆形地毯+玩偶（中部）、书桌衣柜（右侧）；而 L1 三簇全部落在空旷地板带，叙事标签（「床边浮尘」「飘窗晨光尘」）与美术锚点未对位。按 scene_room 像素区换算重排 BuildL1 坐标，把 A 簇贴到床投影下沿、C 簇贴到左窗光斑落点、sock 移到床底阴影位。②乱感补强——scene_room 地板上已有美术散落物（毛线球/玩偶/玩具老鼠），在其正上方各叠 1 只 dust（视觉成组：「杂物+灰」），房间从「整洁样板间」变「住过的家」。
- 落点：①`Levels/LevelCatalog.cs` BuildL1 坐标重排（手写数据，不碰 rng 契约）；②`ContentCatalog.ApplySignatureInjections` 关 1 注入位或 BuildL1 直加 3 条 dust（BuildL1 属样例关、L1 即位序新 id1——注意 `SampleOptimalSec=16f` 与 45s 时限需同步 +2.4s 复核 ≥1.8×，实测 18.4/45≈2.4 倍仍达标，仅更新注释四难度数据）。
- 机器可验判据：①新工具测试：簇心世界坐标→scene 像素坐标换算后落在指定家具 bounding box 内（box 表写进测试常量）；②`TestLevels` 回归：坐标界内+goal 合法+roundtrip；③最优秒注释与实际 spawn 数一致。
- 预期效果：「晨光房间」叙事落地为画面事实；散落物+灰尘成组让「该打扫」一眼可读（截图 04 判读：像早安问候卡而非清扫关卡）。

**T6｜打扫进程可视化（越扫越亮）**（对应 G6/G8 ← P10）
- 改动：灰幕 alpha 随进度阶梯下降——已清 ≥50% 时降至当前值 ×0.6、≥85% 时降至 ×0.25（线性插值过渡，1s 缓动），过关全揭+泛光（现有）。
- 落点：`Game/RevealVeil.cs` 订阅 `ObjectCaptured`（或复用 `InGameHud` 已有 `_cleared/_total` 镜像转发进度事件，避免 Gameplay→Game 依赖，任选其一）。
- 机器可验判据：①断言清 9/17 时 veil alpha ∈ [0.20×0.34×0.6±公差]（与 T4 联动后章 1 值 0.34→0.20→0.09）；②清 15/17 时 ≤0.10；③过关帧 alpha==0（回归）。
- 预期效果：「进程感」中间反馈——玩家每抬头看一眼房间都能看到变亮（PowerWash 式多巴胺的自家注释兑现）。

### 丙、捕获-星星-庆祝果汁链（Juice Chain）

**T7｜簇级庆祝仪式（连扫一簇=小高潮）**（对应 G8 ← P8 teach→test→celebrate）
- 改动：检测「一个簇被吸空」→ 簇心金色星雨（`CaptureBurst` 复用 ×3 密度+Gold tint）+连击音阶上行一档+围观者 Happy 跳。16 件平铺捕获被切成 3 个节拍群。
- 落点：新 `ClusterMilestone` 组件（Gameplay，订阅 `ObjectCaptured`）；簇归属判定=构建时把簇心写进 `LevelData`（`BuildL1` 手写簇心数组；生成关可按 ContentCatalog 簇规格反推——首期只做关 1-5 样例/手写位即可验证价值）。
- 机器可验判据：①关 1 全通关埋点恰计 3 次簇级庆祝（A/B/C 各 1）；②每次庆祝视觉时长 ≤0.6s 且不阻塞输入（raycast 无新增）；③跨簇捕获不误触发（按距离 ≤1.5u 归簇）。
- 预期效果：正反馈从「每件等幅」升级为「件-簇-关」三级节奏；连扫一团的手感有句点。

**T8｜过关命名仪式「房间亮啦！」+剩余时间换星沙**（对应 G9 ← P4 Sugar Crush 律）
- 改动：①过关瞬间（胜局延迟窗内）叠 104px 显示字大字「房间亮啦！」+专属「亮啦」短音（`SfxFlow.PlayUiClip` 新增 sfx_win_shine 资产或合成回退）；②剩余秒数变现：每剩 1s=+1 星沙、封顶 +10，在结算 detail 行加「+N 时光奖励」——快扫有额外甜头，与 45s 宽限形成「早清多赚」正循环。
- 落点：①`UI/ResultScreen.cs` 胜局延迟窗（`CancelPendingWinShow` 既有窗口）或 `RevealVeil.Lift` 同帧；②`Game/MetaFlow.cs` `OnLevelCompleted`→`FlushSand` 前加 timeBonus 计算（`LevelTimer.Limit-Elapsed`，需 GoalTracker 结算事件带 Elapsed——已带）；文案落 `ResultScreen` detail 行。
- 机器可验判据：①「亮啦！」显示 ≥0.8s 且与揭幕泛光同帧起；②TestDoubleReward 扩测：剩 20s 过关→结算星沙=基础 21+时光奖 10；剩 3s→+3；③封顶断言 +10。
- 预期效果：过关从「静默跳结算」变命名仪式+收益惊喜；P4 判据（每次过关=1 命名仪式+剩余资源变现）完整对齐。

**T9｜袜子主角化三件套（发现时刻+逃跑拖尾+残局兜底）**（对应 G5 ← P5 角色反应律）
- 改动：①**发现时刻**——sock 首次进入吸力圈（`ObjectEscaped`/圈内登记沿）触发一次性「咦？！」演出：嘟嘟惊呆帧 0.35s+toast「找到床底的袜子啦！」（落档 `vh.tut.sock1`）；②**逃跑拖尾**——sock 逃窜时每 0.12s 落一枚小脚印淡出（`SuctionTrail.Emit` 直调，灰白色）——喜剧感可视；③**残局兜底**——当全场仅剩 sock 未清时，屏幕边缘金色箭头指向它+「就差袜子啦！」——首关找袜子零卡壳。
- 落点：①③新 `NewbieMomentLayer`（UI，订阅总线事件，模式同 TutorialHint）；②`SignatureTargets.SockTarget.ExtraForce` 逃窜分支内调 `SuctionTrail.Emit`。
- 机器可验判据：①关 1 sock 首次进圈 0.3s 内演出触发恰一次（重开复位）；②拖尾发射率 ≥8 粒/s（逃窜速度 >1u/s 时）；③仅剩 sock 时指向常驻直至捕获（PlayGate 断言）；④演出 raycastTarget=false 红线回归。
- 预期效果：把「全民找袜子梗」（`ContentCatalog` 关1 注释原话）从隐彩蛋升格为首关记忆点+名场面候选。

### 丁、节奏曲线（Rhythm）

**T10｜大招充能首关降档（嚏 12→8、伙伴 15→10）**（对应 G4 ← P8/P9）
- 改动：充能需求按关卡 id 分档——关 1-5：嚏 `NeededCaptures=8`、伙伴 `ChargeNeeded=10`；关 6+ 回 12/15。首关中段（清至 8/17≈47%）即满能，「嘟嘟满啦——按下去！」教学 toast 首次兑现点前移，玩家能在首关完整走一遍「蓄能→释放风暴（半径 ×2.5）」核心爽循环；17 件小盘+风暴=几乎全屏吸走的「名场面首秀」。
- 落点：`Gameplay/SneezeSystem.cs`（`NeededCaptures` const→按 `LevelRunner.Active.CurrentLevelData.id` 取档的静态函数）；`Core/Companions/CompanionProgress.cs` 同款（注意 `TestCompanionRoster` L182 键规约锁需同步改——判据进测试）。
- 机器可验判据：①关 1 清第 8 件时收到 `SneezeChargeChanged(Ready=true)`；关 6 第 12 件才 Ready（回归）；②埋点：首关嚏释放率（首关至少 1 次 TryStorm）≥60%；③风暴后 LevelCompleted 仍由 GoalTracker 正常结算（不因风暴提前达标而跳结算异常——全清关达标即结算，风暴吸走的照常计数）。
- 预期效果：首关即完成「大招教学-释放-爽爆」完整闭环——新手在 60 秒内见到游戏最大的爽点（对照 P7：头部游戏前 4 关必给一个「看得见的爽」）。

**T11｜里程碑节拍 25/50/75%**（对应 G8 ← P8）
- 改动：清至 4/17、9/17、13/17 三个阈值各触发一次轻量时刻——4 件：嘟嘟兴奋咀嚼拍（`_chomp=1.25` 触发位）+「真棒！」短音；9 件：灰幕半揭（接 T6 同拍）+围观者 Happy；13 件：嘟嘟鼓腮+「快好啦～」toast。三次时刻把 17 件切成 4 段（4/5/4/4），每段 ≤5 件。
- 落点：新 `ProgressBeats` 组件（UI 或 Gameplay，订阅 `ObjectCaptured`，阈值按 `TotalTargets` 百分比换算——只对全清关生效，goal 关不触发）；音效走 `SfxFlow.PlayUiClip` 既有通路。
- 机器可验判据：①每阈值恰触发一次（重开/复活复位）；②三次时刻与 T7 簇级庆祝互不吞拍（同帧去重：簇级优先，里程碑让 1 帧）；③全关新增非输入阻塞时长 ≤1.5s。
- 预期效果：16 件捕获的中段不再「平直」——每 4-5 件一个反馈升级，节奏曲线成型。

### 戊、教学流（Tutorial）

**T12｜嘟嘟演示首吸（实体化教学）**（对应 G3 ← P3/P5，长线项）
- 改动：首关教学两段式——①0.3s 起，嘟嘟自动走向 B 簇旁做一次「示范吸」：把 1 只 dust 拉向自己再弹回原位（纯视觉戏法，不真捕获、不计进度），配「吸——！」奶音；②「按住屏幕」大字与演示并行出现，玩家首按接管。备选重方案：额外 spawn 1 只不计目标的「教学 dust」真捕获走全反馈链（需动 `LevelRunner.TotalTargets` 口径，工程纠缠大，列为备选）。
- 落点：新 `TutorialDemo`（控制 `ActorDudu.SetTarget` 走位+对该 dust 做一次性 transform 插值）；与 `TutorialHint` 协同（大字照旧）。
- 机器可验判据：①演示全程 ≤1.2s；②演示件位置最终回弹误差 ≤0.05u、不计入 `ObjectCaptured`（注册表计数断言不变）；③演示期间玩家随时可按（教学层零阻塞红线）。
- 预期效果：「看见嘟嘟吸=学会」——微信官方「边玩边学，不要用大量文本」律的实体化。

**T13｜满能 toast 时序防御验证**（对应 G12 遗留面）
- 改动：U315 截图实据：0/17 时「嘟嘟满啦——按下去！」已可见（现役代码按沿触发理论上不该发生——疑似 U315 时序残留）。防御三件：①`SneezeSystem.Ensure()` 在 `LevelStarted` 处理器内先行（实例先建、充能必清）；②`TutorialHint` toast 增加双条件（`e.Ready && 本关已捕获 ≥ 当前档 NeededCaptures`）；③PlayGate 加断言锁死该时序。
- 落点：`Gameplay/SneezeSystem.cs` OnLevelStart；`UI/TutorialHint.cs` OnSneezeCharge；`Tests/PlayGate/PlayLoopDriver.cs` 新断言。
- 机器可验判据：新建档首进关 1，0 至 7 捕获期间 toast 绝不出现（PlayGate 录制断言）；8 捕获 Ready 后 toast 正常出现。
- 预期效果：消灭截图级时序错位观感——教学出现的每一秒都与真实状态一致。

### 己、新手激励与验收（跨幕）

**T14｜首胜见面礼（关 1 结算赠礼+菜单首次星沙跳涨）**（对应 G10 ← P7/P11）
- 改动：关 1 首次通关（`LevelId==1` 且未标 `vh.gift.l1`）→ 结算屏加「嘟嘟的见面礼 +30 星沙」金条幅 + 星沙飘字；菜单 `StardustChanged` 首次 +30 涨动（`NumberRoll.FloatUp` 既有通路）。首会话即完成「付出→可见成长」闭环，菜单从满屏 0 变成有第一笔资产。
- 落点：`Game/MetaFlow.cs` `OnLevelCompleted` 加关 1 首通档（`MetaStore.AddSand(30)`+标记，模式同章首通赠）；展示落 `UI/ResultScreen.cs` 金条幅（`ChapterChestScreen` 点亮位同款 Gold 样式）。
- 机器可验判据：①新档通关关 1 → `MetaStore.TotalSand ≥ 30+本关 21`；重复通关不重发（标记位）；②结算屏见面礼字样出现恰一次；③`TestDoubleReward`/`TestMetaStore` 回归不破。
- 预期效果：D1 首会话的「第一笔回报」成立——对照 P11（低 D1=首会话问题），把首会话时长与回访动机同时抬升。

**T15｜新手三指标埋点基线（改造验收的机器口径）**（对应 P11）
- 改动：把三项 FTUE 指标定为关 1 吸引力改造的验收基线并接入 `TelemetryRelay`：①**关 1 完播率**（LevelStarted→LevelCompleted 转化）；②**首按延迟**（LevelStarted→首次 `SuctionField._pressed` 的秒数，T2/T3 的直接量尺）；③**教学流失点**（vh.tut.press 未落档且退出的会话占比）。上线前先跑基线、改造后对照。
- 落点：`Game/TelemetryRelay.cs`（既有全事件中继，加首按时刻打点）；指标口径写进 `Tests/Editor/NewbieFlowCapture.cs` 旁注文档位。
- 机器可验判据：微信侧后台（branch-analytics 通道）可按日拉取三指标；本仓库 PlayGate 断言三项事件必上报。
- 预期效果：给本报告全部提案定标尺——没有基线就没有「吸引力提升」的证明（P11 原文：低 D1 → check FTUE completion, first-session length, tutorial drop-off）。

## ④ 优先级

**P0（首关吸引力主诉·纯程序侧可落地·判据全部可机验）——建议本冲刺执行**

| 提案 | 一句话理由 |
|---|---|
| T1 脏房亮相 | 首帧即「乱」——清洁欲是本品类唯一引擎（P10 双源） |
| T2 首按计时 | 消灭教学期扣秒的隐性焦虑，零成本高体感 |
| T3 教学落位最爽点 | 第一按=大团吸入+全屋回应，首分钟钩子闭环 |
| T4 灰幕章 1 加强 | before/after 反差的前半段，改一个常量+一张表 |
| T7 簇级庆祝 | 16 件平铺→3 个节拍群，反馈密度的结构性修复 |
| T10 大招首关降档 | 首关 60 秒内必须见到游戏最大的爽点（嚏风暴全屏吸） |

**P1（次优先·含少量美术/数据配合）**

| 提案 | 一句话理由 |
|---|---|
| T6 进程可视化 | 「越扫越亮」中间反馈，与 T4 联动放大 |
| T8 过关仪式+时光奖 | Sugar Crush 律落地：过关有名、余量有奖 |
| T11 里程碑节拍 | 25/50/75% 三拍，中段不平直 |
| T9 袜子三件套 | 首关唯一活物升格为记忆点（找袜子梗兑现） |
| T5 对位+乱感 | 叙事落地+房间「住过感」（坐标重排+贴簇） |
| T14 首胜见面礼 | 首会话回报闭环，菜单满屏 0 的修复 |
| T15 三指标基线 | 一切改造的验收标尺，先行埋点 |

**P2（长线/防御·工程纠缠大或待验证）**

| 提案 | 一句话理由 |
|---|---|
| T12 嘟嘟演示首吸 | 「边玩边学」实体化，需动教学编排工程，待 P0 见效后评估 |
| T13 toast 时序防御 | 现役代码推演正常，属防御+回归锁，随测试批收口 |

**执行顺序建议**：T15（埋点先行）→ T4/T2/T3（常量与小改快热身）→ T1/T7/T10（三个结构性爽点）→ P1 批次。全程以 T15 基线对照 P11 口径（关 1 完播率/首按延迟/教学流失点）验收。

**未能核实项（诚实披露）**：①U315 截图中「0/17 时满能 toast 已现」的确切成因（推断为该版时序残留，现役代码推演不发生，留 T13 断言锁死）；②scene_room 各家具的精确世界坐标 bounding box（需运行时打印 SceneBounds+像素换算工具化，本报告以多模态读图的相对位置为准）；③Royal Match 关 1 是否有强制首动手型教学的原始截图级证据（ gameplay 视频可见手型引导，但未能取到官方设计文档级来源——以微信官方指南「边玩边学」与 CC 赞叹词体系为双源替代）。
