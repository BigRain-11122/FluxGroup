# R-20260929 · 头部三消「meta 编排 + 商业化模型 + 留存钩」深度调研

**服务对象**：吸嘟嘟（治愈系三消 + 收集小可爱 · 微信小游戏 · IAA 为主 + 轻 IAP · 已定谳 Royal Match 系风格）

- 调研日期：2026-09-29（周二 · Asia/Shanghai）
- 调研席：游戏公司调研席（Codely agent）
- 研究对象：①Royal Match（Dream Games）②Gardenscapes / Homescapes（Playrix）③Lily's Garden（Tactile Games）④Candy Crush（King）⑤微信小游戏同形态本土头部（三消 / 合成 + 收集；抓大鹅、羊了个羊本体排除，但其模型仍作旁证）

## 调研纪律与方法
- 信源优先级：deconstructoroffun.com / naavik.co / pocketgamer.biz / gamelook.com.cn / 游戏葡萄 / Sensor Tower / AppMagic 公开报告页 / 官方财报电话会转述
- 分级：【确认】＝有信源 URL 直接支撑；【待证】＝二手转述、记忆数据或推断，需二次核验
- 写盘纪律（存活律）：拆完一题立即追加写盘

## 吸嘟嘟现状基线（落差分析锚点 · 甲方给定）
1. 六屏静态板：主菜单 / 章节旅程 / HUD / 结算 / 图鉴 / 道具铺
2. 收集 meta：图鉴 3/6（约 50% 进度；无解锁动画 / 无图鉴奖励闭环证据）
3. 经济：金币单币种；「看视频领 60 金币」为目前唯一 IAA 插点位
4. 商业化：IAA 为主 + 轻 IAP 定位（未观察到 IAP 结构落地）

## 进度
- [x] 题一：meta 编排（已完成，见下文 1.1–1.8）
- [x] 题二：商业模型（已完成，见下文 2.1–2.6）
- [x] 题三：留存与回访钩（已完成，见下文 3.1–3.8）
- [x] 题四：活动与 LiveOps（已完成，见下文 4.1–4.6）
- [x] 附：吸嘟嘟适配初判（已完成，三档结论见文末专节）

## 题一：meta 编排——头部三消的四条路线与「收集小可爱」先例（2026-09-29 完成初稿）

### 1.1 Royal Match（Dream Games，2021-02-25 全球上线）：「装饰线·极简版」

**核心 meta 循环（官方口径）**：每赢 1 关得 1 星 → 星星驱动该区域「任务」（tasks＝该区域内可建造的装饰物，每区域固定若干个）→ 完成区域内全部任务 → 开启 **Area Chest（区域宝箱：金币+道具+卡牌）** → 点「New Area」按钮解锁下一区域。【确认】Royal Match 官方帮助中心 https://dreamgames.helpshift.com/hc/en/3-royal-match/section/12-tasks-and-areas-1608111909/?l=en

**节拍数字**：
- 区域规模：写作时点共 **106 个区域**，每区域 **10~100+ 关**；最新区域「Air Festival」＝第 8701–8800 关（≈100 关/区域，后期区域）【确认】https://www.esports.net/news/mobile-games/royal-match-areas/
- 「Jousting Arena」区域总计需 100 星【确认】https://royalmatch.fandom.com/wiki/Jousting_Arena（fandom 快照）
- 新关卡**每两周**更新一批【确认】https://naavik.co/deep-dives/royal-match/
- 结构解读：区域＝粗颗粒大目标（每数十~上百关一次区域结算+装饰大场面），星星＝细颗粒每关可见进度，双层节拍互补

**设计要点（Naavik 2022-05 深拆）**【确认】https://naavik.co/deep-dives/royal-match/
- RM 定位＝King（极简 meta）与 Playrix（重 meta）之间的 **wedge**：无文字叙事、**无装修三选一**，装饰自动完成，玩家专注解谜本身
- King Robert 头像置于棋盘顶部、表情镜像玩家状态（步数将尽时「卖惨」）→ 情绪化驱动关末（EoR）续命付费
- **Butler's Gift（管家礼物）**：连胜最多 3 关 → 下关开局棋盘预置最多 3 个道具（慷慨感+连胜留存钩，道具靠它「合理超模」）
- **Card Collection 卡牌收集册（2022-05 新增）**：RM 第一个永久二级进度系统；参与事件/主进度里程碑掉落主题套卡；重复卡可换成任选卡；集齐后回环奖励金币+道具。Naavik 判断：此举不为长留，为「**奖励空间感/可收集感**」——即 RM 官方也承认纯 progression 缺收集维度，需补收集册
- 关卡按 near-miss（差一点点就赢）精调，失败关强写「本关已收集的道具将失去」二次挽留
- RM 无广告无 IAA（纯 IAP），全篇多处确认【确认】naavik + https://raijinnstudio.com/blog/match-3-game-development-guide-royal-match

**抓取失败记录**：royalmatch.fandom.com/wiki/1-20（403）、gardenscapes.fandom.com/wiki/Garden_Locations（403）、pocketgamer.biz 51% 文（403，见题二）、medium.com Udonis《Lily's Garden Monetization》（403）。均如实记录，改用替代信源。

### 1.2 Gardenscapes / Homescapes（Playrix，2016）：「家装线·选择权版」

- 星星机制（官方）：**每赢 1 关得 1 星**；星星用于平板上的装修任务；每任务星耗不同、部分任务分 2–3 阶段【确认】https://playrix.helpshift.com/hc/en/5-gardenscapes/faq/61-stars/
- 叙事按「Day（天）」推进：Austin 管家主线+每日任务；各区域需在设定天数内靠星星+任务完成解锁【确认】https://gardenscapes.fandom.com/wiki/Garden_Locations（搜索摘要，正文 403）+ https://omg.rocks/gardenscapes-tip-tricks-resources
- 与 RM 最大差异：**装修提供三选一选择权**（玩家 agency）+持续文字剧情；Naavik 的 meta 复杂度坐标把 GS/Homescapes 放最重端、RM 最轻端【确认】naavik 同上文
- **Renovation Events（装修活动）**：7–10 天限时，消除带标记棋子收集「装修票」→ 场外房间装修+装饰选择——把「家装 meta」本身做成可复用活动模板【确认】https://gardenscapes.fandom.com/wiki/Renovation_Events（搜索摘要，正文 403）
- 赛道定位：P&D（Puzzle & Decorate）三巨头＝Homescapes/Gardenscapes/Fishdom【确认】DoF 2021-03 https://www.deconstructoroffun.com/blog/2021/3/21/royal-match-the-new-king-from-turkey

### 1.3 Lily's Garden（Tactile Games，2019-01 上线）：「剧情线·连续剧版」

- 结构：剧情以「天（Day）」为单位，**30 天剧情大弧+穿插支线**；每天翻新 LaRosa 庄园一个地点；Day 1 总钩子＝「30 天内完成装修，否则取消继承权」【确认】https://lilysgarden.fandom.com/wiki/Category:Days + https://lilysgarden.fandom.com/wiki/Day_1
- 节拍数字：每天需 **~40–49 星**完成任务（Day 24＝47 星、Day 70＝49 星、Day 214＝40 星）；每关 1 星 → **一个 Day≈40–50 关的长期目标**，剧情回报密度远低于 GS（每关都有剧情期待，但每天才一个大结算）【确认】fandom 各 Day 页（Day_24 / Day_70 / Day_214）
- 恋爱连续剧叙事+女性 30+/35+ 核心受众；累计 IAP 接近 **5 亿美元**【确认】https://www.gamigion.com/tactiles-ad-strategy-in-heavy-iap-games-%F0%9F%A7%A8/ + https://www.pocketgamer.biz/how-tactile-games-made-marketing-and-diversity-core-to-lilys-gardens-500-million-success/
- **Stories（2022+）**：房间装修支线（Lily's Living Room / Kitchen / Study / Bedroom / Bathroom / Luke's Basement…）＝把「新房间」当内容型收集目标长线运营【确认】https://lilysgarden.fandom.com/wiki/Category:Stories
- Lily's Garden 装修是否提供三选一：未见可靠信源，按剧情驱动线性处理【待证】

### 1.4 Candy Crush Saga（King，2012）：「极简线·元游戏即地图」

- meta＝Saga 地图+Episode（章节）：每 episode 自有名称主题、官方在此引入新障碍/元素；快照数据：Emerge Tools 深拆＝**14.5k 关/968 episodes**；fandom＝**1561 episodes**（Reality，快照时点不同，量级一致）【确认】https://www.emergetools.com/deep-dives/candy-crush-saga + https://candycrush.fandom.com/wiki/Episode
- King 哲学：玩法为纲、meta 极薄（Naavik 评述：RM 学 King 的「重玩法轻 meta」但做得比 King 更慷慨）【确认】naavik
- 无装修、无收集册；长留靠活动/地图里程碑（题四展开）
- grokipedia 快照：各平台文档化关卡 21,000+，episode 至 1461【确认】https://grokipedia.com/page/Candy_Crush_Saga_Wiki

### 1.5 「收集小可爱」类 meta 的头部先例（非家装路线）——对吸嘟嘟最关键

- **Best Fiends（Seriously，2014-10）＝最强先例**：55+ 只虫虫 Fiends 收集+进化；上阵 5 只小队；**收集直接作用于玩法**（每只 Fiend 专属技能，升级进化增强消除能力）；稀有度越高所需碎片越多；2018 加 Epic Fiends；能量系统+IAP。数字：11,000+ 关、累计约 1 亿下载；2016 年时 BF 双作累计收入 **$65M**/下载 60M；**2019-08 Playtika 约 $2.75 亿收购 Seriously**，2022 Seriously 关闭、开发并入 Playtika【确认】https://grokipedia.com/page/best_fiends + https://www.pocketgamer.biz/seriously-on-the-evolution-of-best-fiends/
  - ⚠️ 信源勘误：grokipedia 将玩法误写为「交换相邻块」；Best Fiends 实为**连线消除**（link/draw），该页仅作数字交叉参考【待证】
- **Fishdom（Playrix）**：水族箱装修+鱼类收集（养鱼喂食），P&D Top3 之一——三消里「收集可爱生物」作为主 meta 的最接近头部案例【确认】DoF 2021-03（同 1.2 链接）
- **Royal Match Card Collection（2022）**：Dream 用卡册补收集维度（见 1.1）——头部自己也补了这一课
- **结论**：纯「收集可爱」主 meta 的头部**交换式三消**没有出现过；可行范式两条：
  1) Best Fiends 式「收集＝能力/数值」（深度高，做成头部极难，且其巅峰期已过、公司被收购）
  2) RM 卡册式「收集＝奖励空间+目标感」（轻、易落地，为奖励表提供第二根进度条）
  - 吸嘟嘟的图鉴（3/6）目前是第 2 条路线的雏形，但**无解锁奖励闭环、无数值作用**，两头都不占

### 1.6 小游戏生态侧的 meta 证据（微信）

- 微信 IAA 小游戏大盘（2026 微信小游戏大会口径）：**IAA 小游戏 MAU 超 4 亿**、用户规模同比 +25%、商业规模 +30%；**70% 小游戏用户只玩 IAA 休闲**；IAA 休闲女性 60%/男性 40%；人均每月体验 7.5 款【确认】https://www.toutiao.com/article/7644856624368206370/ + https://www.163.com/dy/article/KTUVU42H05466ZM9.html
- 混合 meta 在小游戏内的价值：一款「三消+家园装扮」混合休闲小游戏的用户日均时长与广告展示次数≈纯三消的 **1.5 倍**【待证（二手博客转述，未见原始数据）】https://blog.csdn.net/weixin_33585822/article/details/163031430
- 合成+叙事赛道头部：柠檬微趣 Gossip Harbor 2025 年流水超 **5.4 亿美元**（合成+剧情装修）；2025 年流水过亿人民币的合成产品 15 款（9 款出海）【确认】https://m.36kr.com/p/3697346329882247（36 氪转述 DataEye 口径）
- 微信畅销榜样本《趣乐消消》（海南挺有趣）：三消+买量+IAA 长尾打法（题二详拆）【确认】https://www.lightgame.cc/game/wechat-c29a00a3dc.html

### 1.7 题一小结：四条路线钩子结构对照表

| 维度 | Royal Match | Gardenscapes/Homescapes | Lily's Garden | Candy Crush |
|---|---|---|---|---|
| 每关 meta 奖励 | 1 星+金币 | 1 星 | 1 星 | 通过本身（+活动层） |
| 区域/章节节拍 | 区域=10~100+ 关，Area Chest 大结算 | Day 制剧情；任务 2–3 星、分 2–3 阶段 | Day 制剧情；每天 ~40–49 星 | Episode 章节制，每章引入新元素 |
| 玩家 agency | 无三选一（自动装饰） | **三选一装修** | 线性剧情驱动【待证】 | 无 |
| 收集册/册子 | 卡牌册（2022 补） | 无主线册（活动装修即收集）【待证】 | 无主线册 | 无 |
| 角色 IP | King Robert+管家+狗 | Austin | Lily/Luke/Regina 等 | 无主角 |
| meta 强度 | 轻（wedge 定位） | 重 | 中重（叙事） | 极轻 |

### 1.8 对吸嘟嘟的即时落差（题一）
- 「章节旅程」有 RM 区域的壳，缺三层钩：①星星型进度货币（每关可见 meta 进度）；②任务化装饰节拍（每章节内若干小任务逐个点亮）；③区域结算宝箱（Area Chest 式大节拍奖励）。
- 图鉴 3/6 走的是 RM 卡册路线但**没做完**：无解锁动画、无集齐奖励、无数值作用——「收集=奖励空间」闭环断裂。
- 六屏静态板缺 King Robert 式情绪载体：无角色表情镜像/无管家式连胜奖励人物。

## 题二：商业模型——RM/GS 的 IAP 结构、无 IAA 之谜、微信小游戏侧 IAA 形态（2026-09-29）

### 2.1 Royal Match：纯 IAP 的「重税模型」

**收入基本盘（多口径交叉）**：
- 年度收入：2021 年 $172M（上线首 9 个月）→ 2022 年 $428M → 2023 年 $850.76M（Sensor Tower 口径）/$932M（AppMagic 净分成口径）→ **2024 年 $1.46B**（两个口径一致，AppMagic 榜第 3，仅次于 Honor of Kings $1.87B 与 Monopoly Go $1.58B，超过 Candy Crush）【确认】https://www.mobilemarketingreads.com/royal-match-revenue-and-download-statistics/ + https://mobilegamer.biz/the-top-grossing-mobile-games-of-2024/
- 累计：**用户总支出 $5B（2025-01-22，AppMagic；净 IAP $3.1B）**；2024-05 时点刚近 $3B → 8 个月净增约 $2B；后突破 $6B【确认】https://app2top.com/news/user-spending-in-royal-match-has-exceeded-5-billion-276759.html + https://app2top.com/news/players-have-spent-over-6-billion-in-royal-match-280790.html
- 月收入约 **$130M**（2025-09 口径）；2024-12 **RpD 达 $55**（AppMagic：2024 战略转向「变现+live-ops 优先于扩量」）【确认】https://www.blog.udonis.co/mobile-marketing/mobile-games/royal-match-analysis + mobilemarketingreads 同上文
- 下载：2023 年 137M、2024 年 113M；**61.5% 下载来自买量广告**（Candy Crush 仅 15.4%–25%，Sensor Tower）【确认】Udonis 同上文
- 市场：AppMagic 2024 休闲报告——休闲 IAP 总盘 $15.2B（+11.7%）；**RM 占 match-3 子品类 IAP 收入 51%**（口径：美英加法德澳等西方头部市场）；剔除 RM 后 match-3 品类收入 **-8%**、下载 -12%【确认】https://www.mobilemarketingreads.com/royal-match-and-monopoly-go-lead-the-charge/ （AppMagic 报告转述）+ pocketgamer.biz 标题转述（正文 403，已记录）

**IAP 结构（单币种金币）**：
- 金币是唯一货币：用途＝续 5 步 / 买道具 / 补生命；官方商店＝金币包+宝物礼包（Prince's/Queen's/King's Treasure）+限时优惠；Google Play 价格梯度 $0.64–$159.83（跨国对比）【确认】https://royalmatch.fandom.com/wiki/Coins + https://dreamgames.helpshift.com/hc/en/3-royal-match/faq/22-how-can-i-purchase-coins/ + https://opentherank.com/mobile-game-pricing/royal-match/
- **EoR（差步续命）递进税——全品类最高**：第一组 +5 步 ≈ $2 等值金币（对比 Project Makeover $1.19、Fishdom $0.89），随后递进 $4.35 → $6.65 → $8.95【确认】naavik
- **Royal Pass（战令）**：37 级解锁，月度 30 步奖励轨；定价 **>$10**（对比 Homescapes $4.99 / Lily's Garden $5.99 / Candy Crush $6.99）——上线 30 天内收入 +31%、D30 留存 +2%；奖励走「社交声望」路线：生命上限 +60%×1 月、金色头像框、全队小奖励【确认】naavik
- **Endless Treasure（无限宝箱/Prize Road）**：免费奖励可见 → 低价高价值 IAP 卡点续领（禀赋效应，新版 Piggy Bank）；上线 30 天收入 +20%；每周一重置，玩家首购后 offer 会升级变贵（玩家社群观察）【确认】naavik + https://www.facebook.com/groups/royalmatchfan/posts/951486055853604/ 类帖（社群观察，弱信源）
- 活动即变现：事件期间先让玩家处于「资源富余环境」体验，再推 IAP 复刻这种富余感【确认】Udonis
- 无任何广告位（零 IAA），多处确认【确认】naavik + raijinnstudio 同上文

### 2.2 头部三消「无 IAA」的原因拆解

- **官方定位**：Dream Games 以「no ads, ever」为卖点做 premium 体验——「游戏内每个挫败点只有一个泄压阀，就是 IAP 商店」；无广告本身是差异化变现策略（在广告饱和的休闲市场，干净=尊重玩家=品牌溢价）【确认】https://raijinnstudio.com/blog/match-3-game-development-guide-royal-match
- **机制自洽（分析性推断）**：RM 收入核心＝EoR 递进税（$2→$8.95），激励视频「看广告续命」会直接对冲这条最高价付费链路；RM 的核心体验＝全品类最快棋盘+零加载（DoF/naavik），插屏/强制广告破坏「速度即爽感」；受众为高付费意愿大龄玩家（45+），LTV 由鲸鱼驱动，广告 ARPU 增量远小于 IAP 稀释风险【待证（合理推断，非单一信源直接陈述）】
- **血统**：创始团队来自 Peak（Toon Blast/Toy Blast 同为无广告 IAP 模式）【待证】naavik（提及 Peak 出身但未直接论广告政策）
- **关键反例——Tactile（Lily's Garden，累计 IAP 近 $500M）在重 IAP 游戏上做分层 IAA**：用「关卡进度+安装后时间」做用户分层，识别 non-purchasers 单独提广告负载；配合换 mediation+新增激励视频插位，**广告 ARPDAU +101%**；结论：重 IAP 三消也能加广告，但必须分层，付费用户保护、零氪用户单独运营【确认】https://www.gamigion.com/tactiles-ad-strategy-in-heavy-iap-games-%F0%9F%A7%A8/ + https://www.gamebizconsulting.com/case-study/tactile-games
- Candy Crush 同属无第三方广告阵营（King 长期纯 IAP；历史口径）【待证——本轮未获直接信源，快查未成】
- **对吸嘟嘟结论**：无 IAA 是「高 ARPU×零摩擦×EoR 重税」的特定组合，IAA 为主的吸嘟嘟不可照抄；可直接移植的是 Tactile 式**分层原则**（付费者降广告/零氪者广告克制）与「激励视频奖励价值略低于等值付费」的守则

### 2.3 Gardenscapes / Homescapes（Playrix）：单币种+七日变现爬坡

- 体量：Homescapes 2017-09 上线，累计下载 **540M+**、累计收入 **$2.5B+**（美国>$1B；下载第一印度仅贡献 $5.5M，收入第 35）；AppMagic 净 IAP 榜（复杂 meta 三消，2025-01）：**Gardenscapes $4B（672M 下载）> Homescapes $3.4B（619M）> Royal Match $3.1B（325M）** > Project Makeover $755M > Matchington Mansion $716M > Clockmaker $324M【确认】https://www.blog.udonis.co/mobile-marketing/mobile-games/homescapes-monetization + app2top 同上
  - 2024 单年（AppMagic）：Gardenscapes $504M（同比 -$130M）、Homescapes 约第 21（同比 -$110M）、Township $403M、Toon Blast $287M（+$87M）、Zynga Match Factory 新品 $178M【确认】mobilegamer.biz 同上文
- **商店＝Bank，单币种金币**（Playrix 创意总监原话：「玩家需要付出努力挣金币……单币种更优雅」——PocketGamer 转述）【确认】Udonis Homescapes 文
- Bank 首屏五档：**Starter Pack $1.99 / Apprentice Pack $6.99 / 金币 $0.99 / $4.99 / $9.99**（前三为最畅销档）；更多里 6 个礼包 $1.99–$99.99 按身份命名（Starter→Pro→Veteran→Champion，身份定价锚），金币 6 档 $0.99–$74.99【确认】Udonis 同上文
- **Gold Reserve（存钱罐）**：D2 上线；此后所挣金币一部分进罐、4 倍加成，砸罐 $2.99 可得最多 5,000 金币（商店 $4.99 才 5,500）——比商店更划算的「第一笔付费」陷阱，从 D2 起制造持续金币饥饿【确认】Udonis
- D3：每日奖励后弹 **Farm Bargains**（$2.99/$4.99，标「5 折/3 折」+10 小时倒计时）；D4：约 28 级撞硬墙（7 日试玩记录）——变现爬坡=「D1 完全不变现→D2 存钱罐→D3 折扣弹窗→D4 难度墙」【确认】Udonis
- 生命系统：5 命、20 分钟/个、回满 1h40m（要命=找朋友或花金币）；59% 的 top500 三消（US iOS）用交换式玩法（GameRefinery）【确认】Udonis
- Gardenscapes 战令 **Golden Ticket $4.99**；Homescapes 2025 年前后新增订阅制【确认】naavik（价格）+ Udonis（订阅）
- 2020 年「误导广告」风波（被禁）→ 小游戏（拉栓等）从后期彩蛋挪到开局必体验，以自洽广告素材【确认】Udonis

### 2.4 Candy Crush（King）：金条硬通货+超长线稳定器

- **Gold Bars（金条）＝硬通货**，2013-09 上线；消耗型（续命/续步/道具）【确认】https://candycrush.fandom.com/wiki/Gold
- 2026 年 IAP 收入 $1.2B，金条约占 60%、道具 30%、捆绑 10%【待证——仅搜索摘要（pushwoosh 转述），正文抓取未含此数据，需二次核验】
- 2024 年仍为 AppMagic 年榜第 7 左右、同比微增（「十多年后仍在缓慢爬升的稳定印钞机」）；战令 $6.99【确认】mobilegamer.biz + naavik
- 玩法为纲、极简 meta（见题一 1.4），变现靠 14.5k+ 关卡的难度税+金条经济

### 2.5 微信小游戏侧（IAA 为主）同形态的做法

**A. 平台官方方法论（微信公开课·史凯中，2024-04，GameLook 全文速记）**【确认】http://www.gamelook.com.cn/2024/04/542933/
- 变现公式：收益＝曝光×eCPM；曝光＝请求量×填充率×曝光率；**把广告频次当核心优化指标**；eCPM 平台负责
- 设计总纲：**「基于玩法设计最小循环集→刻意制造货币/资源缺口→在缺口处承接广告」**；场景原子化两类：局内挑战（开局明确目标→难度梯度→失败给额外机会）与经营成长（自动化省时/离线收益多多益善）；激励视频承接缺口场景，各页面再配 banner/原生模板广告
- 优化顺序铁律：**先提广告渗透率，再提频次**（eCPM 更平稳）
- 标杆案例《幸福路上的火锅店》（千万级流水）：货币缺口（消耗>产出）+多场景（排队/包间/大堂）→ **人均广告 8+ 次/日，DAU 商业化渗透率 55%**
- 大盘：2024Q1 用户变现 up 值同比 +25%、流量主数 +15%；**益智、消除、放置、塔防**四品类流水与 eCPM 大幅提升（消除与塔防最猛）；女性用户略多、45+ 男性 eCPM 增长明显；外部渠道用户广告流水平台配赠 40% 广告金
- 平台规则：激励视频**每用户每日可观看次数有限**（平台侧限），展示前先判断广告是否拉取成功【确认】https://developers.weixin.qq.com/minigame/dev/guide/open-ability/ad/rewarded-video-ad.html；流量主开通门槛 1000 UV（开发者社区口径）【待证】

**B. 基准数据（行业流传口径，个人博客转述，标注待证）**【待证】https://eastondev.com/blog/zh/posts/media/20260524-mini-game-monetization/
- 激励视频 eCPM 50–120 元 vs Banner 8–20 元（5–6 倍）；激励视频渗透率上限约 78%；**资源耗尽/关卡失败场景渗透率最高（38.1%）**
- 触发建议：每局 1–2 次、时长 15–30 秒；场景优先级＝资源耗尽>关卡失败>通关双倍>新内容解锁
- 消除类 ARPU 2–3 元/月属正常（休闲 3.7 vs SLG 82）；轻度游戏收入结构≈激励视频 85%+插屏 15%；ARPDAU 基准 $1–3；首充转化率基准 8%，限时折扣 +30%

**C. 2026 微信生态政策与大盘**【确认（大会转述）】https://www.163.com/dy/article/KTUVU42H05466ZM9.html + https://juyougf.com/articles/20260713-wechat-hybrid-monetization-design.html
- 微信小游戏 MAU 约 5 亿：**IAA 约 4 亿 + IAP 约 3 亿（高度重叠）**；官方定调「很多用户既看广告也付费，关键是节点匹配」；广告+混合变现游戏已成推广消耗贡献主力；模拟经营内购年增速 +200%、合成类 +70%+
- 政策：IAP 首发新品流水最高 **5000 万元不分成**；IAA 在 50% 现金分成基础上叠激励**最高拿 90% 收益**；2026-02 广告变现激励（首发）上限 7000 万；可选 30 天 40% 广告金或 90 天 35% 广ight金方案（巨游工坊转述）【待证（政策细节为二手转述）】
- 买量：腾讯 AIM+ 智能投放 2026Q2 消耗同比 +390%，支持「广告+内购」双目标混合出价

**D. 混合变现设计方法论（IAA 为主+轻 IAP 的正确姿势）**【确认（方法论文章）】https://juyougf.com/articles/20260713-wechat-hybrid-monetization-design.html + https://www.pinlekeji.com/wiki/mini-game-iap-design-guide.html
- **时间分层**：新手期（前 30 分钟）只做广告不做付费引导；成长期（D1–3）轻付费试探（1 元首充/6 元月卡，目的是「付费破冰」——有过任意付费的用户后续付费意愿为零氪的 3–5 倍）；稳定期（D3+）按 4–5 层运营：零氪（广告克制、插屏每 5 分钟≤1 次）/微氪（月卡、通行证）/中氪（限定外观、赛季通行证，**降低广告触达**）/大 R（几乎零广告）
- **激励视频铁则**：「奖励要大、频次要控」＋每日观看软上限；奖励价值**略低于**等值付费产品（防内购被广告自废）；付费用户广告频次显著低于零氪
- 小游戏 IAP 主流档位：**1 / 6 / 30 / 68 元**（首充常见 6 元；战令 68/128 元）；锚定法（先 128 后 6）；「去广告卡」是把广告用户转付费的最轻钩子
- 行业参考：混合休闲广告:内购≈40–60% : 40–60%；首日人均广告观看 >8 次且留存稳＝接受度 OK，<3 次或留存大跌＝设计有病

**E. 微信侧同形态产品实况（旁证）**
- **《抓大鹅》（蓝飞互娱，2023-12-16 上线，微信+抖音）**：3D 堆叠三消+「颠锅」体感；难度致敬羊了个羊（前期爽后期墙）；**通关解锁限定大鹅（图鉴收集）+全国排行榜**；IAA 激励视频续命/道具；峰值 DAU 破千万（2025-08 口径），2026 春节抖音 DAU 破千万、挑战赛播放 12 亿、总曝光 780 亿；已转向「文旅/非遗 IP 化运营」【确认】http://www.gamelook.com.cn/2025/08/575356/ + https://www.lightgame.cc/game/wechat-ec65dc715b.html + https://www.10100.com/article/125967226
- **《开心消消乐》小程序版**：现居微信人气榜 top10（2026-09-24 快照）——大 IP 三消以小游戏形态长期霸人气榜【确认】https://ai.xianjianwendao.com/kb/rank?platform=wx_minigame&rank_type=popularity
- **《趣乐消消》（海南挺有趣）**：微信畅销榜 #98 长尾样本；买量+IAA（插屏+激励）+去广告/道具轻内购；消除赛道 CPI 可控、ROI 回收周期短，但 LTV 天花板低、同质化严重【确认】https://www.lightgame.cc/game/wechat-c29a00a3dc.html
- **畅销榜格局**（2025-12，引力引擎转述）：前五＝《三国：冰河时代》《向僵尸开炮》《道友来挖宝》《无尽冬日》《我的花园世界》——全是 IAP 重度；**消除 IAA 产品基本不在畅销榜头部，而在人气榜/畅玩榜**（按付费排序的畅销榜天然不利 IAA 休闲）；箭头类（合成射击）新品类持续崛起【确认】https://www.sohu.com/a/977961790_121826140
- 出海旁证：柠檬微趣 Gossip Harbor（合成+剧情）2025 年流水超 $5.4 亿、9 款合成出海产品流水过亿人民币【确认】https://m.36kr.com/p/3697346329882247

### 2.6 对吸嘟嘟的即时落差（题二）
- 现状「看视频领 60 金币」是**主动领取式**广告（无资源缺口驱动、无场景情绪），对照官方方法论应改造为：结算双倍奖励、失败续步/复活、道具补给、图鉴解锁加速、每日签到补签等**缺口驱动式**激励点位
- 缺插屏/banner 层：微信官方建议激励视频承接缺口+各页面 banner/原生补位——吸嘟嘟六屏中结算/主菜单/道具铺三个屏都可补位
- 金币单币种可保留（与 RM/Homescapes 同构），但目前**没有「货币缺口」**：60 金币/次的产出与道具铺消耗没有形成失衡张力（需产出<消耗的刻意设计）
- 轻 IAP 完全未落地：微信休闲小游戏最轻结构＝6 元首充礼包 + 去广告卡/月卡（1/6/30/68 档位）
- 每日广告上限：平台硬限+自设软上限双轨；当前 60 金币/次无上限记录，也无「先渗透后频次」的排期逻辑

## 题三：留存与回访钩——D1/D7/D30 节拍与失活召回（2026-09-29）

### 3.1 留存基准（2026 年口径，用于给吸嘟嘟定标尺）

- 全品类中位：D1 ≈26% / D7 ≈10% / D30 3–4%；「好」＝35/15/5；前 25 分位＝40/20/10；**头部 top-grossing 三消高达 47/24/13**（install-weighted，US/iOS 口径）【确认（两独立信源一致）】https://blog.playio.co/d1-d7-d30-retention-benchmarks-2026 + https://turbine.games/2026/06/17/retention-benchmark-casual-2026/
- match 品类 D1 均值 32.65%（超休闲 D30 仅 1.38%）；D30 均值 iOS 3.10%/Android 2.82%【待证（基准类博客转述）】https://segwise.ai/blog/mobile-gaming-app-user-retention-strategies + https://blog.playio.co/re-engagement-strategies-lapsed-mobile-gamers
- **订阅/内购型 D30 14% vs 广告变现型 5.4%（差 2.5 倍）——IAA 产品的 D30 天花板天然低，考核口径必须换**【确认（AppsFlyer 数据转述）】playio 同上文
- 微信侧：IAA 休闲次留中位 **18–25%、头部 35–50%**（转述微信 2026 披露）；小程序次留平均 20–30%、头部 50%+【待证（二手转述）】https://juyougf.com/articles/20260702-wechat-minigame-retention-optimization.html + ref://fc9fb414
- 诊断框架：**D1 低＝首局体验/素材承诺未兑现；D7 低＝习惯回路缺失（每日目标/奖励周期）；D30 低＝内容深度+活动日历问题**【确认】playio 同上文

### 3.2 Royal Match：分阶段钩子拆解

**D1（激活层）**：
- 秒进棋盘、无叙事门槛、无加载（retry 间零等待、去掉目标横幅滑动）——「到达爽点的时间」全品类最优【确认】DoF + naavik
- 慷慨道具+Butler's Gift 连胜预置开局道具；King Robert 表情镜像情绪；单局 1–5 分钟（均值 3+）【确认】naavik + Udonis
- 区域进度条前置展示+锁定区域可见（foreshadowed content）→ 首日即有「明天继续」的可见目标【确认】Udonis

**D7（习惯层）**：
- **活动日历密度：任何时刻至少 2–3 个活动并行**（live-ops cadence 图）【确认】naavik
- **两个轮换任务事件：Mission Pursuit 与 Mission Control**——非严格每日，但轮换频率高到「几乎是常驻」；任务例：「首试过关 X 关」「收集 X 货币」；显式命名任务可缩短漏斗（移动端少一次点击=更大影响）【确认】https://www.deconstructoroffun.com/blog/2024/9/23/daily-missions-in-puzzles-why-should-we-see-them-more-often
- 团队 21 级解锁+队友生命互助；King's Nightmare 每日刷新限时挑战关【确认】Udonis + naavik
- 5 命+计时回复+金币/队友补给 → 会话节奏天然分段（等待=明天的理由）【确认】Udonis

**D30（深度层）**：
- 区域装饰大节拍（Area Chest）+每两周新关；Card Collection 长线集卡（41 级解锁、Silver/Gold 双稀有度）【确认】Udonis
- Royal League（通关全部关卡者的全球联赛）= 「内容毕业玩家」的永续钩【确认】Udonis
- 战令实证：Royal Pass 上线当月 D30 留存 +2%；King's Nightmare 改为隐形插入后 D14 留存环比 +3%（但放在主界面按钮时下载 -21%——**召回/常驻功能的摆放位置本身就是变量**）【确认】naavik

### 3.3 Gardenscapes / Homescapes：区段剧情钩

- D1：怀旧 intro video+Austin 叙事+**首关即广告同款 mini-game**（2020 误导广告风波后的自洽改造）；**首日完全不变现，先留人**【确认】Udonis Homescapes 文
- D2：Gold Reserve 存钱罐上线（金币饥饿开始）；D3：每日登录奖+Farm Bargains 折扣弹窗；D4：约 28 级难度墙（7 日实测爬坡剧本：D1 爽→D2 欠→D3 折扣→D4 墙）【确认】Udonis
- 事件密度：Fireworks Show（小任务给道具）、Flint's Adventures（首试过关奖励）在 D3–D4 密集出现，配合难度墙输出道具【确认】Udonis
- D7–D30：Day 制剧情（每 Day 有角色剧情结算）＝天然 30 日连续剧节拍；Golden Ticket 区域战令；Renovation events 7–10 天装修活动【确认】playrix helpshift + fandom + naavik
- 每日登录礼（Homescapes daily gift）是三消通用 appointment 底座，但 DoF 评价为「最浅形态」：登录即领、无玩法参与【确认】DoF daily missions 文

### 3.4 Lily's Garden：剧情连续剧钩

- 30 天剧情弧+每 Day 结算悬念（Day1 即立「30 天装修否则失继承权」总钩）；「想知道角色接下来怎样」本身是付费与回访动机（Playrix 创意总监语，同适用于 Tactile 系）【确认】lilysgarden fandom + Udonis
- Naavik 评：RM 的连胜损失厌恶是「在 Lily's Garden 的 live-ops 里已被执行得炉火纯青的 streak-based loss aversion」——Tactile 是该机制的先行者【确认】naavik
- Stories 房间支线（2022+）＝大版本级回归内容钩【确认】fandom

### 3.5 Candy Crush：极简 meta 下的留存

- meta 仅地图+Episode；每日机制以任务型活动形式存在（Classic Chocolate Box：4 任务顺序完成、可换 3 次、奖励前置可见）【确认】DoF daily missions 文
- 长留主力＝十多年 live-ops 与内容供给（题四展开）；2024 年收入仍同比微增（「越老越稳的印钞机」）【确认】mobilegamer.biz

### 3.6 微信小游戏侧留存钩（IAA 休闲实战）

**激活铁律（巨游工坊 180 天 A/B 复盘）**【确认】https://juyougf.com/articles/20260702-wechat-minigame-retention-optimization.html
- D1 流失 80% 非「不好玩」而是「未被激活」——没走完「懂规则→正反馈→可见进度」的爽点循环；**次留优化本质＝第一天就种下「明天回来的理由」（未完成任务/未领奖励/未探索内容）**
- 一款塔防产品：次留 22%→45%+、7 留 8%→22%；次留翻倍后 30 日 LTV +3.2 倍（留存 7 天用户 LTV=留存 1 天的 5–8 倍）
- **激励视频时机比数量重要 10 倍**（正确时点投放次留 +8–12pp）：①复活场景先播 3 秒「就差一点」动画再弹复活（点击率 31%→54%）；②资源短缺时「看视频双倍收益」转化 ×2.3；③离线收益放大（「离开期间自动探索 3 房间，看视频解锁第 4 隐藏房」→ 完播率 78%）
- 新手引导：自由探索+适时提示 vs 强制教程 → 次留 27%→36%（但首日通关率 -5%——通关率与留存非正相关，**保留「未完成感」**）
- 签到 A/B：「10/20/40 逐日翻倍」vs「连 7 天大礼」→ 翻倍组 7 留 +14pp（「断了就亏大了」损失厌恶锚）
- 社交三招：对战邀请码（回流用户 7 留=普通 1.7 倍）；好友浇水（分享率 11%）；排行榜「接近效应」只展示 ±1–3 名好友（点击排行后继续游戏概率 +18%）

**其他微信侧数据点**：
- 离线收益＝生态级留存杠杆（《剑与远征》《无尽冬日》到整个微信小游戏生态的留存底盘）【待证（知乎专栏，403 仅存摘要）】https://zhuanlan.zhihu.com/p/2080605300269359886
- 爆款留存五件套：签到（习惯养成）/等级（沉没成本）/奖励过期提醒（损失厌恶）/排行榜（社交认同）/进度条（目标梯度），实例数据：次留 +8%、7 留 15%→21%、通关率 +30%【待证（知乎专栏 403，搜索摘要级）】https://zhuanlan.zhihu.com/p/2013712987437967093
- 案例：签到+挑战阶段目标设计 → 次留 28%（圣捷游戏，原文 404，摘要级）【待证】https://www.sohu.com/a/1020940945_122569490
- 每日签到可使日登录率 +20%；世界杯集 32 国旗皮肤活动要求连续登录 16 天【待证（10100 转述微信开放社区）】https://www.10100.com/article/54740184

**微信官方召回通道（小游戏版 push）**【确认（官方文档）】
- 订阅消息：绝大多数模板为**一次性订阅**（每次提醒都要游戏内重新调起订阅），仅「游戏更新提醒」为长期订阅 https://developers.weixin.qq.com/minigame/dev/guide/open-ability/subscribe-message.html
- **关系链互动提醒**：好友互动提醒、排行榜好友超越提醒——各订阅 1 次即可持续触发服务通知（好友赠礼/偷道具/排行榜被超越）＝天然的社交召回引擎 https://developers.weixin.qq.com/minigame/dev/guide/open-ability/subscribe-system-message.html

### 3.7 失活召回件（Re-engagement 标准打法）

**框架（playio 2026-06）**【确认】https://blog.playio.co/re-engagement-strategies-lapsed-mobile-gamers
- 成本：**召回失活用户成本＝拉新的 1/5**
- 分层：高价值（有付费史）→VIP offer+专属活动邀请；中价值（深度游玩过、未付费）→中度奖励+新内容通知；低价值 →**低成本激励视频**（对未付费者推 IAP 促销是浪费）
- 按流失原因给方案：内容耗尽→新内容/季节活动；**卡关弃坑→直接送过墙资源（boosters/货币）**；注意力转移→差异化事件；技术挫败→先说修了什么
- 渠道组合：push（个性化：「上次玩到第 X 关」「新章节开了」「你的公会等你」）；邮件/SMS（7/30/60 天分层序列）；再营销广告（素材≠UA 素材）；**liveops 季节活动+定向 push 组合效率最高**
- 回归承接（catch-up）：回归资源礼包（离线期积攒一次性发放）、回归专属任务链（Clash Royale 回归挑战）、变更摘要式教学回顾
- 微信落地组合（本报告综合）：一次性订阅消息（新区域/新活动上线时点触发）+关系链提醒（好友赠送/排行榜被超）+「新图鉴可爱上架」通知+回归金币礼包+卡关救助礼包

### 3.8 对吸嘟嘟的即时落差（题三）
- 六屏目前**没有任何「明天回来的理由」结构**：无签到、无每日任务、无待领奖励、无离线收益、无进度到期损失厌恶件——对照基准，D7 习惯层完全空缺
- 图鉴 3/6 是唯一长线钩，但缺三件套：解锁提醒（订阅消息）、「新可爱上架」回归触发、集齐奖励闭环
- 「看视频领 60 金币」无翻倍递增/无每日限次节奏，浪费了签到类损失厌恶空间
- 无关系链位（好友赠礼/超越提醒），微信生态最强的社交召回引擎未接
- 结算屏无「差一点」挽留动画与复活位设计（3 秒情绪消化→复活点击率 31%→54% 的实证可直接用）
- 无卡关救助召回包（卡关弃坑用户的过墙资源直送）

## 题四：活动 / LiveOps——RM 事件体系与节拍、战令结构、微信侧活动打法（2026-09-29）

### 4.1 品类基准：什么叫「及格」的活动矩阵（Sensor Tower 2026-05）

- 对 12 款头部休闲游戏的 live-ops 基准（Playliner 追踪，>5,500 个标准锦标赛实例）：**每款至少 1 个标准锦标赛；平均 2.5 个标准锦标赛格式 + 1.4 个冲刺目标型 + 0.9 个冲刺限时型**；冲刺限时型节奏最快（平均 9.4 场/月/游戏）【确认】https://sensortower.com/blog/what-royal-matchs-calendar-teaches-about-live-ops-in-2026
- 及格线建议：≥2 个标准锦标赛 + ≥1 冲刺目标型 + ≥1 冲刺限时型；不及格者即落后品类预期。反面案例：MONOPOLY GO! 无冲刺赛；Matchington 无冲刺目标型；Gossip Harbor 6 个冲刺目标型但 0 个冲刺限时型【确认】同上文
- 2025 年大盘结构（Appfigures）：休闲占 top1000 收入产品 32%（中重度 50%、赌场 11%）；**解谜是休闲第一大、全品类第二大（占 top1000 收入产品 16.3%）**【确认】https://mobilegamer.biz/data-digest-royal-match-hits-6bn/ （ref://b763dce9）

### 4.2 Royal Match：事件体系全谱（三层架构）

**事件编年史与收入冲击（Naavik + GameRefinery，上线首 15 个月）**【确认】naavik
| 时间 | 事件 | 30 天收入冲击 |
|---|---|---|
| 2021-02 上线自带 | King's Cup（单机 PvP）+ Book of Treasure / Propeller Madness（收集型，伪装成活动的常驻二级进度） | — |
| 2021-06 | Royal Pass 战令 | **+31%**（D30 留存 +2%） |
| 2021-06 | Endless Treasure（Prize Road） | **+20%** |
| 2021-10 | Sky Race（PvP 竞速，最快赢 15 关者前三拿奖） | **+12%** |
| 2021-10 | Piñata Party（限时里程碑，全奖励可见） | +6% |
| 2021-11 | Team Treasure（团队宝箱，奖励=全套道具；留存导向） | +2% |
| 2021-12 | Lightning Rush（1 小时 5 连消竞赛，赢者通吃） | +9% |
| 2022-02 | King's Nightmare（广告同款限时关；主界面入口致下载 -21%，改隐形插入后 D14 留存环比 +3%） | +1% |

**2026 年现行三层活动架构（Sensor Tower 拆解，RM＝全球 IAP 收入第一休闲游戏）**【确认】Sensor Tower 同上文
- **RM 同时跑 6 种标准锦标赛格式**，且其 IAP 收入**在周末集中冲高——由活动带来的转化驱动，而非 DAU/下载/时长**
- **短期层（紧急感+损失厌恶，玩今天的理由）**：连胜事件 **Lava Quest**（连赢 7 关否则清零）；冲刺赛 **Space Mission / Propeller Madness**；滚动 offer **Jungle Treasure**——在连胜/冲刺将断时转化付费
- **中期层（社交+竞争，管一周的节奏）**：**Weekly Contest / Archery Arena / Team Battle / Champion Clash** 锚定周节奏；**Friends Train Journey**（好友 co-op）；**Mission Pursuit**（里程碑奖励）；**Merge Smith**（合成副玩法延展中期循环）
- **长期层（长线追猎，撑月/季度）**：**Culinary Collection 图册收集（为期 2 个月的 album chase）**；**Easter Pass**（季节进度轨）；图册+通行证=骨架，其余活动都绕其运转
- **排期艺术（事件不是独立的，是连招）**：图册周期后段重复卡变多→「保新卡包」升值→**Train Journey 把保新卡包设为 co-op 大奖**（为团队而玩）→活动最后 3 天弹出 **Team Gift Offer**（全队金币+道具+无限生命）——长线追猎临近完成时压力被层层加码
- 代价与争议：RM 的难度驱动变现同时也是玩家投诉最集中的点——活动日历之所以有效，正因为事件与「摩擦时刻」交叉【确认】同上文
- 季节活动：已确认存在 **Easter Pass**（季节轨）与万圣节/圣诞/情人节等换装活动传统；「Halloween/Christmas/Valentine 为 Top3 季节活动」的说法**本轮未找到直接排名信源**【待证——甲方已知信息，保留待证标记】

### 4.3 战令 / Pass 结构对照

- **Royal Pass**：37 级解锁；月度 30 步；定价 **>$10**（品类最贵：Homescapes $4.99 / Lily's Garden $5.99 / Candy Crush $6.99）；奖励走社交声望（生命上限+60%×1 月、金色头像框、全队小奖励）+复活道具/金币；上线 30 天收入 +31%【确认】naavik + Udonis
- **Gardenscapes Golden Ticket**：区域进程型通行证 $4.99；Homescapes 2025 年前后新增订阅制【确认】naavik + Udonis
- **Candy Crush**：通行证 $6.99（naavik 口径）；**All Stars 2025 锦标赛：15M+ 参与者、真实奖金池，把游戏推到史上第二高收入月（单月净 IAP ~$110M）**；live-ops 类型：季节庆典、锦标赛、进度挑战、收集奖励、竞技排行榜，每周近乎固定上新关卡【确认】https://stepico.com/blog/candy-crush-business-model/
- 广告位修正：**Candy Crush 已非完全无广告——King 数年前撤掉强制广告，保留少量激励视频（换续步/生命/道具）**；主体仍 IAP【确认】stepico 同上文（更新题二 2.2 中 CCS「无 IAA【待证】」的表述）

### 4.4 Playrix / Tactile 活动体系要点

- Gardenscapes：**Renovation Events**（7–10 天，消「装修票」装修场外房间+三选一装饰）＝把家装 meta 本身做成活动模板；Fireworks Show / Flint's Adventures（首试过关）等小事件高频轮换【确认】fandom + Udonis
- Homescapes：daily gift（登录礼，DoF 评为最浅 appointment）+ 小游戏事件；每周上新关卡【确认】DoF daily missions 文 + Udonis
- Lily's Garden：**streak-based loss aversion live-ops 的品类先行者**（RM 的连胜损失厌恶是向它取的经）；Stories 房间支线=大版本级回归内容【确认】naavik + fandom

### 4.5 微信小游戏侧的活动 / LiveOps 打法

- **《抓大鹅》（最接近吸嘟嘟形态的本土标杆，旁证）**：**每日更换消费场景主题**（烧烤店/超市等）保持新鲜感；**通关解锁限定大鹅+全国排行榜**（收集×竞争复合）；难度致敬羊了个羊（前期爽后期墙）；后续走向 **IP 化运营**（文旅/非遗联动）；2026 春节抖音端：挑战赛播放量 12 亿+、总曝光 780 亿次、DAU 破千万【确认】https://www.lightgame.cc/game/wechat-ec65dc715b.html + https://www.10100.com/article/125967226 + http://www.gamelook.com.cn/2025/08/575356/
- **视频号直播=IAA 小游戏的活动级增长位**（官方口径）：IAA 直播场观增长迅速、优质直播间破 10 万场观；找茬/脑洞品类靠直播实现日活与流水数倍增长（原三位数日流水产品翻数倍）【确认】gamelook 史凯中（题二 2.5A 同链）
- **小游戏运营常规位**（知乎七方向/运营综述，摘要级）：社交玩法、中心化推荐位、广告采买、**矩阵互跳**（小游戏间/公众号跳转）、私域（企业微信/社群）【待证（知乎问答摘要）】https://www.zhihu.com/question/278419425
- **微信侧活动触发基建**＝订阅消息（一次性，活动上线时点触发）+关系链互动提醒（好友赠礼/排行榜被超越，长期有效）——对应 App 的「活动 push」（详见题三 3.6）【确认】微信官方文档
- 2026 微信平台侧赋能方向：内容生产、商业变现、长线运营三维度全链路 IAA 赋能；「解谜、消除等经典休闲品类仍具持续升级空间」被平台点名【确认】https://www.163.com/dy/article/KTUVU42H05466ZM9.html

### 4.6 对吸嘟嘟的即时落差（题四）
- 吸嘟嘟当前**活动矩阵=0**，对照品类及格线（≥2 标准锦标赛+2 冲刺型）与 RM 三层架构，短期/中期/长期三层全部空缺
- 六屏无任何活动入口位/活动日历位；无周末节奏设计（RM 收入周末峰值的启示）
- 图鉴 3/6 有「长期追猎」的潜质（对应 RM 的 2 个月 album chase），但无周期、无稀有度分层、无「保新卡」类稀缺设计、无 co-op/分享联动
- 无通行证（免费轨都没有，更别说付费轨）
- 无季节/节令活动位（治愈系+收集可爱天然适配节令上新，如春节/樱花季）

## 吸嘟嘟适配初判（三档：IAA 可直接用 / 需改造 / IAP 重度专属不适用）

> 结论基于吸嘟嘟现状基线：六屏静态板（主菜单/章节旅程/HUD/结算/图鉴/道具铺）+ 图鉴 3/6 + 金币单币种 + 「看视频领 60 金币」唯一插点位 + IAA 为主轻 IAP 定位。

### 档一：IAA 小游戏可直接用（微信生态零冲突，拿来做）

1. **缺口驱动式激励视频矩阵**（替换现在的「主动领取式」60 金币位）——官方方法论直译：「最小循环集→制造货币/资源缺口→在缺口处承接广告」：
   - 结算屏双倍金币位（资源短缺场景转化率 ×2.3 实证）
   - 失败续步/复活位：先播 3 秒「就差一点」动画再弹复活（点击率 31%→54% 实证；治愈系把「差一点」做成小可爱表情更顺）
   - 关前道具试用/补给位；图鉴解锁加速位（收集×广告复合钩，吸嘟嘟独有优势位）
   - 离线收益位：「离开期间小可爱们帮你攒了金币，看视频翻倍」——治愈系叙事天然适配，完播率 78% 类设计
   - 主菜单/道具铺/结算补 banner/原生位（官方建议的页面级补位）
   - 排期纪律：**先渗透后频次**；首日人均 8 次左右为健康线（<3 次=设计有病）；设每日软上限
2. **每日任务显式化**：3 个小任务（赢 X 关/用 X 次道具/收集 X 星）→ 金币+图鉴碎片；DoF 论证「显式命名+专属入口+少点击」；与每日签到联动出 appointment 组合拳
3. **翻倍递增签到**：「10/20/40…逐日翻倍」替代固定大礼（7 留 +14pp 实证；「断了就亏大了」）
4. **章节结算宝箱（Area Chest 式）**：把「章节旅程」从静态板改为双层节拍——每关产出星星型进度→章节内任务逐个点亮→章末宝箱（金币+道具+图鉴解锁券）
5. **King Robert 式情绪载体**：选一只「主理小可爱」常驻 HUD，表情镜像步数与胜负——RM 已验证的最强情绪杠杆，治愈系比城堡王更顺
6. **微信召回件包**：一次性订阅消息（新章节/新可爱上架/体力回满）+ 关系链互动提醒（好友赠礼/排行榜被超越，一次订阅长期触发）+ 回归金币礼包 + 卡关救助包（卡关弃坑者直送过墙资源）
7. **周末峰值排期**：RM 收入周末冲高由活动转化驱动——小游戏版=周末双倍活动日/限定可爱限时上架/好友互赠体力加成
8. **图鉴闭环三件套**：解锁动画 → 集齐奖励（金币/称号/限定皮肤）→ 「下只新可爱」预告位——把 3/6 图鉴从静态记录变成运营资产

### 档二：头部 IAP 经验，需改造后用（转译到 IAA 语境）

1. **Royal Pass → 「嘟嘟通行证」轻战令**：RM 月度 30 步改成「免费轨+广告轨」（看视频解锁额外档），付费轨仅 6 元档（微信休闲小游戏档位锚 1/6/30/68）；奖励把 RM 的「社交声望」转译为「收集声望」（限定可爱皮肤/图鉴专属框）
2. **Endless Treasure → 广告版 Prize Road**：免费奖励前置可见+「再看 1 个视频解锁下一档」——禀赋效应的 IAA 等价物
3. **Gold Reserve 存钱罐 → 广告存钱罐**：D2 起「看广告攒双倍金币」入罐、隔日可领（把 $2.99 砸罐换成回访钩，或留作 6 元轻 IAP 位）
4. **EoR 递进税 → 广告递进流**：RM 的 $2→$8.95 递进在 IAA 语境=「首看免费续步→第二次金币→第三次分享或明日再来」——保留损失厌恶节拍但不设现金墙
5. **RM 卡牌册机制 → 图鉴升级**：Silver/Gold 双稀有度、重复换任选、集齐回环奖励——整套套在「收集小可爱」上（普通/稀有两档可爱、重复碎片换任选、套集奖励）；周期拉到 4–8 周（对标 2 个月 album chase 的节奏感）
6. **难度墙节拍**：Homescapes 的 D4/L28 硬墙过重；取 RM 温和版——hard 关前置标注+连胜必给开局道具（Butler's Gift 式），硬墙点位留给广告救助而非付费墙
7. **团队系统 → 轻量社交先行**：先做好友互赠体力+「接近效应」排行榜（只展示 ±3 名好友，继续游戏概率 +18%）；Team Battle 类 co-op 事件成熟后再上
8. **季节活动 → 本土节令版**：「万圣/圣诞/情人节」传统改配春节/中秋/樱花季/国庆等本土节令+微信生态节点；活动形式用「限定可爱上新+图鉴主题套」（收集系季节活动天然比家装系轻）
9. **赛事矩阵 → 及格线先达标**：≥2 个标准型+≥1 冲刺目标+≥1 冲冲刺限时（ST 品类基准），IAA 版奖励全部用金币/道具/图鉴碎片
10. **「三消+收集装扮」混合 meta 的 1.5 倍杠杆**：同屏广告展示与时长约为纯三消 1.5 倍的实证方向（待证但方向明确）——吸嘟嘟的收集线就是这条混合 meta 的本土化载体

### 档三：IAP 重度专属·不适用（明确不做）

1. **纯 IAP 无广告模型**（Dream Games 哲学、「no ads, ever」）——与吸嘟嘟 IAA 为主的定谳直接冲突；但其中「付费用户降广告」的分层原则必须继承
2. **EoR 现金递进税与 >$10 月度战令**——微信消除类 ARPU 2–3 元/月量级（休闲 3.7 vs SLG 82），撑不起 RM 式重税；战令定价上限对标微信 6/30 元档
3. **61.5% 付费下载+名人广告 UA 策略**——小游戏生态靠微信社交裂变、中心化推荐与平台激励（IAP 首发 5000 万不分成、IAA 激励最高 90%），买量模型与手游完全不同
4. **Royal League / 满级全球联赛**——需要 10k+ 关与海量用户底盘，图鉴 3/6 阶段遥不可及
5. **Webshop / 订阅制基建**——微信小游戏无对应基建（订阅消息+虚拟支付是本生态等价物，形态不同不可平移）
6. **Peak 式每两周百关内容工业**——吸嘟嘟应走「收集可爱上新+节令活动」的内容轴，而非关卡量产轴
7. **剧情连续剧重叙事**（Lily's Garden 式）——治愈系轻叙事可点缀，但 30 天剧情弧的内容成本与吸嘟嘟「收集小可爱」定位不匹配，不建议做主线

### 六屏逐屏落差速查（吸嘟嘟现状 → 头部基准）

| 屏 | 现状缺口 | 对应头部做法（题号） |
|---|---|---|
| 主菜单 | 无签到/无每日任务/无活动位/无 banner | 翻倍签到+显式每日任务+活动日历入口（题三/四） |
| 章节旅程 | 无星星货币/无章节任务/无章节宝箱 | 星星→任务→Area Chest 双层节拍（题一） |
| HUD | 无情绪角色/无连胜奖励/无活动快捷位 | King Robert 表情+Butler's Gift 连胜（题一/三） |
| 结算 | 无双倍位/无「差一点」复活流/无翻倍递增 | 3 秒情绪动画+复活位+双倍金币（题二/三） |
| 图鉴 | 3/6 无解锁动画/无集齐奖励/无上新预告/无稀有度 | RM 卡册机制全套+2 月周期追猎（题一/四） |
| 道具铺 | 无货币缺口/无 6 元首充/无去广告卡 | 缺口经济+轻 IAP 三件套（6 元首充/去广告卡/月卡）（题二） |

### 最短路径优先级（一句话结论）
**先做档一的 1/2/4/8 四件**（缺口式广告矩阵+显式每日任务+章节宝箱+图鉴闭环）——一次性补齐「缺口驱动变现（题二）+D7 习惯（题三）+D30 收集追猎（题四）」三层结构，是六屏静态板到「可运营 IAA 产品」的最短路径；档二在其后按战令→存钱罐→节令活动的顺序叠加；档三列入负面清单。

---

## 附：信源与抓取失败记录（完整性声明）

**主要信源清单**（详见各节内联链接）：deconstructoroffun.com（RM 深拆、每日任务专文）、naavik.co（RM deep dive）、dreamgames.helpshift.com / playrix.helpshift.com（RM/GS 官方 FAQ）、sensortower.com（RM live-ops 日历 2026）、mobilegamer.biz（AppMagic 年榜/数据摘要）、app2top.com（AppMagic $5B/$6B 里程碑）、pocketgamer.biz（51% 报道，正文 403 以搜索摘要+二手转述双源交叉）、blog.udonis.co（RM/Homescapes 商业化拆解）、stepico.com（Candy Crush 商业模式）、grokipedia（Best Fiends）、gamelook.com.cn（微信 IAA 公开课速记）、微信官方文档（激励视频/订阅消息/关系链提醒）、163/toutiao（2026 微信小游戏大会转述）、juyougf.com（混合变现/留存实战）、pinlekeji.com（IAP 设计清单）、eastondev（eCPM 基准）、lightgame.cc（抓大鹅/趣乐消消拆解）、36kr（合成出海/抓大鹅）、esports.net（RM 区域数）、各产品 fandom 维基。

**抓取失败记录（如实）**：pocketgamer.biz 51% 文（403，双工具均失败→改用搜索摘要+mobilemarketingreads 全文交叉）；medium.com Udonis《Lily's Garden Monetization》（403）；royalmatch.fandom.com/wiki/1-20 与 gardenscapes.fandom.com/wiki/Garden_Locations（403）；zhuanlan.zhihu.com 爆款留存拆解（403，仅存搜索摘要）；businessofapps.com RM 统计页（超时，其数据以 raijinn 转述标待证）；sohu 留存案例页（404，仅存摘要）。

**已知口径分歧（未强行归一）**：①RM 累计消费 AppMagic 口径 $5B（2025-01）→$6B（2025-05）vs Udonis「$3B+」（净收入口径，两者并记）；②RM 2024 收入 $1.46B（AppMagic/ST 一致）vs 章节内其他月度口径；③Candy Crush 终身 $8B（AppMagic，2025-05）vs 「>$10B 累计」（stepico 引 Business of Apps，含全平台）；④微信 IAP 首发激励「5000 万不分成」（大会转述）vs 博客口径「前 1000 万高激励+2:8 分成」（均记录，前者标确认后者标待证）。

（调研完成时间：2026-09-29 · 调研席输出 · 全文以本文件为准）
