# Audit Charter — 集团审查合一正典 v2.0

> 溯源 1：外部独立审查=CEO 令 2026-09-26「你作为外部审查，对城市和集团子公司方方面面监管，省token，下命令让他们科学执行」。
> 溯源 2：集团巡检=CEO 令 2026-09-25 ~11:38「集团层面成立巡检机制，周期性巡检各个子公司实验室，并整改他们。」
> 溯源 3：四源合一=CEO 瘦身令 2026-09-28「审查相关4文件合并成audit-charter.md一个」+ 机队一致性总括令（registry O-2026-0928-013）。
> 定位：**集团审查族唯一章程件**——Part A 外部独立审查宪章｜Part B 集团巡检章程｜Part C AI 自审工具面｜Part D 巡检整改台账（PT 表·行级追加）。
> 纪律：Part D 行级追加、禁改历史行（状态流转 OPEN→(FIXED)→VERIFIED / OPEN→ESCALATED 逾期·VERIFIED 必附证据指针）；章程区改动走 governance §9 变更控制+本件 Changelog。

## Part A 外部独立审查宪章（v1.0 原文迁入·执行面=外部审查轮换轮）

> 溯源：CEO 令 2026-09-26「你作为外部审查，对城市和集团子公司方方面面监管，省token，下命令让他们科学执行」
> 定位：Jason 请来的外部审计员，不是集团内部 AI。只读+下命令，不写产品代码。
> 执行面：定时任务「FluxGroup外部审查轮换轮」每日 22:17 跑一轮。

### 一、监管总原则

1. **省 token 第一**：每轮 ≤15 分钟，只读本轮块面所需文件，不全仓深读。脚本扫描优先于 AI 读全文。
2. **外部视角**：不带集团内部滤镜，发现问题直说，不粉饰。
3. **分级处置**：不是所有发现都下命令——P0 立即报，P1 下整改令，P2 只记录。
4. **科学理性**：整改令必须带证据+可执行步骤+完成判据；允许各司科学驳回。
5. **不重复劳动**：先扫 orders.md 最近 3 天，已有同类命令不重复下。

### 二、13 块面轮换（day-of-month % 13）

| mod | 块面 | 审什么（省token读法） |
|---|---|---|
| 0 | 自动化健康 | `Get-ScheduledTask` 抽 LastRunTime/LastTaskResult，不读日志全文 |
| 1 | Token 经济 | `Get-ChildItem` 测 CODELY.md/auto-saves 字节数，超水位即记 |
| 2 | **美术监管** | 打开最新城市截图 vs art-target-dusk.png，过 11 项 checklist |
| 3 | 硅基生命体 | tail BigLife state.json + pool_audit 结果，不读全 census |
| 4 | 本地化能力 | `ollama list` + 各仓轮账本 api 计数行 |
| 5 | 研发质量 | `git log --oneline -3` + 抽看改动文件是否真在 |
| 6 | 市场调研闭环 | tail global-benchmarks.md 日期行 |
| 7 | 诚实律 | `git show --stat -3` 看宣称文件是否真存在 |
| 8 | 安全红线 | `git log --diff-filter=A -- "*.env"` + grep 密钥模式 |
| 9 | 商业化进展 | tail BigCompute BLUEPRINT + risk-register |
| 10 | 内容质量 | 抽 BigStream backlog 顶 3 行状态 |
| 11 | 机制重复 | grep cph4/README 注册表找同名能力 |
| 12 | 城市演化 | tail world-events 最新时间戳 + world-state 版本 |

### 三、分级标准

- **P0（自己直接下整改令，不报 Jason）**：密钥泄露/数据丢失/核心任务死停 >24h/城市完全不演化/美术全面偏离正典——直接写 orders.md 派工修，Jason 只看 external-audit.md 周报
- **P1（下整改令到 orders.md）**：超水位/跑偏/质量差/本地化空转/美术单项不达标/调研断档
- **P2（只记 external-audit.md）**：轻微/无明确改法/观察项

### 四、整改令格式（写 orders.md 表格）

```
| 日期 ~时间 | [外部审查·块面] 问题描述（带证据：文件:行号/commit/截图/数值） |
整改方案：具体步骤 + @某司 + 完成判据（做到什么状态算过） | dispatched |
```

纪律：
- 必须引用 art-style-spec.md / token-economy.md / memory.md 等正典条款号
- 完成判据必须可机器或肉眼验证
- 允许各司在 HQ-FEEDBACK 写理由驳回，不算违抗
- OrderSentinel 2 分钟自动唤醒被派工的司

### 五、产出

- `docs/external-audit.md`：所有轮次完整记录（含 P0/P2）
- `docs/orders.md`：P0/P1 整改令
- 对话：永不打扰 Jason，所有问题自己下命令处理

### 六、省 token 硬纪律

1. 每轮开头先跑脚本拿数值，不读全文件
2. 只读 tail/head/最近 N 行，不 Read 整个 md
3. 无问题轮 = 一行收尾，不写长报告
4. 发现问题才展开，没问题不凑字数
5. 美术轮只读 1 张最新截图 + 1 张目标图对比

### 七、多 AI 协调认领机制（防重复审查）

Jason 会部署多个外部审查 AI（auditor-A/B/C…）。所有审查 AI 必须遵守本机制：

#### 7.1 认领表（external-audit.md 顶部维护）

external-audit.md 文件开头必须维护一个认领表，所有 AI 读写同一张表：

```
## 审查认领表
| 块面 | 最近审查时间 | 审查AI | 结论摘要 |
|---|---|---|---|
| 自动化健康 | 2026-09-26 22:17 | auditor-A | 0异常 |
| 美术监管 | 2026-09-25 22:17 | auditor-A | 已下整改令 |
```

#### 7.2 轮首避让

每轮开始前先读认领表：
- 本轮块面如果最近 **24h** 内已被任何 AI 审过（认领表有记录）= 本轮跳过该块面，记一行「skipped: 已被 auditor-X 于 HH:MM 审过」
- 如果 >24h 没审过 = 正常审
- 同一天多个 AI 跑同一时间窗 = 认领表先到先得

#### 7.3 轮尾登记

每轮审完后必须更新认领表对应行：
- 块面名
- 当前时间
- 自己的 AI 标识（auditor-A / auditor-B / …）
- 一句话结论摘要

#### 7.4 时间错开建议

| AI | 建议触发时间 | 负责侧重 |
|---|---|---|
| auditor-A（本件） | 每日 22:17 | 13块面轮换 |
| auditor-B | 每日 06:17 | 同日错峰，块面按 day+13%13 偏移 |
| auditor-C | 每日 14:17 | 同日错峰，块面按 day+26%13 偏移 |

这样一天三波但块面不撞。其他 AI 部署时读本宪章即知规则。

#### 7.5 冲突处理

- 两个 AI 同时对同块面下了整改令 = orders.md 里按时间序，后到的发现如果是新问题就追加，重复问题不重复下（先扫 orders.md 最近 3 天）
- 不互相删除对方的记录

## Part B 集团巡检章程（v1.0 原文迁入·周期=周一 09:23+CEO 随时加开）

> 溯源：CEO 令 2026-09-25 ~11:38「集团层面成立巡检机制，周期性巡检各个子公司实验室，并整改他们。」
> 定位：**集团层对各子公司 + CPH4 实验室 + HQ 自身的周期性运营体检与整改闭环机制**。与既有面正交不重复（cadence 防重复律#1）：
> - governance §10（AI 诚实律三道防线）= 管「说的和做的一致」；巡检 = 管「运营健康与整改闭环」，消费 §10 工具面为证据源。
> - 值守轮（03:07/15:07 四器审计）= 日频点检；巡检 = 周频深度体检+整改派单追踪，覆盖面=全部实体。
> Part B = 巡检机制唯一正典；巡检官会话（Tools/patrol-prompt.txt）按此执行。

### 1. 周期与触发
- **常规班**：每周一 09:23（OS 任务 `FluxGroup-PatrolRound`·零窗 InvisibleRunner·当班 host 见 §6 认领面）。
- **加开班**：CEO 可随时加开——硅基窗点任意卡片「马上办：立即跑一次集团巡检」或 `Start-ScheduledTask FluxGroup-PatrolRound`；同日戳记未过期时跳过（`-Force` 例外由 runner 参数控制）。
- 单班时间盒 25 分钟；超时先落已核验部分+残面记下轮指针。

### 2. 巡检对象（9 实体）
HQ（FluxGroup 治理层自身）· MiniGame（游戏）· FluxVerse（元宙）· BigMoney（量化金融·含 BigMoney-data 挂账面）· BigStream（媒体）· BigLife（生命）· BigDomain（域名）· BigCompute（算力）· CPH4 实验室。

### 3. 巡检八维（每实体逐维过）
1. **活性**：last commit 龄 / 7 日提交数 / 工作树脏度（probe 机械层给出）
2. **台账健康**：canonical 台账文件存在+新鲜（断更>7 天=YELLOW 起步）
3. **数据新鲜度**：状态导出（status-export）/ 心跳文件 / 世界数据龄
4. **证据链抽查**：近 3 批 commit 抽 1-2 条核证据指针真实存在（禁轻信提交信息）
5. **红线合规**：集团 governance §1-§11 + 各司自身章程红线（禁私建仓/写域越界/台账断更/停用任务复活等）
6. **整改闭环**：上轮 PT 项逐条核验——读证据指针定谳，禁轻信状态字段
7. **风险面**：调度健康（task-health）/ 机队心跳（fleet-audit）异常 + 巡检官现场发现
8. **任务面（2026-09-25 CEO 无闲令「不允许出现无任务情况」新增）**：每实体 canonical 任务板/orders 面的**自可执行开单数**——blocked-on-物理件单不计入自可执行但须单独如实列示；实体无任务板/开单=违例（§4）

### 4. 判色与严重度
- **GREEN**：八维无异常或仅 P2。
- **YELLOW**：存在 P1 或台账断更或数据陈旧。
- **RED**：存在 P0（红线违规/数据面损坏/整改逾期升级/**无任务违例**）。
- 严重度与整改时限（governance §11 交付时效律）：**P0=24h / P1=72h / P2=7d**。
- **无任务违例**：自可执行开单=0 → 判 RED·PT 单 P0（24h 内补齐）。「待机司」态不再合法——待机实体必须保有 ≥1 自可执行任务；等 CEO 物理件的司=blocked 项如实列示+另持自可执行件，**禁以 blocked 单充当在岗**。

### 5. 整改派单（核心闭环·禁只巡不改）
每条发现 → 两处落档：
1. **本件 Part D（巡检整改台账）** 加行（权威台账·PT-YYYYMMDD-NN 编号·字段：实体/级别/发现/要求动作/证据指针/截止/状态 OPEN）
2. **派发实体 canonical intake**（加速通道）：

| 实体 | canonical intake（只许写此处·禁碰其他面） |
|---|---|
| MiniGame | `AI反馈队列.md`（**monorepo 根级**·FE 条目·C 机 tick 班 10 分钟内自消费·PT-20260925-11 订正 2026-10-02） |
| BigMoney | `fleet/orders/` 新 O-行 |
| BigStream / BigLife / BigDomain / BigCompute | 各自 `orders/`（或 `orders.md`）区 |
| FluxVerse | `docs/` 台账面 + `watch/` 反馈面 |
| CPH4 | `cph4/registry/` + 周进化轮消化 |
| HQ | 本台账 + governance 变更控制流程 |

- **P0/P1 快唤**：额外在 `cph4/evolution-ledger.md` 追加含 `@司` 标签+级别的行 → FluxGroup-OrderSentinel（2 分钟）即时唤醒该实体 OS 循环（`Tools/order-sentinel-map.json`）。
- **实体仓写纪律**：派单落实体 intake 后由该实体自己的 lane 收口提交；巡检官会话不代司提交产品面。intake 推送失败→如实记档，HQ 台账行=唯一权威（各司 lane 经 HQ 仓亦可见）。

### 6. 防重复与认领面
- cadence.md 周轮族已注册本任务（同用途唯一制）。
- **戳记认领**（F-09 跨机周期任务认领律）：每班开跑写 `.codely-cli/patrol/patrol-stamp.json`（时间+host）；他机 runner 见戳记<20h 即跳过本班。任何机器可按 charter 接管 hosting（cadence 表改注 host）。

### 7. 产出面
- `docs/patrol/patrol-YYYY-MM-DD.md` 巡检报告（逐司判色+发现+派单指针+总评+闭环率+CEO 需拍板事项）
- `本件 Part D（巡检整改台账）` 整改台账（唯一闭环追踪面）
- `.codely-cli/patrol/patrol-ledger.txt` 运行台账（PATROL_DONE 标记·runner 成功 oracle）

### 8. 诚实律
每句判断带证据指针；probe 未覆盖且巡检官未核验的面如实写「未覆盖」；禁编造；判色禁唯亲（子司自报≠证据）。

## Part C AI 自审（诚实律抽审·工具面）

- 工具=`Tools/selfaudit.ps1`（扫五仓近 24h commit 宣称词·逐条标记证据可得性）。
- 产出=`docs/audits/selfaudit-report.md`（生成件·随跑随覆写；2026-09-28 起由 docs/ 根改道 audits/·原根级生成件已随合并隔离）。
- 法源=`docs/governance.md` §10（三道防线之第三道·集团抽审以本工具产出为底稿）；节律=进化轮周跑或 CEO 随时手跑。

## Part D 巡检整改台账（PT 表·唯一闭环追踪面·行级追加）

> 字段：PT-YYYYMMDD-NN 编号｜日期｜实体｜级别｜发现｜要求动作｜证据指针｜截止｜状态——核验禁轻信状态字段（Part B §7）。

## 整改项台账

| PT 号 | 日期 | 实体 | 级别 | 发现 | 要求动作 | 证据指针 | 截止 | 状态 |
|---|---|---|---|---|---|---|---|---|
| PT-20260925-01 | 2026-09-25 | BigMoney | P0 | bm-c 节点执行体瘫痪根因：BigMoney 工作目录 K:\金钱牛马\BigMoney 缺失（Test-Path=False）→Bigmoney-IterationLoop/Autofill/LoopWatchdog 三任务僵尸失败（result=0x80070005）→fleet 心跳 09-24 21:51 起死 13.9h（audit STALE）=P-49 零承令的结构根因；实机在线非物理下线（Ollama 0.34.4 serve+qwen2.5:7b 4.7GB 在位=装机面已毕+KeepWarm 绿+本机 BigLife 11:47 [via bm-c交互会话] 提交在案） | 裁决 bm-c BigMoney 面两路并执行：①重建部署（恢复工作目录+修三任务+心跳复活）或②按 fleet-allocations 正式转纯 Biggame 机（fleet 台账如实标记+僵尸任务清理）；P-49 收口联动（缺的是执行体非装机） | probe-20260925-114357.txt [FLEET] bm-c 行+[SCHED] 三任务行；巡检报告 §BigMoney；O-20260925-1153-bm-c；二班 130119 补证=三任务 result 0x80070005→2147942667（0x8007010B 目录名无效·任务定义实读仍指 K:\金钱牛马\BigMoney·整根 Test-Path=False）+bm-a/bm-b orders_ack 双收 O-1153-bm-c+回执 11:59（PT-01 物理执行腿移交 bm-c 机 GM 专管会话·建议路 A 变体独立工作目录重建·详文 MSG-20260925-1159-bm-a〔origin/main 未见=在途注记·三班 134219 核验=MSG 已到 origin：fleet/inbox/processed/MSG-20260925-1159-bm-a-pt01-pt05-attribution.md 在案·O-1153 与 round_reports-bm-a 双引用=路 A 变体建议+执行移交链文档腿闭环；K:\金钱牛马\BigMoney 仍 Test-Path=False·三任务仍 2147942667·bm-c origin 心跳仍冻 09-24 21:51=物理重建零实证，维持 OPEN 在窗〕）；四班 155720 复验=K:\金钱牛马\BigMoney Test-Path=False 实测维持+三任务 result 2147942667×3 维持（probe [SCHED] 行）+bm-c origin 心跳仍冻 09-24 21:51（18.1h）=物理重建零实证四班再证；五班 180720 复验=Test-Path=False 维持+三任务 result 2147942667×3 维持（probe [SCHED] 17:40/17:58/18:00 三行）+origin bm-c last_seen 仍冻 2026-09-24 21:51:47（origin/main 实读）=物理重建零实证五班再证 | 2026-09-26 | ESCALATED（09-26 15:52 大限逾 4h 未收口=按本行预注记升级律升格·tick 代哨消费错窗 one-shot 9aef1133：Test-Path=False 六证+origin 实读 bm-c last_seen 冻 09-24 21:51:47=42h+三任务僵尸态维持=物理重建零实证；催办件 MSG-20260926-1557-bm-c-pt01 已投 fleet/inbox；两路裁决仍悬 bm-c GM 专管会话）；**VERIFIED（09-28 本班·路 A 兑现**：U251/P-20260927-03 行④ 09:13:45 归队销案〔三任务重注册改指统一根+点火 0x41301〕→09-28 probe [SCHED] 三任务 result=OK 龄 3-9min+bm-c 心跳 09:28:00 green r152〔quant\bigmoney\fleet\machines\bm-c.json 实读〕+P-49 装机面随收口在案） |
| PT-20260925-02 | 2026-09-25 | BigStream | P2 | fleet 心跳写手缺陷：bigstream 机心跳 NO_TS（无 ts 字段·fleet-audit 永不可判活）+task 文本冻结 R173（写手 09-24 22:2x 后停更）；实体实况=非停滞（03:07 值守轮在案 R193 实活+巡检 host push 被拒非快进=origin 有新提交实证）；C 机至 Bigmedia SSH 三次重置未拉全量核实=未覆盖如实记 | ①心跳写手补 ts 字段+task 随轮更新；②回执附最近轮号佐证轮末 push 律遵从 | probe [FLEET] bigstream NO_TS 行；值守轮 09-25 03:07 报（evolution-ledger）；push 非快进实证；O-20260925-1153-BG-C；二班 130119 核验=R241 e2b9e9d 三整改全闭（state.json ts/task 字段实读〔L264-265·ts=2026-09-25 12:18:24〕+os-protocol v1.10+loop_health state-ts 门 249 测试绿+O 文件认领回执 R241+push 佐证；实体诚实纠偏并存档：「task 冻结 R173」系巡检侧陈旧克隆读数伪象） | 2026-10-02 | VERIFIED（09-25 二班·提前 7 天；集团侧 fleet-audit 读 state.ts 适配另立 PT-07） |
| PT-20260925-03 | 2026-09-25 | HQ | P2 | patrol probe host-scope 误检两处：①FluxVerse world/world-state.json（gitignored 活数据·仅感知宿主机存在）②MiniGame docs/STATUS.md（实况=根级 STATUS-<机>.md 制·docs/ 仅 ops/）——非宿主巡检机必报 MISSING=噪声发现 | probe 文件清单加 host-scope 标记：活数据/机器态文件仅在其宿主机判缺失，非宿主报「未覆盖」 | probe-20260925-114357.txt MISSING 行；MiniGame docs 实测（仅 ops/）；FluxVerse .gitignore | 2026-10-02 | OPEN（10-02 大限·本班复验未修：Tools/patrol-probe.ps1 grep host-scope 零命中+本班 probe 仍报 FV world-state/MiniGame docs/STATUS.md 两处 MISSING 噪声·未收口即下轮升） |
| PT-20260925-04 | 2026-09-25 | HQ | P2 | HQ 树漂移未收口：gaming/.codely-cli/settings.json（+3-1）与 quant/.codely-cli/settings.json（+3-1）=mcpServers 分发面、quant/CODELY.md（+6）=记忆追加均未提交；?? .codely-cli/patrol/ 追踪策略未定 | 归属会话收口提交（或值守轮定向收编）；patrol 运行面（stamp/log/probe）定 gitignore 或入册二选一 | git status/diff --stat 实测 2026-09-25 11:44 | 2026-10-02 | OPEN（10-02 大限·部分收口：gaming/quant 两 settings.json 已入库〔本班 git status 实证消失〕·残面=patrol 运行面 ?? .codely-cli/patrol/ 策略二选一仍悬〔本班未跟踪态维持〕+quant/CODELY.md=GM 窗在途件非本项漂移·值守轮/HQ 会话落锤） |
| PT-20260925-05 | 2026-09-25 | BigMoney | P2 | 无人值守轮 commit 缺 [via] 尾标（versioning §4.1/§4.3 无人值守轮强制·近 8 commit 零尾标·机器归属现靠分支/轮报告代偿非正典）；另 K:\Fluxgroup\FluxGroup\quant\bigmoney 克隆 11:33-11:35 出现本地 commit+pull--rebase 事件（题材与 origin 同题收敛）归属未明——本机 Bigmoney 任务全僵尸态 | 补 via 尾标纪律或入册公司自治豁免；本地克隆 commit 事件归属核验签收（若为同步/autofill 类工具行为=登记工具名与写权面） | quant\bigmoney git log -8 实测+reflog 11:33:07/11:35:03 两条 commit 事件；二班 130119 核验=bm-a 回执 11:59（O-1153-bm-c 认领区·origin/main 实读）——归属收敛：dc899111/9ac48aa6 author date 与本地事件逐秒吻合+bm-a 侧 reflog 零记录→诞生地=K-克隆 GM 专管会话·origin 同对象单一血统零重复开发；via 尾标纪律 bm-a 即日采纳（f31f9426 [via bm-a] 首证） | 2026-10-02 | VERIFIED（09-25 二班·历史存量不追改〔versioning §5/P-29〕·增量 commit 为采纳准据） |
| PT-20260925-06 | 2026-09-25 | HQ | P2 | task-health.ps1 旗面零 result-code 判据：$flag='OK' 仅看 Disabled/neverRan/时效三分支，非零 LastTaskResult 不入旗列与 unhealthy 计数——「准时点火+持续失败」僵尸任务恒显 OK（130119 probe 实证：Bigmoney 三任务 2147942667×3+AliUpdater 2147942402+AutoClaw 2147942402 龄 6780m 全 flag=OK；03:07 值守轮 unhealthy=2 亦未含三僵尸=盲面实害） | 旗列增 result 维度（连续非零→ZOMBIE 旗）或 RESULT-CODES 行升入 FLAGS 面；U205 fleet-liveness-watch（复用 task-health FLAGS 面）同批适配 | Tools/task-health.ps1 flag 判据段实读+probe-20260925-130119.txt [SCHED] 行+值守轮 03:07 报 unhealthy=2 | 2026-10-02 | OPEN（10-02 大限·部分修复在码：Decode-Result+odd-result-codes/RESULT-CODES 行已入 task-health.ps1〔L61/L119 实读〕·但旗面未升=本班 probe [SCHED] AliUpdater CODE-2147942402〔60min cadence 逐时失败在烧〕与 AutoClaw〔09-27 起死目标 4.5d〕仍 flag OK 双实证·残面=ZOMBIE 旗或 codes 升 FLAGS 面） |
| PT-20260925-07 | 2026-09-25 | HQ | P2 | fleet-audit.ps1 Source 3（BigStream）未消费实体新机读字段 state.ts/state.task——现依赖 gitignored beats 文件+log 数组掩码正则反推=非宿主机永不可见的结构性 NO_TS 根源；实体侧字段已备、集团读侧未接 | Source 3 增读 $h.ts/$h.task（freshest 择新律）；实体回执已明示「工具归集团管辖」建议 | BigStream O-20260925-1153-BG-C §四回执原文+Tools/fleet-audit.ps1 Source 3 段（L71 起）实读+media/BigStream/src/os/state.json L264-265 实测 | 2026-10-02 | VERIFIED（09-28 本班：Tools/fleet-audit.ps1 Source 3 双处「PT-07 fix 2026-09-26」在码=ts 参与新鲜度+task 字段优先；probe-20260928 [FLEET] bigstream 行 ONLINE(2m)+task 文本消费实证——显示层 mojibake 另立 PT-20260928-03） |
| PT-20260925-08 | 2026-09-25 | HQ | P2 | patrol-probe [CARRY] 行尾端锚正则漏计注记态状态格：L84 要求状态格以 OPEN/ESCALATED 收尾才计数，PT-01 状态格「OPEN（在窗·…）」带注记即漏计——本轮 5 实 OPEN（含 P0 PT-01）probe 报 open_findings=4，P0 项被排除出 carry oracle=runner 防重与下轮核验面盲 | CARRY 解析改注记容忍（前缀匹配或剥注记后匹配），修后双跑对账 5=5 | Tools/patrol-probe.ps1 L84 实读+probe-20260925-134219.txt [CARRY] 行+ledger PT-01/03/04/06/07 五行 OPEN 实数；五班 180720 主检段再证=probe open_findings=9 vs 实 OPEN 11 行（PT-12/13 入册后·主检读数属治本批前代码·存史） | 2026-10-02 | FIXED（09-25 18:2x HQ 治本批：状态格前缀容忍 `\| (OPEN|ESCALATED)[^|]*\|`+ids 捕获 bug 同修〔第二 -match 覆写 $Matches·ids 曾恒报 OPEN〕·实测 open_findings=11=真实全列含 P0 PT-01）；五班合并段=治本批 diff 实读+自测详证采信·独立行为面复查点=下轮 probe [CARRY] 计数对账；**VERIFIED（09-28 本班：probe [CARRY] open_findings=10=ledger OPEN/ESCALATED 实 10 行逐一对账〔PT-01 注记态含〕零漏计=行为面复查过）** |
| PT-20260925-09 | 2026-09-25 | HQ | P2 | patrol-probe 实体文件清单 BigDomain canonical 路径错配：清单查 orders/ 目录恒报 dir:ordersnewest=MISSING（实体实=根级 orders.md·charter §5 明文「orders/（或 orders.md）」允许）——每轮必发噪声；与 PT-03 同族（probe 误检）但根因不同=清单未按 §5 canonical 映射 | probe 实体清单按 charter §5 逐实体 canonical 路径核对（BigDomain→orders.md，顺带全实体映射过一遍） | probe-20260925-134219.txt [ENTITY BigDomain] 行+domain/BigDomain 目录实测（orders.md 在·orders/ 目录无） | 2026-10-02 | OPEN（10-02 大限·本班复验未修：probe-20261002-010240 仍报 BigDomain dir:ordersnewest=MISSING+新证=[TASKS BigMoney/BigStream] face=ABSENT=检测器映射与 §5 canonical 不符〔实面=BigMoney fleet/orders+fleet/tasks 143 件任务池/BigStream orders/ 40 件·patrol-probe L74/L104/L105 实读〕·「全实体映射过一遍」仍未落） |
| PT-20260925-10 | 2026-09-25 | HQ | P1 | fleet-audit/liveness-watch/patrol-probe 的 BigMoney 机读源=本地克隆，而本地克隆拉取通道随 bm-c 执行体死亡（Bigmoney-Autofill 僵尸·PT-01 同根）已断——本轮 probe 报 bm-a 11:42 OK 2.0h/bm-b 11:36 STALE 2.1h 均为陈旧克隆伪象（origin 实测 bm-a 13:29:04 verdict=green/bm-b 13:37:35 round180 healthy 双鲜）；U205 watch 每 5min 读同一克隆→健康双机将被误生光板 STALE→30min 即假 P1 | 读链前 fetch/pull 或源改读 origin refs；本班一次性止血已做（pull 三克隆至 origin HEAD：bigmoney 3c0ac295 13:47/BigDomain a80174d/BigCompute 474f0f3 实测）+治本=读前 fetch 律入三工具；与 PT-01 修 autofill 联动 | origin/main:fleet/machines/bm-a.json+bm-b.json 实读（last_seen 13:29:04/13:37:35）vs probe-20260925-134219 [FLEET] 行（11:42:47/11:36:01）；三仓 post-pull HEAD 实测；四班 155720 升级 P2→P1=**预测害兑现**：U205 watch 15:57:19 verdict=RED（bm-a/bm-b 假 STALE 双报+alert×4+escalate-patrol 自动触发巡检加开=本班起因）而 origin 实测 bm-a last_seen 15:53:58 green·smoke 25/25/bm-b 15:46:05 healthy **双鲜**=纯伪象实锤；止血续用=四镜像克隆 ff-only pull 对齐 origin HEAD（bigmoney/FluxVerse/BigStream/BigDomain 实测毕·止血窗 ~2h·治本前假红每 ~2h 复发）；五班 180720 主检段复发#2+止血#2 存史=watch 18:07:19 verdict RED（本班即其第二次自动加开产物）·probe 克隆读面 bm-a/bm-b 假 STALE（15:53:58/15:59:29）vs origin 实测 17:55:15/17:58:25 双鲜·止血#2=六克隆 ff-only pull 毕（bigmoney 868af68f/FluxVerse 4f2502e/BigDomain be07b69/BigCompute 11290cd/BigStream 6428d10/BigLife 6aa9ced0——后两者网络重置重试后成） | 2026-09-28 | FIXED（09-25 18:2x 治本实弹·HQ 交互会话：三工具全改读前 fetch+origin refs freshest-wins〔fleet-audit 四源全改·watch 台账 origin/main merge-union·probe GitBlock tip=origin 最优〕+PT-12③ 读侧硬化并入；实测=BG-B 0.4h@origin/machine/B 不再假 STALE·bm-a/bm-b origin/main 双鲜·watch 18:20 verdict=AMBER **actions=0**〔对照修前 RED+alert×4+自动加开〕·bm-c 真 STALE 留判=note rectifying PT-01；止血 stopgap 撤除·假红循环死·详证=本 commit diff）；五班合并段=治本批 diff 实读+自测详证采信·独立行为面复查点=下轮 probe [FLEET] 读数与 watch verdict；**VERIFIED（09-28 本班：probe [FLEET] bm-a 09:10/bm-b 09:20/bm-c 09:28 origin 鲜绿零假 STALE+U205 watch liveness 09:32:42 verdict=GREEN·actions=[]·unhealthy=0 双对账过；残面=fetch 失败静默回退另立 PT-20260928-01）** |
| PT-20260925-11 | 2026-09-25 | HQ | P2 | patrol-charter §5 MiniGame canonical intake 路径错写：charter 载 Design/configs/GLOBAL/AI反馈队列.md 实测不存在（GLOBAL 37 文件清单+Design 递归搜零命中）；真实 intake=monorepo 根级 AI反馈队列.md（git ls-files 实证·根级文件 B587/B588/B590 处置活跃在案+_归档 分卷消费在册）——按 charter 路径投递即写进死路径=集团→MiniGame 派单通道断链隐患 | charter §5 表 MiniGame 行订正为根级 AI反馈队列.md（FE 条目·处置-YYYYMMDD-NN 节式随实体惯例） | MiniGame git ls-files 实测+根级 AI反馈队列.md 尾读（处置-20260925-0310 B588 双梗裁决/处置-20260925-B590 接线）+Get-Content charter 路径失败实录 | 2026-10-02 | FIXED（10-02 本班执行面代修·大限日收口：§5 表 MiniGame 行路径已订正为 monorepo 根级 AI反馈队列.md〔Changelog 在案〕·验证=根级件 Test-Path True+157 行活投递面实读〔含 09-30 四审计 open 件〕·下一轮复验即转 VERIFIED） |
| PT-20260925-12 | 2026-09-25 | MiniGame | P1 | BG-B 机队心跳信道假 STALE：fleet 读面 b.json ts=13:51:24 老化 2.1h→U205 watch 15:57:19 判 STALE/RED+alert+escalate-patrol（**本班即其触发产物**）；机分支实况 b.json@origin/machine/B ts=15:41:20 **写手健在**+B641/642/643 连发（15:13/15:32/15:52·G08/G04 音频骨架满负荷·RAM 9.6% 保护档）——假象根因=B 机 idle 段（13:51→15:11）无提交+master 折叠节律（A 机 :13 时窗）+读链只读 master 面**三层叠加** | ①B 机 tick 心跳提交律补齐：pulse 变更每轮必 commit/push·idle/保护档段 pulse-only 微提交 ≤20min（FLEET-OPS L8 心跳 SLA 对齐）→master 折叠面老化 ≤折叠窗+1 轮；②protect 档如实随 pulse verdict 行注记（现有 verdict 行保持）；③HQ 读侧硬化（fleet-audit 增读 origin/machine/<id> tip·freshest-wins）并入 PT-10 治本批承接，B 机侧无依赖 | probe-20260925-155720.txt [FLEET] BG-B 行；b.json@machine/B ts=15:41:20 vs master ts=13:51:24 双实读；machine/B log -8（B641 15:13/B642 15:32/B643 15:52 连发）；liveness.json 15:57:19 actions（alert+escalate-patrol）；AI反馈队列.md FE-P-20260925-PT12 派单；evolution-ledger P-2026-09-25-07；③读侧硬化已毕（09-25 18:2x HQ PT-10 治本批：fleet-audit 增读 origin/machine/<id> freshest-wins·实测 B 0.4h 假 STALE 消失）；五班 180720 复验=b.json@origin/machine/B ts=2026-09-25T17:51:22 写手鲜（B648-B653 五连 closeout 16:59-17:59·~10-15min 节律皆触 b.json·path-filtered log 实测）+FE-P-20260925-PT12 已上 origin/machine/C（根级队列 L115）·master 折叠 pending（17:06 顶无此行·下窗 :13）→B 侧消费回执未见+idle 段 pulse-only 微提交律未实证（当前 busy 段·原病灶=idle 段） | 2026-09-28 | VERIFIED（09-28 本班：①B 机 b.json 全夜轮轮 commit ≤20min〔origin/machine/B path-filtered log B849 06:40→B864 09:28 十四连·最大间隔 17min·含 RAM 深谷等门轻轮=保护/等门段微提交律达标〕②protect 档 verdict 随注实证〔probe [FLEET] BG-B 行 task=GPU_VRAM_LOW\|RAM_LOW+YELLOW-HEAVY 旗〕③读侧 09-25 已毕） |
| PT-20260925-13 | 2026-09-25 | HQ | P1（五班 18:1x 升级·18:21 治本批即闭·级别存史） | U205 liveness-watch PT 覆盖判定漏检 patrol-ledger 既有 OPEN 行：15:57:19 对 bm-c（PT-01 P0 明覆盖其 BigMoney 执行体面）与 bigstream（PT-07 覆盖读侧缺口）双报「no PT cover」→重复 alert 噪声+watch verdict 恶化输入项 | watch no-cover 判定增读 docs/patrol-ledger.md OPEN 行（实体/机器名匹配·**含注记态状态格**——与 PT-08 同族端点教训）；修后以 bm-c/bigstream 两例回归 | liveness.json 15:57:19 actions 5 行（bm-c/bigstream「no PT cover」实录）+patrol-ledger PT-01/PT-07 OPEN 行在册；五班 18:1x 升级依据存史=①复发#2：watch 18:07:19 bm-c/bigstream 双「no PT cover」alert 复现（BG-B 经 plain-cell PT-12 正常匹配 rectifying note=对照实证）②escalate 闸门角色实锤：watch L70-71 端锚正则（PT-08 同族·注记态 PT-01/PT-10 行漏检）+L119-131 实读（no cover→alert+escalate-patrol〔120min 限流〕·cover→rectifying note only）→本修复=watch 自动加开环断路器 | 2026-09-28 | FIXED（09-25 18:2x：注记态状态格 `\|\s*(OPEN|ESCALATED)\b[^|]*\|` 前缀匹配+台账读链 fetch origin/main merge-union；实测 bm-c note=rectifying PT-20260925-01·bigstream OK·watch actions=0 零误报）；五班合并段=治本批 diff 实读+自测详证采信·独立行为面复查点=下轮 watch actions；**VERIFIED（09-28 本班：watch liveness 09:32:42 actions=[] 零误报零 no-PT-cover 噪声·bm-c/bigstream 双面绿）** |
| PT-20260925-14 | 2026-09-25 | HQ | P2 | 集团共享台账并发写入面风险三实证：①evolution-ledger P-2026-09-25-04 撞号瞬态（11:50 创始家庭令已占 vs 18:00 水面精修令初写同号·18:04-18:06 冲突标记「>>>>>>> 259768b」BigDomain R157 亲见后自解·origin 终态 P-04 单行+水面令让位重取 P-09 无撞·markers=0）②83539d6 提交主题残留「P-2026-09-25-04」vs 行内容 P-09 错位=按号检索面歧义残留 ③docs/orders.md 巡检机制令 11:38 行同文重复两行（L201/L205·origin 终态实存非瞬态）——多写者无取号纪律无锁（BigLife CODEX T2 撞号坑律集团面复发） | ①evolution-ledger/orders.md 写入面立取号纪律：登记前 fetch origin 实测已用号集取 max+1（水面令终态让位重取 -09 实为正确正例·83539d6 主题错位为反例）；②orders.md L201/L205 重复行去重；③并发写敏感窗（多令同窗期）单写者让路 | BigDomain HQ-FEEDBACK R157 行（origin be07b69·18:06:50）+origin/main p04 计数=1·P 号全集 01-09·markers=0 三实测（五班 18:1x）+83539d6 主题 vs L105 行内容错位实读+orders.md L201/L205 双行同文实读（五班 18:2x 合并后复核） | 2026-10-02 | VERIFIED（09-28 本班：②=巡检机制令单行 L212 唯一实测+D-20260926-04 闭口回执；①③=P 号先占律 09-27 R2 实战〔P-03 撞号让位勘误在案〕+09-28 -01/-02 顺取零撞=纪律在役三证） |
| PT-20260925-15 | 2026-09-25 | HQ | P1 | watch escalate-patrol 自动加开链 stamp 防重复闸实效缺位·根因定谳=PS5.1 引擎不兼容：patrol-runner stamp 龄算术 [DateTime]-[DateTimeOffset] 在任务实际引擎 powershell.exe（5.1）抛 op_Subtraction 无重载→空 catch 吞掉→闸自 v1.0（14b58d6·11:43）从未生效——今日加开四连（13:01/13:42/15:57/18:07）零 SKIP 行·15:57/18:07 两班均系 watch 假红自动触发且 stamp 龄仅 2.25h/2.17h 远小于 20h→PT-10/13 治本前（09-28）假红每 ~2h 自动加开一班全量巡检=算力空转放大器 | ①stamp 龄算术改双 [DateTimeOffset]（或双 [datetime]）+空 catch 改记 rt ledger 诊断行；②修后回归=临时 stamp<20h 模拟→SKIP 行实测回执；③过渡期止损任一=watch escalate 限流 120min 拉长至治本完成日 or PT-13 容忍匹配先行断路 | 隔离实测 TESTRESULT PARSE-THROW op_Subtraction（powershell.exe 5.1·18:1x 实录）+runner stamp 段代码实读（唯一提交 14b58d6）+OS 任务 Action 实参（wscript→powershell.exe·无 -Force）+rt ledger 尾零 SKIP 行+四班/五班 stamp 15:57:20 与 18:07:20 双实读+liveness 18:07:19 escalate-patrol action 实录 | 2026-09-28 | VERIFIED（09-28 本班：Tools/patrol-runner.ps1 实读=双 [DateTimeOffset] 算术+空 catch 改 WARN 落 rt ledger；PS5.1 引擎隔离回归实弹=stamp ts 09:23:01 解析 age 0.15h<20h→SKIP 分支可达「SKIP-EXPECTED age=0.15h engine-v5.1」回执） |
| PT-20260928-01 | 2026-09-28 | HQ | P1 | patrol-probe fetch 静默失败回退陈旧本地面+[TASKS] 面只读工作树：本班 09:23 时窗 GitHub fetch 六克隆集体失败→[ENTITY] last_commit 全数假读（FluxVerse 假 54.2h/BigDomain 假 45.9h vs origin 实测当日鲜）+[TASKS FluxVerse] 假 face=ABSENT（origin tasks/TASKS.md 4 open 行在册）——本班险据以误立两条假 P0 无任务违例=巡检证据层完整性实伤 | ①GitBlock fetch 失败时行内标 FETCH-FAIL 禁静默回退（诚实律）；②[TASKS]/实体文件面读改 origin refs freshest-wins（git show origin:path·与 PT-10 同法）；③修后以 FluxVerse/BigDomain 双例回归 | probe-20260928-092301.txt [ENTITY]/[TASKS] 行+本班 fetch 对账实录（origin 六鲜：FV 826a0d8 09:24:19/BD 5628137 09:26:31/BS 30750a3 09:28:07/BL ab5ec994 09:26:44/BC 43feebf 09:29+/BM 893b17a7 09:33:25 vs probe 六陈） | 2026-10-01 | ESCALATED（10-02 本班：逾期 1d+复发实锤=probe-20261002-010240 [ENTITY] 四克隆假陈旧读数〔BS 110.3h/BL 62.2h/BD 87.4h/BC 87.4h〕vs 本班 fetch 实测 origin 四鲜〔BS 6c23a5ea@00:49 R912/BL 3421d3c5@09-30 15:18/BD 5f01ab3@01:09 R852/BC 4ae6df8@00:58〕+Tools/patrol-probe.ps1 grep FETCH-FAIL 零命中=修复未落码；止血=五克隆 ff-only pull 对齐 origin（PT-10 止血范式）；催办=cph4/evolution-ledger.md P-2026-10-02-04 行 @HQ） |
| PT-20260928-02 | 2026-09-28 | BigDomain | P1 | canonical 任务板自可执行开单=0：tasks.md 全行 [x] 收口+orders.md 仅 09-24 单行 done+其本扫描 R527/R528 自报 claimable=0——v2.1 生态令（P-20260928-02·09:20 下发）09:26 R529 两步适配第一步刚落（提案轨+docs/proposals.md BD-PROP-001 open 首件），板面尚未落自可执行锚 | 72h 内：①tasks.md 落 ≥1 open 自可执行行（BD-PROP-001 实施件+提案轨常设锚「每窗 ≥1 提案」）；②blocked-on-CEO 物理件单（M2/开号族）单列如实禁充当在岗；③回执 patrol 台账 | domain/BigDomain tasks.md 全 [x] 实读+docs/proposals.md BD-PROP-001 open 实读+origin log R527/R528/R529 实读+orders.md 派单行 | 2026-10-01 | VERIFIED（10-02 本班：origin 实测=orders.md 三行 open 自可执行单在册〔O-20260928-015/016/017 硅基域三令·BLUEPRINT 承接面〕+09-28 派单行状态格「①②③ done 2026-09-28 R531（tasks.md 三行锚+backlog 镜像）」实读+④回执三载体〔state log R531+HQ-FEEDBACK R531+commit 令号〕+R852 01:09 活跃——板面锚达标销案） |
| PT-20260928-03 | 2026-09-28 | HQ | P2 | fleet-audit→patrol-probe 管道中文乱码：子进程 stdout 经父 PS5.1 控制台 GBK 解码→probe [FLEET] bigstream task 文本 mojibake（「瀹炴椿杞稰…」=实时轮询族不可读）——机队审计任务面可读性降级 | patrol-probe 捕获 fleet-audit/task-health 输出前后统一 [Console] 编码（或改中转文件+UTF8 读入）；修后 bigstream 行中文可读回归 | probe-20260928-092301.txt [FLEET] bigstream 行 mojibake 实读+Tools/fleet-audit.ps1 L33 子进程侧 OutputEncoding UTF8 已设·父捕获侧缺 | 2026-10-05 | OPEN（10-02 本班复验未修：probe-20261002-010240 [FLEET] bigstream 行仍 mojibake「鐢熶骇杞?86…」实读·在窗） |
| PT-20260928-04 | 2026-09-28 | BigCompute | P2 | 心跳面仅宿主机可见：state/heartbeat.txt 为 gitignored 本地件（本机 Test-Path state=False）→非宿主机 fleet-audit 永缺此机行（09-25 五班与今日 probe [FLEET] 均 7 台无 bigcompute 双实证 vs 宿主机夜报「机队 8 台」）=集团审计面不完整 | 按 os-protocol 使 beat 跨宿主机可读：beat 入 git 追踪（随 freshness 节律）或写手双跳 origin；修后任一机 fleet-audit machines=8 回归 | compute/BigCompute state Test-Path=False 实测+probe-20260925-180720/probe-20260928 双无 bigcompute 行+夜报 03:07 八台对照 | 2026-10-05 | OPEN（10-02 本班复验未修：probe [FLEET] machines=7 仍缺 bigcompute 行·在窗） |
| PT-20261002-01 | 2026-10-02 | HQ | P2 | probe [CARRY] 复合格误计：PT-20260925-01 终态 VERIFIED（09-28 已销案）因状态格历史前缀「ESCALATED（…）」被 L136 前缀匹配计入 open——本班 carry=10 vs 实 9（runner 防重 oracle 与下轮核验面带死项噪声） | CARRY 解析增终态后验（状态格含 VERIFIED/FIXED 注记即剔除计数）·修后双跑对账 9=9 | probe-20261002-010240.txt [CARRY] 行+Tools/patrol-probe.ps1 L136 实读+PT-20260925-01 行终态实读 | 2026-10-09 | OPEN |
| PT-20261002-02 | 2026-10-02 | MiniGame | P2 | C 机 status 导出面断更 7 天：STATUS-c.md mtime 2026-09-25 07:55（末次=dc35cb658 C1075 批）后零更新——同制对照 STATUS-b.md 10-01 20:39 新鲜；C 机 tick 本身活（tick-ledger 0.1h）=bookkeeping 面 STATUS-c 步疑似 09-25 崩轮修复后遗留丢失 | C 机 lane 修复 STATUS-c 导出面（随轮回写）·若面已迁移则勘误 probe 实体清单+队列回执 | STATUS-c.md mtime 实测+git log -1 -- STATUS-c.md（dc35cb658 09-25 07:55:34）+MiniGame 根 STATUS* 三件对照+FE 队列派单 FE-P-20261002-PT02 | 2026-10-09 | OPEN |
| PT-20261002-03 | 2026-10-02 | BigLife | P1 | 主产线静默 ~34h：origin/main 末提交 3421d3c5=09-30 15:18 R777 决策轮回执后零轮提交——对照 09-30 日内 R711-R741 15-30min 节律（TASKS.md 实录）；宿主 BG-A 机活 1.2h（fleet）非物理下线；任务板 15+ open 自可执行（非无任务违例）·静默未声明 | 车道自检+回执（≤72h）：调度让路/资源门=如实声明一行入令件；loop 死停=重启+根因一行 | origin/main git log 实测（本班 fetch 对账）+life/BigLife tasks/TASKS.md 实读+probe [FLEET] BG-A 行+fleet 机读面无 biglife 行（PT-20260928-04 族监测盲区叠加）+令件 life/BigLife/orders/O-20261002-0118-HQ-C.md | 2026-10-05 | OPEN |

## 闭环统计

- 首班 2026-09-25（RUN_ID=20260925-114357·host=BG-C/bm-c）：pt_new=5（P0×1·P2×4·PT-02 依 push 非快进新证据 P1→P2 修正定稿）·pt_verified=0（首班无上轮项·[CARRY] open_findings=0）·pt_escalated=0。红黄绿分布=8G/0Y/1R（BigMoney=R·余 G）。
- 二班 2026-09-25 加开（RUN_ID=20260925-130119·host=BG-C/bm-c·13:01-13:2x）：pt_new=2（P2×2·PT-06 task-health 旗面 result 盲区/PT-07 fleet-audit 读 state.ts 适配——均 HQ 工具面）·pt_verified=2（PT-02 BigStream R241 e2b9e9d 三整改闭/PT-05 bm-a 回执归属收敛+via 采纳）·pt_escalated=0（PT-01 截止 09-26 11:52 在窗·余 P2 截止 10-02）；红黄绿=8G/0Y/1R（BigMoney=R 维持=bm-c 执行体 P0 物理重建在途·核心面双机满载）。
- 三班 2026-09-25 加开（RUN_ID=20260925-134219·host=BG-C/bm-c·13:42-13:5x）：pt_new=4（P2×4·全 HQ 工具/正典面：PT-08 probe CARRY 端锚正则漏计注记态/PT-09 probe BigDomain 路径错配/PT-10 机读源陈旧克隆伪象+三克隆一次性 pull 止血/PT-11 charter MiniGame intake 路径错写——真身=monorepo 根级 AI反馈队列.md）·pt_verified=0（5 OPEN 全在窗·PT-01 计划腿进实=MSG 到 origin·物理腿零实证）·pt_escalated=0（PT-01 截止 09-26 11:52 在窗）；红黄绿=8G/0Y/1R（BigMoney=R 维持=PT-01 bm-c 执行体 P0 在窗·核心双机 origin 实测鲜绿满载）。
- 四班 2026-09-25 加开（RUN_ID=20260925-155720·host=BG-C/bm-c·15:57-16:2x·**触发=U205 watch escalate-patrol**：BG-B STALE 无 PT 覆盖→watch 判 RED 自动加开）：pt_new=2（**P1×1**=PT-12 MiniGame BG-B 心跳信道假 STALE——写手健在·根因=idle 段无提交+折叠节律+只读 master 三层·B641-643 连发满负荷实证；**P2×1**=PT-13 watch PT 覆盖判定漏检〔bm-c/bigstream 双报 no PT cover 而 PT-01/07 在册〕）+**PT-10 P2→P1 升级**（预测害兑现=watch 假 RED 实锤·bm-a/bm-b origin 双鲜·截止 10-02→09-28）·pt_verified=0（9 OPEN 全在窗）·pt_escalated=0（PT-01 大限 09-26 11:52 在窗）；红黄绿=**6G/2Y/1R**（HQ=YELLOW 首开=PT-10 P1·MiniGame=YELLOW=PT-12 P1·BigMoney=R 维持=PT-01·实体产线 origin 实测九面零新案）；止血=四镜像克隆 pull 对齐 origin（PT-10 处方续用·止血窗 ~2h）。
- 五班 2026-09-25 加开（RUN_ID=20260925-180720·host=BG-C/bm-c·18:07-18:4x·**触发=U205 watch escalate-patrol 第二次**（18:07:19 liveness 实录 bm-b「no PT cover」——PT-10 伪象+PT-13 cover-miss+PT-15 stamp 闸死三因叠加链本班全定谳））：pt_new=2（**P1×1**=PT-15 escalate 链 stamp 防重复闸 PS5.1 不兼容根因定谳·**P2×1**=PT-14 集团台账并发写入面三实证〔P-04 撞号瞬态自解+83539d6 主题错位残留+orders.md L201/L205 同文重复实存〕）+**PT-13 P2→P1 升级**（复发#2+escalate 闸门角色实锤=自动加开环断路器·截止 10-02→09-28）·pt_verified=0（主检段 13 项 OPEN 全在窗·存史）·pt_escalated=0（PT-01 大限 09-26 11:52 在窗）；红黄绿=6G/2Y/1R（主检段判色：HQ=Y〔PT-10/13/15 三 P1〕·MiniGame=Y〔PT-12 P1〕·BigMoney=R〔PT-01〕·实体产线 origin 九面实测零新案）；止血#2=六克隆 ff-only pull 毕（BigStream/BigLife 网络重置重试后成）；**收口合并增记（18:4x）**=HQ 治本批 f74de62（18:21·同窗竞写）行级并集收编：PT-08/10/13 三行 FIXED（其自测详证在案·五班 diff 实读采信）+PT-12③ 读侧毕（状态=OPEN〔③已毕·①②待 B 机〕）——主检段判色不受影响（治本在主检段后到达）；独立行为面复查点=下轮 probe [CARRY] 计数/probe [FLEET] 读数/watch actions 三对账。
- 周一班 2026-09-28（RUN_ID=20260928-092301·host=FLUXGROUP/bm-c·常规班 09:23 触发）：pt_new=4（**P1×2**=PT-20260928-01 probe fetch 静默回退六克隆假读/PT-20260928-02 BigDomain 板面零自可执行锚·**P2×2**=PT-20260928-03 probe 管道乱码/PT-20260928-04 BC 心跳宿主独占）·**pt_verified=8**（PT-01 bm-c 归队路 A 兑现/PT-07 Source 3 ts+task/PT-08 CARRY 对账 10=10/PT-10 [FLEET]+watch 双对账/PT-12 B 机 pulse 节律/PT-13 watch 零误报/PT-14 取号纪律三证/PT-15 PS5.1 回归实弹）·pt_escalated=0（PT-12/PT-15 双双当日 VERIFIED 抢在截止内）·余 OPEN=PT-03/04/06/09 四条 P2（10-02 窗内）+新 4 条；红黄绿=**7G/2Y/0R**（HQ=Y〔PT-28-01 P1〕·BigDomain=Y〔PT-28-02 P1〕·余 G——origin 九面全活实测：BM 三机满载/FV r232+板 4 open/BS R630/BL R586/BC 09:29 smoke 在飞/MG 三机+队列当日消费/CPH4 研究三件当日）；**probe 陈旧读数假象已由本班六克隆 fetch 对账作废**（PT-28-01 立案·判色一律按 origin 实测非 probe 机械值）。

- 凌晨班 2026-10-02（RUN_ID=20261002-010240·host=FLUXGROUP/bm-c·01:02 OS 任务触发·时间盒内收口）：pt_new=3（**P1×1**=PT-20261002-03 BigLife 主产线静默 ~34h 未声明·**P2×2**=PT-20261002-01 probe [CARRY] 复合格误计〔PT-01 终态被计 open·carry 10 vs 实 9〕/PT-20261002-02 MiniGame STATUS-c.md 断更 7 天）·**pt_verified=1**（PT-20260928-02 BigDomain 板面锚 09-28 R531 实已收口·本班 origin 实测定谳销案）·**pt_escalated=1**（PT-20260928-01 probe fetch 静默回退逾期 1d+本班四克隆假读复发实锤）；五 P2 大限日注记=PT-03/04/06/09 未收口各注记·**PT-11 执行面代修=FIXED**（§5 MiniGame 路径订正+Changelog）；止血=五陈读克隆 ff-only pull 对齐 origin（BS 6c23a5ea/BL 3421d3c5/BD 5f01ab3/BC 4ae6df8·PT-10 止血范式）；红黄绿=**7G/2Y/0R**（HQ=Y〔PT-28-01 P1 逾期〕·BigLife=Y〔PT-20261002-03 P1〕）；origin 九面实测=BM W38 freeze 01:01 满载/BS R912 00:49/BD R852 01:09/BC blind-box 渲染复验 00:58/MG 1135 commits/7d 三机在产/CPH4 registry 1.0h/FV 13.6h 正常+板 8 open。

### Changelog
- 2026-10-02: Part B §5 表 MiniGame intake 路径订正（PT-20260925-11 兑现：`Design/configs/GLOBAL/AI反馈队列.md`→monorepo 根级 `AI反馈队列.md`·根级件 git 实证在册）——巡检班 20261002-010240 执行面代修（大限日收口）。
- 2026-09-30: **附录 A 外审前置与验收六律**立（源=2026-09-30 全域外审会话·D-20260930-26·T2 否决窗至 2026-10-07）。六律由本会话**六次自我勘正**反推得出（详见 `docs/audits/external-audit-handover-20260930.md` §六/§七）。零预算、零红线、可机器验；不新增审批层级、不新增文件。执行面=外部审计轮（Part A）＋patrol（Part B）＋自审（Part C）三面自检项。
- 2026-09-28: v2.0 四源合一（CEO 瘦身令 #3·机队一致性总括令 O-2026-0928-013）：audit-charter v1.0（外部审查宪章）+ patrol-charter v1.0 + patrol-ledger + selfaudit-report（生成件改道 docs/audits/）并入本件；工具改线=patrol-prompt.txt / patrol-probe.ps1 / fleet-liveness-watch.ps1 / selfaudit.ps1；旧件隔离 docs/_trash/2026-09-28-audit-merge/（git 史全保·7 日观察后清）。

---

## 附录 A 外审前置与验收六律（2026-09-30 立 · T2 · 否决窗至 2026-10-07）

> 性质：**外部审计/巡检/自审三面共同的前置步与验收判据**。六律源自 2026-09-30 全域外审会话的**六次自我勘正**（其中四次根因同一：**在读懂被审方自己的规则之前就下了结论**）。违反不判违规，但**结论不得入库**（同 Part B §8：无证据指针＝宣称无效）。
> 成本：纯文本校验＋既有 git/read 工具，**零新增采集、零新计划任务**。

### A1 外审前置三步（任何"新发现"必须依次走完）
1. **先 grep 官方索引件**——命中即**重复发现**，降级为"确认/催办"并标注索引件路径。实证：本会话把 `gaming/MiniGame/_共享与总控/俯视角3D资产_POLYGON48包全景梳理.md:12` 早已记载的"48 包无商业授权红线"当新法务发现，实为重复发现。
2. **再查既有立法**——问题若已有律，**一律走"延伸适用范围"，禁新立法**。实证：本会话几乎自造"投递层统一"新律，而 `cph4/evolution.md:43-46`「落台账≠送达」已于 09-24 立法且三司机轮自然合规。
3. **最后才提新立法**，须附一句"为何既有律不可延伸"。

### A2 验收最省可信式：同法同数
跨司交付验收＝**审查方用同一方法与同一输入把同一个数测一遍**；两方吻合（如 53.4% vs 53.3%）＝无口径造假空间，可采信。**禁止仅凭 commit 主题/自述文档采信。**

### A3 禁无 ground truth 改口径
不得因"偏差投诉"直接改判据口径；须**先建人工标注验证集**（建议 ≥30 样本、标注者非工具作者），出一致率与混淆矩阵；**一致率 <85% 不得用于点名/判负**。实证：照投诉改口径产生反向过冲（某司 2 档率 1.2%→53.3%）。

### A4 冻结类令必写"禁什么/不禁什么"
正文须并列两清单：**禁**（如新单首次入库／新序号／新供给线）与**不禁**（在飞批收口／已冻结件证据回填／内容修订／数据刷新）；否则次日即被读成"不许提交"而瘫痪收口。

### A5 探针全绿 ≠ 状态健康
每条探针须声明**所依律条 + 覆盖面 + 上次命中时间**（建议增"探针自证表"）；**阈值必须与律同源**（实证：某探针判据 14 天 vs 律定 48h＝门比说明书松 7 倍）；覆盖面外的问题不得以"全 OK"呈现（实证：三探针全绿时集团正处"7 日 10,858 commit 对 10 处销项提及"＝1:1086）。

### A6 核查口径须与所依律原文一致
判定"是否送达/是否存在/是否达标"时，检索口径须逐字对齐所依律原文（含等价编号族 `P-/O-/T-/D-/XL-`、**消息全文而非仅主题**、state log 等第二证据面）。实证：两次收窄口径换来"一次放过＋一次冤枉"。

### A7（配套·编辑纪律）
已落台账**行结构冻结**：新增只追加；修表另开 commit 并在派工通告板注明。理由：**行数水位受排版编辑漂移**，修表会污染各司水位（实证：三次修表导致某司水位越过派工行却未产出 ack）。

**判据自检三问（机器/人工可验）**：
① 新结论是否已走完 A1 三步？（查结论段是否含索引件路径与既有律条）
② "陈旧/失效"类判定是否已读被审方自己的**刷新律**（谁刷、什么条件刷）？——实证：把某司 09-23 一次性准备度报告当"失效看板"，而该司 `docs/status-export.json` 实测 12:51 已刷新。
③ 负向结论是否标注了**检索面**（文件名模式／行级／全仓／git A-M-D）？

---

## 附录 B 量化业务外审问责面（2026-09-30 立 · T2 · 否决窗至 2026-10-07）

> 性质：**量化条线（BigMoney）的外部管理边界与问责判据**。源=CEO 令 2026-09-30「当好外部专家，在量化金融这块做好外部管理和审计审查，确保集团业务在正确的轨道上」。
> 工具：`Tools/quant-audit-probe.ps1`（只读五查·首跑 D-20260930-27）。**本附录只定"要证什么/不能做什么"，不规定策略与参数**（那是司内自治面）。

### B1 外审边界（既授权也限制）
**可做**：只读取证；集团层立档/派工/裁决；建独立重算与校验工具（放集团 `Tools/`）；对司内宣称行使**引用禁令**。
**不可做**：写任何子公司仓（含"顺手修一下"）；代替司内做研究/调参/选策略；直接下单或触碰资金；把未经验证的读数呈 CEO。
**原则**：外审的价值是**让数字骗不过人**，不是替业务做决策。

### B2 量化条线必须持续自证的六件事（缺一＝对外宣称不得成立）
1. **收益真实性**：任一对外收益数字须可被独立重算（净值＝现金＋逐仓市值，逐条可对账）。
2. **风险真实性**：风控闸门须**在代码执行路径上**（非文档）；熔断/止损/仓位帽有单测；下单前强制过闸。
3. **样本外与稳健**：判据须过前向锁盒＋多重检验校正＋过拟合概率；**bars 不足禁年化**（见 B4）。
4. **数据完整性**：在役标的须新鲜（无行情者不得静默按 0 计入权益）；数据陈旧与重复标的一律出局。
5. **可复现**：新机一条命令可复跑其宣称（环境、数据、口径三者齐备）。
6. **失败留痕**：判负/退役记录须完整可查（本集团此项为强项，须保持）。

### B3 红线（触即升级 CEO，外审不代裁）
- **真金永禁全自动**；无券商**模拟盘**＋**程序化交易报备**，不得进入任何真实资金链路。
- 任何"修复前口径"的历史数字**一律作废**，不得再引用（先例 D-20260930-22）。
- 不得以"活动量/commit 数/文档量"替代收益证据。
- 不得隐瞒未定价/未成交/零活动的持仓与账户状态（编制面须如实标注在册数 vs 实动数）。

### B4 引用禁令（外审可直接执行·48h 生效）
1. `bars < 20` 时**禁止**引用任何年化收益/Sharpe 类指标（数学无意义）。
2. 存在**未定价仓位**且其市值未计入权益时，**禁止**引用当期净值与纸盘战绩。
3. 未过前向锁盒/未校正多重检验的读数，**禁止**以"已验证/validated"字样呈现。
4. 违背以上＝治理 §10 不实宣称，按点名/升级链处理。

### B5 节奏与产出
- **周轮**（随周报）：`quant-audit-probe.ps1` 重跑，产出「量化外审一行」——五查命中数 + 与上期对比。
- **月轮**（月界）：净值/回撤/换手/成本四项独立重算；在册 vs 实动编制对账；引用禁令合规扫描。
- **触发式**：任何对外收益宣称、编制变动、判负/退役、引擎口径变更，**48h 内**一次定向复核。
- **产出形态**：集团层裁决行（`docs/decisions.md`）＋一行证据指针；**不新增报告文件族**（防报告通胀）。

### B6 三态判定（每次外审必给）
| 态 | 含义 | CEO 面措辞 |
|---|---|---|
| **可宣称** | 六项自证齐备＋本轮五查全过 | 可对外用数 |
| **有条件** | 有已知缺口但已标注与限期 | 可用但须附缺口注记 |
| **不可宣称** | 触 B3/B4 任一 | 禁用其数字，直至修复复跑 |

### B7 下一批扩展（登记未开工）
`Q6` 成本口径核（13bp/边是否真进纸盘链路）｜`Q7` 数据陈旧门（现 1,670 只停 09-22）｜`Q8` 冻结窗越权读（lockbox 硬截断是否落地）｜`Q9` 纸盘成交对账（标记成交 vs 真实可成交价）。


