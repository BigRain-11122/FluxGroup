# 吸嘟嘟游戏软件 V1.0 软件设计说明书

> 编写：吸嘟嘟项目组　｜　版本：V1.0　｜　对应构建：V0.10.20　｜　最后更新：2026-11-23

## 1 项目背景

吸嘟嘟是一款竖屏休闲收集游戏，2026 年 9 月 13 日提交第一版工程，到今天（11 月 23 日）累计 848 次代码提交、分布在 39 个工作日里。立项时的判断很直接：市面上的收集类游戏大多把"爽"做成了数值成长，我们想做一个只靠手感和节奏的版本——玩家按住屏幕，产生一个圆形吸力场，把房间里的灰尘、毛球、碎屑吸进嘟嘟的肚子里。

嘟嘟是一台有生命的吸尘器。它会打喷嚏、会吃饱、会在看到脏东西时兴奋。这些不是装饰，它们是"吸到了"这件事的反馈：吸到一个东西，屏幕上要有粒子、有音效、有 HUD 数字跳动，玩家要在 0.2 秒内知道"我刚才那一下是对的"。

本文档描述这个软件的完整设计：玩法规格、系统架构、关键模块、开发过程中真实遇到过的问题与改法，以及实机截图。它同时作为软件著作权登记的说明书材料。

## 2 需求与范围

### 2.1 核心玩法

一句话：**按住屏幕产生吸力场，把目标吸进来；吸够目标数过关。**

- 单局 60–90 秒，一次会话 5–15 分钟，没有失败态。
- 目标是"吸得准、吸得爽"，不是"数值变强"。
- 章节推进给新场景、新目标族、新伙伴；元系统（签到、图鉴、伙伴、日常、离线、商店）围绕核心循环，不做脱离玩法的独立养成线。

### 2.2 明确不做的范围

| 不做 | 原因 |
|---|---|
| 多人联机、排行榜 | 家庭向产品，避免社交压力与合规成本 |
| 真实付费、抽卡 | 全程纯 IAA，核心进度不依赖广告 |
| 真人语音、写实人脸 | 家庭安全线，避免肖像权与适龄风险 |
| 复杂剧情分支 | 竖屏单手操作，剧情只做碎片化 |

## 3 核心玩法与数值

### 3.1 吸力场参数

吸力场是手感核心。当前版本的实际配置（`SuctionFieldConfig.cs`）：

| 参数 | 值 | 说明 |
|---|---:|---|
| `radius` | 2.2 | 吸力场半径（世界单位） |
| `baseStrength` | 12 | 基础吸力强度 |
| `followLerp` | 0.35 | 场心跟随指针的插值系数 |
| `maxParallelCaptures` | 3 | 同帧最多并行捕获的目标数 |

`maxParallelCaptures = 3` 是刻意压低的。如果整簇目标同时攒进度，玩家按住不动就能一次清屏，"逐件吸"的节奏就没了；限制并行数是让"按住—移动—收"这个循环保持张力。

### 3.2 每帧两阶段

1. **登记阶段**：倒序扫目标注册表，把吸力场圈内的目标全量登记进"本帧在圈内"集合，同时选出距场心最近的 K 件。
2. **施加阶段**：只对最近 K 件调用 `ApplySuction`，进度到阈值当场捕获并发 `ObjectCaptured` 事件；上一帧在圈内、本帧出圈的目标发 `ObjectEscaped`，用预分配的字典记录上一帧状态，避免每帧分配。

### 3.3 目标族

灰尘、毛球、碎屑三类，按重量区分吸收速度：灰尘一吸就走，碎屑要追，毛球会滚。目标族的差异体现在 `ApplySuction` 的阻力系数上，不在数值面板上。

## 4 系统架构

代码按 9 个命名空间分层，依赖方向单向：

```
GimmeAll.Core       事件总线、状态机、对象池、服务注册、关卡数据
GimmeAll.Gameplay   吸力场、主角嘟嘟、目标族、喷嚏、捕获特效
GimmeAll.Levels     章节剧情、关卡目录、规则、计时、进度存储
GimmeAll.Game       引导流程、签到、图鉴、伙伴、日常、离线、商店
GimmeAll.Ads        广告位管理、频次门控、metrics
GimmeAll.Audio      分层混音、环境循环
GimmeAll.UI         HUD、弹窗、图鉴页、商店页
GimmeAll.Social     分享、截图、回放
GimmeAll.Replay     操作录制与回放
```

规则只有一条：**跨模块只通过事件总线、注册表或 Core 里的服务接口通信，不直接引用别的模块的类型。** 这样加新玩法只在对应层动，不会牵一发动全身。

## 5 关键模块设计

### 5.1 吸附场 SuctionField

场心跟随用帧率无关的 lerp：`pos = Lerp(pos, target, 1 - Pow(1 - followLerp, dt * 60))`。直接 `Lerp(pos, target, 0.35)` 在 30fps 和 120fps 下手感差一倍，这是我们早期踩过的坑（见 6.1）。

### 5.2 捕获与逃脱

捕获判定用"进度阈值"而不是"距离阈值"：目标在圈内每帧累加进度，满了才捕获。这样玩家有"追"的空间——毛球会滚，得预判。逃脱判定依赖上一帧的圈内集合，用字典存，每帧只增删变化项。

### 5.3 对象池

灰尘、粒子、飘字全部走对象池。竖屏低端机（4GB 内存）上，运行时 GC 峰值会直接掉帧，池化后单局 GC 分配控制在 0。

### 5.4 关卡目录与章节

关卡数据与表现分离：`LevelCatalog` 提供关卡 id、目标数、时限、可用目标族；场景只负责摆位。加关卡不改代码，只加数据。

### 5.5 存档

存档采用"写临时文件 + 原子替换"，中断后回退到上一份可用存档。家庭向产品里，"孩子玩到一半被叫走"是高频场景，丢进度比崩溃更伤。

### 5.6 HUD 与车机适配

手机版 HUD 在顶部；车机版是 4:3 横向，如果沿用竖屏柱缩放（0.5625），信息带会被压成一条。我们把顶部信息带整体移到左翼（`InGameHud.AttachInfoBandToCarWing`），并加了 204 条断言防止回退。

### 5.7 广告位门控

纯 IAA 产品最怕"广告打断玩法"。当前实现：前 5 关不插广告、插屏冷却 ≥180 秒、每日 ≤12 次、核心玩法进行中不插、不得诱导点击。门控逻辑在 `Ads` 层，玩法层不知道广告存在。

## 6 开发过程中真实遇到的问题

这一节记录我们实际返工过的地方。它们能说明这个软件是怎么一步步变成现在这样的。

### 6.1 低帧率下吸附迟滞

第一次内测（9 月 20 日）时，测试机 40fps 下吸力场明显"跟不上手"，120fps 机器上正常。原因是场心插值直接用了固定系数，帧率越低每帧补得越少。改成帧率无关形式后，40fps 与 120fps 的手感一致。这个问题让我们定了一条规矩：**所有跟手相关的插值必须带 `dt`。**

### 6.2 车机版信息带被压扁

车机版最初直接复用竖屏 HUD，按 0.5625 缩放进 4:3 画面，结果顶部信息带只剩一条细线，看不清"今日任务 0/3"。改成左翼竖排后解决。为了不再回退，加了 `car_hud_wing_check` 断言（204 条）。

### 6.3 4K 母版与裁切件对不上

商店物料需要 16:9 与 4:3 两种裁切。早期两张图各自生成，导致"同一张画"其实是两张不同的图。后来改成：先出 1:1 母版（3840×3840），16:9 与 4:3 都从母版中心裁切，再用同框比对（逐像素）验证。现在 `family_4k_accept_check` 会同时校验尺寸、构图和边缘。

### 6.4 离线奖励弹窗挡住主按钮

"欢迎回来，+6 星沙"弹窗最初盖住了底部"同吸"按钮，玩家点不到。改成弹窗内提供"收下"与"看视频翻倍"两个明确动作，关闭后回到主界面，不依赖点空白处。截图见 10.2。

## 7 性能与适配

| 项 | 目标 | 说明 |
|---|---|---|
| 帧率 | 60fps（手机） / 30fps（车机 8155） | 低端机优先保 30 |
| 纹理 | 非背景资产 ≤1024 | 显存预算约 15.5MB |
| GC | 单局 0 分配 | 对象池 + 预分配字典 |
| 启动 | 首屏 ≤3 秒 | 资源分包加载 |

## 8 构建与发布

- 当前构建：V0.10.20（Win64 调试包与 Android APK，APK 132.9MB）。
- 构建流程：团结引擎命令行构建 → 冒烟 → 门禁 G1–G4 巡检 → 出包。
- 发布渠道：Android 应用商店（国内），车机版单独出包。

## 9 测试

- 用例 119 条，覆盖核心循环、存档、广告门控、车机适配。
- 门禁 G1 可玩、G2 亲子切片、G3 发布候选、G4 发布，每道门有独立的就绪检查脚本。
- 负面控制：每个门禁都有一条"故意写坏必须红"的用例，防止闸失效。

## 10 实机截图

以下截图取自 V0.10.20 Windows 构建，1920×1080 竖屏窗口（客户区 540×960 缩放），2026-11-23 实拍。

### 10.1 启动与健康游戏忠告

![启动页](shots-20261123/01_splash.png)

启动页包含游戏名、健康游戏忠告与适龄提示（8+），符合国内上架要求。

### 10.2 离线奖励

![离线奖励](shots-20261123/04_level.png)

离开 50 分钟后回到游戏，弹出"+6 星沙"离线奖励，提供"收下"与"看视频翻倍"两个动作；顶部可见今日任务 0/3、旅程第 1 章·宝箱 0/5、星沙 0。

### 10.3 关卡内

![关卡](shots-20261123/05_suction.png)

进入关卡后按住屏幕，吸力场展开，目标被吸入。

### 10.4 扫吸

![扫吸](shots-20261123/06_sweep.png)

横向拖动，连续吸取多个目标。

## 附录 A 源文件清单

见附录 A 表格（由构建脚本从工程生成，共 432 个 C# 文件）。

## 附录 B 命名空间与类型索引

见附录 B 表格。

## 附录 A 源文件清单

本软件共 448 个 C# 源文件，按工程路径排列。

| # | 文件 |
|---:|---|
| 1 | .codely-cli/mod/mm-committed.cs |
| 2 | .codely-cli/mod/MOD-12-orig-MetaStore.cs |
| 3 | Assets/_Project/Ads/AdConfig.cs |
| 4 | Assets/_Project/Ads/AdsSelfTest.cs |
| 5 | Assets/_Project/Ads/RewardCatalog.cs |
| 6 | Assets/_Project/Ads/StubAdRunner.cs |
| 7 | Assets/_Project/Ads/StubAdService.cs |
| 8 | Assets/_Project/Ads/WeChatAdBootstrap.cs |
| 9 | Assets/_Project/Ads/WeChatAdService.cs |
| 10 | Assets/_Project/Audio/AudioSelfTest.cs |
| 11 | Assets/_Project/Audio/BgmBus.cs |
| 12 | Assets/_Project/Audio/SfxBus.cs |
| 13 | Assets/_Project/Audio/SfxFlow.cs |
| 14 | Assets/_Project/Audio/SfxSynth.Base.cs |
| 15 | Assets/_Project/Audio/SfxSynth.cs |
| 16 | Assets/_Project/Audio/SfxSynth.Families.cs |
| 17 | Assets/_Project/Audio/SfxSynth.Signature.cs |
| 18 | Assets/_Project/Car/CarCabinBridge.cs |
| 19 | Assets/_Project/Car/CarCabinMock.cs |
| 20 | Assets/_Project/Core/AdCopy.cs |
| 21 | Assets/_Project/Core/AdFrequencyGate.cs |
| 22 | Assets/_Project/Core/AdServiceSeam.cs |
| 23 | Assets/_Project/Core/AdsPolicy.cs |
| 24 | Assets/_Project/Core/CaptureBeat.cs |
| 25 | Assets/_Project/Core/ComboTracker.cs |
| 26 | Assets/_Project/Core/Companions/CompanionDef.cs |
| 27 | Assets/_Project/Core/Companions/CompanionProgress.cs |
| 28 | Assets/_Project/Core/Companions/CompanionRuntime.cs |
| 29 | Assets/_Project/Core/Events/AdMetrics.cs |
| 30 | Assets/_Project/Core/Events/AdsEvents.cs |
| 31 | Assets/_Project/Core/Events/AudioEvents.cs |
| 32 | Assets/_Project/Core/Events/LevelEvents.cs |
| 33 | Assets/_Project/Core/Events/MetaEvents.cs |
| 34 | Assets/_Project/Core/Events/ProfileEvents.cs |
| 35 | Assets/_Project/Core/Events/UIEvents.cs |
| 36 | Assets/_Project/Core/GameEventBus.cs |
| 37 | Assets/_Project/Core/GameEvents.cs |
| 38 | Assets/_Project/Core/GameStateMachine.cs |
| 39 | Assets/_Project/Core/IAnalyticsService.cs |
| 40 | Assets/_Project/Core/ICanvasBoard.cs |
| 41 | Assets/_Project/Core/ICarCabinSignalSource.cs |
| 42 | Assets/_Project/Core/IMetaService.cs |
| 43 | Assets/_Project/Core/InterstitialPolicy.cs |
| 44 | Assets/_Project/Core/IRecordable.cs |
| 45 | Assets/_Project/Core/IServices.cs |
| 46 | Assets/_Project/Core/ISuctionable.cs |
| 47 | Assets/_Project/Core/ISuctionGuide.cs |
| 48 | Assets/_Project/Core/LevelData.cs |
| 49 | Assets/_Project/Core/ObjectPool.cs |
| 50 | Assets/_Project/Core/ObjectRegistry.cs |
| 51 | Assets/_Project/Core/PlaceholderSpriteFactory.cs |
| 52 | Assets/_Project/Core/PrefsFlush.cs |
| 53 | Assets/_Project/Core/ProfileClaim.cs |
| 54 | Assets/_Project/Core/ProfileDelete.cs |
| 55 | Assets/_Project/Core/ProfileReloadContract.cs |
| 56 | Assets/_Project/Core/ProfileRosterContract.cs |
| 57 | Assets/_Project/Core/ProfileScope.cs |
| 58 | Assets/_Project/Core/ProfileSwitch.cs |
| 59 | Assets/_Project/Core/ServiceRegistry.cs |
| 60 | Assets/_Project/Core/SpawnRegistry.cs |
| 61 | Assets/_Project/Core/SystemUnlockGate.cs |
| 62 | Assets/_Project/Editor/BuildAndroid.cs |
| 63 | Assets/_Project/Game/AmbientLoopLayer.cs |
| 64 | Assets/_Project/Game/AutoPilotMenuStart.cs |
| 65 | Assets/_Project/Game/AutoPilotStationAdvance.cs |
| 66 | Assets/_Project/Game/BackdropBoard.cs |
| 67 | Assets/_Project/Game/Bootstrap.cs |
| 68 | Assets/_Project/Game/CameraRig.cs |
| 69 | Assets/_Project/Game/CarAppLifecycle.cs |
| 70 | Assets/_Project/Game/ChapterArt.cs |
| 71 | Assets/_Project/Game/ChapterChestFlow.cs |
| 72 | Assets/_Project/Game/CheckInFlow.cs |
| 73 | Assets/_Project/Game/CodexAccelFlow.cs |
| 74 | Assets/_Project/Game/CodexFlow.cs |
| 75 | Assets/_Project/Game/ComboChoiceFlow.cs |
| 76 | Assets/_Project/Game/CompanionAdFlow.cs |
| 77 | Assets/_Project/Game/CompanionCoordinator.cs |
| 78 | Assets/_Project/Game/CompanionRosterFlow.cs |
| 79 | Assets/_Project/Game/CompanionSeatFlow.cs |
| 80 | Assets/_Project/Game/CompanionUpgradeFlow.cs |
| 81 | Assets/_Project/Game/DailyTaskFlow.cs |
| 82 | Assets/_Project/Game/DevLevelBoot.cs |
| 83 | Assets/_Project/Game/DuelRope.cs |
| 84 | Assets/_Project/Game/Editor/ArtImportRules.cs |
| 85 | Assets/_Project/Game/Editor/AudioPackageMatrix.cs |
| 86 | Assets/_Project/Game/Editor/NewbieRunSetup.cs |
| 87 | Assets/_Project/Game/Editor/O1610BorderBake.cs |
| 88 | Assets/_Project/Game/Editor/ProjectBuild.cs |
| 89 | Assets/_Project/Game/Editor/StoreAssetGen.cs |
| 90 | Assets/_Project/Game/FeelPulse.cs |
| 91 | Assets/_Project/Game/FileAnalyticsService.cs |
| 92 | Assets/_Project/Game/HapticPulse.cs |
| 93 | Assets/_Project/Game/HapticsRelay.cs |
| 94 | Assets/_Project/Game/HiddenTreasureFlow.cs |
| 95 | Assets/_Project/Game/InLevelChoiceFlow.cs |
| 96 | Assets/_Project/Game/LevelSupplyFlow.cs |
| 97 | Assets/_Project/Game/Meta/MetaService.Companion.cs |
| 98 | Assets/_Project/Game/Meta/MetaService.Daily.cs |
| 99 | Assets/_Project/Game/Meta/MetaService.Offline.cs |
| 100 | Assets/_Project/Game/Meta/MetaService.Profile.cs |
| 101 | Assets/_Project/Game/Meta/MetaService.Sand.cs |
| 102 | Assets/_Project/Game/Meta/MetaService.Supply.cs |
| 103 | Assets/_Project/Game/Meta/MetaService.TestKeys.cs |
| 104 | Assets/_Project/Game/MetaFlow.cs |
| 105 | Assets/_Project/Game/MetaService.cs |
| 106 | Assets/_Project/Game/MetaStore.cs |
| 107 | Assets/_Project/Game/OfflineEarningsFlow.cs |
| 108 | Assets/_Project/Game/PadLevelSwitch.cs |
| 109 | Assets/_Project/Game/PreLevelChoiceFlow.cs |
| 110 | Assets/_Project/Game/ProfileReload.cs |
| 111 | Assets/_Project/Game/ProfileRoster.cs |
| 112 | Assets/_Project/Game/QuitTrace.cs |
| 113 | Assets/_Project/Game/RevealVeil.cs |
| 114 | Assets/_Project/Game/ScreenshotKey.cs |
| 115 | Assets/_Project/Game/ShareLandingGate.cs |
| 116 | Assets/_Project/Game/StationArt.cs |
| 117 | Assets/_Project/Game/StoreAdFlow.cs |
| 118 | Assets/_Project/Game/StoreFlow.cs |
| 119 | Assets/_Project/Game/TelemetryRelay.cs |
| 120 | Assets/_Project/Game/UnlockFlow.cs |
| 121 | Assets/_Project/Game/WeChatAnalyticsService.cs |
| 122 | Assets/_Project/Gameplay/ActorDudu.cs |
| 123 | Assets/_Project/Gameplay/AmbushBeat.cs |
| 124 | Assets/_Project/Gameplay/Art/GameplayArt.cs |
| 125 | Assets/_Project/Gameplay/BellyWindow.cs |
| 126 | Assets/_Project/Gameplay/BinZone.cs |
| 127 | Assets/_Project/Gameplay/CaptureBurst.cs |
| 128 | Assets/_Project/Gameplay/CarryMouth.cs |
| 129 | Assets/_Project/Gameplay/ChapterEvolveFlow.cs |
| 130 | Assets/_Project/Gameplay/ChapterFinale.cs |
| 131 | Assets/_Project/Gameplay/ChapterOnlooker.cs |
| 132 | Assets/_Project/Gameplay/ChapterOnlookerSelfTest.cs |
| 133 | Assets/_Project/Gameplay/ClusterMilestone.cs |
| 134 | Assets/_Project/Gameplay/DebrisTarget.cs |
| 135 | Assets/_Project/Gameplay/DustTarget.cs |
| 136 | Assets/_Project/Gameplay/EscapeBrake.cs |
| 137 | Assets/_Project/Gameplay/Families/BubbleTarget.cs |
| 138 | Assets/_Project/Gameplay/Families/GhostTarget.cs |
| 139 | Assets/_Project/Gameplay/Families/HeavyTarget.cs |
| 140 | Assets/_Project/Gameplay/Families/MimicTarget.cs |
| 141 | Assets/_Project/Gameplay/Families/PlayBand.cs |
| 142 | Assets/_Project/Gameplay/Families/SparkleTarget.cs |
| 143 | Assets/_Project/Gameplay/Families/SplitterTarget.cs |
| 144 | Assets/_Project/Gameplay/Families/StickyTarget.cs |
| 145 | Assets/_Project/Gameplay/Families/SwarmTarget.cs |
| 146 | Assets/_Project/Gameplay/Front3Fx.cs |
| 147 | Assets/_Project/Gameplay/Front3SuctionGrowth.cs |
| 148 | Assets/_Project/Gameplay/FullChargeCeremony.cs |
| 149 | Assets/_Project/Gameplay/FurTarget.cs |
| 150 | Assets/_Project/Gameplay/GameplayDirtPalette.cs |
| 151 | Assets/_Project/Gameplay/GameplayEscape.cs |
| 152 | Assets/_Project/Gameplay/GameplaySelfTest.cs |
| 153 | Assets/_Project/Gameplay/GameplaySpawnFactory.cs |
| 154 | Assets/_Project/Gameplay/GrayscaleDriver.cs |
| 155 | Assets/_Project/Gameplay/GroundShadow.cs |
| 156 | Assets/_Project/Gameplay/GuideRing.cs |
| 157 | Assets/_Project/Gameplay/HitStop.cs |
| 158 | Assets/_Project/Gameplay/JuiceCurves.cs |
| 159 | Assets/_Project/Gameplay/LandmarkBeacon.cs |
| 160 | Assets/_Project/Gameplay/LevelScope.cs |
| 161 | Assets/_Project/Gameplay/PadInput.cs |
| 162 | Assets/_Project/Gameplay/PointVacuum.cs |
| 163 | Assets/_Project/Gameplay/ScratchTargets.cs |
| 164 | Assets/_Project/Gameplay/ScriptedPointer.cs |
| 165 | Assets/_Project/Gameplay/ScriptedSuctionPilot.cs |
| 166 | Assets/_Project/Gameplay/SignatureArt.cs |
| 167 | Assets/_Project/Gameplay/SignatureTargets.cs |
| 168 | Assets/_Project/Gameplay/SneezeSystem.cs |
| 169 | Assets/_Project/Gameplay/SpawnSpecTable.cs |
| 170 | Assets/_Project/Gameplay/SuctionField.cs |
| 171 | Assets/_Project/Gameplay/SuctionField.Visual.cs |
| 172 | Assets/_Project/Gameplay/SuctionFieldConfig.cs |
| 173 | Assets/_Project/Gameplay/SuctionGuideWiring.cs |
| 174 | Assets/_Project/Gameplay/SuctionTarget.cs |
| 175 | Assets/_Project/Gameplay/SuctionTrail.cs |
| 176 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch07.cs |
| 177 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch08.cs |
| 178 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch09.cs |
| 179 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch10.cs |
| 180 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch11.cs |
| 181 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch12.cs |
| 182 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch13.cs |
| 183 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch14.cs |
| 184 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch15.cs |
| 185 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch16.cs |
| 186 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch17.cs |
| 187 | Assets/_Project/Levels/Campaign/CampaignCatalog.Ch18.cs |
| 188 | Assets/_Project/Levels/Campaign/CampaignCatalog.cs |
| 189 | Assets/_Project/Levels/Campaign/CampaignCatalog.Id04_12.cs |
| 190 | Assets/_Project/Levels/Campaign/CampaignCatalog.Id13_21.cs |
| 191 | Assets/_Project/Levels/Campaign/CampaignCatalog.Id22_30.cs |
| 192 | Assets/_Project/Levels/ChapterLore.cs |
| 193 | Assets/_Project/Levels/ContentCatalog.cs |
| 194 | Assets/_Project/Levels/DailyLevelPolicy.cs |
| 195 | Assets/_Project/Levels/Editor/ContentCatalogEditor.cs |
| 196 | Assets/_Project/Levels/Editor/LevelEditorWindow.cs |
| 197 | Assets/_Project/Levels/Generation/BeatInjection.cs |
| 198 | Assets/_Project/Levels/Generation/LevelGenerator.cs |
| 199 | Assets/_Project/Levels/Generation/SignatureInjection.cs |
| 200 | Assets/_Project/Levels/Generation/VarietyInjection.cs |
| 201 | Assets/_Project/Levels/GoalTracker.cs |
| 202 | Assets/_Project/Levels/LevelCatalog.cs |
| 203 | Assets/_Project/Levels/LevelDiag.cs |
| 204 | Assets/_Project/Levels/LevelProgressStore.cs |
| 205 | Assets/_Project/Levels/LevelRules.cs |
| 206 | Assets/_Project/Levels/LevelRunner.cs |
| 207 | Assets/_Project/Levels/LevelSourceResolver.cs |
| 208 | Assets/_Project/Levels/LevelsSelfTest.cs |
| 209 | Assets/_Project/Levels/LevelTimer.cs |
| 210 | Assets/_Project/Levels/ParentKeyGuide.cs |
| 211 | Assets/_Project/Levels/RemainderGuide.cs |
| 212 | Assets/_Project/Levels/Stations/StationAbLayout.cs |
| 213 | Assets/_Project/Levels/Stations/StationCatalog_Station1.cs |
| 214 | Assets/_Project/Levels/Stations/StationCatalog_StationA.cs |
| 215 | Assets/_Project/Levels/Stations/StationCatalog_StationB.cs |
| 216 | Assets/_Project/Levels/Stations/StationCatalog_StationC.cs |
| 217 | Assets/_Project/Levels/Stations/StationCatalog_StationD.cs |
| 218 | Assets/_Project/Levels/Stations/StationCatalog_StationE.cs |
| 219 | Assets/_Project/Levels/Stations/StationCatalog_StationF.cs |
| 220 | Assets/_Project/Levels/Validation/LevelReport.cs |
| 221 | Assets/_Project/Levels/Validation/LevelValidator.cs |
| 222 | Assets/_Project/Levels/WaveDirector.cs |
| 223 | Assets/_Project/Replay/GhostPlayback.cs |
| 224 | Assets/_Project/Replay/PostcardComposer.cs |
| 225 | Assets/_Project/Replay/PosterComposer.cs |
| 226 | Assets/_Project/Replay/ReplayConfig.cs |
| 227 | Assets/_Project/Replay/ReplayRecorder.cs |
| 228 | Assets/_Project/Replay/ReplayRingMath.cs |
| 229 | Assets/_Project/Replay/ReplaySelfTest.cs |
| 230 | Assets/_Project/Replay/ReplayShareService.cs |
| 231 | Assets/_Project/Replay/WanderDot.cs |
| 232 | Assets/_Project/Replay/WeChatShareService.cs |
| 233 | Assets/_Project/Social/ArenaAnchor.cs |
| 234 | Assets/_Project/Social/CloudScoreParser.cs |
| 235 | Assets/_Project/Social/PersistentLeaderboardService.cs |
| 236 | Assets/_Project/Social/ScoreFlow.cs |
| 237 | Assets/_Project/Social/SocialSelfTest.cs |
| 238 | Assets/_Project/Social/StubLeaderboardService.cs |
| 239 | Assets/_Project/Social/TimeService.cs |
| 240 | Assets/_Project/Social/WeChatLeaderboardService.cs |
| 241 | Assets/_Project/Tests/Editor/BVersionSevenShot.cs |
| 242 | Assets/_Project/Tests/Editor/ChapterTurnCapture.cs |
| 243 | Assets/_Project/Tests/Editor/DevRigToggles.cs |
| 244 | Assets/_Project/Tests/Editor/DuduIdleShot.cs |
| 245 | Assets/_Project/Tests/Editor/EditModeSpawnDrive.cs |
| 246 | Assets/_Project/Tests/Editor/EntityProbeGate.cs |
| 247 | Assets/_Project/Tests/Editor/FxGate.cs |
| 248 | Assets/_Project/Tests/Editor/HeadlessRunner.cs |
| 249 | Assets/_Project/Tests/Editor/HeadlessTestAttribute.cs |
| 250 | Assets/_Project/Tests/Editor/NewbieFlowCapture.cs |
| 251 | Assets/_Project/Tests/Editor/O1610MenuShot.cs |
| 252 | Assets/_Project/Tests/Editor/PlayLoopGate.cs |
| 253 | Assets/_Project/Tests/Editor/SettlementCapture.cs |
| 254 | Assets/_Project/Tests/Editor/SweepCapture.cs |
| 255 | Assets/_Project/Tests/Editor/TestAdCopyFamilyFace.cs |
| 256 | Assets/_Project/Tests/Editor/TestAdPolicyFaceVisible.cs |
| 257 | Assets/_Project/Tests/Editor/TestAds.cs |
| 258 | Assets/_Project/Tests/Editor/TestAdsMetrics.cs |
| 259 | Assets/_Project/Tests/Editor/TestArtAssets.cs |
| 260 | Assets/_Project/Tests/Editor/TestAudioAssets.cs |
| 261 | Assets/_Project/Tests/Editor/TestAudioPackageMatrix.cs |
| 262 | Assets/_Project/Tests/Editor/TestBellyMath.cs |
| 263 | Assets/_Project/Tests/Editor/TestBVersionChapterJourney.cs |
| 264 | Assets/_Project/Tests/Editor/TestBVersionEntries.cs |
| 265 | Assets/_Project/Tests/Editor/TestBVersionPortMap.cs |
| 266 | Assets/_Project/Tests/Editor/TestBVersionStoreScreen.cs |
| 267 | Assets/_Project/Tests/Editor/TestChainIntegration.cs |
| 268 | Assets/_Project/Tests/Editor/TestChapterChest.cs |
| 269 | Assets/_Project/Tests/Editor/TestChapterChestUi.cs |
| 270 | Assets/_Project/Tests/Editor/TestChapterEvolveFlow.cs |
| 271 | Assets/_Project/Tests/Editor/TestCheckIn.cs |
| 272 | Assets/_Project/Tests/Editor/TestCheckInUi.cs |
| 273 | Assets/_Project/Tests/Editor/TestCodexAccel.cs |
| 274 | Assets/_Project/Tests/Editor/TestCodexAccelUi.cs |
| 275 | Assets/_Project/Tests/Editor/TestCodexCatalog.cs |
| 276 | Assets/_Project/Tests/Editor/TestCodexFlow.cs |
| 277 | Assets/_Project/Tests/Editor/TestCodexUi.cs |
| 278 | Assets/_Project/Tests/Editor/TestCompanionAds.cs |
| 279 | Assets/_Project/Tests/Editor/TestCompanionFace.cs |
| 280 | Assets/_Project/Tests/Editor/TestCompanionFamilies2.cs |
| 281 | Assets/_Project/Tests/Editor/TestCompanionQi2b.cs |
| 282 | Assets/_Project/Tests/Editor/TestCompanionRoster.cs |
| 283 | Assets/_Project/Tests/Editor/TestCompanionRosterUi.cs |
| 284 | Assets/_Project/Tests/Editor/TestCompanionRuntime.cs |
| 285 | Assets/_Project/Tests/Editor/TestCompanionSeat.cs |
| 286 | Assets/_Project/Tests/Editor/TestCompanionSeat2.cs |
| 287 | Assets/_Project/Tests/Editor/TestCompanionUpgrade.cs |
| 288 | Assets/_Project/Tests/Editor/TestCopyPools.cs |
| 289 | Assets/_Project/Tests/Editor/TestCoreBus.cs |
| 290 | Assets/_Project/Tests/Editor/TestCoreJsonState.cs |
| 291 | Assets/_Project/Tests/Editor/TestCoreRegistry.cs |
| 292 | Assets/_Project/Tests/Editor/TestDailyTask.cs |
| 293 | Assets/_Project/Tests/Editor/TestDailyTaskUi.cs |
| 294 | Assets/_Project/Tests/Editor/TestDoubleReward.cs |
| 295 | Assets/_Project/Tests/Editor/TestEmotionCurve.cs |
| 296 | Assets/_Project/Tests/Editor/TestEvolveRitualFrame.cs |
| 297 | Assets/_Project/Tests/Editor/TestFeatherRevive.cs |
| 298 | Assets/_Project/Tests/Editor/TestFiveBeats.cs |
| 299 | Assets/_Project/Tests/Editor/TestFont.cs |
| 300 | Assets/_Project/Tests/Editor/TestGameplayCapture.cs |
| 301 | Assets/_Project/Tests/Editor/TestInLevelChoiceFlow.cs |
| 302 | Assets/_Project/Tests/Editor/TestJuiceCurves.cs |
| 303 | Assets/_Project/Tests/Editor/TestLevelRules.cs |
| 304 | Assets/_Project/Tests/Editor/TestLevels.cs |
| 305 | Assets/_Project/Tests/Editor/TestLevelSupply.cs |
| 306 | Assets/_Project/Tests/Editor/TestLevelSupplyUi.cs |
| 307 | Assets/_Project/Tests/Editor/TestLevelTimerRearm.cs |
| 308 | Assets/_Project/Tests/Editor/TestMetaProgress.cs |
| 309 | Assets/_Project/Tests/Editor/TestNewbieAttraction.cs |
| 310 | Assets/_Project/Tests/Editor/TestO1610WelcomeBand.cs |
| 311 | Assets/_Project/Tests/Editor/TestOfflineEarnings.cs |
| 312 | Assets/_Project/Tests/Editor/TestOfflineEarningsUi.cs |
| 313 | Assets/_Project/Tests/Editor/TestPaywallGate.cs |
| 314 | Assets/_Project/Tests/Editor/TestPersistence.cs |
| 315 | Assets/_Project/Tests/Editor/TestPrewarmWiring.cs |
| 316 | Assets/_Project/Tests/Editor/TestProductFx.cs |
| 317 | Assets/_Project/Tests/Editor/TestProfileScope.cs |
| 318 | Assets/_Project/Tests/Editor/TestRemainderGuide.cs |
| 319 | Assets/_Project/Tests/Editor/TestReplayMath.cs |
| 320 | Assets/_Project/Tests/Editor/TestReplayPoster.cs |
| 321 | Assets/_Project/Tests/Editor/TestReviveRearm.cs |
| 322 | Assets/_Project/Tests/Editor/TestSfxFamilySounds.cs |
| 323 | Assets/_Project/Tests/Editor/TestSfxSynthClips.cs |
| 324 | Assets/_Project/Tests/Editor/TestShareLanding.cs |
| 325 | Assets/_Project/Tests/Editor/TestSignatureLevels.cs |
| 326 | Assets/_Project/Tests/Editor/TestSocial.cs |
| 327 | Assets/_Project/Tests/Editor/TestSocialCloud.cs |
| 328 | Assets/_Project/Tests/Editor/TestStoreAds.cs |
| 329 | Assets/_Project/Tests/Editor/TestStoreFlow.cs |
| 330 | Assets/_Project/Tests/Editor/TestSuctionFamilies.cs |
| 331 | Assets/_Project/Tests/Editor/TestSweepVerb.cs |
| 332 | Assets/_Project/Tests/Editor/TestSystemUnlocks.cs |
| 333 | Assets/_Project/Tests/Editor/TestTutorialHint.cs |
| 334 | Assets/_Project/Tests/Editor/TestU351BankCleanup.cs |
| 335 | Assets/_Project/Tests/Editor/TestU351BottomRhythm.cs |
| 336 | Assets/_Project/Tests/Editor/TestU351CapsuleWash.cs |
| 337 | Assets/_Project/Tests/Editor/TestU351Density.cs |
| 338 | Assets/_Project/Tests/Editor/TestU351Hitpad.cs |
| 339 | Assets/_Project/Tests/Editor/TestU351StardustSplit.cs |
| 340 | Assets/_Project/Tests/Editor/TestU351Stopgap.cs |
| 341 | Assets/_Project/Tests/Editor/TestU360L4BWalk.cs |
| 342 | Assets/_Project/Tests/Editor/TestU360L4LegacyLayout.cs |
| 343 | Assets/_Project/Tests/Editor/TestU360L4Ui.cs |
| 344 | Assets/_Project/Tests/Editor/TestU360L6B4Combo.cs |
| 345 | Assets/_Project/Tests/Editor/TestU360L6B4Lick.cs |
| 346 | Assets/_Project/Tests/Editor/TestU360L6B5BellyTower.cs |
| 347 | Assets/_Project/Tests/Editor/TestU360L6B5ChallengeStar.cs |
| 348 | Assets/_Project/Tests/Editor/TestU360L6B5PreLevelChoice.cs |
| 349 | Assets/_Project/Tests/Editor/TestU360L6FullPowerStorm.cs |
| 350 | Assets/_Project/Tests/Editor/TestU360L7SweepTeach.cs |
| 351 | Assets/_Project/Tests/Editor/TestU360S3Feel.cs |
| 352 | Assets/_Project/Tests/Editor/TestWaveDirector.cs |
| 353 | Assets/_Project/Tests/Editor/U360L3S3MomentShot.cs |
| 354 | Assets/_Project/Tests/Editor/U360L4CShot.cs |
| 355 | Assets/_Project/Tests/Editor/U360L4WalkShot.cs |
| 356 | Assets/_Project/Tests/Editor/U360L7FtueCapture.cs |
| 357 | Assets/_Project/Tests/Editor/U360LevelTour.cs |
| 358 | Assets/_Project/Tests/Editor/U360StageDiagnostics.cs |
| 359 | Assets/_Project/Tests/Editor/U360SweepShot.cs |
| 360 | Assets/_Project/Tests/Editor/X1958MenuShot.cs |
| 361 | Assets/_Project/Tests/PlayGate/EntityProbeDriver.cs |
| 362 | Assets/_Project/Tests/PlayGate/FxLoopDriver.cs |
| 363 | Assets/_Project/Tests/PlayGate/PlayLoopDriver.cs |
| 364 | Assets/_Project/UI/ArrivalBanner.cs |
| 365 | Assets/_Project/UI/ButtonSquash.cs |
| 366 | Assets/_Project/UI/BVersionPortMap.cs |
| 367 | Assets/_Project/UI/Car/CarLayout.Wing.cs |
| 368 | Assets/_Project/UI/CarLayout.cs |
| 369 | Assets/_Project/UI/ChapterChestScreen.cs |
| 370 | Assets/_Project/UI/ChapterJourney/ChapterJourneyScreen.Car.cs |
| 371 | Assets/_Project/UI/ChapterJourneyScreen.cs |
| 372 | Assets/_Project/UI/ChapterPalette.cs |
| 373 | Assets/_Project/UI/Chest/ChapterChestScreen.Car.cs |
| 374 | Assets/_Project/UI/ChoiceBanner.cs |
| 375 | Assets/_Project/UI/CodexCatalog.cs |
| 376 | Assets/_Project/UI/CodexRevealFx.cs |
| 377 | Assets/_Project/UI/Collection/CollectionCodex.cs |
| 378 | Assets/_Project/UI/Collection/CollectionCompanions.cs |
| 379 | Assets/_Project/UI/Collection/CollectionScreen.Car.cs |
| 380 | Assets/_Project/UI/CollectionScreen.cs |
| 381 | Assets/_Project/UI/CopyPools.cs |
| 382 | Assets/_Project/UI/DailyTask/DailyTaskScreen.Car.cs |
| 383 | Assets/_Project/UI/DailyTaskScreen.cs |
| 384 | Assets/_Project/UI/DuduIdlePlayer.cs |
| 385 | Assets/_Project/UI/FamilyNamePrompt.cs |
| 386 | Assets/_Project/UI/FlyToTarget.cs |
| 387 | Assets/_Project/UI/FrameGeometryProbe.cs |
| 388 | Assets/_Project/UI/FullChargeOverlay.cs |
| 389 | Assets/_Project/UI/FxEvents.cs |
| 390 | Assets/_Project/UI/HealthNoticeScreen.cs |
| 391 | Assets/_Project/UI/Hud/CompanionChargeRing.cs |
| 392 | Assets/_Project/UI/Hud/CompanionRecharge.cs |
| 393 | Assets/_Project/UI/Hud/Front3HudPanel.cs |
| 394 | Assets/_Project/UI/Hud/InGameHud.Boosters.cs |
| 395 | Assets/_Project/UI/Hud/ParentKeyHudPanel.cs |
| 396 | Assets/_Project/UI/ICommerceService.cs |
| 397 | Assets/_Project/UI/InGameHud.cs |
| 398 | Assets/_Project/UI/Leaderboard/LeaderboardScreen.Car.cs |
| 399 | Assets/_Project/UI/LeaderboardScreen.cs |
| 400 | Assets/_Project/UI/MainMenuScreen.cs |
| 401 | Assets/_Project/UI/Menu/MenuChromeKit.cs |
| 402 | Assets/_Project/UI/Menu/MenuEntryBar.cs |
| 403 | Assets/_Project/UI/Menu/MenuProgressBadges.cs |
| 404 | Assets/_Project/UI/NumberRoll.cs |
| 405 | Assets/_Project/UI/OfflineEarningsPopup.cs |
| 406 | Assets/_Project/UI/ParentGatePanel.cs |
| 407 | Assets/_Project/UI/Paywall/PaywallScreen.Car.cs |
| 408 | Assets/_Project/UI/Paywall/PaywallScreen.Flow.cs |
| 409 | Assets/_Project/UI/Paywall/PaywallScreen.Helpers.cs |
| 410 | Assets/_Project/UI/PaywallScreen.cs |
| 411 | Assets/_Project/UI/ProfileManagerPanel.cs |
| 412 | Assets/_Project/UI/ProfileScreen.cs |
| 413 | Assets/_Project/UI/Result/ResultScreen.Car.cs |
| 414 | Assets/_Project/UI/Result/ResultScreen.Postcard.cs |
| 415 | Assets/_Project/UI/ResultScreen.cs |
| 416 | Assets/_Project/UI/SafeAreaFitter.cs |
| 417 | Assets/_Project/UI/ScreenRouter.cs |
| 418 | Assets/_Project/UI/SneezeButton.cs |
| 419 | Assets/_Project/UI/Store/StoreScreen.Car.cs |
| 420 | Assets/_Project/UI/StoreCatalog.cs |
| 421 | Assets/_Project/UI/StoreScreen.cs |
| 422 | Assets/_Project/UI/StubCommerceService.cs |
| 423 | Assets/_Project/UI/TutorialHint.cs |
| 424 | Assets/_Project/UI/UIArt.cs |
| 425 | Assets/_Project/UI/UiBob.cs |
| 426 | Assets/_Project/UI/UiDrift.cs |
| 427 | Assets/_Project/UI/UiEasing.cs |
| 428 | Assets/_Project/UI/UiFade.cs |
| 429 | Assets/_Project/UI/UiFlash.cs |
| 430 | Assets/_Project/UI/UiKeySubmit.cs |
| 431 | Assets/_Project/UI/UIRoot.cs |
| 432 | Assets/_Project/UI/Wardrobe/WardrobeScreen.Car.cs |
| 433 | Assets/_Project/UI/WardrobeScreen.cs |
| 434 | production/reports/p0-quarantine-2026-09-17/BellyWindow.cs |
| 435 | production/reports/p0-quarantine-2026-09-17/HapticPulse.cs |
| 436 | production/reports/p0-quarantine-2026-09-17/JuiceCurves.cs |
| 437 | production/reports/p0-quarantine-2026-09-17/MetaFlow.cs |
| 438 | production/reports/p0-quarantine-2026-09-17/MetaStore.cs |
| 439 | production/reports/p0-quarantine-2026-09-17/ShareLandingGate.cs |
| 440 | production/reports/p0-quarantine-2026-09-17/SignatureArt.cs |
| 441 | production/reports/p0-quarantine-2026-09-17/SuctionTrail.cs |
| 442 | production/reports/p0-quarantine-2026-09-17/TestBellyMath.cs |
| 443 | production/reports/p0-quarantine-2026-09-17/TestJuiceCurves.cs |
| 444 | production/reports/p0-quarantine-2026-09-17/TestMetaProgress.cs |
| 445 | production/reports/p0-quarantine-2026-09-17/TestShareLanding.cs |
| 446 | production/reports/p0-quarantine-2026-09-17/UiBob.cs |
| 447 | production/reports/p0-quarantine-2026-09-17/UiFade.cs |
| 448 | production/reports/p0-quarantine-2026-09-17/WardrobeScreen.cs |

## 附录 B 命名空间与类型索引

| 命名空间 | 文件数 |
|---|---:|
| GimmeAll.Tests | 124 |
| GimmeAll.UI | 74 |
| GimmeAll.Game | 58 |
| GimmeAll.Gameplay | 58 |
| GimmeAll.Core | 42 |
| GimmeAll.Levels | 37 |
| GimmeAll.Replay | 10 |
| GimmeAll.Audio | 8 |
| GimmeAll.Levels.Stations | 8 |
| GimmeAll.Social | 8 |
| GimmeAll.Ads | 7 |
| GimmeAll.Game.Editor | 6 |
| GimmeAll.PlayGate | 3 |
| GimmeAll.Car | 2 |
| GimmeAll.Levels.Editor | 2 |
| GimmeAll.EditorTools | 1 |

| 文件 | 类型 | 公开方法数 |
|---|---|---:|
| mm-committed.cs | - | 3 |
| MOD-12-orig-MetaStore.cs | MetaStore | 47 |
| AdConfig.cs | AdConfig | 2 |
| AdsSelfTest.cs | AdsSelfTest | 0 |
| RewardCatalog.cs | RewardCatalog | 1 |
| StubAdRunner.cs | StubAdRunner | 2 |
| StubAdService.cs | StubAdService | 4 |
| WeChatAdBootstrap.cs | WeChatAdBootstrap | 0 |
| WeChatAdService.cs | WeChatAdService、AdUnitIds、AdUnitConfig | 8 |
| AudioSelfTest.cs | AudioSelfTest、AudioSelfTestRunner | 0 |
| BgmBus.cs | BgmBus、DuckTicker | 6 |
| SfxBus.cs | SfxKind、SfxBus | 6 |
| SfxFlow.cs | SfxFlow | 8 |
| CarCabinBridge.cs | CarCabinBridge、Keeper | 11 |
| CarCabinMock.cs | CarCabinMock、Drawer | 19 |
| AdCopy.cs | AdCopy | 9 |
| AdFrequencyGate.cs | AdFrequencyGate | 3 |
| AdServiceSeam.cs | AdServiceSeam | 3 |
| AdsPolicy.cs | AdsPolicy | 2 |
| CaptureBeat.cs | CaptureBeat | 3 |
| ComboTracker.cs | ComboTracker | 2 |
| CompanionDef.cs | CompanionDef、CompanionVersion、SkillKind、PointCaptureMode | 2 |
| CompanionProgress.cs | CompanionProgress | 17 |
| CompanionRuntime.cs | CompanionRuntime | 6 |
| AdMetrics.cs | AdMetrics | 3 |
| AdsEvents.cs | AdRewarded、InterstitialShown | 0 |
| AudioEvents.cs | SneezeStormBurst、CodexCryRequested、PostcardComposed、DuduReactionBeat | 0 |
| LevelEvents.cs | LevelStarted、BinInfo、LevelCompleted、LevelFailed | 3 |
| MetaEvents.cs | MetaItem、StardustChanged、ItemStockChanged、ItemUsedRequested | 6 |
| ProfileEvents.cs | ProfileSwitched | 0 |
| UIEvents.cs | SneezeChargeChanged、SneezeRequested、DailyFocusResolved、ShareLandingResolved | 0 |
| GameEventBus.cs | GameEventBus | 1 |
| GameEvents.cs | GameStateChanged | 0 |
| GameStateMachine.cs | GameState、GameStateMachine | 2 |
| IAnalyticsService.cs | IAnalyticsService | 0 |
| ICanvasBoard.cs | ICanvasBoard | 0 |
| ICarCabinSignalSource.cs | ICarCabinSignalSource、CarCabinChannel、CabinLightScene、SeatVibrationLevel | 0 |
| IMetaService.cs | IMetaService、MetaServices | 0 |
| InterstitialPolicy.cs | InterstitialPolicy | 0 |
| IRecordable.cs | RecordSnapshot、IRecordable | 0 |
| IServices.cs | SharePayload、LeaderboardEntry、IAdService、IShareService | 0 |
| ISuctionable.cs | SuctionState、ISuctionable | 0 |
| ISuctionGuide.cs | ISuctionGuideTarget、SuctionGuideField | 1 |
| LevelData.cs | SpawnEntry、LevelData、BinSpec、LevelJson | 2 |
| ObjectPool.cs | ObjectPool | 2 |
| ObjectRegistry.cs | ObjectRegistry | 6 |
| PlaceholderSpriteFactory.cs | PlaceholderSpriteFactory | 3 |
| PrefsFlush.cs | PrefsFlush、PrefsFlushPump | 2 |
| ProfileClaim.cs | ClaimOutcome、ProfileClaim | 2 |
| ProfileDelete.cs | DeleteOutcome、ProfileDelete | 6 |
| ProfileReloadContract.cs | ProfileReloadContract | 1 |
| ProfileRosterContract.cs | ProfileRosterContract | 3 |
| ProfileScope.cs | ProfileScope | 5 |
| ProfileSwitch.cs | SwitchOutcome、ProfileSwitch | 2 |
| ServiceRegistry.cs | ServiceRegistry | 1 |
| SpawnRegistry.cs | ISpawnFactory、SpawnRegistry | 4 |
| SystemUnlockGate.cs | SystemUnlockGate | 6 |
| BuildAndroid.cs | BuildAndroid、SpritePpuEnforcer、LockEntry、LockFile | 3 |
| AmbientLoopLayer.cs | AmbientLoopLayer、ChapterAmbient | 0 |
| AutoPilotMenuStart.cs | AutoPilotMenuStart | 0 |
| AutoPilotStationAdvance.cs | AutoPilotStationAdvance | 0 |
| BackdropBoard.cs | BackdropBoard | 2 |
| Bootstrap.cs | Bootstrap | 0 |
| CameraRig.cs | CameraRig | 2 |
| CarAppLifecycle.cs | CarAppLifecycle | 0 |
| ChapterArt.cs | ChapterArt | 4 |
| ChapterChestFlow.cs | ChapterChestFlow | 4 |
| CheckInFlow.cs | CheckInFlow | 2 |
| CodexAccelFlow.cs | CodexAccelFlow | 2 |
| CodexFlow.cs | CodexFlow | 2 |
| ComboChoiceFlow.cs | ComboChoiceFlow | 7 |
| CompanionAdFlow.cs | CompanionAdFlow | 2 |
| CompanionCoordinator.cs | CompanionCoordinator | 2 |
| CompanionRosterFlow.cs | CompanionRosterFlow | 0 |
| CompanionSeatFlow.cs | CompanionSeatFlow | 2 |
| CompanionUpgradeFlow.cs | CompanionUpgradeFlow | 1 |
| DailyTaskFlow.cs | DailyTaskFlow | 3 |
| DevLevelBoot.cs | DevLevelBoot、Runner | 0 |
| DuelRope.cs | DuelTier、DuelResult、DuelRope、DuelRopeSession | 15 |
| ArtImportRules.cs | ArtImportRules | 0 |
| AudioPackageMatrix.cs | AudioPackageMatrix、Tier | 2 |
| NewbieRunSetup.cs | NewbieRunSetup | 2 |
| O1610BorderBake.cs | O1610BorderBake | 1 |
| ProjectBuild.cs | ProjectBuild | 15 |
| StoreAssetGen.cs | StoreAssetGen | 1 |
| FeelPulse.cs | FeelPulse | 2 |
| FileAnalyticsService.cs | FileAnalyticsService | 2 |
| HapticPulse.cs | HapticPulse | 0 |
| HapticsRelay.cs | HapticsRelay | 0 |
| HiddenTreasureFlow.cs | HiddenTreasureFlow | 1 |
| InLevelChoiceFlow.cs | InLevelChoiceFlow | 9 |
| LevelSupplyFlow.cs | LevelSupplyFlow | 1 |
| MetaService.Companion.cs | - | 4 |
| MetaService.Daily.cs | - | 9 |
| MetaService.Profile.cs | - | 1 |
| MetaService.Sand.cs | - | 8 |
| MetaService.TestKeys.cs | - | 2 |
| MetaFlow.cs | MetaFlow | 0 |
| MetaService.cs | - | 2 |
| MetaStore.cs | MetaStore | 25 |
| OfflineEarningsFlow.cs | OfflineEarningsFlow | 3 |
| PadLevelSwitch.cs | PadLevelSwitch | 0 |
| PreLevelChoiceFlow.cs | PreLevelChoiceFlow | 5 |
| ProfileReload.cs | ProfileReload | 2 |
| ProfileRoster.cs | ProfileRoster | 3 |
| QuitTrace.cs | QuitTrace、FocusWatch | 0 |
| RevealVeil.cs | RevealVeil | 3 |
| ScreenshotKey.cs | ScreenshotKey | 0 |
| ShareLandingGate.cs | ShareLandingGate、LandingQuery | 2 |
| StationArt.cs | StationArt | 2 |
| StoreAdFlow.cs | StoreAdFlow | 0 |
| StoreFlow.cs | StoreFlow | 0 |
| TelemetryRelay.cs | TelemetryRelay | 0 |
| UnlockFlow.cs | UnlockFlow | 0 |
| WeChatAnalyticsService.cs | WeChatAnalyticsService | 1 |
| ActorDudu.cs | ActorDudu | 3 |
| AmbushBeat.cs | AmbushBeat、AmbushHidden | 5 |
| GameplayArt.cs | GameplayArt、Slot | 0 |
| BellyWindow.cs | BellyWindow、Chip、BellyMath、BellyTowerMath | 8 |
| BinZone.cs | BinZone | 3 |
| CaptureBurst.cs | CaptureBurst、Particle | 5 |
| CarryMouth.cs | CarryMouth、Piece、Batch | 2 |
| ChapterEvolveFlow.cs | ChapterEvolveFlow | 12 |
| ChapterFinale.cs | ChapterFinale、FinaleSequence | 3 |
| ChapterOnlooker.cs | ChapterOnlooker、EmotionFrame、EmoteBadge、BaseMood | 2 |
| ChapterOnlookerSelfTest.cs | ChapterOnlookerSelfTest | 0 |
| ClusterMilestone.cs | ClusterMilestone | 2 |
| DebrisTarget.cs | DebrisTarget | 0 |
| DustTarget.cs | DustTarget | 0 |
| EscapeBrake.cs | EscapeBrake | 2 |
| BubbleTarget.cs | BubbleTarget | 0 |
| GhostTarget.cs | GhostTarget | 1 |
| HeavyTarget.cs | HeavyTarget | 0 |
| MimicTarget.cs | MimicTarget | 1 |
| PlayBand.cs | PlayBand | 0 |
| SparkleTarget.cs | SparkleTarget | 0 |
| SplitterTarget.cs | SplitterTarget、SplitKidTarget | 0 |
| StickyTarget.cs | StickyTarget | 1 |
| SwarmTarget.cs | SwarmTarget | 0 |
| Front3Fx.cs | Front3Fx | 1 |
| Front3SuctionGrowth.cs | Front3SuctionGrowth | 1 |
| FullChargeCeremony.cs | FullChargeCeremony、State、FullChargePreannouncePublished、FullChargeRungPublished | 1 |
| FurTarget.cs | FurTarget | 0 |
| GameplayDirtPalette.cs | GameplayDirtPalette | 1 |
| GameplayEscape.cs | GameplayEscape | 1 |
| GameplaySelfTest.cs | GameplaySelfTest | 0 |
| GameplaySpawnFactory.cs | GameplaySpawnFactory | 1 |
| GrayscaleDriver.cs | GrayscaleDriver | 2 |
| GroundShadow.cs | GroundShadow | 1 |
| GuideRing.cs | GuideRing | 1 |
| HitStop.cs | HitStop、HitStopDriver | 6 |
| JuiceCurves.cs | JuiceCurves | 6 |
| LandmarkBeacon.cs | LandmarkBeacon | 2 |
| LevelScope.cs | LevelScope | 1 |
| PadInput.cs | PadInput | 2 |
| PointVacuum.cs | PointVacuum | 1 |
| ScratchTargets.cs | ScratchTarget | 3 |
| ScriptedPointer.cs | ScriptedPointer | 3 |
| ScriptedSuctionPilot.cs | ScriptedSuctionPilot、ProbeNote | 0 |
| SignatureArt.cs | SignatureArt | 1 |
| SignatureTargets.cs | SockTarget、FurBallTarget、SnakeTarget、CoinTarget | 0 |
| SneezeSystem.cs | SneezeSystem | 5 |
| SpawnSpecTable.cs | SpawnKind、SpawnSpec、SpawnSpecTable | 1 |
| SuctionField.cs | SuctionField | 6 |
| SuctionField.Visual.cs | SuctionField | 0 |
| SuctionFieldConfig.cs | SuctionFieldConfig | 0 |
| SuctionGuideWiring.cs | SuctionGuideWiring | 0 |
| SuctionTarget.cs | SuctionTarget | 11 |
| SuctionTrail.cs | SuctionTrail、Dot、TrailHost | 1 |
| CampaignCatalog.cs | ClusterSpec、LevelSpec | 0 |
| ChapterLore.cs | ChapterLore | 3 |
| ContentCatalog.cs | EmotionCurveRow | 22 |
| DailyLevelPolicy.cs | DailyLevelPolicy | 1 |
| ContentCatalogEditor.cs | ContentCatalogEditor | 1 |
| LevelEditorWindow.cs | LevelEditorWindow | 0 |
| GoalTracker.cs | GoalTracker | 1 |
| LevelCatalog.cs | LevelCatalog | 1 |
| LevelDiag.cs | LevelDiag | 0 |
| LevelProgressStore.cs | LevelProgressStore | 3 |
| LevelRules.cs | LevelRules | 4 |
| LevelRunner.cs | LevelRunner | 5 |
| LevelSourceResolver.cs | LevelSourceResolver | 3 |
| LevelsSelfTest.cs | LevelsSelfTest | 0 |
| LevelTimer.cs | LevelTimer | 1 |
| ParentKeyGuide.cs | ParentKeyGuide、Ticker | 7 |
| RemainderGuide.cs | RemainderGuide | 4 |
| StationAbLayout.cs | AbRow、AbPiece、AbSpec、StationAbLayout | 0 |
| StationCatalog_Station1.cs | StationCatalog_Station1、FamilySpec | 2 |
| StationCatalog_StationA.cs | StationCatalog_StationA | 1 |
| StationCatalog_StationB.cs | StationCatalog_StationB | 1 |
| StationCatalog_StationC.cs | StationCatalog_StationC | 1 |
| StationCatalog_StationD.cs | StationCatalog_StationD | 1 |
| StationCatalog_StationE.cs | StationCatalog_StationE | 1 |
| StationCatalog_StationF.cs | StationCatalog_StationF | 1 |
| WaveDirector.cs | WaveDirector | 9 |
| GhostPlayback.cs | GhostPlayback、GhostDot | 6 |
| PostcardComposer.cs | PostcardComposer | 1 |
| PosterComposer.cs | PosterComposer | 1 |
| ReplayConfig.cs | ReplayConfig | 0 |
| ReplayRecorder.cs | ReplayRecorder | 7 |
| ReplayRingMath.cs | ReplayRingMath | 2 |
| ReplaySelfTest.cs | ReplaySelfTest | 0 |
| ReplayShareService.cs | ReplayShareService | 3 |
| WanderDot.cs | WanderDot | 2 |
| WeChatShareService.cs | WeChatShareService | 6 |
| ArenaAnchor.cs | ArenaAnchor | 3 |
| CloudScoreParser.cs | CloudScoreParser、WxGameValue、WxGame | 1 |
| PersistentLeaderboardService.cs | PersistentLeaderboardService | 4 |
| ScoreFlow.cs | ScoreFlow | 0 |
| SocialSelfTest.cs | SocialSelfTest | 0 |
| StubLeaderboardService.cs | StubLeaderboardService | 2 |
| TimeService.cs | TimeService | 1 |
| WeChatLeaderboardService.cs | WeChatLeaderboardService | 6 |
| BVersionSevenShot.cs | BVersionSevenShot | 1 |
| ChapterTurnCapture.cs | ChapterTurnCapture | 1 |
| DevRigToggles.cs | DevRigToggles | 0 |
| DuduIdleShot.cs | DuduIdleShot | 1 |
| EditModeSpawnDrive.cs | EditModeSpawnDrive | 3 |
| EntityProbeGate.cs | EntityProbeGate | 1 |
| FxGate.cs | FxGate | 1 |
| HeadlessRunner.cs | HeadlessRunner | 1 |
| HeadlessTestAttribute.cs | HeadlessTestAttribute | 0 |
| NewbieFlowCapture.cs | NewbieFlowCapture | 1 |
| O1610MenuShot.cs | O1610MenuShot | 1 |
| PlayLoopGate.cs | PlayLoopGate | 1 |
| SettlementCapture.cs | SettlementCapture | 1 |
| SweepCapture.cs | SweepCapture、ModalPlan | 1 |
| TestAdCopyFamilyFace.cs | TestAdCopyFamilyFace | 3 |
| TestAdPolicyFaceVisible.cs | TestAdPolicyFaceVisible | 2 |
| TestAds.cs | TestAds、AdUnitConfigProbe | 8 |
| TestAdsMetrics.cs | TestAdsMetrics | 3 |
| TestArtAssets.cs | TestArtAssets | 20 |
| TestAudioAssets.cs | TestAudioAssets | 5 |
| TestAudioPackageMatrix.cs | TestAudioPackageMatrix | 3 |
| TestBellyMath.cs | TestBellyMath | 3 |
| TestBVersionChapterJourney.cs | TestBVersionChapterJourney | 3 |
| TestBVersionEntries.cs | TestBVersionEntries | 1 |
| TestBVersionPortMap.cs | TestBVersionPortMap | 2 |
| TestBVersionStoreScreen.cs | TestBVersionStoreScreen | 7 |
| TestChainIntegration.cs | TestChainIntegration、FakeAdService、FakeLeaderboardService、ChainEnv | 9 |
| TestChapterChest.cs | TestChapterChest | 3 |
| TestChapterChestUi.cs | TestChapterChestUi | 2 |
| TestChapterEvolveFlow.cs | TestChapterEvolveFlow | 7 |
| TestCheckIn.cs | TestCheckIn | 3 |
| TestCheckInUi.cs | TestCheckInUi | 2 |
| TestCodexAccel.cs | TestCodexAccel | 3 |
| TestCodexAccelUi.cs | TestCodexAccelUi、AccelStubAdService | 5 |
| TestCodexCatalog.cs | TestCodexCatalog | 6 |
| TestCodexFlow.cs | TestCodexFlow | 2 |
| TestCodexUi.cs | TestCodexUi | 4 |
| TestCompanionAds.cs | TestCompanionAds | 4 |
| TestCompanionFace.cs | TestCompanionFace | 2 |
| TestCompanionFamilies2.cs | TestCompanionFamilies2 | 3 |
| TestCompanionQi2b.cs | TestCompanionQi2b | 4 |
| TestCompanionRoster.cs | TestCompanionRoster | 9 |
| TestCompanionRosterUi.cs | TestCompanionRosterUi、Seat2StubAdService | 10 |
| TestCompanionRuntime.cs | TestCompanionRuntime | 3 |
| TestCompanionSeat.cs | TestCompanionSeat | 3 |
| TestCompanionSeat2.cs | TestCompanionSeat2 | 4 |
| TestCompanionUpgrade.cs | TestCompanionUpgrade | 3 |
| TestCopyPools.cs | TestCopyPools | 7 |
| TestCoreBus.cs | TestCoreBus | 6 |
| TestCoreJsonState.cs | TestCoreJsonState | 6 |
| TestCoreRegistry.cs | TestCoreRegistry、FakeRecordable、FakeSuctionable、FakeFactory | 11 |
| TestDailyTask.cs | TestDailyTask | 3 |
| TestDailyTaskUi.cs | TestDailyTaskUi | 2 |
| TestDoubleReward.cs | TestDoubleReward、CaptureAnalytics | 5 |
| TestEmotionCurve.cs | TestEmotionCurve | 5 |
| TestEvolveRitualFrame.cs | TestEvolveRitualFrame | 5 |
| TestFeatherRevive.cs | TestFeatherRevive | 3 |
| TestFiveBeats.cs | TestFiveBeats | 8 |
| TestFont.cs | TestFont | 6 |
| TestGameplayCapture.cs | TestGameplayCapture | 6 |
| TestInLevelChoiceFlow.cs | TestInLevelChoiceFlow | 6 |
| TestJuiceCurves.cs | TestJuiceCurves | 6 |
| TestLevelRules.cs | TestLevelRules | 8 |
| TestLevels.cs | TestLevels、ProbeTarget、ProbeFactory | 15 |
| TestLevelSupply.cs | TestLevelSupply | 3 |
| TestLevelSupplyUi.cs | TestLevelSupplyUi、SupplyStubAdService | 6 |
| TestLevelTimerRearm.cs | TestLevelTimerRearm | 3 |
| TestMetaProgress.cs | TestMetaProgress | 6 |
| TestNewbieAttraction.cs | TestNewbieAttraction | 3 |
| TestO1610WelcomeBand.cs | TestO1610WelcomeBand | 1 |
| TestOfflineEarnings.cs | TestOfflineEarnings | 3 |
| TestOfflineEarningsUi.cs | TestOfflineEarningsUi | 2 |
| TestPaywallGate.cs | TestPaywallGate | 18 |
| TestPersistence.cs | TestPersistence、FriendsOnlyInner、LowSelfInner | 9 |
| TestPrewarmWiring.cs | TestPrewarmWiring | 2 |
| TestProductFx.cs | TestProductFx | 6 |
| TestProfileScope.cs | TestProfileScope | 26 |
| TestRemainderGuide.cs | TestRemainderGuide | 2 |
| TestReplayMath.cs | TestReplayMath | 6 |
| TestReplayPoster.cs | TestReplayPoster | 4 |
| TestReviveRearm.cs | TestReviveRearm | 1 |
| TestSfxFamilySounds.cs | TestSfxFamilySounds | 1 |
| TestSfxSynthClips.cs | TestSfxSynthClips | 1 |
| TestShareLanding.cs | TestShareLanding | 4 |
| TestSignatureLevels.cs | TestSignatureLevels | 6 |
| TestSocial.cs | TestSocial | 6 |
| TestSocialCloud.cs | TestSocialCloud | 6 |
| TestStoreAds.cs | TestStoreAds | 3 |
| TestStoreFlow.cs | TestStoreFlow | 4 |
| TestSuctionFamilies.cs | TestSuctionFamilies | 18 |
| TestSweepVerb.cs | TestSweepVerb | 4 |
| TestSystemUnlocks.cs | TestSystemUnlocks | 5 |
| TestTutorialHint.cs | TestTutorialHint | 1 |
| TestU351BankCleanup.cs | TestU351BankCleanup | 2 |
| TestU351BottomRhythm.cs | TestU351BottomRhythm | 3 |
| TestU351CapsuleWash.cs | TestU351CapsuleWash | 2 |
| TestU351Density.cs | TestU351Density | 3 |
| TestU351Hitpad.cs | TestU351Hitpad | 2 |
| TestU351StardustSplit.cs | TestU351StardustSplit | 2 |
| TestU351Stopgap.cs | TestU351Stopgap | 2 |
| TestU360L4BWalk.cs | TestU360L4BWalk | 2 |
| TestU360L4LegacyLayout.cs | TestU360L4LegacyLayout | 2 |
| TestU360L4Ui.cs | TestU360L4Ui | 3 |
| TestU360L6B4Combo.cs | TestU360L6B4Combo | 5 |
| TestU360L6B4Lick.cs | TestU360L6B4Lick、LickProbe | 8 |
| TestU360L6B5BellyTower.cs | TestU360L6B5BellyTower | 5 |
| TestU360L6B5ChallengeStar.cs | TestU360L6B5ChallengeStar | 3 |
| TestU360L6B5PreLevelChoice.cs | TestU360L6B5PreLevelChoice | 5 |
| TestU360L6FullPowerStorm.cs | TestU360L6FullPowerStorm | 4 |
| TestU360L7SweepTeach.cs | TestU360L7SweepTeach | 3 |
| TestU360S3Feel.cs | TestU360S3Feel | 7 |
| TestWaveDirector.cs | TestWaveDirector | 13 |
| U360L3S3MomentShot.cs | U360L3S3MomentShot | 1 |
| U360L4CShot.cs | U360L4CShot | 1 |
| U360L4WalkShot.cs | U360L4WalkShot | 1 |
| U360L7FtueCapture.cs | U360L7FtueCapture | 1 |
| U360LevelTour.cs | U360LevelTour | 1 |
| U360StageDiagnostics.cs | U360StageDiagnostics | 1 |
| U360SweepShot.cs | U360SweepShot | 1 |
| X1958MenuShot.cs | X1958MenuShot | 1 |
| EntityProbeDriver.cs | EntityProbeDriver | 0 |
| FxLoopDriver.cs | FxLoopDriver | 0 |
| PlayLoopDriver.cs | PlayLoopDriver | 0 |
| ArrivalBanner.cs | ArrivalBanner | 1 |
| ButtonSquash.cs | ButtonSquash | 4 |
| BVersionPortMap.cs | BVersionPortMap、PortState | 1 |
| CarLayout.Wing.cs | InfoPlateFitter、SlotActiveFollower、InfoVisibilityFollower、CameraViewportFitter | 5 |
| CarLayout.cs | - | 14 |
| ChapterChestScreen.cs | - | 4 |
| ChapterJourneyScreen.Car.cs | - | 1 |
| ChapterJourneyScreen.cs | - | 5 |
| ChapterPalette.cs | ChapterPalette | 4 |
| ChoiceBanner.cs | ChoiceBanner | 0 |
| CodexCatalog.cs | CodexCatalog、CodexEntry | 12 |
| CodexRevealFx.cs | CodexRevealFx | 1 |
| CollectionCodex.cs | CardView | 1 |
| CollectionCompanions.cs | CompanionCardView | 0 |
| CollectionScreen.cs | - | 3 |
| CopyPools.cs | CopyPools、DailyFocus、ShareLanding | 20 |
| DailyTaskScreen.cs | - | 3 |
| DuduIdlePlayer.cs | DuduIdlePlayer | 0 |
| FamilyNamePrompt.cs | FamilyNamePrompt | 3 |
| FlyToTarget.cs | FlyToTarget、FlyRunner | 4 |
| FrameGeometryProbe.cs | FrameGeometryProbe | 1 |
| FullChargeOverlay.cs | FullChargeOverlay | 2 |
| FxEvents.cs | HealthNoticeClosed、LevelStartRequested、DailyLevelRequested、ContinueRequested | 0 |
| HealthNoticeScreen.cs | HealthNoticeScreen、AutopilotLandingDriver | 3 |
| CompanionChargeRing.cs | CompanionChargeRing | 0 |
| CompanionRecharge.cs | CompanionRecharge | 0 |
| Front3HudPanel.cs | Front3HudPanel | 4 |
| ParentKeyHudPanel.cs | ParentKeyHudPanel | 4 |
| ICommerceService.cs | CommerceChannel、PurchaseStatus、PurchaseReceipt、ICommerceService | 3 |
| InGameHud.cs | InfoRowSeat | 5 |
| LeaderboardScreen.cs | - | 3 |
| MainMenuScreen.cs | - | 3 |
| MenuChromeKit.cs | HitpadSpec | 0 |
| MenuEntryBar.cs | - | 1 |
| NumberRoll.cs | NumberRoll、FloatUpDriver | 3 |
| OfflineEarningsPopup.cs | OfflineEarningsPopup | 3 |
| ParentGatePanel.cs | ParentGatePanel | 7 |
| PaywallScreen.Helpers.cs | PostcardRetainKeys | 9 |
| PaywallScreen.cs | PaywallEntry、Stage | 5 |
| ProfileManagerPanel.cs | ProfileManagerPanel | 6 |
| ProfileScreen.cs | ProfileScreen | 2 |
| ResultScreen.cs | - | 3 |
| SafeAreaFitter.cs | SafeAreaFitter | 0 |
| ScreenRouter.cs | ScreenRouter | 0 |
| SneezeButton.cs | SneezeButton | 0 |
| StoreCatalog.cs | StoreCatalog | 6 |
| StoreScreen.cs | UiNudge | 5 |
| StubCommerceService.cs | StubCommerceService | 6 |
| TutorialHint.cs | TutorialHint | 7 |
| UIArt.cs | UIArt | 2 |
| UiBob.cs | UiBob | 0 |
| UiDrift.cs | UiDrift | 0 |
| UiEasing.cs | UiEasing | 5 |
| UiFade.cs | UiFade | 3 |
| UiFlash.cs | UiFlash | 3 |
| UiKeySubmit.cs | UiKeySubmit | 3 |
| UIRoot.cs | UIRoot、ButtonShadowPad | 10 |
| WardrobeScreen.cs | - | 6 |
| BellyWindow.cs | BellyWindow、Chip、BellyMath | 3 |
| HapticPulse.cs | HapticPulse | 0 |
| JuiceCurves.cs | JuiceCurves | 4 |
| MetaFlow.cs | MetaFlow | 0 |
| MetaStore.cs | MetaStore | 8 |
| ShareLandingGate.cs | ShareLandingGate、LandingQuery | 2 |
| SignatureArt.cs | SignatureArt | 1 |
| SuctionTrail.cs | SuctionTrail、Dot、TrailHost | 1 |
| TestBellyMath.cs | TestBellyMath | 3 |
| TestJuiceCurves.cs | TestJuiceCurves | 4 |
| TestMetaProgress.cs | TestMetaProgress | 6 |
| TestShareLanding.cs | TestShareLanding | 4 |
| UiBob.cs | UiBob | 0 |
| UiFade.cs | UiFade | 3 |
| WardrobeScreen.cs | WardrobeScreen | 3 |

## 附录 C 公开方法索引

| # | 文件 | 方法 |
|---:|---|---|
| 1 | mm-committed.cs | SetDuduPose |
| 2 | mm-committed.cs | Show |
| 3 | mm-committed.cs | Hide |
| 4 | MOD-12-orig-MetaStore.cs | StageOf |
| 5 | MOD-12-orig-MetaStore.cs | AddSand |
| 6 | MOD-12-orig-MetaStore.cs | TrySpendSand |
| 7 | MOD-12-orig-MetaStore.cs | ItemCount |
| 8 | MOD-12-orig-MetaStore.cs | GrantItem |
| 9 | MOD-12-orig-MetaStore.cs | TryConsume |
| 10 | MOD-12-orig-MetaStore.cs | ChapterClearedOnce |
| 11 | MOD-12-orig-MetaStore.cs | MarkChapterCleared |
| 12 | MOD-12-orig-MetaStore.cs | SetDailyDay |
| 13 | MOD-12-orig-MetaStore.cs | SetDailyTaskBits |
| 14 | MOD-12-orig-MetaStore.cs | LevelClearedOnce |
| 15 | MOD-12-orig-MetaStore.cs | MarkLevelCleared |
| 16 | MOD-12-orig-MetaStore.cs | LevelClearBits |
| 17 | MOD-12-orig-MetaStore.cs | ChestClaimedOnce |
| 18 | MOD-12-orig-MetaStore.cs | MarkChestClaimed |
| 19 | MOD-12-orig-MetaStore.cs | CodexFullHouseOnce |
| 20 | MOD-12-orig-MetaStore.cs | MarkCodexFullHouse |
| 21 | MOD-12-orig-MetaStore.cs | CompanionLevel |
| 22 | MOD-12-orig-MetaStore.cs | SetCompanionLevel |
| 23 | MOD-12-orig-MetaStore.cs | CompanionSeat |
| 24 | MOD-12-orig-MetaStore.cs | SetCompanionSeat |
| 25 | MOD-12-orig-MetaStore.cs | WipeTestKeysForCurrentPrefix |
| 26 | MOD-12-orig-MetaStore.cs | UsePrefsKeyForTests |
| 27 | MOD-12-orig-MetaStore.cs | Flush |
| 28 | MOD-12-orig-MetaStore.cs | StageOf |
| 29 | MOD-12-orig-MetaStore.cs | AddSand |
| 30 | MOD-12-orig-MetaStore.cs | TrySpendSand |
| 31 | MOD-12-orig-MetaStore.cs | ItemCount |
| 32 | MOD-12-orig-MetaStore.cs | GrantItem |
| 33 | MOD-12-orig-MetaStore.cs | TryConsume |
| 34 | MOD-12-orig-MetaStore.cs | ChapterClearedOnce |
| 35 | MOD-12-orig-MetaStore.cs | MarkChapterCleared |
| 36 | MOD-12-orig-MetaStore.cs | SetDailyDay |
| 37 | MOD-12-orig-MetaStore.cs | SetDailyTaskBits |
| 38 | MOD-12-orig-MetaStore.cs | LevelClearedOnce |
| 39 | MOD-12-orig-MetaStore.cs | MarkLevelCleared |
| 40 | MOD-12-orig-MetaStore.cs | LevelClearBits |
| 41 | MOD-12-orig-MetaStore.cs | ChestClaimedOnce |
| 42 | MOD-12-orig-MetaStore.cs | MarkChestClaimed |
| 43 | MOD-12-orig-MetaStore.cs | CodexFullHouseOnce |
| 44 | MOD-12-orig-MetaStore.cs | MarkCodexFullHouse |
| 45 | MOD-12-orig-MetaStore.cs | CompanionLevel |
| 46 | MOD-12-orig-MetaStore.cs | SetCompanionLevel |
| 47 | MOD-12-orig-MetaStore.cs | CompanionSeat |
| 48 | MOD-12-orig-MetaStore.cs | SetCompanionSeat |
| 49 | MOD-12-orig-MetaStore.cs | WipeTestKeysForCurrentPrefix |
| 50 | MOD-12-orig-MetaStore.cs | UsePrefsKeyForTests |
| 51 | AdConfig.cs | IsRewardedPlacement |
| 52 | AdConfig.cs | IndexOfRewardedPlacement |
| 53 | RewardCatalog.cs | GetIntent |
| 54 | StubAdRunner.cs | RunRewarded |
| 55 | StubAdRunner.cs | RunInterstitial |
| 56 | StubAdService.cs | RewardedReady |
| 57 | StubAdService.cs | ShowRewarded |
| 58 | StubAdService.cs | ShowInterstitial |
| 59 | StubAdService.cs | ShowBanner |
| 60 | WeChatAdService.cs | RewardedReady |
| 61 | WeChatAdService.cs | ShowRewarded |
| 62 | WeChatAdService.cs | ShowInterstitial |
| 63 | WeChatAdService.cs | ShowBanner |
| 64 | WeChatAdService.cs | RewardedReady |
| 65 | WeChatAdService.cs | ShowRewarded |
| 66 | WeChatAdService.cs | ShowInterstitial |
| 67 | WeChatAdService.cs | ShowBanner |
| 68 | BgmBus.cs | ClipNameForLevelId |
| 69 | BgmBus.cs | Bind |
| 70 | BgmBus.cs | Init |
| 71 | BgmBus.cs | SwitchTo |
| 72 | BgmBus.cs | EnsurePlaying |
| 73 | BgmBus.cs | Duck |
| 74 | SfxBus.cs | Init |
| 75 | SfxBus.cs | Play |
| 76 | SfxBus.cs | Play |
| 77 | SfxBus.cs | StopAll |
| 78 | SfxBus.cs | CaptureWindowFor |
| 79 | SfxBus.cs | Reset |
| 80 | SfxFlow.cs | Bind |
| 81 | SfxFlow.cs | Reset |
| 82 | SfxFlow.cs | PlayEnterSting |
| 83 | SfxFlow.cs | PlayWinSting |
| 84 | SfxFlow.cs | PlayFailSting |
| 85 | SfxFlow.cs | StingLoadStatus |
| 86 | SfxFlow.cs | PlayStarRelease |
| 87 | SfxFlow.cs | PlayCry |
| 88 | CarCabinBridge.cs | RegisterOem |
| 89 | CarCabinBridge.cs | EnsureInstalled |
| 90 | CarCabinBridge.cs | TrySetAmbientLight |
| 91 | CarCabinBridge.cs | TryPlayAmbientScene |
| 92 | CarCabinBridge.cs | TryVibrateSeat |
| 93 | CarCabinBridge.cs | TrySetFragrance |
| 94 | CarCabinBridge.cs | TryDistributeToScreen |
| 95 | CarCabinBridge.cs | TrySpeak |
| 96 | CarCabinBridge.cs | StopSpeaking |
| 97 | CarCabinBridge.cs | RestoreCabin |
| 98 | CarCabinBridge.cs | Bind |
| 99 | CarCabinMock.cs | SetChargingSoc |
| 100 | CarCabinMock.cs | SetChargingPowerKw |
| 101 | CarCabinMock.cs | TriggerChargingCompleted |
| 102 | CarCabinMock.cs | SetOdometerKm |
| 103 | CarCabinMock.cs | SetSeatbelt |
| 104 | CarCabinMock.cs | SetAllSeatbelts |
| 105 | CarCabinMock.cs | SetParkingGear |
| 106 | CarCabinMock.cs | SetSteeringAngle |
| 107 | CarCabinMock.cs | PressSteeringKey |
| 108 | CarCabinMock.cs | IsChannelSupported |
| 109 | CarCabinMock.cs | IsSeatbeltBuckled |
| 110 | CarCabinMock.cs | SetAmbientLight |
| 111 | CarCabinMock.cs | PlayAmbientScene |
| 112 | CarCabinMock.cs | RestoreAmbientLight |
| 113 | CarCabinMock.cs | VibrateSeat |
| 114 | CarCabinMock.cs | SetFragrance |
| 115 | CarCabinMock.cs | Speak |
| 116 | CarCabinMock.cs | StopSpeaking |
| 117 | CarCabinMock.cs | DistributeToScreen |
| 118 | AdCopy.cs | DoubleReward |
| 119 | AdCopy.cs | Revive |
| 120 | AdCopy.cs | Supply |
| 121 | AdCopy.cs | Trial |
| 122 | AdCopy.cs | CodexAccel |
| 123 | AdCopy.cs | SeatUnlock |
| 124 | AdCopy.cs | OfflineDouble |
| 125 | AdCopy.cs | Vault |
| 126 | AdCopy.cs | ShopSand |
| 127 | AdFrequencyGate.cs | CanShowInterstitial |
| 128 | AdFrequencyGate.cs | RegisterInterstitialShown |
| 129 | AdFrequencyGate.cs | Reset |
| 130 | AdServiceSeam.cs | Provide |
| 131 | AdServiceSeam.cs | Activate |
| 132 | AdServiceSeam.cs | Reset |
| 133 | AdsPolicy.cs | FaceVisibleFor |
| 134 | AdsPolicy.cs | IsFamilyOrCarBuild |
| 135 | CaptureBeat.cs | PredictAudible |
| 136 | CaptureBeat.cs | IsSignature |
| 137 | CaptureBeat.cs | Reset |
| 138 | ComboTracker.cs | NoteCapture |
| 139 | ComboTracker.cs | Reset |
| 140 | CompanionDef.cs | ForVersion |
| 141 | CompanionDef.cs | ById |
| 142 | CompanionProgress.cs | UpgradeCost |
| 143 | CompanionProgress.cs | PowerScale |
| 144 | CompanionProgress.cs | ChargeProgress01 |
| 145 | CompanionProgress.cs | UnlockLevelId |
| 146 | CompanionProgress.cs | TrialPending |
| 147 | CompanionProgress.cs | ResolveActiveWithTrial |
| 148 | CompanionProgress.cs | Seat2Unlocked |
| 149 | CompanionProgress.cs | Seat2OfChapter |
| 150 | CompanionProgress.cs | ScaledRadius |
| 151 | CompanionProgress.cs | ScaledDuration |
| 152 | CompanionProgress.cs | ScaledSeconds |
| 153 | CompanionProgress.cs | ScaledCaptureCount |
| 154 | CompanionProgress.cs | ScaledHaltSec |
| 155 | CompanionProgress.cs | ScaledStardustFlat |
| 156 | CompanionProgress.cs | ScaledShieldCount |
| 157 | CompanionProgress.cs | PrimarySeat |
| 158 | CompanionProgress.cs | ResolveSeat |
| 159 | CompanionRuntime.cs | ResetForLevel |
| 160 | CompanionRuntime.cs | OnCapture |
| 161 | CompanionRuntime.cs | TryConsume |
| 162 | CompanionRuntime.cs | ArmShield |
| 163 | CompanionRuntime.cs | TryRechargeFill |
| 164 | CompanionRuntime.cs | ConsumeShield |
| 165 | AdMetrics.cs | InterstitialsFor |
| 166 | AdMetrics.cs | RewardedsFor |
| 167 | AdMetrics.cs | Reset |
| 168 | LevelEvents.cs | Envelope01 |
| 169 | LevelEvents.cs | Falloff01 |
| 170 | LevelEvents.cs | StrengthAt |
| 171 | MetaEvents.cs | RewardFor |
| 172 | MetaEvents.cs | ChestItemOf |
| 173 | MetaEvents.cs | SupplyItemOf |
| 174 | MetaEvents.cs | AccelItemOf |
| 175 | MetaEvents.cs | PriceOf |
| 176 | MetaEvents.cs | ItemOf |
| 177 | GameEventBus.cs | ClearAll |
| 178 | GameStateMachine.cs | Set |
| 179 | GameStateMachine.cs | ResetToBoot |
| 180 | ISuctionGuide.cs | Reset |
| 181 | LevelData.cs | ToJson |
| 182 | LevelData.cs | FromJson |
| 183 | ObjectPool.cs | Acquire |
| 184 | ObjectPool.cs | Release |
| 185 | ObjectRegistry.cs | NextId |
| 186 | ObjectRegistry.cs | Register |
| 187 | ObjectRegistry.cs | Unregister |
| 188 | ObjectRegistry.cs | GetAt |
| 189 | ObjectRegistry.cs | CopyActive |
| 190 | ObjectRegistry.cs | Clear |
| 191 | PlaceholderSpriteFactory.cs | Ring |
| 192 | PlaceholderSpriteFactory.cs | Circle |
| 193 | PlaceholderSpriteFactory.cs | Square |
| 194 | PrefsFlush.cs | Request |
| 195 | PrefsFlush.cs | FlushNow |
| 196 | ProfileClaim.cs | ClaimGuest |
| 197 | ProfileClaim.cs | RecoverPending |
| 198 | ProfileDelete.cs | IsNamedSlot |
| 199 | ProfileDelete.cs | IsOccupied |
| 200 | ProfileDelete.cs | SlotName |
| 201 | ProfileDelete.cs | CountNamed |
| 202 | ProfileDelete.cs | FindEmptySlot |
| 203 | ProfileDelete.cs | DeleteProfile |
| 204 | ProfileReloadContract.cs | Reset |
| 205 | ProfileRosterContract.cs | IntKeys |
| 206 | ProfileRosterContract.cs | StringKeys |
| 207 | ProfileRosterContract.cs | Reset |
| 208 | ProfileScope.cs | IsValidSlot |
| 209 | ProfileScope.cs | Key |
| 210 | ProfileScope.cs | KeyInSlot |
| 211 | ProfileScope.cs | Reload |
| 212 | ProfileScope.cs | UseSlotForTests |
| 213 | ProfileSwitch.cs | SwitchProfile |
| 214 | ProfileSwitch.cs | ReloadActive |
| 215 | ServiceRegistry.cs | Clear |
| 216 | SpawnRegistry.cs | Register |
| 217 | SpawnRegistry.cs | IsRegistered |
| 218 | SpawnRegistry.cs | TryCreate |
| 219 | SpawnRegistry.cs | Clear |
| 220 | SystemUnlockGate.cs | IsChallengeLevel |
| 221 | SystemUnlockGate.cs | RebindForProfile |
| 222 | SystemUnlockGate.cs | IsUnlocked |
| 223 | SystemUnlockGate.cs | MarkUnlocked |
| 224 | SystemUnlockGate.cs | UsePrefsKeyForTests |
| 225 | SystemUnlockGate.cs | WipeForCurrentTestPrefix |
| 226 | BuildAndroid.cs | Probe |
| 227 | BuildAndroid.cs | BuildWindows |
| 228 | BuildAndroid.cs | Build |
| 229 | BackdropBoard.cs | Show |
| 230 | BackdropBoard.cs | ShowLarge |
| 231 | CameraRig.cs | AddShake |
| 232 | CameraRig.cs | DecayAmp |
| 233 | ChapterArt.cs | ChapterOf |
| 234 | ChapterArt.cs | HasLargeScene |
| 235 | ChapterArt.cs | Scene |
| 236 | ChapterArt.cs | For |
| 237 | ChapterChestFlow.cs | ChapterOf |
| 238 | ChapterChestFlow.cs | LevelsDoneOf |
| 239 | ChapterChestFlow.cs | FocusChapter |
| 240 | ChapterChestFlow.cs | TryClaimChest |
| 241 | CheckInFlow.cs | TryCheckIn |
| 242 | CheckInFlow.cs | SetNowUnixForTests |
| 243 | CodexAccelFlow.cs | MissingCount |
| 244 | CodexAccelFlow.cs | PublishSnapshot |
| 245 | CodexFlow.cs | FullHouseReached |
| 246 | CodexFlow.cs | TryClaimFullHouse |
| 247 | ComboChoiceFlow.cs | HandleLevelStarted |
| 248 | ComboChoiceFlow.cs | HandleObjectCaptured |
| 249 | ComboChoiceFlow.cs | HandleObjectCaptured |
| 250 | ComboChoiceFlow.cs | HandlePickRequested |
| 251 | ComboChoiceFlow.cs | HandleLevelCompleted |
| 252 | ComboChoiceFlow.cs | HandleLevelFailed |
| 253 | ComboChoiceFlow.cs | ResetForTests |
| 254 | CompanionAdFlow.cs | TryArmTrial |
| 255 | CompanionAdFlow.cs | TryUnlockSeat2Timed |
| 256 | CompanionCoordinator.cs | TryRecharge |
| 257 | CompanionCoordinator.cs | TryRechargeById |
| 258 | CompanionSeatFlow.cs | TrySetSeat |
| 259 | CompanionSeatFlow.cs | TryUnlockSeat2Permanent |
| 260 | CompanionUpgradeFlow.cs | TryUpgrade |
| 261 | DailyTaskFlow.cs | TryClaim |
| 262 | DailyTaskFlow.cs | SetNowUnixForTests |
| 263 | DailyTaskFlow.cs | ClearCacheForTests |
| 264 | DuelRope.cs | TierAt |
| 265 | DuelRope.cs | SeatOf |
| 266 | DuelRope.cs | InNeutralBand |
| 267 | DuelRope.cs | ModeAvailable |
| 268 | DuelRope.cs | SteeringSignalAvailable |
| 269 | DuelRope.cs | Step |
| 270 | DuelRope.cs | Arm |
| 271 | DuelRope.cs | SetWheelSource |
| 272 | DuelRope.cs | Disarm |
| 273 | DuelRope.cs | RestartRound |
| 274 | DuelRope.cs | Attach |
| 275 | DuelRope.cs | Begin |
| 276 | DuelRope.cs | Refresh |
| 277 | DuelRope.cs | ResetForNewRound |
| 278 | DuelRope.cs | Teardown |
| 279 | AudioPackageMatrix.cs | TierOf |
| 280 | AudioPackageMatrix.cs | EnsurePackageOverrides |
| 281 | NewbieRunSetup.cs | Prepare |
| 282 | NewbieRunSetup.cs | ClearOnly |
| 283 | O1610BorderBake.cs | Run |
| 284 | ProjectBuild.cs | BuildWin64 |
| 285 | ProjectBuild.cs | PrepareScene |
| 286 | ProjectBuild.cs | ProbeMiniGame2 |
| 287 | ProjectBuild.cs | ProbeMiniGame3 |
| 288 | ProjectBuild.cs | ProbeMiniGame5 |
| 289 | ProjectBuild.cs | ProbeMiniGame4 |
| 290 | ProjectBuild.cs | ProbeMiniGame6 |
| 291 | ProjectBuild.cs | ProbeMiniGame7 |
| 292 | ProjectBuild.cs | EnsureAudioMonoImported |
| 293 | ProjectBuild.cs | ProbeU330AudioOverride |
| 294 | ProjectBuild.cs | ApplyAudioPackageMatrix |
| 295 | ProjectBuild.cs | BuildWeChatMiniGameProfile |
| 296 | ProjectBuild.cs | ProbeMiniGame |
| 297 | ProjectBuild.cs | BuildWeixinMiniGame |
| 298 | ProjectBuild.cs | ForceReimportBgmLongLoops |
| 299 | StoreAssetGen.cs | GenerateStoreIcon |
| 300 | FeelPulse.cs | Bind |
| 301 | FeelPulse.cs | Reset |
| 302 | FileAnalyticsService.cs | Report |
| 303 | FileAnalyticsService.cs | Flush |
| 304 | HiddenTreasureFlow.cs | ClearForTests |
| 305 | InLevelChoiceFlow.cs | ShouldOffer |
| 306 | InLevelChoiceFlow.cs | HandleLevelStarted |
| 307 | InLevelChoiceFlow.cs | HandleObjectCaptured |
| 308 | InLevelChoiceFlow.cs | HandleTimeRunningLow |
| 309 | InLevelChoiceFlow.cs | HandlePickRequested |
| 310 | InLevelChoiceFlow.cs | ApplyExtend |
| 311 | InLevelChoiceFlow.cs | HandleLevelCompleted |
| 312 | InLevelChoiceFlow.cs | HandleLevelFailed |
| 313 | InLevelChoiceFlow.cs | ResetForTests |
| 314 | LevelSupplyFlow.cs | PublishSnapshot |
| 315 | MetaService.Companion.cs | CompanionLevel |
| 316 | MetaService.Companion.cs | SetCompanionLevel |
| 317 | MetaService.Companion.cs | CompanionSeat |
| 318 | MetaService.Companion.cs | SetCompanionSeat |
| 319 | MetaService.Daily.cs | SetDailyDay |
| 320 | MetaService.Daily.cs | SetDailyTaskBits |
| 321 | MetaService.Daily.cs | LevelClearedOnce |
| 322 | MetaService.Daily.cs | MarkLevelCleared |
| 323 | MetaService.Daily.cs | LevelClearBits |
| 324 | MetaService.Daily.cs | ChestClaimedOnce |
| 325 | MetaService.Daily.cs | MarkChestClaimed |
| 326 | MetaService.Daily.cs | CodexFullHouseOnce |
| 327 | MetaService.Daily.cs | MarkCodexFullHouse |
| 328 | MetaService.Profile.cs | RebindProfileKeys |
| 329 | MetaService.Sand.cs | StageOf |
| 330 | MetaService.Sand.cs | AddSand |
| 331 | MetaService.Sand.cs | TrySpendSand |
| 332 | MetaService.Sand.cs | ItemCount |
| 333 | MetaService.Sand.cs | GrantItem |
| 334 | MetaService.Sand.cs | TryConsume |
| 335 | MetaService.Sand.cs | ChapterClearedOnce |
| 336 | MetaService.Sand.cs | MarkChapterCleared |
| 337 | MetaService.TestKeys.cs | WipeTestKeysForCurrentPrefix |
| 338 | MetaService.TestKeys.cs | UsePrefsKeyForTests |
| 339 | MetaService.cs | Install |
| 340 | MetaService.cs | Flush |
| 341 | MetaStore.cs | DeviceKey |
| 342 | MetaStore.cs | Flush |
| 343 | MetaStore.cs | StageOf |
| 344 | MetaStore.cs | AddSand |
| 345 | MetaStore.cs | TrySpendSand |
| 346 | MetaStore.cs | ItemCount |
| 347 | MetaStore.cs | GrantItem |
| 348 | MetaStore.cs | TryConsume |
| 349 | MetaStore.cs | ChapterClearedOnce |
| 350 | MetaStore.cs | MarkChapterCleared |
| 351 | MetaStore.cs | SetDailyDay |
| 352 | MetaStore.cs | SetDailyTaskBits |
| 353 | MetaStore.cs | LevelClearedOnce |
| 354 | MetaStore.cs | MarkLevelCleared |
| 355 | MetaStore.cs | LevelClearBits |
| 356 | MetaStore.cs | ChestClaimedOnce |
| 357 | MetaStore.cs | MarkChestClaimed |
| 358 | MetaStore.cs | CodexFullHouseOnce |
| 359 | MetaStore.cs | MarkCodexFullHouse |
| 360 | MetaStore.cs | CompanionLevel |
| 361 | MetaStore.cs | SetCompanionLevel |
| 362 | MetaStore.cs | CompanionSeat |
| 363 | MetaStore.cs | SetCompanionSeat |
| 364 | MetaStore.cs | WipeTestKeysForCurrentPrefix |
| 365 | MetaStore.cs | UsePrefsKeyForTests |
| 366 | OfflineEarningsFlow.cs | NowUnix |
| 367 | OfflineEarningsFlow.cs | ComputeAtBoot |
| 368 | OfflineEarningsFlow.cs | TryClaimBase |
| 369 | PreLevelChoiceFlow.cs | HandleLevelStarted |
| 370 | PreLevelChoiceFlow.cs | HandlePickRequested |
| 371 | PreLevelChoiceFlow.cs | HandleLevelCompleted |
| 372 | PreLevelChoiceFlow.cs | HandleLevelFailed |
| 373 | PreLevelChoiceFlow.cs | ResetForTests |
| 374 | ProfileReload.cs | InstallForTests |
| 375 | ProfileReload.cs | Rebind |
| 376 | ProfileRoster.cs | InstallForTests |
| 377 | ProfileRoster.cs | IntKeys |
| 378 | ProfileRoster.cs | StringKeys |
| 379 | RevealVeil.cs | AlphaForLevel |
| 380 | RevealVeil.cs | Cover |
| 381 | RevealVeil.cs | Lift |
| 382 | ShareLandingGate.cs | ResolveFromLaunch |
| 383 | ShareLandingGate.cs | TryParseLevelId |
| 384 | StationArt.cs | IsStationLevel |
| 385 | StationArt.cs | Scene |
| 386 | WeChatAnalyticsService.cs | Report |
| 387 | ActorDudu.cs | Ensure |
| 388 | ActorDudu.cs | SetTarget |
| 389 | ActorDudu.cs | PlaySignatureReaction |
| 390 | AmbushBeat.cs | EnabledFor |
| 391 | AmbushBeat.cs | ClearForTests |
| 392 | AmbushBeat.cs | RevealAllArmed |
| 393 | AmbushBeat.cs | Arm |
| 394 | AmbushBeat.cs | Reveal |
| 395 | BellyWindow.cs | Ensure |
| 396 | BellyWindow.cs | ApplyTowerCharge |
| 397 | BellyWindow.cs | FlightPos01 |
| 398 | BellyWindow.cs | OrbitOffset |
| 399 | BellyWindow.cs | Clamp01 |
| 400 | BellyWindow.cs | FillLocalY |
| 401 | BellyWindow.cs | TowerCenterY |
| 402 | BellyWindow.cs | ReadyPulseScale |
| 403 | BinZone.cs | Ensure |
| 404 | BinZone.cs | Hit |
| 405 | BinZone.cs | TypeKeyOf |
| 406 | CaptureBurst.cs | Spawn |
| 407 | CaptureBurst.cs | Spawn |
| 408 | CaptureBurst.cs | Spawn |
| 409 | CaptureBurst.cs | ParticlesFor |
| 410 | CaptureBurst.cs | Prewarm |
| 411 | CarryMouth.cs | Ensure |
| 412 | CarryMouth.cs | TryIntercept |
| 413 | ChapterEvolveFlow.cs | ChapterFor |
| 414 | ChapterEvolveFlow.cs | IsChapterFirstLevel |
| 415 | ChapterEvolveFlow.cs | EvolveNameFor |
| 416 | ChapterEvolveFlow.cs | RotationSlotOf |
| 417 | ChapterEvolveFlow.cs | ChapterMaterialFor |
| 418 | ChapterEvolveFlow.cs | SneezeRadiusFactorFor |
| 419 | ChapterEvolveFlow.cs | SweepBeatWindowFor |
| 420 | ChapterEvolveFlow.cs | HeavyCaptureMulFor |
| 421 | ChapterEvolveFlow.cs | SparkleGrantFor |
| 422 | ChapterEvolveFlow.cs | LickUnlockedFor |
| 423 | ChapterEvolveFlow.cs | HandleLevelStarted |
| 424 | ChapterEvolveFlow.cs | ResetForTests |
| 425 | ChapterFinale.cs | BossKeyFor |
| 426 | ChapterFinale.cs | ClearForTests |
| 427 | ChapterFinale.cs | Step |
| 428 | ChapterOnlooker.cs | ChapterOfLevel |
| 429 | ChapterOnlooker.cs | Cheer |
| 430 | ClusterMilestone.cs | Ensure |
| 431 | ClusterMilestone.cs | BuildClusters |
| 432 | EscapeBrake.cs | Note |
| 433 | EscapeBrake.cs | CountOf |
| 434 | GhostTarget.cs | HiddenAt |
| 435 | MimicTarget.cs | Setup |
| 436 | StickyTarget.cs | SpringPull |
| 437 | Front3Fx.cs | Ensure |
| 438 | Front3SuctionGrowth.cs | Ensure |
| 439 | FullChargeCeremony.cs | Ensure |
| 440 | GameplayDirtPalette.cs | TintOf |
| 441 | GameplayEscape.cs | Report |
| 442 | GameplaySpawnFactory.cs | Create |
| 443 | GrayscaleDriver.cs | Ensure |
| 444 | GrayscaleDriver.cs | SetGrey01 |
| 445 | GroundShadow.cs | Attach |
| 446 | GuideRing.cs | Attach |
| 447 | HitStop.cs | DurationFor |
| 448 | HitStop.cs | RequestCaptureStop |
| 449 | HitStop.cs | Request |
| 450 | HitStop.cs | Step |
| 451 | HitStop.cs | Reset |
| 452 | HitStop.cs | SetDeadlineForTests |
| 453 | JuiceCurves.cs | SpawnPop01 |
| 454 | JuiceCurves.cs | CapturePop01 |
| 455 | JuiceCurves.cs | InflateFor |
| 456 | JuiceCurves.cs | Breath |
| 457 | JuiceCurves.cs | StretchOf |
| 458 | JuiceCurves.cs | GulpRebound |
| 459 | LandmarkBeacon.cs | Polish |
| 460 | LandmarkBeacon.cs | Beckon |
| 461 | LevelScope.cs | SetForTests |
| 462 | PadInput.cs | Held |
| 463 | PadInput.cs | Down |
| 464 | PointVacuum.cs | CaptureNearest |
| 465 | ScratchTargets.cs | SetupKey |
| 466 | ScratchTargets.cs | ApplyBeatAt |
| 467 | ScratchTargets.cs | TickDecay |
| 468 | ScriptedPointer.cs | Drive |
| 469 | ScriptedPointer.cs | Release |
| 470 | ScriptedPointer.cs | TryRead |
| 471 | SignatureArt.cs | SpriteOf |
| 472 | SneezeSystem.cs | NeededFor |
| 473 | SneezeSystem.cs | Ensure |
| 474 | SneezeSystem.cs | AddCharge |
| 475 | SneezeSystem.cs | ResetCharge |
| 476 | SneezeSystem.cs | FillCharge |
| 477 | SpawnSpecTable.cs | Attach |
| 478 | SuctionField.cs | SetLockUpgradeEnabled |
| 479 | SuctionField.cs | BoostRadius |
| 480 | SuctionField.cs | SetActiveRadius |
| 481 | SuctionField.cs | SetStrengthMult |
| 482 | SuctionField.cs | SweepBeatReached |
| 483 | SuctionField.cs | TickLickDwell |
| 484 | SuctionTarget.cs | BeginEscape |
| 485 | SuctionTarget.cs | SetVertical |
| 486 | SuctionTarget.cs | ApplySuction |
| 487 | SuctionTarget.cs | ApplyBurst |
| 488 | SuctionTarget.cs | ApplyPull |
| 489 | SuctionTarget.cs | AttachGuideHalo |
| 490 | SuctionTarget.cs | Halt |
| 491 | SuctionTarget.cs | HaltAll |
| 492 | SuctionTarget.cs | HaltEscaping |
| 493 | SuctionTarget.cs | OnCaptured |
| 494 | SuctionTarget.cs | WriteSnapshot |
| 495 | SuctionTrail.cs | Emit |
| 496 | ChapterLore.cs | GetChapterTitle |
| 497 | ChapterLore.cs | GetNextChapterName |
| 498 | ChapterLore.cs | GetNextChapterTitle |
| 499 | ContentCatalog.cs | All |
| 500 | ContentCatalog.cs | IsVarietyKey |
| 501 | ContentCatalog.cs | IsGearKey |
| 502 | ContentCatalog.cs | Beat5BossKey |
| 503 | ContentCatalog.cs | IsScratchKey |
| 504 | ContentCatalog.cs | IsStationAbKey |
| 505 | ContentCatalog.cs | IsStationCdeKey |
| 506 | ContentCatalog.cs | IsSpawnKey |
| 507 | ContentCatalog.cs | CountWeightOf |
| 508 | ContentCatalog.cs | WeightOf |
| 509 | ContentCatalog.cs | VarietyPriceOf |
| 510 | ContentCatalog.cs | VarietyRebateOf |
| 511 | ContentCatalog.cs | IsSignatureKey |
| 512 | ContentCatalog.cs | SelfCheck |
| 513 | ContentCatalog.cs | BuildEmotionCurve |
| 514 | ContentCatalog.cs | BuildEmotionCurve |
| 515 | ContentCatalog.cs | ValidateEmotionCurve |
| 516 | ContentCatalog.cs | GetTheoreticalOptimalSec |
| 517 | ContentCatalog.cs | FamilyStation1 |
| 518 | ContentCatalog.cs | FamilyChallenge |
| 519 | ContentCatalog.cs | FamilyStationA |
| 520 | ContentCatalog.cs | FamilyStationB |
| 521 | DailyLevelPolicy.cs | ResolveDaily |
| 522 | ContentCatalogEditor.cs | Run |
| 523 | GoalTracker.cs | StarsFor |
| 524 | LevelCatalog.cs | Get |
| 525 | LevelProgressStore.cs | RebindForProfile |
| 526 | LevelProgressStore.cs | UsePrefsKeyForTests |
| 527 | LevelProgressStore.cs | Reset |
| 528 | LevelRules.cs | ResolveGoal |
| 529 | LevelRules.cs | GoalReached |
| 530 | LevelRules.cs | ShouldCountdown |
| 531 | LevelRules.cs | StepCountdown |
| 532 | LevelRunner.cs | StartLevel |
| 533 | LevelRunner.cs | StopLevel |
| 534 | LevelRunner.cs | LevelHasSweepStains |
| 535 | LevelRunner.cs | SpawnWave |
| 536 | LevelRunner.cs | SpawnOne |
| 537 | LevelSourceResolver.cs | SourceId |
| 538 | LevelSourceResolver.cs | Resolve |
| 539 | LevelSourceResolver.cs | WritesCampaignProgress |
| 540 | LevelTimer.cs | Extend |
| 541 | ParentKeyGuide.cs | ReadyFor |
| 542 | ParentKeyGuide.cs | Clear |
| 543 | ParentKeyGuide.cs | TryLight |
| 544 | ParentKeyGuide.cs | TryPauseClock |
| 545 | ParentKeyGuide.cs | TryPullTogether |
| 546 | ParentKeyGuide.cs | Tick |
| 547 | ParentKeyGuide.cs | ClearForTests |
| 548 | RemainderGuide.cs | MarkedAt |
| 549 | RemainderGuide.cs | Clear |
| 550 | RemainderGuide.cs | RefreshForSpawn |
| 551 | RemainderGuide.cs | ClearForTests |
| 552 | StationCatalog_Station1.cs | FamilyStation1 |
| 553 | StationCatalog_Station1.cs | FamilyChallenge |
| 554 | StationCatalog_StationA.cs | FamilyStationA |
| 555 | StationCatalog_StationB.cs | FamilyStationB |
| 556 | StationCatalog_StationC.cs | FamilyStationC |
| 557 | StationCatalog_StationD.cs | FamilyStationD |
| 558 | StationCatalog_StationE.cs | FamilyStationE |
| 559 | StationCatalog_StationF.cs | FamilyStationF |
| 560 | WaveDirector.cs | KindFor |
| 561 | WaveDirector.cs | EnabledFor |
| 562 | WaveDirector.cs | PeekStaggerForTests |
| 563 | WaveDirector.cs | Clear |
| 564 | WaveDirector.cs | BeginSession |
| 565 | WaveDirector.cs | CountGoalPieces |
| 566 | WaveDirector.cs | TickStagger |
| 567 | WaveDirector.cs | StepStaggerForTests |
| 568 | WaveDirector.cs | ClearForTests |
| 569 | GhostPlayback.cs | Bind |
| 570 | GhostPlayback.cs | LoadClip |
| 571 | GhostPlayback.cs | Clear |
| 572 | GhostPlayback.cs | Play |
| 573 | GhostPlayback.cs | Pause |
| 574 | GhostPlayback.cs | SetSpeed |
| 575 | PostcardComposer.cs | ComposePostcard |
| 576 | PosterComposer.cs | ComposePng |
| 577 | ReplayRecorder.cs | StartSession |
| 578 | ReplayRecorder.cs | MarkFailMoment |
| 579 | ReplayRecorder.cs | TryBuildSharePayload |
| 580 | ReplayRecorder.cs | GetFrameTrackCount |
| 581 | ReplayRecorder.cs | GetSnapshot |
| 582 | ReplayRecorder.cs | GetFrameTime |
| 583 | ReplayRecorder.cs | PickHighlightFrameIndex |
| 584 | ReplayRingMath.cs | ChronoOffsetOf |
| 585 | ReplayRingMath.cs | SlotOf |
| 586 | ReplayShareService.cs | ShareSupported |
| 587 | ReplayShareService.cs | SharePoster |
| 588 | ReplayShareService.cs | ShareReplay |
| 589 | WanderDot.cs | SpawnAt |
| 590 | WanderDot.cs | WriteSnapshot |
| 591 | WeChatShareService.cs | ShareSupported |
| 592 | WeChatShareService.cs | SharePoster |
| 593 | WeChatShareService.cs | ShareReplay |
| 594 | WeChatShareService.cs | ShareSupported |
| 595 | WeChatShareService.cs | SharePoster |
| 596 | WeChatShareService.cs | ShareReplay |
| 597 | ArenaAnchor.cs | Open |
| 598 | ArenaAnchor.cs | ReportScore |
| 599 | ArenaAnchor.cs | Close |
| 600 | CloudScoreParser.cs | TryParseScore |
| 601 | PersistentLeaderboardService.cs | BestScoreKey |
| 602 | PersistentLeaderboardService.cs | RebindKeyPrefix |
| 603 | PersistentLeaderboardService.cs | SubmitScore |
| 604 | PersistentLeaderboardService.cs | GetFriendScores |
| 605 | StubLeaderboardService.cs | SubmitScore |
| 606 | StubLeaderboardService.cs | GetFriendScores |
| 607 | TimeService.cs | NowUnixSeconds |
| 608 | WeChatLeaderboardService.cs | SubmitScore |
| 609 | WeChatLeaderboardService.cs | GetFriendScores |
| 610 | WeChatLeaderboardService.cs | ShowBoard |
| 611 | WeChatLeaderboardService.cs | HideBoard |
| 612 | WeChatLeaderboardService.cs | SubmitScore |
| 613 | WeChatLeaderboardService.cs | GetFriendScores |
| 614 | BVersionSevenShot.cs | Run |
| 615 | ChapterTurnCapture.cs | Run |
| 616 | DuduIdleShot.cs | Run |
| 617 | EditModeSpawnDrive.cs | DriveAllSpawned |
| 618 | EditModeSpawnDrive.cs | Drive |
| 619 | EditModeSpawnDrive.cs | DriveAllOnDisable |
| 620 | EntityProbeGate.cs | RunEntityProbe |
| 621 | FxGate.cs | RunFxLoop |
| 622 | HeadlessRunner.cs | RunAll |
| 623 | NewbieFlowCapture.cs | Run |
| 624 | O1610MenuShot.cs | Run |
| 625 | PlayLoopGate.cs | RunClosedLoop |
| 626 | SettlementCapture.cs | Run |
| 627 | SweepCapture.cs | Run |
| 628 | TestAdCopyFamilyFace.cs | Test_DefaultIsAdForm |
| 629 | TestAdCopyFamilyFace.cs | Test_FamilyIsMechanicallyPlain |
| 630 | TestAdCopyFamilyFace.cs | Test_OverrideRestores |
| 631 | TestAdPolicyFaceVisible.cs | Test_FaceVisibleTruthTable |
| 632 | TestAdPolicyFaceVisible.cs | Test_PropertyDelegatesToTruthTable |
| 633 | TestAds.cs | Test_AdConfigFrequencyConstants |
| 634 | TestAds.cs | Test_AdConfigRewardedPlacements |
| 635 | TestAds.cs | Test_RewardCatalogIntents |
| 636 | TestAds.cs | Test_AdGateResetAllowsInterstitial |
| 637 | TestAds.cs | Test_AdGateSessionCapBlocksAtThree |
| 638 | TestAds.cs | Test_AdGateCooldownBlocksIndependently |
| 639 | TestAds.cs | Test_AdGateResetRestoresAfterCap |
| 640 | TestAds.cs | Test_AdUnitConfigChannel |
| 641 | TestAdsMetrics.cs | Test_AutoBind_CountsByPlacement |
| 642 | TestAdsMetrics.cs | Test_NullPlacement_CountsTotalOnly |
| 643 | TestAdsMetrics.cs | Test_Reset_ZeroesTotalsAndPlacements |
| 644 | TestArtAssets.cs | Test_ChapterOnlookerBaseFramesLoad |
| 645 | TestArtAssets.cs | Test_ChapterOnlookerHomeExpressionFramesLoad |
| 646 | TestArtAssets.cs | Test_ChapterOnlookerHomeSadFrameKnownGapDegrades |
| 647 | TestArtAssets.cs | Test_ChapterOnlookerJapanExpressionFramesLoad |
| 648 | TestArtAssets.cs | Test_ChapterOnlookerParisExpressionFramesLoad |
| 649 | TestArtAssets.cs | Test_ChapterOnlookerEgyptExpressionFramesLoad |
| 650 | TestArtAssets.cs | Test_ChapterOnlookerForbiddenExpressionFramesLoad |
| 651 | TestArtAssets.cs | Test_ChapterOnlookerSpaceExpressionFramesLoad |
| 652 | TestArtAssets.cs | Test_ChapterOnlookerEmoteBadgesLoad |
| 653 | TestArtAssets.cs | Test_AmbientLoopBandSpritesLoad |
| 654 | TestArtAssets.cs | Test_AmbientLoopParticleSpritesLoad |
| 655 | TestArtAssets.cs | Test_BackgroundAnchorSpritesLoad |
| 656 | TestArtAssets.cs | Test_TargetAnchorSpritesLoad |
| 657 | TestArtAssets.cs | Test_EffectAnchorSpritesLoad |
| 658 | TestArtAssets.cs | Test_SignatureSpritesDegradeAware |
| 659 | TestArtAssets.cs | Test_DuduReactionFramesDegradeAware |
| 660 | TestArtAssets.cs | Test_UiIconSpritesDegradeAware |
| 661 | TestArtAssets.cs | Test_PropIconSpritesDegradeAware |
| 662 | TestArtAssets.cs | Test_UiPadSpritesLoad |
| 663 | TestArtAssets.cs | Test_DuduIdleFramesLoad |
| 664 | TestAudioAssets.cs | Test_W15AudioAssetsAllLoadable |
| 665 | TestAudioAssets.cs | Test_W19UiAndDuduClipsAllLoadable |
| 666 | TestAudioAssets.cs | Test_U320OperationsClipsAllLoadable |
| 667 | TestAudioAssets.cs | Test_BgmSeasonRouting |
| 668 | TestAudioAssets.cs | Test_CodexCryKeysComplete |
| 669 | TestAudioPackageMatrix.cs | Test_U330TierClassification |
| 670 | TestAudioPackageMatrix.cs | Test_U330PackageOverridesOnDisk |
| 671 | TestAudioPackageMatrix.cs | Test_U330FullAndSfxTiersUntouched |
| 672 | TestBellyMath.cs | Test_FlightEndpointsAndLift |
| 673 | TestBellyMath.cs | Test_FlightHorizontalApproachMonotonic |
| 674 | TestBellyMath.cs | Test_OrbitOnCircleAndDeterministic |
| 675 | TestBVersionChapterJourney.cs | Test_ChapterJourneyFaceBindsLiveData |
| 676 | TestBVersionChapterJourney.cs | Test_ChapterJourneyDisplayCensusCovers |
| 677 | TestBVersionChapterJourney.cs | Test_ChapterJourneyArtAssets |
| 678 | TestBVersionEntries.cs | Test_MenuBVersionEntriesWired |
| 679 | TestBVersionPortMap.cs | Test_BVersionPortMapIntact |
| 680 | TestBVersionPortMap.cs | Test_SkeletonScreensLazyLifecycle |
| 681 | TestBVersionStoreScreen.cs | Test_StoreFaceBindsLiveData |
| 682 | TestBVersionStoreScreen.cs | Test_StoreDisplayCensusCovers |
| 683 | TestBVersionStoreScreen.cs | Test_StoreArtAssets |
| 684 | TestBVersionStoreScreen.cs | Test_StorePurchaseWiringAndLiveRefresh |
| 685 | TestBVersionStoreScreen.cs | Test_StoreRejectFeedback |
| 686 | TestBVersionStoreScreen.cs | Test_StoreSeat2PurchaseChain |
| 687 | TestBVersionStoreScreen.cs | Test_StoreSeat2PoorWalletGuard |
| 688 | TestChainIntegration.cs | RewardedReady |
| 689 | TestChainIntegration.cs | ShowRewarded |
| 690 | TestChainIntegration.cs | ShowInterstitial |
| 691 | TestChainIntegration.cs | ShowBanner |
| 692 | TestChainIntegration.cs | SubmitScore |
| 693 | TestChainIntegration.cs | GetFriendScores |
| 694 | TestChainIntegration.cs | Test_G27Chain_StartRequest_PublishesLevelStartedAndSpawnsTargets |
| 695 | TestChainIntegration.cs | Test_G27Chain_CaptureAll_CompletesWithSingleInterstitialAndScore |
| 696 | TestChainIntegration.cs | Test_G27Chain_WithReplayRecorder_RecordsAllCaptures |
| 697 | TestChapterChest.cs | Test_ChapterChestProgressDedupeAndClaimGuard |
| 698 | TestChapterChest.cs | Test_ChapterChestChapterIsolationAndFocusSnapshot |
| 699 | TestChapterChest.cs | Test_ChapterChestPersistenceAcrossRestart |
| 700 | TestChapterChestUi.cs | Test_ChapterChestUiRequestChannelAndCapsuleFaces |
| 701 | TestChapterChestUi.cs | Test_ChapterChestScreenModalFlow |
| 702 | TestChapterEvolveFlow.cs | Test_EvolveMomentExactlyOnChapterFirstLevels |
| 703 | TestChapterEvolveFlow.cs | Test_BuffsOnlyAddNeverReduce |
| 704 | TestChapterEvolveFlow.cs | Test_HeavyCaptureHotPathChapterMul |
| 705 | TestChapterEvolveFlow.cs | Test_SweepBeatWindowChapterSlot |
| 706 | TestChapterEvolveFlow.cs | Test_ChapterMaterialVariantTable |
| 707 | TestChapterEvolveFlow.cs | Test_EvolveComboNameIndependence |
| 708 | TestChapterEvolveFlow.cs | Test_EvolveNameBusCarriesMaterialChapters |
| 709 | TestCheckIn.cs | Test_CheckInLadderDoublingAndCap |
| 710 | TestCheckIn.cs | Test_CheckInBreakDoesNotReset |
| 711 | TestCheckIn.cs | Test_CheckInRequestChannelAndMenuSnapshot |
| 712 | TestCheckInUi.cs | Test_CheckInStripStatesAndClaimChain |
| 713 | TestCheckInUi.cs | Test_CheckInStripCapFaceAcrossDays |
| 714 | TestCodexAccel.cs | Test_CodexAccelOneAwayGrantAndGuards |
| 715 | TestCodexAccel.cs | Test_CodexAccelRefreshAnchorsAndCrossLock |
| 716 | TestCodexAccel.cs | Test_CodexAccelPersistence |
| 717 | TestCodexAccelUi.cs | RewardedReady |
| 718 | TestCodexAccelUi.cs | ShowRewarded |
| 719 | TestCodexAccelUi.cs | ShowInterstitial |
| 720 | TestCodexAccelUi.cs | ShowBanner |
| 721 | TestCodexAccelUi.cs | Test_CodexAccelUiFaces |
| 722 | TestCodexCatalog.cs | Test_CodexEntriesCompleteAndNonEmpty |
| 723 | TestCodexCatalog.cs | Test_CodexChapterCoverageIsExact |
| 724 | TestCodexCatalog.cs | Test_CodexChapterNamesVerbatim |
| 725 | TestCodexCatalog.cs | Test_CodexUnlockBoundaries |
| 726 | TestCodexCatalog.cs | Test_CodexProgressLineStates |
| 727 | TestCodexCatalog.cs | Test_CodexProgressLineNamesTheMissingOne |
| 728 | TestCodexFlow.cs | Test_CodexFlowFullHouseGrantIdempotent |
| 729 | TestCodexFlow.cs | Test_CodexFlowMenuAnchorAndRosterCrossLock |
| 730 | TestCodexUi.cs | Test_CodexPreviewLineStates |
| 731 | TestCodexUi.cs | Test_CodexScreenRevealBookkeeping |
| 732 | TestCodexUi.cs | Test_CodexRetainMarkLitByChapterKey |
| 733 | TestCodexUi.cs | Test_CodexRetainMarkUnlitKeepsPill |
| 734 | TestCompanionAds.cs | Test_PlacementCatalogTrioRegistered |
| 735 | TestCompanionAds.cs | Test_TrialArmGuardsPersistDailyCap |
| 736 | TestCompanionAds.cs | Test_TrialResolveAndConsumeChain |
| 737 | TestCompanionAds.cs | Test_RechargeFillGuardsAndRestore |
| 738 | TestCompanionFace.cs | Test_RosterFaceSpritesAll24Imported |
| 739 | TestCompanionFace.cs | Test_HudCompanionFaceRingAndStates |
| 740 | TestCompanionFamilies2.cs | Test_PointVacuumRespectsGhostHiddenWindow |
| 741 | TestCompanionFamilies2.cs | Test_HaltAllFreezesBubbleAutonomousDrift |
| 742 | TestCompanionFamilies2.cs | Test_PointVacuumChainsSplitterRupture |
| 743 | TestCompanionQi2b.cs | Test_HaltEscapingFreezesOnlyDrifting |
| 744 | TestCompanionQi2b.cs | Test_HaltAllFreezesLiveTargetsOnly |
| 745 | TestCompanionQi2b.cs | Test_PointVacuumNearestAndHonestShortfall |
| 746 | TestCompanionQi2b.cs | Test_PointVacuumEventPayloadMatchesTarget |
| 747 | TestCompanionRoster.cs | Test_RosterCompleteAndWellFormed |
| 748 | TestCompanionRoster.cs | Test_VersionSplitTwelveAndTwelve |
| 749 | TestCompanionRoster.cs | Test_ChapterSeatsExactlyTwoPerChapter |
| 750 | TestCompanionRoster.cs | Test_AllSevenSkillKindsCoveredPerVersion |
| 751 | TestCompanionRoster.cs | Test_DesignTableBindingsLocked |
| 752 | TestCompanionRoster.cs | Test_SkillParamsWithinDesignEnvelope |
| 753 | TestCompanionRoster.cs | Test_ProgressChargeCurve |
| 754 | TestCompanionRoster.cs | Test_ProgressUpgradeAndPowerCurve |
| 755 | TestCompanionRoster.cs | Test_UnlockChainChapterEndLevels |
| 756 | TestCompanionRosterUi.cs | Test_RosterZoneTabsAndCardCount |
| 757 | TestCompanionRosterUi.cs | Test_SeatRequestUiRoundTrip |
| 758 | TestCompanionRosterUi.cs | Test_UpgradeRequestUiRoundTrip |
| 759 | TestCompanionRosterUi.cs | Test_SnapshotOpenSyncsEffectiveSeat |
| 760 | TestCompanionRosterUi.cs | RewardedReady |
| 761 | TestCompanionRosterUi.cs | ShowRewarded |
| 762 | TestCompanionRosterUi.cs | ShowInterstitial |
| 763 | TestCompanionRosterUi.cs | ShowBanner |
| 764 | TestCompanionRosterUi.cs | Test_Seat2BannerVideoRoundTrip |
| 765 | TestCompanionRosterUi.cs | Test_Seat2BannerReceiptAndLayoutLock |
| 766 | TestCompanionRuntime.cs | Test_ChargeFsmLifecycle |
| 767 | TestCompanionRuntime.cs | Test_ShieldLifecycleOneShot |
| 768 | TestCompanionRuntime.cs | Test_PrimarySeatReadyFamilyFirst |
| 769 | TestCompanionSeat.cs | Test_SeatPersistenceRoundTripAndBounds |
| 770 | TestCompanionSeat.cs | Test_ResolveSeatExplicitWinsAndFallbacks |
| 771 | TestCompanionSeat.cs | Test_TrySetSeatGuardsAndBroadcast |
| 772 | TestCompanionSeat2.cs | Test_Seat2UnlockedMatrix |
| 773 | TestCompanionSeat2.cs | Test_Seat2VideoGrantChain |
| 774 | TestCompanionSeat2.cs | Test_Seat2StardustPermanentPath |
| 775 | TestCompanionSeat2.cs | Test_Seat2DualSeatResolution |
| 776 | TestCompanionUpgrade.cs | Test_UpgradeTransactionGuardsAndOrdering |
| 777 | TestCompanionUpgrade.cs | Test_CompanionLevelPersistenceAndDirtySaveClamp |
| 778 | TestCompanionUpgrade.cs | Test_UpgradeBroadcastsBothEvents |
| 779 | TestCopyPools.cs | Test_SharePoolsCopyLocked |
| 780 | TestCopyPools.cs | Test_SharePoolGatesAndDraws |
| 781 | TestCopyPools.cs | Test_DailyFormDeterministic |
| 782 | TestCopyPools.cs | Test_PostcardProgressMapping |
| 783 | TestCopyPools.cs | Test_HarvestTopRules |
| 784 | TestCopyPools.cs | Test_DailyFocusLines |
| 785 | TestCopyPools.cs | Test_DailyMenuLinePick |
| 786 | TestCoreBus.cs | Test_BusSubscribePublishDelivers |
| 787 | TestCoreBus.cs | Test_BusStructDefaultsZero |
| 788 | TestCoreBus.cs | Test_BusReverseDispatchOrder |
| 789 | TestCoreBus.cs | Test_BusUnsubscribeDuringPublish |
| 790 | TestCoreBus.cs | Test_BusClearAllStopsDelivery |
| 791 | TestCoreBus.cs | Test_BusTypeIsolation |
| 792 | TestCoreJsonState.cs | Test_LevelJsonRoundtripAllFields |
| 793 | TestCoreJsonState.cs | Test_LevelJsonEmptyInputSafe |
| 794 | TestCoreJsonState.cs | Test_StateMachineSetFiresEventWithPrevNext |
| 795 | TestCoreJsonState.cs | Test_StateMachineSameStateSilent |
| 796 | TestCoreJsonState.cs | Test_StateMachineEnumHasSixStates |
| 797 | TestCoreJsonState.cs | Test_StateMachineResetToBoot |
| 798 | TestCoreRegistry.cs | WriteSnapshot |
| 799 | TestCoreRegistry.cs | ApplySuction |
| 800 | TestCoreRegistry.cs | ApplyBurst |
| 801 | TestCoreRegistry.cs | OnCaptured |
| 802 | TestCoreRegistry.cs | Create |
| 803 | TestCoreRegistry.cs | Test_ObjectRegistryRegisterUnregister |
| 804 | TestCoreRegistry.cs | Test_ObjectRegistryNextIdMonotonic |
| 805 | TestCoreRegistry.cs | Test_ObjectRegistryCopyActiveTruncates |
| 806 | TestCoreRegistry.cs | Test_SpawnRegistryFactoryLifecycle |
| 807 | TestCoreRegistry.cs | Test_ObjectPoolAcquireReleaseReuse |
| 808 | TestCoreRegistry.cs | Test_PlaceholderSpriteFactoryCache |
| 809 | TestDailyTask.cs | Test_DailyTaskProgressClaimAndHotPathGuard |
| 810 | TestDailyTask.cs | Test_DailyTaskResetAcrossDays |
| 811 | TestDailyTask.cs | Test_DailyTaskPersistenceAndMenuSnapshot |
| 812 | TestDailyTaskUi.cs | Test_DailyTaskUiRequestChannelAndCounters |
| 813 | TestDailyTaskUi.cs | Test_DailyTaskScreenModalFlow |
| 814 | TestDoubleReward.cs | Test_DoubleGrantsLevelSandTwice |
| 815 | TestDoubleReward.cs | Test_DoubleRearmsOnNextSettlement |
| 816 | TestDoubleReward.cs | Test_DoubleIgnoresOtherPlacementsAndZeroSand |
| 817 | TestDoubleReward.cs | Test_ReviveAttributionFunnel |
| 818 | TestDoubleReward.cs | Report |
| 819 | TestEmotionCurve.cs | Test_EmotionCurveCovers90Levels |
| 820 | TestEmotionCurve.cs | Test_EmotionCurveChapterDoublePeak |
| 821 | TestEmotionCurve.cs | Test_EmotionCurveNoTripleLowNovelty |
| 822 | TestEmotionCurve.cs | Test_EmotionCurveSpecAnchorsChapterOne |
| 823 | TestEmotionCurve.cs | Test_EmotionCurveValidationClean |
| 824 | TestEvolveRitualFrame.cs | Test_ComposeEvolveLineFormatChapters |
| 825 | TestEvolveRitualFrame.cs | Test_RitualSharesBannerEnvelope |
| 826 | TestEvolveRitualFrame.cs | Test_EvolveNameCarriedOnBusEvent |
| 827 | TestEvolveRitualFrame.cs | Test_BannerMergesRitualBothOrders |
| 828 | TestEvolveRitualFrame.cs | Test_EvolveLineTypographyStepDown |
| 829 | TestFeatherRevive.cs | Test_FeatherReviveConsumesAndReenters |
| 830 | TestFeatherRevive.cs | Test_FeatherReviveRejectsWithoutStock |
| 831 | TestFeatherRevive.cs | Test_FeatherMirrorReadsSameKey |
| 832 | TestFiveBeats.cs | Test_Beat2AmbushHideAndReveal |
| 833 | TestFiveBeats.cs | Test_Beat3LandmarkPolishExactlyOnce |
| 834 | TestFiveBeats.cs | Test_Beat4DualFamilyOnLevel4 |
| 835 | TestFiveBeats.cs | Test_Beat4DualFamilyReplicatedCh2ToCh6 |
| 836 | TestFiveBeats.cs | Test_Beat5FinaleExactlyOnce |
| 837 | TestFiveBeats.cs | Test_BeatDomainS3Replication |
| 838 | TestFiveBeats.cs | Test_Beat2AmbushReplicatedCh3 |
| 839 | TestFiveBeats.cs | Test_Beat5FinaleReplicatedCh3ToCh6 |
| 840 | TestFont.cs | Test_CnFontAssetLoadsFromResources |
| 841 | TestFont.cs | Test_CnFontCoversKeyGlyphs |
| 842 | TestFont.cs | Test_GlyphSetReportExists |
| 843 | TestFont.cs | Test_DisplayFontAssetLoadsFromResources |
| 844 | TestFont.cs | Test_DisplayFontCoversKeyGlyphs |
| 845 | TestFont.cs | Test_DisplayFontSubsetBudgetHeld |
| 846 | TestGameplayCapture.cs | Test_DustVariantIdentity |
| 847 | TestGameplayCapture.cs | Test_DustRecordIdSequence |
| 848 | TestGameplayCapture.cs | Test_DustApplySuctionAccumulates |
| 849 | TestGameplayCapture.cs | Test_DustOnCapturedFreezesState |
| 850 | TestGameplayCapture.cs | Test_DustRegistryLifecycle |
| 851 | TestGameplayCapture.cs | Test_DustSnapshotContract |
| 852 | TestInLevelChoiceFlow.cs | Test_OfferGate_LowTimeAndClearBelowGate_OncePerLevel |
| 853 | TestInLevelChoiceFlow.cs | Test_OfferGate_ClearAtOrAboveGoal_NoOffer |
| 854 | TestInLevelChoiceFlow.cs | Test_PickGamble_ArmsAndSettlesPlusFifteenSand |
| 855 | TestInLevelChoiceFlow.cs | Test_PickGamble_FailLosesBet_NoPenalty_NoFreeRide |
| 856 | TestInLevelChoiceFlow.cs | Test_PickExtend_GateMirrorRejectionAndRefund |
| 857 | TestInLevelChoiceFlow.cs | Test_ApplyExtend_ActiveRunnerTimer_PlusTenSeconds |
| 858 | TestJuiceCurves.cs | Test_SpawnPopEndpointsAndOvershoot |
| 859 | TestJuiceCurves.cs | Test_CapturePopBumpThenSettle |
| 860 | TestJuiceCurves.cs | Test_InflateForMonotonicAndClamped |
| 861 | TestJuiceCurves.cs | Test_BreathEnvelope |
| 862 | TestJuiceCurves.cs | Test_StretchOfEndpointsAndClamp |
| 863 | TestJuiceCurves.cs | Test_GulpReboundEnvelope |
| 864 | TestLevelRules.cs | Test_ResolveGoal_MinusOneFallsBackToTotal |
| 865 | TestLevelRules.cs | Test_ResolveGoal_ZeroFallsBackToTotal |
| 866 | TestLevelRules.cs | Test_ResolveGoal_GoalAboveTotalPassesThrough |
| 867 | TestLevelRules.cs | Test_ResolveGoal_PlainGoalPassesThrough |
| 868 | TestLevelRules.cs | Test_GoalReached_NonPositiveGoalAlwaysFalse |
| 869 | TestLevelRules.cs | Test_GoalReached_AtGoalTrueBelowFalse |
| 870 | TestLevelRules.cs | Test_ShouldCountdown_OnlyPositiveLimitCounts |
| 871 | TestLevelRules.cs | Test_StepCountdown_DecrementsInPlaceUntilZero |
| 872 | TestLevels.cs | Test_CatalogCountIsThree |
| 873 | TestLevels.cs | Test_CatalogL1DustOnlyAllClear |
| 874 | TestLevels.cs | Test_CatalogL2DustFurMix |
| 875 | TestLevels.cs | Test_CatalogL3DebrisHeaviest |
| 876 | TestLevels.cs | Test_CatalogGetOutOfBoundsNull |
| 877 | TestLevels.cs | Test_CatalogGetReturnsDeepCopy |
| 878 | TestLevels.cs | Test_CatalogAllLevelsCommonValid |
| 879 | TestLevels.cs | Test_CatalogRoundtripAllLevels |
| 880 | TestLevels.cs | Test_DailyPolicyDeterministicInRange |
| 881 | TestLevels.cs | Test_DailyPolicyEdgeCases |
| 882 | TestLevels.cs | ApplySuction |
| 883 | TestLevels.cs | ApplyBurst |
| 884 | TestLevels.cs | OnCaptured |
| 885 | TestLevels.cs | Create |
| 886 | TestLevels.cs | Test_RunnerStopLevelClearsWholeScene |
| 887 | TestLevelSupply.cs | Test_SupplyArmClaimLapseGuards |
| 888 | TestLevelSupply.cs | Test_SupplyDailyCapAndRollover |
| 889 | TestLevelSupply.cs | Test_SupplyPersistenceAndSnapshotRequest |
| 890 | TestLevelSupplyUi.cs | RewardedReady |
| 891 | TestLevelSupplyUi.cs | ShowRewarded |
| 892 | TestLevelSupplyUi.cs | ShowInterstitial |
| 893 | TestLevelSupplyUi.cs | ShowBanner |
| 894 | TestLevelSupplyUi.cs | Test_SupplyDefeatFaceFullFlow |
| 895 | TestLevelSupplyUi.cs | Test_SupplyMenuChipFaces |
| 896 | TestLevelTimerRearm.cs | Test_TimeoutFail_Extend_RearmsCountdownWithBoughtSeconds |
| 897 | TestLevelTimerRearm.cs | Test_Fail_ExtendZeroOrNegative_IsIgnored_NoRearm |
| 898 | TestLevelTimerRearm.cs | Test_FirstPressGrace_GuidedLevels_ThenPressedAndReamed |
| 899 | TestMetaProgress.cs | Test_MetaStageBoundaries |
| 900 | TestMetaProgress.cs | Test_MetaSandAccrualAndStageGrants |
| 901 | TestMetaProgress.cs | Test_MetaItemConsumeAndRefuse |
| 902 | TestMetaProgress.cs | Test_MetaChapterFlagsOnce |
| 903 | TestMetaProgress.cs | Test_WardrobeUnlockBoundaries |
| 904 | TestMetaProgress.cs | Test_MetaScaleMirrorZeroDrift |
| 905 | TestNewbieAttraction.cs | Test_SneezeChargeTier_GuidedLevels |
| 906 | TestNewbieAttraction.cs | Test_VeilAlphaTier_ByChapter |
| 907 | TestNewbieAttraction.cs | Test_ClusterBuild_LinkDistance |
| 908 | TestO1610WelcomeBand.cs | Test_WelcomeBandSlotGeometryAndYield |
| 909 | TestOfflineEarnings.cs | Test_OfflineAccrueCapAndGuards |
| 910 | TestOfflineEarnings.cs | Test_OfflineClaimDoubleAndRejects |
| 911 | TestOfflineEarnings.cs | Test_OfflineSnapshotHeartbeatPersistence |
| 912 | TestOfflineEarningsUi.cs | Test_OfflinePopupFaces |
| 913 | TestOfflineEarningsUi.cs | Test_OfflinePopupModalClaimFlow |
| 914 | TestPaywallGate.cs | Test_Judge_NeedsExactlyTwoDigits |
| 915 | TestPaywallGate.cs | Test_Judge_RejectsNonDigits |
| 916 | TestPaywallGate.cs | Test_Judge_EveryLegalPairIsTwoDigitSum |
| 917 | TestPaywallGate.cs | Test_NextQuestion_InRangeAndNeverRepeats |
| 918 | TestPaywallGate.cs | Test_NextQuestion_NullRngIsSafe |
| 919 | TestPaywallGate.cs | Test_DrivingLocked_ProbeWinsAndFailsSafe |
| 920 | TestPaywallGate.cs | Test_CanOpenNow_RespectsGameStateAndDriving |
| 921 | TestPaywallGate.cs | Test_CanOpenNow_AutoEntryNeedsOptIn |
| 922 | TestPaywallGate.cs | Test_Retention_OwnedSkipsPaywall |
| 923 | TestPaywallGate.cs | Test_Retention_FirstPostcardFreeIsSingleUse |
| 924 | TestPaywallGate.cs | Test_Retention_BlockedPathNeverMarksRetained |
| 925 | TestPaywallGate.cs | Test_Retention_PaidAfterPaywallMarksRetained |
| 926 | TestPaywallGate.cs | Test_Retention_ReceiptDerivedFromKey |
| 927 | TestPaywallGate.cs | Test_GuestFace_SeesNoPaywallAndSpendsNoCredential |
| 928 | TestPaywallGate.cs | Test_Geometry_PillAndTapFloorArePinned |
| 929 | TestPaywallGate.cs | Test_Retention_ChapterKeyIsUnit |
| 930 | TestPaywallGate.cs | Test_Retention_LegacyLevelKeyMigrates |
| 931 | TestPaywallGate.cs | Test_StubCommerce_ValidateCodeRule |
| 932 | TestPersistence.cs | SubmitScore |
| 933 | TestPersistence.cs | GetFriendScores |
| 934 | TestPersistence.cs | SubmitScore |
| 935 | TestPersistence.cs | GetFriendScores |
| 936 | TestPersistence.cs | Test_PersistedBestNeverFalls |
| 937 | TestPersistence.cs | Test_MergeInjectsAndElevatesSelf |
| 938 | TestPersistence.cs | Test_NullInnerStillPersists |
| 939 | TestPersistence.cs | Test_ProgressStoreClampsAndMonotonic |
| 940 | TestPersistence.cs | Test_PlayerPrefsKeysStayIsolated |
| 941 | TestPrewarmWiring.cs | Test_CaptureBurst_AutoBind_MenuEvent_PrewarmsHost |
| 942 | TestPrewarmWiring.cs | Test_SfxFlow_BindPrewarms_ResetClears_RebindPrewarmsAgain |
| 943 | TestProductFx.cs | Test_ButtonPressHoldCurve |
| 944 | TestProductFx.cs | Test_ButtonReboundOvershootExact |
| 945 | TestProductFx.cs | Test_PopCurveOvershootEnvelope |
| 946 | TestProductFx.cs | Test_FlashEnvelope |
| 947 | TestProductFx.cs | Test_NumberRollEasing |
| 948 | TestProductFx.cs | Test_FlyBezierArcUpward |
| 949 | TestProfileScope.cs | Test_SlotZeroIdentity |
| 950 | TestProfileScope.cs | Test_SlotNShape |
| 951 | TestProfileScope.cs | Test_SlotGuardRejectsOutOfRange |
| 952 | TestProfileScope.cs | Test_NonRootKeysPassThrough |
| 953 | TestProfileScope.cs | Test_DeviceLevelKeysAreDeclared |
| 954 | TestProfileScope.cs | Test_ClaimGuest_MovesEveryKeyAndSwitchesSlot |
| 955 | TestProfileScope.cs | Test_ClaimGuest_LeavesNoGuestKeysAndInventsNone |
| 956 | TestProfileScope.cs | Test_ClaimGuest_RollsBackOnVerifyFailure |
| 957 | TestProfileScope.cs | Test_ClaimGuest_ReportsSlotFullWithoutTouchingAnySlot |
| 958 | TestProfileScope.cs | Test_ClaimGuest_RefusesWithoutRoster |
| 959 | TestProfileScope.cs | Test_ClaimGuest_RecoversPendingMarker |
| 960 | TestProfileScope.cs | Test_ProductionRosterShape |
| 961 | TestProfileScope.cs | Test_DeleteProfile_RemovesEveryKeyInSlot |
| 962 | TestProfileScope.cs | Test_DeleteProfile_RefusesGuestAndOutOfRange |
| 963 | TestProfileScope.cs | Test_DeleteProfile_RefusesWithoutRoster |
| 964 | TestProfileScope.cs | Test_DeleteProfile_FallsBackToGuestWhenActive |
| 965 | TestProfileScope.cs | Test_DeleteProfile_ClearsStaleClaimMarker |
| 966 | TestProfileScope.cs | Test_DeleteProfile_OccupationSharedWithClaim |
| 967 | TestProfileScope.cs | Test_Switch_RefusesOutOfRange |
| 968 | TestProfileScope.cs | Test_Switch_RefusesEmptyNamedSlot |
| 969 | TestProfileScope.cs | Test_Switch_RefusesWithoutRebindHost |
| 970 | TestProfileScope.cs | Test_Switch_SameSlotIsNoOp |
| 971 | TestProfileScope.cs | Test_Switch_RecoversPendingClaimBeforeSwitching |
| 972 | TestProfileScope.cs | Test_ReloadActive_AfterDeleteOfActiveSlot |
| 973 | TestProfileScope.cs | Test_ReloadActive_RefusesWithoutRebindHost |
| 974 | TestProfileScope.cs | Test_ReloadActive_DoesNotMoveTheSlot |
| 975 | TestRemainderGuide.cs | Test_ActivatesAtTailAndClearsOnClose |
| 976 | TestRemainderGuide.cs | Test_ZeroWeightPropHiddenFromGuide |
| 977 | TestReplayMath.cs | Test_ChronoOffsetOf_HeadMinusValidFrames |
| 978 | TestReplayMath.cs | Test_ChronoOffsetOf_FullRingIsZero |
| 979 | TestReplayMath.cs | Test_ChronoOffsetOf_WrapNeverNegative |
| 980 | TestReplayMath.cs | Test_SlotOf_WrapsAroundRing |
| 981 | TestReplayMath.cs | Test_PickHighlightFrameIndex_Guards |
| 982 | TestReplayMath.cs | Test_PickHighlightFrameIndex_MostSuckedWinsTieTakesLater |
| 983 | TestReplayPoster.cs | Test_PosterComposeValidPng |
| 984 | TestReplayPoster.cs | Test_PosterEdgeInputsStayValid |
| 985 | TestReplayPoster.cs | Test_PosterSizeMatchesConfig |
| 986 | TestReplayPoster.cs | Test_PosterTempFileRoundtrip |
| 987 | TestReviveRearm.cs | Test_ReviveRearmsGoalTracker |
| 988 | TestSfxFamilySounds.cs | Test_SfxFlow_FamilyKeys_RouteToOwnClip |
| 989 | TestSfxSynthClips.cs | Test_SynthClips_CreateArgOrder_ChannelsFrequency |
| 990 | TestShareLanding.cs | Test_ParseValidLevelIds |
| 991 | TestShareLanding.cs | Test_RejectsUntrustedInput |
| 992 | TestShareLanding.cs | Test_RejectsZeroAndOverflow |
| 993 | TestShareLanding.cs | Test_LandingLineVerbatimAndRedLines |
| 994 | TestSignatureLevels.cs | Test_SignatureOnePerNewbieLevel |
| 995 | TestSignatureLevels.cs | Test_SignatureTimingUnfailable |
| 996 | TestSignatureLevels.cs | Test_SignatureSpawnsInBounds |
| 997 | TestSignatureLevels.cs | Test_SignatureInjectionDeterministic |
| 998 | TestSignatureLevels.cs | Test_SignatureWhitelistExcludesFuzz |
| 999 | TestSignatureLevels.cs | Test_FuzzHillBandMirrorMatchesCatalog |
| 1000 | TestSocial.cs | Test_StubSubmitKeepsBestScore |
| 1001 | TestSocial.cs | Test_StubFriendScoresDefaultAnchor |
| 1002 | TestSocial.cs | Test_StubFriendScoresCenterOnSelf |
| 1003 | TestSocial.cs | Test_StubScoresClampAtZero |
| 1004 | TestSocial.cs | Test_TimeServiceUnixSecondsUtcWindow |
| 1005 | TestSocial.cs | Test_ArenaAnchorShapeLock |
| 1006 | TestSocialCloud.cs | Test_TryParseScore_ValidPayloadParsesScore |
| 1007 | TestSocialCloud.cs | Test_TryParseScore_ZeroScoreIsValid |
| 1008 | TestSocialCloud.cs | Test_TryParseScore_MissingScoreFieldFails |
| 1009 | TestSocialCloud.cs | Test_TryParseScore_NotJsonFails |
| 1010 | TestSocialCloud.cs | Test_TryParseScore_NullInputFails |
| 1011 | TestSocialCloud.cs | Test_TryParseScore_EmptyStringFails |
| 1012 | TestStoreAds.cs | Test_VaultAccruesToCapAndBreakGrants960 |
| 1013 | TestStoreAds.cs | Test_VaultRejectsWhenNotFull |
| 1014 | TestStoreAds.cs | Test_ShopSandDailyCap |
| 1015 | TestStoreFlow.cs | Test_StorePurchaseSettlesBundle |
| 1016 | TestStoreFlow.cs | Test_StorePurchaseRefundsWhenShort |
| 1017 | TestStoreFlow.cs | Test_StorePurchaseSingleOffersAndUnknown |
| 1018 | TestStoreFlow.cs | Test_MetaMilestoneSpendsNeverShrinkStage |
| 1019 | TestSuctionFamilies.cs | Test_VarietyKeysRegistered |
| 1020 | TestSuctionFamilies.cs | Test_VarietyKeyConstantsMatchFactory |
| 1021 | TestSuctionFamilies.cs | Test_CountWeightingAndPrices |
| 1022 | TestSuctionFamilies.cs | Test_VarietyInjectionCoverage |
| 1023 | TestSuctionFamilies.cs | Test_VarietyFrontLoadMonotonePricing |
| 1024 | TestSuctionFamilies.cs | Test_GoldenFirstLevelContract |
| 1025 | TestSuctionFamilies.cs | Test_VarietyRebateKeepsMargin |
| 1026 | TestSuctionFamilies.cs | Test_ChapterTintsApplied |
| 1027 | TestSuctionFamilies.cs | Test_DirtPaletteBoundsAndDistinct |
| 1028 | TestSuctionFamilies.cs | Test_PlayBandMirrorMatchesCatalog |
| 1029 | TestSuctionFamilies.cs | Test_GhostPhaseMath |
| 1030 | TestSuctionFamilies.cs | Test_StickySpringPull |
| 1031 | TestSuctionFamilies.cs | Test_FamilyConstantsLock |
| 1032 | TestSuctionFamilies.cs | Test_GhostEngagedNeverBlocked |
| 1033 | TestSuctionFamilies.cs | Test_MimicDisguiseAndReveal |
| 1034 | TestSuctionFamilies.cs | Test_FactoryTintAndGearApplied |
| 1035 | TestSuctionFamilies.cs | Test_SplitterTotalWeightingAndSweep |
| 1036 | TestSuctionFamilies.cs | Test_ContentSelfCheckAllGreen |
| 1037 | TestSweepVerb.cs | Test_SweepBeatBoundaryLocks |
| 1038 | TestSweepVerb.cs | Test_ScratchThreeBeatsClear |
| 1039 | TestSweepVerb.cs | Test_ScratchDecayDwelling |
| 1040 | TestSweepVerb.cs | Test_ScratchZeroWeightNotInTotals |
| 1041 | TestSystemUnlocks.cs | Test_GateIdempotentMarkAndBits |
| 1042 | TestSystemUnlocks.cs | Test_UnlockTableOnLevelComplete |
| 1043 | TestSystemUnlocks.cs | Test_FirstChestOnFifteenCaptures |
| 1044 | TestSystemUnlocks.cs | Test_DeadTaskRetargetLock |
| 1045 | TestSystemUnlocks.cs | Test_MenuGatesNewPlayerSurface |
| 1046 | TestTutorialHint.cs | Test_TutorialHintKeysAndFlags |
| 1047 | TestU351BankCleanup.cs | Test_DeadIconsRetired |
| 1048 | TestU351BankCleanup.cs | Test_ConsumedIconPairLive |
| 1049 | TestU351BottomRhythm.cs | Test_PaperEdgeExtendsBelowBanner |
| 1050 | TestU351BottomRhythm.cs | Test_RhythmSecondaryRow180Gap30 |
| 1051 | TestU351BottomRhythm.cs | Test_PaletteJsonSourcePackGate |
| 1052 | TestU351CapsuleWash.cs | Test_StateWashClampsToWatercolorBand |
| 1053 | TestU351CapsuleWash.cs | Test_CapsuleStateColorRoutesThroughWash |
| 1054 | TestU351Density.cs | Test_MenuFontSizeBandsThree |
| 1055 | TestU351Density.cs | Test_MenuSecondaryEntriesFour |
| 1056 | TestU351Density.cs | Test_CollectionFoldPortsWired |
| 1057 | TestU351Hitpad.cs | Test_HitpadStackTilesAroundVisuals |
| 1058 | TestU351Hitpad.cs | Test_HitpadBuildProducesPad |
| 1059 | TestU351StardustSplit.cs | Test_StardustPillPureCurrency |
| 1060 | TestU351StardustSplit.cs | Test_StardustIconReshaped |
| 1061 | TestU351Stopgap.cs | Test_MultiplierWindowRearmsOnLevelStart |
| 1062 | TestU351Stopgap.cs | Test_StormChargeFullSneezeRefusesConsume |
| 1063 | TestU360L4BWalk.cs | Test_ChoiceBannerGeometryAndCopy |
| 1064 | TestU360L4BWalk.cs | Test_DefeatReasonHumanized |
| 1065 | TestU360L4LegacyLayout.cs | Test_JourneyScrollAndNameGeometry |
| 1066 | TestU360L4LegacyLayout.cs | Test_WinPostcardGeometry |
| 1067 | TestU360L4Ui.cs | Test_CapsuleIconsAndSoftLiftWired |
| 1068 | TestU360L4Ui.cs | Test_WcSlicedPpuStadiumLock |
| 1069 | TestU360L4Ui.cs | Test_StardustLabelAlignAndIconLift |
| 1070 | TestU360L6B4Combo.cs | Test_ComboTrackerChainWindowContract |
| 1071 | TestU360L6B4Combo.cs | Test_ComboOfferFiresOncePerChain |
| 1072 | TestU360L6B4Combo.cs | Test_ComboSilenceWindowGuardsReoffer |
| 1073 | TestU360L6B4Combo.cs | Test_ComboPointRewardCapturesThreeAtPointer |
| 1074 | TestU360L6B4Combo.cs | Test_ComboBoostRewardAppliesRadius |
| 1075 | TestU360L6B4Lick.cs | ApplySuction |
| 1076 | TestU360L6B4Lick.cs | ApplyBurst |
| 1077 | TestU360L6B4Lick.cs | OnCaptured |
| 1078 | TestU360L6B4Lick.cs | WriteSnapshot |
| 1079 | TestU360L6B4Lick.cs | Test_LickContractValues |
| 1080 | TestU360L6B4Lick.cs | Test_LickDwellLocksAtThreshold |
| 1081 | TestU360L6B4Lick.cs | Test_LickDwellResetsOnMoveAway |
| 1082 | TestU360L6B4Lick.cs | Test_LickStrengthAppliesInField |
| 1083 | TestU360L6B5BellyTower.cs | Test_TowerContractValues |
| 1084 | TestU360L6B5BellyTower.cs | Test_TowerFillAnchorMath |
| 1085 | TestU360L6B5BellyTower.cs | Test_TowerReadyPulseBounds |
| 1086 | TestU360L6B5BellyTower.cs | Test_TowerBuildAndChargeMapping |
| 1087 | TestU360L6B5BellyTower.cs | Test_TowerChargeClampMirror |
| 1088 | TestU360L6B5ChallengeStar.cs | Test_ChallengeSegmentBandMatchesCatalog |
| 1089 | TestU360L6B5ChallengeStar.cs | Test_HudChallengeStarAndFirstHint |
| 1090 | TestU360L6B5ChallengeStar.cs | Test_HardMarkUnlockTimePoint |
| 1091 | TestU360L6B5PreLevelChoice.cs | Test_PreLevelChoiceContractValues |
| 1092 | TestU360L6B5PreLevelChoice.cs | Test_PreLevelOfferBandMapping |
| 1093 | TestU360L6B5PreLevelChoice.cs | Test_PreLevelHourglassExtendsTimer |
| 1094 | TestU360L6B5PreLevelChoice.cs | Test_PreLevelMagnetAppliesBoost |
| 1095 | TestU360L6B5PreLevelChoice.cs | Test_PreLevelHoldFreezesAndReleases |
| 1096 | TestU360L6FullPowerStorm.cs | Test_FullPowerContractValues |
| 1097 | TestU360L6FullPowerStorm.cs | Test_FullPowerTreatAppliesRadius3 |
| 1098 | TestU360L6FullPowerStorm.cs | Test_BelowChainKeepsBaseRadius |
| 1099 | TestU360L6FullPowerStorm.cs | Test_TreatNeverReducesChapterBuff |
| 1100 | TestU360L7SweepTeach.cs | Test_DataFaceSweepStainsOnlyAtStainLevels |
| 1101 | TestU360L7SweepTeach.cs | Test_HudSweepTeachShowBeatHideAndDailyYield |
| 1102 | TestU360L7SweepTeach.cs | Test_TutorialToastSurvivesPressHintExit |
| 1103 | TestU360S3Feel.cs | Test_HitStopTierDurations |
| 1104 | TestU360S3Feel.cs | Test_HitStopWatchdogRestoresOnDeadline |
| 1105 | TestU360S3Feel.cs | Test_AvLockThrottleWindowFastChain |
| 1106 | TestU360S3Feel.cs | Test_CaptureBeatPredictorContract |
| 1107 | TestU360S3Feel.cs | Test_CaptureBurstAudibleDowngrade |
| 1108 | TestU360S3Feel.cs | Test_CameraShakeTakeMaxAndDecay |
| 1109 | TestU360S3Feel.cs | Test_StormFlashProfileEnvelope |
| 1110 | TestWaveDirector.cs | Test_WavePlanSplitsAndThresholdAdvance |
| 1111 | TestWaveDirector.cs | Test_WaveDisabledOutsidePilot |
| 1112 | TestWaveDirector.cs | Test_CountOnlyAdvanceAndZeroWeightExcluded |
| 1113 | TestWaveDirector.cs | Test_MidEventKindRotationMapping |
| 1114 | TestWaveDirector.cs | Test_MidEventHiddenTreasureLiveChain |
| 1115 | TestWaveDirector.cs | Test_MidEventHiddenTreasureNoTemplateNoAction |
| 1116 | TestWaveDirector.cs | Test_MidEventBuddySkillLessonLiveChain |
| 1117 | TestWaveDirector.cs | Test_MidEventLandmarkBeckonLiveChain |
| 1118 | TestWaveDirector.cs | Test_W3PieceThresholdAcrossCatalog |
| 1119 | TestWaveDirector.cs | Test_W3ChainFiresWhenGoalSitsInW3 |
| 1120 | TestWaveDirector.cs | Test_W3ThresholdNegativeControl |
| 1121 | TestWaveDirector.cs | Test_SignatureSpriteMovesToW3Head |
| 1122 | TestWaveDirector.cs | Test_W3GoalTypeFilterSplitsPieceAccounts |
| 1123 | U360L3S3MomentShot.cs | Run |
| 1124 | U360L4CShot.cs | Run |
| 1125 | U360L4WalkShot.cs | Run |
| 1126 | U360L7FtueCapture.cs | Run |
| 1127 | U360LevelTour.cs | Run |
| 1128 | U360StageDiagnostics.cs | Run |
| 1129 | U360SweepShot.cs | Run |
| 1130 | X1958MenuShot.cs | Run |
| 1131 | ArrivalBanner.cs | ComposeEvolveLine |
| 1132 | ButtonSquash.cs | PressScaleAt |
| 1133 | ButtonSquash.cs | ReboundScaleAt |
| 1134 | ButtonSquash.cs | OnPointerDown |
| 1135 | ButtonSquash.cs | OnPointerUp |
| 1136 | BVersionPortMap.cs | AssertIntact |
| 1137 | CarLayout.Wing.cs | SetWingContentVisible |
| 1138 | CarLayout.Wing.cs | WingActionBadgeX |
| 1139 | CarLayout.Wing.cs | WingActionCaption |
| 1140 | CarLayout.Wing.cs | Bind |
| 1141 | CarLayout.Wing.cs | Bind |
| 1142 | CarLayout.cs | PlayViewAspect |
| 1143 | CarLayout.cs | Build |
| 1144 | CarLayout.cs | AttachWingAction |
| 1145 | CarLayout.cs | AttachWingParent |
| 1146 | CarLayout.cs | AttachWingParentLeft |
| 1147 | CarLayout.cs | AttachWingParentPull |
| 1148 | CarLayout.cs | AttachWingInfo |
| 1149 | CarLayout.cs | AttachWingInfoSlot |
| 1150 | CarLayout.cs | AttachWingInfoBackground |
| 1151 | CarLayout.cs | FitWingInfoWrap |
| 1152 | CarLayout.cs | WingFont |
| 1153 | CarLayout.cs | WingInfoRowHeight |
| 1154 | CarLayout.cs | FitWingInfoRow |
| 1155 | CarLayout.cs | BindWingInfoVisibility |
| 1156 | ChapterChestScreen.cs | Show |
| 1157 | ChapterChestScreen.cs | CapsuleLabel |
| 1158 | ChapterChestScreen.cs | CapsuleLit |
| 1159 | ChapterChestScreen.cs | ItemNameOf |
| 1160 | ChapterJourneyScreen.Car.cs | CarStationOf |
| 1161 | ChapterJourneyScreen.cs | Show |
| 1162 | ChapterJourneyScreen.cs | Hide |
| 1163 | ChapterJourneyScreen.cs | CardNameOf |
| 1164 | ChapterJourneyScreen.cs | CardSubOf |
| 1165 | ChapterJourneyScreen.cs | CardStatOf |
| 1166 | ChapterPalette.cs | AccentOf |
| 1167 | ChapterPalette.cs | ButtonOf |
| 1168 | ChapterPalette.cs | BannerOf |
| 1169 | ChapterPalette.cs | VeilOf |
| 1170 | CodexCatalog.cs | CryKeyOf |
| 1171 | CodexCatalog.cs | ChapterNameOf |
| 1172 | CodexCatalog.cs | RebindForProfile |
| 1173 | CodexCatalog.cs | UsePrefsKeyForTests |
| 1174 | CodexCatalog.cs | TotalCount |
| 1175 | CodexCatalog.cs | Get |
| 1176 | CodexCatalog.cs | IsUnlocked |
| 1177 | CodexCatalog.cs | LevelsDoneOf |
| 1178 | CodexCatalog.cs | LevelsDoneTotal |
| 1179 | CodexCatalog.cs | UnlockedCount |
| 1180 | CodexCatalog.cs | ProgressLine |
| 1181 | CodexCatalog.cs | ChapterDisplayName |
| 1182 | CodexRevealFx.cs | Play |
| 1183 | CollectionCodex.cs | PreviewLine |
| 1184 | CollectionScreen.cs | Show |
| 1185 | CollectionScreen.cs | Hide |
| 1186 | CollectionScreen.cs | AccelLabel |
| 1187 | CopyPools.cs | WinLineWeight |
| 1188 | CopyPools.cs | WinLineAt |
| 1189 | CopyPools.cs | DrawWinShareLine |
| 1190 | CopyPools.cs | FailLineWeight |
| 1191 | CopyPools.cs | FailLineAt |
| 1192 | CopyPools.cs | DrawFailShareLine |
| 1193 | CopyPools.cs | TryGetSignatureItem |
| 1194 | CopyPools.cs | DisplayNameOf |
| 1195 | CopyPools.cs | RarityRankOf |
| 1196 | CopyPools.cs | TryBuildHarvestLine |
| 1197 | CopyPools.cs | DailyFormOf |
| 1198 | CopyPools.cs | BuildFormLine |
| 1199 | CopyPools.cs | VisitedChaptersOf |
| 1200 | CopyPools.cs | BuildPostcardCountLine |
| 1201 | CopyPools.cs | ReadProgressRaw |
| 1202 | CopyPools.cs | BuildDailyMenuSubtitle |
| 1203 | CopyPools.cs | BuildDailyHudLine |
| 1204 | CopyPools.cs | TryBuildDailySignatureLine |
| 1205 | CopyPools.cs | PickDailyMenuLine |
| 1206 | CopyPools.cs | BuildLandingLine |
| 1207 | DailyTaskScreen.cs | Show |
| 1208 | DailyTaskScreen.cs | DoneCount |
| 1209 | DailyTaskScreen.cs | ClaimableCount |
| 1210 | FamilyNamePrompt.cs | RebindForProfile |
| 1211 | FamilyNamePrompt.cs | PromptSeen |
| 1212 | FamilyNamePrompt.cs | MarkPromptSeen |
| 1213 | FlyToTarget.cs | WorldToCanvas |
| 1214 | FlyToTarget.cs | CanvasCenterOf |
| 1215 | FlyToTarget.cs | Bezier01 |
| 1216 | FlyToTarget.cs | Fly |
| 1217 | FrameGeometryProbe.cs | Install |
| 1218 | FullChargeOverlay.cs | RebindForProfile |
| 1219 | FullChargeOverlay.cs | Ensure |
| 1220 | HealthNoticeScreen.cs | Begin |
| 1221 | HealthNoticeScreen.cs | Show |
| 1222 | HealthNoticeScreen.cs | Hide |
| 1223 | Front3HudPanel.cs | Build |
| 1224 | Front3HudPanel.cs | SetVisible |
| 1225 | Front3HudPanel.cs | HudLine |
| 1226 | Front3HudPanel.cs | Tick |
| 1227 | ParentKeyHudPanel.cs | Build |
| 1228 | ParentKeyHudPanel.cs | ResetForLevel |
| 1229 | ParentKeyHudPanel.cs | TickCooldown |
| 1230 | ParentKeyHudPanel.cs | RefreshLabels |
| 1231 | ICommerceService.cs | Ok |
| 1232 | ICommerceService.cs | Fail |
| 1233 | ICommerceService.cs | Cancel |
| 1234 | InGameHud.cs | RebindForProfile |
| 1235 | InGameHud.cs | AddInfoRow |
| 1236 | InGameHud.cs | GetInfoRow |
| 1237 | InGameHud.cs | SetInfoRow |
| 1238 | InGameHud.cs | SetInfoRow |
| 1239 | LeaderboardScreen.cs | Open |
| 1240 | LeaderboardScreen.cs | Show |
| 1241 | LeaderboardScreen.cs | Hide |
| 1242 | MainMenuScreen.cs | SetDuduPose |
| 1243 | MainMenuScreen.cs | Show |
| 1244 | MainMenuScreen.cs | Hide |
| 1245 | MenuEntryBar.cs | InvokeLandingForAutopilot |
| 1246 | NumberRoll.cs | Attach |
| 1247 | NumberRoll.cs | Set |
| 1248 | NumberRoll.cs | FloatUp |
| 1249 | OfflineEarningsPopup.cs | Show |
| 1250 | OfflineEarningsPopup.cs | AwayText |
| 1251 | OfflineEarningsPopup.cs | AmountText |
| 1252 | ParentGatePanel.cs | Judge |
| 1253 | ParentGatePanel.cs | NextQuestion |
| 1254 | ParentGatePanel.cs | Build |
| 1255 | ParentGatePanel.cs | Begin |
| 1256 | ParentGatePanel.cs | Show |
| 1257 | ParentGatePanel.cs | SetInteractable |
| 1258 | ParentGatePanel.cs | OnKey |
| 1259 | PaywallScreen.Helpers.cs | IsRetained |
| 1260 | PaywallScreen.Helpers.cs | FlushPendingRetention |
| 1261 | PaywallScreen.Helpers.cs | ChapterOf |
| 1262 | PaywallScreen.Helpers.cs | HasCard |
| 1263 | PaywallScreen.Helpers.cs | FullCharge |
| 1264 | PaywallScreen.Helpers.cs | DuelRope |
| 1265 | PaywallScreen.Helpers.cs | Of |
| 1266 | PaywallScreen.Helpers.cs | MigrateLegacyLevelKeys |
| 1267 | PaywallScreen.Helpers.cs | LegacyLevelKey |
| 1268 | PaywallScreen.cs | DrivingLocked |
| 1269 | PaywallScreen.cs | RequestRetention |
| 1270 | PaywallScreen.cs | Show |
| 1271 | PaywallScreen.cs | CanOpenNow |
| 1272 | PaywallScreen.cs | ResetSessionSuppression |
| 1273 | ProfileManagerPanel.cs | Open |
| 1274 | ProfileManagerPanel.cs | Refresh |
| 1275 | ProfileManagerPanel.cs | OnSwitchClicked |
| 1276 | ProfileManagerPanel.cs | OnDeleteClicked |
| 1277 | ProfileManagerPanel.cs | Close |
| 1278 | ProfileManagerPanel.cs | ShowPanel |
| 1279 | ProfileScreen.cs | Show |
| 1280 | ProfileScreen.cs | Hide |
| 1281 | ResultScreen.cs | SupplyLabel |
| 1282 | ResultScreen.cs | Show |
| 1283 | ResultScreen.cs | Hide |
| 1284 | StoreCatalog.cs | UsePrefsKeyForTests |
| 1285 | StoreCatalog.cs | ReadSand |
| 1286 | StoreCatalog.cs | ReadItemCount |
| 1287 | StoreCatalog.cs | ReadVaultBalance |
| 1288 | StoreCatalog.cs | ReadShopSandCappedToday |
| 1289 | StoreCatalog.cs | ReadSeat2Mode |
| 1290 | StoreScreen.cs | Show |
| 1291 | StoreScreen.cs | Hide |
| 1292 | StoreScreen.cs | SandLabelOf |
| 1293 | StoreScreen.cs | OwnedLabelOf |
| 1294 | StoreScreen.cs | Kick |
| 1295 | StubCommerceService.cs | ValidateCode |
| 1296 | StubCommerceService.cs | SubmitCode |
| 1297 | StubCommerceService.cs | Purchase |
| 1298 | StubCommerceService.cs | Restore |
| 1299 | StubCommerceService.cs | ReadBuyout |
| 1300 | StubCommerceService.cs | WriteBuyout |
| 1301 | TutorialHint.cs | RebindForProfile |
| 1302 | TutorialHint.cs | PressSeen |
| 1303 | TutorialHint.cs | MarkPressSeen |
| 1304 | TutorialHint.cs | SneezeSeen |
| 1305 | TutorialHint.cs | MarkSneezeSeen |
| 1306 | TutorialHint.cs | ReleaseSeen |
| 1307 | TutorialHint.cs | MarkReleaseSeen |
| 1308 | UIArt.cs | Icon |
| 1309 | UIArt.cs | Plain |
| 1310 | UiEasing.cs | EaseOut01 |
| 1311 | UiEasing.cs | EaseOutCubic01 |
| 1312 | UiEasing.cs | EaseIn01 |
| 1313 | UiEasing.cs | Pop01 |
| 1314 | UiEasing.cs | FlashAlphaAt |
| 1315 | UiFade.cs | Ensure |
| 1316 | UiFade.cs | PlayIn |
| 1317 | UiFade.cs | PlayOut |
| 1318 | UiFlash.cs | ResetProbe |
| 1319 | UiFlash.cs | Flash |
| 1320 | UiFlash.cs | Flash |
| 1321 | UiKeySubmit.cs | Attach |
| 1322 | UiKeySubmit.cs | Listen |
| 1323 | UiKeySubmit.cs | Ignore |
| 1324 | UIRoot.cs | EnsureRoot |
| 1325 | UIRoot.cs | CreateText |
| 1326 | UIRoot.cs | CreateButton |
| 1327 | UIRoot.cs | CreatePanel |
| 1328 | UIRoot.cs | AnchorStretch |
| 1329 | UIRoot.cs | AnchorCenter |
| 1330 | UIRoot.cs | AnchorTop |
| 1331 | UIRoot.cs | AnchorBottom |
| 1332 | UIRoot.cs | Hitpad |
| 1333 | UIRoot.cs | Hitpad |
| 1334 | WardrobeScreen.cs | Show |
| 1335 | WardrobeScreen.cs | OutfitNameOf |
| 1336 | WardrobeScreen.cs | IsUnlocked |
| 1337 | WardrobeScreen.cs | UseEquipKeyForTests |
| 1338 | WardrobeScreen.cs | UseProgressKeyForTests |
| 1339 | WardrobeScreen.cs | RebindForProfile |
| 1340 | BellyWindow.cs | Ensure |
| 1341 | BellyWindow.cs | FlightPos01 |
| 1342 | BellyWindow.cs | OrbitOffset |
| 1343 | JuiceCurves.cs | SpawnPop01 |
| 1344 | JuiceCurves.cs | CapturePop01 |
| 1345 | JuiceCurves.cs | InflateFor |
| 1346 | JuiceCurves.cs | Breath |
| 1347 | MetaStore.cs | StageOf |
| 1348 | MetaStore.cs | AddSand |
| 1349 | MetaStore.cs | ItemCount |
| 1350 | MetaStore.cs | GrantItem |
| 1351 | MetaStore.cs | TryConsume |
| 1352 | MetaStore.cs | ChapterClearedOnce |
| 1353 | MetaStore.cs | MarkChapterCleared |
| 1354 | MetaStore.cs | UsePrefsKeyForTests |
| 1355 | ShareLandingGate.cs | ResolveFromLaunch |
| 1356 | ShareLandingGate.cs | TryParseLevelId |
| 1357 | SignatureArt.cs | SpriteOf |
| 1358 | SuctionTrail.cs | Emit |
| 1359 | TestBellyMath.cs | Test_FlightEndpointsAndLift |
| 1360 | TestBellyMath.cs | Test_FlightHorizontalApproachMonotonic |
| 1361 | TestBellyMath.cs | Test_OrbitOnCircleAndDeterministic |
| 1362 | TestJuiceCurves.cs | Test_SpawnPopEndpointsAndOvershoot |
| 1363 | TestJuiceCurves.cs | Test_CapturePopBumpThenSettle |
| 1364 | TestJuiceCurves.cs | Test_InflateForMonotonicAndClamped |
| 1365 | TestJuiceCurves.cs | Test_BreathEnvelope |
| 1366 | TestMetaProgress.cs | Test_MetaStageBoundaries |
| 1367 | TestMetaProgress.cs | Test_MetaSandAccrualAndStageGrants |
| 1368 | TestMetaProgress.cs | Test_MetaItemConsumeAndRefuse |
| 1369 | TestMetaProgress.cs | Test_MetaChapterFlagsOnce |
| 1370 | TestMetaProgress.cs | Test_WardrobeUnlockBoundaries |
| 1371 | TestMetaProgress.cs | Test_MetaScaleMirrorZeroDrift |
| 1372 | TestShareLanding.cs | Test_ParseValidLevelIds |
| 1373 | TestShareLanding.cs | Test_RejectsUntrustedInput |
| 1374 | TestShareLanding.cs | Test_RejectsZeroAndOverflow |
| 1375 | TestShareLanding.cs | Test_LandingLineVerbatimAndRedLines |
| 1376 | UiFade.cs | Ensure |
| 1377 | UiFade.cs | PlayIn |
| 1378 | UiFade.cs | PlayOut |
| 1379 | WardrobeScreen.cs | Show |
| 1380 | WardrobeScreen.cs | IsUnlocked |
| 1381 | WardrobeScreen.cs | UseProgressKeyForTests |

## 附录 D 版本演进时间线

| 日期 | 当日提交数 |
|---|---:|
| 2026-09-13 | 1 |
| 2026-09-14 | 4 |
| 2026-09-15 | 7 |
| 2026-09-16 | 13 |
| 2026-09-17 | 2 |
| 2026-09-29 | 16 |
| 2026-09-30 | 48 |
| 2026-10-01 | 3 |
| 2026-10-05 | 33 |
| 2026-10-08 | 7 |
| 2026-10-09 | 19 |
| 2026-10-10 | 8 |
| 2026-10-11 | 3 |
| 2026-10-19 | 1 |
| 2026-10-20 | 2 |
| 2026-10-23 | 25 |
| 2026-10-24 | 5 |
| 2026-10-25 | 1 |
| 2026-10-26 | 14 |
| 2026-10-27 | 14 |
| 2026-10-28 | 12 |
| 2026-10-29 | 13 |
| 2026-11-02 | 32 |
| 2026-11-03 | 90 |
| 2026-11-04 | 52 |
| 2026-11-05 | 46 |
| 2026-11-06 | 23 |
| 2026-11-07 | 31 |
| 2026-11-08 | 86 |
| 2026-11-09 | 103 |
| 2026-11-10 | 80 |
| 2026-11-11 | 74 |
| 2026-11-12 | 85 |
| 2026-11-13 | 89 |
| 2026-11-14 | 89 |
| 2026-11-15 | 103 |
| 2026-11-16 | 76 |
| 2026-11-17 | 70 |
| 2026-11-23 | 1 |
| **合计** | **1381** |
