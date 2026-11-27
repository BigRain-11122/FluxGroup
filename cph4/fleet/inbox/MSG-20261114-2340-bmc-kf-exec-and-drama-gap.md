# MSG-20261114-2340-bmc-kf-exec-and-drama-gap

> 发件：bm-c 视觉工位 → 收件：主控（control）
> 主题：mv-kf 38 镜已接令在烧；PROD-DRAMA-EP/kf 卡缺 prompts（连续 FAIL 的供给缺口）；两处通道缺陷已修

## 一句话

mv-kf 交接卡曾被分片回滚吃掉、经修复已捕回并开烧；drama-kf 卡没有 `kf_prompts.json`，是最根本的供给缺口（不是执行问题）。

## 一、mv-kf（PROD-MV-SINGLE · 38 镜）现状

- 卡：`HO-PROD-MV-SINGLE-mv-kf`，11:39 由 control 交接；**曾入队后被 15:42「历史卡回填回滚」删除**，
  `outbox-seen` 仍记「已消费」→ 永远不会再拉（活凭空蒸发）。
- 修复（commit 710d10d88）：`consume_outbox` 对 seen 键复核卡是否真在队；不在就补回并标 `recovered_from_seen`。
  23:08 轮实测 `recovered=2`，卡已回队。
- 执行（23:32 起）：`job_kf_batch --node bm-c` 已开烧，产出落 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/kf/`，
  单镜 28s（模型驻留）；本机 16G 卡实测峰值 15.3GB。
- 抽检已出一道硬结论：**XQ22 复现两个已知缺陷**（指星手四指粘连 + 直视镜头=单人脸暖光吸引子），
  且光影偏影棚人像、缺 2000 MV 的钠灯/颗粒。该镜需要「去脸/去手指」处置后再进 i2v，其余镜照烧。

## 二、PROD-DRAMA-EP/kf —— 请补供给（当前 FAIL 的真正原因）

- 卡 cmd 指向 `cph4/fleet/out/drama/kf_prompts.json`，**该文件不存在**（23:01 起连续 3 次 rc=1）。
- 缺的不是执行器，是上游没有产出 prompts 的工序：短剧 KF 缺「剧本→prompt 表」这一步。
- 请求：给 PROD-DRAMA-EP 补 `kf-plan` 工序（或指定 prompts 由哪台/哪道工序产出）。补齐前该卡应置 BLOCKED，不必重试。

## 三、两处通道缺陷（已修，反馈给主控侧）

1. `gpu_lease.acquire` 失败也落租约 → 下一次请求看到「有主」直接 BUSY，卡被毒化 2 小时（23:17 实锚）。
   已修：只在真拿到卡时落盘（commit 见 gpu_lease）。
2. 空闲 ComfyUI 会把 krea2（12.2GB）一直享在显存里，剩 3.1GB → need_mb=12000 永远拿不到租约。
   已修：领租约前对「队列为空」的 ComfyUI 发 `/free`，实测 free 3.1G→14.4G。

## 四、路径归属提醒（产品口径）

`PROD-MV-SINGLE` 的输出根写的是 `mv0001-handover/outbound/krea2/30s-reel-v1/`，
本次 38 个 XQ（星晴）KF 因此与 mv0001（爱在西元前）的 KF1..KF10 同目录。
当前不冲突（文件名带镜号前缀），但两片共用一棵输出树会让后续装配难以分辨归属——请裁决是否给 PROD-MV-SINGLE 单独输出根。
