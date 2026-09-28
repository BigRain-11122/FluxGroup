# R-20260928-lowpoly3d-05-assembly — Synty POLYGON 装配范式与场景编辑面（CEO 令 P-65 lowpoly3d 调研波第 05 件）
> 溯源：ledger P-65「硅基生命城市 lowpoly 3D 搭建」装配波 2026-09-28·消费方=FluxVerse City3D 装配 SOP+Phase 0 学习清单（URP·俯视角·48 包 Synty POLYGON 在库 P3D_Spike·首批 AD-048/022/015/042/010/039·AD-022 实查=SM_Env_Road_* 全套路面件+转角公寓族·窗=几何色块无自发光）·判据预注册=①Synty 装配最佳实践（demo 构图/街区密度/模块拼接网格/换色法）②场景编辑工程面（blockout→dress/prefab 化与 variants/多场景 additive）③俯视角城市 demo 社区经验（密度数字/镜头角/先学后建流程）
> 验证声明：读数 20/20 触顶（本地 5=技能件 2+R 模板 1+存量 R 件直读 2；外部 15=检索 7+成源直采 8·失败尝试 2 不计·沿 R-02 成源计数口径）·成源 A=5（Synty FAQ·Synty 官方博客·官方教程视频 FAQ 直链·Unity Manual MultiSceneEditing/PrefabVariants）B=2（Level Design Book·镜像店拷）C=8（直采 2：Diversion·eshannaithani；摘要级 6：gamedev.tv·Build 2.0·Unity Discussions×2·镜头角多源×5）·零断言三态：确认 12·推测 1·待证 2

## 一、Synty POLYGON 装配最佳实践（判据①）
- 拼接范式【确认·B+A】官方店拷「Modular sections are easy to piece together in a variety of combinations」（镜像转载 B）；官方教程视频《Modular Buildings in Unity》专讲 Synty 模块化建筑系统（POLYGON Palm City 演示·官方频道带 syntystore 短链·A 存在性）→装配法=乐高式模块拼装。
- 网格规则【确认·C 摘要级】Build 2.0 系统（2021-07-05 随 POLYGON Shops 引入·gamedevbits）「为模块包引入统一横纵网格」为三大变化之一；转角件族在库（AD-022 实查）；网格具体米数官方未公开【待证】→收口=仓内实测 SM_Env_Road_* 件 bounding。
- demo 场景与官方通道【确认·A】每包含 demo scene（镜像店拷 B）；仓内 48 包=75 个 demo=官方构图/密度学习样本源；官方文档面扫描：博客=新闻向（Made with Synty/Humble/jam·直采）、FAQ=商务授权向——官方无 demo 构图与街区密度方法论文【确认·A 通道扫描】→装配知识载体=官方视频教程（Starter Guide+Mixamo 两支 FAQ 直链）+demo 本体；镜像计 331 资产 vs 仓内锚件 728 件（AD-022）——计数以仓内直读为准。
- 换色法【确认·R-02 A×2 承接+C】flat=一张共享渐变图集·换色=挪 UV（R-02 已闭环不重复采）；社区细则=复制材质→调 Tiling/Offset X/Y 挪 UV 选色板（gamedev.tv·C）·坑=整材质挪 UV 连带错色（树干例）；官方路径=3D 软件改件+Photoshop 改纹理（FAQ·A）。
- 编辑授权与支持面【确认·A】FAQ 明文允许任意 3D 软件（Maya/Blender 等）改件用于项目·禁转售改件；官方支持仅 Unity/Unreal（Godot 技术可用无支持）；官方工具链=Maya 建模+Photoshop 纹理→L1 原型改造面合规承接（交付链红线不变）。

## 二、场景编辑工程面（判据②）
- blockout→dress 定式【确认·B+C 双源同构】正典工艺（Level Design Book·B）：blockout（blockmesh/graybox）=简单几何草稿关·「删草稿便宜·扔成品贵」·五法中 modular kit=「乐高式连接预制件」（=Synty 装配的正典工艺位）；Unity 实操四阶段（eshannaithani·C）：①Blockout 简单形状先玩法规→②玩法规测试（移动/相机角/遭遇）→③Art Pass 换成品模型·纹理·光照→④优化（减 draw call/烘焙/碰撞）→俯视角城的相机角必须在白盒期定谳。
- 白盒底座【确认·仓内锚件+C】AD-048=POLYGON Prototype 白盒件族=Synty 自家 blockout 通道（仓内起步组合定位）；Unity 白盒工具=ProBuilder+Polybrush（Unity Discussions·C）。
- prefab 化组织【确认·A·PrefabVariants 2022.3 Manual】模块建筑预制化+Prefab Variant 出楼层/配色变体（variant 继承 base·override 优先·Project 右键 Create>Prefab Variant）；限制=变体不能重排/删除 base 子物体（deactivate override 替代删除）；坑=变体内 apply overrides 会写回 base（官方原文「often not what you want」）。
- 多场景 additive 组织【确认·A+C】多场景同开=大世界流式加载+协作编辑·支持跨多场景同烘 lightmap/NavMesh/occlusion（MultiSceneEditing 2022.3·A）；社区三坑（Diversion·C）：①跨场景引用禁止→按引用边界切场景 ②光照/NavMesh/遮挡数据按场景存→全局灯与相机归属须定死（错放独立场景未烘焙=全黑）③Additive 异步加载（LoadSceneAsync/UnloadSceneAsync）初始化时序。

## 三、俯视角城市 demo 社区经验（判据③）
- 镜头角【确认·C 多源收敛·A 未直采·防线二候选】方位角 45° 四源共识（Unity Discussions/Reddit godot 45-45 律/Roblox devforum·FOV~70/lensviewing）；俯角档=真等距 35.264°（lensviewing 数学口径）·经典俯视斜角 ~60°（Unity Discussions「rotate 45°·tilt typically 60°」+superdocs Angles(60,0,0)）·纯顶视 90°（superdocs）→俯视角城判据=方位 45°·俯角 35°/60° 双档实拍定谳。
- 密度数字【待证·网面零命中】官方与社区均无「每 32m chunk 建筑数/道具数」公认参考数→收口=Phase 0 仓内实测（75 demo 按 chunk 统计出自建密度基线）。
- 先学后建流程【确认·A 通道+仓内底座】开官方 demo→拆 Hierarchy（分组结构/网格对齐/密度）→复制到自建 chunk——P3D_Spike 点开即用+官方 Starter Guide 在册→流程可行；Synty demo 本为第一/三人称构图【推测·Palm City 教程演示形态】→俯视改造须顶面补强（skill 正法承接：屋顶道具/贴花/细高树种）。

## 四、结论应用表（research-protocol §二.1 强制·落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 装配四阶段：blockout（AD-048/ProBuilder）→玩法规与相机角验证→dress（AD-022 成品件）→优化烘焙收口 | 任务单：全盘方案 lowpoly3d-transition-plan.md「装配 SOP」节 | 接线中 |
| 换色细则（Tiling/Offset 挪 UV+连带错色坑）+改件授权（可改禁转售） | 任务单：全盘方案「材质规范」节（承接 R-02） | 接线中 |
| prefab variants 组织律（变体出楼层/配色·慎 apply 回写·deactivate 代删） | 任务单：全盘方案「装配 SOP」节 | 接线中 |
| 多场景 additive 城市组织+三坑（跨场景引用/烘焙归属/异步时序） | 任务单：全盘方案「工程组织」节 | 接线中 |
| 俯视角镜头角判据（方位 45°·俯角 35°/60° 双档·90° 纯顶特殊档） | 任务单：全盘方案「俯视角构图」节+双轨截图判据 | 接线中 |
| Phase 0 编辑器内 demo 学习清单（见下行）·两待证收口位（网格米数/密度） | 任务单：全盘方案「Phase 0」节 | 接线中 |
| L1 注记：demo 拆解与实测=原型/规格研究合规面·交付链红线不变 | 判负留痕→法文红线承接 | 已闭环 |
- Phase 0 demo 学习清单（AD-022 优先）：①开包内 demo 读 Hierarchy 分组结构 ②量 SM_Env_Road_* bounding 收口网格米数 ③按 32m chunk 统计建筑/道具数出密度基线 ④45° 方位×35°/60° 俯角双档试拍接双轨判据 ⑤窗=几何色块无自发光（实查）→夜景演出另案。

## 五、更新记录+失败面+防线二候选
- T0 骨架早落盘→T1 仓内查重（polygon-style/city-tools-02：换色/管线/WebGL/光照面承接不重复采）→T2 Synty 装配域→T3 场景编辑域→T4 俯视角域→终稿 39 行（帽 ≤60 内）。
- 失败面：gamedevbits.com DNS 解析失败（Build 2.0 降摘要级·重访触发器）·docs.unity3d.com MultiSceneSetup 子页 404（烘焙细则由 MultiSceneEditing 页+Diversion 承载）·YouTube 视频页正文不可抓（官方教程文字面=检索摘要级·视频本体未看）·Synty 官方博客无装配方法论文（通道判据·A）。
- 防线二候选（两承重主张待主会话独立直验）：①Build 2.0「统一横纵网格」主张（C 摘要级）②真等距俯角 35.264° 数学口径（C）。
- 调研完成时间：2026-09-28
