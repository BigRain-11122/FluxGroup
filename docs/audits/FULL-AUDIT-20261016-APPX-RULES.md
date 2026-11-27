# 附录A 规则正典面全量盘点（普查F 代理=general-purpose 只读 2026-10-16 机械提取自任务转写档案）

# 规则正典面纸面盘点报告（只读·2026-10-16）

**盘点口径**：通读了 law-registry.md（工作树现版）+ governance.md（84.7KB 全文）+ resource-chain.md（91.5KB 全文）+ token-economy.md / memory.md / versioning.md / council.md / audit-charter.md（含 PT 台账）+ RULES.md / AI.md / CODELY.md 全文；抽查了 MV-PIPELINE-PLAYBOOK-v1、PROMPT-EXPERT-GATE-v1（实位于 mv0001-handover/outbound/krea2/）、QC-MASTER-CHECKLIST-v1、drama-dept-v1 四件、CEO-PROXY 六件（SHIFT-SUPERVISOR-PROMPT.txt 只记名）、mechanism-map.md、knowledge-registry.md、S4U 机制件三件、orders.md 尾部 ~64 行。Tools\ 99 件全列名，关键机制件（silence-enforce/order-sentinel/audit-sentinel/delivery-watch/shift-supervisor/task-register 等）逐一开头实读验明身份。正典大文件无行号工具，指针一律用 `文件:§节`；rg 命中处用 `文件:L行号`。计划任务实况（schtasks）属机器面，本报告只核「正典写明的载体名在文件系统是否存在」。

---

## 一、规则盘点总表

### 块 1｜宪典与顶层治理（RULES.md / AI.md / governance.md）

| 规则名 | 载体文件 | 来源 | 执法机制 | 状态 |
|---|---|---|---|---|
| 命名规则（英文 kebab-case·禁人名/任务 ID 命名） | RULES.md §2 | 2026-09-23 初始法+legacy exception | 纸面·无机制（无命名 lint；asset-audit.ps1 只审资产面）；MiniGame 09号§7 豁免在案 | 现行（cph4/fleet/mv-album-001-jay/星晴-*.md 等中文件名与「group-layer 英文」条款张力，见 C-6） |
| 代码规则（先跑后宣告/密钥入 .env） | RULES.md §3 | 09-23 | 与 governance §10 同源执法：selfaudit.ps1 抽审+各司 verify 门禁 | 现行 |
| CEO 令触发器 /CEO+命令发布台 | RULES.md §7 | CEO 令 09-23+O-20261014-1210 | CEO-PROXY 席（CHARTER.md+ROUND.md v3.1·durable cron 8 班/日）+Tools/order-sentinel.ps1（OrderSentinel 2min）+Tools/fleet-dispatch.ps1 poke | 现行·有机制 |
| 治理铁律（零产品代码/禁跨仓写/冲突优先级/实况优先） | governance.md §1 | 09-23 立国 | patrol 红线合规维（patrol-runner.ps1+patrol-probe.ps1·Part B §3.5）+巡检抽审；CPH4 巡检例外② 09-24 授权 | 现行·审计承载 |
| 开线五步/收线（登记簿+gitignore） | governance.md §3 | 09-23 | 纸面流程·无机制（§2 登记簿人工维护；09-30 BigHouse 补单教训在案） | 现行·纸面 |
| 集团令统一台账 orders.md+令落点 | governance.md §4 | 09-23 | 台账单写手制（CEO-PROXY 唯一写手·2026-10-14 勘注）+git-atomic-push append 模式 | 现行·有机制 |
| 命令查重律 | governance.md §4+law-registry 头注 | C-20261008-06（CEO「各种命令重复」） | law-registry.md 用法行=查表纪律·无脚本机核 | 现行·纸面（查表靠会话自觉） |
| CEO 委托决策令 v2/v3（科学自决·「待 CEO 裁」禁令） | governance.md §4 | CEO 原话 09-24/09-29 | 「新建待裁字样=夜轮扫描项」——night-round-prompt.txt 承载 | 现行·纸面（夜轮扫描） |
| 三级记忆分层 | governance.md §5 | 09-23 | append/update 工具+Tools/memory-budget-gate.py（§10）+Tools/fleet-memory-sync.ps1 | 现行·有机制 |
| 交互窗并发三律+轮首脏禁 add -A+台账冲突检查钩子 | governance.md §6（含 §6.5） | 09-23+09-24 F2+09-29 D-20260927-05③ | 纸面·无机制（rg 冲突标记=人工步；10-15/16 sparse-checkout 三连删仓事故=无机核实害样本，orders 10-15 21:0x/10-16 00:2x 行） | 现行·纸面（高危） |
| 安全与密钥禁入 git | governance.md §7 | 09-23 | Tools/secret-scan.ps1（夜轮感知+secret-scan.Tests.ps1 回归） | 现行·有机制 |
| 编码律（ASCII/BOM/中文外置 UTF-8） | governance.md §7 | 09-23 PS5.1 坑 | 纸面坑律·无 lint；X345 BOM 转码事故族复发（orders 10-16 13:1x 行②） | 现行·纸面 |
| 变更控制+溯源条款（无溯源=周报点名） | governance.md §9 | 09-23 | evolution-tick-prompt.txt 周报点名+selfaudit.ps1 抽审 | 现行·纸面+抽审 |
| 修法优先律+法熵守恒+回访窗冻结 | governance.md §9 | C-20261008-04 | law-registry §六法熵账本+季度瘦身日（首跑 10-19·进化轮承载） | 现行 |
| AI 诚实律（五律+三防线+证据通道可信度律） | governance.md §10 | CEO 令 09-23「严格防止AI幻觉」+C-20261010-02 | 三防线：轮内自审（mandate）+门禁机核（各司 verify·执行侧不自证）+Tools/selfaudit.ps1 周抽审；fleet-reality.ps1 活体实测戳 | 现行·有机制（防线一纸面） |
| 交付时效律（快速件 24h/可见交付 ≤5 天） | governance.md §11 | CEO 时限令 09-24 | 夜轮 SLA 扫描（night-round-prompt ①）+周轮抽验——扫描在册；自动催办闭环缺（P-2026-09-29-13 逾期 17 天靠 CEO 令才催，orders 10-16 12:41 行） | 现行·半机制 |
| AI 行为铁律 9 条 | AI.md §5 | 多源（09-23 起汇编） | 铁律2=Tools/fleet-reality.ps1（强制实测）；铁律7=task-register.ps1 唯一正门；铁律3 查重=law-registry；其余纸面 | 现行·两件有机制 |
| 静默律（机制级三件套） | AI.md §5.7+resource-chain §七+P-2026-10-08-18 | CEO 令 09-23→10-06 三申→10-08「从机制上静默」 | Tools/task-register.ps1（唯一正门·强制隐藏链+读回）+HQ-SilenceGuard-Lane PT1M（Tools/silence-enforce.ps1/vbs·60 秒兜底）+toast 双路闸值 | 现行·有机制 |
| 台账单写手（委员会对三台账只读只议） | governance.md §0.1 勘注+MASTER-AGENT/COUNCIL-DIVISION-ANNOTATION-20261014.md | 10-14 三次丢行案 | CEO-PROXY 写手纪律+Tools/git-atomic-push.py（append 模式）+Tools/git-no-reversal-check.py 反转闸 | 现行·有机制 |
| 可视化统一线（禁各司另建） | governance.md §1 表 | CEO 令 09-23 | 禁双建律同源——patrol 审计；无专门机核 | 现行·纸面 |
| 美术资产库共享池（AA 登记制+消费链+L1 禁入交付链） | governance.md §6.7 | CEO 令 09-23 | Art Assets/README.md AA-XXX 登记制（宿主仓承载）+audit-charter Part A §2 mod 2 美术监管班；3D 线=48 包索引 AD 引用制（skills 承载） | 现行·登记制+外审班 |
| 台词生产唯一所有权律 | governance.md §6.8 | G1 判决 09-24 | 组织归口（BigLife 单点）——纸面 | 现行·纸面 |
| 跨司工单互投 SLA（ack ≤30min·双向闭环） | governance.md §6.9 | CEO 提速令 09-24 | 值守轮点名（每日两班·night-round 承载）；10-16 加 FleetLink 直连+ExpectSha 闭环（O-20261016-1120） | 现行·升级中 |
| 三层研究边界律 | governance.md §6.10 | G3 判决 09-24 | cph4/README 注册表归属判定——查表纪律 | 现行·纸面 |
| CEO 用机让路律（触发词 pause/全面开工） | resource-chain §六 | CEO 最高命令 10-06（C-20261006-01） | cph4/fleet/machine-state-kit/（machine-state.ps1 v6+gamewin_cron_suspend.py·三机部署）+触发词入各机记忆；WorkEnd 自动复工已被 10-15 口令制退役 | 现行·有机制（10-15 修订版） |
| bm-a 工作日停产口令制 | resource-chain §9.1 changelog+orders 10-15 18:4x | CEO 令 10-15 18:4x | WorkStart（09:00 pauseLite）保留+「开工」口令人工；AutoYield-WorkEnd 停用退役 | 现行·有机制（口令人工） |
| 机队静默工作律（零窗/toast 闸/写后读回） | resource-chain §七 | CEO 令 10-06 三申升格 | 任务运行器 22/22 隐藏链审计+双路闸值+写后读回；执法面与 AI.md 铁律7 同链 | 现行·有机制 |

### 块 2｜决策与委员会（council.md / decision-chain）

| 规则名 | 载体文件 | 来源 | 执法机制 | 状态 |
|---|---|---|---|---|
| 决策链路由总表+回执 SLA+7 天回访 | cph4/decision-chain.md §一 | CEO 令 09-24「统一梳理决策链条」 | 决策轮双班（cph4/decision-round-prompt.txt·00:00/12:00） | 现行 |
| 委员会章程（七席/触发八判据/4-7、5-7 记名投票） | cph4/council.md v2.3 | CEO 令 09-27 成立+09-29 常设化（C-20260929-03） | Tools/council_vote.py（记票·--major/--round·8 场景自测）+决策轮 mandate | 现行·有机制 |
| 否决窗制度 | 曾遍布 council/governance/token-economy 等 | 2026-10-11 CEO 直令「我不会后悔，不要立这个」（D-20261012-02） | 已废止正典化（council §一.5/§三⑧/§七.1 等 6 处勘注）；token-economy §八 v2.2 段已就地修订——但 memory.md 头注「T2+否决窗 7 天」（L4）、versioning §4.2 等散件头部仍有未勘注残留 | **废止（头部残留待清）** |
| 常设运转（复盘四问+自迭代闭环） | council §一.5.3/4 | CEO 令 09-29 | decision-round-prompt ⑤复盘步+reflection-journal.md 委员会班次行（单写者=当班常务轮） | 现行·有机制 |
| 顶级专家强度五律+挂席专家+利益申报回避 | council §二.5/§二.6/§四.6 | CEO 令 10-08（C-20261008-02/03） | 秘书处打回（人执）+席7 审视+月度 KPI 面板（入 M5） | 现行·人执为主 |
| E3 紧急通道（席1+2+7·≤1h） | council §七.1 | C-20261008-03 W3 | 无常设载体（哨兵/值守轮可发起·临时召集）；判据「首月 0 触发如实报 0」 | 现行·纸面 |
| 缺席=弃权律+秘书处备份 | council §七.2/7.3 | 同上 W4 | 值守轮代秘书（mandate 一行）——纸面 | 现行·纸面 |
| 席位月度 KPI 面板 | council §七.4 | 同上 | 入 M5 治理日（evolution-tick-prompt 月度触发承载）——10-31 首测前无载体 | 现行·未首测（待证） |
| 决策轮三冲突升级/两轮驳回升 CEO | decision-chain §一 | 09-24 | decision-round-prompt 流程承载 | 现行·纸面 |

### 块 3｜机队与资源（resource-chain.md 合典）

| 规则名 | 载体文件 | 来源 | 执法机制 | 状态 |
|---|---|---|---|---|
| 调度三原则+主调度席（原「不建中央调度器」收窄） | resource-chain §一.0 | CEO 令 09-23+O-20261012-2225 修订 | Tools/fleet-dispatcher.ps1（L0 PT30M 巡班·零 LLM）+L2 判断班（durable cron 00:13/12:13·已由 CEO-PROXY 承接防双写手） | 现行·有机制 |
| 配置分配表+借池律+verdict 驱动 | resource-chain §一/§二 | CEO 令 09-23/24 | Tools/fleet-audit.ps1（三源聚合·GREEN-IDLE 等旗标·夜轮跑） | 现行·有机制 |
| 云算力默认态 | resource-chain §二.三 | CEO 令 09-23 | 原文「并行全量」已三次就地修订：§九必要闸（10-07）→§十并发帽（10-15）——**现役=最新版**·旧句仍存档 | 现行（时间层叠勘注·见 C-3） |
| 战略倾斜态（城建 P0-Resource） | resource-chain §二.四 | CEO 令 09-23 23:02 | 时态条款（M1 判据过后复审）；City3D 全面开工令 10-14 后倾斜仍有效 | 现行·时态 |
| 物尽其用律+闲置自领+闲置硬触发闭环 | resource-chain §8.2/§9.6 | CEO 令 09-24/09-27/10-07 | Tools/fleet-idle-watch.ps1（IdleWatch v2 车道判闲）+各机循环每轮自检步+idle_rounds 心跳字段+补货 SLA | 现行·有机制 |
| 扩容采购判据线（默认不扩容） | resource-chain §二.六.6 | CEO 快速调查令 09-24 | 判据人工核（夜轮计量先行）——纸面判据 | 现行·纸面 |
| 三机三车道定岗 v2+抢单闸三律 | resource-chain §9.1 | CEO 令 10-12（C-20261012-03）+10-14 两令 | Tools/fleet-nodes.json lane 字段+IdleWatch 判闲+派单点名/池单标记/禁双开（POOL 卡律） | 现行·有机制 |
| tailnet 利用律+信息同步律（秒级 poke→2min 哨兵→10min 轮） | resource-chain §9.2/§十 | CEO 令 10-08（C-20261008-01） | Tools/fleet-link.ps1+fleet-poke-worker.ps1+register-fleet-link.ps1+fleet-dispatch.ps1+order-sentinel.ps1（2min）；10-16 升 v1.6 union 同步+O-20261016-1215 tailnet 第一通道实装中 | 现行·有机制（升级在飞） |
| 记忆上链律（跨机价值禁入私有层） | memory.md §8（resource-chain §十.2 同源） | C-20261008-01 | 会话开场 pull --ff-only+同窗 commit——纸面纪律（EEXIST 故障机等效通道在册） | 现行·纸面 |
| 四级保留制 R1-R4+防误伤五闸+防膨大三律 | resource-chain §三 | CEO 令 09-23 | Tools/retention-scan.ps1（只读周测·进化轮资源健康节） | 现行·有机制 |
| 坚决清理律 v2+磁盘预算与分层响应制 | resource-chain §三.11 | CEO 令 09-29/09-30 | Tools/disk-sweep.ps1（值守轮周日窗步）+Tools/disk-sentinel.ps1（FluxGroup-DiskSentinel 5min 哨兵·三线 700/620/500GB） | 现行·有机制 |
| 批跑自清律+管线缓存纪律（批内 ≤20GB/实验区 30GB 帽） | resource-chain §三.11.8 | CEO 令 09-30「硬盘再大也不够用」 | 值守轮水位行环比（日燃 >20GB 连续 2 班点名）——哨兵+人工判读 | 现行·半机制 |
| 存量三分律（热/冷/死层+月卷轮转） | resource-chain §三.10 | CEO 令 10-07（C-20261007-04 D1） | 首扫实弹 10-07（docs/audits/stock-slimming-audit-2026-10-07.md）+月卷轮转——专项执行·无常设机核 | 现行·半机制 |
| WIP 上限律+入口窄化+流程瘦身日 | resource-chain §三.8 | CEO 令 09-24 | 「各司自定 cap·MiniGame 建议 M5 复审定值」——**未定值未核** | 现行·纸面（cap 待证） |
| 机队协议三条款（心跳/认领/传输）+批次先占/轮值/自愈车道归属 | resource-chain §四 | G7 判决配套 09-24+R2 立法 09-27 | git commit 即锁（git 本身）+fleet-audit 源行开闭原则——协议面纸面+git 承载 | 现行 |
| 机队保活律（心跳即法线/无静默掉线/自愈优先/双通道） | resource-chain §五 | CEO 令 09-25 U205 | Tools/fleet-liveness-watch.ps1（各机 5min 看门器·liveness.json/alerts.jsonl 契约） | 现行·有机制 |
| 机队分工协作总机制（四铁律+交接验收） | resource-chain §八 | CEO 令 10-06（C-20261006-02） | patrol 周轮交接抽验 ≥2 件/周——审计承载 | 现行·半机制 |
| 本地算力主供+云端必要闸+产线探针律 | resource-chain §九 | CEO 令 10-07（C-20261007-02） | attribution 台账（C-20261001-01 硬律）+30 天本地可达性验证单——台账纪律 | 现行 |
| 机队同构三层律+heartbeat 维度清单 v1 | resource-chain §二.10 | CEO 令 10-07（C-20261007-04 D2） | fleet-audit 消费方按清单读+巡检同构合规判据——纸面判据+probe | 现行·半机制 |
| 云道并发帽 v1.0 | token-economy §10.6 | CEO 令 10-15（C-20261015-03） | 三司 spawn 闸 preflight（bm-c=quant/bigmoney 仓 Tools/spawn_gate.ps1 回执 PASS·bm-b 逾期 5h39m 记档）+codely_live_count 观察哨 | 现行·落位中（回访 10-17） |
| 新机接入三层模型 | cph4/onboarding.md | CEO 令 09-23 | Tools/bootstrap-machine.ps1（六相幂等）+Tools/InvisibleRunner.vbs | 现行·有机制 |
| 服务器律 v2（必要性闸/入册制） | cph4/server-governance.md | CEO 令 09-24（废零服务器死命令） | 服务器入册表（§〇.2）——登记纪律·无核 | 现行·纸面 |

### 块 4｜token 经济与记忆

| 规则名 | 载体文件 | 来源 | 执法机制 | 状态 |
|---|---|---|---|---|
| Token 五律（计量先行/路由三问/L3 留痕/结构性替换/速度优先） | token-economy §二 | CEO 令 09-24 | 轮账本 tokens 行+周报聚合——记账纪律·无脚本核 | 现行·纸面 |
| 顶层锚定语五律（工作选择/沉淀/必要性闸/执行默认/严管复位） | token-economy §〇.1 | CEO 锚定语 09-24+O-20261015-1200 复位 | 执行默认/严管=§十执法细则（白名单六类+attribution+SLI-8）；SLI-8 对账挂 CEO-PROXY 周日 21:43 深复盘 | 现行·有机制 |
| 云端严管执法细则 v3.0（白名单六类/路由收严/生成面统管） | token-economy §十 | CEO 令 10-15（O-20261015-1200·C-20261015-02） | attribution 单字段+周报云端行+SLI-8 违例计数=0+EXPERIENCE-LEDGER 落闸；判据回访 10-19 | 现行·判据待回访 |
| 上下文管家模式 | token-economy §3.4 | CEO 参考方案令 09-24 | P-48 pilot@BigMoney（判据=input 降 ≥50%）——**试点回执未见** | 现行·试点（待证） |
| 本地推理栈/并发车道/极限使用令 | token-economy §3.1/3.3 | CEO 令 09-24 | Ollama 环境变量+keepwarm 让路（machine-state）——部署承载；**§3.1 表 qwen2.5:14b 现状已漂移**（10-15 换代删除·见 C-9） | 现行·表漂移 |
| 台账行宽律 ≤500 字/禁裸 tail/多模态眼闸 ≤8 轮 | token-economy §9.1/9.2/9.5 | CEO 直令 O-2026-0930-018 | 回访窗 10-07 已过——**回执未见**（纸面抽验） | 现行·回访待证 |
| 记忆水位表+梳理窗协议（周日 03:07·熔断 10 条） | memory.md §2/§3 | CEO 令 09-24（D-20260924-01） | 夜轮梳理步（night-round 承载·update_memory 唯一合规通道·EEXIST 故障降级在册）；**§2 水位法「热层 ≤20KB」曾长期失守**（memory.md §10 病理自认） | 现行·曾失守已根治 |
| 四字令执法面（精简/随时维护/保持最新/科学有效） | memory.md §9 | CEO 令 O-20261009-1915 | Tools/fleet-memory-sync.ps1 v2+memory-tombstones.jsonl+周日窗扩容 | 现行·有机制 |
| 分层注入面预算律（L0 ≤40KB/≤60 条·三层制） | memory.md §10 | CEO 令 10-15（O-20261015-1230/1235·D-20261015-04） | Tools/memory-budget-gate.py（零 LLM·KEEP 白名单+竞写守卫+快照回滚）+HQ-MemoryBudgetGate schtasks 每 4h；机队推广@bm-b/c 派单回执窗内 | 现行·有机制（判据回访 10-19） |

### 块 5｜git 版本与并发（versioning.md）

| 规则名 | 载体文件 | 来源 | 执法机制 | 状态 |
|---|---|---|---|---|
| trunk-based 主干开发+合法分支四类 | versioning §1/§2 | CEO 令 09-23 | 夜轮「非主干分支 >30 天/超水位点名」感知项；单仓 ≤8 分支——审计承载 | 现行·半机制 |
| tag 档案律+发布锚律（先 tag 后发布） | versioning §3.3/3.4 | 09-23 | Tools/release-scan.ps1 在库（**用途对应待证**）；MiniGame G 系 tag 既有范式 | 现行·执法件待证 |
| 提交者身份律（junsheng.sun+[via 机]） | versioning §4.1 | 09-23 | bootstrap-machine.ps1 P3 相写全局身份——部署时一次·日常无核 | 现行·半机制 |
| 提交消息规范（四层结构/500 硬顶/指针制） | versioning §4.3 | CEO 令 09-24 | 「周进化轮抽审点名·不建新工具」——**自述无工具·纯抽审** | 现行·纸面 |
| 多窗活树推送唯一正道（外科提交/原子推/反转闸） | versioning §4.4 | O-20261014-1215 | Tools/git-atomic-push.py+Tools/git-no-reversal-check.py（推前必跑·CEO-PROXY ROUND 步8 丢行守望 --audit） | 现行·有机制 |
| 禁 force-push/历史保全/revert 追加式 | versioning §5 | 09-23 | **远端 branch protection=CEO 物理件未落**（G12/G6·mechanism-map §三.3「待 CEO 一次同意」·G12-BP-PREPUSH-PROPOSAL.md 在库）——纯纪律 | 现行·**远端机核缺位** |
| 密钥泄露机核 | versioning §4.2 | 09-23 | Tools/secret-scan.ps1（P0 分级·夜轮接线） | 现行·有机制 |
| 受保护件哈希锚 22 件 | mechanism-map §三.3+Tools/protected-hash-registry.json | 丢行案后立 | Tools/protected-hash-register.ps1（Verify 拦推） | 现行·有机制（BP 未落） |

### 块 6｜审计与哨兵族（audit-charter + 机制件）

| 规则名 | 载体文件 | 来源 | 执法机制 | 状态 |
|---|---|---|---|---|
| 外部独立审查（13 块面轮换+分级处置+认领表） | audit-charter Part A | CEO 令 09-26 | OS 任务「FluxGroup外部审查轮换轮」每日 22:17（**10-14 降频日一班**；§7.4 三 AI 三班表未勘注=残留） | 现行·降频（两处残留见 C-2） |
| 集团巡检（八维+判色+PT 台账闭环） | audit-charter Part B | CEO 令 09-25 | OS 任务 FluxGroup-PatrolRound 周一 09:23（Tools/patrol-runner.ps1+patrol-probe.ps1+patrol-prompt.txt）+戳记认领 F-09 | 现行·有机制 |
| 自审工具面 | audit-charter Part C | governance §10 | Tools/selfaudit.ps1（docs/audits/selfaudit-report.md 底稿） | 现行·有机制 |
| 外审前置与验收六律（附录 A） | audit-charter 附录 A | D-20260930-26 | 三面自检项（外审/patrol/自审提示词内嵌）——纸面纪律 | 现行·纸面 |
| 量化外审问责面+引用禁令（附录 B） | audit-charter 附录 B | CEO 令 09-30「当好外部专家」 | Tools/quant-audit-probe.ps1（+v2/quant-audit-cadence.ps1/quant-nav-recompute.ps1/quant-oversight-digest.ps1 族）——周轮重跑·月轮独立重算 | 现行·有机制 |
| 集团审计部（八面内容矩阵） | cph4/audit-office.md v1.0 | CEO 令 09-24 ~21:55 | Tools/audit-sentinel.ps1（L1 三探针·值守轮代跑·D-20260930-34 修窗对齐） | 现行·有机制（**law-registry 未登记=孤儿 D-2**） |
| 值守轮（四器审计+催办+自愈+回执核销） | AI.md §3+cph4/night-round-prompt.txt | CEO 令 09-23 | 夜轮 03:07/15:07 双班（四器=retention-scan/selfaudit/task-health/fleet-audit） | 现行·有机制 |
| 任务健康五信号 | cadence §6+Tools/task-health.ps1 | CEO 令 09-24 | Tools/task-health.ps1（STALE/NEVER-RAN/结果码·夜轮全量扫）+task-health.Tests.ps1 | 现行·有机制 |
| 自动化周期总账（防重复/错峰/单实例锁） | cph4/cadence.md | CEO 令 09-24 | cadence 表登记+task-health 消费——登记纪律 | 现行·半机制 |
| 进化轮（分级立法 T0-T3+法熵审视+四环周期） | cph4/evolution.md | CEO 令 09-23 | FluxGroup-EvolutionTick 周日 09:17（cph4/evolution-tick-prompt.txt） | 现行·有机制 |
| 错误定级 E0-E3+熔断 | cph4/errors.md | CEO 令 09-24 | 夜轮自愈步+熔断（同错误两轮未愈升 E1）——prompt 承载 | 现行·半机制 |
| 调研纪律（行程标准+应用表强制+闭环率 KPI） | cph4/research-protocol.md+skill cph4-research-dispatch | CEO 令 09-24 | patrol「调研断档」判据+audit-sentinel Probe C（research_health_baseline.py） | 现行·有机制 |
| 发布安全门（默认不可见/打包律） | cph4/release-gate.md v1.0 | CEO 令 09-24 晚（设计授权） | 「CEO 明示批准后才对外」——审批人工；**law-registry 未登记=孤儿 D-1** | 现行·纸面（孤儿） |

### 块 7｜域内产线硬门件（MV / drama / CEO-PROXY 席）

| 规则名 | 载体文件 | 来源 | 执法机制 | 状态 |
|---|---|---|---|---|
| MV 全链条方法论（10 站 6 闸+精度阶梯+海选制） | cph4/fleet/mv-album-001-jay/MV-PIPELINE-PLAYBOOK-v1.md（v1.1） | CEO 令 O-20261015-1655/1725 | 站出口判据「缺件禁开站」+POOL 卡派单；流程纪律·星晴=试点 | 现行·试点执法中 |
| 提示词专家审闸（十一面·无 verdict 派单=烧制侧拒收） | cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/PROMPT-EXPERT-GATE-v1.md | CEO 令 O-20261015-1630（原话「每次提示词都要过1遍提示词专家审」） | lint 机核（三名单）→专家审 verdict 随包上链→导演席签发；烧制侧断言=派单含 verdict 文件名；首包星晴 A 已执法（PROMPT-GATE-星晴-KF-PACK-A-v1.md） | 现行·有机制（**PLAYBOOK 指针表相对路径悬空·见 D-10**） |
| MV QC 原子清单（24 类细化+判例落闸律） | cph4/fleet/mv-album-001-jay/QC-MASTER-CHECKLIST-v1.md | CEO 令 O-20261013-1830 | 每检项绑定对应闸（检查单→lint→QC 检项→脚本断言升格律）+EXPERIENCE-LEDGER-v1 判例行 | 现行·闸位绑定 |
| 帧闸（十席两波 ≥9+白名单签章才 i2v） | QC §7+mv0001-handover/outbound/krea2/kf-demo-20261012/FRAME-GATE-WHITELIST-v1.4.md | 导演判例 | 帧审流程+签章文件；i2v 派单断言 | 现行 |
| 成片闸（盲评 ≥9+三律自审+CEO 终审唯一终点） | PLAYBOOK S8+EXPERT-PANEL-PROTOCOL.md | CEO 终审制 | 十席盲评流程+QC §13；中间态零呈审纪律 | 现行 |
| CEO-PROXY 交接卡九要素+card-lint | CEO-PROXY/CHARTER.md §7 | O-20261014-1745（十三席群审定版） | Tools/card-lint.py（九要素缺一=派单无效·lint exit≠0 禁派；--min 档） | 现行·有机制 |
| POOL 写手制+五态+核销双勾 | CHARTER §7.3+dispatcher/POOL.json | 同上 | 本席独占写手+晨检抽检 ≥1 单/23:43 对账；10-16 Cure-1 加 Tools/delivery-watch.ps1 交付存在性哨（every:5m 任务 bm-a-DeliveryWatch+交付契约 JSON） | 现行·有机制（哨今日上线） |
| 班哨（L2 监督班 S4U 化） | Tools/shift-supervisor.ps1+CEO-PROXY/SHIFT-SUPERVISOR-PROMPT.txt | C-20261016-02 Cure-6 | bm-a-ShiftSupervisor 任务（InteractiveToken 降级·入 task-s4u-backlog.md 待提权转换）——12:43 首班 LAUNCHED 实证 | 现行·今日上线 |
| 部署即点火律（点火律：60 秒实弹+读日志） | C-20261016-02 Cure-9（焊进 task-register.ps1） | CEO 令 10-16 13:3x「为什么每次写的科学合理做起来全是 bug」 | Tools/task-register.ps1（S4U 默认+LogonType 读回+注册即试发 FireTest+UAC 拒则降级入 Tools/task-s4u-backlog.md 不静默） | 现行·今日焊入 |
| S4U 注册律（车道任务一律 S4U 禁 InteractiveToken） | cph4/fleet/memory/CODELY-fleet-global.md L21 判例 | 用户令 2026-09-29 23:17 | **17 天无登记器焊点**：10-16 才焊 task-register.ps1；bm-a 存量 ~106 件实况皆 Interactive（C-20261016-02 L69）·转换候委员会裁决；task-s4u-backlog.md 仅 2 件登记（L3-4） | 现行·**存量未转换（立法≠机制重灾区 A-1）** |
| 漫剧/短剧产线（10 站 7 闸+精度阶梯+OSS 三红线） | cph4/fleet/drama-dept-v1/DRAMA-PRODUCTION-SYSTEM-v1.md+DEPT-CHARTER.md | CEO 令 10-15 20:4x/23:1x 开线 | 闸链（IP 授权核/剧本闸/分镜闸/帧闸/视频闸/配音闸/成片闸）——纸面闸+PILOT-001《一路长虹》试点已出片；「GUARDRAILS 件」实存于 drama-001-stockera/GUARDRAILS（八红线+每集自审表）非 drama-dept-v1 | 现行·试点期 |
| 金融题材合规护栏 | cph4/fleet/drama-001-stockera/GUARDRAILS | CEO 令 10-16 00:0x | 每集自审表——纸面检项 | 现行·新立 |
| Agent 业务法（发现>创新>审查+失败分类学+处置矩阵） | dispatcher/AGENT-BUSINESS-LAW-v1.md | O-20261015-1030「弄全面且科学」 | 晨审哨消费（07:37 one-shot·今日改事件班常设）+点名名单；三补件（产出账本/引擎心跳/令执行率）**挂账未交付** | 现行·三补件挂账 |
| 巡视舰队（十域章程+域 digest） | dispatcher/PATROL-FLEET/BLUEPRINT.md+CHARTERS.md | O-20261014-2250 | Tools/patrol-fleet-carrier.ps1+patrol-fleet-config.json（×10 PT30M 载体·v1.1 晨波在排） | 现行·有机制 |
| 事件班承载件（红旗→无头事件班 ≤15min） | mechanism-map L0 层 | O-20261014-2345 | Tools/proxy-event-carrier.ps1（PT15M） | 现行·有机制 |
| SLI 席外对账（自产自审计破） | mechanism-map §四+dispatcher/SLI-RECONCILE.md | 10-14 主AGENT 批 | Tools/sli-reconcile.ps1+Tools/sli-reconcile-wrapper.ps1（bm-b daily 08:35） | 现行·有机制 |
| 思考路由律 v2（量产本地 35B/深判云端） | token-economy §10.2+CEO-PROXY/ROUND.md 步10 | O-20261015-1200 | ROUND 步10 硬映射+l1-client.py+SLI-4 计数台账——**L1 消费率 ~0.2% vs ≥20% 目标（止损线 10-28）** | 现行·消费率失速（A-5） |
| 十域知识地图（判断前新鲜度闸） | cph4/registry/knowledge-registry.md | CEO 令 10-14 15:4x | ROUND 步10 周一域轻研——纸面+会话；**law-registry 未登记=孤儿 D-6** | 现行·纸面（孤儿） |

*（其余在册但本次未逐字抽读的司域正典——venture/culture/city-lab/global-vision/github-radar/oss-harvest/local-first/self-drive/master-plan 等——均经 law-registry §一登记、AI.md §3/§4 指针双向可查，未发现指针断链，不再单列。）*

---

## 二、发现清单

### A｜立法≠机制最重的 10 条（法在册但执法载体缺位/迟到）

1. **S4U 注册律**（CODELY-fleet-global.md L21·09-29 判例）：法在册 17 天，登记器 10-16 才焊（C-20261016-02 L68）；bm-a 存量 ~106 件车道任务实况全 Interactive（L69），转换候委员会裁决；task-s4u-backlog.md 仅 2 件登记（L3-4）。
2. **禁 force-push 的远端机核**（versioning §5）：branch protection 自 09-23 起=CEO 物理件挂账至今未落（mechanism-map §三.3「待 CEO 一次同意」；G12-BP-PREPUSH-PROPOSAL.md 在库）——远端零闸，全靠纪律。
3. **P0 超时哨**：10-16 11:4x orders 行宣称「在役」，13:0x 行诚实律勘正自认「承 O-1120 未验证宣称·普查 A 实锤零载体」——当日才补挂到分叉修复令契约上。
4. **FleetLink 直连指挥链「机制有而没用」**（orders 10-16 11:2x 行定谳）：:8790 秒级链 10-08 已验收在役，18h jayredo 静默期间催办走 git 异步慢道、直连链零调用——部署≠执法。
5. **L1 小脑消费率**（mechanism-map §四 SLI-4）：≥20% 目标 vs 实况 ~0.2%（§五.6 诚实面）——l1-client.py 建了没人用，10-28 止损线。
6. **交付存在性监督**（C-20261016-02 病根②「派单无交付契约→监督瞎找货」）：POOL 五态法 10-14 立（CHARTER §7.3），交付哨 delivery-watch.ps1 10-16 才有——18h 静默误判案+POOL 池 16 张 open 中 10 张陈旧卡（orders 10-15 23:1x 行）同期暴露。
7. **监督班依赖 REPL durable cron**（C-20261016-02 Cure-6 根因）：CEO 在线时段 gamewin 暂停连坐清空监督 cron（10-16 08:34 实证：02:43/05:43/08:43 三班全 miss）——shift-supervisor.ps1 今日才迁 S4U 载体。
8. **交付时效律自动催办闭环**（governance §11）：夜轮 SLA 扫描在 mandate，但 P-2026-09-29-13（MiniGame .git 3.96GB 超水位）**逾期 17 天**，靠 10-16 12:41 CEO「全面清理」令才催办（orders 行自证）——扫描与催办之间无自动升级载体。
9. **台账冲突检查钩子**（governance §6.5）：纯人工 rg 冲突标记步·无脚本钩；同期实害=10-15/16 sparse-checkout 三连删仓事故+autostash 冲突族 7 天 ≥6 起（C-20261016-02 §四普查 D 路）。
10. **「机制件反向孤儿」**：Tools\ 下 banned_direction_gate.py/banned-direction-gate.ps1/banned_dispatch.py/banned_waste.py/gate_fused.py/chunk_vote_gate.py/rename_resubmit_detector.py/video_qc.py/wt-park.ps1/抓弹窗.bat 等**无任何正典条目登记其执法对应的法条**（law-registry L2 只按簇头登记产线）——机制在、法条无册可回指（用途待证）。

### B｜该归档的被替代/过期法条

1. **否决窗制度**：已废（2026-10-11 D-20261012-02）·6 处勘注已做；**残留**：memory.md 头注「T2+否决窗 7 天」、token-economy §9 头注「否决窗随主窗至 10-06」、evolution.md/versioning §4.2 类「否决窗 7 天」字样散布未逐一勘注——季度瘦身日应清。
2. **audit-charter §7.4 外审三 AI 三班制表**（auditor-A/B/C·06:17/14:17 错峰）：被 10-14「外审班日一班降频」终谳取代（law-registry §一）——表未勘注未归档。
3. **AI.md §3「日三班 22:17/06:17/14:17」行**：同上被降频取代——AI.md 10-14 三批修法未及此行，**漏勘**。
4. **resource-chain §8.1 产线矩阵 v1**：被 §9.1 定岗 v2 取代（changelog 明「冲突处以本表为准·v1 全保 git 史」）——判例合规，建议工作树压缩为指针（瘦身候选）。
5. **U252「图片一律云端」**（09-27）：被 resource-chain §九 9.1.2 云端必要闸收窄（10-07）——已勘注，旧句归档面待清。
6. **fleet-allocations §三「云默认=并行全量调用」**：被 10-15 并发帽就地修订「云道并行降档」——已勘注（resource-chain 10-15 changelog 行）。
7. **bm-a 白天 CPU 开放令（10-13）+AutoYield-WorkEnd 19:00 自动复工**：被 10-15 两令废止（§9.1 bm-a 行勘注+orders 10-15 18:4x 行「就地勘正」）——已完成勘注，任务残留备份待清（.codely-cli\task-backups）。
8. **MV-PREPRO-MASTER-v1**：被 PRODUCTION-SYSTEM-v2 升正典取代（orders 10-15 17:1x「v1 归档」）——QC-MASTER-CHECKLIST 头注仍以 v1 为「24 项类别索引」正身互锁（QC 头 L3）——两件锁死互引与新正典的交接未收口（待证）。
9. **零服务器死命令**：被服务器律 v2 废止（09-24·九处改写）——已完成。
10. **pointer 存根 8 件**（scheduling/fleet-allocations/retention/fleet-protocol/assessment/decision/review/fleet-liveness-charter）：2026-10-14 终谳=合法设施保留非死件（law-registry §四）——**不归档**（防误清）。

### C｜互相矛盾或重复的规则对

1. **S4U 律（09-29 判例：一律 S4U）vs D-20261002-02（BigMoney 域=缺省 principal 全线·S4U 0x80070005 本环境不可安装）**：decisions.md L54 明载「S4U 用户令偏离随本行呈报 CEO 改判·给提权窗即可切 (a)」——10-16 Cure-9 焊 S4U 默认后，BigMoney 域新增任务将撞 D-02 政策；同题两政策未收口（两案都自证·裁决悬置）。
2. **外审班频**：audit-charter Part A 头注「每日 22:17 一轮」+§7.4 三班表 vs law-registry「日一班降频（10-14 终谳）」vs **AI.md §3「日三班」**——三处口径，AI.md 最旧未勘。
3. **云端默认态三层叠写**：resource-chain §一.0.1「云端无限并行优先」/§二.三「默认=并行全量」vs §九（10-07 必要闸）vs token-economy §十（10-15 严管+并发帽）——现役=最新，但 §一/§二原句未就地勘注（§二.三有 10-15 changelog 修订行·正文句仍在），新会话误读风险高。
4. **memory.md §2 水位表司级 ≤50KB/热层 ≤20KB vs CODELY.md L1 卡「MiniGame 司域 84KB=线级水位 ≤10KB 的 8 倍超」**：司级与线级两套水位口径在同族文件间混用（84KB 判超引用的是 10KB 线级线）。
5. **governance §11「禁一周窗默认 SLA·存量压缩至 5 天」vs 各正典大量「两周回执窗/一周回访/10-19 回访窗」**：豁免两类（日历节点）边界含糊——回访窗属豁免、交办 SLA 属硬顶，实际执行中两类混写。
6. **RULES.md §2「文件名 English only（group-layer）」vs cph4/fleet/mv-album-001-jay/星晴-*.md、可爱女人-*.md 等中文件名（cph4=集团层新件）**：legacy exception 仅豁免子公司内部（MiniGame 09号§7），cph4 下 10 月新建中文件名按文义违反——或需扩豁免条款或属违例未纠（待证）。
7. **token-economy §3.1 本地推理栈表「14b ✓已装盘/深度线」vs 10-15 Qwen 换代（orders 10-15 15:3x 行「old qwen2.5 two models re-deleted」+35B 迁站）**：正典表现状漂移未刷（实况优先律·文档限期修正面）。
8. **audit-charter Part B §1「单班时间盒 25 分钟」vs 实况班记录 13:47-14:3x（=40min+）等多班**：时间盒为预算值·超时优雅收尾律允许，但无超限计数判据——软约束无度量。
9. **「值守轮双班 03:07/15:07」（AI.md §3）vs 资源链 §9.6 每轮自检+补货 SLA「下一决策轮 00:00/12:00」**：闲置执法三级节拍（轮级/双班/决策轮）职责交叠——§9.6 自述收编提速，但旧 §8.2「两夜 RED」链与「轮级两读触发」并存未删。
10. **law-registry「必读三件 ~21KB ≤30KB」线 vs AI.md 已漂至 ~11.1KB**（registry §六备案）——备案在册·非硬矛盾·持续漂移面。

### D｜正典登记簿查无登记的「孤儿规则文件」

| # | 孤儿件 | 性质 | 证据 |
|---|---|---|---|
| D-1 | **cph4/release-gate.md**（对外发布安全门 v1.0·T2 法） | 硬门法·law-registry L0 簇无此行 | 文件头「T2 生效+7 天否决窗」·law-registry §一 L0 表无 release-gate |
| D-2 | **cph4/audit-office.md**（集团审计部正典 v1.0·直属 CEO） | 组织法·有执法件（audit-sentinel.ps1 头注自证正身）·登记簿无行 | audit-sentinel.ps1 L1「(cph4/audit-office.md)」 |
| D-3 | **cph4/autonomy-target.md**（完美闭环自治 v1.0·T2·六指标预注册） | 目标法·无登记行 | 文件头「T2 生效+7 天否决窗」 |
| D-4 | **cph4/local-llm-pipeline.md**（本地大模型生产管线纲领 v1.0） | 建设法·无登记行（与 token-economy §3/local-first 职责分界未注） | 文件头「溯源 CEO 令 09-25」 |
| D-5 | cph4/global-benchmarks.md（全球基准面索引） | 台账/索引形态·弱候选（audit-charter Part A mod 6 消费面） | 文件头「机制=global-vision §四·本件=实验室线基准面」 |
| D-6 | **cph4/registry/knowledge-registry.md**（十域权威源地图·CEO-PROXY ROUND 步10 正身） | 执法正身·无登记行 | CEO-PROXY/CHARTER §一.6 指针+文件头 |
| D-7 | cph4/fleet/memory/CODELY-fleet-global.md（机队记忆正本·memory.md §9.1③ 承载） | 边界候选：经 memory.md 间接在册·登记簿无行 | memory.md §9.1③ |
| D-8 | 根 handover.md | 未读·形态待证 | 待证 |
| D-9 | **登记漂移**：law-registry §一「CEO-PROXY（5 件）」vs 实存 6 件（+SHIFT-SUPERVISOR-PROMPT.txt·10-16 Cure-6 新增未入账）；dispatcher 族实存 46 件（含 AGENT-BUSINESS-LAW/POOL.json/SLI-RECONCILE/L1-POOL-TRIAGE/ROUND-PROMPT/NEED-JUDGMENT 等）登记簿只覆盖簇头 | 结构漂移 | 目录实列 vs law-registry §一行 |
| D-10 | **PROMPT-EXPERT-GATE 指针悬空**：MV-PIPELINE-PLAYBOOK 指针表写「prompt-writing-spec-v1/PROMPT-EXPERT-GATE-v1.md」+CODELY.md L1 卡同写法，实存路径=cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/（mv-album-001-jay/ 下无此子目录）——消费面沿用的相对根与文件实位不一致 | 指针断链候选 | glob 实证（mv-album-001-jay 78 件中无 prompt-writing-spec-v1/） |
| D-11 | docs/ 根无真孤儿：17 件全部在册或属台账（external-audit.md=Part A 产出台账·经 audit-charter §五间接在册） | — | docs/*.md 全列比对 law-registry |

### E｜docs/orders.md 尾部 open/executing 状态行·规则挂账清单（只列不判）

- 10-15 11:0x｜O-20261015-1055 MV 全速+金融 CPU 排满令——**open**（@bm-b/@bm-c 受理）
- 10-15 13:1x｜O-20261015-1250 记忆机制优化批⑤⑥——**dispatched**（@bm-b/@bm-c 守门件机队推广+@Biggame MiniGame CODELY 84KB→≤10KB·死线 10-16 12:00）
- 10-15 18:0x｜C-20261015-03 spawn 闸 preflight 三司落位——**dispatched**（bm-c PASS·bm-b 迟到 5h39m 记档·第三司待证）
- 10-15 18:2x｜POOL-0020 bm-b 满性能恢复——**dispatched**→10-16 13:0x 行定谳「活已干卡未销」
- 10-15 20:50｜PT-20261015-01 BigStream 心跳写手长轮间隙——**dispatched**（截止 10-22·10-16 Cure-6 升级催办：席位轮换资格复审）
- 10-15 23:1x｜夜窗排产单③——POOL 池 16 张 open 中 10 张陈旧卡+POOL-0014 状态漂移（→10-16 Cure-7 清账落地）；POOL-0003 词锚复核批 **open 自 10-12**
- 10-16 00:0x｜drama-001-stockera《一路长虹》开笔令——**open**（→00:2x 剧本首包 done·GUARDRAILS 新立）
- 10-16 11:2x｜O-20261016-1120 直连同步指挥律（P0 超时哨+fleet-dispatch -ExpectSha 闭环+OrderSentinel hook 常设）——**executing**
- 10-16 11:4x｜《一路长虹》试映片 Taildrop 直送——**open**（候到件·DeliveryWatch 契约死线已过自动点名）
- 10-16 11:5x｜C-20261016-02 委员会反省+全机制普查根治案（立法≠机制病根定谳）——**in-flight**
- 10-16 12:11｜严查加深令·普查E（产出/空转/巡查对账）——**in-flight**
- 10-16 12:1x｜O-20261016-1215 机队同步架构定谳令（tailnet 第一通道/git 降位第二层）——**open**（bm-b/c 候令自升级）
- 10-16 12:41｜全面清理+催办令——**dispatched**（@Biggame git gc·软死线 10-17 12:00·P-2026-09-29-13 逾期 17 天）
- 10-16 12:4x｜O-1215 执法强化·随时同步常设令 v1.6——**executing**（候三机绿回执）
- 10-16 13:0x｜bm-a 委员会 Cure-1/3/7/8 部署回执——**executing**（Cure-2/6 已派·Cure-4/5 实装中）
- 10-16 13:0x｜@bm-c 仓分叉修复令——**P0**（2h 超时哨挂契约）；@bm-b 欠件追缴五件——**P1**（死线 14:00）
- 10-16 13:0x｜Cure-6 监督载体迁 S4U 立项——**open**（实装中）
- 10-16 13:3x｜Cure-9 点火律——**executed**，但附带挂账：bm-a 存量 ~106 件 S4U 转换**候委员会裁决**（本批未动）
- 星晴 POOL-0015 T1 海选/jayredo 17 件链——**in-flight**→13:52 done 17/17 候装配（产线件·非规则挂账·列示备查）

---

**总结一句话**：正典面 66 行规则中，约 35 行有实在执法载体（工具/哨兵/计划任务名实相符），约 22 行为「纸面·无机制或半机制」（靠 prompt/查表/抽审），9 行处于废止/被替代/漂移态。最重病根与 CEO 令 10-16「立法≠机制」定谳完全吻合：S4U 律、远端 branch protection、交付/超时/监督哨族、L1 消费率是「法在册、载体迟到或缺席」的四个最大窟窿；同时登记簿本身有 6-8 件孤儿法（release-gate/audit-office/autonomy-target/local-llm-pipeline/knowledge-registry 等）和 2 处指针断链（PROMPT-EXPERT-GATE 实位·CEO-PROXY 件数漂移），建议随 10-19 季度瘦身日一并收口。