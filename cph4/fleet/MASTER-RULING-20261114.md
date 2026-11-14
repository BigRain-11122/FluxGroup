# 主控裁决 2026-11-14（00:10-00:30）

> 令源：CEO 2026-11-13 深夜「我要你真正的负责起集团的主控角色 好好全面的反思和审查，然后闭环」。
> 口径：只写可复算的事实；每条裁决都有执行动作与验收物；不催办 CEO，物理件写台账。

## 一、我看清了什么（取证）

| 面 | 事实 | 来源 |
|---|---|---|
| 职责 | 36 项职责 35 OK / 1 IDLE，执行体与证据都新鲜 | `duties_audit.py` |
| 产出 | 近 24h 全机队只有 **3 张 DONE**（control 2 / visual 1 / delivery 0 / audio 0 / brain 0） | 同上（本轮新增产出面） |
| 工序 | 在产 43 道：**可自驱 19 / 待接命令 23 / 权限 1**；另有 16 道被挂起 | `integrity_check.py` C1 |
| 机器 | 传家宝 在线且代码最新；公司生产力机 状态面在线但 **538 分钟没拉代码、分叉 222/35、唤醒口 8790 不响应**；小钢炮 不可达（物理离线，11-11 起候开机）；算力大脑 未入网 | `fleet_control --status` + `notify --send` 实测 |
| 供给 | 只有视觉工位有 6 张卡可建；control 10 / delivery 4 / audio 8 / brain 0 道**全是"命令未接"** | `station_drive --dry --force` 五工位 |
| 模型 | 本地 4B 两天 530 次生成，全在评审判卷与压测探针；产出侧 0 | `rt/control/local-model.jsonl` |

**一句话**：职责表满分、产出为零——不是机器懒，是**能跑的机器只有一台（主控自己）**，而主控手上的 23 道工序里 10 道没接命令。

## 二、裁决

### 裁决 1：挂起 5 条零产出线（按既有规则「线连续 7 天无产物自动挂起」）

`PROD-FLUXVERSE-SCENE` / `PROD-BIGHOUSE-FLOW` / `PROD-BIGLIFE-POP` / `PROD-QUANT-REPORT` / `PROD-CAR-GAMING`
—— 全部"零产物且零命令"。挂起不是废弃：每条带 `parked_reason` 与 `revive_condition`（接任意一道命令即复活）。
副作用已验证：`station_drive` 现在真的不派挂起产品的卡（原来 `status` 是装饰字段）。

### 裁决 2：下一批只接"主控本机能立刻跑"的命令

理由：能跑的机器只有主控，别的线的命令接了也没有机器执行。control 侧 7 道模型类工序优先：

`PROD-RECON-RECIPE/抓取` · `PROD-RECON-RECIPE/拆解` · `PROD-BIGDOMAIN-MATERIAL/文案` · `PROD-BIGDOMAIN-MATERIAL/页面` · `PROD-DRAMA-EP/script` · `PROD-DRAMA-EP/storyboard` · `PROD-MV-SINGLE/mv-plan`

排序原则：输入已在盘 > 有现成判据 > 产出可给 CEO 看。第一批（配方卡）已跑通，同模式复用。

### 裁决 3：audio 8 道与 delivery 4 道**暂不接**

它们的机器现在不在（小钢炮物理离线 / 生产力机接不到新代码）。接了只会变成"有命令无机器"，把待接数字改成另一个假象。等机器回来再接。

## 三、本轮已闭环的机制缺陷（都有负控或实测）

1. **职责审计不看产出** → 新增产出面（近 24h DONE + 有心跳机器数）；有机器执行却零产出直接判红。
2. **全量测试永不执行** → `TEST-FULL` 历史 583s、预算 240s，每天被"预算不足"跳过。改为允许长任务"包场一轮"（6 小时最多一次），并把 `max_sec` 提到 900。
3. **决策席没接排班** → `fleet_brain --apply` 自 11-11 只在已停用的 master_pulse 里。已作为 `BRAIN-PICK`（每 30 分钟）接进 `AUTOMATION-v1.json`。
4. **假派单** → 决策席报 `cards=9` 但分片一张没有：`night_plan` 只写已退役的 `PRODUCTION-BACKLOG.jsonl`。改为同时投 v3（本机入自己分片，别家走 outbox 由对方向上领）。
5. **远程收口卡自 11-11 起发不出** → 旧队列文件已归档，脚本 `FileNotFoundError` 直接崩。已修并补 v3 投递。
6. **PARKED 不生效** → 供给循环不看 `status`。已修（挂起产品不再算供给，且显式报 `PARKED`）。
7. **群控把过期快照显示成"在线"** → 改为 `在线·陈旧`，避免拿 538 分钟前的快照下结论。

## 四、需要 CEO 的只有两件（零催办·已在 orders 台账）

1. 小钢炮开机（物理离线自 11-11；开机后车道自会重连，无需其他动作）。
2. 算力大脑装机（3×V100 已定方案，未入网；它决定 18 道文本工序能不能上大模型）。

公司生产力机不需要 CEO 动手：它在跑 MV，只是收不到新代码，收口卡已投递到它的 outbox。

## 五、验收

- 全量测试 ≥56 项全绿（脚本自跑，见提交）。
- `duties_audit` 现在必须同时打出「职责 N 项 + 近 24h 产出 N 张」。
- `station_drive --dry` 五工位：无 PARKED 建卡，待接命令只数在产 23 道。


## 七、下一批命令的实际结果（2026-11-14 11:40 复核）

裁决里点名的 7 道，逐个核过输入与判据后：**接通 2 道，5 道按证据不接**。

| 工序 | 结果 | 依据 |
|---|---|---|
| `PROD-MV-SINGLE/mv-plan` | **已接通** | `Tools/mv_emit_prompts.py` 从真实镜头脚本产 38 镜计划（kf_prompts.json 40KB）；卡实跑 DONE，`verify_cmd` 校验 ≥10 镜 |
| `PROD-RECON-RECIPE/拆解` | **已接通** | 新建 `Tools/fleet/recon_analysis.py`：6 部拆解卡按九面结构化，输出覆盖率（平均 **54%**）与未测面；卡实跑 DONE 7942B |
| `PROD-RECON-RECIPE/抓取` | 不接 | `batch_recon.py` 要 targets.json + 网络下载，盘上无样本包 → 外部依赖，接了必挂 |
| `PROD-BIGDOMAIN-MATERIAL/文案` | 不接 | 对外材料没有事实源（产品/定价/入驻规则未定，收款卡商户号＝CEO 物理件）；没有事实只能编造 |
| `PROD-BIGDOMAIN-MATERIAL/页面` | 不接 | 同上（页面由文案派生） |
| `PROD-DRAMA-EP/script` | 不接 | 需先定题材/世界观（人判）；本地 4B 写剧本达不到过导演席的质量，等算力大脑 32B |
| `PROD-DRAMA-EP/storyboard` | 不接 | 依赖 script |

结论修正：**本机能立刻提产的只有 2 道**，其余 5 道是"输入/算力未到位"，不是"命令没写"。
在产三桶由 19/23/1 变为 **21 可自驱 / 21 待接 / 1 权限**。

顺带修掉两处会让卡永久失败的工具缺陷：
- `mv_emit_prompts.py` 不建父目录（与当初 `game_submit_pack.py` 同型）；已补 makedirs。
- 机械工序被判据交评审团空转；新增工序级 `judges` / `verify` 覆盖（同一 task_type 下不同工序可用不同判据+复核命令），并加了永久回归。

## 八、我不做的事（防止自己越界）

- 不代别家写分片、不代别家回收卡（本地闭环）。
- 不把"命令未接"写成"人判"、不用假命令凑数。
- 不催 CEO、不替他做商务与账号。
- 不在没有产物契约的工序上造卡。
