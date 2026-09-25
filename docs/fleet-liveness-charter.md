# Fleet Liveness Charter — 机队信息通畅律（顶层正典 v1.0）

> **溯源**：CEO 令 2026-09-25 U205「机队信息要保持通畅，不要看到什么掉线离线，看不到心跳，建立顶层规则和技术」。
> **定位**：机队一切心跳/活性/信息链路的**唯一顶层法源**——本件管「心跳必须活着+离线必须带整改注记+谁来修+怎么升级」；在哪跑=scheduling.md；巡检发现与整改闭环=patrol-charter.md（本件是其 L0 常态前置层）；周期总账=cph4/cadence.md。T2+否决窗 7 天。

## §1 心跳即法线（Heartbeat-is-Lifeline）

1. 机队每个实体（BG-A/B/C 游戏机·BigMoney bm-* 量化机·BigStream·BigCompute·各司 OS 循环）**必须**按其额定周期发布心跳（额定周期=各实体 cadence 自报入账）。
2. **分级判据**（与 `Tools/fleet-audit.ps1` 实现逐字对齐·诚实律）：`ONLINE`＝心跳龄 ≤2h（10min 级机器实为分钟级新鲜）｜`STALE`＝>2h｜`OFFLINE`＝>24h｜`NO_TS`＝心跳缺时间戳字段＝写手缺陷（永远不可判活）。BigStream/BigCompute 哨兵类按其协议 20min 判活线。
3. 心跳文件契约：`Design/configs/GLOBAL/fleet/<机>.json`（MiniGame 系）/`fleet/machines/bm-*.json`（BigMoney 系）/各司 state+beat 文件（见 fleet-audit.ps1 源清单）——**新心跳源=在 fleet-audit.ps1 加一行**（开闭原则·禁另起采集面）。

## §2 无静默掉线律（No-Silent-Offline）

1. **CEO 任何可见面（看板/巡检报告/夜报）不得出现光板「离线/无心跳」**——每个非 ONLINE 实体必须携带**整改注记**，三来源任一：①看门器自愈动作记录（liveness.json actions）②巡检 PT OPEN/ESCALATED 行（「整改中·PT-xxx」）③alerts 升级记录（「已升级·时间戳」）。
2. 违例线：光板非 ONLINE 持续 **30 分钟无注记＝P1 机制违例**；持续 **24h 无注记＝P0**。注记不是掩盖——是「正在处理」的诚实可见性（实体可以坏，处理状态必须可见）。
3. 看板消费契约：像素小镇 `Read-SubPulse`/硅基窗心跳面读取 `liveness.json`（§7）——有注记显示「修复中·…」，无注记才允许显示离线原文（而看门器保证无注记态 ≤30min）。

## §3 自愈优先律（Self-Heal-First）

1. 心跳生产者必须**可自愈**，已知故障模式配方表（全部历史实证·坑录在案）：
   | 故障模式 | 自愈配方 |
   |---|---|
   | codely/引擎挪窝（SCRIPT_ERROR 假跑） | 取运行中进程 ExecutablePath 自适配回写 machine.json |
   | 陈死锁（.git/index.lock/tick 锁） | 零属主进程+龄>12min 才清（既有配方法） |
   | 信息链任务停跳（心跳/看板/CEO台） | 看门器 `Start-ScheduledTask` 点火（任务自带单飞锁，重入安全） |
   | CeoDeskServer 挂 | 健康探针（127.0.0.1:8791/api/health）失败即点火 |
   | ComfyUI/Ollama 熄火 | 既有 KeepWarm/保活任务族（不在看门器代管面） |
2. **自愈动作必须留痕**（liveness.json actions 数组+stdout 行）——无痕自愈=违例。
3. 自愈边界（F-08 车道归属律）：**本机自愈仅限本机信息链任务集**（EngineTick/CockpitBeat/CeoDeskServer 三件·v1）；生产任务（ComfyDraftTick/BoardForge 等）归其 owner 车道自愈，看门器只观测注记；**跨机永不代修**（bm-c 的修法在其 owner 车道）。
4. 熔断（E1 既有律）：自愈两轮未愈禁硬修升级 E1——看门器对同实体同故障只记 alerts 不重复点火。

## §4 双通道律（Dual-Channel）

带内=实体自写心跳（§1 契约）；带外=**宿主看门器独立探活**（文件 mtime+任务 LastRun+服务探针三源）——生产者死了也不失察，两通道互为冗余。看门器本身入 task-health 五信号面（被监控者也要被监控）。

## §5 升级阶梯（Escalation Ladder）

检测→配方内自愈→复探→未愈→**alerts.jsonl 落行+限流触发 FluxGroup-PatrolRound**（巡检官模型会话消费 alerts 正式化 PT 行·P0=24h/P1=72h 时效律）→PT 整改闭环（patrol-charter §7）。限流=同实体 120min 内不重复触发（防风暴）；巡检戳记认领（F-09）照常生效——触发被认领跳过=诚实记录非失败。

## §6 机器对称律（Fleet Symmetry）

1. 每台机各宿主**同件看门器**（`Tools/fleet-liveness-watch.ps1` 随 git 分发·OS 任务 5min·InvisibleRunner 零窗·非提权 -User 注册范式）——各机自愈自己信息链、注记自己视角、互不越机（F-08）。
2. 跨机实体活性：各机看自己本地快照（含 git fetch 滞后·诚实注记「as-of fetch」）+巡检周班权威复核（fetch 陈旧误判坑在案）。
3. **A/B 机采纳窗＝下一巡检轮（周一 09:23）前**：注册 OS 任务+cadence 行+首跑证据各机自报（08 号协议自报范式）；未采纳=巡检 P2 发现。

## §7 数据契约（liveness.json）

路径=`%USERPROFILE%\.codely-cli\fleet-liveness\`（每机本地·git 零噪声·与 fleet-audit 同区）：`liveness.json`＝`{ts, verdict(GREEN/AMBER/RED), machines:[{id, flag, last_seen, note}], sched:{unhealthy, flags}, actions:[{ts,do,detail}]}`＋`alerts.jsonl`（升级流水）。消费面=看板（Read-SubPulse 注记）+巡检+夜报。

## §8 与既有法关系（零新车道·防重复律 #1）

复用三件零新采集：`fleet-audit.ps1`（心跳聚合·-Json）+`task-health.ps1`（调度五信号）+`docs/patrol-ledger.md`（OPEN 行=现成整改注记源）；本件不建新心跳源、不代 owner 修（F-08）、不越认领（F-09）、不停用态复活（U166）、不绕熔断（E1）。变更控制=本件 T2+cadence.md 行变更+changelog。

### Changelog
- 2026-09-25: initial v1.0（CEO 令 U205·C 机首宿主：charter+watch 工具+OS 任务+看板注记契约）。
