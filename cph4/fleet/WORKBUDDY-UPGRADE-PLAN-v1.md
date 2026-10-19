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

## Changelog
- v1.0（2026-10-19 11:5x·bm-a 交互窗）：立项+Phase 0 收口（深研双源+盘点+六阶段拆解+护栏+验收）。
- v1.1（2026-10-19 12:1x·bm-a 交互窗）：**Phase 1 收口**——OpenClaw 2026.10.5 上机（npm 全局+allow-scripts 补授权）；配置=tailnet bind+token 认证（64hex）+rateLimit+allowedOrigins 白名单+**白天 4b 轻面主模型**（ollama/qwen3:4b-instruct·让路律合规）+35B(:8090) 夜窗备选 provider+telemetry 关+mdns off+4b web 工具组禁（防注入）；网关在听 **127.0.0.1:18789+100.110.185.62:18789 双 bind**·health 双绿；安全审计 **0 critical 0 warn**；真话一句往返 15s 实证（Control UI→token→网关→本地 4b→回话）；守护=**HQ-OpenClawGateway**（task-register 正门·every:10m 幂等保活·点火 result=0·S4U 被 UAC 拒→按律降级隐藏链+入提权积压账）；runner=Tools/openclaw-gateway-runner.ps1（幂等+tailnet 等待+分离隐藏进程）。CEO 接入=手机装 Tailscale 入网→浏览器开 http://100.110.185.62:18789→贴 token（物理件一行）。
