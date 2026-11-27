# D-20261116-02 回执：视觉工位卡面对账（选项 b）

- 执行机：bm-c（machine.json machine_id=bm-c，本机=视觉工位宿主）
- 回执时刻：2026-11-16 00:2x（+08:00）
- 令源：D-20261116-02（2026-11-16 00:00 决策轮，T2 dispatched，截止 2026-11-16 12:00）
- 选择：**(b) 把 OPEN 卡显式置 BLOCKED 并写入具体缺项**（D-12 冻结自启任务注册/恢复，(a) 不可用）

## 一、先纠正令面上的陈旧读数（承 D-20261115-12 自己的教训）

D-20261116-02 的依据行写的是 22:58 的读数。本机 00:2x 实读三面，已移动：

| 面 | 令面读数（22:58） | 本次实读（00:2x） |
|---|---|---|
| `queue.jsonl` | 16,527 B / mtime 22:58 / OPEN 2 | **52,200 B / mtime 11-15 23:38 / OPEN 6** |
| `heartbeat.json` | 不存在 | **存在**（102 B，`ts=2026-11-15T13:51:16`，`round=594`，`via=station_drive`）→ 停了约 10.5h，不是不存在 |
| `log/` 最新 | `20261111.jsonl`（mtime 11-12 16:09） | **`20261115.jsonl`（30,980 B，mtime 23:49:50）+ `20261114.jsonl`（956,678 B）** |

所以"队列还在被写而执行器掉了"这个**结论**成立，但**依据**要换：日志是新的，新行却不是执行行。

## 二、日志新鲜度来自审计器，不是执行器

`log/20261115.jsonl` 尾 4 行全是 `evt=FINDING`：

```
F-DONE-NO-ARTIFACT  bigstream-drama-src-scan-2026-11-15   DONE 但产物不存在：cph4/fleet/queue-receipts/drama-src-2026-11-15.json
F-DONE-NO-ARTIFACT  asset-lib-library-check-2026-11-15    DONE 但产物不存在：cph4/fleet/queue-receipts/asset-library-2026-11-15.json
F-DONE-NO-ARTIFACT  R-NEXT-BIGSTREAMD-EVIDENCE-20261115   DONE 但产物不存在：cph4/fleet/queue-receipts/triage-bigstream-drama-20261115.md
F-DONE-NO-ARTIFACT  asset-lib-voice-dataset-2026-11-15    DONE 但产物不存在：cph4/fleet/queue-receipts/asset-voice-2026-11-15.json
```

`state.json` 同刻 `ts=2026-11-15T23:49:50 / findings=12 / by_severity={high:10,warn:2} / sec=5.82 / model=unavailable`
—— 这是**审计拍的**，不是心跳拍的。两个面同目录、都叫"最新状态"，一个说执行器 10.5 小时前停摆（heartbeat），一个说 5 秒前刚跑过（state），读者按哪个都读不到"有没有在干活"。

## 三、顺带证实：4 张 DONE 卡的回执在盘上确实不存在

审计点名 4 个交付路径，本机逐个 `Test-Path` 全部 **False**；`cph4/fleet/queue-receipts/` 全目录 45 件、**零件**匹配 `*2026-11-15*`。
其中 `R-NEXT-BIGSTREAMD-EVIDENCE-20261115` 的卡面自己记着 `audit: {exists: true, size: 779}`、`closed_by: closer.py @ 2026-11-15T01:04:24`——**卡面说"当时在、779 字节"，盘上说"现在不在"**。两种可能（closer 的存在性判定与今天不在同一个根／文件事后被删），本回执只按盘上事实记账，不替 closer 下判断。

## 四、动作（选项 b 落地）

`_bmc_d02_block_open.py --apply`：6 张 OPEN 卡全部 `state=BLOCKED`，行内写
`blocked_by=visual-executor-not-running`、`blocked_reason`（心跳停摆+审计代写日志+D-12 冻结）、`blocked_at`。

| 卡 | prio | needs | 置 BLOCKED 后的具体缺项 |
|---|---|---|---|
| R-NEXT-BIGSTREAMD-TTS-QC-20261114 | P2 | cpu | 无执行器；卡面缺 `blocked_by` 字段（D-02 第三项要求） |
| asset-lib-face-dataset-2026-11-14 | P0 | cpu | 同上；且与 11-15 同名卡重复（**未自动合并/撤卡，留给车道属主判定**） |
| asset-lib-face-dataset-2026-11-15 | P0 | cpu | 同上（重复对之一） |
| asset-lib-char-gen-2026-11-15 | P0 | gpu | 无执行器 + 本机 GPU 已被 MV LoRA 训练占用（00:14 起 2 个 `sdxl_train_network.py`） |
| asset-lib-asset-gen-2026-11-15 | P0 | gpu | 同上 |
| asset-lib-asset-gen-scenes-2026-11-15 | P0 | gpu | 同上；卡面原有 `route_note: no local GPU lane free` |

守卫：写前复读 mtime（变则 abort）、逐行 JSON 往返、写后行数断言、原子替换。实读 `before open=6 → after open=0`。

## 五、未做（如实）

- **没有**启用/注册/恢复任何计划任务（D-12）。`HQ-VisualStation` 在本机 `schtasks /query` **查无同名任务**（只匹配到 `\Microsoft\VisualStudio` 两类），说明执行器从来不是本机计划任务——恢复它属于机队面决策，不在本司射程。
- **没有**改动 `heartbeat.json`。手工补一条心跳=伪造活面，正是本回执在骂的东西。
- **没有**修 `closer.py` 的存在性判定（属 cph4 工程面，且本窗只有 10 分钟；已按盘上事实留证）。
- 两处重复卡（face-dataset 11-14/11-15）留给车道属主；本回执不自动撤卡。
