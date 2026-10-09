# 萌宠开店啦游戏软件 V1.0 软件设计说明书

## 1 软件概述

竖屏萌宠放置经营小游戏。玩家经营一家宠物打工小队，招募猫狗、把它们派到咖啡店、快递站、洗车行、钓鱼点等岗位上打工赚金币，攒金币开新岗位、招新宠物、升店铺星级。宠物有自己的亲和岗位和怪癖，干喜欢的活工资更高，还会时不时闹出喜剧事件。

数据本地存储不连服务器，激励视频变现。团结引擎C#开发，数值全部冻结在 PetData 里，结构改动要升 SchemaVersion。

## 2 运行环境

| 项 | 要求 |
|---|---|
| 操作系统 | Android 8.0及以上 / iOS 12.0及以上 |
| 运行平台 | 微信小游戏、抖音小游戏、移动端 |
| 游戏引擎 | Unity 2021.3 LTS（团结引擎1.10.3） |
| 编程语言 | C# |
| 运行内存 | 2GB以上 |
| 存储空间 | 100MB以上 |
| 屏幕分辨率 | 720x1280以上，竖屏 |

## 3 工程结构

运行时代码在 `Assets/_Game/Scripts/Runtime/`：

```
Runtime/
├─ Boot/
│  ├─ BootRunner.cs
│  ├─ BootSequence.cs
│  └─ BootServices.cs
├─ Game/
│  ├─ PetData.cs          全部数值真相表
│  ├─ PetSim.cs           模拟核心
│  ├─ PetMainHost.cs      MonoBehaviour主宿主
│  ├─ PetSaveData.cs      存档结构
│  ├─ PetDexView.cs       宠物图鉴
│  └─ PetDispatch.cs      派工
├─ Copy/
│  ├─ CopyTable.cs        英文文案表
│  ├─ CopyTableZh.cs      中文文案表
│  └─ CopyLocaleService.cs 多语言切换
├─ Iaa/
│  └─ IaaGate.cs
├─ Audio/
│  └─ G15AudioCatalog.cs
└─ UI/
   ├─ ShopView.cs
   └─ EventCardView.cs
```

## 4 岗位系统

PetData.Jobs 定义10个岗位，每个岗位有解锁店铺等级、基础每秒产出、首次开店成本：

| 岗位 | Id | 解锁等级 | 基础速率 | 开店成本 |
|---|---|---|---|---|
| 咖啡店 | job_coffee | R1 | 40 | 0（免费） |
| 快递站 | job_courier | R2 | 60 | 300 |
| 洗车行 | job_carwash | R2 | 55 | 280 |
| 钓鱼点 | job_fish | R3 | 90 | 800 |
| 花店 | job_flower | R3 | 85 | 750 |
| 烘焙坊 | job_bakery | R4 | 130 | 1800 |
| 书店 | job_book | R4 | 120 | 1600 |
| 修车铺 | job_garage | R4 | 180 | 3600 |
| 果园 | job_orchard | R4 | 170 | 3200 |
| 消防站 | job_fire | R5 | 250 | 8000 |

咖啡店免费开，是开局锚点，保证玩家进来第一秒就有产出。

## 5 岗位产出软帽

岗位升级后产出不是线性涨，走对数软帽，防止单个岗位堆太高：

```
// 数值包律2：等级产出 = 基础 × (1 + 0.25 × ln(等级 + 1))
double JobRatePerSec(int jobId, int level)
{
    return Jobs[jobId].BaseRatePerSec
         * (1.0 + 0.25 * Math.Log(level + 1.0));
}
```

对数软帽让前几级提升明显、越往后越平，逼着玩家把金币投向下一个岗位而不是平均撒。

## 6 升级成本与等级上限

升级成本是线性的，开店成本乘以等级，没有指数：

```
double JobUpgradeCost(int jobId, int level)
{
    if (jobId == JobCoffee) return CoffeeUpgradeCostBase * level;
    return Jobs[jobId].OpenCost * level;
}
```

咖啡店开店免费，若按零乘等级会永远零成本退化，所以单独冻结基础250、升级费250×等级。这个250是在扫参网格200到600、步长50里，按首次升级回本周期最接近60秒核心决策节奏选出来的。

岗位最高30级，到顶拒绝再投、状态不变，避免误操作把钱全砸一个岗位。

## 7 店铺晋升

店铺共5阶，从R1到R5。晋升要同时满足三道单调门槛：

| 升阶 | 至少开岗位 | 至少招宠物 | 至少星级 |
|---|---|---|---|
| R1→R2 | 1 | 2 | 1 |
| R2→R3 | 3 | 4 | 2 |
| R3→R4 | 5 | 7 | 3 |
| R4→R5 | 8 | 10 | 4 |

三道门槛分别查已开岗位数、图鉴宠物数、店铺星级，光攒金币跳不过去。早期版本修车铺和果园错配在R5，会把R4到R5的门槛锁死（要求8个岗位但R4只能开7个），已重新冻结到R4。

## 8 星级系统

店铺星级代表口碑，只升不降，不做衰减、不做签到、不做比拼：

| 常量 | 值 | 含义 |
|---|---|---|
| StarDustPerMinPerPet | 1.0 | 每个在岗宠物每分钟产1星尘 |
| StarDustDexBonusCoef | 0.05 | 图鉴宠物每多一只，星尘乘(1+0.05×数量) |
| StarUpCostBase | 100 | 升星成本=100×(当前星级+1) |
| StarMax | 5 | 最高5星 |

在岗宠物越多、图鉴越全，星尘攒得越快，攒够就升星，星级又是晋升门槛之一，形成闭环。

## 9 宠物招募

宠物用金币直接购买，不做随机获取。共12只，6猫6狗，开局免费送一只橘猫：

| 宠物 | Id | 种类 | 招募成本 |
|---|---|---|---|
| 橘猫 | pet_orange | 猫 | 0（免费） |
| 雪球 | pet_snowball | 猫 | 200 |
| 柯基 | pet_corgi | 狗 | 350 |
| 金毛 | pet_goldie | 狗 | 600 |
| 豆豆 | pet_bean | 狗 | 850 |
| 芝麻 | pet_sesame | 猫 | 1200 |
| 漩涡 | pet_swirl | 猫 | 1500 |
| 布丁 | pet_pudding | 猫 | 2200 |
| 暗影 | pet_shadow | 猫 | 3200 |
| 大壮 | pet_brawn | 狗 | 4500 |
| 闪电 | pet_flash | 狗 | 6500 |
| 阿旺 | pet_awang | 狗 | 9000 |

阿旺是消防站的终局伙伴宠。

招募是金币直购，三道校验——越界id拒、已招拒、钱不够拒，全部零状态改动，通过才扣款、置位、图鉴数加一：

```
RecruitResult RecruitPet(int petId)
{
    if (petId < 0 || petId >= PetCount) return NoCoin;
    if (_petRecruited[petId]) return AlreadyRecruited;
    double cost = RecruitCosts[petId];
    if (_coin < cost) return NoCoin;
    _coin -= cost;
    _petRecruited[petId] = true;
    _dexCount++;
    if (FirstRecruitT < 0f) FirstRecruitT = (float)_simTime;
    OnPetRecruited?.Invoke(petId, (float)_simTime);
    OnIdlePetsChanged?.Invoke(IdlePetCount, (float)_simTime);
    EvaluateAchievements();
    return Ok;
}
```

开店 OpenJob 同样校验职级门槛和开店成本，未到职级直接拒、不扣钱。里程碑赠送走 GiftPet，只置位不动金币，零随机获取零概率。

## 10 宠物图鉴与被动

每只宠物有亲和岗位、一个被动技能和一个喜剧怪癖。被动分三类：收益加成、速度加成、星级加成。

| 宠物 | 亲和岗位 | 被动 | 数值 | 怪癖 |
|---|---|---|---|---|
| 橘猫 | 咖啡店 | 收益 | +10% | 偷三文鱼 |
| 雪球 | 咖啡店 | 速度 | +15% | 睡在机器上 |
| 柯基 | 快递站 | 速度 | +20% | 被自己耳朵绊倒 |
| 金毛 | 钓鱼点 | 收益 | +15% | 烤鱼 |
| 豆豆 | 洗车行 | 收益 | +10% | 洗成毛球 |
| 芝麻 | 钓鱼点 | 收益 | +20% | 藏鱼 |
| 漩涡 | 花店 | 星级 | +5% | 偷拍柯基 |
| 布丁 | 烘焙坊 | 收益 | +10% | 在面团里打盹 |
| 暗影 | 快递站 | 速度 | +15% | 送错门被感谢 |
| 大壮 | 果园 | 收益 | +15% | 把树吼秃 |
| 闪电 | 修车铺 | 收益 | +10% | 越修越坏 |
| 阿旺 | 消防站 | 收益 | +25% | 救援时烤肠 |

名称走多语言键，不硬编码。

## 11 派工与亲和匹配

玩家把宠物拖到岗位上派工。宠物干自己的亲和岗位时，工资节拍乘1.25：

```
// 亲和匹配律：干喜欢的活 +25% 工资
bool IsAffinityMatch(int petId, int jobId)
{
    return petId >= 0 && petId < PetCount
        && PetDex[petId].AffinityJob == jobId;
}
```

只做正反馈：匹配拿1.25倍，不匹配拿正好的基础工资，不罚钱。派工因此是个真实决策——把对的宠物放对岗位收益更高。

## 12 喜剧事件

在线时每180到300秒，在在岗宠物所属岗位里 roll 一个事件。事件分喜剧和暖心两类，结算时做一次星尘修正（±5到10）并可收集进事件相册：

| Id | 岗位 | 类型 | 演出 | 星尘 |
|---|---|---|---|---|
| event_e01 | 快递 | 喜剧 | 包裹翻倒 | +8 |
| event_e02 | 烘焙 | 喜剧 | 装睡被摄像头拍到 | +6 |
| event_e03 | 修车 | 喜剧 | 点赞事故车 | +10 |
| event_e04 | 消防 | 暖心 | 烤肠救援 | +7 |
| event_e05 | 咖啡 | 喜剧 | 狗拿铁 | +6 |
| event_e06 | 钓鱼 | 喜剧 | 放生鱼 | +9 |
| event_e07 | 洗车 | 喜剧 | 毛球翻滚 | +8 |
| event_e08 | 果园 | 喜剧 | 咆哮丰收 | +10 |
| event_e09 | 花店 | 喜剧 | 偷拍柯基 | +5 |
| event_e10 | 快递 | 暖心 | 送错门五星好评 | +9 |

所有数值都是正的，喜剧从不惩罚，怪癖和意外是零数值惩罚的笑点。event_e01 同时是脚本化的首个笑点卡，保证新玩家很快笑一次。

## 13 双选选择卡

除了自动结算的事件，还有双按钮选择卡。玩家在两个选项里选一个，两个选项都是正向的，差别只在拿多拿少：

| 卡 | 岗位 | A臂 | B臂 |
|---|---|---|---|
| event_c00 | 咖啡 | 风险臂：零星尘+暂停工资30秒 | +4星尘+相册位 |
| event_c01 | 快递 | 风险臂：零星尘+暂停工资30秒 | +4星尘+相册位，插旗解锁c02 |
| event_c02 | 快递 | 风险臂：零星尘+暂停工资30秒 | +4星尘+相册位（需c01旗） |

选择卡每解决1到2张自动卡出现一次，避免决策疲劳。唯一的损失面是明示的风险臂：零星尘并让来源岗位暂停工资30秒，这是为了不让策略位结构性必胜。B臂插的故事旗会解锁后续卡，形成回调弧。

每次自动事件结算后推进选择窗口，窗口剩余次数走确定性哈希、不用随机API：

```
void AdvanceChoiceWindow()
{
    if (!ChoiceViewLive || _choicePendingId >= 0) return;
    if (_choiceWindowLeft < 0)
    {
        int span = ChoiceCadenceMaxResolves - ChoiceCadenceMinResolves + 1;
        _choiceWindowLeft = ChoiceCadenceMinResolves
            + (int)(Mix32(0x51ed270bu + (uint)_eventResolveCount) % (uint)span);
    }
    _choiceWindowLeft--;
    if (_choiceWindowLeft > 0) return;
    int c = RollChoiceEvent();
    if (c >= 0)
    {
        _choicePendingId = c;
        _choiceWindowLeft = -1;
        OnChoiceOpened?.Invoke(c, (float)_simTime);
    }
    else _choiceWindowLeft = ChoiceCadenceMinResolves;
}

int RollChoiceEvent()
{
    int eligible = 0;
    for (int c = 0; c < ChoiceCount; c++)
    {
        var d = ChoiceEvents[c];
        if (d.ReqFlag >= 0 && !_choiceFlags[d.ReqFlag]) continue;
        if (!_jobUnlocked[d.Job] || _jobPet[d.Job] < 0) continue;
        eligible++;
    }
    if (eligible == 0) return -1;
    // 确定性哈希在合格集里挑一张
    ...
}
```

合格集为空时诚实跳过、重开窗口，不硬塞一张无人能接的卡。待处理卡期间自动节奏暂停，保证一次只面对一个决策。

## 14 打工明信片

明信片相册是进度条式收集，不靠概率。每个(宠物,岗位)对的工作时间累计，干满一条4小时的工作条必得一张明信片：

| 常量 | 值 |
|---|---|
| PostcardWorkSecPerCard | 4小时（14400秒） |
| PostcardPairCount | 12宠物×10岗位=120 |
| PostcardAlbumCapacity | 120张起 |

在线节拍和离线计入时长都算数，是真正的放置收集。明信片Id格式 `pc_<宠物>_<岗位>`，同时是相册和分享的键。明信片分工资明信片和外出明信片两类。

## 15 签到留存

SchemaVersion 8 加入签到留存奖励循环，按天给递增奖励，补签走广告，不断签也不重罚，只影响当天奖励。

## 15.1 工资节拍主循环

PetSim 用1秒一个工资节拍（WageBeatPeriodSec）驱动产出，节拍进位用 carry 字段保存，切场景或帧率波动都不会丢节拍，开局进位种子取半个节拍。

每个节拍结算一次所有在岗宠物的产出。岗位速率乘等级软帽、乘宠物被动、乘亲和匹配系数，累加进金币。Tick 是唯一推进入口，每帧拿增量时间、内部累计到整拍才结算，保证不同帧率下产出一致。

在岗判定 IsPetOnDuty 同时要求宠物已招募且被派到某岗位。岗位占用 JobOccupant 记当前派在该岗位的宠物，一个岗位一只。

## 15.1.1 Tick结算链

每个 Tick 内的处理按固定顺序走。先结算星尘和星级，再逐岗位跑节拍，再处理事件，最后跑明信片和成就。

星尘与自动升星：在岗宠物数决定星尘产出，每宠每分钟1点、再乘图鉴加成，攒够自动升星：

```
double perMin = StarDustPerMinPerPet * OnDutyPetCount
              * (1.0 + StarDustDexBonusCoef * _dexCount);
_starDust += perMin / 60.0 * dt;
while (_starLevel < StarMax
       && _starDust >= StarUpCostBase * (_starLevel + 1))
{
    _starDust -= StarUpCostBase * (_starLevel + 1);
    _starLevel++;
}
```

岗位节拍结算，一个节拍的金币是多个因子连乘：

```
double delta = _simTime < _jobRiskPauseUntil[j] ? 0.0
    : JobRatePerSec(j, _jobLevel[j]) * WageBeatPeriodSec
    * (boosted ? AdBoostAmp : 1.0) * _ngWageCoef
    * (IsAffinityMatch(occ, j) ? AffinityWageCoef : 1.0);
```

即岗位速率（含等级软帽）×节拍时长×加速（最多2倍红线，救援和速度窗不叠加超过2倍）×NG继承系数×亲和匹配。风险臂暂停窗口内节拍照走、Amount为0，是登记在案的零节拍而不是跳过。

每节拍还把工作时间累计到该宠物的明信片进度条。事件首张8秒脚本触发、之后按180到300秒节奏在有在岗宠物的岗位里 roll，待处理选择卡会暂停自动事件节奏、保证一次只面对一个决策。

## 15.1.2 反馈三同步

工资节拍的反馈走三同步契约：一个节拍在同一帧内同时给出叮声、读数脉冲和飘字数字三个面，不允许先出声后跳字。首次派遣反馈控制在1秒内，让玩家一上岗就看到宠物在产出。

组合器是纯静态函数，可在无场景下断言这个契约，宿主在节拍触发的同一帧把三个面一起应用。首次派遣时工作剧场开场，宠物在派遣落地的同一帧出现在岗位上，不会出现岗位空着却在发工资的错位。

## 15.2 加速系统

加速分两类：救援加速（BoostKindRescue）和速度加速（BoostKindSpeed）。看广告获得的加速倍率2.0、持续1800秒（30分钟），只作用于指定岗位。

速度加速期间该岗位产出翻倍，SpeedBoostActive 查加速是否在有效期。加速是基础速率面、不是广告抽成，离线不推进加速计时。

## 15.3 离线结算

离线结算结果 OfflineSettleResult 字段：原始离开秒数、计入秒数、金币。离线系数0.6、计入时长封顶12小时，即离线产出按在线速率的六成、最多算12小时：

| 常量 | 值 |
|---|---|
| OfflineCoef | 0.6 |
| OfflineCapSec | 12小时 |
| OfflineDoubleMult | 2.0 |

回来时弹离线摘要，玩家可看广告把离线金币翻倍，TryClaimOfflineDouble 在广告确认后发放，拒绝或广告失败则不翻倍、状态不变。离线计入的工作时长同样累计明信片进度。

## 15.4 签到系统

签到按本地天结算，SignInResult 字段：连续天数、奖励槽位（0到6循环）、金币。7天一个奖励循环，连续天数越高对应槽位奖励越好。

| 结构 | 字段 |
|---|---|
| SignInResult | Streak、CycleIndex、Reward |
| SignInPreview | NextStreak（断签后回到1） |
| SignInDoubleResult | Streak、CycleIndex、Bonus |

签到预览提前展示下次领取会落到的连续天数和奖励。断签不重罚、连续天数回到1，已领奖励不回收。当天奖励可看广告翻倍，SignInDoubleResult 发放等额加成。所有拒绝路径金币为0、镜像当前连续天数。

## 15.5 成就与荣誉墙

成就按终身账本判定，IsAchievementUnlocked 查成就是否解锁。首个成就解锁对应荣誉墙节拍，FirstAchievementT 记录首次解锁时间。成就幂等单调、解锁后不取消，覆盖招募、岗位、星级、明信片、事件收集等维度。终局页首次展示后标记 MarkEndgameShown，不重复弹。

## 15.6 新周目继承

达成终局后可进入新周目。开新周目时重置风险暂停窗、明信片进度、终局标记、各类首次时间戳和节拍计数，免费咖啡店重新开放。

玩家在终局选择的修炼道（perk）只在新周目生效，决定两项继承系数：

```
_ngPlusPerk = perk;
_ngWageCoef   = perkDef.WageCoef;    // 工资继承系数
_ngPairBarCoef = perkDef.PairBarCoef; // 明信片进度条继承系数
_ngPlusCount++;
```

工资继承系数乘进每个岗位节拍，明信片进度条继承系数影响收集节奏，不同修炼道给不同的开局侧重。新周目是干净工资状态，风险暂停不跨周目。

## 16 存档

PetSaveData 含金币、岗位及等级、已招宠物、派工状态、星级、星尘、图鉴、明信片、事件相册、设置。JSON本地存储带版本校验，自动保存加备份。损坏或版本不符返回全新开局，不崩溃。

存档读写都带 SchemaVersion，结构有改动就升版本号、在加载处做旧档迁移，避免字段缺失导致默认值错乱。写盘前先写临时文件再替换，防止中途退出留下半截存档。

离线收益在加载存档时按离岗时间一次性结算，产出系数和上限与在线一致，不会因为关游戏就拿到超出规则的工资。设置项里的音效和音乐开关也一并存下。

## 17 多语言

CopyTable 是英文文案表，CopyTableZh 是中文文案表，CopyLocaleService 负责切换，全工程文案按键取、不硬编码，切换实时生效。

## 18 广告

纯IAA，广告位：加速、金币翻倍、补签、活动等，全部可选，核心进度零广告。预加载，有每日上限和冷却，失败给跳过。

## 19 容错与性能

- 存档解析失败用备份或全新开局
- 资源缺失用占位
- 全局异常捕获，广告失败不卡死
- 对象池、按需加载、静态合批
- 数值表冻结，结构动则升版本号
- 包体20MB内

模拟核心吃外部传入的 deltaTime，岗位节拍、星尘、事件都按模拟时钟走，同一串输入在任何帧率下结果一致，帧率只影响画面、不影响产出。核心不持有 UI 引用，界面订阅事件自己画，模拟和表现互不拖累。

岗位产出、星级、亲和、明信片最终都汇到同一份账本，钱和星尘只有一个出处。亲和匹配给加成、不匹配给精确基础值、零惩罚，玩家放错宠物不会倒扣、只是拿不到加成，策略空间在搭配而不在规避损失。

明信片按工作时长稳定发放、不看概率，是给持续派工的确定回报，图鉴收集进度随游玩自然推进。新周目的继承系数让不同修炼道给不同开局侧重，多周目有延续也有变化。

## 20 版本信息

| 项 | 内容 |
|---|---|
| 软件全称 | 萌宠开店啦游戏软件 |
| 软件简称 | 萌宠开店啦 |
| 版本号 | V1.0 |
| 开发完成日期 | 2026年09月30日 |
| 发表状态 | 未发表 |
| 开发方式 | 独立开发 |
| 权利取得方式 | 原始取得 |
| 权利范围 | 全部权利 |
| 编程语言 | C# |
| 源程序量 | 约5200行（运行时代码） |
