# 2026-11-25 竞品拆解晨报

基于`cph4/research/R-20261111-oss-skill-scan.md`扫描结果，本周对 BigStream 最有价值的结论是：**引入 `promptfoo/promptfoo` 作为红队测试工具**。该工具提供“用例即断言”机制，完美契合 BigStream 当前在生产面飞行的状态下，对 LLM 决策的稳定性需求。

**具体落点**：立即集成到 BigStream 的推理输出管线中，配置生产日志中的真实 Prompt-Response 对作为测试用例（tests），建立自动化红队扫描。将利用其“红队”功能模拟对抗性输入，强制检测模型是否出现逻辑漂移或幻觉，从而在发布前拦截不稳定模型。

需补充：当前摘录未提供 BigStream 当前具体使用哪个基础模型及现有的输出稳定性指标数据，无法量化引入 promptfoo 后的预期效率提升幅度。

【给谁·下一步】
给 BigStream 生产负责人；本周内完成 `promptfoo` 依赖引入与首波红队扫描验证，产出实测报告至 `docs/decisions.md`。

<!-- verify: citations=2 unverified=0 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
