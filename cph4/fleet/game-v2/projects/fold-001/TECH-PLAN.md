# Fold It（折一折）技术方案 v1

> 项目 FOLD-001 / E02-T1；契约 `game-v2/contracts/fold-001.yaml` v2.0.2（**不改**，本文件只落技术决定与执行口径）。
> 引擎：团结 2022.3.62t17 + URP 2D（GLES3）。平台：Steam（主）、微信小游戏 3 关、车机 4K60。
> 单关 60–90s，2–4h 内容，无失败态；复用 ≥80%（口径 §6）；排期 4.3 周（D1–D30，契约 6 周内）。
> 契约待办（只登记，不改契约）：`shells` 仍为空、`content_hours=3` 与"2–4h"、`cloud_save` 需制作人补 addendum 后放 S3。

## 1. 折叠实现选型

| 方案 | 原理 | 优点 | 代价 | 结论 |
|---|---|---|---|---|
| A 2D 网格变形（CPU） | 纸=32×32 顶点网格；每折=绕折线轴的三维旋转，fold tree 逐层累积 | 几何确定→可判定；无平台依赖；易测 | 每次折重算 CPU；折痕光影自写 | **主选（权威层）** |
| B 顶点折叠（Vertex Shader） | 折线与角度进常量，顶点着色器旋转半区顶点，折痕处平滑过渡 | 零 CPU、折痕顺滑、4K 无压力 | 状态在 GPU，判定仍要 CPU 副本；微信 GLES 精度/变体风险；层遮挡与拾取难 | **辅选（呈现层）**，不做权威 |
| C 分层 Sprite | 预设切口切成若干 Sprite，折=换图/换层/遮罩 | 最省、最稳、量产快 | 只能折在预设缝上，折线任意性丧失；判定退化成"看起来像" | 否（降级预案） |
| D 纯 Shader 变形 | 全屏 SDF/UV 扭曲模拟纸与布 | 折布手感最好 | 无可判定状态；跨端不一致 | 否（仅视觉点缀） |

**推荐：A+B 混合——CPU 权威 + GPU 呈现。**
1. 判定必须"同一输入→同一结果"，几何只能由 CPU 用 double 持有；GPU 只做折痕高光/法线/软过渡。
2. 纸 32×32=1089 顶点 / 2048 三角面；最坏 6 折=6534 次顶点变换 ≈0.2ms。
3. fold tree 让"折过的部分再折"自然成立（层序=fold 深度），穿模与层偏移有明确抓手。
4. 折布变体共用同一套：细分提到 48×48 + 视觉松弛，**不引入布料解算**。

## 2. 输入

- **单指针抽象**：`IPointerSource`（Mouse/Touch/Pen/车机旋钮）→ 屏幕→正交世界坐标；全平台一套手势代码，不写两套。
- **折线选择**：按下=起点、拖拽=折线，实时 ghost 折线 + 半透明翻折预览；吸附优先级 锚点>网格线>自由（±12px@1080p，按 DPI 线性放大，4K=24px）；松手提交，长度<15% 纸宽或出界则静默取消。
- **角度**：松手后 0.25s 插值到 180°（或关卡指定角）；拖拽中反向拖回=取消本次折。
- **撤销**：命令栈；`FoldCommand` 只存折线 + 受影响顶点索引 + 层深，撤销 O(受影响顶点)，不存整网格快照；入口 HUD 键 + Esc/Ctrl+Z；无次数限制无冷却。
- **触控/鼠标统一**：只走 Pointer 事件，不读 `Input.mousePosition`；悬停仅高亮 → 可交互元素必须常驻可见（触屏/车机无悬停）。
- **车机大屏**：CanvasScaler 1920×1080 + match 0.5；最小点击区 ≥96px@4K（≈12mm）；按 `SafeArea` 收边；触摸单指 + 可选旋钮（旋钮=转折线角度，确认键=提交）；禁止"双击/长按才算"的隐式手势。
- **驾驶态**：`ICarState.Driving` 为真时锁输入、自动暂停到检查点，只留"继续/退出"；`Driving` 由车机 HMI 信号注入，不自行判定车速。

## 3. 数据结构

关卡（`Assets/FoldIt/Data/Levels/*.json`，只读随包）：
```json
{"schema":"fold.level/1","id":"L0032","family":"corner-fold","difficulty":3,
 "paper":{"w":1.0,"h":0.70,"grid":[32,24],"mat":"paper_kraft"},
 "target":{"outline":[[0,0],[1,0],[1,0.35],[0.5,0.35],[0.5,0.70],[0,0.70]],"layers":2},
 "solution":{"folds":[{"a":[0.5,0],"b":[0.5,0.70],"angle":180,"order":1},
                      {"a":[0,0.35],"b":[0.5,0.35],"angle":180,"order":2}]},
 "judge":{"pos_tol":0.02,"ang_tol":4.0,"iou_pass":0.975,"iou_perfect":0.995},
 "hints":[{"at":20,"type":"crease_ghost","fold":1}],
 "audio":{"fold":"paper_fold_01","settle":"paper_settle_01"}}
```
存档（`persistentDataPath/save.json`，tmp→rename 原子写，`SaveMigrations` 管版本）：
```json
{"schema":"fold.save/1","levels":{"L0032":{"done":true,"perfect":true,"folds":2,"ms":54321}},
 "settings":{"lang":"zh","sfx":0.8,"music":0.6,"assist":true,"quality":"auto"},
 "stats":{"total_folds":1234,"perfect":37},"last":"L0032"}
```
设置与存档同文件、向后兼容（缺字段=默认，未知字段忽略）；坏档备份 `save.bad.json` 后从空档起，不崩。

## 4. 判定（几何，不看画面）

全部在 `Core` 内 double 计算：`Judge(level, foldStack) → Result`；无随机、无时间依赖、无 ML、无图像相似度。

| 项 | 判据 | 阈值 |
|---|---|---|
| 折痕位置 | 提交折线到目标折线的垂距（归一化纸宽） | pass ≤0.02（600px 纸≈12px）；perfect ≤0.008 |
| 折痕角度 | 与目标折线夹角 | pass ≤4°；perfect ≤2° |
| 折痕覆盖 | 目标线段被提交线覆盖比例 | ≥0.85 |
| 折叠完成度 | flap 与静止层夹角 | 与 180° 差 ≤1° 才算"落定" |
| 折序 | 序列匹配；两折影响区域不相交时可换序 | 严格序 + 独立折可换 |
| 成型 | 折栈投影轮廓 vs `target.outline`，512² 栅格 IoU | pass ≥0.975；perfect ≥0.995 且折数=解折数 且无多余折 且全折痕达 perfect 容差 |
| 多层正确 | 每区域层数、顶层材质与 `target.layers` 一致 | 完全一致，无容差 |

- 判定时机：全部"落定"且无输入 0.25s 后判一次；折中不判，避免半折误判。
- 无失败态：不通过=不推进，显示差异提示（哪条折痕偏多少），可继续折/撤销；同关 20s 或 2 次未成型自动提示。
- 可测性：`FoldSolver` 由 `solution` 复算目标轮廓，导入即校验"可解"；CI 全量自解 0 失败才允许出包。

## 5. 性能

| 预算 | Steam 1080p60 | 车机 4K60 | 微信小游戏 |
|---|---|---|---|
| 帧率 | 平均 ≥60，1% low ≥50 | ≥60，1% low ≥55 | 高端 60 / 中低 30（质量档） |
| 网格顶点 | ≤1200/张，同屏 ≤3 张（≤4000） | 同左 | 同左（低档 24×24=625） |
| DrawCall | ≤30（纸 1–2、道具 ≤10、UI ≤10、VFX ≤5） | ≤30 | ≤25 |
| 内存 | ≤600MB | ≤600MB | ≤300MB（低端 ≤220MB） |
| 纹理 | ≤2048 图集，ASTC 6x6 | 同左 + TMP SDF 文字 | ASTC 4x4/6x6，无 4K 源图 |
| 后处理 | 无 HDR；暗角=1 次可选 blit | 禁实时阴影；假阴影=烘焙 Sprite | 全关后处理 |
| 包体 | — | — | **主包 ≤3.5MB**（留 0.5MB 余量），美术/关卡走 Addressables 分包，总 ≤20MB |

- 每帧零 GC：顶点数组池化、`Mesh.SetVertices` 复用、fold 重算只在提交帧；UI 不每帧改文本。
- 车机：URP 2D + SRP Batcher；单 Canvas 分 2 层（HUD/Overlay）；shader 只保留 2 个 keyword 组合。
- 微信：裁剪 + IL2CPP 体积报告入闸；首包只含 Boot 场景 + Core dll + 1 套 UI 图集。

## 6. 工程结构

```
Assets/FoldIt/
  Art/{Sprites,Materials,Shaders,Fonts}   Audio/{SFX,Music}
  Data/{Levels/*.json,Config/,Platforms/*.json}
  Prefabs/{Paper.prefab,FoldGhost.prefab,UI/…}
  Scenes/{Boot.unity,Main.unity,LevelSandbox.unity}
  Scripts/
    Core/      FoldIt.Core.asmdef      // 纯 C#：FoldSolver/Judge/LevelModel/SaveModel/Geometry
    Runtime/   FoldIt.Runtime.asmdef   // Unity：PaperMesh/Renderer/InputRouter/View/AudioHook
    UI/        FoldIt.UI.asmdef        // HUD/暂停/设置/无障碍
    Platform/  FoldIt.Platform.asmdef  // 唯一平台差异：IPlatform 三 adapter（Steam/WeChat/Car）
    Editor/    FoldIt.Editor.asmdef    // 关卡校验、解算、批量判定、包体报告
  Tests/{EditMode/FoldIt.Tests.Core.asmdef, PlayMode/FoldIt.Tests.Play.asmdef}
```
- 依赖单向 `UI→Runtime→Core`；`Platform` 只被 Runtime 引用；Core 不引用 UnityEngine（判定与解算 100% EditMode 可测）。
- 场景极简：Boot（初始化/存档迁移/平台探测）→ Main（唯一游戏场景，关卡=数据不切场景）→ LevelSandbox（仅编辑器）。
- Prefab 只 3 类：Paper（网格+材质参数）、FoldGhost（预览）、UI 模块；关卡不产 Prefab，防资产爆炸。

**复用 80% 怎么保证（可核算）**
1. 平台差异唯一入口 `Scripts/Platform/` + `Data/Platforms/*.json`；`#if WECHAT/CAR` 出现在 Core/Runtime/UI 即 G1 失败（Editor 扫描脚本）。
2. 口径：共享 LOC 占比×0.6 + 共享资产占比×0.4 ≥0.80；每次构建出 `reuse_report.json` 入闸回执。
3. 内容复用靠"折叠语法家族"：8 family（对角/边/角/卷/叠加/对称/翻面/布卷）→ 参数化 120 关，新增关=JSON 不加代码。
4. 三端同 Core/Runtime，微信与车机只换 Boot 配置与质量档；Steam 增量=成就+Steam Cloud 适配器。

## 7. 4.3 周计划（D1–D30）

| 阶段 | 天 | 产出 | 门/判据 |
|---|---|---|---|
| Spike | D1–D3 | 独立工程：拖折线→折到 180°→折 3 次→判定回执 | §7.1 六条全过，否则走降级预案 |
| 核心 | D4–D10 | Core（fold tree/judge/save）+ 输入 + 撤销 + 3 关可玩 Steam 包 | G1 编译 0 error；3 关各 60–90s 通；判定单测 ≥40 条 |
| 内容 | D11–D18 | 120 关（8 family，含 20 手工签名关）+ 关卡校验器 + 提示 + 微信 3 关包 | 全量自解 0 失败；包体/帧率入表 |
| 打磨 | D19–D24 | 手感（折痕音/震动/缓动）、完美反馈、无障碍（色弱/大字号）、车机 4K 首过、zh/en | 4K60 达标；试玩 5 人首次成功率 ≥85% |
| RC | D25–D30 | 三端 RC 包、8 闸回执、物料清单、性能报告、复用报告 | 8 闸全 PASS 且证据新于代码 |

每周产出：W1(D1–7) spike 回执+骨架+1 关+10s 片；W2(D8–14) 3 关切片包+判定 v1+存档；W3(D15–21) 120 关+微信 3 关包；W4(D22–28) 打磨包+4K/性能报告；W5(D29–30) RC+闸。

**7.1 Spike 判据（D3 结束全过才算过；证据存 `projects/fold-001/spike/`）**
1. 32×32 纸，单指拖折线，松手 0.25s 内到 180°，录屏 10s 无穿模/闪烁/破面。
2. 连折 3 次成 ≥3 层，层序与遮挡正确；1080p 与 4K 截图均无 z-fighting（像素检查）。
3. 折痕位置：同目标折线拖 10 次，误差中位数 ≤0.01 纸宽、最大 ≤0.03。
4. 判定确定性：同形状重放 20 次结果 100% 一致；单次判定 ≤2ms。
5. 性能：1080p 平均 ≥58fps、1% low ≥50；fold 重算 ≤0.5ms；DC ≤12。
6. 管线：同工程导出微信小游戏，主包含 Core+1 关 ≤4MB，真机冷启 ≤8s。

**Kill/降级**：1 或 4 不过 → 降 C（分层 Sprite + 预设折线，关卡量下调 30%）；5 不过 → B 做呈现 + CPU 16×16 低模只做判定；6 不过 → 微信只出 3 关试玩，主平台收敛 Steam。

## 8. 风险

| 风险 | 触发表现 | 对策 | 验证方法 |
|---|---|---|---|
| 折叠穿模 | flap 穿纸/自交、闪烁 | 层深偏移 0.002/层 + 提交前 2D 多边形相交检测，冲突吸附到最近合法角度；假阴影固定层 | 随机 200 组折序自动跑断言 0 相交；30 分钟人工 soak |
| 触控精度 | 折线放不准、误提交 | 磁吸（锚点>网格>自由）+ ghost 预览 + 提交阈值 + 2% 容差 + 无限撤销 | 真机 5 人×20 折：首次成功率 ≥85%、平均修正 ≤1 次 |
| 微信性能/包体 | 主包超限、低端机掉帧 | Addressables 分包、ASTC、24×24 低模档、无后处理、首包 3 场景→1 | 开发者工具 + 中/低端真机各跑 3 关，包体与帧率入闸 |
| 车机 4K | UI 过小、填充率不足、驱动花屏 | CanvasScaler+SDF 文字、禁实时阴影/HDR、≤2 次全屏 pass、GLES3 变体白名单 | PC 强设 3840×2160 + 8295 实机各 30 分钟，≥60fps 无花屏 |

## 9. 明确不做

服务器、联网/多人、账号系统、自建云存档（Steam 用 Steam Cloud，微信仅本地）、3D 重资产（纸=2D 网格+假阴影）、布料/柔体解算（除非 spike 证明必须且只在视觉层）、广告/IAA、数值成长与内购、多指手势、运行时下载关卡、随包关卡编辑器（编辑器只在 Editor asmdef）。
