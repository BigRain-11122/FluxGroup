# 裁决收敛（decision-close）2026-11-05 02:56

扫描 39 件判定：结案 4 / 待 CEO 0 / 规则缺口 0

- [结案] CAPACITY:bm-c（27.9h）实测空闲 0.1GB < 2GB → 暂停该机重活等夜窗，不杀进程 → {"kind": "PAUSE-HEAVY", "owner": "bm-c"}
- [结案] CAPACITY:bm-b（71.5h）实测空闲 0.5GB < 2GB → 暂停该机重活等夜窗，不杀进程 → {"kind": "PAUSE-HEAVY", "owner": "bm-b"}
- [结案] LINE-STALE:biglife（74.9h）证据已过期：队列里有 R-PLAN-BIGLIFE-20261105(OPEN) 在跑，本判定作废 → {"kind": "NOOP", "card": "R-PLAN-BIGLIFE-20261105"}
- [结案] RETRY:CHK-DUPES-20261103（25.7h）已重排 2 次 → 不放行第 3 次；先按 receipt_attrib 归因（TOOL 修工具 / INPUT 补输入 / LANE 换机），改卡后再入队 → {"kind": "ATTRIBUTE", "owner": "bm-m"}
