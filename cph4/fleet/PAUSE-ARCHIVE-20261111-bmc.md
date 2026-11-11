# bm-c 全自动化暂停归档（2026-11-11）

> CEO 令（2026-11-11 ~12:00）：「我让你暂停所有自动化，并归档，我要大改工作流」
> 执行窗：bm-c 交互会话 2026-11-11 11:49–12:xx
> 本件=bm-c 全停快照+恢复入口。**新工作流定稿前，本机一切自动化车道保持停用；任何窗/任何机不得擅自复启旧车道**（新工作流令优先）。

## 一、停面清单（三面全停）

### 1. 常驻进程（已杀，11 个）

| 进程 | 说明 |
|---|---|
| saturation_engine.py ×2（PID 3288/19864） | 量化烧批引擎双实例（11-08 开机自启双起，本身是待修病灶） |
| ollama serve + llama-server 71808 | 不应在役（bm-c=LLM 退役机，10-17 CEO 令零本地 LLM），连带清理 |
| ComfyUI main.py :8188 | MV i2v/KF 出图出片主产线 |
| agent.py --node bm-c --loop 60 | HQ 车道执行器（心跳+领卡） |
| lane_agent.py --node bm-c | 车道卡执行器 |
| etf_book_order.py --selftest | 量化在飞批 |
| orphan_face_probe.py / resident_dispatcher.py | 资产库探针 / 量化常驻派发器（随任务停自退） |
| smoke_test / panel_level_anchor_audit selftest | lane 子任务（随执行器停） |

### 2. 计划任务（29 个已 Stop+Disable）

**Bigmoney 族（8）**：Autofill / IterationLoop / LoopWatchdog / MoneyflowPull / PoolWorker / ResidentDispatcher / SatEngine-bm-b / SaturationEngine
**HQ 族（5）**：HQ-bm-c-Sentinel / HQ-MemoryBudgetGate / HQ-SilenceGuard / HQ-SilenceGuard-Lane /（HQ-Agent 若在册同禁）
**MiniGame 族（17）**：AuditTick / BoardForge / CeoDeskServer / CockpitBeat / ComfyDraftTick / ComfyKeepAlive / ComfyRamGuard / DraftJanitor / EditorSentry / EngineTick / GateTick / Housekeeping / RadarDeepTick / RadarTick / RedlineAudit / SiliconWatchTick / TickWatchdog
**守护（1）**：BmcIdleGuard

此前已禁用面保持原态未动：ShortVideo 4 件（O-20261017-1741 冻结令）、Ollama 族 4 件（LLM 退役令）、BigLife-QA-Server（census 冻结）。

### 3. cron 班（2 个 durable 已删）

- cloudF 满槽续发·循环班（:17/:47）
- U235 硅基窗小时迭代轮（:37）

prompt 全文与调度备份：`media/logs/converge-backup-20261111/scheduled_tasks.json.bak`。

## 二、收敛手术记录（停机前完成）

- 发现主病：agent pull `--ff-only` 撞分叉反复失败（rc=128）但继续跑卡 → 本地滚出 **127 个未推提交**；push node/bm-c 被 non-ff 拒。
- 双向核验：本地 127 提交的回执内容 **全部已在 origin/main**（主控已折枝）；远端 node/bm-c 独有 6 提交内容 **也全部已在 origin/main**。零丢失风险。
- 处置：停执行器 → 脏文件备份 → `git reset --hard origin/main` → **HEAD == origin/main 0/0**（收敛完成）。
- 备份目录：`media/logs/converge-backup-20261111/`（mem-20261111-fleet-arch-audit.md、scheduled_tasks.json.bak、git-status-preserved.txt、dirty/ 修改件）。
- 主树上未跟踪工具脚本（idle-guard-kit 手术族/voicebank/patrol_local 等）**留盘未删**（归档态保留，新工作流可清理或收编）。

## 三、停机时挂账快照

1. **W2 短镜批已自然收官**（11-09 01:46）：LJ 批 `ALBUM LANE DONE ok=2 fail=0`、JD 批 `ok=5 fail=0`，产物在 `media/mv-album-001-jay/clips-local-768/`（123 mp4）。长镜池（LJ 11 + JD 15）未烧（本机 16GB 墙：src_s >10s 禁单烧，11-09 判例）。
2. **主控车道压着一张 bm-c 跑不了的卡**：`R-NEXT-BIGSTREAMM-REBUILD-20261109`（cmd 引用 `cph4/fleet/mv0001-handover/...`——该目录 bm-c 不存在，11-03 已判 E-INPUT 域）。全停后主控将判 bm-c OFFLINE，不再派活。
3. **PuLID 身份一致性链已跑通**（11-09 3/3 SAME 跨姿势，权重/路径细节见 CODELY.md 11-09 条）。
4. **资产库现况**：props 20 / scenes 12 / motions 15 / transitions 10 / characters 96 / faces 96（12 视角）；styles 与 typography 为 0（无生产卡）。
5. **game-10s 质量闸无生产者**（MSG-20261108-1825 已提请主控，未回）。

## 四、恢复入口（新工作流定稿后按新令执行，勿照抄旧架构）

- 计划任务：`Get-ScheduledTask` 按上表逐一 `Enable-ScheduledTask`（或按新工作流重建）。
- ComfyUI：`D:\ComfyUI\python_embeded\python.exe -s D:\ComfyUI\ComfyUI\main.py --listen 127.0.0.1 --port 8188`（cwd=D:\ComfyUI\ComfyUI，隐藏启动，冷启 ~50-60s，/system_stats 回 devices 才算成功）。
- 执行器：`python Tools/fleet/agent.py --node bm-c --loop 60`（每机只准一个执行器）。
- cron：从 `scheduled_tasks.json.bak` 读原文重建（禁凭记忆重写 prompt）。
- **已知待修病灶（复启前必看）**：① saturation_engine 开机自启双起（复启前先杀孤儿、任务面单实例化）；② agent pull 撞分叉滚雪球（R11 架构下隔夜 behind>100 须做收敛手术，本次已做）；③ bm-c=零本地 LLM（勿复启 Ollama 族）。

## 五、未动面声明

- 他机（bm-a/bm-b/bm-m）自动化**未动**——本令由 bm-c 窗承接，按机队口令律只停本机面。他机若需同停，等 CEO 新工作流令统一部署。
- 本机硬件/网络/文件系统未动；盘上产物（media/ 全部交付物）完好。
- git 基线：FluxGroup HEAD==origin/main 0/0；MiniGame machine/C 未动。

---
归档人：bm-c 交互窗 · 2026-11-11 12:xx · 等 CEO 新工作流令
