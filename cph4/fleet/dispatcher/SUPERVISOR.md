# 机队监督摘要 2026-10-31 12:41

- 在线 4/4 · 队列 open=1 running=3 failed=7 · 主控脉 3588s 前 · 本轮 38.3s
- 主控脉搏判定：异常

## 下一步（按优先级）
- bm-a 有派单但 16 分钟无执行回执：执行器(lane_agent/HQ-ProductionClaim)没跑——本机执行 `python Tools/fleet/lane_agent.py --node bm-a`
- bm-b 有派单但 ? 分钟无执行回执：执行器(lane_agent/HQ-ProductionClaim)没跑——本机执行 `python Tools/fleet/lane_agent.py --node bm-b`
- bm-c 有派单但 ? 分钟无执行回执：执行器(lane_agent/HQ-ProductionClaim)没跑——本机执行 `python Tools/fleet/lane_agent.py --node bm-c`
- 失败件 7 个：Q-AUD-1002,Q-TTS-1202,Q-GPU-BMC-001,Q-VIZ-2001 —— 要么重派要么改卡，不能挂着
- 总控脉 60 分钟未更新：看门狗应 kickstart com.fluxgroup.pulse
