# R-20260923-02 评审件① · 架构与扩展性（独立评审·三视角之一·互不见稿）

> 评审对象=02c 方案件；判据=章程 §四。**诚实律标注**：评审员完成全部核证（含 governance §2/§3、orders.md 双表结构、evolution.md 状态机、BRAND §8、fleet-allocations、根 CODELY.md、orders_hq 探针实读）后于成文时中断，本件由 HQ 会话按其手稿代落，判定与理由均出自评审员原稿。

## ① 七条验收线逐条判定

1. 单一事实源 — **CONDITION**：治理面闭合成立（L1 唯一登记+复述禁令+批2 吸收四处）；但两处未闭合——governance §2 登记簿「备注」列的叙述型事实（仓名悬置/职责叙述）在 org.yaml 无字段归属；记忆面（12.5 万 tok·比治理面更重）批3 只治根、批5 只转办立法不执行——事实源改造对记忆面只是纪律约束。
2. 机器优先 — **PASS**：L1 全结构化+探针直读+size-lint 接线（Backstage/event sourcing 先例在 02b）。
3. 冷启动预算 — **CONDITION**：场景1（根）批3 有实测判据 <2k ✓；场景2（产品仓 BigMoney 10.5 万 tok）仅批5 转办、无判据无时限；章程「暂定 2k」vs 02b 定标「注入 2k+首读 2k=4k」的解读差须显式定稿入册。
4. 开线成本≤2 — **CONDITION**：批2 演练判据好；但开线五步剩余触碰面（.gitignore 加行/线 README/线 CODELY）未列入派生或豁免清单——演练必须含这三步才算重演 BigLife（02a §5 实测它碰的就是这十处）。
5. 体量三律 — **PASS**：三档水位+selfaudit+夜轮+周报四接线全落点。
6. 禁 big-bang — **PASS**：五批独立 revert+pilot 单件+24h 观察窗（rainbow 先例）。
7. 运转不中断 — **CONDITION**：探针影子读覆盖 ✓；但①orders_hq 探针正处 P-10 内容寻址修法在途，与批1 影子基线的时序协调未写（两条并行线防互相扑空）；②夜轮 mandate（night-round-prompt.txt 感知步）的源切换未列入批1 交付物。

## ② 专项审查（架构与扩展性）

**2-1 三层覆盖不到的事实类型（四项须补 schema 归属）**：①orders.md 三个非令段落——CEO 待办物理件（无 ts 锚点的状态清单·可划线消项）/悬置项/AI 代决记录（否决窗跟踪），六字段「一令一行」表达不了；②governance changelog 派生依赖 commit 规范先立（P-24 尾标纪律刚立·commitlint 类规范未有——**派生前置=commit 规范立法**）；③architecture Roles 表（人）=L2 显式豁免声明；④时态条款（资源倾斜态「至 M1/v1.0 tag 后复审」）——org.yaml/machines.yaml 需有效期字段或 L2 指针，否则战时令永久化。
**2-2 org.yaml schema 三分叉**：①状态枚举未正典（§2 active/onboarding/closed+BRAND locked/codename+「待 remote」并存——须枚举表+状态机+codename→locked 正名流程接线，防探针派生踩 F3 写死状态同款坑）；②**实体模型分叉：「一行一实体」在 gaming 线两产品仓（MiniGame+FluxVerse）面前不成立——线/公司/仓必须三实体类型+多对多关系边**（bm-a 一机三角色、BigDomain「中台=三司产能」同证）；③schema 自身须版本化（FluxVerse 协议宪法同款：加字段任意/删改义升版本）——第 6-10 家子公司每次加字段都可能破坏探针解析。
**2-3 orders.jsonl 最大未决=状态更新语义**：append-only 状态事件流（status 变更追加事件行·检索时折叠得最终态·event sourcing 正统）vs 原地改行（违反追加纪律）——方案未定，直接决定探针游标与生成器实现；连带：跨窗未闭环令（如 O-1602 executing 跨月追踪）在 30 天归档后仍须可达（governance §9 溯源条款要求）。

## ③ 新增风险（方案清单之外）

1. changelog 派生链断裂：commit 规范未立前不能撤散文 changelog。
2. 「一行一实体」歧义随第 6 家子公司爆炸（实体模型不定的结构性风险）。
3. 批3 只治根记忆·线记忆（gaming 5.5k+media/life/quant 合计 ≈9.8k tok）=治理盲区（与评审③③-3 撞点互证）。
4. P-10 与批1 双线并行的时间窗风险（互扑空/基线错位）。
5. BRAND §8 是 T0 面——其迁移批的「CEO 终审」须写进批2 判据本身，不能只停留在方案层注记。

## ④ 总体 verdict：**有条件放行**（4 CONDITION/3 PASS/0 FAIL）

放行条件四条：
- **A1**：orders.jsonl 状态更新语义定稿（评审建议=append-only 状态事件流+折叠检索，与 P-10 内容寻址游标天然同构）+三个非令事实段落的 schema 归属。
- **A2**：org.yaml 三实体模型（线/公司/仓+关系边）+状态枚举正典+schema 版本号。
- **A3**：开线演练判据补全（含 .gitignore/线 README/线 CODELY 三步）→实测 ≤2 触碰。
- **A4**：批1 与 P-10 在途修法时序协调条款+夜轮 mandate 切换入批1 交付物。
