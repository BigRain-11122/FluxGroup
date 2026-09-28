# R-20260928-td-stardew-crosscode — 日漫/高清像素质感对照：Stardew Valley+CrossCode（CEO 令 P-2026-09-28-10·案例解剖波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse 俯视城质感升维线+CEO 决策面·判据预注册=①两款 tile 规格/过渡手法能否逐格映射 32px·PPU32+16 变体掩码 demo？②「贵感」配方中对 demo 成本最低见效最快 3 动作？③各手法对日漫 cel 锚（非像素风）适配度？
> 验证声明：实读 19 次（Stardew 7·CrossCode 10 触顶·公用 2）·成源 8 条（A=5：SV 官方 wiki（Barone 2021 年收回所有权）Modding:Maps/Villagers+Steam 官方页+RFG 官网及存档；B=2：两条 Wikipedia 具名转引 Gamasutra/PC Gamer/Polygon；C=1：wiki NPCs 分类页弱成源；M=2 待证项）·失败面：gamedeveloper.com/pcgamer.com/siliconera.com/crosscode.fandom.com 反爬 403/404×4、RFG 站内 3 路径 404、archive CDX 超时×1——Barone 一手访谈未直读，经 Wikipedia 具名转引采信为 B 级

## 一、逐游戏六维要点
**Stardew Valley**（ConcernedApe·2016-02-26·C#/XNA→2021 迁 MonoGame·单人开发·至 2026-02 累计 5000 万份【B】）
- ①视角与规格：纯 2D 正交俯视【B】；tile=16×16px、自定义表必须 16×16 分格【A:Modding:Maps】；源外屏幕放大倍数未获权威源【M/待证】
- ②城市与建筑：世界=多地图分区切换（黑屏过场）【A】；建筑=Buildings 层整格占位、默认碰撞墙；地图宽>200 tile 破图层【A·工程红线】
- ③地形施工（主维）：五层渲染 Back→Buildings→Paths→Front→AlwaysFront【A】；Tiled tileset 内含 terrain 类型定义=边缘过渡变体体系（岸线/草皮边缘预画在 tilesheet+地形规则）【A】；Front 层=玩家在其北侧时盖住玩家的行级遮挡（树冠类）【A】；水=Back 层 Water 标记+引擎自动叠水面动画 overlay【A】；草/树/石/灌木=Paths 图标格在地图生成时转可交互对象（草22·蓝草36·树9-12/23/31-32·树 50%/日重生·灌木24-26）【A】；瓦片翻转/旋转免镜像变体【A】
- ④光照（主维）：AmbientLight=从白(255,255,255)减去 RGB 的减法 tint+夜间独立值（室外昼夜循环引擎驱动，DayTiles glow 文本可证）【A】；9 型点光源按格摆放+白天专属窗光 WindowLight+Paths 层刷灯【A】；DayTiles/NightTiles=6 点-19 点昼/夜整格换瓦+glow 模拟日光（路灯/窗）【A】；季节=整套 tilesheet 切换（spring_outdoorsTileSheet 命名可证）【A】；评测「lighting effects…magical」【B:4Players】
- ⑤动效与状态：AnimatedTile 均帧动画（例：Gil 摇椅）【A】；割草/砍树即时消失再生【A】；BrookSounds=地图级环境音源布点（溪/火/蟋蟀/瀑布 5 型）【A】
- ⑥生活感：34 名可送礼村民各有每日作息+按天气/时段换位+独特礼物偏好好感度【A:Villagers】；节庆专用地图定期改造城镇【A】；美术音乐一人包办（Paint.NET 像素画+Reason 作曲）·约 5 年·按太平洋西北家乡实景取材【B】

**CrossCode**（Radical Fish Games·2018-09-20·Deck13 发行·2011 立项 7 年开发·核心≈7 人·JavaScript 代码·主机版靠发行商编译【B】）
- ①视角与规格：2D 俯视+自建 3D 物理系统=多高度层级（高台跳跃）【B】；tile 具体尺寸未获权威源【M/待证】；官方口径「16-bit SNES-style graphics」【A:Steam 页】
- ②城市与建筑：MMORPG 题材自带城镇功能分区叙事；开发序=玩法→地图→叙事后置【B】
- ③地形施工（主维）：图形锚=SNES《Chrono Trigger/Terranigma》，「保留旧风但加现代图形元素如 shadow maps」（据 RPG Maker 经验）【B:Wikipedia 引 Gamasutra 访谈】；引擎名（社区传 ImpactJS）与瓦片施工细节未直接成源【M·勿采信】
- ④光照（主维）：shadow maps=官方确认的现代元素【B】；评测「packed with all kinds of detail and colour」「pleasingly fluid」【B:Nintendo Life】
- ⑤动效与状态：「butter-smooth physics」官方卖点【A:Steam】；战斗动效密度高（弹球/元素切换）；Switch 忙时掉帧=特效重的反证【B】
- ⑥动态环境层次：远景/天气层未成源【待证·防线二抽验候选】

## 二、对照判定面（两款「贵感」配方·三判据作答）
- 判据①：Stardew 施工法（大瓦片底+图层分职+terrain 变体+图标撒物件+整套季节换皮）与 demo 的 32px·16 变体掩码+Y 排序路线同构度极高，可逐格映射【确认】；CrossCode 仅可抄光影/动效层【确认】
- 共同配方=「瓦片只做底色，贵感来自光照时段循环×物件密度×柔影」：Stardew 同一地图=昼夜换瓦+季节整套换皮+点光≈16+ 套视觉状态；两款皆非靠瓦片精度堆料【确认·A/B 双源】
- 判据②（成本最低 3 动作）：S1 减法 tint 时段色 ＞ C1 全场景接触阴影 ＞ S4 撒物件提密度【确认】
- 判据③：光照/阴影/撒物件与日漫 cel 锚全兼容（cel 渲染本以光照色块为主干）；像素抖动混色类手法判负不抄【确认】

## 三、可抄点清单（怎么抄+cel 锚适配度·S6 条/C4 条）
- S1 减法 tint：全屏色罩做 255−RGB 映射，白昼→黄昏→夜→深夜 4 阶段插值+夜间独立色板【适配度：高】
- S2 点光+窗光：路灯/窗=地图标注 light 点，夜间暗幕挖光圈（仿 9 型光源+白天 WindowLight）【高】
- S3 昼夜换瓦：对 AI 建筑素材做日/夜两套贴图，7 点前后 SetTile 批量切（仿 DayTiles/NightTiles）【高·暖窗色块=cel 强生活感符号】
- S4 撒物件层：运行时把逻辑格转装饰对象（草/灌木/石/杂物）成组撒+边缘规则，每屏数十个【高·直接治滨水孤树】
- S5 前景层：树冠/建筑顶盖走行级遮挡（demo 512−⌊y⌋ 已等价）；增量=AlwaysFront 前景枝叶层【高】
- S6 环境音源：水边/广场/林荫布循环音源仿 BrookSounds【中】
- C1 接触阴影：建筑/树脚统一椭圆柔影——SNES 风+shadow map 不违和即 CrossCode 实证，cel+柔影=最大高清感杠杆【高】
- C2 发光体：招牌/灯笼/全息自发光+泛光，与 S2 光圈联动【中高】
- C3 动效纪律：一切交互带缓动（「butter-smooth」卖点）【高】
- C4 节庆换皮：整套换贴图+物件做「灯会模式」（仿 festival maps）【中·后置】

## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 贵感=光照时段循环+物件密度+柔影三件套，非瓦片精度 | 任务单：TopDownTileCity 质感升维（S1→C1→S4 先行） | 接线中 |
| 32px·PPU32+16 变体掩码与 Stardew 施工法同构，底座保留不推翻 | 任务单：现有 demo 底座确认 | 接线中 |
| 虚线曲路噪/水草直切治法=S4 边缘规则成组撒+S1 tint 弱化远观噪点 | 任务单：demo 已知瑕疵修复线 | 接线中 |
| CrossCode tile 规格/引擎名未获权威源，勿据此立项 | 判负留痕（重访触发器=RFG 博客 Technical 旧帖直读） | 已闭环 |
| 质感量化验收：每屏装饰物件数+光照时段态数入多模态判据 | 决策呈报：7-9/10→9+ 验收面补充 | 接线中 |

- 更新记录：T0 骨架落盘（早落盘律）→T1 Stardew 六维（7 读·A=2/B=1/失 2）→T2 CrossCode（10 读触顶·A=3/失 6）→T3 终稿（实读 19 次·成源 8 条·60 行内）
- 防线二：（留空待主会话抽验）
