# 本机「一线一进程 / 一线一模型 / 一线一算力槽」（2026-11-27 立）

> 令源：CEO 2026-11-27「先把本机自动化任务和算力分配都停了，然后规划好，每条线给一个专用的，
> 比如 b 站的给一条，公众号给一条，好好测试」＋「每条线专用一个模型和一块算力资源 不要重叠，
> 当然如果本地不够同时运行的时候就可以排队」。
> 正身：`cph4/fleet/LOCAL-LANES-v1.json`（机读）/ `.md`（人读）

## 一、结构（当前在跑）

- 5 条线：bili（B站双号）、gzh（公众号）、collect（纯 HTTP 采集）、train（烘焙+训练+评测）、ops（只读体检+一屏）。
- 3 个底座：`com.fluxgroup.base.browserd`(8791)、`com.fluxgroup.model.bili`(8788)、`com.fluxgroup.model.gzh`(8789)。
- 执行体：`Tools/fleet/line_runner.py --lane <线>`；安装/卸载/踢一拍：`Tools/fleet/lane_install.py --install/--uninstall/--kick`。
- 算力槽：`Tools/fleet/compute_broker.py`（flock 原子租约 + pid 存活 + TTL + queue.jsonl 先来先得）。
- 一屏：`cph4/fleet/LANES-BOARD.md`（含"算力槽：持有者/排队"行与"最近实跑（含失败）"列）。
- 总开关：`.codely-cli/state/LANES-PAUSED`；状态：`.codely-cli/state/lanes/<线>.json|.jsonl`。
- 旧 35 项归档：`~/Library/LaunchAgents/disabled/20261127-ceo-stop/`；停机清单 `STOP-INVENTORY-20261127.json`。

## 二、为什么要重建（旧形态的病灶）

- 35 个 LaunchAgent 里养号 9 个调度器、训练 6 个、体检 6 个，互相抢同一个 browser profile。
- `res_alloc.may()` 的"平台时段轮转"让公众号给 B 站让位，gzh 台账里 68 拍空转。
- 判据看"台账有没有长"，于是「入库 0 篇、失败 38 次」也记 OK（假绿）。
- 专用车道（`FLUX_LANE`）现在只受容量闸，不受轮转；轮转只留给无车道的临时调用。

## 三、踩到并修掉的五个坑（都可复用）

1. `res_alloc.train_running()` 只 grep `mlx_lm` → 把 8788 推理服务当训练，训练线永远让路、一屏永远说"训练在跑"。正法=按真实训练命令行匹配（train_build/train_forever/mlx_lm lora），并加纯函数负控。
2. `user_agent.py` 的 `coin/fav/follow` 走 `_with_video → sc._launch` 冷启动；常驻 browserd 握着 profile 锁时必超时抛错，整场会话 rc=1。正法=单步兜异常、记失败继续（"任何一步失败不中断整场"）。
3. `forum_comments.py --books N` 先切片再过滤"已采过"→ 前 N 本采过就天天采 0 本。正法=每拍采 N 本**没采过的**。
4. `news_comments.py` 无单拍上限，列表页带出上百篇 → 一拍跑十几分钟。正法=`--max-docs`；采集器 `rc=3` 语义=本轮无新内容（判 SKIP，不是故障）。
5. 自检写生产路径：`--self-test` 里调 `h_ops` 写真实一屏、调 `tick` 写真实状态，把"表外作业 com.fluxgroup.rogue"写进了生产面板。正法=tick 加 `persist=False`、一屏路径与 launchctl 读取都可注入、自检只写临时文件。

## 四、判据纪律（写死）

- 只认产出：gzh 看 style_pool/articles/industry/train_rows/struct_n 增长（`pool_todo` 变小可能是清死链，不算）；bili 看窗口内真实动作且无 need_login；collect 看语料行数真的涨。
- 一屏要留失败：单独一列"最近实跑（含失败）"，不让 10 分钟后的 SKIP 把失败盖住。
- 坏号先停：某号 need_login 之后再无成功动作就不排它，另一个号顶上；登录后有成功动作自动恢复。
- 排队是正常状态：QUEUED 不算失败，下一拍再来；任何"偷偷并行"都必须能被 `compute_broker --self-test` 打红。

## 五、实测数字（2026-11-27 夜）

- 两模型各 RSS ≈ 2.9GB；加第二个后 swap 仍 2866.5MB（未涨）。
- 并发租约：bili granted 22:42:03 / released 22:42:11 / gzh granted 22:42:12（零重叠）。
- 采集四子任务：news +472、music +27、forum +106、industry +50；语料 117,958 → 119,179 行。
- 自检：line_runner 33/33、compute_broker 9/9、res_alloc 22/22（均含负控）。
- 已知阻塞：B站 acct1 登录失效（需扫码）；公众号风格池只剩死链（需新种子或修 chejiahao 解析）。
