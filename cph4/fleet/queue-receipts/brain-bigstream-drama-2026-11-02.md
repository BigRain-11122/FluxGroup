2026 年 10 月 29 日
**漫剧线解堵方案·Bm-m 判读席指令**

基于审计与回归实测，当前核心堵点为"EP004-060 默片交付”与"CSA 一致性未达 9/10"。
**动作一（立即执行）**：由**音频组**依据`cph4/fleet/drama-dept-v1/R-20261027-drama-audio-remux-01.md`指令，对 EP002-003 执行 `-shortest` 合流；EP004-060 调用`drama_voicegen_eps_r998.py` 补全 TTS 后复混。
**动作二（流程固化）**：由**工程组**修改`sim_kinsoku4.py` 折行逻辑，并植入`cph4/fleet/drama-dept-v1/epburn-handover/CSA-SMOKE-VERDICT-20261017.md` 所要求的“两遍 loudnorm"参数至默认链。
**动作三（验收闭环）**：运行`audit_durations.py` 校验新合流片长，复测 CSA 跨镜一致性；若黑帧误报需剔除`sim_kinsoku4.py` 已验证的卡片类型干扰项。

【给 CEO·下一步】
请批准“全量配音排产”优先级，授权将两遍 loudnorm 压入装配器默认链；验收物为 EP001-060 完整音画流及 CSA 批内锁 9/10 复测报告。

---
*副大脑 bm-m · qwen3.5:4b 本地产出 · 依据仓库摘录*
