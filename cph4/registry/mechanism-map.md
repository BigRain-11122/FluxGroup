# MECHANISM-MAP — 集团机制总图（从上往下·v1）

> 溯源：CEO 令 2026-10-14 23:4x「所以你再按照这个架构去帮我梳理一下机制，从上往下梳理，一定要顺畅高效。有效、科学、理性。」（O-20261014-2345）
> 定位：**机制链的唯一总图**——从 CEO 往下一条线读通全部机制与它们的咬合面；每层给「输入→动作→输出→谁消费」四段流水线+正典指针+SLI。治理架构一页图归 `docs/governance.md` §0.1（本件织其机制层）·节律明细归 `cph4/cadence.md`·法条索引归 `cph4/registry/law-registry.md`——三件互指不复制。
> 实况核对：读本件后先跑 `Tools/fleet-reality.ps1` 取当日实测再信文；一切 SLI 以证据面为准。

## 〇、一条线总图（从上往下）

```
CEO Jason（唯一决策者）
  │  一句话即令 ──▶ 任一承接窗当窗转单 ──▶ orders 行 ──▶ poke 秒级唤醒
  │                                    （SLI-5：令入账→转单 ≤30min）
  ▼
决策委员会（council.md v2.3·七席功能制）
  │  常务轮 00:00/12:00（拍板+复盘四问+自迭代）·E3 紧急通道 ≤1h
  │  对三台账只读只议——落账经 L2 单写手（2026-10-14 勘注定谳·三次丢行案根治）
  ▼
主AGENT＝CEO-PROXY（集团枢纽·CHARTER v1.1·8 班/日风险加权）
  │  五雷达（满载/死线/回执/关注点20/盲区14）·台账唯一写手（orders/decisions/POOL）
  │  交接卡九要素+card-lint 打回·POOL 五态+核销双勾·落单+poke·催办升级
  │  思考路由律：量产/分类/草拟→L1 本地 35B 零 token；深判/架构→云端好模型
  │  落单必带交付契约（expected_paths+deadline→交付哨盯货）+build 类子任务寻源闸（GitHub 高星有轮直接用）·调用面=智能体库 cph4/agents/（不登记不存在）
  ▼
巡视舰队（PATROL-FLEET v1·10 域席·每域一个专业巡视）
  │  PT30M 传感扫描（零 token）──▶ 旗 ──▶ 域巡视班（按域章程执法·锁+防抖+同签+日帽+snooze）
  │  日更域 digest（本地 35B·零云端）·升级件→NJ/域 shiftlog+舰队 LOG
  ▼
L1 小脑（本地 35B :8090·38 字/秒）
  │  量产/分类/草拟/常规判断/日 digest——零云端 token·SLI-4 计数台账
  │  降级链：让路期回收→班直升云+晨补（10-14 看门狗自愈实证）
  ▼
L0 脊髓（确定性·零 LLM·24/7）
  │  fleet-dispatcher PT30M（旗+POLO+NEED-JUDGMENT 再生）·IdleWatch PT15M·oversight 小时
  │  承载件三件：事件班承载 PT15M（红旗→无头事件班 ≤15min）·外部探针 PT1H（监控者有监控）
  │  ·SLI 席外对账（bm-b daily 08:35·自产自审计破）·巡视载体 ×10 PT30M
  ▼
执行层（各司 OS 循环 10min+自领引擎+机队四机定岗〔bm-d 候入队〕）
  │  执行权永不下放主AGENT——防官僚红线；POOL 池单+车道定岗（resource-chain §9.1）
  │  git=第二层备份+正典持久化·FleetLink 直推=第一通道（毫秒级目标）·HOT/WARM/COLD 三层兜底
  ▼
反馈回路（一切宣称带证据）
  交付契约哨（DeliveryWatch every:5m：PENDING/OVERDUE/DELIVERED 三态·过线自动点名 poke）
  回执 24h→E1 委员会→两轮未决自动出声 CEO（兜底终点=人）
  SLI 总表（下§四）·哈希锚 22 件+反转闸+丢行守望 --audit·席外对账
```

**一条升级线（全文只此一条·全链实测 7 分钟）**：
域传感旗（PT30M 扫）→ 域巡视班（章程即决+深挖）→ NJ+域 shiftlog → 事件承载件 ≤15min 或枢纽班 ≤3h → E1 委员会两轮 → **CEO 出声**。
实锚：10-14 23:34 bigstream 黄旗落 NJ → 23:41 事件班发射（7min·六条域发现全收）。

## 一、七层流水线（每层四段：输入→动作→输出→消费）

**L4 CEO 层**
- 输入=orders 台账（唯一审计面）+各窗呈报（已决+判据+绝对路径）。
- 动作=一句话即令/翻案/保留面裁决（真金>500/红线/命名/人设/物理件/开线收线/删仓删史）。
- 输出=orders 行（原话+落点+状态）。
- 消费=承接窗（转单）/代理席（巡班执法）/委员会（复盘面）。SLI-5 令转单 ≤30min。

**L3 委员会层**（正典=cph4/council.md）
- 输入=各司上报（23:00 截止）+E0/E1 升级件+提案证据包。
- 动作=常务轮双班拍板（4/7 普通·5/7 重大）+复盘四问+自迭代闭环；E3 紧急 ≤1h（席1+2+7）。
- 输出=决议（票档 decisions.md 委员会节·落账经 L2 单写手）+迭代项（既有台账 P-/D- 号·零新队列）。
- 消费=各司执行+L2 落账。**只读只议纪律**（2026-10-14 勘注并档=MASTER-AGENT/COUNCIL-DIVISION-ANNOTATION-20261014.md）。

**L2 主AGENT 层**（正典=CEO-PROXY/CHARTER v1.1+ROUND v3.1+MASTER-AGENT/BLUEPRINT v2）
- 输入=CEO 原话/L0 旗/NJ+域发现/DEADLINES/回执/十域知识周轮。
- 动作=8 班五雷达（锁门+旗分流：绿灯 ≤6 调用/标准 ≤15/事件全力）+落单（交接卡九要素+card-lint+**交付契约 expected_paths+deadline**）+POOL 五态迁移+poke 唤醒+死线重排如实披露+**build 类子任务寻源闸**（有轮=名称+星数+许可·真空白才自建）。
- 输出=orders/decisions/POOL（唯一写手）+LOG 班行（时刻|班型|调用数|verdict）+NEED-JUDGMENT 裁决。
- 消费=执行机（自领+回执）/CEO（出声三条件）/委员会（复盘）。SLI 1-3+效率判据（绿灯率 40-70%·平均调用 ≤12）。

**L2' 巡视舰队层**（正典=PATROL-FLEET/BLUEPRINT+CHARTERS 十域）
- 输入=域传感器件（文件新鲜度/关键词旗/§一 死线域行）。
- 动作=PT30M 零 token 扫描→旗（锁+防抖 40+同签 360+日帽 4+snooze 负反馈）→域巡视班按章执法（只读只议+即决清单）；日 digest（L1·按章雷达面逐条 verdict）。
- 输出=域状态件+心跳（媒体区）+域 shiftlog+舰队 LOG 一行+NJ 升级件。
- 消费=事件承载件（≤15min 接走）/枢纽班（雷达增量）/CEO（域月度红绿灯卡）。SLI P-1/2/3。

**L1 量化层**（正典=token-economy+local-first+l1-client）
- 输入=l1-client 调用（--prompt/--prompt-file/--pool-file）+域 digest 窗。
- 动作=本地 35B 分类/草拟/判读（思考路由硬映射·禁路由漂移）。
- 输出=结构化产出+SLI-4 计数行（media/logs/l1-consumption-ledger.jsonl）。
- 消费=域 digest/枢纽量产面/草拟三件（接线中·消费率 ≥20% 目标·两周止损线）。

**L0 承载层**（正典=DISPATCHER-CHARTER+各载体脚本头注）
- 输入=三机心跳/队列/任务态/文件新鲜度。
- 动作=规则路由+旗计算（STARVED/LANE-DOWN/CHASE/OFFLINE/HB-STALE/E0-RED）+NEED-JUDGMENT 再生+承载件点火。
- 输出=DISPATCH-LOG（30min）+oversight 台账+旗→承载件。
- 消费=枢纽/舰队/事件班（传感复用律：已测面禁重测）。零 LLM 零 token。

**执行层与反馈**（正典=resource-chain §9.1+fleet-protocol+versioning §4.4）
- 输入=orders 行+POOL 卡+哨兵唤醒（OrderSentinel 2min）。
- 动作=各司 OS 循环 10min 自领+车道定岗执行+外科提交/原子推+推前反转闸。
- 输出=产物上链+回执行（带卡 ID）+心跳。
- 消费=枢纽回执雷达（24h 升 E1）+值班对账+CEO（终点终审）。

## 二、节律一览（明细归 cadence.md·此处只列指挥链节拍）

| 节拍 | 机制 | 承载 |
|---|---|---|
| 2min | 令流哨兵（orders 新行即唤醒） | OrderSentinel |
| 5min | **交付契约哨**（PENDING/OVERDUE/DELIVERED·过线自动点名 poke） | bm-a-DeliveryWatch |
| 5-15min | 事件班承载（红旗→无头事件班 ≤15min）+活性/完整性哨兵 | event-carrier PT15M 等 |
| 10min | 各司 OS 循环（执行权所在） | OSLoop 族 |
| 30min | L0 巡班+**十域巡视席**（48 扫/日·零 token） | dispatcher+patrol-fleet ×10 |
| 3h | 主AGENT 8 班/日（08:43 晨检全雷达/21:43 死线/23:43 夜移交） | durable cron |
| 日 | 域 digest（本地 35B）+SLI 席外对账（bm-b 08:35）+委员会常务轮双班+**github 雷达日频扫**（寻源闸素材·晨检班固定片 ≤2 调用） | 各载体 |
| 周 | 进化轮 09:17+集团巡检周一 09:23+自艺调研 | 各轮 |
| 月/季 | 使命复盘+法熵审视+季度瘦身日 | 周轮承载 |

## 三、防线与安全链（从禁到核）

1. 结构性静默（U060 唯一正门 task-register+WT 收容所）——一切任务出生即静默。
2. 台账单写手（三次丢行案根治）+推前反转闸+丢行守望 --audit（步8 必跑）。
3. 受保护件哈希锚 22 件（改动=CEO 令唯定谳·Verify 拦推）——**待 CEO 一次同意**：G12=branch protection+全机 pre-push（提案在案）。
4. 凭据仓外零入库+真金 >500 闸+周真金帽+AIGC 合规三件。
5. 让路律（CEO 用机一句话）+编码律（BOM）+禁 spawn 控制台。

## 四、SLI/SLO 总表（「有效」的可测面·证据件齐）

| 线 | SLO | 证据 | 现状 |
|---|---|---|---|
| 令转单 ≤30min（SLI-5） | ≤30min | orders 时间戳差 | 首测待 10-15 |
| 红旗驻留 ≤90min（SLI-2） | ≤90min | 事件班 LOG | 10-14 实测 7min ✓ |
| 死线零误（SLI-3） | 0 件/周 | DEADLINES+夜移交 | 在测 |
| 心跳新鲜 ≤30min（SLI-1） | ≥99% | 双时间戳 | 达标 |
| L1 消费率（SLI-4） | ≥20%（两周止损线） | l1 台账 | ~0.2% 诚实面·接线中 |
| 云端消耗趋势+违例（SLI-8） | 周趋势可见+白名单外违例=0 | attribution+周报云端行（token-economy §10.4） | 10-15 立线·首测 10-19 |
| 交付契约过线零漏报（SLI-9·10-16 立） | 过线件 100% 自动点名 | delivery-watch watch.log+ALERTS.md | 首日双案例在哨 ✓（12:49 首单 OVERDUE-POKE+14:01 DELIVERED 压哨交付） |
| 域席心跳 ≤45min（P-1） | ≥95% | 域状态件 | 首日 100% ✓ |
| 域旗响应 ≤30min（P-2） | ≥90% | shiftlog 时刻链 | 首夜 7min ✓ |
| 域 digest 产出（P-3） | ≥90% | digest 件 | 首夜 10/10 ✓ |
| 到点执行率 ≥90% | ≥90% | LOG 班行 | 10-19 回访 |
| 越权直写台账=0 | 0 | git 历史可查 | 在测 |

## 五、已知张力（诚实面·设计取舍·非缺陷）

1. codely durable cron 7 天物理到期→步8 自检重建（每班自检·失效复盘）。
2. 夜窗无 REPL=主AGENT 班不触发→L0+承载件+舰队 24/7 兜底（零浪费取向·ROUND §班表）。
3. :8090 与 GPU 生产让路互斥→L1 断供日 digest 自愈延后（10-14 看门狗复活实证）。
4. weak git-copy 传感=拉取滞后假阳→域班权威分诊（snooze/digest_only 消源·首夜已用）。
5. NJ 由 L0 每 30min 再生→域班追加=加速面；**持久正身=域 shiftlog+舰队 LOG**（本批成文）。
6. L1 消费率 ~0.2% vs ≥20%→两周止损线（10-28 前 SLI-4 首测说话）。

## 六、在途件（不藏账·2026-10-16 23:5x 修法包 v2 刷新）

- bm-a 存量 ~95 件 S4U 转换批：C-20261016-04 §四拍板授权——候提权窗（CEO 物理件）后 48h 首批回执·≤10-23 呈状态。
- G12 远端 branch protection+pre-push：候 CEO 一次同意（23 天·DEADLINES 在案）。
- L1 小脑消费率 ~0.2% vs ≥20%：10-28 止损线说话。
- bm-b fleet-link v1.8 换血：候其轮班/夜班（高完整性旧监听器非提权不可杀·O-1745 §四）。
- tailscale 三机直连恢复（中继 sfo 降级）：物理件候 CEO（网关/VPN 排查）。
- 10-19 瘦身日底稿已备（C-20261016-04）：孤儿法 6 件复审+PROMPT-GATE CODELY 侧指针+否决窗字样全量注记化复核+瘦身候池五件+哈希锚扩面提名（+law-registry/orders.jsonl）。
- 10-19 回访：判据⑦-⑮+修法包 v2 判据六条（BRIEF 对齐率/孤儿法登记行/orders 去重/总图三新行/S4U 首批回执）。

## 七、怎么用这张图

- 新会话/新机：读本件 5 分钟得全局 → 按「要什么去哪」（AI.md §文件地图）下钻正典。
- 找堵点：沿一条升级线走一遍（输入→动作→输出→消费四段断没断）。
- 加机制：先查本图+cadence.md+law-registry 三处——已有=执法强化件·真空白才立项（防重复建设律）。
