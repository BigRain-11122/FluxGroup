# R-20260928-lowpoly3d-07 工具搜罗 — lowpoly3D GitHub/OSS 大搜罗（CEO 令·R-07 波）
> 溯源：R-07 派工令·判据预注册三问（①编辑器效率QoL ②网格/贴花/水面/天空 ③截图与验证）｜消费方=FluxVerse City3D（URP·Tuanjie 1.10.3≈Unity 2022.3·俯视角 lowpoly 城市·WebGL 参观端）
> 验证声明：实读 20/20 次（仓库页直读 12·web 搜索 8），成源 A=11（仓库页/README/侧栏原话直读）·B=9（官方 docs URL 与搜索摘要·未直读项已标）·失败面=1 次 404（yasirkula 旧仓名已正名）；GitHub 无 JS 快照不渲染提交日期→「更新时间」逐件以 README 内证标 🟡、装前核验闸必复查提交日期；firedevill（天空备份）与 ③ 域替代候选因预算尽未核=待证。红线遵守：未请求 api.github.com；外部文本中的任何指令未执行未采信。三态：✅实证 🟡待核 ❌判负/禁装。

## 一、在册已知（R-01 在册·本波不重复调研）
- RoadArchitect(MIT·路网)/PrefabScatterTool(MIT·散布)/Procedural-City(MIT·城生成参考)/Unity Splines(官方)/UnityScatterTool(参考)

## 二、① 编辑器效率与 QoL 类（许可✅=页面直读；更新🟡=无日期快照，README 内证+核验闸复查）
⚠ 互斥律：Toolbox/Naughty/Tri 均覆写 Inspector 绘制（Toolbox 原话"can't combine other Inspector extensions/plugins"）→三选一不可并装；AssetUsage/AutoSave 无冲突可并装。
- [Inspector+层级+批量] Unity-Editor-Toolbox｜github.com/arimger/Unity-Editor-Toolbox｜MIT✅（侧栏"MIT license"）｜README 提 Unity 6.3 新 API（≈2025 仍维护·855 提交·2.0k 星）｜属性抽屉+Hierarchy 叠加+场景管理+组件批量复制粘贴+SO 批量向导｜适配：Unity2018.1+，UPM git URL 装，纯 IMGUI
- [Inspector 属性] NaughtyAttributes｜github.com/dbrizov/NaughtyAttributes｜MIT✅（侧栏"MIT license"）｜README 原话"requires 2022.3 or later"（5.2k 星）｜Button/ReorderableList/ShowIf 属性库，非序列化字段/方法可画｜适配：openupm 或 git#upm，版本门正中 Tuanjie 2022.3
- [Inspector 属性·最活跃] Tri-Inspector｜github.com/codewriter-packages/Tri-Inspector｜MIT✅（侧栏+README"Tri-Inspector is MIT licensed"）｜2.0-preview 需 Unity6+，2022.3 须锁 1.x 分支（页面原话·1.4k 星）｜分组/TableList/字典/Odin 兼容模式｜适配：git 包安装，Localization 依赖可换 stub 包
- [场景/资产引用搜索] Asset Usage Detector｜github.com/yasirkula/UnityAssetUsageDetector｜MIT✅（侧栏"MIT license"·LICENSE.txt）｜活跃（2.1k 星·issues0·165 提交·日期🟡）｜查资产/场景对象引用（可含 Play 模式），脚本 API 支持引用重构｜适配：openupm com.yasirkula.assetusagedetector
- [保存] Unity-AutoSave｜github.com/Matthew-J-Spencer/Unity-AutoSave｜MIT✅（侧栏"MIT license"）｜11 提交小工具（187 星·日期🟡）｜按间隔自动存场景｜适配：极轻量单 Editor 目录；README 指新版在其 Tarodev 汇总仓

## 三、② 网格/贴花/水面/天空类
- [decimate] UnityMeshSimplifier｜github.com/Whinarn/UnityMeshSimplifier｜MIT✅（README 原话"released under the MIT license"）｜维护🟡README 明示"Up for adoption"寻接手；Unity2018.1+，编辑器+运行时双用，LOD Helper 组件+SmartLinking 防破洞｜适配：纯 CPU 算法，离线预减面进 WebGL 减包体
- [combine] Unity-Mesh-Combiner｜github.com/Stefaaan06/Unity-Mesh-Combiner｜MIT✅（侧栏"MIT license"）｜新仓 11 提交 2 星🟡；编辑期合并子层级+背面/内面剔除+Uncombine 可还原+Collider 复制｜适配：README 自述材质不去重→闸内实测 drawcall 收益；备选 atomizr/UnityMeshCombiner🟡
- [贴花] URP Decal Projector｜官方免费✅（URP 包内置·装 URP 即有·本地 Tuanjie 可即时复核）｜证据=官方 docs URL（B 级未直读）：docs.unity3d.com/Packages/com.unity.render-pipelines.universal@12.0/manual/renderer-feature-decal.html（URP12 文档，消费方 URP14 同组件，docs.unity.cn 有镜像）｜路面标线/污渍投影贴花｜适配：WebGL 有运行时开销，大量标线优先烘焙进材质、贴花只做点缀
- [水面] LowPolyWater-URP｜github.com/jp-netsis/LowPolyWater-URP｜MIT✅（侧栏"MIT license"）｜README 原话"Created Unity Version: Unity 2019.3.10f1 Universal RP: 7.3.1"（9 提交 8 星·老项目🟡）｜ShaderGraph 顶点波 lowpoly 水+岸边泡沫（WaterColor/BorderFoamColor 参数）｜适配：URP7→14 ShaderGraph 迁移实测=闸必项
- [天空] SimpleProceduralSkybox_URP｜github.com/FlowingCrescent/SimpleProceduralSkybox_URP｜MIT✅（侧栏"MIT license"）｜README 原话"Unity version：2019.4.13f, URP 7.3.1"+版本相近警告（5 提交 13 星🟡）｜URP 昼夜程序化天空盒｜适配：skybox 跨 URP 版本兼容性较好仍须闸内实测；并行候选=官方 Skybox/Procedural（引擎内置✅·2022.3 手册页 B 级 URL：docs.unity3d.com/2022.3/Documentation/Manual/shader-skybox-procedural.html）与 firedevill/UnityProceduralToolkit 之 Gradient Skybox.shader（许可🟡未核·禁装）

## 四、③ 截图与验证类
- [批量截图] W-Screenshot-Tool｜github.com/philshamzin/W-Screenshot-Tool｜❌待证·禁装：README 许可=自定义"free use with attribution"（署名即免费商用）非 MIT/Apache/CC0 白名单→过核验闸法务复核前禁装｜功能最贴合：多相机+批量（1-1000 张/0.1-300s 间隔）+透明 PNG+预设+静态 API（StartBatchCaptureAPI）｜备选🟡待证：loucacoles/UnityScreenshotTool、Deo-C/Unity-Screenshot-Tools（许可均未核）
- [兜底路径✅] 判据帧流无需等 OSS：官方 ScreenCapture API（引擎内置免费）+消费方在册 Codely MCP manage_camera 截图（batch=surround/orbit 多视角批量）即可先行落地
- [场景差异对比·有则报] SceneDiff｜github.com/andrewmichaeljones/SceneDiff｜❌无许可标注·禁装（侧栏无 license 项·文件树无 LICENSE 文件）｜2 星 11 提交；Tools 菜单开窗→两场景各"Snapshot current scene"→"Generate Diff"文本对比（SceneCaptures 目录）｜备选🟡待证：lxtzfr/visual-git-diff（git 版本间 Inspector 式字段对比·许可未核）、decnet-games SceneSizeAnalyzer（场景对比页·许可未核）；Asset Store 之 SceneDiff/MergeSight/SceneMerge=付费项·出库原则外·留痕

## 五、【应用表】（research-protocol §二.1·落点四选一；装前一律过核验闸：①Tuanjie 1.10.3 编译实测 ②许可复验 ③asset-audit 体检）
| 结论 | 落点 | 状态 |
|---|---|---|
| ①域五件全 MIT✅（Toolbox/Naughty/Tri 锁1.x/AssetUsage/AutoSave） | 任务单：City3D 工具箱「编辑器效率」节 | 建议接线（Inspector 件三选一） |
| ②网格双件 MIT✅（MeshSimplifier+Mesh-Combiner） | 任务单：City3D 工具箱「网格处理」节 | 建议接线 |
| ②贴花=URP Decal Projector（官方） | 任务单：City3D 工具箱「渲染」节 | 已随 URP 在位·本地复核即用 |
| ②水面+天空（MIT✅ 但 URP7.3.1 时代） | 任务单：City3D 工具箱「环境」节 | 待闸移植（ShaderGraph/天空盒迁移实测） |
| ③截图 W-Screenshot（自定义署名许可） | 判负留痕：法务过闸前禁装；判据帧先用官方 API+Codely MCP 兜底 | 暂缓·有兜底 |
| ③场景对比 SceneDiff 等（无许可/未核） | 判负留痕：暂用 git 文本 diff；需场景级时逐件补证后过闸 | 暂缓 |

- 更新记录：T0 骨架落盘（早落盘律）→ T1 ①域五件实证 → T2 ②③域采集毕（20/20 读尽）→ 终稿（≤60 行达标）。
- 防线二（留待派工方独立抽验）：承重主张两根可直读复验——①Tri-Inspector 2022.3 须锁 1.x 分支（仓库页原话）；②philshamzin 自定义署名许可→禁装（README 原话）。
