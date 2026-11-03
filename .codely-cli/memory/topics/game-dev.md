
- [2026-09-23 15:29:23] CEO 令「我说了 全部是2D 不碰3D」（2026-09-23 元宙讨论）：①像素风格默认=2D，CEO 的原始措辞就是约束本身，不得自行「升级」维度；②元宙及未来游戏类项目硬约束=团结引擎原生+全 2D，无 3D 模型/场景/相机；③高科技感≠3D，用 2D 光效（发光/光晕/扫描线/粒子）达成；④给 CEO 的选择题选项要贴合其原始指令，不要用推荐权重诱导偏离。

- [2026-10-24 23:06:11] CEO 令：吸嘟嘟要三种模式——1人爽玩 / 2人对抗 / 3人亲子（同一块车机屏，不分屏）。落地=Proto03_DuduModes（commit 8e0b97807）：①单人=吸力圈 190→520px、5 秒上头、无失败；②对抗=两人抢同一件的拔河，**必须设中线中立带（各让 110px）**否则谁贴线谁通吃（首版 5:24 一边倒，加带后 10:11 对称），40 秒、双方都有奖；③亲子=孩子吸（唯一得分者）+爸爸「聚」拉回散件 CD10s+妈妈「照」点亮遗漏 CD8s，共享目标无失败。Why=车机不能分屏，玩法必须"一块屏多人、每人一根手指"；亲子是三人各管一件事而非把单人玩法拆三份。

- [2026-10-28 17:46:19] CEO 硬令「不要再自动化运行游戏包了！」：任何自动循环/agent 会话不得自行启动已打包游戏（Unity player/exe/WebGL）做截图/QA/演示——自动化弹游戏=打扰工作+资源抢占，属不可接受的自主行为（MiniGameEngineTick 等已禁用）。要跑游戏包必须 CEO 明令或人工发起。

- [2026-09-23 23:00:50] 硅基生命正典要点（正身=life/BigLife docs/CODEX §一+SILICON-LIFE.md）：全城居民皆硅基生命体同种平等（族源三分=碳源/硅源/城源·宿主披露三态·数据层记录社会层平等）；「真正的硅基智能生命体」正典译法=12 条生命体征功能完备（机器可验）——永不译「有意识的」；T0 禁语=意识/感受/灵魂/数字永生/意识上传/电子人格；居民永禁声称专业资质；合规=AIGC 标识办法（2025-09-01 已施行）→参观端开门帧显著标识=硬判据；价值锚=硅基服务碳基。

- [2026-10-24 10:59:37] 车机游戏业务条线 G0 立项（CAR-GAMING-BU-001·委员会 C-20261024-01·正典=cph4/fleet/car-gaming-v1/{CAR-GAMING-MARKET-REPORT/CAR-GAMING-STRATEGY/CAR-GAMING-CHARTER}-20261024.md）：核心判断=车机游戏现为车企渠道市场非消费者市场，C 端付费三年内约 0.45 亿元/年（自底向上测算），主收入须靠 OEM 适配/预装/联合运营；切口=家庭亲子，首产品=吸嘟嘟家庭版车机版；渠道序=理想×Unity＞比亚迪 OIP＞鸿蒙 NEXT＞小米。90 天 G1=可玩 demo+3 家渠道材料+1 份 LOI。物理件待 CEO：8295/8155 样机、版号主体、OEM 引荐。注意：iim/cir 等站「全球车载游戏市场规模」互相差数倍，不可采信。

- [2026-10-24 13:16:56] 车机屏幕自适应定谳（CEO 令「按最高端车屏像素生产」·正身=GimmeAll/docs/car/CAR-ADAPT-MATRIX-20261024.md）：①**玩法区永远 4:3**（profiles 规定 clamp 0.75..1.3333）——任何车机的玩法区像素上限=屏高×4/3 → 4K 屏与 8K 45″贯穿屏的玩法区都只有 2880×2160，**不需要 8K 位图**；翼区用程序化座舱底+九宫格，永不做位图拉伸；②母版=2880×2160（4:3）；③profiles 10 档（新增 2560×1440/3840×2160/7680×2160 32:9）；④闸=Tools/car_adapt_check.py（10 档渲染像素+触摸底线 360px）+family_ui_kit_4k.py（从原始层重编、非等比即拒），已接入 PipelineRun car-adapt 阶段。

- [2026-10-23] 吸嘟嘟家庭/车机档（绝对路径前缀 C:\Users\sjs20\Desktop\FluxGroup\gaming\MiniGame\09_吸嘟嘟GimmeAll\GimmeAll\）：主文档 docs/FAMILY-EDITION-MASTER-20261023.md；族内件=30DAY-SPRINT/AI-PIPELINE/WBS/PROJECT-CHARTER/MARKET-BRIEF/QA-PLAN/LEVEL-DESIGN/ASSET-LIST/ASSET-PRODUCTION-PLAN/CAR-EDITION-RESEARCH/CAR-DATA-BRIEF（docs/ 与 docs/family/·文件名带 FAMILY-EDITION-*/CAR-* 前缀）+commerce-catalog-v1.json/car-screen-profiles.json/qa-testcases-v1.csv。

---

- [2026-11-02 14:56:08] FLUX OS v2 顶层架构定案并已开工（2026-11-02·正典=cph4/ARCHITECTURE-v2-FLUXOS-20261102.md）：轴从「公司/业务线」换成「能力」——5 层 17 模块（K1 决断／F1 普查 F2 契约 F3 事件／C1 侦察 C2 生产 C3 闸 C4 分发 C5 资产 C6 商业／R1 编排 R2 节点 R3 模型 R4 存储／O1 一屏 O2 不变量 O3 元宙）、6 契约（ORDER/CARD/RECEIPT/ARTIFACT/VERDICT/RECIPE，对齐 MCP+A2A）、12 条不变量+基线棘轮、三仓分离（法码／状态／资产）、13 线→产品组（定案经两轮修正=内容组／策略组19.9／游戏组Biggame；车机挂起等OEM）+4 归属+5 停止。选型：运行时改 dsh（不自研）、持久化用 SQLite step journal（不用 Temporal）、视频 Wan2.2、云端 DeepSeek V4.1-Flash。迁移 S0 止血→S1 契约→S2 编排→S3 资产与合规→S4 90 天见钱。

- [2026-11-02 17:35:29] 执行层自动化已落地并进主环（2026-11-02 晚·commit 9ffe0dc7 系列）：主环慢批按序 census→gate(16 条断言+通信体检合成一行)→metrics→showcase；新增 Tools/fleet/{census,flux_check,flux_contracts,comms_check,gate_report,ops_metrics,showcase,ship_ledger,audit_dupes}.py。规则：组配额 24h（内容14/游戏8/策略6/城市3，cph4/fleet/QUOTA.json）；断言红→该线卡插队；还债跟踪（2026-11-02 基线重设为 305 条、从该日起算 0%，原 258 条口径作废）；跨机产物认回执不再按本机磁盘判假红；作品墙 SHOWCASE.md 每 5 分钟刷新并列远端成片。通信四信号（心跳/上报/认领/回执）与判定口诀见 cph4/fleet/COMMS-RULES-v1.md。

- [2026-11-02 16:52:06] 自上而下自审的结构发现（2026-11-02）：①委员会形同虚设——判定队列 43 条中 23 条被机制 SUPERSEDED、19 条本地模型自答、仅 1 条升级，委员会实际裁决 0 次，「24h 裁决」是纸面 ②业务层只按优先级排队会互相饿死（游戏组曾 0 卡 0 产出），已用组配额修 ③资产库未建却已有 I4/I5 断言，永远 total=0 造成假绿 ④白天产能只剩 1 台（bm-a 让路 + bm-b 无回执 + bm-c 心跳沉默）⑤baseline 记 258 条债且无清债机制，红被永久合法化 ⑥元问题：设计/执行/检查全在内部，唯一外部锚是 CEO 抽查与真实发布数据。

- [2026-11-02 19:05:16] [2026-11-02] 游戏子公司（Biggame）CEO 全盘梳理定谳：39 款在册（P 系 8+G 系 31；G31=GlyphTower 小钢炮机在研·G24=OddTales 传家宝机在研·吸嘟嘟=本机双线）、约 9 款机器判毕业有真包（吸嘟嘟/G26/G28/G02/G04/G05/G07/P02/P06）、**0 款上线**——唯一战略卡点=账号资质链（微信 AppID→ICP→软著报审→提审，CEO 物理件，09-16 挂至今）；三机分工=本机总控+吸嘟嘟/小钢炮 10 款/传家宝 15 款（组合登记簿.md=多机唯一仲裁面）；疯狂系列六款（CEO 09-20 钦点·立项书设计详案最厚）停在设计档未排产；软著材料约 30 款已备；已呈 CEO 建议=先集中 1-3 款上线（吸嘟嘟→G05 离谱钓手/G07 人潮）再谈攒货。

- [2026-11-02 19:57:33] [2026-11-02 晚] 家庭版 FD 循环席上线（CEO 令「创建循环 agent 自动化开发·尤其加载多专家和相关技能」）：①三件套=GimmeAll/docs/family/ai/FD-PROMPT.md（循环脑：family-producer 必装+8 车道→专家技能映射+门禁先行/断点接力/独占目录制）+Tools/family_dev_tick.ps1（承 ModeTick v2 成熟配方：静默窗击杀/240 分硬顶/锁保鲜）+docs/family/ai/FD-STATE.json（断点+独占目录表，防并行撞车）；②计划任务 MiniGameFamilyDevTick 每 30 分钟（schtasks 通道非提权可建；Register-ScheduledTask S4U 被拒——S4U 转换欠提权窗顺手并入 s4u_fix 批）；③**本机 codely.exe 真身=D:\TUANJIEAI\Tuanjie Cowork\cli\bin\win32-x64\codely.exe**——MiniGame 仓无 tools/machine.json、ModeTick 的 LOCALAPPDATA 默认路径在本机不存在（FD 首火即死于此），任何车道脚本勿再默认路径；④取证：MiniGame ModeTick 全系车道被其内建 CLOUD-OFF 守卫整吞（当日 262 轮被吞：守卫见 FluxGroup 根的 CLOUD-OFF-LOCAL-ONLY-v1.md 即整体 exit 0，连本地会话一并吞=老空转病根之一）——FD 驱动器有意不带此守卫（溯源=CEO 10-22 云解禁修订+11-02 特批），并发帽=10。

- [2026-11-03 11:58:06] [2026-11-03] 技能库执行态（承 11:48:50 两层结构条·commit 0d1fb998+后续·已推 origin）：①质检基线=45 件合格 15→17；触发词问题清零（ccgs 10 件补英文 Use when；llama-params-optimizer 折叠块补触发句、原解析不出 description；闸补「时使用/时调用/questions」三种中文触发写法属补漏不是放宽）；art-critique 1047→2794 字补三条自查。②新增 `Tools/fleet/skill_eval.py` 成对评测（同题同模型同温度，挂技能 vs 不挂，比 must-hit）：**ship-ops with 1.000/without 0.250/delta +0.750，fleet-ops 0.833/0.000/+0.833，各 5 胜 0 负，各约 35 秒**（评测模型 qwen3:4b-instruct；回执=queue-receipts/skill-eval-*.json）。不挂技能时 4B 把「成片要不要标 AI」「push 返回 0 算不算成功」「发布回执写什么」全答反——技能价值首次有差分证据。③真发现：fleet-ops「poke 返回 ok 但机器不动」一题挂了技能仍 with=0.000，因为技能把那步写成句子（tasks=[该机 wake_tasks]）而非命令 → 精确执行的规则必须做成命令/断言，与 HEXIS +16.2 分结论一致。④接线完成：skills 阶段进主控脉慢批（deploy_gate 六关 PASS → 11:56:34 重启 → 11:57:04 实测 rc=0、0.1 秒）。⑤ccgs 11 件归属=**不装**（MIT 外部包、与自有 14 个游戏技能重叠；仓内留档+触发词已修，随时可装），规则=装不装由评测决定不由"看起来全"决定。⑥待 CEO 裁决=27 件口号型（ccgs 10/城市 5/其余 12）是「补齐判据」还是「归档」。⑦坑：Python `ok=bad=[]` 是同一 list 别名，导致"patched 10 / missed 10"自相矛盾的输出（与 PS5.1 变量不分大小写同类错）。

- [2026-11-03 13:11:02] [2026-11-03 13:12] 主控 MacBook 游戏环境已搭好（正身=cph4/fleet/hardware/BM-M-GAMING-SETUP-v1.md + Tools/fleet/ceo_mode.sh）：①装三条免费路线并清 Gatekeeper 隔离——Steam 6.1（universal 二进制，原生跑）、Whisky 2.3.5（Wine+Apple GPTK 跑 Windows 独占，甜点在 DX11 级/小体量，DX12 大作多失败）、RetroArch 1.22.2（仅 x86_64，走 Rosetta，核心首次启动在线下载）。②新增 ceo_mode.sh start/stop/status：玩游戏时先 bootout watchdog 再 pulse（顺序反了看门狗会把脉拉回来），--with-ai 连 ollama 一起停多让 3-4GB；stop 必须先跑 deploy_gate（闸不过不许起）；来回已实测（start 后三者全停、stop 后六关 PASS 且 PULSE 恢复刷新）。③边界已写进文档：M1 Pro 不是游戏显卡、不要用 Parallels 跑 x86 游戏（二次翻译比 Whisky 更差）、想认真跑 Windows 3A 唯一正解是 CrossOver 26.3（约 74 美元/年，付费决定归 CEO，我不代购）。④坑：bash 里变量名后紧跟中文会被吞进变量名（`$WATCHDOG（` → unbound variable），一律写 `${VAR}`。⑤git 手术前置=先 ceo_mode start 停脉，否则并发写状态文件必在 rebase 的 autostash 上撞冲突。

- [2026-11-03 13:17:50] [2026-11-03 13:20] 游戏环境改走 Switch 路线（CEO 令「不要 steam，不跑大作，大概就用 switch 什么的玩玩」·正身=cph4/fleet/hardware/BM-M-GAMING-SETUP-v1.md v2）：①Steam 已彻底卸载（/Applications 下需 sudo，走 osascript 提权；cask 记录在 $HOME/.homebrew/Caskroom 可无 sudo 删；无用户数据残留）。②Switch 模拟器用官方 Ryubing 分支 1.3.3：brew 里没有（任天堂法律施压后全部下架），真实下载端点=`https://update.ryujinx.app/download/query?os=mac&arch=arm64&rc=stable`（302 → `https://git.ryujinx.app/projects/Ryubing/releases/download/1.3.3/ryujinx-1.3.3-macos_universal.app.tar.gz`，66MB，universal 含 arm64，ad-hoc 签名→必须 `xattr -dr com.apple.quarantine`）；已实跑生成配置，默认 graphics_backend=Vulkan（走 MoltenVK），配置落在 `~/Library/Application Support/Ryujinx/`。③硬前提（我不代劳也不指引来源）：prod.keys/title.keys 放 `.../Ryujinx/system/`，固件从自己机器导出后用 Tools→Install Firmware 装，游戏用自购卡带转出；没有 key+固件则能开但起不了游戏。④M1 Pro 关键设置=分辨率 1x 原生、卡就关 Docked Mode（按掌机 720p 跑）、Texture Recompression 关；崩溃先换 Memory Manager HostMappedUnsafe→HostMapped。⑤老主机走 RetroArch（已装 1.22.2，x86_64 走 Rosetta，核心首批在 Online Updater 下载）。⑥Whisky 保留但不用（那是跑 Windows 游戏的）。

- [2026-09-29 17:16:53] CEO 主角/吉祥物设计双令与偏好（2026-09-29 交互直令）：①「去设计一批吸嘟嘟主角，让我来挑，风格一定要抓人眼球，各种特点，不要千篇一律」——主角探索=候选批制（多款并呈·回复编号挑·可多选混搭），五维差异化（物种/配色/材质/记忆点/性格零重复）；②追加令「3D的先保留，之前的2D水彩风格也生产一批，角色要更加夸张和有记忆点」——**定谳风格不锁死主角探索**（U279 3D 定谳照用 + 旧 2D 水彩复刻并板呈选），且主角设计取向=**夸张记忆点 > 保守可爱**。How to apply：未来角色/吉祥物/生物批默认多风格并呈；每款必带一个放大档记忆点（爆炸呆毛/半身巨嘴/三倍巨尾/巨型蝴蝶结类）；CEO 可指定混搭（如「B02 换 3D 做」）。

- [2026-10-08 20:12:59] [2026-10-08 20:1x] bm-a GimmeAll EditMode 门禁三坑律（10-08 U360-L3/L6 批三跑实录·HeadlessRunner batch 环境在册事实）：①AddComponent 在 batch EditMode 不自跑 Awake/OnEnable/OnDisable（生成/注销全须测试侧补驱）——公共驱动件已落 GimmeAll Assets/_Project/Tests/Editor/EditModeSpawnDrive.cs（DriveAllSpawned/DriveAllOnDisable/Drive），新测试一律用它勿再手写反射驱动；②**双发纪律**：SendMessage 与 GetType().GetMethod 只达最派生私有魔法方法——派生类自定义 OnEnable（如 LandmarkBeacon 总线订阅）会遮蔽基类 SuctionTarget.OnEnable 的注册面，必须基类 MethodInfo 直调（绕遮蔽）+派生面另发；③StopLevel 后 ObjectRegistry 残留已销毁件 C# 引用=OnDisable 同不自跑，DriveAllOnDisable 经基类反射 Unregister（纯 C# 面假 null 安全）。Why：10-08 门禁 11 红→4 红→0 三轮归因全落此三坑。

- [2026-10-08 20:13:20] [2026-10-08 20:1x] bm-a GimmeAll ContentCatalog 时限覆盖层语义（10-08 关7/9 断崖修一跑实录）：All() 第3/3b/3c 步的 timeLimitSec 覆盖=**注入前**位序（签名/变奏层在其后再回补）——终值=覆盖值+变奏回补（关7 41.5→45+1.5=46.5/关9 40.5→44+1.5=45.5）；TestSignatureLevels.ExpectedLimit 硬锁 90 关终值=改任何关注入必同步该表否则秒红。另：「每关恰 1 变奏」锁存于 TestSuctionFamilies+TestSignatureLevels 两处（关4 拍4 双族升格须两测试同改例外档）。垢类/地标类计价 0 件（可跳过爽点）不入 TotalTargets 但入生成面——LevelRunner 契约对账已改权重口径。

- [2026-10-09 12:43:05] bm-a U360-L4B 全屏走查批判例（10-09 12:2x-12:4x·承 CEO「继续优化」令·O-20261008-1438 L4 线 17 屏走查执法）：①**UI 走查正法=源码密度扫（Select-String 长文案模式）→取证工具拍 BEFORE 帧→多模态锐评→手术→gate+AFTER 终验**，锐评比源码扫多挖出三起源码看不出的：抉择横幅真布局崩坏（640 板×280 钮塞 56px 文案=折行溢出互叠不可读·生产稀有路径一直坏·测试只锁流程不锁布局——**新 UI 件必须锁几何**已落 TestU360L4BWalk）+败局副标题 "timeout" 英文码直出（LevelTimer 生产 Reason="timeout"→显示层 HumanizeFailReason 映射正法·总线载荷零改动防 TestCoreBus roundtrip）+商店驻场位空圆占位读感（剪影圆心加锁标=状态视觉化）；②广告披露律（U320 P0/P1「看视频」字样必留）与密度律的调和=去逗号并单短语（「看视频，星沙 ×2」→「看视频领双倍星沙」「续 10 秒（看广告）」→「看广告续 10 秒」）——禁删披露只裁句式；③取证工具复制律生效（U360L4WalkShot=BVersionSevenShot 复制件+新模态幕）·**复制 BVersionSevenShot 时必须带 using System.Reflection**（漏=CS0103 首跑全红实录）；④吸友榜开屏真路径=图鉴底带「吸友榜」钮 ClickButtonByText（无静态 Show·ScreenRouter 持实例）；⑤抉择横幅取证=发布 InLevelChoiceOffered{ExtendAvailable=true} 即现·LevelFailed 同拍自动收横幅（ChoiceBanner 六事件收口在册）。

- [2026-10-09 12:56:07] bm-a U360-L4B 走查批收尾判例（10-09 12:4x-12:5x·gate 6→8 三轮实录）：①**静态改文案必须全扫运行时写入点**——ResultScreen 复活钮改「看视频再吸 10 秒」后帧上仍带逗号，真凶=RefreshReviveFace() 运行时双态刷面（「用羽毛，再吸」/「看视频，再吸」）盖掉静态钮文——改 UI 文案 grep 该 label 全写入点否则帧终验必翻车；②**测试锁同步两坑**：CountTexts 类助手=精确匹配（"已永久解锁"双面同文后计数 1→2 秒红）+Contains 锁可能藏在看似无关的测试文件（TestCompanionRosterUi Contains("视频解锁")）——改串后跑 gate 用三红定位比预扫锁面更稳；③**渲染序陷阱**：懒建模态（图鉴）渲染在 ScreenRouter 预建屏（吸友榜）之上——从 A 屏按钮开 B 屏再拍照=先关 A 才拍得到 B（取证工具幕序修实录）；④图鉴占位「敬请期待～」路径=真机无 LeaderboardService 态才现，编辑器有 mock 服务喂排行行——帧面验不到≠代码没生效；⑤历史遗留布局账单在案待下场=旅程屏三处遮挡（标题被卡压/长卡名截断/CTA 压状态标签）+胜局数据行被明信片板盖+明信片框上下切字。

- [2026-09-28 11:29:44] U271 收口判例三条（开源 UI 自动装配落地批·2026-09-28·MiniGame commit e345212ec 已推）： → 全文档案: .codely-cli/memory/mem-20260930-g-012.md

- [2026-09-28 11:34:51] Tuanjie 批建造 SOP+TD demo 双坑律（09-28 五跑点火实证·FluxVerse City 工程）： → 全文档案: .codely-cli/memory/mem-20260930-g-013.md

- [2026-09-28 13:27:24] MiniGame 仓 GitBloatGate 门禁律（2026-09-28 U274 批三撞实录）：pre-commit 钩子=SOFT 1.5MB（需白名单）+HARD 6MB（永拒）——**证据截图一律 JPEG q88 化再入仓**（1080×1920 水彩风 PNG≈2.5MB→JPEG≈250KB·九成减量·审核板观感无损）；board_all 类全景拼图超 HARD=不入仓留沙盒；git add 目录前先删超限件否则被重暂存连环拦。另：游戏侧资产缺陷三件在案待转办=ui_postcard_frame 邮戳烤调试色值文本（入包提审风险）/icon_star 与 icon_star_dim 形状断裂（星形=漩涡·dim=五角星）/scene_japan 竖向水彩接缝。

- [2026-09-28 15:10:02] FluxVerse 瓦片城 v1 技术面（2026-09-28·TopDownTileCity.unity·FluxVerse 13a5277）： → 全文档案: .codely-cli/memory/mem-20260930-g-020.md

- [2026-09-28 15:53:27] [2026-09-28 15:53] Tuanjie 编辑器+Unity-MCP spike 实弹坑律（P-2026-09-28-10·判据①包解析✓②编译✓桥自启✓·③④在飞）： → 全文档案: .codely-cli/memory/mem-20260930-g-023.md

- [2026-09-28 16:21:23] [2026-09-28 16:25] Unity-MCP v10 深度用法坑律五条（承 15:53 spike 条·样区施工期实证）： → 全文档案: .codely-cli/memory/mem-20260930-g-025.md

- [2026-09-28 17:18:55] lowpoly 3D 域整理+AD标记+P3D_Spike 落盘（CEO 令「清理垃圾·分类整理·统一归lowpoly·分风格大类·按unity规范」+「做好资产的标记和理解」+「 → 全文档案: .codely-cli/memory/mem-20260930-g-026.md

- [2026-09-28 18:01:32] U279/U281 收口判例（2026-09-28·MiniGame e071797d2 已推·六屏 3D 糖瓷卡通重构批·与 U280 审计窗叠加态）： → 全文档案: .codely-cli/memory/mem-20260930-g-030.md

- [2026-09-28 22:39:01] [2026-09-28 22:5x] 城市活性升维方案 v1 立档（CEO 令「重点研究怎么让硅基城市真正的活起来」·FluxVerse 1b34b96·根仓 3c3a315）： → 全文档案: .codely-cli/memory/mem-20260930-g-039.md

- [2026-09-29 10:53:04] U299=Unity_UI自动拼装SOP全员学习令收口态（CEO 令 2026-09-29·orders O-2026-0929-002·HQ 25d14d8）： → 全文档案: .codely-cli/memory/mem-20260930-g-043.md

- [2026-09-29 15:02:09] U304/U305 判例收口（2026-09-29·CEO 双令全闭环·MiniGame 2a63e031a 已推·HQ 998417a 已推）： → 全文档案: .codely-cli/memory/mem-20260930-g-051.md

- [2026-09-29 15:14:01] [2026-09-29 15:2x] Tuanjie 2022.3.62t15 编辑器脚本编译两坑（09-29 Top1 施工批三连败实证）： → 全文档案: .codely-cli/memory/mem-20260930-g-052.md

- [2026-09-29 17:45:42] U308 吸嘟嘟真工程产品级动效改造批收口（2026-09-29·CEO 令「基于最新的流程和知识 去改造一下吸嘟嘟的界面 ui等」·orders O-2026-0929-010· → 全文档案: .codely-cli/memory/mem-20260930-g-057.md

- [2026-09-29 17:53:28] U309 判例收口（2026-09-29·CEO 令「吸嘟嘟的这 2 个不同风格的资产我都非常满意， → 全文档案: .codely-cli/memory/mem-20260930-g-060.md

- [2026-09-29 18:32:09] [2026-09-29 18:3x] U314 判例收口（CEO 令「吸嘟嘟的玩法，系统，流程，体验等等，全部优化一遍，并行工作。 → 全文档案: .codely-cli/memory/mem-20260930-g-066.md

- [2026-09-30 13:19:57] U320 尾巴收口+Unity 构建新鲜度三判例（2026-09-30 13:0x·真包冒烟后台通道收壳）： → 全文档案: .codely-cli/memory/mem-20260930-g-077.md

- [2026-09-30 13:19:57] O-20260930-1316 吸嘟嘟音频 v2+新手关令（在飞）：CEO 复听回执「吸嘟嘟的声音还是不够洗脑，其他的还不错，BGM分场景，每个关卡要有当地的地域或者国家特色。 → 全文档案: .codely-cli/memory/mem-20260930-g-079.md

- [2026-09-30 15:16:16] GimmeAll 批跑链两枚操作事实（U325 收口实测）： → 全文档案: .codely-cli/memory/mem-20260930-g-088.md

- [2026-09-30 16:57:04] 硅基生命元宇宙.html（CEO 令 09-30 起「可视化」恒指件）打磨管道事实： → 全文档案: .codely-cli/memory/mem-20260930-g-096.md

- [2026-09-30 18:08:56] [2026-09-30 18:10] FluxVerse/City3D 团结引擎 meta 加密判例： → 全文档案: .codely-cli/memory/mem-20260930-g-100.md

- [2026-09-30 19:19:37] [2026-09-30 19:2x] O-20260930-1856 三路调研收口（O-1706 追加令执行面·三 R-件入仓 cph4/research/·commits ceef389/f38f847/bc17d8f）：①unity-assembly-01＝8 步组装 SOP+判据表（微信面单线程单帧无法 GC=团结官方在册=数组预载翻帧官方依据；SRP Batcher 不辖 SpriteRenderer→合批验收以 drawcall 实读为准；SpriteAtlas 内包 vs TexturePacker 外包=外包主选）；②prompt-params-01＝12 填空模板卡（6 动作×水彩/糖瓷双锚）+三模型参数 profile（Wan 官方 50 步/CFG5.0/121 帧@24fps/仅 1280×704 两档；Cog 49 帧@8fps 快动作禁排候实测；LTX 30 步/CFG3.0=M1 在官方带内+≤128 token 压缩安全线）；③atlas-precision-01＝判据全表 J1-J18 可机检+SOP 十条。**四枚判负/勘误入产线正法**：a.Allow Rotation 官方存在且默认开（推翻旧内联「SpriteAtlas 不可旋转」）→图集打包必须显式关闭；b.20MB 首资源包=我司内定保守线非微信官方（官方=主包≤4M/总≤30M/单普通分包不限/独立分包≤4M·wx.preDownloadSubpackage 预下载 API 在册）；c.微信转换工具原 GitHub 仓停用（商标）→正源=微信官方文档站+团结 SDK 新仓 minigame-tuanjie-transform-sdk；d.ASTC 6x6=3.56bpp 三源互证但「默认档」无官方逐字=内定线。落实链=SOP 增章+嘟嘟试点件=实验室窗承接（O-1706/O-1856 台账）。How to apply：SOP 立典判据直接抄三件 §0；拼图集先显式关 rotation；包体口径用官方四值；转换工具问题查 SDK 新仓勿查旧仓。

- [2026-10-03 11:08:27] 本地 coder 产线现役态（U340-U345·CEO 令链「QWEN3 新模型 16G 全载」+「承担游戏子公司任务看准确率效率」+「最大化利用本地 coding 算力」+「速度可以缓缓·保证正确率复审和调试好·节省云端 token」）：主力=qwen3.6-coder:35b（34.7B MoE·IQ3_S·12.8GB·全量驻 16G 显存+16k ctx 零卸载·常驻 expires=never），副选 qwen3.8:27b——qwen2.5 老族已清出本机勿再引用；local_coder.py（MiniGame tools/llm/）流程=spec json→生成→机检→复审探针→证据→promote-on-pass；**实弹五坑律**（Windows 编码时区族·①utf-8-sig 读 BOM ②naive 时区禁注入 tz ③subprocess 显式 utf-8 ④stdout reconfigure utf-8 ⑤harness reader 同律）已固化 PROMPT_LAWS 自动追加；**U344 泵**=tools/llm/queue/（NN 升序·done/parked·补货法禁忙工），U345 改版=每 2h 一轮 ≤2 件·三层闸（机检唯一死闸+复审探针+验收实跑）·调试律禁盲跑（失败定病根·一次定向复跑·再败 parked）；**U345 复审校准判例=同族自审 [BUG] 噪声 10/11（自反证条目）——复审当探针不当闸门·[BUG] 人/泵轮分诊（真缺陷特征=可复现/违规格/回退丢失）·首轮分诊抓 2 真缺陷修毕（猴档死稿 main_v2+仓摘要 GIT_FAIL 回退=机检漏检被复审抓到）**；两批 9 任务 14 轮=终态 9/9 收编·首过 88.9%·均 12.2s·89.9-95.2tps（10-03 报告已呈）；真发现=cloudF 172 行补录审计 100%/DDO 20 处无守卫/SortIt 零门禁/登记簿 U259-U262 四组重复行；泵 cron 2cdc463e（7 天过期 10-10 续窗）；权威=登记簿 U340-U345 行。

- [2026-09-24 17:43:18] 硅基生命元宇宙窗（集团唯一指定整体可视化观测窗口·CEO 令 2026-09-24 ~16:45）维护面文件地图 v3： → 全文档案: .codely-cli/memory/mem-20260930-g-102.md

- [2026-09-29 17:16:53] 吸嘟嘟旧版 2D 水彩风格锚真值（2026-09-29 art_backup_v2_watercolor 真图拆解·dudu_full.png+creature_paris.png → 全文档案: .codely-cli/memory/mem-20260930-g-103.md

- [2026-10-04 23:08:06] MiniGame 三台账新分区路径（10-04 实况·旧路径 Design/configs/GLOBAL/ 直挂位已废）：①U 号登记簿活动账=**gaming/MiniGame/Design/configs/GLOBAL/台账/用户限制登记簿.md**（CRLF+BOM 契约不变·「正典/用户限制登记簿.md」=指针存根勿写）；②顶层设计组合过筛矩阵=**Design/configs/GLOBAL/档案/顶层设计组合过筛矩阵.md**（LF 无 BOM 不变·§9.x 节号现用至 §9.96=U351·写前查重）；③GLOBAL 下另有 正典//台账//档案/ 三分区结构（10-01~10-04 重组产物）·定位一律走 git ls-files 过滤勿凭旧路径直读。最新 U 号=U351（10-04）。游戏仓 GitBloatGate/定向提交律照旧。
