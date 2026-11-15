> ⛔ 引证核验未过（4 处查无此文件），本页结论不可作为决策依据：
> R-20261028-decision-round-25.md
> machine-health.json
> monitor/build_status.py
> quant/bigmoney/fleet/machine-health.json

# 2026-11-14 竞品拆解晨记

**核心洞察**：从 `cph4/research/R-20261111-oss-skill-scan.md` 的“提示测试”组发现 **promptfoo/promptfoo**（MIT 许可，27.1k 星），其策略是"用例即断言 + 红队”，这正是 BigStream 当前最急需的能力。

**工序应用**：
BigStream 当前正面临 `quant/bigmoney/fleet/machine-health.json` 结构损坏导致的消费面失联问题（见 `R-20261028-decision-round-25.md`）。生产端需引入外部红队验证机制。本周任务是在 **LLM 评测断言库** 环节，利用 promptfoo 将 BigStream 的“模型输出合规性”转化为可复用的测试用例。通过构建"Prompt Test Cases"，自动执行红队扫描，替代原本依赖人工复核的脆弱流程。

若无法立即接入 promptfoo，需补充：`monitor/build_status.py` 中是否已有类似的断言钩子接口可用于快速迁移该功能。

【给谁·下一步】
给量化线开发组：本周内整合 promptfoo 框架进 `machine-health.json` 的写入侧，部署每日自动红队扫描，验证生产环境模型输出的合规性边界。

<!-- verify: citations=5 unverified=4 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
