# 开工条件（15 条线）2026-11-19

证据源：`cph4/fleet/state/lines.json`(17:00:04, census.py 生成) / `cph4/fleet/lanes/*.json` / `cph4/fleet/CAPABILITIES.md` / `cph4/fleet/ISLANDS.json`(missing_nodes=bm-a,bm-b,bm-c,bm-d) / `cph4/fleet/BLOCKER-LOOP.md` / `cph4/fleet/state/ceo-queue.json`
本机现状：bm-m 在线(hb 1s)，能力 `cpu,ios-build,text,llm,audio,tts`，本地模型 qwen3.5:2b/4b/9b-mlx；**无 GPU、无 i2v/KF/render/backtest**（CAPABILITIES.md）。故 GPU 重活一律等机。

## 一、逐线开工条件（一条线一行）

| # | 线 | 产出年龄/状态 | 判定 | 在哪台机器 | 前置条件 | 第一件产物 | 判据 |
|---|---|---|---|---|---|---|---|
| 1 | bigstream-mv | 98.8h ACTIVE | **等他机** | bm-a 或 bm-c（`i2v768,kf768`） | bm-a 仓库已分叉（head 93d68447 非 origin/main 祖先，BLOCKER-LOOP.md NODE-REPO-DIVERGED），必须先对齐；bm-c 需开机+心跳 | `mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v`（BLOCKER-LOOP.md 记为 ARTIFACT-MISSING，已重开假完成卡） | 该文件落盘且过质量席（ACCEPTANCE-BOARD.md 口径） |
| 2 | bigstream-drama | 16.9h ACTIVE | **本机可干** | bm-m | 无；`drama-dept-v1/subs/_asr-sync-2026-11-19.json` 已在盘 | `drama-dept-v1/subs/_qc/` 逐集 SRT 复核清单（时间轴/字数/静音段） | 至少 3 集 SRT 全项过 QUALITY-SPEC-v2.md 且零缺句 |
| 3 | bigstream-duanju | 478.3h PARKED | **缺前置物料** | — | `cph4/fleet/duanju-dept-v1` 仅 2 文件，无选题/剧本/素材；需内容侧给 1 份选题单 + 素材目录 | 选题-素材盘点表 | 盘点表覆盖 ≥10 集且每集有素材路径 |
| 4 | bigstream-shortvideo | 411.8h PARKED | **等他机** | bm-c（`render`） | bm-c OFF (hb 54454s)；需 1 份可复用的 remix 源素材清单 | 首条 remix 成片 | 成片过质量席（非台账） |
| 5 | biggame | 383.7h ACTIVE | **本机可干** | bm-m | 无（截图取图受 2026-10-28『不许自动跑游戏包』令约束，见 ceo-queue.json biggame 项，属人工决策部分，本机只做不依赖该令的一半） | 36 款隐私政策 + 提审台账补登 | SUBMIT-PACK 里『隐私政策』『提审台账』两类缺件归零（ceo-queue.json accept 原文） |
| 6 | fluxverse | 385.9h ACTIVE | **本机可干** | bm-m | `gaming/FluxVerse/*` 全 missing，但 `state/city-state.json` 17:00 仍活；仅做规则/索引 | CITY-FACES-v1.json 字段一致性校验报告 | 报告列出所有不一致字段且 0 未解释项 |
| 7 | bigmoney | 364.9h ACTIVE | **等他机** | bm-d（`backtest`） | bm-d `enabled=false`、hb 1120336s(13天)、lanes/bm-d.json ts=11-06；需先启用+上线 | 首份回测净值曲线 JSON（`quant/bigmoney/results/`） | 回测可复现（同参两次结果差 <1e-6）且过质量席 |
| 8 | bigdomain | 383.6h ACTIVE | **本机可干** | bm-m | `domain/BigDomain` 目录 missing；仅做漏斗规则/文案 | FUNNEL-v1.json 漏斗步骤与文案终稿 | 每步转化定义有唯一字段口径，无重复步骤 |
| 9 | bigcompute | 383.6h ACTIVE | **本机可干** | bm-m | 无；CAPACITY-LEDGER-v1.json 在盘 | 产能台账对账（台账 vs CAPABILITIES.md 实况） | 5 节点差异逐条列出且 0 未解释 |
| 10 | biglife | EMPTY drift | **待裁** | — | `life/BigLife` 无盘、`life/BigLife/census` missing（lines.json drift=true） | — | **待裁**：biglife 是开新线还是从 15 线名录删除？ |
| 11 | bighouse | NO-DISK PARKED | **缺前置物料** | — | `house/BigHouse` 不存在，无章程无素材，也无上游供给方登记 | — | 缺：线章程 + 素材来源各一份，谁给未判 |
| 12 | car-gaming | 405.1h PARKED | **缺前置物料** | — | `gaming/MiniGame/09_吸嘟嘟GimmeAll/GimmeAll/Tools` missing；本机有 ios-build 但无工程目录 | — | 缺：GimmeAll 工程/Tools 目录由哪台机提供，未判 |
| 13 | recon | 292.4h ACTIVE | **本机可干** | bm-m | 无；`recon-dept-v1` 23 文件在盘 | recon 情报条目去重+分级索引 | 索引条目全部可回溯到原文件路径 |
| 14 | fleet-ops | BOOKKEEPING drift | **本机可干** | bm-m | 无；canary 529 文件 15:57 在盘 | 心跳/判定口径复核表（含 bm-a 分叉、bm-d disabled） | 5 节点状态与 lanes/*.json 逐一致，0 冲突 |
| 15 | asset-lib | 98.2h ACTIVE | **本机可干** | bm-m | 无；`state/asset-dedupe.json`(93KB) 与 queue-receipts 2968 在盘 | 资产去重结果转人工可读清单 | 重复组数收敛且每组保留项有理由 |

合计：本机可干 8（#2,5,6,8,9,13,14,15）｜等他机 3（#1,4,7）｜缺前置 3（#3,11,12）｜待裁 1（#10）

## 二、本机可立刻开工的三件

1. **drama 字幕 QC**｜工具：`ls/awk` 只读扫 `cph4/fleet/drama-dept-v1/subs/` + 本地 qwen3.5:4b 审文本｜产出：`cph4/fleet/drama-dept-v1/subs/_qc/QC-20261119.md`｜判据：≥3 集全项过 QUALITY-SPEC-v2.md，零缺句｜预计 40 min
2. **biggame 提审缺件清零（不依赖放行令的那半）**｜工具：`grep -r` 扫 `cph4/fleet/game-v1/SUBMIT-PACK-20261119.json` + 本地模型起草｜产出：`cph4/fleet/game-v1/PRIVACY-TEMPLATE-36.md` + 台账补登表｜判据：隐私政策 36/36、台账缺件归零｜预计 70 min
3. **机队口径复核（先修判定再派卡）**｜工具：`cat cph4/fleet/lanes/*.json` 与 `CAPABILITIES.md`、`ISLANDS.json` 三方比对｜产出：`cph4/fleet/FLEET-RECONCILE-20261119.md`｜判据：5 节点状态逐一致、bm-a 分叉与 bm-d disabled 各有明确处置｜预计 20 min

## 三、人工决策未定（一句话各一条）
- biglife：开新线还是从名录删除？（lines.json drift=true、EMPTY）
- biggame 截图取图是否放行 2026-10-28『不许自动跑游戏包』令？（ceo-queue.json need_ceo）
- bm-d 回测机是否重启启用？（enabled=false、13 天无心跳）
- bigstream-duanju / shortvideo 两条 PARKED 线是否复线？
