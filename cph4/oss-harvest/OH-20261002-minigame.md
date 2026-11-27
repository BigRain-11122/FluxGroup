# OH-20261002-minigame — 开源收获轮·MiniGame 实体切片（游戏公司自驱·AI 游戏开发全流程 agent/skill 专项）

- **窗**：第 3 窗 2026-10-02 21:40 → 10-05 21:40；本切片=2026-10-02 ~23:4x（CEO 直令「自己也要去 github 找评价很高的 AI 游戏开发全流程 agent/skills 充实自身」·执行=bm-c 交互会话）·正典=cph4/oss-harvest.md v1.0。
- **实搜面（gh api 实测·授权态**）：①search q=claude+skills+game（6 结果）②search q=game+development+agent+skills（6 结果）③repo 直读×5（hub/sprite-gen/scenario-labs/godogen 均含 license+pushed_at 直验）④hub contents 直读×6（unity/workflows/disciplines/genres/skills 根+audio-design 样件）⑤sprite-gen SKILL.md base64 全文直读（9591B）。
- **候选**：gamedev-skills/awesome-gamedev-agent-skills（1282★Apache·09-27 活跃·74 skill 聚合枢纽）｜aldegad/sprite-gen（2248★Apache·10-02 当日）｜scenario-labs/skills（829★MIT·10-01）｜htdt/godogen（7034★MIT·10-01）｜rehan-remade/universal-modder（1888★MIT·09-30）｜zenstory-ai/novel-to-game（820★MIT·09-21）。

## 一 反重复门基线（关键定谳）

hub 的 unity/ 八件（animation/build-pipeline/csharp-scripting/input-system/navmesh/physics/scriptableobjects/tilemap-2d）+disciplines 已役七件（game-ai/game-ui-ux/level-design/procedural-gen/shader-programming/create-game-assets/game-designer 同族）**先前批次已收编在役=零撞不采**；本批只采未役缺口面。

## 二 五门评估与采用→落点（本批采 9 件·全 Apache-2.0 随仓继承+来源注记+NOTICE）

| # | 件 | 门判定要点 | 落点 |
|---|---|---|---|
| 1 | disciplines/audio-design（6.8KB） | 契合=吸嘟嘟音频 v2/BGM-SFX 线在产直配·许可 Apache·健康随仓·成本零 | 双落位（用户级发现面+司仓源） |
| 2 | disciplines/game-feel（9.0KB） | 契合=U314 玩法体验全优化令直配 | 同上 |
| 3 | disciplines/performance-optimization（9.0KB） | 契合=PerfDog 三档基线/性能线 | 同上 |
| 4 | disciplines/camera-systems（8.5KB） | 契合=City3D 机位律（U265 机位矫正批直配） | 同上 |
| 5 | disciplines/physics-tuning（7.5KB） | 契合=ArrowRush 物理时机类 | 同上 |
| 6 | disciplines/save-systems（7.3KB） | 契合=游戏款通用基建 | 同上 |
| 7 | disciplines/dialogue-systems（7.4KB） | 契合=游戏叙事面+城线居民对话参照 | 同上 |
| 8 | workflows/prototype-fast（6.0KB） | 契合=立项漏斗提速 | 同上 |
| 9 | genres/puzzle（6.9KB） | 契合=G12 画线/SortIt/puzzle 族直配 | 同上 |

统一五门：契合 ✓（各落点见上）｜反重复 ✓（§一基线）｜许可 ✓ Apache-2.0（API SPDX 直验·NOTICE 落位 GAMEDev-SKILLS-NOTICE.md）｜健康 ✓ hub 1282★·09-27 活跃｜成本 ✓ 纯 md 零依赖。技能发现=次会话生效；references 子目录按需自上游取不镜像。

## 三 parked+理由（诚实面）

- **aldegad/sprite-gen（2248★Apache·10-02 当日）**：**成本门不直装**——深度绑定 GPT/Grok 云 API（codex OAuth）+24 自家脚本运行时，与 U218 云端额度优先/本地优先律冲突；**技法面收参照**=component-row 管线/alpha 清洗/帧提取/atlas 合成/取帧律与 O-1706 本地取帧管线同构互补（Apache 许可可抄实现思路）——参照库候选：浅克隆待下窗。
- **htdt/godogen（7034★MIT）**：引擎面=Godot/Bevy/Babylon 与我方 Unity/团结栈不合·契合门不过→参照位（其 autonomous game dev 编排结构可学）。
- **scenario-labs/skills（829★MIT）**：Scenario MCP=外部付费 API 消费型·成本/外发面不过→parked；其 Blender/Maya/ZBrush/Unreal/Unity expert teams 提示词结构留参照。
- **workflows/itch-publish+steam-publish**：平台面=itch/Steam 与微信小游戏上线链不合→parked（发布律结构可参照）。
- **rehan-remade/universal-modder / zenstory-ai/novel-to-game**：题材面错配（mod 工具/小说转游戏）→不采留痕。

## 四 下窗指针

①sprite-gen 浅克隆进参照库+技法对照 O-1706 管线出增补判据；②hub genres 增补按 G 系题材表逐件评（merge/cooking/idle 族上游缺=诚实零发现合法）；③CCGS team-* 编排 9 件=游戏公司工作流编排参照下窗深挖。
