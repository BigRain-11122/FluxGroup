# R-20260925-decision-round-2 — 决策轮 09-25 批调研与抽验底稿

> 立项三问：为谁而研=决策轮本批拍板依据（decisions.md D-20260925-01~06）；仓内已有=R-20260924-decision-round-1（首轮底稿范式）；判据预注册=各 D 行「依据」列可直接回查本件。
> 验证声明：外部源=检索结果页标题级（🟡未逐条入原文）；内部证据=本机 git/Test-Path/grep 实测（✓）。

## §1 收取面（当日批次盘点）
- 新到：BigMoney F-20260924-11~16（6 条）+FluxVerse F-20260924-02~20（回执链 19 条·F-13 为请裁件）+BigLife F-BL01~06（含 P-58 制卡回执）+BigDomain R13/R14（锁活性险情）+BigCompute 日清×2（D-08/09/10/11 审核回执）。BigStream 0 新；MiniGame 反馈面仍未落位（D-05 pending·夜轮点名链照旧）。
- 昨日 overruled=0（decisions.md 全行无驳回→无再报请件）；escalated=0；夜轮新点名=P-13（Biggame 反馈面·同源 D-05）+P-08 48h 窗 09-25 到期。
- 集团自身面：orders 未 executed 行均有主；ledger open=P-01（CEO 物理件）/P-52/P-57（影子期在途）/P-58（本批核销）。物理件=CEO 常设提醒面零催办（别催令）。

## §2 调研要点（外部锚+内证）
- **§2.1 硬界设计（F-11）**：业界=分布界（MAD/IQR/波动率调整阈值）为坏数据检测主责、上下文/交叉验证抓微妙错（Referential Labs「Market Data Hygiene」P1/P2·🟡标题级）——与 F-11 三件套同向（分布界主责+max 硬界配危机日感知+极端日先验）。判=采纳。内证=D-C 批 12 极端日（2015-07 救市日 |Δr1|=461.6bp>200bp 等）击穿硬界但三佐证裁定非腐坏=界设计失误非数据问题。
- **§2.2 P-12 解锁（F-13）**：纯内规解释件，外部调研不适用。依据链=委托决策令 v2（例外两类不适用：纯软件·零预算·零账号）+先做律+同域先例（P-10/11/43 均为 tick/verify/探针面修改且全在册）+安全网（T2 先登记后产出+沙盒断言+双绿律）。
- **§2.3 锁活性（BigDomain R13/R14）**：业界正典=锁文件写 PID+原子独占建（O_EXCL/CreateNew·禁 check-then-act 竞窗）+已存在则读 PID 探活、确认死才移除（dev.to「A PIDFILE lock is only as good as its stale check」/commandinline「never [ -f lock ] || touch lock」/sandcastle#429/racefree-filelock 等 5 源·🟡标题级）——与 FluxVerse r63/r66 已实证范式一致。心跳 touch=非主流（增写流量与竞写面）；纯加长接管窗=治标。判=采纳 PID 判活+原子抢锁，接管窗 ≥1.2×轮预算为辅。触发实证=17:45 整机重启→陈旧锁 15min 接管窗<轮预算 25min。
- **§2.4 GBK 乱码（F-BL01）**：grep 复验「闊抽」12 处在流✓（BigLife 报 22 处同族口径）；修法=git 输出显式 UTF-8（i18n.logOutputEncoding+控制台 OutputEncoding）——探针契约第 8 律（world\ 读取显式 UTF-8）扩 git 输出面。历史行留痕不改写（versioning §5）。
- **§2.5 转办提速（F-12/16）**：哨兵 P-77 已立法令流 ≤2-4min（唤醒面=ledger P0/P1 行）——F-12 原设「夜轮/周轮转达 48h」为哨兵前旧慢道→本批改走当日落 P-81 哨兵快道；F-16 需求（交易员持仓大字上窗）已被 P-78 v5 量化区吸收→反重复并轨，BigMoney T-35 paper_export 数据面前置（M2 09-29 依赖）。

## §3 抽验录（09-25 00:0x 本机实测）
- FluxVerse git log：r57~r90 全在册（r61/r62/r63/r64/r65/r66/r67/r69/r73/r74/r75/r76/r77/r79/r80 对位各回执切片）✓
- BigLife：census/reserved 3 卡+manifest 在✓·citizens-light 10003 行✓·OSLoop 年轮/行为线活（09-25 批次在跑）✓
- BigMoney：CODELY.md 27,965B（F-14 报 60.2KB 后再降=≤50KB 司级线达成✓）·results/regime_deep_replay.json+research/REGIME_GUARD_DEEP_REPLAY.md 在✓·r122 T-38 履约引擎接口稿 v0.1 已交（non-binding 待 GM+HQ 复核=如实注记·复核留下轮）
- world-events.jsonl「闊抽」12 处✓

## §4 留待下轮
- P-61 撞号改号（职能批/接口批）=周日周轮；切片回执行内注记批扫=夜轮 03:07；D-05/P-13=夜轮点名链；P-08 48h 窗今夜到期=夜轮盯。
- D-20260924-02 法条化+D-01 入口第⑤问修订=周日周轮；T-38 接口稿 GM+HQ 复核=下轮收取面。
- 否决窗 10-01 到期群（D-08~11/D2/落锁六件/T2 群）=周轮消点面预备。

## §5 结论应用表
| 结论 | 落点 |
|---|---|
| 硬界三件套/传输收尾步/fallback 后缀/水位出口 | D-20260925-01（任务单·BigMoney 即行） |
| P-12 解锁 | D-20260925-02（决策落行·DevLoop 自领） |
| 锁活性标准 | D-20260925-03（决策落行·两司先行+周轮条款化） |
| 乱码修复路由 | D-20260925-04（任务单·DevLoop ≤48h） |
| CEO 令转办提速 | D-20260925-05+ledger P-81（转办行·哨兵唤醒） |
| 回执核销+勘误 | D-20260925-06（台账翻面三处+登记） |
