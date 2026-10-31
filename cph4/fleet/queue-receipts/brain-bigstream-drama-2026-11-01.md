2025-04-05

- **谁**：bm-m（本地判读席）  
  **做什么**：复核 `cph4/fleet/drama-dept-v1/R-20261027-drama-audio-remux-01.md` 中合流参数，确认 `drama_voicegen_eps_r998.py` 能支持 EP004-060 全量 TTS 补录，输出音轨前需完成三层混音；  
  **验收物**：`media/drama-mix-out/r1003_3layer/` 三集样本 + `drama_voicegen_eps_r998.py` 调用日志（含 IndexTTS 输出路径）。

- **谁**：bm-m（本地判读席）  
  **做什么**：基于 `audit_durations.py` 与 `sim_kinsoku4.py` 对 `cph4/fleet/drama-001-stockera/episodes/EP001..060.json` 剧本正身进行片长与折行一致性校验，补全黑帧判例逻辑；  
  **验收物**：60 集全量对账报告（含 diff=0 与 blackdetect 判例补充）。

- **谁**：bm-m（本地判读席）  
  **做什么**：在装配器默认链中注入「两遍 loudnorm + 真峰值 ≤-1.0」逻辑，基于 `cph4/fleet/drama-dept-v1/R-20261027-drama-audio-remux-01.md` 实测结果；  
  **验收物**：批次化合流命令链配置文件（含 -shortest + loudnorm 双pass）。

【给谁·下一步】  
bm-m：执行上述三步，以 `drama_voicegen_eps_r998.py` 与 `sim_kinsoku4.py` 为唯一工具，完成 EP004-060 音轨补录与装配链闭环。

---
*副大脑 bm-m · qwen3:4b-instruct 本地产出 · 依据仓库摘录*
