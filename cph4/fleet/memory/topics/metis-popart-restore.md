# metis 美漫/素描全链重建蓝图 v3（2026-10-15 16:5x 素描域还原后正典）

> **v3 变更**：CEO 令「素描风格化部分全部还原成 git 上最新的，美漫保留不要动」已执行完毕——当前工作树=**美漫全量保留+素描域回退至 HEAD 原厂**。mirror 已重建为 v3 新正典；素描全量态镜像保留在 `mirror-v2-fullstate\`（反悔药）。§8 为 v3 还原记录（含边界判定保留清单，重建/后续操作前必读）。

> **用途**：CEO 把 metis 工作树还原到 git 后，凭本档+park 镜像精确重建全部美漫/素描/描边/昼夜/材质调优效果。
> **v2 要点**：P0 玻璃门边+BandSoft、P1 墨链 10 图断头**已全部修复并烤进镜像**——恢复流程零手术步骤。
> **权威层级**：park 镜像（字节级正本）＞ 本档参数表 ＞ 记忆条目。冲突以镜像为准。
> **基线**：快照时 git HEAD=8d6b60446（MK 资产面已入库：MKHalftone 14+MKSketch 13+组合墨图 PopArtInkCombo_SketchStrokeHalftoneDot 明文 guid=0a7966a274d747b4285028ca6263b880+Picker/EditorArm/UV7Baker，该子面回滚走 git）。此前基线 522213bc5「第三空间夜景第一版」。
> **盘点时点**：2026-10-15 15:30。快照对象 = 426 个 tracked 修改 + 13 项 untracked，零删除。

---

## 0. 一键恢复流程（TL;DR，按序执行）

```
恢复物料 park = C:\Users\sjs20\.codely-cli\tmp\metis-uya\popart-restore-park-20261015\
  mirror\            453 文件工作树镜像（修复后状态·相对仓库根路径存放：mirror\Unity\...）
  full-worktree.patch git diff HEAD --binary 全量补丁（对 8d6b60446·备用）
  manifest.json       全部 426+13 路径清单（可编程消费）
  manifest-sha256.txt 镜像完整性校验
  tools\              210 手术/审计脚本（metis-uya__*/metis-sky__*/chainfix-20261015__* 前缀=来源目录）
  key-diffs\          ProjectSettings/manifest/lock/sky.mat/cs×7/launcher-hull 等专项 diff
  audit-report-20261015.txt  全量审计报告（图手术特征矩阵/渲染器探针/材质抽查·15:00 版）
  reachability-report.txt    19 图可达性报告（修复后版·死簇分类见 §3.1.x）
```

**步骤**（还原完成后）：
1. **bridge 保命**：若还原时把 `Unity/Packages/manifest.json` + `packages-lock.json` 也 checkout 了，必须先从 mirror 回填这两件再开 Unity（diff 仅 bridge 一项 `cn.tuanjie.codely.bridge 1.0.85`），否则 MCP 工具链断。
2. **镜像回填**：`robocopy "C:\Users\sjs20\.codely-cli\tmp\metis-uya\popart-restore-park-20261015\mirror" "C:\一汽奔腾实验室2期\metis" /E`（含美漫+卫生件全量·已含全部修复；嫌脏可排除 `mirror\Unity\Assets\Ress\DengZhaoHong\*\Spline*.asset` 与 `mirror\Unity\ProjectSettings\`——后者实为 0 字节行尾噪声，可跳过）。
3. **untracked 资产区**：`git checkout .` 不删 untracked、`git clean` 才删。若被 clean 了，mirror 里已含 `Unity\Assets\AIGC_MultipleRendering\PopArtAssets\{BakedMeshes,Editor,Scripts,Shader,Textures}` 全部新文件（MK 贴图已入 git 8d6b60446，不靠 mirror），步骤 2 一并恢复。
4. **Unity refresh**（unity_editor.refresh）→ 编译。已知良性白名单：节点版本提示×2 / _MainTex Assert / Autodesk×2（vendored ShadowCaster 缺声明，存量）/ ReflectionPalne·HMILit·Mountains 各 1 条 smoothstep 等值边缘 fxc 警告。
5. **验证**：§6 清单。
6. 交 CEO 视觉自验（验证分工令：视觉=他的）。

**择要恢复（备选）**：若只要美漫不要卫生件，从 manifest.json 过滤路径逐目录 robocopy；核心面 = `Unity/Packages/ArtAssert/**` + `Unity/Packages/frp-pipeline/**` + `Unity/Assets/AIGC_MultipleRendering/**` + `Unity/Assets/Settings/**` + `Unity/Assets/Scenes/Launcher.scene` + 354 个 .mat（清单在 manifest.json）。卫生件见 §4.8。

---

## 1. 统计总览（2026-10-15 实测）

| 类别 | 数量 | 说明 |
|---|---|---|
| shadergraph 手术图 | **19** | 全在 Packages（ArtAssert 16 + frp-pipeline 3），Rubik 在 Assets/AIGC |
| hlsl | 1 修改 + 1 新建 | Hatching.hlsl(M)；PopArtOutline.hlsl(新建 15KB) |
| shader | 2 修改 + 1 新建 | SkyBoxTwoBlend + _Cloud(M)；PopArtHullOutline.shader(新建 8KB) |
| 材质 | **354** | 车漆/车身 16、轮系 21、玻璃 47、内饰 40、环境/天空 32、窗系/UI 9、其他 189 |
| C# | 6 新建 + 7 小修 | 新建=美漫运行时/工具；小修=报错清零（各 2-7 行） |
| 渲染器/管线资产 | 9 | 5 台 Default 系 + 3 档 renderer + URP-Performant.asset |
| 场景/预制体 | 6 | Launcher.scene(美漫+卫生)；5 件纯卫生 |
| 贴图资产 | 29 新 + 14 对 meta 修改 | MKHalftone 14 + MKSketch 13 + InkCombo 1 + SketchEffect 笔刷 meta |
| UV7 烘焙网格 | BakedMeshes 12 文件 | 6 资产+meta |
| 全局量 | 3 | _StylizedProcess / _PopArtProcess / _IsCloud |

## 2. 架构总图（重建前必读）

- **FRP fork 双块**：master 的 StylizedColor 块=光照域分带链（Lambert/Sky 双 smoothstep→min→Posterize(LightSteps)→Shadow/Mid/Highlight 三色映射+高光带 NdotL 门控+EdgeFade 溶边+折痕）；BaseColor 块=描边×网点墨链。`FRPForwardPass L705: color.rgb = lerp(PBR结果, stylizedColor, stylizedBlend)`——美漫档下 BaseColor 路被 StylizedBlend 全遮蔽（挂 BaseColor 的美漫效果永远不可见，B 型图除外：无 StylizedColor 块的图美漫走 BaseColor Lerp）。
- **全局开关**（拼写铁律：**_StylizedProcess（z 正确拼写）**+_PopArtProcess+_IsCloud）：gpb=False 全局量；三档=写实 0/0、素描 1/0、美漫 1/1。图属性 `_Stylied*`（e 错拼）只是 metis 材质属性名，与全局量是两回事，勿混。
- **自举双件**：PopArtRuntimeBootstrap（RuntimeInitializeOnLoadMethod·BeforeSceneLoad·真机包）+ PopArtEditorArm（Editor·InitializeOnLoad·域重载自动装填）；两者都带 SceneManager.sceneLoaded 重自举且**跳过含 PSRM(ProceduralStateRenderManager) 的场景**（PSRM 是 metis 原生写入者，每帧写全局——防毒化粘滞 0）。Bootstrap 另补 `SetGlobalInt("_IsCloud",1)`。
- **深度链**：5 台 Default 系渲染器 m_CopyDepthMode=2（R2 修复=读当帧深度防描边鬼影；ForcePrepass 下深度纹理在描边 pass 前已生成）+ URP-Performant.asset m_RequireDepthTexture=1。
- **描边三层**：①Hull 反壳（PopArtHullOutline.shader，pass 300·ZWrite On 防天盖线，Feature 逐子网格 DrawRenderer）②屏幕空间深度墨线（PopArtOutlineDepth——**Process 门=popart 开才画墨线**（hlsl `Process<0.001→Outline=0`），B 型图墨链吃总混合输出再喂 BaseColor=美漫档可见；**旧记「写实档可见」为反记，勘误**）③折痕线（PopArtCreaseLine 双尺度法线差，挂美漫分支+素描档 _StylizedProcess 门控版）。
- **昼夜**：_IsNight 全局（PSRM/WeatherTimeManager DOTween 驱动）→ 三路夜色（§3.6）。
- **素描链**（10-14 修复正态）：Hatching.hlsl 六阶影线（RGB 打包 3 阶×亮暗对），_Hatch0=Dark/_Hatch1=Bright（槽序铁律），_dist=绝对距离（LOD），HatchWeight=真墨量 h'=1−w(1−h)，亮度向量 Rec.709 全值 (0.2326,0.7152,0.0722)，_HatchToneScale 色调放置旋钮，UV=Triplanar×Tiling×角度(RotateNode m_Unit=1 度化)。

## 3. 文件清单与手术履历

### 3.1 shadergraph 19 图矩阵（2026-10-15 实测探针）

| 图（Packages/ 前缀省略） | v5分带 | 墨链 | 素描夜 | 美漫夜三色 | 环境夜染 | 度化 | Hatch默认 | 折痕CFN |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| frp-pipeline/.../CarPaintBRDFUV1 | Y | Y | Y | Y | . | 1 | D/B | Y |
| ArtAssert/.../DrivingMode/Wheel | Y | Y | Y | Y | . | 1 | D/B | Y |
| ArtAssert/.../HMILit | Y | . | Y | Y | . | 3 | D/B | Y |
| ArtAssert/.../HMILitGlass | Y | . | Y | Y | . | 3 | D/B | Y（**门边断头→手术A补**） |
| ArtAssert/.../ModelControl/CarAbat | Y | . | . | Y | . | 0 | . | Y |
| ModelControl/CarTailgate | Y | . | . | Y | . | 0 | . | Y |
| ModelControl/CarTailgateEdge | Y | . | . | Y | . | 0 | . | Y |
| ModelControl/CarTopWindow | Y | . | . | Y | . | 0 | . | Y |
| ModelControl/CarWindow | Y | . | . | Y | . | 0 | . | Y |
| ModelControl/CarWindowPoint | Y | . | . | Y | . | 0 | . | Y |
| Resources/LaneLevelNavi/RoadSign/MatCapDefault | Y | . | . | Y | . | 0 | . | Y |
| frp-pipeline/.../GlassMaster | Y | . | . | Y | . | 0 | . | Y |
| MusicPlayer/MusicPlayerShadowsSG | Y | . | . | Y | . | 0 | . | Y |
| MusicPlayer/MusicPlayerUnlit | Y | . | . | Y | . | 0 | . | Y |
| Launcher/Mountains/Mountains | . | . | Y | . | Y | 3 | D/B | . |
| Shaders/Water Shader/Lake | . | . | Y | . | Y | 3 | D/B | . |
| Shaders/Water Shader/Water | . | . | Y | . | Y | 3 | D/B | . |
| frp-pipeline/.../ReflectionPalne | . | . | Y | . | Y | 1 | D/B | . |
| Assets/AIGC.../SketchEffect/RubikStyliedEffect | . | . | Y | . | . | 1 | D/B | . |

（D/B=PencilDiagonal Dark/Bright 图默认绑定，guid：Dark=3fe12e4fc2d8e63418243b1b0f086757 / Bright=bf0cfe47fb237ec4eb90305d8ce1eb86；度化=RotateNode `"m_Unit":1` 出现数）

**手术语义**：
- **CarPaintBRDFUV1=母本**：v5 分带簇（Lerp d712089c 反向闭包 86 节点）+墨链 8 节点（CFN PopArtBrushInk+2 Sample+ScreenPos+2 Tiling+7 PropertyNode）+素描链全修+夜三色+TintNight+度化+面板 hidden 45 处+笔触窗口 float4 hidden；21 属性克隆按 ref 撞名复用原生。
- **S 型**（Wheel/HMILit）：原生 StylizedColor 门 Lerp 的 B 槽换车漆链；Wheel 另克隆墨链 13 节点（tone[68409c3e]out3→CFN in0→gate[cc73da52]in1）；HMILit 原厂老美漫四色（_PABaseFront/BackColor）值层中性化 (1,1,1)（不删图）。
- **S2 型**（HMILitGlass）：新建 StylizedColor 门——三输入门（A=素描门 bcde11f7/B=trio/T=PopArtProcess）+最终边 d2b1a739 out3→f3cdc516 in0（**P0 白板病边·2026-10-15 15:12 已由 glass_smooth_surgery --apply 落上**）。
- **B 型 10 图**：BaseColor←Lerp(原色,车漆分带链,PopArtProcess)；CarWindow/GlassMaster 美漫吃 Posterize 硬分带——玻璃手术 B 已插 BandSoft（默认 1）。
- **素描环境 4 图**（Mountains/Lake/Water/ReflectionPalne）：Unlit 型 master 无 StylizedColor 块，走 BaseColor；夜染=`Lerp(原,原×_PopArtNightTint,_IsNight×_PopArtProcess)` 隐藏色属性默认 (0.80,0.87,1)。
- **Rubik**：素描链+槽序换正（上批曾 Bright-first 病理带）。
- 全局声明修正：12 图 _PopArtProcess hlslDeclarationOverride 2→1（Global）——10-13 体检批。
- 面板瘦身：18 图 169 项 m_Hidden=true（=编译 [HideInInspector]，属性/材质键全保留零脱钩）；保留活旋钮（颜色/密度/强度/对比/层数+HMILit PostOutLine×2+PopHight/PopColor 材质库 16-20 处散调值）。

#### 3.1.x P1 断链收口正典（2026-10-15 15:2x 修复·已烤进镜像）

**真断头仅一类（已修）**：B 型 10 图（CarAbat/CarTailgate/CarTailgateEdge/CarTopWindow/CarWindow/CarWindowPoint/MatCapDefault/GlassMaster/MusicPlayerShadowsSG/MusicPlayerUnlit）的**墨链末端 Lerp 零出边**（PopArtOutlineDepth CFN→Multiply→Lerp 算了没进画面——v5 克隆时最终边没落上，与白板病同病根）。修法（对照 CarPaint/Wheel/HMILit 全绿参照+CFN Process 门方向定谳）：
- `ink_Lerp.in0 ← 总混合Lerp.out3`（原错接旧色源）
- `ink_Lerp.out3 → BaseColor 块 in0`（替换 总混合→BaseColor）
- 语义：BaseColor=lerp(美漫分带色,黑,墨线掩码)——墨线只 popart 开时画（CFN 门），写实档零墨线零开销。
- 工具=metis-uya\chainfix_20261015\fix_b_ink.py（幂等·断言+bak+round-trip）；bak=同目录 bak\。

**其余死簇判定（勿再误判为断头·HEAD 边 diff 铁证）**：
| 死簇 | 定性 | 证据 |
|---|---|---|
| Wheel 59 节点簇（bd3d5a5f 分带输出零出边） | **v5 有意换门孤儿**（原生老美漫链被 v5 链替换：removed=bd3d5a5f→gate cc73da52、added=68409c3e(v5 分带输出)→BrushInk→gate） | 现活链=9a85846e/3534a61f/998a8c49/87c49404/68409c3e→BrushInk 3a10e7c4→cc73da52→StylizedColor ✓ |
| HMILit 52 节点簇（c25e3127 老美漫 Multiply 零出边） | **v5 有意换门孤儿**（removed=c25e3127→e79f3774、added=d2500f2a(v5)→e79f3774） | 四色值已中性化 (1,1,1)，不删图 |
| HMILit/HMILitGlass/Mountains/Lake/Water 的 Rotate+TAO 三元组 ×2/图 | **HEAD 即死原厂残件**（边集与 HEAD 完全一致·零出边在 HEAD 已存在；knob 批只把这些 Rotate 的 m_Unit 度化了） | Hatching in1 各图均由**活的** Rotate 喂（33ab8978/9895e47c/93efd71c/7d50ac78/dad5aac4/dbf49049）——素描 UV 链没断 |
| HMILitGlass CarWeatherFog 簇16 / GlassMaster Refraction 簇6+Split 簇6 / ReflectionPalne 4 小簇 / Water SceneDepth 簇10 / Rubik RgbToGrayscale / MusicPlayerShadowsSG Length / MusicPlayerUnlit 变色链23 | **HEAD 即死原厂备用/条件禁用件**（CEO 判定边界内·全部边集与 HEAD 一致） | MPU 变色链（SliderTex/R_Color 变色 UI）HEAD 时就零出边喂 e27bacb4——非本批造成 |
| Wheel Saturate 6ab3dde1/Lerp a510ff13、HMILit Power/Redirect对/Lerp 9cca64a7/GetUV→OcclusionMap | **HEAD 即死原生小残件**（knob 批照旧把新输入接进死节点=Saturate 6ab3dde1，无害） | — |

**审计工具正法**：可达性分析=metis-uya\chainfix_20261015\chain_audit.py（BlockNode 反向 BFS+variablesIndex→m_RegisterIDs 逻辑边——漏接逻辑边会 CarPaint 假阳性）；断头判别必须叠 **HEAD 边 diff**（`git show HEAD:<path>` 边集对比）——「与 HEAD 边集一致的死簇=原厂残件，removed/added 成对出现的=有意换门，其余=真断头」。

### 3.2 hlsl / shader

| 文件 | 角色 |
|---|---|
| `Assets/AIGC_MultipleRendering/PopArtAssets/Shader/PopArtOutline.hlsl`（新建 15KB） | 共享 include（12+ 图消费）。函数：PopArtHash21/PopArtVNoise3（世界锚定噪声）、PopArtSampleRawDepth、PopArtReconstructWorld（含 GLES3 非逆Z分支 lerp(UNITY_NEAR_CLIP_VALUE,1,raw)）、PopArtReconstructView、PopArtSafeNormalize、**PopArtOutlineDepth**（屏幕深度墨线）、**PopArtCreaseLine**（双尺度法线差折痕：近=ddx/ddy 深度重建、远=4px 环 4 采样、连续性闸、窄带收笔）、**PopArtBrushInk**（In/Hatch/Dot/Strength→Out，Strength≤0.001 早退）。死代码 PopArtTone 已删（v3 残件清理批）。 |
| `Assets/AIGC_MultipleRendering/SketchEffect/Shaders/HLSL/Hatching.hlsl`（M） | 六阶影线 Hatching/Hatching2；guard `METIS_HATCHING_HLSL`（include 幂等）+ log2(max(_dist,1e-4)) 钳制修复 |
| `Assets/AIGC_MultipleRendering/PopArtAssets/Shader/Resources/PopArtHullOutline.shader`（新建 8KB） | Hull 反壳描边：视空间法线外扩+UV7 平滑法线槽（any() 防护）+ZWrite On（防天盖线）+clip 空间回压 _OutlineClipOffset（reversed-Z 双分支）+_OutlineScreenConstant 远近恒定+_OutlineFadeMin/Max 淡出+**手绘配方 _OutlineHandDrawn（默认 0.15）/_OutlineWobbleFreq（默认 30）**：对象空间锚定 3D value noise，宽度呼吸±强度×2+沿视线切向手颤（3.7×高频·幅度≤宽度）+顶点早退门+clip(_PopArtProcess-0.001) 跟美漫总开关 |
| `Packages/ArtAssert/Arts/Shaders/SkyBoxTwoBlend.shader`（M） | 分带漫画天：_PopArtSkyGradient(1)/GradHeight(0.35)/Bands(4) 天顶→地平线 ceil 量化+日/夜四色 _PopArtZenith/HorizonColor×Day/Night+漫画云（cloudAlphaRaw 裸盖度 posterize _PopArtCloudCut(0.3)/CloudSteps(2)+复用 _CloudEdge 公式画黑边+_PopArtCloudColor×2）+**CEO 双 cubemap 槽 _PopArtSkyTexDay/Night+_PopArtSkyTexOn(0)**（接 _IsNight 交叉淡化）+mask 装饰夜压暗 _PopArtNightDim(0.4)+_PopArtMaskBlend(1)/SkyDots(1)/SkyHatch(0.5) |
| `Packages/ArtAssert/Arts/Shaders/SkyBoxTwoBlend_Cloud.shader`（M） | 原厂残废资产健康化（删死 RenderFog 函数+补声明，hasError→False） |

### 3.3 C#（Assets/AIGC_MultipleRendering/PopArtAssets/）

| 文件 | 角色 |
|---|---|
| Scripts/PopArtRuntimeBootstrap.cs | 真机自举全局量 1/1/_IsCloud 1 + sceneLoaded 重自举（跳 PSRM 场景） |
| Scripts/PopArtHullOutline.cs | Hull 组件：OnEnable 注册静态表/私有材质实例/GetComponentsInChildren 收集(Faw.CarPaintParts 过滤+carpaintIndex 子网格)/isVisible LOD；字段 outlineWidth/outlineColor/useSmoothedNormal/outlineClipOffset/outlineScreenConstant/outlineFadeMin/Max+**outlineHandDrawn/outlineWobbleFreq**；脚本 guid=29bea3f1b8418f341bb602d123cbe1e8 |
| Scripts/PopArtHullOutlineFeature.cs | ScriptableRendererFeature：AfterRenderingOpaques·cmd.DrawRenderer 逐子网格；_PopArtProcess<0.5 CPU 闸门整 pass 跳过（关态零 draw） |
| Editor/PopArtEditorArm.cs | 编辑态域重载自动装填全局量 |
| Editor/PopArtUV7Baker.cs | 菜单 AIGC/PopArt/Bake UV7 Smoothed Normals：位置焊接→UV7→BakedMeshes/+实例替换（SerializedObject 法，防 prefab setter 静默回滚） |
| Editor/PopArtInkPatternPicker.cs | 菜单 AIGC/PopArt/Ink Pattern Picker：MKSketch 13 排线×MKHalftone 14 网点宫格点选→RG 通道合成 combo PNG→批量换绑 _PopArtBrushTex 系材质；内置 sky.mat 泄漏卫兵（SaveAssets 前 ClearDirty） |
| （删除态确认）PopArtStyleMenu.cs / PopArtMKTuningWindow.cs | 已删勿复建（10-14 还原批+MK 掉头批） |

### 3.4 渲染器/管线资产（Assets/Settings/）

| 资产 | 改动 |
|---|---|
| URP-Default-{Renderer,Renderer_Map,AppView,MusicPlayer,Simple}.asset | HullFeature 子资产注入（FRP fork 字段名 **m_RendererFeatureMap** 单数·纯 List&lt;long&gt; 实例 ID≠原版 m_RendererFeaturesMap）+m_CopyDepthMode=2 |
| URP-{Balanced,HighFidelity,Performant}-Renderer.asset | m_CopyDepthMode=2（无 Hull） |
| URP-Performant.asset | m_RequireDepthTexture 0→1（8155 档描边静默丢线根治） |

### 3.5 贴图资产
- `PopArtAssets/Textures/MKHalftone/` 14 张 + `MKSketch/` 13 张（MK Toon 借鉴收割，sRGB=Off 线性墨量+Repeat）
- `PopArtAssets/Textures/PopArtInkCombo_SketchStrokeHalftoneDot.png`：R=笔触 G=网点通道打包（17 采样器上限修复：ps_4_0 最坏变体 17 采样器→1 张双 T&O 独立平铺）
- `SketchEffect/Textures/Brush/` 14 对 .png.meta 修改（PencilDiagonal 等 7 风格×亮暗）
- `PopArtAssets/BakedMeshes/` 12 文件（UV7 平滑法线烘焙网格，已 assigned 22 处实例）

### 3.6 材质 354 件·参数正典（族值=live 实测）

**分带族**（美漫核心，材质 Inspector 可调）：`_PopArtTilling=180`（整除锁防拍纹）·`_PopArtLightSteps=4`·`_PopArtLambertSmoothStepUp=0.129`·`_PopArtSkySmoothStepUp=0.488`·`_PopArtHighlightBandUp=0.62`·EdgeFade 溶边 0.229·EdgeSmoothStep Down=1/Up=0。

**对比族** `_Day_Contrast`=`_Night_Contrast`：车漆 1.2 / EXT 1.2 / 轮 0.9 / HMILit 0.8 / 玻璃+HMILitGlass 1.1 / 内饰 0.8 / 环境 1.0。

**美漫三色**：Shadow=墨青 (0.18,0.22,0.3)·Mid=乘性 (0.97,0.99,1)·Highlight=(1,1,1)；分族变体——内饰 PShadow (0.13,0.15,0.2)+PMid (0.94,0.96,1)、玻璃 PMid (0.38,0.42,0.5) 暗带族、37 件 Shadow 纯黑族 (0.06 系)。

**夜色矩阵**（_IsNight 驱动）：夜三色 Shadow_Night=(0.08,0.10,0.16)/Mid_Night=日值×(0.80,0.87,1) 乘性/Highlight_Night=(1,1,1)（14 图：CarPaint+13 车族）；素描夜纸 _TintNight=(0.80,0.84,0.92)（9 图，Lerp(Tint,TintNight,_IsNight) 插 Tint 全消费者前，槽位 A0/B1/T2/Out3）；环境夜染 _PopArtNightTint=(0.80,0.87,1)（4 图）+天空夜四色。

**素描**：纸 _Tint=(0.93,0.91,0.87) 暖白·墨 _StrokeColor=(0.06,0.06,0.065) 石墨·_HatchTiling=3·_HatchWeight=1（White 车 0.77）·_HatchAngleRotation 度化=45°（轮 -45°）·_StyliedMetallic 全 0（刺白斑灭）·明度层级铁律 胎纸 0.24＜辋纸 0.6＜身纸 0.93。

**CEO 手调特例（还原后必须原样保留）**：M_CarPaint_White：LambertUp=0.297 / SkyUp=0.451 / HighlightBandUp=0.227 / Shadow 近黑 (0.0609,0.062,0.064) / Highlight (1,1,1) / BrushStrength=0 / Curvature=0 / OutlineIntensity=0 / HatchWeight=0.77。M_EXT：LambertUp=0 / SkyUp=1 / HighlightBandUp=0.921 / **BrushStrength=0.374** / Curvature=0.127 / Outline=0.129（墨链开着）。散调活旋钮（HMILit PostOutLine×2+PopHight/PopColor 16-20 处）勿动。

**代表验收读回**（恢复后抽查）：
- M_CarPaint_White：1.2/180/4/0.297/0.451/0.227/45°/(0.0609,0.062,0.064) ✓
- M_Glass_Front：1.1/0.129/0.488/0.62/Shadow(0.18,0.22,0.3)/Mid(0.38,0.42,0.5)/NightMid(0.304,0.3654,0.5)/Curvature 0.037/Outline 0.129
- M_Wheel_1_FL：0.9/-45°/Mid(0.94,0.96,1)/Tint(0.6,0.61,0.64)
- M_INT_Cluster：0.8/Shadow(0.13,0.15,0.2)/AO 0.8
- 12 轮辋=M_Wheel_{1,2,3}_{FL,FR,RL,RR}（M_Wheel_FL=卡钳材≠轮辋）

**sky.mat**（唯一活天空材质·全场景 RenderSettings.skybox 引用）：_TWO_SKY_TEX 关键词已移除·_PopArtSkyGradient=1/GradHeight=0.35/Bands=4/CloudCut=0.3/CloudSteps=2/NightDim=0.4/SkyTexOn=0/MaskBlend=1/SkyDots=1/SkyHatch=0.5·Zenith 日(0.25,0.55,1)/夜(0.075,0.165,0.3)·Horizon 日(0.62,0.78,1)/夜(0.16,0.24,0.45)·CloudColor 日(0.97,0.98,1)/夜(0.5,0.6,0.85)·_Exposure=0.6·_FirstOrSecond=0·_Tint=(0.756,0.814,0.86)·_CloudAttenuation=2.9575/EdgeThreshold=0.42/EdgeWidth=2.5/CloudHatchTiling=8/SkyHatchTiling=5/Layer1=1/SkyColorPref=0.08/CloudLightColor=1.347 HDR·_Tex1=_Tex2=e06f8f0818b934740b9a673f8a477ae7（同图）·PopArtSkyTexDay/Night 空槽待 CEO 拖图。

### 3.7 场景/预制体
- **Launcher.scene**（美漫核心）：5 个 PopArtHullOutline 实例（car_ext_Transform/car_ext 系：主车+AlphaLerp+Battery+DrivingMode+PhotoPicture），序列化值全同：outlineWidth=0.0028/outlineColor=(0.08,0.09,0.12)/useSmoothedNormal=1/outlineClipOffset=0.25/outlineScreenConstant=1/Fade 0/0；outlineHandDrawn 未序列化→运行时吃 C# 默认 0.15/30（预期态）。另含死组件清理（卫生）。
- 车 Variant×2 + Carsetting_model×2 + ThirdPlace.unity：**纯卫生**（死组件清理），非美漫。

### 3.8 卫生件（非美漫·建议一并恢复）
- 7 件 .cs 报错修复（各 2-7 行，diff 在 park key-diffs\cs\）：AIGCAssetConfigManager/AIGCManager/WeatherTimeManager（PlanarReflectionVolume null 守卫重构）/MultimediaPlaceController/NotificationPushCtr/ZeusSingleton/TimeOfDay（DontDestroyOnLoad 根物体守卫）。
- ProjectSettings.asset + ShaderGraphSettings.asset：**0 字节行尾噪声，无需恢复**。
- SplineExtrude×6 + renderTexture×3 + fbx.meta + RubikRT：编辑器再序列化噪声，恢复与否皆可（不建议还原后主动回写）。

### 3.9 bridge（还原禁区）
manifest.json + packages-lock.json 的全部 diff = `cn.tuanjie.codely.bridge 1.0.85` 一项。**还原会断 MCP 桥——必须保住或从 mirror 回填。**

## 4. 挂起项（快照点未完成/待 CEO）
1. ~~玻璃 P0 手术未落盘~~ **已落盘**（15:12 --apply：门边+BandSoft+滑条 11 图全绿·已烤进 mirror）+ P1 墨链 10 图断头**已修**（15:2x fix_b_ink·已烤进 mirror）——恢复后无任何待手术件。
2. 昼夜过渡 1s→2s（ISO 15008）：写入点 Assets\Scripts\Launcher\Manager\WeatherTimeManager.cs DOTween 末参——**metis 团队码未动待点头**。
3. 5 个原厂坏死材质删除待点头（M_Alpha White/M_INT White/M_INT_01/03 White/M_Mirror Sound=HEAD 即坏·零场景引用）。
4. 真机回归清单：GLES3 非逆Z 深度重建 R1 真机验+最坏变体（AlphaLerp+FLAKE+阴影+cookies）+8155 实测+TAA×网点观察。
5. 车机策略三选（机制已备·CPU 闸门=接线点）：行车关/静止超时回写实防烧/白天退网点防摩尔纹。

## 5. 坑录速查（重建/后操作必防 Top15）
1. **PS `>`/`2>` 重定向=UTF-16 炸解码**——git/长输出一律 python subprocess 字节写盘。
2. **git status -z chunk 禁 .strip()**——吃前导空格=路径掉首字符整批假失败。
3. **git checkout 批必须逐文件**——单条坏 pathspec 让整批全灭；仓库根在 metis（Unity/ 前缀勿丢）。
4. **FSJSON 图手术**：多文档流（json.load 炸 Extra data→raw_decode 逐文档）；json.dumps indent=N 首行 0 列花括号会被当新文档→列表条目必须整体绝对缩进+断言 0 列 { 数==文档数；删列表尾条目无后置逗号须回吃前置逗号；多 span 编辑单趟倒序。
5. **图手术验证闸 v2（白板病教训）**：编译零错+读回全对≠链路通——verify 必含①目标块输入边数=1 ②关键链 BFS reachability 到 master ③新增节点出边非零。
6. **SaveAssets 毒化**：AssetDatabase.SaveAssets() 会把全部内存脏资产落盘（PSRM/动画器运行期泄漏态全上盘）——材质批量编辑用 python YAML 或逐文件 SaveAssets(obj)；InkPatternPicker 已内置 sky 泄漏卫兵。
7. **编辑器包虚拟路径≠磁盘目录**：AssetDatabase 用 Packages/com.unity.artassert/、Packages/com.unity.render-pipelines.universal/；磁盘是 Packages/ArtAssert、Packages/frp-pipeline。检索必须 Assets+Packages 双扫。
8. **HLSL**：变量名 line=保留字炸；if 一律裸写（UNITY_FLATTEN 报 unknown attribute）；共享 hlsl 顶部防御 include DeclareDepthTexture.hlsl（幂等 guard）。
9. **贴图默认 m_SerializedTexture 必须 JSON 信封** {"texture":{"fileID":2800000,"guid":"…","type":3}}——YAML 式写法=导入期全材质 GraphErrorShader2。
10. **Tuanjie Shader 无 HasProperty**（用 Material.HasProperty/Shader.FindPropertyIndex）；Global 声明(gpb=False)属性 Material.HasProperty 恒 False——勿误判缺属性。
11. **FindAssets 坑**：t:ShaderGraph 返回 0（shadergraph 不按该类型索引）；t:Material 会把 .shadergraph 误匹配（.mat 后缀过滤）；资产赋值前必 null 守卫+先 refresh。
12. **材质 YAML 列表式浮点行带 "- " 前缀**（旧式 dict 正则漏扫）；空壳材质裸 "m_TexEnvs:" 行=预存炸弹须补 "[]"。
13. **UV7Baker**：prefab 上属性 setter 赋值静默回滚——必须 SerializedObject(FindProperty).ApplyModifiedPropertiesWithoutUndo。
14. **.bak 移出 Packages 时伴生 .meta 必须同移**（孤儿 meta=asset can't be found Error，再 refresh 自愈）。
15. **PSRM=ExecuteAlways 每帧写全局**（frp FRPCore/Runtime/Sky/ProceduralStateRenderManager）——含 PSRM 场景不自举（尊重每场景风格态）；StateRenderer.prefab 在 Assets\Resources_moved=死路（三按钮风格切换断线为既有态，bootstrap 保底）。

## 6. 重建完成判据（验证收口）
1. refresh：控制台仅已知良性白名单（§0 步骤 4）零 Error。
2. 19 图 ShaderUtil：err=0（15:3x 实测过一轮 19/19 err=0·warn=3 已知良性）。
3. 全局量：_StylizedProcess=1/_PopArtProcess=1/_IsCloud=1（EditorArm 自动，可用探针确认）。
4. 材质抽查：§3.6 代表验收读回表逐位对。
5. 渲染器：5 台 HullFeature=1+全 renderer CopyDepthMode=2+Performant RequireDepthTexture=1。
6. 链路专项（v2 验证闸）：HMILitGlass 门2→块边连通+三图 _PopArtBandSoft 存在+**10 图墨链末端 Lerp 出边→BaseColor（ink.in0←总混合.out3）**——正法=chain_audit.py 复跑，真断头应=0（残留死簇全为 §3.1.x 分类件）。
7. 场景 1348 渲染器零 error-shader；Hull 组件 5 实例在位。
8. 视觉验收=CEO 亲自（验证分工令）。

## 7. 附录：工具索引（park\tools\ 前缀=来源目录）
- metis-uya__glass_smooth_surgery.py（--dry/--apply·玻璃 P0）
- metis-uya__night_knob_surgery.py / env_night_tint.py / sketch_knob_surgery.py / mat_tune_batch.py（幂等可复跑）
- metis-sky__graft_v5.py / v5_drive.py / bake_defaults.py / extract_popart.py / compute_cluster.py（v5 簇克隆族）
- metis-uya__audit_popart_20261015.py / park_build_20261015.py（本日审计/建 park）
- chainfix-20261015__chain_audit.py（19 图可达性审计·验证闸工具）/ fix_b_ink.py（B 型墨链接线·幂等）/ trace_reference.py / verdict_probe.py（断头判别探针）
- 备份：metis-uya\glass-smooth-bak-20261015\（P0 前）、metis-uya\chainfix_20261015\bak\（P1 前）、night-knob-bak\、tune-snapshot-20261014\（229 mat+9 图中间快照·已被 mirror 超覆）
- 台账：TUNE-CHEATSHEET-20261014.md / DIAGNOSIS-DOSSIER-v1.md / SKETCH-KNOBS-DOSSIER-v2.md（调参速查/诊断卷宗）

---
*v2 由 2026-10-15 审计+P0/P1 修复实测定稿（audit-report / reachability-report / verdict-probe 三件为原始数据）。恢复操作如与实际文件冲突，以 mirror 字节为准并回写本档勘误。*

---

## 8. v3 素描域还原记录（2026-10-15 16:5x 定稿）

**CEO 令**：「帮我把素描风格化部分全部还原成 git 上最新的，美漫保留不要动！好好甄别！千万不要出问题！」——执行=素描域逐项退回 HEAD 原厂态，美漫域字节级不动。全部落盘，python 电池全绿；Unity 侧终验待编辑器桥复活（见 §8.7）。

### 8.1 甄别定谳总表（素描=还原/美漫=保留）

**素描域还原清单**（对 HEAD 基线 8d6b60446）：
- **材质 174 件键级手术**：218 处值还原+1476 处键删除。素描键全集=_Hatch0/_Hatch1/_HatchToneScale/_TintNight/_HatchTiling/_HatchWeight/_HatchAngleRotation/_StrokeColor/_Tint/_Day_Contrast/_Night_Contrast/_StyliedMetallic/_StyliedSmoothness/_StyliedAmbientOcclusion/_CurvatureIntensity/_EdgeIntensity+六键 GUID 前身族（Texture2D_f5b1096f…×2/Color_f1c1645d…×2/Vector1_50b8ac…/Vector1_753aa7…，HEAD 编译名=GUID、六键正名前写入的旧键）+sky 素描影线键（_CloudHatchTiling 8→HEAD 25=纯素描消费✓；**_SkyHatchTiling 17:3x 勘误回修 30→5**——素描天空影线与美漫 popHatch **共用旋钮**、美漫正典=5〔v2 §3.6 canon〕，素描还原时误伤美漫密度×6，算法体检批发现+运行时复位，磁盘固化挂 Play 退）。值还原含：_HatchAngleRotation 度化 51 件回弧度（如 84.79775→1.48）、Day/Night_Contrast 156 件回 HEAD（0 或原厂散值）、M_CarPaint_White Color_f1c1645d 0.95→**HEAD 0.85（CEO 原厂素描纸调值·回位）**、_EdgeIntensity 0.698→0.663、_StyliedMetallic 12 件回原厂（1/0.5/0.582）。
- **9 张素描图 FSJSON 跨度手术**（CarPaint/Wheel/HMILit/HMILitGlass/Mountains/Lake/Water/ReflectionPalne/Rubik；B 型 10 图+GlassMaster 零素描足迹未触碰）：
  - 删除插入簇（含槽文档/propnode/m_Nodes/m_Properties/分类子项）：h′ 墨量链三节点（OneMinus→Multiply InkWeight←HatchWeight→OneMinus）、ToneScale 乘法（亮度×_HatchToneScale→Hatching.in2）、TintNight 夜纸 Lerp、Wheel/RP 的 Rotate Hatch+propnode、CarPaint 素描折痕簇（PopArtCreaseLine 克隆 CFN+Lerp(SketchCrease)）
  - 复位工厂件（HEAD 原字节）：每图被 knob 批删掉的 _dist Multiply（HatchWeight×|distance|）+3 槽文档+m_Nodes 条目；hatch 槽位边集 in{1,2,7}/out{6} 全数==HEAD；Tint 直连素描 Lerp.in1；Wheel T&O 直连 Add；RP TriplanarUV 直连；CarPaint 素描 Lerp.out3→总混合 9de8074a.in0（crease 前原接线）
  - 素描属性文档整档==HEAD（字段级）：六键 GUID 正名回退（m_OverrideReferenceName 回 'Texture2D_f5b1…' 族）、m_Hidden 回 false（面板瘦身素描项）、m_Value 默认回 HEAD（hatch 贴图默认清空/墨纸回黑白色/对比回 0）、滑条回退（Day_Contrast 0-3→0-1、HatchTiling 0-12→0-1）、度化回退（RotateNode m_Unit 1→0 全 14 处+'HatchAngleRotation (deg)'显示名回 'HatchAngleRotation'）
  - Rubik 达到**语义==HEAD**（doc/edge 零残差）
- **Hatching.hlsl 整件 checkout 回 HEAD**（素描批 guard+log2 钳制两处改动）
- **Hull 素描档扩展回退**（美漫核心描边全保留）：Feature CPU 闸门 stylized||popart→popart-only；shader frag 铅笔灰 lerp→纯墨 return half4(_OutlineColor.rgb,1.0)

**边界判定保留清单**（甄别为非素描·未动，后续勿误伤）：
- PopArtRuntimeBootstrap/PopArtEditorArm 的 `_StylizedProcess=1` 装填=**美漫档全局闸门本体**（StylizedColor 块求值需 stylized=1+popart=1）——非素描支持件
- PopArtInkPatternPicker 的 "Sketch"=MK 排线纹理目录名（美漫墨链资产）
- 材质 GUID 键 `Texture2D_943f80e5…`（65 件 null）=**MainTexture/StyliedAOTex 的 null 覆盖**（非 hatch 六键族）；`Vector1_94faf…`（RP 10 件）=Brightness——保留
- FBX 材质 _MainTex null×12、_AlphaTec、_Night* 工厂夜景键、_BaseColor/_Color/sky _Tint/_Exposure/_FirstOrSecond、_EdgeFade*（v5 溶边族）、_Night 三色族、render-state 键族——全部美漫/卫生/泄漏既有面，保留
- 图残差 changed 文档字段直方图全=美漫域：_PopArt* hidden（面板瘦身美漫项）、_PopArtTilling 滑条修正（0-400+默认 180）、夜三色 hidden、_PostOutLine FloatType、hlslDeclarationOverride（Global 修正）、CategoryData 重组

### 8.2 手术工具（正本在 sketch-revert-20261015\，副本已入 park\tools\ 前缀 sketch-revert-20261015__）
- `revert_sketch_mat.py`：材质键级（HEAD 值还原/无源键删除+逐键断言美漫键术前术后逐位一致）
- `revert_sketch_graph.py`：图跨度手术（字面拼接：还原件=HEAD 原字节/拆除件=当前字面切除/bypass 边=克隆现边换 id；断言=FSJSON 全文重解析+doc 计数+0 列花括号+边集 multiset+popart spot docs 不变+槽位规则+丢源闭包）
- `verify_post.py`：盘面独立终验（素描属性==HEAD 字节/hatch 槽边集==HEAD/mul 复位/353 材质素描键==HEAD 或消失/无 ToneScale/TintNight 残留）
- `changedoc_hist.py`：残差字段直方图（证明剩余差异全在美漫域）
- 勘查链：recon1/2/3+analyze1/analyze2（图素描链逐节点逐边取证，含每图 h′ 簇/ToneScale/夜纸/旋转/Multiply id 全录）

### 8.3 验证证据（2026-10-15 16:4x 实测）
- verify_post：**ERRS=0**（353 材质 bad=0；9 图素描属性/hatch 槽/mul 复位全过；Rubik 语义==HEAD）
- 手术账目逐图对账：CarPaint 增 198→163（-35=删文档数）/删 98→94（+4=复位件）；Wheel 435→403/5→1；HMILit 379→354/5→1；HMILitGlass 407→382/4→0；env4 图 41→16/4→0；RP 49→16/4→0；Rubik 25→0/4→0——全部吻合
- diff 对账（Wheel 实测）：术前 vs HEAD=47626 行 → 术后=46320 行（净减=素描拆除量；巨型 diff 数=v5 簇+git 对 FSJSON 的匹配特性，**非手术损伤**——排查虚警实录：先查行尾（全 LF 原生无损）再对术前备份量 diff 定谳）
- 坑录新增：python 文本模式读写大文件前先验行尾（本例全 LF 无损）；`git diff --stat` 对 FSJSON 巨簇文件行数严重失真——归因必用"术前备份 vs HEAD"对照法

### 8.4 park v3 物料（已重建）
- `mirror\` 535 文件=**新正典（美漫保留+素描原厂）**·robocopy /E 直映射仓库根
- `mirror-v2-fullstate\` =素描全量态（v2 镜像改名保留·反悔药：想恢复素描调优态从此目录回填）
- `full-worktree.patch` 11.3MB（对 8d6b60446·术后态）·manifest.json/sha256 已更新
- 双保险：`sketch-revert-20261015\bak\`（逐文件术前态：174 mat+9 graph+Hull 两件）+`full-worktree-pre.patch`（术前全量 diff）

### 8.5 挂起：Unity 侧终验（编辑器桥断）
编辑器进程活着但 MCP 监听器随脚本域重载消失（先例=10-14 Hull 批）。桥复活后补验四件：①refresh 控制台仅已知良性白名单（节点版本×2/_MainTex Assert/Autodesk×2/ReflectionPalne·HMILit·Mountains smoothstep×3）②ShaderUtil 9 图 err=0 ③readback 探针（新材质 GetTexture("_Hatch0")=null+Shader.FindPropertyIndex("Hatch0")<0 即六键回退生效；M_CarPaint_White Color_f1c1645d=0.85）④chain_audit 复跑零真断头。

### 8.6 素描原厂态行为预告（CEO 视觉自验基线）
素描档=HEAD 工厂态：Hatch0/1 空→0.5 灰平涂无笔触；无外轮廓（Hull 仅美漫档画）；对比/纸墨=工厂散值；Inspector 六键回 GUID 名（调参需按 HEAD 编译名或临时正名）。美漫档=与还原前逐位一致（popart spot 断言+材质美漫键断言全过）。
