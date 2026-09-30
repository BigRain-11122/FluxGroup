# BigMoney 可信度审计与修复单 RW-1~RW-7（2026-09-30）

> ## ⚠️ 旧数作废通告（2026-09-30 12:57 后生效·D-20260930-22）
> **本件 §一「实况台账」及其他章节中引用的历史 Sharpe／年化／J 线读数，均系"出场未来函数修复前"口径，自 D-20260930-22 起全线作废，不得再引用。**
> 依据：BigMoney `d15f6dc60` 12:57 修复 `engine/backtester.py` 出场成交时点（当日 close → **T+1 open**）后重跑 6 在册员，虚高幅度实测：`COMPOSITE-CE-01 1.7479→0.8620（−51%）`／`NEEDLE-DE-01 0.4089→0.1927`／`ENGULF-CE-01 0.3835→0.1686`／`VOLATILITY-CE-01 2.0568→1.7166`／`COMPOSITE-CE-02 1.6392→1.5605`／`DROUGHT-CE-01 1.2130→1.2407`。
> **后果（如实）**：6 员中 **NEEDLE 与 ENGULF 已跌破其自身 OOS≥0.8 门**（实质合规 4 员）；`OOS Sharpe 1.73 validated`、`NEEDLE ×3 0.483`、`ENGULF ×2 剃刀线 +0.002` 等宣称**一并失效**。
> 本件保留原读数**仅作审计留痕**，并在读到时点一律以此横幅为准。

> 性质：集团层独立审计 + 可派工修复单。**集团层零产品代码**（RULES/CODELY 结构律）——本件只在集团层立档与派工，**不动 BigMoney 仓一行代码**；司域实现与 T- 票号由 BigMoney 自领落 `quant/bigmoney/`。
> 触发：CEO 2026-09-30 令「指出问题，指明方向」→ 本件为选定方向 A（可信度修复）的执行件。
> 方法：五路专家并行审计（策略有效性／回测工程／风控合规／自治组织／对抗性红队）+ HQ 独立复算。**证据一律为文件路径+行号+实数**，宣称与证据不符者当场标注。
> 诚实分级（governance §10 三态）：✓=本次实证 · 🟡=部分证据 · ⬜=未验证（标注原因）。

## 〇 一句话结论

**BigMoney 的"科学诚实层"（预注册/DSR/PBO/CSCV/ADV 分层滑点）是行业以上水准的真代码；但"有效性层"与"策略层"已脱钩——出场未来函数、锁盒只在元数据、三面口径分叉、数据半旧半重复——导致它输出的每一个 Sharpe 都不足以支撑 CEO 决策；同时判据线已被自身试验账本（N=361,984）抬到项目史上从未触及的高度（1.1958），系统进入"诚实但无产出"的闭环。**

## 一 实况台账（HQ 独立复算 · 全部 ✓）

| # | 项 | 实数 | 证据 |
|---|---|---|---|
| 1 | 实盘 / 券商模拟盘 | **0 / 0**；仅自研 shadow 纸盘 | `live/gateway.py` 全 76 行仅 `emit_order_sheet` 写 CSV，**不调引擎**；`live/paper.py` 末次改动 09-28 |
| 2 | 纸盘实绩 | 6 名交易员 **全部 0 完成交易、`months_tracked=0`**，`bars=4` | `results/paper/*_paper.json`（六件全同构） |
| 3 | 纸盘净值 | 600 万虚拟本金 → **净 −4,646.49 元（−0.077%）**，3/6 账户零交易 | `results/paper_export/export-2026-09-29.json:361` |
| 4 | 试验账本 | **N=361,984**；技能线 v2=**1.1958**；被动基线=0.3792 | `results/scorecard_v1.json` |
| 5 | 真过门 | gate_attrition **106 批仅 2 条 `validated=true`**；`strategy_rank.csv` 59 行 **`g1_pass=True` 0 个** | 专家① `Import-Csv` 复算 |
| 6 | 北极星 | SPM J4=**0.4854** vs 冻结线 0.70（缺口 0.2146，达线率 69.3%）；SPM-v1 过闸=**0** | `firm/STABLE_PROFIT_MODEL.md:20` |
| 7 | 亏损归因 | 21.46pp 缺口中成本仅占 1.0pp；真因=政体（bear 0.1793 vs bull 0.633），533/533 窗"正收益但跑不过被动" | `SPM_J4_ATTRIBUTION.md` |
| 8 | 当日 commit | **190 个：流程类 127 / 实物类 33（≈4:1）** | HQ `git log --since=09-30` 逐条分类 |
| 9 | 历史撞车 | 全史 3584 commit 中 **885（24.7%）** 标题含 collision/rebase/UU；`results/` 积 540 个 resolve 脚本 | 专家④实测 |

## 二 P0 级缺陷（阻断"数字可用于决策"）

### P0-1 出场是未来函数（回测系统性高估） ✓
- 现象：入场严格 T+1 open（`engine/backtester.py:407-408`），**出场却用当日 close 信号在当日 close 成交**（同文件 `:591` `exit_sig.loc[date]` + `:583` `row_close`）。
- 影响：出场零延迟 = 收益系统性高估；实盘只能次日开盘卖，**回测与实盘不可比**。
- 盲区：`smoke_test.py:128-131` 的"T+1 respected"**只查入场日**，测不出此偏差。

### P0-2 前向锁盒只是元数据（OOS 恒盲靠纪律不靠代码） ✓
- 现象：`engine/*.py` 搜 `oos_start` / `lockbox` / `evidence_cutoff` **零命中**；`scripts/science_gates.py:538-613` 只写账本字段；`science_audit` C2 只扫"字段是否存在"。
- 自我承认：`research/BACKTEST_SCIENCE.md:34` 已定谳 2025-01→2026-09-22 窗「烧穿」降格 IS2。
- 影响：任何脚本只要不自愿截断，就能读到锁定窗；**越权不可检测**。

### P0-3 回测/纸盘/网关三面口径分叉（"一套代码三开关"名存实亡） ✓
| 面 | 成本 | 停牌 | pnl | 证据 |
|---|---|---|---|---|
| 回测默认 | 13.04bp/边 flat | ffill **可成交**（`strict_open_fills` 默认 False） | **不含买入成本** | `tasks/backtest_task.py:56`、`engine/backtester.py:202/205/629`、`knowledge/rules.py:23` |
| 纸盘 | CostPatch(2) **双倍** + fill_guard + regime | 有 guard | — | `live/paper.py:472/516` |
| 网关 | 不调引擎 | — | — | `live/gateway.py` |
- 影响：三面数字互不可校验；任一面出问题都不会被另一面发现。

### P0-4 数据面半旧半重复 ✓
- `data/daily` 共 **1724 个 CSV**，仅 **48 只**更到 2026-09-29；**1670 只停在 2026-09-22**（stale 实测 1671）。
- **双键同券**：`sh510300.csv` 与 `510300.csv` 并存；而 `tasks/backtest_task.py:37` **直接以文件名当 symbol**。
- 影响：任何全量 `data/daily` 回测被"1.5 周陈旧数据 + 重复标的"污染。

### P0-5 判据线已成死栓（N_eff 自杀螺旋） ✓
- 技能线 `:= max(被动+0.10, μ_null + σ_null·√(2·ln N_eff))`，N=361,984 → **1.1958**。
- 项目史上最强读数：CTA `ma_slope_200@daily` **0.7462**、`vol_target_tsmom_60@daily` 0.7408；对子单面 skill_line 曾达 2.278。
- 影响：**全项目从来没有任何东西接近过这条线**；"每格入队即付账"（D6）+ 池子不扩正交广度（低波族与复合族 OOS 相关 **0.87**，"真独立风险引擎仅 1.5 个"）= 用越来越高的罚金惩罚同一个池子。

## 三 P1 级缺陷（阻断"上产线/上实盘"）

### P1-6 风控是死代码 ✓
`live/gateway.py:29-65` 定义 `RiskGate` / `daily_loss_breaker`，全仓**零调用者**（仅 `live/__init__.py:1` 导出）；阈值 `config/settings.py:29-32` 无执行点；`knowledge/market_rules.md:179` **自认**「P4 风控闸门外无执行点=审计 F-C」；`PLAN.md:208`「禁绕过风控下单」无机检。

### P1-7 退出优先级缺"熔断层"且单测薄 ✓
`engine/exit_rules.py:59-95`=signal_reversal→stop_loss→take_profit→time_decay→loss_time_stop→hard_limit，**无熔断**，与 `PLAN.md:205`「熔断>止损>时间>兜底」不符；`smoke_test.py:92-102` 仅 4 条 reason 断言，无跨优先级/日亏用例。

### P1-8 旧闸门在噪声地板之下 ✓
`PLAN.md:149-158`（≥30 笔／OOS Sharpe≥0.8／回撤≤25%）：20 条**随机入场**基线中 9 条 OOS≥0.8、**3 条同时通过全部三条**（`rand_p0.05_s6=1.494`、`rand_p0.02_s6=1.3932`、`rand_p0.02_s5=1.3581`；同表 `rand_oos_p95=1.3982`）→ 该门把 2025+ 多头 beta 记成技能。

### P1-9 库存三套口径，报不出唯一"过门数" ✓
`PLAN.md` §3「8 流派 35 骨架」／`research/STRATEGY_LIBRARY.md` §一「77 函数（底座 4＋判负 34＋袖珍 11＋候选 2＋余量 24）」／`strategy_rank.csv` 59 行（39 真＋20 随机）——三源不相等；`PLAN.md:151` 自认「历史快照」。

### P1-10 撞车跑步机：已诊断、修一半、然后遗忘 ✓
`HQ-FEEDBACK.md:39`（F-20260927-06）已定性「26 面共享快照每轮全机重写＝结构生成器」；三天后仍在连解 UU（r253=33／r455=19／r457=15／r458=17+19+19／r468=19）。lane 件（`compute_audit.bm-a.json`）已建，**共享面 `compute_audit.json` 仍每轮双写**；tick 自提交×轮 rebase 竞态 r366 修过后 r453 仍两次 push 被拒。仓根残留 **13 个「XX的冲突文件」副本**（`.gitignore`/`CODELY.md`/`dashboard.html`/`HQ-FEEDBACK.md`/`PLAN.md`/`smoke_test.py`/`state-bm-a×2`/`state-bm-c×2`/`state×2`/`town.html`），git 未跟踪、**无清理 commit、`.gitignore` 无对应规则**——即"已遗忘"而非"已修"。

### P1-11 红队点名两处"宣称与实况不符" ✓
1. `research/portfolio_report.md:80` **一句话内自相矛盾**：宣称"组合 OOS 全部强于任何单员"，括号内自承成员最高 2.06 > 组合 1.73；同文实算分散化增益仅 **+0.0299**、OOS 相关 0.87。
2. `t35_export equity 5,995,354` 被当终态成就展示，实为净 **−4,646 元**、3/6 账户零成交；并存事实=`round_reports.md:712` 自述"r457 push 从未落地"、worktree 37 条未提交、`state-bm-a.json` round_no=470 而 did=469。

### P1-12 法熵超标 ✓
全仓 **≥954 个 md**（firm 21 + docs 22 + research 383，depth≤4 下界），集团上限 5；`CODELY.md` 8943B **靠每轮 hot-cold 重排硬压 10KB 顶**；`round_reports.md` 714 行中 **128 行含"合法 idle"**；r262 自认 W1-W9 九连判负、A 层配额耗尽，同窗又开 SLOT-6~10 五条新线。

## 四 修复单 RW-1 ~ RW-7（可派工 · 逐条判据）

> 排序即执行序。**RW-1~RW-4 未全部验收前，RW-5 冻结令生效。**
> 每条判据均为**机器可验**；"完成"=判据命令实跑通过 + commit 指针，非文档宣称。

| 票 | 修什么 | 判据（机器可验） | 依赖 |
|---|---|---|---|
| **RW-1** | 出场未来函数 | `engine/backtester.py` 出场改 **T+1 open** 成交；`smoke_test.py` 新增断言 `exit_fill_price == 次日 open`；对 6 在册员重跑，**新旧读数差写入批报告**（诚实披露高估幅度） | 无 |
| **RW-2** | 锁盒代码化 | `evidence_cutoff` 升为 `backtester` **入参**并在数据装配处**硬截断**；越权读取 rc≠0；`science_audit` C2 增"实际读取行 ≤ cutoff"断言（非字段存在性） | 无 |
| **RW-3** | 三面口径归一 | 单源成本 spec（`knowledge/` 冻结件），回测/纸盘/网关**共用**；`pnl` 默认含买入成本；`strict_open_fills` 默认 True；selftest 断言三面对同一 bar 得同价同成本 | RW-1 |
| **RW-4** | 数据门禁 | symbol 归一化（去 `sh/sz` 前缀孪生键）＋ N 日无新 bar 剔除；在役面板锁定 **30 只**（现 48 只中混入 1670 只陈旧件）；门禁不通过=批不受理 | 无 |
| **RW-5** | **冻结新波次**（硬闸） | 自 2026-09-30 起，**暂停开新 prereg / 新供给线 / 新 SLOT**；既有在飞批可收口；解冻条件=RW-1~RW-4 全绿 | RW-1~4 |
| **RW-6** | 复算重发 | RW-1~4 全绿后**一次性重跑**：6 在册员 + null 池 + T-28 基线 + 判线 v2 重算；出「旧数 vs 新数」对照表（每员 4 数：IS/OOS Sharpe、年化、笔数、回撤） | RW-1~5 |
| **RW-7** | 风控接线 + 坑法二犯闸 | ①`RiskGate.check` + `daily_loss_breaker` **接入唯一下单出口**，拒单抛异常；②`exit_rules` 补**熔断层**且优先级单测覆盖；③**同一坑法第二次出现强制开修复单，禁止再写 CODELY 坑律**；④仓根 13 个「冲突文件」副本清理或入 `.gitignore` | 并行可做 |

### 验收面（RW-1~4 全绿判定）
- RW-1：`smoke_test.py` 新断言 PASS ×3 连续轮 + 高估幅度对照表落盘
- RW-2：注入式测试（构造 cutoff 后 bar 的读取尝试）**恰 FAIL** + 真机 rc=0 双证
- RW-3：三面同 bar 同价同成本断言 PASS
- RW-4：1670 只陈旧件被排除、孪生键去重后 symbol 集合无重复（打印 `len(set)==len(list)`）

### 时序与窗口
- 起点：2026-09-30；RW-1/2/4 可并行，RW-3 依赖 RW-1，RW-6 依赖全绿。
- 预计：RW-1~4 三日窗（10-03 复核）；RW-6 一个满窗；RW-7 独立并行。
- 与既有节律冲突处理：**RW-5 冻结令优先于"队列永不清空"（O-1819）与创新配额轨**——此二律在数字不可信期内不适用，解冻后自动恢复。

## 五 解死栓的登记项（不在本次修复范围，交 T-52/T-54）

> 本件只立档不派工——属"方向 B"面，另行呈批。
1. 准入判据降维：以**随机 null 分位相对判据**替代绝对 0.8（现 `rand_oos_p95=1.3982`），并把"过门"定义单源到 `g2_registration_v2`。
2. 北极星对齐：J4 是 beat 率而非 Sharpe，健康搜索目标应直接是**跨政体 12 月池化 beat-passive 率**。
3. 扩正交不扩数量：库内三件 **OOS 留存 >100%** 的族优先策略化——`lhb_count_20`（IS IC −0.0642／IR **−0.84**）、`gdhs_chg_2q`（IS IR **−0.675**）、zoo 行为族 `zoo85_stv`（留存 120%）/`zoo92_coin_team`（留存 109%）。

## 六 诚实度声明（governance §10）

- ✓ 实证：本件 §一 全部 9 行、§二 P0-1~5、§三 P1-6~12 均带路径/行号/实数，由 HQ 或专家当场复算。
- 🟡 部分证据：P1-12 的 "≥954 md" 为 depth≤4 下界（未遍历 `Money02/`3.1GB、`Money0923/`、`legacy/`、`.codely-cli/`1.6GB、`results/`500MB、`data/`343MB）。
- ⬜ 未验证（标注原因）：
  1. **零未来函数的历史宣称**——唯一来源是自审 `research/AUDIT-20260923.md:16`，无独立复算；RW-1 修完后应重立此宣称。
  2. **`dualrun ZERO-DRIFT 49/3`** 的语义——`results/_s6_r470_dualrun.log` 全文一行，cutoff 字面为占位符「11:5x」未填充；且为 merged-view==shared-blob **自比对**，非独立验证。
  3. **`.codely-cli/`（1.6GB）未审计**→密钥/凭据风险未排除；`config/`、`scripts/`、仓根扫描 0 命中且无 `.env`，但 `.gitignore` 缺显式 `.env` 规则（低风险）。

## 七 溯源

- 派工令：D-20260930-05（`docs/decisions.md`），CEO 令 2026-09-30 方向 A。
- 审计方法：五路专家并行（策略有效性／回测工程／风控合规／自治组织／对抗性红队）+ HQ 独立复算；专家回执为一次性证据采集，未改动任何文件。
- 集团法依据：`docs/governance.md` §6 禁重复开发 + §10 诚实律；`docs/executive-protocol.md`（产出=git commit 非 md 文档）；`RULES.md` §3 测试后再宣称。
- 司域实现与票号：由 BigMoney 自领，禁 HQ 代写产品代码（`CODELY.md` 结构律）。
