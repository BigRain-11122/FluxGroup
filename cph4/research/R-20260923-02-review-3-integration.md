# R-20260923-02 评审件③ · 三司接入成本（独立评审·互不见稿·诚实律）

> 判据=02 章程 §四七线 + 02a/02b 实测 + 02c 方案件。本评审自补实测：根 CODELY.md=59 行/54 条（02a 时点 49 条，同晚 +5——追加速度实证）；BigMoney CODELY.md=163 行/149,345 chars（均行≈916 chars，**行数水位抓不住它**）；Tools/selfaudit.ps1=60 行只读件（现无 size-lint）；quant/bigmoney/fleet/orders/=27 件入库（O-*.md 单令+T-*.json 任务）+MSG 流+bm-a/bm-b.json 心跳；gaming/FluxVerse/TECH.md L29/L77：fleet_machines 探针读心跳 JSON，**不读 fleet-allocations.md**。

## ① 七条验收线（章程 §四）

| 线 | 判定 | 理由（引方案件） |
|---|---|---|
| 1 单一事实源 | PASS | 02c §一 L1「事实只在此登记一次」+复述禁令（CEO 原话仅存 orders.jsonl 一处）；产品令面（BigStream orders/ 23 件、fleet O-*.md）属子公司自治不算复述，但 schema 须注明两命名空间分界（③-4）。 |
| 2 机器优先 | PASS | 02c §一 L1 全 jsonl/yaml+探针直接消费；批1③ orders_hq 探针影子模式在案；selfaudit.ps1 实测 60 行只读，加 size-lint 段为小改。 |
| 3 冷启动预算 | CONDITION | 02c §四目标 ≤4k tok 与 §一 L0 帽「200 行/25KB」不自洽：25KB≈8.5k CJK chars≈6k tok、200 行×200 chars≈40KB，帽为目标 3 倍以上；须分「硬帽 25KB」与「根索引卡工作目标 ≤3k chars（≈2k tok）」两档写进 §二水位。 |
| 4 开线成本≤2 | PASS | 02c §三批2 判据=BigLife 案例重演（org.yaml 一行+changelog 自动），正治 02a §5 现状超 3-5 倍；BRAND §8 T0 面方案已自曝并由 CEO 终审覆盖。 |
| 5 体量三律 | CONDITION | 02c §二三档水位+size-lint+夜轮近限齐备（02b 路四有先例）；但首版水位全悬「待波A 定标」，且根卡只有行数档——BigMoney 163 行<200 行帽实测证明行数轴单独失效，须补 chars/bytes 轴才可落 lint。 |
| 6 禁 big-bang | PASS | 02c §三批间纪律：每批独立 commit 可 revert+批后 24h 观察窗+pilot 单件，rainbow 同款（02b 映射表）。 |
| 7 运转不中断 | CONDITION | 批1 影子读一夜全等切主源覆盖 orders_hq ✓、机队面零触碰 ✓（见②核查）；但批2 吸收 fleet-allocations.md 后 scheduling.md §1/governance §6 引用链、批4 后 Biggame 转办投递面（其只 poll MiniGame 仓、靠 ledger+夜轮催办）均**不在各批判据内**——读侧换源是接入成本大头。 |

## ② 专项：三司接入成本

**批1-5 改动清单（谁动 mandate/探针/协议）**
- 批1：三司零触碰 ✓（BigMoney fleet/orders、BigStream orders/、Biggame U 号面均不在范围=02 §七边界正确）；实际承担方=FluxVerse orders_hq 探针——其游标已改内容寻址 hqorder:\<sig\>（P-10 已收口），jsonl 路径须沿用同范式防位置游标复发。
- 批2：三司 mandate/协议零动，开线受益（6-10 文件→1 行）；须同批改指针的下游=scheduling §1、governance §6（未入判据，见①-7）。
- 批3：HQ 单侧（根记忆 54 条）；三司纯受益。
- 批4：三司零改；DevLoop 自领切读（02c 批4 行内）；Biggame 投递面保通未列判据。
- 批5：三司各领自家记忆件（BigMoney=P1/BigStream/MiniGame）：只动记忆面，fleet 协议件（FLEET-OPS/TRANSFER.md）不动；机队协议类记忆条应转指针指向 fleet/*.md 原件（顺带去重减量）。

**多花/少花对账（冷启动自动注入·est tok·02a 口径）**
| 面 | 现状 | 治理后（建议） | 备注 |
|---|---|---|---|
| 根/HQ 窗（集团脑） | ≈25.0k | ≤2k（批3） | 每 HQ 冷会话省 ≈23k，三司共用此脑 |
| BigMoney 产品仓 | ≈104.5k | 索引卡 ≤50 行/≤5KB≈1.2k+按需主题 ≤2k/次 | 全案最大单点收益（≈-100k/冷会话） |
| BigStream | ≈7.9k | ≤1.5k | 轻件 |
| Biggame（线 5.5k+MiniGame 4.2k） | ≈9.8k | 各 ≤1.5k（线/产品卡去重后） | 见③-3/③-5 |
| media/life/domain 线+BigLife 产品 | ≈3.1k | 暂不动 | 量小但治理无归属（③-3） |
- 多花面：拆分后每任务多 1-3 次「按需读主题文件」（≤2k tok/次）+各司一次性「append 一行指针制」纪律切换；生成器维护税在 HQ 侧不在三司。
- 口径风险（诚实律）：02a 假设全量注入；若 Codely 同款 25KB 截断生效，现状实际注入 ≤6k tok、账面节约缩 4-10×——但 read_memory 全量返回与 context rot 不受截断保护，治理结论不变；批3 前须一次产品仓冷注入实测定口径（02c §四本承诺前后实测）。

**BigMoney 拆分工作量评级**：P1·多会话工程，禁一次会话毕——154 条×均 916 chars，全量读入≈105k tok 已超单窗实用预算，须按 02b 路二「子代理分档摘要回传」分 2-4 会话读入+1-2 会话分类重写校验；现实治理后预算=索引卡 ≤5KB/≤50 行+主题 5-10 档（策略账/机队协议/任务史/故障史/CEO 令/其他）。
**批5 权责**：CODELY.md 是机队+策略账正史——执行权=BigMoney 自领（机侧会话），拆错责任=自领件回执人+git 整体 revert 兜底；02c §三批5「集团只立法不代改」+风险 6 边界清晰 ✓，但三缺：①无批3 同款备份/冻结要求；②无问责明文；③无回滚判据。且拆分期 bm-a/bm-b 在途回测窗仍会 append（竞态，③-2）。

**机队消费面核查（验收线 7 实证）**：fleet orders（O-*.md/T-*.json/MSG 流）、心跳（bm-a/bm-b.json、MiniGame a/b/c.json、fleet/machines/*.json）批1-5 全程零触碰 ✓；FluxVerse 轨道坞读心跳不读分配表（TECH.md L29 实证），批2 吸收 fleet-allocations.md 不影响城；唯一动作=scheduling §1 等引用改指针（须入批2 判据）。

## ③ 新风险（方案 §五清单之外）
1. 行数水位单独失效（实测 BigMoney 163 行<200 行帽）——全部水位须 chars/bytes 双轴。
2. 批3/批5 重写记忆文件期间并行窗 append 竞态：根记忆同晚 49→54 条速度下，覆写与追加互吞；须冻结窗或「快照→拆→diff 补写」；governance §6 写域纪律未覆盖记忆工具面。
3. 线级 CODELY.md（gaming 5.5k+media/life/quant 线合计 ≈9.8k tok）不在批3（仅根）也不在批5（仅三司产品面）——治理盲区。
4. 命名撞车：registry/orders.jsonl、registry/machines.yaml vs BigMoney fleet/machines/*.json、BigStream orders/——schema 须显式「集团登记处≠产品机队面」注记，防探针/代理想当然读错源。
5. gaming 线卡与 MiniGame 产品卡同主题重复（02a §7-8）——批5 转办件须定线/产品去重归属，否则双改双膨胀。
6. size-lint 须守 selfaudit.ps1 只读律+ASCII 律（PS5.1 GBK 陷阱）——CJK 文件统计须显式 UTF-8 读，现脚本无此先例段。
7. BigMoney fleet/orders/ 有两枚 2.46MB croc 传输态 JSON（未入库 ✓）——retention-scan 水位面应纳入 fleet 运行时件，防 size-lint 报表被工作树噪音淹没。

## ④ verdict：有条件放行
- 条件1（最关键）：「每批下游消费方清单+影子判据」升为批2-批5 通用纪律——批2 补 scheduling §1/轨道坞指针链验证、批4 补 Biggame 转办投递保通实测、批5 补记忆面回执三件（条件3）。
- 条件2：批3 落地前两项定标入册：产品仓冷注入实测（定截断口径）+根/线卡水位补 chars 档（工作目标 ≤3k chars、硬帽 25KB）。
- 条件3：批5 转办件模板补三行：冻结窗/快照要求（批3 备份律平移）+拆错问责=自领人+回滚判据=git 整体 revert。
- 一句话最关键修改：接入成本的大头在读侧换源、不在写侧登记——把下游消费方影子验证从批1 特例写成每批通用判据。
