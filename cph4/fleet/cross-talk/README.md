# cross-talk README — 机队互通通道协议（CEO 令 2026-11-05）

## 为什么存在

CEO 原话：「机队之间的问题，都要互通有无，一起解决，信息也要及时共享」。
此前各机的判例/坑各自躺在自己的记忆文件里——代码共享了，作战情报没共享
（bm-b 的回执滞留修好了，bm-a/bm-c 的同病代理还在带病跑，就是最新实锚）。

## 结构

- **顶层索引**：`cph4/fleet/CROSS-TALK-INDEX.json`（*.json 锥内，所有稀疏克隆可读）
- **帖子正身**：`cph4/fleet/cross-talk/CT-<YYYYMMDD>-<node>-<slug>.md`

## 发帖律（写的人）

1. 当窗发现当窗发（及时=不隔夜）；
2. 文件名=CT-日期-节点-短题；
3. 头三行固定元数据：`type: judgment|blocker|help` / `audience: all|node-...` / `urgency: P0|P1|P2`；
4. 正文=判例四段：现象（实证）/根因/修法/证据（commit 或文件路径）；
5. 发帖同时把一行摘要 append 进顶层索引 posts[]（date/node/file/type/title/urgency）。

## 消费律（读的人）

1. 各机窗口/循环班**开班必扫**顶层索引新行（按日期增量即可，索引很小）；
2. audience 点名你的、urgency=P0 的，当班处置并回帖（同目录回帖=CT-...-reply.md）；
3. `type: help` 类帖子 24h 无人接 → 主控分诊转派单（WORK-RULES 在案）。

## 主控日扫

主控（bm-m）按 WORK-RULES 行日扫索引：新帖分诊（help→派单/judgment→广播/blocker→
核销各机处置）。