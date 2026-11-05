# 24h 无人值守自动化系统 v1（2026-11-05·契约正身）

> 令源：CEO 2026-11-05「打造自动化的系统，全面合理使用本地和云端算力，无人监管 24 小时自动化推进，确保高效和科学、质量」。
> 阈值唯一来源=`cph4/fleet/AUTONOMY-CONFIG.json`（代码内禁再写字面量）。
> 本件的定位：解释层与验收判据。机读口径以配置为准，配置变则本件随改。

## 一、这套系统治什么（2026-11-05 实测病灶）

| 病灶 | 实测证据 | 治法 |
|---|---|---|
| 假绿：记账被当产出 | fluxverse/biglife 显示 0.1h，证据是 `state/city-state.json` | census 只认真实产物，记账目录单列 BOOKKEEPING |
| 摸鱼：心跳≠干活 | bm-a/bm-b 4.2h、bm-c 17.5h 零回执，三台都 online 且握着 RUNNING 卡 | 进展信号 = 子进程 stdout 字节 + 交付物大小；30 分钟不涨判 STALL |
| 空转：自检占产线 | 730 回执里 257 份是 CANARY（39%），队列里 152 张 CANARY 卡 | 自检不入生产队列；监视面与生产面分开计 |
| 无效重派 | voice-corpus 连三天对四机重派，全 FAILED 且无 error_class | 同任务失败达 3 次停线，落根因后才许再派 |
| 闲置 | CPU 13.8% / GPU 21%，bm-a 空 31 槽 | 每机常备 5 张可派卡，库存不够就补 |

## 二、四层结构

1. **真值层**（`census.py`）：产出 = 真实文件（排除 `cph4/fleet/state/`、`queue-receipts/`、`dispatcher/`）。只有记账没有产物的线判 `BOOKKEEPING`，声明 ACTIVE 即 DRIFT。
2. **供给层**（`workgen.py` + `PRODUCTION-QUEUE.jsonl`）：每机常备 `floor_cards_per_node=5`；只有带 `deliverable` + `accept` 的卡入队；停产任务由 `blocked_stems()` 拦住。
3. **执行层**（`lane_agent.py` + `closer.py`）：
   - 车道每 45s 上报 `out_bytes`（子进程已产出 stdout 字节数），不再只报 `elapsed_s`；
   - closer 用 `progress_bytes`（stdout 字节与交付物大小的较大值）判定进展，`stall_after_s=1800` 无增长即释放；
   - 同一张卡累计 3 次未成 → `FAILED` + `error_class=E-ROOTCAUSE-3X`，停线等根因。
4. **质量+经济层**：产物不达标不算 DONE（闸在环内）；本地优先，云端按日预算 `¥100` 硬上限（`cloud_budget.py`），>500 积分必须 CEO 签字。

## 三、云端口径（改自 2026-10-20 T0 令；2026-11-05 收紧为最后手段）

CEO 2026-11-05 原话：「优先本地算力互相赋能，其次云端算力有必要才用，不要浪费」。

- **默认不走云**：任何活先过本地三道问——① 本地有没有这个能力？② 全队同类能力是不是都在飞？③ 资产库里有没有可复用的现成产物？
- **允许上云的三种情形**：本地能力缺失（重 GPU 生成 / 最强判断 / 实时云端 API）；本地产能确已排满且有明确等待成本；本地跑过的同类批绝不重跑。
- **禁止**：用云替代本地 CPU 可做的批量活；本地有余量时上云；同一批活本地跑过又花钱重跑；单次 >500 积分不签字；凭据入库。
- **强制凭证**：`cloud_budget.py spend` 必须带 `--local-checked`（本地试过/查过的证据）与 `--why-not-local`（本地为什么不行），缺一即拒（rc=2）。
- **记账**：落 `cph4/fleet/token-ledger/SPEND.jsonl`，含本地证据字段；`cloud_budget.py check` 同时报本地余量（`squeeze.json` 的空槽数与 GPU/CPU 占用），让人一眼看出"本地其实没满"。
- **预算**：日硬上限 ¥100，到限即停。

## 三·二、本地算力互相赋能（默认路径）

一台机的产物就是下一台的输入，不让机器互相等、不让能力重复买：

1. `bm-c` 出关键帧/生图 → `bm-c`/`bm-a` 图生视频 → `bm-a` 剪辑装配 → `bm-b` 配音配乐 → `bm-a` 终检。
2. `bm-d` 入网后承担全部 LLM 服务（代码代理/评审/裁决），三机不再各自跑本地小模型、不再抢同一块显存。
3. `asset-lib` 先查库再生成：能复用就不新造，复用率入账。
4. 本地自检与小模型判读只占主控余量，不占生产车道。

## 四、机队分工（含 bm-d）

| 机 | 角色 | 边界 |
|---|---|---|
| bm-a | 中枢 + 装配（CEO 主力机） | 白天只接 day_ok，夜窗才吃重 GPU |
| bm-b | 声音（TTS/配乐/训练） | CPU 全天，TTS 抢核时让路 |
| bm-c | 画图（生图/图生视频/LoRA） | 内存 <8GB 只接只读与轻 CPU |
| bm-d | 大脑（3×V100/48G 显存/256GB） | 本周入网；承接 LLM 服务、回测重批、十席评审 |
| bm-m | 主控 | 只做调度/监督/轻量本地模型，禁重生产 |

## 五、24h 主推进线（CEO 2026-11-05 指定）

1. `bigstream-mv`：MV 41 曲，四闸（重复/静止/抖动/闪烁）在环内。
2. `biggame`：39 款在册 0 上线，硬指标=可玩包与提审材料。
3. `asset-lib`：角色/音色/道具资产，为各线复用降本。
4. `bigmoney`：金融回测，吃 CPU 闲时，产物判据=年化/夏普/最大回撤三数。

## 六、验收判据（系统是否真的在转）

1. **真值**：`census.py` 里 ACTIVE 线的 `real_output_age_h` 均 < 24h（不再出现 BOOKKEEPING 假绿）。
2. **进展**：任一时刻 RUNNING 卡的 `progress_bytes` 在 30 分钟内必有增长；否则 30 分钟后自动释放并计一次失败。
3. **停线**：同一任务（id 去掉日期后缀）不再出现第 4 次派发；失败卡必须带 error_class。
4. **供给**：`squeeze.json` 每机 `can_take_more > 0` 时，`stock_dispatchable >= 3`。
5. **成本**：`cloud_budget.py check` 的 `spent_cny <= 100`，超限即停。
6. **质量**：DONE 卡必须带闸回执，首过率（first_pass_rate_pct）作为核心 KPI 记录。

## 七、主控职责（本系统的操作者，2026-11-05 定）

主控只做五件事，且只产出「卡、裁决、告警、一屏」：

1. **盘点**：用真值层回答每条线"最后一次真实产出是什么时候"，不信心跳、不信台账自述。
2. **派单**：把方向变成卡——`LINE-NEXT-STEPS.json` 写每线的唯一产物，卡必须带 `cmd`（本机可执行）+ `deliverable` + `accept`，无三者不入队。
3. **监督**：看进展而不是看在线；RUNNING 卡 30 分钟无进展即 STALL 释放，同任务 3 次未成即停线。
4. **裁决**：卡点只分四类——ENGINE（机队自解）/ CEO（物理件）/ INPUT（缺投料）/ EXTERNAL（等外部）；每类给出唯一下一步，不留在"等"。
5. **一屏**：一页说清"当前最重要的一次决策 + 证据指针"，不拿过程当产出。

**不做**：亲自出图/渲染/装配/回测；代签任何对外承诺；代发任何平台内容；为决策编造盘上没有的证据。

**调动手段四件**：方向=LINE-NEXT-STEPS；活=PRODUCTION-QUEUE（每机常备 5 张）；纪律=STALL/3 次停线；要活=机器 `need-work` 信号自动回传。

**每轮顺序**：真值盘点 → 阻塞归因 → 补卡入队 → 派给空槽机 → 跟踪进展 → 停摆收回 → 一屏。

## 八、回归方式

```
python3 Tools/fleet/census.py                 # 真值口径
python3 Tools/fleet/closer.py                 # STALL/停线（每轮由主控脉调用）
python3 Tools/fleet/workgen.py --dry          # 供给与停产拦截
python3 Tools/fleet/cloud_budget.py check     # 云端余额
python3 -m py_compile Tools/fleet/{census,closer,lane_agent,workgen,master_agent,cloud_budget}.py
```