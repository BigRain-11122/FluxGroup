# R-20260928-td-craft-light-daynight — 施工技法C：光照氛围与日夜（CEO 令 P-2026-09-28-10·技法波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse「灰盒→优质化施工法」环④+32×32 样区实证·判据预注册=Q1 cel 风下 Light2D 与烘焙/自发光 sprite 的分界线；Q2 日夜四档色轮在 URP 2D 的最优工程载体；Q3 霓虹·窗灯·街灯锥斑能否以参数初值在样区一次成型
> 验证声明：实读 20 次触顶（成源 10=URP14 官方 A 级 7 页[Lights-2D-intro·2DLightProperties·Bloom 手册·Light2D/Bloom/ColorAdjustments/WhiteBalance API 类页]+仓内锚件 3 件承接·纪律读 1·失败读 9[Lights-2D-Global/Spot/Point/Freeform·post-processing.html·post-processing-color-adjustments 六 URL 404=URP14 改名，正确名经 Light2D.HelpURL 采得；2DLightSpot/2DLightGlobal 二猜 404→Spot 型滑条范围判负留痕；锚件路径笔误 1 次即纠]）·关键结论 A 级双页源或锚件承接（勘误条=单页原文直引）·未获证处一律标 M 待样区验
## 一、URP 2D 体系在 cel 风下的取舍判定
- 勘误【确认·A·2DLightProperties 页原文直引】：编辑器四型=Freeform/Sprite/Spot/Global（下拉另含 Parametric 共五型），**"The Point Light Type has been renamed to the Spot Light Type from URP 11 onwards"**——任务前提"四类型 Global/Free/Spot/Point"须改写
- 机制【确认·A 双页】：2D 光只影响 2D Renderer（Sprite/Tilemap/SpriteShape），3D 光对 2D 无效（intro 页）→Light2D 属纯 2D 子系统，**全 2D 红线天然合规**；"Global 影响目标排序层上全部 sprite"+"灯只点亮其目标排序层"（properties 页）→**多 Global 分层可行**=黄昏互补色的工程通道
- cel 硬边抓手【确认·A·API】：点光/Spot 内外角与内外半径"间隙=半影(penumbra)大小"→**收窄内外间隙=硬边光**；falloffIntensity 控光缘衰减亮度与距离；intensity 默认 1 且可>1"提亮 sprite 超其原色"（properties 页）=霓虹超亮供 bloom 的原生通道；灯间默认 Additive 合并（properties 页）
- 性能纪律【确认·A·intro 页】：混合风格"简单场景 1 个、常用至多 2 个"；批渲染判据=连续排序层+完全相同光集合（分层 Global 增批次须节制层数）；光渲染纹理默认 0.5x 屏幕分辨率；法线贴图=昂贵（每层批全尺寸深度预渲染）且**Global 不用法线、非 Global 默认 Disabled**（properties 页）→**cel 平涂建筑/瓦片零法线，仅江面可选开（技法B 域）**
- Q1 判定【锚件承接】：适合 cel=Global tint（整屏乘色零糊边）+Spot 硬边锥（街灯）+Additive 溅光（江面）；忌讳=Freeform 大衰减光池与法线 diffuse 渐变落在平涂上=糊边——装饰性光池一律以 HLM「烘焙三件套」（逐房环境色洗+硬投影暗带+值域隔离霓虹·零动态光零光晕【锚件 B+A 双源】）与 Stardew「减法 tint」+昼夜换瓦【锚件 A】替代；**Light2D 动态光只留给功能性光位**
## 二、黄昏/夜/霓虹/日夜循环实现法（逐条做法+2022.3 参数）
1. 日夜载体对比（Q2 答）：①Global Light2D 色/强度脚本 lerp——URP 下全屏 tint 的原生乘法载体（分层数·零后处理·不染 bloom 输出）【A 机制】=**推荐主载体**；②后处理 Volume·ColorAdjustments colorFilter="Tint the render by multiplying a color"【API】——postExposure 注明"applied after HDR effect and right before tonemapping"【API】=链位自证会连 bloom 霓虹一起染，只作黄昏轻 grade（WhiteBalance temperature/tint 冷暖±品红绿补偿【API】）不作主 tint；③Stardew 式 sprite 减法色罩（255−RGB）——URP 2D 下须全员 Unlit 材质=弃灯能力，判不推荐。**落地=①主（双 Global：前景层暖橙×江面/背景层冷紫=黄昏互补色，各只指目标排序层【A】）**；四档 Gradient 锚点（晨曦橙粉/昼白/黄昏暖紫金/夜蓝黑青·承 R-20260925 五件①）·北京时间驱动（TimeZoneInfo UTC+8·M 工程）·2-4s 交叉淡变=邻档窗口 lerp（M）·夜档 Global 初值 M：强度 0.35-0.5·色 (0.45,0.55,0.85) 系
2. 霓虹/招牌（Q3）：三层法=自发光 sprite（Unlit 材质不受 Light2D 影响→夜暗压不住窗/牌【M·编辑器一键可证·防线二候选】）+加法光晕 sprite（软圆贴图·Additive·scale 1.5-2.5×·α 0.15-0.35·M）+Bloom 收晕【A 手册】：Threshold 默认 0.9（gamma 空间·低于阈值不上晕·"above 0 will disregard energy conservation rules"【API】）·Intensity 0~1 且**默认 0=必须显式开**·Scatter 默认 0.7·Clamp 65472·HighQualityFiltering 移动端关·MaxIterations 6；灯内溅光=intensity>1 提亮【A】；HLM 证**值域隔离可免 bloom 成霓虹**（bloom 关或阈值 1.2+ 亦成）【锚件】
3. 街灯锥形光斑：Spot Light2D 四参=内/外角+内/外半径+falloff（API spotLightInner/OuterAngle·Inner/OuterRadius）·**硬边=内外间隙收窄**【A】；初值 M（官方滑条范围未采得·样区定）：内角 30°/外角 45°·内半径 0.2-0.5·外半径 2-3 单位·falloffIntensity 0.7-0.9·intensity 1.2-2；灯下光池 sprite 预烘焙双保险（HLM 律）
4. 夜灯窗灯：主法=sprite 换图（日版受光→夜版 Unlit 自发光暖黄窗·Stardew S3 昼夜换瓦同构【锚件 A】·入夜 batch 触发+每楼随机 0-3s 延迟 M）；副法=遮罩层（Stardew S2 暗幕挖光圈【锚件 A】）或窗层专用暖色 Global（灯只影响目标层【A】）；**大量 Point 窗灯=烧灯预算**（分层增批次·intro 批渲染律【A】）→窗光晕以烘进 sprite 为先
5. 江面三色碎光带（光照侧）：品红/金/青 additive 条带 sprite 为主+少量 Additive 灯为辅（灯间默认 Additive 合并【A】）；intensity>1 提亮通道供 bloom【A】；水面法线/波帧归技法B
6. 雾/雨光照配合（与技法B 分工=光照面）：Volumetric 体积雾"全灯型可用·0 透明→1 不透明"（properties 页·API volumeIntensity 字段）→雨夜街灯锥调 0.3-0.5（M）；VolumetricShadowStrength 0-1 可遮灯锥【A】；雾天=Global 饱和↓+冷蓝灰 tint（M）；湿地反光=路面对应灯色加法微带（R-20260925 光感三补③）
7. 施工顺序（喂灰盒→优质化两段法）：灰盒段=只接 ①Global 四档 lerp+④窗灯换图（零后处理可成样）；优质化段=+②霓虹三层法+③Spot 锥斑+⑤碎光带+⑥体积雾，逐层验收
## 三、样区实证建议清单（32×32 样区演示项）
1. 全天四档循环+2-4s 淡变实录（同机位 5 帧·多模态对锚 7-9/10）；2. 双 Global 分层黄昏互补色帧（暖前景×冷江/背景）；3. 街灯锥斑三对照=纯 Spot 灯 vs 烘焙光池 vs 灯+光池；4. 霓虹三色（品红/金/青）bloom 开/关对比帧；5. 窗灯批量换图+随机延迟实录；6. 江面三色碎光带（additive 条带+Additive 灯数上限实测）；7. 雨夜体积雾灯锥+湿地微反光；8. 灯数×帧率曲线（10/20/40 盏×混合风格 1/2 组·验"至多 2 风格"律）；9. 江面法线开/关对照（验昂贵警告与 cel 取舍）；10. 夜档 Global 0.35/0.5 强度双档选优
## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| cel 光路分界=烘焙/自发光主体+Light2D 仅功能光位·硬边=内外间隙收窄（Q1） | 施工法（环④光照章） | 接线中 |
| 日夜载体=分层 Global Light2D 四档 lerp+北京时间+2-4s 淡变·Volume 仅黄昏轻 grade（Q2） | 施工法（环④日夜章） | 接线中 |
| 霓虹三层法（Unlit 自发光+Additive 晕 sprite+bloom 0.9/0.5-0.8/0.7）+窗灯换图法（Q3） | 施工法+样区实证 | 接线中 |
| 街灯锥斑/碎光带/体积雾/夜档 Global 初值参数组 | 样区实证（一次成型验收） | 接线中 |
| 勘误：Light2D"Point 型"已于 URP11 改名 Spot·编辑器四型=Freeform/Sprite/Spot/Global | 任务单（前提修正注记） | 已闭环 |
| Bloom 默认 Intensity=0 须显式开·法线默认关且 Global 不用法线·混合风格≤2 | 施工法（防呆注记） | 接线中 |
| Spot 型官方滑条范围未采得（2DLightSpot/2DLightGlobal 二猜 404）→锥斑初值 M 待样区定 | 判负留痕（重访触发器=URP15+ 手册页或编辑器直读） | 已闭环 |
- 更新记录：T0 骨架落盘→T1 三锚件+intro/Bloom 手册（13 读）→T2 四 API 类页+双 Global 机制（17 读）→T3 2DLightProperties 勘误与全参数（18 读）→终稿 20 读触顶·31 行
- 防线二：（留空待主会话抽验）
