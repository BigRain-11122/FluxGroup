# R-20260928-td-sor-syx — 程序街区与千人城市：Streets of Rogue+Songs of Syx（CEO 令 P-2026-09-28-10·案例解剖波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse 俯视城质感升维线+CEO 决策面·判据预注册=①SoR 街区装配如何保建筑内外可读 ②SoS 千人城表示法与渲染性能取舍 ③程序街区 vs 手工精修配比定值
> 验证声明：实读 18 次（每款恰 9·红线内）·纯失败 6（fandom 403·Wikipedia 404·Steam 新闻 JS 壳·roadmap 空壳·DDG 验证码×2）·误中 2 已纠错留痕（appid 265630=Fistful of Frags·1158290=Mini Words·正确=512900/1162750）·成源 12 条（A4/B3/C5）·M 级印象项全部标待证·DDG 后段触发人机验证=通道降级

## 一、逐游戏六维要点
### Streets of Rogue（消歧✓：Matt Dabrowski"Madguy"·tinyBuild 发行·appid 512900·SoR2=2165810）
1. 视角规格：俯视像素 sprite；店铺文案"randomly generated cities""Nuclear Throne meets Deus Ex, mixed with the anarchy of GTA"（B·SteamDB+Steam 双载体）·v1.0=2019-07-12·EA≈2.5 年·开发>5 年（A·itch devlog 原话）·销量>100 万份（B·cosmocover 通稿 2024-02-15）——确认
2. 城市结构：关卡制 level-based 程序生成（确认·A·dev 访谈直录反证："SoR2 将是 giant procedurally-generated world as opposed to something that's level-based"）+chunk=装配单元（确认·C·fandom Version_88 2019-03-14 摘要"Warning…saving a chunk when walls are placed at the chunk edges"=边缘接缝纪律）；街区 grid+建筑可进内部+五区 Slums/Industrial/Park/Downtown/Uptown 递进=推测（M·游玩印象·fandom 403 未直证）
3. 地形施工：道路平涂深灰·中线虚线极少·人行道弱化=待证 M；与 demo 瑕疵"曲路虚线远观噪"直接互证
4. 光照氛围：火/爆炸径向光晕+全屏白闪·无昼夜循环=待证 M
5. 动效状态：可燃地表火灾蔓延·水灭火·墙体可爆毁·血迹持久=待证 M（玩法传闻面广·本会话无直源）
6. 可抄点：S1-S3（见三）
### Songs of Syx（消歧✓：Gamatron AB·Jake the Dondorian·appid 1162750·勿混 Songs of Conquest）
1. 视角规格：标签 Top-Down+Pixel Graphics（A·Steam）；"retro base/city builder inspired by Pharaoh, Dungeon Keeper, Rome Total War"（A·官网）·EA 自 2020-09-21 至今·好评 94%（6409 评·A）——确认
2. 城市结构："big maps with 1:1 scale buildings"（确认·A·官网原话）·房间=墙围合+家具触发（确认·A·devlog v0.48 2019-10-31"Furniture…Used primarily to build rooms"）；布局由玩家笔画+需求涌现=判定（类型所致·无逐字直源）；市民 sprite/建筑 3D 挤出/近景切墙=待证 M
3. 地形施工：farming/crafting 成体系（C·wiki.gg 157 篇目录+种族六种）；铺装细节未直证
4. 光照氛围：昼夜/季节=待证 M
5. 动效状态："huge populations, while still simulating each individual in great detail"（确认·A·官网）+"vast real-time battles simulating tens of thousands of citizens and soldiers"（确认·A·Steam 文案）+"mega cities on the highest speed"+"Reduced lagging"（确认·A·devlog v0.48·原型期即做性能）；引擎=自研 Java（待证 M·本会话未成源）
6. 可抄点：S4-S7（见三）

## 二、对照判定面（程序街区 vs 手工精修）
- 两极样本：SoR=手修 chunk 库+程序拼装（结构预制化·服务"每局城市都可读"的 roguelite 承诺）；SoS=零程序布局·纯玩家笔画+模拟涌现密度（密度即氛围）——判定
- 天花板证据：同设计师把 SoR2 改判开放世界（A·访谈直录）且 devlog#2 专讲程序生成+building system（B·destructoid/stridepr/cosmocover 三载体）——chunk 关卡制天花板在"城市场景连续性"，64×64 demo 远未触及
- 配比结论（判定非实测）：64×64 取"手工骨架 70%+程序填充 30%"——江/螺旋环/district 调色手工（demo 已有），chunk 内部与绿化散布走 16×16 手修库拼装；SoS 证：尺度纪律+缩放两端可读成立，密度自成氛围

## 三、可抄点清单（怎么抄+cel 锚适配度）
- S1（SoR·chunk 装配）：64×64 拆 4×4 个 16×16 手修 chunk 库+拼装旋转镜像+边缘过渡瓦片强制收口（学"边缘墙"接缝纪律）→顺带修"水草直切"；cel 适配 高
- S2（SoR·低标记道路）：曲路取消中线虚线或对比度降 50%·仅直路保留标记→直修"曲路虚线远观噪"；cel 适配 高（cel 描线本应克制）
- S3（SoR·五区调色）：2~3 个子区同瓦片库调色板 swap→变体感近零成本；cel 适配 高
- S4（SoS·1:1 尺度纪律）：人物 1 格·建筑 footprint 3~5 格·街宽≥2 格·树冠 1~2 格→密度感立起来；cel 适配 中高
- S5（SoS·两端可读双瓦片层）：远观简化层+近观细节层随相机缩放阈值切换（SoS 远观屋顶体量/近景切墙的 2D 等价）→与 S2 合并落地；cel 适配 高
- S6（SoS·人群降级表现）：agent 同图集同材质批量+远端切剪影/色点（"tens of thousands"承诺的工程前提）；cel 适配 中
- S7（SoS·房间最小规则）：墙围合+家具=房间成立→建筑内部若做即用此最小规则；cel 适配 高

## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| S1 chunk 库+接缝收口（修水草直切） | 任务单（TopDownTileCity 迭代） | 接线中 |
| S2+S5 缩放双瓦片远观降噪（修曲路虚线噪） | 任务单（demo 瑕疵修复） | 接线中 |
| S4 1:1 尺度+footprint 规范 | 任务单（demo 建筑规范） | 接线中 |
| SoR2 转向=chunk 关卡制天花板证据 | 决策呈报（程序/手工配比论据） | 已闭环（本件） |
| SoS 渲染内部（sprite/切墙/自研引擎/昼夜） | 判负留痕（本会话未成源·全 M 待证） | 待证 |
| S3/S6/S7 调色 swap·人群降级·房间规则 | 任务单（低优先批） | 接线中 |

- 更新记录：T0 骨架→T1 SoR 域收口（9 读·3 败 1 误中）→T2 SoS 域收口（9 读·3 败 1 误中）→T3 终稿 46 行
- 防线二：（留空待主会话抽验）
