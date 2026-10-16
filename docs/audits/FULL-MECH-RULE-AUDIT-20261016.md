# 全机制·全规则总审视（普查F）·2026-10-16

> 令源：CEO 2026-10-16 13:5x「所有机制和规则，全部审视一遍」。
> 执行标准：部署=点火律（C-02 Cure-9）——每条结论带实弹证据行；查不到证据的明确标 ⬜纸面/待证，禁假绿。
> 方法：任务库全量异常筛（113 项非微软任务）+ 载波链实弹核 + 机队远端 /health+/status + 双后台代理并行盘点（规则正典面/工具引用网）+ 本窗现场深查定谳。
> 诚实分级：✓=实弹在案 · 🟡=有载体未实弹 · ⬜=纸面无机制 · 待证=存疑待查。

## 一、机制面总账

### 1.1 任务库全量筛（113 项·2026-10-16 14:0x 扫）

**基数**：82 Ready / 27 Disabled / 4 Running。隐藏链覆盖=自建任务除 1 项死件外全绿（pythonw.exe 直跑 2 项天生静默 ✓；wscript+SilentShimRunner 无引号形式 4 项=本窗检测器假阳性·勘正 ✓；vbs 自载体 2 项 ✓）。

**断链死任务（脚本路径不存在·清理候选候裁）**：
| 任务 | 指向 | 状态 |
|---|---|---|
| GimmeAll-AutoSentinel | gaming\MiniGame\09_吸嘟嘟GimmeAll\...\auto_round.ps1（不存在） | Disabled 自 09-28 |
| MoneyAutoGuardian | C:\Users\sjs20\Desktop\Money\tools\watchdog.ps1（**旧基地根·迁移残留**） | Disabled 自 09-22 |

**无隐藏链自建件（唯一真件）**：HQ-C10-Pilot2（cmd 直跑·10-08 试点遗留·Disabled）——死件候裁。

**BAD-RC 定谳（14 项中自建 10 项）**：
| 任务 | rc | 定谳 |
|---|---|---|
| HQ-bm-a-Sentinel | 1（14:05 当拍） | **语义告警非故障**——BM 子仓哨兵对 BM 栈黑灯/队列态如实报错；BM 心跳面 a.json 13:58/14:07 仍在写=车道活 |
| bm-a-ModelWhitelistProbe | 1（13:37） | 探针职责面（检出白名单外即 rc1）·待证其输出面 |
| BigCompute-CleanWindowProbe / OSLoop / ResidentQA / OrderSentinel / GPU-IdleWatch / OSLoop-PM / CoderServe / KeepWarm / OllamaServe | 3/… | **AutoYield 日间停用族**（今日 08:4x-08:59 WorkStart pauseLite 执行实证 ✓·19:00 WorkEnd 恢复）——停用边界拍即末拍 rc，设计内 |
| Bigmoney-ResidentDispatcher | 1073807364 | 10-15 14:43 起停用族（BM 车道另案） |
| MiniGameCeoDeskServer | 2147946720（14:07 每分钟失败中） | **域内待判**——转 MiniGame 域轮跟进（疑似端口占用/依赖挂） |
| MiniGameDailyDigest | 2（11:07） | 域内待判（疑空档语义码） |
| CarGZH_Erchuang / GimmeAll / PopupWitness | 1/4294770688/4294967295 | 尸体产线族（09-2x 停·见下） |

**本窗自纠假阳性 2 处（验证器自身 bug·当场勘正）**：
1. 「3 轮子停摆 5 天」误判——MiniGameHousekeeping/MiniGameRadarDeepTick/FluxGroup-EvolutionTick 实为 **weekly 触发器**（下一槽 10-18），周轮非死件 ✓。
2. 隐藏链检测正则漏匹配 SilentShimRunner 无引号形式——4 项误报勘正 ✓。

**尸体产线清单（退役候裁·占册不动人）**：CarGZH×8（09-19/20 全停）、MoneyAutoGuardian、GimmeAll-AutoSentinel、HQ-C10-Pilot2、MiniGameBoardForge/PopupWitness（09-2x 停）。

### 1.2 载波链实弹验证（本窗逐件点火/读回执）

| 载波 | 证据行 | 级 |
|---|---|---|
| DeliveryWatch 交付哨 | watch.log 14:01:21 **DELIVERED jayredo-r1034-6i2v hit=6**（PENDING→DELIVERED→done 落盘全闭环）+13:51:47 OVERDUE-POKE drama→bm-b ok=3/3 | ✓ |
| ShiftSupervisor 班哨 | 13:32:23 点火 rc=0·下班 15:43·首班 12:45-12:56 产物两笔提交在链（exit=254=退出码语义坑·看产物不看码） | ✓ |
| FleetLink 数据面 | bm-b/bm-c /health **version=1.7**（自升级腿闭环=上窗遗留项收口）+last_pull 13:51/13:45 origin_main=c1f86e8 与本地一致 | ✓ |
| dispatcher | 13:26 逗号拆分 deny-probe 三机全绿+13:35/13:51 ok=3/3 | ✓ |
| AutoYield 让路面 | WorkStart 今日 09:00 执行（BigCompute 族 08:4x-08:59 停用实证）；WorkEnd 维持 Disabled=口令制 O-20261015-1845 正态 | ✓ |
| cron 商店 | repo .codely-cli\scheduled_tasks.json 5 件在册（R1.8/R1.9 探针+21:43/23:43 桥+14:33 装配班）·无 .gamewin-bak 挂起态 | ✓ |
| MV V4 装配班 | 14:33 自续班在册（cron_list 核验）·原料 6/6 已齐（14:01 DELIVERED） | ✓ |
| git hooks / 平台 hooks | bm-a 总控仓 core.hooksPath 空+.git\hooks 无实体+.codely-cli\settings.json 无 hooks 字段 | ⬜ |

### 1.3 头号纸面机制定谳：OrderSentinel（秒级令分发哨兵）

- 设计令 **O-20260909-2336**（v1.3：双格式行+双台账扫描+集游标+Disabled 冻结+dispatch 钩传 Tasks·判据回访 10-16）在册。
- 工具件在盘：`Tools\order-sentinel.ps1`（8.7KB·10-10 12:37 版）+ `Tools\order-sentinel-map.json`。
- **实况：无任务调用·无钩挂载·零日志零 state 文件（`*ordersentinel*` 扫描零命中）=设计 6 天从未在役**。
- 加重情节：`cph4\registry\orders.jsonl` 本地未提交改动把 O-20260909-2336 令行**删了一行**（工作树 diff 实证）——正身令在机器台账上被抹。
- 虚构宣称面：fleet-dispatch.ps1 头注释「Called by ... the OrderSentinel hook」——注释级虚构（hook 不存在）。
- 实害：秒级令分发自动面=0，本窗 13:35 上链 push 后**无任何自动 poke**（dispatch-log 13-14 点 5 条全为人工/哨兵件）——CEO 令至今全靠 10min 轮询+人工 poke 兜底。
- **判**：P0 级「立法≠机制」头号案；修复路径已明（v1.3 脚本在盘只需挂载：S4U/静默任务每 N 分一拍或 push 后触发）——候 Cure-10 立项。

### 1.4 机队远端与悬案

- bm-b/bm-c /health 双绿 v1.7 ✓；bm-b **PROBE_ERR 悬案仍开**（哨兵 01:1x 起·另案候查）；drama 试映片欠交 2h+（交付哨每小时自动点名在跑·死线已过如实报）。
- 14:12 装配班 cron 蒸发案：已重挂 14:33+注册核验 ✓；历史根因不可溯（无日志面）——会话件承载生产职责的结构病已在 Cure-9 记档。

## 二、规则面总账（66 行规则·全量表=附录A）

**命中率**：约 35/66 行有实执法载体（工具/哨兵/任务名实相符）；约 22 行纸面或半机制（靠 prompt/查表/抽审承载）；9 行处废止/被替代/漂移态。登记簿自身健康（法熵账本净负管理 ✓·季度瘦身日在册），但见下病灶。

**Top 病灶（与机制面实况交叉验证）**：
1. **OrderSentinel**（正典宣称 2min 哨兵·RULES.md §7/CHARTER；工具件在盘 8.7KB；设计令 O-20260909-2336 在册且今晨令行被本地误删·已保护性恢复）——实况 **6 天从未在役**（§1.3）。判 Cure-10 立项。
2. **S4U 律**（09-29 判例·17 天）：登记器昨才焊（Cure-9）·bm-a 存量 ~106 件未转（§1.1）。
3. **远端 branch protection**：CEO 物理件挂账 23 天未落——禁 force-push 至今纯纪律无远端机核。
4. **L1 小脑消费率**：~0.2% vs ≥20% 目标（止损线 10-28）——l1-client.py 建了没人用。
5. **孤儿法 6-8 件**（law-registry 查无登记行）：release-gate / audit-office / autonomy-target / local-llm-pipeline / knowledge-registry / global-benchmarks / CODELY-fleet-global 边界候选。
6. **否决窗残留**：废止已勘 6 处·memory.md/versioning/token-economy 头部散布残留待清。
7. **矛盾对 10 组**（附录A C 清单）：最要害=S4U 律 vs BigMoney 域 D-20261002-02 缺省 principal 政策（两案都自证·悬置待同窗收口）+云端默认态三层叠写+外审班频三口径（AI.md「日三班」漏勘）。
8. **PROMPT-EXPERT-GATE 指针悬空**：PLAYBOOK/CODELY.md L1 写相对路径·实位在 mv0001-handover/outbound/krea2/ 下（CODELY.md 侧受 L1 写入通道阻塞无法修·见 §三.8）。
9. **催办闭环**：orders 尾部 15+ 条 open 挂账（附录A E 清单）·超时哨只挂在分叉案未普挂——P-2026-09-29-13 逾期 17 天靠 CEO 令才催=样本实害。

**工具面（附录B·88 件）**：无真死件级断链；核心 6 提示词件→脚本引用快检 **0 缺失**（余 24 件抽检未全·待证）；「任务面候选」25 件经主会话 113 任务实况交叉核对——**order-sentinel 唯一未挂载**（余 24 件均有对应任务/载体 ✓）；sli-reconcile 双件根路径硬编码 C:\Fluxgroup\FluxGroup（=bm-b 部署位·bm-a 册上件不可移植=移植陷阱）；降级留证件 3（chunk_vote_gate.py 等）勿用于生产判定；InvisibleRunner/SilentShimRunner 双静默器=分层设计非重复（后者给 codely/git 子进程静默）。

## 三、当场抓获+当场修（本窗）

| # | 抓获 | 处置+证据 |
|---|---|---|
| 1 | OrderSentinel 六天纸面在册（§1.3） | 定谳入卷·候 Cure-10 |
| 2 | orders.jsonl 令行被本地删除（O-20260909-2336） | 入卷·恢复候裁（先勘正入档·防误提交删行） |
| 3 | 2 断链死任务+1 无链死件+尸体产线 13 项 | 清单入卷候裁（退役=决策不擅动） |
| 4 | 2 处自检器假阳性（周轮误判+正则漏匹配） | 当场勘正 ✓（§1.1） |
| 5 | jayredo 6 件压哨交付 | 无需处置——交付哨闭环实证（§1.2） |
| 6 | orders.jsonl 令行被本地误删（O-20260909-2336·OrderSentinel 正身令） | **已保护性恢复**（git checkout·尾行读回实证 11:48 事故窗） |
| 7 | 核心 6 提示词件→脚本引用断链快检 | 实测 **0 缺失**（余 24 件抽检未全·标待证） |
| 8 | L1 写入通道双路阻塞（append 工具 EEXIST+replace 工具拒改 CODELY.md·本窗双实测） | 如实入卷——bm-a 侧 L1 事实上冻结·新内容只能走 git 正典（案卷/orders）；平台故障待报 |

## 四、待 CEO/委员会裁决清单（10 项）

1. **OrderSentinel 挂载（Cure-10·P0）**——正典宣称 2min 哨兵 vs 实况 6 天未在役；脚本在盘只差挂载（task-register every:2m 即可）。
2. **尸体任务退役批（13 项）**——法熵守恒的机器面（含 2 断链死任务+1 裸链死件+CarGZH 8 项老产线）。
3. **bm-a 存量 ~106 项 S4U 大手术**——需提权窗+委员会量裁；同窗收口 BigMoney 域 D-20261002-02 政策冲突。
4. **远端 branch protection**——CEO 物理件 23 天挂账（禁 force-push 远端机核缺位·G12 提案在库）。
5. **L1 小脑消费率止损**——10-28 线·现 ~0.2% vs ≥20% 目标。
6. **孤儿法 6-8 件+否决窗残留+外审班频三口径（AI.md 漏勘行）**——随 10-19 季度瘦身日收口。
7. **PROMPT-EXPERT-GATE 指针悬空修复**——PLAYBOOK 侧可修·CODELY.md L1 侧被写入通道阻塞。
8. **CeoDeskServer 每分钟失败+DailyDigest rc2**——MiniGame 域内待判移交。
9. **orders 尾部 15+ open 挂账催办闭环**——超时哨普挂（现只挂分叉案）。
10. **sli-reconcile 根路径硬编码（bm-b 件不可移植）+fleet-mechanism-audit.ps1 引用者待证**。

## 五、结论

机制面：核心载波 8 件全绿带证据（交付哨/班哨/数据面/调度器/让路面/cron 商店/装配班/机队远端）；病灶集中在「**登记在册但已死**」家族——纸面哨兵 OrderSentinel 一只、断链死任务 2、尸体产线 13、存量 S4U 106——全部与 C-02 病根「立法≠机制」同源同症。规则面：66 行法约 53% 有实载体、33% 纸面、14% 废止/漂移；登记簿自身健康（法熵净负+瘦身日机制在册），欠账在孤儿法 6-8 件+矛盾对 10 组+指针断链 2 处。

**总判**：集团的病不在「没有规则」，在「规则与机器两张皮」。缝合线已经焊上——部署=点火律（Cure-9）从今天起强制：凡新立法必须同时带「挂载点+点火证据」才准宣称在役；凡存量大扫除（S4U/尸体任务/孤儿法）按 10-19 季度瘦身日批裁决节奏走。本报告+附录A/B 为普查F 全档，待裁 10 项已列。
