# LOST-CARDS — 队列卡被抹台账（append-only·人读面）

> 立件 2026-11-08 01:0x（CEO-PROXY 事件班·承载件触发）。
> 本文件**不在** `state_push.py` 的 STATE_FILES 白名单里，因此不会被每 1–2 分钟的状态同步覆盖；
> 用来记录「投进 origin 队列、随后被写手抹掉」的卡，避免损失只出现在别人看不见的日志里。

## 一、机理（已定位·已修·未生效）

`Tools/fleet/state_push.py` 的 `sync_into_worktree()` 原本把**主工作树的本地副本整文件拷进隔离工作树**再提交推送。
主工作树那份是「上一次同步时」的快照，于是 **origin 上由别窗 append 的新卡会被整文件覆盖**。

- 覆盖证据（首例）：`RESCUE-FREEMEM-BM-C-20261108` 由 00:45 窗随 `ce524cf21` 推 origin，
  在 `f1246e864 → 9c1e58012` 的同步里被删（`git diff --numstat` = **15 增 / 15 删**，删侧首行即该卡）。
- 复现 3 次：`ce524cf21` → 抹；`4aec20ac2` → 抹（`702afaccd` 00:58）；`ee9639199`（01:01 推 + 立即 poke）→ 100 秒内被 `ffb3d208c` 抹。
- 机制量化（近 60 提交中 18 次 `state: 队列/回执同步`）：
  **丢失卡 id 2 个** —— `RESCUE-FREEMEM-BM-C-20261108`（5 次）、`CANARY-20261108T005026`（1 次，
  由兄弟窗专门下的探针卡）。
  即：损失面＝「bm-m 上次同步之后别人新加的卡」，对派单路径就是「刚派的活凭空消失」。

## 二、修法（已上链）

- 提交 `4aec20ac2`：`sync_into_worktree()` 对 `PRODUCTION-QUEUE.jsonl` / `PRODUCTION-BACKLOG.jsonl`
  改为 **origin ∪ 本地，按卡 id 合并**；同一 id 时**终态优先**（DONE/CANCELLED/FAILED/UNVERIFIED/BLOCKED
  胜 OPEN/RUNNING），平手取本地；**行字节不重新编码**（防止 GBK/混合编码的队列被转码损坏）。
- 自证（用真实 blob 复算，不是口头声明）：
  `merge(80a2bf064 的队列, 5023fd112 的本地)` → 卡在、`lost_ids=0`、`dup=0`；
  首轮自测 `1385 origin id + 1 = 1386`。

## 三、为什么修了还会丢（关键·未解）

`state_push.py` 的 `ensure_worktree()` / `git reset --hard origin/main` **只作用于隔离工作树
`.fluxgroup-state-wt`**；脚本本体执行的却是 **ROOT 工作树里的那份 `Tools/fleet/state_push.py`**。
bm-m 的 ROOT 工作树分叉/脏，不前进 ⇒ 进程永远加载旧代码 ⇒ 继续整文件覆盖。

决定性证据：`git merge-base --is-ancestor 4aec20ac2 702afaccd` = **是**
（即 00:58 那次同步的父链里已经有修法提交），但它仍然抹了卡 ⇒ 拿到提交≠跑新代码。

## 四、解闸（bm-m 本机一次·本席无远程执行通道）

```
cd <FluxGroup 根> && git fetch origin && git reset --mixed origin/main && git status
```

- 允许保留未提交业务文件（`--mixed` 不动工作区）。
- 收口后下一次 `state_push` 即走合并逻辑；验收＝一张新 append 的卡在 origin 存活 ≥10 分钟。
- 若 ROOT 有本地独有提交，先判是否含业务产物，再决定 rebase 或保留（禁 `--hard`）。

## 五、本席纪律（已执行）

- 同一张卡 **不再第三次以上重投**：1 小时内 3 次投放全被抹，继续投＝无效 churn。
- `RESCUE-FREEMEM-BM-C-20261108` 的去留：**非阻断**——bm-c 现 `ram_free` 2.1–2.5G，
  且 00:50 起已在跑 `asset-lib-char-gen-2026-11-07`；RAM 再破闸才重立，重立必须等解闸之后。
- 回访探针：一次性 durable cron `6636da00-2fbc-42af-b05c-f4565326dd57`（2026-11-08 02:36），
  复探本文件四条：①同步提交是否仍成批删行 ②`origin/main:Tools/fleet/state_push.py` 是否含 `merge_jsonl`
  ③新 append 卡存活时长 ④两机 `/health`（90s 超时）。

## 六、同族历史（为什么这次能一次定到根上）

R11-7（双源分叉）、R12-1（队列结构性损毁）、R14-7（append 卡被覆盖）、R9-2（未提交台账被 auto-sync 覆盖）
——此前都记成「同步把台账冲了」，但没有一处指到 `state_push.py` 的**整文件覆盖**这一行逻辑。
本次用「同一张卡三次复现 + 版本对照（祖先关系证明拿到新码仍丢）」把责任定死。
