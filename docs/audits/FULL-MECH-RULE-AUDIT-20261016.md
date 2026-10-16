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

### 1.3 【勘误 14:3x·原 P0 定谳撤回】OrderSentinel 实况=**在役双活**；原「6 天从未在役」系本审计自身检测器假阴性

- **勘误前错误宣称**（14:0x 版）：「无任务调用·无钩挂载·零日志零 state=从未在役」。
- **真相（14:32 复核实证）**：任务 `FluxGroup-OrderSentinel` 在役——PT2M 节奏（P3650D 窗）·**最新一拍 14:32:51 result=0**·每日心跳日志（10-13→10-16 四天连跳）·**今日 12:42:52 真唤醒 MiniGameEngineTick:WAKE**·dispatch-log 全史 **20 条 reason=order-sentinel 三机直推记录**（含 9029f15a 批）——本地唤醒腿+远端分发腿双活。
- **本审计检测器两处假阴性根因（自我追溯）**：①日志搜索用文件名通配 `*ordersentinel*`——而哨兵真实日志=log.txt/state.json 在 `.codely-cli\sentinel\`（路径明明写在后来读到的脚本头里——先搜后读、未交叉核对）；②任务面宣称「无此任务」——而 106 项清单里 FluxGroup-OrderSentinel 明明在列（命名盲区：找「OrderSentinel」没认出「FluxGroup-」前缀载体）。
- **判**：①OrderSentinel ✓ 在役——**O-20260909-2336 的 10-16 回访判据（哨兵活性+跨机唤醒）由本次复核正式闭环**；②14:0x 版「Cure-10 挂载立项」撤回；③勘误入坑录：**审计的否定性宣称与机制的肯定性宣称同受部署=点火律约束——宣称「零日志」前必先读载体脚本自带的路径定义再搜盘**；④O-2336 令行被本地误删案独立成立（11:48 工作树回退族·已恢复·见 §六）。
- 遗留真缺口（小·by design）：orders.md 行不带 @机标签时不路由唤醒——本窗 13:3x/14:4x 两行未带标签故无自动直推（人工 poke 兜底合规）；后续 CEO 令行按 O-2336 map v2 惯例带 @bm-x 标签即获自动直推。

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
| 9 | 【勘误】OrderSentinel「从未在役」= 本审计检测器假阴性（文件名通配搜错路径+前缀命名盲区） | **14:32 复核撤回原判**——哨兵双活实证（心跳四天连跳+今日真唤醒+20 条远端直推史）+O-2336 回访判据闭环（§1.3 勘误版）；坑录=否定性宣称必先读载体自带路径定义 |
| 10 | 11 件断链死任务（CarGZH 退役线×8+GimmeAll/MoneyAutoGuardian 旧根残留+HQ-C10-Pilot2——比初判 2 件多 9 件：task-health 焊点首发全抓） | task-health.ps1 焊 BROKEN-LINK 检测（enabled=E2/disabled=E3 register）→**首发即抓 11 件**→全量 XML 定义备份（.codely-cli\task-backups\retire-20261016-waveF\）→**注销 11 件**→复跑 **BROKEN-LINKS 清零**（86 项受审·三步实弹闭环） |
| 11 | law-registry.md 工作树被回退丢 10-15 三批立法台账行（与 #6 同秒 11:48:04·三文件同刻=一次批量 git 恢复类操作） | **已恢复**（git checkout·diff 归零实证）——根因追溯见 §六 |

## 三.1【治本令执行回执 14:3x·追溯链】

| 问题 | 追溯（为什么发生） | 治本（根上怎么治） | 状态 |
|---|---|---|---|
| OrderSentinel「纸面」误判 | 审计验证器搜错文件名+命名盲区=否定性宣称未到源核验 | 勘误公开+坑录入律（否定性宣称必先读载体路径定义）+O-2336 回访判据闭环回执 | done |
| 令行/法条行被删（11:48 工作树回退族） | law-registry.md+orders.jsonl+task-health.ps1 **mtime 同一秒 11:48:04**=一次批量 git 恢复类操作把工作树文件回退到旧版（多窗并发在脏树上做 checkout/stash 类动作·与 sparse-checkout 删仓/autostash 冲突族同源） | ①两文件已 checkout 恢复（diff 归零实证）②根治=多窗并发恢复类 git 动作禁令候裁（现有让路律「他人在途态禁碰」扩面到 checkout/stash/restore）③深防=哈希锚扩面候裁（保护清单变更按其法走 governance §9 提名） | ①②done③候裁 |
| 断链死任务 11 件 | 迁移/退役流程从不重指或注销计划任务（MoneyAutoGuardian 指旧基地根=迁移残留；CarGZH 线退役时连脚本一并删除但任务留册） | ①task-health 焊 BROKEN-LINK 常设检测（夜轮自动捕获·下次迁移/退役漏网 ≤24h 内现形）②11 件已备份+注销③收线法（governance §3）执法注记候裁：退役令必附「任务注销/重指清单」 | ①②done③候裁 |
| 14:12/14:33 装配班 cron 两连蒸发 | 会话件（session cron）承载跨会话生产职责=结构性脆弱（busy 时槽位滑失无日志） | 生产职责一律常设计划任务/durable 载体；本窗装配已亲手执行（build_full_mv_v3 跑批在飞）；后续班次载体改挂建议候裁 | done+候裁 |
| S4U 存量 106 件 | 法 09-29 立而无部署计划（无转换令/无 owner/无死线）+登记器未焊 | 增量面已焊（Cure-9）；存量转换=提权窗+量裁+BigMoney 域 D-20261002-02 政策冲突同窗收口 | 候裁（§四.3） |
| 孤儿法 6-8 件+矛盾对+残留 | 登记簿纯手工维护·立新法与入册两步分离无闸 | 10-19 季度瘦身日批收口（既有载体）+本次盘点全清单已备好给该班 | 候批（§四.6） |

## 四、待 CEO/委员会裁决清单（治本令执行后更新·7 项）

1. ~~OrderSentinel 挂载~~ **已撤回**（勘误 §1.3——在役双活·回访判据闭环）。
2. ~~尸体任务退役批 13 项~~ **已执行**（11 件断链件注销+备份；余 2 件 BoardForge/PopupWitness=设计内停用件·保留观察）。
3. **bm-a 存量 ~95 项 S4U 大手术**（注销 11 件后基数）——需提权窗+委员会量裁；同窗收口 BigMoney 域 D-20261002-02 政策冲突。
4. **远端 branch protection**——CEO 物理件 23 天挂账（禁 force-push 远端机核缺位·G12 提案在库）。
5. **L1 小脑消费率止损**——10-28 线·现 ~0.2% vs ≥20% 目标。
6. **孤儿法 6-8 件+否决窗残留+外审班频三口径（AI.md 漏勘行）+矛盾对 10 组**——随 10-19 季度瘦身日批收口（本次盘点清单=该班工作底稿）。
7. **多窗并发 git 恢复类动作禁令扩面**（checkout/stash/restore 在脏树上的让路纪律=11:48 工作树回退族根治）+**哈希锚扩面候选**（law-registry/orders.jsonl 入保护清单·按其法走 governance §9 提名通道）。
8. **CeoDeskServer 每分钟失败+DailyDigest rc2**——MiniGame 域内待判移交；**sli-reconcile 根路径硬编码**（bm-b 件不可移植）+**fleet-mechanism-audit.ps1 引用者待证**——合并为小件候批。
9. **生产班次载体改制**（装配/装配后班改挂常设计划任务或 durable 载体·戒会话件承载生产职责）。
10. **orders 尾部 15+ open 挂账催办闭环**——超时哨普挂（现只挂分叉案）；P- 卡 schema 加死线字段候裁。

## 五、结论

机制面：核心载波 8 件全绿带证据（交付哨/班哨/数据面/调度器/让路面/cron 商店/装配班/机队远端）；**OrderSentinel 经勘误后并入健康面（在役双活+回访闭环）**；病灶集中在「**登记在册但已死**」家族——断链死任务 11 件（已治：检测焊进 task-health+全量退役+清零实证）、尸体产线、存量 S4U ~95 件（候裁）——与 C-02 病根「立法≠机制」同源同症。规则面：66 行法约 53% 有实载体、33% 纸面、14% 废止/漂移；登记簿自身健康，欠账在孤儿法+矛盾对+指针断链（10-19 批收口）。

**总判（含治本令回执）**：集团的病不在「没有规则」，在「规则与机器两张皮」。缝合线已焊上并首次全量执法——部署=点火律（Cure-9）连本审计自身都被它纠了一次（§1.3 勘误）；「登记在册但已死」族已完成首轮根治（检测常设化+11 件退役+数据恢复）；存量扫除（S4U/孤儿法/矛盾对）按 10-19 瘦身日批裁决走。**追溯的最终结论：大多数病案的根都长在「立法/退役/迁移时没有配套的机器面收口步骤」——今后凡立法/退役/迁移令，必须附「挂载点+点火证据+注销/重指清单」三件套才算闭环。**
