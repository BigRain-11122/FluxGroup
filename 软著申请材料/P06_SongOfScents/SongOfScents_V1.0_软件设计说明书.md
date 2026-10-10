# 调香师游戏软件 V1.0 软件设计说明书

## 1. 软件概述

调香师是一款2D经营模拟游戏，运行于Unity引擎，面向Android与iOS小游戏平台。玩家扮演调香师，在小镇上经营一家香氛工坊，通过调配RecipeConfig定义的香料配方吸引不同季节的客人，接待RareGuest配置的稀有访客，逐步扩建FacilityPanel管理的工坊设施。

游戏核心循环为：商店营业 → 接待客人 → 调配香水 → 获得好评 → 升级设施 → 解锁新配方与新季节。ShiftSim模拟每个班次的客流，SeasonOracle根据当前季节调整客人偏好与商品价格。

命名空间为Sy.P06，运行时代码共56个.cs文件，有效代码行9158行。

## 2. 运行环境

| 项目 | 配置 |
|---|---|
| 开发硬件 | Intel i7处理器，16GB内存，512GB SSD |
| 运行硬件 | ARM四核处理器，2GB内存，占用空间100-150MB，触控屏 |
| 开发操作系统 | Windows 10 |
| 开发工具 | Unity 2022，Visual Studio 2022 |
| 运行平台 | Android 8.0+，iOS 12.0+，微信小游戏平台 |
| 支撑环境 | Unity Runtime |
| 编程语言 | C# |
| 源程序量 | 约9200行 |

## 3. 系统架构

启动流程由BootRunner驱动BootSequence，注入BootServices注册的核心服务。经营模块由ShopSim驱动：ShopView渲染商店场景，GuestConfig定义客人行为，ReceptionOracle处理接待流程，ScentAtmosphere计算当前氛围值。

```
BootRunner → BootSequence → BootServices
ShopSim → ShopView → GuestConfig → ReceptionOracle
       → RecipeConfig → RecipeHint → SeasonCardComposer
       → FacilityPanel → FacilityProgress
       → CaravanPanel → CaravanSupply
       → LetterInbox → LetterPanel → LetterConfig
SeasonOracle → SeasonMood → SeasonPalette
```

## 4. 核心模块设计

### 4.1 配方调配系统

RecipeConfig定义了超过80种香水配方，每种配方由3-5种香料组合而成。ScentCard表示一张配方卡，ScentLureConfig定义每种香料的吸引属性：

| 香料类别 | 吸引季节 | 吸引客人类型 | 基础价格 |
|---|---|---|---|
| 花香 | 春 | 年轻女性 | 12金币 |
| 木香 | 秋 | 中年男性 | 18金币 |
| 果香 | 夏 | 家庭客人 | 15金币 |
| 海洋 | 夏 | 年轻男性 | 20金币 |
| 东方 | 冬 | 稀有客人 | 35金币 |

RecipeHint在玩家调配失败时给出提示，CraftSpeedOracle控制调配动画速度。

### 4.2 客人接待系统

GuestConfig定义了普通客人的行为模式：进店 → 浏览货架 → 询问推荐 → 试香 → 购买或离开。GuestVariantOracle根据当前季节生成客人变体。

RareGuest配置了特殊稀有客人，每24小时随机出现一位：

| 稀有客人 | 触发条件 | 购买倾向 | 好感度奖励 |
|---|---|---|---|
| 香水评论家 | 店铺等级3 | 东方调 | 解锁高级配方 |
| 皇室使者 | 季节切换时 | 花香调 | 设施折扣 |
| 流浪调香师 | 连续签到7天 | 自由调配 | 赠送珍稀香料 |

ReceptionOracle处理接待流程，RareGuestBoostOracle在稀有客人出现时提升全店氛围值。

### 4.3 设施升级系统

FacilityPanel管理工坊设施建设：

| 设施 | 功能 | 最高等级 | 升级费用 |
|---|---|---|---|
| 货架 | 增加陈列位 | 5 | 500-5000金币 |
| 调香台 | 提升调配速度 | 5 | 800-8000金币 |
| 休息区 | 增加客人停留时间 | 3 | 1200-6000金币 |
| 橱窗 | 吸引路人进店 | 3 | 600-3000金币 |
| 储藏室 | 增加香料库存上限 | 5 | 400-4000金币 |

FacilityProgress记录每项设施的当前等级。

### 4.4 季节系统

SeasonOracle驱动四季循环，每个季节持续现实时间7天。SeasonMood定义当前季节的情绪基调，SeasonPalette切换商店配色方案。

| 季节 | 客流倍率 | 热销品类 | 特殊事件 |
|---|---|---|---|
| 春 | 1.2x | 花香 | 樱花限定配方 |
| 夏 | 1.5x | 果香/海洋 | 海边度假客人 |
| 秋 | 1.0x | 木香 | 丰收节折扣 |
| 冬 | 0.8x | 东方 | 新年限量版 |

SeasonCardComposer在季节切换时生成纪念卡片。

### 4.5 商队与信件系统

CaravanPanel管理商队补给：每48小时商队到访，玩家可购买稀有香料与限时商品。CaravanSupply定义库存清单。

LetterInbox接收客人来信，LetterPanel展示信件内容，LetterConfig定义触发条件。每封信附带小礼物或配方线索。

### 4.6 图鉴与故事系统

CodexPanel记录已解锁的配方、客人、设施图鉴。CodexProgress计算完成百分比。BookCompleteOracle在图鉴全部完成时触发特殊结局。

StoryPanel展示解锁的剧情故事，StoryCardComposer生成故事卡片，StoryBoard管理故事线进度。

## 5. 数据持久化

FormalSessionSave序列化经营进度：

```json
{
  "shopLevel": 4,
  "gold": 28500,
  "facilities": {"shelf": 3, "bench": 2, "lounge": 1},
  "recipes": {"rose_01": true, "sandalwood_03": true},
  "guests_met": 47,
  "season": "spring",
  "letters_received": 12
}
```

SignInPanel驱动每日签到，SignDoubleOracle在连续签到时给予双倍奖励。

## 6. 增长与广告

AdPointTable定义广告点位：双倍收益、免费香料、稀有客人刷新。InterstitialSettleOracle在班次结束时弹出结算插屏。GiftImport与GiftLinkCodec处理分享链接，GiftLinkOracle奖励邀请好友的玩家。

## 7. 技术特点

- 80+配方组合，客人类型30+
- 四季动态循环，商品与客流随季节变化
- 设施升级树5级深度
- 图鉴收集驱动长期目标
- 代码基于Unity引擎C#编写，命名空间Sy.P06统一管理

## 8. Steam买断分支说明

本项目规划Steam买断制分支。Steam版移除广告点位，改为纯单机经营模拟体验：

- 移除所有IAA广告点位，双倍收益与免费香料改为游戏内玩法
- 增加深度内容：更多配方组合、客人类型、季节事件
- 增加剧情模式：调香师的成长故事与NPC关系线
- 支持Steam成就与云存档
- 支持键鼠操作与界面缩放
- 定价策略：买断制，后续DLC扩展新配方与新场景
