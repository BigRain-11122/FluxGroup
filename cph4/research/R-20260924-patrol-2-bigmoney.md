# R-20260924-patrol-2-bigmoney — BigMoney 技术底层巡检报告

- 巡检日: 2026-09-24（第二次巡检）· 巡检窗口 ≈13:33–13:46 · 授权: governance 铁律 6 例外②
- 模式: **只读巡检**（只报告不修复·零 git 写操作·本报告=唯一写入件）
- 对象: `quant/bigmoney/`（gitignored 子仓·检索一律 `rg --no-ignore`/read_file 直读·实测绕过 glob/内容工具静默跳过）
- 三态: ✅在位达标 / ⚠️偏差待察 / ❌违规缺口 · 证据=实测（未测项在 §9 声明）

---

## §0 巡检卡

分级定义: E0=当日红线(重灾/即行件) · E1=本周内处置 · E2=两周窗内 · E3=观察项

| # | 级 | 事项 | 一行态 |
|---|---|---|---|
| 1 | **E0** | 产品仓根 CODELY.md = **470,562 B**（司级水位 50KB 的 9.4×）；F-10 于 10:40 实测 396,764B → 13:32 再 +73.8KB（<3h +18.6%）；对照已知上午 247.8KB = **持续恶化非梳理下降**；D-01 即行件**未启动**（`research/memory-archive/` 目录不存在=F-07/F-10 热冷分层方案零落地征兆） | ❌ |
| 2 | E1 | P-33 心跳字段扩展**未落地**：三机 `bm-*.json` 均无 `total_ram_gb`/`cpu_util_pct`；另有 schema 漂移（`cores`/`cpu_cores` 并存、bm-b GPU 双单位冗余 2355MB vs 2.5GB）+ **bm-c `last_seen`=13:58:00 未来时间戳**（>自身 clock_read 13:29:29） | ❌ |
| 3 | E1 | P-44 过拟合 8 票 Phase 0 **前腿已领后腿悬空**：T-18 归因分解批已认领+预注册冻结（r96/r97）；T-13 分段政体扩检 11:20 开票至巡检 2h+ **status=open 未认领** | ⚠️ |
| 4 | E1 | P-32 决策审核步**未接 BigMoney mandate**：iteration_prompt.txt 含 HQ-FEEDBACK 面（上报步✅）但 **decisions.md 零引用**（集团台账实在 `FluxGroup/docs/decisions.md`，决策轮首跑 R-20260924-decision-round-1 已在案） | ❌ |
| 5 | E2 | commit `[via]` 尾标 **0/15 未观察**（长度律全过：12 条抽查 max 264 字符 ≤500）；尾标口径待集团确认 | ⚠️ |
| 6 | E2 | `.gitignore` 注释引用 `Money02/ARCHIVE_MANIFEST.md` **断链**（该文件不存在；实存清单=`research/MONEY02_ASSETS.md`）；`machine/bm-a-r68` 遗留分支在 origin | ⚠️ |
| 7 | E2 | HQ-FEEDBACK **F-01~F-10 共 10 条全 open、0 处理 0 核销**（SLA 两周窗内、10-07 周轮待收；无「已处理未核销」形态） | ⚠️ |
| 8 | E3 | EM 阻断部分恢复（moneyflow 最近两拉 +3600/+120 行但每拉仍 3 连失败；P-B clist ~15.5h 后已解除）；XSTOCK build 236/274 在飞；main 落后 origin 3 commit+脏树 16 路径=ACP/GM 会话在制面（单写者让位纪律执行中，非违规） | ⚠️ |

**直优化候选**（不动语义·一次动作多收）:
1. E0 根治件=F-07/F-10 三层方案落地（热层近窗+冷层 `research/memory-archive/<YYYYMM>.md`+read_memory 热层优先口径）——方案文档已备（O-2325 链+firm/LOCAL_FIRST.md），缺的只是执行。
2. 心跳再生时一次顺带：补 `total_ram_gb`+`cpu_util_pct` 两字段+统一字段名（cores/cpu_cores 合一）+修 bm-c last_seen 未来时间戳——三缺陷同文件一次修。
3. `.gitignore` 注释指针改指 `research/MONEY02_ASSETS.md`（或补建 ARCHIVE_MANIFEST.md）。

**转办/立法建议**:
- P-33 一周回执窗内建议 fleet/tasks 开单由循环自领（心跳脚本同轮带字段扩展，避免与 F-09 周期任务撞车须 MSG 认领先行）。
- `[via]` 尾标适用口径请集团明确（实测 0/15；若仅 CEO/GM 中继 commit 适用则本面达标）。
- P-32 决策审核步建议补入 iteration_prompt.txt 一行（读 `docs/decisions.md` 新行→科学判断→执行+回执/不执行+HQ-FEEDBACK 理由），对齐 BigLife 已接形态。
- T-13 认领建议指 bm-a/bm-c 研究轮（bm-b 已满载 T-18+XSTOCK；T-13 lane affinity 本就开放 bm-a/bm-c）。

---

## §1 OS 循环健康 — ✅

- **计划任务实况**（Get-ScheduledTask 实测）: `Bigmoney-IterationLoop` State=Ready·LastRun 13:28:01·**LastResult=0**·NextRun 13:38（10min 节奏）；`Bigmoney-LoopWatchdog` State=Ready·LastRun 13:20:01·**LastResult=0**·NextRun 13:50（30min 节奏）。动作链: wscript→InvisibleRunner.vbs→`Tools/iteration_loop.ps1` / `Tools/watchdog.ps1`。
- **轮账本新鲜度**: state.json（bm-b r97·last_round_at 2026-09-24 13:17:11·last_result=ok）；state-bm-a.json（R73·13:31:21）；state-bm-c.json（r51·13:25:00）；round_reports.md 152,107B@13:22 / bm-a 112,388B@13:32 / bm-c 77,100B@13:32；run_20260924_132802.log@13:33:32——三账本全部 ≤20min 新鲜。
- **tokens 标准行在位性**（token-economy 计量先行律）: ✅ 每轮 S6 链尾均有 token delta 实测行（r86 -198 / r89 +63 / R69 +92 / r95 -137 / r96 -11 / r97 -80 / R73 +365）；`scripts/token_meter.py` 在位；`results/token_usage.json` 1,456B@13:41:41（巡检中仍在更新=活计量）。

## §2 记忆水位 — ❌（E0·全巡检最重灾）

- `quant/CODELY.md` = **3,135 B** ✅（远低 50KB 水位）。
- 产品仓根 `quant/bigmoney/CODELY.md` = **470,562 B**（13:32:41）❌ = 司级 ≤50KB 水位的 **9.4×**。
- 恶化轨迹: 已知 09-24 上午 247.8KB（巡检令给定）→ F-10 于 10:40 复测 396,764B（≈110k tokens/轮·3 机×6 轮/h≈日数千万 tokens 级重复读载）→ 本次 13:32 **470,562B**——**验证结论: 未开始梳理下降，反而在加速膨胀**；D-01 即行件零落地征兆（`research/memory-archive/` 目录 ABSENT；CODELY.md 内「token」115 处命中=条目持续累积）。
- 顺带实测: 集团根 `FluxGroup/CODELY.md` = 100,787B（超水位 2×，非本巡检主对象，记录备查）。

## §3 git 纪律 — ⚠️（主干健康·尾标口径待证）

- **remote 连通**: `git@github.com:BigRain-11122/BigMoney.git`（SSH）·ls-remote 实测通（5 heads）✅。
- **push 积压**: origin/main..HEAD = **0** ✅ 无未推积压；本地 main 落后 origin 3 commit（S0 退避=ACP 会话在制所致，轮报告自述一致，非违规）。
- **commit 长度抽查**: 最近 12 条 max **264 字符** ✅ 全部 ≤500；`[via]` 尾标 **0/15 未观察** ⚠️（口径待集团确认，见 §0-E2）。
- **fleet 机器分支面**: origin 四支实在 ✅——machine/bm-a（79418e2·09-23 17:28·T-01 接收官）/ machine/bm-b（71c40c6·09-24 10:53）/ machine/bm-c（e7e21e0·09-24 01:10）/ machine/bm-a-r68（a656cfb·遗留快照支）。
- 脏树 16 路径（M×7: CODELY.md+6 镜像+update_daily.py；??×9: V3/V4 会话研究文档+状态件）= 已知 ACP/GM 会话在制面，循环按单写者让位不碰（R69-73 先例链在案）。

## §4 台账与决策轮 — ⚠️（台账面✅·P-32 半接·P-33 未落）

- **orders 台账**: 41 单实测；最新 `O-20260924-1325-bm-a.md`@13:22:52（<20min 新鲜）✅；bm-a ack **41/41**，bm-b/bm-c ack 40（O-1325 待各自下一轮，节奏内非滞后）。
- **HQ-FEEDBACK 当日上报（23:00 截止制）**: ✅ 当日 3 条（F-20260924-08 01:45 bm-a / F-09 04:38 bm-c / F-10 10:55 quant-GM），截止未到。
- **P-32 上报/审核步 mandate 接线**: 上报步 ✅（prompt 含 HQ-FEEDBACK 面+当日 3 条实弹）；**决策审核步 ❌**——`Tools/iteration_prompt.txt` 中 `decisions.md` **零引用**（-o 精确匹配仅命中 HQ-FEEDBACK 一处）；集团台账实在 `FluxGroup/docs/decisions.md`，决策轮已活（decision-round.ps1+首跑报告在案）。
- **P-33 心跳字段扩展（一周回执窗验证）**: ❌ 三机 `fleet/machines/bm-*.json` 均无 `total_ram_gb`+`cpu_util_pct`（bm-a/bm/bm-c 逐字段核对实测）；附带数据质量: bm-c `last_seen`=13:58:00 **未来时间戳**（>自身 heartbeat_epoch 1790227769=clock_read 13:29:29，>文件 mtime 13:32）；bm-b GPU 字段双单位冗余（`gpu_idle_vram_mb` 2355 与 `gpu_free_vram_gb` 2.5 并存）；`cores`/`cpu_cores` 两代字段名并存（bm-c 同文件双写）。

## §5 工具链门禁 — ✅

- **smoke**: 23/23 ×12 连 pass（10:18→13:29 smoke.log 实测；任务书基线「smoke 20」已自然扩至 23）✅。
- **G1'/G2/gates 最近 verdict**: `results/regime_calibration_v3.json`（@13:10:47）`"verdict": "PASS"`——T-10 v3 首次校准全过（r94 12:55: G1 R+O 196d=12.01%∈[2,25]；G2 orange FA 0.0%→LOW-POWER 注记随 enforce 提案；G3 zero-gap）；science_gates selftest **30/30**（r97）；ENFORCE_PROPOSAL_REGIME_GUARD_V3.md 已建档→GM 已批（O-1325→**T-21** enforce 接线票，与 T-20 构成 10-01 同界锁，兄弟姐妹机不得自启 enforce wiring）。
- **D7 样本充分性律后新增判据运行状态**: ✅ `research/BACKTEST_SCIENCE.md` §10 已立法（CEO 亲令 O-20260924-1141·T2 机制级·否决窗至 2026-10-01）；新判据已接线在跑——T-18 预注册含「有效样本四必报（IS2 笔数/覆盖年数/独立政体窗数=floor(日/63)/CI 宽度）」+stationary bootstrap 95% CI（块长 10 日·1000 重抽）+PBO（López de Prado 2015·C(8,4)=70 组合）；DEEP_AXIS_REVALIDATION.md 已按 D7「滚动全量口径」落 null 深轴重生成条款。

## §6 技术债对账 — ⚠️（T-18 在途✅·T-13 未领❌·P-44 半自领）

- **P-44 过拟合 8 票认领痕迹**（票源=cph4/research/R-20260924-infra-0-synthesis.md: Phase 0=归因分解批+分段政体扩检先行→Phase 1 加性补件 E4/E5/E3/E8/E9）:
  - 前腿 **T-18 归因分解批（深史主轴复验）= 已循环自领** ✅——r96 认领（MSG-1325+ticket flip+commit 1045da2=F-04 锁）→ r97 预注册冻结（DEEP_AXIS_REVALIDATION.md sha 5cdea03e·seed 54_000 入 SEED_REGISTRY·零引擎跑）。
  - 后腿 **T-13 分段政体扩检 = status open 未认领** ❌（11:20 GM 开票，至巡检 2h+ 无 claim；票面经 read_file 字节级复核为干净 UTF-8，spec 完整）。
  - Phase 1 判据补件：E4 walk-forward/E5 purged CV 仅见 V3/V4 会话文档讨论层（STRATEGY_SYSTEM_V3/V4_EVOLUTION/SYSTEM_LOGIC，均未跟踪在制），科学层无实现件——未到启动期（Phase 0 先行纪律使然，非缺口）。
  - 注: 「P-44」字串在 bigmoney 仓内零直接命中（承接形态=T-18/T-13 任务票）。
- **T-18 深史批在途状态**: ✅ 健康——prereg 冻结完成→下一程 gates/build 实现（GA-GF 基建门+manifest 冻结；nulls/reval/pbo 受 GF 硬门闸=T-19 adjusted view 前置，O-1310 s3 遵守）。
- **T-13 政体批在途状态**: ❌ 未启动（见上）。
- 顺带: **T-10 已 CLOSED**（全 4 交付: v3 全过+cf 12 腿+enforce 提案+票据 done）。

## §7 资源面 — ✅/⚠️

- **三机心跳实况**: bm-a last_seen 13:31:21（32 核/free_ram 37.9GB/GPU free 4.8GB·dev-machine）；bm-b 13:20:20（16 核/10.7GB·compute-node·**XSTOCK build 236/274 在飞** PID 22736 累计 cpu 9975s+waiter 27680 BelowNormal 已武装，harvest r98+）；bm-c clock_read 13:29:29（32 核/9.9GB）——全部 ≤22min 新鲜 ✅（bm-c last_seen 未来时间戳异常计入 §4-E1）。
- **Money02 大资产在途（retention §3 引用闸·T-01 状态）**: ✅ **T-01 链已闭环非在途**——transfers/T-2026-09-23-01 receiver manifest: 10,444 文件/1,167,172,943 字节/full_hash sha256 逐件；本地 `Money02/data/bars` 实测 **10,444 文件**；machine/bm-a 末端 commit 自述「T-01 bars receive leg COMPLETE (dual -Verify PASS)」；T-13 票面引「bars anchor 10444 files verified local, T-01 chain closed」三源互证。retention 引用闸（.gitignore: Money02/* 排除+小件白名单；bars 1.1GB/cache 6.5GB 排除归档）执行中 ✅；唯注释引用的 `Money02/ARCHIVE_MANIFEST.md` 断链（实存=research/MONEY02_ASSETS.md）⚠️。
- **回测动员令（CPU 保留 20%）执行征兆**: 令面已进化——09-23 23:47 MSG-2347 动员令（Worker=floor(核×0.8)≈保留 20%）→ **09-24 11:36 O-1136 CPU 满载令取代 O-1738 保留 20%**（CODELY.md 11:50 条目实录: BelowNormal 满载批池·空闲 ≥95% 铺真实回测批·禁造任务凑数·违令判据=S6 水位项 py<70% 持续 15min+）。执行征兆实测: bm-b 在飞批+waiter BelowNormal（O-1136 批池纪律）✅；水位探针三机接线（watermark probe bootstrap·MSG-1310 共享实现零重复）✅；bm-a/bm-c 无票可跑**如实报 idle_with_work**（R69/R71/R73 audit 旗标诚实；R71 cap_violation 88%=GUI 会话租户、我方 py 0.6%=诚实归因非我方超限）✅ 禁凑数纪律遵守。

## §8 安全面 — ✅（零真实泄漏·指纹如下）

- **secret 样式扫描**（rg --no-ignore 全仓·只报指纹）: 命中 3 文件全良性——`PLAN.md`=环境变量设计行（`BIGMONEY_API_KEY` 等一律从 env 读=好实践）；`Money0923/MoneyViz/ProjectSettings/*.asset`=`ps4NPTitleSecret:`/`uosSecret:` **空值** Unity 字段；**零** AKIA/sk-/ghp_/BEGIN PRIVATE KEY 命中。
- **gitignore 密钥面**: 无 .env 类排除行（现仓无 secret 文件=低风险，建议预置一行防未来误入）；`fleet/machine.json` 明确不跟踪（X104 跨机身份覆盖教训）✅；`Tools/bin/`（croc 传输件）排除 ✅。
- **SSH**: remote 走 SSH；仓局部 `core.sshCommand = ssh -o ProxyCommand=none`（ssh.github.com:443 直连加速，MSG-1520 在案）；IP 面仅 127.0.0.1 回环（config/settings.py `QUANT_MASTER_TS_IP` 默认值、llm_assist.py OLLAMA_HOST:11434）；无 sshpass/无公网 IP/无硬编码凭据。

## 专项三查

- **① watchdog 车道归属律（F-08 修复后复发检查）**: ✅ **未复发**——`Tools/watchdog.ps1` 车道护栏代码在位（`$BatchLaneOwner='bm-b'`+C4/C5 非 owner 记日志跳过，车道迁移须同 commit 移动常量）；watchdog.log 尾部 09:20→13:20 每 30min 稳定输出「C4/C5 skipped on bm-a: ext-slots/P-1c lane owned by bm-b」，01:20 首违规后再无重启动作行。
- **② EM 行情域阻断（F-06）当前态**: ⚠️ **子域级间歇·部分恢复**——moneyflow_refresh.log 尾部仍循环「source-level block suspected (3 consecutive connection failures)」但最近两拉实收 **+3600 行/+120 行（cutoff 2026-09-23）**；bm-b r89（10:53）P-B CLIST BLOCK **LIFTED**（~15.5h 后解除，复拉 PID 21012 在飞·checkpoint 续拉·f102 熔断保护）；push2/push2his/emappdata 族间歇、datacenter 域通——按 F-06 子域分块判定口径，**未全解**，自愈循环按设计运转。
- **③ HQ-FEEDBACK F-01~F-10 十条 open 处理进度（SLA 10-07 周轮）**: 10/10 全 open·**0 处理 0 核销**；无「已处理未核销」形态（处理面为空=SLA 窗内未逾期，09-23 提报最早到期 10-07）；F-07/F-08（CODELY token 烧点）已由 F-10 以一日 ×2.6 恶化实证刷新升级，证据链完整待周轮收件。

## §9 诚实自检

1. **读法伪影披露**: Windows PowerShell `Get-Content` 默认 GBK 解码致 UTF-8 中文显示乱码（HANDOVER.md/MONEY02_ASSETS.md/T-13 票 JSON 首读均现乱码）——经 read_file 字节级复核**三处皆为干净 UTF-8，乱码是巡检读法伪影非仓内损坏**；该 PS GBK 陷阱本身即 r97 轮报告在册坑律（R13 家族），巡检全程改用 rg/read_file 后未再误判。
2. **未测项**: ① `[via]` 尾标口径未从集团规则文核实（仅实测 0/15 缺席）；② bm-b/bm-c 远端机内进程实况未直连验证（以心跳 JSON+轮报告自述为准）；③ secret 扫描为样式扫描非穷尽熵扫描；④ T-18 预注册 sha 5cdea03e 未重算复核（引用 r97 轮报告自述）；⑤ EM 阻断根因未活探（仅读日志+轮报告）。
3. **大文件纪律**: 470KB CODELY.md 未全量读（仅 rg 定位+水位测量+定点条目引用）✅。
4. **快照声明**: 活跃系统实时变化——巡检中 `regime_state.json`@13:41:08、`token_usage.json`@13:41:41 仍在被循环更新；本报告所有数值=13:33–13:46 时点快照。
5. **巡检动作合规**: 全程零修复·零 git 写操作·唯一写入件=本报告 ✅。

— CPH4 Labs 技术底层巡检员 · 2026-09-24
