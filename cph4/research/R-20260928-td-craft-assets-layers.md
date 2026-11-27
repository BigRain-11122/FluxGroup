# R-20260928-td-craft-assets-layers — 施工技法A：素材管线+图层建筑（CEO 令 P-2026-09-28-10·技法波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse「灰盒→优质化施工法」+32×32 对比样区·判据预注册=Q1 32px/PPU32+16 掩码规格是否够/需否升档；Q2 512−⌊y⌋ 手排 vs sorting layer 混用何者施工更稳；Q3 悬空/孤树/直切三病最低成本处方
> 验证声明：实读 20 次（read_file 6+web_fetch 14·预算帽打满）·成源 9（A 级 4=pixel-perfect 本机包文档/SpriteAtlas/sortingOrder/GraphicsSettings 官方页；A 转录 1=SOP 内团结官方表；仓内锚件正典 4）·半成 2·失败面 9 如实列：Pixel Perfect 网页 4 连 404（包名实为 com.unity.2d.pixel-perfect@5.1.0·改本机 Documentation~ 直证闭环）、Wang 文 403+archive 未归档（47 转待证）、TilemapRenderer 2 slug 404（Chunk/Individual 转待证）、2D-sorting 页 404、纹理平台表抓取不全（ASTC 判据改以 SOP 团结官方表转录为源）；另注：gitignored PackageCache 被 glob/list 静默跳坑×3，改 run_shell_command 只读列名直证（不占读取预算·不改盘）
## 一、环① 素材与像素管线（逐条做法+参数）
- **tile 规格（Q1a）**：**维持 32px/PPU32** ✓——PPU=tile 像素宽→1 tile 精确=1 world unit（td-tileset.py 头注「32px·1 unit at PPU 32」直读同构）；升 64px=全资产 4x 像素重制、无收益证据。高清像质感正路=**非网格件原生高分辨率**（seedream 建筑/树/钟塔已在用·引用不重建）+图集统一压缩+30° 俯角美术纪律本身；地面升 64px 只作样区 A/B（改 S=64 重渲·非放大）→应用表①。
- **切割规格（Q1b）**：现 4-bit 边掩码（N=1/E=2/S=4/W=8→2^4=16 变体·td-tileset.py 直读）=2 色 Wang 边片等价（算术自明）。判定：**道路=边连接·16 掩码够用** ✓（曲病在画法不在掩码数·见§三）；**面过渡（水→草）需 8 邻域内角**：2^8=256（算术）·对称归并≈47 变体【待证：Tulleken 2013 名篇 403+archive 未归档·防线二/下波补源】。水草直切根因≠掩码不足=**水面瓦片零过渡变体**（water1/2 纯色+高光·源码直读）。
- **瓦片产线**：PIL 产线 ✓ 保留为基座（确定性/调色板锁/零成本/秒级重生成/manifest 驱动）；缺陷=ImageDraw 无抗锯齿、arc(width=) 低半径锯齿、dash 手工常数不随弧长（road_tile() 曲线段直读）=曲路虚线噪机制根因。修法：①2x-4x supersample 画布+LANCZOS 回缩②虚线改 2px 实线或 8px 段+4px 隙（2^n 对格）。AI 产线只入**非网格层**（AI 地形瓦片需无缝+掩码裁切·不划算）；**com.unity.2d.aseprite@1.1.9 已在盘**（PackageCache 直证·com.unity.feature.2d@2.0.1 特性集在列）=.ase/.aseprite 导入通道【功能面 M 通识·文档在盘未读】——手工补角变体零安装成本可选·非必需。
- **图集与压缩**：25 张散 PNG（源码直读·头注写 24=陈旧计数）→**必须入图集**（团结官方 SpriteAtlas 口径=「合并小贴图减少 DrawCall」·SOP §2.3 A 转录）且图集**单格式 ASTC 6x6**（团结 WebGL Normal 官方默认·SOP §2.2 转录；微信转换工具识别集 {8x8,6x6,5x5,4x4} 双源）；「多纹理压缩格式不支持图集」→禁 per-atlas 多格式（同源）；**Padding 默认 4px**（Unity SpriteAtlas 官方 ✓）——ASTC 6x6 块=6px·32/6=5.33 非整除【🟡 推断跨缝渗色风险→padding 4 维持或加到 6】；.meta 九律走 ArtSetup 机械导入（SOP §2.2）。
- **像素完美（判负留痕）**：com.unity.2d.pixel-perfect@5.1.0 在盘（PackageCache 直证）但**判负不启用**：官方准备清单=全员同 PPU+Filter Mode=**Point**+Compression=**None**（本机包文档 A 原文）——与房规 Bilinear+ASTC 6x6（SOP §2.2）正面对撞且像素风已废；Pixel Snapping「prevents subpixel movement」冲突 NPC 平滑移动+滚轮连续 zoom 4.5→18；Crop Frame 黑边冲突全屏城景。可借鉴=PPU 全员一致律+官方 snap 公式 Move X/Y/Z=1/PPU（A 原文）。重访触发器=样区转像素风或锁整数缩放镜头时重评。
## 二、环② 图层与建筑表示（逐条做法+参数）
- **分层架构**：Grid 内多 Tilemap 层=标准做法；sorting layer 栈=Water(-3)<Ground(-2)<Road(-1)<Decal(0·标线/泡沫/落叶)<Structure/Actor(1·建筑+NPC 同层 Y 排)<Overlay(2·雾光)<UI。demo 现有 ground+road 两层 ✓（road 透明带宽出带外·头注直读）→**补 Water 与 Decal 两缺失层**（水移专层·过渡瓦片落 Ground）；tilemap 层保持默认合批·结构与活动件走独立 SpriteRenderer 非 tile【TilemapRenderer Chunk/Individual=M 通识待证·官网 2 slug 404】。
- **30° 俯角建筑表示**：单 sprite actor=上部屋顶盖+朝下立面露门脸·**pivot=基脚**（着地律同源：pivot 脚底非中心）；比例律沿正典执行（R-20260924 §二①直读）：角色:建筑 1:4·L1 门脸=4×角色身高·门洞≥1.5×角色身高·招牌≤楼体 1/2·tile 阶梯=沿街 2-4/办公 4-6/地标 96-160px 大精灵；建筑可读性=门脸+招牌+阶梯三件·屋顶主色块+浅高光防噪。
- **Y 排序（Q2）**：方向核对 ✓：官方原文「lower number=further back·higher=closer to camera」→512−⌊y⌋=低 y（画面下方近景）得高序在前·正解；范围 −32768..32767（官方 A 原文「must be between -32768 and 32767」）→512−⌊y⌋ 在 y≤33279 内合法（64×64→order 448-512 安全区）——实践无忧；同行并列=序并列（tie 由创建序兜底）。判定=**双轨**：静态建筑 spawn 算一次 ✓（零运行成本）；NPC/动态件二选一：逐帧重算同式（最稳·无方向疑点）或同层同 order+**Transparency Sort Mode=Custom Axis·Axis=(0,1,0)**（官方机制 A 原文·「Custom Axis=Sort objects based on the sort mode defined with the Transparency Sort Axis」·2D 专用）【🟡 轴向与手排同向为推断·官方页未给方向语义·样区一帧实验定：判据=NPC 站钟塔基脚正下 1 格时 NPC 须遮立面】；⚠️ 手排 order 与轴排不可同层混用【🟡 Order 层内优先于轴=通识·2D-sorting 页 404 待补】。
- **接地处理（Q3）**：着地三查律正典在册（①pivot 脚底②Y 贴地面 tile 上沿零离缝③带接地阴影·R-20260924 §二③直读）——本环补「阴影怎么做」三件套：①脚下椭圆影**单 sprite**（黑·alpha 0.2-0.35·order=actor−1；SOP §1.3 族5「影子椭圆单件化」判例同源）②sprite 底边烘焙 AO 暗边（PIL/AI 后处理一道）③滨水件加倒影/暗化条+岸线泡沫 decal；水面禁栽律沿正典（静态物件禁直立水面·须岸线内或带堤墩——R-20260924 直读）。
## 三、对 demo 三瑕疵与历史病的针对性处方
- **曲路虚线远观噪**：根因=arc 无抗锯齿+dash 手工常数（§一产线条）→supersample 2x+LANCZOS/改 2px 实线/dash 8px+4px 对格；标线移入 Decal 子层与路面底色解耦（线形不再继承掩码复杂度）。
- **滨水孤树**：根因=树无接地影+近水落位违例→椭圆影单件+树位约束 grass tile+岸边 AO 暗化+岸线泡沫 decal（§二三件套）。
- **水草直切**：根因=水瓦零过渡变体（§一）→td-tileset.py 扩 shore 变体类（**16 掩码管线直接复用**·泡沫/湿边 1-2px）+RuleTile MirrorXY 规则化（大地图 R 件灰盒行动表在册·引用不重建）；内角要圆再议 47-blob（待证）。
- **历史病**（比例失调/NPC 悬空）：§二建筑表示+着地三查已覆盖（1:4/门洞 1.5×/pivot/阴影）——正典在册引用不重立。
## 四、结论应用表（research-protocol §二.1 强制·落点四选一=任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| ①维持 32px/PPU32·非网格件原生高清；地面 64px 留样区 A/B 对比 | 任务单：@32×32 样区（32px vs 64px 重渲·多模态评分） | 接线中 |
| ②道路 16 掩码够用；水→草过渡=16 掩码管线扩 shore 变体 | 任务单：@td-tileset.py 扩 shore 类（泡沫边 1-2px） | 接线中 |
| ③PIL 产线保留+supersample 抗锯齿补丁（虚线噪根因修复） | 任务单：@td-tileset.py 曲线重绘改造 | 接线中 |
| ④25 散 PNG 入图集·单格式 ASTC 6x6·Padding=4 | 任务单：@City 工程图集接线（沿 SOP §2.3 判例） | 接线中 |
| ⑤Pixel Perfect Camera 判负不启用（Point+无压缩清单撞房规·像素风已废） | 判负留痕：施工法像素节「不引入·PPU 纪律+1/PPU 动步取代·重访触发器在册」 | 已闭环 |
| ⑥分层栈补 Water/Decal 两层·Structure 层=建筑+NPC 同层 Y 排 | 任务单：@施工法图层节+@样区接线 | 接线中 |
| ⑦Y 序双轨：静态 spawn 手排一次/动态逐帧重算（轴排=备选·方向一帧实验定） | 法文修改：施工法排序节（512−⌊y⌋ y≤33279 合法域注记） | 接线中 |
| ⑧接地三件套（椭圆影单件/AO 底边/接水暗化+泡沫 decal） | 法文修改：着地三查律补「执行注」 | 接线中 |
| ⑨两待证数（blob-47·TilemapRenderer Chunk/Individual 原文） | 任务单：@防线二/下波补源（403/404 死面已留痕） | 接线中 |
- 更新记录：T0 骨架落盘 → T1 锚件 5 直读（模板/两 R/SOP/tileset 源码）→ T2 环①外部投采（SpriteAtlas/纹理表半成/pixel-perfect 网页 404→PackageCache 本机包文档直证）→ T3 环②外部投采（sortingOrder/GraphicsSettings 成·TilemapRenderer 404）→ 终稿 33 行。
- 防线二：（留空待主会话抽验）
