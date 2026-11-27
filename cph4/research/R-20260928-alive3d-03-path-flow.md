# R-20260928-alive3d-03-path-flow — 路径流动族技法（CEO 令「让硅基城市真正的活起来」·活性三波③）
> 溯源：CEO 令 2026-09-28·消费方=活性升维方案循环活面+细胞活通勤流·判据预注册=Q1-Q3
> 验证声明：实读 20 次（fetch 14+搜索 6）·成源 A12·C1（社区佐证）·待证 ⬜3（团结注册表收录/包内 LICENSE/WebGL compute 实测）·失败面：splines@2.5 spline-animate.html 404×1（换径 @2.8 API 页成）；VFX@14.0 SysReq 页无「WebGL」显式原句（判负改依 compute/SSBO 硬要求链）
> 版本锚：Unity 2022.3 / URP 14 官方文档为准；团结引擎 2022.3.62t15f1=2022.3 中国版；WebGL 30fps 底线

## 一、Q1 答面（Unity Splines 包核验）
- 包名/安装：com.unity.splines，**非引擎内置，必须 Package Manager 另装**——原文「Before you can use Splines, you must install the Splines package from the Package Manager」；页言支持 Unity 2022.1+ ⇒ 含 2022.3【确认 A：docs.unity3d.com/Packages/com.unity.splines@2.5/manual/index.html】
- 版本：官方注册表 2.6.0→2.9.1 各版 unity 字段=2022.3；全球版 2022.3 Manual「2.8.4 is released for Unity Editor version 2022.3」（页更新 2026-07）；docs.unity.cn 中国版 Manual 冻结「2.5.2 is released for Unity Editor version 2022.3」（页版权 2023）——团结引擎预计跟中国档 2.5.x ⬜待证·装机首验【确认 A 双源直读·差异如实注记】
- 依赖：2.8.4/2.9.1 manifest=com.unity.mathematics+imgui 模块+settings-manager，**无 Burst**（Burst 仅 1.x~2.0.0-pre 依赖，2.0.0 起移除）⇒运行时=纯托管 C# 数学，WebGL「must run on a single C# thread」单线程托管环境可跑【确认 A：packages.unity.com manifest+2022.3 Manual/webgl-technical-overview】
- API 面（沿样条移动官方组件/求值）：**SplineAnimate**=「A component to animate an object along a spline」（Container/Duration/MaxSpeed/Loop/Alignment/Easing/Play/Pause/Restart/Completed 事件）【确认 A：docs.unity3d.com/Packages/com.unity.splines@2.8/api/UnityEngine.Splines.SplineAnimate.html】；求值=SplineUtility.EvaluatePosition(spline,t)「Return an interpolated position at ratio t」+Evaluate 三合一（官方注明比分开调用快）+SplineContainer 世界空间求值法【确认 A：@2.8/api/UnityEngine.Splines.SplineUtility.html】；另有 SplineInstantiate 沿样条铺件【A：注册表 changelog】
- URP 无关性：manifest 零渲染管线包+组件皆普通 MonoBehaviour（命名空间 UnityEngine.Splines）⇒与 URP/HDRP/Built-in 无关【确认 A（manifest+API 直读）】；2.6.0 官方已修 SplineContainer 求值 GC 分配（SPLB-246）⇒2.8.4 档无 GC 遗留【A：changelog】
- 许可：manifest 无 license 字段；UPM 官方分发随 Unity 条款；包内 LICENSE 文件未直读 ⬜待证

## 二、Q2 答面（轻量路径移动定谳·场景=几十~几百实例·全既定正交路线）
- waypoint 队列插值：每实例每帧 1 次 Vector3.Lerp（官方定义「most commonly used to…move an object gradually between those points」=a+(b-a)*t 少量乘加）+段推进判断；零包依赖零 GC（缓存 Transform）；8m 正交骨架 90° 转角=折线天然拟合【确认 A：docs.unity3d.com/2022.3/Documentation/ScriptReference/Vector3.Lerp.html】
- 样条求值移动：每实例每帧 1 次 EvaluatePosition(t)（同量级常数数学）；SplineAnimate 即插即用，附 Loop/Easing/Completed 事件语义【确认 A：SplineUtility+SplineAnimate API】
- 直线 tween：仅覆盖单段；多段路线串联后=waypoint 方案退化形；引第三方 tween 库=新增依赖，本场景无收益 🟡
- 开销对比定谳（无官方微基准故不给数字）：三者皆每实例每帧 O(1) 少数浮点运算，几十~几百实例同在预算内；决定项=依赖复杂度+数据面生成成本——路网/作息/机队事件可直生 waypoint 列表 ⇒ **主技法=waypoint 队列插值**；Splines 求值列为「艺术曲线流」备选（正交网格无需曲线，不为主）
- NavMeshAgent 判定：职责=NavMesh 动态寻路+避障（SetDestination「triggering the calculation for a new path」/pathPending/obstacleAvoidanceType）【确认 A：docs.unity3d.com/2022.3/Documentation/ScriptReference/AI.NavMeshAgent.html】；**判据：需要 NavMesh ⇔ 移动体须运行时求解未知路线或动态避障**——本线三件演出全为既定路线数据投影，无一满足 ⇒ 判负留痕（WebGL 单线程下省 navmesh 烘焙 CPU/数据内存+每 agent steering；运行时烘焙 WebGL 支持未核 ⬜，因不采用不承重）

## 三、Q3 答面（街带光流选型判据·硬前提=URP shader WebGL 可实现）
- 硬前提 A 级锚：URP Unlit「optimal for lower-end hardware」「uses the most simple shading model in URP」；Additive 混合官方注「good for holograms」；GPU Instancing 同几何同材质合一批「This makes rendering faster」【确认 A：docs.unity3d.com/Packages/com.unity.render-pipelines.universal@14.0/manual/unlit-shader.html】
- A 路面 UV 流动：Unlit 自带 Tiling/Offset 即可驱动贴图滚动（零自定义 shader）【A：同页 Surface Inputs】；但语义=整条街统一呼吸，非「A→B 离散转移脉冲」；逐街独立方向/相位需多材质实例，破「同材质合批」条件 🟡——降为全街氛围辅层
- B 发光粒子拖尾：VFX Graph 判负——官方硬性最低要求「Support for compute shaders」+SSBO，且 URP 档「not yet out of preview」「only supports a subset of platforms that URP supports」「only supports unlit particles」【确认 A：docs.unity3d.com/Packages/com.unity.visualeffectgraph@14.0/manual/System-Requirements.html】；WebGL 2.0 API 无 compute 阶段无法满足 ⇒ 死路【🟡常识级+装机验证 SystemInfo.supportsComputeShaders==false ⬜；社区佐证 C：discussions.unity.com 实测帖】；CPU Particle System Trails 模块（沿粒子运动路径落顶点成带）为核心组件无平台限制记载 WebGL 可用【确认 A：docs.unity3d.com/2022.3/Documentation/Manual/PartSysTrailsModule.html】但贴合精确街路须逐发射器脚本驱动，开销与工程量高于单物体方案 🟡
- C 移动发光条：Unlit+Additive 发光 quad/条带（贴路面上方微抬）沿 Q2 waypoint 代码移动；1 个 TRANSFER 事件=1 实例 spawn→行进→到达销毁；同材质同 shader 走 GPU Instancing 合批【A：unlit-shader 页】；事件语义精准=「一个数据包从 A 到 B」
- 定谳：**C 为主选**（性能/工程量/事件语义三维最优）；A 仅限非事件氛围层；B 判负（WebGL 硬前提失败·决策留痕）

## 四、结论应用表（落点四选一）
| # | 判定 | 证据强度 | 落点 |
|---|---|---|---|
| 1 | Splines=另装包·中国档 2.5.2/全球档 2.8.4·URP 无关·纯托管数学 WebGL 可跑 | A（manifest+双 Manual+API 三直读） | 任务单：包准入+装机首验项（团结注册表收录/求值 GC） |
| 2 | 路径技法=waypoint 队列插值（SplineAnimate 备用）；NavMesh 判负（既定路线⇏寻路） | A 级 API 锚+工程定谳 | 任务单：三件演出统一移动规格（机器人出动=事件驱动/通勤流=作息窗口投影） |
| 3 | 街带光流=移动发光条（Unlit+Additive+GPU Instancing）；UV 流动限氛围层；VFX Graph WebGL 判负 | A 级硬前提+设计定谳（WebGL 无 compute 🟡+装机验证项） | 任务单+决策呈报：WebGL 演出技法红线（VFX Graph 禁入演出面） |

- 更新记录：T0 骨架落盘 2026-09-28→T1 Q1 域落盘（含 Q2/Q3 锚点）→终稿 Q2+Q3 域补全+应用表（20/20 预算采毕一次成稿）
- 防线二（主会话 2026-09-28 22:4x）：两承重主张直验过——SplineAnimate API 页全属性逐字命中；VFX Graph System-Requirements 页 compute+SSBO 原句命中（docs.unity.cn 直读·与波②双源互证）。
