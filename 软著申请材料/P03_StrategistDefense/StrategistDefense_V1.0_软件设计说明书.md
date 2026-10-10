# 军师救我游戏软件 V1.0 软件设计说明书

## 1. 软件概述

军师救我是一款三国题材塔防肉鸽游戏，运行于Unity引擎，面向Android与iOS小游戏平台。玩家扮演军师，在战场格子上部署武将与防御塔，抵御敌军波次进攻，通过天赋三选一构筑流派，在关卡循环中不断强化阵容。

游戏采用关卡波次结构：BattleLauncher根据当前关卡编号加载敌军配置，BattleSim执行每帧的塔防计算与碰撞判定，BuildService管理武将部署与防御塔建造。每完成一波防守，天赋系统弹出三选一卡牌，玩家从卡池中选择强化方向。

命名空间为Sy.P03，运行时代码共14个.cs文件，有效代码行1749行。

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
| 源程序量 | 约1750行 |

## 3. 系统架构

游戏启动流程由BootRunner驱动，依次执行BootSequence中的场景切换，注入BootServices注册的单例服务。核心服务包括SaveService（本地存档）、BuildService（建造部署）、ShareService（微信分享）、SubscribeService（订阅消息）。

战斗模块由BattleLauncher统一调度：传入LevelState当前关卡与TalentState已激活天赋，BattleSim执行每帧的敌军移动、防御塔攻击判定与伤害结算，BattleView负责渲染血条、伤害飘字与攻击特效。

```
BootRunner → BootSequence → BootServices
                           ├── SaveService
                           ├── BuildService
                           ├── ShareService
                           └── SubscribeService
LevelLauncher → BattleLauncher → BattleSim → BattleView
                              → TalentLauncher → TalentSim → TalentView
```

## 4. 核心模块设计

### 4.1 塔防战斗系统

BattleSim采用格子寻路算法，敌军沿预设路径推进，防御塔在攻击范围内自动锁定目标。空间分区碰撞检测将战场划分为8x8网格，每个格子内的单位距离检测在O(1)复杂度完成。

敌军类型由EnemyTemplates配置：

| 敌军类型 | 基础血量 | 移动速度 | 伤害 | 出现关卡 |
|---|---|---|---|---|
| 步兵 | 40 | 1.0 | 5 | 第1关 |
| 弓兵 | 30 | 1.2 | 8 | 第3关 |
| 骑兵 | 80 | 1.8 | 12 | 第5关 |
| 重甲 | 150 | 0.6 | 20 | 第8关 |
| 战车 | 300 | 0.8 | 35 | 第12关 |

防御塔分为四类：箭塔（单体远程）、炮塔（范围伤害）、冰塔（减速控制）、雷塔（连锁闪电）。BuildService在部署时校验格子可用性与资源消耗。

### 4.2 武将部署系统

BuildService管理武将的招募与部署。武将分为三个兵种：步兵（高血量近战）、弓兵（远程输出）、谋士（范围技能）。每个武将有独立的等级与技能树，部署时消耗粮草资源。

武将技能由SkillTemplates定义，主动技能在战斗中积攒怒气后手动释放，被动技能在满足条件时自动触发。

### 4.3 天赋构筑系统

每完成一波防守后弹出三选一天赋卡牌。天赋卡池分为三个流派：

- **火攻流**：范围灼烧、燃烧持续伤害、击杀后爆炸
- **冰策略**：减速效果强化、冻结概率提升、暴击伤害
- **雷法系**：连锁闪电、攻击速度提升、击杀回蓝

TalentState记录已激活卡牌的组合，BuildSnapshotCodec负责将天赋序列序列化为JSON存档。

### 4.4 关卡波次系统

BattleLauncher根据关卡编号加载波次配置。每关包含5-8波敌军，最后一波为Boss波。Boss属性为同关卡普通敌军的15倍，附带阶段切换：

- 第一阶段（100%-50%血量）：常规攻击
- 第二阶段（50%-0%血量）：召唤援军+狂暴加速

关卡难度由LevelScaling公式动态计算，敌军血量与伤害随关卡数线性增长。

### 4.5 资源经营系统

粮草与银两是核心资源。粮草用于部署武将与建造防御塔，银两用于升级武将与解锁天赋。资源在每波防守结束后自动结算，击杀敌军掉落额外奖励。

BuildService提供加速建造功能，消耗广告点位可立即完成建造。

### 4.6 新手引导系统

TutorialFlow驱动首次进入游戏的引导流程，NewbieSession记录引导步骤进度。引导通过HighLight高亮交互区域，配合UiText中的多语言文本完成教学。SafeAreaMath适配不同屏幕的安全区。

## 5. 数据持久化

SaveService使用PlayerPrefs存储关键进度，BuildSnapshotCodec序列化天赋与武将数据：

```json
{
  "level": 7,
  "gold": 3200,
  "food": 1500,
  "generals": ["zhangfei_lv3", "zhaoyun_lv2"],
  "talents": ["fire_1", "burn_2", "crit_1"],
  "unlocked": {"arrow_tower": true, "ice_tower": true}
}
```

存档在每波结束与退出战斗时自动写入，加载时做版本号兼容校验。

## 6. 社交与增长

ShareService封装微信分享接口，玩家通关或解锁新武将后弹出分享卡片。WxOpenDataBoard驱动微信开放数据域的好友排行榜，FriendBoardPanel展示好友最高关卡。

AdPointFunnel控制广告点位：复活一次、天赋刷新、双倍奖励、加速建造四个点位，由LauncherTelemetry上报转化数据。

## 7. 技术特点

- 格子寻路+空间分区碰撞，同屏50单位掉帧控制在15ms以内
- 天赋卡池40+张，流派组合超过120种
- 武将系统12名可招募武将，3兵种差异化技能
- 关卡波次动态难度，单局时长10-20分钟
- 代码基于Unity引擎C#编写，命名空间Sy.P03统一管理
