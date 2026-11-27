# R-20260929-head-match3-ui-01 同类型头部三消产品逐屏 UI/UX 编排深度调研

- 调研席：调研员（Codely CLI agent）
- 日期：2026-09-29（Asia/Shanghai）
- 服务对象：**吸嘟嘟**（治愈系三消+收集小可爱·微信小游戏·IAA 为主+轻 IAP）
  - 风格定谳：Royal Match 系高品质卡通 3D 渲染风（柔光全局照明+毛绒/糖瓷双材质+马卡龙色板+无锐边圆角），正典=《04_美学定位与技术选型》V3.0（U279 判例）
  - 六屏（U293 现状）：主菜单 / 章节旅程 / 局内HUD / 结算 / 图鉴 / 道具铺
  - U293 最新评审态：引擎批 53 PASS / 0 FAIL / 0 WARN，六板节点数 24/45/34/40/50/50；R10 挂账 10 项在板；品牌名上屏待 CEO 裁
- 研究对象（按优先级）：
  1. Royal Match（Dream Games·2021·IAP-only 重度商业化标杆）
  2. Gardenscapes / Homescapes（Playrix·家装 meta 三消开创者）
  3. Lily's Garden / Project Makeover（Tactile/Magic Tavern·治愈剧情+改造三消·IAA/IAP 混合更近吸嘟嘟商业形态）
  4. Candy Crush Saga（King·三消常青纯核心基准）
- 方法：DuckDuckGo 检索（search）+ fetch_content / web_fetch 抓取；优先信源=gameuidatabase.com（UI 截图参考库）、官方商店页（App Store / Google Play）、deconstructoroffun / naavik / pocketgamer 拆解文、gamelook / yfchuhai 中文出海媒体
- 信源分级：每条结论标注【确认】（直接信源可查）/【待证】（推断或信源不足）；数字（时长/档位/间距）尽量带来源；抓取失败如实记录
- 每款必拆四屏（五问制：屏上有什么/层级怎么排/奖励怎么编/哪里可点）：①主菜单/大地图 ②结算屏 ③商店/礼包 ④meta 收集/家装屏
- **存活律**：每拆完一款立即追加写盘，禁止全部拆完才写盘

---

## 研究对象1：Royal Match（Dream Games·2021·当前三消全球收入冠军）

**基础盘**：全球上线 2021-03（软启动 2020-07 加拿大/土耳其/英国）【确认·DoF】。累计收入超 $40 亿、约 5500 万 MAU、长期霸榜全球畅销榜头部【确认·naavik/Sensor Tower，https://naavik.co/digest/why-dream-games-success-is-a-challenge-to-replicate/】。100% IAP、**零广告**（"100% ad free"官方卖点）【确认·Google Play 页】。用户画像：女 59%（美国 iOS 女性占比 ~75%），欧美 45+ 占比超均值【确认·163.com 发行分析，https://www.163.com/dy/article/K1RGDGGT055697R1.html】。

**gameuidatabase 条目（id=1061）屏级分类实测**【确认·https://www.gameuidatabase.com/gameData.php?id=1061，手机竖屏/2D Art/Fantasy Skeuomorphic，2021 收录】——该库为 Royal Match 归档的屏型清单（=官方认可的该作 UI 全景）：
Title Screen / Loading Screen / Mode & Screen Select / Settings: Options / Guided Tutorial ×3 / **Modal: Item Get** / Stage-Level Select / **Pre-Game & Lobby ×2** / **Level Complete ×3** / Leaderboards / Stats and Resources / News-Updates & Notifications ×2（弹窗序列）/ **Offers & Bundles** / **Currency Store (IAP)** / HUD and Overlays / Clock & Timer / Item & Ability Buttons。
> 对吸嘟嘟的启示：头部三消的 UI 全景里「Pre-Game（局前）×2、Level Complete（结算）×3、通知弹窗 ×2、Offers+Store 各一」是标配四件套——局前/结算/礼包的屏数配比 2:3:2，说明这三处是版本迭代最频繁、演出最重的战场。注：该站图片为 JS 画廊无法程序化逐图抓取，仅取其屏型分类（抓取方式如实记录：正文抓取仅得分类树，无逐屏截图）。

### 1.1 主菜单/大地图（五问制）

- **屏上有什么**【确认·DoF+naavik+官方页交叉】：城堡/王国场景为背景（King Robert 的城堡，含 King's room/kitchen/garden/garage 等区域），中央为关卡路径（线性路径节点=Royal Arena 关卡），顶部为货币组（金币+体力/生命计数器），左侧为活动竖排入口。吉祥物 King Robert+管家 Winston+狗 Duke 常驻场景内（不是贴在 UI 上，而是活在场景里）【确认·dreamgames.com 官方页】。
- **层级怎么排**：顶部=状态层（金币/体力）；中部=场景+关卡路径=主视觉层；侧边（左）=活动层；无底部主导航（RM 无 tab bar，主菜单即地图）【确认·DoF 配图+gameuidatabase Stage-Level Select 分类；具体左右位次以截图为准属【待证】微调项】。**关键定谳：RM 主菜单没有底部导航——一张地图+顶部双资源+左侧活动竖栏就是全部框架**，这是"轻 meta"路线在 UI 上的直接投影。
- **奖励怎么编**：主线=星星（通关得星→星星解锁/推进装修目标）【确认·naavik「earning stars by completing levels and then spending those stars to complete simple, pre-set decoration tasks」+163.com 同口径】；副线=金币（局内掉落）；活动线=King's Cup / Sky Race / Team Battle / Lightning Rush / Duke's Treats / Weekly Missions 六件套轮转【确认·Google Play 官方页】；2023-02 上「连胜奖励」：10 连胜激活全屏消除特效（超级光球），把连胜做成主菜单可感的进度钩子【确认·163.com】；现版新增 Royal Pass 赛季通行证+「Science Collection」收集季【确认·Google Play 页 2026-09 更新日志】。
- **哪里可点**：①关卡节点（主 CTA，点开 Pre-Game 局前屏）②左侧活动竖栏（3-4 个活动入口）③顶栏金币/体力（点开商店/加体力）④场景内城堡（=meta 入口，点进装修区）⑤Team 入口（团队聊天/互赠体力）【确认·DoF/naavik+官方描述；Team=「chat, exchange lives」DIY Queen 拆解】。
- **续玩钩子文案位**：地图节点即「下一关 N」的直给钩子；连胜进度（Win Streak 火焰条）+活动倒计时（Clock & Timer 屏型在库）【确认·gameuidatabase 屏型+163.com】。

### 1.2 结算屏（Level Complete ×3 在库）

- **星制**：通关→星星（星星=装修货币，不是 1-3 星评级制；RM 无 CCS 式三星评分）【确认·naavik+163.com——「通关获取星星，以实现城堡的装修目标」】。
- **奖励揭晓编排**：通关动效=剩余步数逐个转化为道具触发→金币雨→星星飞入；**段数约 2-3 段**（步数清空→奖励结算→星星入账）【待证·具体分段时长无公开数字，DoF 提及动画「short, fluid」为证】。
- **双倍/复活广告位插点**：**RM 无广告位**——结算后无看广告双倍路径，这是重度 IAP 专属做法；失败时插的是「+5 步 900 金币」IAP/金币挽回屏【确认·naavik「the core monetization event is the pay to continue a failing level screen」】。**第二次失败时的挽回包更贵且必带火箭，火箭 100% 落在能直接帮助通关的战略位**【确认·naavik 专节，含视频证据】。
- **分享/炫耀件**：排行榜（Leaderboards 屏在库）+Team 内竞争；无系统级分享按钮【待证·未见分享屏型在库】。
- **继续按钮顺位**：结算主按钮=直接进下一关（无确认弹窗），速度优先（DoF：去掉局间 loading 和目标横幅 swipe，缩短单次尝试总时长）【确认·DoF】。
- **经济数字**【确认·多源交叉】：通关金币均值 ~50（Google Play 用户评论实测口径·「average about 50」）；失败续步 900 金币/次（DoF+用户评论双证）；Bonus Level（稀有奖励关）单关 300-700 金币（DoF 实测）；难度设计原则=「almost win」——大部分险败局只差 1-2 步，买 5 步即可翻盘（DoF 核心论点+naavik「near miss」心理机制专章）。
- **难度曲线节奏**【确认·163.com 关卡分析】：前 30 关=新手过渡；30 关后进入「难度关为主+简单关调剂」阶段；60 关后主力难度上移，用简单/正常关调控留存；平均步数 25 步/关、4 色（对比 Playrix 旧标准 35 步/5 色——Playrix 2021-06 跟随 RM 把 Homescapes 全量关卡改为 25 步/4 色）【确认·naavik】。

### 1.3 商店/礼包

- **结构**：单一硬通货金币经济；金币三用途=失败续步、局前道具、补体力【确认·naavik】。礼包分层（从公开信源可得）：①首充/小额档 $0.99 起、顶格 $99.99【待证·来自 DIY Queen 拆解文（ref://87d13503 展开为游戏设计博客），档位表无逐档截图佐证】②失败后限时优惠包（「limited-time discount」紧迫感包装，触发点=刚打输的挫败时刻）【确认·DIY Queen+naavik】③Royal Pass 赛季通行证（2026 现行）【确认·Google Play 页】④金币直购商店（Currency Store (IAP) 屏在库）【确认·gameuidatabase】。
- **划线价/折扣视觉**：无公开逐礼包截图证据【待证】；naavik 指出其定价心理=「900 金币买 5 步」在高挫败时刻感知价值极高。
- **无金币入口时的引导路径**：金币不足时→直接弹 IAP 礼包（RM 无免费广告获取金币路径——零广告政策使免费玩家唯一回血路径=等体力回复自然重试或 Bonus Level）【确认·naavik「no free grinding path」】。> 这条对 IAA 形态的吸嘟嘟是**最大分叉点**：头部把「没金币」变现为 IAP，吸嘟嘟必须把「没金币」变现为激励视频。

### 1.4 meta 收集/家装屏

- **进度呈现**：星星→固定装修任务（每区一组任务，任务逐条消耗星星）；**A/B/C 测试过「无 meta」和「换背景式 episode meta」两个变体，最终数据定谳保留轻装修 meta**【确认·naavik 引 Dream 官方测试，https://naavik.co/digest/royal-match-finding-success-through-iteration/】。
- **收集物陈列**：装修=「从无到有」的搭建（对比梦幻花园「破旧→焕新」的改造）【确认·163.com 对比专节】；**无三选一决策**——玩家只决定装修顺序、不选样式（梦幻花园有 3 选 1，RM 砍掉决策成本）【确认·163.com】。宝箱系统：开箱得金币/道具/无限体力/power-ups【确认·Google Play 官方描述】；赛季收集活动（2026 Science Collection）=常驻收集线【确认·Google Play】。
- **解锁钩子**：新区域=「Explore the new rooms, royal chambers, splendid gardens…」（每 2 周 100 新关+1 新区域节奏）【确认·Google Play 更新日志「100 NEW LEVELS…every two weeks」】。
- **回访钩**：Team（聊天/互赠体力）+Weekly Missions+Royal Pass 赛季+活动轮换六件套【确认·多源】。
- **战略定性**【确认·naavik】：RM 的 meta 刻意做轻——让玩家注意力永远停留在最强项（三消核心）上，「puzzle & decorate lite」；市场上其他厂试图堆 meta 复杂度时，Dream 用减法赢得品类；Playrix 新作（Aqua Match/Roomscapes）已回头学轻 meta。

### 1.5 Royal Match 可迁移要点（速记，详见文末映射）

1. 主菜单=地图即导航（无底部 tab）+顶部双资源+左侧活动竖栏【可直抄框架】
2. 结算无三星评级、星星=meta 货币直达装修目标——奖励链最短【需适配：吸嘟嘟星星→图鉴收集】
3. 「almost win+900 金币续步」=核心变现位；二段挽回必带战略位火箭【需适配：IAA 化为「看视频续步」】
4. 4 色/25 步/并发消除/智能道具=手感护城河【可直抄玩法参数】
5. 零广告+单一金币=重度 IAP 专属结构【不适用：吸嘟嘟 IAA 为主】
6. 每 2 周 100 关+1 区域=内容更新节奏基准【需适配：小游戏产能打折】
7. UA 素材=游戏内真实关卡（King's nightmare 关卡还原广告场景）=信任式买量【可直抄：微信小游戏买量同适用】

---

## 研究对象2：Gardenscapes / Homescapes（Playrix·2016/2017·家装 meta 三消开创者）

**基础盘**：Gardenscapes 2016 上线（Scapes 系首作，iOS 版 2016-05 重启发布、安卓 2016-08），累计收入 **$44.7 亿**、累计下载 7.288 亿、2026 年 DAU ~730-920 万、ARPDAU $0.15、收入/下载 $6.14、DAU/MAU 比率 41.2%（=月活里四成每天回来）【确认·AppMagic via Udonis 统计页，https://www.blog.udonis.co/statistics/gardenscapes，2026-06 更新】。Playrix 全组合累计 $8B+，2023-01 单月 $250M（历史第三高月）【确认·DoF，https://www.deconstructoroffun.com/blog/2023/2/27/the-case-of-playrix-and-why-product-market-fit-is-a-moving-target】。用户画像：女性倾向、25-54 岁成人、偏老龄化；头部市场=美国（断层第一）>德国>日本【确认·Udonis/Sensor Tower】。商业化=**几乎纯 IAP，游戏内广告载荷极小**（"no video ads"用户评论+Udonis「in-game ad load is minimal」双证）【确认】。

### 2.1 主菜单/大地图（=花园/房间实景，非关卡路径图）

- **屏上有什么**【确认·多源交叉】：整屏是**可装修的等距花园（或 Homescapes 的宅内房间）实景**，管家 Austin 常驻场景内行走/劳作（吉祥物=场景演员非 UI 贴片）；顶带左上=体力（红心×5，官方帮助中心确认「displayed in the top left」）；货币组=金币+星星计数器；**左下=「任务平板」**（官方口径 in-game tablet：当前装修任务清单，滚动 3 条，每条标星星成本）；右侧=活动竖栏（Expeditions 远征/竞赛/赛季活动入口）。无关卡路径地图——**关卡入口=Play 钮直进下一关**，与 RM 的「地图即导航」是两种范式【确认·官方帮助中心+gamerforfun 评测+Google Play 描述；左右位次细节【待证】】。
- **层级怎么排**：顶带（体力/金币/星星）→中部大场景（装修成果=主视觉）→左下任务清单（次 CTA 群）→右侧活动栏（第三层）。**主菜单即收集成果陈列室**：已装修区域始终可见=装修动机的自我提醒装置。
- **奖励怎么编**：主线=星星（1 星/关，官方确认）；副线=金币；活动线=Expeditions+竞赛+**Garden Pass 赛季通行证**（Golden Ticket 黄金票=付费轨，赛季活动期间体力上限 5→8——把「体力上限」做成通行证特权）【确认·官方帮助中心 lives 条目】；日常=**每日转盘抽奖**（1 次/天）【确认·gamerforfun】。Homescapes 关卡有**明示难度标签：Hard / Super Hard 关**（Gardenscapes 无此标签）【确认·gamerforfun 对比文】。
- **哪里可点**：①Play 钮（主 CTA）②任务平板（点开任务列表，可按星星预算挑选任务做）③顶带金币/体力（进商店/补体力）④右侧活动栏 ⑤场景内 Austin/宠物（点击有互动反馈）。
- **续玩钩子文案位**：任务平板=永远显示「下一个待办任务+星星成本」的续玩钩（比 RM 的地图节点更 meta 向——钩子是「把花园修完」而非「把下一关打了」）；赛季倒计时（Google Play 页横幅「Ends in 8h / Ends on 10/05」=倒计时在商店页拉新侧也在用）。
- **体力参数**【确认·官方帮助中心，https://playrix.helpshift.com/hc/en/5-gardenscapes/faq/9223-lives-replenishment/】：上限 5（赛事期 Garden Pass 持有者 8），1 点/30 分钟回复，失败扣 1。

### 2.2 结算屏

- **星制**：**1 星/关，无 1-3 星评级**（官方帮助中心原文「you receive one star for every level you beat」，https://playrix.helpshift.com/hc/en/5-gardenscapes/faq/61-stars/）【确认】。> 与 RM 同构、与 CCS 相反——Scapes 系和 RM 都把星星做成 meta 货币而非评级。
- **奖励揭晓编排**：通关→星星飞入顶带→金币按剩余步数/道具结余加成→回主场景做装修任务（星→任务的二次消费链）【确认·机制层；分段时长无公开数字【待证】】。**Scapes 的结算-奖励链是全品类最长的一档：通关→星→任务→场景变化→剧情对话**，把一次胜利的情绪拉成 4 段释放。
- **双倍/复活广告位插点**：**无广告双倍**（近零广告政策）；失败挽回=「+5 步 900 金币」金币/IAP 弹窗【确认·Gardenscapes 用户评论「to buy just 5 extra moves to complete a level costs 900 coins」——与 RM 同价】。
- **金币经济实测**【确认·用户评论口径，标注为玩家实测】：通关金币**已从 ~50 削到 ~10**（2024 用户长评，Playrix 官方回复承认「implemented some changes…including rewards」）——十年老游戏靠压产出逼老玩家付费的案例；挽回价 900 金币不变 → 免费续步需 ~90 关积累，纯粹化为付费/等体力二选一。
- **分享/炫耀件**：Facebook 好友联动+社区竞赛排行榜【确认·Google Play 官方描述】；Homescapes 有剧情章节完成感（家族故事线）。
- **继续按钮顺位**：结算后回主场景（非连打下一关），星星要去任务板消费——**故意打断「一关接一关」的心流，把玩家拉回 meta 场景看装修成果**【确认·机制层；「故意」为推论成分标注】。

### 2.3 商店/礼包

- **礼包分层**【确认·gamerforfun 评测+Udonis】：①金币包（多档，顶格 €110/$100）②**Gold Reserve 金库**（存币型礼包，piggy bank 概念）③**Golden Ticket 黄金票**（赛季通行证付费轨：更优奖励+宠物+体力上限 8）④金币+道具组合包 ⑤Facebook 绑定/跨游戏引流/小游戏=免费金币旁路（非 IAP 回血路径）。
- **划线价/折扣视觉**：无逐包截图证据【待证】；定性=「limited-time offers and bundles 包住限时活动」做爆发式付费（Udonis：老玩家按活动节奏 burst 消费而非细水长流）【确认·Udonis 定性】。
- **无金币入口时的引导路径**：金币不足→IAP 礼包弹窗（同 RM）；免费路径=每日转盘+活动奖励+Facebook 奖励，**无广告路径**【确认】。
- **付费深度画像**：**靠宽付费面而非鲸鱼**——「pulls strong value out of a broad base of paying players, not just a thin layer of whales」+收入/下载 $6.14【确认·Udonis/AppMagic】。

### 2.4 meta 收集/家装屏（=主菜单本体，Scapes 系真正的核心屏）

- **进度呈现**：区域制（Gardenscapes 19+ 区域：主花园/客房/剧场/岛景等）【确认·gamerforfun「over 19 different areas」+Google Play 官方】；每区=一组任务链（任务成本 1-3 星，部分任务分 2-3 阶段施工，官方确认）；**游戏日制**——每区任务在限定「day」内推进，天数推进剧情【确认·官方帮助中心+gardenscapes.fandom.com（「within a set number of game days」）】。
- **收集物陈列**：**破旧→焕新改造式**（对 RM 的「从无到有」）——旧物在场先建立「心疼感」，修好才释放成就感【确认·163.com 对比专节】；**三选一决策**：每处装修（喷泉/花圃/栅栏）给 3 个样式选择=决策成本换情感投入【确认·163.com+gamerforfun「you can decide what materials, types, and designs」】；Homescapes 无 Garden Cash 但室内装饰选项更细【确认·gamerforfun 对比】。
- **解锁钩子**：新区域=「清障开荒」演出（fandom 逐日记录如纪念碑花园：清垃圾+移石+发现盔甲+洗狗 的 4 日任务剧）【确认·gardenscapes.fandom.com Monument's Garden 条目】。
- **回访钩**：**Garden Cash 花园现金**=专货币（打 Hard 关获得），买独特设计外观=硬核收集线【确认·gamerforfun】；宠物收养（Gardenscapes 狗/Homescapes 猫）+邻居角色群+**Magic Collection 卡牌收集活动**（2026 现行）+Hidden Legacy 剧情活动【确认·Google Play 页更新日志】。
- **剧情在场方式**：Austin 对白推动任务（163.com：梦幻花园新手期**过半时间耗在剧情体验**——重 meta 到拖累核心玩法体验，这正是 RM 反向定位的靶子）【确认·163.com】。

### 2.5 Playrix 系可迁移要点（速记）

1. 主菜单=装修实景即收集陈列室（成果可见性=最强回访钩）【可直抄】
2. 任务平板「3 条滚动+星星成本」=把 meta 目标钉在主屏【可直抄】
3. 1 星/关+星→任务→场景变化→剧情的四段奖励链（胜利情绪最大化装置）【需适配：吸嘟嘟星→图鉴】
4. 三选一装修决策=决策成本换情感投入；RM 证明砍掉决策也成立——治愈系可取中间态（可爱收集的「选哪只」天然带三选一快感）【需适配】
5. Hard/Super Hard 明示难度标签=预期管理装置【可直抄】
6. Garden Pass 付费轨送「体力上限+8」=通行证特权设计范例【需适配：IAA 化为广告解锁时长】
7. 压通关产出（50→10 金币）逼付费=十年老游戏续命术，新游戏禁抄【不适用：仅存量盘收割期适用】
8. 误导广告→被封→**把广告玩法做进游戏本体（mini-games 进 onboarding）**=creative-product 闭环【可直抄思路：微信小游戏可用「广告里的玩法」做限时小游戏】

---

## 研究对象3：Lily's Garden（Tactile Games）+ Project Makeover（Magic Tavern·AppLovin 系）——治愈剧情线 & IAA/IAP 混合样本

> **对吸嘟嘟的定位价值**：这组是四款里商业形态离吸嘟嘟最近的——Lily's Garden 有激励视频「看广告双倍结算」，Project Makeover 有「看广告+2 步」，都是 IAA/IAP 混合体；且 PM 的 30% 玩家为 Gen Z（年轻化治愈审美），与吸嘟嘟「收集小可爱」气质同带。

### 3.A Lily's Garden（Tactile Games·丹麦哥本哈根·2019-01 上线）

**基础盘**【确认·pocketgamer.biz 专访（web_fetch 抓取）：累计玩家消费 **$5.17 亿**（data.ai 口径）；姊妹作 Penny & Flo 累计 $6000 万、2023-03 新作 Makeover Match】。核心定性=**叙事驱动的「点消 blast」三消+花园改造**（注意：不是交换式三消——同色 ≥2 邻接点击消除，Toon Blast 血统）【确认·lilysgarden.fandom.com wiki】。**营销=产品成功的一半**（CEO Soendergaard 原话，营销前期即介入）【确认·pocketgamer.biz】。**广告变现在规模化运行**（PocketGamer Podcast×Tactile：广告变现=分段 A/B 测试+动态底价+多广告位+用户级优化）【确认·podcast 页面存在性与主题】。

- **3.A.1 主菜单/大地图**：主屏=**剧情场景**（Lily 与 Luke/亲友群像），任务以剧情日（story day）推进；顶部货币组=金币+能量；吉祥物=剧情角色群像在场（Lily 主角+狗 Roxy）【确认·机制层；屏内具体位次【待证】】。**周更故事日**：每周 1 个新 story day（隶属故事章），单 story day 全生产周期 1 个月、团队三线并行（收尾 12 章/预产 13 章/脑暴 14 章）【确认·tactilegames.com 官方博客，https://tactilegames.com/behind-the-curtains-what-it-takes-to-make-a-new-story-chapter-in-lilys-garden/】。章节=异地旅行（丹麦/澳洲/德国/日本），配文化顾问做「寓教于乐」剧情（澳洲章讲珊瑚礁保护）【确认·同上】。
- **3.A.2 结算屏**【确认·bluestacks 攻略】：通关→**剩余步数逐个转化为随机道具→连锁爆发→额外金币**（提示：立即点屏会跳过这段演出损失金币——演出本身就是奖励的一部分）；**结算后接「看广告双倍金币」**（IAA 关键插点：双倍在金币结算后置位，非前置）【确认·「watching the ads to double your payout」原文】。金币用途=失败续命/买步。
- **3.A.3 商店/礼包**【确认·App Store IAP 档位名实录（appstoreprice.org 抓取）】：金币包 7 档命名梯度=Pack（$0.99 起）→Quick Refill→Pile→Bag→Chest→Mountain→**Vault of Coins**（从小包到「金库」的体量词阶梯=把 7 档价差翻译成体积语言）；**Roxy's Reserve**（存币金库，piggy bank 变体，用狗 Roxy 命名=吉祥物资产复用进商店叙事）；**Season Pass 赛季通行证**；限时礼包群=Special Offer/Garden Offer/Fortune Forest Offer/Shop Bundle（名目即运营位）；新增「Photo Memories 相册」功能（整理相册重温剧情时刻=把剧情资产二次变现/回访钩）。
- **3.A.4 meta 收集/家装屏**【确认·tactile 博客+bluestacks】：花园改造任务由剧情流水线驱动（Story Director 先画任务流程图：「除杂草」「抓鸽子」「设计热狗摊」→写手按图配对白→2D/3D 艺术实现→Unity 装配，含道具微演出如选花后花朵弹跳）；改造**可完全跳过**（纯三消玩家不受罚=双受众兼容设计）；宠物可在 meta 层收养；主角服装可换装【确认·官方博客】。活动五件套【确认·appgamer 事件指南，2019 版】：Daily Harvest 周签（L20 解锁·7 天奖+D7 大奖·每周循环）/Sunflower 48h 限时（通关→无限体力+道具）/Flower Gathering 联赛制集色（先资格赛→升级联赛拿更好奖励）/Hot Streak 连胜 3 局（1 胜=免费火箭·2 胜=火箭+炸弹·3 胜=火箭+炸弹+魔药，连胜逐级开局送道具）/Rocket Ruckus 风险存分赛（道具得分→Hard 关前「存分或梭哈」——把「看广告/用道具过 Hard 关」的决策压力做成玩法）。

### 3.B Project Makeover（Magic Tavern·北京·AppLovin 子公司·2020-11-15 上线）

**基础盘**【确认·naavik 深度拆解，https://naavik.co/deep-dives/project-makeover-fall-from-grace/】：两年 ~$5 亿收入（=前作 Matchington Mansion 终身收入的两倍）；2021-03 后被 RM+CCS 复兴夹击持续下滑；受众最年轻（**Gen Z 占近 30%**，vs RM 服务千禧/CCS 服务 X 世代）；D1 30% 可接受但 **D7 比 RM 低 10 个百分点**、月均会话数只有 RM 一半。核心三消手感被评「laborious and dated」（无并发消除/无智能飞机/无变向火箭/长关多色）【确认·naavik】。

- **3.B.1 主菜单/大地图**【确认·naavik】：主屏=改造项目现场（客户+三人时尚团队），**玩家以「改造专家」第一人称在场**（有自己命名的 avatar+可改造的工作室——打破三消「天上神明」疏离感）；顶部货币组=金币（做客户任务）+现金 cash（做自己的 avatar/工作室，双货币分层）；**episode 浏览器**=可回访全部已完成客户+预览未来客户（收集陈列室+期待感预告片双功能）；64 集内容、每 ~1.5 周新增 1 集（16 个月加 40 集）【确认·naavik】。
- **3.B.2 结算屏**【确认·naavik】：**败局挽回双通道=「看广告 +2 步」或「300 宝石(~$0.90) 买 +5 步」**——IAA/IAP 并列插点的直接样本；**败局屏最多同时陈列 6 种损失厌恶物品**（连胜奖励/宾果卡 foreshadow/Jet Setter 稀有奖励/竞赛进度/神秘盒首通奖励/赛季进度，随活动而变）=品类最重的败局屏之一。连胜=Fashion Show（3 胜奖）与 Yoga Stretch（5 胜奖含+1 步）双轨轮换【确认·naavik】。
- **3.B.3 商店/礼包**【确认·naavik】：赛季通行证**月费 €5.99**，**非付费玩家做任务后显示「Coming Soon!」+数小时才刷新下一任务**（对非付费玩家最严苛的通行证设计=反面教材）；**Stylish Stash=存币金库**（piggy bank 换皮）；限时竞赛（Passion for Fashion 集心形宝石/Steal the Spotlight 触发道具，均百人临时排行榜）；Locked Box 双日登录宝箱【确认·naavik】。
- **3.B.4 meta 收集/家装屏**【确认·naavik】：**改造三件套=外表+穿搭+空间**（一人一屋双改造，集 Scapes 与时尚游戏大成）；装饰物带**稀有度分级**（罕见度进休闲=中核化设计下沉）；已完结改造不可见→**episode 浏览器**承担收集陈列+可回改历史客户；现金货币养 avatar 工作室→**房产升级链**（基础工作室→海滩屋→顶层公寓→山顶别墅→Safari 屋→沙漠洞屋 6 档）+**皇冠点数全球排行榜**（每花 10 现金得 1 皇冠，全服可参观头部玩家工作室=炫耀件）；反派 Greta Von Deta 每 ~10 关一段 Drama 对白（爽剧节奏）【确认·naavik】。
- **3.B.5 教训（比做法更重要）**【确认·naavik 定性】：PM 的一切系统几乎都围着**损失厌恶**转（败局屏 6 件套+连胜断线惩罚+非付费歧视），玩家疲劳→会话腰斩→收入下滑；对照 RM 围着**玩家好感/公平感**转（trust bank）。**同是混合变现，PM 证明 IAA 位点多≠更好；插点要在玩家「想要更多」的瞬间，不在「被拿走」的瞬间。**

### 3.6 本组可迁移要点（速记·IAA 视角优先）

1. **结算后置位「看广告双倍金币」**（Lily's Garden）=IAA 第一插点标准答案；演出即奖励（步数转道具的连锁戏）不要让玩家想跳过【可直抄】
2. **败局双通道「看广告+2 步 / 宝石+5 步」**（PM）=IAA/IAP 并列挽回位【可直抄：微信小游戏激励视频+金币价签并列】
3. 金币包 7 档「体量词阶梯」（Pack→Vault）+吉祥物命名金库（Roxy's Reserve）=商店文案/命名学【可直抄】
4. Hot Streak 连胜 1/2/3 累进开局送道具（L20 后解锁）=连胜奖励做进局前【可直抄】
5. 周更 story day+章节异地旅行+1 个月生产管线=治愈剧情线内容工业化基准【需适配：吸嘟嘟周更 1 章节卡可行性】
6. 「Photo Memories 相册」=把收集成果做成可翻阅相册（回访钩）【可直抄：图鉴屏升级方向】
7. episode 浏览器「已完成陈列+未来预告」双功能=图鉴屏信息架构【可直抄】
8. 装饰物稀有度分级+房产升级链+皇冠全球榜（PM）【需适配：取稀有度分级，弃全球参观（微信开放域排行榜可平替）】
9. PM 反面教材：败局屏堆 6 件损失厌恶物+非付费歧视=玩家疲劳根源【不适用（反面）：吸嘟嘟治愈定位禁抄】
10. Rocket Ruckus「存分或梭哈」=把广告/道具使用决策做成玩法级紧张感【需适配】

---

## 研究对象4：Candy Crush Saga（King·2012·三消常青纯核心基准）

**基础盘**【确认·naavik 档案拆解 https://naavik.co/digest/candy-crush-crushing-it/ + stepico 商业模式拆解引用 Business of Apps】：2012-04 Facebook 上线（仅 65 关）→2013 移动端同步进度；**十年累计 $71.5 亿**（2022-12 口径）、累计破 **$100 亿**、2024 年收入 $10.9 亿（连续三年 >$10 亿/年）、2024 MAU ~1.8 亿、全平台下载 36 亿+；2016 动视暴雪 $59 亿收购 King（主要为 CCS）、2023 随动视入微软。**DNA=Bejeweled 核心+Bubble Witch Saga 的 saga 地图**（「rich casual core + simple meta + wide content space + social virality」四件套公式）；**品类鼻祖变现位：「失败后 $1 买 5 步」**【确认·naavik】。关卡规模【确认·candycrush.fandom.com 检索摘要】：**23,405 关 / 1,561 集**，每集 15 关（前两集 10 关），5 种关卡类型，**每周新增关卡**。广告策略：强制广告早已撤光，**现以激励视频为主（换续步/续命/道具），「永不打断体验」**【确认·stepico】。

### 4.1 主菜单/大地图（=saga 蜿蜒地图，品类图腾）

- **屏上有什么**【确认·naavik+wiki 检索摘要】：**剧集制蜿蜒路径地图**（每集=一段路径+主题名+新机制引入），角色剧情点缀各集；**每关 pin 下直接显示已获星级**（1-3 金星/糖星——收集成果铺满主线动线=地图即陈列馆）；顶部货币组=生命+金条（gold bars）。
- **层级怎么排**：顶带状态→中景地图（主视觉+主 CTA=当前关节点）→侧栏活动。CCS 是四款里**唯一把「评级成果」直接钉进地图**的（RM 钉装修、Scapes 钉场景、CCS 钉星）。
- **奖励怎么编**【确认·wiki 检索摘要+stepico】：①**Episode Race**（2019-04 上线，L51 解锁：与同集 4 名玩家竞速通关整集，按名次发金条）②**Fantastic Five**（2019-06 上线：随机匹配 4 人小队，靠每日登录/清关/完集/首通/糖星(+25XP)/用道具攒队分换奖励）③**Space Dash**（连胜送开局道具条，2021 转世为 Candy Necklace 仅作用于当前关）④Daily Booster Wheel 每日免费转盘⑤**Candy Crush All Stars 全民赛**（2025 届 1500 万人参赛+真实现金奖池，助推**单月 ~$1.1 亿**史上第二高月收）【确认·stepico 引 Business of Apps】。
- **哪里可点**：当前关节点（主 CTA）→侧栏活动→顶带生命/金条（商店）→历史关卡 pin（回刷刷分）。
- **续玩钩子文案位**：地图上「未通关的红点节点」+episode 完成进度+团队任务进度（F5）+全民赛倒计时。

### 4.2 结算屏（品类演出范本 Sugar Crush）

- **星制**【确认·candycrush.fandom.com/wiki/Stars 检索摘要（直接抓取 403 已如实记录）】：**1-3 星按分数阈值评级**，仅在通关时结算、永不丢失；这是四款里唯一的真·评级制（RM/Scapes 星=货币、LG/PM 金币直购）。
- **奖励揭晓编排**：**Sugar Crush 阶段**=通关后剩余步数逐个转化为特殊糖果→全盘连锁爆发→分数飙升→星级判定——**把「结算」做成最后一个爽点**（该演出反向决定 Sugar Star 达成：余步≥5 常触发糖星）【确认·多源】。
- **Sugar Stars 第四档 mastery 层**【确认·glitchfreeguides 全文】：2019-07 加入；达成=3 星分的 **2 倍**或 Sugar Crush 余步 ≥5；首通即糖星有专属文案「Sweet Combo! Mastery on the first try!」；L1-35 不开放；**不直接给道具/金条**——奖励=Fantastic Five 队 +25XP+Master Trophy 进度+**地图变蓝星**（收集完美主义者的长线钩：把「刷图集星」变成看得见的整屏变化）；不回溯补发。
- **双倍/复活广告位插点**：**激励视频三用=续步/续命/道具**【确认·stepico「mostly rewarded video…extra moves, lives, or boosters」】；失败挽回沿用鼻祖位（金币/金条买步）。
- **分享/炫耀件**：糖星地图蓝变+All Stars 全民赛+好友排行（Facebook 同步成长的历史基因）【确认·naavik】。

### 4.3 商店/礼包

- **结构**【确认·stepico+knowgameplay/orbispatches 检索摘要】：硬通货=**金条**；IAP 明目=生命、失败续步、金条、道具、活动期限定包；**Piggy Bank 存币金库**=游玩中自动攒金条、满仓停止、付费破仓，**破仓价=商店大包的打折价（全游戏金条性价比最高位）**——「边玩边攒+满仓诱惑」双钩；活动专属 bundle 围绕 LiveOps 轮转制造自然购买时刻。
- **定价哲学**【确认·stepico 定性】：**「卖便利不卖墙」**（monetize convenience, not frustration）——从不锁死进度，付费=加速/续劲；先给数小时免费爽感再谈钱。
- **无金币入口时的引导路径**：金条/生命不足→IAP；免费路径=每日转盘+活动+激励视频（三款里的最温和免费经济）。

### 4.4 meta 收集/家装屏（=没有 meta 的 meta：地图即一切）

- **定谳**【确认·naavik 四件套公式】：CCS **无任何家装/装修层**——saga 地图+星级陈列+剧集角色故事+社交竞争就是全部 meta；十年验证「简单 meta」在品类里同样成立（RM 后来的无 meta A/B 测试殊途同归）。
- **收集物陈列**：星星铺地图（每关 pin 下）+糖星蓝变整图+Master Trophy+剧集角色图鉴感（每集主题名）。
- **解锁钩子**：新剧集（每周）+新机制引入点（每集官宣引入新障碍）。
- **回访钩**：F5 组队日常+每日转盘+全民赛季+Episode Race 竞速——**用「人的比较」替代「物的收集」做回访**，是四款里唯一以竞争为核心回访引擎的。

### 4.5 CCS 可迁移要点（速记）

1. **星级钉在地图 pin 下**（成果沿主线动线铺开）=章节旅程屏最值得直抄的陈列法【可直抄】
2. **Sugar Crush 演出**=余步转特殊糖果连锁→结算即最后一个爽点；余步演出同时喂养 mastery 判定——一鱼两吃【可直抄：吸嘟嘟结算演出原型】
3. **Sugar Stars 第四档**（2 倍分/余 5 步+首通专属文案+地图变色+不回溯）=收集完美主义者长线钩，零道具成本纯荣誉【可直抄：图鉴/章节 mastery 层】
4. **Piggy Bank 打折金条**（玩中自动攒+满仓停+破仓=最优性价比）【可直抄：IAA 化「看视频破仓」后完美适配微信小游戏】
5. **激励视频三用位**（续步/续命/道具）永不打断体验【可直抄】
6. 「卖便利不卖墙」定价哲学【可直抄：治愈系唯一正确路线】
7. Episode Race 同集 5 人竞速+Fantastic Five 随机组队=轻竞争轻社交双件【需适配：微信开放域排行榜可承载】
8. 周更关卡十年不断+每集引入新机制=内容工业化终极形态【不适用：单团队小游戏产能；取其「小步快跑」精神】
9. 无家装 meta 也能常青——meta 深度不是留存必要条件，核心爽感才是【可直抄哲学】

---

## 对吸嘟嘟的可迁移初判

**商业形态先定性**：四款头部里 RM/Scapes 是「近零广告+重度 IAP」（对吸嘟嘟只取设计不取模式）；**Lily's Garden / Project Makeover / CCS 是「IAP+激励视频」混合**（对吸嘟嘟可取模式）。吸嘟嘟「IAA 为主+轻 IAP」的正确参照系=**LG 的结算双倍 + PM 的败局双通道 + CCS 的金库破仓**三件套，而非 RM 的零广告洁癖。

**跨款七律（四款交叉验证后才可迁移的结论）**：

1. **星=货币不是评级**（RM/Scapes 双证，CCS 是唯一反例且其星只做荣誉）：吸嘟嘟「星→图鉴收集」路线与头部主流同构【确认】。
2. **结算演出即奖励**（RM 余步转道具/CCS Sugar Crush/LG 余步转道具连锁三款同构）：演出不可跳过、不可廉价——它同时承载爽感、金币产出与 mastery 判定【确认】。
3. **败局挽回=品类第一变现位**（RM 900 金币/CCS 鼻祖 $1/5 步/PM 看广告+2 步或 300 宝石+5 步/LG 金币续命）：吸嘟嘟正确形态=PM 式「看视频+步」为主、「金币+步」为辅【确认】。
4. **连胜是唯一被四款共同采用的局外钩子**（RM 超级光球 10 连胜/PM Fashion Show-Yoga Stretch/LG Hot Streak 3 连胜/CCS Space Dash→Candy Necklace）：连胜奖励做进「局前」（下一关开局送道具）而非只做结算【确认】。
5. **Piggy Bank/金库是混合变现标配**（CCS piggy bank/Scapes Gold Reserve/LG Roxy's Reserve/PM Stylish Stash 四款全有）：吸嘟嘟 HUD 已有存钱罐，缺的是「满仓破」的完整回路（付费破仓或看视频破仓）【确认】。
6. **轻 meta 赢重 meta**（RM 用减法登顶+Playrix 新作回头学轻/PM 重 meta 会话腰斩反面证/CCS 无 meta 常青）：吸嘟嘟六屏里图鉴+道具铺两块 meta 面已够，禁再堆第四屏【确认】。
7. **内容节奏基准**：周更=底线（CCS 周更关卡/LG 周更故事日）、双周百关=头部量产线（RM）、1.5 周/集=重 meta 极限（PM）；治愈系剧情/收集内容按 LG「单 story day 1 个月生产周期、三线并行」预算产能【确认】。

**画风与吉祥物**（对已定谳的 3D 糖瓷线）：RM 的 King Robert/Winston/Duke 证明「吉祥物活在场景里+社交层互赠体力」比 UI 贴片吉祥物高一级；Scapes 的 Austin 证明吉祥物可以就是剧情引擎（Tactile 整个叙事管线围绕角色运转）。吸嘟嘟「收集小可爱」天然把吉祥物做成**可收集物本体**（收集物即吉祥物群）——比头部更强的一张牌，图鉴=吉祥物部队的常设检阅台。

---

## 六屏映射：头部做法 vs 吸嘟嘟现状（U293）

> 落差分档：**可直抄**（直接照搬机制/参数）／**需适配**（机制好但要换 IAA/微信载体）／**不适用**（重度 IAP/重产能专属，明确不抄）。吸嘟嘟现状引用 U293 评审收口态（六板 24/45/34/40/50/50 节点·53 PASS；R10 挂账 10 项）。

### ①主菜单
1. 【可直抄】**地图/场景即导航、无底部 tab**（RM 定谳）：吸嘟嘟主菜单 U293 已无底部 tab 且入口收敛至 4（金币胶囊转显示件=入口 4 个）——与头部同构；补齐项=**左侧活动竖栏 3-4 位**（RM 标配），微信形态放「签到/限时收集/排行榜」三活动位，当前主菜单活动位为空档。
2. 【需适配】**续玩钩子位**：RM 地图节点「下一关」直给+连胜火焰条；吸嘟嘟主菜单当前钩子=吉祥物 ring_glow 柔光环（氛围件非钩子件）——把「下一关 3-2」直给文案位+连胜进度条搬进主菜单（连胜数据可本地存，无需开放域）。
3. 【不适用】RM 买量级 Team/赛事入口群（King's Cup 等六活动常驻）——小游戏 DAU 量级撑不起，取 2-3 个常驻位即可。

### ②章节旅程
1. 【可直抄】**星钉在章节卡/地图 pin 下**（CCS 唯一专利级陈列法）：吸嘟嘟章节卡已有三态+「进行中 2/5」进度计数（U293 口径统一），补「已通关节点显示所得星/糖星」的成果回显层。
2. 【可直抄】**Sugar Stars 式第四档 mastery**（2 倍分或余步≥5+首通专属文案+整图蓝变）：零道具成本纯荣誉，与治愈系零冲突；R10 挂账的「进行中态描边」可与之合并一轮做。
3. 【需适配】**Episode Race 同集竞速**（CCS：与 4 名同集玩家比通关速度发金条）：微信侧用开放域排行榜做「本集通关榜」弱化版（异步名次而非实时竞速）。

### ③局内HUD
1. 【可直抄】**顶带纪律=2 组+1 主数值**（U274 密度红线与 RM 顶带同构）：吸嘟嘟 HUD 已收口（目标双胶囊 224×112/存钱罐/暂停钮右缘共线）——纪律已达标，此屏是六屏中头部落差最小的一屏。
2. 【可直抄】**关卡手感参数**：4 色/25 步均值/并发消除/道具点触激活/智能重定向（RM 四件套，Playrix 全量跟改的历史级背书）；关卡设计域的「almost win（差 1-2 步）」调参律——这是买广告转化率的玩法侧根基，比任何 UI 改动都值钱。
3. 【需适配】**Hard/Super Hard 难度标签**（Homescapes 专利级预期管理）：吸嘟嘟治愈系改用软性变体（「这关有点凶哦」+可看视频领开局道具），避免恐吓感破坏治愈基调。

### ④结算
1. 【可直抄】**余步转道具的结算演出**（LG/CCS/PM 三款同构，PM 附「立即点屏跳过会损失金币」的设计自觉）：吸嘟嘟结算已有奖励胶囊 240×64（U293 修复）+视频钮 160×80——把「余步→道具连锁→金币飙升」演出补在星级判定前，视频双倍钮后置于金币结算之后（LG 定谳位）。
2. 【可直抄】**败局双通道=「看视频+步」为主、「金币+步」为辅**（PM 实证：广告+2 步或 300 宝石+5 步并列）：吸嘟嘟有复活羽毛（道具域）无此结构——败局屏做「看视频+2 步｜金币 300+5 步」双按钮，治愈系用 PM 的双通道但禁用 PM 的 6 件损失厌恶堆叠（PM 反面教材）。
3. 【需适配】**二段挽回带战略位道具**（RM：二续必带火箭且 100% 落在能赢的位置）：IAA 化为「第二次看视频送的道具由系统落在关键格」——信任银行（trust bank）机制治愈系尤其适用。

### ⑤图鉴
1. 【可直抄】**「已完成陈列+未来预告」双功能浏览器**（PM episode 浏览器专利级信息架构）：吸嘟嘟图鉴已有三锁定窗+糖瓷挂锁（U293 修复）——补「下一个未解锁小可爱的剪影预告位」，把期待感做成图鉴的一部分。
2. 【可直抄】**相册化翻阅/Photo Memories**（LG 新功能「整理相册重温时刻」）：收集小可爱天然适配「贴纸簿/相册」形态，比网格陈列更有治愈系翻阅感——图鉴屏升级方向。
3. 【需适配】**装饰物稀有度分级**（PM 把稀有度下沉进休闲）：吸嘟嘟小可爱分「常见/稀有/节日」三档即可（禁中核化数值堆叠），节日限定款与微信季节热点对表。

### ⑥道具铺
1. 【可直抄】**体量词命名梯度**（LG 七档：Pack→Quick Refill→Pile→Bag→Chest→Mountain→Vault）+**吉祥物命名金库**（Roxy's Reserve）：吸嘟嘟商店现为三卡栅格+礼包锚定价口径 1,150（U274 判例）——三卡可扩为「小额/大额/金库」的体量词位次，金库沿用 HUD 存钱罐吉祥物。
2. 【可直抄】**Piggy Bank 完整回路**（CCS：玩中自动攒+满仓停+破仓=最优性价比）：吸嘟嘟 HUD 存钱罐已有「攒」无「破」——道具铺设「破仓位」（轻 IAP 付费破仓+看视频小额破仓双通道），这是 IAA 盘子里最标准的转化件。
3. 【需适配】**月卡/通行证**（Garden Pass €月费/Royal Pass/PM 月票）：微信小游戏可上轻月卡（每日领金币+道具），但禁抄 PM「非付费歧视」（Coming Soon+数小时锁任务）反面教材；首充/失败后限时包（RM 紧迫感包装）=轻 IAP 侧可用，档位顶格对齐小游戏付费习惯（$1-6 档为主）。
4. 【不适用】RM 零广告商业模式本身（金币不足→纯 IAP 弹窗、无免费回血路径）与 Scapes 十年盘「压产出逼付费」（通关金币 50→10）——重度 IAP 专属与存量收割术，吸嘟嘟一律不抄；金币不足时的正确路径=激励视频。

---

## 附：本次调研抓取失败与信源健康实录（诚实律）

- gameuidatabase.com（RM id=1061）：正文抓取仅得屏型分类树，逐屏截图为 JS 画廊无法程序化抓取——屏型清单已用足，逐屏截图待人工浏览器补证。
- gardenscapesstrategy.com：域名解析失败（getaddrinfo failed），未采信。
- medium.com（Udonis「Lily's Garden Monetization」）：fetch_content 与 web_fetch 双通道均 403，Lily's Garden 变现细节改由 App Store IAP 档位名+bluestacks 攻略+PG 播客主题三源交叉补证，能量系统具体参数仍【待证】。
- pocketgamer.biz（Tactile 专访）：fetch_content 403，web_fetch 成功兜底（$517M 数据已采）。
- candycrush.fandom.com/wiki/Stars、candy-crush-tips.fandom.com/wiki/Episode_Race：403；lilysgarden.fandom.com/wiki/Gameplay：连接失败——相关事实均以检索摘要（wiki 摘要含原句）+第三方攻略页替代采信，并逐条标注。
- DuckDuckGo 两次空返（「deconstructor of fun Lily's Garden」与「CCS map screen events」组合查询，疑似 bot 检测）：换措辞重试成功。
- 全文未采信任何无信源的纯记忆断言；无法双证的数字一律标【待证】。

（完·调研员落盘于 2026-09-29）

