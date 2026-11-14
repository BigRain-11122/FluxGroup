# 堵/坏/卡点闭环 2026-11-15T01:42:08

分类表：`cph4/fleet/BLOCKER-TAXONOMY-v1.json`（每类四件套：判据/解法/周期/升级轮次）。
本轮命中 72 项 · 已解 71 · 待升级 0 · 未到周期跳过 1 类

## SUPPLY-SHORT（1）

- `lanes-2` 2 台空转（bm-b,bm-c），待派卡只有 6 张 ✅night_fill.py rc=0 队列已有 6 张待领，够用，不灌

## DECL-UNDISPATCHED（3）

- `bigstream-mv` 声明 rebuild 但无在飞卡 ✅night_plan rc=0 [night_plan] cards=4 waiting=0 已投v
- `biggame` 声明 submit-pack 但无在飞卡 ✅night_plan rc=0 [night_plan] cards=4 waiting=0 已投v
- `fluxverse` 声明 city-state 但无在飞卡 ✅night_plan rc=0 [night_plan] cards=4 waiting=0 已投v

## CARD-DEFECT-LOOP（2）

- `-/E-UNKNOWN` E-UNKNOWN 类失败 2 次（SD-visual-D02-FLUXVERSE-EVENT-SUPPLY-20261114,R-MODE ✅撤销 4 张反复失败的卡（仅限已死状态）
- `bigstream-mv/E-UNKNOWN` E-UNKNOWN 类失败 2 次（bigstream-mv-gate-2026-11-15,R-NEXT-BIGSTREAMM-REBUI ✅撤销 4 张反复失败的卡（仅限已死状态）

## STAGE-STALE（53）

- `executor_guard` 阶段超期未真跑 ✅executor_guard rc=0   bm-c   unreachable
- `market` 阶段超期未真跑 ✅executor_guard rc=0   bm-c   unreachable
- `quality` 阶段超期未真跑 ✅executor_guard rc=0   bm-c   unreachable
- `ossradar` 阶段超期未真跑 ✅executor_guard rc=0   bm-c   unreachable
- `inventory` 阶段超期未真跑 ✅executor_guard rc=0   bm-c   unreachable
- `census` 阶段超期未真跑 ✅executor_guard rc=0   bm-c   unreachable

## FAKE-RED（2）

- `remote:bigmoney` BigMoney·量化 的产物面在子仓（bm-a、bm-b、bm-c、bm-d），本机不可判；最后一次可得证据已停 253 小时 ✅已定性为不需行动（2 项），不重复报
- `remote:bigdomain` BigDomain·硅基域商业化 的产物面在子仓（bm-a、bm-b、bm-c），本机不可判；最后一次可得证据已停 272 小时 ✅已定性为不需行动（2 项），不重复报

## QUEUE-DRIFT（7）

- `R-PLAN-RECON-20261115` 队列=CANCELLED 备队列=READY ✅对齐 7 行
- `R-PLAN-BIGDOMAIN-20261115` 队列=CANCELLED 备队列=READY ✅对齐 7 行
- `bigstream-mv-gate-2026-11-15` 队列=CANCELLED 备队列=FAILED ✅对齐 7 行
- `R-NEXT-BIGSTREAMM-REBUILD-20261115` 队列=CANCELLED 备队列=RUNNING ✅对齐 7 行
- `asset-lib-voice-corpus-2026-11-14` 队列=FAILED 备队列=RUNNING ✅对齐 7 行
- `R-PLAN-FLUXVERSE-20261115` 队列=DUP-SKIP 备队列=READY ✅对齐 7 行

## ARTIFACT-MISSING（1）

- `asset-lib-voice-corpus-2026-11-15` 交付物不在盘：cph4/fleet/queue-receipts/voice-corpus-2026-11-15.json ✅重开 1 张假完成卡

## UNVERIFIED-STUCK（1）

- `asset-lib-voice-corpus-2026-11-15` 回执未对上 ✅receipt_match rc=0 [receipt-match] 可收口 0 张｜歧义 0｜证据

## QUALITY-BELOW（1）

- `关键帧 / 美术图（图像类）` | 关键帧 / 美术图（图像类） | 0.67 | FAIL | 1.00 | 退步 33% | · 待解（第 3 轮）

## NODE-REPO-DIVERGED（1）

- `bm-a` bm-a 仓库已分叉（head ed691030d 非 origin/main 祖先），/poke 只会假受理，新卡与产出归集到不了；解=在 ✅已定性为不需行动（1 项），不重复报

---
_自动解只做确定性动作；解不了的按轮次升级，不许静默留着_
