# 主 Agent + 子公司 Agent（机队调度执行闭环）v1

> CEO 令 2026-10-29「建主 Agent 和几个子公司 Agent，循环派活、盯产出、不许闲置；调度要科学，每次能调云端或本地算力看自己该做什么」。
> 上一轮复盘已定根因：机队有心跳、有队列、有认领脚本，但**没有会造活和仲裁的执行器**，所以「没 OPEN 任务」被当成正常，三台机同时健康的空转（见 2026-10-27/28 判例）。

## 一、两层结构

| 层 | 文件 | 谁跑 | 干什么 |
|---|---|---|---|
| 主 Agent | `Tools/fleet/master_agent.py` | bm-a 计划任务 `HQ-MasterAgent`（每 2 分钟） | 造活 → 路由 → 派活 → 盯租约 → 报状态 |
| 子公司 Agent | `Tools/fleet/lane_agent.py` | 各机 `HQ-ProductionClaim`（每 5 分钟，经 `queue_claim.py` 接入） | 领本机任务 → 执行 → 回执 + NATS 上报；没活时自己翻本机积压 |

单写手原则：**只有主 Agent 改队列和车道文件**，执行机只读自己的车道文件。三台机是三个 git 克隆，双写队列必然分叉（2026-10-27 已实锤）。

## 二、主 Agent 每轮五个动作

1. **感知**：读 NATS KV `FLEET_STATE.state.<node>`（心跳、CPU/RAM/GPU、快照年龄）。
2. **造活**（只造真活）：
   - `PRODUCTION-BACKLOG.jsonl`：`requires` 全在、`deliverable` 不在才入队；
   - `WORK-RULES.jsonl`：规则化派生（当前 5 条 = v718 重建 → 交付闸 → 逐镜分级 → AIGC 标识 → 保真判定），同样按文件存在性判定，不猜不编。
3. **路由**：本地优先；只有任务自带云端腿且预估 ≤500 积分才走云端，>500 标 `blocked` 等 CEO 确认（不自行授权）。
4. **派活**：按 `needs` + 实时容量 + 工作时间让路 + 优先级选车道；**每车道同时只一件**，写 `cph4/fleet/lanes/<node>.json`。
5. **盯产出**：租约到期未回执 → 重排（3 次转 FAILED）；回执说 DONE 但交付物不存在 → FAILED；被让路推迟的任务立刻释放，不占租约。

## 三、子公司 Agent 的规矩

- 只读自己的车道文件（优先读 `origin/main` blob，脏工作树也拦不住）。
- 没派活时**先扫本机积压**（`backlog_fill`），只在输入真实存在于本机时才跑——这就是「问本地算力我该干什么」。
- GPU 任务先走 `gpu_lease.py acquire`（停常驻 LLM、禁 keepwarm、等显存、起 ComfyUI），跑完 release。
- 硬红线：**禁止自动拉起已打包游戏**（CEO 2026-10-28 令）；bm-a 白天（09:00-19:00 工作日）不接重活和 GPU 活，让路给 CEO。
- 结果写本地回执 + 发 NATS KV `FLEET_STATE.lane.result.<node>`，不回写主仓。

## 四、闲置的判定（关键）

「没派活」≠「闲置」。只有车道自己上报 `IDLE` 且连续两轮无活，才算 `IDLE-CONFIRMED` 并进 `violations`。其余情况必须带原因：

- `WORKHOUR-YIELD`：任务在等夜间窗口（CEO 自己电脑的正常让路）；
- `CAPACITY-BLOCKED-RAM`：内存不足，需要释放或改派；
- `SELF-DISPATCH`：正在翻本机积压。

状态机核面：`cph4/fleet/dispatcher/MASTER-STATE.json`（每轮覆盖）+ `MASTER-LOG.md`（追加一行）。

## 五、运行与验收

```powershell
python Tools\fleet\master_agent.py                 # 跑一轮（人工）
python Tools\fleet\master_agent.py --dry --no-push # 只看决策，不落盘
python Tools\fleet\lane_agent.py --node bm-a       # 手动跑一次本机执行
```

验收判据：①队列不再长期 0 OPEN；②每台在线机的 `idle_reason` 非空且可解释；③任务从派发到回执闭环（2026-10-29 首测：smoke 任务 0.2s 完成、回执落盘、主 Agent 收口 done+1）。

## 六、业务条线层（2026-10-29 增）

条线不再是散落的文档，而是主 Agent 每轮盘一遍的对象。登记表 `cph4/fleet/LINE-REGISTRY.json` 只放**机器可判的字段**（仓/证据目录/过期阈值/活源前缀/闸/负责人/状态），规则正文仍在各正典，不复制法条。

每轮判定：

| 判 | 含义 | 是否计为问题 |
|---|---|---|
| `WORKING` | 队列里有本线的 OPEN/RUNNING 活 | 否 |
| `WAITING` | 没活，但最近产出未超阈值 | 否（正常等待） |
| `STALE` | 超过阈值无产出 | **是**，进 violations |
| `BLOCKED` | 有活但没有可用车道（如 bm-b 仓库分叉） | **是** |
| `PARKED` | CEO 明令停产（短视频线） | 否（不计闲置） |

产出新鲜度取「仓最近一次提交」与「证据目录最新文件」两者中较新的一个；内容线用证据目录（MV/漫剧/短剧/车机/拆解），公司线用 git。

首个结果（2026-10-29 10:45 实测）：STALE 3 条（短剧 280h、BigHouse 267h、拆解 120h）、BLOCKED 1 条（漫剧·bm-b 仓库分叉）、PARKED 1 条、WAITING 8 条。

新增/调整一条线：改 `LINE-REGISTRY.json` 一行即可，不改代码。主 Agent 不会因为条线过期就自己编活——它只把「谁欠产出、欠多久」写进 `NEED-SUPPLY.md`。

## 七、工段级分配与硬件配额（2026-10-29 增）

线级还不够细：一条线可能“整体看着没停，某个工序早停了”。登记表每条线再拆 `stages`，每道工序三件事——**谁判（owner）、算什么档（model）、哪台机跑（lane）**，外加证据目录（判新鲜度）。

判定：`WORKING / WAITING / STALLED / NO-DATA / PARKED`；**线级 = 最早断供的工序**（`STALLED-STAGE`），所以报告写“MV 卡在关键帧段”，不是“MV 线闲着”。证据目录不在本机的段记 `NO-DATA`，不冤枉（素材常在另一台机）。

硬件按实测写进 `LANES`，不按型号口碑：

| 机 | 卡/内存 | 能接 | 不能接 |
|---|---|---|---|
| bm-a | 4070S 12GB / 94GB | **夜间满负荷**：768p KF/i2v、装配、闸 | 工作日 09–19 全让路（`quiet_hours`，只接 `day_ok` 标记的活） |
| bm-b | 3070 8GB / 24GB | 480p animatic、音频/TTS | 768p（显存不够） |
| bm-c | 3070 16GB / 24GB | 768p 生产 | RAM 常年吃紧，CPU 活慎派 |
| bm-m | M1 Pro 32GB | **调度中枢**、iOS 出包、文本（可跑 14B–27B）、音频 | 无 CUDA 不接 GPU；单件写入 >20GB 不接 |
| bm-d | 3×V100 48GB / 256GB | 768p 批量、回测 | 装机未完成 |


**工作机白天让路（CEO 2026-10-29「台式机是我的工作机，只有晚上可以满负荷」）**：bm-a 带 `quiet_hours=(9,19)`，工作日白天不接任何活（连 CPU 也不接），除非任务显式标 `day_ok: true`；19:00 后自动恢复满负荷。这种等待在状态里显示 `DAY-YIELD`，**不计为闲置、不进 violations**——那是合规，不是故障。

`vram_min_gb` / `cap` 是硬过滤：8GB 卡永不接 768p，无 CUDA 永不接 GPU 活；`model=local-small` 的活只派给带 `llm` 能力的机（bm-a/b/c/m/d）。本地模型名不写死——车道读该机 `/api/tags`，配置的模型不在就用本机最大的那个，换机不用改代码。bm-m / bm-d 标 `auto_join`——**只要它一上报心跳就自动并入排产**，不用改代码、不用再问硬件到没到。

## 八、算力分配（2026-10-29 定，正身 `MODEL-POLICY.json`）

原则：**按适配度分配，不按身份分配**。能本地做的绝不上云；本地做不了才上云；本地有产能却让活排队等云=浪费，要报警。

| 活 | 去哪 | 理由 |
|---|---|---|
| 脚本/闸/转码/扫描 | 本地（零模型） | 没有需要模型的地方 |
| 摘要/分类/抽取/改写 | 本地小模型（`qwen3:4b-instruct`） | 4B 够用；本地全占就排队，不为省等待花钱 |
| KF/i2v/渲染 | 本地 GPU | 产能本身就是目的 |
| 仲裁/归因/取舍/创意方向 | 云端最强大脑 | 本地小模型给不出可用结论 |
| 本地无车道且卡住下游 | 云端（须声明 `cloud_ok`） | 唯一允许为“等不起”花钱的情形 |

闸门：单次 ≤50 积分、当日 ≤200、硬顶 500（超线须 CEO 亲批）。**主 Agent 的 2 分钟心跳永远是零成本**——判定不了的写进 `cph4/fleet/dispatcher/JUDGMENT-QUEUE.jsonl`（一行一个问题+证据），由最强大脑回答后回填 `state=ANSWERED`，答案本身即审计痕迹。判云端但有匹配的空闲本地车道 → `CLOUD-WHILE-LOCAL-IDLE` 进 violations。

实测（2026-10-29）：五类样活分别落到 local / local-llm / cloud / blocked(600 分) / local-GPU，本地调用 `qwen3:4b-instruct` 返回正常。


## 九、总控只有一个（2026-10-29）

`cph4/fleet/MASTER-NODE.json` 一行声明谁写队列。bm-a 与 bm-m 是两个克隆，没有共享锁，两个总控会把同一件活派两次。声明式而不是运行时抢占：切总控是决定，就写下来。

- 切到 Mac：改 `"node": "bm-m"` → commit → bm-a 下一轮自动打 `STANDBY`（只读，不碰队列）。
- Mac 上的角色是 **control plane**：跑 master、挂总线、接轻文本活；`role_class=control` 只硬拒 GPU 活与单件写入 >20GB 的活，并保留 ≥20GB 磁盘余量；32GB 统一内存可跑本地大模型与重 CPU 活，只是排产时优先级低于生产机。
- Mac 不需要装媒体素材。clone 用 `--filter=blob:none` 即可，媒体目录在别的机上。

## 十、首日实跑发现（2026-10-29）

1. **v718 重建规则被证伪并回撤**：`mv_rebuild_from_edl.py` 按同一 EDL 重建，产物与 v717 **逐字节相同**（MD5 均为 `B75435845FCA145DB16CFB7283F8E76B`），交付闸结论也一字不差。结论=重建不能修 D1/D2/D4（缺陷在素材镜本身），只能逐镜重烧/调色/插值。5 条规则已移到 `WORK-RULES.disabled-20261029.jsonl`，v718 母版与派生产物已删，队列行标 `INVALID`。**教训：任何“重跑就能修”的规则必须先验证产物不是副本再上生产。**
2. **白天让路的漏洞已补**：`self_dispatch` 当时只看 GPU 窗口，漏了 `heavy`，导致 10:06 在 bm-a 工作时间跑了一次重活。现已按 `heavy_allowed()` 拦截。
3. **两台远程机的结构性阻塞（需人处理）**：poke 返回 `bm-b .:updated` / `bm-c .:fail`，但两者工作树 HEAD 一直停在 `da7652f5` / `994d63ca`，拉不下新代码 → 新的 lane 执行器落不了地。各自在本机跑一次 `Tools/fleet-hot-sync.ps1` 即可解决；bm-c 另有空闲内存仅 0.8GB 的硬约束。

## 十一、默认放行律（2026-11-01 CEO 令·最高规则）

CEO 原话：「所有的你们都可以按以前制定的规则和方案自我决策和推进，不要等我…不能因为等我而不去推进，这是最高的规则，所有的流程都要按这个打造」「你做的门槛太多了，经常出现闲置等的情况」。

流程硬约束（新写或改任何环节都按此审）：

1. **禁「等」**：任何环节不得以等 CEO／等授权／等签核／等确认为由停工。按既有规则自行决策并推进，CEO 巡视时提出返工再改。
2. **闸只留三类**：花钱超限、不可逆删除/覆盖、对外发布（平台账号与发言权在 CEO）。其余一律默认放行。
3. **签署改事后否决**：原本要 CEO 签字才能前进的工段（如 MV `mv-approve`）改为 Production 席自决放行 + CEO 否决窗；否决即回滚到上一段重出。
4. **闲置即缺陷**：任一机器/agent/条线无活而队列有可宣告工作时，判流程缺陷，当场改流程，不接受「在等」的解释。
5. **供给源必须上电**：宣告工作席（`night_plan.py` / `workgen.py`）是脉冲的每轮前置阶段，不是人工脚本。新增任何「宣告/补料」类工具，必须同时接进 `master_pulse.py` 的 STAGES。
6. **库存按可执行判定**：只有「能变成活」的卡算在途；产物已在盘的 READY 卡由 workgen R6 收口，不得当库存。
7. **跨机卡不带本机绝对路径**：`cwd` 一律空串，由各机的 lane 用自己的仓库根执行。

## 十二、角色与大脑分层（2026-11-01 CEO 令）

CEO 原话：「你务必清楚自己的角色，主控大脑，要创新要科学，轻度赋能什么的，后面还有真正的算力服务器大脑介入」。

### 我的角色（bm-m 控制面）

做：判断与决策、派单与补料、监督（四信号+磁盘事实）、把重活路由给有产能的机器。
不做：重媒体生产、常驻大模型、占用 CEO 办公时段的重 CPU。
判据：`BRAIN.md` 每轮的「本机角色自检」——负载长期接近核数即角色越界，先查是不是主控自己在干活。

### 大脑分层（不是写死在 Mac 上）

正身=`cph4/fleet/BRAIN-SEAT.json`，三层、可切换：

| 层 | 席位 | 用途 | 现在 |
|---|---|---|---|
| local | bm-m 4B | 快判：路由/归因/短动作 | ACTIVE（3–4s，不换页） |
| server | bm-d | 重判断/规划/量化重批/创意方向 | PENDING，等入网 |
| cloud | 付费席位 | 前两层都判不了的方向与仲裁 | 由 agent 会话执行，单次≤50、当日≤200 积分 |

**升级不靠改代码**：bm-d 入网后填 `LANES['bm-d'].llm.endpoint/model`、把 `tiers[server].state` 改 ACTIVE，`local_judge` 自动优先 server，本机降为兜底。

### 科学的两条纪律

1. **不许越级硬判**：上一层明确说「判不了/证据不足」才升下一层；任何一层不得改写问题以使自己能判。
2. **不许装能上云**：`router.py` 的 cloud 分支是占位符，脚本不得声称上过云；判断题进 `ESCALATED`，由会话执行并留痕。


## 七、主控职责增补（CEO 令 2026-11-04 三连·正身=本节+令总线广播）

> 原话①「你的任务首先是主控电脑给你，实在没有才是自己给自己排」②「机队没活就赶紧找主控要，并通知主控早早准备好」③「主控 MACBOOK 也要完全知道自己的职责，并随时准备好给机队各个机器的进度和未来要做什么了解和安排好」

1. **need-work 响应**：见 `cph4/fleet/state/need-work/<node>.json`（车道无派单且申报池无可晋升行时自动挂出）→ 该车道 P0 优先派单（目标 2 秒内）；派单后确认旗标撤除。
2. **备单制（随时有活可派）**：每条活动车道常备 ≥3 张输入就绪、可立即派发的卡——backlog 晋升预检（每小时）+ line_plan 工序预生成（对 LINE-REGISTRY 中 STALLED/PARKED/NO-DATA 段提前备卡）。
3. **进度总览与未来安排（随时可答）**：
   - 每轮脉：刷新 `dispatcher/MASTER-STATE.json`（各机 hb/容量/在办/last_result + 线段判读 + 违规清单）——主控脉既有段，保持；
   - 每日：产出「机队进度与备单板」`queue-receipts/bm-m-fleetboard-<YYYYMMDD>.md`（逐机：在办/最近产出/卡点/下一步 + 每机 ≥2 张备卡）；workgen 每日滚动生成次日板行（R-FLEETBOARD-<date> 模式）；
   - 既有节奏保持：NEXT-ACTIONS-<date>.json / NIGHT-PLAN-<date>.md / FORECAST-<date>.json / DAILY-OUTPUT-REPORT.md / SYNC-BOARD.md / WAIT-MAP.md。
4. **自知道义务**：每次执行主控侧行（workprep / fleetboard 等）先重读本节与 WORK-RULES 对应行 prompt，只按盘上文件事实作答，不编造。
5. **待办工程项（机队窗口协同）**：
   - agent state 推腿缺口：pull() 自动收口不提交新建的 `cph4/fleet/state/**` 文件（need-work 旗标出不了机箱）——正法=OUR_OUTPUT 增 `cph4/fleet/state/` + 对自有未跟踪 state 件 git add（详见 queue-receipts/NEEDWORK-LASTMILE-20261104-bm-b.json）；
   - bm-a/bm-c 各自窗口自查 FleetAgent 克隆新鲜度（git -C <clone> rev-list --count HEAD..origin/main）并重启常驻加载 need-work 新码。
