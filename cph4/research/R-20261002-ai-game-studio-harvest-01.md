# R-20261002-ai-game-studio-harvest-01 — GitHub AI 游戏工作室盘点与收编（agent/skill 架构专项）
> 溯源：CEO 令 2026-10-02 ~21:4x「去查github评价很好的AI游戏工作室，他们具备很多专门的AGENT和skill，利用好」·消费方=集团技能面（P-2026-09-26-01 技能律）+Biggame G 系+City3D 城线+BigLife 参照·判据预注册=①高星头部盘点（星数/许可/活跃实测）②agent/skill 架构拆解 ③五门评估 ④收编落点
> 验证声明：gh api 实测（search×3+repo 直读 6 仓+contents×4+license×2）·CCGS 计数=README 自述+目录文件数双源交叉（agents 49 文件/skills 74 目录 ✓）·unity-mcp 许可=LICENSE 原文直读（首 25 行核心条款）·参照源已浅克隆在位=`K:\Fluxgroup\.tools\ccgs-reference`

## ① 头部盘点表（实测 2026-10-02）
| 仓库 | 星 | 许可 | 活跃 | 定谳 |
|---|---|---|---|---|
| **Donchitos/Claude-Code-Game-Studios** | **25,655** | **MIT** | 09-29 | **主收编**：Claude-Code 游戏工作室模板=49 agent+74 skill+12 hook+13 规则+39 模板 |
| AnkleBreaker-Studio/unity-mcp-server | 488 | 署名型（AnkleBreaker Open v1.0） | 10-01 | **POC 候选**：Unity MCP 347 操作/80 工具·多项目多 agent 路由 |
| OpenBMB/ChatDev | 34,435 | Apache-2.0 | 07-24 | 参照位：虚拟软件公司角色制（我 OS 循环已自研同构·反重复门） |
| a16z-infra/ai-town | 10,577 | MIT | 08-26 | 参照位：AI 小镇启动包——硅基城=其理念的 3D 城市版（BigLife 社交面参照） |
| MineDojo/Voyager | 7,237 | MIT | 24-04 停 | 已在册（global-benchmarks 引用·不重复收） |
| camel-ai/oasis | 5,220 | Apache-2.0 | 09-30 | 参照位：百万级社会 agent 仿真（census 10030→扩容参照） |
| Yuan-ManX/ai-game-devtools | 1,353 | MIT | 07-21 | 索引参照（资源枢纽） |

## ② CCGS 架构拆解（主收编件·MIT·Windows 主测·与我 Codely 技能体系同构直兼容）
- **三层工作室制 49 agent**：Tier1 总监 3（creative/technical-director+producer）→Tier2 部长 9（game-designer/lead-programmer/art/audio/narrative-director+qa-lead 等）→Tier3 专才 36；**引擎专家组**：Godot4/Unity/UE5 三套（Unity=unity-specialist+addressables/dots/shader/ui 四子专——City3D/MiniGame 直配）。
- **74 skill 全名单已录**（gh api contents 实测）：设计族 /brainstorm /design-system /balance-check｜评审族 /design-review /code-review /gate-check｜QA 族 /smoke-check /regression-suite /playtest-report /test-evidence-review｜性能族 /perf-profile /tech-debt｜生产族 /vertical-slice /prototype /sprint-plan｜编排族 /team-{combat,narrative,ui,release,polish,audio,level,live-ops,qa} 9 件多 agent 协同。
- **12 hook 自动执法**：validate-commit（硬编码/TODO/JSON 门）/validate-push（保护分支）/validate-assets+session 生命周期+agent 审计轨迹——与我 git 红线/闸链互补。
- **三判据与我同律（CEO 文化印证）**：①「story 不关闭除非游戏真跑+截图留证」≡我 U319 真包验证律；②modes.rigor 三档实测结论「29 份额外文档买的是可追溯性不是更好的游戏」≡我 C-02 反规则通胀；③协作非自治协议（Ask→2-4 选项→你拍板→草稿→签收）≡我决策链四律。
- **五门**：契合 ✓（游戏线+城线+技能面三承接）/反重复 ✓（集团技能现役仅 cph4-research-dispatch 首例·无此规模游戏专化库）/许可 ✓ MIT/健康 ✓ 25.7k★+周更/成本 ✓ 纯 md 模板零依赖。
- **采用**：参照源浅克隆在位 `.tools\ccgs-reference`（49 agent/74 skill 全文件）。

## ③ unity-mcp-server 评估（POC 候选）
- 许可门定谳：AnkleBreaker Open License v1.0=MIT 型+**署名硬条款**（整合产品须显「Made with AnkleBreaker MCP」+logo）→ 内部工具可用+署名入台账；**入硅基城产品交付链须带 credits**=商业面成本项。
- 价值面：347 命名操作/80 MCP 工具/269 按需——会话直驱 Unity 编辑器（场景装配/构建/截图/profiling/多项目多 agent 各自队列+可审查历史+undo）=City3D A 腿与 O-023 产品化令的工程杠杆（替代部分 batchmode 循环）。
- 未证面：Tuanjie 2022.3 兼容（Unity 2022.3 同源·Editor C# 插件大概率兼容·须 POC 实弹）；Node server + mcpServers 配置接线。
- 落点：POC 工单建议=下窗 A 机 City3D 试点（装 plugin→连 MCP→判据=会话内完成一次「场景改动→截图→build」闭环+署名位落 README）。

## ④ 结论应用表（research-protocol §二.1 强制·落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| CCGS 参照源在位+架构拆解 | 参照库：`.tools\ccgs-reference`（本件 §② 为索引） | ✓ 已落 |
| CCGS 择固化清单（技能律 P-01 承接）：unity-specialist 族→City3D 技能增补｜QA skill 族（smoke-check/playtest-report/test-evidence-review）→Biggame 闸链证据面｜/design-review /balance-check→城线评审团律 agent 化补充 | 转办：MiniGame 游戏前沿调研部+CPH4 技能面（技能律四条·源入司仓 tools/skills/·安装副本 gitignored） | 待派（下窗） |
| modes.rigor 分档+system_overrides+testing.strict 分型纪律 | 参照：任务书 rigor 档位设计（与我 WIP 帽/U177 互证） | parked（机制参照位） |
| unity-mcp POC 工单（署名条款+Tuanjie 兼容双前置） | 转办：CPH4 排程（A 机 City3D 试点） | 待派（下窗） |
| ChatDev/ai-town/oasis=参照位不入库 | 反重复门留痕（我 OS 循环/BigLife 已自研同构） | 已定谳 |

## ⑤ 失败面与防线二候选
- 失败面：Stanford generative_agents 原仓检索未中（3 结果均非原仓·M 待证·ai-town 已承载其理念）；MetaGPT 直读 TLS 超时×1（重试未做·已知头部不承重）；unity-mcp LICENSE 全文未读毕（核心署名条款已获·全文随 POC 验）。
- 防线二候选：①CCGS「49/74」计数=自述+文件数双源已交叉 ✓（可注销）②unity-mcp「268 tools」旧自述 vs 现版「347/80/269」=README 现版为准（候选留证）。

- 更新记录：T0 gh api 三路检索 → T1 头部直读 6 仓 → T2 CCGS 深挖（README+contents+license）→ T3 unity-mcp 深挖（README+LICENSE）→ T4 参照源克隆在位 → 终稿（≤60 行）。

## ⑥ CCGS 择固化启用清单（2026-10-02 批 2·CEO 续令「全面调研。有适配的启用」·P-2026-10-02-07·§④ 转办行本窗落地）

**新鲜面补扫勘误（gh api 实测 2026-10-02 22:3x）**：①**unity-mcp 主收编换血**=CoplayDev/unity-mcp **14,655★MIT**（09-30 活跃）——§③ AnkleBreaker 488★ 署名型候选**淘汰**（署名硬条款+星量级全面被超），POC 候选改录 CoplayDev（MIT 直用·A 机 City3D 试点下窗）；②gamedev-skills/awesome-gamedev-agent-skills 1,283★Apache=技能聚合清单仓在册（skills/ 目录+router 结构·后续技能源位）；③aldegad/sprite-gen 2,242★Apache（10-02 当日推）/scenario-labs/skills 829★MIT/CoderGamester/mcp-unity 1,919★MIT/IvanMurzak/Unity-MCP 4,375★Apache=参照族留痕；④letmeow/spark-arc-studio AGPL-3.0=许可门不入。

**CCGS 库内分型定谳（依赖扫描实测）**：74 skill=70 件深度绑 CCGS 运行时（yaml-helper.sh resolve_config/Agent spawn/斜杠命令编排/.claude/docs 配置面）→**不装留参照**（编排骨架思想=team-* 9 件多 agent 协同范式已在 §② 录）；4 件 hook-free（asset-audit/estimate/scope-check/start）择 3 直装——start=CCGS 模板自绑定引导件跳过。

**启用清单（11 件·装 C:\Users\Dasheng\.codely-cli\skills\·MIT © 2026 Donchitos·CCGS-NOTICE.md 署名）**：

| # | 技能 | 源型 | 价值面 |
|---|---|---|---|
| 1 | asset-audit | skill·hook-free | 资产审计（尺寸预算/孤儿检测/NOT ASSESSED 反编造律）→Biggame 五闸+City3D 资产面 |
| 2 | scope-check | skill·hook-free | 范围蔓延检查（净变更分档+NOT ASSESSED 反假 PASS 律）→承建链纪律 |
| 3 | estimate | skill·hook-free | 三档估算+置信级+反静默加垫 |
| 4 | unity-specialist | agent→技能 | Unity 角色协作面→City3D 技能增补（P-06 择固化清单兑现） |
| 5 | unity-shader-specialist | agent→技能 | Shader/VFX/管线角色面 |
| 6 | systems-designer | agent→技能 | 系统设计（CitySim 仿真面直配） |
| 7 | game-designer | agent→技能 | 游戏设计角色面 |
| 8 | economy-designer | agent→技能 | 游戏经济（硅基城经济体系储备） |
| 9 | technical-artist | agent→技能 | 美术↔工程桥接 |
| 10 | performance-analyst | agent→技能 | 性能分析角色面→Biggame 闸链 |
| 11 | qa-lead | agent→技能 | QA 策略/回归/发布质量门→Biggame 闸链证据面（P-06 兑现） |

适配法=frontmatter 裁 Claude-Code 专键（tools/model/maxTurns/allowed-tools）保 name+description+正文原文+来源注记（工具映射：AskUserQuestion→ask_user/Bash→run_shell_command/Agent→task/job/斜杠命令→对应工作流）；UTF-8 字节面验证过；**技能发现=次会话生效**（本会话发现列表会话初冻结=机制面·activate_skill 实测确认）。未装面=team-* 编排 9 件+hooks 12 件+规则 13 件=CCGS 运行时绑定族，参照库 .tools\ccgs-reference 全量在位随时可查。
