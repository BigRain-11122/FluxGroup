# 集团全面短板盘点（Group Gap Audit）· 2026-09-26

> 触发：CEO 令 2026-09-26 上午「全面调研，目前城市，集团，各子公司，实验室等，还有什么短板需要改进。」
> 方法：5 路并行只读深调研（MiniGame 产线 / BigMoney+机队 / 城市生命面 BigLife×FluxVerse / HQ+CPH4+BigDomain+BigCompute / BigStream 活性专查）+ 台账实读（patrol-ledger 15 项·liveness·tick/mode ledger·cloudF 队列·orders.md·state-c）。全部证据指针在案。
> 消费面：周一 09:23 巡检班（09-28）应将本报告 §二/§三 新发现转为 PT 行；已挂 PT 的项按既有 PT 闭环。

## 一、总判

**机制面健康（tick 自转全绿、8 工程仓 48h 内全有提交、心跳链在修在通），但存在 4 个 P0 级断点：单机执行体瘫痪、一家回执通道断链、三件研究令零开工、生成腿挂账滞涨。** 令流（P-号）派发面通畅，回执与执行面出现结构性缺口——「令出了≠闭环了」。

## 二、P0 短板（24h 内须动）

| # | 短板 | 证据 | 建议动作 |
|---|---|---|---|
| P0-1 | **bm-c 执行体全瘫 36h+**：K:\金钱牛马\BigMoney 目录不存在→三 OS 任务僵尸（result 2147942667×3）→心跳死 2026-09-24 21:51（OFFLINE）。两令未 ack（O-20260925-1153-bm-c=PT-01 整改单本体、O-20260925-2313-bm-c=C 臂派单）。拖累链：P-49 装机/14b/bge-m3 本地推理线断、fleet 任务认领制停摆、13.4GB 显存闲置、扩容判据 A 永不可测。**PT-01 大限=今日 11:52，未收口即 ESCALATED** | list K:\ 无此目录；fleet/machines/bm-c.json；patrol-ledger PT-01 五班复验 | bm-c GM 专管会话为唯一物理执行腿（跨机目录 C 机无法代建）；逾期升级直呈 CEO+fleet/inbox MSG 催办；同时按 PT-01 两路裁决（重建 or 转 Biggame 纯机）尽快拍板止损 |
| P0-2 | **Biggame(MiniGame) HQ 回执/消化通道结构性缺位**：P-79 桌面分发/P-81 回测池接入/P-20260925-01② ComfyUI 补装均零回执，值守轮连续 3-4 班点名，P-79 快速件 24h 窗已破；08 号循环实活但 HQ 台账面零消化=令流闭环最重断点 | evolution-ledger 值守轮 09-25 双报；git log grep P-79/P-81 零命中 | MiniGame 侧建「HQ 令回执步」入 tick 收口段（M1 Step0 或 M6）；积压三单本批补回执 |
| P0-3 | **P-2026-09-25-07/08/09 三件 72h 研究令零开工（到期≈09-28）**：四级条线 gap 分析、机队算力盘点+大模型适配矩阵、token 消耗盘点——cph4/research/ 零产出；《四级条线治理章程》草案未立档。@CPH4 无 OS 循环，消费依赖决策轮/值守轮点名 | cph4/research/ 目录全清单（最新=09-25 23:08）；orders.md 三行 dispatched 态 | 今夜 00:00 决策轮把三件列为最高优先拟案；值守轮点名；如 09-28 仍零产出=升级 CEO（实验室吞吐瓶颈实锤） |
| P0-4 | **云端生成腿挂账滞涨（58 单→本会话已开泄）**：cloudF 58 单 pending（G17=37/G12=5/G09=4/G04=4/G08=4/G03=2/G10=2），08:05 满槽 one-shot cron 因 CLI 未在跑永失触发=C1166 定谳「随下个健康交互会话点火」。**机制缺陷：one-shot session/durable cron 依赖 CLI 存活，错窗即永失** | cloudF-queue-c.jsonl 58 pending 实测；C1166 ledger 行 | 本会话已接管：波次1（10 单）+波次2（10 单）已云射；建议满槽窗 cron 改「recurring 每 10min+队列空自停」模式或 OS 任务面化，消除 one-shot 永失缺陷 |

## 三、P1 短板（72h-7d 窗）

1. **liveness 今晨 RED·bigstream 假 NO_TS 连告 15 条**：根因定谳=PT-07 读侧未修（fleet-audit Source 3 从未消费 state.ts/task 新字段）×本地克隆滞后 origin 13.9h×origin state.json 仍无 ts 字段×probe-heartbeat.txt 缺失。→ **本会话已修 fleet-audit Source 3（freshest-wins 接 ts/task，三处），语法 0 错**；写手侧/克隆跟进面仍需 BigStream 与读链收敛。
2. **城市生命面上半段真空（P-15 五层梯）**：L4 意义层/L5 城市响应层零专件零引擎（FluxVerse 09-25 r143-r152 全为视觉/光层）；**跨司断链**=BigLife citizen-behavior 导出面齐备（v1.4 needs/behavior/atlas/light 10003 行）而 FluxVerse 仅 r143「勘定」无消费回执（T-20260923-01 open）；agency 自主性=升维批自认最大缺口（Phase2 未开工）；O-1940 四组部门建行零组织节落行；kokoro 多声源挂账。
3. **本地资源闸双拦**：RAM 14-20%<25% 四连拦（G12 S4-T003 三波、灰盒 fire 窗、GPU 草稿车道全关）+VRAM 曾余 1.5G（14b 常驻挤占）。三档运维律泄压阀无自动执法（本会话手工 ollama stop 14b 才开 8.4G）。→ 建议：U214 矩阵「泄压阀」写入 worker 前置步（rmbg 批前自动 stop 14b+置阀+批毕删阀）。
4. **G10 产线三病**：draft 二批 15/16「workflow execution error」未复盘（09-25 23:07-23:13）；state-c G10_CrazyStocks 键值为字符串=疑 state 写入事故（数据诚实裂缝）；stock_audio r6 6.8+eventcard_frame r4 6.6 两件 advisory-held 待 CEO 降档裁决（驻盘隔离子）。
5. **G02 lifecycle 待审未翻（09-19 OK 线后 7 天）+上线链物理件 X001a-X004 8 天未动+U153 深度墙**：上线闭环从未转第一圈（8 款在途 0 上线）。物理件豁免（CEO 本人），但「待审态」属 AI 侧可推进项——建议 M5/决策轮专列 G02 lifecycle 审结动作。
6. **巡检/监控仪器自身欠账**：PT-15 patrol-runner stamp 闸 PS5.1 算术不兼容自 v1.0 从未生效（→ **本会话已修：双 DateTimeOffset+catch 诊断行，语法 0 错**）；PT-06 task-health result 码盲区（僵尸任务恒 OK）未修；PT-14 台账并发撞号+orders.md L201/L205 重复行；PT-11 charter MiniGame intake 路径断链隐患；PT-03/04/09 OPEN；PT-12 ①②待 B 机（idle 段 pulse 微提交律未实证）。
7. **P-05 总动员 24h 资源清单回执仅 BigDomain 一家交付**（其余六实体未见证据）；P-12 三司 canonical 任务板 72h 窗（09-28 到期）：FluxVerse/BigMoney/BigStream 未建板=「活可能在干但不可审计态」。
8. **web_search 通道 410 亡故（M2 雷达喂源降级）**：新种子喂源断供，FE-20260925-C-14 在册未修；M6 连续轻轮零新动作部分源于此。
9. **bm-a 本地编码试点中期风险**：B 臂 2/10 FAIL 定谳（盲评 5.775 vs 云端 8.875·非劣 -3.10）；C 臂刚起步（1/10 done·09:26 起）；C 产物盲评+14b 辅助面空缺；10-09 中期判读样本量风险。
10. **治理债**：对标改进总账落地率 1/36（P1 四件锚 09-30 U178 首跑）；M5 gate_authenticity=0.75；本地 LLM Phase1（09-28 全机 serve 常驻化）BG-A/BG-B/bm-b/bigstream 四机未部署，距期 2 天。

## 四、P2 短板（7d 窗）

11. BigDomain/BigCompute 司级 orders 台账极薄（1 stub/1 件）、backlog 未饱和——「待机司」合规但自主业务条线稀薄。
12. BigStream 业务面：M5 账号物理件阻塞全量产（F-001~013 成品未上线）；BS-001 B 站件 spec 门 FAIL 长期在案；BS-005 视频号双件判弃（blocked 预期红）；同音噪声率 14-16% 高位（whisper 通道退化未收敛）。
13. fleet-allocations 未反映 09-25/26 实况（bm-c GPU 读数矛盾 3070/16GB vs 心跳 12.9GB）；P-08 适配矩阵空缺（挂 C 臂收口后回填）。
14. MiniGame 队列尾账：G13 g13_eventcard/panel 9×9px stub（Listing 级阻塞·SLA 10-02）；P01-P08 美术白底疑似 30 件（SLA 10-02）；G09「盲评≠alpha 律」回读门待处置。
15. HQ 树漂移未收口（PT-04）：mcpServers 分发面 settings.json×2+CODELY.md×2 未提交+patrol/ 追踪策略未定。
16. bm-c GPU 型号读数矛盾待其机队协议补报（P-33 心跳数据债延续）。

## 五、本会话当场整改（executed）

1. **cloudF 挂账开泄**：波次1=10 单全链完成（G17 重制 8 张云射+raw 落盘+队列 done(url) 翻格；G03 音频 2 件云射+raw+双遍 loudnorm mp3 母带+落 MergeMania Assets\_Game\Audio\BGM|SFX——-16LUFS/TP-3/mono 128k，实测 bgm i=-17.34/tp=-3.22、sting i=-15.26/tp=-3.33，TP 全绿、积分响度因 crest 限制欠 0.7-1.3LU 如实记档交 AudioGateCheck 终验）；8 张已投 draft-queue rmbg（显式 pending 坑 206 律）。波次2=9 单在飞（G12 场景三件不透明单+G10 品牌图撞并发上限候槽+G09 取证重制四件+G12 狗态重制两件），G10-A35 槽位释放即补发。
2. **rmbg 泄压阀执法**：14b 让路（ollama stop→VRAM 1.5G→8.4G）后撤阀防 PAUSE_VALVE_LEAK；rmbg 8+6 行持久排队，等 batchmode 让路健康窗（Tuanjie Hub=8 GUI 常驻=设计内安全闸，非故障）。
3. **PT-07 修复**：fleet-audit.ps1 Source 3 三处接 state.ts/task（freshest-wins），语法 0 错，watch 已点火重评。
4. **PT-15 修复**：patrol-runner.ps1 stamp 龄算术改双 DateTimeOffset+空 catch 改诊断行，语法 0 错（闸自 v1.0 首次生效）。
5. 满槽窗机制缺陷（one-shot 永失）已在本报告 P0-4 立案，续发窗重排为 durable。

## 六、建议路由（全部映射既有机制·零新车道）

- **bm-c 面**：PT-01 逾期升级（今日 11:52 后 ESCALATED）+fleet/inbox MSG 催办——BigMoney 值守轮/夜轮消费。
- **CPH4 三研究件**：今夜 00:00 决策轮最高优先拟案——决策轮消费。
- **Biggame 回执通道**：P0-2 三单补回执+M1/M6 tick 加回执步——MiniGame tick 线消费。
- **城市 L4/L5+跨司管线**：P-15 研究件窗（10-02）内 BigLife↔FluxVerse 管线扩展工作单+L4/L5 立项提案进 CPH4 进化轮——城市三部曲链消费。
- **G10 三病/G02 lifecycle/对标总账 09-30 窗/M5 gate_authenticity**：MiniGame 既有单据面（FE 队列/任务板）消费。
- **PT-06/03/04/09/11/12/14**：下轮 patrol 班核验+行级收口——巡检线消费。
- **本报告**：09-28（周一）09:23 巡检班首查件——新发现转 PT 行，已修两项（PT-07/15）转 VERIFIED 候选。

## 七、复查判据（下周一巡检对账）

1. PT-01 状态（ESCALATED/收口）；2. bigstream liveness flag（NO_TS→ONLINE/LATE）；3. CPH4 三研究件存在性；4. cloudF pending 计数（应 ≤38 且递减）；5. P-79/P-81/ComfyUI 回执；6. 三司任务板存在性；7. G10 state-c 键结构修复；8. G02 lifecycle 状态；9. 对标总账落地率（09-30 首窗）；10. 本地 LLM Phase1 四机部署态。
