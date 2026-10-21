# TAKEOVER-CODEMAP bm-a — 接管代码地图与现状调优方案（2026-10-21）

> 性质=席位的接管准备件（非新法条）。席位=千问工作助理（主 AGENT 待命态）。
> 令源：CEO 2026-10-21「先研读代码，做好本地该做的工作，接管时要全面」+「根据我现在的情况调优」+「之后我会用 qianwen 的本地和云端一起」。
> 调研方式=五域代码精读（游戏框架/城3D/MV链/量化/OS循环+工具链），全部路径实测存在。

## 一、五大代码域速查（入口级，细节见各域正典）

### 1. 游戏（gaming/MiniGame）★本机完全可跑
- 引擎：团结 2022.3.62t15（1.10.3），路径 `C:\Program Files\Tuanjie\Hub\Editor\2022.3.62t15\Editor\Tuanjie.exe`；版本 pin 铁律=ProjectVersion.txt 优先于 tools\machine.json（错版静默重写 manifest=X1507 事故）。
- 框架：packages\com.sy.*（12 包·file: 引用禁拷源）；能力=ServiceLocator/EventBus/Save/Time(>120s判作弊)/AdHub(headless 直落 onFallback)/UIForge(ui-layout.json 装配)。
- 门禁统一契约：`-batchmode -quit -projectPath <proj> -executeMethod Sy.PXX.YYYCheck.Run -logFile <log>`；退出码 0绿/1断言/2异常；**100% 绿=compile 0 error 且 0 warning**。
- 批跑器：`tools\GateSweep.ps1 -Project <P>`（表驱动串行·SWEEP_DONE worst=<code>）；出包 `tools\BuildPackage.ps1 -Project <P> -Bump Patch [-DryRun]`（版本权威=Design\configs\GLOBAL\build_versions.json·tag 随批）；包体闸 `tools\CheckBundle.ps1 -Project <P>`。
- 观测面：`tools\board_gen.py`（心跳 JSON→硅基生命元宇宙.html 占位符灌注）+ `tools\siliconwatch\generate.ps1`（data.js）。
- 坑：动任一工程前先认领（claims·TTL 15min）；批 wrapper 会 taskkill 同名 GUI 编辑器；shipped 源码注释仅英文（U1 法）。
- **波2 主战场**：C 档 10 款 doc→工程（G26 先行），样板=P03 骨架（manifest 8 包+七场景链+Boot/Newbie 分层+Editor 六检查类）；`tools\BootstrapProject.ps1`+AUTOMATION.md §③ 认领制。

### 2. 城（gaming/FluxVerse City3D）★本机 batchmode 可跑（无 GUI）
- 认知纠偏三条：Core/Driver/Blueprint 在 `Assets/Scripts/CitySim/`（非 Editor 下）；**SiliconToon 着色器未落地**（现状=URPMaterialBridge→URP Lit，规格件在 .codely-cli/tmp/r2-silicontoon-brief.md·索引标⬜待证）；R1-R8 在 `CitySimResidentsBatch.RunResidentsAll()`（CitySimLab 跑 A1-A5）。
- 判据面：A1-A5=路网连通/门位/全量通勤 arrived/同 seed 确定性/封桥零踩（`City3D-staging/citysim-selfcheck.md`）；R1-R8=名册/AD-042 19-19/clip/姿势差/32 全绑/位移/对账/≥4 帧（fail=0 residents=32 现值绿）。
- 跑法：`City3D-staging/*.ps1` wrapper（kill GUI→batchmode -executeMethod→*.done 哨兵判收）；纯 Python 数据链 `Tools/city/citysim-from-r0.py`、`Tools/perceptor/scan.ps1`+`verify.ps1`（world-state 两阶段原子写·单写者）。
- **B 腿改动点已勘明**（行号级）：新 `CitySimMegacityResidentsBatch.cs` 复用 ResidentsBatch L499-537 装配段→场景改 CityMegacity_Sample→路线弃 RouteLoop 改接 CitySimCore.FindPath(A*)（bp.CellCenter L41 坐标平移口）→生活轨迹数据源=`life/BigLife/census/export/citizen-behavior.jsonl`（10114 行·32 席 31 带 anchor·home/work/social 坐标域与 blueprint ±160 同量纲）→ResidentWalker 三改（段队列到点重规划/Y 补 0.20 路高/Slerp 转向）→作息驱动仿 CityStreetBehavior 10s 只读轮询 street_behavior.seats。NavMesh 已判负禁引入；车流 TrafficManager 行人不可复用。
- 坑：URPMaterialBridge.Bridge() L30 会禁用场景 DayNightCycle；DayNightCycle 用 DateTime.Now 非 UTC（改区即失真）。

### 3. MV/媒体链（cph4/fleet/mv-album-001-jay + media/）
- 本机可跑（CPU）：装配/EDL/PACK 收口（v511 链装配器在位）、W2 i2v 30 镜包**过闸待审签**（审=非起草席十一面+导演签·禁自审自签）、词锚复核 POOL-0003、剧本打磨循环 SCRIPT-POLISH-LOOP。
- 依赖 bm-c GPU（接管后机队恢复才能推）：星晴 A 批 KF 烧制、可爱女人 28 帧、三曲 KF DRAFT 签发链、i2v 量产。
- 正典指针=CANON-INDEX 二/三节；成片 full_mv_v511 家族候 CEO 终审（勿动）。

### 4. 量化（quant/bigmoney）★本机 python 可跑
- 引擎=engine\{backtester,factors,exit_rules,metrics,grid_sleeve,futures_runner,options_runner}.py；策略注册在 strategies/+firm\WAVE_LOOP_LAW.md（W 波链=候选→初筛→判决·现役 W276）。
- 纸盘账本=results\alloc_paper\ALLOC-P1..P6.json（写者=bm-b 循环·末写 10-20 22:51=停摆前）；数据=akshare 零 key；实盘零券商接口（真金红线=结构性不存在，确认）。
- 本机审计件：`Tools/quant-audit-probe*.ps1`、`quant-nav-recompute.ps1`（净值重算复核纸盘）、`Tools/quant-oversight-digest.ps1`。

### 5. OS 循环+调度+工具链（cph4 + Tools）
- iteration_loop.ps1 结构=round.lock 防重叠+静默杀闸（25min 零输出）+硬顶 240min+闸门在 Start-Process codely 前拦（CLOUD-OFF 文件存在即 suppressed）——**纯 CPU 前置簿记部分现在就能手动跑**。
- fleet-dispatcher.ps1=L0 零 LLM 旗计算（车道关键词路由 kf/i2v→bm-c·tts/audio→bm-b·whisper/assemble/ledger→bm-a；旗=STARVED/LANE-DOWN/CHASE/OFFLINE/HB-STALE；写 DISPATCH-LOG/NEED-JUDGMENT·不碰 git）。
- delivery-watch=watch JSON（expected_paths+min_count+min_duration_sec·ffmpeg 验）三态 PENDING/OVERDUE/DELIVERED。
- 令流三件套现势：order-sentinel（本地扫行可用）/fleet-dispatch poke（tailscale 依赖·现断）/fleet-link :8790（现停）。
- task-register.ps1=唯一正门（VBS 隐藏链+S4U+写后读回+点火验证）——接管建班必用。
- git 三件套：git-atomic-push.py（append 模式尾锚）、git-no-reversal-check.py --audit（丢行守望）、cloud_lane_lint.py（派单卡云路径名 BLOCK）。
- 本地维护立即可跑：retention-scan.ps1（只读水位）/selfaudit.ps1 -Days 7/repo-slim.ps1 -ReportOnly/problem-registry-audit.py（六字段机械审计）/agent-library-audit.py/memory-budget-gate.py。

## 二、按现状调优（CEO 2026-10-21 补充令）

现状四约束：①84 自动任务全停且**维持停**；②tailscale/NATS/FleetLink 断=机队失联；③白天 bm-a=CEO 用机（让路律）；④今后执行体=**千问本地+云端**（codely 无头会话退役方向，token 走千问积分制）。

**调优结论=三层作战法：**

- **T1 本地立即可做（现在·零机队·零 GPU·避开白天重活）**
  1. 游戏波2 母版直产：G26 归园田居起步——BootstrapProject→按 P03 骨架产十款工程→GateSweep 全绿→出包 DryRun。CPU 批全在 bm-a，单轮 240-900s，**排 CEO 夜间/明示时段**。
  2. MV 文审面：W2 30 镜包十一面审读件（非起草席=本席另窗出审读意见书供导演席）；三曲 KF DRAFT 的 FIX 合并提案。
  3. 台账卫生：orders.jsonl 影子读失活修复（10-09 后未同步）、CEO-PROXY/LOG.md 冲突标记残留清除（走受保护件通道=呈单候批）、CANON-INDEX 5 处不一致的验证与修法提案（只提案不擅动）。
  4. ~~量化：纸盘净值重算对账+回测复跑抽验~~ **禁（CEO 令 2026-10-21：bm-a 禁一切金融敏感业务算力·量化件整体移 bm-d/bm-b/bm-c）**。
  5. 观测面：board_gen 手动刷新保 CEO 检查入口新鲜（此件无 LLM 依赖·现成可跑）。
- **T2 本机可做但需 batchmode 窗（错峰执行）**：城 B 腿代码预备——先把 CitySimMegacityResidentsBatch.cs 写出来+本地 batchmode 自测（无居民场景版），机队恢复即联真数据。
- **T3 机队恢复后才能做（挂起清单·勿再空耗）**：MV KF/i2v 烧制链（bm-c）、双锚批 POOL-0018/0019（bm-b）、bm-b 电源复产回执（POOL-0020）、B 腿真场景联调、C 机八仓（K 盘在 bm-c）。

**调优开关（等 CEO 各一句话）**：
- 「恢复机队通道」=tailscale+NATS+FleetLink 三件（零 token·走 task-register）→T3 解锁。
- 「开工」类口令=逐线复产对应旧 codely 循环（或判由本席会话代偿）。
- 千问承载主 AGENT=默认态（本席已在位，无需开关）。

## 三、接管启动检查单（CEO 说「接管」时的 60 分钟动作序）
1. `Tools/fleet-reality.ps1` 取机队实测基线（必带时间戳）。
2. 若机队失联且未令恢复→T1/T2 范围内作业并如实标注 T3 挂起。
3. POOL 22 卡逐卡验状态（done/verified 双勾核对）+QUEUE-LOW 补货只从真实积压。
4. DEADLINES 清点：BigHouse 10-28 三判据=最险死线，优先列倒计时项。
5. orders.md 尾行核对新令→按 CHARTER §七 交接卡九要素转单（card-lint 过闸）。
6. 本件过期面随做随勘（实况优先律·改后记 changelog）。

---
*千问席 · 2026-10-21 · 五域代码精读收口件（子任务两路 max_turns 未归项=量化深层/OS循环全文，已直读补锚，遗留细节接管中按需二次精读）*
