# R-20260928-td-gungeon-throne — 顶视光效打击感：Gungeon+Nuclear Throne（CEO 令 P-2026-09-28-10·案例解剖波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse 事件动效质感升级线+CEO 决策面·判据预注册=①顶视 2D 事件动效「高级感」=哪些光效/粒子/反馈手法？②参数（数量/亮度/时长/幅度）公开披露面=多少？③哪些可直移植 Tuanjie 1.10.3 URP 2D+30° 俯角日漫 cel 锚？
> 验证声明：尝试 18 读·成功 13（Gungeon 9/NT 9·双域封顶）·成源 9 条（A=3/B=2/C=4）·M 级断言均显式标注
> 失败面：dodge-roll.com 连接失败·Gungeon fandom 403·Wikipedia×2 直取返回非维基内容（NT 侧意外得 PlayStation Blog·Rami 一手文·采用）·thatguyglen JS 墙（仅 DDG 摘要片段·C）·末次 DDG 反爬拦截·『extensive list of game feel tricks』精确短语零命中=记忆线索证伪不采信

## 一、逐游戏六维要点
**Enter the Gungeon**（Dodge Roll·Devolver·2016-04-05·Steam A；前 EA/Mythic 员工组队·设计师 Dave Crooks·htxt 采访 B）
- ①俯视弹幕地牢（A："bullet hell dungeon crawler"；核心动词="shoot, loot, dodge roll and table-flip"·A）；俯视角/引擎 Unity=常识级未获直读源（M）
- ②结构=房间/楼层序列（A："a challenging and evolving series of floors"）→ 对城市 demo 仅「事件发生于离散空间单元」一条可映射
- ③地形施工披露=0 源（待证）
- ④光效/粒子/色彩实现书面披露=0（官网死·fandom 403·深度文不可达）→ 待证；主维判负见应用表
- ⑤动效绑定=玩法即动词清单（A）→ 行为-反馈强绑定的文案级确认；弹壳/火光/爆炸表现=常识级（M）
- ⑥可抄点 G1-G3（见三）
**Nuclear Throne**（Vlambeer·PC/Mac/Linux/PS4/Vita·官方站 A；2025-12-05 十周年 Update #100 仍在更·A）
- ①顶视俯角（B：Rami"fast-paced, top-down action"）；12 角色/7 世界/120+ 武器/近 30 变异（A）
- ②世界轮换 deserts→frozen cities→underground labs（A）→ 城市仅背景板；Twitch 直播开发「Performative Development」周更（A）→ 动效经公开打磨可考
- ③团队 6 人×2.5 年（B）；美术 Paul Veer+Justin Chan·音频 Jukio Kallio+Joonas Turner（A）
- ④光照书面披露=0（待证）；调色板随世界变化=由世界主题推测（推测）；引擎 GameMaker=常识 M
- ⑤juice 正典=《The Art of Screenshake》JW Nijman·INDIGO Classes 2013·45min·YouTube AJdEqssNZ-U（C 双源）；内容=「从故意无聊的 platform shooter 现场叠加 30 个微小改动直至手感质变」（C 双源：gamedesign.gg+Reddit 帖）；技法与视角正交（推测）→ 顶视城可移植
- ⑥可抄点 N1-N5（见三）

## 二、juice 手法清单（逐条带出处）
- 《Screenshake》已披露技法名（C·gamedesign.gg）：bigger bullets／muzzle flash／hitstop／camera kick；30 项全目=待证（正典视频 JS 墙不可直读·Reddit 称 tricks 清单在 7:53 处·C）
- 通用七件套（C·freegamesprites·明注源自 JW 2013 演讲）：hitstop·hit flash·knockback·screen shake·particles·sound layering·anticipation；「叠 4 层即胜 90% 同行」（C）
- 参数披露面（C 级"Numbers that ship"·freegamesprites）：hitstop 通用 4-8 帧；轻武器 2-3f／中 4-6f／重 6-10f@60fps；双冻结律（攻受同冻，冻单方=劣化）；Hyper Light Drifter 冲刺接触≈4f；screenshake 配额制（reserve shake for moments that earn it·每击必震 3 分钟即失效）；光效亮度/粒子数/震幅=零披露（待证）
- 原版 demo 社区镜像 colinbellino.com/public/stuff/screenshake-controlconf.zip（C）；关联正典《Juice It or Lose It》Nordic Game Indie Night 2012（C·gamedesign.gg 著录）

## 三、可抄点清单（怎么抄+cel 锚适配度）
- N1 顿帧分级：事件按权重停时（建议起点：微事件 2-3f／脉冲 4-6f／大 commit 6-8f·非披露值），Time.timeScale≈0 双冻结→适配=优（日漫 impact frame 同构）
- N2 反馈堆叠：每事件≥4 层（闪白 1-2f+粒子迸发+顿帧+微震+音效），Vlambeer 30 叠法压成 5-7 层事件包→适配=优
- N3 震感配额：只给 commit/令/claim 三类震，微行为只闪不震（C 纪律）→适配=优
- N4 光点放大律（bigger bullets·C）：过江光点显著大于环境粒子+短尾迹 3-5f（建议值）→适配=良（cel 硬边光点·禁糊光晕）
- N5 出动微粒子：claim=尘土 3-5 粒+前冲 2-3f（建议值；Gungeon 弹壳同构·M 推断）→适配=良
- G1 动词绑定：事件动效包按动词命名（过江/脉冲/出动），一动词一专属反馈包（A 文案同构）→适配=优
- G2 行为-动效一一映射：可执行行为必有伴随反馈（A 文案级+M 视觉级）→「禁装饰动画」的反向同律→适配=优
- G3 战利品收束：大事件收尾给落点反馈（loot 式落下+光圈·A 确认 loot 存在+表现=推断）→适配=良

## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 30 叠法+七件套反馈堆叠 | 任务单：FluxVerse 三事件各配 5-7 层反馈包 | 接线中 |
| hitstop 分级表（C 级参数起点·双冻结律） | 任务单：demo 事件动效标定起点（标注非官方值） | 接线中 |
| screenshake 配额制 | 法文修改：FluxVerse 动效纪律补「震感配额」条 | 提案中 |
| 亮度/粒子数/震幅公开零披露 | 决策呈报：参数转 demo 内自标定·外采线终止 | 已闭环 |
| Gungeon 光效书面源=0（官网死/403/JS 墙） | 判负留痕：Gungeon 参数级采集判负·防重复调研 | 已闭环 |

- 更新记录：T0 骨架落盘→T1 NT 域+正典入账（14 读）→T2 双域终采（18 读·Gungeon 9/NT 9 封顶）→终稿 48 行
- 防线二：（留空待主会话抽验）
