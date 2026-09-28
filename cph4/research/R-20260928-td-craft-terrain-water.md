# R-20260928-td-craft-terrain-water — 施工技法B：地形过渡+水岸天气（CEO 令 P-2026-09-28-10·技法波）
> 溯源：ledger P-2026-09-28-10（CEO 原话 2026-09-28 ~15:2x 摘要）·消费方=FluxVerse 灰盒→优质化施工法+32×32 样区实证·判据预注册=①除 Isometric/Hexagonal 外有无官方 Top-Down 专用过渡件？②2D 瓦片图集 mipmap 开关与防渗色参数？③全屏天气在本工程的最短实现路径？
> 验证声明：实读 19 次（锚件 4+技能纪律 1+外网 6+本地官方包文档/目录 8）·成源 A=7/B=0/C=0/M=3·失败面：GitHub extras 仓 404（锚件已证正典分发=Package Manager·改本地直读）·URP 官网索引 ToC 空载（被 PackageCache 在盘直证取代）·PS Manual 主页为模块桩页（改读 ScriptRef 成）·PS 渲染模式枚举值未逐字直读（属性面已证）
## 一、环③ 地形过渡施工（逐条做法+参数）
1. **①水岸过渡**：判据①答——**无 Top-Down 专用官方过渡件**：extras@3.1.3 文档在册 tile 仅 Animated/Rule/RuleOverride（A·Tiles.md 直读）·Runtime 全脚本=RuleTile/Hexagonal/IsometricRuleTile/Animated/RuleOverride/AdvancedRuleOverrideTile/GridInformation·全库零「top-down」字样（A·在盘直证）；俯视过渡机=Rectangle RuleTile 3×3 三态+Rotated/Mirror 变换（锚件 RuleTile.md 精读·A）。施工=双环+一线：**水侧泡沫环**=临陆水格画泡沫线·缩进 2px 勿贴边·断续线（段 4-6px/隙 3-4px·α70-85% 白青）·2-3 帧与波动帧同步（六件④律·R-20260925）；**陆侧湿滩环**=临水草格压暗+增饱和、或现役 SAND 104 格环带靠水 1 格改湿沙深色变体（沙带=改造基底非推倒）；草沙边 2-3 行 50% 棋盘 dither；再叠 2-3 格大幅 decals 补丁层破网格（F2·FFF-219 不受平铺约束）。堤岸可选=城侧陆格水向 2-4px 暗边+1px 亮棱。
2. **②曲路标线远观噪**：病根算式（M·推导·1080p 假设）：屏上 1 美术 px=1080/(2·S·PPU32)≈16.9/S——S=11→1.53px/S=16→1.05px/S=32（整城远观）→0.53px<1 必闪。三层处方：a) 美术底线=标线 2px（tile 的 1/16）·段≥6px·隙≥4px·线/路面明度差≥30%；b) 纹理=地面图集开 **Generate Mip Maps**（A·SpriteAtlas 属性表原文）+**Padding 保默认 4px** 防瓦间渗色（A·同页）+瓦片纹理 mipmapEnabled（A·TextureImporter）+alphaIsTransparency 透明区膨胀防边缘伪影（A·同页）；Filter Mode=Point 保 cel 硬边（A·pixel-perfect 备律）→Point+mip 远缩把虚线聚合成色带（F3 同族·锚件）；c) LOD 保险带=S>16 时切第二 Tilemap「无虚线色带变体」层（同掩码数据双份预摆·renderer.enabled 切换零重摆成本）。备选=弃虚线改 4px 色带。注：Pixel Perfect Camera 会改正交尺寸（A）·与缩放脚本共存须样区实测【🟡】。
3. **③交叉口/桥头**：4bit 16 掩码已含全 15 非空组合（3 通×4+4 通×1）——交叉口零新机制·只需 16 变体美术画全（25 张现役集查缺补 3/4 通）；桥头=新桥件 4+2：4 向桥头瓦（abutment·「路向+桥向」双掩码保接缝零突起）+2 向桥面（桥面宽=路宽-4px·两侧 2px 栏杆）；BRIDGES 96 格现役·验收取景 SHOT_BRIDGE 23.5,30.5（数据直证）。
4. **④16 vs blob-47**：4 邻 16 掩码可表边+外角·**缺内角（凹角）**——蜿蜒江湾对角对冲处现体系必漏变体（推测·水草直切部分来源）；最小升级=+4 内角变体（16+4=20·样区先验）；blob-47（8 邻组合旋转镜像去重=47·M 推导无外源）仅斜向大量内凹才值——RuleTile 3×3 三态原生即 47 语义（锚件）→升级=纯美术成本·机制零改。
5. **⑤装饰散布**：禁植掩码（F1 路径减法·FFF-401）=水格+2 格缓冲+路格±1+桥头 1 格；**丛植律**=3-5 株/丛（1 大 2-4 小·丛内距 1.5-2.5 格）·沿江两岸交替每 8-12 格一丛·单株仅许内部街区（距水≥5 格）；撒种=Poisson-disk min 距 1.5 格+确定性 seed；冠幅越线 2-4px 抗网格感（F2 思想）。现役实锤：TREES 53 株多为单株·无 3 株以上丛·最近树距水 1 格（49,28↔水 48,27 对角）。
## 二、环⑤ 天气与动态地表（逐条做法+参数）
1. **管线判定（判据③）**：City 在盘包族全列无 URP（A·PackageCache 直证：tilemap@1.0/pixel-perfect@5.1/animation@9.2/aseprite@1.1.9/feature.2d@2.0.1…）→**Built-in 管线**→URP Full Screen Pass Renderer Feature 在本工程不存在；全屏天气二选一=粒子 vs 精灵遮罩层（自写全屏 shader=高成本弃）。注：Assets 内嵌 URP 资产未扫（微险【🟡】）。
2. **雨=粒子主路径**（A·ParticleSystemRenderer）：renderMode 拉伸板+lengthScale（沿运动向拉伸·直读）+velocityScale（随速拉伸·直读）；Simulation Space=World·初速 -Y 18-30 u/s·条形贴图 2×16~2×24 artpx·发射 250-500/s·寿 1.2-2s（稳态 300-1000 粒）；排序=PS 继承 sortingLayerName/sortingOrder（地面上·UI 下·直读）；maxParticleSize 防正交爆屏（直读）；落地水花=免碰撞·随机触发 3-4 帧涟漪小精灵。雨矢量与 30° 俯角演出面一致（M·画风律）。
3. **雾/阴=精灵遮罩层**：2-3 张大软噪贴图精灵（α0.05-0.10·漂 0.2-0.6 u/s）+全屏暗化 quad（相机子物体·α0.10-0.15）·色相挂日夜色轮 tint（五件正典·R-20260925）；正交无深度=无距离雾概念（M）。
4. **云影=精灵层**：4-8 个软椭圆暗精灵（α0.10-0.18·12-30 格·漂 0.5-1.5 u/s 顺风同向）；Built-in 无 2D 灯→黑 α 叠加=暗化冒充 multiply（默认精灵 shader 为 alpha blend·M）。
5. **水面动态（补强·规格引用不重写）**：六件正典=R-20260925 §一；实装=AnimatedTile：Number of Animated Sprites 2-4·**Speed Min10/Max12**（帧率随机带宽=逐格错相·防满屏乱闪·A·AnimatedTile.md「A speed value will be randomly chosen between the minimum and maximum speed」）；泡沫线同步六件④；rain 事件驱动涟漪密度+倒影扰动=六件⑥（P-75）；水草/装饰低频更新 F5（N tick 一算+绘制插值·FFF-281）。
## 三、三瑕疵处方（每条 2022.3 可执行）
1. **曲路噪**：2px+段隙节奏 → atlas Generate Mip Maps+Padding4+alphaIsTransparency → S>16 切色带 LOD 变体层（算式 16.9/S·S=32→0.53px 必噪）。
2. **滨水孤树**：禁植掩码（水+2 格+路±1+桥头 1）+丛植律（3-5 株/丛·沿江 8-12 格两岸交替）+Poisson-disk 确定性撒种；样区 20/20 对比孤植 vs 丛植。
3. **水草直切**：双环过渡（泡沫环缩进 2px 断续 2-3 帧+湿滩/dither）+凹角 +4 内角变体（16+4=20）+decals 补丁层；SAND 104 环带=现役改造基底。
## 四、结论应用表
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 无 Top-Down 专用过渡件·Rect RuleTile 即俯视过渡机 | 优质化施工法 | ✓A（Tiles.md+包内直证） |
| City=Built-in（无 URP 包）→天气走粒子+精灵遮罩层 | 优质化施工法 | ✓A（PackageCache 直证·内嵌资产微险🟡） |
| 图集 Generate Mip Maps+Padding4+alphaIsTransparency 防渗 | 优质化施工法 | ✓A/A 双源（Manual+ScriptRef） |
| 曲路噪三层处方（2px 节奏/mipmap/S>16 色带 LOD） | 优质化施工法+32×32 样区 | 算式✓M·观感待样区实证 |
| 水岸双环+20 变体（16+4 内角·RuleTile 3×3 原生支持） | 32×32 样区 | 待实证 |
| 滨水丛植律+禁植掩码（F1 同源·49,28 临水 1 格实锤） | 优质化施工法 | 待实证 |
| AnimatedTile 2-4 帧·Speed 10-12 带宽错相 | 正典补遗（接六件①④⑥） | ✓A·逐格随机性待样区证 |
| 桥头 4+2 桥件·双掩码接缝法 | 优质化施工法 | 待实证 |
| Pixel Perfect Camera 备律：全 sprite 同 PPU+Filter Point+Compression None+Snap=1/PPU | 灰盒施工法 | ✓A（在盘包·Built-in 专用版可用） |
- 更新记录：T0 骨架 → T1 四锚件+判据校准 → T2 外网官方 4 件（SpriteAtlas/TextureImporter/PSRenderer/pixel-perfect）→ T3 本地包文档 3 件+PackageCache 直证 → T4 Runtime 脚本清单核验（零 top-down 字样·判据①收口）→ 终稿 33 行。
- 防线二：（留空待主会话抽验）
