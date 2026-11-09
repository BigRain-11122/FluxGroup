# 2026-11-08 夜：把「满负荷」从假象改成真的（四处根因 + 复发纪律）

CEO 令：「我睡觉了 你保证智能体和机队满负荷工作」。进场时账面 22–27 张在飞，
实际只有主控一台在跑、且大量卡永久卡死。四处根因与处置：

## 1. lane_agent 的 `_run_one_job` 定义第二次被顶掉（复发）
- 症状：并行槽位分支 `LANE-SLOTS` 打印后立刻 `NameError: name '_run_one_job' is not defined`，
  卡被标 RUNNING 但永不执行 → 实测堆积 18 张，机器静默空转。
- 根因：并行分支的**调用点**在主干上，而函数**定义**是另一个提交加的，被 `checkout --theirs`
  式合并顶掉；`laye_agent` 单卡路径 `run_job()` 正常，所以只有多槽机器受影响。
- 处置：把定义补回 `run_lane_cycle` 内（步序 RUNNING→run_job→RESULT，与单卡一致）。
  实测一轮 6 张并行、5 张真出产物。
- **纪律**：定义与调用点必须同一提交；本类缺陷目前**没有回归断言**（RG 未覆盖），
  下次改 lane_agent 应补一条"并行分支引用的每个名字都存在"（AST 级检查即可）。

## 2. `keep_alive=0` 被 Python 假值吞掉（两个方向同时错）
- `budget.resident_set` 只含 resident+embedding，但 `LOCAL-MODEL-POLICY.duties` 与
  `MODEL-MONITOR-MATRIX-v2.tiers` 两处都写 `keep_alive: "1m"` → `model_plan` 每轮 E-KEEPALIVE，
  且 1.7B/8B 实际被钉在内存里。
- 网关侧还有第二层坑：`str(cfg.get("keep_alive") or "5m")` 会把**数字 0 变成 5m**，
  于是"策略写 0"这个合法意图被静默改成相反行为。
- 处置：两处数据同时改 `0`；网关改为 `_ka = "0" if _ka in (0, "0") else ...`。
- **纪律**：读配置里可能为 0/False 的字段一律用 `is None` 判缺省，不要用 `or`。

## 3. 队列被 git 冲突标记污染并提交进历史
- 症状：`PRODUCTION-QUEUE.jsonl` 有 138 个 `<<<<<<< HEAD / ======= / >>>>>>>` 块（414 行非 JSON），
  `PRODUCTION-BACKLOG.jsonl` 20 块。容错解析的脚本照跑，**严格 JSON 解析的路径静默崩**，
  所以长期无人发现。
- 根因：`job(<id>): artifact` 类提交**整份覆盖**队列文件，出提交那一侧的工作树里还留着未解决的冲突。
- 处置：新增 `Tools/fleet/queue_sanitize.py`（`--check`/`--fix`）：冲突块取**两侧并集**、
  按 id 去重（保留文件中最后出现的一行）、每处状态冲突写审计报告；两份队列已清、卡数不变。
  新增 RG-30（禁冲突标记 + 清洗器负控：认出→并集修复→不丢卡）。
- **纪律**：任何"整文件覆盖"共享状态的提交都是污染通道；队列/台账类文件只许按键合并。

## 4. 审计卡把 `nodes` 与 `hard_nodes` 都钉死成 `["bm-m"]`
- 症状：17 张纯 CPU 的软著/提审审计卡全压主控（CEO 硬边界=主控不做生产），
  而 bm-a/bm-c 空转；账面 19 张在飞其实一台在干。
- 根因：`supply_batch.build_cards()` 里两类卡都硬编码 `["bm-m"]`，且 `hard_nodes` 拦掉了
  跨机回落（配置里 `allow_cross_node_fallback: true` 等于没生效）。
- 处置：新增 `prod_nodes()`，从 `AUTONOMY-CONFIG.supply.slots_per_node` 取非主控机轮转，
  去掉 `hard_nodes`；实测 16 张铺成 bm-a/bm-b/bm-c/bm-d 各 4。
- **纪律**：卡上的 `hard_nodes` 只在**真依赖本机硬件/本地盘**时才写；
  依赖随 git 分发的（材料目录、清单 JSON）都不许钉机器。

## 修复后的实测口径
- 回归 30/30 PASS；`PULSE.json` blockers=[]；在飞从 bm-m 独干变为五台分摊。
- bm-m 两分钟消化 14 张（17→3），这是"并行真在跑"的可核验证据。
- 三台 FleetLink 1.9.7 `health=200`、`HQ-ProductionClaim` 均 WAKE；poke 后 bm-a/bm-c 开始领卡。
- 夜间值守记录：`cph4/fleet/NIGHT-WATCH-20261108.md`。

## 诚实边界（不算做到）
- 供给是真瓶颈：能铺的真活已幂等铺完，OPEN 常年 2–5 张；再铺就是造假活。
- bm-d 自 2026-11-06 17:48 无心跳，tailnet 查不到该机。
- 三条子仓线（bigdomain/bigcompute/bigmoney）仍无"第一件真产物"定义，属方向决策。

## 5. 上午复盘：读数面错位 + 停摆工作者（第 17 类堵点）

### A. 读数面：队列是活文件，单次读本地必然骗人
- 同一时刻本地工作树 `RUNNING=26`、`origin/main` 只有 `5`；**执行机读的是 origin 快照**。
- 用本地文件统计 → 报"在飞 26 张"是假绿，报"空转"是假红（当晚两件都干过）。
- 正法：所有"多少在飞/待派"一律从 `git show origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl` 读，
  并至少两次采样看趋势。`fleet_status.py` 已加 `rows_origin()`，输出标 `[fleet-status/origin]`，
  origin 读不到才回落本地并标 `local`。

### B. STALLED-WORKER（新增第 17 类，四件套齐全）
- 实锚：bm-a 自 03:15 起零产出，但**仍在认领卡**（能连、能领、就是不执行）；
  卡挂到名下即 `RUNNING`，别的机器 claim 看不见 → 4 张卡锁死 7 小时。
- 判据：该机最后真产出距今 > `CARD-POLICY.stall.no_output_hours`（缺省 6h），
  且名下有"认领超过 5 分钟仍无产出"的卡。
- 解法：退回 `OPEN` + 清 `owner` + `nodes` 改派其他在线机 + 写 `release_reason`（可逆）。
- 护栏：5 分钟内新领的不动；已完成/已改状态不覆盖；无回执档案的机器不在此判。
- 实测：释放 2 张，90 秒后 origin 显示 bm-b 接手；全轮 `命中 14 / 已解 13 / 升级 1`。
- **教训：只报不修的红最危险**——`fleet_status` 早已报 `STALE 7.3h + 4 张死卡`，
  但没有动作，红屏过一整夜。报红处必须同时回答"谁来修、怎么修"。

### C. 机器名解析：只切最后一个 "-" 会得到 "a"
- 回执名形如 `AUD-GAME-…-bm-a.json`；`rsplit("-",1)[-1]` = `a` ≠ `bm-a` → 停摆检测静默失效（命中恒 0）。
- 正法：`"-".join(b.rsplit("-",2)[-2:])`，抽成 `_node_of()` 并进 RG-31 负控。

### D. 断言面扩到 32 条
- `RG-31`：停摆卡必须能释放改派；不许误伤新鲜在飞卡与已完成卡；全新鲜时不许命中；机器名解析须完整。
- `RG-32`：`lane_agent` 并行分支的 `_run_one_job` 必须真有定义且在 `run_lane_cycle` 作用域内（AST），防第三次复发。

## 6. 赋能通电：830 次被拒的真因是"没人送钥匙"

- 事实：网关 8792 当天 835 次调用，**成功 6 次、被拒 830 次**，几乎全是
  `bad or missing X-Flux-Token`；而全仓 `token_env: FLUX_LLM_TOKEN` 只有 4 处**声明**、
  **零个读取者** —— 配置是装饰品，"机队能调本地大模型"一直停在纸面。
- 点名手法（可复用到任何"有人在打但不知道是谁"的现场）：给拒绝日志补
  `path` / `port` / `user-agent` 三列，重启服务等下一次命中 —— 立刻看到
  `UA=Python-urllib` 每 20–60 秒打 `/api/tags`。**只看 IP 永远分不清是哪个进程。**
- 两个空打口：①`fleet_lane.local_llm` 主端点失败后回落网关，拼裸请求不带 header；
  ②`_llm_tags()` 探测模型列表同样裸奔。
- 修法：新增 `Tools/fleet/llm_client.py` 统一客户端 —— 令牌取环境变量或
  `~/.fluxgroup-llm-token`，端点按「参数→`FLUX_LLM_BASE`→回环」解析，
  四态返回 `0 成功 / 3 缺令牌(缺料，**不发请求**) / 1 真故障 / 4 熔断中(300s 退避)`；
  两个空打口都改走它。
- 实测：有令牌 → 网关回"收到"；无令牌 → rc=3 且**网关日志零新增**；
  修完后 10:56 起无令牌拒绝 **0 次**（此前每小时上百）。
- 未闭合：跨机只对主控通电。bm-a/b/c 要真可用，仍需把令牌文件带外放一次
  （没有加密分发通道；卡片内容进 git＝泄漏，不许这么干）。

## 7. 僵尸机：FleetLink 活着 ≠ 能干活

- 实锚：bm-a `/status` 显示 `online`、能收 poke，但 **`wakes: []`** —— 它的 Windows
  唤醒清单是空的，派过去的卡只能挂到 6h 后被停摆判据释放。
- 判据：在线 + 6 小时零产出 → 不接受新活，容量判据返回 `EXECUTOR-DEAD (N 小时零产出)`。
- 护栏：判不出来就不排除（宁可不拦，也不许凭空拦活）；RG-34 双向验证（僵尸机拒、正常机通）。
- 边界：这台机器**只能人工恢复**（远程唯一执行器是卡，而卡要靠它自己的认领任务跑）。

## 8. 并发供给会铺重（第 4 次同族）

- `supply_batch` 被脉按轮调用，两轮并发都读到"没有活卡" → 同一交付物铺成两张
  （实测 4 组）。修法：落盘前再复检一次活卡，把竞争窗从"整个构建过程"缩到毫秒。
- 已在 `workgen`（RG-27）、`supply_batch`（复检+按交付物去重）两处收口；
  残留的通用教训：**"先查后写"在并发下永远不安全，必须在写前一刻复检或用锁**。

## 9. 断言面 34 条（本轮新增）
- `RG-33`：没令牌必须返 3 且零请求；跨机回落必须接 `llm_client`；`_llm_tags` 必须带令牌。
- `RG-34`：僵尸机不许接活，正常机不许被误排除。

## 10. CEO 说"好好确认是否真的"之后的复核纪律（本轮实证）

### A. 单次快照不能当结论——快轮/慢轮不一样
- 脉有两种轮：**95 阶段慢轮**（带 `blockers` 列表）与 **24 阶段快轮**（`blockers` 键为 `None`）。
- 我三次采样恰好都落在同一轮空档里，先误判"卡住了"，回头又把同一份慢轮快照当"健康"汇报。
- 正法：**连续采样 ≥4 次、间隔 30s**，看 `ts` 是否推进；判定"阻塞"必须取到慢轮且看到 `blockers` 列表（`None` ≠ 空）。

### B. 模型是否真在决策，要用"规则给不出的选择"反证
- `source="model"` 只是代码里的标记，证明不了模型真答了。
- 可靠反证：`A_NOOP`（什么都不做）在规则里永远不会被首选（规则首选=第一个非 NOOP），
  它出现过的次数就只能是模型给的。同日实测 430 次决策 / 422 次 model / `A_NOOP` 3 次。

### C. "DONE 数"不是产出口径，必须核交付物本身
- 实测 12 张卡从 `DONE` 被降成 `UNVERIFIED`：`ExileFarm.json`、`MonsterInn.json` 等**该卡自己的交付物根本不在盘**。
- `verify_done` 降得对，错的是"数 DONE 当产出"。核对一项产出的最小四件：
  文件存在 → 合法 JSON/可解析 → 非空 → mtime 是当天。

### D. 改完代码还要重启"握着旧模块的长驻进程"
- `com.fluxgroup.console` 是 11-05 启动的，我 11-08 改的令牌修复对它无效，它继续每 15s 打
  `/api/tags` 不带 header。**重启后才算验证过**。
- 判据：`launchctl list` 里服务的启动时间早于改动时间 = 它跑的是旧代码。

### E. 残留拒绝的归因方法
- 网关仍有 2 次 401，`ua=Python-urllib/3.13`；不是主控（主控已带令牌），而是 **bm-b 分叉**
  （`pulls:['.:fail']`，HEAD `8239204a` vs origin `c092cc8d`）→ 它跑旧代码。
- 结论：**修复没到机器前，不能宣称"问题已解决"**；节点分叉必须先用收口卡对齐。

### F. 并发写共享状态：查与写必须在同一把锁里
- 供给器两轮并发各自通过"无活卡"检查再各写一张 → 复检只能缩窗，不能消除。
- 正法：`fcntl.flock(LOCK_EX|LOCK_NB)` 跨进程互斥，拿不到锁就跳过本轮（负控：第二把锁必须被拒）。
- 配套坑：去重器把 append log 里**同 id 的旧行**也算活卡，于是"撤了等于没撤"（连撤三轮组数不动）；
  必须先**按 id 折叠（最后一行即当前状态）**再分组。

## git 操作副作用：CRLF 脏文件让 rebase 失败（本轮反复踩）
- 现象：独立 worktree 里 `git rebase origin/main` 反复报 `cannot rebase: You have unstaged changes`，
  源头是 `.gitattributes` 声明 `eol=lf` 而索引里存的是 CRLF 的文件（mv-album / drama-tools 等 5–10 个），
  每次 checkout 出来就是"modified"，`git stash` 后 autostash 又把它弹回来。
- 可用解法：`git update-index --skip-worktree <这些文件>` 让状态干净 → rebase/push 正常。
- 治本（未做）：对这批文件做一次 `git add --renormalize` 并单独提交"换行符归一"。