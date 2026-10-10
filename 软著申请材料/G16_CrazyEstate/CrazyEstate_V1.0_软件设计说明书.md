# 我有一栋楼游戏软件 V1.0 软件设计说明书

## 1 软件概述

竖屏模拟经营小游戏，题材是城市空间经营。玩家从老旧小空间起步，与顾问协商，获取空间装修经营，盯市场周期择机转让，还能切换五条职业线，在二十年的时代变迁里把城市天际线拿下。游戏全程架空城市绿洲市，建筑、银行、建设方全虚构，经营现象做喜剧化演绎，不点名真实对象。

数据本地存储，不连服务器，激励视频变现。团结引擎C#开发，逻辑在 `Sy.CrazyEstate` 命名空间下，各玩法拆成独立模块。

## 2 运行环境

| 项 | 要求 |
|---|---|
| 操作系统 | Android 8.0及以上 / iOS 12.0及以上 |
| 运行平台 | 微信小游戏、抖音小游戏、移动端 |
| 游戏引擎 | Unity 2021.3 LTS（团结引擎1.10.3） |
| 编程语言 | C# |
| 运行内存 | 2GB以上 |
| 存储空间 | 150MB以上 |
| 屏幕分辨率 | 720x1280以上，竖屏 |

## 3 工程结构

运行时代码在 `Assets/_Game/Scripts/Runtime/`，按玩法分目录：

```
Runtime/
├─ Boot/        BootRunner、BootSequence、BootServices
├─ Listing/     ListingRoller、ListingTable、SkylineShow
├─ Bargain/     BargainSim、BargainTalkTable、CopyTable、BargainViewHost
├─ Reno/        RenoSim、RenoTable
├─ Rent/        RentLedger、TenantTable
├─ Market/      MarketCycle、DiveMarket
├─ Mortgage/    MortgageSim
├─ Lottery/     LotterySim
├─ License/     LicenseSim、LicenseTable、LicenseGate、EndgameShow
├─ Era/         EraTable、EraSim、EraEventPump、CitySkin
├─ Story/       PlayGate、DramaBuff、ArcState
├─ Events/      EventStream、EventTable、EventPopupHost
├─ Album/       AlbumSystem
├─ Achieve/     AchieveSystem
├─ Iaa/         IaaSim
└─ About/       AboutPanel
```

## 4 房源 Listing

房源卡由 ListingRoller 滚动生成。ListingTable 冻结了10套房源 H01-H10，构成五步阶梯，每套字段：

| 字段 | 含义 |
|---|---|
| Id / Tier | 编号、档次 |
| HouseKey / NoteKey | 房源名、备注文案键 |
| TagIds | 标签id数组 |
| BuiltSqm / InnerSqm | 建筑面积、套内面积 |
| ListPriceWan | 挂牌价（万） |
| RentBasePerBeatCoin | 每30秒节拍的租金基础（币） |
| AgentId | 对应顾问 |

部分房源：

| 房源 | 建面/套内 | 标签 | 挂牌价 | 租金基础 |
|---|---|---|---|---|
| H01 起步老破小 | 58/40 | 无 | 40万 | 60 |
| H02 阳光两居 | 89/61 | 地铁规划 | 75万 | 84 |
| H03 学府苑 | 89/61 | 学区 | 120万 | 96 |
| H04 江景苑 | 120/85 | 江景 | 160万 | 100 |
| H05 中央公馆 | 140/100 | 无 | 199万 | 200 |
| H06 云顶壹号 | 200/132 | 无 | 299万 | 260 |
| H07 未来城 | 89/61 | 无 | 350万 | 300 |

建面和套内分开显示，落差就是公摊，直接暴露在详情页。H01公摊31%配楼道声控灯梗，H02的"地铁规划"标签规划了二十年，H04的江景在枯水期。

## 5 房源标签

标签乘数在1.0到1.8之间，影响租金和售价：

| 标签 | 文案键 | 乘数 |
|---|---|---|
| 无 | tag_none | 1.00 |
| 地铁规划 | tag_metro_planned | 1.12 |
| 近地铁 | tag_metro | 1.30 |
| 学区 | tag_school | 1.50 |
| 江景 | tag_riverview | 1.80 |

租金公式：基础租金（按档次）×标签乘数。市场事件会增减标签，标签变了租金售价跟着变。

## 6 砍价对决 Bargain

核心主动玩法。进入对决后顾问逐个弹话术气泡，玩家在限时内点按反驳，每反驳成功一个按当前价格基点砍掉一部分。

BargainTalkTable 共10组话术，每组带话术文案键、反驳文案键、折扣基点：

| 项 | 值 |
|---|---|
| 每组折扣 | 350-500基点（3.5%-5.0%） |
| 整场最佳 | 砍到挂牌价的10.4%-14.3% |
| 砍价基数 | 按当前价百分比，最低砍1万 |

砍价金额按当前价算，代码：

```
// 每次砍价：当前价 × 折扣基点，四舍五入，保底1万
int CutWan(int priceWan, BargainTalkDef talk)
{
    if (priceWan < 1) priceWan = 1;
    var cut = (int)Math.Round(
        priceWan * (talk.DiscountBp / 10000.0),
        MidpointRounding.AwayFromZero);
    return cut < 1 ? 1 : cut;
}
```

折扣从固定万数改成当前价百分比，是因为固定万数在高段位会崩（高挂牌价下砍价毫无喜剧空间），基点带宽让每一场对决的砍幅都落在喜剧窗口内。砍价有底价，砍到底价气泡停止，成交后盖成交章，显示砍掉的总价差。文案全走 CopyTable 键值。

砍价界面 BargainViewHost 在运行时构建，美术未到位时用色块兜底，按红线时间线推进：开场0到3秒是欢迎和口号钩子，约3秒出第一次报价，之后是引导式二选一、正确反击选项高亮，模拟逐帧驱动。成交仪式把闪光、盖章和收款组合在同一个结算 tick 内，保证约0.8秒同时性，不出现盖章未扣款的中间态。开场钩子上的内容清单条直接读四个真实表计数，不手工填数。

## 7 装修 Reno

获取空间后选简装、精装、豪装三档，消耗金币和工期，提升租金和转让价格。RenoTable 冻结三档参数：

| 档位 | 成本（买价） | 租金乘数 | 残值 | 怪癖率 | 工期 |
|---|---|---|---|---|---|
| 简装 | 5% | x1.00 | 1.02 | 0 | 45秒 |
| 精装 | 10% | x1.25 | 1.08 | 0 | 90秒 |
| 豪装 | 18% | x1.50 | 1.15 | 15% | 150秒 |

租金=基础租金×标签乘数×装修乘数；售价=买入价×市场倍率×装修残值。装修成本=买入价×成本百分比、半入取整：

```
// 装修成本（万）：买价 × 成本基点
int CostWan(int tier, int buyPriceWan)
{
    if (!IsValid(tier) || buyPriceWan <= 0) return 0;
    var pct = GetTier(tier).CostPctBp;
    return (buyPriceWan * pct + 9999) / 10000;
}
```

工期对应1.5、3、5个租金节拍（节拍30秒）。豪装有15%概率触发怪癖（效果图仅供参考），怪癖只掉1点口碑星、不做任何数值重罚。RenoSim 跑工期和怪癖判定。

## 8 收租 RentLedger

空间出租后自动计租，在30秒节拍上结算，和月供同一个节拍。RentLedger 管每套的租约、收租周期、累计租金。

租客由 TenantTable 确定性分配，不靠随机API：

```
// 同一批买入 -> 双跑得到同样租客
// 7/11步长避免相邻单位撞同一个租客
int TenantForRow(int rowOrdinal, int unitId)
{
    return ((unitId * 7 + rowOrdinal * 11) % Count) + 1;
}
```

租客随机触发差评、损坏、续租、退租事件。差评进差评图鉴当收集品，意外事件零惩罚。离线租金照结。

## 9 租客表

TenantTable 定义10个喜剧租客，每个带名称键和差评键，文案走 CopyTable 中英文表。租客性格和事件倾向不同，有的爱给差评、有的会续租、有的损坏房屋。名称和差评都要求中英文键齐全，校验时缺键直接报问题。

## 10 市场周期 MarketCycle

宏观价格引擎，三态循环：

| 状态 | 倍率区间 | 特征 |
|---|---|---|
| Rush 热销期 | x1.20 - x1.50 | 价格走高，认购活跃 |
| Flat 横盘 | x1.00 | 交易平淡 |
| Panic 低迷期 | x0.70 - x0.90 | 价格下探，特价入手 |

常量：

| 常量 | 值 |
|---|---|
| PhaseSecMin / Max | 120 / 180秒 |
| MultRushMin/MaxBp | 12000 / 15000 |
| MultFlatBp | 10000 |
| MultPanicMin/MaxBp | 7000 / 9000 |
| NewsRollSec | 12秒 |
| FullNewsCount | 10条 |
| OfflineAdvanceCapSec | 180秒 |

每态持续120到180秒，时长由确定性步数哈希决定，不用随机API。态内倍率沿半正弦在区间内扫描，事件通过 ApplyEventShift 临时推移倍率。新闻滚动条12秒换一条，标题走喜剧演绎。

售价=买入价×市场倍率×装修残值。离线时周期最多快进180秒（约一个态），不做跨多周期模拟。DiveMarket 处理低迷期特价入手。

态内倍率走半正弦，牛市中段冲到上沿、熊市中段跌到下沿，读时再叠加事件偏移、钳回态内窗口，倍率永远不越出0.7到1.5：

```
int CurrentMultBp
{
    get
    {
        var t = PhaseElapsedSec / PhaseDurationSec;
        if (t < 0f) t = 0f;
        if (t > 1f) t = 1f;
        double mult;
        switch (Phase)
        {
            case Rush:
            {
                var lo = WindowMin();
                var hi = WindowMax();
                mult = lo + (hi - lo) * Math.Sin(Math.PI * t);
                break;
            }
            case Panic:
            {
                var lo = WindowMin();
                var hi = WindowMax();
                mult = hi - (hi - lo) * Math.Sin(Math.PI * t);
                break;
            }
            default:
                mult = MultFlatBp;
                break;
        }
        var total = (int)Math.Round(mult) + _eventShiftBp;
        return ClampToPhaseWindow(total);
    }
}
```

推进 AdvancePhase 时累计时长、到点切态，同时按12秒节奏滚新闻。事件偏移有正负5000基点上限、切态即清零，时代振幅则围绕平稳锚点缩放牛熊偏离度。

## 11 房贷 MortgageSim

购房首付30%，贷款=房价-首付。货币单位是币，1万=1000币，月供在30秒节拍上结算：

| 常量 | 值 | 含义 |
|---|---|---|
| TermMonths | 360 | 喜剧化无息"30年" |
| StressYellowBp | 5000 | 压力<50%绿 |
| StressRedBp | 8000 | 压力>80%红 |
| CrisisRedStreakMonths | 2 | 连续2个红色预警月逾期 |
| LeverageCapBp | 23000 | 总贷款≤现金2.3倍 |

月供=ceil(贷款/360)。压力计=当月应还/租金现金流，绿黄红三档。连续两个红色预警月触发逾期提醒、进入困难期，玩家可看激励视频申请延期，延期期间月供减半。

一个月的结算逐行扣、钱不够的行记漏供、本金只留实际到账部分、永不出现负钱包：

```
MortgageMonth SettleMonth(int cashCoins, int rentFlowCoins, float nowSec)
{
    var month = new MortgageMonth();
    var relief = ReliefActive(nowSec);
    var wallet = cashCoins < 0 ? 0 : cashCoins;
    for (var i = 0; i < Rows.Count; i++)
    {
        var r = Rows[i];
        if (r.Sold || r.LoanCoins <= 0) continue;
        var inst = InstallmentCoins(r, relief);
        month.DueCoins += inst;
        var take = inst < wallet ? inst : wallet;
        r.LoanCoins -= take;
        wallet -= take;
        TotalPaidCoins += take;
        if (take >= inst) r.MonthsPaid++;
        else { r.MissedMonths++; TotalMissedMonths++; }
        Rows[i] = r;
    }
    month.PaidCoins = (cashCoins < 0 ? 0 : cashCoins) - wallet;

    if (month.DueCoins <= 0) month.StressBp = 0;
    else if (rentFlowCoins <= 0) month.StressBp = NoFlowStressBp;
    else month.StressBp = month.DueCoins * 10000 / rentFlowCoins;
    month.Zone = month.StressBp > StressRedBp ? Red
        : month.StressBp >= StressYellowBp ? Yellow : Green;

    if (month.Zone == Red) RedStreak++;
    else RedStreak = 0;
    month.RedStreak = RedStreak;
    month.CrisisPending = CrisisPending;
    return month;
}
```

延期在每行单独作用、月供减半，压力计分母为零租金流时直接判红、不做除零。

贷款比例上限2.3倍：签约前必须查 CanLeverage，AddLender 再深度强制一次，超限直接拒绝、状态不变（银行拒贷（喜剧化处理））。转让结算，银行扣除差额。

## 12 限时认购 LotterySim

热盘触发限时认购节奏小游戏，每个热盘一次：

| 常量 | 值 |
|---|---|
| WindowSec | 8秒点按窗口 |
| SlotSec | 2秒一个节奏槽，共4槽 |
| BaseWinBp | 3000（基础认购成功率30%） |
| OnBeatBonusBp | 750（每踩点+7.5%） |
| WinCapBp | 6000（硬上限60%） |
| HotPriceBp | 8500（倒挂价=挂牌85%） |

玩家在8秒内按2秒节奏踩点，踩得越准认购成功率越高、封顶60%。认购成功即按挂牌价85%的优惠价购买，优惠价就是即时节省。未认购成功零惩罚，正常挂牌价不受影响。认购走确定性步数哈希，双跑字节一致。

时代调制认购：城市更新期 Off 不开放、经营热潮 Hot 概率×1.5、财富起伏 Low ×0.5、岁月安家 Normal 基础。

## 13 五线职业 LicenseTable

执照制，新手房东为主线，首套成交即解锁且不可放弃。其余四线各按单轴条件解锁：

| 职业 | 玩法 | 解锁轴 | 条件 |
|---|---|---|---|
| 新手房东 SmallLandlord | 空间装修收租主线 | 无 | 首单成交 |
| 资深房东 RentTycoon | 收储转租 | Holdings | 持有3套房 |
| 资深顾问 GoldAgent | 接单议价、门店升星 | SavingsWan | 累计议价省10万 |
| 城市建设者 Developer | 规划建设、自担工程风险 | CashWan | 现金600万 |
| 价值投资者 BottomFisher | 低迷期择时、特价入手 | PanicDeals | 低迷期窗口成交 |

单轴律：每条非主线只挂一个解锁条件，四个锚点刻意不同，让每条线讲一个不同的"你立业了"的故事。城市建设者线早期锚点90万会在开局白送（启动资金40万即满足），已重新锚定到600万，意为"有能承担建设风险的储备"。各线带专属事件、图鉴和终局，五线全通解锁绿洲市风云人物成就墙。

## 14 时代引擎 EraTable

二十年跨度分四幕：

| 幕 | 年份 | 振幅 | 认购 | 事件率 | 租金权重 |
|---|---|---|---|---|---|
| 老城翻新 RenewalSpring | 1-5 | 8000 | Off | High | 800 |
| 经营热潮 LotteryBoom | 6-10 | 高 | Hot | Mid | 中 |
| 财富起伏 PaperBust | 11-15 | 急跌后磨底 | Low | Mid | 中 |
| 岁月安家 SettleHome | 16-20 | 平 | Normal | Low | 最高 |

每幕调制市场振幅、认购模式、事件率、租金权重、贷款风险，并切换城市皮肤：绿网脚手架→霓虹塔吊→特价横幅加围栏→翻新脚手架回归。每幕挂至少10个演绎事件槽，全部架空、零真实姓名。EraEventPump 按幕投放。财富起伏幕做喜剧安全阀，只给温暖结局不做绝望叙事。

## 15 剧情 Story

十二章，PlayGate 章门只按真实玩法里程碑解锁、永不做时间墙。章门锁存玩家的足迹事实，严格按线性顺序推进，一个未满足的门会阻塞后面所有章节、不能跳章，每章解锁事件只抛一次。

里程碑馈送 GateFeed 共14种：

| 馈送 | 触发事实 |
|---|---|
| DealClosed | 成交（带房源id） |
| RenoCompleted | 首次装修完成 |
| TenantMovedIn | 首个租客入住 |
| DemolitionEvent | 城市更新事件（黄金雨） |
| LotteryEntered | 首次进入认购 |
| NetWorthSnapshot | 净资产快照 |
| ResaleSettled | 转售结算（单笔利润） |
| MortgageCrisis | 首次房贷压力提醒 |
| HoldingH07 | 持有未来城预售房 |
| CashTight | 现金流紧张信号 |
| HouseSold | 转让动作计数 |
| TenantsHoused | 当前在住租客数 |
| PackageLicense | 资深房东执照解锁 |
| LinesAtFinale | 五线终局档位数 |

冻结门槛：净资产章600万、首笔转售利润10万、第9章转让2次、第10章安置租客5名、第11章达成2条职业线，城市皇冠对应H10、未来城对应H07。门槛锚定在启动资金之上，避免开局白送解锁。

每章末尾给可选 DramaBuff，不看剧情也能正常通关。ArcState 维护NPC弧态，人物立场随章节翻转并改变玩法行为。剧情变量读真实存档、不写死。

## 16 事件 Events

EventStream 管事件卡触发和结算。事件卡按180到300秒窗口投放，第一张卡在8秒内保证触发（公摊曝光卡），是首个反馈节拍。每次事件卡抽取和窗口长度都走确定性步数哈希、不用随机API，双跑字节一致。

事件卡结构 EventCard 字段：卡id、序号（0为保证的首张）、触发时间。已收集卡进事件图鉴（10槽）。

| 常量 | 值 | 含义 |
|---|---|---|
| FirstCardAtSec | 8 | 首张卡≤10秒 |
| WindowMin/MaxSec | 180 / 300 | 事件窗口 |
| DemolitionRateBp | 80 | 城市更新头奖0.8% |
| JackpotMult | 3 | 头奖赔3倍买价、3倍即上限 |
| CodexCapacity | 10 | 事件图鉴槽 |

城市更新头奖是0.8%的稀有 roll，且只有玩家名下至少有一套房时才会中（没房无可更新），中了奖励该套买价的3倍、3倍就是封顶。装修延期卡退全部装修成本，是零惩罚喜剧——不掉星、不扣款。

EraEventPump 按时代和市场状态投放对应事件，LineEventPump 按职业线投放。EventPopupHost 处理卡牌交互，事件选项结算后更新账本。

## 16.1 图鉴相册

AlbumSim 管四个图鉴：空间、租客、事件、差评文学。解锁状态一律从实时数据派生、不另存第二份真相，避免副本漂移。

| 图鉴 | 条目 | 解锁来源 |
|---|---|---|
| 空间 | 每空间一条 | 租金账本里拥有该空间id |
| 租客 | 每租客席一条 | 账本行带该租客id |
| 事件 | 每事件卡一条 | 事件流图鉴收集 |
| 差评文学 | 镜像租客 | 租客在册时其差评可收集 |

派生逻辑直接读账本行收集已拥有的id集合，再逐条对照冻结表标解锁，图鉴面永远反映当前账本。

## 16.2 年报分享

分享双通道，全部本地组合、零服务器零上传，载荷本身就是产物：

| 通道 | 内容 |
|---|---|
| 短分享卡 | 简要资产卡 |
| 大亨年报长图 | 标题加六条统计行 |

年报文案全走 CopyTable，中英文都以文案表为唯一权威。空资产时两个通道都拒绝、不发事件（还没有值得晒的东西）。每次成功分享走一个分享卡事件、带卡id。

## 17 存档

存档含现金、空间清单、贷款状态、职业等级、章节进度、时代年份、市场周期状态、图鉴成就、设置。JSON本地存储带版本校验，自动保存加备份，支持导出码。损坏或版本不符返回全新开局。

存档带版本号，加载时按版本做迁移，缺失字段补默认值而不是直接判废。写盘走临时文件再替换，避免切后台时写坏存档。市场周期和贷款这类跨时段状态记下时间戳，回来时按经过时间推进、离线快进有上限，不会一进游戏就跳过一整个周期。

导出码把关键进度编码成文本，换机时可手动恢复，码里只放进度、不放隐私信息。

## 18 广告

纯IAA，广告位：逾期延期、交易加速、离线租金翻倍等，全部可选，核心进度不依赖广告。有每日次数上限和冷却，预加载，广告失败给跳过选项不卡流程。

## 19 容错与性能

- 全架空，游戏面不出现真实地名、房企名和政策词
- 解析失败用备份，资源缺失用占位
- 全局异常捕获，广告失败不卡流程
- 对象池、按需加载、静态合批
- 各表带 Validate 校验，缺键、越界、重复id直接报问题
- 包体20MB内

模拟核心吃外部 deltaTime，市场、贷款、租金都按模拟时钟推进，同一串输入在任何帧率下结果一致，掉帧只影响画面、不会让价格和月供跳变。核心不持有 UI，界面订阅事件自己渲染，结算和表现解耦。

议价、买卖、租金、贷款、事件最后都过同一份账本，现金只有一个出处，任何渠道都不会凭空多发。贷款比例和压力计在签约前强制校验，超限直接拒、状态不变，把风险拦在落子之前而不是事后补救。

时代线调制市场振幅、认购和事件率，职业线给不同的解锁目标，两条轴独立推进又在同一座城市里汇合，玩家可以只走一条、也可以交替。图鉴和年报全部从账本派生、不另存，看到的永远是当前真实进度。

## 20 版本信息

| 项 | 内容 |
|---|---|
| 软件全称 | 我有一栋楼游戏软件 |
| 软件简称 | 我有一栋楼 |
| 版本号 | V1.0 |
| 开发完成日期 | 2026年09月30日 |
| 发表状态 | 未发表 |
| 开发方式 | 独立开发 |
| 权利取得方式 | 原始取得 |
| 权利范围 | 全部权利 |
| 编程语言 | C# |
| 源程序量 | 约14000行（运行时代码） |
