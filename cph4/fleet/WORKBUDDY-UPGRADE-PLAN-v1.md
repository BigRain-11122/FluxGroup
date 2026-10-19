# WORKBUDDY 模式升级工程总案 v1.0（大工程拆解·2026-10-19 立项）

> 令源：CEO 2026-10-19 原话「参照workbuddy的模式，升级所有涉及的，这个是大工程，好好思考拆解，一步步来」＋「github若有 直接用」（orders.md 2026-10-19 11:54 行）。
> 本件=大工程总拆解正身（Phase 0 产物）。阶段执行状态随批更新于 orders.md 对应行；总回访=2026-10-26 治理窗。

## 〇 一句话拆解

WorkBuddy=腾讯效率智能体（个人 AI 办公助手·日访问量居国内效率智能体首位），其模式的**开源同构本体=OpenClaw**（github.com/openclaw/openclaw·MIT·OpenClaw Foundation 501c3·WorkBuddy 官方兼容其技能体系）——「github 若有直接用」正身即此。逐要素对照我们集团现状：**十要素九已有六、缺三**——真缺口=①统一 Gateway 控制面 ②**CEO 手机遥控通道**（最大价值件：CEO 随时随地一句话→集团执行）③技能市场互通（连接器健康半残另计）。升级工程=用 OpenClaw 开源本体打底补三缺口，其余要素做**映射正典化**（查重律：已有且部分超配的面=映射注记，禁重建）。

## 一 WorkBuddy 模式正身（十要素·双源验证）

来源：WorkBuddy 蓝皮书 28 章（workbuddy.homes·开源实战读本·四篇「从0到1→真实案例→工作系统→岗位行业」+TASK→CASE→WORKFLOW→AI TEAM 沉淀律）＋OpenClaw 官方仓/文档（docs.openclaw.ai·2026-10-19 实读）＋WorkBuddy 工程设计拆解（三层记忆+模块化系统提示词）。

| # | 要素 | WorkBuddy 形态 | OpenClaw 同构位（现成轮） |
|---|---|---|---|
| 1 | Gateway 统一控制面 | 客户端=会话/工具/事件/通道的本地控制平面 | OpenClaw Gateway（默认端口 18789·绑 loopback） |
| 2 | 多通道+手机遥控 | 桌面客户端+手机遥控+Slack/TG/Discord 远程联动（海外版） | 20+ channels（WhatsApp/TG/WeChat/Slack/Discord/Feishu…）+iOS/Android/Win/macOS 原生 app+Control UI 网页 |
| 3 | 技能生态 | Skills 市场+SKILL.md 格式+官方技能仓 | ClawHub（clawhub.ai 技能注册表·与 Claude Code 技能互通） |
| 4 | 连接器 | GitHub/企微/公众号/腾讯地图/MCP 接入 | Channels + MCP servers + plugins |
| 5 | 专家/数字员工 | 7×24 专家数字员工+多 Agent 执行层+专家调度层（企业版） | Multi-agent（Agents 框架·主/子会话） |
| 6 | 项目 | 项目制人机协作（企业版三大能力之二） | Workspaces/projects |
| 7 | 三层记忆 | 云端画像（Cloud）+用户级（User·跨项目全局规则）+工作区（Workspace）+会话 0 层+人格层+两级会话压缩 | memory（session/log/brain 三层·自动蒸馏） |
| 8 | 自动化 | Automations（定时/触发） | cron/定时任务 |
| 9 | 权限沙箱 | 默认权限 vs 完全访问两级+安全策略模块 | pairing 配对+untrusted input 包裹+tool policy+sandboxing |
| 10 | Agent Loop+三模式 | Craft/Auto/Skills 三种工作模式 | agent loop+skills 自动激活 |

## 二 对照盘点（我们现状 × 十要素·九强六缺三）

| # | WorkBuddy 要素 | 我们现状（实测 2026-10-19） | 判定 | 升级动作 |
|---|---|---|---|---|
| 1 | Gateway 控制面 | Codely CLI 会话+FleetLink :8790 微监听+dispatcher 三层（L0/L1/L2）——分散无统一网关 | **缺** | Phase 1：OpenClaw Gateway 上机 @bm-a |
| 2 | 手机遥控 | CEO 只能开 CLI 窗口/当面下指令；tailnet 已通三机（100.110.185.62）但 CEO 手机未入网 | **缺（最大价值）** | Phase 1：WebChat/原生 app 走 tailnet（零公网暴露·零第三方账号）；手机入网=CEO 物理件一行 |
| 3 | 技能生态 | canon 25 skill（cph4/skills/·SKILL.md 同格式）+agent-library-sync+外部池 awesomeskills.dev 47,237 实测在册 | 强·缺市场对接 | Phase 3：ClawHub 精选过五门入库+我方 25 skill 互通验证 |
| 4 | 连接器 | GitHub MCP 401 凭据故障（本窗实测）+B站线候 cookie+MCP 片段在库（Tools/mcp-servers-fragment.json） | **半残** | Phase 4：修凭据+整合 |
| 5 | 专家数字员工 | AGENT-LIBRARY 30+ 席位+CEO-PROXY 8 班/日+PATROL-FLEET 十域 | **超配** | Phase 5：映射注记（Gateway 调度面接线） |
| 6 | 项目 | orders.md 台账+POOL 工单池+O 令体系+决策链四层 | **超配** | Phase 5：映射注记 |
| 7 | 三层记忆 | L0 全局/L1 项目/L2 主题 三层制 v3+memory-curator 写入五问+4h 预算闸（v2 首跑 -81% 实证） | **超配** | Phase 5：映射注记（WorkBuddy 三层↔我方 L0/L1/L2 对照表） |
| 8 | 自动化 | 60+ 计划任务族+task-register 唯一正门+S4U 律+自愈三件套 | **超配** | Phase 5：映射注记（OpenClaw cron 不启用·防双建） |
| 9 | 权限沙箱 | --yolo 静默启动器+静默律+让路律+机器让路触发词——散装无正式分级 | 部分 | Phase 5：权限分级表正式化入 governance+Phase 1 安全配置先行 |
| 10 | Agent Loop+三模式 | 交互窗（=Craft）/无人值守循环（=Auto）/skill 自动激活（=Skills）——**已同构在役** | **超配** | Phase 5：三模式映射注记 |

## 三 六阶段拆解（一步步来·每阶段带验收）

### Phase 0 · 深研+盘点+立项（本窗收口）
- 产出=本件+orders.md 登记行。
- 验收=双件上链 ✓

### Phase 1 · OpenClaw Gateway 上机 @bm-a（P0·补缺口①②·即刻起跑）
- **前置实测（已毕）**：Node v24.20.0 ✓（要求 24.16+）；npm 被 PS 执行策略挡→`npm.cmd` 绕过；git 索引干净；bm-a=集团中枢+tailnet 100.110.185.62 在网。
- **步骤**：
  1. 安装：`npm.cmd install -g openclaw@latest`（npm<11.16 去 --allow-scripts）
  2. 配置（**手写配置文件跳过交互 wizard**——静默律+无人值守正法）：model provider=`llama.cpp` 本地端点 `http://127.0.0.1:8090`（bm-a CoderServe 35B·本地优先律·llama.cpp=OpenClaw 官方一等 provider）；gateway bind=tailnet；telemetry 全关（`update.checkOnStart:false`）；pairing 强制；后续云端快车道 provider 随需加（CEO 直令件云端优先律）
  3. 服务化：`openclaw gateway install`（Windows=计划任务）——**与 task-register 唯一正门二选一**（若其自装任务违反 S4U/静默律→改用 task-register.ps1 包 run 命令注册 HQ-OpenClawGateway）
  4. 安全：`openclaw security audit` 过线（无高危发现才放行）
  5. CEO 手机入网（物理件一行）：手机装 Tailscale→登 tailnet→浏览器开 `http://100.110.185.62:18789` Control UI 即对话
- **验收**：①gateway 在听（status 实证）②Control UI 从 tailnet IP 可达 ③security audit 无高危 ④真话一句往返（问集团实况→回话含 fleet-reality 级数字）⑤零弹窗零公网暴露
- **让路律注记**：网关=轻量控制面（Node 常驻 ~百 MB 级）非重算力，工作日白天在役合法（与 FleetLink/CoderServe 同级基础设施）。

### Phase 2 · 机队遥控接线（缺口①深化）
- Gateway agent ↔ FleetLink/poke/fleet-dispatch 秒级链：CEO 手机一句话→网关工具调用→poke 唤醒机队→回执回报通道。
- 验收=手机发「让 bm-c 汇报当前 GPU 状态」→bm-c 被唤醒→回执经网关回到手机（全程 ≤5 分钟）。

### Phase 3 · 技能生态对接（缺口③）
- ClawHub/awesomeskills 精选技能（按九司缺口）→**过 oss-harvest 五门**（契合/反重复/科学使用/许可/健康+安全审——ClawHub 曾有 26% 技能带病先例=安全审强制）→cph4/skills/ 入册+agent-library-sync 分发。
- 我方 25 skill 在 OpenClaw 侧互通验证（SKILL.md 同格式=零适配理论，实测确认）。
- 验收=首批 ≥5 外部技能入册（带五门评估档）+我方技能侧载可用。

### Phase 4 · 连接器修复（半残补齐）
- GitHub MCP 401：凭据域（Codely MCP 配置 token 失效）→修复或 gh CLI 通道顶替；MCP 片段整合（merge-mcp-config.py 在库）。
- 验收=GitHub 读写链恢复（本会话即受益）。

### Phase 5 · 映射正典化+权限分级（收口）
- 三模式映射（Craft=交互窗/Auto=无人值守循环/Skills=skill 自动激活）+三层记忆映射（Cloud↔L0/User↔跨项目常设法/Workspace↔L1+L2）+权限分级表（CEO=完全访问·机队会话=按车道白名单·外部=pairing）→ governance/AI.md 一段指针。
- 验收=正典上链+AI.md 指针+查重律自检（零重复立法）。

## 四 红线与护栏（全程执法）

1. **静默律**：安装/服务化全走正门（task-register/官方服务二选一·S4U·零弹窗）；交互 wizard 禁（手写配置）。
2. **账号安全律**：微信/企微/Telegram 等第三方账号通道=**CEO 物理件域**默认零接入——手机遥控先行走 tailnet 自有通道（零公网暴露+零第三方账号+零封号风险）；第三方通道接入须 CEO 点头（B站 cookie 先例同律）。
3. **OpenClaw 安全教训**（社区实测：CVE 批量+ClawHub 26% 技能带病）：pairing 强制+不装未过五门的 ClawHub 技能+telemetry 关+bind 只限 tailnet+入站按 untrusted 处理+`openclaw security audit` 过线才放行。
4. **让路律**：CEO 原话「我要打游戏/我要工作」触发词→machine-state pause（网关进程归轻面是否停随 pauseLite 档定）；bm-a 白天=网关合法·重算力照旧禁。
5. **git 纪律**：本仓多窗共享——定向 add+commit（索引已核干净）+原子推；不碰他窗在飞件。
6. **查重律**：三层记忆/专家席位/项目台账/自动化/三模式=已有超配面只做映射注记禁重建（法熵预算）。

## 五 总验收+回访

- **总验收**=CEO 从手机发一句话→集团真实执行→回报到手机，全程 ≤1 分钟；三缺口闭合（Gateway/手机遥控/技能互通）+连接器恢复+映射正典上链。
- **CEO 物理件面（随简报附·不催办）**：①手机装 Tailscale 入 tailnet（App Store/应用市场搜 Tailscale→登录账号→自动入网）②第三方 IM 通道授权（微信/企微/TG·可选·点头才接）③GitHub MCP 凭据轮换（顺手两分钟）。
- **回访**=2026-10-26 治理窗：六阶段状态+总验收判据+法熵对账（本工程新增正典 ≤3 件）。

## 六 WorkBuddy↔我方映射正典（Phase 5·查重律执法=映射注记·零重建）

> 本节=十要素中「已有且部分超配」面的正式映射表（禁重建律）；新立面仅=权限分级表（散装规则首次集中成表·非新规则）+AI.md §3 一行指针。

**三模式映射**（WorkBuddy Craft/Auto/Skills ↔ 我方在役形态）：
- **Craft（人机协作共创）↔ 交互窗**（CEO 直令会话·本工程全程形态）
- **Auto（自动化执行）↔ 无人值守循环**（OS 循环族/EngineTick/值守轮/决策轮/CEO-PROXY 巡班·提速令 v2 频率常数）
- **Skills（技能自动激活）↔ skill 自动激活双面**（Codely skills 全库+OpenClaw 网关 skills allowlist 门控〔fleet-ops 现役〕）

**三层记忆映射**（WorkBuddy Cloud/User/Workspace ↔ 我方 L0/L1/L2 三层制 v3）：
- **Cloud（云端画像·跨设备）↔ L0 全局硬法+索引**（各机 <home>\.codely-cli\CODELY.md 注入面·预算闸执法）+**git 正典=跨机正身唯一源**（记忆 §8/§10）
- **User（用户级·跨项目全局规则）↔ L0 用户偏好面**（CEO 常设法五条=管家人格 USER.md 同源）
- **Workspace（工作区记忆）↔ L1 项目层（git 分发）+L2 主题层（按需读）**；会话 0 层+人格层 ↔ OpenClaw SOUL/IDENTITY/USER 三件（管家人格正典）+Codely 会话上下文
- 超配注记：我方多出=memory-curator 写入五问+2h 预算闸（WorkBuddy 无预算闸机制）；WorkBuddy 多出=两级会话压缩（OpenClaw memory 自带·管家用默认）

**权限分级表**（首次集中成表·各条在役执法件照旧）：

| 级 | 面 | 权限 | 在役执法件 |
|---|---|---|---|
| P0 | CEO 本人（含手机遥控通道） | 完全访问+物理件域独占（账号/凭据/建仓/支付/保留面） | OpenClaw 网关 token 认证+tailnet-only bind+让路触发词唯一例外 |
| P1 | 机队会话（各机 Codely 窗/循环/席位） | 按车道白名单（三车道定岗+同活禁双开）+git FluxGroup 面全自主/metis 面点头制 | resource-chain §9.1+让路律+S4U 律+静默律 |
| P2 | 网关管家（OpenClaw butler） | 只读+唤醒（三命律：实测再答/大白话/禁改）·命令手册白名单制 | AGENTS.md 红线+skills allowlist+4b 工具组 deny（web/browser） |
| P3 | 外部件（ClawHub 技能/未配对客户端） | 五门过才入册+pairing 强制+untrusted 包裹+许可未验明不用 | CLAWHUB-ADOPTION-LEDGER+OpenClaw pairing+安全双门（verify+install） |

**查重律自检**：三层记忆/专家席位/项目台账/自动化/Agent Loop/三模式=六面已有超配→本节纯映射注记 ✓零新机制零新文件；唯一新增=权限分级表成表（规则全部在册·无新法条）✓；消费面=AI.md §3 一行指针 ✓。

## Changelog
- v1.0（2026-10-19 11:5x·bm-a 交互窗）：立项+Phase 0 收口（深研双源+盘点+六阶段拆解+护栏+验收）。
- v1.1（2026-10-19 12:1x·bm-a 交互窗）：**Phase 1 收口**——OpenClaw 2026.10.5 上机（npm 全局+allow-scripts 补授权）；配置=tailnet bind+token 认证（64hex）+rateLimit+allowedOrigins 白名单+**白天 4b 轻面主模型**（ollama/qwen3:4b-instruct·让路律合规）+35B(:8090) 夜窗备选 provider+telemetry 关+mdns off+4b web 工具组禁（防注入）；网关在听 **127.0.0.1:18789+100.110.185.62:18789 双 bind**·health 双绿；安全审计 **0 critical 0 warn**；真话一句往返 15s 实证（Control UI→token→网关→本地 4b→回话）；守护=**HQ-OpenClawGateway**（task-register 正门·every:10m 幂等保活·点火 result=0·S4U 被 UAC 拒→按律降级隐藏链+入提权积压账）；runner=Tools/openclaw-gateway-runner.ps1（幂等+tailnet 等待+分离隐藏进程）。CEO 接入=手机装 Tailscale 入网→浏览器开 http://100.110.185.62:18789→贴 token（物理件一行）。
- v1.2（2026-10-19 13:4x·bm-a 交互窗）：**Phase 1.5 管家换脑收口**（CEO 批评令 13:0x「没调整到位…不要浅尝辄止」响应——Phase 1 空壳三缺〔未灌集团知识/未接机队/未自动化模型切换〕全补）：①**正典五件**=cph4/fleet/workbuddy-gateway/（SOUL.md 人格+AGENTS.md 操作手册〔三条命律+让路触发词唯一执行例外+命令手册〔fleet-reality.ps1 查机队/orders.md 尾 8 行/fleet-dispatch.ps1 -Reason "CEO-remote" 唤醒/AI.md §4 文件地图〕+红线〔禁 git 写/禁建任务/禁改生产/静默/账号安全〕〕+IDENTITY.md+USER.md CEO 五条偏好+skills/fleet-ops 管家版）——runner 段 0 每次启动同步正典→workspace（git=唯一源·10 分钟热更新）；②**代理式流程三连败全链定谳**（工程师实测·坑律入册）：败一=原生 ollama 插件请求 32k→4b 占 10.5GB 显存（让路律违例·当窗卸载还 CEO）→改走自定义 provider `ollama4b`=http://127.0.0.1:11434/**v1**（openai-completions）；败二=「对话对模型太长」——/v1 默认 4k 装不下 ~13k 指令栈→setx 16k+Ollama 重启；**败三（根因真身）=setx 只写注册表不进老父进程环境块**——13:11 重启只杀 serve 没杀托盘，托盘用旧环境块（无 CONTEXT_LENGTH+遗留 KEEP_ALIVE=-1 模型永驻显存）复活 serve→/api/ps 实锚 context_length=4096·expires 2319 年；正法=**先杀托盘本体重启**（托盘=旧环境复活源·杀 serve 它就换旧环境拉新的）+显式 `$env:` 值随 Start-Process 传+注册表双落；上下文 32k 实测 9.8GB=败一同级违例→**16k 定谳**（加载 7GB·5 分钟自动卸载=bursty 轻面合规·KEEP_ALIVE -1→5m 同窗归正）；③**模型昼夜自动切换在役**=Tools/openclaw-model-switch.ps1（provider id 勘正 ollama4b/·健康感知幂等·config 热重载）+HQ-OpenClaw-ModelDay(09:07)/HQ-OpenClaw-ModelNight(19:07)（task-register 正门·S4U 拒→按律降级隐藏链入提权账·夜班 35B 在听才切·白班 35B 挂才回 4b）；④**端到端验收 PASS**（13:23 实锚）：新会话问机队状态→4b 发起 exec 工具调用→实跑 `powershell -NoProfile -ExecutionPolicy Bypass -File "...\Tools\fleet-reality.ps1"`→读真实探测（bm-b/bm-c hb_age=117m·bm-d tailnet=N）→作答携强制时间戳 2026-10-19T13:24:35（认知更新律服从实证）——1 分 23 秒 302 词元；⑤诚实边界：4b 白天=代理可用但慢（首轮 ~1.5 分钟·fleet-reality 实测数据 117 分钟心跳延迟如实呈报）；**云端 API key（Kimi/火山等）=物理件可根治白天质量**；夜窗 35B 全能力；已知小瑕疵=fleet-reality 输出中文段经 exec 管道 GBK 乱码（模型能绕开·非阻塞·候修）。
- v1.3（2026-10-19 13:4x·bm-a 交互窗）：**Phase 2 机队遥控接线收口**（CEO 令 13:3x「严格参考 workbuddy 改造所有，按计划自动化一步步推进」）：①**发现=秒查通道已存在**——FleetLink 监听器 /status（v1.9.3 Get-StatusJson）本就带 gpu/ram_free/cpu_load/disk_free 字段（nvidia-smi 直查），管家缺的只是入口；②**新工具=Tools/fleet-node-status.ps1**（v1.0·只读 fail-soft）：按名册逐机 curl :8790/status 压缩成单行 ASCII（gpu 型号/vram_free/ram_free_gb/cpu_pct/disk/repo head 同步位/last_pull 龄）——4b 免 JSON 解析直读；reason 字段 ASCII 前 24 字符净化（bm-c 曾收中文 reason 经 exec 管道 mojibake 实锚）；③**管家手册升 v2**=命令 4 新增「机器资源秒查」（全机队/单机 -Node 过滤·CEO 问 GPU/显存/算力空闲必跑）·原读正典顺延为命令 5；runner 同步实测到位（workspace 手册 27-28 行实锚）；④**模型卡 contextWindow 勘正**——OpenClaw 原以为自定义模型 128k（UI 显示 108k 用量）=长会话必溢 16k 真实上限；`contextWindow` 字段实测生效（models list：4b=16k/35B CoderServe=8k 双槽实况/27b=16k）→OpenClaw 会在真实窗口前自动 compact；⑤**端到端验收 PASS·25 秒**（验收线 ≤5 分钟）：新会话「让 bm-c 汇报当前 GPU 状态」→管家实跑 fleet-node-status →答 bm-c=RTX 3070·空闲显存 14,316 MiB·空闲内存 5.2GB·CPU 23%·磁盘 1227.3GB·实测时间戳 2026-10-19 13:39:25+引用净化 reason（X2670-XQ-REDO-ESCALATION）——274 词元·结论先行·大白话合格；⑥运维实锚：CEO 13:34 亲测管家在用（4b 在线 expires 实锚）·keep_alive 5m 自动卸载工作正常。
- v1.4（2026-10-19 13:5x·bm-a 交互窗）：**Phase 3 技能生态对接收口**（CEO 令 13:3x 推进令）：①**我方技能侧载互通确认**——SKILL.md 格式原生兼容（fleet-ops 被 OpenClaw 正确解析+激活：`agents.defaults.skills:["fleet-ops"]` 后 skills list 1/60 ready 实锚·16k 预算内 +150 词元）；②**ClawHub 市场通道打通**=OpenClaw 自带 skills search/verify/install 正门（verify=注册表级安全扫描+install=安装时二次审计=双门执法）；③**首批五件全五门过入册**（全 MIT-0·全 clean/benign）：llmxray-diagnose-ollama-calls（Ollama 调用诊断=10-19 排障问题类）·llama-params-optimizer（llama.cpp 调优四阶段法·卡内明示对齐 contextWindow=当日同坑）·fleet-doctrine（机队多模型路由）·model-routing（重试只降不升+预算帽纪律）·github-repo-ops（**免 token GitHub 公共仓=Phase 4 降级通道**）——落点=cph4/skills/ 五目录（agent-library-sync 跨机分发）+管家工作区正门安装+评估档正身=cph4/skills/CLAWHUB-ADOPTION-LEDGER.md+OH-20261019-hq-workbuddy；④**五门执法实录**：18 件评估·8 件安全否决（CRITICAL 97/HIGH 62 实锚=44% 带病率·「不装未过五门」红线实证）·5 件 parked（1 同域重复 model-routing-orchestrator+4 许可空白未验明不用）·4 域反重复整域否决（git/rss/quant/video 撞自有超配）；⑤外域启发式两条留档候立法：「重试只降不升」「30 秒专注思考即升档」；⑥验收判据达成：≥5 外部技能带评估档入册 ✓+我方技能侧载可用 ✓（fleet-ops ready 实锚）。
- v1.5（2026-10-19 14:1x·bm-a 交互窗）：**Phase 4 GitHub 连接器修复收口**（CEO 令 13:3x 推进令）：①**根因实锚**=Codely MCP `github` 连接器（settings.json→本地 github-mcp-server.exe stdio·toolsets 8 域）env 内 PAT 过期（29 字符·api 401 Bad credentials 实测）+gh CLI 未登录——而 **Windows 凭据管理器存有一枚活 PAT**（git:https://github.com·`git ls-remote` HTTPS 实测返回当日 push 尖 f9da0b27=活性铁证）；②**修复=换装**（Tools 流程：git credential fill 进程内取存储 PAT→api.github.com/user 预验〔200·login=BigRain-11122·scopes=[gist,repo,workflow]=覆盖 repos/issues/PRs/actions 工具集〕→settings.json 连接器 env 原键换值〔old_len=29→new_len=40·全程零打印零落盘零进 git〕）；③**陈旧进程清场**=杀本机五枚过期 token 陈旧 github-mcp-server 进程（11:37/12:47/12:57/14:06/14:08 五窗各一枚·全机无活连接=零伤害）；④**诚实边界**=MCP 连接器会话启动时拉起不热重载——本会话工具面到重启前仍断（如实）；新会话/全机新 CLI 窗自动吃到新 token=**GitHub 读写链在配置+凭据双层恢复**；⑤**降级通道三件在役**（401 期间即用）：SSH git 数据面（当日 5 推全成实锚）+匿名 API（本仓公共可读 200 实锚）+Phase 3 入册 github-repo-ops 技能（免 token 公共仓操作）；⑥**MCP 片段整合幂等执行**=merge-mcp-config.py 复跑 MERGE_OK（context7/playwright/unity-mcp/search 四服务器在位·additive 零删）；⑦**CEO 物理件面变更**：原「GitHub MCP token 轮换」物理件**就地销账**（机器自有存储凭据已顶上）——新物理件=零（若未来 401 复发再按轮换流程走 CEO）。
- v1.6（2026-10-19 14:1x·bm-a 交互窗）：**Phase 5 映射正典化+权限分级收口=工程全线 Phase 0-5 完结**（CEO 令 13:3x 推进令）：①**§六映射正典落档**=三模式映射（Craft↔交互窗/Auto↔无人值守循环/Skills↔技能自动激活双面）+三层记忆映射（Cloud↔L0+git 正典/User↔L0 偏好面/Workspace↔L1+L2·含双向超配注记〔我方多=预算闸+curator·对方多=两级会话压缩〕）+**权限分级表 P0-P3 首次集中成表**（CEO/机队会话/网关管家/外部件四级·各条在役执法件照旧·零新法条）；②**查重律自检过**=六面超配纯映射注记零重建零新文件 ✓；③**AI.md §3 指针落位**（机制表 WorkBuddy 行）；④**总验收达成判据**：CEO 手机一句话→集团执行→回报〔手机装 Tailscale 后即用·网关通道全绿〕+三缺口闭合〔Gateway ✓/手机遥控 ✓/技能互通 ✓〕+连接器恢复 ✓〔配置+凭据双层·新会话生效〕+映射正典上链 ✓——**六阶段全部收口·回访 2026-10-26 治理窗照案**。
