
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
