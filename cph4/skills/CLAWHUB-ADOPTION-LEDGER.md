# ClawHub 技能采用台账（WorkBuddy Phase 3·五门评估档正身）

> 溯源：CEO 令 2026-10-19 11:58「参照workbuddy的模式升级所有涉及的…github若有直接用」＋13:3x 推进令。
> 机制：oss-harvest §四 科学使用五门（契合/反重复/许可/健康/成本安全）＋ WorkBuddy 总案 Phase 3 红线（不装未过五门的 ClawHub 技能·26% 带病先例）。
> 安全双门：`openclaw skills verify`（ClawHub 注册表级扫描）+ `openclaw skills install`（安装时二次安全审计）——本台账五件全部双绿。
> 窗：2026-10-19 13:4x-13:5x·bm-a 交互窗。

## 一 采用五件（全五门过·MIT-0·clean/benign）

| # | 技能 | 版本 | 许可 | 安全面 | 契合（替谁省什么） | 落点 |
|---|---|---|---|---|---|---|
| 1 | `llmxray-diagnose-ollama-calls`（@lognebudo） | 0.8.6 | MIT-0 | clean/benign（2×MEDIUM 提示：npx 未锁版→使用时锁 `llmxray@0.8.6`；本地流量留痕→只路由非涉密提示词） | Ollama 调用慢/截断/缓存丢失/CPU 混跑/num_ctx 选择——正是 10-19 网关排障全手工踩的问题类，替网关运维省逐案盲查 | cph4/skills/ 入册+管家工作区已装；源=github.com/LogneBudo/llmxray |
| 2 | `llama-params-optimizer`（@hoperealize） | 3.1.0 | MIT-0 | clean/benign·LOW 13 | llama.cpp/llama-server 参数调优四阶段控制变量法（context×VRAM 甜点）——卡内明示「对齐 OpenClaw contextWindow 与 llama-server 上下文」=10-19 上下文定谳同问题类；BigCompute 夜窗 35B 调参与网关模型卡维护的 methodology 底座 | cph4/skills/ 入册+管家工作区已装 |
| 3 | `fleet-doctrine`（@jarvis-drakon） | 1.2.0 | MIT-0 | clean/benign（纯 markdown 零执行件） | 多模型机队「哪类活派哪个模型档」策略——dispatcher L1 本地分类/网关昼夜模型档（4b/27b/35B）选型的 advisory 层；与 resource-chain §十路由律互补（律=政策·此=可激活技能面） | cph4/skills/ 入册+管家工作区已装 |
| 4 | `model-routing`（@sam-k-migz） | 1.0.1 | MIT-0 | clean/benign·LOW 0 | 请求路径路由纪律：显式模型锁优先/预算帽/重试只降不升（retry fallback 禁升档）——token-economy 路由律的可激活技能化（重试只降不升=我方法典未成文的净新增纪律） | cph4/skills/ 入册+管家工作区已装 |
| 5 | `github-repo-ops`（@blalf） | 1.0.0 | MIT-0 | clean/benign·LOW 0（无执行件·无持久化） | **免 token GitHub 公共仓操作**（代码分析/issues/PR/repo 结构/搜索）——GitHub MCP 401 凭据故障期（WorkBuddy Phase 4 同项）的降级通道；公共仓只读面零凭据即可用 | cph4/skills/ 入册+管家工作区已装；Phase 4 直接消费 |

## 二 parked（评估过不采·理由留痕）

| 技能 | parked 理由 |
|---|---|
| `model-routing-orchestrator`（@stephensu66·MIT-0·clean） | 反重复门：与 fleet-doctrine/model-routing 同域（请求路由），居中重叠件——三采一域=双建；任一退役可替补 |
| `smart-model-routing-for-zai`（@princnl·clean） | 许可门：ClawHub 卡 License 栏空白=未验明不用（其「30 秒专注思考即升档」启发式已摘录至本台账备查） |
| `windows`（@ivangdavila·clean） | 许可门：License 栏空白；内容面与我方 tool-pitfalls 50+ 条 Windows 判例高度重叠 |
| `ollama-local`（@timverhoogt·clean） | 许可门：License 栏空白 |
| `rss-feed-digest`（@zacjiang·clean·LOW 13） | 许可门：License 栏空白＋反重复门（与雷达日报线重叠） |

## 三 安全门否决实录（26% 带病先例的当日实证）

| 技能 | 否决依据 |
|---|---|
| `ollama-memory-setup`（@brasco05） | **CRITICAL score=97**+可执行脚本（verify fail） |
| `openclaw-tailscale-remote-access`（@jiangagentlabs） | **HIGH score=62**+10 件含可执行脚本（verify fail·suspicious） |
| `ollama`（@ivangdavila） | skillspector HIGH score=51（verify 虽 pass·从严不采） |
| `fleet-comm`（@dagangtj） | suspicious（verify fail）＋反重复（与 NATS 实时通信调研线 R-20261019-fleet-realtime-comm-01 重叠） |
| `tailscale`（@jmagar）/`ollama-memory-embeddings`（@vidarbrekke）/`ffmpeg-video-editor`（@mahmoudadelbghany）/`diagnose-openclaw-model-routing`（@can4hou6joeng4）/`agent-peer-tailscale`（@fuzzyb33s） | verify fail/suspicious（安全门一律否） |

## 四 反重复门否决域（整域不采·已有超配）

- git 域 4 件（git-deploy/git-backup-publish/git-manager/github-issues）：撞我方 git-surgery 35 条判例+每日外科实弹（超配）
- rss/news 域 6 件：撞雷达日报+radar-daily-sweep 线
- quant 域 10 件：撞 BigMoney 自有回测引擎+backtest-expert（W 波成熟）
- video 生成域：撞切片部管线与 10-15 开源工具栈 15 仓批（OH-20261015 记档）

## 五 维护律

- 更新走 `openclaw skills update`（ClawHub 托管目录）；台账五门结论随批重验（新版本=重跑 verify）。
- 「重试只降不升」「30 秒专注思考即升档」两条外域启发式已并入本表留档——立法吸收走 resource-chain/token-economy 正门，禁双源。
- 技能体保持上游 verbatim（零改写·升级可替换）；激活面由各 agent 的 skills allowlist 门控（网关管家现役=仅 fleet-ops）。
