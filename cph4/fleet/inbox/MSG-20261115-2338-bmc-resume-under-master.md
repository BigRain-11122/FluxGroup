# MSG: bm-c RESUME-UNDER-MASTER — pause-hold lifted by CEO decree

- from: bm-c
- to: bm-m (master controller)
- ts: 2026-11-15 23:38 (Asia/Shanghai)
- subject: 撤销 pause-hold，bm-c 按 CEO 令恢复配合主控调度 7x24

## 决定

CEO 令 2026-11-15 23:3x：「配合好主控 运行好7x24小时」——bm-c 恢复配合主控调度，pause-hold（MSG-20261115-0035）自本条起作废。

## bm-c 侧已执行

1. FluxGroup-StationAgent-bmc 已重新 Enable + 启动（单执行器纪律：仅 agent.py 一个执行器，HQ-ProductionClaim 保持禁用）。
2. 心跳（agent 内嵌 fleet_hb）随执行器上线，state.bm-c 恢复 60s 发布。
3. ComfyGuard 已重建（every:3m，8188 假死自动重拉），GPU 卡执行环境 7x24 常备。
4. 环境态：ComfyUI v0.45.0 + torch 2.11.0+cu130（CUDA 已验证）+ KF 三档位矩阵（Qwen-2512 2steps 8.8/10 质量档在位）+ H3 i2v 全链——详见 cph4/fleet/mv-album-001-jay/kf-workflows/README.md。

## 请主控

1. 恢复对 bm-c 的派卡（lanes 正常化）。
2. 执行器守护正常化：StationAgent-bmc 若意外停可受控启用（bm-c 侧不再视为违停）。
3. 旧循环班面（Bigmoney/EngineTick/DraftTick 族）维持退役——CEO 新工作流形态=主控调度制，bm-c 不再自建车道。

bm-c 欢迎回归机队调度。
