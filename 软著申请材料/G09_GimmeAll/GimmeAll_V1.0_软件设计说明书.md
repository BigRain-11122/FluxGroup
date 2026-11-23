# 吸嘟嘟游戏软件 V1.0 功能说明书与操作手册

> 编写：吸嘟嘟项目组　｜　版本：V1.0　｜　对应构建：V0.10.20　｜　最后更新：2026-11-23

## 说明

本手册按玩家实际使用顺序描述软件功能：从启动、进入游戏、核心玩法，到图鉴、商店、伙伴、日常等元系统，再到设置与家长锁。每个功能写明**入口、界面元素、操作、反馈、异常状态**，并标注对应的代码位置，便于核对。截图取自 V0.10.20 Windows 构建（2026-11-23）。

---

## 1 启动与健康忠告

**入口**：双击运行程序。

**界面元素**：启动页展示游戏名"Gimme All"、嘟嘟形象、健康游戏忠告（抵制不良游戏、注意自我保护、适度游戏益脑、合理安排时间）、适龄提示"8+"，底部为"进入游戏"按钮。

**操作**：点击"进入游戏"进入主界面。

**反馈**：按钮按下有缩放与高亮反馈（`ButtonSquash`）。

**异常状态**：若本地无存档，进入后按新档流程；若有存档，进入前弹出离线收益（见第 12 节）。

**代码位置**：`GimmeAll.UI.HealthNoticeScreen`、`GimmeAll.UI.ButtonSquash`。

![启动页](shots-20261123/01_splash.png)

---

## 2 主界面

**入口**：启动页点击"进入游戏"。

**界面元素**：顶部显示今日任务进度（0/3）、旅程章节与宝箱进度（第 1 章·宝箱 0/5）、星沙数量；中部为嘟嘟待机动画（`DuduIdlePlayer`）；底部为"同吸"主按钮，以及"图鉴""商店"入口。

**操作**：
1. 点击"同吸"进入关卡；
2. 点击"图鉴"进入收藏页；
3. 点击"商店"进入商店页。

**反馈**：嘟嘟待机有呼吸与眨眼；点击入口有按压反馈。

**异常状态**：离线收益未领取时，主界面下方弹窗拦截（见第 12 节），需先"收下"或"看视频翻倍"。

**代码位置**：`GimmeAll.UI.InGameHud`、`GimmeAll.Tests.DuduIdlePlayer`。

![主界面](shots-20261123/02_home.png)

---

## 3 关卡内：吸力场

**入口**：主界面点击"同吸"。

**界面元素**：全屏房间场景；嘟嘟位于画面中；目标物（灰尘、毛球、碎屑）散布在房间；顶部 HUD 显示目标数与计时。

**操作**：按住鼠标/手指，吸力场在指针位置展开；拖动指针移动吸力场；松开结束。

**反馈**：
- 吸力场为圆形范围指示（`SuctionGuideField`）；
- 目标进入范围后向场心加速；
- 捕获瞬间有粒子爆发、音效与 HUD 数字跳动（`JuiceCurves` 控制曲线）。

**异常状态**：目标逃离吸力场时播放逃脱提示音，不扣分（本作无失败态）。

**代码位置**：`GimmeAll.Gameplay.SuctionGuideWiring`、`GimmeAll.Gameplay.JuiceCurves`。

![关卡内吸附](shots-20261123/05_suction.png)

---

## 4 吸力场的手感设计

**参数**：半径 2.2（世界单位），基础强度 12，场心跟随插值 0.35，同帧最多并行捕获 3 件（`SuctionFieldConfig.cs`）。

**为什么限制并行数**：如果不限制，玩家按住不动就能一次清屏，"逐个追"的节奏消失。限制为 3 件后，玩家必须移动吸力场，形成"按住—移动—收割"的循环。

**帧率无关**：场心跟随使用 `1 - Pow(1 - followLerp, dt * 60)` 的插值形式，保证 30/60/120fps 手感一致（见第 15 节问题记录）。

---

## 5 目标族与捕获

**目标族**：灰尘（轻、一吸即走）、毛球（会滚动、需要预判）、碎屑（重、需要持续吸附）。

**捕获判定**：目标在范围内每帧累加进度，进度到阈值即捕获，发 `ObjectCaptured` 事件；上一帧在范围内、本帧出圈的目标发 `ObjectEscaped`，用预分配字典记录上一帧状态，避免每帧分配。

**反馈**：捕获有 3 层反馈（粒子、音效、HUD 计数），漏掉任何一层都会让玩家怀疑"我到底吸到没有"。

---

## 6 关卡结算

**入口**：吸满目标数后自动结算。

**界面元素**：结算面板展示本关吸取数量、获得星沙、是否首次通关；提供"下一关""回主界面"。

**操作**：点击"下一关"直接进入下一关；点击"回主界面"返回。

**异常状态**：若本关为章节末关，结算后回到旅程页并播放宝箱动画。

![结算/章节](shots-20261123/07_result.png)

---

## 7 章节旅程

**入口**：主界面顶部"旅程 第 1 章·宝箱 0/5"。

**界面元素**：章节地图、宝箱进度（每 5 关一个宝箱）、已通关节点、未解锁节点。

**操作**：点击已通关节点可重玩；点击宝箱领取奖励。

**反馈**：宝箱开启有开箱动画与奖励飞入（`ChapterChestScreen`）。

**代码位置**：`GimmeAll.UI.ChapterJourneyScreen`、`GimmeAll.UI.ChapterChestScreen`。

---

## 8 图鉴

**入口**：主界面"图鉴"。

**界面元素**：两页签——"收藏"（目标物图鉴）与"伙伴"（嘟嘟的伙伴）。

**操作**：
1. 左右滑动切换页签；
2. 点击未解锁条目显示解锁条件；
3. 点击已解锁条目查看描述。

**反馈**：新条目解锁时有揭示特效（`CodexRevealFx`）。

**异常状态**：无网络时仍可查看已解锁内容（全部本地存储）。

**代码位置**：`GimmeAll.UI.CollectionScreen`、`CollectionCompanions`、`CollectionCodex`。

---

## 9 每日任务

**入口**：主界面顶部"今日任务 0/3"。

**界面元素**：三条每日任务（如吸取 50 个灰尘、完成 3 关、使用 1 次伙伴技能），各自进度条与奖励。

**操作**：点击"领取"领取已完成任务奖励；未完成时按钮置灰。

**反馈**：领取后星沙数字跳动并飞入顶栏。

**异常状态**：跨天刷新时按本地时间 0 点重置；离线期间不消耗任务次数。

**代码位置**：`GimmeAll.UI.DailyTaskScreen`、`GimmeAll.Game.DailyTaskFlow`。

---

## 10 商店

**入口**：主界面"商店"。

**界面元素**：商品列表（伙伴碎片、加速道具、皮肤），每个商品显示价格（星沙）与"看广告免费拿"按钮。

**操作**：
1. 点击商品用星沙购买；
2. 点击"看广告免费拿"播放激励视频，完成后发放。

**反馈**：购买成功有获得动画；广告未加载完成时按钮显示加载态。

**异常状态**：广告不可用时降级为纯星沙购买，不阻断流程（`StoreAdFlow`）。

**代码位置**：`GimmeAll.UI` 商店相关类、`GimmeAll.Game.StoreFlow`、`StoreAdFlow`。

---

## 11 伙伴系统

**入口**：图鉴 → 伙伴页签。

**界面元素**：伙伴列表、充能环（`CompanionChargeRing`）、升级按钮、上阵座位。

**操作**：
1. 选择伙伴上阵（最多 1 个上阵位）；
2. 消耗星沙升级，提升技能效果；
3. 充能满后可在关卡内释放技能。

**反馈**：充能环随时间填充；升级时属性数字滚动。

**异常状态**：充能未满时技能按钮置灰并显示剩余时间。

**代码位置**：`GimmeAll.Game.CompanionCoordinator`、`CompanionUpgradeFlow`、`CompanionSeatFlow`、`GimmeAll.UI.CompanionRecharge`。

---

## 12 离线收益

**入口**：离线超过 10 分钟后回到游戏时自动弹出。

**界面元素**：弹窗显示"欢迎回来！离开 X 分钟"、获得星沙数量、"收下"与"看视频翻倍"两个按钮。

**操作**：点击"收下"领取基础收益；点击"看视频翻倍"播放广告后领取双倍。

**反馈**：领取后星沙飞入顶栏。

**异常状态**：广告不可用时"看视频翻倍"置灰，只保留"收下"，不阻断进入游戏。

![离线收益](shots-20261123/04_level.png)

---

## 13 签到

**入口**：主界面活动入口（按版本开启）。

**界面元素**：7 天签到格、当日高亮、补签按钮。

**操作**：点击当日格子领取；漏签可用星沙补签。

**异常状态**：跨天刷新按本地 0 点；重复领取被服务层拒绝并提示。

**代码位置**：`GimmeAll.Tests.TestCheckInUi`（用例覆盖）。

---

## 14 设置与家长锁

**入口**：主界面右上角齿轮。

**界面元素**：音效/音乐开关、震动开关、语言、家长锁入口、隐私政策、版本号。

**操作**：
1. 开关即时生效并持久化；
2. 家长锁需按提示完成验证（数学题），验证后可关闭广告与内购入口。

**异常状态**：家长锁连续错误 3 次锁定 60 秒。

**代码位置**：`GimmeAll.Levels.ParentKeyGuide`（家长锁引导）、`GimmeAll.Game.MetaStore`（持久化）。

---

## 15 开发中真实遇到的问题

### 15.1 低帧率吸附迟滞

首次内测（9 月 20 日）在 40fps 测试机上，吸力场明显跟不上手指，120fps 机器正常。原因是场心插值用了固定系数，帧率越低每帧补得越少。改成帧率无关形式后，40fps 与 120fps 手感一致。此后定规矩：所有跟手插值必须带 `dt`。

### 15.2 车机版信息带被压扁

车机版复用竖屏 HUD，按 0.5625 缩放进 4:3 画面，顶部信息带只剩一条细线。改成左翼竖排后解决，并加了 `car_hud_wing_check`（204 条断言）防止回退。

### 15.3 4K 母版与裁切件对不上

商店物料需要 16:9 与 4:3 两种裁切。早期两张图各自生成，导致"同一张画"其实是两张不同的图。后来改为：先出 1:1 母版（3840×3840），两个比例都从母版中心裁切，再用同框逐像素比对（`family_4k_accept_check`）。

### 15.4 离线弹窗挡住主按钮

"欢迎回来，+6 星沙"弹窗最初盖住底部"同吸"按钮。改成弹窗内提供"收下"与"看视频翻倍"两个明确动作，关闭后回到主界面，不依赖点空白处。

### 15.5 抓屏取证失败

给软著材料拍截图时，用 GDI 抓屏在场景切换后拿到的是纯色空白图。改用 `PrintWindow(PW_RENDERFULLCONTENT)` 直接向窗口要渲染位图后正常。这类问题不影响功能，但会让材料没法自证。

---

## 16 性能与兼容

| 项 | 目标 | 实测/说明 |
|---|---|---|
| 帧率 | 60fps（手机）/30fps（车机 8155） | 低端机优先保 30 |
| 纹理 | 非背景资产 ≤1024 | 显存预算约 15.5MB |
| 单局 GC | 0 分配 | 对象池 + 预分配字典 |
| 启动 | 首屏 ≤3 秒 | 资源分包加载 |
| 分辨率 | 1080×1920 竖屏 / 4:3 车机 | 安全区 5% |

---

## 17 构建与发布

- 当前构建：V0.10.20；Android APK 132.9MB；Windows 64 位包。
- 构建流程：团结引擎命令行构建 → 冒烟测试 → 门禁 G1–G4 巡检 → 出包。
- 发布渠道：Android 应用商店；车机版单独出包。

---

## 18 测试

- 用例 119 条，覆盖核心循环、存档、广告门控、车机适配、家长锁。
- 门禁 G1 可玩、G2 亲子切片、G3 发布候选、G4 发布，每道门有独立就绪检查脚本。
- 每个门禁都配一条"故意写坏必须红"的负控用例，防止闸失效。

---

## 附录 源文件统计

| 项 | 数量 |
|---|---:|
| C# 源文件 | 432 |
| UI 相关类 | 126（含测试） |
| 设计文档 | 909 |
| 代码提交 | 848 次，覆盖 39 个工作日（2026-09-13 至 2026-11-23） |

---

## 19 数据结构

### 19.1 存档

存档以 JSON 持久化在本地（`MetaStore`），包含：玩家 id、星沙数量、已通关关卡集合、章节宝箱领取状态、伙伴拥有与等级、伙伴上阵位、每日任务进度与刷新时间、签到记录、商店已购商品、设置项（音效/音乐/震动/语言）、家长锁状态。

写入采用"临时文件 + 原子替换"：先写 `*.tmp`，`Flush` 后替换目标文件，断电或强杀时回退到上一份可用存档。

### 19.2 关卡数据

关卡由数据驱动（`LevelCatalog` / `ContentCatalog`）：关卡 id、目标数、时限、可用目标族权重、场景 id。加关卡只加数据，不改代码。

### 19.3 配置

`SuctionFieldConfig`：半径 2.2、基础强度 12、跟随插值 0.35、并行捕获上限 3。其余手感参数（加速度、阻力、捕获阈值）在同类中以字段暴露，便于调参时不动代码。

### 19.4 事件

跨模块通信走 `GameEventBus`：`ObjectCaptured`、`ObjectEscaped`、`LevelCompleted`、`CompanionCharged`、`AdRewardGranted` 等。订阅方在 `OnEnable` 注册、`OnDisable` 注销，避免悬挂引用。

## 20 服务接口

| 接口 | 职责 | 实现 |
|---|---|---|
| `IMetaService` | 元数据读写（星沙、进度、设置） | `MetaService` 分部类（Daily/Companion） |
| `ICommerceService` | 商品、购买、恢复 | `StoreFlow` |
| `ISuctionGuide` | 吸力场引导与范围提示 | `SuctionGuideField` |
| `LevelProgressStore` | 关卡进度与章节推进 | 本地存储 |

接口放在 Core 层，玩法层只依赖接口，不依赖具体实现。这样替换商店实现（本地/平台）不影响玩法代码。

## 21 状态机

### 21.1 界面栈

界面采用栈式管理：`Push` 打开新界面，`Back` 关闭当前界面并恢复下层。返回键与安卓物理返回一致。

### 21.2 关卡状态

`Idle → Playing → Settling → Result`。`Settling` 期间禁止输入，防止连点重复结算。

### 21.3 广告状态

`Idle → Loading → Playing → RewardGranted → Idle`。`Loading` 超过 10 秒视为失败，降级为纯星沙购买（`StoreAdFlow`）。

## 22 异常与降级矩阵

| 异常 | 表现 | 处理 |
|---|---|---|
| 无网络 | 广告、排行榜不可用 | 降级为本地功能，不阻断主流程 |
| 广告加载失败 | 激励按钮置灰 | 保留星沙购买入口 |
| 存档损坏 | 读取失败 | 回退上一份可用存档，并提示 |
| 系统时间回拨 | 离线收益异常 | 以服务端/单调时钟校正，收益置 0 并记录 |
| 进程被杀 | 关卡中断 | 进度按已通关节点保留，不重复扣次数 |
| 低内存 | 纹理被回收 | 重新加载，界面短暂白屏可接受 |

## 23 权限与隐私

- 应用不申请通讯录、短信、位置权限；仅使用网络与存储。
- 所有进度保存在本地；不上传个人信息。
- 家长锁可关闭广告与内购入口，符合家庭向产品的适龄要求（8+）。
- 隐私政策在设置页可查看（`privacy-policy.md`）。

## 24 版本与兼容

| 版本 | 主要变化 |
|---|---|
| V0.10.19 | 车机版 HUD 左移；4K 母版裁切 |
| V0.10.20 | 离线收益弹窗交互修正；截图取证工具 |

兼容：Android 8.0+（API 26+）；Windows 10+ 64 位；车机 Android Automotive（8155 台架）。

## 25 安装与卸载

**安装**：Android 通过应用商店或 APK 安装；Windows 解压即用，无需安装。

**卸载**：Android 长按图标卸载；Windows 删除目录。卸载会清除本地存档，卸载前可在设置页查看存档说明。

## 26 术语表

| 术语 | 含义 |
|---|---|
| 吸力场 | 按住屏幕产生的圆形吸附范围 |
| 星沙 | 游戏内唯一软货币 |
| 伙伴 | 可上阵提供技能的收集角色 |
| 金痕（图鉴） | 收藏满级的视觉标记 |
| 章节宝箱 | 每 5 关解锁一次的奖励节点 |


---

# 界面元素清单 v1

共 52 个界面类。每个界面列出其代码中出现的界面文案（截取前 24 条），可按界面名与源文件逐条核对。

## CompanionDef

源文件：`Assets/_Project/Core/Companions/CompanionDef.cs`

- 嘟嘟·典藏版
- 紫白毛绒小鸡·肚皮金漩涡纹（Logo 同构）
- 金漩涡
- 嘟嘟·吸吸嘴版
- 嘴=软吸管·玩法直译
- 吸管点吸
- 团子猫头鹰
- 心形脸盘+团子体型+琥珀大眼
- 鹰眼定身
- 草莓折耳兔
- 一耳立一耳折+白围嘴
- 竖耳预警
- 蜜金水手鸭
- 奶油旋呆毛+白水手帽金锚
- 金锚定泊
- 珊瑚小狐狸
- 蓬大尾奶白尖+狡黠眯眼
- 蓬尾旋风
- 蓝莓小企鹅
- 白肚兜+扑腾短翅+冷色反差
- 企鹅扑腾
- 抹茶小鳄鱼
- 圆钝大嘴咧笑+反差萌
- 大嘴吞屏

## CompanionRuntime

源文件：`Assets/_Project/Core/Companions/CompanionRuntime.cs`

- 败局瞬间白捡

## StoreAssetGen

源文件：`Assets/_Project/Game/Editor/StoreAssetGen.cs`

- GimmeAll/生成商店图标

## MetaStore

源文件：`Assets/_Project/Game/MetaStore.cs`

- 嘟崽
- 嘟墩
- 嘟吨
- 嘟府

## DailyLevelPolicy

源文件：`Assets/_Project/Levels/DailyLevelPolicy.cs`

- 截断到当天零点

## LevelProgressStore

源文件：`Assets/_Project/Levels/LevelProgressStore.cs`

- 续玩起点
- 已进入
- 清除我的数据
- 重置存档

## TestBVersionStoreScreen

源文件：`Assets/_Project/Tests/Editor/TestBVersionStoreScreen.cs`

- 已有 x2
- 道具铺
- 返回
- 今日特惠
- 常用道具
- 打扫礼包
- 磁铁
- 沙漏
- 复活羽毛
- 嘟嘟金库
- 已攒 480 / 960
- 看视频破仓
- 看视频领 60 星沙
- 磁铁 x2 · 沙漏 x3
- 复活羽毛 x1
- 好价常在
- 原价 1,150
- 时间 +5 秒
- 吸力 +25% · 15 秒
- 本局 1 次 · 原地复活
- 6.1折
- 第 2 驻场位
- 视频解锁 24 小时
- 第驻场位已永久解锁

## TestCodexAccelUi

源文件：`Assets/_Project/Tests/Editor/TestCodexAccelUi.cs`

- 只差 1 只！看视频领沙漏
- 只差 1 只！看视频领磁力

## TestCodexCatalog

源文件：`Assets/_Project/Tests/Editor/TestCodexCatalog.cs`

- 家 · 晨光房间
- 京都 · 樱花庭院
- 巴黎 · 花街清晨
- 埃及 · 金字塔黄昏
- 紫禁城 · 红墙晨光
- 星海 · 太空终章
- 威尼斯 · 水巷黄昏
- 圣托里尼 · 白屋晨曦
- 阿尔卑斯 · 雪夜木屋
- 桂林 · 漓江烟雨
- 大堡礁 · 浅海珊瑚
- 芬兰 · 极光之夜
- 荷兰 · 花田春日
- 薰衣草田 · 夏日晚风
- 枫叶湖 · 秋日野餐
- 雪中广场 · 冬夜市集
- 云端 · 天空之城
- 回家 · 满屋星光
- 户口本必须恰 17 只小可爱，实测
- ) 不得为 null
- 只名字为空
- 个性三词为空
- 记忆点为空
- 叫声为空

## TestCodexUi

源文件：`Assets/_Project/Tests/Editor/TestCodexUi.cs`

- 下一位新朋友在「京都 · 樱花庭院」等你
- 神兽小家全员到齐！神秘礼物已送达
- 下一位新朋友在「云端 · 天空之城」等你
- 章键=0 的卡不许盖印
- pill 必须钉在首个未收编未留存卡上
- pill 必须挪到下一张未收编未留存卡
- 未留存的卡不许跟着亮
- 章键=0 ⇒ 环不可见
- 章键=0 ⇒ pill 仍在首个未收编未留存卡上
- 已留存的空框卡不得再吃 CTA（死按钮判负）
- pill 必须离开已留存卡

## TestCompanionFace

源文件：`Assets/_Project/Tests/Editor/TestCompanionFace.cs`

- 名册恒 24（零淘汰律），实测
- 件，首缺=
- 伙伴钮必须挂 ChargeRing 径向环
- Icon 槽在位
- 脸槽 Sprite 已接线
- 环=Filled 径向
- 环值=Fill01 真值，实测
- 充能中环=珊瑚基色
- 满能环=1
- 满能环翻深紫（双充能色系分离锁·X2684）
- 满能
- 满能态文字保留
- 盾备环翻丁香
- 盾备
- 盾备态文字保留
- 双 id 双槽：两枚径向环在位，实测
- 槽②Icon 槽在位
- 槽②脸=席位②伙伴立绘，实测
- 槽②环值=Fill01 真值，实测
- 槽②环=珊瑚基色
- 围巾捞定
- 槽②技能名随名册 skillName，实测
- 槽①环值不随槽②事件漂移，实测
- 槽①盾备态跨槽事件保色（双槽互不干扰）

## TestCompanionFamilies2

源文件：`Assets/_Project/Tests/Editor/TestCompanionFamilies2.cs`

- ghost 工厂创建失败
- ghost 起步必须 Idle
- bubble 工厂创建失败
- bubble 起步必须 Idle
- splitter 工厂创建失败
- splitter 起步必须 Idle
- 破裂链必须恰出
- 破裂链必须可定吸清零（注册表零存活残留），实测
- 事件键族必须为 1 splitter +
- splitkid，实测

## TestCompanionQi2b

源文件：`Assets/_Project/Tests/Editor/TestCompanionQi2b.cs`

- 起步两件必须 Idle
- 踢出件必须判漂移中（IsDrifting 读面）
- 静止件不得判漂移
- 逃逸件必须被冻结（HaltEscaping）
- Halt 必须当场清速（瞬间钉住非滑停）
- 冻结窗内再踢必须先有速度（更新前）
- 定身件吸取进度必须累积（捕获流零干预）
- 到期必须解除定身（Halted 读面）
- 两静止件起步不得判漂移
- OnCaptured 必须置 Captured
- HaltAll 对已捕获件必须零干扰
- 存活件照常冻结
- 请求 3 实捕必须 3，实测
- 距原点最近三件（0/1/2）必须被捕获
- 远处两件（5/9）必须原样存活（最近选择律）
- 第二发事件数必须 2，实测
- 余下两件必须补捕
- 空场必须 0 捕 0 事件（诚实收手），实测
- 单件单捕必须 1，实测

## TestCompanionRoster

源文件：`Assets/_Project/Tests/Editor/TestCompanionRoster.cs`

- 名册长度必须=24，实测
- 款 id 为空
- id 重复：
- 名字为空
- 名字重复：
- 记忆点为空
- 技能名为空
- 资源键为空
- 资源键重复：
- 章号越界：
- （已上线 6 章·章 7-18 走客串位不占席）
- A 版缺
- B 版缺
- 版本位错
- 版章
- 席位必须恰 2，实测
- 技能族越界：
- 版技能族
- 零覆盖（七族全员玩法化律）
- 设计案绑定锁：名册缺
- 章绑应为
- ，实测
- 技能族应为
- A12 吸管嘴必须=定吸系（记忆点直译）

## TestCompanionRosterUi

源文件：`Assets/_Project/Tests/Editor/TestCompanionRosterUi.cs`

- 技能：
- 主战席
- 上主战席
- 升级 50 星沙
- 升级 120 星沙
- 已满级
- 星沙不足
- 视频解锁
- 500 星沙
- 看视频解锁
- 已解锁
- 再看续 24 小时
- 已永久解锁

## TestCompanionRuntime

源文件：`Assets/_Project/Tests/Editor/TestCompanionRuntime.cs`

- 重置态必须零充能
- 捕获不得满能
- 未满 TryConsume 必须拒付
- 拒付不得清零充能
- 捕获必须满能
- 满能后 OnCapture 必须封顶不涨
- 满能 TryConsume 必须成功
- 释放后必须清零回充
- 重置必须全清
- 未满 ArmShield 必须拒付
- 拒付不得置备位
- 满能 ArmShield 必须成功
- 预备后=备位置位+充能清零（点击语义消耗充能）
- 备位 ConsumeShield 必须成功
- 护盾必须一次性（二次消费拒付）
- 消费后备位必须复位
- 再次充能可再备
- 关重置必须连护盾备位一起清（关内增益不跨关）
- A 版章 1 主战席=A01（半径·名册序）
- A 版章 2 主战席=A08（迟滞·名册序回归）
- A 版章 3 主战席=A02（迟滞·名册序回归）
- A 版章 4 主战席=A05（定吸·名册序回归）
- A 版章 5 主战席=A07（星沙）
- A 版章 6 主战席=A03（半径）

## TestDailyTask

源文件：`Assets/_Project/Tests/Editor/TestDailyTask.cs`

- 反射未命中
- 未满任务不得领奖
- 早领不得入账星沙
- 已满任务续捕获不得再发布快照（热路径零发布）
- 全满态领奖位应全 false
- 任务1 领奖应兑 20 星沙
- 领奖后星沙应为 20，实测
- 同任务重复领必须拒付
- 任务2/任务0 应正常领奖
- 三任务日总应为 60，实测
- 越界任务 id 必须拒付
- 领奖位应全 true
- 当日领奖应正常兑付
- 当日星沙应为 20，实测
- 跨日首捕获应重新计数 1/3，实测
- 跨日不得清星沙余额（元货币不日清），实测
- 跨日未满任务不得领旧日奖
- 同日进度应续涨 2/3，实测
- 领奖应正常兑付
- 星沙应为 20，实测
- Menu 态应恰发一次快照（晚订阅者补刷），实测
- 重启后星沙余额必须续航，实测
- 非 Menu 态不得发任务快照，实测

## TestDailyTaskUi

源文件：`Assets/_Project/Tests/Editor/TestDailyTaskUi.cs`

- 可领 +20 星沙
- 已领

## ChapterChestScreen

源文件：`Assets/_Project/UI/ChapterChestScreen.cs`

- 宝箱可开！
- 宝箱全开啦
- 宝箱
- 沙漏
- 磁力
- 章节宝箱
- 集齐一章五关即可开箱
- 知道啦
- 章 ·
- 已开箱
- 章宝箱全部收齐
- 收好啦 · 下一章见
- 开箱！
- 星沙 +1
- 还差
- 开箱 +
- 星沙+1

## ChapterJourneyScreen.Car

源文件：`Assets/_Project/UI/ChapterJourney/ChapterJourneyScreen.Car.cs`

- 返回
- 章节旅程
- 未解锁
- 已通关
- 进行中
- 宝箱
- 继续旅程

## ChapterJourneyScreen

源文件：`Assets/_Project/UI/ChapterJourneyScreen.cs`

- 返回
- 章节旅程
- 未解锁
- 已通关
- 进行中
- 宝箱
- 继续旅程

## ChapterChestScreen.Car

源文件：`Assets/_Project/UI/Chest/ChapterChestScreen.Car.cs`

- 章节宝箱
- 集齐一章五关即可开箱
- 知道啦
- 星沙

## ChoiceBanner

源文件：`Assets/_Project/UI/ChoiceBanner.cs`

- 还差一点点！
- 看广告续 10 秒
- 豪赌 +15 星沙
- 连击 5 连发！
- 定向吸 ×3
- 范围吸 ×1.5·5s
- 开吸前挑个免费的！
- 沙漏 +5 秒
- 磁力 ×1.25·15s

## CodexCatalog

源文件：`Assets/_Project/UI/CodexCatalog.cs`

- 绒团
- 奶凶·户主瘾·絮暖芯
- 噗噜绒~
- 樱吹小鹿
- 竞技脑·偏执狂·记风仇
- 呦咻！
- 玫瑰小鸽
- 迷之自信·死不问路·仪式感重
- 咕噜噗~
- 沙暮小猫
- 落日惯偷·贵族做派·越亏越偷
- 每天黄昏蹲金字塔影尖偷走夕阳最后一格光揣进围巾
- 喵呜噜~
- 朱红小熊猫
- 官瘾大·轴到发光·秒rua破功
- 唧——嘎！
- 瞌睡小星宝
- 睡神执法·梦话玄学·越睡越亮
- 唔咻~
- 嘎船长（条纹帽小海鸥）
- 戏精·大嗓门·外强中干
- 嘎嗦咪~
- 小云（小白猫）
- 神游·慢性子·谜之自信

## CollectionCodex

源文件：`Assets/_Project/UI/Collection/CollectionCodex.cs`

- 终章领队
- 等你
- 神兽小家全员到齐！神秘礼物已送达
- 新收编
- 只 · 下一位新朋友在「
- 」等你
- 下一位新朋友在「

## CollectionCompanions

源文件：`Assets/_Project/UI/Collection/CollectionCompanions.cs`

- A 版 · 12 款（在玩）
- B 版 · 12 款
- 第 2 驻场位 · 双主战
- 已永久解锁
- 已解锁 24 小时
- 再看续 24 小时
- 视频解锁 24 小时 · 500 星沙永久
- 升级星沙
- 技能：
- 章 · Lv.
- 升级
- 星沙

## CollectionScreen.Car

源文件：`Assets/_Project/UI/Collection/CollectionScreen.Car.cs`

- 神兽小家 · 回家纪念册
- 上一页
- 下一页
- 关闭
- 衣橱
- 吸友榜
- 档案
- 终章领队

## CollectionScreen

源文件：`Assets/_Project/UI/CollectionScreen.cs`

- 生物图鉴
- 伙伴团
- 主战席
- 上主战席
- 切版启用
- 今日已试用
- 已试用·下关生效
- 已满级
- 星沙不足
- 存下来
- 已存下来
- 神兽小家 · 回家纪念册
- 关闭
- 档案
- 衣橱
- 吸友榜

## DailyTaskScreen.Car

源文件：`Assets/_Project/UI/DailyTask/DailyTaskScreen.Car.cs`

- 今日任务
- 每天零点刷新
- 知道啦
- 每日签到
- 签到 +10 星沙

## DailyTaskScreen

源文件：`Assets/_Project/UI/DailyTaskScreen.cs`

- 通关
- 大口吸掉
- 只小可爱
- 捕获
- 今日任务
- 每天零点刷新
- 每日签到
- 签到 +10 星沙
- 知道啦
- 已领
- 可领 +
- 星沙
- 已签
- 签到 +

## FamilyNamePrompt

源文件：`Assets/_Project/UI/FamilyNamePrompt.cs`

- 嘟嘟
- 给嘟嘟起个名字
- 跳过
- 就叫这个
- 先删一个档再建档
- 现在存不了，先玩着

## HealthNoticeScreen

源文件：`Assets/_Project/UI/HealthNoticeScreen.cs`

- 健康游戏忠告
- 适龄提示：8+
- 进入游戏
- 家长
- 家庭版 v0.10

## Front3HudPanel

源文件：`Assets/_Project/UI/Hud/Front3HudPanel.cs`

- 吸力 ×1
- 嘴里 0/
- 情绪价值 +0
- 吸力 ×
- 嘴里
- 情绪价值 +
- 连击 ×

## InGameHud.Boosters

源文件：`Assets/_Project/UI/Hud/InGameHud.Boosters.cs`

- 盾备
- 满能

## ParentKeyHudPanel

源文件：`Assets/_Project/UI/Hud/ParentKeyHudPanel.cs`

- 用完

## InGameHud

源文件：`Assets/_Project/UI/InGameHud.cs`

- 零压力 UI
- 零信息 UI
- 时间提示走暖色
- 紧迫但不惊吓
- 这是块硬骨头
- 吸不掉？快划三下！
- 满啦，松手吐！
- +5 秒
- 磁力
- 伙伴
- 从结算屏直接回菜单
- 还差
- 已清

## LeaderboardScreen.Car

源文件：`Assets/_Project/UI/Leaderboard/LeaderboardScreen.Car.cs`

- 吸友榜
- 关闭
- 名次
- 吸友
- 分数
- （我）

## LeaderboardScreen

源文件：`Assets/_Project/UI/LeaderboardScreen.cs`

- 吸友榜
- 关闭
- 敬请期待～
- 正在拉取好友成绩…
- 快去抢占第一名！
- （我）

## MainMenuScreen

源文件：`Assets/_Project/UI/MainMenuScreen.cs`

- 嘟崽
- 嘟墩
- 嘟吨
- 嘟府
- 成长 ·
- 一指吸走所有烦恼
- 早安，今天的烦恼已经摆好，就等你来吸了。
- 今日份已上桌，趁热吸。
- 晚上好，今天的烦恼已经摆好，就等你来吸了。
- 今日任务 0/3
- 旅程 第 1 章
- 开吸！
- 同吸
- 图鉴
- 商店

## OfflineEarningsPopup

源文件：`Assets/_Project/UI/OfflineEarningsPopup.cs`

- 小时
- 分钟
- 星沙
- 欢迎回来！
- 收下
- 离开

## ParentGatePanel

源文件：`Assets/_Project/UI/ParentGatePanel.cs`

- 请家长算一下
- 这里只有家长能过。孩子玩的都还在。
- 换一道题慢慢来

## PaywallScreen.Flow

源文件：`Assets/_Project/UI/Paywall/PaywallScreen.Flow.cs`

- 已经开通了，这本相册都是你的。
- 已开通
- 这次没成，钱没扣
- 再试一次
- 正在开通…
- 开通

## PaywallScreen.Helpers

源文件：`Assets/_Project/UI/Paywall/PaywallScreen.Helpers.cs`

- 充电小站.fullcharge
- 充电小站.duelrope

## PaywallScreen

源文件：`Assets/_Project/UI/PaywallScreen.cs`

- 把这本相册留下来
- 先回地图
- 一次开通，没有别的东西要买。
- 一次开通，整本相册都留下来
- 开通
- 开通后随时可以退回来找我。
- 恢复购买
- 这本相册都留下来了
- 每一站的明信片都能存、能打印，也能投到车里。
- 回地图

## ProfileManagerPanel

源文件：`Assets/_Project/UI/ProfileManagerPanel.cs`

- 家庭档案
- 切换
- 删除
- 未命名档
- 空位
- （当前）
- 确认删除
- 已切到
- 这个档还是空的
- 已经在用这个档了
- 暂时不能切换
- 这个档位用不了
- 这个档已经删掉了，已回到游客档
- 已删除
- 号档
- 暂时不能删档
- 没删干净，请再试一次

## ResultScreen.Car

源文件：`Assets/_Project/UI/Result/ResultScreen.Car.cs`

- 送你一张
- 下一站
- 回主菜单

## ResultScreen.Postcard

源文件：`Assets/_Project/UI/Result/ResultScreen.Postcard.cs`

- 旅装：
- 下一站：
- 京都
- 巴黎
- 埃及
- 紫禁城
- 星海
- 威尼斯
- 圣托里尼
- 阿尔卑斯
- 漓江
- 大堡礁
- 极光
- 花田
- 薰衣草
- 枫叶湖
- 冬夜市集
- 云端之城
- 回家

## ResultScreen

源文件：`Assets/_Project/UI/ResultScreen.cs`

- 收进相册
- 本章已收编
- 送你一张
- 下一站
- 回主菜单
- 先收好啦！
- 清完啦！
- 清理
- 金档
- 银档
- 铜档
- 未到铜档
- 下次多收 3 件到银档
- · 下次多收
- 件到
- time · 坚持了 44.9 秒
- 时间到了
- 就差一点点！
- 再吸一次
- 重开 L1
- 进入 L2
- 用羽毛再吸 10 秒

## StoreScreen.Car

源文件：`Assets/_Project/UI/Store/StoreScreen.Car.cs`

- 磁铁
- 吸力 +25% · 15 秒
- 沙漏
- 时间 +5 秒
- 复活羽毛
- 本局 1 次 · 原地复活

## StoreScreen

源文件：`Assets/_Project/UI/StoreScreen.cs`

- 常用道具
- 磁铁
- 吸力 +25% · 15 秒
- 沙漏
- 时间 +5 秒
- 复活羽毛
- 本局 1 次 · 原地复活
- 星沙不够
- 已有 x
- 已攒
- 返回
- 道具铺
- 今日特惠
- 6.1折
- 打扫礼包
- 磁铁 x2 · 沙漏 x3
- 复活羽毛 x1
- 好价常在
- 原价
- 第 2 驻场位
- 已永久解锁
- 已解锁 24 小时
- 视频解锁 24 小时
- 嘟嘟金库

## WardrobeScreen.Car

源文件：`Assets/_Project/UI/Wardrobe/WardrobeScreen.Car.cs`

- 嘟嘟的衣橱
- 先这样

## WardrobeScreen

源文件：`Assets/_Project/UI/WardrobeScreen.cs`

- 失踪袜嘟嘟
- 千纸鹤嘟嘟
- 贝雷嘟嘟
- 木乃伊嘟嘟
- 龙筝嘟嘟
- 手套嘟嘟
- 船桨嘟嘟
- 桌布嘟嘟
- 毛线嘟嘟
- 烟蓑嘟嘟
- 瞌珠嘟嘟
- 留缕嘟嘟
- 花骑嘟嘟
- 穗灯嘟嘟
- 橡贝嘟嘟
- 栗兜嘟嘟
- 云帽嘟嘟
- 归袜嘟嘟
- 嘟嘟的衣橱
- 先这样
- 原皮


## 附录 源文件清单

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
