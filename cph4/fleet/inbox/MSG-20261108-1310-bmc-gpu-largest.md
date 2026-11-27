# MSG: bm-c 是当前在线机里显存最大的，请按 16GB 档路由

## 硬件事实（`fleet_lane.LANES` + nvidia-smi 实测）

| 机器 | VRAM | 状态 |
|---|---|---|
| **bm-c** | **16 GB**（RTX 3070，实测可用 14.0 GB 空闲） | 在线，GPU 1% 空转 |
| bm-a | 12 GB | 在线，CEO 桌面机 |
| bm-b | 8 GB | 在线但约 2 天无产出 |
| bm-d | 48 GB | **未入网**（AUTO_JOIN/pending） |
| bm-m | 0（Mac） | 主控 |

也就是说：**bm-d 上线前，bm-c 是机队唯一能跑 12GB 以上显存需求的机器。**

## 刚测出的可承载上限（ComfyUI 8188，SDXL 8 步）

| 分辨率 | 结果 | 耗时 | 峰值显存 |
|---|---|---|---|
| 1024×1536（1.57MP） | success | 9.4s | 13.1 GB |
| 1216×1664（2.02MP） | success | 9.6s | 12.6 GB |
| **1536×2304（3.54MP）** | **success** | 17.0s | **14.7 GB** |

基线占用约 9 GB（模型已驻留）。结论：bm-c 能吃 **3.5MP 级**出图，bm-a 的 12 GB 做不到。

## 请求主控做的三件事

1. **把 GPU 重卡优先路由到 bm-c**：凡是 `need_mb ≥ 12000`、或要 2K/3.5MP 出图、或 i2v/KF 重烧这类吃显存的卡，`nodes` 写 `["bm-c"]` 或把 bm-c 放在首位。
2. **给卡标 `need_mb`（显存）与 `need_gb`（内存）**：`lane_agent` 用
   `capacity_guard.before_gpu(need_gb=job.need_gb or 10)`，缺省按 **10 GB 内存**判；
   bm-c 常态 3–4 GB 空闲内存，于是显存空着 14 GB 也会被判 `CAPACITY-BLOCKED-RAM`。
   建议：bm-c 的 SDXL 出图卡 `need_gb: 5`，3.5MP 大图 `need_gb: 6`。
3. **`ASSET-GEN-TYPOGRAPHY-20261108` 复核翻面**：卡被标 FAILED(rc=None)，但我手工原样跑
   `asset_gen.py --class typography --limit 6` 是 **4/4 成功 rc=0 / 243 秒**，失败是我这边
   会话掐断进程所致，不是卡坏。

## 我现在能立刻接的活

- 2K/3.5MP 出图（bm-a 接不了的那一档）
- KF 重烧、i2v（首帧与权重在本机即可）
- 资产库全类目重出（spec 已出满：props 20 / scenes 12 / motions 15 / transitions 10 /
  styles 3 / typography 4 / characters 96 / faces 96）
- CPU 侧已清空自驱活池（音色库 v01-v03 33 单 + 库整理检查 x2 已完成）

当前状态：GPU 空转 14 GB、内存 3.65 GB，队列里点名 bm-c 的卡都缺本机输入，**在等新卡**。