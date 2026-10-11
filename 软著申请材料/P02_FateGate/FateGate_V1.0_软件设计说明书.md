# 异界行者游戏软件 V1.0 软件设计说明书

## 1. 软件概述

异界行者是一款2D塔防策略游戏，运行于Unity引擎，面向Android与iOS小游戏平台。玩家通过DestinyGate穿越不同命运棋盘，在Grid地图上布阵防御敌人波次，利用SummonPool召唤单位强化防线，击败TimedWaveProfile配置的定时进攻。

游戏核心循环为：进入命运棋盘 → 布防单位 → 抵御波次 → 获得奖励 → 强化召唤池 → 穿越下一扇门。OfflineEarnings在离线期间自动累积金币与经验。

命名空间为Sy.P02，运行时代码共48个.cs文件，有效代码行10969行。

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
| 源程序量 | 约11000行 |

## 3. 系统架构

启动流程由BootRunner驱动BootSequence，注入BootServices注册的核心服务。战斗模块由BattleLauncher调度：RandomLevel生成随机关卡棋盘，BoardFormation处理单位布阵逻辑，BattleSim执行每帧攻击与移动判定，BattleView渲染塔防场景。

```
BootRunner → BootSequence → BootServices
DestinyGate → DestinyBoard → DestinyPin → GateTable
RandomLevel → BoardFormation → BattleSim → BattleView
                            → SummonPool → SummonWeightTable
DefenseChallenge → DefenseSnapshot → DefenseReplay → DefenseReward
OfflineEarnings → LuckyWallet → LuckyTable
```

## 4. 核心模块设计

### 4.1 命运棋盘系统

DestinyBoard是游戏核心地图载体，由DestinyPin节点组成路径网络。每扇DestinyGate对应一个棋盘主题，GateTable定义了12种棋盘配置：平原、森林、沙漠、雪原、遗迹、深渊、火山、水城、天宫、幽冥、镜界、混沌。

棋盘宽度为固定12格，路径长度随机生成。玩家在非路径格子上放置防御单位，敌人沿路径从起点向终点移动。

### 4.2 战斗系统

BattleSim每帧执行以下逻辑：
1. 遍历所有敌人，沿路径点移动
2. 遍历所有防御单位，检测攻击范围内的敌人
3. 命中后扣除血量，触发暴击判定
4. 敌人血量归零时掉落金币，触发击杀奖励

防御单位由UnitTable定义基础属性：

| 单位 | 攻击范围 | 攻击间隔 | 伤害 | 解锁条件 |
|---|---|---|---|---|
| 弓箭手 | 3格 | 1.0s | 12 | 默认 |
| 法师 | 2格 | 1.5s | 25 | 第3门 |
| 炮手 | 2格 | 2.0s | 40（溅射） | 第6门 |
| 治疗师 | 3格 | 1.2s | 回血8/帧 | 第9门 |
| 龙骑士 | 4格 | 1.8s | 60 | 第12门 |

### 4.3 召唤池系统

SummonPool是单位获取核心。SummonWeightTable定义了不同稀有度的召唤权重：

- 普通单位：权重60
- 稀有单位：权重25
- 史诗单位：权重10
- 传说单位：权重5

每次召唤消耗LuckyWallet中的幸运石，幸运石通过DefenseReward通关获得。MythicTable定义了传说级单位的专属技能。

### 4.4 防御挑战系统

DefenseChallenge提供无尽模式。玩家通关主线棋盘后可进入无尽波次，每10波难度递增。DefenseSnapshot记录最佳战绩，DefenseReplay回放通关过程，DefenseReward按波数发放奖励。

### 4.5 离线收益系统

OfflineEarnings计算离线期间的收益：
- 基础金币产出 = 已解锁棋盘数 × 100 × 离线小时数
- 经验产出 = 已通关波数 × 5 × 离线小时数
- 上限为12小时

LuckyWallet管理幸运石余额，LuckyTable定义了每日免费召唤次数。

### 4.6 图鉴系统

CodexView展示已解锁的单位、棋盘、敌人图鉴。每解锁新条目弹出收集动画。StarCardTable定义了星级升级路径，单位可通过重复召唤升星，每星提升20%基础属性。

## 5. 数据持久化

存档包含当前进度、召唤池、单位星级、最佳战绩：

```json
{
  "currentGate": 5,
  "gold": 12500,
  "luckyStones": 320,
  "units": {"archer": 2, "mage": 3, "cannon": 1},
  "starLevels": {"archer": 2, "mage": 1},
  "bestWave": 27
}
```

## 6. 社交与分享

ShareReturn封装分享回调，玩家通关后分享可获得一次免费召唤机会。ShareCardSpecs定义分享卡片的文案与素材。TutorialFlow驱动首次进入的引导流程，NewbieConfig配置新手保护期内的难度系数。

## 7. 技术特点

- 随机关卡生成，每局体验不同
- 召唤池权重系统，稀有度梯度明确
- 离线收益自动累积，上线即有回报
- 无尽挑战模式延长游戏寿命
- 代码基于Unity引擎C#编写，命名空间Sy.P02统一管理

## 8. Steam买断分支说明

本项目规划Steam买断制分支。Steam版移除广告点位与离线收益限制，改为纯单机塔防策略体验：

- 移除所有IAA广告点位，召唤与刷新改为游戏内资源消耗
- 增加深度内容：更多命运棋盘主题、召唤单位类型、Boss波次
- 增加自定义关卡编辑器与创意工坊分享
- 支持Steam成就与云存档
- 支持键鼠操作与快捷键自定义
- 定价策略：买断制，后续DLC扩展新棋盘与新单位
