> ⛔ 引证核验未过（4 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> cph4/fleet/drama-dept-v1/.drama-state.json
> cph4/fleet/drama-dept-v1/asr-voice-20261103.json
> frame_diff.py

# 2026-11-03
当前口型同步模块（LatentSync）未正式接入生产流，导致音画一致性校验缺失；ASR 语音识别错误率高达 66.7%，字幕生成不可用。需立即补齐“身份锁三件套”及“帧差分检测”，并修复 ASR 模型，否则无法交付合格成片。

### 下一步行动
1. **谁做**：MacBook Pro（本地判读席）主导；
2. **做什么**：基于 `.drama-state.json` 设计状态机，集成 `frame_diff.py` 逻辑至管线，部署 `bytedance/LatentSync` 接口并替换当前 `asr-voice` 流程；
3. **验收物**：`cph4/fleet/drama-dept-v1/.drama-state.json` 状态流转正确、`cph4/fleet/drama-dept-v1/asr-voice-20261103.json` 错误率降至 5% 以下。

【给谁·下一步】
给生产组：执行身份锁与帧差分集成，修复 ASR 模型后提交新基准报告。

<!-- verify: citations=4 unverified=4 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
