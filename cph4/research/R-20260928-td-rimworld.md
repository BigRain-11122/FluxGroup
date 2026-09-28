# R-20260928-td-rimworld — 地形过渡与事件驱动画面：RimWorld（CEO 令 P-2026-09-28-10·案例解剖波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse 俯视城质感升维线+CEO 决策面·判据预注册=①边缘混合规则能否 cel 化治水草直切？②画面是否全由模拟事件驱动（验「AI 行为剧场·禁装饰动画」红线同构）？③分区渲染与增量更新能否移植 Unity Tilemap？
> 验证声明：实读 20 次（含 1 仓内模板读）·成源 11 条（A=4：官方wiki Environment/Mental break/Events+作者自介；B=1：维基百科访谈引语；C=6：反编译件×4+GitHub检索+仓树）·失败面：tynansylvester.com 首页仅返 2003 旧档；wiki Terrain HTML=嵌表乱码（API 判定重定向 Environment）；wiki「Map」页=Odyssey 书籍物品（判负留痕）；站内搜 250x250 零命中；MapSizeCategory 404；Verse/MapGenUtility 404→250×250 默认值与生成期平滑细节转待证；引擎内幕无官方文档面，以反编译件互证并透明标注
## 一、六维要点（主维=③地形过渡+⑤事件绑定）
① 视角与规格：俯视格网+显式 AltitudeLayer 高度带铺层（C·非纯 Y 排序）；引擎=Unity（确认·C 三重旁证：代码全量 using UnityEngine+3.9MB Burst 生成物+Assembly-CSharp 命名），Verse=其上自研模拟框架——与 demo 同栈可直译；地图按 17×17 分 Section（C·Section.cs 常量 Size=17）；250×250 默认=待证（wiki 无专页；Events 页作者实测旁证 300×300 在用）
② 基地结构：建筑合法性由地表 Support 亲缘裁决（Light/Medium/Heavy/ShallowWater/MovingFluid/Bridgeable/GrowSoil/Diggable·A）；邻居采样时墙下格替换 Underwall 专用代理地形（C）；美=逐格累加值（-10+2=-8·A）
③ 地形与地表施工（主维①·机制全解）：
- 边缘过渡核心（确认·C·SectionLayer_Terrain.Regenerate）：每格 8 邻域采样，邻居地形≠本格且 edgeType≠Hard 且邻居 renderPrecedence≥本格时，邻居材质以 9 顶点扇形渗入本格（8 环点按方向 alpha=1/0、中心=0→辐射线性渐变）——高优地形的边向低优邻居扩散
- edgeType 四档 Hard/Fade/FadeRough/Water ↔ 四 shader；FadeRough/Water 加挂 AlphaAddTex 噪声贴图=有机糙边；renderPrecedence<400、渲染序=2000+precedence 定压盖次序（确认·C·TerrainDef）
- 水面独立层渲染（waterDepthShader 深度材质+HasTag("Water") 从地表层排除·C）；Odyssey 另设 SectionLayer_TerrainEdges 显式边变体 9 类（O形/U形/内角/外角/平边/环左/环右/环单/环序贴图+专用 TerrainEdge shader）——alpha 渐变之外官方已补硬边变体轨（C）
- 地表=状态机（A+C 双证）：driesTo（marsh/mud→soil、浅水→stony soil）·burnedDef 烧毁迁移·tempTerrain/floodTerrain 临时洪水·extinguishesFire·takeFootprints/takeSplashes·throwFleckChance+fleckData（踩踏扬尘=事件 fleck）·glowRadius+glowColor 自发光·traversedThought 踩踏心情·filthAcceptanceMask/generatedFilth 污渍产排·tags 体系
- 数值锚（确认 A·Environment）：浅水移速30%·路径代价30/深水0%·300 不可通行/mud48%·14/marsh30%·30·产Mud伤·可建桥/soil87%·2·肥力100%；rich140%/stony70%/sand10%；移速=13/(13+代价)；道路=Packed dirt 93%·代价1 与 Broken asphalt 100%·0——素面零标线（美-1）
- 自然生成管线（确认 C·GenStep_Terrain：SeedPart=262606459→逐格 MapGenUtility.GetNaturalTerrainAt 定原生地表+Biome.terrainPatchMakers 群系补丁器=富土/沼泽斑块；0.3.410 版史「Added rich dirt patches」A 旁证）；山=rough/rough-hewn stone+overhead mountain 不可毁（A）·河=shallow moving water 带 MovingFluid 水力亲缘（A）·群系拼合=天气/疾病权重逐群系数值化（A·Events）；生成期平滑细节=待证（MapGenUtility 404 判负）
④ 光照氛围：格级 0~100% 三档 Dark/Lit/Brightly lit（30/90 分界）·自然光不扩散·屋顶下恒 0%·灯具径内约 50% 线性衰减·日照曲线随纬度 sin(SolarAltitude+BonusAngle)/0.7（A·wiki 注源反编译 GenCelestial）；光全量绑玩法：植物生长率=(光-最小)/(最优-最小)·0 光工作×80%·手术×75%·黑暗心情-5（A）；日影/边影=SectionLayer_SunShadows/EdgeShadows 分区静态烘焙层+地表可自发光（C）→阴影同为静态网格
⑤ 动效与状态绑定（主维②）：
- 精神崩溃=纯模拟事件（确认 A）：三档心情阈值 minor35%/major20%（=4/7×minor）/extreme5%（=1/7×minor）·MTB 4/0.8/0.5 天；可视化三层协议=①名字转绿②头顶闪电图标黄(非攻击)/红(攻击)③行为本体即画面：狂暴近战/纵火点火/锤楼生瓦砾污渍/掘尸上桌/神游脱衣/幻觉周身黑影——VFX 全挂真实状态；恢复 Catharsis +40×5 层防螺旋（A·Mental break；Events 页将其列为事件=A×2 双源）
- 事件与通知（确认 A·Events）：事件由 AI 讲述者驱动；信件右缘四色制（蓝好/灰中/黄坏/红威胁）+变量化标题；袭击生成管线=派系→攻击型→到达方式（边缘步行/中心空投/散投）→编成，权重表 Raid 7.40 居首（事件表 9.0）；天气全带机制数字：雾命中50%/雨80%·灭火/闪电10火伤3×3/雪按率堆层·0.0.245 版起「天气影响命中」；火=模拟对象（firedanger=Σ(0.5+0.1×火势)＞90→雨事件进度×15·426tick 检一次）；Zzztt 爆炸半径=clamp(sqrt蓄电×0.05,1.5,14.9)
- VFX 双系统 Mote+Fleck，后者带 FleckParallelizationInfo 并行化（C）——性能化事件动效；设计哲学=Tynan 原话「The real engine of story is the gameplay systems themselves」（B·维基访谈引语）+著《Designing Games》（A·作者自介）
⑥ 可抄点：见三（5 条·均达「直接可移植」标准）
## 二、对照判定面（demo 三瑕疵→针对性解法映射）
- 水草直切：机制解=五级湿阶谱 deep(300)→shallow(30)→marsh/mud(14~30)→marshy soil(14)→soil(2)（A）；贴图解=8 邻域渗入+FadeRough 噪边（C）；cel 转译=保邻域掩码与压盖逻辑、弃 alpha 渐变改 2~3 档硬边色带变体（demo 16 变体底座可复用；Odyssey 9 类边变体=硬边轨官方先例）
- 滨水孤树：湿带地形自带生态语义（肥力梯度+水系亲缘+踩踏 fleck+湿带专属 Terrain 链）→植被按肥力/湿带分布而非均匀撒；水生植物清单未证（M·待证）→先落分布规则再查物种
- 曲路虚线远观噪：RimWorld 道路素面零标线且以 renderPrecedence 压草不压水——降噪靠克制非加料（A+C）；demo 对策=标线随缩放 LOD 淡出/远观整体降对比
## 三、可抄点清单（怎么抄+cel 锚适配度）
1. 五级湿阶地形带+DriesTo 状态机：水陆间按深度铺 5 级 Tilemap 带+邻接掩码 SetTile，干涸/烧毁/冻结按 driesTo/burnedDef/canFreeze 迁移；cel 适配=高（硬边色带天然 cel）
2. 8 邻域边缘渗入+edgeType 分档+噪边：按 renderPrecedence 定「谁渗入谁」，cel 化=邻向只画硬边变体条（弃 alpha 渐变）；适配=中高（渐变→色带跳变改造）
3. Section 17×17+ulong 脏标记+视野裁剪惰性重建（TryUpdate 仅重建与视野重叠的脏区、视野外脏保留）：Unity 同栈直译——把日影/污渍/污染设为平行 SectionLayer 静态网格批次；适配=高（同引擎直解 250×250 规模）
4. 精神态三层可视化协议：阈值触发+图标分色+行为即画面+恢复 buff 防螺旋——直配「AI 行为剧场」红线；适配=高（图标化=日漫友好）
5. 信件四色+变量化标题+事件权重表：城市事件通知与节奏系统（讲述者制）；适配=高
## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 五级湿阶+DriesTo 状态机（治水草直切） | 任务单（FluxVerse demo 直改） | 接线中 |
| 8 邻域渗入+噪边 cel 化变体集 | 任务单（demo 直改） | 接线中 |
| Section 分区+脏标记+视野惰性重建 | 任务单（demo 大图基建·Unity 同栈直译） | 接线中 |
| 精神态三层可视化协议 | 任务单（AI 行为剧场线） | 接线中 |
| 「零装饰动画」红线同构先例（全 VFX 挂模拟状态） | 决策呈报（CEO 红线佐证） | 已闭环 |
| 250×250 默认值+生成期平滑细节+水生植物清单 | 判负留痕（404×2·复访触发器=补勘仓内 MapGenUtility 实路径+wiki 植物页） | 待证 |
- 更新记录：T0 骨架→T1 wiki 环境面→T2 精神崩溃页+仓锁定→T3 代码三件套→T4 生成管线件成源+双 404 判负+引擎认定纠偏（Unity 非「自研」）→终稿 40 行（2026-09-28 R28-TD-03）
- 防线二：（留空待主会话抽验）
