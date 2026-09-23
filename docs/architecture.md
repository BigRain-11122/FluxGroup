# Group Architecture

## Parent
超体宇宙集团 / FLUX Group

## Governance（核心团队）

### Operating principles（运营原则）
1. **业务决策：Jason 随时定。** 不搞流程、不等人、不开会走形式。业务线怎么走，Jason 一句话定。
2. **企业文化：慢慢打磨，不急着执行。** `philosophy.md` 现在只是沉淀方向，不是 KPI、不是考核、不是马上要落地的清单。它会被长期修改、增删、修正。任何 AI 或人不得拿它当执行要求去 push 团队，也不得急着"落地文化"。
3. **运转模式：AI 赋能自治（CEO 宣言 2026-09-23）。** 集团 = 一名 CEO + AI 劳动力 + 机队。CEO 只做决策、发号施令、定方向；子公司由各自 OS 循环自动运作、运转、迭代，无人值守推进。CEO 输入面 = 方向变更、P1 新方向署名、红线裁决、资源调配；其余一切由 AI 在各自边界内闭环（`docs/governance.md` §4）。

### Roles

| 角色 | 中文 | English | 职位 | 分管 |
|---|---|---|---|---|
| 创始人 | 孙君晟 | Jason Sun | Founder & Group CEO | 统管全局，战略与最终决策 |
| 联合创始人 | 许瑛琦 | Qiqi Xu | Co-founder & Chief Brand & Culture Officer | 品牌、文化、媒体线、人文内核 |
| 原点继承人 | 孙弋杰 | Rain Sun | Origin Heir / Chief Future Officer | 集团未来与初心的象征，品牌精神符号 |

### Notes
- Jason owns the whole group. No major move without his sign-off.
- Qiqi owns the soul of the group: brand voice, culture, media line, and the human side that philosophy.md protects.
- Rain (Rain = 大雨 = the origin name) is the group's future and its conscience.
  He does not run operations now; he is the reason the group must outlive any quarter.

## Business lines

- CPH4 Labs (CPH4 实验室) — AI research core + FluxVerse future-planning lab（元宙未来规划与发展·2026-09-23 CEO 令），reports to Jason（集团层地址 = `cph4/README.md`，横切研发层）
  - FLUX Gaming (超体游戏)
  - FLUX Quant (FLUX 量化)
  - FLUX Media (超体自媒体) — cultural lead by Qiqi

## Relationships
- FLUX = the flow (top level).
- CPH4 Labs = the engine that powers the flow.
- Three lines run on the engine, each on one kind of flow.
- Philosophy is guarded by Qiqi, owned by the family.

## System architecture（系统三层结构 · 2026-09-23 立）

```
集团治理层  FluxGroup 仓（品牌/文化/规则/治理契约/线 README/集团记忆）
    │  .gitignore 隔离 · 互不嵌套 · 各自独立 remote
    ├── gaming/（线工作区）──> Biggame 产品仓 MiniGame.git（master）
    ├── quant/ （线工作区）──> BigMoney 产品仓 BigMoney.git（main）
    ├── media/ （线工作区）──> BigStream 产品仓 BigStream.git（main·remote 待 CEO 建）
    └── cph4/  （CPH4 Labs 集团实验室 · 元宙规划 · 横切层）
```

- 治理细则与产品登记簿：`docs/governance.md`。
- 三公司均为「一人 + AI 劳动力 + 机队」形态：
  - Biggame = MiniGame* 任务群（10 分钟 tick 引擎 + 审计/看板/风线/保温），08 号多机分治；
  - BigMoney = Bigmoney-IterationLoop 10 分钟自迭代（bm-a 开发节点 + bm-b 回测节点，fleet 协议 + 预注册科研范式）；
  - BigStream = AI 内容生产线（M0 选题→M6 复盘七段·会话驱动；P0-P2 阶段不建循环，常态后按需装——其 PLAN.md §8）。

## Machine fleet（机队 = 集团共享基础设施）

| 机 | 角色 |
|---|---|
| bm-a（DASHENG·32 核） | BigMoney 开发节点 ∥ Biggame 主机（A 机） |
| bm-b（16 核） | BigMoney 回测/数据节点（Money02 宿主） |
| Biggame B/C 机 | 游戏分机（08 号协议：认领制 + X128 机器分支） |

- 双公司同机纪律与互见层：`quant/bigmoney/fleet/README.md` §10（集团层引用，不重复立法）。
