# Fold It（折一折）· 项目索引

> 新体系的首个新项目；不涉及吸嘟嘟/GimmeAll。
> 核心动词：**折**。题材：**折衣 / 衣柜收纳**（2026-11-20 由折纸 PIVOT，见 `PIVOT-DECISION.md`）。

## 一、状态

| 项 | 值 |
|---|---|
| 项目 ID | `FOLD-001` |
| 类别 | A 旗舰（Steam 买断） |
| 阶段 | experiment / G-A → G-B |
| 契约 | `contracts/fold-001.yaml`，哈希 `2071576133e55bd4` |
| 价格 | $14.99 |
| 内容 | 3 小时（目标 2–4h） |
| 愿望单 | 5,000 |
| 周期 | 6 周（试验） |
| 复用 | 80% |

## 二、文档

| 文档 | 作者 | 状态 |
|---|---|---|
| `OPPORTUNITY-CARD.md` | 市场情报 | **已完成（108 行）——折纸 NO-GO** |
| `GAMEPLAY-DESIGN.md` | 玩法设计 | **已完成（143 行）** |
| `REQUIREMENTS.md` | 产品 | **已完成（160 行）** |
| `ART-AUDIO-PLAN.md` | 美术/音频 | **已完成（139 行）** |
| `TECH-PLAN.md` | 技术 | **已完成（147 行）** |
| `DECISIONS.md` | 制作人 | **已裁决 21 项口径** |
| `PIVOT-DECISION.md` | 制作人 | **折纸→折衣/衣柜** |
| `WARDROBE-CONTENT.md` | 内容设计 | **已完成（119 行）：25 房间/100 件/首通 127min** |
| `G-A-REVIEW.md` | 制作人 | **GO：3 天 spike，≤¥2,000** |
| `SPIKE-REPORT.md` | 原型工程 | **Conditional PASS：折+装箱成立；层遮挡/6件/性能待 Unity** |
| `proto/index.html` | 原型工程 | **可玩：44.5KB，双击打开，点「▶ 演示」** |
| `game/Assets/Scripts/` | Unity 客户端 | **引擎内编译 0 error；重放 20 次 hash 一致；IoU 判定 + 三态负控 `live=YES`** |
| `data/garments.json` | 内容数据 | **100 条、25 房间各 4 件、12 项自检 PASS** |
| `market/STEAM-PAGE.md` + `WISHLIST-PLAN.md` | 发行增长 | **120/89 行，8 周 5,000 愿望单** |
| `LOCAL-REVIEW-20261120.md` | 9b 点审 | **5 条发现 + 裁决** |
| `WORK-ORDER.md` / `UNITY-SPIKE-PLAN.md` | 制作人 | **8 任务并行单 / 3 天计划** |

## 三、下一步

1. 五份文档齐 → 代审 G-A。
2. 3 天技术 spike：折一张纸，折痕可信、单指可完成、10 秒有爽点。
3. spike 过 → G-B；不过 → PIVOT/KILL，成本上限 3 天。
4. 过门后进 S3 切片（前 3 关）。
