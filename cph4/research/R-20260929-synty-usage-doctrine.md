# R-20260929-synty-usage-doctrine — Synty 官方与生态「正确使用」范式调研（CEO 令：48 包如何正确高效使用）
> 消费方=City3D 资产战略（bm-a 机·外部资料调研）·判据预注册=①哲学②demo 证据③工作流④图集⑤EULA·禁下载/禁 Unity/禁云端生成=已遵守

## ①官方设计哲学与模块化范式
- 自述库哲学（A·syntystore.com/collections/polygon）："expansive and **cohesive** library"——『连贯统一库』=跨包兼容官方措辞；系列 84 产品在售（Unity82/UE82/Godot18），风格语言平台无关
- 官方博客载开发者证言（A·syntystore.com/blogs/blog/made-with-synty-death-scourges）："one of the few providers offering a **consistent art style across a wide range of themed packs**"
- 模块化=官方第一使用法（A·syntystore.com/products/polygon-city-pack）："Modular sections are easy to piece together in a variety of combinations"；特性表全列 Modular X Set（Road/Apartment/Shop Front/Park 等 6 套）
- 定位=生产工具库而非单件艺术品："We strive to produce the best art to enable you to produce the best games"（A·官网）；单包卖点 "Fully modular buildings!"（A·Shops Pack·1933 prefabs）

## ②demo 场景=用法说明书的证据
- demo=包体标配（A）："Includes a demo scene"（City Pack）；"Demo Scene - Included in Unity and Unreal project files"（Prototype Pack）
- demo=主题整成品组合现场："Includes a shopping mall demo scene"（A·Shops Pack——1933 个 prefab 的官方装配示范）
- demo 被当活文档维护（A·官方更新日志）："Demo scene cleanup"（City Pack v1.12.3）；"Fixed material issue with SM_Bld_ShopFront_04 **in demo scene**"（Shops Pack v1.5.1）
- 官方 Sketchfab 账号上传 demo 场景做公开预览（A·"One of the demo scenes from POLYGON Mini - City Pack" by Synty Studios·sketchfab.com/3d-models/5654893）
- 官方用途自证（A·两产品页）：Starter Pack="learning the Synty art style"；Prototype Pack="grey boxing demo scenes"——demo 兼任风格教材+灰盒样板

## ③官方工作流要点（组装流程·grid 尺度·风格统一律）
- 官方教程双证（A·官方 YouTube 频道）：《Modular Buildings in Unity (Tutorial)》(youtube.com/watch?v=cwKy7MEYW70) 教模块建筑拼装；《How to use a Synty Map Pack》(youtube.com/watch?v=4a40CjuvsSs) 教直拷官方预装配地图——先读 demo/Map、后自拼
- 官方关键词区（A·Unity 商店 Starter Pack 页 keywords）："pro grids / pro builder / grey box / Prototype"——网格吸附+灰盒=官方认定的核心用法
- 社区共识 SOP（C·reddit.com/r/Unity3D 帖 zpvd7k）："Their modular stuff is built on a grid, so get comfy with using grid snap movement. Or use vertex snap"→整楼带道具封装新 prefab 复用——与我方 City3D 装配 SOP 同构
- 技术兼容官方口径（A·City Pack Technical Info）：Unity 2022.3+·"Supports URP and Built-in"——Tuanjie URP 工程在官方支持射程内
- 上手门槛自述（A·Unity 发行商页）："easy to use, great for beginners, and fun for prototypes and game jams"——不要求建模能力，拼装即用

## ④图集机制要点（共享图集·换色=UV 挪动·材质数量策略）
- 机制（C·Palette Modifier 发布帖）：Synty 模型 "use a **single material and a texture atlas with a series of color palettes arranged in a grid like pattern**"
- 换色=UV 挪动（C·community.gamedev.tv/t/a-trick-for-recoloring-synty-assets/245419 直读原文）："click and drag to adjust **Offset X and Offset Y**. This will move the UV around and select different color swatches"；多色件有串色风险
- 官方包自带色板行（A·Prototype Pack Key Features）："10 alternative texture colors"——换色走材质/贴图预设，不动模型不动贴图
- 材质策略=少材质+共享图集（C·UE5 教程视频 WPMzVRmXncI/cRog4fM4Qro 同证）：单材质→draw call 低；官方 UE 日志 "Convert to instanced materials"（A·Shops Pack）=走共享/实例化材质路线

## ⑤EULA 商用边界要点（原文短引·主源 A=syntystore.com/pages/licences-overview）
- 现行名 One Time Purchase Licence，"(Formally known as the Standard EULA)"（A）
- 知产保留："We retain all intellectual property in the Asset"；"Modifying an Asset does not mean you own that Asset"（A）
- 商用边界=嵌入 Product 制："Product means any **videogame (which will always be covered by your licence)**, or any other product or production that we agree with you in writing"——游戏类默认覆盖、非游戏类须书面另约（A）
- 授权起点=官方渠道："Store means the Synty Store, Unreal Marketplace, or any other store where we offer Assets for purchase or download (**excluding the Unity Asset Store**)"——淘宝转售渠道不在 Store 定义内=无授权通道
- 转分发禁令："You must not distribute our Assets as stock images or stock art (2D or 3D) or **otherwise share them for re-use by third parties**"（A）——第三方转售/分享复用=直接违约
- 源文件与 AI 禁令（A·原文列举）：源文件禁出 team（承包商离场删副本·禁上传做 3D 生成）；禁入 AI 训练集·禁 AI 生成 3D 模型·禁 AI 产品推广；另禁 NFT·区块链·元宇宙类产品
- 团队定义含承包商："all employees, **contractors** and other collaborators working in a technical or creative role"（A）——Reddit C 源「承包商须各自持证」与之有张力·官方 FAQ 404 未能仲裁=待证
- 红线校准：我方「正版采购 gate=商业化前」成立且必要——48 包淘宝转售现状=零授权（连内部开发亦无正式依据）；商业化前须每包经官方 Store 购买

## ⑥一句话定谳
- Synty 官方范式=把全部包当一个统一风格语言的乐高库用：读 demo 学件间组合、按 grid 模块化拼装、共享图集单材质换色控 draw call；而一切商业化前每包必须经官方 Store 补授权——转售渠道在 EULA 的 Store 定义之外=零授权。

## 结论应用表（落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 模块化范式+demo 学习法（①②③） | 任务单：City3D 9 已进驻包逐包建 demo 学习档（装配 SOP 补「demo=说明书」步骤） | 接线中 |
| 共享图集单材质机制（④） | 任务单：URP 材质策略=材质预设/UV offset 换色·禁改贴图改模 | 接线中 |
| EULA 授权起点=官方 Store+禁 stock art 转分发（⑤） | 决策呈报/法文校准：红线表述成立；补「AI 用途全禁·承包商待证」两条 | 已闭环（本件即呈报件） |

- 更新记录：T0 骨架落盘（早落盘律）→ T1 面①⑤授权面 → T2 面②③④检索+Prototype/Shops 直读 → T3 EULA 限制面+City Pack+社区直读 → 终稿落盘。
- 验证声明（文末）：web_fetch 直读 13 页成 9——404×2（syntystore.com/pages/faq、/pages/faqs）·仅吐导航无正文×2（Unity 商店页、ultimategameassets.com）；另检索 7 次。
- 成源分级：A=7（syntystore 官方产品/授权/博客页+官方 YouTube+官方 Sketchfab+Unity 发行商自述）·B=0·C=4（Reddit/GameDev.tv/Palette Modifier 帖/UE5 教程视频）。
- 承重主张均 A 级直读（模块化范式·demo 标配·EULA 原文短引）；「换色=UV 挪动」为 C 级多源同证（GameDev.tv 直读+Palette Modifier+2 个 UE5 视频）——按纪律标推测级而非确认级。
- 失败面：官方 FAQ 全路径 404 → 承包商持证疑点无法 A 级仲裁=待证留痕；防线二建议直读 syntystore.com/pages/licences-overview 与 products/polygon-city-pack 抽验两承重主张。
