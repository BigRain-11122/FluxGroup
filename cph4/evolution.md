# Evolution — 集团自进化治理体系（CPH4 进化引擎）

> AI 时代的治理不是写完就死的制度，而是一个**会自己进化的系统**。
> 法 = 版本化数据（git，changelog 是唯一立法史）；AI = 立法起草人 + 执法巡检员；CEO = 宪法级唯一裁决人。
> 本章程由 CEO 令设立（2026-09-23：「引入 AI 时代最先进最牛逼最能自我进化的集团化治理体系」），属 CPH4 Labs 旗舰机制。

## 1. 进化循环（四步 · 周频+触发式）

```
① 感知 Sense      扫三级记忆 + 两公司坑录与队列 + 文档漂移 + 登记簿漂移 + 悬置项
② 提案 Propose    向 cph4/evolution-ledger.md 追加提案（五字段：现象/证据/建议/风险级/影响面）
③ 裁决 Adjudicate 按分级立法权处理（§2）
④ 立法+瘦法       改法+changelog；每季度附「法熵审视」——哪条法过时/可合并/可退役
```

- 节律三源：**周进化轮**（OS 任务 `FluxGroup-EvolutionTick`，周日静默跑）+ **CEO 会话即时轮**（任何与 CEO 对话的会话可随时执行四步）+ **触发式**（重大坑/事故即入提案）。
- 进化轮 = 无头静默轮：禁提问禁交互，产出只落台账与法律文件。

## 2. 分级立法权（谁可以动什么法）

| 级 | 对象 | 立法权 |
|---|---|---|
| **T0 宪法** | `BRAND.md` / `docs/philosophy.md` / `RULES.md` / `docs/architecture.md` 角色与运营原则 / `docs/governance.md` 铁律 | **CEO 签字才动**——AI 只起草提案 |
| **T1 治理** | `governance.md` 非铁律条款 / 产品登记簿拓扑 / 开线收线 / 涉密与账号事项 | **CEO 一句话裁决**——提案入台账待裁 |
| **T2 机制** | 线 README 实况刷新 / docs 与 cph4 注册表漂移修正 / 机制接线 | **AI 可直接落地** + changelog + 标注「AI 立法·否决窗 7 天」（CEO 随时否决，git 即回滚通道） |
| **T3 数据** | `evolution-ledger.md` 台账 / 导航注释 | AI 全权，随改随记 |

- 跨仓写禁令在本体系内依然成立：进化轮对产品仓**只读**；产品仓内部问题=提案**转办**（台账注「转办@公司」，由该公司自己的循环消化）。

## 3. 瘦法律（防法熵）

- 立新法优先改旧法，**禁法上叠法**；每季度进化轮必附法熵审视（合并/退役先例=X035 范式同源）。
- 法条数量是负债不是资产——治理层文档总数超限（>20 件）即触发瘦身审视。

## 4. 台账

`cph4/evolution-ledger.md` = 唯一进化台账（提案区 + 裁决区 + 进化轮报告区）。任何机器任何会话皆可追加提案；裁决记录必须带 CEO 原话或日期；状态：open / applied / rejected / transferred / self-healed。

## 5. 周进化轮（载体）

```
Windows 任务 FluxGroup-EvolutionTick（周日 09:17）
  → cph4/evolution-tick.ps1（纯 ASCII·单实例锁 120min）
  → cph4/evolution-tick-prompt.txt（中文 mandate，UTF-8 外置）
  → 无头 codely 轮（日志=.codely-cli/evolution-last.log）
```

- 集团层除本进化轮外不建任何高频循环（`governance.md` §8 例外条款）。
- push 被拒=pull --rebase 重试一次，再拒顺延下轮（X128-lite 精神）。

## 6. CEO 接口（你只需要做三件事）

1. 周轮报告末尾自动汇总「**待裁决清单**」——对 T0/T1 提案说一句话：准 / 改 / 驳。
2. T2 已由 AI 自主落地并标注否决窗——不满意的直接说，git 秒回滚。
3. 想立即进化就说一句「**跑一轮进化**」。
