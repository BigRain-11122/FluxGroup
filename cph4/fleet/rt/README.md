# 运行态分片（rt/）· 2026-11-11

> 正典：`cph4/fleet/SYNC-DESIGN-v2.md`。本目录只放**运行态**：队列、回执、心跳、当日日志。

## 一句话规则

**一台机只写自己那一份。** 同路径只有一个写入者，冲突在物理上不可能发生。

## 目录

    rt/<station>/
      queue.jsonl       本工位队列（只有该工位写）
      receipts/         本工位回执（append-only）
      state.json        心跳与容量（每轮覆盖，只有该工位写）
      log/YYYYMMDD.jsonl 当日事件（追加）

station 取值：`delivery` 交付工厂、`visual` 视觉工位、`audio` 声音工位、
`brain` 大脑工位、`control` 主控台。对应机器见 `cph4/fleet/STATIONS.json`。

## 读别人的分片

    git fetch origin main
    git show origin/main:cph4/fleet/rt/visual/queue.jsonl

不 checkout、不 merge、不改工作树——读侧不产生冲突。

## 禁止

1. 跨工位写（写别家目录）。
2. 对 `rt/**` 使用 union 合并（`.gitattributes` 已禁）。
3. 把运行态写回 `cph4/fleet/*.jsonl`（旧队列已冻结只读）。

## 迁移期

老路径 `PRODUCTION-QUEUE.jsonl`、`PRODUCTION-BACKLOG.jsonl`、`lanes/*.json`、
`queue-receipts/*` 冻结为只读；分片启用后 48 小时无冲突再移入
`cph4/fleet/archive/legacy-queue-20261111/`。
