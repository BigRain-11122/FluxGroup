# bm-c 7×24 生产计划 v1（2026-11-21）

> 令源：CEO 2026-11-21「建立科学的计划，保证 7×24 不间断的自动化生产高质量产出，有自我迭代、优化、修复、解决问题、积累经验，把相关的智能体都建立好并常驻」。
> **本件不新立法**——它把既有机制装成一条能自转的生产线，并写明每一环用的是哪一个既有件（CEO 2026-11-21 另一令：规则工作流不要推翻，能用就用）。

---

## 一、架构（四席一环，全部挂在既有件上）

```
        ┌──────────── 工作银行 cph4/fleet/work-bank/bm-c-gpu-bank.json ────────────┐
        │  jobs[]: id / cmd / deliverable / accept / status(pending|claimed|done|blocked) │
        └───────────────▲──────────────────────────────────┬───────────────────────┘
                        │ 写 pending                         │ 认领 pending
        ┌───────────────┴──────────┐          ┌────────────▼─────────────────────┐
        │ 播种 bmc_prod.py seed    │          │ 生产者席 BmcIdleGuard（既有件）  │
        │ （生产计划→jobs，幂等）   │          │ 闲置≥10min→认领→隐链点火          │
        └──────────────────────────┘          └────────────┬─────────────────────┘
                                                           │ Popen（无窗·脱离会话）
                                          ┌────────────────▼──────────────────────┐
                                          │ 执行：drama_ep_chain.py --stages all  │
                                          │ plan→kf→i2v-plan→i2v→audio→asm→qc     │
                                          └────────────────┬──────────────────────┘
                        ┌──────────────────────────────────▼─────────────────────┐
                        │ 收口员席 Bmc-ProdFinalize（10min）                       │
                        │ 产物+闸 → done │ 无产物无进程 → pending(≤3) → blocked    │
                        │ 每步写 production/LEDGER.jsonl                          │
                        └──────────────────────────────────┬─────────────────────┘
                                                           │
                        ┌──────────────────────────────────▼─────────────────────┐
                        │ 自省员席 Bmc-ProdIterate（每日 05:07）                    │
                        │ 耗时/产能/失败聚类/迭代建议 → ITERATION-YYYYMMDD.md       │
                        └────────────────────────────────────────────────────────┘
   旁路：审稿员席 drama_prompt_critic（本地 LLM·num_gpu=0 纯 CPU，与烧片并行）
   旁路：FluxGroup-ComfyGuard-bmc（ComfyUI 挂了 3 分钟自愈）· Bmc-AutodriveGuard（心跳/死批）
```

**为什么这样切**：既有的 `bmc_idleguard.py` 只负责"点火"，从不收口；`bmc_prod.py` 只补"对账+自省"，
**不复写执行器**。一台机器只有一个 GPU 认领入口，天然不会双烧。

---

## 二、节律表（常驻，无需点名）

| 席 | 任务名 | 节律 | 干什么 | 状态 |
|---|---|---|---|---|
| 生产者 | `BmcIdleGuard` | PT10M | 闲置≥10min 且无 GPU 活 → 认领首条 pending → 点火 | **已启用** |
| 收口员 | `Bmc-ProdFinalize` | PT10M | claimed→done/requeue/blocked + 台账 | **已注册·fire 实测 result=0** |
| 自省员 | `Bmc-ProdIterate` | 每日 05:07 | 指标+失败聚类+建议 | **已注册** |
| 守卫 | `FluxGroup-ComfyGuard-bmc` | PT3M | ComfyUI 假死自愈（既有） | Ready |
| 监管 | `Bmc-AutodriveGuard` | PT10M | GPU 空转心跳/死批重启（既有） | Ready |

> 三条新任务均走 `Tools/task-register.ps1` 正门（InvisibleRunner 隐链）。非提权下 S4U 被拒 →
> InteractiveToken 降级 + 自动入 `Tools/task-s4u-backlog.md`；**代价=注销后不自启**，提权后转换即补。

---

## 三、质量门（一道不加、一道不减）

| 环节 | 门 | 出处 |
|---|---|---|
| 烧前 | `preflight_gate.guard(profile="drama")`——①首帧②token③零否定④场景锚 | `PREFLIGHT-GATE-v1`（同一道闸，不另开） |
| 关键帧 | 伪文字/画风漂移人审抽检 | `DRAMA-PRODUCTION-SYSTEM-v1` D3 |
| i2v | 崩坏六检（morph/伪文字/物理/匀速/首帧保真/速度线） | 同上 D4 |
| 成片 | `drama_quality_gate.py` 七条（竖屏/帧率/音轨 LUFS/时长/3s 钩/镜长/字幕） | 同上 D8 |
| 字幕 | `subs_qc.py` 八条（17 字/停留/CPS/标点/时间码/行数/错字/一致性） | `QC-20261119` 判例 |
| 收口 | accept 字段机核（如 `verdict=PASS`） | 本件 |

**判据铁律**：accept 不过 = 不算交付（DONE 不等于交付）。闸红的东西不给人看。

---

## 四、自我迭代（每晚出报告，只建议不立法）

`bmc_prod.py iterate` 每晚产出 `production/ITERATION-YYYYMMDD.md`：

1. **面**：银行总活 / 状态分布 / 已完成 / 判死；
2. **指标**：单集耗时均值、24h 理论产能（按均值，扣让路窗）；
3. **失败聚类**：`no-deliverable` / `gate-fail:*` 计数；
4. **建议**（按聚类给）：
   - `no-deliverable` ≥2 → 先查 SKIP 判据与旧件归档（10-24 判例）
   - 出现 `gate-fail` → 提示词层先过 critic 再烧
5. **边界**：判死件需人工/主控裁定，**禁自动放宽闸**（放宽闸=把闸变成噪声源，v730 判例）。

经验积累走既有 `EXPERIENCE-LEDGER` 与 `drama-dept-v1/LEDGER.md`；本件台账
`production/LEDGER.jsonl` 是机读流水（done/requeue/blocked/iterate 四类事件）。

---

## 五、修复与问题解决（失败梯）

| 症状 | 自动动作 | 升级 |
|---|---|---|
| 进程死、无产物 | 置 pending，retries+1（≤3） | 3 次后 blocked + 原因入台账 |
| 产物在、闸不过 | `gate-fail:<回执>` 入台账，重排 | 同上 |
| ComfyUI 假死 | ComfyGuard 3 分钟自愈 | 连续失败→blocked |
| GPU 空转 | IdleGuard 10 分钟认领 | 银行空 → 日志 `PRODUCER VIOLATION`（曝光而非静默） |
| 让路窗 | `machine-state.flag` 含 paused → 零动作 | — |

---

## 六、产能与预算（实测基线，不是估算）

| 项 | 实测 |
|---|---|
| 漫剧单集（21 镜·480P 验证档） | 约 60 分钟（KF 20s/张 + i2v 155s/镜 + 装配闸） |
| 单机 24h 理论 | 约 20 集（不含让路窗；实际按 60–70% 计 ≈ 12–14 集） |
| 768P 正片档 | 约 2.5 倍耗时（按需另批，不占验证档队列） |
| 云端 | 默认不参与（CEO 令：云端只作辅助） |

---

## 七、人的位置（保留面）

- **不改闸、不放宽判据**、对外发布、花钱 —— 均不在自动化射程内；
- 判死件（blocked）需人裁定，自动只到"重试 3 次"；
- 显存相冲（LLM vs 烧卡）由纪律处理：烧卡时 LLM 走 `num_gpu=0` 纯 CPU。

—— bm-c · 2026-11-21
