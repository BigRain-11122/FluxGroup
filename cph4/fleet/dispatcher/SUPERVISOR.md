# 机队监督摘要 2026-11-01 00:14

- 在线 4/4 · 队列 open=3 running=2 failed=3 · 主控脉 65s 前 · 本轮 64.7s
- 主控脉搏判定：正常

## 下一步（按优先级）
- bm-a 自扫积压中；持续 >2 轮=该机无已声明活，需生产席补卡
- bm-m 自扫积压中；持续 >2 轮=该机无已声明活，需生产席补卡
- bm-b 有派单但 ? 分钟无执行回执：执行器(lane_agent/HQ-ProductionClaim)没跑——本机执行 `python Tools/fleet/lane_agent.py --node bm-b`
- 失败件 3 个：Q-AUD-1002,Q-TTS-1202,R-LLM-BMC-PROBE —— 要么重派要么改卡，不能挂着
