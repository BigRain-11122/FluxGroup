# bm-c GPU 租约回执

- 节点：bm-c / K:\Fluxgroup\FluxGroup
- 时刻：2026-10-31T17:44:09
- 令：Q-GPU-BMC-01R（前卡 5 次租约到期零回执 → 重试一次并留回执）
- 结果：**LEASE-HELD-OK**（本机租约在位，无需重复抢占）

## 实测

- 租约文件 `Tools/nats/data/gpu.bm-c.lease.json`：owner=`gpu_lease`，need_mb=12000，ttl=7200s
- 取证命令：`python Tools/fleet/gpu_lease.py --node bm-c --status` → LEASE 在位
- 命中原因：本作业第一次 `--acquire` 在 2026-10-31T17:38:21 已成功拿到租约，之后的重复轮次撞自己的锁判 LEASE-BUSY(rc=2)，被队列记成 FAILED（自锁型假失败）。
- 修复：`gpu_lease.py` 新增 `--if-held-ok`（同节点租约新鲜即视为成功，返回 0），队列条目 cmd 同步补该参数；默认严格抢占语义不变（其他调用方仍拿 rc=2 让路）。
- 验证：`python Tools/fleet/gpu_lease.py --node bm-c --acquire --need-mb 12000 --if-held-ok` → `LEASE-HELD-OK`，rc=0

## 后续

GPU 租约已成立，POOL-0021 等 GPU 线可被本机车道接管；租约到期后由下一轮 acquire 续拿。
