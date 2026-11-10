# 挂起线处置台账（2026-11-10 23:40）

> 口径：每条超 72h 无产物的线，当天必须二选一：出最小可验收物（记产物路径），或判死/阻塞（记死因）。
> CEO 令暂停的线（PARKED）不计入停血；`COMMAND-BOARD` 已按此修正统计口径。

| 线 | 声明 | 产出年龄 | 处置 | 依据 |
|---|---|---|---|---|
| fluxverse | ACTIVE | 176.5h | **PRODUCE** | 派 `PRODUCE-FLUXVERSE-20261110`，产物 `cph4/fleet/reports/fluxverse-city-state-20261110.md`（12 面现状一页） |
| biggame | ACTIVE | 174.2h | **PRODUCE（已交）** | `cph4/fleet/reports/submit-pack-20261110.json`（23:20，36 款/可提交 1/缺件明细） |
| recon | ACTIVE | 82.9h | **PRODUCE** | 派 `PRODUCE-RECON-20261110`，产物 `cph4/fleet/reports/market-brief-20261110.md` |
| bigmoney | ACTIVE | 155.5h | **BLOCKED** | 回测/信号产物必须生成在 `quant/bigmoney`（bm-b 持有）；bm-b 当前 git 锁死（B-ENV），主控不可代跑 |
| bigdomain | ACTIVE | 174.1h | **BLOCKED（物理件）** | 商户号/支付资质未签（CEO 域）；前置件做完前无产品可交 |
| bigcompute | ACTIVE | 174.1h | **BLOCKED（物理件）** | bm-d 未入网/未装系统（需现场）；无算力可跑 |
| bigstream-duanju / shortvideo / drama / car-gaming / bighouse | PARKED | — | **不计停血** | CEO 2026-11-03 令：暂停，先铺底层资产库；恢复需 CEO 一句话 |

## 下一轮复核点
- fluxverse / recon 两张 produce 卡是否落盘（有产物即改 PRODUCE-DONE，无产物 48h 内改 DEAD）
- bm-b 清锁后 bigmoney 是否恢复（清锁是唯一人工步骤）
