# 提灯斩鬼游戏软件 V1.0 软件设计说明书

## 1. 软件概述

提灯斩鬼是一款2D俯视角动作肉鸽游戏，运行于Unity引擎，面向Android与iOS小游戏平台。玩家手持提灯在暗域中探索，通过击杀游魂收集魂火，在天数循环中强化天赋、构筑流派，最终挑战Boss波次通关。

游戏采用昼夜双循环结构：白天在MapService生成的格子地图上移动搜刮，夜晚进入BattleSim驱动的战斗场景迎击EnemyTemplates配置的游魂波次。每完成一个DaySim周期，TalentLauncher弹出三选一的天赋卡牌，玩家从BuildCardSpecs定义的卡池中抽选强化方向。

命名空间为Sy.P01，运行时代码共49个.cs文件，有效代码行9570行。

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
| 源程序量 | 约9500行 |

## 3. 系统架构

游戏启动流程由BootRunner驱动，依次执行BootSequence中的场景切换，注入BootServices注册的单例服务。核心服务包括SaveService（本地存档）、MapService（地图生成）、ShareService（微信分享）、SubscribeService（订阅消息）。

战斗模块由BattleLauncher统一调度：传入DayState当前天数与TalentState已激活天赋，BattleSim执行每帧的位移与碰撞检测，BattleView负责渲染敌人血条、伤害飘字与魂火粒子。

```
BootRunner → BootSequence → BootServices
                           ├── SaveService
                           ├── MapService
                           ├── ShareService
                           └── SubscribeService
DayLauncher → DaySim → DayState → BattleLauncher → BattleSim → BattleView
                                          → TalentLauncher → TalentSim → TalentView
```

## 4. 核心模块设计

### 4.1 天数循环系统

DayState维护当前天数、存活状态、已完成波次数。DaySim在每帧推进时间轴，当时间到达夜晚阈值时自动调用BattleLauncher进入战斗。白天阶段玩家在格子地图上自由移动，触发MapService中的事件点。

天数上限由NewbieConfig中的新手保护期与EndlessRunCheck校验的无尽模式共同决定。普通模式第15天解锁BossWaveDirector导演的最终Boss战。

### 4.2 战斗系统

BattleSim采用SpatialHashGrid做空间分区碰撞，每个敌人与玩家的距离检测在O(1)复杂度完成。EnemyTemplates定义了游魂的基础属性表：

| 敌人类型 | 基础血量 | 移动速度 | 伤害 | 出现天数 |
|---|---|---|---|---|
| 游魂 | 30 | 1.2 | 5 | 第1天 |
| 怨魂 | 60 | 1.0 | 10 | 第3天 |
| 厉鬼 | 120 | 1.4 | 18 | 第6天 |
| 煞 | 250 | 0.8 | 30 | 第10天 |

玩家攻击判定由提灯范围触发，范围半径默认为1.5格，天赋可扩展至3.0格。击杀敌人掉落魂火，魂火自动吸附至玩家，每100点魂火提升一次生命上限。

### 4.3 天赋构筑系统

TalentSim在每个天数结束后弹出三选一卡牌。BuildCardSpecs定义了超过60张天赋卡，分为三个流派：

- **火流派**：提灯范围扩大、魂火吸附距离增加、灼烧持续伤害
- **冰流派**：击杀后短暂冻结、移动速度提升、闪避概率
- **雷流派**：连锁闪电、暴击率提升、击杀后爆发

TalentState记录已激活卡牌的组合，TalentView在主界面显示当前流派标识。BuildSnapshotCodec负责将天赋序列序列化为JSON存档，SaveService持久化至本地。

### 4.4 Boss波次系统

BossWaveDirector在第5天、第10天、第15天分别触发Boss战。Boss属性由BossWaveCheck校验，血量为同天数普通敌人的20倍，附带阶段切换：

- 第一阶段（100%-60%血量）：直线冲撞
- 第二阶段（60%-30%血量）：召唤3个游魂护卫
- 第三阶段（30%-0%血量）：全屏弹幕

### 4.5 图鉴收集系统

CollectionBook记录已击杀过的敌人种类、已解锁的天赋卡牌、已通关的天数。每解锁一个新条目弹出CodexFlowCheck校验的动画反馈。图鉴完成度在MainUI显示百分比。

### 4.6 新手引导系统

TutorialFlow驱动首次进入游戏的引导流程，NewbieSession记录引导步骤进度。引导通过HighLight高亮交互区域，配合UiText中的多语言文本完成教学。SafeAreaMath适配不同屏幕的安全区。

## 5. 数据持久化

SaveService使用PlayerPrefs存储关键进度，BuildSnapshotCodec序列化天赋与图鉴数据：

```json
{
  "day": 7,
  "hp": 150,
  "soulFire": 320,
  "talents": ["range_up_1", "burn_1", "crit_2"],
  "codex": {"wraith": true, "revenant": true}
}
```

存档在每次天数结束与退出战斗时自动写入，加载时做版本号兼容校验。

## 6. 社交与增长

ShareService封装微信分享接口，玩家通关或解锁图鉴后弹出分享卡片，卡片素材由ReportCardSpecs定义。WxOpenDataBoard驱动微信开放数据域的好友排行榜，FriendBoardPanel展示好友最高天数。

AdPointFunnel控制广告点位：复活一次、天赋刷新、双倍奖励三个点位，由LauncherTelemetry上报转化数据。

## 7. 技术特点

- 空间哈希网格碰撞，百人同屏掉帧控制在20ms以内
- 天赋卡池60+张，流派组合超过200种
- 昼夜双循环驱动，单局时长15-25分钟
- 代码基于Unity引擎C#编写，命名空间Sy.P01统一管理

## 8. Steam买断分支说明

本项目规划Steam买断制分支。Steam版移除广告点位，改为纯单机动作肉鸽体验：

- 移除所有IAA广告点位，天赋刷新与复活改为游戏内资源消耗
- 增加深度内容：更多天赋卡牌、敌人类型、Boss战机制
- 增加每日挑战模式与种子分享功能
- 支持Steam成就、排行榜与云存档
- 支持手柄操作与键鼠自定义键位
- 定价策略：买断制，后续DLC扩展新天赋与新Boss
