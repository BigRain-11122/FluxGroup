# UNITY-RUN-RESULT · Fold-001 spike（2026-11-20）

## 0. 先修掉的一个假绿（本轮最重要的一条）

首轮报的 `shape = PASS cov=1.0000` **不能证明折对了**。

- 原因：目标剪影 = 纸的左半边，而旧判定的分母是「目标面积」（covered/target）。未折的整张纸同样把左半边盖满，所以**没折也拿 1.0000**。
- 证据（负控实测，同一张纸同一次运行）：`folded cov=1.0000` / `unfolded cov=1.0000` / `wrongside cov=0.0000`。
- 修法：判定改用 IoU（交并比，对「跑到目标外的纸」同样扣分）。负控三态实测：`folded iou=1.0000` / `unfolded iou=0.5000` / `wrongside iou=0.0000`。
- 常驻化：`ReplayHarness` 每轮自动跑这三态，`live=YES` 才允许结论成立；编辑器侧 `!GateLive` 直接抛错退出（本轮已实测：编译错时 batchmode 返回码 1）。

## 1. 编译 / 执行状态

| 项 | 结果 |
|---|---|
| 引擎 | 团结 2022.3.62t17，`-batchmode -nographics -quit -executeMethod` |
| 编译 | **0 error**（log 中 `error CS` 命中 0；仅有 licensing client 的无关告警） |
| 运行 | 正常退出，log 结尾 `Exiting batchmode successfully` |
| 执行入口 | `FoldSpike.Editor.FoldSpikeSceneBuilder.BuildAndRun` |
| 日志 | `game/Logs/unity_run.log`（100,678 B） |

## 2. 产出

| 项 | 路径 |
|---|---|
| 场景 | `game/Assets/Scenes/FoldSpike.unity`（17,115 B，已存盘并序列化引用） |
| Editor 脚本 | `game/Assets/Editor/FoldSpikeSceneBuilder.cs`（仅 Editor 程序集） |
| 材质 | `game/Assets/Materials/FoldPaper.mat`（`Sprites/Default`） |
| 结果数据 | `game/Logs/replay_result.json` |

权威副本 = `game/Assets/Scripts/FoldSpike/`（引擎内实际编译运行的就是它）。`unity/Scripts/` 是同一份的镜像，本轮已同步；`unity/README.md` §0 的「未在引擎内编译」已被本文件取代（引擎内编译 0 error 已实测）。

场景层级：`FoldSpike`(FoldController+DrawerController+ReplayHarness) / `Main Camera`(正交 size 0.5, z=-10) / `Paper`(MeshFilter+MeshRenderer) / `Drawer`→`Slot0..5`(x=-0.45..0.45, y=-0.55)。
注：`CoverageJudge` 是普通 C# 类（由 ReplayHarness 内部 new），**不能**挂成组件——按 README 的组件表处理。
已核验序列化：`PaperWidth 1 / PaperHeight 0.7 / MinCommitAngle 25 / SettleSeconds 0.15 / RepeatCount 20 / SlotPitch 0.18`，候选 3 条且索引 0 为解，`Cam`/`PaperMeshFilter`/`Controller`/`Drawer`/`Slots[6]` 引用非空。

## 3. Replay 数字（20 次，synthesised log = 1 折右半→左）

| 指标 | 值 |
|---|---|
| consistent | **YES** |
| shape | **PASS** |
| iou（新判据） | **1.0000** |
| coverage（旧判据，保留仅作对照） | 1.0000（8192/8192, paper=8192） |
| 负控 | folded **1.0000** / unfolded **0.5000** / wrongside **0.0000** → `live=YES` |
| ms (min/p50/max) | **0.84 / 0.85 / 3.05**（total 21.3ms） |
| vertex hash | `0x41B025C7E3A201E3`（20 次同值） |
| folds in log | 1（无实拖，harness 合成默认轨迹） |

## 4. 抽屉数字

`placed6=True rejected7=True pickedUp=True refilled=True occ=6`
→ 6 件占 6 格、第 7 件被拒且不丢失、可回取并复填。

## 5. 未通过 / 未测项（诚实清单）

1. **coverage_perfect = false**，非缺陷：默认回放只调 `Judge()`（剪影判定），`JudgeItem()` 的金痕（+PERFECT）需要候选折痕与提交折痕比对，默认轨迹没有该输入。要拿 PERFECT 需补一条带 crease 目标的回放路径。
2. **帧率 / 1% low / DrawCall 未测**：本次是 `-nographics` batchmode，只验证几何与判定；PERF-NOTES 的三个数字仍需 Play 模式 1080p 采样。
3. **手动手势未验**：吸附、拖拽 0-180° 映射、25° 提交阈值、150ms 补间均未在 Play 模式实操（batchmode 不跑 Update/Input）。
4. **ms 口径**：0.84/0.85/2.72 是单次 `ResetForReplay + Fold + Judge` 的合计，不是纯判定耗时；不能直接对比 TECH-PLAN 的「判定 ≤2ms」单列预算（判定本身未单独隔离）。

## 6. 下一步

1. Play 模式跑一次，量帧率 / 1% low / DrawCall（PERF-NOTES 的硬线）。
2. 补 `JudgeItem` 回放用例，拿到 PERFECT/金痕数字；同时把 `TargetOutline` 换成真实关卡剪影。
3. 单独给 `CoverageJudge.Judge` 打点，把判定耗时才落到 ≤2ms 预算上。
4. 接 Addressables 前不动脚本：本轮未改任何运行时脚本语义。
