①堵因：引用 `idle_reason`："CAPACITY-BLOCKED-RAM OFFLINE (hb age Nones)"。
②修复步骤（均在 bm-a 本机执行，禁止跨机）：
1. 在 bm-a 执行 `sysctl -p` 重置内存阈值配置，尝试恢复 `online` 状态。
2. 若仍离线，在 bm-a 执行 `reset_heartbeat --force` 强制上报心跳以清除僵死标记。
3. 若资源仍阻塞，需 CEO 人工介入执行 `unblock_capacity` 指令进行物理资源重置。
③不可修复部分：若内存硬件故障导致无法恢复 RAM 状态，指定 **CEO** 进行物理巡检与更换处理。