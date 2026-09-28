# R-20260928-td-simcity-oss — 城市正典源流与开源营建：SimCity1989+Micropolis+Cytopia（CEO 令 P-2026-09-28-10·案例解剖波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse TopDownTileCity demo（Tuanjie 1.10.3·64×64·30° 俯角·日漫 cel 锚）质感升维线+CEO 决策面·判据预注册=J1 极简 tile+分层网格能否达商业可读城市表达·J2 demo 三瑕疵（曲路远观噪/滨水孤树/水草直切）有无已验证修复技法·J3 技法在 cel 锚+许可边界下哪些可入交付链
> 验证声明：实读 20 次（满预算）·成源 15 条（A=14·B=1·C=0·M=0）·失败面 5：cytopia.net 官方域名沦陷为赌博站（不采信，Cytopia 官方面改以 GitHub/itch.io 为准）·SimHacker/micropolis wiki 3 链接 404（has_wiki=false，README 内链已死）·MicropolisCore/src/Micropolis 目录路径 404
## 一、逐项六维要点（源分级随条；三态=确认/推测/待证）
### ① SimCity 1989（Maxis·Will Wright）[B：维基全文直读]
- 视角规格：纯 2D 顶视无俯角；DOS=EGA 320×200/640×350→后版 VGA 640×480/256 色；Amiga V2 可整包热换 tileset（原句"a tileset consists of all the images the game uses to draw the city"）；CDTV 为电视远观改更近视角=可读性优先
- 城市结构：R/C/I 分区+Sims 按交通/电力/犯罪/邻里自建并升级（house→apartment/light·heavy industrial）；特殊建筑多格（警/消/体育场/港/机场/电站）；场景=真实城市布局复刻；分区=3×3 章【A：Micropolis 源码 RESBASE 240-248/COM 423-431/IND 612-620 各 9 格证——此前"2×2/3×3 两档"社区记忆判负留痕】
- 地形地表：官方 Terrain Editor=forest/land/water 三态刷+随机地形；BBC Micro 25KB/4 色版功能几乎全保=tile 语义表达>像素细节
- 光照氛围：无动态光照；SNES 版季节全城 tile 调色置换（夏绿/秋锈/冬白/春樱）
- 动效状态：灾害序列动画（怪物/龙卷风/火灾/地震）；建筑成长=tile 变体直换
- 可抄点：SC-a tileset 全量换皮架构；SC-b 状态→瓦片直换；SC-c 远观可读性（缩放换粗虚线变体）；SC-d 4 色极简读性测试。许可：1989 商业闭源→纯思想公地，零风险
### ② Micropolis（EA 2008 GPL·Don Hopkins 系）[A：SimHacker 双仓+micropolis.h 源码直读]
- 视角规格：纯顶视；地图=120×100 格（源码注释原文"Map[0 <= x < 120][0 <= y < 100]"）；tile=16×16px（EDITOR_TILE_SIZE=16）；每格 ushort=低 10bit tile ID（TILE_COUNT=1024 槽）+高 6bit 标志位（ANIMBIT/BULLBIT…）；引擎/UI 完全解耦；MicropolisCore=C++→WASM→SvelteKit+WebGL tile 渲染（Canvas2D/WebGL2/WebGPU/软件四后端）
- 城市结构：分区 3×3 章+章内分级长成（单格 house→公寓；工业=population 0-3×value 0/1 双轴 tile 组）；特殊建筑 3×3（医/教/警/消）与 4×4（体育场/电站/港/机场）；移动体=SimSprite 独立图层 8 类（火车/直升机/飞机/船/怪/龙卷风/爆炸/公交）
- 地形地表：base tile 图+10 余张覆盖层按 2×2/4×4/8×8 降采样（人口/交通/污染/地价/犯罪=MapByte2·地形=MapByte4·电力=MapByte1·成长率/警消覆盖=MapShort8）；地形生成=种子→岛（ISLAND_RADIUS=18·10% 概率）+河弯/湖泊/树量参数+treeSplash 后 smoothTrees/smoothRiver/smoothWater 平滑；水岸 16 边缘 tile（FIRSTRIVEDGE 5→LASTRIVEDGE 20）
- 光照氛围：无动态光，明暗烘焙于 tile 内；四角明暗变体社区技法【待证 M：本波未直验，勿采】
- 动效状态：FIRE=8 帧+ANIMBIT 注册制 animateTiles()；烟囱 4 组×4 帧（COALSMOKE 916-931）/喷泉/雷达/核涡同类；交通→道路 tile 段直换（LTRFBASE=80 低密度/HTRFBASE=144 高密度）+decTrafficMap 时间衰减；断电=powered/unpoweredZoneCount+doSpecialZone(PwrOn) 状态分叉
- 可抄点：MP-1 覆盖层分级降采样热力带；MP-2 地形后处理平滑；MP-3 状态→tile 段直换+衰减；MP-4 1024 槽+标志位布尔编码；MP-5 .cty 存档+CLI ASCII 网格自检
- 许可：GPL-3.0-or-later+§7 附加条款（无商标权/禁称 SimCity/须标 modified）【A：micropolis.h 头文件直读】+2024"Micropolis Public Name License"（名=Micropolis GmbH 注册商标·非商业·须署名·禁域名/招牌用途）——思想可抄，代码与资产零搬
### ③ Cytopia（CytopiaTeam·2018-·C++/SDL2）[A：README+wiki×4 直读]
- 视角规格：等距渲染引擎基于 SDL2（README 原文"custom isometric rendering engine based on SDL2"）+像素美术（Kingtut 101 团）；相机平移/缩放/重定位；⚠等距≠顶视：技法可迁移、视觉不可直抄
- 城市结构：一切建筑=TileData.json 条目（id/RequiredTiles WxH 多格/power 负=耗/water/inhabitants/价格/维护/犯罪/污染/火险/教育/happyness/wealth 低中高/style 亚欧美/zones R-I-C-农/biomes）；放置模式↔TileType 映射：SINGLE=DEFAULT·WATER｜LINE=AUTOTILE·UNDERGROUND｜RECT=ZONE·GROUNDDECORATION
- 地形地表：tileType 枚举=TERRAIN/WATER/AUTOTILE（原文"like roads, power lines, etc"）/ZONE/GROUNDDECORATION（装饰层，建筑可上盖）/UNDERGROUND（BLUEPRINT 层）；terrain 专项 shoreLine（水岸过渡精灵）+slopeTiles（坡地）；程序化地形=libnoise；spritesheet=clip_w/h+count+offset+pickRandomTile（道路等有序 tile 须关随机）；等距拾取=列遍历+不透明像素精检+Z 序取前景
- 光照氛围：日/夜循环未证实【待证】；groundDecoration=建筑脚底铺草地/混凝土（多 tileID 随机·拆除连带·可上盖）；planned：Biomes/OpenGL 渲染器/Lua mod
- 动效状态：spritesheet count 帧序动画；施工/废弃阶段未直证【待证】；OpenAL 双耳音轨/环境音
- 可抄点：CY-1 TileData 全量真值表 schema；CY-2 shoreLine/slopeTiles 专项资产清单制；CY-3 AUTOTILE/装饰层/BLUEPRINT 分层思想；CY-4 资产命名律 type_WxH_名_作者.png+作者署名；CY-5 资产许可 CC-BY-SA 4.0（wiki 原文"Cytopia is licensed under GPLv3 and it's assets under CC-BY-SA 4.0"）
## 二、对照判定面（含许可判定表）
- 消歧[A：api.github.com 直读]：Micropolis 正典=SimHacker/micropolis（1109★·C·历史仓·license 字段 null→许可在源码头文件+名许可文件）+SimHacker/MicropolisCore（197★·C++/TS·2026-09 活跃·live=micropolisweb.com）；镜像 osgcc/simcity=GPL-3.0（152★）；同名排除：graememcc/micropolisJS（727★ JS 港）·bsimser/Micropolis（97★ Unity C# 重写·NOASSERTION 慎用）·dheid/micropolis（52★ Java）；血统 C64→Mac→NeWS/HyperLook→X11/TclTk（SimCityNet 多人）→OLPC→C++Core→WASM/TS【A】
- Cytopia=CytopiaTeam/Cytopia（2167★·130 fork·GPL-3.0·master·2026-09 活跃·TileData-Editor 伴仓）；GitHub 用户"cytopia"=DevOps 工具人无关；cytopia.net 域沦陷【失败面】
- 许可史[A/B 双源吻合]：2008-01 EA 开源+GPL§7（维基 B+osgcc license 字段 A+头文件 A）；Cytopia 资产=CC-BY-SA 4.0【A】
| 项目 | 代码 | 资产 | 名称 | 判定 |
|---|---|---|---|---|
| SimCity1989 | 无源 | ©EA 美术不可用 | SimCity™=EA | 仅思想公地可学 |
| Micropolis | GPL-3.0-or-later+§7 | 随代码 GPL | "Micropolis"=Micropolis GmbH 名许可（2024·非商业·署名） | 代码/资产禁入集团交付链；思想/数据结构可学 |
| Cytopia | GPLv3 | CC-BY-SA 4.0 | — | 代码禁搬；资产可改用但衍生须同许可+署名（ShareAlike 传染→闭源商用须法务评估） |
- 判定：J1 确认——1024 槽 tile+覆盖层数据网格即达商业可读（1989 全平台畅销：PC 50 万+SNES 198 万【B】+源码架构【A】），demo 64×64 网格路线获正典背书；J2 确认——三瑕疵修复技法三源流全命中（见三.1-3）；J3——思想层全绿/代码层全红（GPL 传染）/Cytopia 资产层黄（条件可用）
## 三、可抄点清单（逐条怎么抄进 demo·cel 适配度·许可边界）
1. 水草直切→抄 Micropolis 水岸 16 边缘 tile+smoothWater：把 demo 现有"道路 16 邻接掩码"系统复制到水↔草轴（同 4-bit 邻接码+岸滩内圈两档过渡）｜cel 适配高：岸线 cel 描边+平涂浅滩，忌噪点抖动｜纯思想复用零代码
2. 滨水孤树→抄 treeSplash+smoothTrees：种子点爆+密度变体（TREEBASE 21-43 稀疏→森林 5 档）+离水约束+簇状散布消灭单棵噪点｜cel 适配高：硬边树影+色阶化簇｜纯思想
3. 曲路远观噪→抄 CDTV 近视角先例+SC-b 变体直换：按相机 zoom 档位切"细虚线/粗实线"两套道路瓦片（阈值驱动 sprite swap），远观可读优先于近观细节｜cel 适配高：远观统一粗描线正合 cel 纪律｜SimCity 思想公地
4. 覆盖层热力带→抄 MP-1：2×2/4×4/8×8 分级 byte 图做人气/交通/地价层，驱动建筑分级与橱窗亮灯（不直接显示热力色，翻译成建筑状态）｜64×64 直接可抄｜数据结构思想
5. 状态→瓦片直换引擎→抄 MP-3：统一"状态字节→sprite 段"映射（交通段/断电 doSpecialZone(PwrOn)）；cel 断电表现=关窗暗色+冷色调，非全黑｜思想
6. 瓦片注册表→抄 MP-4：10bit ID+6bit 标志位=1024 槽+布尔可查询（可燃/可推土/动画/导电），Tilemap 配置化+Unity ScriptableObject 化｜数据结构思想
7. 瓦片真值表→抄 CY-1：TileData schema（尺寸/社会经济属性/wealth/style/biomes/groundDecoration）为 demo 单源瓦片库，比 RuleTile 多模拟轴（Tiled/LDtk/RuleTile 详见 R-20260928-unity2d-bigmap-oss* 专件，不重复）｜schema 思想自研实现
8. 分层纪律→抄 CY-3：地表/AUTOTILE 自连/装饰底（可上盖）/结构四层+统一放置模式（单格/线/矩形），兼容现有 Y 排序｜思想
9. 建筑底面→抄 CY groundDecoration：建筑脚底强制铺统一底纹（草地/混凝土·多 tileID 随机），消灭"建筑浮在草纹上"脏感｜cel 适配高｜思想
10. 资产工程律→抄 CY-4 命名律 type_WxH_名_作者.png+单源 TileData；产能不足时可评估 Cytopia CC-BY-SA 资产改用（署名+同许可传染；且等距资产对顶视 demo 适配差，大概率仅参考其调色【M 推测】）
## 四、结论应用表（落点四选一=任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 三瑕疵修复三招（水岸邻接掩码/树簇平滑/远观变体直换）正典+源码双证 | 任务单（TopDownTileCity 质感升维任务单） | 已闭环 |
| 覆盖层热力带+状态直换引擎=城市活感骨干（120×100 正典同构缩至 64×64） | 任务单（demo 模拟层任务单） | 已闭环 |
| TileData 真值表+分层纪律+建筑底面处理=美术工程基建 | 任务单（demo 资产管线任务单） | 已闭环 |
| GPL 双仓只学不搬；Cytopia 资产 CC-BY-SA 4.0 传染性红线 | 法文修改（研发许可红线条款） | 接线中 |
| "Micropolis"=Micropolis GmbH 商标（2024 名许可）+SimCity 名义禁区 | 决策呈报（对外命名避雷） | 接线中 |
| 社区记忆"1989 分区含 2×2 档"=误（源码=3×3 章） | 判负留痕（见一.①） | 已闭环 |
- 更新记录：T0 骨架落盘→T1 SimCity1989+双仓消歧（读 6）→T2 Micropolis 许可/架构+Cytopia 框架（读 15·败 5）→T3 micropolis.h 源码+TileData schema+Engine/Game wiki（读 20 满）→终稿 58 行
- 防线二：（留空待主会话抽验）
