# 工位岗位书（stations/）

> 每台机读自己那一份：`stations/<工位>/CHARTER.md`。读完就开工，不用翻集团法条。
> 上位法：`cph4/registry/CANON-V2-20261111.md`；数值：`cph4/fleet/STATIONS.json`。

## 一、五个工位

| 工位 | 机器 | 岗位书 | 一句话 |
|---|---|---|---|
| delivery | 公司生产力机（DASHENG） | `delivery/CHARTER.md` | 引擎与交付；白天让路，夜间满负荷 |
| visual | 传家宝（FLUXGROUP） | `visual/CHARTER.md` | 只出图与片；先修资产再抽卡；禁假动 |
| audio | 小钢炮（BIGMONEY） | `audio/CHARTER.md` | 只做声音；先人声后配乐；响度收口 |
| brain | 算力大脑（3×V100） | `brain/CHARTER.md` | 量化与深判；入网后才上岗 |
| control | MacBook | `control/CHARTER.md` | 只判、只验、只记账；不碰 GPU |

## 二、每份岗位书的固定结构

1. 你的领域（只做哪些产品与工序）。
2. 你不做的事（越界清单）。
3. 时段与前置（什么时候干、开工前查什么）。
4. 输入与输出（读哪个分片、回执带什么）。
5. 判据（做完怎么被机器验）。
6. 坏了怎么报（BLOCKED 与根因，不重试循环）。
7. 上岗自检（三条全过才接活）。
8. 一句话（领回去时对它说的那句话）。

## 三、机器怎么“领回去”

1. 把该工位的 `CHARTER.md` 全文作为该机执行体的系统提示/开工提示。
2. 开工第一条命令：`python3 Tools/fleet/station_status.py --remote`，确认自己的分片有活。
3. 任何与岗位书冲突的旧提示词，一律以岗位书为准。

## 四、边界

1. 岗位书只管“怎么干”；“什么算过了”在规则引擎与产品注册表里。
2. 岗位书不写阈值数字（避免第二份口径），需要数字时指向 `STATIONS.json` / `CARD-POLICY` / `drama_rules.py`。
3. 新增工位或改领域：改 `STATIONS.json` 与本目录，同步 `PRODUCTS.json` 的 `owner_station`。
