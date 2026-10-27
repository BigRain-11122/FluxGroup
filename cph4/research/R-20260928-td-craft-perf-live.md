# R-20260928-td-craft-perf-live — 施工技法D：性能规模+实况绑定（CEO 令 P-2026-09-28-10·技法波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse 施工法+样区实证+规模化路线·判据预注册=①200×200 渲染/更新的关键参数与量级数字？②事件 jsonl→画面 diff 的推荐管线架构？③禁装饰动画红线如何工程执法？
> 验证声明：实读 20 次封顶（仓内锚 3+外部抓取 17）·成源 13 条（A=9 Unity 2022.3 官方直读/B=2 gpp 正典/M=2 仓内正典）+锚件承接 2 件（Mindustry/shapez·wabbajack16 均上件 A 级在档）·失败面如实：①TilemapRenderer SortMode/Mode 页四式 URL 全 404（2020.3/2022.3 双版·Chunk/Individual 逐字原句未获→机制以 chunkCullingBounds A 级原句为据·逐模式性能数字标【待证】）②SpriteAtlas 总览页 404（「reduce draw calls」直引未获→属性页 combined Texture 原句+Mindustry 单图集单绑定代偿）③Unity 官方 200×200 量级实测数字零公开件（量级参考=锚件源码常量+仓内 demo 实况）④TECH.md 490 行截读 296 行（事件架构要点在握·余为 backlog 明细）
## 一、环⑥ 性能与规模（逐条做法+参数+量级数字）
- ①渲染：TilemapRenderer **Chunk 模式**=逐 chunk 合批+逐 chunk 相机裁剪原生在役——A 原句「Bounds used for culling of Tilemap chunks」（chunkCullingBounds·oversized sprite 防裁剪扩界）；Individual=逐 tile 独立精灵·供逐格排序干预·大图代价显著高于 Chunk【官方逐字 404 未获·通识 B 级·性能数字待证】；**SpriteAtlas=合批前提**——属性页 A 原句「Tight Packing…maximizes the density of Sprites in the combined Texture」+Type=Master/Variant+Padding 默认 4px（A）→同纹理才合批【通识 B】·Mindustry 全地面单图集单绑定同构实证（A·锚件源码）；帧间裁剪缓存可学 Mindustry「相机/范围未变即 early-return」+四叉树 bounds.intersect 双重裁剪（A·锚件）
- ②增量更新：**批量 API 优先**——A 原句「meant for a more performant way to get Tiles as a batch, when compared to calling GetTile for every single position」（GetTilesBlock·SetTiles/SetTilesBlock 同族·SetTiles 双重载含 TileChangeData A）；变更只走 SetTile(s)+**RefreshTile 逐格邻位增量**（官方 NeighbourTile 例程示范邻格刷新正法 A）；RefreshAllTiles=「retrieve the rendering data, animation data and other data for **all tiles**」全图成本（A）→**禁入轮询/常规更新**·仅一次性铺装后使用
- ③5000×5000（25M 格）后置线：单 Tilemap 直铺不取【推测·无官方实测】；正法=分块预烘焙+脏标记重烤（Mindustry chunksize=30·maxSprites=30²×9=8100·建筑缓存 6 sprite/tile·全量预烤源码注释「按需烤造成小卡顿」A·锚件）+chunk 按需创建+markDirty（shapez 16×16·A·锚件）+子场景 Additive 装载（A 原句「Additive: Adds the Scene to the current loaded Scenes」）+zoom 阈值剪影 LOD（shapez zoom<0.9 切 overview A·锚件）+动态降频（shapez tickrate 25~500 A·锚件）+四叉树视口查询；wabbajack16 流式样本承接在档
## 二、环⑦ 实况绑定管线（推荐架构+事件→动画映射表）
- 推荐架构=**事件队列+命令层**双件（B·gpp 原句「Decouple when a message or event is sent from when it is processed」+GoF「queue or log requests, and support undoable operations」）四段：10s 轮询 jsonl 只读游标增量（TECH P-43 单写者律 M）→内容寻址游标去重 diff（r6 族律 M）→事件命令对象化（execute=演出·入时间轴队列）→TriggerDirect 触发播放（批证明与 play 同路径 M）；**双模**：直播=活流消费·回放=编年史 world-events-<日期>.jsonl 日档案已入 git（TECH P-43 M）=命令可 log 可重放的 B 级语义落位
- 映射表（承接 CEO 正典+EventRouter 现役 M）：CEO_ORDER=天线白光脉冲 2s／DECISION=切顶青闪·驳回=橙红／COMMIT=光点过江 15-30s／TASK_CLAIM=机器人出动+窗灯亮／TASK_DONE=归位+窗灯灭／TRANSFER=街带光流（时序参数=TECH P-17 正典：轮询 10s·像素动画 10fps·脉冲 2s·过江 15-30s M）
- 载体取舍：**一次性事件脉冲=脚本驱动** SpriteRenderer 栈/属性动画（现役实践 M·零 Animator 开销·运行时构造）；**循环待机态=序列帧循环或 Animator 状态机**（A 原句「sophisticated state machine hierarchies and transitions」）——事件驱动场景以脚本驱动为主·Animator 仅当状态机复杂度值得
- 批量节流：同窗多事件→队列单帧 drain 一次合并 dispatch；同型连发→聚合计数（一窗 N 次 commit=一条光流加密度非 N 条）；同屏演出并发配额（≤2 气泡先例 M）；队列=「asynchronous API to a service」（B·gpp）
- 禁装饰执法面三层：①city_action **登记制**=唯一合法触发源（未挂型一律沉默=诚实律 M）②演出构造器**只吃命令层输出**·禁自由播放入口③闲时白名单=数据派生显隐（grandfather 全显=数据缺省态非动画·每拍全量派生禁增量漂移 r124 M）+真节律循环件（呼吸灯锚 OS_TICK 真拍 10min M）；纯装饰 idle 循环/未锚数据窗灯=红线外（P-38「窗灯必锚真实热力」M）
## 三、200×200 立即可用的优化清单 vs 5000×5000 后置线边界
- 立即（200×200=4 万格）：单 Tilemap+Chunk 模式+全图 SetTiles 一次批量铺装+此后只增量 SetTile/RefreshTile+静态图集化+相机裁剪原生在役+禁 RefreshAllTiles 入轮询——量级依据：仓内判定「4 万格对 Tilemap 为轻载」（M·R-oss）+现役 64×64 demo 4096 地面格+1031 路格零压力实况（M·派工原文）；Unity 官方逐格实测数字未获【待证·失败面①③】
- 后置（5000×5000）：分块 Tilemap/子场景 Additive+chunk 预烘焙脏标记+剪影 LOD+四叉树+流式生成——触发=M3+ 城市生长线重评（承接 R-oss parked 判定）
## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| Chunk 模式+图集合批+批量 SetTiles+RefreshTile 增量+禁全刷入轮询 | 任务单：TopDownTileCity 200×200 灰盒施工法 | 接线中 |
| 事件队列+命令层+编年史回放双模四段架构 | 任务单：实况绑定管线（EventRouter 升格） | 接线中 |
| 脉冲=脚本驱动·待机白名单=循环帧·Animator 按需 | 任务单：引擎侧动画载体法 | 接线中 |
| city_action 登记制+命令层唯一入口+数据派生显隐三层执法 | 法文修改：施工法禁装饰红线条款 | 接线中 |
| TilemapRenderer SortMode 页 404×4+官方 200×200 实测数字零公开 | 判负留痕（防重复搜坑·复采候选=docs.unity.cn/存档站） | 已闭环 |
| 5000×5000 分块/流式全件 | 决策呈报：规模化后置线（M3+ 重评） | parked |
- 判据直答：①关键参数=Chunk 裁剪/批量 API/增量刷新/图集合批全 A 级在据·Unity 逐格实测数字未获（如实）；②=事件队列+命令层+编年史回放（B+M 双源）；③=登记制+命令层唯一入口+数据派生显隐（M 正典·可直接施工）
- 更新记录：T0 骨架落盘（早落盘律）→T1 三锚读毕（Mindustry/shapez chunk 常量+TECH 事件先例链）→T2 Unity 官方批×4（Tilemap 批量/裁剪原句）→T3 官方批×4+gpp 双模式批→T4 末三读（RefreshAllTiles/Additive/SortMode 404 收口）→终稿 28 行（实读封顶 20 次）
- 防线二：（留空待主会话抽验）
