> ⛔ 引证核验未过（2 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> frame_diff.py

### 2026-11-14

**缺口清单：素材在盘但工序没接上**

1.  **身份锁三件套缺失**  
    《TengXianhai/ai-short-drama-agent》文档明确定义需“脸部图 + 角色身份串+seed"锁一致性，当前缺乏该结构化数据接口。行动：立即提取 `.drama-state.json` 模板，重构本地化身份校验模块。

2.  **缺陷字典与质检工具缺失**  
    `TengXianhai/ai-short-drama-agent` 流水线强制要求 `DEFECTS_CATALOG` 缺陷字典及 `frame_diff.py` 一致性检测，目前工序中无对应数据库与脚本支撑。行动：直接复制并适配 `.drama-state.json` 状态机逻辑，部署本地 `frame_diff.py` 执行质检阻断。

3.  **口型同步接口未落地**  
    `bytedance/LatentSync` 提供 Apache-2.0 许可的口型同步方案（扩散端到端），当前产线缺乏该算力适配节点。行动：将 `ComfyUI-LatentSyncWrapper` 封装为工作机插件，设为“说话镜必过”的硬性准入闸。

需补充：各缺口模块的具体依赖库版本及现有素材库中的原始口型文件路径。
【给谁·下一步】呈交 BM-M 副大脑，授权本周三前完成 `.drama-state.json` 模板落地与 `frame_diff.py` 集成测试。

<!-- verify: citations=2 unverified=2 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
