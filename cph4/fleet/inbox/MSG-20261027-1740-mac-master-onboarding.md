# MSG-20261027-1740 — bm-m（M1 Pro）入列规格：集团主控 + iOS 出包

## 角色定盘

| 节点 | 角色 |
|---|---|
| **bm-m** = M1 Pro 16（32G/512G） | **集团主控**：命令总线、调度看板、时钟/状态面、iOS 出包（Xcode） |
| bm-a | Windows 执行中枢 + 夜窗 GPU + 主控热备（bm-m 不在线时接管） |
| bm-b | CPU/声音车道（配音、混音、词锚） |
| bm-c | GPU 生产车道（KF/i2v/渲染） |
| bm-d | 算力大脑（V100×3，装机中；采购已完） |

## 硬边界（Mac 不能做什么）

- 不能跑 Windows 计划任务 / S4U / PowerShell 循环（machine-state、task-register、iteration_loop 系列）。
- 不能跑 FleetLink listener（Windows 专用）；Mac 通过 **NATS** 加入状态面。
- 不能跑 GPU 生产（无 CUDA；ComfyUI/Krea2/H3 不可用）。
- 笔记本会睡眠：主控必须 `caffeinate -s` 或 launchd 常驻 + 接电源，否则命令分发会断。

## 到位当天步骤

1. Tailscale 入网，记录 `tailnet_ip`。
2. `git clone` 总控仓；确认 `python3 --version`（≥3.10）。
3. 填 `Tools/fleet-nodes.json` 的 bm-m：host / tailnet_ip / root，`enabled=true`。
4. 跑心跳（Python 版，到位即交付）→ `FLEET_STATE state.bm-m` 出现 `ts_utc_ms/seq/clock_offset_ms`。
5. 跑时钟报告，确认 bm-m 的 offset 与 precision（同局域网应 <1ms；经中继约 ±70–130ms）。
6. 主控接管命令总线：用 Python 版 `fleet-order-bus`（到位即交付）；bm-a 的 PowerShell 版保留为热备。
7. Xcode + iOS Build Support 单独验证：空工程 → 导出 → 装到 iPad → 跑通。

## 切换顺序（不中断）

状态面 → 时钟 → 命令总线 → 监督/看板 → iOS 产线。前一步验收通过再动下一步；bm-a 的主控任务在 bm-d 入网前不撤，只降为热备。

## 到位即交付（我这边）

- `fleet_hb.py`：stdlib-only，向 NATS 发 v2 心跳 + 时钟校准。
- `fleet_order_bus.py`：一条命令拆车道、写唯一命令文件、推送、poke 各机。
- `fleet_board.py`：读 STATE/CLOCK-SKEW/PRODUCTION-QUEUE，出主控看板。

## 当前待办

- bm-b 需一次 `Tools\fleet-hot-sync.ps1 -Push` 解除本地分叉（见 MSG-20261027-1725）。
- bm-d 装机完成后：填 fleet-nodes、跑 onboarding、接入 W 波与 MV 备援。