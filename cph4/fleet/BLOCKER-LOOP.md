# 堵/坏/卡点闭环 2026-11-14T23:43:30

分类表：`cph4/fleet/BLOCKER-TAXONOMY-v1.json`（每类四件套：判据/解法/周期/升级轮次）。
本轮命中 126 项 · 已解 124 · 待升级 0 · 未到周期跳过 0 类

## DECL-UNDISPATCHED（2）

- `bigstream-mv` 声明 rebuild 但无在飞卡 ✅night_plan rc=0 [night_plan] cards=0 waiting=0 已投v
- `fluxverse` 声明 city-state 但无在飞卡 ✅night_plan rc=0 [night_plan] cards=0 waiting=0 已投v

## CONTRACT-BAD（1）

- `BACKLOG/CHK-RECEIPT-20261105` [OUT-MISMATCH] cmd 产出的路径与卡的 deliverable 不同 ⇒ 永远 FAIL 重试 · 待解（第 1 轮）

## SYNC-BEHIND（1）

- `ahead1` 本地领先 origin 1 个提交 ✅state_push rc=0 [state-push] 无状态变化（2071 个文件已同步）

## STAGE-STALE（98）

- `hb` 阶段超期未真跑 ✅hb rc=0 HB bm-m seq=12038 offset=648.9ms
- `artifact_push` 阶段超期未真跑 ✅hb rc=0 HB bm-m seq=12038 offset=648.9ms
- `executor_guard` 阶段超期未真跑 ✅hb rc=0 HB bm-m seq=12038 offset=648.9ms
- `night_plan` 阶段超期未真跑 ✅hb rc=0 HB bm-m seq=12038 offset=648.9ms
- `market` 阶段超期未真跑 ✅hb rc=0 HB bm-m seq=12038 offset=648.9ms
- `quality` 阶段超期未真跑 ✅hb rc=0 HB bm-m seq=12038 offset=648.9ms

## FAKE-RED（2）

- `remote:bigdomain` BigDomain·硅基域商业化 的产物面在子仓（bm-a、bm-b、bm-c），本机不可判；最后一次可得证据已停 185 小时 ✅已定性为不需行动（2 项），不重复报
- `remote:bigcompute` BigCompute·硅基算力 的产物面在子仓（bm-a、bm-b、bm-c），本机不可判；最后一次可得证据已停 185 小时 ✅已定性为不需行动（2 项），不重复报

## QUEUE-DRIFT（12）

- `R-PLAN-BIGGAME-20261114` 队列=RUNNING 备队列=READY ✅对齐 12 行
- `R-PLAN-RECON-20261114` 队列=CANCELLED 备队列=READY ✅对齐 12 行
- `bigmoney-backtest-2026-11-14` 队列=RUNNING 备队列=READY ✅对齐 12 行
- `bigstream-mv-gate-2026-11-14` 队列=RUNNING 备队列=READY ✅对齐 12 行
- `R-PLAN-FLUXVERSE-20261114` 队列=OPEN 备队列=READY ✅对齐 12 行
- `biggame-pack-scan-2026-11-14` 队列=RUNNING 备队列=READY ✅对齐 12 行

## CARD-UNOWNED（7）

- `R-PLAN-FLUXVERSE-20261114` 无 owner ✅定责 7 张
- `R-NEXT-BIGSTREAMD-TTS-QC-20261114` 无 owner ✅定责 7 张
- `CHK-LIB-20261111` 无 owner ✅定责 7 张
- `LINE-TRIAGE-MV-20261114` 无 owner ✅定责 7 张
- `CHK-RECEIPT-20261105` 无 owner ✅定责 7 张
- `R-TRIAGE-BIGSTREAMMV-BMM-20261114` 无 owner ✅定责 7 张

## QUALITY-BELOW（1）

- `关键帧 / 美术图（图像类）` | 关键帧 / 美术图（图像类） | 0.67 | FAIL | 1.00 | 退步 33% | · 待解（第 1 轮）

## VOLUME-MISSING（1）

- `移动硬盘` 台账有引用但卷未挂载 ✅vault rebuild rc=0 重建 0 条（已可达跳过 643，历史快照 8，无法重建 0）

## NODE-REPO-DIVERGED（1）

- `bm-a` bm-a 仓库已分叉（head 1adb1ee03 非 origin/main 祖先），/poke 只会假受理，新卡与产出归集到不了；解=在 ✅已定性为不需行动（1 项），不重复报

---
_自动解只做确定性动作；解不了的按轮次升级，不许静默留着_
