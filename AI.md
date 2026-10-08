# AI.md — FluxGroup 集团与元宙 AI 总览（正典入口）

> 目的：任何 AI 会话/新机器/新执行体读本文件 5 分钟建立全局认知，再按指针深潜。性质=唯一速览正典——**只给指针与结论，细节以目标文件为准**（单一事实来源）。
> 版本 v2.0 · 2026-10-08 · **瘦身令**（CEO 令「规则太多了，造成思考拥堵」·C-20261008-06 Phase 1：本件 17.9KB→≤10KB——历史沿革/案例复述/行内长文全部移出，git 史全保·指针零删除）·结构变更须 changelog+溯源（docs/governance.md §9）。

## 0. 一句话

**FluxGroup = 一人 CEO（Jason）+ AI 劳动力 + 机器机队的控股集团**：七条业务线（游戏/量化/媒体/商业化/数字生命/算力/城市安家）+ 一个横切实验室（CPH4 Labs）+ 一座元宙城（FluxVerse）。AI 干活、机器 24h 运转、CEO 只做决策和发令。商业×元宙总纲=`docs/master-plan.md`（城商一体双螺旋）。

## 1. 组织（谁是谁）

| 名 | 是什么 | 仓/位置 | 正典 |
|---|---|---|---|
| **Jason（CEO）** | 唯一决策者：方向/P1 署名/红线/资源四输入面 | — | `docs/orders.md` |
| **Biggame** | 游戏公司：**只做 2D 小游戏**（城建另属·不辖） | `gaming/MiniGame/`（独立仓） | 仓根文档+`gaming/README.md` |
| **BigMoney** | 量化公司：沪深 ETF 波段·双节点机队 | `quant/bigmoney/`（独立仓） | `PLAN.md`+`fleet/` 协议 |
| **BigStream** | AI 媒体公司：集团 AI 生态内容线+AI 短剧/漫剧/MV 产线 | `media/BigStream/`（独立仓·GH 仓名 Bigmedia） | 仓内 `PLAN/`+`orders/` |
| **BigDomain** | 硅基域商业化：引流/共创/19.9 算力包/代币内循环 | `domain/BigDomain/`（独立仓） | `BLUEPRINT.md` |
| **CPH4 Labs** | 集团实验室：机制淬炼+**技术/架构底层唯一问责**+城市三底座总装（`cph4/city-lab.md`） | `cph4/` | `cph4/README.md`（能力注册表） |
| **FluxVerse** | 元宙城：**集团直属独立载体**（城内含 3D 骨骼动作·Biggame=受托承建位） | `gaming/FluxVerse/`（独立仓） | `BLUEPRINT/DESIGN/TECH.md` |
| **BigLife** | 数字生命生产：城人口与人设资产（万人户籍库 census） | `life/BigLife/`（独立仓） | `docs/CODEX.md`+`docs/SILICON-LIFE.md` |
| **BigCompute** | 硅基算力：**商业化中枢司**（对外成交/定价/粉丝私域/渠道唯一出口·九部门全编制） | `compute/BigCompute/`（独立仓） | `BLUEPRINT.md`+`docs/plans/`+`docs/risk-register.md` |
| **BigHouse** | 硅基城市安家·数字生活（三柱=安家/邻里/共长·传统行业词族门禁） | `house/BigHouse/`（独立仓·remote 待 CEO 建库） | `BLUEPRINT.md` |

**机队**：bm-a（DASHENG·32 核·总控+开发+游戏 A 机）｜bm-b（16 核·回测+TTS/音频主力）｜bm-c（32 核·3070 16GB·ComfyUI 主产线+云天线+交互窗）｜CEO 笔记本=豁免位（移动指令总控·非机队·不入算力池）。配置分配唯一权威=`cph4/resource-chain.md` §二；新机接入=`Tools/bootstrap-machine.ps1`+`cph4/onboarding.md`。

## 2. 元宙（FluxVerse）思路

- **定义**：对标现实的赛博未来元宇宙——「城因现实而活，现实因城而治」；**城即超体**（脑塔=集团中枢·黄浦江=数据/资金/流量三流道·陆家嘴三城=四肢·街道机器人=机队 AI·git 全史=记忆）。
- **AI 行为剧场**：城里每个动画必须对应一次真实 AI 行为（commit=光点过江/令=光脉冲/认领=机器人出动）——**禁装饰性动画**。
- **驾驶舱**：看（L0 城市全景）→查（L1 建筑内景=司面板）→令（L2 台账留痕可审计）。
- **美术正典**：世界层=lowpoly 3D polygon（Synty 48 包资产库+自研 SiliconToon 卡通渲染·URP·日夜循环真实北京时间+真天气·工程=`gaming/FluxVerse/City3D`）；正典族=`gaming/FluxVerse/docs/lowpoly3d-*.md`+技能 `lowpoly-city-3d`。
- **里程碑**：M0 设定✓→M1 立骨（建城中）→M2 神经接通→M3 真孪生→M4 无处不在→M5 栖居。
- **数据面**：`world/world-state.json`（快照）+`world/world-events.jsonl`（事件流·按日归档）——引擎只读轮询 10s。

## 3. 运转机制速查（详细条款一律看正典件·行内不复述）

| 机制 | 节律 | 正典 |
|---|---|---|
| OS 循环/DevLoop（各司） | 10min | 各司 mandate |
| **决策委员会常务轮**（日常代管+复盘四问+自迭代） | 00:00/12:00 双班 | `cph4/council.md` |
| 值守轮（四器审计+催办+自愈+**回执核销步**） | 03:07/15:07 双班 | `cph4/night-round-prompt.txt` |
| 进化轮（立法+法熵审视+考核面） | 周日 09:17 | `cph4/evolution.md` |
| 巡检 patrol+外部独立审查 | 周一 09:23／日三班 22:17/06:17/14:17 | `docs/audit-charter.md` Part B／Part A |
| 令流（CEO 令→台账→执行→回执→核销） | 随时：秒级 poke→2min 哨兵→10min 轮询三层 | `docs/orders.md`+`cph4/resource-chain.md` §十 |
| 分级立法 T0-T3 | T0 宪法 CEO 签/T1 治理+否决窗/T2 机制 AI/T3 数据 AI | `cph4/evolution.md` §2 |
| 决策/审查/考核三链×四层（L0 团队→L3 集团·底层优先） | 常设 | `cph4/decision-chain.md` |
| 错误定级 E0-E3（E0=三通道直呈 CEO） | E0 即时/E1 当日/E2 轮内~周/E3 豁免 | `cph4/errors.md` |
| 诚实律三道防线（证据对/新鲜验证/宣称分级） | 常设 | `docs/governance.md` §10 |
| 交付时效（快速件 24h/CEO 可见交付 ≤5 天） | 常设 | `docs/governance.md` §11 |
| 调度+机队（verdict 驱动·云无限并行·保活/静默/让路/分工/本地主供/信息同步） | 常设 | `cph4/resource-chain.md` §一~§十 |
| 资源保留清理（R1 永不清~R4 随轮清·磁盘预算） | 日/周/月/季 | `cph4/resource-chain.md` §三§11 |
| 本地化算力（L1 确定性→L2 本地 LLM→L3 云 API）+Token 经济 | 常设 | `cph4/local-first.md`+`cph4/token-economy.md` |
| 自动化周期总账（防重复/防冲突/流转时限） | 全周期登记 | `cph4/cadence.md` |
| 新公司开线 SOP（P1-P5 判据制） | 随开线 | `cph4/venture.md` |
| 调研部门（九司·应用表强制）+GitHub 雷达+OSS 收获轮 | 常设/周/72h | `docs/research-dept-charter.md`+`cph4/github-radar.md`+`cph4/oss-harvest.md` |
| 记忆梳理（入口四问+热冷水位·周日窗） | 周日 03:07 | `cph4/memory.md` |
| 四环周期（反思日/批评周/进化月/宪法审季） | 四节律 | `cph4/evolution.md` §8 |
| 自驱力生态（零空闲+创新轨+本地批活供需） | 常设 | `docs/self-drive.md` |
| 极简执行协议（每轮启动只读 <2KB·产出=commit 非文档） | 常设 | `docs/executive-protocol.md` |
| QA Smoke 自验（Build→截图→自判） | 每轮 commit 后 | `docs/qa-smoke-test-charter.md` |
| 服务器律 v2（最小化最简化·入册制） | 常设 | `cph4/server-governance.md` |
| CEO 观测面（可视化=硅基生命元宇宙.html·第一检查入口+ceo-review 决策日志） | 随时 | `gaming/MiniGame/`+`docs/ceo-review.md` |

## 4. 文件地图（按需深潜）

| 要什么 | 去哪 |
|---|---|
| CEO 令与裁决 | `docs/orders.md` |
| **顶层治理架构一页图+八原则** | `docs/governance.md` §0 |
| 治理契约（边界/开线收线/协同/**命令查重律**/变更控制） | `docs/governance.md` |
| 商业×元宙双螺旋总纲 | `docs/master-plan.md` |
| 品牌/文化/红线 | `BRAND.md`／`docs/philosophy.md`／`RULES.md` |
| 三级记忆 | 根/线/产品仓 `CODELY.md` |
| 能力唯一清单（反重复先查） | `cph4/README.md` 注册表 |
| 城市正典族+48 包索引 | `gaming/FluxVerse/docs/`+`gaming/MiniGame/Design/configs/GLOBAL/` |
| 城市实况/人口档案 | `gaming/FluxVerse/world/`+`life/BigLife/census/` |
| 新机部署 | `Tools/bootstrap-machine.ps1`+`cph4/onboarding.md` |
| 治理工具（水位/自审/机队审计） | `Tools/retention-scan.ps1`/`selfaudit.ps1`/`fleet-audit.ps1` |
| 架构全景与历史审计 | `docs/audits/group-architecture-review-2026-09-27.md` |

## 5. AI 行为铁律（9 条）

1. **先读记忆再动**：开仓先读 `CODELY.md`+本文件；改前必读目标文件。
2. **宣称带证据**：完成/通过/存在必带 commit/路径/输出指针；无证据=宣称无效（`docs/governance.md` §10）。
3. **反重复+查重**：新建能力先查 `cph4/README.md` 注册表；**接令先查重**（governance §4 命令查重律——已有法覆盖=执法件非新立法）。
4. **禁跨仓写**：不写兄弟公司仓；集团零产品代码。
5. **令落台账**：CEO 原话入 `docs/orders.md`；无溯源=假令=T0 最高违规。
6. **小步快提交**：交互会话禁长脏树；无人值守只定向 add。
7. **静默律**：机制级静默——建/改计划任务唯一正门=`Tools\task-register.ps1`（强制隐藏链+读回验证）；**禁裸 schtasks/Register-ScheduledTask**（违例挂 patrol·60 秒兜底守卫在案）；开发态后台长活=pythonw/隐藏链。
8. **红线**：3D 库唯一源（禁云端生成·缺口呈 CEO 填库）；48 包商用 gate=正版采购待 CEO；密钥不入 git；真金永禁全自动；城市 UI/参观端禁金融行情视觉；服务器最小化；未来数据/跑到达标为止。
9. **拿不准**：一句问 CEO，带方案不带怨；CEO 三裁决通道=文字令/附图定案/选 A/B/C。

## 6. 变更纪律

本文件=速览+指针：目标文件改了只改指针不改结论；结论与实况冲突时**实况优先**（先改文档）；结构变更须 `docs/governance.md` changelog+溯源。

### Changelog
- 2026-10-08: **v2.0 大瘦身**（CEO 令「规则太多了，造成思考拥堵」·C-20261008-06 Phase 1·17.9KB→≤10KB）：历史沿革/案例复述/行内长文全数移出（git 史全保）——§1 组织表速查化（BigHouse 并回主表）、§3 机制表 30+长行→24 速查行（机制+节律+指针·合并审计部/本地管线/外审等入上位行）、§2/§4/§5 压缩、铁律 3 增查重；指针零删除。
- ≤v1.7：建仓至 10-07 沿革全档 git 史（组织/载体边界/美术定谳/常设化/梳理批各版本注记）。
