> ⛔ 引证核验未过（3 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> AI-DRAMA-WORKFLOW-MINDMAP-20261111.md
> frame_diff.py

# 2026-11-19

当前瓶颈在口型同步与资产身份锁。文档明确《TengXianhai/ai-short-drama-agent》需安装“身份锁三件套”，缺失正合“闸门定成本”之要；`bytedance/LatentSync` 提供 Apache-2.0 商用口型接口，但本地落地需封装以适配 ComfyUI。现缺 `ShmuelRonen/ComfyUI-LatentSyncWrapper` 以打通"真人与动画角色"同框能力。

## 下一步动作
1. **谁做**：后端组
   **做什么**：部署 `ShmuelRonen/ComfyUI-LatentSyncWrapper` 作为 ComfyUI 节点库，并基于 `TengXianhai/ai-short-drama-agent` 逻辑硬编码“身份锁”（脸部图 + 角色串+seed）。
   **验收物**：本地 pipeline 启动无报错，生成视频包含完整身份锁结构。

2. **谁做**：质检组
   **做什么**：运行 `frame_diff.py` 脚本，比对关键帧差异与口型置信度；手动验证《AI-DRAMA-WORKFLOW-MINDMAP-20261111.md》定义的“单集公式”钩子执行率。
   **验收物**：生成 `.drama-state.json` 状态报告，缺陷项清零率达 90%。

3. **谁做**：算法组
   **做什么**：将 `bytedance/LatentSync` 接口接入本地工作流，设定“说话镜过口型否则不许进成片”的阻断规则。
   **验收物**：产出一集含标准口型的试看版本（Seedance 2.5 风格），热度模拟分≥8.0。

【给谁·下一步】给全组：本周内合流完成本地口型接口落地，产出带身份锁的测试视频。

<!-- verify: citations=3 unverified=3 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
