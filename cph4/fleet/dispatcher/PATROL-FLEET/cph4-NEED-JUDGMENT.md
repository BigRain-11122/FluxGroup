# cph4-NEED-JUDGMENT — CPH4 巡视席（实验室·调研/技术底层）

> 章程 = cph4/fleet/dispatcher/PATROL-FLEET/CHARTERS.md §9。本件只登记本席域内未决项与待枢纽消费项；不直写 orders/decisions/POOL/DEADLINES（章程纪律），不改法条（修法走 governance §9）。

## 呈上级枢纽（2026-11-01 06:10 R1 班·载波触发）

- [cph4#R1-1 | 节奏·域研断供] **十域知识周轮研 8.1 天零产出 + 覆盖仅 5/10 域 + 知识地图 17.8 天未更** ｜证据链：① `cph4/research/` 末一批域研件 = `R-20261023-scan-*` 五份（bigstream 10-23 23:33:49 / cph4 23:35:14 / biggame 23:37:57 / bigmoney 23:39:18 / silicon-city 10-24 04:36:24），此后至 2026-11-01 06:07 无任何域研 R- 新件（8.1 天）；② **品种缺口**：该批仅 5 份，十域（Biggame / BigMoney / BigStream / BigLife / BigDomain / BigCompute / FluxVerse / BigHouse / CPH4 / 集团横切）中 **BigLife / BigDomain / BigCompute / FluxVerse / BigHouse 五域零覆盖**；③ 地图面 `cph4/registry/knowledge-registry.md` 2,772B，mtime **2026-10-14 16:17**（17.8 天未更）——ROUND 步10「每周一域轻研·R- 档落 cph4/research/」的产出面与地图面**同时静默**；④ 期间 `cph4/research/` 仅有 decision-round 体裁（10-26~10-28 共 7 份），实测 `R-20261028-decision-round-25.md` 结构为收取面/四处硬证据/拍板传导表/复盘四问，**该体裁不承担域研**，不能顶替 ⑤ 判读：非单件延迟，是「周轮研节奏」整体断供。责任面 = CEO-PROXY ROUND 步10（12 班/日在跑，PULSE 06:03:11 brain 行「all 6 lines served today」=六线在役，唯域研未落），本席只登记不代派。｜建议动作（枢纽决）：a) 明确 11-01~11-08 周内五缺域的轮研排期与 R- 命名/交付窗；b) 复核步10 是否被更高优先级长期挤压；c) 是否将域研并入既有 12 班或单设周班——改频走 cadence §8 正法，禁自建新机制（命令查重律）。

- [cph4#R1-2 | 能力面·技能文件损坏] **`unity-graphics` SKILL.md frontmatter YAML 破损（一行两列表项）→ 该技能可能整枚不加载** ｜证据链：① `C:\Users\sjs20\.codely-cli\skills\unity-graphics\SKILL.md`，22,092B，mtime 2026-10-20 20:48；② 第 6-7 行原文实测 = `  - "**/*.hlsl"  - "**/*.shadergraph"`（两个列表项挤同一行），第 7 行即解析异常点（另席 06:10 报 line 6 col 18，同源）；③ 本席独立扫描两处技能根（`C:\Users\sjs20\.codely-cli\skills` 与仓内 `.codely-cli\skills`）全部 SKILL.md 前 15 行的同类「一行两项」模式，**命中 1 处即本件**——其余技能面干净，非批量腐化。｜影响：Unity 图形/渲染指引（URP/HDRP/Built-in、Shader Graph、Render Graph、批处理/Draw Call、GPU Instancing）属静默能力损失；非生产代码风险，不影响在飞产品。｜建议动作（枢纽决）：a) 一行拆分修复（第 7 行还原为 `  - "**/*.hlsl"` 与 `  - "**/*.shadergraph"` 两行）；b) 修复后做一次技能加载验证确认恢复；c) 是否给技能文件加 frontmatter 语法闸由枢纽裁，本席不自行加闸。本件为可逆一行修复，但不在 §9 即决清单（章程仅授登记权），故不代改。

- [cph4#R1-3 | 本席自身·复用不重立] **HQ-Patrol-CPH4 计划任务 Disabled → 本域巡视自 10-18 起全靠载波触发** ｜证据：`group-NEED-JUDGMENT.md` group#R9-4（八域 Disabled 在案 `Tools/task-expected-disabled.json`，理由「HQ-Patrol 系已被 HQ-Patrol-Group 取代」，review_by 2026-11-08）；本席 `cph4-shiftlog.md` 末次自跑班 = 2026-10-18 07:5x，此后仅 10-19/10-20 digest 与 2026-11-01 06:07 载波班。**已在案，按命令查重律不重立**，仅作 R1-1 的结构成因备注：域研无人盯 = 「巡视席不在岗」×「步10 未落」双因叠加。11-08 复审面由 group 席持有，本席不催办。

## 已裁/维持（不重复升）

- **必读三件超帽**：AI.md 13,418B + RULES.md 4,369B + CEO-DIRECTION-BRIEF 15,582B = 33,369B（32.6KB）> 30KB 帽 —— 已由 NJ-4 r2 判「维持」，本班不重旗（传感复用，禁重测）。
- **law-registry 陈旧**：16,233B / 75 行，≤30KB 帽内；mtime 2026-10-20 18:20（约 12 天）——group 席已多轮在案（R11/R12/R13 行），按查重律不重立。
- **调研五律**：近 7 份 R-（decision-round 17/18/19/20/21/25/retro）行数 15-27 行均 ≤60 ✓；`R-20261023-scan-cph4/bigmoney/silicon-city` 含应用表/验证声明/分级源 ✓；decision-round 体裁以「收取面+硬证据+拍板传导表」为应用表等价物，不判打回。
- **能力注册表新鲜度**：`cph4/agents/AGENT-LIBRARY.md` 16,810B mtime 2026-10-30 13:22（2 天内）✓。
## CPH4 巡视 R2 · 2026-11-02 06:2x（触发=carrier R2.63(b) bm-b 打盹+分叉 · 全只读·零云端·零 poke·零 spawn）

[cph4#R2-1 | 机器面·触发复核：**打盹已变性、分叉未收**]
触发所据证据=00:13:10 `/health` ok + RAM 饿死；06:23:15 实测已变：`/status` ram_free=13.3GB、KV `state.bm-b` seq=393 @06:23:50 ram 13.1GB cpu 29%、:8790 health ok → **RAM 阻塞已解除，bm-b 有产能**。残留问题转移为两条：①**分叉仍在**——`repo_heads["."]=c1d7762e`，bm-a 侧 `git cat-file -t c1d7762e` = fatal（origin 无此对象）⇒ bm-b 本地独有提交，pull 报 `.:updated` 但 HEAD 不动，工具树停在旧版；②**wake 仍被自己挡**——last_pull(03:30:11) wakes=`HQ-ProductionClaim:deny / MiniGameEngineTick:deny`，正是旧 `fleet-nodes.json` 判据（承 D-R261-POKECFG-STALE）。判据/建议（本席只登记，不改机器域）：bm-b 侧需一次 `reset --mixed origin/main`（或人工）才能收敛，CEO 10-23 令禁远端调度 ⇒ 候枢纽指派。

[cph4#R2-2 | 机器面·bm-c 全域不可达（第 3 班）]
06:23:0x `http://100.123.74.104:8790/health` 超时；NATS `state.bm-c` = key not found（TTL 10m 已过期）⇒ 非探测抖动，是真离线。R2.63(00:01)/R2.64(03:26)/R2.65(04:06) 已三度登记，本级为第 4 次观测，L2 遥测 SLO 违约持续 >6h。远程不可修（CEO 2026-10-23）⇒ 仍候枢纽/现场处理。

[cph4#R2-3 | 派单面·4 张 OPEN 全部指 bm-b，其中 2 张重复、1 张产物已在盘]
`PRODUCTION-QUEUE.jsonl` 现 OPEN 4：`Q-TTS-1202R`(bm-b，交付路径在 bm-b 本机 media/drama-tts-out) / `Q-TRIAGE-BIGMONEY-20261101`(bm-b) / `R-TRIAGE-BIGSTREAMDUANJU-BMB-20261101`(bm-b) / `C-FIN-ETF-COMPOSITE`(bm-b)。
重复面：同 id `Q-TRIAGE-BIGMONEY-20261101` 另有 bm-a 侧 RUNNING 行（03:34:11 claim）；`R-TRIAGE-BIGSTREAMDUANJU-BMB-20261101` 的交付物名与 bm-c 的 `Q-TRIAGE-BIGSTREAMDUANJU-20261101`(UNVERIFIED) 同件。
已在盘面：`quant/bigmoney/results/etf_composite_pf.json` mtime 2026-11-02 04:18:39 ⇒ C-FIN-ETF-COMPOSITE 的交付物已存在却仍未收口（承 D-R264-ZOMBIE-DELIVERABLE 同族：只看存在性不收口）。
含义：bm-b 已恢复产能、bm-a 有 45.7GB 空闲却 16 轮 IDLE，产能被"指卡"结构卡住，不是算力问题。

[cph4#R2-4 | 台账面·bm-a 僵尸重跑 R-PLAN-BIGLIFE-20261102（3h 33 次）]
`git log --since=2026-11-02 03:00` = 54 提交，其中 33 条为同一卡 `job(R-PLAN-BIGLIFE-20261102): artifact`（61%），节奏约每 5 分钟一条（05:39/05:44/05:49…06:24）。该卡在队列里已 DONE，但每轮仍被重派重跑并提交同件制品 ⇒ 提交噪音 + 主控真空的假象来源之一（bigcompute r11 独立测到"72/98 条重复产物提交"，同源）。承 D-R263/D-R264 同族，本次为第 3 班观测。

[cph4#R2-5 | cph4 域·十域调研节奏 **第 2 轮未决 → 按章程升枢纽**
`cph4/research/` 末件 = `R-20261028-decision-round-25.md`（10-28 00:09，5 天前）；`cph4/research/waves/` 末件 = W4（10-15 17:17，**18 天**）；十域中 BigLife/BigDomain/BigCompute/FluxVerse/BigHouse 仍零覆盖。承 `cph4#R1-1`（11-01 06:10 登记）本轮无任何进展 ⇒ 两轮未决，候枢纽收。

**本域核实无旗（避免重复登记）**：①`law-registry` 16,233B / 75 行 < 30KB 帽；②`cph4/agents/AGENT-LIBRARY.md` mtime 10-30 13:22（3 日内，无撞车面扫描需求）；③本班无可审的新 R- 研究件——`research/` 现存件均为 decision-round（结构=萃取+硬证据+四版传输+反向问题），非 §9① 意义上的调研五律件，故五律/防线二本轮**无对象可审**（非"已合规"）。

**触发旗处置**：本触发源自 DISPATCH-LOG 中 00:13:10 的历史行重复点火（其 RAM 论据已失效）⇒ snooze 至 2026-11-03 06:25；真实残留（分叉/bm-c/指卡/僵尸重跑/调研节奏）已按上 R2-1..R2-5 独立登记。复活条件见 snooze 件 note。

## CPH4 巡视 R3 · 2026-11-02 07:37-07:45（触发=R2.66(d) D-R266-LANE-MTIME-SELFPROOF · 全只读 · 零云端 · 零 poke · 零 spawn · 零受保护件改动）

[cph4#R3-1 | 技术底层·D-R266 机制级复核：**缺陷属实且当下仍在生效，但 R2.66 的机制表述有三处需勘正**]

**（1）生效实证（本班 07:4x 直读盘面）**：`cph4/fleet/lanes/bm-c.json` = `{node:bm-c, ts:2026-11-02T07:30:40, jobs:[], idle_reason:"SELF-DISPATCH: lane scans its own backlog", lane_ok:true, capacity_note:"ram-unknown"}`，mtime=07:33:20；而 bm-c 于 07:27 实测 TCP 8790/4222 双 closed、NATS KV 无 `state.bm-c`（R2.65 04:1x / R2.66 07:27 两测在案，本班按传感复用律不再复测）⇒ `master_agent.py::sense()` L84-96 回退读该件 mtime（age < OFFLINE_AFTER_S=900s）判 `online=True`。离线机仍被当在线派活，卡片静默滞留，**成立**。

**（2）勘正①·写频**：R2.66 称「每轮对每台机写一次（含离线机）」——不成立。`write_lane_files` L548-551 有去重闸：`if old.get("jobs") == payload["jobs"] and old.get("idle_reason") == idle_reason: continue`。离线空闲机的 `jobs=[]` 与 `idle_reason` 恒定 ⇒ 反而**不重写、mtime 不推进**（属陈旧漏判面），不是「恒新鲜」；只有状态变化（如 idle_reason 在 DAY-YIELD / CAPACITY-BLOCKED / SELF-DISPATCH 之间切换）才落盘。

**（3）勘正②·mtime 归属**：该 mtime 连「谁写的」都不代表。本班 git reflog 实证：`07:32:52 rebase (start): checkout origin/main` → `07:32:52 rebase (finish)`，随后 `bm-a/bm-b/bm-c` 三件 lane 文件 mtime **齐刷为 07:33:20**，且 `git status` 三件均为 ` M` ⇒ 任一节点的 git checkout / rebase / pull 都会刷新全部 lane 件 mtime。故 mtime 是「主控最近写过或有人 checkout 过」的代理，不是「机器活性」的代理。

**（4）勘正③·第二条强制在线路径**：`master_agent.py` L602-613 BUSY-SILENT —— 对**持 RUNNING 卡且心跳陈旧**的节点直接 `_f["online"] = True`，并注 `note="busy-silent: RUNNING <id>, heartbeat stale"`。这条是为 2026-11-01 bm-b「在跑 TTS 却被判 OFFLINE」误判加的补丁位，**修 D-R266 时不可一刀切删**（删则复发同类误判，L79-83 代码注释明载该事故）。

**（5）深因（R2.66 未指出）**：`sense()` L84-96 回退注释写的是「the lane file **the box commits** every cycle」——但 `Tools/**/*.py` 全量 grep 实测：写 lane 件的只有 `master_agent.write_lane_files`（`fleet_lane.lane_file()` 除 `master_agent.py` 外无任何写入点，`agent.py` / `lane_agent.py` 均无）⇒ **回退所依赖的那位「机器自写 lane」的写手从未存在**，回退读到的是主控自己的心跳节奏。这是本缺陷的架构级根因，比「mtime 自证」更准确地描述了它。

**（6）修法候选（枢纽决；Tools 属受保护面，本席只登记不改）**：
- a) 最小手术：`write_lane_files` 的 payload 增 `hb_age_s` / `hb_src`（落盘时取 `sense()` 的 KV age 与来源），`sense()` 回退改读该字段而非 `getmtime`；回退命中时标 `state_source="lanes-file-stale"`。
- b) 派单面止血（可零代码先做）：`state_source` 为 lanes-file 回退、或 `capacity_note=="ram-unknown"` 的节点**禁派新 OPEN 卡**，只允许其名下 RUNNING 卡继续被监视（与 BUSY-SILENT 同语义），即可立刻停掉「离线机被派活→卡片静默滞留」。
- c) 根治：让机器自写 liveness（`agent.py` 每轮写 `lanes/<node>.self.json` 含自身 `ts_utc_ms` 并随心跳提交）——但 bm-b/bm-c 工树分叉使自动提交不可靠（R2.59/R2.61/R2.65 在案），须先修分叉，否则等于再造一个假绿面。

**（7）查重声明**：缺陷本体 D-R266 已由 R2.66 登记，bigdomain 席 07:34 已就同一触发现出判（「属实但非新根源」）；本席不重登记缺陷本体、不重派、不写 snooze（真实事故禁 snooze），仅补上述机制级勘正与修法收窄，避免枢纽按错误机制实施修法。

**（8）本班域雷达面（§9 · 复用不重测）**：①调研五律 / ②防线二——`cph4/research/` 末件仍 `R-20261028-decision-round-25.md`（10-28 00:09），无新 R- 件 ⇒ 本轮无对象可审；③能力注册表——`cph4/agents/AGENT-LIBRARY.md` 16,810B @10-30 13:22（4 天内）；两个技能根（repo/home）近 4 天**零新增目录** ⇒ 撞车扫描无对象；④正典链——`cph4/registry/law-registry.md` 16,233B @10-20 18:20，≤30KB 帽内（13 天陈旧已在 group 席多轮在案，不重立）；必读三件 33.4KB>30KB 已判「维持」（NJ-4 r2），不重旗；⑤十域周轮研节奏——`cph4#R2-5` 已两轮未决升枢纽候收，本轮零进展，按查重律不重立；⑥技术底层巡检授权面——本班只读代码与台账，零产品代码改动、零 spawn、零云端，合规。

