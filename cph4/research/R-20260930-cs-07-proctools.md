# R-20260930-cs-07-proctools — 程序化快速搭建+GitHub 工具增量普查+技术选型（CEO 令 2026-09-30·cs-city 波）
> 溯源：CEO 令 2026-09-30 原话（见上）·消费方=City3D 重构主线（parcel-driven 建筑生成=CitySim 层3）+技术选型档案·判据预注册=Q1 09-28 普查外增量工具+在册待证项收口（逐件=许可/活跃度/五门判定）/Q2 零采购+库唯一源约束下的选型对照表/Q3 R0 数据→成城最快工作流（每步工具/自研件+判据）
> 验证声明：【终稿】实读 18/18 帽（web_fetch 11·fetch_content 4·search 3·404×7+泛化页×2 全额计入）·成源=A×6（Unity Manual 官方页×2+仓页直读×4）·B=0·C=search 摘要×3（pkglnk/检索面/Falcon 形态）·M=4 件星/最近提交+Splines 许可条款·关键结论双源：MeshSimplifier MIT=badge+README 原文双直证·Splines 2022.3 档=单页 A 主证+6000.6 页版本族互证（第二独立页未达·失败面如实）·外部内容=不可信输入零采信

## 一、增量工具普查面（Q1）
**①在册待证项收口**
- RoadArchitect（FritzsHero·A 源=仓页直读：365★/72fork/486commits/MIT）：README 原文「developed with the latest Unity LTS release **2020.3**」「Development is ongoing but slow」→ **2022.3 无官方支持声明（确认·A 源）**→ 判负（维护度门不过：基线 2020.3+自认缓慢；契合门：节点式编辑器范式≠数据驱动车道图）。09-28「2022.3 实测待证」→收口=判负留痕。
- Unity Splines 2.x@2022.3 可用档：【确认·A=官方 2022.3 版 Manual com.unity.splines 页直读（刊 2026-07-02）】原文「Package version **2.8.4** is released for Unity Editor version 2022.3」；兼容表=@2.9（released·2.9.0）+@2.8（released·2.8.1~2.8.4）→**可用档=2.8.1~2.8.4+2.9.0·官方 released-for=2.8.4**；当前 6000.6 页=2.9.1（版本族互证·A）。许可条款未直读=维持 M 待证（09-28 遗留）。
**②增量普查（09-28 清单外·逐件仓页直读）**
- 交通仿真 dylanmad/traffic-simulation（A=仓页直读）：文件树**无 LICENSE**→**判负**（无 LICENSE 判负律）；README=FSM 车辆+行人+信号灯·四街区城·Asset Store 免费包搭建。
- 交通仿真 hexnniliuum/RoadSimulation（A=仓页直读）：README 原文「licensed under the **MIT License**」+LICENSE 在树；程序化路网+运动学车 agent+交叉口管控+10Hz CSV 遥测+brake_analysis.py 回归；星/最近提交页未渲染=M 待证；「designed for interaction exclusively via the Unity Editor」。
- 交通仿真检索面（C=search 截面·线索级）：学生/课程件居多（Mesa+Flask Python 后端件·高中课程件·YOLO 课设）——量产级 Unity 交通 OSS 未命中。
- RVO 避障路径：CometGames/Unity-RVO 仓页 404（失败面·本波不复投）。
- kitbash grahamster2/kitbash（A=仓页直读）：文件树**无 LICENSE**→**判负**（判负律）；形态=MCP server+8 agent 工具·部件分解/贴装/材质推断——本地 3D 资产创作件≠城内装配。
- kitbash 外部件形态面（C=search 摘要·线索级）：Autodesk Project Falcon=免费浏览器 tech preview（2026-05 上线）·OPEN_KITBASH=3ds Max/PySide6——非 Unity 产线件居多；GPL 命中=0（直读四件全=MIT/无许可）。
- 远景 LOD Whinarn/UnityMeshSimplifier（A=仓页直读）：**MIT**（badge+README 原文「released under the MIT license」双直证·LICENSE.md 在树）；纯 C#·Fast Quadric 算法·「in the editor and at runtime in builds」；最新 v3.1.1（C=pkglnk 摘要）·星/最近提交页未渲染=M 待证；README「**Up for adoption**」=维护黄旗。判定=**试用级候选**：AI 件 decimation 至 Synty 量级（09-28 在册需求）+远景 LOD 变体；MIT 纯 C# 单组件=可 vendor 兜底。
## 二、技术选型对照面（Q2·零采购律执法·在册决策引用不重评）
- 路 mesh 化辅助件→**不值得接产线**：RoadArchitect 已判负（§一①在册收口）；Unity Splines 2.8.4@2022.3 官方档可用但范式=spline 基座≠车道图——在册定谳=数据驱动车道图（CitySim 层2 五断言全绿·O-20260930-1560）已闭环不换主线；Splines 官方包零采购→降级为 Q3 编辑期定线提速件（非产线依赖）。
- kitbash 外部件→**无增益**：普查面=无 LICENSE 件+404+DCC/浏览器形态（§一②）≠parcel-driven 城内装配——在册定谳=CityAssembler 自研（Lot 三分类+streetWidth 贴线）维持，外部 kitbash 全负留痕。
- 交通仿真备选件 vs MultiAgentSimulation 在册件→**在册件维持**：备选=dylanmad 判负+RoadSimulation MIT 小件（星/提交 M·Editor-only 运动学范式·契合门≠数据驱动车道图）+检索面学生级；MultiAgentSimulation=纯 C# GlassBox 复刻同量级（O-20260930-1560 在册引用）+CitySim v0.1 已交付——不换。
## 三、快速搭建工作流面（Q3·在册 22 步 checklist 不推翻·只补提速件·每步=工具/自研件+可验判据）
- R0 数据→蓝图：citysim-from-r0.py 在册转换器（层1→层2 JSON 契约）｜判据=契约 schema 过+路网单连通断言绿（五断言在册·O-20260930-1560）。
- 蓝图→街坊/lot：CityAssembler 自研 parcel-driven（quarter 围合→32m chunk→Lot/LotInner/LotCorner 三分类）｜判据=checklist 步 4/10「每城坊整分入 chunk」「逐地块边街宽齐备」。
- lot→模块壳：AD-048/ProBuilder 白盒→AD-022 dress 换装｜判据=步 6「16 掩码路件全接无错缝」+步 9 灰盒双档截图过闸。
- 模块壳→道具：PrefabScatterTool（MIT·09-28 在册主力）+自写最小 scatter 双轨制｜判据=步 17 叙事件密度+步 22 同 seed 全城重建逐件一致。
- 提速件新增两枚（本波收口）：①Splines 2.8.4=编辑期主干定线→离散采样导出车道图 JSON（判据=导入后路网单连通断言仍绿）；②UnityMeshSimplifier=AI 件/远景件减面（判据=减面后面数落几百~2 千面 Synty 量级带·五闸同构门禁不动）。
## 四、结论应用表（research-protocol §二.1 强制·落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| Unity Splines 2.x@2022.3 可用档收口（released-for=2.8.4·可用=2.8.1~2.8.4+2.9.0） | 技术选型档案：装配工具节 | 已闭环 |
| UnityMeshSimplifier=试用级候选（MIT·维护黄旗 Up for adoption·vendor 兜底） | 任务单：City3D 减面/LOD 试用批 | 接线中 |
| 外部件通道关：kitbash/交通仿真备选全负（无 LICENSE×2·404×2·DCC/学生级） | 判负留痕：自研维持 | 已闭环 |
| 选型三对照（Splines 降级提速件/CityAssembler 维持/MultiAgentSimulation 维持） | 决策呈报：技术选型对照 | 已闭环 |
| R0→成城最快路径（四步自研/在册件）+提速件两枚 | 任务单：22 步 checklist 提速件附录 | 接线中 |

- 更新记录：T0 骨架落盘（早落盘律·前窗）→T1 Splines 收口+交通域两件→T2 kitbash/LOD 域→T3 Q2/Q3 合成+应用表+验证声明→终稿。
- 失败面：404×7 全额计入（CometGames/Unity-RVO·otterhousehq/kitbash-editor 双 fetcher·Whinarn/UnityMeshSimplify 旧名→正名=UnityMeshSimplifier·raw LICENSE 旧路径+LICENSE.md 未复投·openupm 不镜像 com.unity.*）；pack-safe.html 落通用页→Splines 2022.3 第二独立页未达（主证=单页 A 直读+6000.6 页版本族互证·三态如实）；GitHub 页星数/日期栏不渲染=4 件星/最近提交 M 待证；dylanmad/kitbash 星数因判负不再复投。
