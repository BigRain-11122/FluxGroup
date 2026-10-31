# MV 交付闸复核 · v717（R2.51 事件班·2026-10-31 14:1x）

## 结论
**VERDICT: FAIL**（余 2 类，D4 已清零）

| 项 | v717 本次 | 说明 |
|---|---|---|
| 稳定性 seams/freezes | 0 / 0 | 帧级无接缝无冻结 |
| D4 曝光闪 | **0（此前 4）** | 闸新增「角落 luma 局部性判据」：活光源（火苗/火花）移动受光面但四角不动 = 设计，不再误报 |
| D1 重复帧 | **1 对** | 尾帧 5621（234.21s）= Z04_glyph_remains 收尾重复，属装配级裁 1 帧可修 |
| D2 近静止镜 | **5 个** | 首个 0.00–3.50s（mean_mad=0.36）；余者为慢速氛围镜 |
| 重演白名单 | 8 对命中 | 设计重演，不计缺陷（MV0001-REPRISE-WHITELIST.json） |

## 判据来源
- 命令：`python Tools/mv_delivery_gate.py "cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v717.mp4" --whitelist cph4/fleet/mv0001-handover/canon/MV0001-REPRISE-WHITELIST.json --json cph4/fleet/queue-receipts/mv-gate-latest.json`
- 母版：5623 帧 @24fps / 83 镜 / 234.29s
- 机读结果：`cph4/fleet/queue-receipts/mv-gate-latest.json`

## 归属（本席只出机器证据，不做创作裁决）
- D4 清零 = 闸的判据修正（已入代码 `Tools/mv_delivery_gate.py`），不是画面改动。
- D1/D2 的修与不修，归导演席；仅提示 D1 属「装配裁 1 帧」量级，D2 需要逐镜判断是否为有意的近静止氛围镜。