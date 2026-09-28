# R-20260928-td-openra-cdda — 开源引擎与程序城市生成：OpenRA+Cataclysm DDA（CEO 令 P-2026-09-28-10·案例解剖波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse TopDownTileCity demo（团结引擎 1.10.3=Unity 2022.3.62t15 fork·2D Tilemap 全家桶）俯视城质感升维线+程序化城市储备·判据预注册=①OpenRA 地形渲染层/精灵排序/过渡+地图格式哪些可平移 Unity？②CDDA overmap→城市→街区→建筑生成层级与 JSON 地图表示？③两项目 LICENSE 直读后学什么思想、什么禁入交付链？
> 验证声明：实读 20 次（满预算）·成源 18 条（A=18/B=0/C=0/M=0——全部 GitHub 仓 API/源码/官方 wiki/官方 doc 一手直读）·失败面：OpenRA Graphics/TerrainRenderer.cs 与 Map/TileSet.cs 猜路径 404×2（瓦片变体数据模型→待证）；overmap.cpp 大文件截断（place_cities/build_cities 算法体内文→待证）

## 一、逐项架构与手法要点
### 1. OpenRA（C#/.NET·自研 RTS 引擎·重演 RA1/Tiberian Dawn/Dune 2000·主分支 bleed·star≈17,447·pushed 2026-09-25 活跃）
- 消歧与分层【确认·A=repo API+根目录清单】：OpenRA/OpenRA，官方自述"Open Source real-time strategy game engine for early Westwood games…C# using SDL and OpenGL"；分层=OpenRA.Game 核心/Mods.Cnc+Common+D2k 规则层/Platforms.Default+glsl 着色器/Utility 工具链；Mod SDK 为独立仓 OpenRAModSDK。
- 地形渲染【确认·A=Graphics/TerrainSpriteLayer.cs 全文】：地形=独立静态层——全图一次性顶点缓冲（每格 4 顶点）+跨层共享静态索引缓冲（引用计数，注释"PERF: we can reuse the IndexBuffer as all layers have the same size"）；改动走 dirtyRows 行级脏标记，Draw 只上传可见区脏行、单次 DrawVertexBuffer 画整层——**地形永不参与逐帧排序**。
- 精灵排序【确认·A=Graphics/WorldRenderer.cs 全文】：排序键=Pos.Y+Pos.Z+ZOffset，打包 ((long)key<<32)+i 稳定排序（注释"must be ordered using a stable sorting algorithm to avoid flickering artefacts"）；相位=地形层最先→排序后世界精灵（ScreenMap 空间分区只取屏内 actor）→后处理→Shroud→overlay；等距网格可选深度缓冲；调色板纹理索引打包进顶点色、RGBA 精灵跳过调色板（PERF 注释）；缓冲全复用+键数组 2 次幂增长。
- 高度/坡道【确认·A=TerrainSpriteLayer.cs】：Grid.Ramps[map.Ramp[cell]].CenterHeightOffset 直接偏移地形精灵 Z；地形光照按格四角采样线性插值平滑"楼梯感"。
- 地图格式【确认·A=官方 wiki Mapping 页】：.oramap=改后缀 ZIP，至少含 map.bin（地形+资源二进制）+map.yaml（Actor 放置/武器/规则覆写）+可选 map.png（360×200 预览）+任务用 Lua；**边界须 8 整除+外圈 cordon 不可达带**；官方"extremely large maps degrade game performance"；resource.openra.net 以内容哈希防 desync；Utility --import-ra-map 可从原版格式转换。
- 地形过渡数据模型【待证】：TileSet.cs 两赌路径均 404；已读源/wiki 均无邻接自动过渡系统痕迹，原版 tileset 模板+变体为数据驱动【推测·缺直读源】。
### 2. Cataclysm: Dark Days Ahead（C++·CleverRaven/Cataclysm-DDA·master·star≈13,256·pushed 2026-09-28 当日活跃）
- 消歧【确认·A=repo API】：Whales 系社区续作线，回合制末日生存 Roguelike；GitHub license=NOASSERTION（原因见下行）。
- 许可【确认·A=LICENSE.txt 全文直读】：首句"Cataclysm is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License"——整项目单一 CC BY-SA 3.0，**非 GPL**；第三方件单列（字体 OFL/Apache、fmt/snmalloc MIT、zstd BSD、PLF zLib 等）。
- 尺度层级【确认·A=src/map_scale_constants.h】：SEEX=SEEY=12（子图/nonant）·MAPSIZE=11（现实泡 132×132 tile）·OMAPX=OMAPY=180·OVERMAP_LAYERS=21（z=-10..+10）·SEG_SIZE=32 存档分块；**OMT=24×24 tile（2×2 子图）双源交叉确认**（constants+overmap.cpp 24×24 通行位集）。
- 生成管线【确认·A=overmap.cpp generate() 原文】：urbanity/forestosity 区域梯度→河→湖→海→森林→沼泽→峡谷→polish_river→高速→**place_cities 放中心→place_highway_interchanges→build_cities 扩街区**→林道→道路/铁路（先后可配置）→specials→finalize_highways→地下层循环（Sewer/地铁由地面 manhole/sub_station 派生+connect_closest_points 连通）→桥层（支撑柱垂直下延+桥头堡 ramp 朝向判定）→怪物/电台。**水系先行、城市次之、道路殿后**。
- 街区算法【部分确认】：place_building/build_city_street(block_width=2 默认) 签名【A=overmap.h】+generate() 调用序【A=overmap.cpp】；**算法体内文因截断未读→待证**；已知 city.size 字段、怪物群密度∝size²·半径∝size。
- 道路/水系算法【确认·A=overmap.cpp】：lay_out_connection=**贪心寻路 pf::greedy_path+成本场**（subtype->basic_cost+existence_mult×dist，已有路×1 新路×5"Prefer existing connections"）；place_roads 保**跨 overmap 路网连续**：≥3 边缘出口（避角 10 格+避河及贴河格），无城时 fallback 中心随机点，末步 connect_closest_points 近邻成网；河流=overmap_river_node 贝塞尔控制点+river_meander 蜿蜒；**峡谷=随机场成本 rng(1,2)**（注释原话"easily produces decent looking windy ravines"）；森林=逐格噪声双阈值、沼泽=河泛洪面×噪声交集、林道=4 连通泛洪+四向极值点。
- 连线位掩码【确认·A=overmap.h om_lines+MAPGEN.md】：16 变体 N/E/S/W 位掩码表+位循环 rotate()；线性地形后缀 _end/_straight/_curved/_tee/_four_way——**与 FluxVerse 16 变体道路邻接掩码同构，A 级实锤**。
- JSON 地图定义【确认·A=doc/JSON/MAPGEN.md（86KB 官方文档）】：建筑按 oter id **懒生成**（"on discovery"，"fraction of a second"）；om_terrain 支持嵌套列表→单 JSON 定义多 OMT 大建筑（如 2×2 OMT=48×48 公寓塔）；rows=24×24 ASCII 行+terrain/furniture 字符映射（权重 [id,n] 数组·Unicode 字符可用）；set/place_* 指令（point/line/square·随机区间·chance/repeat·载具≤24 格+rotation）；**place_nested 按邻接 OMT/joins/flags 条件拼块**（官方用途"smoother transitions between biome types"）；**rotation=90° 步进随机旋转**；predecessor_mapgen=先跑基底地形再生建筑；palette 符号复用（standard_domestic_palette 等·可嵌套·可随机选择）；**参数作用域**（overmap_special/omt/omt_stack——一次掷骰整楼一致如 roof_type）+switch 派生值；weight 默认 1000；update_mapgen 后更新既有 OMT。
- 性能【确认·A=overmap.h/cpp+MAPGEN.md】：OMT 粒度懒生成+常驻现实泡仅 132×132+oter 查询 8 槽 LRU+24×24 通行位集占位共享 CoW。

## 二、许可判定表（LICENSE 直读）
| 项目 | 直读判定 | 交付链结论 |
|---|---|---|
| OpenRA | COPYING=GPL-3.0 标准全文（35,151B·无例外条款），README 口径"GPL v3 or later" | 红线适用：**代码/资源件禁入交付链**；读源学思想合法（版权不保护思想）；原版 Westwood 素材不在仓内（玩家自备），仿像素风格属风格不受保护、具体素材禁抄 |
| CDDA | LICENSE.txt 首句=CC BY-SA 3.0（整项目统一，GitHub 因此报 NOASSERTION） | 非 GPL 但同为 ShareAlike 传染：**件（代码/美术 gfx/tileset/JSON）禁入商业交付链**（除非整链 SA+署名）；算法思想与数据格式概念可学 |

## 三、可学实现点清单（思想级·逐条标注许可边界）
1.【OpenRA】静态地形层（持久缓冲+行级脏提交）与动态精灵层（Y+Z+ZOffset 稳定排序）分层——FluxVerse 大城瓦片层静态化与 Y 排序纪律直接校准（思想平移✓·零代码拷贝）
2.【OpenRA】排序键含 Pos.Z 高度项+索引稳定化防同格闪烁——俯视角伪高度/头顶物件排序参照（思想✓）
3.【OpenRA】map.yaml（可读规则）/map.bin（紧凑地形）分离+边界 8 整除+cordon 外圈+哈希防 desync——城市扩展存档格式成熟参照（格式概念✓）
4.【CDDA】分层生成管线（水→城→路→specials→地下/桥）+urbanity 梯度控城市密度——未来程序化城市蓝图（算法思想✓·代码禁搬）
5.【CDDA】成本场贪心铺路（旧路×1 新路×5 汇聚成网）+随机场成本造蜿蜒形——蛇形江之外"有机形"第二实证（思想✓）
6.【CDDA】JSON 建筑模板数据面：rows 字符画+palette 复用+参数作用域整楼一致+90° 随机旋转+place_nested 邻接感知拼块——建筑模板系统完整数据面参照（设计可学✓·JSON 件禁拷）
7.【CDDA】OMT=24×24 懒生成+位集通行缓存——城市扩展流式加载架构参照（思想✓）

## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| OpenRA 双层渲染+稳定排序→瓦片层静态化与 Y 排序校准 | 任务单（FluxVerse 俯视城质感升维） | 待接线 |
| CDDA 分层城市管线+成本场路网+贝塞尔/蜿蜒河→程序化城市储备 | 任务单（未来城市扩展程序生成参照） | 待接线 |
| CDDA JSON 建筑模板数据面→建筑模板格式设计参照 | 任务单（同上） | 待接线 |
| GPL-3.0/CC BY-SA 3.0 双红线判定：件禁入、思想可学 | 决策呈报（法红线确认） | 已闭环 |
| 待证×2：OpenRA 地形过渡数据模型（TileSet.cs 未直读）+CDDA 街区算法体内文（overmap.cpp 截断） | 判负留痕（重访触发器：定位 TileSet.cs 真实路径+overmap.cpp 后半段） | 留痕 |

- 更新记录：T0 骨架（早落盘律）→T1 双仓元数据消歧+许可直读→T2 OpenRA 引擎结构+CDDA overmap 架构→T3 渲染源码+城市生成算法→T4 地图格式+JSON mapgen→终稿 50 行
- 防线二：（留空待主会话抽验）
