# bm-c 生产自省 · 2026-11-25 05:07

## 一、面

| 项 | 值 |
|---|---|
| 银行总活 | 12 |
| 状态分布 | {"done": 1, "blocked": 11} |
| 已完成 | 1 |
| 判死 | 11 |

## 二、指标

- 单集耗时（已完成 1 集）：均值 4.8 分钟，明细 PROD-DRAMA-EP002=4.8
- 24h 理论产能（单机）：约 300.0 集/天（按均值，不含让路窗）

## 三、失败聚类（近全量台账）

- `no-deliverable` × 44
- `fail:kf` × 18
- `fail:kf,assembly,qc` × 4
- `gate-fail:cph4/fleet/out/drama/EP005/ep005-gate.json=FAIL` × 4
- `gate-fail:cph4/fleet/out/drama/EP003/ep003-gate.json=None` × 4
- `gate-fail:cph4/fleet/out/drama/EP004/ep004-gate.json=None` × 4
- `gate-fail:cph4/fleet/out/drama/EP005/ep005-gate.json=None` × 4
- `gate-fail:cph4/fleet/out/drama/EP006/ep006-gate.json=None` × 4
- `gate-fail:cph4/fleet/out/drama/EP007/ep007-gate.json=None` × 4
- `gate-fail:cph4/fleet/out/drama/EP008/ep008-gate.json=None` × 4
- `gate-fail:cph4/fleet/out/drama/EP003/ep003-gate.json=FAIL` × 3
- `gate-fail:cph4/fleet/out/drama/EP004/ep004-gate.json=FAIL` × 3
- `gate-fail:cph4/fleet/out/drama/EP006/ep006-gate.json=FAIL` × 3
- `gate-fail:cph4/fleet/out/drama/EP007/ep007-gate.json=FAIL` × 3
- `gate-fail:cph4/fleet/out/drama/EP008/ep008-gate.json=FAIL` × 3
- `fail:assembly,qc` × 1
- `fail:kf,i2v,qc` × 1

## 四、迭代建议（建议，不是法）

1. **重复「无产物」** ≥2 次 → 先查 SKIP 判据与旧件归档（10-24 判例：旧帧不归档=命令秒过零产出）。
2. **闸失败** → 病灶多半在提示词层（否定句/场景词/伪文字），走 `drama_prompt_critic.py` 先筛再烧。

## 五、下一步（自动）

- 本报告只落档；**判死件需人工或主控裁定**（禁自动放宽闸）。
- 重试梯已在 finalize 内（≤3 次自动重排）。
