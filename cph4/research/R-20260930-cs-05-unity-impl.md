# R-20260930-cs-05-unity-impl — Unity 城市级实现技术面（CEO 令 2026-09-30·cs-city 波）
> 溯源：CEO 令 2026-09-30 原话（见上）·消费方=City3D 重构主线 R0-R6+CitySim 仿真层（纯 C# 升档路径）·判据预注册=Q1 Unity 大场景组织/剔除/LOD/流送官方实现带源/Q2 agent 仿真的 Unity 实现选型（纯 C# vs DOTS/Burst 升档判据）带源/Q3 俯视角 512m+URP14+WebGL 转译 ≥8 条
> 验证声明：实读 20 次预算打满（search 6·fetch 14）·直读成源 A×9（docs.unity3d.com 2022.3 手册/脚本API/包文档）·检索片段补证 A×4/C×3·失败面透明见文末·三态=确认/推测/待证

## 一、大场景组织与剔除面（Q1）
- Occlusion Culling（A·Manual MultiSceneEditing 页术语表直读）：官方定义「A process that disables rendering GameObjects that are hidden (occluded) from the view of the camera」＝视点依赖剔除；官方将 occlusion culling data 与 lightmap/NavMesh data 并列为按场景烘焙数据。专页直读三连败（404→curl 后端缺失→301→301→404，根因=2022.3 手册 slug 重构死链，与 09-28 五连同源）。俯视角判定（推测）：L0 320m 高空相机下屋面互遮弱→收益低；仅 L2 24m 街景密集高层间有实际遮挡收益；且烘焙按场景计费→拆 chunk 场景会放大烘焙成本。2022.3 可用（非 Unity 6 专属）。
- CullingGroup API（A·ScriptReference 直读）：官方定位「Describes a set of bounding spheres that should have their visibility and distances maintained」——C# 侧包围球视锥+距离带（SetBoundingDistances）剔除：onStateChanged 事件回调/IsVisible 查询/QueryIndices 批查/targetCamera 锁定/enabled 暂停；不参与渲染路径＝模拟侧降频的官方通道。
- LOD（A·Manual class-LODGroup 直读）：LODGroup=逐 GameObject 组件，阈值=「ratio of the GameObject's screen space height to the total screen height」；交叉淡入=Fade Mode→Cross Fade，官方措辞「Unity usually implements the cross-fading by using either screen-space dithering or transparency」，时间驱动（Animate Cross-fading）或 Fade Transition Width 位置驱动两式；官方「For the last LOD level, there is no cross-fading: the current level just fades out」＝末档即剔除位。官方无 chunk 级 LOD 管理 API（逐件语义）→chunk 级须自管。
- Impostor/billboard（A·LODGroup 页+C 检索）：URP14（2022.3）核心无 impostor 组件（absence 主张=待证）；官方支持路径=LOD 末档挂 Billboard Renderer（手册实测配文「Billboard Renderer for LOD 3」）；社区 impostor 工具链要求 Unity 6000+/URP17.3+（C·GitHub ImpostorSystem）；官方包域 Pixyz industry toolkit 可烘 impostor（A·检索片段·工业数据域非游戏线）。→原生 impostor=Unity 6 版本域·标注版本不可用；替代=低模壳+emission 窗灯/VAT（alive3d-04）。
- 场景组织/流送（A·Manual MultiSceneEditing+Addressables 1.21 直读）：官方措辞「If you need to create large streaming worlds or want to effectively manage multiple scenes at runtime, you can open and edit multiple scenes」；烘焙数据（lightmap/NavMesh/occlusion）可多场景同烘。Addressables.LoadSceneAsync 内部走 SceneManager.LoadSceneAsync，loadMode 明文支持 Additive（官方示例=加载后 OnDestroy 卸载释放；Single 则卸当前场景并 UnloadUnusedAssets）。Unity 6 才有官方 Large Worlds 大世界指引·版本不可用。
- 合批边界（A·Manual DrawCallBatching+SRPBatcher 直读）：静态合批 URP=Yes（官方表）+警语「static batching incurs memory and storage overhead」；动态合批=CPU 变换顶点仅小网格；SRP Batcher=「reduces the CPU time Unity requires to prepare and dispatch draw calls for materials that use the same shader variant」（Built-in No/URP Yes）；**GPU instancing 与 SRP Batcher 互斥**（官方原句「if you want to use GPU instancing, which isn't compatible with the SRP Batcher」——须 Graphics.RenderMeshInstanced 或手动摘除兼容性）；MaterialPropertyBlock 会摘 SRP Batcher 兼容（SRP 下禁用）；Skinned Mesh Renderer 不入合批（官方明文·交叉印证 alive3d-01）。

## 二、仿真实现选型面（Q2）
- 纯 C# vs DOTS（A·Entities 1.0 文档直读+unity.com/dots 检索片段）：官方定位「data-oriented implementation of the Entity Component System (ECS) architecture」；Entities 1.0 官方要求「Unity version 2022.3.0f1 and later」→DOTS 在 2022.3 引擎=1.0 定版可用（非版本不可用·团结包仓库可用性待验证=M）；官方措辞「data-oriented framework compatible with GameObjects」＝混合/渐进升档合法。社区向佐证（C）：千级 GameObject 即现性能压力、DOTS 面向 10 万级实体。「DOTS 非银弹」官方原句未直读＝待证（e-book 需另读·不采信记忆）。
- Job System（A·Manual JobSystem+WebGL Advanced overview 直读）：官方定位「write simple and safe multithreaded code so that your application can use all available CPU cores」；**WebGL 官方限制原句**「Managed (C#) threads aren't supported due to the lack of a multithreaded garbage collection feature in WebAssembly…anything in the C# System.Threading namespace isn't supported」+「must run on a single C# thread」（实验性 Native C/C++ Multithreading 需 COOP/COEP 响应头+SharedArrayBuffer〔PlayerSettings.WebGL.threadsSupport·A 直读（cs-10 补证 09-30：2022.3 页=EXPERIMENTAL 仅原生 C/C++ 级·C# 全不可；6000.6 页=去 EXPERIMENTAL+Burst 编译 C# jobs 可跑独立线程·防线二抽验过）〕）→**Job 并行在 WebGL 主路径无收益**，「先 Job 化热路径」仅桌面端有效。
- 群体部分模拟（A·CullingGroup 直读）：Unity 官方侧机制=CullingGroup 视锥可见性+距离带 onStateChanged 事件→「视锥内全模拟/屏外降频 tick」为官方 API 支持路径（事件驱动·非轮询）；CS 侧先例由另一件承接，本件不重复。
- NavMesh（A·Manual 术语表直读+检索）：官方定义「A mesh that Unity generates to approximate the walkable areas and obstacles in your environment for path finding and AI-controlled navigation」＝步行域寻路语义，非车道/交规语义；AI Navigation 包=runtime/edit-time 烘焙+动态障碍+links（A·6000.2 手册检索片段·同一包线）；论坛实测（C）：导航系统内部已 Job 化、voxel size 影响复杂度、大规模有性能坑。→佐证已判负项：城市交通不用 NavMesh。

## 三、施工转译面（Q3·≥8 条）
1. Occlusion Culling：L0 俯视档判负（屋面互遮弱+烘焙按场景计费）；仅 L2 24m 街景档实测遮挡省 draw>10% 才烘焙——判据=Renderer stats 烘前烘后对比（推测·可验收）。
2. CullingGroup→CitySim：agent 包围球注册单组，onStateChanged 屏外降频（tick 降至 1/10）+距离带三档对齐相机 L0/L1/L2——判据=agent>200 且帧预算超支才启用（官方 API 零渲染开销）。
3. LOD：Synty 单栋几百~2千面→不逐栋挂 LODGroup；相机三档=天然 LOD（L0 远档用低细节件集）；仅地标高层超预算时挂 LODGroup（Cross Fade=dither 路径·URP14 支持）——判据=单帧三角数超 WebGL 预算。
4. Impostor：版本不可用（Unity 6 域）→远天际线=低模壳+emission 窗灯（city-3d-lighting 件）+LOD 末档 Billboard Renderer（官方支持）+动画件 VAT（alive3d-04 件）。
5. 场景组织：512m=单场景+chunk prefab 实例化，不启用 additive 流送（烘焙数据按场景计·拆场景放大烘焙/同步成本）——判据=世界>2km 扩容才走 additive+Addressables.LoadSceneAsync(Additive)。
6. 合批组合：建筑壳静态合批=关（官方内存开销警语×WebGL 内存红线）→SRP Batcher 主路径+材质共享（同 shader variant）；重复小件=Graphics.RenderMeshInstanced（官方指定·与 SRP Batcher 互斥·沿 lowpoly3d-01 优先级链）；全管线禁 MaterialPropertyBlock。
7. 仿真架构：纯 C# 维持（WebGL 单 C# 线程封死 Job 并行收益→升档第一优先=算法降频/事件驱动，非 Job 化〔cs-10 补证 09-30：本条对团结 2022.3.62t15 基线维持成立；Unity 6+threadsSupport 域 Burst jobs 有条件并行收益——引擎基线变更时重判〕）；ECS 仅在 agent 万级+非 WebGL 目标双条件才立项（CSL2 先例〔升 A·cs-10〕+官方海量定位同向·团结包仓库可用性先验证）。
8. NavMesh 限域：城市交通=车道图 A* 维持判负（官方「walkable areas」定义佐证）；NavMesh 允许域收窄=32m 单 chunk 内模块壳室内步行寻路——判据=室内 agent<50/单壳。
9. 群体屏外降频：视锥内全速/屏外降频=官方 CullingGroup 事件路径（非轮询）——与 alive3d-01 群体性能件衔接，勿重复施工。

## 四、结论应用表（research-protocol §二.1 强制·落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| Occlusion Culling L0 俯视判负·L2 条件烘焙 | 决策呈报（City3D 渲染决策） | 确认（判定=推测·判据可验收） |
| CullingGroup 屏外降频进 CitySim | 任务单（CitySim 升档任务） | 确认 |
| Impostor 2022.3 版本不可用→替代链 | 判负留痕 | 确认 |
| WebGL 单 C# 线程→Job/ECS 升档判据加注 | 法文修改（CitySim 升档路径法文） | 确认 |
| DOTS Entities 1.0 可用性（2022.3.0f1+·团结仓待验证） | 决策呈报 | 确认（M 存疑点标注） |
| NavMesh 城市交通判负（官方定义佐证补源） | 判负留痕 | 确认 |

- 更新记录：T0 骨架落盘（早落盘律）→T1 采集完成（20 读预算打满·search 6/fetch 14）→T2 Q1+Q2 落盘→T3 Q3+结论表+终稿化（行数帽验收）。
- 失败面：①Occlusion Culling 专页三连未达：fetch_content 404（重定向死链）→curl 重试律不可执行（curl_cffi 未装·工具面事实）→web_fetch 301→301→404；根因=2022.3 手册 slug 重构死链（与 09-28 五连同源），官方定义改经 MultiSceneEditing 术语表直读采得（A）。②DOTS 首次搜索无果（DuckDuckGo bot 拦·换措辞后成）。③「DOTS 非银弹」官方原句待证（e-book 未读·预算尽·不采信记忆）。④URP14「无 impostor 组件」为 absence 主张（手册未见·待证）。⑤团结引擎包仓库 Entities 可用性未验证（M）。
