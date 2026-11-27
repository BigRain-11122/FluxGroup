# Fold-001 工作单（本地 9b 起草 + 制作人审校）

> 起草：qwen3.5:9b（59 tok/s）｜审校：制作人｜2026-11-20
> 本地稿修正：删掉"吸嘟嘟规避确认/环境检查/预算控制"等非任务项；修正产出名与负责人；补上门禁与证据包。

| # | 任务 | 负责 | 产出 | 依赖 | 并行 | P |
|---|---|---|---|---|---|---|
| 1 | Unity 折叠核心：32×32 网格、折树、层遮挡、92/80 判定、6 格抽屉 | build-engineer + designer | `projects/fold-001/unity/`（C# + 场景说明） | HTML 原型 | 否 | P0 |
| 2 | Unity 性能：1080p/1% low/DC/6 件一格 | build-engineer | `unity/PERF.md` + 数据 | 1 | 可与 3/4/5 并行 | P0 |
| 3 | 闸执行器支持新工程：`--project-root` + Fold 构建脚本 | build-engineer | `Tools/agents/gate_runner.py`、`Tools/agents/build_fold.ps1` | 无 | 是 | P0 |
| 4 | 100 件衣物折法数据：id/类别/折法/格位/难度/材质 | asset-steward | `projects/fold-001/data/garments.json` + README | 内容包 | 是 | P1 |
| 5 | Steam 商店页 + 愿望单 8 周计划 | radar-scout + publisher | `market/STEAM-PAGE.md`、`market/WISHLIST-PLAN.md` | 竞品数据 | 是 | P1 |
| 6 | 40 件资产 + 28 条音频落地 | asset-steward + audio | `assets/manifest.json` + 实物 | 美术音频方案 | 是 | P1 |
| 7 | 自动化注册：雷达/审计/周扫 3 条轻任务 | build-engineer | `AUTOMATION-PLAN` 更新 + 任务注册 | 无 | 是 | P1 |
| 8 | Spike 证据包 + G-B 决策 | producer | `G-B-REVIEW.md` | 1/2/4 | 否 | P0 |

## 并行分组

- **A 组（立即可并行）**：1（Unity 核心）、3（闸）、4（数据）、5（商店页）。
- **B 组（依赖 A）**：2（性能）、6（资产落地）、7（自动化）。
- **C 组（收口）**：8（G-B 决策）。

## 约束

- 单生产槽；spike 3 天 ≤¥2,000；不碰吸嘟嘟。
- 本地优先：草稿/数据/摘要走 9b；Unity 代码与商店页可云端，但草稿先本地。
- 每个产出必须自检（JSON 可解析、C# 无明显语法错、商店页无夸大）。
