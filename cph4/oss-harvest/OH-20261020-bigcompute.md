# OH-20261020-bigcompute — 开源收获轮·BigCompute 切片（PT-20261014-05 超窗补领·M78）

- **窗**：PT-20261014-05（audit-charter 在册 OPEN·大限 10-21）——本司上一 OH- 切片=OH-20261008-bigcompute（10-08 22:2x）/官方在册最后一片=OH-20261005-bigcompute（10-05 00:5x），72h 节律下已超窗 ~140h 以上，本片=补领。采时 2026-10-20 03:2x-03:3x +08:00。
- **业务面**：算力商业化引擎现役四条 JSONL 轨（M73 MOCK 成交环 mock-order-ledger／批池 batch-pool-stock／distr 归因轨预设计／月末归集 N1 聚合）——现役字段校验全为手写：deal_flow_mock.py／batch_pool.py 逐键 if 断言，字段改名或类型漂移只能靠下游读错才暴露。真缺口=**声明式结构闸**（一个 schema 定义、多消费点复用、漂移秒级暴露）。
- **反重复门基线（先查后采·三面·本窗实跑）**：
  1. 仓内面：`Select-String Tools\*.py -Pattern 'jsonschema|msgspec|beancount|pydantic'`=**零命中**（本司工具族尚未接入任何 schema 校验库·真缺口非双建）。
  2. 集团注册表面：`cph4/README.md` 命中 **1 行——「开源采用·JSON Schema 结构校验（2026-09-26 首例）」jsonschema（python-jsonschema·MIT·5k★）BigLife 采用=QC 巡检 schema 断言面**。→ 结论：**集团层面已采用（BigLife 首例），本司属复用面，不是新采用**（反重复律正形：先复用再谈接入，零新登记）。
  3. 实机面：本机 python 3.14.7 已装 jsonschema **4.26.0**（importlib.metadata 实测）→ 接线零安装成本。
- **实搜面（3 查 + 3 仓读 + 3 LICENSE 原文直采·全 A 级免登录·零翻页）**：
  - `api.github.com/search/repositories?q=json+schema+validation+python`（top5 全录）：python-jsonschema/jsonschema 4,990★·MIT·pushed 2026-10-19T19:01Z；msgspec/msgspec 4,175★·BSD-3-Clause·pushed 2026-10-19T12:58Z；Stranger6667/jsonschema（Rust）828★·MIT；horejsek/python-fastjsonschema 498★·BSD-3；Grokzen/pykwalify 296★·MIT·pushed 2024-01（停更）。
  - `api.github.com/search/repositories?q=plain+text+accounting+double+entry`（top5 全录）：bex-co/beancount-io 307★·MIT·pushed 当日（移动端外壳·非核心库）；redstreet/fava_investor 181★·GPL-3.0；redstreet/beancount_reds_importers 166★·GPL-3.0·pushed 当日；blossom-hub/blossom 30★·MIT；Nef10/SwiftBeanCount 16★·MIT。
  - `api.github.com/search/repositories?q=idempotency+key+event+ledger+python`（1 命中）：AlexKurinets/ops-workflow-hub 0★·MIT·pushed 2026-10-15——**诚实负发现**：描述与需求同构（effects ledger verify-by-key + dead-letter replay），但 0★/单人/无可信社区史 = 不采（脆弱依赖）。
  - 仓读三项：`repos/beancount/beancount`=6,100★·480 forks·**GPL-2.0**·pushed 2026-08-23·open_issues 251；`repos/python-jsonschema/jsonschema`=4,990★·701 forks·MIT·pushed 2026-10-19·open_issues 60；`repos/msgspec/msgspec`=4,175★·216 forks·BSD-3-Clause·pushed 2026-10-19·open_issues 234。
  - LICENSE 原文：①raw `python-jsonschema/jsonschema/main/COPYING`=MIT 全文逐字（「Copyright (c) 2013 Julian Berman」+ grant/notice 双段 verbatim）；②raw `msgspec/msgspec/main/LICENSE`=BSD-3-Clause 全文逐字（「Copyright (c) 2021, Jim Crist-Harif」+ 三条款 verbatim）；③raw `beancount/beancount/master/COPYING`=GPL-2.0 全文（Preamble verbatim）。**诚实注记**：beancount 仓根无 `LICENSE`（raw 404）·许可正本文件名=COPYING（API 与 raw 双源互证）。
- **五门评估**：
  - **python-jsonschema/jsonschema（复用面）**：①契合 过=四条 JSONL 轨声明式结构闸（漂移秒级暴露·一份 schema 多消费点复用）；②反重复 **过（复用）**=集团注册表已采用（BigLife 首例），本司按复用面接入不重复评估不新登记；③许可 过=MIT 原文逐字验；④健康 过=4,990★·pushed 当日·open_issues 60/4990=1.2%·十年长寿；⑤成本/安全 过=纯本地零外发零密钥·本机 4.26.0 已在装（零新依赖）。
  - **msgspec（判定不采·留痕）**：契合 △（更快的序列化+校验一体化），但④**重叠负**——与 jsonschema 面重叠而本司数据结构简单（9 行实数据 3 轨），msgspec 的 C 扩展收益不抵「两套校验语义并存」的成本（J 面：单一真源律）→ 判负留痕，重访触发器=轨行量 ≥10^4 或吞吐成瓶颈。
  - **beancount/beancount（参考位·许可负）**：①契合 过=月末归集 N1 复式对账语义（借贷平衡断言/账户树/期间闭合）；③许可 **负=GPL-2.0**→ 仅方法学参考，**代码一行不搬**（与 10-15 漫剧工具栈同律「GPL 只学不搬」）；④健康 过=6,100★·pushed 2026-08-23（两月内）·python 生态标准件；⑤成本 过=零实装。→ **参考位**：N1 月末单可借其「每笔双分录、期末必须平衡」的断言式对账思路（现役 cost_ledger 为单式累加→月末 join 面）。
  - **ops-workflow-hub（判负）**：健康负（0★·单人新仓）→ 不入采用面，仅记录「事件级 dedupe + verify-by-key」术语对照（本司 tx_id 幂等已自建同构）。
- **采用→落点（needs-based·本窗即落地·非囤积）**：jsonschema 复用面**已实装**=`Tools/rails_schema_check.py`（check/selftest/dump 三命令，两 schema=mock_order 14 必填字段+`^MOCK-` 前缀+`mock:true` 常量、batch_card 11 必填字段+`^B-` 命名域+status 封闭词表+consumer_plan ≥10 字指名律）——**selftest 6/6 PASS+live `VERDICT=RAILS-SCHEMA-GREEN violations=0 rows=9`**（mock_order 3 行〔R1 subscription/R2 gacha/R3 b2b_direct〕+batch_card 6 行），证据 `state/rails-schema-20261020-0326.txt`。消费面=环内巡检 C1 簿记零断账（M73 建设案 §三）+批池 validate 前置结构闸（J1-J5 之外的声明式复用层）。
- **parked+理由**：msgspec=重叠判负（重访：轨量 ≥10^4）；beancount=GPL 许可负（参考位·只学不搬）；ops-workflow-hub=健康判负（0★）。
- **下窗指针**：①distr 归因轨（建设案 §七 15 字段）实装时同法加 schema（轨文件尚未落盘）；②月末归集 N1 单的「双分录平衡断言」方法学落地评估（cost_ledger 现为单式·勿在本月窗内改数学面）；③jsonschema 本体引入轮判据已天然满足（已安装+已测），若后续换 venv 隔离则复核 4.x API 稳定性。
- **回执**：本件=M78（PT-20261014-05 补领）交付；实搜面 3 查 ≥2 满足；五门/落点/参考位/判负全留痕；本司反馈面=HQ-FEEDBACK.md 10-20 日清行。

## 结论应用表（research-protocol §结论应用律强制·无表=未交付）

| 候选 | 五门判定 | 落点（改了什么） | 消费面（谁吃产出） | 状态 |
|---|---|---|---|---|
| python-jsonschema/jsonschema（复用面） | 契合✓（四轨声明式结构闸）/反重复✓（集团已采用·BigLife 首例·复用非新采）/许可✓（MIT 原文逐字）/健康✓（4,990★·pushed 当日·issues 1.2%）/成本✓（本机 4.26.0 已装零新依赖） | **已实装**=Tools/rails_schema_check.py（check/selftest/dump）·selftest 6/6+live GREEN rows=9 | 环内巡检 C1 簿记零断账（M73 建设案 §三）·批池 validate 结构层 | **adopted（复用实装）** |
| msgspec | 契合△（快序列化+校验）/反重复✗重叠（与 jsonschema 语义并存=两套真源）/许可✓（BSD-3 原文逐字）/健康✓（4,175★·pushed 当日）/成本✓ | 判负留痕（不装·重访=轨量 ≥10^4 或吞吐瓶颈） | — | **judged-negative（重叠）** |
| beancount/beancount | 契合✓（N1 复式对账语义）/反重复✓/许可**✗GPL-2.0**（COPYING 全文·只学不搬）/健康✓（6,100★·pushed 08-23）/成本✓（零实装） | 参考位记档（月末双分录平衡断言方法学·零代码搬运） | N1 月末归集单设计（10-31 窗） | **参考位（许可负）** |
| ops-workflow-hub | 契合△（术语同构）/反重复✓/许可✓（MIT）/健康**✗**（0★·单人新仓）/成本- | 判负留痕（不入采用面·术语对照=tx_id 幂等已自建） | — | **judged-negative（健康）** |