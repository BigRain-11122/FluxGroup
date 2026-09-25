# Patrol Ledger — 集团巡检整改台账

> 集团巡检机制唯一闭环追踪面（patrol-charter.md §7）。行级追加；禁改历史行；状态流转=OPEN→(FIXED)→VERIFIED / OPEN→ESCALATED（逾期）。核验禁轻信状态字段——每次 VERIFIED 必附证据指针。

## 整改项台账

| PT 号 | 日期 | 实体 | 级别 | 发现 | 要求动作 | 证据指针 | 截止 | 状态 |
|---|---|---|---|---|---|---|---|---|
| PT-20260925-01 | 2026-09-25 | BigMoney | P0 | bm-c 节点执行体瘫痪根因：BigMoney 工作目录 K:\金钱牛马\BigMoney 缺失（Test-Path=False）→Bigmoney-IterationLoop/Autofill/LoopWatchdog 三任务僵尸失败（result=0x80070005）→fleet 心跳 09-24 21:51 起死 13.9h（audit STALE）=P-49 零承令的结构根因；实机在线非物理下线（Ollama 0.34.4 serve+qwen2.5:7b 4.7GB 在位=装机面已毕+KeepWarm 绿+本机 BigLife 11:47 [via bm-c交互会话] 提交在案） | 裁决 bm-c BigMoney 面两路并执行：①重建部署（恢复工作目录+修三任务+心跳复活）或②按 fleet-allocations 正式转纯 Biggame 机（fleet 台账如实标记+僵尸任务清理）；P-49 收口联动（缺的是执行体非装机） | probe-20260925-114357.txt [FLEET] bm-c 行+[SCHED] 三任务行；巡检报告 §BigMoney；O-20260925-1153-bm-c | 2026-09-26 | OPEN |
| PT-20260925-02 | 2026-09-25 | BigStream | P2 | fleet 心跳写手缺陷：bigstream 机心跳 NO_TS（无 ts 字段·fleet-audit 永不可判活）+task 文本冻结 R173（写手 09-24 22:2x 后停更）；实体实况=非停滞（03:07 值守轮在案 R193 实活+巡检 host push 被拒非快进=origin 有新提交实证）；C 机至 Bigmedia SSH 三次重置未拉全量核实=未覆盖如实记 | ①心跳写手补 ts 字段+task 随轮更新；②回执附最近轮号佐证轮末 push 律遵从 | probe [FLEET] bigstream NO_TS 行；值守轮 09-25 03:07 报（evolution-ledger）；push 非快进实证；O-20260925-1153-BG-C | 2026-10-02 | OPEN |
| PT-20260925-03 | 2026-09-25 | HQ | P2 | patrol probe host-scope 误检两处：①FluxVerse world/world-state.json（gitignored 活数据·仅感知宿主机存在）②MiniGame docs/STATUS.md（实况=根级 STATUS-<机>.md 制·docs/ 仅 ops/）——非宿主巡检机必报 MISSING=噪声发现 | probe 文件清单加 host-scope 标记：活数据/机器态文件仅在其宿主机判缺失，非宿主报「未覆盖」 | probe-20260925-114357.txt MISSING 行；MiniGame docs 实测（仅 ops/）；FluxVerse .gitignore | 2026-10-02 | OPEN |
| PT-20260925-04 | 2026-09-25 | HQ | P2 | HQ 树漂移未收口：gaming/.codely-cli/settings.json（+3-1）与 quant/.codely-cli/settings.json（+3-1）=mcpServers 分发面、quant/CODELY.md（+6）=记忆追加均未提交；?? .codely-cli/patrol/ 追踪策略未定 | 归属会话收口提交（或值守轮定向收编）；patrol 运行面（stamp/log/probe）定 gitignore 或入册二选一 | git status/diff --stat 实测 2026-09-25 11:44 | 2026-10-02 | OPEN |
| PT-20260925-05 | 2026-09-25 | BigMoney | P2 | 无人值守轮 commit 缺 [via] 尾标（versioning §4.1/§4.3 无人值守轮强制·近 8 commit 零尾标·机器归属现靠分支/轮报告代偿非正典）；另 K:\Fluxgroup\FluxGroup\quant\bigmoney 克隆 11:33-11:35 出现本地 commit+pull--rebase 事件（题材与 origin 同题收敛）归属未明——本机 Bigmoney 任务全僵尸态 | 补 via 尾标纪律或入册公司自治豁免；本地克隆 commit 事件归属核验签收（若为同步/autofill 类工具行为=登记工具名与写权面） | quant\bigmoney git log -8 实测+reflog 11:33:07/11:35:03 两条 commit 事件 | 2026-10-02 | OPEN |

## 闭环统计

- 首班 2026-09-25（RUN_ID=20260925-114357·host=BG-C/bm-c）：pt_new=5（P0×1·P2×4·PT-02 依 push 非快进新证据 P1→P2 修正定稿）·pt_verified=0（首班无上轮项·[CARRY] open_findings=0）·pt_escalated=0。红黄绿分布=8G/0Y/1R（BigMoney=R·余 G）。
