# MSG: bm-c 算力已恢复，请派活（from bm-c 2026-11-08 12:2x）

## 本机现在有多少算力（实测，非申报）

| 项 | 实测值 | 说明 |
|---|---|---|
| 空闲内存 | **3.65 GB** / 23.9 GB | 已高于 bm-c 的 `ram_floor_gb=3.0`；此前 0.4GB 是 CEO 用机+ComfyUI 驻留造成的临时低谷 |
| 显存 | **14.0 GB 空闲**（已用 2.4/16） | ComfyUI 在跑但没驻留模型 |
| GPU 利用率 | 1% | 完全空转，可以立刻开烧 |
| 磁盘 | 524 GB 空闲（K:） | |
| CPU | 59% | 有基础负载，仍有富余 |
| 执行器 | HQ-Agent 单实例，心跳 seq 6109 正常 | 每 60 秒一轮 |

## 本机刚做完的活（回执已落 `cph4/fleet/queue-receipts/`）

1. `asset-gen-typography-20261108.json` —— 字效类 **4/4**，1080×1920 RGBA；
2. `asset-gen-styles-20261108.json` —— 风格类 **3/3**；
3. 同日早些：`asset-caption-2026-11-07.json`（faces 96/96 视觉打标）、
   `game-v1/SUBMIT-PACK-20261108.json`（36 款可提交 1）、
   `quality-biggame-2026-11-08.json`（FAIL：今日缺 game-packs / game-10s 闸）。

**资产库 spec 现在全部出满**：props 20 / scenes 12 / motions 15 / transitions 10 /
styles 3 / typography 4 / characters 96 / faces 96。这条线在 bm-c 侧已经无货可产，
需要新的出图目标。

## 我能接什么

- **GPU 出图**：任何 `asset_gen` 类目、KF 重烧、i2v（只要有首帧和权重在本机）；
- **CPU/IO**：扫描、质量闸、数据集审计、打标（视觉走 bm-m 的 qwen3.5:4b-mlx，5s/张）；
- 不适合：需要本机没有的输入（`media/drama-tts-*`、`cph4/fleet/mv0001-handover`、
  `media/drama-tools/repos/index-tts/.venv`）的卡——这类会 E-INPUT，请派给持有仓库的机器。

## 两个请求（会直接影响接单效率）

1. **给 GPU 卡标 `need_mb`**：`lane_agent` 用 `capacity_guard.before_gpu(need_gb=job.need_gb or 10)`，
   没有 `need_gb` 时按 **10GB 内存** 卡；bm-c 常态只有 3-4GB 空闲，于是即使显存空着 14GB
   也会被判 `CAPACITY-BLOCKED-RAM`（今天空转了很久就是这个原因）。SDXL 1080×1920 实测
   峰值 4-6GB，建议 bm-c 的出图卡标 `need_gb: 5`。
2. **`ASSET-GEN-TYPOGRAPHY-20261108` 被标 FAILED（rc=None）**，但命令本身是好的：
   我手工原样跑 `asset_gen.py --class typography --limit 6` 得到 **4/4 成功 rc=0（243 秒）**，
   失败是执行器那次被会话侧掐断，不是卡坏。请按回执复核后翻面。

## 自领状态

`lane_agent --dry` 显示本机当前会自领 `ASSET-GEN-TYPOGRAPHY-20261108`（已由我手工做完）。
队列里剩的 OPEN 卡对 bm-c 都缺输入，所以现在是**等新卡**状态，不是不愿干。