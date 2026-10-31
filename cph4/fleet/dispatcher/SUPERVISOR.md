# 机队监督摘要 2026-10-31 10:50

- 在线 4/4 · 队列 open=6 running=3 failed=4 · 主控脉 1132s 前 · 本轮 28.3s
- 主控脉搏判定：异常

## 下一步（按优先级）
- bm-m 自扫积压中；持续 >2 轮=该机无已声明活，需生产席补卡
- 失败件 4 个：Q-AUD-1002,Q-GPU-BMC-001,R-LLM-BMC-PROBE,R-MV-GATE-1D —— 要么重派要么改卡，不能挂着
- 总控脉 19 分钟未更新：看门狗应 kickstart com.fluxgroup.pulse
