# 硅基地球 · 模块地图

> 由 `tools/world_ops.py doc` 生成，**不要手改**。改模块请改脚本里的 MODULES，并登记到 TASKS。

状态：`empty` 未开工 / `building` 在写 / `usable` 能跑 / `stable` 稳定

| 域 | 模块 | 名称 | 状态 | 独占写 | 下一步 |
|---|---|---|---|---|---|
| 平台 | `m-f1-contracts` | 契约与数据 | usable | — | 给事件补 causes 的环检测规则 |
| 平台 | `m-f2-service` | 服务与 API | empty | modules/m-f2-service/src/ | 先做 /today 与 /region/:id |
| 平台 | `m-f4-qa` | 质量闸 | building | tools/world_ops.py | 把 validate 扩成负控自测（self-test） |
| 平台 | `m-f5-onboard` | 协作与接入 | usable | START-HERE.md<br>MODULES.md<br>TASKS.json<br>HANDBOOK.md | 把 claim 规则写进 TASKS 与 TEAM |
| 世界 | `m-w1-regions` | 地理与区域 | usable | modules/m-w1-regions/data/regions.json | 补地理邻接（谁挨着谁） |
| 世界 | `m-w2-clock` | 时间与事件 | usable | modules/m-w2-clock/data/time.json<br>modules/m-w2-clock/data/events.jsonl<br>modules/m-w2-clock/engine.py<br>modules/m-w2-clock/intervene.py | 从一天一条升级为八拍一日 |
| 世界 | `m-w3-settle` | 状态结算 | usable | modules/m-w3-settle/data/state.json<br>modules/m-w3-settle/settle.py | 把年龄/人口变化也纳入结算 |
| 世界 | `m-w4-history` | 历史与纪年 | empty | modules/m-w4-history/data/history.json | 先做「纪年」：一件大事之前的都归旧纪 |
| 人 | `m-p1-census` | 居民与户籍 | usable | modules/m-p1-census/data/people.json | 从 27 扩到 100，保持每人一件未了的事 |
| 人 | `m-p2-memory` | 记忆链 | usable | modules/m-p2-memory/data/memory.json<br>modules/m-p2-memory/data/seed.json<br>modules/m-p2-memory/derive.py | 记忆必须可删可重建；种子独立存 seed.json |
| 人 | `m-p3-bonds` | 关系与相助 | empty | modules/m-p3-bonds/data/bonds.json | 每次 help 事件产生一条关系，欠与还分开记 |
| 人 | `m-p4-behavior` | 需求与行为 | empty | modules/m-p4-behavior/data/behavior.json | 先做规则版：需求满足度决定动作 |
| 镜 | `m-r1-intake` | 现实采集 | empty | modules/m-r1-intake/data/raw.jsonl | 先做手工录入版 |
| 镜 | `m-r2-translate` | 翻译规则 | empty | modules/m-r2-translate/data/rules.json | 先定 20 条对照 |
| 表现 | `m-v1-globe` | 地球渲染 | empty | modules/m-v1-globe/src/ | 复用 CityWeb 的 three.js 栈 |
| 表现 | `m-v2-city` | 城市渲染 | empty | modules/m-v2-city/src/ | 把 CityWeb 接成一个区 |
| 表现 | `m-v3-interact` | 交互与介入 | empty | modules/m-v3-interact/src/ | 先做「点开一个人，看到他的记忆链」 |
| 表现 | `m-v4-audio` | 声音与氛围 | empty | modules/m-v4-audio/data/ | 先做一条广播 |
| 生意 | `m-b1-output` | 内容与分发 | empty | modules/m-b1-output/out/ | 先出第一条 |
| 生意 | `m-b2-citizen` | 身份与入籍 | empty | modules/m-b2-citizen/data/ | 先定三档身份与权限 |
| 生意 | `m-b3-archive` | 保管 | empty | modules/m-b3-archive/data/ | 先定「存什么、怎么找得到」 |
| 生意 | `m-b4-billing` | 结算与定价 | empty | modules/m-b4-billing/data/ | 先定「看免费、动收费」的分界 |

## 依赖顺序（不许跳）

契约 → 区域/人（静态定义）→ 时间与事件（世界会动）→ 状态结算（世界会变）
→ 记忆/关系（人会有过去）→ 表现（能被看见）→ 交互（能被进入）→ 生意（能被付钱）

## 铁律

1. 一模块一目录一 owner；**只写自己声明的 writes**
2. 同一路径只能有一个 writer（validate 会查）
3. 契约只加不改义；改契约走总控
4. 每模块必须能单独跑、单独验（run 与 verify 非空）

