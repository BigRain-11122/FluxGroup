# 同步后第一件事（ONBOARD-AFTER-SYNC）· 2026-11-11

> 任何机器 `git pull` 之后，按本页顺序做，不要先干活。
> 上位：`cph4/registry/CANON-V2-20261111.md`。你的岗位：`cph4/fleet/stations/<你的工位>/CHARTER.md`。

## 第 0 步：确认你是哪个工位

| 机器 | 工位 id | 岗位书 |
|---|---|---|
| 公司生产力机（DASHENG） | `delivery` | `cph4/fleet/stations/delivery/CHARTER.md` |
| 传家宝（FLUXGROUP） | `visual` | `cph4/fleet/stations/visual/CHARTER.md` |
| 小钢炮（BIGMONEY） | `audio` | `cph4/fleet/stations/audio/CHARTER.md` |
| 算力大脑（3×V100） | `brain` | `cph4/fleet/stations/brain/CHARTER.md` |
| MacBook | `control` | `cph4/fleet/stations/control/CHARTER.md` |

机器与硬件口径见 `cph4/fleet/STATIONS.json`；交付物与判据见 `cph4/fleet/PRODUCTS.json`。

## 第 1 步：读自己的岗位书（全文）

它写清了：你的领域、禁做清单、时段与前置、输入输出、判据、坏了怎么报、上岗自检。
**与旧提示词冲突时，以岗位书为准。**

## 第 2 步：跑三条自检命令

    python3 Tools/fleet/station_shards.py --list          # 分片在不在
    python3 Tools/fleet/station_status.py --remote       # 全队谁有活（只读 origin）
    python3 Tools/fleet/station_agent.py --station <id> --once   # 巡自己一遍

任何一条失败：先报 BLOCKED + 具体缺什么，不要开始领卡。

## 第 3 步：确认自己的队列

    git show origin/main:cph4/fleet/rt/<id>/queue.jsonl

- 只读；不要改别人的分片。
- 只领本工位的卡；卡上必须带 `product_id` 与可执行判据，否则拒收并说明。

## 第 4 步：起自己的智能体

    python3 Tools/fleet/station_agent.py --station <id> --loop 300

Windows 用计划任务每 5 分钟 `--once`（静默包装）。
它的职责是巡你自己、产出发现；它不改卡、不自证验收。规格见 `cph4/fleet/stations/AGENT-SPEC.md`。

## 第 5 步：需要判断时，调主控算力

- 端点：`http://100.75.133.10:8792/api/generate`（主控网关）。
- 令牌：环境变量 `FLUX_LLM_TOKEN`；没有令牌就纯规则跑，不许自己装大模型。
- 白名单模型、上下文、并发、死线由网关强制；拿不到就排队。

## 第 6 步：生产时守三条新规

1. **无产品不入队**：卡必须挂到某产品的某道工序。
2. **无验收不入队**：判据必须可执行（路径/哈希/尺寸/条数）。
3. **机制活不进业务队列**：审计巡检修复只在夜窗，白天一张不出。

## 第 7 步：内容线（漫剧/MV）开工前多跑一条

    python3 Tools/fleet/drama_rules.py --self-test     # 14/14 必须通过

判据（镜长、抽卡、响度、盲评、AIGC 标识等）全在引擎里，文档不复述数字。

## 出问题时按这个顺序报

1. 环境缺失 → `BLOCKED` + 缺什么（不重试）。
2. 输入缺失 → `BLOCKED` + 缺哪个文件（不造数据）。
3. 同一错误两次 → 停下写根因，第三次不许再试。
4. 一个工位连续报同一 BLOCKED → 主控派修卡，并在一屏上点名。
