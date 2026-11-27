# Fold-001 · Unity/团结 2D 折叠 spike 脚手架

> 团结 2022.3.62t17 + URP 2D（GLES3），纯 C# 无第三方包，运行时脚本不引用 `UnityEditor`。
> **未在引擎内编译**：脚本已用独立 C# 编译器 + UnityEngine 桩类型全量编译通过，并跑了 50 条几何/回放断言（0 失败）；
> 但**在 Unity 打开后仍需修编译错**（API 版本差异、asmdef、着色器与材质引用）。"能编译"≠"引擎里能跑"。

## 1. 建工程（约 10 分钟）

1. 团结 Hub → 新建 → 模板 **2D (URP)** → 版本 2022.3.62t17 → 工程名 `FoldSpike`。
2. `Project Settings > Player`：1920×1080；spike 期用 Mono 迭代更快，出包再转 IL2CPP。
3. `Main Camera`：`Projection = Orthographic`，`Size = 0.5`，`Position = (0, 0, -10)`（纸面在 z=0）。

## 2. 导入脚本

1. 建 `Assets/FoldIt/Scripts/`，把本目录 `Scripts/*.cs` 五个文件拖进去，等一次编译。
2. 命名空间统一 `FoldSpike`；`FoldController` 里的 `LegacyPointerSource` 读旧输入 API（见 §5-7）。

## 3. 场景层级（LevelSandbox）

```
Main Camera        Camera                      Orthographic, Size 0.5, z=-10
Paper              MeshFilter + MeshRenderer + FoldController
Drawer             DrawerController
  Slot0 … Slot5    空物体                      x = -0.45 / -0.27 / -0.09 / 0.09 / 0.27 / 0.45, y = -0.55
Replay             ReplayHarness
```

- `Paper` 的 `MeshFilter.mesh` 留空，`FoldMesh` 在 `Awake` 里生成 1089 顶点网格。
- 材质：`Create > Material`，Shader 选 `Sprites/Default`（无光照，吃顶点色，层明暗直接可见）。

## 4. 挂组件

| 组件 | 字段 | 值 |
|---|---|---|
| FoldController | Paper Width/Height | 1.0 / 0.7 |
| | Paper Mesh Filter | `Paper` 的 MeshFilter |
| | Cam | Main Camera |
| | Candidates | size=3，见下表（**索引 0 必须是解**） |
| | Min Commit Angle / Settle Seconds | 25 / 0.15 |
| DrawerController | Slots | 6 个空物体拖进来；`SlotPitch` 0.18 |
| ReplayHarness | Controller / Drawer | 同名组件；RepeatCount 20 |

| # | a | b | is Solution |
|---|---|---|---|
| 0 | (0, -0.35) | (0, 0.35) | ✓ |
| 1 | (-0.18, -0.35) | (0.18, 0.35) | ✗ |
| 2 | (-0.5, 0.12) | (0.5, 0.12) | ✗ |

## 5. 跑法

1. Play → 按住纸面靠近竖中线拖动（吸附半径 = 屏宽 3%）→ 松手 ≥25° 自动走完 150ms 补间 → 折痕落地。
2. 撤销：Inspector 上 `FoldController` 没有按钮，spike 期用 `Undo()`（脚本/HUD 自行挂）；正式版接长按 0.4s。
3. 回放：Play 中点 `ReplayHarness` 的上下文菜单 **Run replay**（或勾 `Run On Start`）。
4. 期望输出：`consistent=YES`、`shape=PASS cov≈1.0000`、`ms ≈ 0.3–1`、`drawer placed6=True rejected7=True`。
   没有录过输入时，harness 自动合成一条"对折 + 左半剪影"的默认轨迹，所以空白场景也能跑。

## 6. spike 简化（不是最终布料模拟）

1. 折 = 绕折线的刚体旋转 + 层序 +1 + 每层 2mm z 偏移；**没有**自碰撞、软弯、回弹、厚度。
2. 层上限 5，超出直接钳制（正式版第 6 折改贴花层）。
3. 折线不能自由画：只能咬住预设候选线（解 1 + 干扰 1–2），这是为验证判定而非验证输入。
4. 覆盖率把三角面栅格进 128×128（目标剪影走多边形填充）；正式版接关卡 JSON 与 512² 离线 mask。
5. 金痕只判"折痕中线垂距 + 夹角"，不判分段覆盖比例、不判折序。
6. 抽屉一件占一格位（6 格 = 6 件）；内容包的 1–4 格位宽度未实现。
7. 回放记的是"落定后的折"（候选索引 + 角度 + 侧），不是逐帧指针：它证明几何确定性，不用于调手感。
8. 输入适配器读旧 `Input`：生产版应换成单一 `IPointerSource`（鼠标/触摸/笔/旋钮），只换实现不动控制器。
9. 判定三态 = PERFECT / PASS / BELOW-BAR；第三态不是失败屏，只是"还没到 92%"，可继续折或撤销。
