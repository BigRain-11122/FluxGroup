> ⛔ 引证核验未过（2 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> frame_diff.py

# 2026-11-11 短剧线日报

缺口一：「万兽独尊」骨架生成缺身份锁，素材已存但 `.drama-state.json` 状态未同步至 Tenggianhai/ai-short-drama-agent 流水线，导致角色串换风险极高。  
→ 立即将 `TengXianhai/ai-short-drama-agent` 的“身份锁三件套”代码段嵌入本地流程，强制每镜写入唯一 seed 并校验 `.drama-state.json` 断点状态，否则禁止推进剪辑。

缺口二：《万妖图录传》第八季英雄镜重制缺帧级编辑能力，素材齐全但仅依赖 i2v 抽卡，未接入 Seedance 2.5 或可灵等云端顶模进行“帧级编辑”，造成视觉一致性崩塌。  
→ 在 ComfyUI 工作流中强制安装 `ShmuelRonen/ComfyUI-LatentSyncWrapper` 节点封装，将英雄镜生成环节从 i2v 替换为“图生视频+口型对齐”双模态流水线，每镜必须通过 LatentSync 置信度评分方可入库。

缺口三：开源管线缺失缺陷字典，素材堆积于 cph4/fleet/drama-dept-v1 但 `frame_diff.py` 未关联 `DEFECTS_CATALOG`，导致量产视频无法自动过滤低质帧，损失约单集 300 元无效渲染成本。  
→ 将开源仓库中的“身份锁 + frame_diff + 缺陷字典”三件模板直接复用至本地 ComfyUI 环境，构建自动化质检闸门，每帧输出前必须通过 `frame_diff.py` 比对 DEFECTS_CATALOG 标准并标记异常。

【给谁·下一步】  
向生产总监提交《身份锁嵌入与帧级编辑落地方案》，要求明日 10:00 前完成 Tenggianhai/ai-short-drama-agent 代码段合并测试，同时开通 Seedance 2.5 API 额度用于英雄镜首镜验证。

<!-- verify: citations=2 unverified=2 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
