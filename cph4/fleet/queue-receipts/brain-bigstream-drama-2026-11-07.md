> ⛔ 引证核验未过（3 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> cph4/fleet/drama-dept-v1/.drama-state.json
> frame_diff.py

# 2026-11-03 漫剧线解堵方案

当前 ASR 语音检测失败（字错率 66.7%，verdict: FAIL），口型同步未部署。依据摘录清单，需先补齐“身份锁 +frame_diff"与“口型接口”。**TengXianhai/ai-short-drama-agent**提供标准七步流水线及`.drama-state.json`断点管理、`frame_diff.py`一致性检测；**bytedance/LatentSync**（Apache-2.0）需安装至工作机作为"6.5GB 显存”端点的口型门禁。

下一步三个动作：
1. **谁做**：MacBook Pro  
   **做什么**：基于**TengXianhai/ai-short-drama-agent**设计七步流程，引入其“身份锁三件套”，并将**bytedance/LatentSync**拉取至工作机部署。  
   **验收物**：`cph4/fleet/drama-dept-v1/.drama-state.json`状态恢复、LatentSync 端点口型过测报告。

2. **谁做**：MacBook Pro  
   **做什么**：利用摘录中 `frame_diff.py`逻辑重跑全片，生成 `DEFECTS_CATALOG`缺陷字典对比旧片误差。  
   **验收物**：更新后的 `.drama-state.json`及 `DEFECTS_CATALOG` 差异报表。

3. **谁做**：MacBook Pro  
   **做什么**：依据**cph4/fleet/drama-dept-v1/qa/asr-voice-20261103.json**中语音检测失败记录，重写配音质检模块并接入新 ASR 结果。  
   **验收物**：ASR 字错率降至 5% 以下、生成的 `cph4/fleet/drama-dept-v1/subs/2026-11-03-voice.srt` 校验通过。

【给谁·下一步】
给 **BM-m**，立即拉取 **TengXianhai/ai-short-drama-agent** 与 **bytedance/LatentSync** 至本地执行口型门禁联调，产出新的 `.drama-state.json` 状态文件。

<!-- verify: citations=4 unverified=3 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
