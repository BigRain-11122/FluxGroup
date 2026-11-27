> ⛔ 引证核验未过（4 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> AI-DRAMA-WORKFLOW-MINDMAP-20261111.md
> GITHUB-PIPELINES-20261103.md
> frame_diff.py

# 2026-11-14 漫剧线解堵方案

当前阻塞点：本地量产环节缺乏“身份锁 + 缺陷字典”闭环。依据《AI-DRAMA-WORKFLOW-MINDMAP-20261111.md》，现有 Agent 骨架仅出图，未执行“关键帧→逐镜视频”的一致性门禁；依《GITHUB-PIPELINES-20261103.md》，`TengXianhai/ai-short-drama-agent` 拥有完整工序表但缺本地实施代码，《bytedance/LatentSync` 口型同步模块需接入工作机。

## 下一步动作
1. **谁做**：本地判读席团队（bm-m）  
   **做什么**：基于《AI-DRAMA-WORKFLOW-MINDMAP-20261111.md》中定义的“身份锁三件套”逻辑，在 `frame_diff.py` 框架内嵌入 `TengXianhai/ai-short-drama-agent` 的断点状态机与 `DEFECTS_CATALOG` 校验规则。  
   **验收物**：生成 `.drama-state.json` 格式的生产进度日志，自动拦截无口型同步与角色 ID 不一致帧。

2. **谁做**：本地工程团队  
   **做什么**：调用 `bytedance/LatentSync`（Apache-2.0）封装的 ComfyUI 节点（参文档路径 `ShmuelRonen/ComfyUI-LatentSyncWrapper`），在 ComfyUI 工作流中强制开启口型同步检查。  
   **验收物**：输出带有“音画同步置信度”评分的逐镜视频批次报告，零容忍低于阈值的片段进入后续流程。

3. **谁做**：流程编排团队  
   **做什么**：依据《GITHUB-PIPELINES-20261103.md》中定义的七步流水线（立项→剧本→拆解→资产→分镜提示词→关键帧→逐镜视频），重构本地执行链，将云端英雄镜结果回传至本地 `Wan2.2`/`LTX-2.x` 环节。  
   **验收物**：打通“云端顶模→本地开源”的硬编码链路，实现从角色资产到成片的单条连续产出记录。

【给谁·下一步】
请流程编排团队在 48 小时内完成上述三处路径的代码重构与参数绑定，并将生成的 `.drama-state.json` 样本同步至 `cph4/fleet/drama-dept-v1/GITHUB-PIPELINES-20261103.md` 的验证库中。

<!-- verify: citations=5 unverified=4 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
