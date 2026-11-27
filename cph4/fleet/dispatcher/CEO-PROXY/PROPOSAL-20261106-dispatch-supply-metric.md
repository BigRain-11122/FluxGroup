# 提案：调度供给口径改读生产队列（受保护件，待 CEO 令）

- 提出：CEO-PROXY 事件班 2026-11-06 02:46-03:0x
- 对象：`Tools/fleet-dispatcher.ps1`（BLUEPRINT §九 受保护四件之一）——**本席未改，只提方案**

## 问题（实测）

`fleet-dispatcher.ps1` 判定「某 lane 是否有活」时只统计 `cph4/fleet/dispatcher/POOL.json`
的 open 卡（`$open/$exec`）。自 POOL-0024 之后 POOL 再无新卡，唯一 open 件是 POOL-0010
（被 `CEO-PHYSICAL:submit-materials` 锁死）。而真实工作在 `cph4/fleet/PRODUCTION-QUEUE.jsonl`
（本轮实测 OPEN 22 → 清理后 4，RUNNING 3）。

后果：`STARVED-EXEC` 每 10 分钟对三台机各报一次，2026-11-05 00:20、11-05 02:5x、
11-06 00:20 三个班次都只能用文字解释它是「结构性假红」。而本轮真正的原因（19 张卡的 cmd
指向不存在的根、raw 从未落地）恰好被这条常红噪音盖住。

## 建议改法（最小面）

1. `$exec[$lane]` 改为双源：POOL 可执行卡 **+** PRODUCTION-QUEUE 中
   `state=OPEN` 且 `nodes|hard_nodes` 含该 lane、`needs` 与该 lane 能力匹配的行数。
2. `SUPPLY-DRY` 只在「两源皆 0」时发；`STARVED-EXEC` 附 `pool=x queue=y` 明细。
3. 新增 `FLAG CARD-DEFECT` 行：队列中存在 `queue_card_audit.py` 判为缺陷的行时，直接报
   缺陷卡号（本轮 19 张即属此类），把「有卡但跑不了」与「根本没卡」分开报。

## 判据

- 上线后连续 3 个班次 `STARVED-EXEC` 不再对三机全报，且任一班次出现 SUPPLY-DRY 时
  都能给出「两源皆 0」的证据。
- 反例保留：把一张 cmd 指向 `C:/nonexistent/` 的卡放回队列，须报 `CARD-DEFECT` 而非
  `STARVED-EXEC`。

## 需要的授权

受保护件改动 = CEO 令唯定谳（ROUND 步9 / BLUEPRINT §九）。获批后由 master 席实施，
本席不自行落地。

## 复发实锚（第 4 次·2026-11-10 01:2x 事件班）

- 触发：00:21 / 00:51 / 01:01 / 01:21 四连 `STARVED-EXEC lane=bm-b|
  bm-c open_cards=0`。
- 本轮证据（比 11-06 更硬，可复算）：
  - `cph4/fleet/dispatcher/POOL.json` 中 lane=bm-b 的 9 张卡状态为
    done×6 / closed-stale×2 / closed-parked×1 → **open=0 是事实**，旗标没算错 POOL。
  - 同刻 `origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl` 有 **OPEN 卡
    `R-NEXT-BIGSTREAMD-EVIDENCE-20261110`，nodes=[bm-b]、owner=bm-b、needs=cpu**。
  - bm-b `/status` 自述本轮在跑：`cyc_round=1590`、`card=E627 done`、
    `pool carried 3 ready cards`、`agenda_starved=false`、`ram_free_gb=8.1`。
    → 机器在干活，旗标说它没活：**结构性假红成立**。
- 结论：提案不需要改法，只需要 CEO 令放行第 1 条（`$exec` 双源）。第 4 次复发
  已证明「文字解释」不能替代改口径。