# 堵/坏/卡点闭环 2026-11-07T23:39:27

分类表：`cph4/fleet/BLOCKER-TAXONOMY-v1.json`（每类四件套：判据/解法/周期/升级轮次）。
本轮命中 5 项 · 已解 2 · 待升级 2

## 需升级（连轮未解）

- CONTRACT-BAD QUEUE/R-SUB-ASSESS-BIGDOMAIN-20261107（连续 3 轮未解）
- CONTRACT-BAD QUEUE/R-SUB-ASSESS-BIGMONEY-20261107（连续 3 轮未解）

## CARD-DEFECT-LOOP（2）

- `fleet-ops/E-UNKNOWN` E-UNKNOWN 类失败 2 次（CHK-CANON-20261106,CHK-RECEIPT-20261106） ✅撤销 5 张反复失败的卡（仅限已死状态）
- `biggame/E-UNKNOWN` E-UNKNOWN 类失败 3 次（SIM-NOCMD-20261107T154454,SIM-DUP-20261107T194456,SI ✅撤销 5 张反复失败的卡（仅限已死状态）

## CONTRACT-BAD（2）

- `QUEUE/R-SUB-ASSESS-BIGDOMAIN-20261107` [SPEC-IMPOSSIBLE] 交付物需人裁判定而 cmd 不产出它 ⇒ 机器队列不可满足 · 待解（第 3 轮）
- `QUEUE/R-SUB-ASSESS-BIGMONEY-20261107` [SPEC-IMPOSSIBLE] 交付物需人裁判定而 cmd 不产出它 ⇒ 机器队列不可满足 · 待解（第 3 轮）

## FAKE-RED（1）

- `remote:bigcompute` BigCompute·硅基算力 的产物面在子仓（bm-a、bm-b、bm-c），本机不可判；最后一次可得证据已停 102 小时 · 待解（第 3 轮）

---
_自动解只做确定性动作；解不了的按轮次升级，不许静默留着_
