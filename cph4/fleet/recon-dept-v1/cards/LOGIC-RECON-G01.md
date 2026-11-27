# G-01 逻辑与数值还原（LOGIC-RECON）

> 对象：《向僵尸开炮》Android 版 `com.xjskp.gztv1.hnsc` v1.10（Unity 2021.3.30f1 / IL2CPP arm64）
> 方法：解包 → Il2CppDumper 还原类型与字段 → Cpp2IL 还原 IL → 解配置表二进制
> 证据分级：**[A] 直接从产物还原** ／ **[B] 由字段语义推定** ／ **[C] 待验证**
> 合规：只用于理解结构与数值，不搬运代码/资源。

## 一、已确认的系统骨架 [A]

从 `global-metadata.dat`（8.9MB）枚举出的类型符号（按域计数）：

| 域 | 类型/符号数 | 代表类型 |
|---|---|---|
| 战斗 | 1,741 | `ActorAttrData`、`ActorBuffStateChange`、`BattleBossHpData` |
| 技能/构筑 | 2,344 | `ActiveSkill`、`ActiveSkillCfgMgr`、`AbysSkillSelectItem` |
| 关卡/波次 | 1,688 | `LevelWaveConfig`、`ActorWave`、`AbyssInitLevel` |
| 成长/任务 | 972 | `AchieveLevelAwardData`、`Task*` |
| UI/流程 | 2,470 | `*Panel`/`*Popup`/`*Tips` |
| 经济 | 790 | `BuyDiamond`、`AddGold`、`GoodsConfig` |
| 关卡生成 | 557 | `SnakeMonsterGroup`、`Path`/`Grid` |
| 存档/账号 | 438 | `PlayerData`、`Save*` |
| 广告/变现 | 139 | `CSAdConfigEntry`、`CSAdVideoProgressAwardCfgEntry` |

配置表结构**全量导出**：**3,164 张表 / 10,106 个字段** →
`media/recon/apk/il2cpp_out/schema.json`（生成脚本 `Tools/recon/dump_schema.py`）。

## 二、关卡/波次系统 —— 真实字段 [A]

`LevelWaveConfig`（29 字段，顺序即序列化顺序）：

| 字段 | 类型 | 作用 |
|---|---|---|
| `LevelID` / `WaveID` / `Wave` | uint/uint/int | 关卡与波次标识 |
| `WaveType` | uint | 波次类型（普通/精英/BOSS/事件） |
| **`TriggerTime`** | float | 该波触发时间（秒） |
| `TriggerType` / `TriggerParams[]` | byte/int[] | 触发方式（时间/击杀数/区域） |
| `MonsterID` | uint | 本波主怪 |
| **`MonsterNum` / `MonsterNumRangeRatio`** | int/float | 总数与浮动比例 |
| **`FirstRefreshNum`** | int | 进波立即刷新的数量 |
| **`Interval` / `SingleRefreshNum`** | float/int | 后续分批间隔与每批数量 |
| `DistributeByte` | uint | 分布位掩码（出怪方向/区域） |
| **`AtkRatio` / `HpRatio`** | float | 本波攻/血倍率 |
| `DropItemPoolID` / `GoldDrop` | uint | 掉落池与金币 |
| `FinishDropFirst/Second/Third` | uint | 完成奖励三档 |
| `MonsterLibraryID` / `MonsterDrawCount` | uint/uint | 随机怪物库与抽取数 |
| **`EliteRefreshTime[]` / `BossRefreshTime[]`** | uint[] | 精英/BOSS 在该波内的刷新时刻 |
| `SnakeMonsterGroup` | byte | 蛇形怪编组标记 |

**结论：这不是"每 30 秒一波"的简单模型，而是"每波带触发时间 + 分批刷新 + 独立精英/BOSS 时刻表 + 每波独立攻血倍率"的数据驱动关卡。**
本原型 v0.2 已按这套字段实现（见下）。

## 三、怪物系统 —— 真实字段 [A]

`MonsterCfg`（42 字段）关键项：
`MonsterID`、`ModelID`、`Type`、`Hp`、`HpCount`（多段血量）、`Atk`、`MoveSpeed`、
`Skills[]`、`AttachSkill`、`AITaskID`、`DefaultAttr[]`、`ModelScale`、
`BornBuffID[]`、`IsShowHp`、`CanColliderDamage`、`IsFly`、`NoMove`、
`EarlyWarningType/Param/Time`（预警）、`MissMoveDis/Speed/Interval`（脱战移动）。

## 四、技能系统 —— 真实字段 [A]

`SkillBaseConfg`（24 字段）：
`SkillID`、`SkillType`、`CloseAutoUse`、`SkillRangeType`、`SkillIcon`、`GCDID`、
`CostMP`、`SkillCD` / `MinSkillCD`、`SkillDurationTime`、`DynamicCD`、
`AttrDamageData[]`、`BuffID[]`、`CanBeSilence`、`SkillCastType`。

## 五、关卡基础与经济 [A/B]

`LevelBaseConfig`（37 字段）：
`LevelID`、`PreLevelID`、`LevelType`、`MaxPlayerCnt`、`CurrencyType/Num`、
`RandomSkillPoolID`（本关升级池）、`PassBooty[]`（通关奖励，含星级）、
`PatrolBooty/PatrolTime`、`AttackRatio`/`HpRatio`/`HpCountRatio`（关卡整体倍率）、
**`PassValue` / `ValueMax`**（通关阈值/目标值）、
**`MpRecoverInterval` / `MpRecoverValue`**（技能能量恢复）、`BanOverflowDamage`。

## 六、配置表二进制格式 [C]

- 头部：`00 00 2d 3f | payloadLen | version=1`
- 已确认：整数为大端；字符串带长度前缀；存在 `0x3F` 高频字节（疑似定长/压缩字段）
- **尚未完成**：`ProtoBaseStruct.pack/unpack` 的逐字段解码。公开仓库无此框架（已查 GitHub，零命中），
  正用 **Cpp2IL** 还原 `unpack()` 的 IL，再据此写解码器取**原表数值**。
- 在此之前，原型数值全部标注为"标定值"，不冒充原表。

## 七、已落进原型 v0.2 的映射

| 竞品字段 | 原型实现 |
|---|---|
| `TriggerTime` | 每波按绝对时间触发（不再固定 30s） |
| `FirstRefreshNum` | 进波立即刷一批 |
| `SingleRefreshNum` + `Interval` | 波内分批刷新 |
| `MonsterNum` | 该波剩余待刷总数 |
| `EliteRefreshTime[]` / `BossRefreshTime[]` | 独立队列，到点刷精英/BOSS |
| `AtkRatio` / `HpRatio` + `LevelBase.AttackRatio/HpRatio` | 每波、每关双层倍率 |
| `PassValue` / `ValueMax` | 通关判定（击杀数达目标）+ 三星评价 |
| `CurrencyNum` | 通关货币奖励 |
| `MpRecoverInterval/Value` | 技能能量条恢复 |

## 八、待办（不做完不算收口）

1. Cpp2IL 还原 `unpack()` → 解 `MonsterCfg` / `LevelWaveConfig` / `LevelBaseConfig` / `SkillBaseConfg` 原表。
2. 用原表数值替换原型的标定值（数值不自己拍）。
3. 换皮（美术/题材/音效）放在数值与逻辑对齐之后。