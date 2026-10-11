# R-20260928-td-mindustry-shapez — 开源可读源码：Mindustry+shapez 渲染与 tile 架构（CEO 令 P-2026-09-28-10·案例解剖波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse 俯视城质感升维线+CEO 决策面·判据预注册=Q1 Mindustry 分层渲染/裁剪/世界格式可迁移 Unity 俯视城什么？Q2 shapez 分层/chunk/清晰度策略可学什么？Q3 两件 LICENSE 可否借码（GPL 红线）？
> 验证声明：实读 20 次（外部抓取 17+仓内核验 3）·成源 16 条全 A 级直读（A=16/B=0/C=0/M=0）·失败面：raw `LICENSE.md` 404×1（文件名误猜→根 `LICENSE` 直读闭环）；Mindustry SaveIO 区块内部字节级结构未逐层深采（MapIO 层面已证）
## 一、逐项架构与手法要点
### Mindustry（Anuken/Mindustry·Java/libGDX·29141 星/3800 fork·2026-09-28 API 直读）
- ①分层：Layer.java 单枚举定全 z 序——min=-11/background=-10/floor=0/scorch=10/blockUnder=29.5/block=30/blockCracks=30.1/turret=50/groundUnit=60/power=70/darkness=80/bullet=100/overlayUI=120/weather=130/light=140/max=220·注释「值以 10 增量」留插缝；建筑静态件再按 BuildingCacheLayer 数组二级缓存分层【A·直读】
- ②渲染架构：FloorRenderer 烘死地形、BlockRenderer 管建筑+动态件；processBlocks() 相机/范围/队伍未变即 early-return；drawBlocks() 只画四叉树选出集+缓存 chunk 回放【A·BlockRenderer 直读】
- ③tile/世界格式：1 格=1 Tile（floor/overlay/block 三槽+data 字节+build 引用）；现行地图=SaveIO 版本化 zlib 压缩流（meta/content/preview_map 三区·预览内嵌免全量解）；旧式图片地图=PNG 逐像素（1px=1tile·ColorMapper 色→方块·readImage/writeImage）【A·MapIO.java 直读】
- ④地形表现：floor.drawBase 入本 CacheLayer 的 chunk mesh；floor.drawNonLayer 把跨材质过渡 sprite 烘进邻层 mesh（无缝靠烘焙非运行时）；每 CacheLayer 可挂自定义 shader（begin/end·液体专用混合）；阴影+黑暗度=2 张 world 尺寸 FBO（1tile=1px·阴影 alpha 0.71）仅脏格增量重绘经 shader 投影【A·直读】
- ⑤性能数字（全源码常量）：chunksize=30·maxSprites=30²×9=8100（每 tile 9 sprite 供过渡）·建筑缓存每 tile 6 sprite·SpriteCache 容量=16382-(16382%5400)·顶点 3 浮点紧致格式（pos+color+packedUV·坐标归一化）·全地面单图集单绑定（非环境纹理 region 直接替换 env-error）·缓存 sprite grow 0.04px 防低精度缝·dynamic=false 全量预烤（源码注释：按需烤「造成小卡顿·多数地图不需要」）·5 棵四叉树（block/blockCached/blockLight/overlay/floor）相机 bounds.intersect·可见 chunk 范围+mesh.bounds.overlaps 双重裁剪【A·双渲染器直读】
### shapez 1（tobspr-games/shapez.io·JS·6976 星/1301 fork·消歧=开源 shapez 1·非商业 shapez 2）【A】
- ①渲染：Canvas2D 系即时绘制（所见渲染文件全用 canvas context·未见精灵引擎）；MapView 层序=pattern 背景→backgroundLayer(zone/mapResources/beltUnderlays/belt)→foregroundDynamic(弹射/接收/采矿)→foregroundStatic(建筑)→wires 层→overlay；各层由 systems.*.drawChunk 即时画·chunk 以 renderIteration 脏标记驱动重绘【A·map_view+map_chunk_view 直读】
- ②tile/世界格式：MapChunk=16×16 tile·每格三槽=lowerLayer(地面资源/标记)/contents(正层实体)/wireContents(线层)；chunk 按需创建（getOrCreateChunkAtTile/getChunk(…,true)·未见硬边界→推断支持理论无限图）；4×4 chunk=1 聚合(aggregate)供 overview；实体增删改自动 markDirty 覆盖 chunk【A·直读】
- ③地表施工：全图底面=32px pattern canvas（DPI2·THEME.map.background 单色+细网格线）createPattern 一次填充全屏——地面零逐格绘制；资源 patch=多圆 RNG 烘进 lowerLayer；缩放 LOD：zoom<0.9（mapChunkOverviewMinZoom）切 overview 剪影渲染（CHUNK_OVERVIEW_RES=3px/tile·chunkOverview.filled/empty 双色）【A·直读】
- ④画面清晰度：纯平色地面+细网格+强剪影建筑/资源——信息密度全让给实体（无战斗工厂极简可读性=底面降噪）；canvas 平滑质量 low（源码注释「移动端性能关键」）【A·直读+源码注释】
- ⑤传送带：BeltPath=整条连贯带合一对象（源码自述「用于优化性能」）；物品=一维排序数组 items=[距下一件距离,物品]（非逐格模拟）；update() 自队首向后分配 remainingVelocity·压缩件跳算；渲染：连续同款件打包 1 张缓存 sprite（≤20 件/捆·maxBeltShapeBundleSize=20·buffers.getForKey 按方向+dpi+件型键控）；POTATO 模式整条带只画 1 件代表；增删带=extend/split/delete 全套路径手术迁移物品【A·belt_path.js 直读】
- 关键数字：tileSize=32·mapChunkSize=16·chunkAggregateSize=4·itemSpacingOnBelts=0.63·belt 2 件/s·tickrate 动态 25~500·zoom 0.1~3（初始 1.9）【A·config.js 直读】
## 二、许可判定表（LICENSE 直读）
| 项目 | 直读结果 | 判定 |
|---|---|---|
| Mindustry | 根 `LICENSE`=GNU GPL v3 全文（Version 3, 29 June 2007）+API license 字段 GPL-3.0 | 借码禁入交付链·学实现可（红线内） |
| shapez 1 | master/`LICENSE`=GNU GPL v3 全文+API 字段 GPL-3.0 | 同左 |
- 双件双源确认（API 字段+文件原文直读）→一致结论：任何文件/资产不搬用·只学架构思想·实现全重写【确认】
## 三、可学实现点清单（思想级·GPL 边界=零搬件·全部重写）
- M1 Layer 枚举 z 序「以 10 增量留插缝」→Unity SortingLayer/自绘 z 表设计【Mindustry·学思想】
- M2 静态地形 chunk 烘焙+脏标记重烤→200×200+ 规模线分块静态化（Unity Tilemap 语境：借分块失效+局部重烘思想·或 RenderTexture 快照）【Mindustry】
- M3 跨材质过渡烘邻层（drawNonLayer）→道路 16 变体掩码之外的无缝混合备选思路【Mindustry】
- M4 world 尺寸 FBO 阴影/暗角图（1px/tile·脏格增量）→Unity RenderTexture+CommandBuffer 同思想【Mindustry】
- M5 四叉树视口查询+相机未变 early-return→大图分块裁剪+帧间结果缓存【Mindustry】
- S1 pattern 单次填充底面→俯视城地面网格一张 repeat 纹理·零逐格开销【shapez】
- S2 zoom 阈值剪影 LOD→远景/缩略图减绘制【shapez】
- S3 BeltPath 一维距离链→车流/人流路径级模拟（O(路径) 非 O(个体)·城市交通线选型）【shapez】
- S4 连续同款件打包缓存 sprite→车队合批【shapez】
- S5 chunk 按需创建→200×200+ 内存按需化【shapez】
- S6 动态 tickrate 25~500→大规模模拟分档降频【shapez】
## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| Mindustry 静态 chunk 烘焙+脏标记（M2/M3） | 任务单：TopDownTileCity 200×200+ 规模线 | 接线中 |
| Layer z 序留缝+FBO 阴影增量（M1/M4/M5） | 任务单：俯视城分层与光影质感 | 接线中 |
| shapez pattern 底面+剪影 LOD+极简可读性（S1/S2） | 任务单：底面降噪与远景减绘 | 接线中 |
| BeltPath 路径级流+打包 sprite（S3/S4） | 决策呈报：未来车流系统选型 | 接线中 |
| 双件 GPL-3.0·借码禁入（Q3） | 决策呈报：许可红线确认·零搬码 | 已闭环 |
- 判据直答：Q1=M1~M5 全 A 级直读可迁移；Q2=S1~S6+纯平色+网格+剪影清晰度策略；Q3=均不可借码（GPL-3.0 双源）·学实现不搬件
- 更新记录：T0 骨架（早落盘律）→T1 双仓元数据+shapez LICENSE 直读→T2 Mindustry 双渲染器直读→T3 shapez 层/chunk/config→T4 belt_path+Layer+MapIO→终稿 46 行（实读封顶 20 次）
- 防线二：（留空待主会话抽验）
