---
name: cost-ledger
status: parked   # CEO 2026-11-03：钱的事往后放，先做底层与研发
description: 成本与单位经济席。Use when computing what a deliverable actually cost, judging unit economics per episode/piece/order, auditing cloud credit spend, deciding whether a line is worth running, or answering "这单赚不赚". Triggers on 成本/机时/积分/单位经济/毛利/亏/报价底线/云端花费/credits.
---

# 成本与单位经济席

正典深度位：运营指标=`Tools/fleet/ops_metrics.py`（产出/回执/队列三项）｜云端纪律=`cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md` 头部（云可用但非必要不云；全队云并行 <8；单项 >500 积分须 CEO 确认）｜配方单位经济=`cph4/fleet/products/*.yaml`。本件只收高频硬律。

## 硬律速查（违例即返工族）

1. **分子只算入库产出**：成本除以"已登记 artifact 的交付物"。回执数、卡数、跑了多少轮都不进分子——拿过程当产出算单位经济，算出来的数必然好看且假。
2. **四栏记账，缺栏即不合格**：机器机时（本地折算/不计现金）｜云端 credits（真现金）｜素材与授权（含字体/音乐/肖像）｜外部采购（CEO 物理件，只记不批）。
3. **按交付单位算，不按项目算**：短剧=元/集，MV=元/条，游戏=元/可玩包，策略=元/份结论。项目级总额无法指导任何决策。
4. **云端花钱只有两类正当**：本地画像不匹配（重 GPU/超内存）与"等本地会拖过交付期"。其余一律回本地排队，不为满负荷上云。
5. **失败不计入成本，但计入浪费**：失败任务不花钱（生成只按成功计费），但要单独记浪费工时——它决定下一版要不要换做法。
6. **成本数字必须带时间戳与口径**：写出"机时按夜窗折算/是否含办公占用"，否则两次报表不可比。

## 一次核算的标准动作

```
1. 取交付物清单（vault / artifact 登记，不是回执）
2. 取该批云端 credits 消耗（events/model.jsonl 或网关审计）
3. 取机时（lane 上报的 seconds，按机器分）
4. 相除得单位成本，附三行口径声明
```

## 判断线要不要继续跑（三条停线判据）

```
1. 单位成本 > 同类市场价 60% → 换做法，不换人手
2. 连续 3 批单位成本不降 → 工艺没进步，停线复盘
3. 该线 30 天现金收入 0 且配方 kill_criteria 已触发 → 按配方停，不解释
```

## 工具速查
`Tools/fleet/ops_metrics.py`（产出/回执/队列）｜`Tools/fleet/ship_ledger.py`（发布与收入台账）｜`cph4/fleet/market/`（对标价格带）。