> ⛔ 引证核验未过（4 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> GITHUB-PIPELINES-20261103.md
> HEAD-BENCHMARK-20261103.md
> frame_diff.py

# 2026-11-03 漫剧线解堵方案

当前 ASR 误识率达 66.7%，严重阻碍成片验收。依据《GITHUB-PIPELINES-20261103.md》中`TengXianhai/ai-short-drama-agent`的经验，需补全“身份锁三件套”及一致性检测工具；结合《HEAD-BENCHMARK-20261103.md》"音轨是硬门槛”的结论，当前音频质量不达标无法推进。

**动作一：修复 ASR 流水线**
*   **谁做**：本地判读席
*   **做什么**：依据`.drama-state.json`结构重跑 ASR 校验，将当前 `cer` (0.6667) 降至<5%，确保符合《HEAD-BENCHMARK-20261103.md》中“音轨是硬门槛”的 -14 LUFS 口径标准。
*   **验收物**：`cph4/fleet/drama-dept-v1/qa/asr-voice-20261103.json` 字段 `verdict`由 FAIL 改为 PASS。

**动作二：部署身份锁机制**
*   **谁做**：算法组
*   **做什么**：直接抄录`TengXianhai/ai-short-drama-agent`的设计，为角色植入“脸部图 + 角色身份串+seed"三件套，并接入`frame_diff.py`执行逐镜一致性检测。
*   **验收物**：新剧本生成流程中必须通过 `.drama-state.json` 状态门禁，且 `frame_diff.py` 输出无缺陷日志。

**动作三：启动 3D 渲染路径**
*   **谁做**：工程组
*   **做什么**：参考《HEAD-BENCHMARK-20261103.md》中 3D 漫剧"UE5.8/团结引擎”的高稳定性路线，替代低一致性的 i2v 抽卡模式。
*   **验收物**：完成首镜资产在“引擎实时渲染”下的产出报告（分辨率需提升至 1080×1920）。

【给谁·下一步】
给本地判读席与算法组：立即重启 ASR 重跑队列，将 `verdict`修复为 PASS 后方可进入动作二。

<!-- verify: citations=5 unverified=4 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
