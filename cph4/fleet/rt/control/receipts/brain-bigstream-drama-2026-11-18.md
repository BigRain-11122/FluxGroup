> ⛔ 引证核验未过（2 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> frame_diff.py

# 2026-11-20
当前处于《万兽独尊》5 人组 8 天量产节奏瓶颈期。核心堵点：资产一致性锁未生效，口型同步接口（LatentSync）未集成至本地流水线，导致“身份锁三件套”断档，Frame Diff 无法闭环。

**下一步行动：**
1. **谁做**：Local Pipeline 组；**做什么**：依据 `TengXianhai/ai-short-drama-agent` 方案中的“身份锁三件套”，在本地部署 `LatentSync` 接口，强制所有生成镜通过 `.drama-state.json` 状态校验方可进入渲染；**验收物**：生成镜零帧级口型偏差的 `frame_diff.py` 自动报告。
2. **谁做**：Content Engineer；**做什么**：基于《万妖图录传》与《发配边关》TOP5 数据，重构剧本开场“强悬念钩”的前 3 秒素材库，剔除铺垫超 10 秒的无效场次；**验收物**：单集成本压缩至 800 元内的“黄金前三秒”脚本包。
3. **谁做**：Model Ops 组；**做什么**：从 `ShmuelRonen/ComfyUI-LatentSyncWrapper` 拉取封装节点，挂载至本地 ComfyUI 环境，实现从 Prompt 到 Lip-Synced Video 的一键流水线打通；**验收物**：本地机单镜直出、无需云端回传的英雄镜资产。

【给谁·下一步】：Local Pipeline 组与 Content Engineer

<!-- verify: citations=2 unverified=2 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
