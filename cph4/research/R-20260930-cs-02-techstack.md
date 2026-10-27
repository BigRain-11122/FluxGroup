# R-20260930-cs-02-techstack — 都市天际线技术架构面（CEO 令 2026-09-30·cs-city 波）
> 溯源：CEO 令 2026-09-30 原话「全面调研都市天际线等，硅基城市的建设，按照他们的技术和逻辑等开展，利用我的polygon资源」·消费方=City3D 重构主线 R0-R6+CPH4 Labs 渲染底座·判据预注册=Q1 CS1 引擎/渲染/模拟技术栈带官方源（LOD/instancing/agent 规模）/Q2 CS2 技术增量与性能争议（引擎/模拟架构/官方回应）带源/Q3 俯视角 512m+URP+WebGL 城可抄渲染/性能律 ≥8 条
> 验证声明：实读尝试 20/20（search 8+fetch 12；成功 11·失败 9 全列文末）。成源 14 条=A×1/B×6/C×6/M×1。关键结论 A/B 双源=两代引擎均 Unity、CS1 65k agent 帽；CS2 ECS=升 A〔cs-10 补证 09-30：官方三源已获——官方维基 ECS 专页直读+CO 官方社媒原句+Unity Unite 2024 官方演讲·防线二抽验过；「DOTS」字样维持 C〕；CS1 大版本/instancing/线程寻路=判负留痕。

## 一、CS1 技术栈面（Q1）
- 引擎：Unity【确认·B 双源】=en.wikipedia.org/wiki/Cities:_Skylines 信息框 Engine=Unity + skylines.paradoxwikis.com「developed in Unity3D」；大版本号未获权威源→判负留痕（M：社区泛称 Unity 5.x，勿采信）。官方设计目标=引擎模拟近百万市民日常（维基引官方）。
- 规模帽：人口硬帽 2^20=1,048,576【C】；活跃 agent 帽 65,536(2^16)【B+C 双源：维基 CS2 页「前作 ~65,000 市民同时渲染」+Reddit/Steam 互证，mod 不可破】；默认 9 格 33.18km²、mod 扩 81 格 324km²【B：维基】。
- 局部模拟：每 tick 仅完整模拟 ~1024 可见市民、~256 不可见市民，是否出门由 RNG 决定【C：Reddit r/CitiesSkylines 逆向帖 4anz92】；寻路细节/多线程化未获源→待证，不采信记忆。
- 资产工程律（C：cslmodding.info/asset/building/，对官方 Asset Editor 实测汇编）：主 mesh 顶点硬帽 65,536；三角面「按体量保守、以 vanilla 建筑为参照」+Mesh Info 工具计数；LOD mesh 必备，缺省时游戏自动生成但有视觉风险；**全城 LOD 纹理运行时合并单张 atlas**（LOD UV 必须 0-1 禁平铺防串图）；贴图 2^n 幂/同批统一分辨率/下限 32×32；夜窗=illumination 通道随机亮窗而非实灯。
- 渲染：tilt shift 移轴后处理营造俯视纵深【B：维基】；GPU instancing 在 CS1 的用法未获源→待证。

## 二、CS2 技术增量与性能面（Q2）
- 引擎：Unity【B：维基 CS2 页「continues to use the Unity engine」】。架构=Unity ECS/DOTS 为基石：全部系统（LoadGame/AutoSave/BoardingVehicle/BulldozeTool…含 UI 系统）皆 ECS System，入同一有序大表按 SystemUpdatePhase 枚举分期执行（Rendering/PreTool/GameSimulation…），UpdateAt/Before/After 定序【A（cs-10 补证 09-30·防线二抽验过）：官方维基直读「Systems are an integral part of Cities: Skylines II」+CO 官方社媒原句+Unity Unite 2024 官方演讲三源；反编译 wiki 共识保留为 C 级佐证——「DOTS」字样官方句未现、Burst/JobSystem 组合维持 C】；模拟经 Burst 编译 Jobs 加速【C：r/cities2modding】。
- 规模增量：默认 441 格 171.33km²（mod 扩 529 格 205.52km²）；无 agent 硬帽、上限=玩家硬件【B：维基】；寻路按路径长+成本+舒适+偏好而非纯距离【B：维基】。
- 性能争议与官方回应：发售前官方声明（A：Paradox 论坛 Modding & Performance FAQ 原帖 1601872，全文经 Steam 转载帖核录）承认「未达我们目标的基准…现在发布仍是最佳前进方式」，并将给出「对体验影响极小但显著提性能」的画质配置；目标 30fps【B：gamereactor】。发售补丁 1.0.11f1(2023-10-26)：LOD 独立于渲染分辨率、雾/景深/全局光照优化【C：cs2.paradoxwikis Patch_1.0.X 检索快照】。后续 City Corner #4：GPU/CPU 双瓶颈归因、LOD 与水体模拟优化、内置基准测试工具【B：vortexgaming 报道】。发售即无 Steam Workshop、改跨平台 Paradox Mods（含主机资产 mod）、编辑器 beta 后置【A：同官方声明】。
- CS2 渲染管线归属（HDRP/URP）、shader 编译卡顿归因、官方资产三角面预算：未获源→待证（cs2.paradoxwikis Asset_Creation_Guide 存在但被拦，未录数字）。

## 三、施工转译面（Q3·≥8 条·俯视角 512m+URP+WebGL）
1. LOD 必备律：CS1 缺 LOD 则游戏自动生成、有视觉风险（C cslmodding）→ 三查闸增设「LOD 必备」硬检查。
2. LOD 图集律：CS1 全城 LOD 纹理运行时并单张 atlas（C）→ 我方 L1/L2 档共享材质图集+SRP Batcher 合批（佐证在册 SRP Batcher 优先律）。
3. 顶点帽律：CS1 单 mesh 65536 顶点硬帽+「对照 vanilla」计面法（C）→ 资产入库设三角面帽并登记（Synty 百~千面量级远低于帽，设帽为闸非瓶颈）。
4. 纹理规格律：2^n/统一分辨率/32×32 下限（C）→ 贴图规格闸并入 asset-audit。
5. 亮窗纹理律：CS1 夜窗=illumination 通道随机亮、非实灯（C）→ 佐证窗灯走 emission 五色律，禁加动态点光（对照 9-16 灯帽）。
6. Agent 帽律：CS1 65536 硬帽 mod 不可破（B+C）→ 群体系统先设总量预算帽再谈密度（对照 alive3d-01）。
7. 局部模拟律：CS1 每 tick 仅 ~1024 可见/~256 不可见全模拟（C 逆向）→ sim 视锥内优先、屏外降频/冻结。
8. 成本寻路律：CS2 寻路=路径长+成本+舒适+偏好（B）→ NPC 走 waypoint 权重图而非纯最短路。
9. LOD 距离解耦律：CS2 补丁把 LOD 独立于渲染分辨率（C）→ LOD 切换锚定相机三档固定米数（L0 320/L1 110/L2 24），不随像素比漂移。
10. 性能闸先行律（反例）：CS2 官方承认未达基准仍发布、后补丁追优化（A）→ R0-R6 每阶段 30fps 底线验收前置，不「先发布后优化」。

## 四、结论应用表（research-protocol §二.1 强制·落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| LOD 必备/图集/顶点帽/贴图规格（律 1-4） | 任务单：三查闸+asset-audit 细则修订 | 待发 |
| 亮窗=emission 非实灯（律 5） | 法文修改：不修改，city-3d-lighting 五色律佐证留痕 | 已闭合 |
| Agent 帽+局部模拟（律 6-7） | 任务单：对照 alive3d-01 增预算帽/降频条款 | 待发 |
| LOD 距离解耦+性能闸先行（律 9-10） | 决策呈报：渲染底座 LOD 判例与阶段验收闸呈 CEO | 待呈 |
| CS1 大版本/instancing/线程寻路/CS2 渲染管线与官方资产预算 | 判负留痕：未获权威源，勿采信记忆 | 已留痕 |

- 更新记录：T0 骨架落盘（早落盘律）→ T1 Q1 采齐即更新 → T2 预算尽（20/20）Q2/Q3/Q4 终稿化。
- 失败面（9 次，透明）：search×3 被 DuckDuckGo bot 拦（CS1 引擎版本×1、CS2 DOTS×2）；fetch×6 失败=cs2.paradoxwikis Asset_Creation_Guide/Patch_1.0.X、forum.paradoxplaza.com CEO 帖、skylines.paradoxwikis.com/Modding（均为前端校验拦截）、pcgamingwiki CS1/CS2（403）。连带后果：CS1 Unity 大版本、GPU instancing 用法、寻路线程化、CS2 官方 ECS 表述、渲染管线归属、官方资产三角面预算=全部待证/判负。

〔09-30 补证收口（R-20260930-cs-10-verify-addendum）：其中「CS2 官方 ECS 表述」已升 A——官方维基直读+CO 官方社媒原句+Unity Unite 2024 官方演讲三源（防线二独立抽验过）；渲染管线归属官方仅「standard PBR pipeline 变体」句、维持待证；其余项维持待证。〕
