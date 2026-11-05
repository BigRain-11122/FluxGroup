# PROBLEM-REGISTRY — 问题追溯台账（正身）

- 立法: docs/governance.md §9 问题追溯闭环律（C-20261017-01·2026-10-17）
- 审计: python Tools/problem-registry-audit.py（CEO-PROXY 日 23:43 夜移交班点火·FAIL 阻断次日派单；周日深复盘全条目对账）
- 编号: PR-YYYYMMDD-NN（立册日+当日序号）·六字段=来源/复发史·根因/出生地闸/验证证据/复发计数/状态
- 状态语义: open=在案未闭环｜armed=整改已上链待验证（连续两审计周期 PASS+回访证据才准 closed）｜closed=验证证据在案且两周期零复发｜open-CEO=等 CEO 物理动作（零催办·状态件呈报）
- 铁律: 「已立法≠closed」·复发计数只增不减永不归零（席7 骑士）·复发 ≥2=点名问责窗双窗核对认领
- 收编指针（本册为唯一正身·五散账降为指针行）: EXPERIENCE-LEDGER-v1（cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/）·EXECUTION-FIX-LEDGER-20261011（cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/）·QC-MASTER-CHECKLIST-v1 问题面（cph4/fleet/mv-album-001-jay/）·patrol RED-FLAGS 族（运行时件）·根记忆坑录族（CODELY.md）——新问题一律入本册·禁再开新账
- 条目纪律: 指针式 ≤120 字/字段·周对账抽检

### PR-20261017-01 闲置复发
- 来源: CEO 斥责令族（最近 10-18 21:3x「所以我还是看到机队算力闲置！」+同日「你们真有意思，反反复复的闲置！」）·指针=EXPERIENCE-LEDGER+C-20261001-03/C-20261007-05
- 复发史·根因: 七连复发（10-18 单日三提：晨「GPU闲着干嘛」+晚机队闲置+反反复复）·新根因面=①产线收官链后无预挂后继（bm-c GPU 空窗 20:00-21:44 当窗自认）②备货池补货 SLA 再违例（bm-b board empty 21:38 实测）③导演席积压三件阻塞下游（bm-a S5-27/F5-33c/B批）
- 出生地闸: 派单→执行环节缺回访闭环件（十环节表 #2→#8 断链）+收官链→后继预挂缺位（生产连续性面）
- 验证证据: C-20261007-05 构造化自检三机两席+备货池在役·armed 待两周期审计；10-18 当窗执法=O-20261018-2144-bm-c 实测点名派工（bm-a 三裁+自领活+补货 SLA·bm-b 自有 P1 开工）+bm-c 自查自纠（wave-3 点火 99% 满载）
- 复发计数: 7
- 状态: armed
- 升格记录: 2026-10-17 立册即按二犯档升格·问责面=值守轮点名+CEO 再提闲置即违例计数挂 patrol；2026-10-18 七连记账·单日三提·当班窗=bm-c 交互窗（GPU 空窗自承）+bm-b 循环班（池荒 idle_rounds=5）+bm-a 循环班（GPU 0%）——O-2144 已派·10-19 委员会窗并案判根治

### PR-20261017-02 弹窗复发
- 来源: CEO 静默令族（10-06 三申斥+「又开始疯狂弹窗了！能不能根治！」）·指针=根记忆坑录族 10-06/10-07 条
- 复发史·根因: 四连复发（三次申斥+第七复活源实锤）·根因=复活源清单不全+闸值设完不读回；10-17 五连·CEO 令原话「本机干活静默 不要给我疯狂弹窗」·新面=无头会话控制台窗族（10-08 齐射族·codely 厂商 bug·非 toast 族）
- 出生地闸: 静默执法环节缺「设+读回+服务重启」三步验证件（十环节表 #3 执行面）
- 验证证据: 10-07 托盘 app 先杀+ollama 全家族复验正法在册·部署面 armed 待两周期；10-17 收容所形态实测=quake 接入即弹抢焦点（VIS+FG 全程命令周期实锚）→wt-park v2 普通最小化窗静默吸收（IC=True FG=False 全程）+HQ-WT-Park 保活车道补位
- 复发计数: 6
- 状态: armed
- 升格记录: 2026-10-17 立册按二犯档·复发即点名当班窗问责；2026-10-17 五连复发记账·当窗执法=WT 收容所 v2（useExistingQuiet+普通最小化驻留窗+PT1M 保活车道）·当班窗=bm-c 交互窗自记自承；2026-10-24 六连（CEO 两图：WT「无法加载设置」+「Start-Sleep 参数 2147483647 超范围」）·根因两处=①配方写了不存在的枚举 useExistingQuiet（WT 只认 useNew|useAnyExisting|useExisting）→Terminal 每次启动整份 settings.json 判废、全部配置失效（10-17 起潜伏 7 天无人发现=改完不做启动验证）；②keeper 标签 Start-Sleep -Seconds 2147483647 越 int32 上限（max 2147483）→keeper 秒死、错误窗甩到桌面。当窗执法=settings 改 useExisting（备份 .bak-20261024-useexistingquiet）+5 份 wt-park 副本统一改 while($true){Start-Sleep -Seconds 2147483}+自检器 Tools/fleet-silence-guard.ps1 在役（校验枚举值域+全副本 sleep 上限，exit 1 即违例）·当班窗=bm-c 交互窗自记自承
- 自检: `powershell -File Tools\fleet-silence-guard.ps1`（0=PASS）

### PR-20261017-03 执行落地差
- 来源: CEO 本令 2026-10-17 09:5x「落地一塌糊涂，主要问题一直再犯」+10-16 元批评令「写得科学做得稀烂」
- 复发史·根因: 四连复发（部署=点火律 C-20261016-02 Cure-9 所治族）·根因=已立法≠已执行的口径漂移·收口无三件套
- 出生地闸: 呈报/收口环节缺点火证据+注销清单（十环节表 #5→#6）
- 验证证据: 三件套闭环律 10-16 已立法·本册日审计=首件机械执法·armed 待 10-19 判
- 复发计数: 4
- 状态: armed
- 升格记录: 2026-10-17 立册按二犯档·闭环五件套执法首样本=本案 P1-P11

### PR-20261017-04 规则通胀
- 来源: C-20261001-02 规则通胀与产出不足案（CEO「立了一大堆规则和机制，产出却很少」）+修法优先律法熵账
- 复发史·根因: 反复（10-01 立预算帽后 10-16 修法包仍录孤儿法 6 件）·根因=立法快于收编·只加不减
- 出生地闸: 立法环节缺瘦身对冲（十环节表 #6·法熵账必附）
- 验证证据: 本批 +1 律 −5 集合·季度瘦身日首跑 2026-10-19（法册 §七）
- 复发计数: 1
- 状态: armed
- 升格记录: 2026-10-17 首录·候池首跑后复核

### PR-20261017-05 推送竞态互吞
- 来源: C-20261016-04 双 commit 事故（本窗 commit 与兄弟窗 pull --rebase 重放产孪生 321b32a）
- 复发史·根因: 首录在案（多窗共享索引/推送竞态族·坑录 09-25/10-07 多窗实录）·根因=推前不核远端尖+共享暂存面
- 出生地闸: 上链环节缺「推前 fetch 核尖+暂存面核对+pathspec 定向提交」三连件（十环节表 #6）
- 验证证据: C-04 双签核验法在案（twin 落地不重推·ff-only 收敛）·本案开案前扫 origin 已执法
- 复发计数: 1
- 状态: armed
- 升格记录: 2026-10-17 首录·与 PR-11 联动双查

### PR-20261017-06 CEO 物理件积压
- 来源: S4U 存量 ~95 件+6 游戏真包（微信/抖音开发者登录+AppID+主体认证 23+ 天）+bm-d 入网+商户号/平台账号
- 复发史·根因: 首录（积压面常设）·根因=物理动作无代持可能·呈报后无状态件跟踪
- 出生地闸: CEO 物理件环节（十环节表 #10）·DEADLINES waiting-CEO 区+状态件呈报零催办
- 验证证据: orders 零催办行+提权窗授权 @bm-a（首批回执 ≤48h·≤10-23 状态呈报）在案
- 复发计数: 1
- 状态: open-CEO
- 升格记录: 2026-10-17 首录·零催办·状态件呈报制执法

### PR-20261017-07 会话死=泵停
- 来源: 10-11 斥责令族（「会话死=泵停」结构缺口上会）+bm-b IterationLoop 心跳冻结 53.5h（orders 00:5x E1 行）
- 复发史·根因: 两现（10-11 本会话停摆 36h→cloudF 42 单积压+10-17 bm-b 53.5h 冻结）·根因=长跑批随会话死·无守护兜底
- 出生地闸: 执行环节长跑批缺 pythonw 常驻+监护哨常设（十环节表 #3）
- 验证证据: pythonw+双 redirect 正法 10-11 在册·bmc-ollama-backstop 已立·bm-b 侧待复活部署
- 复发计数: 2
- 状态: open
- 升格记录: 2026-10-17 首录·10-19 窗查守护落地面

### PR-20261017-08 质量闸失效
- 来源: CEO 道具令 10-11（「不要出现这么掉氛围的东西」=帧级 QC 四位检查单全没拦）·指针=QC-MASTER-CHECKLIST 问题面
- 复发史·根因: 复发族（QC 只查当件不查族史·闸在纸不在跑）·根因=无机械点火·检查单人工执行漂移
- 出生地闸: QC 环节（十环节表 #4）·检查单→lint→脚本断言升格路径缺执法
- 验证证据: 四闸（道具/调色/服装/歌词意象）已立+本册日审计=闸升格首件机械模板
- 复发计数: 1
- 状态: armed
- 升格记录: 2026-10-17 首录·周对账抽 QC 族史查重扩面

### PR-20261017-09 同步滞后
- 来源: C-20261001-01 机队信息同步治理案（CEO「机队之间的信息同步很不及时」）
- 复发史·根因: 复发（10-01 六决议后 10-16 仍录登记簿账本缺 12 批/总图缺 4 机制）·根因=发射台账/收割闭环节律不稳
- 出生地闸: 上链/记忆环节（十环节表 #6→#9）·态翻面 SLA 工作窗 ≤2h 执法漂移
- 验证证据: agent-library-sync 10-17 跑批 24/24 unchanged 在案·观察轮 :44 扫回执在役
- 复发计数: 1
- 状态: armed
- 升格记录: 2026-10-17 首录·10-19 判据回访与 C-01 族同窗

### PR-20261017-10 认知滞后
- 来源: 根记忆坑录族复发再犯史+CEO 元批评族「主要问题一直再犯」
- 复发史·根因: 复发族（判例只治已见型·新变体绕闸：10-07 共享索引「被 add 覆盖」型=09-27 暂存面核对律防不住）·根因=会话压缩丢认知·判例无机械消费面
- 出生地闸: 记忆环节（十环节表 #9）·接手窗必读+新鲜度核验缺执法
- 验证证据: 坑录正典化链（判例→法条→出生地闸字段）·本册=认知消费首件
- 复发计数: 1
- 状态: open
- 升格记录: 2026-10-17 首录·10-19 窗抽读核验

### PR-20261017-11 同令多窗重复
- 来源: C-20261016-04 同令双 commit（兄弟窗 pull --rebase 重放产孪生）+坑录 09-27「同令双窗作业先查并行窗」
- 复发史·根因: 首录（同令双窗重复开工族）·根因=开案/接令前不扫 origin+不查 orders 台账并行窗
- 出生地闸: 令接收环节（十环节表 #1）·查重先行=开案前扫 origin/council/decisions 三面
- 验证证据: 本案开案前扫 origin+council 无 C-20261017-*+orders 无追溯令行=查重先行执法首例
- 复发计数: 1
- 状态: armed
- 升格记录: 2026-10-17 首录·与 PR-05 联动

### PR-20261017-12 线级环节梳理未做
- 来源: CEO 本令 2026-10-17 10:0x「梳理每个环节，每个环节都要高效科学合理，一个一个的列计划 直达全完成」·六线现无环节附卷
- 复发史·根因: 首录（C-20261016-04 流程全量梳理只到集团层·未落线级）·根因=集团层与产线层断链
- 出生地闸: 令接收→派单环节（十环节表 #1→#2）·六线附卷缺位
- 验证证据: 本案 §3 六线派单+10-19 委员会窗收卷判据（案 §6）=首个死线跟踪件
- 复发计数: 1
- 状态: open
- 升格记录: 2026-10-17 首录·10-19 窗收卷判·缺卷=点名线主管窗

### PR-20261017-13 export 续鲜断链（BigLife 产线）
- 来源: R1481/R1503/R1507/R1509 四连（轮实录宣称「export 续鲜/全批推送」但 commit 面无件·git show 实证）
- 复发史·根因: 四连·根因=轮实录「先宣称后执行」时序+轮被切断在 commit 前（ledger 先写后执）
- 出生地闸: 呈报环节（十环节表 #5）缺「宣称 ← 证据」执行序
- 验证证据: R1506 通用工具 update_status_export v1.0 resumable（断链段自动补位+--dry-run 账平+round-trip 断言）+R1508/R1510 补账实证
- 复发计数: 4
- 状态: armed
- 升格记录: 2026-10-17 城市线附卷立册按二犯档·观察窗=两审计周期零断链（归族注记：水位漏账 R1477→R1503 并入 PR-03 族）

### PR-20261017-14 前台批取消-续跑双环（BigLife 产线）
- 来源: R1481（前台 5min 取消后 detached 续跑落 7 环→重跑同席产七卡双同日环·外科修复 7c10e956）+R1482（第二实证·查进程树后未盲重跑=幸零伤）
- 复发史·根因: 2 连·根因=「取消≠进程死亡」认知缺位+重跑抢跑（批 self-commit 制下重选同 10 席）
- 出生地闸: 执行环节（十环节表 #3）长跑批点火缺后台化范式
- 验证证据: R1506 起后台化点火范式（Start-Process detached+日志重定向+-u）11+ 轮零复发+取消-续跑判例固化（查进程树再定）
- 复发计数: 2
- 状态: armed
- 升格记录: 2026-10-17 城市线附卷立册按二犯档·观察窗=两审计周期零双环（归族注记：年轮逐字重复 T-20261011-01/meet 闸陈旧出口 T-20261015-01 并入 PR-08 族）

### PR-20261026-01 机器心跳 GPU 字段失真与键爆炸（bm-c / bm-a）
- 来源: 2026-10-26 07:4x 调度席实测（BOARD-20261026 勘误）+ O-20261026-0735/0810 心电面
- 复发史·根因: 连续多班（10-19 起同族登记）·根因=心跳写手把同一事实写成 20+ 个近义键（gpu_free_vram_mb/gpu_idle_vram_mib/gpu_used_mib…），且采样口径不一：bm-c 07:45:44 写入 gpu_face = nvidia-smi 1% / 2044 MiB，同刻 nvidia-smi 实测 100% / 14912 MiB；bm-a.json last_seen 停在 10-24 08:14（机器 tailscale active）
- 出生地闸: 心跳写手（fleet-oversight.ps1 采集 + fleet-audit.ps1 读面）缺「单一真值键 + 采样时刻自证」
- 验证证据: 本窗实测 nvidia-smi 与心跳文件对读不一致；调度判活只能退化为看产物节拍（lookdev 45-50s/张）
- 复发计数: 3
- 状态: open
- 升格记录: 2026-10-26 立册（调度席）；修法候选=只保留 gpu.util_pct/vram_used_mb/vram_total_mb 三键+ts+source，写后回读断言

### PR-20261027-14 STARVED-EXEC 假红旗（pausedLite 让路窗）
- 来源: R2.36 事件班 2026-10-27 16:30/16:31 双触发（lane=bm-a open_cards=2 blocked=2）
- 复发史·根因: 首录（同族=旗面不读 idle verdict）·根因=Tools/fleet-dispatcher.ps1 的 STARVED-EXEC 判据只看 exec 计数，不读 idle-watch verdict；对 bm-a 的 EXPECTED-IDLE-WORKHOURS（CEO 10-15 AutoYield 工作日让路律，pausedLite 09:00-19:00）仍按 P1 supply failure 报旗→每日约 10h 持续假红旗，稀释真红旗信噪比
- 出生地闸: 旗面生成环节·修法=`if ($verdicts[$lane] -eq 'EXPECTED-IDLE-WORKHOURS') { 记 PAUSED-BY-POLICY 不计旗 }`
- 阻塞: fleet-dispatcher.ps1 ∈ BLUEPRINT §九 受保护件（Tools 核心四件）→改动须 CEO 令/群审通道，本席不擅改
- 复发 2026-11-06 02:1x（事件班）：同族换根——exec 判据读 POOL.json（停更 6 天，仅 1 open 且 blocked_by=CEO-PHYSICAL），真实供给在 PRODUCTION-QUEUE（open=25/run=4）+三机 lanes 均在执；同一脚本内 STARVED-EXEC 与 SUPPLY-DRY 读不同面→自相矛盾，每 10min 全三车道刷假 P1。修法同族（判据换供给面或停用 POOL 面）仍需受保护件通道。
- 验证证据: 本班实测 idle state.json verdicts.bm-a=EXPECTED-IDLE-WORKHOURS（16:39:29）+ .codely-cli/machine-state.flag=pausedLite 2026-10-27T09:00 + a.json gpu util 99%（机器在人用）
- 复发计数: 2
- 状态: open
- 升格记录: 2026-10-27 首录（R2.36 事件班）·候选修法入 DEADLINES waiting-CEO 受保护件通道

### PR-20261027-15 POOL 阻断源不随签发清除（P1 卡停滞 7 日）
- 来源: R2.36 事件班实测——POOL-0022 blocked_by=director-signoff:L2-FIX，而签发件 2026-10-20 12:4x 已落盘
- 复发史·根因: 首录·根因=POOL 卡的 blocked_by 由开卡方写入，签发方落地后无人回写清除；dispatcher 每轮把陈旧 blocker 当真实依赖计入 blocked，supply 看着有卡却零可执行，与实际产能脱节
- 出生地闸: 签发/回执落地环节·修法候选=签发件落盘时同步回写卡 blocked_by（POOL 五态迁移的核销双勾欠缺）
- 验证证据: PROMPT-GATE-可爱女人-KF-PACK-A-v1-SIGN.md（2026-10-20 12:4x·判定准烧 28 帧）+ orders 10-20 15:28 行 + 本班实测 bmc/ 与 media/ 零可爱女人 KF 件=7 日真停滞
- 复发计数: 1
- 状态: open
- 升格记录: 2026-10-27 首录（R2.36 事件班）·候选修法=P-/D- 台账入队（受保护件外的流程面）

### PR-20261027-16 bm-c 驻卡 LLM 占满生成视觉道（P1 产能冲突）
- 来源: R2.36 事件班 17:04:30 实测（TCP /status 直读，非心跳文件）
- 复发史·根因: 同族已登记（10-17 三维资源盘点「27b 驻卡 free 918MB」、10-21 bm-a 角色清理「常驻 LLM 驻卡堵生成道」）·根因=驻卡 LLM 与生成视觉道共用同一张 16GB 卡，停卡动作需本机会话执行且无持久守门（重启/自愈即复占）
- 出生地闸: 车道分配/驻卡守护环节·既有法条已明（常驻 LLM 驻卡堵生成道 → ollama stop + pin 任务 disable，整卡还生成线），缺的是「生成道有待烧 P1 卡时自动让卡」的判据
- 验证证据: 17:04:30 /status ram_free_gb=0.5 / cpu_load_pct=82 / gpu=RTX3070 14884MiB（16GB 卡余 ~1.4GB）；对照 14:59 c.json vram_free=15095 = 陈旧假象；后果=POOL-0022（CEO O-20261020-1124 P1）清障后仍点不着火
- 复发计数: 3
- 状态: open
- 升格记录: 2026-10-27 首录（R2.36 事件班）·候选修法=生成道有待烧 P1 卡时置让卡标志、驻卡守护读标志即停（受保护件外流程面，需 bm-c 本机执行通道；24h 无 KF 产出升 E1）


### PR-20261103-01 队列逾期件无机械可见面（CC-2·D-20261101-11 入册）
- 来源: FluxVerse F-20261101-01 附卷候选 CC-2（r743 11-01 00:51）；集团侧实锚=FluxVerse `state/queue/main.md` #8 逾期 13 天、#23 逾期 5 天才被下一轮捡到
- 复发史·根因: 队列件的逾期只在人工翻 `state/queue/main.md` 时可见，tick 面不打印逾期天数；集团各司 tick 报告普遍只有「有活/无活」二态，无「逾期 N 天」字段 → 结构等待与真停摆在报表上同形
- 出生地闸: 队列/回执写入与轮报生成环节——轮报必须带 `overdue=n`）与逾期件 top3 名单（owner+逾期天数），无该字段的轮报不得称健康
- 验证证据: 11-01 附卷 §四 CC-2 条 + `gaming/FluxVerse/state/queue/main.md` 实读；本班未见任何司轮报含 overdue 字段（UNVERIFIED：未做全司轮报普查，仅按已读轮报判）
- 复发计数: 1
- 状态: open
- 升格记录: 2026-11-03 首录（第 39 批·D-20261101-11 承诺 11-03 00:00 逾期后由 @HQ 本班补录）

### PR-20261103-02 城建侧问题未进正身（CC-3·PR-12 变体）
- 来源: FluxVerse F-20261101-01 附卷候选 CC-3；`gaming/FluxVerse/docs/city-problem-registry-annex.md` 12,132B（11-01 00:33）
- 复发史·根因: 城建侧问题只写在 FluxVerse 自家 `TECH.md` §九与附卷，集团 `cph4/fleet/PROBLEM-REGISTRY.md` 中城建条目 **0 条**（census 直数 `entries=18 city=0`）；司际可见性断在「谁写正身」——各司只写自家 TECH，正身无人收
- 出生地闸: 问题首录环节——凡跨司可见的 P1/P2 问题，首录时必须同时落正身一行（六字段），否则附卷不算入册
- 验证证据: census 直数行 `entries=18 city=0 open=7 armed=10 closed=0 max_recur=7 field_gaps=0`（11-01 实跑·r743）+ 本班 PROBLEM-REGISTRY.md mtime 10-29 2:55（未变更）
- 复发计数: 1
- 状态: open
- 升格记录: 2026-11-03 首录（第 39 批·同 PR-20261103-01 补录）
### PR-20261105-01 ????????????????? + ?????P1?
- ??: 2026-11-05 03:26-03:47 CEO-PROXY ????DL ?? STARVED-EXEC / BLOCKED-RAM / CLOCK-SKEW?01:01?03:44 ? 10min ???
- ??????: STARVED-EXEC ???? 9 ????R4-2/R7-1/R8-2/R9-3 ???????????????? POOL.json?????????????=**?????????**?`CLOCK-SKEW max=3910.5ms precision=+/-436.3ms` ?????? ? 90min ??????????????=???? 30 ? OPEN?4 ? RUNNING ?????40min ?????????01:40/02:11/03:26??????????????????
- ????: ????????????+ ?????????????????????`fleet-dispatcher.ps1` ? open/exec ?? `PRODUCTION-QUEUE.jsonl`????????????`proxy-event-carrier.ps1` ?????????**???? BLUEPRINT ?? ?????Tools ???? / L0 ??????????**
- ????: 03:26 ?? `queue_integrity VERDICT=GREEN`?496 ?/0 dup??`git show origin/main:PRODUCTION-QUEUE.jsonl` OPEN 30 / RUNNING 4?owners bm-a/bm-b/bm-c/bm-m??`POOL.json` ?? open=POOL-0010 blocked_by `CEO-PHYSICAL:submit-materials`?`proxy-event-carrier.ps1` L84 `$sig = ((($flags | Sort-Object -Unique) -join ' || ') -replace '"','')`?DUMP=01:40/02:11/03:26 ????? LOG ?
- ????: 5?????????????????????????????? DEADLINES ???
- ??: open
- ????: 2026-11-05 ???R10 ??????????=?????????????+??????????????=CEO ?????? L0 ????????????????

### PR-20261106-01 偏好回落 + 机器绝对路径 = 首跑必死（rc=127）
- 来源: 2026-11-06 02:05 事件班实测 Q-VCORP-PREP-z02-R4（bm-a rc=127 CWD-MISSING；02:06 z03 同形被领）
- 复发史·根因: 同族=2026-11-03 implicit_inputs/E-INPUT 案（卡未声明真实输入，落到没有数据的机器）。新面=卡同时写了「nodes=[bm-b] 偏好」与「C:/Fluxgroup/FleetAgent 绝对路径/cwd」，choose_lane 按 2026-11-02 设计把 nodes 当偏好而非过滤，bm-b 忙即回落 bm-a，路径与输入都不存在→确定性 rc=127，一次 16 张卡全废而账面像「机器懒」
- 出生地闸: 开卡环节（卡作者）——凡 cmd/cwd/requires/when_all 出现非本机绝对路径或依赖某机私有目录，必须同时写 hard_nodes（硬钉）或改仓内相对路径；建议 Tools/card-lint.py 增断言：绝对盘符路径 + 无 hard_nodes = 打回
- 验证证据: cph4/fleet/queue-receipts/Q-VCORP-PREP-z02-R4-20261105-bm-a.json（rc=127，card_defect=CWD-MISSING 且点名 C:/Fluxgroup/FleetAgent）+ lanes/bm-a.json 02:06:02 job=z03 + 队列原行 nodes=[bm-b] cwd=C:/Fluxgroup/FleetAgent
- 复发计数: 1
- 状态: open（当窗已修 42 行：相对路径+hard_nodes；卡作者侧闸待立）
- 升格记录: 2026-11-06 首录（事件班）·当窗直修台账；出生地闸候选入 card-lint

### PR-20261106-02 OS 硬约束只在显式 node_os 时生效（空领一轮）
- 来源: 2026-11-06 02:05:40 事件班实测 bm-b last_result state=OS-MISMATCH（DOCS-* 卡，cmd 用 python3，nodes=[bm-m]）
- 复发史·根因: fleet_lane.infer_node_os 已能从 python3/盘符推断 OS，card_os_ok 也已实现，但 master_agent.choose_lane 只在 job.node_os 显式存在时才过滤候选→未显式写 node_os 的 OS 绑定卡仍会被派到反 OS 机器，靠 lane_agent 事后拒收（白占一个租约轮次）；同族已见 2026-11-03 CHK-RECEIPT 落 bm-b rc=9009
- 出生地闸: 派单环节·修法=candidates 无条件过 fl.card_os_ok(job, n)（infer 已含「空=不限」语义）
- 验证证据: MASTER-STATE.json lanes.bm-b.last_result={state: OS-MISMATCH, reason: "dispatched job requires a different OS", ts: 2026-11-06T02:05:40}；队列 DOCS 两行 node_os 原本缺失（已补 macos）
- 复发计数: 1
- 状态: open（卡侧已补 node_os+hard_nodes；派单侧代码改动候裁）
- 升格记录: 2026-11-06 首录（事件班）·修法一行，候受保护件通道

