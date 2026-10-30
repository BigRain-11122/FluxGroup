2026-10-27  
- **谁做**：bm-m（本地判读席）执行 `cph4/fleet/drama-dept-v1/R-20261027-drama-audio-remux-01.md` 中合流参数链，调用 `sim_kinsoku4.py` 验证 EP002/003 折行合规性  
- **做什么**：对 EP002/003 逐集执行 `-map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.0:LRA=11 -c:a aac -b:a 192k -shortest` 合流，同步用 `sim_kinsoku4.py` 检测字幕/字卡折行，确保 worst_sub ≤17.00、worst_card ≤10.00  
- **验收物**：输出 `media/drama-eps-audio/EP002_AUDIO-r1004.mp4` 与 `EP003_AUDIO-r1005.mp4`，并生成 `sim_kinsoku4.py` 报告（含 worst_sub/worst_card）  

需补充：`drama_voicegen_eps_r998.py` 是否已覆盖 EP004-060 全量 TTS 生成，需确认执行日志  

【给谁·下一步】bm-m 负责推进 EP002/003 合流与折行验证，同时向 CEO 提交“60集全量配音排产”建议，待裁。

---
*副大脑 bm-m · qwen3:4b-instruct 本地产出 · 依据仓库摘录*
