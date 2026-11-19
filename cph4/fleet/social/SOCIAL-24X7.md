# 养号线 24x7 自驱循环 2026-11-19 19:10:52

- 上轮动作：**EVAL** — 段 shallow 候选验收 REJECT（不上线）｜ [e2e] 判词：REJECT——覆盖率 26/43 < 40 | [e2e] 失败归因：{'品味闸': 47, '太长': 0, '太短': 0, '感叹号': 0, '踩红线': 0, '点名他人': 0, '指控': 4, 'Markdown': 0, '与本视频领域无关': 0, '与本批重复': 0, '照抄语料': 0, '语感闸': 0, 'lane_fail': 0}（主因 品味闸 92%）→ 五维闸没过（多为字数带/结构不合）：先看该段语料够不够，别调温度硬凑 | [e2e] 回滚命令：python3 Tools/fleet/lora_switch.sh <上一版 ACTIV
- 画像：8/14 段可用（n≥60）；缺料段：traditional(1), family(9), critic(31), requester(37)
- 语料：4763 条过品味闸；各段（门槛 500）：generic=1426, craft_learner=979, shallow=636, tech_nerd=435, peer_pro=330, music_seeker=304, memer=232, feeler=176
- 距上次训练：0.0 小时（冷却 1 小时）
- 现役适配器：cph4/fleet/social/train/RUNS/20261119-181430/best
- 空闲内存：3.0GB ｜ 连续失败：0/3
- 算力：GPU 41 tok/s（基准 41，101%）｜ CPU 忙 19%

> 采集合训练互斥；训练期间本循环只等不抢。正身账：`state/social-24x7.jsonl`
