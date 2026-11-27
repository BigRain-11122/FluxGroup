# R-20261028-decision-round-25 — 集团决策委员会第 25 轮（2026-10-28 00:00 班）

> 轮次预算 20 分钟；落账指针=docs/decisions.md D-20261028-01~04；复盘行=cph4/reflection-journal.md 第 25 轮行。

## 一、收取面（五司＋集团面）

| 面 | 实况 | 结论 |
|---|---|---|
| quant/bigmoney | F-20261027-01（P0 CODELY.md 损坏）／F-20261027-02（P1 machine-health 结构损坏） | 前者已 by D-20261027-08 修复（本班实测 45,543B／LF 84／PUA 0）；后者在役→D-20261028-02 |
| life/BigLife | 10-27 日清 open=0（R2282/R2293） | no-op |
| gaming/FluxVerse | F-20261027-01（回执 D-20261026-20 已复产）／F-20261027-02（P1 镜像组根陈旧） | 前者回执；后者→D-20261028-04 |
| media/BigStream | HQ-FEEDBACK 末行 10-24（D-20261027-13 死线 10-28 12:00 未到）；生产面在飞 | no-op（不重派） |
| gaming/MiniGame | 无 HQ-FEEDBACK；STATUS.md 尾行 22:07（X2903 产品轮）＝D-20261027-10 双面口径判活 | no-op |
| 集团面 | evolution-ledger open：P-2026-10-25-02/03/04/07（已由 D-20261027-03/04/05 承接）／P-2026-10-25-06（CLOUD-OFF，transferred 未落地） | 仅 P-25-06 仍有实体缺口→D-20261028-03 |

## 二、本轮四处硬证据（均本班实测）

1. **删树修复回滚了分卷**：ceebc703（22:31）删 3494 件；0aa00453（22:34）补 3494 件、`missing=0`（树完整性 OK）。但 orders.md blob：ccd517f1=231,786B → 0aa00453=392,479B（+160,693B），archive 恒 992,318B → 恢复源取了删除前的陈旧快照，把分卷已迁出的行灌回主档。
2. **machine-health 结构损坏**：`quant/bigmoney/fleet/machine-health.json` 3,922B，`json.load` 返回 list，`{"value":[...]}` 嵌套 ≥4 层；消费面 `monitor/build_status.py` 取不到机器键；写入侧每 2h 仍在写。
3. **CLOUD-OFF 闸门**：`Tools/cloud-off-gate.ps1`／`cph4/cloud_off_gate.ps1` 双缺；唯一实现 `media/BigStream/src/os/cloud_off_gate.ps1`（1,720B）；八脚本 gate 判定 8/8 在、`rev-parse` 顶层解析 0/8。D-20261024-13 与 D-20261026-21 两度逾期=第 3 次。
4. **镜像组根**：D:\FluxGroup 台账 10-20/235 行 vs 活树 10-27/373 行；decisions 212 vs 367、orders 366 vs 405。FluxVerse 已自修并实证假触发 3 枚/轮。

## 三、思考与研判

- 四项同属「感知面失真」族：删树恢复、健康面、成本闸、组根解析——共同后果是**系统对着旧世界报绿**。故本轮判据统一为「可机械验真」：字节级去重、JSON 解析断言、三例自测、双面行数比对。
- 司级收益与集团收益无冲突：四项修复成本均 <1 人时，收益覆盖全部五司与成本闸。
- 未做外部调研：四项均为内部可机械证伪的工程缺陷，无业界实践不确定项（非设计决策），故不引外部依据。

## 四、拍板与传导

| 决策 | owner | 承诺时点 | 逾期动作 |
|---|---|---|---|
| D-20261028-01 恢复源规约＋orders 去重 | @HQ 秘书处 | 10-28 02:30 | 夜轮 03:07 点名 |
| D-20261028-02 machine-health 规范态 | @BigMoney | 10-28 12:00 | 夜轮点名计考核 |
| D-20261028-03 CLOUD-OFF helper 落地 | @HQ 工具域 | 10-28 12:00 | 夜轮点名 |
| D-20261028-04 组根解析律四司自查 | @MiniGame/@BigMoney/@BigStream/@BigLife | 10-31 00:00 | 夜轮点名 |

## 五、复盘四问

1. **当日拍板实况**：4 行全 dispatched；ceo-pending 0／escalated 0／overruled 复扫 0；无 CEO 翻案/否决注成本。
2. **chronic 扫描**：BigStream 反馈面死线未到点（no-op）；MiniGame 走 STATUS 双面口径（活）；quant/FluxVerse/BigLife 在途；只审不处=违例 0。
3. **反思行消费**：读值守轮 21:07 行——「OSS 收获九实体全线停摆（169h~682h）＋外审班停摆」判为机制无役；本轮不立法（立法归周轮），路由 11-01 周轮建「缺席即自动补位领受体」议程。15:07 班无独立反思行（仅水位行），如实标注。
4. **迭代核销**：昨日 2 项——「分卷后热窗体量回归」本轮实锤（修复回滚）；「dangling decision ref 探针」待夜轮接线。新增 2 项：恢复源规约（已随 D-01 生效）、组根解析律（已随 D-04 生效）。