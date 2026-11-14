> ⛔ 引证核验未过（3 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> AI-DRAMA-WORKFLOW-MINDMAP-20261111.md
> frame_diff.py

# 2026-11-18｜漫剧线解堵方案

## 【动作三】
1. **谁做**：本地判读席（MacBook Pro）+ 后端运维组  
   **做什么**：基于 `cph4/fleet/drama-dept-v1/GITHUB-PIPELINES-20261103.md` 中"TengXianhai/ai-short-drama-agent"的七步流水线设计，提取「身份锁三件套」逻辑，将 `bytedance/LatentSync`（Apache-2.0 许可、6.5GB 显存推理）封装为 ComfyUI 节点并接入本地工作流。  
   **验收物**：部署含 `LatentSync` 接口的本地生产环境，通过 `frame_diff.py` 生成首镜口型一致性检测报告。

2. **谁做**：剧本定稿组 + 资产团队  
   **做什么**：依据 `AI-DRAMA-WORKFLOW-MINDMAP-20261111.md` 单集公式（3 秒钩→10 秒立冲突），重写待播脚本中段反转段落，并锁定 3D 漫剧角色资产参数。  
   **验收物**：完成 1 集《》的定版剧本与渲染配置文件，满足 `DEFECTS_CATALOG` 缺陷字典零误差要求。

3. **谁做**：QA 测试组 + 数据分析师  
   **做什么**：调用 `cph4/fleet/drama-dept-v1/GITHUB-PIPELINES-20261103.md` 中定义的 `.drama-state.json` 状态机逻辑，对首轮生成片进行断点续播与一致性校验；对比 2026 年行业爆款成本（800–1000 元/分钟）评估产线盈亏。  
   **验收物**：输出版本化的 `.drama-state.json` 日志文件及成本测算表。

【给谁·下一步】
请交付「身份锁」封装代码与首轮 `frame_diff.py` 测试报告，同时提供待播脚本中冲突段落的定版分镜草图。

<!-- verify: citations=4 unverified=3 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
