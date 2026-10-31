# 机队监督摘要 2026-10-31 11:53

- 在线 4/4 · 队列 open=3 running=3 failed=5 · 主控脉 665s 前 · 本轮 38.3s
- 主控脉搏判定：异常

## 下一步（按优先级）
- bm-m 自扫积压中；持续 >2 轮=该机无已声明活，需生产席补卡
- bm-b 有派单但 ? 分钟无执行回执：执行器(lane_agent/HQ-ProductionClaim)没跑——本机执行 `python Tools/fleet/lane_agent.py --node bm-b`
- bm-c 有派单但 ? 分钟无执行回执：执行器(lane_agent/HQ-ProductionClaim)没跑——本机执行 `python Tools/fleet/lane_agent.py --node bm-c`
- 失败件 5 个：Q-AUD-1002,Q-GPU-BMC-001,Q-VIZ-2001,R-LLM-BMC-PROBE —— 要么重派要么改卡，不能挂着
- 总控脉 11 分钟未更新：看门狗应 kickstart com.fluxgroup.pulse
