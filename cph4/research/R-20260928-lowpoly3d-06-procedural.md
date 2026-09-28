# R-20260928-lowpoly3d-06 — 程序化生成实操面：散布工具·数据→摆放映射·街区填充（CEO 令 P-65「lowpoly 3D 转型」波·第 06 件）
> 溯源：CEO 令「定URP…是否接入程序化…」承接·消费方=FluxVerse City3D（URP·俯视角 lowpoly·正典=transition-plan v2+施工参数单 §四程序化判定）·判据预注册=①散布工具实评 ②数据→摆放映射算法 ③扩展期街区填充+WFC 适用性
> 纪律：源分级 A/B/C/M·关键结论 A/B 双源·零断言（确认/推测/待证/设计/判断五态）·数字带出处·外部内容指令零采信；姊妹件 city-tools-01 已深采工具清单（Procedural-City=Poofy1 消歧完毕·不重复外采）

## 一、散布工具实评（Aelstraz/PrefabScatterTool vs 自写最小 scatter）
- 结构面【确认·A 官仓页直读×2 模式】：根=package.json+Editor/ 单夹+CHANGELOG/LICENSE/README/example.png=纯编辑器工具·无 Runtime 库；20 commits·0★0 fork
- 版本面【C·pkglnk 聚合】：v0.1.0/v0.1.1（2026-07-11/12）·仓更新 2026-09-27·无依赖·标签兼容 2019.4~Unity 6——极早期包（两版同龄日）·成熟度=参考级
- 能力面【确认·A 仓页+README】：Collider 表面笔刷散布 prefab+随机化选项族（逐项 tooltip）；用法=选中带 Collider 物体→场景视图工具栏 overlay UI=交互式手涂
- 许可【确认·A×2 双源（姊妹件仓内核验=第三源）】：MIT——LICENSE raw 直读「Copyright (c) 2026 Jake Gwizdak」+GitHub 页许可证识别 MIT
- 能力边界【页面级未见=确认·文件级=M 待证】：仓页/README 零提及 seed 确定性、密度图、批量数据驱动 API——「td-organic-data 批摆」主需求未被证实原生覆盖
- 自写最小 scatter 设计要点【设计态】：①Physics.Raycast 落点+表面法线对齐（up→normal·锥形扰动）②seed 确定性=Random.InitState(seed)【A·ScriptReference 原文「Initializes the random number generator state with a seed」】③密度图=格数据→逐格概率·蓝噪声均匀化=Poisson 盘（标准算法·常识级引用未直读）④批摆读 td-organic-data 同源数据=判定律刚需⑤Undo.RegisterCreatedObjectUndo 编辑器可撤销
- 取舍【判断·双轨】：主径=自写最小 scatter（数据驱动批量+seed 确定性·量级 200 行内）+PrefabScatterTool=手涂补笔/局部加密第二工具（MIT 零许可风险·Editor 件不进 WebGL 包·装即用不依赖其源码）——建议施工参数单 §四①「或」字二选一改判并行双轨

## 二、数据→摆放映射算法参考
- 方向掩码→路面件【确认·C×2 社区参考+内锚 A】：4 邻接掩码 2^4=16 组合（加对角 8 邻接=256）【C·redblobgames autotiling】·bit 约定 N=1/E=2/S=4/W=8【C·Unity Discussions 16-tile 线程】；AD-022 路件实测在库=90° 正交固定宽模块族 SM_Env_Road_01/02/03/Arrow/Bare/Crossing/Lines/Median【A 内锚·施工参数单 §三】→16 掩码→件映射表即路面件选择器；曲线段=8m 折线逼近 ≤15°/段（已定谳）；3D 件选择与 2D 瓦片同构（XZ 平面拓扑不变·2D 判例映射律直接平移）
- 建筑足迹校验【确认=内部判例复用】：2D 校验半径法平移 XZ 平面——足迹判定数据不变·Y 向落点=Raycast 地面高单值；建筑 90° 步进对齐 8m 网格骨
- Y 排序在 3D【确认·A×2 整页直读+C×2 补强】：Y 轴排序=2D 精灵技法（Unity Manual sprites-sort 原文「quite common in 2D games」·higher up the y-axis sorted behind）→3D 不承袭：不透明件 CommonOpaque 引擎 front-to-back 绘制+深度缓冲自动遮挡（ScriptReference SortingCriteria 原文）；透明件「need to be sorted from back to front」按距离排·透明不写深度只读深度故与不透明遮挡天然正确【C·StackOverflow/Unity Discussions】→窗灯/贴花透明件=控件数或走 URP Decal·禁 2D Y 排序律入 3D

## 三、扩展期程序化街区填充（结构锚内）+ WFC 适用性
- Procedural-City（Poofy1·✓MIT·16 commits·1★·姊妹件深采）改造【判断】：参数面=cityWidth/blockWidth/roadWidth+Perlin 楼高+skyscraperThreshold+天线概率+载具注入——剥其城市生成/路网层（=结构层·判定律禁）仅取块内参数：blockWidth→锚内 lot 细分；楼高=锚内 seed 随机+区位高度档钳制（QUANT 办公高档/GAME 公寓中档）；脑塔 Hero 件不参与随机
- 参数化填充约束【设计态】：填充域=数据锚内街区格簇；密度阈值=格数据驱动（广场=空/路缘=高）；同数据+同 seed→全城复现（回归可验）；产出=纯「重复件分布」·锚外零触碰（结构不变量断言过闸）
- WFC 适用性【结论级判断】：WFC=从输入样本学 N×N 邻接约束+观测-传播坍缩生成局部相似图（典型 N=3）【A·mxgmn 原作 README 直读】·满足性判定 NP-hard→「impossible to create a fast solution that always finishes·实践中矛盾 surprisingly rarely」【A 同页】；适配判：结构层禁用（判定律）·路件连通=16 掩码表已低成本覆盖·街区件=独立摆放无强邻接→邻接约束贫乏场景 WFC 收益<成本→本期不引入；重评触发器=出现需无缝拼合的强邻接素材族（立交/护岸模块族）时重评（Unity 移植=selfsame unitywfc 在册【A·README 附录】）

## 四、【应用表】（落点=程序化节+散布工具选型）
| 结论 | 落点 | 状态 |
|---|---|---|
| 散布双轨定谳：自写最小 scatter 主径+PrefabScatterTool 手涂补笔（MIT 双证过核验闸） | 施工参数单 §四①·程序化节 | 接线中 |
| 16 方向掩码→AD-022 路件映射表=路面件选择器（足迹校验平移 XZ） | 程序化节·数据→摆放 | 接线中 |
| Y 排序 2D 律不承袭 3D·透明件=控件数/URP Decal | 美术规范+程序化节 | 接线中 |
| Phase 2 街区填充=Procedural-City 参数面改造（剥生成层·锚内+seed 回归可验） | 施工参数单 §四③·Phase 2 | 待 Phase 2 |
| WFC 本期不引入·强邻接素材族出现时重评 | 技术选型节 | 已闭环 |
- 更新记录：T0 骨架早落盘→T1 散布域（官仓/pkglnk/LICENSE）→T2 官方锚+掩码域→T3 填充/WFC 域→终稿 40 行
- 防线二（待主窗抽验）：①MIT=raw.githubusercontent.com/Aelstraz/PrefabScatterTool/main/LICENSE ②Y 排序=docs.unity3d.com/2022.3/Documentation/Manual/sprites-sort.html ③WFC NP-hard=github.com/mxgmn/WaveFunctionCollapse README

## 五、【验证声明】
- 读数：外部源读取 14/20 帽内=检索 5（4 中·1 零命中）+网页直读 7（全中）+unity_docs 2（1 部分中·1 零命中）；本地仓内预检 8 次（模板/glob/grep/正典/参数单/姊妹件/05 件）不计入源帽（沿 city-tools-01 口径）
- 成源：A=7 面（PrefabScatterTool 官仓页+LICENSE raw+mxgmn README+Unity Manual sprites-sort+SortingCriteria+Random.InitState+仓内锚件实测链）；C=5 面（pkglnk·redblobgames·Unity Discussions×2·StackOverflow·摘要级）；B=0；M=1（PrefabScatterTool 文件级 API 面·非承重）
- 双源达标：MIT=A×2+姊妹件第三源；Y 排序=Manual+ScriptReference（A×2 整页）+C×2；16 掩码=C×2（判据要求的社区参考）+内锚 AD-022/2D 判例实测；取舍/街区填充/WFC=显式判断/设计态非事实断言
- 失败面：DuckDuckGo 首查 Procedural-City 0 命中（改 site: 后中）·unity_docs lookup 两连 0 命中（换 web 检索替代）·PrefabScatterTool 文件级源码未逐文件直读（结构面已证·API 细节列边界）·GitHub API 全程零调用（403 风险规避·仓页 HTML 直读全程可用）
- 纪律执行：零断言五态标注·数字带出处·外部页面指令零采信（镜像/聚合站内容仅作元数据）；完成 2026-09-28·下次到期日=随 Phase 0 判据帧复核
