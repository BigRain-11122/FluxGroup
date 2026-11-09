# 坏卡与堵点处置（bm-a，2026-11-08）

作者：bm-a 交互会话。触发令：CEO「对齐机队和主控，全面开始工作」＋ OB-20261107-180106-609（各机收口）。

## 1. 已修：车道里只剩已收口的卡时，全局队列被堵死

- 现象：`lanes/bm-a.json` 里还挂着已 DONE/CANCELLED 的卡 → `run_lane_cycle` 走 DEFERRED 分支 `return True`
  → `queue_claim.py` 当场退出 → 全局 OPEN 卡一张都领不到（"队列有活、机器空转"）。
- 修法：`Tools/fleet/lane_agent.py` 新增 LANE-ALL-CLOSED 判定——车道作业全部已关时返回 `"NO-JOBS"`，
  让调用方回落共享队列。判据是 `already_closed()`，不是"车道为空"。
- 证据：修后同一秒的取卡日志出现 `lane-mode: empty lane + nothing self-dispatchable -> falling back to shared queue`，
  并真的 CLAIM 到下一张卡。

## 2. 已修：取卡任务 pythonw 无日志，静默死亡与"在工作"无法区分

- 现象：`HQ-ProductionClaim` 动作是 `pythonw.exe queue_claim.py --node bm-a`，pythonw 下 stdout 为 None，
  任何异常不落盘；配合 `MultipleInstances=IgnoreNew`，一个挂住实例让任务 8.5h 一次都不再启动
  （LastTaskResult 267009=仍在运行，看起来完全正常）。
- 修法：动作改为 `wscript //B InvisibleRunner.vbs claim-bm-a.cmd`，壳内用 `python.exe` 并把 stdout/stderr
  追加到 `cph4/fleet/queue-receipts/_claim_bm-a.log`；执行时限 72h→1h。
- 证据：手动按同一动作跑，日志 88→801 字节增长。

## 3. 已撤/已摘：两张坏卡

- `OPS-I2V-CAP-BMA-20261103`：cmd 对 `D:/AI` 做 `**/*.safetensors` 递归 glob 且切片在 glob 之后，
  等于无限期扫描 → 实测把一个取卡实例挂死 23 分钟，正是 IgnoreNew 被永久占用的真因。
  交付物 `queue-receipts/i2v-cap-bma.json` 已存在（重复卡），已置 CANCELLED。
- `VCORP-GEN-r1202-EP001-060-20261108`：依赖 `C:/Fluxgroup/FluxGroup/media/drama-tools/...index-tts` 后缀，
  那是 bm-b 的本机路径；在 bm-a 上认领即 FAILED(0.0s)。已把 bm-a 从 nodes 摘除，卡留给持有依赖的机器。

## 4. 待主控处理（不是 bm-a 能决定）

- `lanes/bm-a.json` 仍挂着已 DONE 的 `biggame-pack-scan-2026-11-08`，请主控刷新车道。
  （已用 LANE-ALL-CLOSED 兜住，但车道文件本身该同步。）
- 队列唯一写者是主控：本次未直接改 origin 队列，只提交本说明与代码修复。