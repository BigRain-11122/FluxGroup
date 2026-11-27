# bm-b 满性能恢复 + animatic 线收官回执（2026-10-15 23:3x · bm-b 会话）

- 依据：CEO 今晚亲令「我已经换好1200W电源了，把我这台电脑显卡CPU什么的都设置的激进一点」；O-20261015-0906-bm-b §4（换电源装机后自动恢复满性能）；C-20261014-01-fleet-fullload-bill §3（换 750W 金牌电源后自动恢复——1200W 已超线）。
- 变更（全部 23:2x-23:3x 落地并验证）：
  1. PSU：550W→1200W（CEO 实装；断电案物理根因闭环，C-20261014-01 §1 表 bm-b 行 🟦安全停车→解除）。
  2. GPU 功耗墙：239.80 W（=240 上限-0.2，nvidia-smi 实证；180W 时代结束）。GPU-PowerCap-180W-Boot/Hourly 任务已不存在（前任会话清理），本会话幂等重申。
  3. 新增 GPU-PowerMax-Boot：S4U + wscript //B 隐藏链开机任务，跑 Tools\gpu-powercap\power_max.cmd（重试 5 次），防重启后驱动回滚 220W 默认；LastTaskResult=0 实测过链路。
  4. Windows 电源计划：高性能→卓越性能（Ultimate Performance；min processor state=100%，交流/直流双面实证 0x64）。
  5. bm-b-BiliAutoReply 复权（S4U ✓）：今晨 09:31 后被禁（无落账原因），按 CEO 10-14 常设令「启用就好」恢复；config 仍空=DRY-RUN 循环 23:33 正常跑通。
- 功率红线律（O-20261013-0951：GPU 满载件一次一件错峰）物理基础消失，随本案解除；CPU 满网格律（O-20261014-0030）不变。
- 产线实况：**mv-album animatic 480P 线 53/53 收官**（29 KN + 24 XQ 全部 >100KB、fails-bmb.txt 空、progress 台账 2026-10-15 15:55 XQ05 为末单）——换电后批烧已由前任自动恢复并于今日收官，无需复燃。bm-b GPU 容量现已全空 + 新电源 + 239.80W 帽，**可接新派工**（车道分配候 CEO/委员会令，不越权自领）。
- 备忘：
  1. 哨兵 00:23→23:03 无心跳（任务疑被昨夜 00:25 会话禁用；23:03 起已复跳正常，复发则查禁用来源）。
  2. Bigmoney-IntradayMarks 任务 LogonType=Interactive 违 S4U 律（BM 仓域，候其自愈重注册或 BM 会话治理）。
  3. AGENDA-STARVED = 本地池空诚实态（意义律不造忙活），候真件补货。
