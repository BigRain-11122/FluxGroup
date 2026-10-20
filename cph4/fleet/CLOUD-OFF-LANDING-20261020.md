# 云道停用落地台账（2026-10-20）

> 令源：CEO 2026-10-20「集团业务全部停止走云端，全部走本地了」（T0）。
> 权威口径：`cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md`。本件=执行面落地记录，不另立法条。
> 原则：**执行面改口径；历史件零改写**——日志、判例、确认件、研究件保持原文，改写等于伪造记录。

## 一、已改（22 件·口径级）

### 1. 法条正身（2 件·核心）

| 件 | 改了什么 |
|---|---|
| `cph4/token-economy.md` | 抬头注记；§10.1 六类白名单**全部冻结**（原文留档）；第 6 类「产能不足」单独标废止；§八 转冻结档 |
| `cph4/resource-chain.md` | 抬头注记；§一.0①「云端无限并行」废止；§二 云算力行改「已停用」；§三「云算力默认态」整节废止；§9.1.2 云端必要闸**①②废止，仅留 CEO 亲批** |

### 2. 调度面（3 件）

| 件 | 改了什么 |
|---|---|
| `dispatcher/DISPATCHER-CHARTER.md` | L2 承载改「工具壳·非业务生成面」；§三.2 判断改本地 35B 先试；§五 新增第 6 条**派单前云道闸**（含云端模型名的单=拒发） |
| `dispatcher/CEO-PROXY/ROUND.md` | 思考路由律 ③ 六类免试白名单冻结，仅 CEO 亲批 |
| `dispatcher/GAME-CLOUD-LANE-PLAN-v1.md` | **整单废止**（授权源 O-20261016-2145 已废），转存档，禁据以派云批 |

### 3. 产线正典抬头注记（14 件）

MV 线 10 件：`MV-PIPELINE-PLAYBOOK-v1`、`MV-PRODUCTION-PIPELINE-v1`（⑤视频/档位检/冲刺表/机队分工逐句改本地）、`PRODUCTION-SYSTEM-v2`、`AUTO-POLISH-LOOP-v1`（引擎与执行面改本地 35B）、`MV-PREPRO-MASTER-v1`、`QC-MASTER-CHECKLIST-v1`、`PRODUCTION-PLAN`（云端岗位行/任务行/配额行改本地）、`MV-0001-RETRO-ACCEL-v1`（三车道/节拍/行动①改本地）、`PROMPT-EXPERT-GATE-v1`（第 2 层专家审改本地 35B 优先）、`PROMPT-SPEC-v2-I2V`。

跨线 4 件：`DRAMA-PRODUCTION-SYSTEM-v1`（云端兜底条款废止）、`shortvideo-dept/PIPELINE.md`（SLA 与排班改本地链）、`meme-daily-v1/README-RUNBOOK.md`（「云端生成为主」改本地生成）、`FLEET-COMPUTE-ARCHITECTURE.md`、`mv0001-handover/outbound/H3-工作流升级清单-v1`（「正式镜头云端出」改本地 int8 主路）。

### 4. 索引（1 件）

`cph4/registry/law-registry.md`：抬头注记 + 新增「2026-10-20 一批·云道停用批」条目，标明被废/被冻的既往授权。

### 5. 工具（1 件）

`Tools/cloud_off_banner_r1020.py`：幂等注记脚本（可重跑，已注记件自动跳过）。

## 二、不改（有意保留原文）

| 类别 | 例子 | 理由 |
|---|---|---|
| 调度/巡视日志 | `PATROL-FLEET/LOG.md`（426 处）、`CEO-PROXY/LOG.md` | 运行史实，改写=伪造 |
| 云端确认/烧制台账 | `V59-CLOUD-CONFIRM-v1`、`V511-CLOUD-BURN-LEDGER`、`V53R-CLOUD-2shot-r1017` | 成本与调用证据，须原样可审计 |
| 评审/反馈记录 | `DIRECTOR-REVIEW-*`、`CEO-FEEDBACK-*`、`PANEL-*`、`REVIEW-PACKAGE` | 当时的判断依据 |
| 研究件 | `cph4/research/*`、`WIDE-*`、`R-*` | 云端模型官方能力仍是写提示词的参考资料，禁当生产授权 |
| 委员会案卷 | `cph4/council/C-*` | 立法档案，状态由 law-registry 注记 |
| 冷层归档 | `memory/archive/*`、`evolution-ledger-archive` | 归档面不执法 |

## 三、扫描数据（2026-10-20 实跑）

| 范围 | 改动前命中 | 改动后残留（排除含 T0/停用/废止/冻结 的行） |
|---|---|---|
| `cph4/**/*.md` | — | 182 文件 / 1295 处 |
| `cph4/fleet/**/*.md` | 113 文件 / 865 处 | 96 文件 / 809 处 |
| MV 线（`mv-album-001-jay` + `mv0001-handover`） | 55 文件 / 158 处 | 52 文件 / 117 处 |

**读数纪律**：残留≠违令。绝大多数是日志、判例、研究引证，以及「云端已停用」这类说明性文字本身。

**工具层扫描**：`Tools/` 与 `cph4/skills/` 内命中云端 API 域名的仅 3 个文件，且都是文档引用，**没有云端调用代码**。结论：本集团的云端调用一直走交互式 MCP 工具，不是脚本——所以停云只能靠**派单闸+纪律**落地，不存在"改一个开关就停"的代码位。

## 四、未完成（按优先级）

1. **派单卡无机械校验**：`POOL.json` / orders 行仍可能写入云端模型名，目前靠 L2 过闸（CHARTER §五.6）人工拦；缺一个 lint 断言。
2. **云端凭据未清点**：环境变量/API key/订阅未逐一登记封存状态。T0 要求「冻结备用、不删、不新增」，现在只有口径，**没有清单**。
3. **在飞云任务未逐条盘点**：`cph4/fleet/h3-local-test/outbound/cloud/` 存在但未核内容与归属；需确认无遗留付费任务在跑。
4. **本地产能预算未量化**：bm-c 单卡日通量 vs 41 曲需求没有算过，排队要排多久是未知数。
5. **装机补齐未动**：Wan2.2-Animate（i2v 表演控制）、LatentSync（口型）仍未装。
6. **「代理脑」边界待 CEO 明确**：本会话本身跑在云端模型上。本件按「工具壳、非业务生产」处理（`DISPATCHER-CHARTER` 已注），但这属解释而非 CEO 原话，**列为待裁项**。

## 五、诚实边界

- 本件只改了**文档口径与派单纪律**；未验证任何本地替代件的实际产出质量。
- 数量全部为词面计数，不代表违规判定，也不代表产能结论。
- 「规则改完」不等于「已经在本地跑通」；真正的验收是下一条片子在无云条件下出得来。

## 六、自动化闸门（追加令 2026-10-20 18:3x「自动化任务全部走本地，不要再消耗云端 token」）

### 6.1 做法

不做逐台停计划任务，而是在**拉起云端会话的那一行之前**加统一闸门：

```powershell
$__co = $PSScriptRoot   # 向上找仓库根，命中 cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md 即拦
... 记一行 media/logs/cloud-off-suppressed.log ... exit 0
```

好处：本地前置工作（读旗/锁/预算/pulse）照常，只有云端回合被掐；解令=改名或删除该正典，不必重新注册任务。

### 6.2 覆盖 16 个脚本

| 线 | 脚本 |
|---|---|
| 调度/巡视（7） | `patrol-runner`、`patrol-fleet-carrier`、`proxy-event-carrier`、`shift-supervisor`、`decision-round`、`evolution-tick`、`night-round` |
| 子公司循环（6） | BigStream / BigLife / BigDomain / BigCompute / BigMoney / FluxVerse 各自 `iteration_loop.ps1` |
| 游戏（3） | MiniGame `EngineTick`、`ModeTick`（8 个定时任务共用）、`BoardForge` |

### 6.3 验证与现场

- 16 个脚本 PowerShell 解析：**0 错误**。
- 闸门自测：退出码 0，日志确实落行。
- 现场：5 个 `codely.exe` 全部是 `--experimental-acp` 交互窗，**没有 `-p` 无头回合**。
- 保留运行：`HQ-FleetDispatcher`/`IdleWatch`/`MemoryBudgetGate`/`SilenceGuard`/`WT-Park`/`bm-a-Sentinel`/`OllamaOrphanWatch`/`OpenClaw`，以及各司纯 CPU 循环、`MiniGameTjcloudSync`（git 同步，零 token）。

### 6.4 副作用（必须说清）

**无人值守轮的 LLM 判断面全部暂停**：L2 八班、各域巡逻席、各司迭代轮不再自动点火。本地确定性巡班（派单规则、探针、心跳）照跑，但"发现问题后自动判断/落单"这一层现在没人做，只能等人工会话来处置。

### 6.5 仍然消耗 token 的

人开的交互会话（含本窗口）。要连它也断，需换本地模型跑 CLI——那是另一件事，须 CEO 明确。

---
*bm-a · 2026-10-20 · 承 CEO T0 云道停用令 + 自动化全本地追加令*