
- [2026-10-23 12:32:31] CEO 再校正「数值不要从头造轮子，我真的很烦你们这一点」：竞品数值一律取原表/原值，禁自己拍数值再当结论；工具也只用现成轮子（Il2CppDumper/Cpp2IL/ILSpy/Capstone/ghidra），不得自造解码器后再反复打磨。拿不到原表就明说卡点类别，不拿标定值充数。

- [2026-10-23 23:29:08] CEO 纠正 UI 资产做法：必须先出整屏全图（含界面/HUD/按钮一起构图），再原位拆层，禁一件件单独生成按钮/面板。业界通行流程=style lock→整屏 mockup→原位拆 buttons/panels/icons（保持相对位置与尺寸）→透明 PNG→引擎，4-8 层为宜。单独生成的单件只作风格参考。

- [2026-10-27 11:02:33] CEO 追问「你一天一夜都干了啥」的教训：**补闸/复核/写报告不算产出**。接到返工，先用一个时间盒（≤半天）把「能看的下一版」做出来，闸只做必过项（稳定性/帧数/码率/转场 OPPOSE），不要在工具完美上纠缠；每半天必须有可见产物或明确卡点，绝不拿过程当进度。

- [2026-11-02 15:17:19] CEO 展示格式令（2026-11-02：「以后就思维导图吧」）：结构与汇报**默认用思维导图（树状缩进）**，一节点一句；确需数字对比时才补一张格表；不写长段落、不写小标题套话，一屏看懂为准。

- [2026-11-03 11:22:06] [2026-11-03] CEO 令「不要婉转的和我说话，直接给最科学的结论，然后我判断如何执行」：所有向 CEO 的输出=结论先行、单一判断、不写「我建议/我倾向/可能/要不要」这类缓冲词；不确定就写明不确定在哪一条证据上，不写套话式两面话。分歧只给一个最优解+它的失效条件，备选只在 CEO 主动追问时给。Why=他要做的是执行判断，缓冲词让判断变慢；此前多次出现「我倾向A但也可能B」被他要求改正。How=每次汇报自检：删掉所有软性措辞后句子是否仍成立，成立才发。

- [2026-11-02 16:51:48] 本地大模型实测定位（2026-11-02）：常驻 qwen3:4b-instruct（3.3GB/100%GPU/8K）。真有用=①每日 DIGEST 摘要（事实级，例「79 份回执、队列 2 件、小钢炮无执行回执」）②社媒拦话（5 条全判不能代答：AI 身份问题、编造创作者经历被硬闸否决）③判定席初筛 16 条归因（半数是模板话）。没用=①brain_service 写「副大脑产出」但 brain 目录零文件，每 4 分钟空转 ②曾给 Windows 机器建议 `sysctl -p` 的幻觉导致返工。结论：它是过滤器/门卫，不是生产力；不得用它写代码、给运维命令、做事实判断。

- [2026-11-03 11:57:57] [2026-11-03] Agent Skills 外部实证台账（2026-11 调研·做技能库决策前先读这份，不要重复调研）：①规范=SKILL.md 只强制 name+description，正文建议 ≤500 行、大材料拆子文件（anthropics/skills + Microsoft Learn agent/skills）。②发现成本实测中位 ≈80 token/技能（官方 17 件：最省 webapp-testing 55、最贵 xlsx 235；全挂 ≈1700 token）→ 挂牌几十个几乎不占上下文。③数量上限：N≈100 时"全量预加载"在所有 rollout 上崩，渐进披露可省最多 81.7% token（arXiv 2609.35692）。④「相关≠有用」：只靠相关性选技能，真实增益只能用 with/without 成对对照测出来（SkillDelta：相关激活仅比随机高 4.3 分、15/15 胜）。⑤硬顺序规则应下沉到运行时/脚本，比写在提示词里高 16.2 分（HEXIS）。⑥生态：Google 2026-09-28 用 skills 取代 Gemini Gems；微软 Agent Framework 内置 agent/skills（load→read resource→run script）；规范 2025-12 成开放标准，MCP 归 Linux 基金会。⑦安全已成独立学科（NVIDIA SkillSpector / A Trust Pipeline for Agent Skills），与我方 ClawHub 18 件里 8 件带病（44%）一致。

- [2026-09-24 16:13:41] CEO 交付物具体性律（2026-09-24 ~16: → 全文档案: .codely-cli/memory/mem-20260930-g-004.md

- [2026-09-24 19:28:50] 无头 Edge 截图三律（2026-09-24 观测窗批2 机检门实测·验图法配套）： → 全文档案: .codely-cli/memory/mem-20260930-g-005.md

- [2026-09-29 18:04:20] CEO 交付路径可靠律（2026-09-28 CEO 批评「你每次给我的目录都找不到 能不能靠谱点」·U273 审核板呈报实录·**2026-09-29 再犯实录=U310 呈报只 → 全文档案: .codely-cli/memory/mem-20260930-g-006.md

- [2026-09-29 18:39:30] [2026-09-29 18: → 全文档案: .codely-cli/memory/mem-20260930-g-009.md

- [2026-09-30 17:51:38] [2026-09-30 17: → 全文档案: .codely-cli/memory/mem-20260930-g-010.md

- [2026-09-28 11:34:55] FluxVerse 美术库正主路径律（09-28 真图素装配批实证）： → 全文档案: .codely-cli/memory/mem-20260930-g-014.md

- [2026-09-28 14:46:06] FluxVerse TD anime demo v2 技术面（2026-09-28）： → 全文档案: .codely-cli/memory/mem-20260930-g-018.md

- [2026-09-28 18:00:00] OSS 工具链全面安装波终态（2026-09-28·P-2026-09-28-15·本机=bm-a CEO 桌面机）： → 全文档案: .codely-cli/memory/mem-20260930-g-029.md

- [2026-09-28 22:21:10] [2026-09-28 22: → 全文档案: .codely-cli/memory/mem-20260930-g-036.md

- [2026-09-29 11:26:03] [2026-09-28 23: → 全文档案: .codely-cli/memory/mem-20260930-g-040.md

- [2026-09-29 11:26:03] [2026-09-29 11: → 全文档案: .codely-cli/memory/mem-20260930-g-045.md

- [2026-09-29 13:25:48] [2026-09-29 13: → 全文档案: .codely-cli/memory/mem-20260930-g-047.md

- [2026-09-29 14:03:29] [2026-09-29 15: → 全文档案: .codely-cli/memory/mem-20260930-g-049.md

- [2026-09-29 15:29:20] [2026-09-29 15: → 全文档案: .codely-cli/memory/mem-20260930-g-053.md

- [2026-09-29 15:29:27] [2026-09-29 15: → 全文档案: .codely-cli/memory/mem-20260930-g-054.md

- [2026-09-29 16:34:01] [2026-09-29 16: → 全文档案: .codely-cli/memory/mem-20260930-g-055.md

- [2026-09-29 17:39:28] U307 在飞占号→已收口（撞号让路面·2026-09-29）： → 全文档案: .codely-cli/memory/mem-20260930-g-056.md

- [2026-09-29 17:24:07] [2026-09-29 17: → 全文档案: .codely-cli/memory/mem-20260930-g-058.md

- [2026-09-29 17:34:11] [2026-09-29 18: → 全文档案: .codely-cli/memory/mem-20260930-g-059.md

- [2026-09-29 17:59:27] [2026-09-29 18: → 全文档案: .codely-cli/memory/mem-20260930-g-061.md

- [2026-09-29 18:02:18] [2026-09-29 18: → 全文档案: .codely-cli/memory/mem-20260930-g-062.md

- [2026-09-29 18:13:49] [2026-09-29 18: → 全文档案: .codely-cli/memory/mem-20260930-g-063.md

- [2026-09-29 18:21:27] [2026-09-29 18: → 全文档案: .codely-cli/memory/mem-20260930-g-064.md

- [2026-09-29 18:23:38] [2026-09-29 18: → 全文档案: .codely-cli/memory/mem-20260930-g-065.md

- [2026-09-29 18:45:57] [2026-09-29 18:4x] 重构主线 R0 版式定版收口（O-019 R0 行·FluxVerse 97a8f59 已推）： → 全文档案: .codely-cli/memory/mem-20260930-g-067.md

- [2026-09-29 18:53:33] [2026-09-29 18: → 全文档案: .codely-cli/memory/mem-20260930-g-068.md

- [2026-09-29 19:20:34] [2026-09-29 20: → 全文档案: .codely-cli/memory/mem-20260930-g-069.md

- [2026-09-29 19:34:43] [2026-09-29 19:5x] U316 终闸前夜预检收口（判据 9/10 绿·余唯判据 10=明晨 08:53 终闸呈报）： → 全文档案: .codely-cli/memory/mem-20260930-g-070.md

- [2026-09-29 19:51:23] [2026-09-29 20: → 全文档案: .codely-cli/memory/mem-20260930-g-071.md

- [2026-09-30 11:42:02] [2026-09-30 11: → 全文档案: .codely-cli/memory/mem-20260930-g-074.md

- [2026-09-30 13:43:11] [2026-09-30 13: → 全文档案: .codely-cli/memory/mem-20260930-g-081.md

- [2026-09-30 15:13:45] [2026-09-30 15: → 全文档案: .codely-cli/memory/mem-20260930-g-086.md

- [2026-09-30 16:04:14] [2026-09-30 16:0x] O-20260930-1560 CitySim v0.1 功能城市白盒闭环（CEO 令「你自己决定，我只要结果。 → 全文档案: .codely-cli/memory/mem-20260930-g-094.md

- [2026-09-30 16:33:34] [2026-09-30 16:4x] 2D Live v4 批中段工程律三枚（O-2026-0930-002 在飞·B/A 线接力实录）： → 全文档案: .codely-cli/memory/mem-20260930-g-095.md

- [2026-09-30 16:52:32] [2026-09-30 16: → 全文档案: .codely-cli/memory/mem-20260930-g-097.md

- [2026-09-28 15:06:40] TJGenerators 云端资产库（search_asset_lib）实测=纯 3D prefab 内容（Kenney/Kaykit 3D 件），无 2D tileset 瓦片包（2026-09-28 top-down city tileset 检索零命中）；本地美术库（FluxVerse ArtPacks/city-art-pool）=像素包与 SDXL 场景背景池，无日漫 TD 瓦片。结论：2D 日漫瓦片图集走 PIL 自绘（Tools/city/td-tileset.py 25 件 cel 瓦片），个体物件（建筑/树/钟塔）走 seedream is_segmentation 生成后入引擎拼装。

- [2026-11-07 23:53:43] [2026-11-07 23:5x] 台账/工具自造假红四例（已修+断言 RG-24/RG-25）：①launchd PATH 不含 ~/bin，`asset_dataset_audit.ff()` 只查 PATH 且返回裸名 → 有 ffmpeg 被报"没有"；改为解析绝对路径并补 ~/bin 等常见目录。②`vault.py verify` 从未支持 `--json`，VAULT-VERIFY 卡每轮 rc=2 无回执；已加 `--json PATH`（实测 rc=0/651 条）。③`card_contract_check` 把"工具按模板拼文件名"（`triage-%s-%s.md`）的真卡判成 SPEC-IMPOSSIBLE；改为读工具源码字面量通配匹配+负控。④**ARCHIVED 此前不是终态**，旧 claim 可把它写回 RUNNING（mv-gate 实锚空转）；merge_jsonl 现保护 CANCELLED+ARCHIVED，显式 requeued_by 仍可重开。另：master_pulse 现自己剪 stage-last.json 孤儿键（去阶段留残留会让 RG-21 假红）。

- [2026-11-08 00:18:20] [2026-11-08 00:2x] 常驻模型收敛（**supersede 早前「四档常驻 14.6GB」的结论**·CEO「一个模型可以干很多事，不需要常驻这么多」）：审计窗 223 次生成调用=主力 4b-mlx 214 次 / 8B 8 次（集中在 21:17-21:18）/ 1.7B 3 次 → 为 11 次调用占着 ~6.6GB 不划算。现策略：`budget.resident_set=['resident','embedding']`（≈5.5GB），`triage`(1.7B) 与 `big`(8B) 改按需 `keep_alive=0`（矩阵 tiers 同步 resident=false，model_plan 的 E-KEEPALIVE 会抓"非常驻却 keep_alive≠0"）。回滚条件=代码/评审类任务 >20 次/天时把 big 改回 resident。另修三处写死：autowork/social_drafts 写死对照档 `qwen3:4b-instruct`、router 写死 `qwen3.5:4b`（与现役 4b-mlx 是两个模型），都会另拉 4B 顶掉主力，已全部改为读 LOCAL-MODEL-POLICY 单源。**改策略后必须重启主控脉**——脉启动时就把 resident_set 读进内存，不重启会继续按旧四档把模型拉回来（实测反复回 29 分钟不卸）。

- [2026-11-11 13:22:26] 造闸纪律（2026-11-11 写 drama_rules.py 时确立，可复用到任何判据引擎）：新闸必须自带「1 正例 + N 反例」可执行自检，反例逐条写成断言再上生产（漫剧九段门 28 判据自检 14/14=1 正例+13 反例+状态机跳步）；反例必须覆盖"数字擦边"（4 秒镜告警/6 秒阻断、480p、抽卡第 4 次、响度偏出 −14±2、盲评 8 分）而不只测明显坏件，否则闸只会在极端样本上亮红、在生产路径上形同虚设。Why：历史上多次造闸失败都是同因——阈值拍脑袋且从未在真实路径生效（如 queue_integrity.py 写裸文件名导致状态校验从未跑过）。


## 归档 2026-11-17（L1 记忆瘦身·原文下沉·来源 memory.md 条目号）

- [from memory.md #26 · Feedback] [2026-09-23 15:26:40] CEO 批评「考虑的很不全面」（2026-09-23 元宙讨论）：单点线性推进不够，重大立项须先全盘系统思考再谈局部——全盘应含：操作闭环（元宙不止「看」，须「看→查→令」三态+CEO 四输入面[governance §4]的游戏化操作映射：方向变更=指挥核心改航道/P1署名=奇点签名/红线裁决=晶片层裁决/资源调配=拖拽无人机）、空间分层钻取（L0 集团宇宙→L1 分区内景→L2 实体事件流）、时间双模（直播+git 历史编年史回放）、行为可见性分级（L1 被动零改造 vs L2 行为总线需立法）、技术选型自洽（承建方技术栈/发布端/自己工作流三方一致——他贴 Tuanjie 场景 5000x5000 Ground 示意引擎内真 3D 大世界）。教训：先出全盘架构，再谈局部决策；「说满」的承诺（如零改造全可见）要诚实分级。
- [from memory.md #49 · Project] [2026-11-11 18:50:58] [2026-11-11] 开源扫描结论（调研件=cph4/research/R-20261111-oss-skill-scan.md，提交 09e86739c）：**框架一律不引**——crewAI/Airflow/Prefect/Kestra/Portkey/new-api/claude-code-router 与本仓约束（离线可跑、Windows+macOS 混合、一机一写者、零云依赖）相反，引进来是运维面不是能力；AGPL 项目还与闭源分发冲突。只偷机制，本轮落地 1 条：**评审位置偏差检验**（ChatEval/Multi-Agents-Debate 的 position-bias）——`panel_review.order_invariance` + `--check-order`，同一批证据换顺序必须同判决，顺序敏感则不放行；自检 10/10 含"顺序敏感必须被判出"负控。另三条待办（需真机/数据）：路由离线胜率（复用 condition_matrix）、同产物两次评审一致率（<80% 视为判决不可用）、24h 长跑句柄/回执增长。取证限制：GitHub API 60 req/h，详情未逐个复核，标注为"未核实"，不得当结论。
- [from memory.md #79 · Project] [2026-10-23 10:11:44] 竞品拆解部 RECON-DEPT 已立（CEO 令：媒体拆短剧/漫剧、游戏扒榜前10并成立专部门）。正典=cph4/fleet/recon-dept-v1/；工具=Tools/recon/drama_recon.py（逐帧场景分+多阈值标定，勿用固定 0.3——低码率竖屏剧会全漏检）与 apk_recon.py。通道实测：YouTube 可用；B站无登录 412（禁套主号 cookie）；应用宝详情页内嵌直链可用；APKPure 403；TapTap API 404。结构性事实：微信小游戏畅销榜前10中仅 3 款有公开安卓包；.wxapkg 解密列红线不碰，替代=实机录屏逐屏测量或第三方数据。
- [from memory.md #88 · Project] [2026-11-05 12:40:51] [2026-11-05] 主控常驻智能体成形（CEO「常驻 agent 去监督/派单/验收」「颗粒度要细，不是并行，是一天安排起来」·commit c1f05e24e）：①职责全表=cph4/fleet/MASTER-AGENT-DUTIES-v1.json，**60 项/10 域**（值守7·监督8·派单10·验收8·资产成本8·账本决策6·汇报5·自愈演进8），每项带 cad(3/15/60分钟/日)、输入、动作、产出、判据、兜底；②时间轴=Tools/fleet/day_plan.py → cph4/fleet/DAY-PLAN.md + state/day-plan.json，**7 个班次串行**（00-06夜窗/06-07交班/07-12上午/12-13决策轮/13-18下午/18-21收口/21-24夜前），同一时刻只干一件事；③常驻体只有一个身体=master_pulse（不再起第二个 agent 进程），新增阶段 order_watch（读任何机器上发的 CEO 令，当轮置最高优先）/day_plan/verify_done（DONE≠做对：空文件/坏JSON/视频0时长/拒答文本，首跑即抓到 1 张坏 JSON）；④可视面=Tools/fleet/console_server.py 常驻 127.0.0.1:8787（launchd com.fluxgroup.console，KeepAlive），页面含当前班次/智能体最近动作/一屏/分层决策/机队实况，15 秒自刷。
- [from memory.md #89 · Project] [2026-11-07 00:26:02] [2026-11-07 00:3x] CEO 需求总账 v1 已立并可自动核验（CEO「纵览我所有命令，自动化做到极致」）：31 条需求/10 域（自治·主控边界·机队满负荷·本地模型·产物真实·同步分发·素材资产·内容质量·汇报形式·边界合规），每条带原话锚点+判据；正身=`cph4/fleet/CEO-DEMAND-LEDGER-v1.json`，核验器=`Tools/fleet/demand_audit.py`（23 个机检探针，已接每日脉，rc=1=有缺口）；人读=`cph4/fleet/AUTOMATION-MAX-v1.md`，一屏=`CEO-DEMAND-BOARD.md`。首跑实况=18 条机检通过 / 1 条物理缺口（移动盘未挂）/ 12 条人判（内容质量与对外边界，故意不机检以免假绿）。**探针四次误报的教训**：主控只判得了自己盘上的东西——Windows 绝对路径、`C:/` 正斜杠盘符、子仓路径（quant/ 等）、`state/` 运行时产物，都必须判"远端待查"而不是"缺失"，否则把别机正常交付报成 48/15/6 张假完成。同轮真修=取消一张重复劳动卡（bm-b 与 bm-m 撞同一交付物，去重闸只在派单时生效、claim 后无人拦，记缺口 DUP-AT-CLAIM）。
- [from memory.md #90 · Project] [2026-11-07 22:57:06] [2026-11-07 22:5x] 复盘席建成（CEO「也要复盘总结并推广经验的智能体」）：核心一条铁律=**推广≠写在报告里**，每条经验必须挂机器可核验落点，四类 rg断点/symbol码里判据/doc正身件/card卡模板。正身=Tools/fleet/retro.py + RETRO-SPEC-v1.json（判据数据）+ LESSONS-SEED-v1.json（人工署名种子）+ LESSONS-LEDGER.jsonl（台账）+ RETRO.md（屏），接脉 43200s。返回码三态=0 全落点 / 1 有"待落点"（不算已推广）/ 2 声称有落点却核验不到（假绿，最严重）。抽取来源=失败卡 error_class 与 cancel_reason 前缀的重复簇（min_occurrences=2）；去重按 (class, 症状前24字)；`also_matches` 让派生候选归到已落点条目下，落盘时把被覆盖的旧台账行剪掉（否则同一件事永远挂在"没推广"）。实测 19 条经验全落点、1 条诚实待落点（E-CONTRACT 重复2次）。RG-19 用三态负控守它（空落点/不存在的 asserción/真断言）。
- [from memory.md #93 · Project] [2026-11-11 11:19:51] [2026-11-11 11:2x] **本机 bm-m 的机队自启已按 CEO 令全部暂停**（原话「都记录在案然后全部暂停，等我梳理工作流」）。现状=这不是故障，别当红来修：44 个用户级 LaunchAgent（43 个 `com.fluxgroup.*` + `com.user.weeklymaint`）已 `launchctl bootout` 并把 plist 移入 `~/Library/LaunchAgents/disabled/20261111-pause/`（未删除）；9 个登录项（Mos/Itsycal/Stats/Raycast/AlDente/Hidden Bar/豆包Doubao/飞书Lark/MonitorControl）已移除并记录真实路径。实测残留：`launchctl` 里 fluxgroup 0 项、8787/8790/8792 端口全释放，仅 Ollama.app 自身 serve 仍在（非自启项）。留档=`cph4/fleet/STARTUP-INVENTORY-20261111.{json,md}`（含每项 ProgramArguments/触发方式/暂停时 PID 与退出码）；恢复=`bash Tools/restore-startup.sh`（全部）或 `bash Tools/restore-startup.sh pulse console`（按名字挑）。**停用顺序有讲究：必须先停守护类 serviceguard/watchdog/selfwatch/resilience/toolwatch/loadwatch/modelwatch/usefulload/resourcegov，否则它们会把已停的重新拉起。**系统级 8 项（/Library/LaunchAgents 的 microsoft.update.agent、entraidentitybrokerxpc、netease.uuremote.agent；/Library/LaunchDaemons 的 aldente helper、macsfancontrol.smcwrite、microsoft.autoupdate.helper、netease.uuremote.daemon、brew tailscale）需 sudo，本轮未动。


## 2026-11-13 三条先踩后修的工程纪律：①**"配置里写了"不等于"连得上"**（Oll…（L1 迁入原文）
三条先踩后修的工程纪律：①**"配置里写了"不等于"连得上"**（Ollama.app 固定绑 127.0.0.1 且不继承 `launchctl setenv`，机队端点写了几个月从没通）——给别人的服务必须用"别人的路径"真调一次。②**超时只杀 shell 等于没超时**——`subprocess.run(timeout=)` 只杀直接子进程，须 Popen + `start_new_session=True` + `os.killpg`，并写负控；同族调用要一次横扫。③**让本地小模型干活要事实与措辞分家**——数字/结论全由规则算，模型只许改写一句话且句中数字必须在事实里，否则整句作废回落模板。


## 2026-11-20 12:03:32 **本地提交不 push＝随时被冲掉**（一晚连丢三次）：机队每轮 `g…（L1 迁入原文）
**本地提交不 push＝随时被冲掉**（一晚连丢三次）：机队每轮 `git pull --rebase --autostash`、并行会话也在做 git 手术，只存在本地的提交会被 `reset --mixed origin/main`／`checkout origin/main -- <paths>`／rebase 卡死挪出 HEAD。铁律=**改完立刻 `git push origin HEAD:main`，push 成功才叫落地**；丢了用 `git reflog` 找回 + `git rebase --abort` + 单文件 `git checkout <commit> -- <file>`。**2026-11-20 补充**：即使跑过 `git add`，文件也可能在 commit 之前就被并发同步回退，提交里于是缺文件——必须 `git show --stat <commit>` 核对文件真的进去了，再 push。


## 2026-09-23/11-04 **主控职责与硬边界**（三条原话合订）：「这个机器不要干重度生产的活，…（L1 迁入原文）
**主控职责与硬边界**（三条原话合订）：「这个机器不要干重度生产的活，他主要是调度，监督和运行常驻轻量模型」「你最重要的作为主控大脑，要多调研，多站在全局统筹，多思考方向，多派单，多监督」「你主要的职责还是调度和监控，主控 懂吗？」：①主控产出只能是**卡、裁决、告警、一屏**，生产产物必须落在执行机的交付物路径上；禁自己写生产链/出图/渲染/装配/回测，禁长时间亲自做 git 收口（事故走"报警→派修复卡→监督回执"，无人可派才亲自动手）；②对外只出草稿不代发；被问「是不是 AI 制作」「创作者身份」、引战/广告一律不代答；③本机禁 i2v/KF/渲染/批量转码/回测，重活 ROUTED 给生产力机夜窗或大脑。每轮先做全局盘点（各线产出年龄/缺口/阻塞）再成批跨线派单。


## 2026-11-21 00:02:13 CEO 两个人模型分工令（2026-11-20/21 原话「你这些尽量都…（L1 迁入原文）
CEO 两个人模型分工令（2026-11-20/21 原话「你这些尽量都利用本地大模型和算力哦，解决不了才上云端来解决」「最好都要适配好苹果系统mlx，除非是在没有」）：本机任务优先本机 MLX（mlx_lm 8788 / Ollama 的 *-mlx 档），本地做不到才上云端；配环境时把 venv 也补成 MLX 可跑（原只有 pyright/playwright、mlx 跑在 pyenv base＝两个解释器是隐患）。Why：他要的是本地产能与成本收敛，不是"能跑就行"的云端兜底。How：装包遇 0% CPU 挂起＝PyPI 直连被卡，一律加 -i https://pypi.tuna.tsinghua.edu.cn/simple。


## 2026-11-22 10:28:36 2026-11-22 CEO 第二次判"太慢"（原话「太慢了，真人不会这…（L1 迁入原文）
2026-11-22 CEO 第二次判"太慢"（原话「太慢了，真人不会这样」）：查下来的主因不是生成慢，而是**不需要 GPU 的活被 GPU 租约锁死**——agent_daemon 开场前就抢 publish，训练一占就整场跳过，浏览/点赞/弹幕全停。通用判据=动手前先问"这一步真的需要那块资源吗"，把不要的依赖去掉比调排班有效（同类要逐条查：出稿窗口、profile 独占、单例锁）。同时按"真人节拍"压掉无意义等待：发前停留会话内为 0、可见性回验移出发帖路径、只有真切换适配器才暖机、GPU 等待 ≤15s 就让路、候选先 3 条不够再追加。Why：他要的是"像人一样快"而不是"看起来在跑"；秒级与分钟级的差别会被直接感知。


## 2026-11-22 13:15:31 2026-11-22 性能优化的判据（CEO「搞到最优」）：慢的时候先查…（L1 迁入原文）
2026-11-22 性能优化的判据（CEO「搞到最优」）：慢的时候先查**缓存命中与进程冷启动**，再查模型速度——本线实测同一件事从 85–130s 压到约 8s，靠的不是换模型而是三件：①提示词前缀固定（随候选变化的内容一律放末尾，否则 8788 缓存每条失效：首枪 5.1s vs 命中 0.6s）②常驻浏览器空闲从 10 分钟改 60 分钟（关一次重付 19.7s 冷启动，而 Chromium 只占 ~500MB）③去掉 4B 兜底与每拍换段件。Why：这三样通常比换模型有效一个数量级，且不需要牺牲质量；判据要落成可量的单轮耗时（压测中位 4.0s、发送链 3.6–3.9s，SD08 ≤30s）。


## 2026-11-22 14:07:23 `except Exception: pass` 会把"调用了一个从未定…（L1 迁入原文）
`except Exception: pass` 会把"调用了一个从未定义的函数"也吞掉，让整步长期是空的（2026-11-22 实锚：practice_tick 里的 `verify_pending(1)` 在本文件从未定义，NameError 被吞，那一步永远不执行，日志里也看不出来）。Why：这类空转不是报错、不是慢，只是"什么都没发生"，最难发现。How：①核心流程里禁止裸 `except: pass`，至少写一行 `log({"skip": why})`；②定期用 `python -m py_compile` 之外再加一次未定义名扫描（如 `ruff check --select F821`）覆盖主流程脚本；③任何"应该做某事"的步骤，要有落账或计数器证明它真的跑过。


## 2026-11-22 17:45:43 只增的运行时台账**不能进 git 跟踪**，否则会被机队同步整段回滚（…（L1 迁入原文）
只增的运行时台账**不能进 git 跟踪**，否则会被机队同步整段回滚（2026-11-22 实锚：`cph4/fleet/social/practice-log.jsonl` 里 14:03 真发的 post/lane/qualified/timing 四行，14:08 恢复成仓库旧版、末尾退回 13:26，而配额/去重/可见率判据全建在它上面——丢行＝判据悄悄变假绿）。Why：pulse 自动提交与机队 reset/checkout 都会用仓库版本覆盖工作区，append-only 文件天然"本地比仓库新"。How：①台账移出 git 跟踪（远端改读日汇总）；②过渡期加高水位守门（`Tools/fleet/ledger_guard.py`：行数变小即 rc=2 并打印差额），把"静默丢历史"变成"立刻报红"。


## 2026-11-22 17:45:48 同一个浏览器 profile 只能有一个入口；第二个入口自己 launc…（L1 迁入原文）
同一个浏览器 profile 只能有一个入口；第二个入口自己 launch 必然 ProcessSingleton（2026-11-22 实锚：常驻浏览器 browserd 把 acct1 的 profile 打开后，会话侧 `login_state()` 仍自己 `_launch` 一次，于是从 11:43 到 17:37 每轮只记 `profile_busy`（51 次），一整天没看/没赞/没发，而日志把它记成"环境被占用不是故障"，安静得像没事）。How：①凡是被别人持着的资源（profile/锁/浏览器/模型），入口必须先去问持有者——已加 `browser_daemon` 的 `nav` 动作，登录态核验改走常驻上下文；②daemon 内做同源 fetch 必须先把页面落到 bilibili 源页，about:blank 里跨源 fetch 会 "Failed to fetch"；③"环境被占用"这类让路必须计数并在连续 3 次时报红，不许当正常状态静默吞掉。


## 2026-11-22 18:14:32 "腔调不像人"只能靠 few-shot 真实样本改，靠形容词改不动（20…（L1 迁入原文）
"腔调不像人"只能靠 few-shot 真实样本改，靠形容词改不动（2026-11-22 实测·4B 生成）。做法：①按平台**自己的分类**取样本（B站 kind=打卡/夸奖/挑刺/玩梗/共鸣/提问/其他），每种给 8 条真人原句 + 各自字数带（打卡 3–12 字、共鸣 15–45 字），按候选序号轮换原型；②同一视频 6 条候选立刻分化成短反应/追问/挑刺/补充信息/具体夸/长夸，而此前是一个模板改字；③弹幕的锚点词必须从**领域词表**取（剪辑/蒙版/转场/团战…），从标题切任意片段会切出"别做一个梦幻""作全流程讲解"这种半个词；④弹幕通用句要**人工筛**，机器按"情绪词+无领域名词"筛出来的仍会串场（实测把"屏幕里的游戏画面有点模糊"发到剪辑教程下）。正身=Tools/fleet/voice_spec.py + corpus/hot/VOICE-SPEC-v1.json。


## 2026-11-22 20:35:31 质量判据的分工铁律：**数字由规则算，判断交本地模型**（2026-11…（L1 迁入原文）
质量判据的分工铁律：**数字由规则算，判断交本地模型**（2026-11-22 立）。规则能算的：长度、重复（开头 2 字/4-gram）、具体词命中、AI 腔词命中、原型占比、人设漂移——4B 的算术与计数不可靠，不让它碰结论。规则算不准的：这条像不像真人随手写、属于哪种原型——正则把 67% 的稿都归成 plain，等于看不出好坏，这类才交 `local_review.py`（2B 座位 triage，只回一行 JSON {human 0-10, archetype 7选1, issue ≤15字}，字段全白名单，解析失败重试一次再失败作废，绝不拿半截输出当结论）。另：模型不可用时（训练独占）要**排队并写明原因**，不能逐条打成"作废"——那会把"GPU 被占"误记成"稿子有问题"。


## 2026-11-14 FleetLink（8790）真实能力边界：只有 `health`/`s…（L1 迁入原文）
FleetLink（8790）真实能力边界：只有 `health`/`status`/`poke`/`sync`，**没有执行通道**（/tasks /run /exec 全 404）；`/sync` 是逐文件推送，白名单=4 个 md 的 union 追加 + `dispatcher/delivery-watch/*.json`，其它路径 `path-deny`——**分叉机拉不到 git 时，union 追加 orders.md 是唯一能真正写进它工作树的通道**；SMB 445 需凭据；`Tools/fleet-nodes.json` 里 ip/mac/tailscale_ip 为 null 的机器连 WoL 都发不了。


## 2026-11-11 自驱架构正身：`AUTONOMY-V3.md` + `Tools/fle…（L1 迁入原文）
自驱架构正身：`AUTONOMY-V3.md` + `Tools/fleet/station_drive.py`（SENSE→SUPPLY→CLAIM→RUN→VERIFY→RECORD+HANDOFF）。主控不造卡；机器没活自己找，只有三件事上报=要模型/对方工位不在线/对外花钱不可逆。四条边界=不对外、不自封人判（manual→PENDING_HUMAN）、无产物契约不建卡、无 cmd 判 NEED-CMD 不假跑。算力大脑=机队本地模型中心（agent 自动化、批量文本、剧本一律走 brain，Mac 禁批量生成）；任务颗粒度正身=`TAXONOMY-v1.json` + `Tools/fleet/work_matrix.py`。


## 2026-11-17 11:43:07 [2026-11-17] 养号 agent v2 定案（CEO 令「用本…（L1 迁入原文）
[2026-11-17] 养号 agent v2 定案（CEO 令「用本地大模型做客服/B站粉丝维护/弹幕交互/评论，先训练好」，已推 0b1f30c39）：正身=cph4/fleet/social/SOCIAL-AGENT-PLAN-v1.md（git 分发，含通道矩阵/模型分工/四闸/上线顺序）。通道=弹幕走 B站开放平台·互动直播（appId+key+secret+直播间身份码，需实名入驻+报备，未批只读不写）／评论与私信无官方 API，只能导出→本地草稿→人复制发。红区=不代发、不逐条自动回弹幕、不套主号 cookie、不爬页面。事实包 faq.jsonl 只认 verified_by，未核实一律转人工。命令=social_drafts(三通道)+social_review(人工批审回流)+social_eval(黄金集38题)。


## 2026-11-17 13:32:18 [2026-11-17] 本机"不换页加速"四条实测（采集侧）：①单个 …（L1 迁入原文）
[2026-11-17] 本机"不换页加速"四条实测（采集侧）：①单个 Chrome 实例 RSS **≈1.05GB**（1/2/3 实例=1.06/2.10/3.16GB 线性），3 个并存会把空闲内存打到 32MB；②**模型才是内存大户**：停掉 4B/9B/2B 后空闲 164MB→4732MB，所以采集前先 `ollama stop`（重载仅 1.5s）；③定案机制=`workers_by_mem`（(空闲−900MB)÷1.1GB，最小1）+ 采集与推理**互斥**（写 `.codely-cli/state/MEM-MODE=collect`，model_queue 见标记即 DEFER_COLLECT）；④B站评论区**不登录不渲染**（页面结构只剩 #commentapp/bili-comments），公开 view/reply API 直接拒 → 采集必须靠登录态。正典=SOCIAL-AGENT-PLAN-v1.md §十四。


## 2026-11-17 14:46:46 [2026-11-17] 记忆文件会被"先截断后写"清空（本机实锚 10…（L1 迁入原文）
[2026-11-17] 记忆文件会被"先截断后写"清空（本机实锚 10:59，仓根 CODELY.md 与 ~/.codely-cli/{CODELY,memory}.md 同秒变 0 字节/残片，11:01 autosave 签入空文件丢 79 条）：任何写 L0 的代码必须 tempfile+fsync+os.replace 原子写，并加"解析出 0 条却要覆盖有条目的 L0 → ABORT rc=1 保留原文件"防空写；闸已改（事务 68ab43971），memory_nightly 同改。另：闸在 darwin 上旧实现靠空的 USERPROFILE 拼相对路径（CWD 恰好是仓根才没炸），主题库落点改为跟着被治理文件走。当次清空的写入者未定位（curator 报告仍是 11-15，故非闸所为）。


## 2026-11-17 15:56:02 [2026-11-17] LoRA 训练四事实（本机 qwen3.5-4…（L1 迁入原文）
[2026-11-17] LoRA 训练四事实（本机 qwen3.5-4b-4bit + mlx_lm 0.32.2）：①基座是思考型模型，不设 apply_chat_template(enable_thinking=False) 会先吐 <think> 推理块；generate() 也不再吃 temp，须 make_sampler(temp=) 传 sampler。②mlx_lm 的 loss 行带 ANSI 色码，不剥 `\x1b\[[0-9;]*m` 正则抓不到，运行卡会静默记 None（假绿的典型）。③训练集弹幕占比过高（>50%）模型只学半句碎片，正法=按来源分层抽样（弹幕≤35%、弹幕<6字不入集）+ 每条样本带视频标题上下文；实测同题输出从「也许是这种在数字世界中」变成「iPhone拍的很稳，但没看懂小孩有啥爱恋」。④--loop 常驻进程只在启动时 import 一次，改采集代码后不重载就永远跑旧逻辑（台账连续 BLOCKED 的真因）。正典=cph4/fleet/HUMAN-CORPUS-v1.md §八 + 工具 social_sweep/train_build/train_lora/train_sample/blind_ab。


## 2026-11-21 19:06:54 分段分类正身（2026-11-21）：segments.classify…（L1 迁入原文）
分段分类正身（2026-11-21）：segments.classify 是关键词命中，62,786 行里 44,351 行(71%)判成 generic，等于每段都在用"平均嗓"训练——段专用件训不出来先查这个。做法=Tools/fleet/corpus_classify.py：qwen3-embedding:0.6b 向量化(44k 行约 28 分钟，batch 96，文本截断 200 字，400 自动减半)+单机 k-means(48 簇)+每簇只问本地 4B 一次(44k 次生成要 8 小时不可行)，产出 SEG2.jsonl 由 train_build 优先消费；命名必须**双问一致**(最近5条+随机5条)，只问一次会把"现在不都这种吗"判成 beginner；加一致性后 48 簇只 12 簇合格→保守重标 11,944 行(27.8%)，宁留 generic 不打错标签。向量缓存 corpus/human/EMB-cache.npz(176MB)，嵌入与命名可分两次跑。


## 2026-11-21 20:39:33 git 大文件事故与修法（2026-11-21）：state_sync.…（L1 迁入原文）
git 大文件事故与修法（2026-11-21）：state_sync.py 的 `git add -A cph4/fleet` 把 train/RUNS 下 167 个 32MB LoRA 权重（整目录 5.1G）扫进历史，远端 pre-receive hook 拒推、本地积压 10 个提交推不出去。修法三件——①.gitignore 加 cph4/fleet/social/train/RUNS/、*.safetensors、*.npz；②state_sync 的 add 加 pathspec 排除（:(exclude)…，不靠 ignore 一层保险）；③本地 git reset --soft origin/main 重建不含权重的提交再推。判据：git ls-files|grep -c safetensors 不应再增长，推送前用 git show --stat 核对。另：远端拒推时错误是 "pre-receive hook declined"，不要按网络问题重试。


## 2026-11-21 22:16:53 本机算力排班正身（2026-11-21 立）：机读表=cph4/flee…（L1 迁入原文）
本机算力排班正身（2026-11-21 立）：机读表=cph4/fleet/social/COMPUTE-SCHEDULE.json，6 通道（publish/train/selfgen/embed/bake/light）+ 白天夜间两窗口，铁律=同一时刻只有一个 GPU 任务、开工前 acquire、结束 finally release、拿不到写让路不许当故障。关键数值：出稿 practicetick 300s→1800s（一天 20–30 次动作够用，每轮只占 GPU 60 秒）；trainloop 保持 300s 但开训前查"出稿到期"并让一 tick，让路冷却必须存在（10→25 分钟，否则出稿长期失败反把训练饿死）；selfgen 新增 com.fluxgroup.selfgen 每 6 小时；daemon 会话持 publish 租约 TTL=时长+10 分钟。实测对照：lr=1e-5(+15.0, 人味8) 优于 3e-5(+12.5, 人味5)，batch4 只提速 1.5 倍（内存带宽 bound）——超参不是瓶颈，数据量才是。


## 2026-11-22 14:07:14 养号线发帖慢的结构性根因＝常驻浏览器 browser_daemon 是*…（L1 迁入原文）
养号线发帖慢的结构性根因＝常驻浏览器 browser_daemon 是**单线程** HTTPServer（Tools/fleet/browser_daemon.py），一次 browse 在 daemon 内睡 25–110s，期间所有发帖/回验请求排队：单条 post 空闲时只需 3.18s（curl dry 实测），排队时 90s（6×15s 采样全停在 post_reply→_daemon）。已缓解未根治＝浏览在 daemon 内限 8s、browse 的 goto 60s→20s、出稿前回验的 profile 锁等待限 10s；未决方案（post 插队／browse 让路、per-key 独立 playwright+ThreadingHTTPServer、POST-PENDING 哨兵）待选。验收判据=连续 10 次真实发帖 post_s 中位 ≤10s。


## 2026-11-22 14:07:19 养号线发送台账的单一真值＝`cph4/fleet/social/prac…（L1 迁入原文）
养号线发送台账的单一真值＝`cph4/fleet/social/practice-log.jsonl` 的 `action=post` 行（按 rpid 去重）。2026-11-22 实锚：实发 10 条而 HEALTH.comment=0、SD05 配额判据恒绿——HEALTH 读 USER-AGENT-LEDGER（只有看/赞/弹幕）、social_comment._today_sent 读 comments-sent.jsonl（已停写）。硬闸 arm_probe.cap_check() 本来是对的（它是唯一读对的一处）。How：任何"今日已发 N 条"类计数，源头只能是 post 行；分区明细靠行内 account 列（practice_tick/arm_probe 的 log 已统一补写 FLUX_ACCOUNT）。


## 2026-11-22 20:35:24 养号线配额＝**带刹车的自动升降档**，判据用**回复质量**不用可见率…（L1 迁入原文）
养号线配额＝**带刹车的自动升降档**，判据用**回复质量**不用可见率（CEO 2026-11-22 原话「你评论是否可见不是很重要，我要的是回复质量和其他的」——可见率取决于平台审核与折叠，把它当加量开关等于让不可控的数决定产量，可见率从此只记录）。`freq_policy.py` 五档 LEVELS（30–44／40–60／54–76／70–96／88–120 条/天，两号合计）；升档全中才升：样本≥8、质量中位≥70、具体率≥60%、撞模板≤10%、AI 腔=0、无真失败；降档：连续 2 次真失败，或质量中位<55／撞模板>25%／AI 腔>20%。质量分来自 `reply_quality.py` 七维（具体性/人味/不撞模板/长度带/贴题/原型分布/人设一致），起点 `QUALITY_SINCE` 只判生效之后的稿。档位落 `state/RAMP.json`，配额落 `FREQ-POLICY.json`。


## 2026-11-22 20:35:37 养号线有常驻质量智能体（CEO 2026-11-22「派个智能体持续干下…（L1 迁入原文）
养号线有常驻质量智能体（CEO 2026-11-22「派个智能体持续干下去」）：`Tools/fleet/quality_agent.py` + launchd `com.fluxgroup.qualityagent`（每 20 分钟一轮），流程 SENSE→DECIDE→ACT→RECORD，决策顺序按"最伤质量"排（AI 腔漏闸→撞模板→长度带→具体性→原型扎堆→扩池→补采高赞样本→等待）。**权限边界写死**：只做确定性可逆动作（扩池≤400/次、补采≥45 分钟冷却、把最扎堆原型计数+3），不发帖、不改阈值、不改代码——那三件归 practice_tick 与主控/CEO；做不了就写清原因，宁可空转不造假活。产物：`state/QUALITY-AGENT.jsonl` 台账 + `cph4/fleet/social/QUALITY-BOARD.md` 一屏（含"12 面：红 N/待判 M"）。


## 2026-11-16 三个容易误判的机队事实 + 巡查正身：①`fleet_cmd card …（L1 迁入原文）
三个容易误判的机队事实 + 巡查正身：①`fleet_cmd card state` 不接受 DONE（DONE 只能由执行器 verify 产生），主控跨工位派单用 `station_shards.upsert(..., allow_cross=True)`；②`llm_gateway`(8792) 长期在线且有 PASS_PATHS + X-Flux-Token，**tailscale 100.64/10 与回环免令牌**，"缺模型网关"类 BLOCKED 多半是旧判据；③「评审团通过票 0/1」是业务判定不是链路故障（36 款仅 1 款材料齐全）。全年巡查=`Tools/fleet/patrol.py`（产物 `PATROL.md` + `state/patrol-history.jsonl`）。


## 2026-11-19 16:46:32 [2026-11-19] 本机工具链盘点与 GitHub 调研结论（br…（L1 迁入原文）
[2026-11-19] 本机工具链盘点与 GitHub 调研结论（brew 前缀 `~/.homebrew`=Tier 3，本次 8 个包因无 bottle 走源码编译；已装 ruff/shellcheck/shfmt/git-delta/yq/duckdb/ast-grep/lnav/macmon/mole/restic；gitleaks 与项目自建 `secret-scan.ps1` 重复故不建议留）。**HuggingFace 在本机不可达**（直连超时、`hf-mirror.com` 的 `/api` 与 `/resolve` 均 308 后目标不可达、关 `hf-xet` 无效、机器无任何代理）⇒ 任何依赖 HF 拉权重的方案（mlx-audio / mlx-omni-server）都只能装不能跑，别把它当可用产能。**待修**：3 处 `try/except` 吞掉的静默 bug（`closer.py:80`、`fork_close.py:163` 缺 `import time`；`regression.py:481` 缺 `import shutil`；`queue_claim.py:257` 调用早于定义）+ **168 处 `subprocess.run` 未写 `timeout`**（ast-grep 可查，可成闸）。**本机零备份**：`tmutil destinationinfo` 无目的地、无本地快照。正身=`cph4/research/GITHUB-MAC-TOOLING-20261119.md`


## 2026-11-22 18:14:32 B站"按热度取高赞评论"接口 `x/v2/reply?...&sort=…（L1 迁入原文）
B站"按热度取高赞评论"接口 `x/v2/reply?...&sort=2` **有 IP 级限流**：匿名连采约 60 个视频后返回 412（之后整条路返回拦截 HTML，登录态同源 fetch 也一样）。可持续姿势=1.2 秒/条 + 遇 412 退避 30 秒 + 按 bvid 记已采（HOT-SEEN.json）续采 + **结果合并绝不覆盖**（第一次采到 58 条，第二次只回 6 条并覆盖，好样本全丢）。工具=Tools/fleet/voice_mine.py（登录态走 browser_daemon 的 hot 动作，失败回落匿名）。另：`x/web-interface/archive/related?bvid=` 公开可取、无限流，是扩内容池的稳定入口（Tools/fleet/pool_expand.py，108→808 条实测）。


## 2026-11-22 20:35:37 养号线"整面体检"正身＝`cph4/fleet/social/QUALI…（L1 迁入原文）
养号线"整面体检"正身＝`cph4/fleet/social/QUALITY-SURFACE-v1.json`（12 面定义：话术/原型多样性/人设一致/互动效果/内容供给/选片贴合/闸有效性/节拍成本/账号安全/训练协同/创新实验/汇报新鲜度）+ `Tools/fleet/surface_audit.py`（逐面从磁盘事实重算，三态 OK/红/待判，待判不算通过，rc=2 有红）。配套创新机制 `Tools/fleet/arch_perf.py`：把 qualified.arch 与 verify.likes 按原型汇总，样本≥5 才下结论，最优原型以 20% 概率倾斜（llm_client._pick_arch 探索-利用，80% 仍走今日最少用）。**路径坑**：social_guard 的判据产物在 `cph4/fleet/social/state/`，其余工具在 `.codely-cli/state/`，体检必须两处都找，否则把"有结果"报成"没结果"（本次实测踩到）。
