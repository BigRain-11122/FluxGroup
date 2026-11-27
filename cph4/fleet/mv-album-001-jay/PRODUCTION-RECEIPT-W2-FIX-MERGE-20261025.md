# L2 FIX 并入回执 — 龙卷风 / 简单爱 KF-PACK-A（2026-10-25 11:0x · bm-c 产线）

> 口径：CEO 一词「A」= F-1 走 A 案（只断句界，不改设计）。产线执行，不签 verdict。
> 复跑证据：`Tools/kf_pack_extract.py` → 两曲 **29/29 与 30/30 帧 CLEAN，零超 200 词**。

## 龙卷风（29 帧）

| 项 | 处置 | 实测 |
|---|---|---|
| F-1 句界 | 14 处 `%s <分词>` → `%s. <分词>`，首字母大写 | T23 由 `the wooden floor's raised palm` 变为 `his raised palm`（毁伤级已解） |
| T18/T23 所有格 | `%s's shoulder` / `%s's palm` → `his …`，格式化参数同步收缩 | 不再把「地板」当主语 |
| F-3 空椅 | `where it has drifted` → `exactly where it was, untouched` | 与「空椅全程不动」对齐 |
| F-4 拇指落点 | → `on the corner where her face is` | note 意图落词面 |
| F-5 勒痕 | `the grip a beat too tight` → `a red pressure line across her wrist` | — |
| F-6 钟链 | T01 加 `its hands stopped at ten past four`；T29 加 `the stopped clock now standing level on the shelf, its hands still at ten past four` | 读数闭合 |
| F-7 相框状态链 | T04 加 `turning the frame face-up in his hands`；T20 改 `the photograph already slipped out beside it` | 取出有物证 |
| F-12 跨帧指涉 | T17/T20/T29 的 `the same room` / `the pale rectangle` → 具体实体（同墙同宽浅方形） | — |
| F-14 冠词 | 模板改 `art = An/A`（按 SHOT_SIZE 首字母） | `An extreme wide…` |
| **F-13 尾段冷暖** | **按 L2 推荐 A 执行**：KF 尾段换冷版（cold neutral skin / black point 10-14 / restrained bloom） | +9 词/帧，max 167→176 <200 |

## 简单爱（30 帧）

| 项 | 处置 |
|---|---|
| F-1 句界 | 12 处断句 + 首字母大写 |
| F-14 冠词 | 同模板改法 |
| F-4 T20 水上写字 | `drawing three characters` → `tracing three short strokes into the water, the marks already illegible and closing over`（去 AI 中文硬伤） |

**未并入（属设计/预算决策，产线不代决）**：F-2 日光物块、F-5 补 ID 块（词数预算 190/192 擦线）、F-7 纹理口径、F-13 尾段冷暖（简单爱本身 I2V 尾段已是「skin tones natural and unlit」，本轮未动）。F-6/F-8/F-9/F-10/F-11 为文档口径勘误，待随草稿同批改。

## 边界
- 未签任何 verdict；未改设计（镜头内容、构图、光位、节奏全部原样）。
- 冷版尾段若导演席不认，一句话可回退（改回 `GRADE_2000 = GRADE_2000_BASE`）。