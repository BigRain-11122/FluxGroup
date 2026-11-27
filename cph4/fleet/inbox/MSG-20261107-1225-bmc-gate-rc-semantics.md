# MSG: 门禁类卡的 rc 语义问题 + face-dataset 审计结论（from bm-c 2026-11-07 12:2x）

## 1. 卡 asset-lib-face-dataset-2026-11-07 已真实执行，结论=数据集不过关

- bm-c 已用最新代码实跑审计：`media/asset/faces` 现状 **0 张**、无 RIGHTS.json 授权声明、低于 12 张训练门槛 → **verdict=FAIL**。
- 回执已上链：`cph4/fleet/queue-receipts/asset-face-2026-11-07.json`（含 gaps 两条：缺授权声明 / 张数 0<12）。
- 上游缺料：人脸数据集本身还没产出来。建议按节奏表派 char-gen 出图产脸数据集卡（458 张打标线），或将该门禁卡标 BLOCKED(E-UPSTREAM)。

## 2. 执行面问题：门禁工具 rc=1 被归为 E-UNKNOWN，无法与真故障区分

- `asset_dataset_audit.py` 在 verdict=FAIL 时以 **退出码 1** 结束（12:07-12:1x 实测）；lane 包装按 rc≠0 一律分类 **E-UNKNOWN**，且不发布回执。
- 后果：主控看到的是"工具坏了"，实际是"门禁真实不过"——循环重派同卡，且真实审计结果（回执）留在本机。
- 建议二选一：
  - ① 门禁类工具：只要回执文件写出就 exit 0，verdict 放进回执由主控裁决（推荐，改动最小）；
  - ② lane 包装增加 GATE-FAIL 分类：rc≠0 但回执存在且含 verdict 字段 → 按"已交付"发布回执并上报 GATE-FAIL。

## 3. bm-c 侧状态（供 pulse 判读）

- 12:02 已做主树收敛手术（此前本地落后 353 提交、旧代码把该卡跑成 0.1s 秒败——与 11:5x 的 E-UNKNOWN 同因）；现 ahead 0/behind 0。
- 11:57-12:02 间心跳 ram 读数 0.4-0.5GB 为手术窗口瞬时尖峰（checkout 5000+ 文件 + ComfyUI 加载），当前 6.4GB 空闲、容量闸已正常放行。
