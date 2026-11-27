# 研究创新部门章程 v1（2026-11-02）

> CEO 令：每个子公司成立对应的研究创新部门，专管本专业的业务创新、调研、赋能、工具更新；
> 实验室负责更整体、更宏大的生产力更新。
> 本件只写"机器能判的"，不写口号。原文法条不复制，指针见 §8。

## 0. 一句话

```
两层创新
├─ 组级创新席（每子公司一席）：只改自己业务的工序/配方/工具
└─ 集团实验室（一席）    ：只改公共生产力，并把组级成果上收成通用能力
计分只用一件事：被产线真的采纳了多少（不是产出了多少文档）
```

## 1. 两层与边界（机器可判：I18）

**组级创新席**

- 席位：内容席（MV / 短剧 / 漫剧 / 切片）、游戏席（Biggame）、策略席（BigMoney + BigDomain）、城市席（P2，暂挂内容席代管）
- 干什么：本业务的调研与拆解、题材/玩法/工序创新、本组提示词与配方、本组工具改造与更新
- 能写哪：`cph4/fleet/ri/<group>/`、`Tools/ri/<group>/`
- 不能碰：`Tools/fleet/*`（平台核心）、`PRODUCTION-QUEUE.jsonl`（I7 单写入口）、契约与断言、主环阶段表

**集团实验室**

- 干什么：整体与宏大的生产力更新——契约、闸、调度、模型路由、资产、一屏；以及把组级重复造的工具合并成平台能力
- 能写哪：`Tools/fleet/`、`cph4/fleet/lab/`
- 不能碰：`products/*.yaml` 正文（组 owner 改，实验室只提议）

> 边界不是讲道理，是路径白名单：组级席的 `writes` 出现平台路径即 I18 红。

## 2. 一条活的唯一状态机

```
IDEA ──► SCOUT ──► PROBE ──► ADOPTED
  │         │         │
  └─────────┴─────────┴──► KILLED（超期自动，不看解释）
```

| 阶段 | 进入条件 | 机器判据 |
|---|---|---|
| SCOUT | 写清假设 + 证据来源 | `hypothesis` 非空、`sources` ≥1 |
| PROBE | 有可跑命令或可看产物，且跑通过一次 | `probe.cmd` 与 `probe.evidence` 在盘 |
| ADOPTED | 产线真的用了它 | `adoption.ref` 指向卡号/回执 |
| KILLED | 超期、被证伪、或已无意义 | `kill.reason` 非空 |

铁律：**只写文档、只写规则、只做汇报 = 不进任何阶段**（补文档不算产出）。
PROBE 45 天内没被采纳 → 自动 KILLED，禁止"继续调研"。

## 3. 记分（唯一 KPI）

```
采纳率 = ADOPTED ÷ (ADOPTED + KILLED)     窗口 45 天
组级席 ≥ 50%   ｜   实验室 ≥ 80%（沿用总管阶段 4 门槛）
连续 2 个窗口不达标 → 该席降为"只读观察"，停止派新活
```

产出量、简报字数、调研页数、工具数量一律不进记分。

## 4. 节奏（按天算，但只设三档）

```
每天  ｜不设日报（反门槛）
每周  ｜每席 1 份扫描简报 ≤1 页：事实 3 条 + 可执行建议 3 条 + 建议对应的 probe
每2周 ｜一次"采纳或杀掉"清算（ri_dept.py settle，机器判）
每月  ｜实验室 1 次生产力上收：把组级重复造的工具合并进平台
```

## 5. 供给规则（治"队列空 = 在等"）

- PROBE 必须写成可执行卡的形状：`cmd` + `deliverable` + `accept`，但**不直接写队列**（I7）
- 落到 `cph4/fleet/ri/PROPOSALS.json`，由派单方（night_fill / master_agent）择取
- 队列空而 PROPOSALS 有 READY 项 = 流程缺陷，不是"没活"

## 6. 一进一出

- 新开一席必须在 registry 写 `supersedes`：被它吸收的旧机制/旧部门，缺则 I17 红
- 例：内容席吸收 `recon-dept-v1` 的选题调研段；实验室吸收散落的工具打磨
- 席位连续 2 窗口不达标 → 先合并或撤销，再谈新开

## 7. 机器可判（三条断言）

| 断言 | 内容 | 红了怎么办 |
|---|---|---|
| **I17** | active 产品组都有席位、登记字段齐全（owner/lane/scope/writes/cadence/kpi/supersedes） | 补齐登记，不许口头声明 |
| **I18** | 组级席未越界写平台路径；`forbid` 不出现在 `writes` | 该席产出作废，改由实验室做 |
| **I19** | 不空转：简报 >7 天无更新、IDEA/SCOUT >14 天、PROBE >45 天 | 自动 KILLED 或当场补 brief |

## 8. 工具与指针

```
Tools/fleet/ri_dept.py
├─ status   看四席：席位/阶段分布/采纳率/最老未动工单
├─ check    跑 I17/I18/I19（flux_check 直接调用同一份逻辑）
├─ new      开一张工单（必须给假设与来源）
├─ brief    写本周简报（落到 cph4/fleet/ri/<group>/briefs/）
├─ probe    升到 PROBE（校验 cmd/evidence 真在盘）
├─ adopt    升到 ADOPTED（必须给 adoption.ref）
├─ kill     杀掉（必须给原因）
├─ settle   两周清算：超期自动 KILLED
└─ feed     产出 PROPOSALS.json 供派单方读取
```

- 登记表：`cph4/fleet/ri/registry.json`
- 工单：`cph4/fleet/ri/<group>/tickets/<id>.json`
- 简报：`cph4/fleet/ri/<group>/briefs/BRIEF-<date>.md`
- 上级不变量：`Tools/fleet/flux_check.py`（I17-I19）
- 组织指针：`cph4/fleet/ORG-20261102.md`、`cph4/fleet/products/*.yaml`
- 意图模型：`cph4/fleet/CEO-INTENT-MODEL-20261102.md`