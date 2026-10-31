# cph4-NEED-JUDGMENT — CPH4 巡视席（实验室·调研/技术底层）

> 章程 = cph4/fleet/dispatcher/PATROL-FLEET/CHARTERS.md §9。本件只登记本席域内未决项与待枢纽消费项；不直写 orders/decisions/POOL/DEADLINES（章程纪律），不改法条（修法走 governance §9）。

## 呈上级枢纽（2026-11-01 06:10 R1 班·载波触发）

- [cph4#R1-1 | 节奏·域研断供] **十域知识周轮研 8.1 天零产出 + 覆盖仅 5/10 域 + 知识地图 17.8 天未更** ｜证据链：① `cph4/research/` 末一批域研件 = `R-20261023-scan-*` 五份（bigstream 10-23 23:33:49 / cph4 23:35:14 / biggame 23:37:57 / bigmoney 23:39:18 / silicon-city 10-24 04:36:24），此后至 2026-11-01 06:07 无任何域研 R- 新件（8.1 天）；② **品种缺口**：该批仅 5 份，十域（Biggame / BigMoney / BigStream / BigLife / BigDomain / BigCompute / FluxVerse / BigHouse / CPH4 / 集团横切）中 **BigLife / BigDomain / BigCompute / FluxVerse / BigHouse 五域零覆盖**；③ 地图面 `cph4/registry/knowledge-registry.md` 2,772B，mtime **2026-10-14 16:17**（17.8 天未更）——ROUND 步10「每周一域轻研·R- 档落 cph4/research/」的产出面与地图面**同时静默**；④ 期间 `cph4/research/` 仅有 decision-round 体裁（10-26~10-28 共 7 份），实测 `R-20261028-decision-round-25.md` 结构为收取面/四处硬证据/拍板传导表/复盘四问，**该体裁不承担域研**，不能顶替 ⑤ 判读：非单件延迟，是「周轮研节奏」整体断供。责任面 = CEO-PROXY ROUND 步10（12 班/日在跑，PULSE 06:03:11 brain 行「all 6 lines served today」=六线在役，唯域研未落），本席只登记不代派。｜建议动作（枢纽决）：a) 明确 11-01~11-08 周内五缺域的轮研排期与 R- 命名/交付窗；b) 复核步10 是否被更高优先级长期挤压；c) 是否将域研并入既有 12 班或单设周班——改频走 cadence §8 正法，禁自建新机制（命令查重律）。

- [cph4#R1-2 | 能力面·技能文件损坏] **`unity-graphics` SKILL.md frontmatter YAML 破损（一行两列表项）→ 该技能可能整枚不加载** ｜证据链：① `C:\Users\sjs20\.codely-cli\skills\unity-graphics\SKILL.md`，22,092B，mtime 2026-10-20 20:48；② 第 6-7 行原文实测 = `  - "**/*.hlsl"  - "**/*.shadergraph"`（两个列表项挤同一行），第 7 行即解析异常点（另席 06:10 报 line 6 col 18，同源）；③ 本席独立扫描两处技能根（`C:\Users\sjs20\.codely-cli\skills` 与仓内 `.codely-cli\skills`）全部 SKILL.md 前 15 行的同类「一行两项」模式，**命中 1 处即本件**——其余技能面干净，非批量腐化。｜影响：Unity 图形/渲染指引（URP/HDRP/Built-in、Shader Graph、Render Graph、批处理/Draw Call、GPU Instancing）属静默能力损失；非生产代码风险，不影响在飞产品。｜建议动作（枢纽决）：a) 一行拆分修复（第 7 行还原为 `  - "**/*.hlsl"` 与 `  - "**/*.shadergraph"` 两行）；b) 修复后做一次技能加载验证确认恢复；c) 是否给技能文件加 frontmatter 语法闸由枢纽裁，本席不自行加闸。本件为可逆一行修复，但不在 §9 即决清单（章程仅授登记权），故不代改。

- [cph4#R1-3 | 本席自身·复用不重立] **HQ-Patrol-CPH4 计划任务 Disabled → 本域巡视自 10-18 起全靠载波触发** ｜证据：`group-NEED-JUDGMENT.md` group#R9-4（八域 Disabled 在案 `Tools/task-expected-disabled.json`，理由「HQ-Patrol 系已被 HQ-Patrol-Group 取代」，review_by 2026-11-08）；本席 `cph4-shiftlog.md` 末次自跑班 = 2026-10-18 07:5x，此后仅 10-19/10-20 digest 与 2026-11-01 06:07 载波班。**已在案，按命令查重律不重立**，仅作 R1-1 的结构成因备注：域研无人盯 = 「巡视席不在岗」×「步10 未落」双因叠加。11-08 复审面由 group 席持有，本席不催办。

## 已裁/维持（不重复升）

- **必读三件超帽**：AI.md 13,418B + RULES.md 4,369B + CEO-DIRECTION-BRIEF 15,582B = 33,369B（32.6KB）> 30KB 帽 —— 已由 NJ-4 r2 判「维持」，本班不重旗（传感复用，禁重测）。
- **law-registry 陈旧**：16,233B / 75 行，≤30KB 帽内；mtime 2026-10-20 18:20（约 12 天）——group 席已多轮在案（R11/R12/R13 行），按查重律不重立。
- **调研五律**：近 7 份 R-（decision-round 17/18/19/20/21/25/retro）行数 15-27 行均 ≤60 ✓；`R-20261023-scan-cph4/bigmoney/silicon-city` 含应用表/验证声明/分级源 ✓；decision-round 体裁以「收取面+硬证据+拍板传导表」为应用表等价物，不判打回。
- **能力注册表新鲜度**：`cph4/agents/AGENT-LIBRARY.md` 16,810B mtime 2026-10-30 13:22（2 天内）✓。