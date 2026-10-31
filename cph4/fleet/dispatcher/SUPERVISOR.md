# 机队监督摘要 2026-10-31 12:09

- 在线 0/3 · 队列 open=4 running=2 failed=5 · 主控脉 1660s 前 · 本轮 38.3s
- 主控脉搏判定：异常

## 下一步（按优先级）
- bm-a 离线：等它自己上报（禁 poke 轰炸），或人工开机
- bm-b 离线：等它自己上报（禁 poke 轰炸），或人工开机
- bm-c 离线：等它自己上报（禁 poke 轰炸），或人工开机
- 失败件 5 个：Q-AUD-1002,Q-GPU-BMC-001,Q-VIZ-2001,R-LLM-BMC-PROBE —— 要么重派要么改卡，不能挂着
- 总控脉 28 分钟未更新：看门狗应 kickstart com.fluxgroup.pulse
